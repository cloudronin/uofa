# Metrics specification (R6 / U8)

Every measure this evaluation reports, with what it can and cannot establish, the
null it is reported against, and where its figures come from. Consumes
[the H2 conclusion](decisions/2026-08-15-h2-narrowed-conclusion.md).

**The governing rules, first, because they apply to every row below.**

> **1. No rate is quoted without its measurement context — corpus, base rate,
> n. Paired synthetic and real measurements are inseparable in every
> citation**, and where they disagree the real number is the result.
>
> **2. Any density or groundedness figure computed over PDF-borne documents
> states the reader's measured recovery rate.** A rate over an instrument whose
> recovery is unstated is a **floor, not a point.**

Rule 1 graduated to a standing rule on its third violation:
opportunities-versus-cards, then two shotgun probes that disagreed (0.740
against 0.9284, because one scored 447 rows and the other 376), then 0.247
against 0.605 on differently-defined labels. Each time the cost was paid
downstream by someone reading a figure in good faith.

**The firewall instance, and the most consequential of them.** In the
model-credibility pack the evaluation-sufficiency factors were originally
counted inside the documentation-completeness denominator, so the two profiles'
rates cross-contaminated: a compound risk escalation rendered under
documentation went from ninefold to twenty-fourfold **purely from
evaluation-layer firings**, meaning a benchmark gap surfaced as a documentation
Critical whose magnitude came entirely from evidence the documentation layer had
never assessed. The rate was arithmetically correct and described a population
its own section did not cover. The repair splits the readout into two firewalled
sections grouped by the node a finding affects, and routes every payload through
a single construction path so a caller cannot assemble it differently.[^firewall]

[^firewall]: `cloudronin/uofa` PR #45, commit `08cbfc78`, with the
    profile-dispatch tests and firewall fixtures that landed alongside it. The
    manuscript spans both repositories; this instance is in the pack repository
    rather than the evaluation harness.

**Rule 1's worked instance at corpus level.** A 4B local model was the claim-density
champion on the synthetic corpus at **0.420** and the only candidate that looked
like a challenger to the shipped extractor. On the real corpus it scored
**0.244**, below the floor, and failed coverage as well. Adoption on the
synthetic figure alone would have shipped a model that fails the bar on the
corpus that decides. The pair is the result; neither half is.

**Rule 2 exists because the instrument was wrong in the direction nobody
checked.** Before 2026-08-15 the scoring path read PDFs with `read_text`, which
surfaces object syntax rather than prose. On one paper the broken reading carried
761 spurious decimals *and was missing 15 of the 39 decimals that appear in the
document's sentences* — 38% of genuine figures unfindable, so honest claims
failed to ground. The direction was initially asserted to be optimistic and is
**pessimistic**; the correction is dated and carries the commit hash in
`studies/model-selection/FINDINGS.md`. The fixed reader's recovery against an
independent reference remains unmeasured, no second extractor being available,
so **every real-corpus density in this specification is a floor.**

---

## 1. Detection F1

**What it measures.** Whether the extractor names the credibility factors the
ground truth marks `assessed`.

**Null.** `control_constant_list` — the pack's fixed checklist, emitted having
read no input.

| | candidate, pre-correction | candidate | null | delta |
|---|---|---|---|---|
| development, 30 bundles | 0.9035 | 0.9637 | 0.9637 | **+0.0000** |
| held-out test, 20 bundles | 0.8909 | 0.9544 | 0.9544 | **+0.0000** |

**Both figures, always, per U2's disclosure discipline.** The pre-correction
column is what this measure read while a prompt-routing defect left six of
nineteen factors unrequested on every NASA document. Repairing the routing
removed the last variance the measure could observe, which is how it arrived at
its null. The V&V 40 half of each split was never affected and did not move
(0.9686 and 0.9652, before and after alike) — the internal control that
identifies this as a routing defect rather than a change in extraction quality.

**Status: reported, gates nothing.** It cannot distinguish reading the document
from not reading it. Per-factor F1 is 1.000 for all nineteen factors on both
splits, for the extractor and for the null alike.

**Never quote without the null in the same table.** That pairing is the
disclosure.

## 2. Attribution

**What it measures.** Whether a rationale cites evidence belonging to the factor
it was filed under — the only measure that sees *which* factor evidence was
assigned to.

**Rule.** Sentence-index: the sentence a rationale is most about, by token-F1
over the segmented source, must be one of the sentences that factor's evidence
occupies. Replaced a keyword-overlap rule that a random blob could beat.

| | candidate | permutation null | lift | n |
|---|---|---|---|---|
| synthetic | 0.4524 | 0.0526 | 8.6× | 515 |
| **real** | **0.0536** | 0.0098 | 5.5× | 56 |

