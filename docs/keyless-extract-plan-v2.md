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

**Keyless should win somewhere, and now there is a metric that shows it.** An
extractive method that quotes the source cannot fabricate, so it scores
groundedness **1.000** against the LLM's 0.994. That reframes keyless from
"cheap approximation everywhere" to "strictly better on fabrication, strictly
worse on coverage".

## The candidates

Five, not seven. Each targets a property rather than all targeting detection.

| | Candidate | Target | Status |
|---|---|---|---|
| **K1** | anchor dictionary | `hasCredibilityFactor` | **measured, failed** — P 0.973 / R 0.235 / F1 0.367 |
| **K2** | extractive rationale — quote the sentence containing the match | rationale groundedness + density | premise confirmed by `control_first_sentence` |
| **K3** | entity patterns — model IDs, dataset names, requirement IDs | `bindsModel` / `bindsDataset` / `bindsRequirement` | needs `expected_entities` accuracy, not coverage |
| **K4** | local sentence embeddings | `hasCredibilityFactor` | the open hypothesis |
| **K5** | section and keyword extraction | `hasDecisionRecord`, `acceptance_criteria` | headed sections are a real surface signal |

**Dropped, with reasons.** C2 (expanded lexicon) is C1's mechanism against C1's
ceiling — the diagnosis was that enumeration is unbounded, so a bigger list is
the same finding at higher cost. C3 (spaCy rules) is C1 with a parser. C6 (NLI)
and C7 (fine-tuned encoder) are not keyless in any useful sense: they are models
you have to ship, train and version, which is the dependency the investigation
exists to remove.

## The gate that must not be skipped

> **A candidate may not be reported on a property until a constant has been
> measured on that property. If the constant matches it, the property is not
> measuring extraction.**

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

## What K2's ceiling actually is

`control_first_sentence` quotes one sentence per factor and scores **coverage
1.0 and groundedness 1.0** while saying the same thing thirteen times. So
groundedness alone is free for any extractive method, and K2's target is
groundedness *at high claim density with per-factor distinctness* — the three
numbers read together, exactly as the metric was designed to be.

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

Not "did a keyless method beat the LLM" — it will not, on coverage. The number
worth producing is the **hybrid ceiling**: with K2/K3/K5 filling their
properties, what fraction of the schema still requires a model, and what does
that leave to pay for? That is the question behind "keyless", and detection F1
was never measuring it.
