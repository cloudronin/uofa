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
| `hasValidationResult` | always (5–15 mentions) | K9 shape routing | **not demonstrated at n=100** — 18 vs 13, p=0.094 | unknown |
| `bindsModel` | always | K3c by NAME | **0.42 / 0.41**, against a naive 0.37 / 0.36 — thin but consistent | probably |
| `bindsDataset` | always | K3c by NAME | **0.09 / 0.16** vs 0.02 / 0.00 — weak, real | unknown |
| `bindsRequirement` | always | K3c by NAME | **0.026, below a naive 0.039** — does not work | unknown |
| `hasContextOfUse` | **V&V 40 only** (0/1 vs 39/33/50) | **K7 definitional** | **15/20 train, 3/4 clean holdout** vs control 11/20, 1/4 | **no** |
| `hasDecisionRecord` | thin everywhere (0–8) | K5 section extraction | **fails** — 0.033 against a 0.833 control | unknown |

**Four rows are solved, one is a bug fix, two are measured negatives, and two are
blocked on gold rather than on documents.** No row is now "not evaluable" for want
of sample size — a 40-paper seeded corpus closed that, and closing it turned three
verdicts from *cannot tell* into *can tell*.

### What the corpus changed

| row | at 5 real documents | at 40 seeded |
|---|---|---|
| `hasContextOfUse` | not evaluable, n=4 | **works** — and K7 did not exist before |
| `bindsModel` | evaluable, unknown | **thin pass** — 0.42 vs a naive 0.37 |
| `hasValidationResult` | not demonstrated, n=24, p=0.135 | **not demonstrated**, n=100, p=0.094 |
| `hasDecisionRecord` | not evaluable, n=5 | **fails**, 0.033 vs 0.833 |

Three of the four remain negative. That is the point: **a negative you can rely
on is a result, and a negative you cannot is an open question wearing its
clothes.** K9's verdict did not change and its standing did — at four times the
sample the effect still fails to separate from the control, so the row is closed
rather than pending.

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

## Seeded generation: three objections, all tested, none supported

The synthetic corpus inverted the ranking between two methods, so a proposal to
generate more of it — seeded on the five real papers — met three objections from
me. Each was tested rather than argued.

**1. "Seeded output will still look like markdown, not like real papers."** Wrong.

| | words | sent-like | kept% | factors named | >20ch |
|---|---|---|---|---|---|
| bologna (real) | 10,998 | 46% | 35% | 11/13 | 0.05% |
| **seeded synth** | 4,457 | **47%** | 39% | **8/13** | 0.07% |
| old synth | 3,162 | 25% | 37% | 0/13 | 0.00% |

Indistinguishable from the real document on surface profile; nothing like the
corpus that caused the problem.

**2. "Entity counts will be definite by construction, as they are not in real
documents."** Wrong, and it overturned a verdict in this deliverable. At five
draws, models and datasets are perfectly stable on *both* a real and a seeded
document; only `requirements` varies, and it varies in both. The earlier claim
came from a two-draw test.

**3. "Gold written in the same pass as the document will be circular."** Not
supported. Generating a paper and its ground truth together, then having a
different model family annotate the document alone:

| | factor selection | same sentence |
|---|---|---|
| synthetic, gold written in the same pass | 100.0% | **10/13 = 76.9%** |
| real, gold written by a reader afterwards | 92.0% | **30/42 = 71.4%** |

**Fisher exact p = 1.000.** Gold written by the generator is not measurably more
reproducible than gold written by a reader. If the document were being written to
make its own gold findable, agreement would approach 100%.

### The one real difference

**Factor selection: 100% against 92%.** The synthetic paper reports a clean
finding for all thirteen factors; real papers are ambiguous about which factors
they address at all, and that ambiguity is where 8 of the 51 real pairs sit. That
is *completeness*, not circularity — synthetic papers are tidier than real ones,
which flatters coverage while leaving the harder judgement untested.

So seeded generation is a sound way to scale the corpus, with one caveat that
should be designed around rather than discovered later: **generate papers that
omit factors, report some ambiguously, and assess several models across several
mechanisms** — because those are the properties the old corpus lacked, and the
seeded output reproduces the prose but not yet the mess.

## What would fill the blanks

In order of value per hour:

1. ~~**Re-specify K3c** as named-entity overlap rather than counts.~~ **Done.
   Names beat counts, and the margin is much smaller than it first appeared.**

   The first measurement reported 0.657 / 0.818 and was wrong twice over: the
   matcher let a fragment match a long name — the bare word "balance" counted as
   naming a 20-word requirement — and the control was a constant that names
   nothing, so any non-zero recall beat it.

   Against the document's most frequent capitalised phrases, which is a control
   that actually competes:

   | property | K3c | naive | |
   |---|---|---|---|
   | `bindsModel` | 0.42 / 0.41 | 0.37 / 0.36 | thin, consistent in direction |
   | `bindsDataset` | 0.09 / 0.16 | 0.02 / 0.00 | weak but real |
   | `bindsRequirement` | 0.026 | 0.039 | **loses to the naive control** |

   Names are still the right measure — counts score 0.133 where names score 0.42
   — but "unblocks three rows" was optimistic. One row is a thin pass, one is
   weak, and one does not work.
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
