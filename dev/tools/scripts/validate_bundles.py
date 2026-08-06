#!/usr/bin/env python3
"""Are these evidence bundles worth extracting, or are they duds?

A bundle is source documents plus the ground truth describing what a correct
extraction should find in them. The extraction pass over 100 bundles takes hours
and, from now on, API spend -- so the question "is this bundle sound" has to be
answerable before that pass, not after it.

`_validate_full_schema` in the generator already checks the ground truth's shape
at write time. This checks the harder thing: whether the ground truth is
**about the documents that were actually written**.

## The check that matters

`evidence_keywords` are specified as "phrases that appear LITERALLY in the
source documents". When they do not, the ground truth is describing a document
that does not exist, and the failure is silent and inverted: the extractor reads
the real document, fails to find evidence the ground truth insists is there, and
is scored wrong for being right. A corpus with that defect makes every candidate
look worse than it is and no number downstream reveals it.

The keyword check is exact-substring, case-insensitive, on normalised
whitespace. It is deliberately not fuzzy: the generator was told to pull
phrases verbatim, so a near-miss is a real finding about the generator, not
noise to be smoothed over.

## What counts as a dud

    hard    ground truth cannot describe these documents -- do not extract
    soft    unusual but extractable; reported, not fatal

Hard failures are what the extraction pass must not be spent on. Soft ones are
worth seeing before drawing conclusions from the run.

Usage:
    python dev/tools/scripts/validate_bundles.py tests/fixtures/extract_corpus_v2/dev
    python dev/tools/scripts/validate_bundles.py <dir> --json report.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# A source set smaller than this cannot plausibly evidence 13-19 credibility
# factors. Chosen from the shipped corpus, whose smallest sound bundle is well
# above it; the point is to catch truncation and empty writes, not to police
# length.
_MIN_SOURCE_CHARS = 1500

# Below this share of evidence_keywords actually present, the ground truth is
# not describing these documents. Not 100%: a keyword may legitimately span a
# line break or be split by markdown emphasis, and failing a whole bundle for
# one such phrase would discard sound work.
_MIN_KEYWORD_HIT_RATE = 0.70


@dataclass
class BundleVerdict:
    bundle: str
    hard: list[str] = field(default_factory=list)
    soft: list[str] = field(default_factory=list)
    keyword_hit_rate: float | None = None
    source_chars: int = 0
    factors: int = 0

    @property
    def ok(self) -> bool:
        return not self.hard


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()


def check_bundle(bundle_dir: Path) -> BundleVerdict:
    v = BundleVerdict(bundle=bundle_dir.name)

    gt_path = bundle_dir / "ground_truth.json"
    src_dir = bundle_dir / "source"
    if not gt_path.exists():
        v.hard.append("no ground_truth.json")
        return v
    if not src_dir.is_dir():
        v.hard.append("no source/ directory")
        return v

    try:
        gt = json.loads(gt_path.read_text())
    except json.JSONDecodeError as exc:
        v.hard.append(f"ground_truth.json is not valid JSON: {exc}")
        return v

    files = sorted(p for p in src_dir.glob("*") if p.is_file())
    if not files:
        v.hard.append("source/ is empty")
        return v

    texts = {p.name: p.read_text(errors="ignore") for p in files}
    joined = _norm("\n".join(texts.values()))
    v.source_chars = sum(len(t) for t in texts.values())
    if v.source_chars < _MIN_SOURCE_CHARS:
        v.hard.append(
            f"source is {v.source_chars} chars, under {_MIN_SOURCE_CHARS} -- "
            f"likely truncated or an empty write")

    factors = gt.get("expected_factors") or []
    v.factors = len(factors)
    if not factors:
        v.hard.append("ground truth lists no factors")
        return v

    # The check this file exists for.
    total = hits = 0
    missing_examples: list[str] = []
    for f in factors:
        for kw in f.get("evidence_keywords") or []:
            if not isinstance(kw, str) or not kw.strip():
                continue
            total += 1
            if _norm(kw) in joined:
                hits += 1
            elif len(missing_examples) < 4:
                missing_examples.append(f"{f.get('factor_type')}: {kw!r}")
    if total:
        v.keyword_hit_rate = hits / total
        if v.keyword_hit_rate < _MIN_KEYWORD_HIT_RATE:
            v.hard.append(
                f"only {hits}/{total} ({v.keyword_hit_rate:.0%}) evidence_keywords "
                f"appear in the source -- the ground truth is describing a "
                f"different document. e.g. {missing_examples}")
        elif missing_examples:
            v.soft.append(
                f"{total - hits}/{total} keywords absent, e.g. {missing_examples[:2]}")
    else:
        assessed = [f for f in factors if f.get("expected_status") == "assessed"]
        if assessed:
            v.hard.append(
                f"{len(assessed)} factors marked assessed but no evidence_keywords "
                f"anywhere -- nothing anchors the ground truth to the source")

    # A named source_file that does not exist means the anchor is unusable.
    for f in factors:
        sf = f.get("source_file")
        if sf and sf not in texts:
            v.soft.append(f"source_file {sf!r} not in source/ ({sorted(texts)})")
            break

    # Every assessed factor should be findable; a bundle where nothing is
    # assessed has no signal to extract.
    assessed = sum(1 for f in factors if f.get("expected_status") == "assessed")
    if assessed == 0:
        v.hard.append("no factor is marked assessed -- nothing to extract")
    elif assessed < 3:
        v.soft.append(f"only {assessed} assessed factors")

    return v


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("corpus", type=Path, help="directory holding bundle_* dirs")
    ap.add_argument("--json", type=Path, default=None, help="write a JSON report")
    args = ap.parse_args()

    bundles = sorted(p for p in args.corpus.glob("bundle_*") if p.is_dir())
    if not bundles:
        raise SystemExit(f"no bundle_* directories under {args.corpus}")

    verdicts = [check_bundle(b) for b in bundles]
    bad = [v for v in verdicts if not v.ok]
    soft = [v for v in verdicts if v.ok and v.soft]

    rates = [v.keyword_hit_rate for v in verdicts if v.keyword_hit_rate is not None]
    print(f"\n  {len(verdicts)} bundles checked")
    if rates:
        print(f"  evidence_keywords found in source: "
              f"mean {sum(rates)/len(rates):.1%}, worst {min(rates):.1%}")
    print(f"  extractable: {len(verdicts) - len(bad)}   duds: {len(bad)}")

    for v in bad:
        print(f"\n  DUD  {v.bundle}  ({v.source_chars} chars, {v.factors} factors)")
        for m in v.hard:
            print(f"       {m}")
    if soft:
        print(f"\n  {len(soft)} bundles with soft findings:")
        for v in soft[:10]:
            print(f"    {v.bundle}: {v.soft[0]}")

    if args.json:
        args.json.write_text(json.dumps(
            [{"bundle": v.bundle, "ok": v.ok, "hard": v.hard, "soft": v.soft,
              "keyword_hit_rate": v.keyword_hit_rate,
              "source_chars": v.source_chars, "factors": v.factors}
             for v in verdicts], indent=2))
        print(f"\n  report -> {args.json}")

    # Non-zero exit so a generation script can gate the extraction pass on this.
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
