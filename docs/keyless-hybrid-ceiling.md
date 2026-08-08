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
| `hasValidationResult` | always (5–15 mentions) | K9 shape routing | **not demonstrated at n=79** — 12 vs 9, p=0.185 | unknown |
| `bindsModel` | always | K3c by NAME | **0.42 / 0.41**, against a naive 0.37 / 0.36 — thin but consistent | probably |
| `bindsDataset` | always | K3c by NAME | **0.09 / 0.16** vs 0.02 / 0.00 — weak, real | unknown |
| `bindsRequirement` | always | K3c by NAME | **0.026, below a naive 0.039** — does not work | unknown |
| `hasContextOfUse` | **V&V 40 only** (0/1 vs 39/33/50) | **K7 definitional** | retrieval **9/20 train, tied with its control**; restraint on 7009A **9/10, 4/4** | **no** |
| `hasDecisionRecord` | thin everywhere (0–8) | K5 section extraction | **fails** — 0.033 against a 0.833 control | unknown |

**Two rows are solved, one is a bug fix, four are measured negatives, and two are
thin passes.** No row is now "not evaluable" for want of sample size — a 40-paper
seeded corpus closed that. What it did *not* do is turn many negatives positive:
of the four rows it unblocked, three came back negative and the fourth split.

**Every seeded figure here was re-run on 2026-08-08 against the current corpus.**
K5 and K3c reproduced exactly. K7 and K9 did not: both had been measured on a
train split regenerated three times afterwards. K9's verdict survived renumbering
and K7's did not — its margin over its control disappeared entirely. A number
measured on a corpus that has since been regenerated is not a result, and nothing
in the tooling said so at the time.

### What the corpus changed

| row | at 5 real documents | at 40 seeded |
|---|---|---|
| `hasContextOfUse` | not evaluable, n=4 | **split** — retrieval ties its control, restraint works |
| `bindsModel` | evaluable, unknown | **thin pass** — 0.42 vs a naive 0.37 |
| `hasValidationResult` | not demonstrated, n=24, p=0.135 | **not demonstrated**, n=79, p=0.185 |
| `hasDecisionRecord` | not evaluable, n=5 | **fails**, 0.033 vs 0.833 |

Three of the four remain negative and the fourth is split. That is the point: **a
negative you can rely on is a result, and a negative you cannot is an open
question wearing its clothes.** K9's verdict did not change and its standing did
— at three times the sample the effect still fails to separate from the control,
so the row is closed rather than pending.

`hasContextOfUse` is the one to read carefully, because it is two capabilities
sharing a row. **Finding** a context of use ties a control that merely names the
term. **Declining** to state one on a NASA-STD-7009A document, which defines no
such concept, works on 9 of 10 and 4 of 4. The second is the rarer skill and the
one a fabricating extractor cannot fake, and it would have been buried by a
single averaged number.

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

## Can a keyless pipeline BE the extractor? Two of the three blockers fell

`dev/tools/scripts/keyless_extract.py` composes every candidate into one
extractor and runs the whole table at once. The result settles a question the
per-candidate scripts could not.

**The shape is an `sh:or` over three profiles**, not one flat requirement:

| profile | required properties |
|---|---|
| `ProfileMinimal` | 7 |
| `ProfileComplete` | 13 |
| `ProfileDisposition` | 14 |

So a sparse package does not fail for want of one field. It fails to reach **any**
profile, and `uofa shacl` says exactly that: *conformsToProfile must be
ProfileMinimal, ProfileComplete, or ProfileDisposition*, then *required fields for
the declared profile are missing*.

### The "no keyless route" verdicts were about three matchers, not three properties

`bindsRequirement`, `hasDecisionRecord` and `hasValidationResult` were each
written off on the strength of **one hand-written pattern matcher**: K3c's
regexes, K5's section scan, K9's shape heuristic. Meanwhile the strongest keyless
method in this project — a trained classifier, which is all K6 ever was — had been
applied to exactly **one property of nine**.