**Nulls, all of them, every run.** Document-order constant, first-sentence,
random, shotgun at k ∈ {1, 5, 12, 20}, and a label-shuffle permutation null
computed on the run's own rationales so it inherits their length.

**Why the null battery is mandatory.** The predecessor rule scored 0.6068 and a
20-sentence blob of random source sentences — filed identically under every
factor, carrying no attribution judgment by construction — scored **0.7527**. A
metric a verbose null can beat is a length measure. The current rule takes that
same blob to 0.0505, and its sweep is nearly flat in k.

**Known residual bias.** Verbatim rationales score 0.5714 against paraphrased
rationales' 0.4399 — a +0.13 quoting advantage, partly structural. Report both
in any comparison between an extractive and a generative method.

**Localiser error rate.** At most 11.7% of scored rows, an upper bound.

## 3. The groundedness triple

**Never a lone number. Three, in this order.**

| | coverage | claim density | groundedness |
|---|---|---|---|
| synthetic, development | 1.000 | 0.188 | 0.982 |
| **six real papers** | **1.000** | **0.000** | **0.000** |

- **coverage** — factors given a rationale at all
- **claim density** — rationales carrying at least one checkable quantity
- **groundedness** — checkable quantities traceable to the source

**Read alone, any one of them misleads, and this has now happened twice in
measurable form.** On real documents, coverage 1.000 describes complete success
and groundedness 0.000 describes total fabrication; what occurred is that every
factor received a rationale and none contains anything to check. And across the
hosted-model migration, coverage *rose* to 1.000 and groundedness held at 0.990
while the corpus's checkable claims fell from 864 to 200 — two of three numbers
moving reassuringly while three quarters of the verifiable content disappeared.

**Goodhart caution, to be stated wherever the triple appears.** Coverage and
groundedness are ratios. When the population shrinks they can improve without
anything improving. The ungrounded triage set fell from 4 to 1 across that same
migration, which reads as progress until divided: 4/864 is 0.46% and 1/200 is
0.50%. The artefact rate did not move.

**Distinctness** is a fourth number and is not implied by the other three. A
control quoting one sentence for every factor scores 1.000 on all three and
0.000 on distinctness. Real papers: **0.417**.

## 4. The H2 replacement conjunction

Thresholds committed before measurement, in
[`2026-08-14-h2-replacement-thresholds.md`](decisions/2026-08-14-h2-replacement-thresholds.md).

| condition | threshold | real | |
|---|---|---|---|
| margin over the permutation null | ≥ 0.25 **and** ≥ 3 sd | +0.044 / 0.5 sd | **FAIL** |
| no null reaches the candidate, any length | absolute | 0.0000 | pass |
| below the agreement ceiling | 0.714 | 0.054 | pass |
| measured on the real corpus | — | 6 papers | pass |
| FP/FN published | — | 6 rows | pass, thin |
| groundedness as the triple | — | reported | pass |

**Condition 3 is a leakage detector, not a quality threshold.** It has no floor
and never passes anything; it only fires. A score above the agreement of the
humans defining truth is impossible for an honest instrument, so exceeding the
ceiling means the candidate and the reference are not independent. It fired on
its first real use, on a measurement that scored 0.8545 with three of six papers
at exactly 1.000 — circularity's signature.

## 5. Reference quality

| | figure | corpus |
|---|---|---|
| inter-annotator, same sentence | **0.714** | **real documents** |
| inter-annotator, same sentence | 0.913 | synthetic |
| ≥50% token overlap | 0.969 | synthetic |

**Use 0.714 for anything about real documents.** Substituting the synthetic
figure is a named trap in this project: the only reliability number it had was
measured on a synthetic corpus that subsequently inverted the ranking between
two methods, and checking the reliability of data you are no longer using is not
a check.

## 6. Sample sizes, which bound everything above

| measurement | n |
|---|---|
| synthetic corpus | 50 bundles, 800 factor rows |
| attribution, synthetic | 515 scored |
| **attribution, real** | **56 pairs, 3 correct, 6 papers** |
| disagreement adjudication, real | **6 rows** |
| decision outcome (segmenter comparison) | **4 fixtures** |
| annotators, real documents | **1** |

**The real-corpus figures do not support mechanism-level inference.** One paper
contributed all three correct attributions; another moved 1/12 to 0/12 between
runs of the same extractor. This is a property of the reference corpus, not of
the system, and no modelling change addresses it — only more annotated documents
and a second annotator.

## 7. Measures deliberately not used

- **A third metric after attribution.** Detection → attribution →
  something-else is gate-shopping. The conjunction was numbered before it ran so
  that there would be nowhere to move afterwards.
- **Bare groundedness.** See §3.
- **Bare detection F1.** See §1.
- **Any figure from an exploratory run.** Runs made without criteria declared in
  advance are marked as such in their scripts and outputs and may not be cited
  as results.
