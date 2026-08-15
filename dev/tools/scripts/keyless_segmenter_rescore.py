#!/usr/bin/env python3
"""Score the keyless route on the fields it actually fills, old segmenter vs new.

The segmenter unification (`uofa_cli.segmentation`) changed the shipped keyless
route materially -- 243 sentence units to 553 on one fixture -- and
`studies/shipped-segmenter/FINDINGS.md` records it as **unrun, not passed**,
with a standing rule that nothing may cite it as an improvement until a scoring
path reaches the fields it moved.

This is that path.

## Why the first attempt found nothing

It scored `assessment_summary` against the corpus ground truth and reported
1 of 240 fields filled under the new segmenter and 5 of 240 under the old, with
zero matches either way. That was not a measurement of the segmenter. Measured
directly: **the keyless route fills zero assessment_summary fields on this
corpus.** It fills `decision.outcome` and `decision.rationale` on every bundle,
plus entities, validation results and factors.

Scoring a route on fields it never fills measures nothing, in either direction.

## What is scored here instead

**Only the decision.** Groundedness was the intended target -- it needs no
ground truth, and it is the exact property K2 used to measure the naive
splitter's cost (truncating "head rise is 0.72%" to "head rise is 0." scored
groundedness 0.000 instead of 1.000). It cannot be used here: **the keyless
route emits factor rows with `rationale: None` by design.** Its own
`summarise()` says so -- *"13 factors named, 0 scored -- keyless factor scoring
is 0.100 end to end"* -- and the module docstring is explicit that the blanks
are the feature, because `uofa import` must refuse the package.

Coverage is therefore 0/228 under both segmenters and the triple is undefined.
That is reported rather than dropped: a scorer returning zeros on a route that
fills nothing is not evidence of anything, and the first attempt at this
measurement failed by treating exactly that kind of zero as a result.

So the scoreable surface is `decision.outcome` against the four regression
fixtures, which carry `expected_decision`. The corpus bundles do not. **n = 4.**

Usage:

    PYTHONPATH=src python dev/tools/scripts/keyless_segmenter_rescore.py
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from groundedness import (  # noqa: E402
    GroundednessResult,
    read_source_text,
    score_factor_rationales,
)
from uofa_cli import keyless_extractor as ke  # noqa: E402
from uofa_cli import segmentation as seg  # noqa: E402
from uofa_cli.document_reader import read_corpus  # noqa: E402

# The splitter as it shipped before the unification, kept here so the comparison
# is against the real thing rather than a description of it.
_OLD = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")


def _old_split(text: str) -> list[str]:
    return [t.strip() for t in _OLD.split(text)]


def _v(fe):
    return getattr(fe, "value", fe)


def _run_corpus(bundles: list[Path]) -> GroundednessResult:
    agg = GroundednessResult()
    for bd in bundles:
        gt = json.loads((bd / "ground_truth.json").read_text())
        src = bd / "source"
        paths = sorted(p for p in src.iterdir()
                       if p.is_file() and not p.name.startswith("."))
        result = ke.extract(read_corpus(paths), gt["pack"])
        factors = [{"factor_type": _v(f.get("factor_type")),
                    "rationale": _v(f.get("rationale"))}
                   for f in result.credibility_factors]
        res = score_factor_rationales(factors, read_source_text(bd))
        for k in ("factors_total", "factors_with_rationale", "rationales_with_claims",
                  "claims_total", "claims_grounded", "factors_distinct"):
            setattr(agg, k, getattr(agg, k) + getattr(res, k))
        agg.ungrounded += res.ungrounded
    return agg


def _run_decisions() -> tuple[int, int, list[str]]:
    """Decision outcome against the four regression fixtures that carry gold."""
    from score_extraction import resolve_fixture

    right = total = 0
    notes = []
    for pack, case in (("vv40", "cou1"), ("vv40", "cou2"),
                       ("nasa-7009b", "cou1"), ("nasa-7009b", "cou2")):
        try:
            evidence_dir, gt_path, _ = resolve_fixture(pack, case)
        except SystemExit:
            continue
        gt = json.loads(Path(gt_path).read_text())
        want = (gt.get("expected_decision") or {}).get("outcome")
        if not want:
            continue
        paths = sorted(p for p in Path(evidence_dir).iterdir()
                       if p.is_file() and p.name != "EVIDENCE_MANIFEST.txt")
        result = ke.extract(read_corpus(paths), pack)
        got = _v(result.decision.get("outcome"))
        total += 1
        ok = isinstance(got, str) and got.strip().lower() == want.strip().lower()
        right += 1 if ok else 0
        notes.append(f"{pack}/{case}: want {want!r}, got {got!r} "
                     f"{'OK' if ok else 'WRONG'}")
    return right, total, notes


def _report(label: str, g: GroundednessResult, dec: tuple) -> None:
    r, n, notes = dec
    print(f"\n  {label}")
    print(f"    coverage       {g.coverage:.3f}   "
          f"{g.factors_with_rationale}/{g.factors_total}")
    print(f"    claim_density  {g.claim_density:.3f}   "
          f"{g.rationales_with_claims}/{g.factors_with_rationale}")
    print(f"    groundedness   {g.groundedness:.3f}   "
          f"{g.claims_grounded}/{g.claims_total}")
    print(f"    distinctness   {g.distinctness:.3f}")
    print(f"    ungrounded     {len(g.ungrounded)}")
    print(f"    decision outcome  {r}/{n}")
    for note in notes:
        print(f"      {note}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    bundles = [Path(b) for b in
               sorted(glob.glob(str(_ROOT / "tests/fixtures/extract_corpus/dev/bundle_*")))
               if (Path(b) / "ground_truth.json").exists()][:args.n]
    print(f"keyless route, {len(bundles)} dev bundles + 4 regression fixtures")

    new_g, new_d = _run_corpus(bundles), _run_decisions()

    original = seg.sentences
    seg.sentences = _old_split
    ke.segment = _old_split
    try:
        old_g, old_d = _run_corpus(bundles), _run_decisions()
    finally:
        seg.sentences = original
        ke.segment = original

    _report("OLD segmenter (naive split)", old_g, old_d)
    _report("NEW segmenter (uofa_cli.segmentation)", new_g, new_d)

    print("\n  delta, new minus old")
    print(f"    coverage       {new_g.coverage - old_g.coverage:+.3f}")
    print(f"    claim_density  {new_g.claim_density - old_g.claim_density:+.3f}")
    print(f"    groundedness   {new_g.groundedness - old_g.groundedness:+.3f}")
    print(f"    distinctness   {new_g.distinctness - old_g.distinctness:+.3f}")
    print(f"    decision       {new_d[0] - old_d[0]:+d} of {new_d[1]}")
    print("\n  Read the triple together. A groundedness gain with a claim_density "
          "\n  loss means fewer figures survived to be checked, which is the "
          "\n  failure the old splitter had -- not an improvement.")

    if args.out:
        args.out.write_text(json.dumps(
            {"old": old_g.as_dict() | {"decision": old_d[0], "decision_n": old_d[1]},
             "new": new_g.as_dict() | {"decision": new_d[0], "decision_n": new_d[1]}},
            indent=1) + "\n")
        print(f"\n  wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
