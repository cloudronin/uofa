#!/usr/bin/env python
"""Draw the A16.3 gold-set sample from the FROZEN corpus and write the label sheet.

    python studies/taxonomy-validation/gold/make_gold_set.py --corpus <modelcard_info.parquet>

Emits:
  gold_set.csv   one blank row per card, columns exactly per instructions §4
  cards/<n>.md   the card text to label from, one file per row

Two properties this script exists to guarantee:

**Reproducible.** Fixed seed, recorded in the manifest. Re-running against the
same pinned corpus draws the same cards, so the sample is a pre-registered draw
rather than a convenience selection.

**Pinned per row.** Each row carries `row_hash`, the content hash of the card
text as it appears in the frozen parquet. That is what makes a label
re-derivable: it identifies WHICH text was labeled, not merely which model.
Labeling from live HF would silently substitute a different artifact, which is
why §4 says label from the parquet.

Labels are written BLANK. This script samples and formats; it does not guess,
and nothing here consults the extractor -- §"Blindness" requires the labeler
never see extractor output for a card being labeled.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "src"))

from uofa_cli.furnishers import card_eval  # noqa: E402

SEED = 20260811          # frozen; changing it draws a different study
PROPERTIES = ["P1_score", "P2_uncertainty", "P3_sampling", "P4_determinism",
              "P5_null_baseline", "P6_claimed_cou", "P7_confound_control"]

# The no-eval stratum validates the detector's NEGATIVE calls -- the direction
# that matters, since a false "no reported evaluation" claims a clean absence
# over evidence that exists. Kept smaller because it is a control, not the
# assessment population.
N_EVAL_BEARING = 120
N_NO_EVAL = 30
N_CALIBRATION = 10       # §5: labeled, then re-labeled at the next session


def _row_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def build(corpus: Path, out_dir: Path) -> dict:
    import pandas as pd

    frame = pd.read_parquet(corpus)
    frame = frame[frame["model_card"].notna()].copy()
    frame["_text"] = frame["model_card"].astype(str)
    frame = frame[frame["_text"].str.strip().str.len() > 50]

    # Recompute the detector rather than trusting a cached column: the sample
    # must reflect the detector the study actually ships.
    frame["_bearing"] = [card_eval.detect(t).found for t in frame["_text"]]
    frame["_words"] = frame["_text"].str.split().str.len()
    frame["_band"] = pd.cut(frame["_words"], bins=[0, 200, 800, 2000, 10**9],
                            labels=["0-200", "200-800", "800-2000", "2000+"])

    eval_pool = frame[frame["_bearing"]]
    none_pool = frame[~frame["_bearing"]]

    def stratified(pool, n, key_cols):
        """Proportional allocation across strata, deterministic within each."""
        if pool.empty:
            return pool.head(0)
        grouped = pool.groupby(key_cols, observed=True, dropna=False)
        sizes = grouped.size()
        alloc = (sizes / sizes.sum() * n).round().astype(int)
        parts = []
        for key, take in alloc.items():
            if take <= 0:
                continue
            block = grouped.get_group(key)
            parts.append(block.sample(n=min(take, len(block)), random_state=SEED))
        drawn = pd.concat(parts) if parts else pool.head(0)
        # Proportional rounding rarely lands exactly on n; top up deterministically.
        if len(drawn) < n:
            rest = pool.drop(drawn.index)
            if not rest.empty:
                drawn = pd.concat([drawn, rest.sample(
                    n=min(n - len(drawn), len(rest)), random_state=SEED)])
        return drawn.head(n)

    eval_sample = stratified(eval_pool, N_EVAL_BEARING, ["task_category", "_band"])
    none_sample = stratified(none_pool, N_NO_EVAL, ["task_category", "_band"])
    sample = (eval_sample.assign(_stratum="eval-bearing")
              .pipe(lambda d: __import__("pandas").concat(
                  [d, none_sample.assign(_stratum="no-eval")])))
    # Shuffle so the labeler does not meet all eval-bearing cards first; order
    # effects are checkable via session_id, but only if order is not stratum.
    sample = sample.sample(frac=1.0, random_state=SEED).reset_index(drop=True)

    cards_dir = out_dir / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    for stale in cards_dir.glob("*.md"):
        stale.unlink()

    rows = []
    for i, rec in sample.iterrows():
        text = rec["_text"]
        digest = _row_hash(text)
        card_file = f"{i + 1:03d}_{digest[:8]}.md"
        (cards_dir / card_file).write_text(text, encoding="utf-8")
        row = {
            "card_id": rec["modelId"],
            "row_hash": digest,
            "card_file": f"cards/{card_file}",
            "task_category": rec.get("task_category", ""),
            "stratum": rec["_stratum"],
            "word_count": int(rec["_words"]),
            "calibration": 1 if i < N_CALIBRATION else 0,
            "seen_before": "",
            "link_only": "",
        }
        for prop in PROPERTIES:
            row[prop] = ""
            row[f"{prop}_note"] = ""
        row["session_id"] = ""
        row["labeled_at"] = ""
        rows.append(row)

    sheet = out_dir / "gold_set.csv"
    with sheet.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    manifest = {
        "study": "taxonomy-validation/gold",
        "instructions": "docs/A16_3_gold_labeling_instructions_v0_1.md",
        "corpus": corpus.name,
        "seed": SEED,
        "n_total": len(rows),
        "n_eval_bearing": int((sample["_stratum"] == "eval-bearing").sum()),
        "n_no_eval": int((sample["_stratum"] == "no-eval").sum()),
        "n_calibration": N_CALIBRATION,
        "properties": PROPERTIES,
        "labels_blank": True,
        "note": ("Labels are blank by construction. This script samples and "
                 "formats; it never consults the extractor, because the "
                 "instructions require the labeler not see extractor output for "
                 "a card being labeled."),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=Path(__file__).parent)
    args = ap.parse_args()
    if not args.corpus.exists():
        raise SystemExit(f"corpus not found: {args.corpus}")

    manifest = build(args.corpus, args.out)
    print(f"gold set: {manifest['n_total']} cards "
          f"({manifest['n_eval_bearing']} eval-bearing, {manifest['n_no_eval']} no-eval)")
    print(f"  first {manifest['n_calibration']} flagged calibration=1 (label, then "
          f"re-label at next session start)")
    print(f"  sheet : {args.out / 'gold_set.csv'}")
    print(f"  cards : {args.out / 'cards'}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
