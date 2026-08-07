# Keyless extraction: plan v4 — fill every row

Supersedes v3's deliverable section. v3 left six of nine rows as `?`, `untested`
or `not attempted`. This proposes a keyless candidate for each and fixes the
measurement discipline v3's numbers lacked.

Measured on **37 factor-document pairs across 5 real journal-prose documents**:
two NASA-STD-7009A (opensim, elemance) and three ASME V&V 40 (bologna,
nagaraja, morrison). Two standards, five documents, one annotator.

### The denominator is the findable subset, and that biases every number

51 factor-document pairs are possible. **39 were annotated and 12 were not** —
and the 12 are not `not_applicable`, they are the ones where a careful reader
looked for evidence and could not locate it.

| document | possible | annotated | excluded |
|---|---|---|---|
| opensim | 6 | 6 | 0 |
| elemance | 6 | 6 | 0 |
| bologna | 13 | 11 | 2 |
| nagaraja | 13 | 10 | 3 |
| **morrison** | 13 | **4** | **9** |
| total | 51 | 39 | 12 (24%) |

Excluded: `Equivalency of input parameters` (all three V&V 40 documents),
`Test conditions` (three), and for Morrison a further seven whose per-factor
content sits inside Tables 3–4 rather than in prose.

**So recall@k is measured on the pairs where evidence was findable, and the
hard cases are outside the denominator.** Every number in this plan carries
that. Two consequences:

* Report **annotation coverage (39/51) beside every recall figure**, and treat
  the excluded pairs as an upper bound on optimism — if a router would have
  missed them too, true recall is lower by up to 24%.
* Coverage is itself a finding. A reader who cannot locate per-factor evidence
  for a quarter of factors is telling you something about the documents, not
  about the router. `Equivalency of input parameters` is unfindable in three
  independent papers, which is a stronger statement than any recall number here.

The fix is not to annotate harder. It is to record, per excluded pair, **why**:
absent from the document, present only in a table, or present but not locatable.
That turns 12 silent exclusions into 12 data points.

## What changed since v3

1. **Synthetic evaluation inverts method rankings.** K6 scores 0.829 recall@5 on
   held-out synthetic bundles and **0.22** on real journal prose; K4 scores 0.505
   and **0.38**. The corpus does not merely flatter absolute numbers — it picks
   the wrong method. v3's headline `K6 → K2, attribution 0.615` names the loser.
2. **Detection is worse than v3 thought.** `control_constant_list` scores 0.960
   synthetic and **1.000** on the real corpus.
3. **The router/selector split is measured.** Selection accuracy falls
   1.000 → 0.833 → 0.250 as the shortlist grows 5 → 20 → 40. The router's job is
   precision at small k, not recall at large k.
4. **Two required properties exist only in one standard's documents.** This is
   the finding that reshapes the deliverable.

### The presence problem, measured on all five

Keyword-presence probes. Crude, so read them as presence/absence, not as
extraction targets.

| property | opensim | elemance | bologna | nagaraja | morrison |
|---|---|---|---|---|---|
| | *7009A* | *7009A* | *V&V40* | *V&V40* | *V&V40* |
| `hasContextOfUse` | **0** | **1** | 39 | 33 | 50 |
| `modelRiskLevel` | **0** | **0** | 22 | 17 | 23 |
| `hasDecisionRecord` | 0 | 3 | 7 | 4 | 8 |
| `hasValidationResult` | 5 | 15 | 10 | 12 | 9 |
| `bindsDataset` | 13 | 29 | 13 | 15 | 12 |
| `bindsRequirement` | 7 | 34 | 4 | 3 | 32 |

The separation is categorical, not marginal: **every V&V 40 document states
context of use and model risk; neither 7009A document states either.** V&V 40 is
a risk-based framework and requires both by construction. NASA-STD-7009A is not
and does not.

So a row can fail two ways, and the deliverable must distinguish them:

* **extractable but unextracted** — the evidence is on the page and no keyless
  method finds it. A candidate can fix this.
* **absent from the source** — the document never states it. *No* extractor
  fixes this, keyless or not. The LLM's 100% population of `hasDecisionRecord`
  is this case: 77% of those values were invented.

**A row whose property is absent is reported as absent, not as a low score.**
Scoring it rewards fabrication, which is the failure mode this work exists to
detect. Two rows are absent *conditionally on the standard*, so the deliverable
needs a per-standard column, not one number.

