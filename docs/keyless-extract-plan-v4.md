# Keyless extraction: plan v4 — fill every row

Supersedes v3's deliverable section. v3 left six of nine rows as `?`, `untested`
or `not attempted`. This plan proposes a keyless candidate for each, and fixes
the measurement discipline that v3's numbers turned out to lack.

## What changed since v3

Four things, each of which invalidates something v3 asserted.

1. **Synthetic evaluation inverts method rankings.** K6 scores 0.829 recall@5 on
   held-out synthetic bundles and 0.13 on real journal prose; K4 scores 0.505 and
   0.43. The corpus does not merely flatter absolute numbers — it picks the wrong
   method. v3's headline `K6 → K2, attribution 0.615` names the loser.
2. **Detection is worse than v3 thought.** `control_constant_list` scores 0.960
   synthetic and **1.000** on the real corpus.
3. **The router/selector split is measured.** Selection accuracy falls
   1.000 → 0.833 → 0.250 as the shortlist grows 5 → 20 → 40. The router's job is
   precision at small k, not recall at large k.
4. **Some required properties are not in the source at all**, and which ones
   depends on the standard the document follows. This is the finding that
   reshapes the deliverable.

### The presence problem, measured

Keyword-presence probes across the three real journal-prose documents:

| property | opensim (7009A) | elemance (7009A) | bologna (V&V 40) |
|---|---|---|---|
| `hasContextOfUse` | **0** | **1** | 39 |
| `modelRiskLevel` | **0** | **0** | 22 |
| `hasDecisionRecord` | 0 | 3 | 7 |
| `hasValidationResult` | 5 | 15 | 10 |
| `bindsDataset` | 13 | 29 | 12 |
| `bindsRequirement` | 7 | 34 | 4 |

Crude probes, so read them as presence/absence and not as extraction targets.
The signal is unambiguous at the zeros: **NASA-STD-7009A does not ask for a
risk-based context of use, so 7009A documents do not contain one.** V&V 40 is
explicitly risk-based and Bologna states both, in detail.

So a row can fail for two different reasons, and the deliverable must
distinguish them:

* **extractable but unextracted** — the evidence is on the page and no keyless
  method finds it. A candidate can fix this.
* **absent from the source** — the document never states it. *No* extractor
  fixes this, keyless or not. The LLM's 100% population of `hasDecisionRecord`
  is this case: 77% of those values were invented.

**A row whose property is absent must be reported as absent, not as a low
score.** Scoring it rewards fabrication, which is the failure mode this whole
line of work exists to detect.

## The nine rows, with a candidate each

Grouped by what kind of problem each actually is.

### Group A — already solved, needs restating with the right router

| row | candidate | measured |
|---|---|---|
| `hasCredibilityFactor` | **K4 routing**, not detection | detection unmeasurable (constant 1.000); routing 0.43 recall@5 real prose |
| per-factor `rationale` | **K4 → K2** (route, then quote) | groundedness 1.000 by construction; attribution via routing |

No new work beyond swapping K6 for K4 and re-reporting. v3's numbers are
synthetic and name the wrong router.

### Group B — announced properties, findable by section + routing

These are *stated* rather than argued, in a small closed vocabulary, usually
under a heading. K5 established that pattern extraction works when the target
is present.

| row | candidate | first question |
|---|---|---|
| `hasContextOfUse` | **K7: CoU section extraction.** V&V 40 documents have a QoI/CoU section by construction; route with K4 to "intended use / context of use" and quote. | present in V&V 40, absent in 7009A |
| `hasDecisionRecord` | **K5, re-run on real documents.** Its synthetic verdict (0.061, abstains on 44 of 49) was driven by the outcome being absent from 38 of 49 sources. | measure presence before accuracy |
| `modelRiskLevel` | **K8: extract-and-validate, not extract.** Find the stated risk level *and* its two inputs, then check the stated level against the standard's own influence × consequence table. Disagreement is a finding, not an error. | present in V&V 40, absent in 7009A |

K8 is the interesting one. V&V 40 defines model risk as a *function* of two
inputs, so the derivation is a lookup table — pure code once both inputs are
found. That makes the keyless route "find two words and index a table", and it
gives a free consistency check no LLM currently performs.

Bologna is the test case: it states decision consequence LOW and substitutes
*regulatory impact* HIGH for model influence, arguing for the substitution. A
validator must report that as a documented deviation, not as a mismatch.

### Group C — quantitative claims, findable by shape

| row | candidate |
|---|---|
| `hasValidationResult` | **K9: comparison-sentence routing.** A validation result is a comparison verb + a quantity + a referent — "compared to PMHS data, error within 10%". Route on that *shape* rather than on factor vocabulary. |

