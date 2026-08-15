# evidence_span fails its product spec twice, and is 2.7x better than the rationale

Phase 2, 2026-08-14. Two arms, both against criteria declared before running
(`DECLARATION.md`). 8 bundles, 152 factor rows,
`meta-llama/Llama-3.3-70B-Instruct-Turbo`.

## Result

| | arm 1 | arm 2 | floor | |
|---|---|---|---|---|
| span filled | 0.993 | 0.980 | ≥ 0.70 | PASS |
| span verbatim in corpus | 0.258 | **0.369** | ≥ 0.70 | **KILL** |
| localises to a source sentence | not measured | 0.711 | — | reported, not gating |
| stitched | 5/151 | 5/149 | — | |

Arm 2's revision — keep parentheticals, the span must survive exact search —
moved verbatim from 0.258 to 0.369. Real movement, less than half the distance
to the floor.

**`evidence_span` is killed as specified.** One declared revision, measured,
failed. There is no arm 3: iterating a prompt until it clears a criterion is the
criterion doing no work.

## What the failure is, stated precisely

The non-verbatim spans are **not invented**. Every one inspected is the
document's own words, in the document's own order, with parenthetical or
trailing material silently removed — similarity to the nearest source sentence
runs 0.75–0.86:

- dropped `(lid-driven cavity Re=1000, backward-facing step, and rotating channel flow)`
- dropped `(scaled residuals)`
- dropped `from the aerodynamics methods group (Dr. …)`

"The model invents evidence spans" would be false and is a worse error than the
one being measured. The true statement: **the model elides without marking the
elision**, so the span cannot be found by exact search — which defeats the one
thing the field was specified for. A reviewer told to search the document for
this string gets no result 63% of the time.

## The comparison the declaration promised, and it is not small

Same 8 bundles. The rationale figures come from the committed `routing-fix-v1`
extractions — a different run of the same model on the same corpus, which is
the right comparison for a question about the *shape* of the output.

| | rationale | evidence_span | ratio |
|---|---|---|---|
| localises to a source sentence (token overlap ≥ 0.60) | **0.263** | **0.711** | **2.7×** |
| verbatim substring of the corpus | 0.039 | 0.369 | 9.5× |
| median length | 14 words | — | |

The field fails the product spec and is, by a wide margin, the better input to
Phase 3. Sentence-index attribution needs a text that maps to a source sentence;
rationales do that 26% of the time and spans 71% of the time.

## The declaration and this result disagree, and that is for the user to resolve

`DECLARATION.md` says, in full: *"If arm 2 fails, `evidence_span` is killed as
specified and Phase 3 proceeds on rationales alone."*

That clause was written before rationale localisation was measured. It assumed
rationales were a workable Phase 3 input; at 0.263 they are a poor one. The
kill criteria themselves were about the **product** claim — a span a reviewer
can find — and that claim is dead on the evidence, twice.

**Overriding a pre-registered consequence because the evidence came out
inconvenient is the exact move this project has spent a month building
discipline against.** So it is not being done quietly here:

- The product claim is dead. `evidence_span` may not be described anywhere as a
  span a reviewer can search for, and it does not become a workbook column.
- Whether Phase 3 may *consume* the field is a decision that overrides a written
  consequence, and it needs to be a dated, visible one rather than a silent one.
- Until it is made, Phase 3's rule is built to accept either text and reports
  both, so nothing is blocked and neither option is foreclosed. The
  rationale-based figure is the primary one, as declared.

## What is not measured either way

Whether the span is the **right** sentence for the factor. Localisation says a
span maps to *some* source sentence, not the correct one. That is attribution,
it is what Phase 3 measures, and neither arm here touches it.

`model-credibility` was deliberately not changed. It is not in the 50-bundle H2
corpus (25 vv40 + 25 nasa-7009b), so any change to its prompt would be unmeasured
— and its FACTOR block has a different shape, with `rationale` after the status
prose rather than adjacent to the fields.

## The change broke a guard the project had already paid for

Inserting the `evidence_span` note after the `status:` field pushed the absence
rule from 1 line away to 16, and
`test_absence_rule_sits_with_the_field_it_governs` failed on both prompts. That
test exists because the rule *was already present* and *was ignored* at 14
lines' distance — the shopping-list failure, where a corpus of groceries scored
thirteen of thirteen factors `assessed`.

The rule now sits immediately below `status:` again and the span note follows
it. Caught by the suite, not by review.

**Consequence for the numbers above:** arm 2 was measured against the
pre-reorder layout, so the shipped prompt now differs from the one that produced
0.369 by paragraph order. Nothing depends on that — the field is killed and no
figure here justifies shipping anything — but the measurement and the artifact
are not identical, and saying so is cheaper than someone finding it.

## Cost note for the plan

The plan estimated this field as free to parse: *"`_parse_kv_block` already
handles unknown keys, so parsing costs nothing."* Parsing does. But
`_validate_factor` is a **whitelist** — it copies six named fields and drops
everything else without a word — so the field died one function past the parser
and a prompt change would have looked like it did nothing. The Credibility
Factors sheet is a further, larger boundary: eight columns indexed positionally
by the writer, `parse_extracted_xlsx`, the import path and the goldens.

That is why this was measured out of `ExtractionResult` rather than the
workbook. A schema change to carry a field that then fails its criteria is
churn spent on nothing.