## The nine rows, with a candidate each

### Group A — solved, but v3 names the wrong router

| row | candidate | measured on real prose |
|---|---|---|
| `hasCredibilityFactor` | **K4 routing**, not detection | detection unmeasurable (constant 1.000); routing 0.38 recall@5 |
| per-factor `rationale` | **K4 → K2** (route, then quote) | groundedness 1.000 by construction |

#### K4's lead is real but smaller than three documents implied

| router | @1 | @3 | @5 | @10 | @20 |
|---|---|---|---|---|---|
| K6 | 0.08 | 0.14 | 0.22 | 0.32 | 0.49 |
| K4 | 0.08 | **0.24** | **0.38** | 0.46 | 0.49 |
| RRF | **0.14** | 0.22 | 0.35 | 0.43 | **0.54** |

K4's advantage at k=5 fell from **3.3× to 1.7×** when the sample went 3 → 5
documents. It wins 4 of 5 documents individually; **Nagaraja reverses it**, K6
0.40 against K4 0.20.

A vocabulary hypothesis was proposed for the exception — K6 is lexical, so it
should win where the document uses the standard's own terminology — and the data
**does not support it**:

| document | canonical factor names present | winner @5 |
|---|---|---|
| opensim | 0/13 | K4 |
| elemance | 0/13 | K4 |
| bologna | 11/13 | K4 |
| nagaraja | 12/13 | K6 |
| morrison | 13/13 | K4 |

**Superseded by D1.** The K4 advantage above was measured against an annotation
that (a) drew Bologna's spans from a summary table rather than the body prose and
(b) excluded 12 pairs the annotator could not find. Correcting both:

Final, at 90% annotation coverage (55 scored pairs):

| k | K6 | K4 | **RRF** |
|---|---|---|---|
| 1 | **0.182** | 0.127 | **0.182** |
| 3 | **0.291** | 0.236 | 0.255 |
| 5 | 0.327 | 0.327 | **0.364** |
| 10 | 0.400 | **0.436** | 0.418 |
| 20 | 0.545 | 0.491 | **0.600** |
| 40 | 0.600 | 0.564 | **0.709** |

K4 minus K6 at recall@5, as the evidence improved: **+0.334 → +0.160 → +0.019**.
K6 now wins at k=1 and k=3.

**"K4 beats K6 on real documents" was an artefact of measuring on the pairs the
annotator could find, and those pairs favoured K4.** No router has a decisive
lead. **RRF is the default** — best at k=5 and k=20, never worst — chosen for
robustness rather than for a margin, since 0.018 at k=5 is inside the noise that
annotation choices have already been shown to produce.

### Group B — announced properties, findable by section + routing

| row | candidate | presence |
|---|---|---|
| `modelRiskLevel` | **K8: extract *and validate*.** | V&V 40 only (22/17/23 vs 0/0) |
| `hasContextOfUse` | **K7: CoU/QoI section extraction.** | V&V 40 only (39/33/50 vs 0/1) |
| `hasDecisionRecord` | **K5, re-run presence-first.** | thin everywhere (0–8) |

**K8 is now the strongest candidate in this plan**, and it moved up on evidence.
V&V 40 defines model risk as a *function* of two inputs, so the derivation is a
lookup table — pure code once both inputs are found. The keyless route is "find
two words, index a table", and it yields a consistency check no LLM performs.

All three V&V 40 documents supply the inputs, and **Morrison supplies them in
prose for two different contexts of use**:

> *"Model Influence: the influence is low because the data to support the safety
> assessment are based on in vitro test data"*
> *"Decision Consequence: if the pump causes high levels of hemolysis while the
> patient is in the surgical suite, then the pump can be replaced"*

Across the synthetic corpus, model influence is stated in **0%** of documents.
Morrison is the K8 test case; Bologna is the adversarial one, because it
substitutes *regulatory impact* for model influence and argues for it — a
validator must report a documented deviation, not a mismatch.

K7 and K8 are both **V&V 40-only rows**. On 7009A documents they must report
absent, and a candidate that returns a value there is fabricating.

### Group C — quantitative claims, findable by shape

| row | candidate |
|---|---|
| `hasValidationResult` | **K9: comparison-sentence routing.** A validation result is a comparison verb + a quantity + a referent — "compared to PMHS data, error within 10%". Route on that *shape*, not on factor vocabulary. |

