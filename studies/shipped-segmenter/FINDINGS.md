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

## Measured 2026-08-15: net neutral, and the error relocates

`dev/tools/scripts/keyless_segmenter_rescore.py`. The citation ban is lifted and
the answer is **not an improvement**.

| | old segmenter | new segmenter |
|---|---|---|
| decision outcome | **3/4** | **3/4** |
| vv40 (Morrison) COU1 | OK | OK |
| vv40 (Morrison) COU2 | **WRONG** — said Accepted | OK |
| nasa COU1 | OK | **WRONG** — said Not accepted |
| nasa COU2 | OK | OK |

**The change fixes Morrison COU2 and breaks nasa COU1.** Net zero at 3/4 either
way. This corrects the section above, which reported the Morrison correction
without knowing the trade: at the time only two fixtures had been looked at.

The Morrison fix is still the more consequential direction — a false `Accepted`
on a Class III VAD that regulators did not accept is the worst error this tool
can make, and `nasa COU1` failing the other way is the safer error. But **n = 4**,
and a 3/4-to-3/4 result with one swap in each direction is not evidence of
improvement in either.

### Why groundedness could not be used

Groundedness was the intended target: it needs no ground truth, and it is
exactly how K2 measured the naive splitter's cost. It cannot be used on this
route. **The keyless route emits factor rows with `rationale: None` by design** —
coverage is 0 of 228 under both segmenters, so the triple is undefined. Its own
`summarise()` says so: *"13 factors named, 0 scored — keyless factor scoring is
0.100 end to end"*, and the module docstring is explicit that the blanks are the
feature, because `uofa import` must refuse the package.

That is reported rather than dropped. The first attempt at this measurement
failed precisely by treating a route's structural zeros as a result — it scored
`assessment_summary`, which the route also never fills, got 1 of 240 versus
5 of 240 with no matches either way, and would have read as "neutral" to anyone
who did not check what was being scored.

### Standing of the change

**A bug fix, measured, and not an improvement.** It is landed because the
truncation defect is unambiguous and because one implementation is strictly
better than two that silently disagree — not because the route got better. It
did not.

Open: the nasa COU1 regression, and the rationale-span degradation on Morrison,
which looks like span *selection* preferring a short header line now that
headers are their own units.

## A limitation of the careful segmenter, pinned rather than left to be found

`(?<!\d\.)` cannot distinguish "0.72% of design" from "below 1e-6. The case", so
a sentence whose last character before the period is a digit runs into the next
one. Kept as is: the two failure directions are not symmetric. An over-split
destroys the figure that makes a span worth quoting; an under-split yields a
longer span that still contains it. `test_a_sentence_ending_in_a_number_does_not_split`
records the behaviour so a future fix has to beat it on both.