Never attempted in v3. It is the most tractable unfilled row: the target has a
distinctive syntactic signature, it is present in all three real documents
(5/15/10), and `expected_validation_results` already exists in the corpus schema
with a `name_keywords` + `has_uq` + `pass_fail` match rule.

### Group D — role disambiguation, where K3 failed

| row | candidate |
|---|---|
| `bindsModel`, `bindsDataset`, `bindsRequirement` | **K3c: embedding role classification.** |

K3 failed at ~5 models per bundle against a ground truth of ~1.8, and its own
diagnosis was that the error is *role*, not type: a document names the model
under assessment, the solver it runs on, models compared against, and models
cited from the literature, and all four look identical to a pattern and to
off-the-shelf NER.

K4's result suggests the fix. Embeddings beat lexical matching precisely where
the abstraction gap is widest, and "is this the model being assessed, or one
cited from the literature?" is a role question an embedding can be asked
directly: score each candidate against *"the computational model under
assessment in this study"* versus *"a model referenced from prior work"*, and
take the margin.

This is K4's trick applied to entity role rather than factor identity, and it
costs nothing new — the encoder is already loaded.

### Group E — not an extraction problem

| row | candidate |
|---|---|
| `wasDerivedFrom` | **Emit the input filenames and their hashes.** |

Measured: 27 of 27 corpus packages satisfy `wasDerivedFrom` with the template's
own help text, which JSON-LD coerces to a `file://` URI and which therefore
satisfies `sh:nodeKind sh:IRI`. The requirement is met by the instructions for
meeting it.

The pipeline already knows which files it read. This is a bug with a one-line
fix, not a research candidate, and it should not be counted as a keyless win.

## Measurement discipline

Everything below was learned the expensive way this session and is not
negotiable for a v4 number to mean anything.

1. **Score on real journal prose.** Synthetic numbers may be reported for
   contrast, never as the result. The corpus inverts rankings.
2. **Every candidate needs a null model, measured on real documents.** The
   constant scores 1.000 on the real corpus — a null that looks weak on
   synthetic data can be unbeatable on real data.
3. **Measure presence before accuracy.** For every row, first report what
   fraction of documents state the property at all. A row that is absent is
   reported as absent.
4. **Report routing recall@k and selection accuracy together.** Optimising
   either alone picks the wrong configuration: the best ceiling (RRF@40, 0.667)
   produced the worst pipeline (0.167 end to end).
5. **Keep shortlists short.** k=5 is the default; anything larger needs the
   selection cost measured, not assumed.
6. **The furniture filter applies to the routing path only.** The CAS table is
   noise for rationale and gold for levels.
7. **`evidence_keywords` may never seed a matcher.** Unchanged from v2.

## Sequencing

Cheapest and most decisive first.

| | work | cost | why first |
|---|---|---|---|
| **1** | Restate Group A with K4 | ~1h, free | v3's headline names the losing router |
| **2** | `wasDerivedFrom` fix | ~1h, free | a bug currently counted as satisfied |
| **3** | **K9** validation results | ~4h, free | most tractable unfilled row, target present in all 3 documents |
| **4** | **K8** risk extract-and-validate | ~4h, free | turns a "needs judgment" row into a lookup |
| **5** | **K3c** entity role by embedding | ~4h, free | reuses the loaded encoder; K3's own diagnosis points here |
| **6** | **K7** CoU section | ~3h, free | narrow: V&V 40 documents only |
| **7** | K5 re-run on real documents | ~2h, free | presence-first, may report "absent" |

All free — no key, no generation spend. The binding cost is annotation, not
compute.

## Kill criteria

Each candidate dies unless it beats its null **on real journal prose**:

* **K9** — beat `control_constant_validation` (emit the first comparison
  sentence) on `name_keywords` recall.
* **K8** — the derived risk must match the stated risk on documents that state
  both. One disagreement that turns out to be a real documented deviation
  (Bologna's regulatory-impact substitution) counts as a pass, not a failure.
* **K3c** — beat `control_constant_entity` on count MAE, the criterion K3 was
  already held to.
* **K7** — beat "first sentence of the document" on CoU match.
* **K5** — beat `control_constant_decision`, on documents that state a decision.

## What this plan will not fix

Journal prose is **three documents, 23 factor-document pairs**, and Bologna
contributes 11 of them. Every number below will carry that. NTRS is exhausted;
the V&V 40 pool has roughly four known applied case studies, two of which are
unusable through a space-loss extraction fault.

More candidates cannot substitute for more documents. If the rows fill and the
sample stays at three, the deliverable says so in its own header.
