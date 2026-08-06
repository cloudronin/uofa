#!/usr/bin/env python3
"""K2: quote the sentence the anchor matched, instead of writing a rationale.

K1 asked whether the pack prompts' `Look for:` anchors can *detect* factors.
They can, at recall 0.235, which is worse than printing the checklist. K2 asks a
different question about the same anchors: when one does match, is the sentence
it matched worth quoting?

The premise is that an extractive method **cannot fabricate**. Every figure in a
quoted span is in the document by construction, so groundedness is 1.000 for
free. That immunity is real and it belongs to K2 alone -- K3 selecting the wrong
model and K5 lifting the wrong decision are *selection* errors, still verbatim,
and groundedness cannot see them.

## What "for free" costs

`control_first_sentence` quotes one sentence of the document for every factor
and scores:

    coverage 1.000   claim density 1.000   groundedness 1.000   distinctness 0.000

All three of the original numbers. So groundedness is not the result here --
distinctness is. K2 has to quote a *different, relevant* span per factor, and
the kill criterion is set there:

    KILL K2 if distinctness < 0.60

Below that it is `control_first_sentence` with extra steps.

## Sentence segmentation is not a detail

Splitting on a bare "." truncates "head rise is 0.72%" to "...is 0.", which
destroys exactly the numeric claims that make quoting worth doing -- it scored
groundedness 0.000 instead of 1.000 when `control_first_sentence` did it. The
segmenter here requires the period to be followed by whitespace and a capital,
and refuses to split inside a decimal, an abbreviation or a numbered list.

## Contamination

Anchors come from the pack prompt files and are asserted to, exactly as in K1.
`evidence_keywords` are verbatim source spans lifted by the corpus generator; a
matcher seeded with them would quote the answer back and score perfectly by
construction.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from groundedness import GroundednessResult, score_factor_rationales  # noqa: E402
from keyless_extract_probe import (  # noqa: E402
    PROMPTS,
    assert_anchors_come_from_the_prompt,
    parse_anchors,
)
from schema_controls import control_first_sentence  # noqa: E402

# A sentence ends at .!? + whitespace + capital/quote/bullet. The lookbehind
# excludes a digit, so "0.72%" never splits, and excludes the common
# abbreviations that otherwise fragment engineering prose.
_ABBREV = r"(?<!\bapprox)(?<!\bFig)(?<!\bEq)(?<!\bNo)(?<!\bvs)(?<!\bcf)(?<!\bi\.e)(?<!\be\.g)"
_SENTENCE = re.compile(rf"(?<=[.!?]){_ABBREV}(?<!\d\.)\s+(?=[A-Z\"“(\-•])")

# A quotable span has to be long enough to carry evidence and short enough to be
# a citation rather than a page dump.
_MIN_SPAN, _MAX_SPAN = 40, 400


def sentences(text: str) -> list[str]:
    """Split into sentences without breaking decimals or abbreviations."""
    out: list[str] = []
    for block in text.split("\n"):
        block = block.strip()
        if not block:
            continue
        # Markdown table rows and bullets are single units; splitting them on
        # punctuation produces fragments that quote as nonsense.
        if block.startswith(("|", "-", "*", "#")):
            out.append(block)
            continue
        out.extend(s.strip() for s in _SENTENCE.split(block) if s.strip())
    return out


def quote_for(anchor_phrases: list[str], spans: list[str],
              taken: set[int]) -> tuple[str | None, int | None]:
    """The best unused span containing one of this factor's anchors.

    Prefers a span carrying a digit: the whole value of quoting is the figures,
    and a sentence that merely names the concept is what K1 already established
    a dictionary can find.

    `taken` is what makes this K2 rather than the control -- a span already
    quoted for another factor is not reused, which is the difference between
    thirteen pieces of evidence and one pasted thirteen times.
    """
    best = None
    for i, span in enumerate(spans):
        if i in taken or not (_MIN_SPAN <= len(span) <= _MAX_SPAN):
            continue
        low = span.lower()
        if not any(p in low for p in anchor_phrases):
            continue
        has_number = bool(re.search(r"\d", span))
        score = (has_number, -abs(len(span) - 160))
        if best is None or score > best[0]:
            best = (score, span, i)
    if best is None:
        return None, None
    return best[1], best[2]


def extract_rationales(source_text: str, anchors: dict[str, list[str]]) -> list[dict]:
    spans = sentences(source_text)
    taken: set[int] = set()
    out = []
    for factor, phrases in anchors.items():
        quote, idx = quote_for(phrases, spans, taken)
        if idx is not None:
            taken.add(idx)
        out.append({"factor_type": factor, "rationale": quote})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", type=Path,
                    default=_ROOT / "tests" / "fixtures" / "extract_corpus_v2" / "dev")
    args = ap.parse_args()

    anchors_by_pack = {p: parse_anchors(path) for p, path in PROMPTS.items()}
    for pack, a in anchors_by_pack.items():
        assert_anchors_come_from_the_prompt(a, PROMPTS[pack])

    bundles = sorted(b for b in args.corpus.glob("bundle_*") if (b / "source").is_dir())
    if not bundles:
        raise SystemExit(f"no bundles under {args.corpus}")

    k2, ctl = [], []
    for b in bundles:
        pack = json.loads((b / "metadata.json").read_text()).get("standard", "vv40")
        src = "\n".join(p.read_text(errors="ignore")
                        for p in sorted((b / "source").glob("*")))
        anchors = anchors_by_pack[pack]

        k2.append(score_factor_rationales(extract_rationales(src, anchors), src))
        ctl.append(score_factor_rationales(
            control_first_sentence(src, list(anchors)).credibility_factors, src))

    def row(label: str, rs: list) -> tuple[str, float]:
        """Ratios from pooled totals, never a mean of per-bundle ratios.

        `groundedness` returns 0.0 for a bundle with no checkable claims -- a
        deliberate rule, since making no claim is not the same as making only
        true ones. Averaging those zeros across bundles reported K2 at 0.492
        when not one of its quotes was ungrounded: a verbatim span cannot
        contain a number the document lacks, and the figure was an artefact of
        the aggregation rather than a fact about the method.
        """
        agg = GroundednessResult()
        for r in rs:
            for k in ("factors_total", "factors_with_rationale", "rationales_with_claims",
                      "claims_total", "claims_grounded", "factors_distinct"):
                setattr(agg, k, getattr(agg, k) + getattr(r, k))
        print(f"  {label:24s} cov {agg.coverage:.3f}  den {agg.claim_density:.3f}  "
              f"gnd {agg.groundedness:.3f}  distinct {agg.distinctness:.3f}")
        return label, agg.distinctness

    print(f"\nK2 -- quote the matched sentence   ({len(bundles)} bundles)\n")
    _, k2_d = row("K2 extractive", k2)
    _, ctl_d = row("control_first_sentence", ctl)

    print(f"\n  KILL CRITERION: distinctness >= 0.60")
    print(f"  K2 distinctness {k2_d:.3f} -> "
          f"{'PASSES' if k2_d >= 0.60 else 'FAILS -- this is the control with extra steps'}")
    print(f"  margin over the control: {k2_d - ctl_d:+.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
