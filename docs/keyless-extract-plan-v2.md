# Keyless extraction: revised candidate plan

Supersedes the C1–C7 candidate list. The original plan had seven candidates all
competing on detection F1. Three findings since have made that framing wrong,
and this records what replaces it.

Companion to [`keyless-extract-findings.md`](keyless-extract-findings.md), which
carries the measurements.

## Why the original framing does not survive

**Detection is not a task on this corpus.** `control_constant_list` — zero
parameters, reads nothing — scores **F1 0.960**, rising to **0.971** on the real
NTRS bundles. Headroom to a perfect detector is 0.040, and the constant is
unbeatable on 23 of 50 bundles. Six more candidates competing there buys nothing
that C1 has not already shown.

**The bar is a package, not a score.** That same constant **fails `uofa import`**
on the Minimal profile's requirements. It does not produce a deficient
credibility package; it produces none. So the question is not "can a keyless
method reach 0.960" but "which of the required properties can it fill at all".

**K2 should win somewhere, and now there is a metric that shows it.** A method
that quotes the source verbatim cannot fabricate, so it scores groundedness
**1.000** against the LLM's 0.994.

That immunity belongs to **K2 alone**, and the distinction matters because the
reframe rests on it. K3 pattern-matching a model name can pick the wrong model —
the one cited from a reference paper rather than the one under assessment. K5
can lift the wrong decision from the wrong section. Those are **selection
errors, not fabrication**, and groundedness cannot see them: the wrong answer is
still verbatim in the document. K3 and K5 therefore need their own correctness
measure, which for K3 is the `expected_entities` count check and for K5 is
outcome accuracy against `expected_decision`.

## The candidates

Five, not seven. Each targets a property rather than all targeting detection.

| | Candidate | Target | Status |
|---|---|---|---|
| **K1** | anchor dictionary | `hasCredibilityFactor` | **measured, failed** — P 0.973 / R 0.235 / F1 0.367 |
| **K2** | extractive rationale — quote the sentence containing the match | rationale groundedness + density | premise confirmed by `control_first_sentence` |
| **K3** | entity patterns — model IDs, dataset names, requirement IDs | `bindsModel` / `bindsDataset` / `bindsRequirement` | needs `expected_entities` accuracy, not coverage |
| **K4** | local sentence embeddings | `hasCredibilityFactor` | the open hypothesis |
| **K5** | section and keyword extraction | `hasDecisionRecord`, `acceptance_criteria` | headed sections are a real surface signal |

### Sizing and kill criteria

Every item has a budget and a stopping rule. The plan this supersedes had
both; dropping them is how an open hypothesis turns a week into a month.

| | Build | Kill criterion — stop if |
|---|---|---|
| **K2** | ~4 h | distinctness < 0.60 after real sentence segmentation. Below that it is `control_first_sentence` with extra steps. |
| **K3** | ~6 h | entity-count MAE not better than `control_constant_entity`'s on **both** corpora. The constant answers "1, always"; failing to beat that is failing outright. |
| **K4** | ~8 h | recall < 0.50 at precision ≥ 0.90 on dev. C1 reached R 0.235; below 0.50 embeddings have not bought enough over substring matching to justify the encoder. |
| **K5** | ~3 h | outcome accuracy not better than `control_constant_decision` (always "Accepted"). |

**Total ~21 h, and a hard cap of 30.** If the four are not measured by then the
finding is that keyless extraction is not cheap to build either, which is itself
worth reporting.

**K4 gets the tightest leash** because it is the open hypothesis and therefore
the one that will absorb unlimited time. One encoder, one pooling strategy, one
threshold sweep. If `all-MiniLM-L6-v2` at its best threshold misses the
criterion, the answer is "not with a small local encoder" — trying six more
models is a different investigation.

**Dropped, with reasons.** C2 (expanded lexicon) is C1's mechanism against C1's
ceiling — the diagnosis was that enumeration is unbounded, so a bigger list is
the same finding at higher cost. C3 (spaCy rules) is C1 with a parser. C6 (NLI)
and C7 (fine-tuned encoder) are not keyless in any useful sense: they are models
you have to ship, train and version, which is the dependency the investigation
exists to remove.

## The gate that must not be skipped

> **A candidate may not be reported on a property until a constant has been
> measured on that property under that metric. If the constant matches it, the
> metric on that property is not measuring extraction — and the fix is a better
> metric, not a dropped property.**

The wording matters. `bindsModel` is a perfectly good property to score; it was
*coverage on* `bindsModel` that a constant saturated. The right response was to
switch to `expected_entities` counts, not to stop scoring the binding. A rule
phrased as "the property is not measuring extraction" tells a future reader to
abandon exactly the wrong thing.

