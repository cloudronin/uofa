#!/usr/bin/env python3
"""C1: can the pack prompts' own `Look for:` anchors detect factors with no LLM?

Answer: they detect a quarter of them, almost always correctly, and that is
*worse* than printing the standard's checklist without reading anything.

    C1 dictionary            P 0.973   R 0.235   F1 0.367
    control_constant_list    P 0.928   R 1.000   F1 0.960

Precision 0.973 against the control's 0.928 is +4.5 points, against a kill
criterion that asked for >= 5 at equal recall -- and the recall is nowhere near
equal. So C1 fails the criterion on both clauses, narrowly on one of them.

The diagnosis matters more than the number. Lexical signal for the missed
factors is present in the source 94-100% of the time; the anchors are written at
the abstraction level of the standard ("QoI directly measures the safety
concern") while the documents are written at the level of the physics ("head
rise prediction", "SST k-omega"). Supplying that mapping is what the LLM does.
Discretization error recalls at 98% precisely because the standard coined one
canonical name for it -- GCI, Richardson extrapolation.

Runs in ~20s. No API key, no model download.

Usage:
    python dev/tools/scripts/keyless_extract_probe.py
    python dev/tools/scripts/keyless_extract_probe.py --split dev

Two limits, recorded rather than fixed:

* `Look for:` is captured single-line only. Harmless today -- all 13 vv40 and
  all 19 nasa factors parse -- but a multi-line anchor clause would be missed
  silently.
* P/R/F1 are macro-averaged per bundle. That is deliberate, not incidental:
  `score_extraction_batch` computes `mean_overall_f1` the same way, so this
  number and the eval's 0.964 are the same statistic and can sit in one table.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))

CORPUS = _ROOT / "tests" / "fixtures" / "extract_corpus"
PROMPTS = {
    "vv40": _ROOT / "packs" / "vv40" / "prompts" / "vv40_extract_prompt.txt",
    "nasa-7009b": _ROOT / "packs" / "nasa-7009b" / "prompts" / "nasa_7009b_extract_prompt.txt",
}


def parse_anchors(prompt_path: Path) -> dict[str, list[str]]:
    """factor label -> anchor phrases, from `N. **Factor**: ... Look for: a, b, c.`"""
    txt = prompt_path.read_text(encoding="utf-8")
    out: dict[str, list[str]] = {}
    for m in re.finditer(r"^\s*\d+\.\s+\*\*(.+?)\*\*:\s*(.*?)$", txt, re.M):
        label, body = m.group(1).strip(), m.group(2)
        lf = re.search(r"Look for:\s*(.+?)(?:\.\s*(?:Note|$)|\.$|$)", body)
        if not lf:
            continue
        anchors: list[str] = []
        for part in re.split(r",(?![^()]*\))", lf.group(1)):
            part = part.strip(" .")
            if not part:
                continue
            # "Grid Convergence Index (GCI)" is two usable surface forms.
            paren = re.match(r"^(.*?)\s*\((.+?)\)$", part)
            anchors += ([paren.group(1).strip(), paren.group(2).strip()]
                        if paren else [part])
        out[label] = [a.lower() for a in anchors if len(a) > 3]
    return out


def assert_anchors_come_from_the_prompt(anchors: dict[str, list[str]],
                                        prompt_path: Path) -> None:
    """Every anchor must be text that is actually in the prompt file.

    The contamination rule is about **provenance**: anchors are authored from
    the standards and the pack prompts, never copied from the corpus, and never
    from `evidence_keywords` -- those are verbatim source spans, so a matcher
    seeded with them scores near 1.00 by construction and `score_factors` does
    not read them, so nothing downstream would catch it.

    What this checks is that every phrase traces back to the prompt. What it
    deliberately does *not* check is overlap with `evidence_keywords`: an
    earlier version did, and it failed on "Richardson extrapolation" and "grid
    convergence index". Those appear in both places because they are the
    canonical names for the thing -- which is the whole reason Discretization
    error recalls at 98%. Convergence on a term of art is the mechanism working,
    not a leak. Overlap cannot distinguish copying from agreement; provenance
    can, and provenance is what the rule is actually about.
    """
    txt = prompt_path.read_text(encoding="utf-8").lower()
    strays = sorted({a for phrases in anchors.values() for a in phrases if a not in txt})
    if strays:
        raise SystemExit(
            f"PROVENANCE: these anchors are not present in {prompt_path.name}, so "
            f"they came from somewhere else and the run is not interpretable: {strays[:8]}"
        )


def detect(text: str, anchors: dict[str, list[str]]) -> set[str]:
    lowered = text.lower()
    return {f for f, phrases in anchors.items() if any(p in lowered for p in phrases)}


def prf(got: set[str], want: set[str]) -> tuple[float, float, float]:
    tp, fp, fn = len(got & want), len(got - want), len(want - got)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--split", choices=["dev", "test", "all"], default="all")
    args = ap.parse_args()

    anchors_by_pack = {p: parse_anchors(path) for p, path in PROMPTS.items()}
    for pack, a in anchors_by_pack.items():
        print(f"anchors: {pack} = {len(a)} factors / {sum(map(len, a.values()))} phrases")

    splits = ["dev", "test"] if args.split == "all" else [args.split]
    bundles = []
    for split in splits:
        for bd in sorted((CORPUS / split).glob("bundle_*")):
            gt = json.loads((bd / "ground_truth.json").read_text(encoding="utf-8"))
            md = json.loads((bd / "metadata.json").read_text(encoding="utf-8"))
            bundles.append({"dir": bd, "split": split, "meta": md, **gt})
    if not bundles:
        raise SystemExit(f"No bundles found under {CORPUS}")

    for pack, a in anchors_by_pack.items():
        assert_anchors_come_from_the_prompt(a, PROMPTS[pack])

    from score_extraction import control_predictions

    rows = []
    missed: dict[str, int] = defaultdict(int)
    for b in bundles:
        anchors = anchors_by_pack[b["pack"]]
        text = "\n".join(p.read_text(errors="ignore") for p in sorted((b["dir"] / "source").glob("*")))
        # Ground-truth and prompt factor labels are identical (verified: 19/19,
        # empty in both directions), so no normalisation is applied. That also
        # means a rules backend emitting these labels scores through
        # score_factors with no translation layer.
        want = {f["factor_type"] for f in b["expected_factors"]
                if f["expected_status"] == "assessed"}
        got = detect(text, anchors)
        control = {f["factor_type"] for f in control_predictions("control_constant_list", b["pack"])}
        rows.append({"split": b["split"], "pack": b["pack"],
                     "quality": b["meta"]["quality"], "format": b["meta"]["format"],
                     "c1": prf(got, want), "control": prf(control, want)})
        for f in want - got:
            missed[f] += 1

    def agg(label: str, sel, key: str) -> None:
        sub = [r[key] for r in rows if sel(r)]
        if not sub:
            return
        print(f"  {label:22s} n={len(sub):3d}  P={statistics.mean(x[0] for x in sub):.3f}"
              f"  R={statistics.mean(x[1] for x in sub):.3f}"
              f"  F1={statistics.mean(x[2] for x in sub):.3f}")

    print("\nC1 -- keyless substring match on the pack prompts' own anchors")
    agg("ALL", lambda r: True, "c1")
    for s in splits:
        agg(f"split={s}", lambda r, s=s: r["split"] == s, "c1")
    for p in ("vv40", "nasa-7009b"):
        agg(f"pack={p}", lambda r, p=p: r["pack"] == p, "c1")
    for q in ("complete", "ambiguous", "sparse"):
        agg(f"quality={q}", lambda r, q=q: r["quality"] == q, "c1")
    for f in ("report-md", "slides", "memo"):
        agg(f"format={f}", lambda r, f=f: r["format"] == f, "c1")

    # Printed in the same table, always. A bare 0.367 invites the reading that
    # a dictionary is a weak extractor; beside the control it is clear that it
    # is a *worse-than-nothing* one on this metric.
    print("\ncontrol_constant_list -- 0 parameters, reads no input")
    agg("ALL", lambda r: True, "control")

    c1_f1 = statistics.mean(r["c1"][2] for r in rows)
    ct_f1 = statistics.mean(r["control"][2] for r in rows)
    c1_p = statistics.mean(r["c1"][0] for r in rows)
    ct_p = statistics.mean(r["control"][0] for r in rows)
    print(f"\n  delta F1        {c1_f1 - ct_f1:+.3f}")
    print(f"  delta precision {c1_p - ct_p:+.3f}  (kill criterion 1 wanted >= +0.05 at equal recall)")
    print(f"  VERDICT: C1 {'beats' if c1_f1 > ct_f1 else 'DOES NOT BEAT'} the control on detection.")

    print("\nMost-missed factors (recall failures):")
    for k, v in sorted(missed.items(), key=lambda kv: -kv[1])[:10]:
        print(f"  {v:3d}/{len(rows)}  {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
