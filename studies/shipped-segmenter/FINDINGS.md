# The shipped keyless route had its own, worse sentence segmenter

Phase 0 plumbing, 2026-08-14. Filed with its costs, because it is a bug fix with
mixed measured consequences and it must not later be cited as an improvement.

## What was wrong

Two segmenters. Fifteen dev components imported the careful one from
`dev/tools/scripts/keyless_k2_extractive.py`. `src/uofa_cli/keyless_extractor.py`
— the route users actually run — had its own:

```python
_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")
```

It splits inside a decimal. "Measured head rise is 0.72% of design" becomes
"Measured head rise is 0." and the figure is gone. K2 measured what that costs
when the fragment is then quoted as evidence: **groundedness 0.000 instead of
1.000**, because the whole value of quoting a span is the numbers in it.

So the shipped route quoted worse spans than every dev experiment that scored
it, and any span-based measurement standing on the naive splitter was partly
measuring the splitter.

## The change

`uofa_cli.segmentation.sentences` is the K2 implementation, moved where
production can import it. `keyless_k2_extractive` re-exports it under the same
name, so its fifteen importers are untouched and there is one definition.
`tests/test_segmentation.py` pins the decimal case, the abbreviation case, the
markdown-row case, and that both call sites resolve to the same function object.

It is larger than "stops truncating decimals". The careful version also splits
per line and treats markdown rows and bullets as units, so the text re-units
substantially:

| corpus | old units | new units |
|---|---|---|
| aero-evidence-cou2 | 243 | 553 |
| morrison-evidence-cou2 | 74 | 335 |

Table rows and bullets become quotable spans instead of being buried inside
oversized blobs that the 40–400 character span filter would reject.

## What that does to the route, measured

The two fixture bundles that carry decision ground truth, comparing the shipped
route's own output fields:

**aero-evidence-cou2** — 1 of 15 fields changed, and it is better. The decision
rationale went from a blob beginning with the section header `"Item 7 -
Decision\n\n…"` to `"NOT ACCEPTED at MRL 4 for cruise creep-life certification
analysis."`

**morrison-evidence-cou2** — 4 of 15 changed, and it is mixed:

| field | old | new | gold |
|---|---|---|---|
| `decision.outcome` | Accepted | **Not accepted** | Not accepted |
| `decision.rationale` | a substantive sentence | `"Decision NOT ACCEPTED"` | keywords incl. "not sufficiently credible", "MRL 5" |
| `summary.cou_name` | wrong span | different wrong span | "CFD prediction of hemolysis levels for VAD device (VAD)" |
| `summary.cou_description` | wrong span | different wrong span | — |

The outcome correction is the one that matters. A false `Accepted` on a Class
III VAD that regulators did not accept is the worst error this tool can make,
and the old segmenter was making it. The rationale span got worse — a header
fragment instead of a sentence — and `cou_name` moved from one wrong answer to
another.

## What is not measured, and should be before anyone claims an improvement

A corpus-scale keyless re-score was attempted over the 30 dev bundles and
**produced no interpretable signal**: the route fills 1 of 240
`assessment_summary` fields under the new segmenter and 5 of 240 under the old,
with zero matches at token-F1 0.6 either way. That is not evidence that the
change is neutral — it is evidence that this harness does not exercise the
fields in question on this corpus. The comparison is unrun, not passed.

So the standing of this change is: **a bug fix with one demonstrated correction
on the most consequential field, one demonstrated regression on rationale span
quality, and no corpus-scale measurement.** It is landed because the truncation
defect is unambiguous and because one implementation is strictly better than two
that disagree — not because the route was shown to improve.

Two follow-ups: a keyless scoring path that actually reaches these fields, and
the rationale-span regression on morrison, which looks like span *selection*
preferring a short header line now that headers are their own units.

## A limitation of the careful segmenter, pinned rather than left to be found

`(?<!\d\.)` cannot distinguish "0.72% of design" from "below 1e-6. The case", so
a sentence whose last character before the period is a digit runs into the next
one. Kept as is: the two failure directions are not symmetric. An over-split
destroys the figure that makes a span worth quoting; an under-split yields a
longer span that still contains it. `test_a_sentence_ending_in_a_number_does_not_split`
records the behaviour so a future fix has to beat it on both.
