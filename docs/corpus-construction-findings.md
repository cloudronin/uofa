# Corpus construction: findings

Running record for building the seeded evaluation corpus. Companion to
[`keyless-extract-findings.md`](keyless-extract-findings.md), which records the
candidate evaluations this corpus exists to serve, and to
[`seeded-corpus-spec.md`](seeded-corpus-spec.md), which holds the requirements.

**The split:** the spec says what the corpus must be. This says what was learned
building it, including the things that were wrong on the way. Append here as new
results land; do not rewrite history, add a dated entry.

---

## The recurring patterns

These transfer beyond this corpus, and each was found more than once. They are
first because they are the most reusable thing in the document.

### 1. A threshold taken from one population, applied to another — six times

Every one rejected or accepted the wrong thing, and every one was fixed by
measuring the population it would actually be applied to.

| threshold | set to | reality | what it did |
|---|---|---|---|
| diversity floor | mean >0.60 / max >0.85 | real 0.141 / 0.261 | would have passed a corpus 4× more homogeneous than real |
| hyphenation floor (per paper) | 0.040 | real spans 0.007–0.083 | rejected opensim **and** elemance |
| two-column floor (per paper) | 0.80 | real spans 0.089–1.000 | rejected the same two |
| hyphenation ceiling | *absent* | real max 0.083 | passed a paper at 0.319 |
| gradation validator | `[0-5]` | R6 *requires* private scales | rejected a paper's 0–12 index three times |
| selection agreement ceiling | 0.95 | real 0.961 | **rejected its own reference** |

**The rule:** a band must be re-derived whenever the measurement behind it
changes, and the first test of any band is whether it accepts its own reference.

A second rule fell out of the same pattern: *per-paper* checks and *corpus-level*
checks answer different questions. Per paper: did this pathology occur at all —
so the floor must sit below every real value. Corpus level: is the rate the real
rate — that is where a two-sided band belongs.

### 2. The defect is often one step upstream of the symptom — four times

| symptom | what it looked like | actual cause |
|---|---|---|
| 91% of gold levels "not stated" | gold's prompt | the write prompt never specified the table |
| the table was device parameters | the write prompt just fixed | a trailing comma truncating the real table away |
| table coverage 0.15, 0.05, 0.39 | the writer under-delivering | a validator discarding valid rows |
| selection agreement 0.631 | the corpus being ambiguous | gold and annotator asked different questions |

Each number was real. Each attribution was wrong. Twice the symptom pointed
directly at a component that had just been corrected.

### 3. Explaining a number before checking what produced it — twice, both flattering

Same-sentence agreement came in at 0.508 against a 0.708 baseline. Two
explanations were offered before either was tested, and both were wrong in the
direction that excused the corpus:

* *"the band does not transfer because our papers have more scopes"* — **refuted**:
  elemance has 8 scopes and the *highest* agreement of the five real papers
  (6/6), while single-scope bologna has the lowest (7/12).
* the actual cause was granularity — per-scope comparison reported against a
  document-level band. Measured the baseline's way: **0.773**, in band.

Running D1 against the real papers cost about **$0.15** and settled it.

### 4. A check that can be satisfied without checking anything — three times

* K8's and K9's kill criteria, satisfiable at any sample size (recorded in the
  companion doc).
* `na_rate` scored **0.000 and passed** while 91% of levels said `"not stated"` —
  a string the `_NA` set happened not to list. The check was satisfied by the
  *wording* of its own failure.

### 5. A fix added in one place and not the other — three times

* `--save-raw` wrote *after* parsing, so the one response worth inspecting was
  the only one not kept. Fixed in the generator; the agreement script then cost
  another $0.46 run for the same reason.
* `parse_or_salvage` repaired the write step's JSON for hours while the plan step
  still used the raw parser, and a paper died on it.
* The agreement script parsed the annotator's JSON with the raw parser, so **one
  trailing comma in thirty responses refused the entire verdict** — and that
  response recovered 13 factors once repaired.

Each repair was written once and needed twice. Grep for the other call site.

### 6. Two of my own requirements contradicting each other — twice

* `_GRADATION` was bounded to `[0-5]` and therefore **rejected the private
  numeric scale R6 requires**. A paper was regenerated three times while its
  writer had produced the full grid correctly every time.