`dev/tools/scripts/keyless_trained.py` applies it to the other three. TF-IDF over
word and character n-grams into logistic regression: `sklearn` and the standard
library, no embeddings, no network, no model call. Trained on the 30-paper train
split, evaluated on the 10-paper holdout, split at the bundle level.

| property | pattern matcher | **trained** | its control |
|---|---|---|---|
| `hasValidationResult` | K9 0.152 | **0.438** recall@5 | 0.125 |
| `hasDecisionRecord`, outcome | K5 0.033 | **0.917** balanced, 0.833 reject recall | 0.500, 0.000 |
| `hasDecisionRecord`, locating it | — | **0.400** top-1, **0.700** top-3 | 0.000 |
| `bindsRequirement` | K3c 0.026 | 0.032 | **0.065 — the control wins** |

**Two of the three now have a keyless route that beats its control**, and the
decision record beats it on the measure that matters: **5 of 6 rejections caught,
against a constant that catches none.**

### The two stages that improved, and the diagnostic that found them

Neither improvement came from tuning a ranker. Both came from measuring what the
stage upstream could reach at all — the eighth time in this project that the
defect was one step above the symptom.

* **The decision locator was denied the feature it needed.** The gold sentence
  sits at median 0.79 through the document and 20 of 34 are in the back half, and
  a bag of n-grams has no way to represent position. Four positional features took
  it from 0.222 to **0.400**. Separately, six papers had no label at all: their
  best-matching sentence scored 0.42–0.53 against a 0.60 gate, so the *label* was
  strict, not the documents unlabelled. At 0.40 all forty papers label, which is
  six more papers of training and of evaluation, and the outcome classifier went
  0.800 → **0.917** balanced on the larger sample.

* **The requirement generator was looking for the wrong syntactic category.** Its
  ceiling was **0.140** — 86% of gold names were never proposed, so no ranker
  could have recovered them. The misses said why: `a recirculation CSE fraction
  below 5%`, `within the predefined 10% tolerance`, `peak resultant linear head
  acceleration`. A requirement here is a lowercase **acceptance criterion** — a
  quantity, a relation, a threshold — not a proper noun, and the generator was
  matching capital letters.

### Raising that ceiling made the result worse, which is the finding

Broadening the generator took the ceiling from 0.140 to **0.822**. End-to-end
recall went from 0.065 to **0.032**, and fell *below* its own control.

Candidates per paper went from ~400 to ~1,225, so picking six became a far harder
selection problem than the recall gain repaid. This is pattern #7 — fixing one
measure by breaking another — arriving in a new place: an upstream ceiling and
downstream precision are not independent, and a recall improvement that is not
paired with a selection improvement can be a net loss.

**`bindsRequirement` is not a naming problem and should stop being measured as
one.** 42% of its gold names do not appear verbatim in the document at all, so no
extractive method can exceed 0.579 by construction; the category was already the
only one that varied across repeated annotation draws. The gold is a set of
paraphrased acceptance criteria, and matching it by name asks a question the
documents do not answer.

### The metric was wrong too, and that mattered more than the method

K5 "failed" at 0.033 against a control scoring **0.833 by answering "Accepted"
every time**, because 34 of 40 papers accept. That control cannot be beaten on
accuracy and is useless in practice: it never identifies a single rejection,
which is the one outcome a reviewer needs the tool to catch. It is
`control_constant_list` scoring 1.000 all over again — a null model topping a
leaderboard because the measure rewards the majority answer.

Scored as balanced accuracy the constant is pinned at 0.500 by construction, and
the trained classifier reaches **0.800, catching 3 of 5 rejections against the
constant's 0**. The property was never unextractable; it was being measured with
a number that a constant function wins.

### The anchor: does it transfer to real papers?

`hasValidationResult` is the one of the three with real-paper gold, so it is the
only one that can be checked against the documents that decide disagreements.
Trained on all 40 seeded papers, tested on the five real ones:

