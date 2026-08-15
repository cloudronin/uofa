#!/usr/bin/env python3
"""Point the attribution metric at human-annotated real documents.

Every attribution figure in this project is scored against `evidence_keywords`,
which gpt-5 wrote. `docs/v1/annot_*.json` is a different reference entirely: six
real papers, hand-annotated, spans written before any extractor ran. It has been
sitting unused by the metric because nothing converted it into the shape
`score_attribution` consumes.

This is that conversion, and nothing more. `v1_router_comparison.load_case`
already does the hard parts -- reading the PDFs, segmenting, mapping published
factor vocabulary onto the pack's via `cas_mapping.VARIANTS`, resolving each
annotated span's character offsets onto sentence indices, and dropping published
factors the pack has no constituent for. This wraps it.

## Read the number it produces with the following in mind

**It is not comparable to the synthetic-corpus attribution figure.** The
references are different units, and the gap is measured, not assumed:
`evidence_keywords` run a median of 3 content tokens, and the references this
script produces run a median of **24 words** (min 14, max 61) because an
annotated span is a whole sentence a reviewer would cite.

`score_attribution` counts a match when the rationale contains the reference
outright or shares at least half its content tokens, and half is not the same
bar at 3 tokens as at 24. A rationale clears "half of three" by accident far
more often than "half of twenty-four". The threshold is not scale-invariant,
which is the same defect -- seen from the reference side rather than the
rationale side -- that lets a long shotgun rationale outscore the extractor.

So a lower figure here is not evidence that real documents are harder. It may
be, and separating the two is the point of the length work, not a thing this
script settles. Report the two side by side, never one as the other.

**The metric being pointed at real documents is still the metric under
investigation.** A 20-sentence shotgun of random source sentences, filed
identically under every factor, scores 0.9284 on the synthetic corpus against
the extractor's 0.6383. Changing the reference does not fix that; it changes
what the ruler is held against, not the ruler. This exists so Phase 3's
candidate rules have a real-document reference to be validated on.

## What the reference is and is not

Six documents, one annotator, written before any extractor ran -- falsifying,
not confirming. `bologna`, `nagaraja` and `morrison` are V&V 40 documents whose
published vocabulary is the pack's, so their mapping is identity. The other
three carry a `cas_variant` and map through `VARIANTS`.

Spans that do not locate in the extracted text are dropped rather than counted
as misses, and the count of dropped spans is reported: a span lost to PDF
extraction is a fact about the reader, not about attribution. Before the
two-column PDF fix only 1 of 13 spans on `opensim` was contiguous, and any
figure computed then would have been measuring the reader.

Usage:

    PYTHONPATH=src python dev/tools/scripts/real_attribution_reference.py
    PYTHONPATH=src python dev/tools/scripts/real_attribution_reference.py --case morrison
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from v1_router_comparison import DOCS, load_case  # noqa: E402


def ground_truth_for(tag: str, bundle: str, annot: str) -> tuple[dict, dict]:
    """An `expected_factors` dict `score_attribution` accepts, from a hand annotation.

    Returns (ground_truth, stats). `evidence_keywords` carries the annotated
    sentences themselves, so the caller can see exactly what the rationale is
    being matched against -- these are references, never matcher seeds.
    """
    sents, _pool, gold, variant = load_case(tag, bundle, annot)
    raw = json.loads((_ROOT / "docs" / "v1" / annot).read_text())

    expected = [{"factor_type": pack_factor,
                 "evidence_keywords": [sents[i] for i in sorted(idxs)]}
                for pack_factor, idxs in sorted(gold.items())]

    stats = {
        "tag": tag,
        "variant": variant,
        "sentences": len(sents),
        "annotated_factors": len(raw["annotations"]),
        "factors_located": len(gold),
        "factors_dropped": len(raw["annotations"]) - len(gold),
        "spans_total": sum(len(a["evidence"]) for a in raw["annotations"]),
        "spans_located": sum(len(v) for v in gold.values()),
    }
    return {"expected_factors": expected}, stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--case", help="one tag from DOCS; default is all six")
    ap.add_argument("--out", type=Path, help="write the ground_truth dicts as JSON")
    args = ap.parse_args()

    cases = [d for d in DOCS if args.case in (None, d[0])]
    if not cases:
        raise SystemExit(f"unknown case {args.case!r}. Known: {[d[0] for d in DOCS]}")

    out, rows = {}, []
    for tag, bundle, annot in cases:
        gt, stats = ground_truth_for(tag, bundle, annot)
        out[tag] = gt
        rows.append(stats)

    print(f"{'case':<12s} {'variant':<14s} {'sents':>6s} {'factors':>8s} "
          f"{'located':>8s} {'dropped':>8s} {'spans':>6s} {'located':>8s}")
    for s in rows:
        print(f"{s['tag']:<12s} {str(s['variant'] or 'vv40 (identity)'):<14s} "
              f"{s['sentences']:>6d} {s['annotated_factors']:>8d} "
              f"{s['factors_located']:>8d} {s['factors_dropped']:>8d} "
              f"{s['spans_total']:>6d} {s['spans_located']:>8d}")

    dropped = sum(s["factors_dropped"] for s in rows)
    if dropped:
        print(f"\n  {dropped} annotated factor(s) dropped: either the pack has no "
              f"constituent for the published factor, or no span located in the "
              f"extracted text. Not scored as misses -- see the module docstring.")

    print("\n  These are references for scoring. They may not seed a matcher, and "
          "\n  nothing trained on these bundles may be scored on them.")

    if args.out:
        args.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
        print(f"\n  wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