* Counting ambiguous findings as N/A made **R8** (every assessed factor scored)
  contradict **R5** (10–20% reported ambiguously, which by definition have no
  gradation). The corpus was being penalised for having the property R5 asks
  for.

Both were resolved by asking which requirement governs the specific thing being
measured — not by loosening a threshold until the conflict stopped showing.

### 7. Fixing one measure by breaking another

Dropping findings whose factor the summary table never scores took `na_rate` to
0 and drove selection agreement **0.891 → 0.765** (AC1 0.876 → 0.702), with
annotator-only rising 6 → 18. Sixteen of those eighteen were exactly the dropped
findings.

The drop removed gold entries using table knowledge the independent annotator
does not have — the same asymmetry corrected an hour earlier for out-of-scope
findings, recreated immediately. And the entries were not even wrong: **two
readers found evidence for those factors in the prose**, so the paper assesses
them and its *table* is incomplete.

The lesson is narrow and useful: when a filter improves one measure, check the
measure that filter's information could distort.

---

## What the gates actually catch

Validated in both directions, which is the only way a gate earns trust:

| input | verdict | why it matters |
|---|---|---|
| five real papers | **passes** | the reference |
| old synthetic corpus (87 papers) | **rejected**, 5 rows | this is the corpus that inverted the K6/K4 ranking |
| five papers off one template | **rejected**, diversity 0.898 vs real 0.141 | my own demo, caught by my own gate |
| three opensim attempts | **rejected** | table covering a twentieth of its assessment |
| one checkpoint paper | **rejected** | 17 rubric sentences against a floor of 20 |

---

## Measurement findings

### Diversity cannot be measured with one number

* **Full-text TF-IDF cosine reads length, not sameness.** Uncapped, it rated the
  known-bad corpus as *more varied* than five real papers, because the real ones
  are 8× longer and long documents share more terms. Capping every document to
  its first 1,500 words restores the true ordering: real 0.141, old synthetic
  0.202.
* **Two of three measures grow with corpus size on their own.** Subsampling one
  unchanged generator 200× at each n: mean pairwise is flat (0.137 → 0.138 from
  n=5 to n=87), max pairwise gains **59%**, mean nearest-neighbour **40%**. A
  ceiling calibrated at n=5 would have failed a 40-paper corpus that was exactly
  as diverse as the real one — and that failure would have read as generator
  collapse.
* **No average detects duplication.** Three exact twins hidden among thirty
  papers move mean pairwise 0.162 → 0.166. Mean nearest-neighbour is better but
  still dilutes. The gate is a **count** of papers with a neighbour ≥ 0.60, and
  it must be 0.

### Cohen's kappa is unusable in this domain

