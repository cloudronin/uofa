# The hybrid ceiling

**What a keyless pipeline can fill, at what quality, and what still needs a
model.** One row per required property, never a fraction: "nine of thirteen
covered" is a useless sentence when the remaining four carry the substance.

**Measured on 5 real journal-prose documents** — 2 under NASA-STD-7009A
(opensim, elemance), 3 under ASME V&V 40 (bologna, nagaraja, morrison), plus
TAVI I for the risk rows only. 56 factor-document pairs, 24 annotated validation
results, **one annotator**. Synthetic figures appear only for contrast, never as
a result: the synthetic corpus was shown to invert the ranking between two
methods.

`ProfileComplete` requires nine properties of the extractor. Four more —
`hash`, `signature`, `generatedAtTime`, `wasAttributedTo` — come from signing and
import and are out of scope.

---

## The table

| Property | In the source? | Keyless route | Result | Needs a model? |
|---|---|---|---|---|
| `hasCredibilityFactor` | always | **RRF routing** (K4+K6) | **0.357 recall@5**, 0.607@20 | for selection |
| — per-factor `rationale` | always | RRF → K2 quote | groundedness 1.000 by construction | no |
| `modelRiskLevel` | **V&V 40 only** (0/0 vs 22/17/23) | **K8** extract-and-validate | **5 of 6 documents correct**, 1 named failure | **no** |
| `wasDerivedFrom` | n/a — a run fact | emit the input filenames | **fixed**; was 100% template placeholder | **no** |
| `hasValidationResult` | always (5–15 mentions) | K9 shape routing | **not demonstrated** — 4 vs 2 of 24, p=0.135 | unknown |
| `bindsModel` | always | K3c entity role | **evaluable** — counts stable over 5 draws | unknown |
| `bindsDataset` | always | K3c | **evaluable** — counts stable | unknown |
| `bindsRequirement` | always | K3c | not evaluable *by count* — unstable in real and synthetic alike | unknown |
| `hasContextOfUse` | **V&V 40 only** (0/1 vs 39/33/50) | K7 section extraction | **not evaluable** — n=4 needs 4/4 | unknown |
| `hasDecisionRecord` | thin everywhere (0–8) | K5 section extraction | **not evaluable** — n=5 needs 4/5 | unknown |

**Two rows are solved, one is a bug fix, one has a real result, one is measured
and negative, and four cannot be judged at five documents.** The blanks are the
finding, and each one now says what would fill it.

---

## The configuration that works

**RRF @ k=5**, then a model selects from the shortlist.

| stage | measured |
|---|---|
| router recall@5 | 0.357 |
| selector, given a shortlist containing the answer | **1.000** at k=5 |
| end to end | 0.417 |
| control: always take rank 1 | 0.000 |

The paid stage reads **5 sentences instead of 539–1326** — a 100–265× reduction
in what the model sees, with the selector no longer the constraint. Every
remaining loss is the router failing to reach the evidence.

**A longer shortlist makes it worse.** Selection falls 1.000 → 0.833 → 0.250 as
k grows 5 → 20 → 40, and at k=40 that more than cancels the best ceiling
(RRF@40 reaches 0.714 and delivers 0.167 end to end). The router's job is
precision at small k, not recall at large k — the opposite of what a recall@k
table implies read alone.

### Router choice

| k | K6 lexical | K4 embeddings | **RRF** |
|---|---|---|---|
| 1 | **0.179** | 0.143 | **0.179** |
| 5 | 0.321 | 0.321 | **0.357** |
| 20 | 0.518 | 0.464 | **0.607** |
| 40 | 0.607 | 0.571 | **0.714** |

RRF is best or tied at every k. K4 and K6 are exactly tied at k=5 — an earlier
claim that K4 beat K6 by 3.3× was an artefact of annotating only the pairs that
were easy to find.

---

## Detection is not a metric, permanently

`control_constant_list` — a function that prints the standard's checklist and
reads nothing — scores **0.960 on synthetic bundles and 1.000 on the real
corpus**. A published credibility assessment enumerates every factor and scores
absent evidence 0 rather than omitting the row; that is what the artefact *is*.