Never attempted in v3, and the most tractable unfilled row: distinctive
syntactic signature, present in **all five** documents (5/15/10/12/9), and
`expected_validation_results` already exists with a `name_keywords` + `has_uq` +
`pass_fail` match rule.

### Group D — role disambiguation, where K3 failed

| row | candidate |
|---|---|
| `bindsModel`, `bindsDataset`, `bindsRequirement` | **K3c: embedding role classification.** |

K3 reported ~5 models per bundle against a ground truth of ~1.8, and its own
diagnosis was that the error is *role*, not type: a document names the model
under assessment, the solver it runs on, models compared against, and models
cited from the literature, and all four look identical to a pattern and to
off-the-shelf NER.

K4's result suggests the fix. "Is this the model being assessed, or one cited
from prior work?" is a role question an embedding can be asked directly: score
each candidate against *"the computational model under assessment in this
study"* versus *"a model referenced from prior work"* and take the margin. The
encoder is already loaded, so this costs nothing new.

### Group E — not an extraction problem

| row | candidate |
|---|---|
| `wasDerivedFrom` | **Emit the input filenames and their hashes.** |

27 of 27 corpus packages satisfy `wasDerivedFrom` with the template's own help
text, which JSON-LD coerces to a `file://` URI and which therefore satisfies
`sh:nodeKind sh:IRI`. The requirement is met by the instructions for meeting it.
A one-line bug fix, not a keyless win, and it must not be counted as one.

## Measurement discipline

Learned the expensive way; not negotiable for a v4 number to mean anything.

1. **Score on real journal prose.** Synthetic may be shown for contrast, never
   as the result. The corpus inverts rankings.
2. **Every candidate needs a null model measured on real documents.** The
   constant scores 1.000 there.
3. **Measure presence before accuracy**, and report it per standard.
4. **Report routing recall@k and selection accuracy together.** Optimising
   either alone picks the wrong configuration: the best ceiling (RRF@40, 0.667)
   produced the worst pipeline (0.167 end to end).
5. **Keep shortlists short.** k=5 default; larger needs the selection cost
   measured, not assumed.
6. **The furniture filter applies to the routing path only.** The CAS table is
   noise for rationale and gold for levels.
7. **`evidence_keywords` may never seed a matcher.** Unchanged from v2.
8. **The reliability check must run on the data being relied on.** Done — D1,
   below. It found two defects and changed the headline result, at a cost of a
   few hours against the 19h of candidates it preceded.
9. **Expect a new extraction pathology per document genre.** Four so far, each
   invisible on synthetic markdown and each found only by reading real output:
   column interleaving, line wrapping, lost inter-word spaces, and reproduced
   gradation rubrics surviving as standalone sentences. Budget for a fifth.

## D1: done, and it changed the result

gpt-5 re-annotated all five documents independently; a second pass by the same
annotator measures consistency, not reliability.

| | first pass | after fix 1 | after fix 2 |
|---|---|---|---|
| factor selection | 76.9% | 81.2% | **92.0%** |
| same sentence | 15.0% | 50.0% | **71.4%** |
| ≥50% token overlap | 40.0% | 66.7% | **76.1%** |

Two defects, one in the data and one in the protocol:

**Fix 1 — my annotation was table-biased.** All 12 Bologna spans sat in sentences
501–525 of 989: a contiguous 2% block that is Table 1. gpt-5 annotated the body
prose the table summarises. Both are "evidence" and the document contains it
twice, but the prose carries the checkable claims — "a dataset of 101 calibrated
CT scans", "an error of 7 pp", "TÜV" — where the table carries the standard's
summary vocabulary. Re-annotated under a rule fixed in advance; Bologna went
0/10 → 5/10.

**Fix 2 — the protocol withheld scope.** These papers assess several models
across several mechanisms, and a bundle is one (model × mechanism) pair. gpt-5
was given the document and the factor list but not the pair, and quoted THUMS
femur/tibia evidence for an Elemance/thoracic bundle. Elemance went 1/6 → 6/6.
The failure mode was already known — naming the model took the selection stage
from 3/6 to 5/6 — and withholding it here manufactured disagreement that would
have been read as unreliable annotation.