| document | | gold | trained | control |
|---|---|---|---|---|
| opensim | seed | 5 | 3 | 0 |
| bologna | seed | 6 | 3 | 1 |
| nagaraja | seed | 6 | 1 | 0 |
| elemance | **clean** | 4 | 1 | 0 |
| morrison | **clean** | 3 | 1 | 0 |
| **all five** | | **24** | **9** | **1** |
| **clean only** | | **7** | **2** | **0** |

Three of the five *are* the generator's seeds, so their phrasing echoes through
the training data and the five-paper total is partly a training score. The clean
read is elemance and morrison, **n=2**: 2 of 7 against a control's 0 of 7. Thin,
in the right direction, and honestly labelled as two documents.

### One clean negative: the locator cannot be deleted

Accept/reject looks like a document-level property — abstract, conclusion and
discussion all carry it — so classifying it from the whole document should skip
the weak 0.222 locator entirely. It does not work: **0.850 accuracy, 0.500
balanced, 0.000 reject recall — identical to the constant to three decimals.**
Given 200+ sentences the classifier learns to say "Accepted" every time.

The decision signal is *localised*, and diluting it destroys it. So the two-stage
design is required, and `hasDecisionRecord` end to end is bounded by the 0.222
locator rather than by the 0.800 classifier.

### What is left in `ProfileMinimal`

| Minimal requires | keyless |
|---|---|
| `hasContextOfUse` | K7, retrieval tied with its control |
| `hasValidationResult` | **trained, 0.438** — transfers to real papers |
| `hasDecisionRecord` | **trained**, outcome 0.917 balanced; bounded by a 0.400 locator |
| `bindsRequirement` | **no route** — 0.032, below its own control, and mis-specified |
| `hash`, `signature`, `generatedAtTime` | signing, not extraction |

One property of the four is still without a route, and two of the remaining three
are too weak to ship unsupervised. That is a quality problem, which is the kind
that responds to work — not the structural wall an earlier draft of this section
claimed. **That claim was wrong, and it was wrong because it generalised from
three failed pattern matchers to the properties themselves.**

### Measured on the 40 seeded papers

Emitted values against gold, on the holdout and train splits. `filled` is
presence and `correct` is accuracy, and the gap between the two columns is the
entire argument of this document:

| property | filled (holdout / train) | correct (holdout / train) |
|---|---|---|
| `hasCredibilityFactor` | 10/10, 30/30 | **0.217 / 0.304** |
| `bindsModel` | 10/10, 30/30 | 0.400 / 0.467 |
| `bindsDataset` | 10/10, 30/30 | 0.500 / 0.267 |
| `hasContextOfUse` | 6/10, 19/30 | 0.500 / 0.200 |
| `modelRiskLevel` | 1/10, 2/30 | no gold |
| `bindsRequirement`, `hasValidationResult`, `hasDecisionRecord` | 0 | — |

`modelRiskLevel` fills 1 in 10 here and 5 of 6 on the real papers. That gap is
the **corpus**, not K8: all four real V&V 40 papers state model influence and
decision consequence, and only 9 of 26 seeded ones do. The seeded corpus does not
exercise K8, so K8's verdict stays where it was measured, at n=6 real.

### What this means for `extract`

A keyless default is not blocked on a wall, it is blocked on quality. Of the four
extractor-facing properties in `ProfileMinimal`, one has no route at all
(`bindsRequirement`) and two have routes too weak to run unsupervised. The usable
shape is a **hybrid with the split declared per property** — trained routes where
they are measured to work, a model where they are not, and `method` recorded on
every value so the division is auditable afterwards.

What would move it: `hasDecisionRecord` needs a locator better than 0.400 top-1 —
the outcome classifier behind it is at 0.917 balanced and is not the constraint,
and top-3 already reaches 0.700, so emitting three candidates rather than one is
available today. `bindsRequirement` needs its *task* redefined before any method
is chosen, because 42% of its gold is paraphrase and the remaining match problem
is a selection problem that a broader generator makes worse.

That is the opposite of the failure this repository already paid for, where 14
turbomachinery models labelled "Class II" validated and honest packages did not.
`minCount` rewards presence; only provenance distinguishes a value that was found
from one that was supplied.

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