Any evaluation built on detection ranks a null model at the top. This is not a
corpus defect and cannot be fixed by a better corpus.

---

## Preconditions: five extraction faults, all invisible on markdown

A reader taking the table above to their own PDFs will hit these before reaching
any of it. Each was found only by reading real output, and each changed a
conclusion.

| fault | effect | fix |
|---|---|---|
| **Two-column raster order** | 12 of 13 evidence spans destroyed; token recall stayed ~1.00 | detect the gutter, read per column |
| **Line-wrap segmentation** | sentences delivered as fragments (989 → 539) | unwrap before segmenting |
| **Lost inter-word spaces** | ~10% of tokens merged; **two documents were discarded over it** | `x_tolerance=1.2` |
| **Hyphenation across breaks** | 0.7–14% of lines split a word | rejoin, using the document's own vocabulary to decide the hyphen |
| **Reproduced gradation rubrics** | the standard's level definitions survive as standalone sentences and outrank findings | drop definitions following a bare gradation letter |

Plus the **furniture filter**: 539 → 213 sentences, 9/9 gold retained. Scoped to
the routing path only — the CAS table is noise for rationale and gold for levels.

---

## What the deliverable cannot say, and why

### The corpus is the constraint, not the methods

Five documents. NTRS yields no further journal prose; the Frontiers collection on
in-silico implantable devices was screened and **0 of 7** publish a per-factor
table. Three of the four known applied V&V 40 case studies are in.

### Three rows are blocked for three different reasons

* **K7, K5 — underpowered.** At n=4 against a coin-flip control, no result is
  distinguishable. A criterion they could pass would demand perfection.
* **K3c — two of its three rows are fine; the third is not countable.** An
  earlier version of this deliverable said the gold could not be constructed,
  from a 2-draw test. At 5 draws, models and datasets are perfectly stable on
  both a real and a seeded-synthetic document, and only `requirements` varies —
  in *both*. Indefiniteness is a property of that category, not of real
  evidence. `bindsModel` and `bindsDataset` are evaluable on counts at n=10;
  `bindsRequirement` needs a named-entity measure.

### The annotation is one reader's, cross-checked once

Inter-annotator agreement, after two fixes: **71.4% same-sentence, 76.1% token
overlap, 92.0% factor selection.** Substantial, not decisive. The check itself
found two defects — a table-bias in the annotation and a withheld-scope bug in
the protocol — and gpt-5 is not a human SME.

Coverage is **42 of 51** factor pairs. Of 12 originally excluded as "no evidence
found", an independent annotator located evidence for 10 — so the exclusions were
the annotator's limit, not the documents'.

### Scope is required at every stage

The unit of assessment is **(model × mechanism × factor)**, and omitting it
produces a confident wrong answer rather than a visible failure. This appeared
four times: selection improved 3/6 → 5/6 once the model was named; the agreement
check manufactured a 1/6 disagreement by withholding it; K8 still fails on
Morrison's two contexts of use.

---

## What would fill the blanks

In order of value per hour:

1. **Re-specify K3c** as named-entity overlap rather than counts. Unblocks three
   rows and needs no new documents.
2. **Relax the sourcing criterion.** Four documents state model risk without a
   per-factor table — enough to make K7 and K8 evaluable, not enough for routing.
3. **A human annotation pass.** 71.4% agreement with a model bounds
   reader-dependence; it does not establish correctness.
4. **More journal-prose documents.** The binding constraint on everything above,
   and the one with no cheap answer.

## The through-line

Six times in this work a number turned out to be measuring the tooling rather
than the method: the template inflated F1 by 0.067; the PDF reader destroyed 92%
of sentences; two documents were discarded over a parameter default; the
annotation was drawn from a summary table; the exclusions were an annotator
limit; and both kill criteria were satisfiable without meaning anything.

Every one was invisible on synthetic markdown. **The synthetic corpus does not
merely flatter absolute scores — it inverted the ranking between two methods**,
which no amount of synthetic evaluation could have detected.
