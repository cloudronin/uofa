#!/usr/bin/env python
"""Run the SIGNED enrichment search protocol over the pinned modelbiome field arm.

    python studies/taxonomy-validation/enrichment/search.py --corpus <ai_ecosystem_withmodelcards.csv>

Protocol: `studies/taxonomy-validation/ENRICHMENT-PROTOCOL.md` (signed 2026-08-11).
Venue for the field arm: `AMENDMENT-01-div07-venue.md` (signed 2026-08-11).

The protocol buys ONE measurement: specificity for P2/P5/P6/P7, the four
properties whose gold-set positive class is empty (0/150). Without positives, a
false FIRE -- a rule accusing a card that genuinely states the property -- has no
test case at all. That is the reputation-damaging direction.

Two properties this script exists to guarantee:

**The filter is mechanical, and both of its counts are reported.** Protocol s7
requires the keyword-selection bias be declared wherever specificity is reported.
So the manifest carries `pattern_v1_candidates` (every keyword hit, before any
exclusion) alongside `excluded_structural` broken out by reason. A reader can see
exactly what the pre-filter removed without re-running it.

**Exclusions are structural, never judgments about the card.** Protocol s5.2 is
binding: a candidate that turns out not to state the property is labeled `absent`
and KEPT, because discarding it biases the stratum toward positives. So nothing
here drops a card for looking unpromising. The two exclusions below remove
matches that are not prose at all, and both were measured on Liang first:

  template-heading  the match sits in a heading carrying no authored content
                    beyond the matched label. On Liang this removed 31 of 32 P6
                    candidates, every one the HF template's `## Intended uses &
                    limitations`. The phrase matched; the claim was never there.
  wordlist          the match sits inside a SentencePiece token inventory. On
                    Liang this removed 11 of 16 P7 candidates -- ASR vocabulary
                    dumps containing the literal token `▁CONFOUND`.

Neither looks at whether the card states the property. They remove text that is
not a sentence, which is a pre-filter's job.

The first rule started as plain "is it a heading" and was WRONG -- checked on
Liang it also removed `#### Ablation Studies 1: End-to-end v.s. Step-by-step:`,
the strongest P7 signal in that corpus. An authored heading is evidence; the
template's furniture is not. See `_is_furniture`.

**Over-cap sampling is random, never quality-ranked** (fixed seed, recorded).
Choosing the 30 "best-looking" candidates would select for the characteristic
language the protocol already warns is an upper bound.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "src"))

from uofa_cli.furnishers import card_eval  # noqa: E402

SEED = 20260811          # same frozen seed as the gold draw
CAP_PER_PROPERTY = 30    # protocol s3 ceiling
MICRO_GROUND_N = 30      # protocol s5a
CHUNK = 20_000

CORPUS_PINS = {
    "modelbiome": {
        "arm": "field arm (AMENDMENT-01, signed 2026-08-11)",
        "repo": "modelbiome/ai_ecosystem_withmodelcards",
        "revision": "4cb5d8739a8fce7c03826994dd756c244b4126bf",
        "file": "ai_ecosystem_withmodelcards.csv",
        "lfs_sha256": "7a6aaed5e4434e9bd3b5141c0fbb48da87ec267cfe96bffa2bb1f4d5b0d7c74f",
        "snapshot": "models 2025-07-13; cards scraped through 2025-07-21",
    },
    "liang": {
        "arm": "A16 validation corpus (PREREGISTRATION.md, frozen 2026-08-11)",
        "source": "Weixin-Liang/AI-model-card-analysis-HuggingFace",
        "file": "modelcard_info.parquet",
        "sha256": "79aa662d94d0112f13043f420d996347aeffea0dff52e0df919a95b6e4a0464d",
        "snapshot": "2023-10-01",
    },
}

# Protocol s5 step 1, made concrete. Frozen here so the frame is the artifact.
PATTERNS = {
    "P2_uncertainty": [
        r"±", r"\+/-", r"\bstd(?:ev|\.|\b)", r"\bstd\s*dev",
        r"95%\s*(?:CI|confidence)", r"confidence interval", r"standard error",
        r"\bstderr\b", r"\bs\.e\.\b", r"error bar", r"\bvariance\b",
        r"across \d+ (?:seeds|runs)",
    ],
    "P5_null_baseline": [
        r"chance level", r"random baseline", r"random chance", r"majority class",
        r"\bbaseline\b.{0,30}\brandom\b", r"above chance", r"majority baseline",
        r"trivial baseline",
    ],
    "P6_claimed_cou": [
        r"intended to demonstrate", r"intended use", r"is intended for",
        r"should (?:not )?be used (?:for|to)", r"out[- ]of[- ]scope",
        r"not intended (?:for|to)", r"suitable for", r"deployment context",
    ],
    "P7_confound_control": [
        r"controlling for", r"controlled for", r"ablation", r"held constant",
        r"same (?:prompt|template|seed) (?:for|across)", r"matched (?:on|for)",
        r"confound", r"all else equal",
    ],
}
COMPILED = {k: [re.compile(p, re.I) for p in v] for k, v in PATTERNS.items()}

_TOKEN_DUMP = re.compile(r"▁[A-Z]{3,}")
_ARXIV = re.compile(r"arxiv", re.I)
_MODEL_INDEX = re.compile(r"^\s*model-index\s*:", re.M)
# Protocol s4: pinned as modelbiome rows, never live HF. The head-card ground is
# the deep-study families; matched on the row's own id so the ground is
# reproducible from the corpus alone.
_HEAD = re.compile(r"^(meta-llama|Qwen|google|mistralai|deepseek-ai|allenai|"
                   r"microsoft|tiiuae|CohereLabs|CohereForAI|nvidia|ibm-granite|"
                   r"HuggingFaceTB|openai|anthropic)/", re.I)
_LMQG = re.compile(r"^lmqg/", re.I)


def _line_of(text: str, pos: int) -> str:
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    return text[start: end if end != -1 else len(text)]


def _is_furniture(heading: str, match: re.Match) -> bool:
    """Is this heading the card template's own furniture, or authored text?

    NOT simply "is it a heading" -- that rule was written against P6 and, when
    checked on Liang, it also removed `#### Ablation Studies 1: End-to-end v.s.
    Step-by-step:`, which is the single strongest P7 signal in the corpus. An
    authored heading is evidence; the template's is not.

    What separates them is residual content. Strip the matched label and see what
    the author actually wrote:

      `## Intended uses & limitations`  -> {limitations}                    -> 1
      `#### Ablation Studies 1: ...`    -> {studies,end,to,step,by,...}     -> 9

    So: furniture if <=2 words survive. Measured margin is 1 vs 9, not a knife
    edge. This is still structural -- it never asks whether the card states the
    property, only whether a human wrote this line or the template did.
    """
    body = heading.lstrip("#").strip()
    residual = re.sub(re.escape(match.group(0)), " ", body, flags=re.I)
    words = [w for w in re.findall(r"[A-Za-z]+", residual) if len(w) > 1]
    return len(words) <= 2


def _excluded_by(scoped: str, match: re.Match) -> str | None:
    """Structural reasons a match is not prose. Never a judgment about the card."""
    line = _line_of(scoped, match.start())
    if line.lstrip().startswith("#") and _is_furniture(line, match):
        return "template-heading"
    lo, hi = max(0, match.start() - 160), match.end() + 160
    if len(_TOKEN_DUMP.findall(scoped[lo:hi])) >= 3:
        return "wordlist"
    return None


def _int(value) -> int:
    """pandas infers dtype PER CHUNK, so one chunk with a missing `downloads`
    turns the column float64 and `int(nan or 0)` raises -- forty minutes in,
    with nothing written. NaN is also truthy, so `or 0` does not save it."""
    try:
        return 0 if value != value else int(value)   # NaN != NaN
    except (TypeError, ValueError):
        return 0


def _grounds(model_id: str, card: str, arxiv: str) -> list[str]:
    out = []
    if _HEAD.match(model_id or ""):
        out.append("head-card")
    if _LMQG.match(model_id or ""):
        out.append("lmqg-style")
    if (arxiv and arxiv.strip() not in ("", "[]")) or _ARXIV.search(card[:4000]):
        out.append("arxiv-citing")
    if _MODEL_INDEX.search(card[:4000]):
        out.append("model-index")
    return out or ["other"]


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def _self_hash() -> str:
    """Stamp the script into its own manifest. Two runs reporting different
    numbers should be attributable to a code change or a corpus change, and
    without this you cannot tell which."""
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:16]


def _records(corpus: Path, pd):
    """Normalize both pinned corpora to one record shape.

    Protocol s4 searches BOTH pinned grounds -- Liang, and the modelbiome field
    arm once AMENDMENT-01 is in force. Running them through two different
    scripts would make the two yields incomparable, which is the whole point of
    reporting them side by side. So the corpus difference lives here and
    nowhere else: same detector, same patterns, same exclusions, same seed.

    Liang is a parquet read whole (31 MB); modelbiome is a 5.2 GB CSV that must
    be chunked. Yields (model_id, card, arxiv, downloads, created_at).
    """
    if corpus.suffix == ".parquet":
        frame = pd.read_parquet(corpus)
        for rec in frame.itertuples(index=False):
            # Liang carries no arxiv/downloads/date columns. Absent stays
            # absent -- _grounds() falls back to scanning the card text for an
            # arXiv mention, which is the same test it applies to modelbiome.
            yield (str(getattr(rec, "modelId", "")),
                   getattr(rec, "model_card", None), "", 0, "")
        return

    reader = pd.read_csv(corpus, chunksize=CHUNK, low_memory=False,
                         usecols=["model_id", "modelCard", "arxiv_papers",
                                  "downloads", "createdAt"])
    for chunk in reader:
        for rec in chunk.itertuples(index=False):
            yield (str(rec.model_id), rec.modelCard, str(rec.arxiv_papers),
                   _int(rec.downloads), str(rec.createdAt))


def scan(corpus: Path) -> dict:
    import pandas as pd

    rng = random.Random(SEED)
    pool: dict[str, dict] = {}          # eval-text hash -> candidate
    micro: list[dict] = []              # s5a reservoir
    v1_counts = {p: 0 for p in PATTERNS}
    excl_counts: dict[str, dict[str, int]] = {p: {} for p in PATTERNS}
    # s7 requires yield reported PER DECLARED GROUND -- "candidates screened,
    # positives found. A low yield is a finding about publishing practice."
    # Screened is countable now; positives come from labeling.
    ground_screened: dict[str, int] = {}
    ground_cands: dict[str, dict[str, int]] = {}
    seen_micro = 0
    n_rows = n_cards = n_eval = 0

    for n_rows, (model_id, card, arxiv, downloads, created) in enumerate(
            _records(corpus, pd), start=1):
        if n_rows % (CHUNK * 10) == 0:
            print(f"  ...{n_rows:,} rows | {n_eval:,} eval-bearing | "
                  f"{len(pool):,} distinct candidates", flush=True)
        if not isinstance(card, str):
            continue
        text = card
        if len(text.strip()) <= 50:
            continue
        n_cards += 1
        secs = card_eval.eval_sections(text)
        if not secs:
            continue
        n_eval += 1
        scoped = "\n\n".join(s.text for s in secs)
        digest = hashlib.sha256(scoped.encode("utf-8")).hexdigest()[:16]
        grounds = _grounds(model_id, text, arxiv)
        for g in grounds:
            ground_screened[g] = ground_screened.get(g, 0) + 1
        # s5a: the unfiltered control, drawn from the richest ground BEFORE any
        # keyword test, so it cannot inherit the filter's bias.
        if "arxiv-citing" in grounds or "lmqg-style" in grounds:
            seen_micro += 1
            row = {"model_id": model_id, "row_hash": digest,
                   "eval_sections": scoped, "card": text,
                   "search_ground": "|".join(grounds),
                   "matched_pattern": "", "stratum": "micro-ground"}
            if len(micro) < MICRO_GROUND_N:
                micro.append(row)
            else:
                j = rng.randrange(seen_micro)
                if j < MICRO_GROUND_N:
                    micro[j] = row

        for prop, pats in COMPILED.items():
            kept, dropped = [], []
            for pat in pats:
                m = pat.search(scoped)
                if not m:
                    continue
                why = _excluded_by(scoped, m)
                (dropped if why else kept).append((pat.pattern, why))
            if not kept and not dropped:
                continue
            v1_counts[prop] += 1
            if not kept:
                why = dropped[0][1]
                excl_counts[prop][why] = excl_counts[prop].get(why, 0) + 1
                continue
            entry = pool.setdefault(digest, {
                "model_id": model_id, "row_hash": digest,
                "eval_sections": scoped, "card": text,
                "search_ground": "|".join(grounds),
                "downloads": downloads, "created_at": created,
                "props": {}, "dupes": 0,
            })
            entry["props"][prop] = "|".join(p for p, _ in kept)
            entry["dupes"] += 1
            for g in grounds:
                ground_cands.setdefault(g, {p: 0 for p in PATTERNS})
                ground_cands[g][prop] += 1

    return {"pool": pool, "micro": micro, "v1_counts": v1_counts,
            "excl_counts": excl_counts, "n_rows": n_rows, "n_cards": n_cards,
            "n_eval": n_eval, "n_micro_seen": seen_micro,
            "ground_screened": ground_screened, "ground_cands": ground_cands}


def select(res: dict) -> list[dict]:
    """Cap at 30/property. Over cap -> RANDOM draw, never quality-ranked."""
    rng = random.Random(SEED)
    chosen: dict[str, dict] = {}
    for prop in PATTERNS:
        having = [c for c in res["pool"].values() if prop in c["props"]]
        having.sort(key=lambda c: c["row_hash"])          # deterministic order
        if len(having) > CAP_PER_PROPERTY:
            having = rng.sample(having, CAP_PER_PROPERTY)
        for c in having:
            chosen.setdefault(c["row_hash"], c)
    return sorted(chosen.values(), key=lambda c: c["row_hash"])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    if not args.corpus.exists():
        raise SystemExit(f"corpus not found: {args.corpus}")

    kind = "liang" if args.corpus.suffix == ".parquet" else "modelbiome"
    actual = _file_sha256(args.corpus)
    pin = CORPUS_PINS[kind]
    expected = pin.get("lfs_sha256") or pin.get("sha256")
    if actual != expected:
        raise SystemExit(
            f"corpus hash mismatch for {kind}: got {actual}, pinned {expected}.\n"
            "Refusing to search an artifact the study has not pinned.")

    res = scan(args.corpus)
    picked = select(res)
    args.out = args.out or (Path(__file__).parent / kind)
    args.out.mkdir(parents=True, exist_ok=True)

    manifest = {
        "study": "taxonomy-validation/enrichment",
        "protocol": "studies/taxonomy-validation/ENRICHMENT-PROTOCOL.md",
        "venue": "AMENDMENT-01-div07-venue.md (field arm, signed 2026-08-11)",
        "corpus": kind,
        "corpus_pin": CORPUS_PINS[kind],
        "corpus_sha256_verified": actual,
        "script_sha256": _self_hash(),
        "seed": SEED,
        "rows_scanned": res["n_rows"],
        "cards_non_empty": res["n_cards"],
        "cards_eval_bearing": res["n_eval"],
        "cap_per_property": CAP_PER_PROPERTY,
        # s7: BOTH counts, so the pre-filter is inspectable rather than trusted.
        "pattern_v1_candidates": res["v1_counts"],
        "excluded_structural": res["excl_counts"],
        "distinct_after_dedup": {
            p: sum(1 for c in res["pool"].values() if p in c["props"])
            for p in PATTERNS
        },
        "selected_rows": len(picked),
        "micro_ground_n": len(res["micro"]),
        "micro_ground_seen": res["n_micro_seen"],
        # s7: a ground that screens many cards and yields none is a finding
        # about publishing practice, not a failed search.
        "ground_screened": res["ground_screened"],
        "ground_candidates": res["ground_cands"],
        "patterns": PATTERNS,
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with (args.out / "candidates.jsonl").open("w", encoding="utf-8") as fh:
        for c in picked:
            fh.write(json.dumps({**c, "stratum": "enriched"}) + "\n")
        for m in res["micro"]:
            fh.write(json.dumps(m) + "\n")

    print(f"scanned {res['n_rows']:,} rows / {res['n_cards']:,} cards / "
          f"{res['n_eval']:,} eval-bearing")
    print(f"{'property':22s} {'v1':>7s} {'excluded':>9s} {'distinct':>9s}")
    for p in PATTERNS:
        ex = sum(res["excl_counts"][p].values())
        print(f"  {p:20s} {res['v1_counts'][p]:>7,} {ex:>9,} "
              f"{manifest['distinct_after_dedup'][p]:>9,}")
    print(f"\nselected {len(picked)} enriched rows + {len(res['micro'])} micro-ground")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
