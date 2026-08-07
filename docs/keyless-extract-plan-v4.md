# Keyless extraction: plan v4 — fill every row

Supersedes v3's deliverable section. v3 left six of nine rows as `?`, `untested`
or `not attempted`. This proposes a keyless candidate for each and fixes the
measurement discipline v3's numbers lacked.

Measured on **37 factor-document pairs across 5 real journal-prose documents**:
two NASA-STD-7009A (opensim, elemance) and three ASME V&V 40 (bologna,
nagaraja, morrison). Two standards, five documents, one annotator.

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

Three of five fit. **The reversal is unexplained.** The honest statement is that
K4 leads on aggregate with one documented exception — not that K4 is better.
`K4 @ k=5` stands as the recommendation, weakly, and RRF is the better hedge if
one router must serve all documents (best at k=1 and k=20, never worst).

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
8. **Expect a new extraction pathology per document genre.** Four so far, each
   invisible on synthetic markdown and each found only by reading real output:
   column interleaving, line wrapping, lost inter-word spaces, and reproduced
   gradation rubrics surviving as standalone sentences. Budget for a fifth.

## Sequencing

| | work | cost | why here |
|---|---|---|---|
| **1** | Restate Group A with K4/RRF | ~1h | v3's headline names the losing router |
| **2** | `wasDerivedFrom` fix | ~1h | a bug currently scored as satisfied |
| **3** | **K8** risk extract-and-validate | ~4h | best-evidenced candidate; 3 documents supply both inputs, Morrison in prose for 2 COUs |
| **4** | **K9** validation results | ~4h | most tractable unfilled row, present in all 5 |
| **5** | **K3c** entity role by embedding | ~4h | reuses the loaded encoder; K3's own diagnosis points here |
| **6** | **K7** CoU section | ~3h | narrow: V&V 40 only |
| **7** | K5 re-run, presence-first | ~2h | may correctly report "absent" |

All free — no key, no generation spend. The binding cost is annotation.

K8 moved from 5th to 3rd: it was speculative in the first draft of this plan and
is now the best-supported candidate here.

## Kill criteria

Each dies unless it beats its null **on real journal prose**:

* **K8** — derived risk must match stated risk where both appear. Bologna's
  regulatory-impact substitution counts as a **pass** if reported as a
  documented deviation, and a **fail** if reported as a mismatch.
* **K9** — beat `control_constant_validation` (emit the first comparison
  sentence) on `name_keywords` recall.
* **K3c** — beat `control_constant_entity` on count MAE, K3's own criterion.
* **K7** — beat "first sentence of the document" on CoU match, and **report
  absent on both 7009A documents**. Returning a value there is a fail regardless
  of what it returns.
* **K5** — beat `control_constant_decision`, on documents that state a decision.

## What this plan will not fix

Five documents, 37 pairs, one annotator. Nagaraja contributes 10 and Bologna 11,
so two documents carry 57% of the sample.

The corpus is close to exhausted: NTRS yields no further journal prose, and of
the four known applied V&V 40 case studies, three are now in — the fourth pair
(TAVI I and II) is unusable through a ~10% inter-word space-loss extraction
fault and publishes no per-factor table anyway.

**Adding candidates cannot substitute for adding documents.** If the rows fill
and the sample stays at five, the deliverable says so in its own header.
