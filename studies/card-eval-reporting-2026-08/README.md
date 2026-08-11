# What model cards report, and whether it overlaps what a furnisher measures

Measured **before** designing the Phase-4 prose path and `W-EV-DIV-07`, because
both rest on assumptions about card content that are cheaper to check than to
debug. Two prior studies in this repo were written after the fact and each caught
a claim that had already been asserted; this one runs first.

| | |
|---|---|
| Population | most-downloaded text-generation models on the HF hub |
| Sample | 50 requested, **49 with a readable card** |
| Measured | 2026-08-11 |

Re-derive: `python studies/card-eval-reporting-2026-08/measure_card_reporting.py`

## Findings

| | |
|---|---|
| Cards with a markdown results table | **21 / 49 · 42.9%** |
| Cards naming **any** raidex constituent | **4 / 49 · 8.2%** |
| Which constituents | `simpleqa` ×3, `ethics` ×1 |

### 1. There is enough to extract — the prose path is justified

43% of cards carry a structured results table. Combined with the A3 finding that
HF `model-index` metadata sits at 4%, this settles the tier order for the eval
detector: **markdown/section scanning is primary, structured metadata
corroborates.** A backend-required prose extractor has real material to work on.

### 2. Cards and this furnisher measure disjoint things

Only 8% of cards name any raidex constituent, and the reason is structural rather
than incidental. Cards report **capability**; raidex measures **responsible-AI
properties**:

| Source | What it reports |
|---|---|
| `google/gemma-3-27b-it` card (40 benchmarks) | AGIEval, ARC, BBH, BoolQ, ChartQA, DROP, GPQA, GSM8K, HellaSwag, HumanEval, MATH, MBPP, MMLU, MMMU, PIQA, TriviaQA, WinoGrande, … |
| raidex (9 constituents) | bbq, wmdp, simpleqa, strongreject, ethics, xstest, advglue, confaide, sycophancy |
| **Shared** | **none** |

These are different questions asked of the same model. A card can report 40
benchmarks and still say nothing about bias, weapons knowledge, jailbreak
resistance, or privacy.

### 3. What a card can supply, per property — the Phase-4 rule table

Drafted **before** the extractor, with the middle column measured rather than
assumed. `n = 49`.

| Property (rule) | Mentioned anywhere | Under an evaluation heading | Can a card supply it? |
|---|---|---|---|
| `hasUncertaintyQuantification` (W-AL-01) | 1 · 2% | **1 · 2%** | Essentially never |
| `harnessDeterminismStatement` (W-EV-DET-03) | 22 · 45% | **2 · 4%** | Rarely — see below |
| `nullBaselineStatement` (W-EV-NULL-04) | 0 | **0** | Never observed |
| `samplingAccount` (W-EV-GEN-02) | 1 · 2% | **0** | Never observed |
| `confoundControlStatement` (W-EV-CAP-06) | 0 | **0** | Never observed |
| `metricValue` | — | 21 · 43% have a results table | Routinely |

**The determinism row is why the split exists, and it nearly cost a defect.**
45% of cards mention a sampling setting; **4% do so under an evaluation
heading**. The other 41% is guidance for the reader — `Qwen3` cards say "For
thinking mode, use `Temperature=0.6`", `opt-125m` explains `do_sample` in a usage
snippet. Those describe how to *run* the model, not how its reported scores were
*produced*.

An extractor keying on the token rather than the context would read that as a
determinism statement and **silence W-EV-DET-03 on 41% of models using evidence
about something else entirely** — manufacturing exactly the claim the rule tests
for. So:

> **The prose extractor must be section-scoped.** A value's presence in the card
> is not evidence about the evaluation. Only content under an evaluation heading
> may populate a Group-B property, and the extraction prompt must say so.

This is the prose-path analogue of the `"N/A"`-string rule in the raidex adapter:
a value that looks like the thing is not the thing.

## What this justifies

**`W-EV-DIV-07` is built, and it is rare.** Where a shared constituent exists it
is the highest-value finding the pack can produce — a self-reported number
disagreeing with an independent measurement. It will have something to compare on
roughly 8% of models, usually one constituent. That is worth building because
once prose extraction exists the rule is a comparison, not new machinery, but the
rate should be stated rather than discovered.

**The other five properties are near-zero from cards, which is itself the
finding.** A model card reports scores and almost never reports what would make
those scores interpretable — no uncertainty, no chance baseline, no sampling
account, no confound control. The prose path will therefore extract
`metricValue` and little else, and the Group-B weakeners will fire on
card-sourced evidence at roughly the rate they fire on raidex-sourced evidence.
Two independent sources, the same gaps: that is convergent evidence about
publishing practice, not about one furnisher.

**The disjointness gets its own rule, because it is the normal case.** For the
other ~92%, the published evaluation record does not cover the dimensions being
assessed at all. Nothing in the pack currently says so, and "this card reports no
evidence about the properties under assessment" is a credibility statement in its
own right — not a silence. A rule that fires only on the 8% would leave the
common situation unreported, which is the shape of gap this pack normally treats
as a finding.

## What would change the answer

Overlap is a property of what furnishers choose to measure and what card authors
choose to publish. A furnisher whose constituents track commonly-reported
capability benchmarks would invert this: DIV-07 becomes routine and the
disjointness rule rare. Re-run and record a new dated study if that happens
rather than editing this one.

The alias list in the script is deliberately generous — a narrow one would
understate overlap and bias the decision toward not building DIV-07 at all.