**The denominator was the bigger finding.** gpt-5 located evidence for **10 of
the 12 pairs excluded** as "no evidence found": "a convergence study was
conducted using three different meshes", "PIV experiments in the pump were
repeated five times". Nine verified and were added. Coverage **39/51 → 46/51**,
scored pairs **37 → 53** — and that recovery is what collapsed the K4 result.

71.4% is substantial, not decisive. Every figure resting on the annotation
carries it, and gpt-5 is not a human SME: this bounds reader-dependence, it does
not establish correctness.

### D2: coverage 39/51 → 46/51, and the last three are documented

Two of the five remaining pairs were findable after all — Morrison's
`Discretization error` ("a convergence study was conducted using three different
meshes") and Bologna's `Equivalency of input parameters` ("analogous boundary
conditions were replicated"). Coverage is **46/51 = 90%**.

The other three now carry a written ledger entry instead of a silent gap:

* **nagaraja / Equivalency of input parameters** — no finding. The paper
  reproduces the gradation definitions and discusses input parameters at length
  in the sensitivity analysis, but never asserts simulation and experiment inputs
  were equivalent. The independent annotator did not find it either.
* **morrison / Numerical solver error** — no finding. The only sentences naming
  it are the V&V 40 definition, not a statement about this model.
* **morrison / Use error** — **UNKNOWN, not absent.** The candidate region is
  damaged: *"Previous literature has is mandatory in this reported user error in
  implementing the situation."* is two columns spliced. The detector splits 11 of
  Morrison's 12 pages, so this is residual damage on a page it handles.

That third entry is the one worth keeping. "Absent from the document" and "our
reader could not parse it" are different claims, and only the first belongs in a
deliverable. Recording it as unknown is what stops a tooling limit from being
published as a property of the evidence.

## Sequencing

An earlier draft of this plan said "adding candidates cannot substitute for
adding documents" and then sequenced five candidates and zero documents. That is
self-contradictory, and the contradiction favoured the fun work. Corrected:
**documents first.**

Two documents did more to the K4 result than any candidate could — going from
three to five halved its apparent lead and produced a reversal that is still
unexplained. Nineteen hours of candidates judged on the same 39 pairs, where two
documents carry 57% of the sample, buys less confidence than two more documents.

| | work | cost | why here |
|---|---|---|---|
| ~~**D1**~~ | ~~Second annotator pass~~ | **done** | 71.4% after two fixes; collapsed the K4 result |
| ~~**D2**~~ | ~~Re-check the 5 remaining uncovered pairs~~ | **done** | 2 recovered, 3 have a written ledger entry; coverage 90% |
| **D3** | **Frontiers V&V/in-silico-implantables collection** | ~6h | 7 articles on stent deployment, stent-grafts, flow diverters, bioresorbable scaffolds — none overlapping the current five |
| **D4** | **TAVI I into the corpus for the risk rows** | ~2h | recovered by the `x_tolerance` fix; states model risk, both inputs, and CoU |
| **1** | Restate Group A with K4/RRF | ~1h | v3's headline names the losing router |
| **2** | `wasDerivedFrom` fix | ~1h | a bug currently scored as satisfied |
| **3** | **K8** risk extract-and-validate | ~4h | best-evidenced candidate; D4 adds a fourth document to it |
| **4** | **K9** validation results | ~4h | most tractable unfilled row, present in all 5 |
| **5** | **K3c** entity role by embedding | ~4h | reuses the loaded encoder |
| **6** | **K7** CoU section | ~3h | V&V 40 only; D4 adds a fourth document |
| **7** | K5 re-run, presence-first | ~2h | may correctly report "absent" |

D1–D4 come first and cost ~13h against the candidates' ~19h. Everything is free
of API spend; the binding cost throughout is annotation.

## Kill criteria

Every criterion in the first draft of this plan was satisfiable without meaning
anything, and both that were actually run proved it:

* **K8** passed all four while capturing `"high"` from *"if the pump causes high
  levels of hemolysis"* — the hazard, not the assigned value — and `"3"` from the
  citation `[3,4]`. The criteria checked the SHAPE of the output and never that
  the spans were risk statements.
* **K9** passed "beat `control_first_comparison` at k=5" on **4 hits against 2
  out of 24**, p = 0.135, tied at k=10 and worse at k=1. The criterion never
  said *by how much*, so it stays satisfied at every sample size.

Writing a criterion in advance is necessary and **not sufficient**. It also has
to be powered for the sample it runs on, and it has to test the content of the
result rather than its shape.

### What is detectable at these sample sizes

One-sided binomial, α = 0.05. Minimum candidate hits needed to separate it from
a control with the given rate:

| n | vs p₀=0.10 | vs p₀=0.25 | vs p₀=0.50 |
|---|---|---|---|
| 4 | 3/4 (75%) | 4/4 (100%) | **impossible** |
| 5 | 3/5 (60%) | 4/5 (80%) | 5/5 (100%) |
| 12 | 4/12 (33%) | 7/12 (58%) | 10/12 (83%) |
| 24 | 6/24 (25%) | 11/24 (46%) | 17/24 (71%) |
| 55 | 10/55 (18%) | 20/55 (36%) | 35/55 (64%) |

At n=4 against a coin-flip control, **no result is distinguishable at all**.

### The remaining candidates, powered

| candidate | n available | needs, vs a 0.25 control | verdict |
|---|---|---|---|
| **K3c** `bindsModel/Dataset/Requirement` | 15 (5 docs × 3 entity types) | 8/15 = 53% | runnable, but only a large effect is visible |
| **K7** `hasContextOfUse` | **4** (V&V 40 documents only) | **4/4 = 100%** | **underpowered — do not run as a test** |
| **K5** `hasDecisionRecord` | **5** (one decision per document) | 4/5 = 80% | **underpowered — do not run as a test** |

**K7 and K5 cannot be evaluated at current n.** A criterion they could pass would
require perfection, and one they could fail would be a coin flip. Running them
produces a number that means nothing in either direction, which is how the last
two candidates consumed a day.

### The rule, for every future criterion

1. **State n before running.** If the minimum detectable effect at that n exceeds
   what the candidate could plausibly achieve, the candidate is **not evaluated**
   — not passed, not failed.
2. **State the margin, not just the direction.** "Beat the control" is not a
   criterion; "beat it by the margin significant at this n" is.
3. **Test content, not shape.** At least one condition must check that a
   returned span is the thing it claims to be. K8's spans were verbatim and
   wrong.
4. **Report the p-value beside the rate.** Both failures above are visible in one
   line of arithmetic that neither criterion asked for.

### Rewritten criteria

* **K3c** — beat `control_constant_entity` on count MAE across all 15
  measurements, with the sign of the difference consistent on at least 4 of the
  5 documents. Per-document consistency substitutes for the power that n=15
  cannot supply, and it is what would have caught K4's document-dependent
  reversal early.
* **K7** — **not evaluated.** Report presence and absence only: does the
  candidate return a value on the 4 V&V 40 documents and `null` on both 7009A
  documents. That is a correctness check, not a comparison, and it is the one
  thing n=4 can support. Any non-null value on a 7009A document is fabrication
  and fails outright, independent of n.
* **K5** — **not evaluated.** Same treatment: report presence, and report that
  the outcome is absent from the source in the documents where it is absent.
  K5's synthetic verdict (0.061, abstaining on 44 of 49) was already driven by
  absence rather than by extraction failure.

## What this plan will not fix

Five documents, 39 annotated pairs of 51 possible, one annotator. Nagaraja and
Bologna carry 57% of the sample.

### The corpus is not exhausted — that claim was wrong

An earlier version of this plan declared the corpus exhausted after two
searches. It is not:

* **The Frontiers collection** *Verification and Validation of In Silico Models
  for Biomedical Implantable Devices* — 7 articles covering stent deployment,
  stent-graft deployment in endovascular repair, flow diverters and bioresorbable
  scaffolds. None overlaps the current five. Whether they publish per-factor
  credibility tables is unchecked, and checking is D3.
* **TAVI I**, discarded for an extraction fault that turned out to be one
  pdfplumber parameter. It is still not a per-factor assessment — 3/13 factor
  names, and the paper says the applicability assessment was not carried out —
  but it states model risk, both of its inputs, and context of use, so it is a
  fourth document for K7 and K8. The original rejection conflated "unusable for
  factor routing" with "unusable".

The lesson is narrower than "search harder": **a document was discarded for a
tooling default that was already on the known-pathologies list.** A known
pathology is a bug with an untried fix, not a property of the document.

**Adding candidates cannot substitute for adding documents** — which is why
D1–D4 now precede every candidate in the sequence above. If the rows fill and
the sample stays at five, the deliverable says so in its own header.