This is not hypothetical caution. Having added schema coverage to fix the
one-property problem, the controls were measured and found this:

| property | LLM | a constant |
|---|---:|---:|
| `bindsDataset` | 80% | **100%** |
| `bindsModel` | 82% | **100%** |
| `bindsRequirement` | 54% | **100%** |
| `hasContextOfUse` / `hasDecisionRecord` / `modelRiskLevel` | 100% | **100%** |

`control_constant_entity` emits *"one model, called 'the model'"*, satisfies
`minCount >= 1`, and **beats the extractor on three properties and ties on
three**. Coverage was about to become the second metric a null model saturated.

So K3 is scored on `expected_entities` **counts**, which the v2 corpus carries
and the shipped one did not — a constant answering "1, always" is wrong by four
on a document naming five models. Coverage is necessary and never sufficient.

## What K2's ceiling actually is, and the fourth number

`control_first_sentence` quotes one sentence per factor. Measured on a real
bundle it scores:

    coverage 1.000   claim density 1.000   groundedness 1.000

**All three.** Reading them together does not catch it. Density counts
rationales that carry a claim; it never asks whether they carry the *same*
claim, so a quoted sentence containing numbers passes every one.

So distinctness is a **fourth column with its own definition**, not an
implication of the other three:

> **distinctness** — the fraction of factors whose rationale does not restate
> another rationale in the same bundle. Two count as the same when their token
> sets overlap by ≥ 60% of the shorter one (containment, not Jaccard, so a long
> quote and a sentence taken from inside it count as one).

    control_first_sentence   cov 1.000  den 1.000  gnd 1.000  distinct 0.000
    LLM (v4-kv, 50 bundles)  cov 0.974  den 0.565  gnd 0.994  distinct 0.995

K2's target is groundedness at high density **and** high distinctness. Without
the fourth column the control built to expose the loophole passes it.

A concrete hazard found while building that control: splitting sentences on a
bare `.` truncates `"head rise is 0.72%"` to `"...is 0."`, scoring groundedness
0.000 instead of 1.000. Naive segmentation destroys precisely the numeric claims
that make extraction worth doing. K2 needs real sentence segmentation on day one.

## K4: local only

Embeddings run from a local encoder — `all-MiniLM-L6-v2`, ~90 MB, one-time
download, no key. An embedding API was considered and rejected: it reintroduces
the dependency the investigation exists to remove, so a win there would answer a
different question than the one asked.

**"Keyless" means a 90 MB encoder, not "no model".** The honest comparison is
against `ollama/qwen3.5:4b` at ~5 GB of weights and 170–202 s per bundle. The
harness already instruments wall clock and peak RSS per run, so the report can
state weight, latency and accuracy together rather than implying the first two
are zero.

## What gets scored, and against what

Every candidate reports against **both** corpora:

- **v2 synthetic** (100 bundles, gpt-5-generated) — levels 1–5, `required_level`
  present, full ProfileComplete ground truth
- **13 Tier 1 real bundles** — transcribed from published NASA CAS tables,
  biomechanics rather than aerospace

The second matters most for K1/K4: a lexicon or embedding space tuned on
aerospace prose meets a domain it has never seen, which is the external-validity
question the synthetic corpus cannot answer.

## The headline deliverable

Not "did a keyless method beat the LLM" — it will not, on coverage.

The deliverable is the **hybrid ceiling**, and it must be reported as a
**named list of the properties still requiring a model, never as a count**.
"Nine of thirteen covered" is a useless sentence: `hasContextOfUse` and
`generatedAtTime` are not the same size of hole, and a fraction lets four
properties carrying the entire substance of the assessment disappear behind a
reassuring 69%.

So the output is a table, one row per required property:

| Property | Filled by | Correctness measure | Verdict |
|---|---|---|---|
| `hasCredibilityFactor` | K1 / K4 | detection F1 vs `control_constant_list` | |
| rationale | K2 | groundedness × density × **distinctness** | |
| `bindsModel` / `bindsDataset` / `bindsRequirement` | K3 | `expected_entities` count MAE | |
| `hasDecisionRecord` | K5 | outcome accuracy vs `control_constant_decision` | |
| `modelRiskLevel`, `required_level` | — | judgment from risk; no keyless route proposed | |
| `hasValidationResult` | — | not attempted | |

The last two rows are the point. If `modelRiskLevel` and `required_level` need a
model, then the shape of the answer is "keyless fills the extractive properties
and a model is still required for the judgment ones" — which is a real finding
about where the cost floor sits, and it is invisible in any fraction.