Measured on the five real papers, κ returns **0.000 for two papers with 92% raw
agreement**, because one rater marked 100% of the checklist. Full reasoning and
the AC1 replacement are in the
[spec addendum](seeded-corpus-spec.md#addendum-why-gwets-ac1-and-not-cohens-kappa).

The short version: **R8** means real assessments enumerate the whole checklist,
so prevalence is near 100% *by the nature of the artefact*. That is the same
property that makes `control_constant_list` score 1.000 and detection useless as
a metric. **Any corpus faithful to R8 will defeat kappa**, and one that did not
would be exhibiting the tidiness R5 exists to prevent.

### Agreement is two-sided, and the high side is the point

Above the band means the papers are too clean — every factor cleanly reported,
the hard judgement untested. The old synthetic corpus and the first seeded paper
both scored **1.000**. A one-sided gate would have called that the best result in
the run.

---

## Corpus construction findings

### What makes generated papers read as synthetic

Not prose quality. **Structure.**

* Real papers are **38–46% short fragments** (<6 words); the first generated ones
  were 19–27%. The source is author initials in the reference list — `Qasim, X.`,
  `[10] F.T.`, `S., Delp, D.` — because a segmenter splits on every period in a
  citation. The generated papers had no bibliography at all. Adding 34 references
  moved sentence-like from **0.652 to 0.465** against a real 0.46.
* **`microtype` was excluded on backwards reasoning.** It was left out to
  *preserve* hyphenation; the target is the *real* rate, not the maximum. Without
  it the rate floors at 10.2% even at `\hyphenpenalty=9999`, above the real
  maximum of 8.3%. Real journal papers use it.
* **The lost-inter-word-space pathology is free.** The plan expected to need a
  special font for one paper in ten; elsarticle's narrow two-column setting
  produces it unaided at **9.0%** against 10–11% on the two real APL PDFs. Every
  generated paper therefore regression-tests the `x_tolerance=1.2` fix.

### The model writes content; the renderer writes every backslash

An intermediate design — renderer preamble, model-authored body markup — does not
hold up. No regex separates a model's stray `}` from the renderer's own
`\begin{tabular}{p{0.3\linewidth}}`, and the version that tried failed to compile
on its own factor table. Escaping prose unconditionally is *correct* rather than
heuristic, because the caller guarantees there is no markup.

Two JSON slips each cost a whole paper and are now repaired rather than fatal:
invalid escapes (`\sep` in keywords — 66,000 chars discarded over two characters)
and trailing commas. The second was worse: salvage truncates at the last
parseable point, and the comma sat immediately before the credibility table, so
recovery returned a document whose only surviving table was device parameters.

### The answer key needs more care than the documents

* **Gold must be given the standard's checklist.** Without it one bundle came
  back with *"Credibility matrix"*, *"Credibility rating"* — **zero of ten** names
  in common with the standard.
* **Gold must be scoped per model.** One call enumerating every
  (model × mechanism × factor) returned 0 bytes twice and 4 findings of 80 once.
* **Spans must be sentence-bounded.** 83 spans crossed sentence boundaries and
  passed a verbatim check against the flattened document. They would have entered
  the key as targets **no sentence-level router can ever match**, and every miss
  charged to the router.
* **Gold must be multi-reference.** Same-sentence agreement of 0.509 turned out
  to be two *defensible* picks, not gold errors — papers state a finding once in
  the methods and again in the results. A single-span key marks a router wrong
  for finding a valid alternative, understating every routing result. 235
  reference spans over 161 findings; one bundle has 79% of findings with more
  than one.
* **Findings for factors the paper does not assess are wrong, not merely out of
  scope.** The plan forbids the factor and the authored table omits it, so the
  paper demonstrably makes no claim. Dropped and counted.
* **Levels come from the authored table, not from a model re-reading the PDF.**
  Not circular: gold still finds evidence by reading the compiled document; the
  level is recorded from where the paper states it.

---

## Process findings

* **Save raw responses *before* parsing.** The one response worth inspecting is
  the one that failed to parse, and it was the only one not kept — $0.22 of
  undiagnosable output. Every fix afterwards was validated against saved
  responses for free. *The same omission was then repeated in the agreement
  script, costing another $0.46 run.*
* **Resume from a compiled PDF.** A paper whose gold failed has already paid for
  a plan and a 9,000-word write. Resume runs cost $0.29 against $0.60.
* **Phasing works.** A timeout-shaped bug cost **$0.04** at pilot scale rather
  than $8 at full scale.
* **Cost fingerprinting locates a failure without logs.** ~$0.014/paper is about
  5,000 tokens, which is the plan call alone — so the write step was what timed
  out.
* **`| tail` masks pytest's exit code.** Two commits landed with a failing test
  because the pipeline returned `tail`'s status.

---

## Results

### Pilot — 3 papers, 2026-08-07

All eleven offline rows pass. Agreement measured at document level, the basis the
bands are anchored to:

| measure | seeded | real | band |
|---|---|---|---|
| factor selection (Jaccard) | 0.917 | 0.961 | 0.85–0.99 |
| same sentence | 0.773 | 0.708 | 0.60–0.85 |
| N/A rate | 0.000 | 0.000 | = 0 |

`na_rate` trajectory across the fixes: 0.910 → 0.687 → 0.326 → 0.114 → 0.059 →
**0.000**.

### Checkpoint — 9 papers, 2026-08-07

**No diversity collapse**, which is what the checkpoint exists to establish.
Three papers cannot show it; pairwise similarity is uninformative at n=3.

| | n=3 | n=9 | ceiling |
|---|---|---|---|
| diversity mean | 0.171 | **0.151** | 0.180 |
| diversity max | 0.188 | 0.224 | 0.340 (size-scaled) |
| diversity nn | 0.188 | 0.197 | 0.272 (size-scaled) |
| twins | 0 | **0** | 0 |

Headroom on the size-stable measure *improved*, 0.009 → 0.029. Distinct devices
per paper, not prose variation, is what does that.

Cost came in at **$0.356/paper** against a $0.43 projection, so 40 papers is
about **$14**.

---

### Agreement at n=8 — 2026-08-07

The pilot's agreement result was n=3 and rested on 24 factor comparisons. At n=8
it rests on 65, across papers seeded on all three sources and spanning eight
devices. Document level, the basis the bands are anchored to:

| measure | n=3 | **n=8** | real | band |
|---|---|---|---|---|
| factor selection (Jaccard) | 0.917 | **0.891** | 0.961 | 0.85–0.99 |
| factor selection (Gwet AC1) | — | **0.876** | 0.952 | 0.85–0.99 |
| same sentence | 0.773 | **0.786** | 0.708 | 0.60–0.85 |
| N/A rate | 0.000 | 0.032 → **0.000** | 0.000 | = 0 |

Selection sits **below** the ceiling on both statistics, which is the result the
gate exists to produce: the papers are not too clean. Same-sentence is *above*
the real corpus and inside its band.

The 2×2 the AC1 needs, document level over 8 bundles: both 57, gold-only 1,
annotator-only 6, neither 1.

**The N/A regression, and why it is one line of code.** Thirteen findings of 404
carried no gradation, all in the four papers added at the checkpoint. In every
case the paper's own summary table scores that factor in **no row at all** — gold
reported a finding for `Test samples` where the table has zero `Test samples`
rows.

Under R8 a paper scores every factor it assesses, so a factor absent from the
table is one the paper does not assess, and the finding is wrong. This is the
same authority already used for the out-of-scope drop: **the authored table
decides what the paper assesses, not the gold model's reading of incidental
prose.** Dropped and counted as `factor-not-scored`; 3.2% of findings, N/A rate
back to 0.

A per-scope figure is also printed now, as a diagnostic only: selection 0.799,
same-sentence 0.564. It is *not* gated, because the bands come from
document-level measurement and comparing across granularities is what produced
the 0.508 mistake recorded above.

### Holdout set — 10 papers, 2026-08-07

Ten papers, three seeds, two standards, ten distinct devices. Every bundle
stamped `split: holdout` **at generation time** — the plan called for ~30 train
and ~10 held out and nothing enforced it, and a split assigned after the fact can
be reassigned after a result.

420 findings, 583 reference spans (1.39 each). All eleven offline rows pass:
diversity mean **0.151** against a 0.180 ceiling, zero twins, `na_rate` 0.000.

`crosses-sentences` removed **225 spans** across the set — every one a target no
sentence-level router could have matched.

Agreement is being re-measured after the incomplete-table fix; the reading taken
before it (0.765 / 0.702 / 0.935) reflects the drop described in pattern 7 and is
**not** a corpus result.

**Zero ambiguous findings**, against R5's 10–20% target. Gold stopped marking
them once its prompt was aligned with the annotator's — it now omits rather than
marking ambiguous. R5's binding test is the agreement band rather than this
count, but a corpus with no ambiguous findings is one where the hard judgement
may be under-represented. Watching it.

### A resume-path asymmetry

Resume skips the write step, which is correct for a paper whose **gold** failed
and wrong for one whose **pathology check** failed — that verdict is about the
PDF itself. A paper rejected for 17 rubric sentences was resumed twice at $0.000,
re-measuring the same PDF and reaching the same verdict, because the fix that
would have helped lives in the write step. A `too clean` rejection needs the
paper rewritten, not its gold redone.

### Holdout validated — 10 papers, 2026-08-07

**Gated:**

| measure | holdout | real | band |
|---|---|---|---|
| gold precision | **0.986** | 0.980 | 0.95–1.00 |
| same sentence (single-reference) | **0.824** | 0.708 | 0.60–0.85 |
| N/A rate (clear findings) | **0.000** | 0.000 | = 0 |

Plus all eleven offline rows: diversity mean 0.156 against a 0.180 ceiling, zero
twins, 490 findings over 706 reference spans.

**Reported, not gated:** selection 0.840, AC1 0.810, gold recall 0.850,
same-sentence multi-reference 0.912.

### Why selection is reported and precision is gated

The 2×2 is `both 68, gold-only 1, annotator-only 12`. A single selection figure
averages two errors with **opposite consequences**:

* a **wrong** gold entry penalises a router that correctly finds other evidence
* a **missing** gold entry leaves that factor untested

Only the first mis-scores. Gold is deliberately precision-biased — its prompt
says returning a factor the paper does not assess is worse than omitting one it
does — so it under-selects against an unbiased reader **by design**, and the
aggregate reads 0.840 while hiding which side moved. Precision 0.986 is the
correctness property and is gated; recall 0.850 is coverage and is reported.

This is a decision to accept a known asymmetry, not a discovery that it does not
exist. The alternative — relaxing gold's omission bias — raises recall by
admitting wrong entries, which is the failure mode that actively mis-scores.

### Why same-sentence is gated on single-reference gold

The key is multi-reference, correctly: a router finding any valid sentence should
count. But that inflates agreement by construction — **0.912 multi against 0.824
single on identical data** — and the 0.708 baseline was measured single-reference.
Comparing them would repeat the granularity mistake recorded above.

Tested rather than asserted, which matters because two earlier explanations of
this same number were wrong and both flattered the corpus.

### Train set — 30 papers, 2026-08-07

30 bundles, **30 distinct devices**, 1,403 findings (1,337 clear, 66 ambiguous),
2,156 reference spans at 1.54 each. `na_rate` 0.000 over clear findings. No table
omits a factor its paper reports on. Every bundle stamped `split: train`.

**$10.72** — $8.64 for the first pass, $2.08 to regenerate six rejections.

All eleven offline rows pass, and diversity **improved with scale**:

| n | diversity mean | twins |
|---|---|---|
| 3 | 0.171 | 0 |
| 9 | 0.151 | 0 |
| 10 (holdout) | 0.156 | 0 |
| **30 (train)** | **0.136** | 0 |

At thirty papers the set is *more* diverse than the five real papers (0.141).
That settles the question the checkpoint existed to ask, in the opposite
direction to the risk: the concern was collapse, and distinct subject matter per
paper produced the reverse.

**Six of thirty were rejected on the first pass**, five of them by gates working
as designed — two too clean on rubric count (13 and 19 against a floor of 20),
three with tables omitting or under-covering the factors they report on. A 20%
rejection rate is the price of gates with teeth; the alternative is those papers
in the corpus.

### A third repairable JSON slip

A plan response opened `"deviation": {` and closed it with `]`. Neither the
escape repair nor the trailing-comma repair touches a mismatched bracket, so
salvage truncated to before the field and the paper was discarded.

`_fix_brackets` tracks open containers on a stack and closes each with the
bracket it was opened with, skipping string literals — a brace in prose is not a
container. Verified not to alter well-formed input.

All three slips share a shape: **the structure is nearly right, and discarding a
whole paper over two characters is the expensive way to be strict.**

## Open

* Agreement re-measurement on the holdout set after the incomplete-table fix.
* Three holdout papers regenerating: their tables omit factors they report on,
  caught by the set check that replaced the ratio.
* **Zero ambiguous findings** against R5's 10–20%. Not gated, but watched.
* The 30-paper train set is not started.
* Retraining K6 on this corpus remains **deferred, not scheduled**: seeding on
  three of the five real papers means training on paraphrases of three test
  documents, and the only clean read would be elemance and morrison, n=2.

## Keeping this document honest

It fell behind once already: four findings existed only in commit messages until
someone asked whether they were being recorded. Commit messages are not this
document — they are per-change and nobody reads them in sequence.

**Append a dated entry when a result lands or a pattern repeats.** If a fix is
worth a commit message explaining *why*, the why belongs here.

### Contaminating the holdout while debugging K7 — 2026-08-07

K7 scored 1/6 on the holdout, exactly matching its control. Diagnosing why, I
opened two holdout bundles and read their gold against K7's proposals. The
diagnosis was correct — `_MODEL` misses the plural "simulations", and many
context-of-use statements never name the model at all ("The COU is to compare
alternative helmet design variants…") — but **deriving a pattern fix from
holdout failures is fitting to the test set.**

The split was built one hour earlier, stamped at generation time specifically so
it could not be reassigned after a result. It does not defend against being
*read*.

Recorded rather than quietly worked around:

* `bundle_seeded_001_bologna` and `bundle_seeded_004_bologna` were inspected.
* Any K7 pattern tuned on them is fitted to two of the ten holdout papers.
* K7 is therefore developed against the **train** set, and holdout numbers for it
  are reported twice — over all ten, and over the eight never opened.

The general lesson is narrower than "do not look at the test set", because
debugging requires looking at something: **decide which corpus you are allowed
to debug against before the first failure, not after.** The train set existed and
was the right place; I reached for whichever bundle was in front of me.
