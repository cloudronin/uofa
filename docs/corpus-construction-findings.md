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

### 2. The defect is often one step upstream of the symptom — eight times

| symptom | what it looked like | actual cause |
|---|---|---|
| 91% of gold levels "not stated" | gold's prompt | the write prompt never specified the table |
| the table was device parameters | the write prompt just fixed | a trailing comma truncating the real table away |
| table coverage 0.15, 0.05, 0.39 | the writer under-delivering | a validator discarding valid rows |
| selection agreement 0.631 | the corpus being ambiguous | gold and annotator asked different questions |
| selection agreement 0.765 | the corpus again | my own `factor-not-scored` drop |
| a table "omitting" a factor | the writer | a substring match and one dropped article |
| K5 and K3c failing outright | the candidates | both called `read_text()` on PDFs |
| K5 "failing" | the candidate | the criterion was unreachable at a 1.000 control |

Each number was real. Each attribution was wrong. Twice the symptom pointed
directly at a component that had just been corrected, and twice it pointed at a
candidate that was reading binary garbage.

**The predictive value is the point.** By the eighth instance this had become the
first thing worth checking: when a component fails, look at what feeds it before
looking at it.

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

### K5 becomes measurable — 2026-08-07

Six papers regenerated so the corpus contains rejections: 5 of 30 train, 1 of 10
holdout, constants 0.833 and 0.900 against the real corpus's 0.815. Both sets
still clear every offline row, diversity 0.136 and 0.154, zero twins.

| | before | after |
|---|---|---|
| constant control | 1.000 | 0.833 / 0.900 |
| K5 | criterion unreachable | **0.033 / 0.100 — fails** |

K5 abstains on 28 of 30. The reason is visible and is not the corpus's:

* 9 of 30 papers use explicit "accepted"/"not accepted" wording — the old corpus
  had 11 of 49, so this is comparable
* 27 of 30 have gold's `outcome_source` verbatim in the document

The conclusion is stated and findable; K5 matches a narrow closed vocabulary
that most papers do not use. **"Untestable" has become "fails, decisively"**,
which is the transition the corpus was built to enable.

### Two more failure shapes, both mine

**A fix that looks applied and does not reach the surface it was for.** The first
accept/reject assignment drew independently per bundle. On the real bundle names
that produced two rejections, both in train — so the holdout would have had none,
a constant would still have scored 1.000 there, and K5 would have stayed
untestable exactly where it matters while the corpus-level number moved
(40/40 → 38/40) and looked fixed. Stratifying by index puts the target rate in
every split at any size.

**Truncating a report before reading it.** `{decision_rule}` was added to a prompt
while the `format()` call was left untouched — a replacement that silently did
not match — and five papers failed at $0.00 each with a `KeyError`. I piped that
run through `tail -4`, which kept the summary and discarded every failure line,
so it read as "generated 0/30, $0.00" and I took it for nothing having happened.

The same instinct that made `--save-raw` worth adding applies to one's own
terminal: **if a step can fail, do not truncate its report before reading it.**
A test now compares each prompt's placeholders against the keywords its call site
passes, so an unsupplied placeholder fails in the suite rather than once per
paper at generation time.

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

### The corpus did not carry the gold it was built to serve

The plan's stated outcome was to unblock K7, K5, K3c and K9 "by giving them an n
at which a result means something". Forty papers were generated, validated and
committed before anyone checked whether their gold contained those candidates'
answers. It did not:

| candidate | reads | in the seeded gold |
|---|---|---|
| K5 | `expected_decision` | absent |
| K3c | `expected_entities` | absent |
| K9 | validation-result spans | absent |
| K7 | context of use | absent, and no K7 existed |

The gold carried `findings`, `models`, `mechanisms` and `scope_allowed` —
everything routing needs and none of the four fields the plan named as the point
of the exercise.

**Nothing forced the check.** R1–R9 describe *document* properties and say
nothing about the gold schema, so every acceptance gate passed on a corpus that
could not answer the questions it was built for. It surfaced only when the four
candidates were finally run against it.

This is a different failure shape from the eight above: not a wrong conclusion
from real data, but a **gap between two documents** — the spec constrained the
papers, the plan promised the outcome, and nothing tied the second to the first.

Fixed by having gold emit all four, named as the existing scripts already read
them so K5, K3c and K9 run unchanged rather than through a shim. Cost about $6.60
to regenerate gold across all 40, PDFs untouched.

**The general form:** a corpus can satisfy every property its spec names and
still not serve its purpose, because a spec describes what the artefact IS and a
plan describes what it is FOR. Check the second explicitly.

### K7, written from nothing

There was no K7. It is now `keyless_k7_context_of_use.py`, and two findings came
out of building it.

**Its 7009A control does not transfer from K8.** K8's works because the risk
vocabulary is genuinely absent from those papers — they never write "model
influence" — so any value is invented. K7 has no such luck: OpenSim states "The
OPENSIM Full Body Model was used to assess a muscle strain injury", which is a
model-purpose statement in exactly the shape a context of use takes. The
standards differ in whether they give that statement a formal role, not in
whether the sentence exists. Requiring `None` there tests whether the extractor
was *told* the standard, not whether it read anything.

**Its first route was built on a premise true only of Bologna** — that the
statement sits away from the term naming it. Measured on train, most papers do
name it, and a definitional route (the term or a synonym plus a copula) beats
both the shape route and the control on retrieval *and* restraint.

### K9 gained a corpus mode

K9 read hand-annotated `docs/v1/valresults_*.json` with hardcoded documents. It
now takes `--corpus`. The real corpus records a verbatim span per result; the
seeded corpus records `name_keywords`, so matching is on keywords, and a sentence
must carry most of a result's keywords rather than merely sit near one.

### The four blocked rows, run at n=40 — 2026-08-07

| candidate | verdict | detail |
|---|---|---|
| **K7** | ~~works~~ **retrieval ties its control** | Corrected 2026-08-08 — 15/20 was measured on a train split regenerated three times afterwards. On the current corpus K7 is 9/20 and its control is also 9/20. 7009A restraint 9/10 and 4/4 holds. |
| **K9** | **not demonstrated, and now convincingly** | Renumbered 2026-08-08 on the current corpus: 12/79 against a control's 9/79, p = 0.185. The recorded 18/100 was measured pre-regeneration; the verdict is unchanged, the numbers are not. |
| **K3c** | **fails on counts** | 0/3 properties better on train, 1/3 on holdout |
| **K5** | **untestable — the corpus's fault** | all 40 papers accept, so a constant scores 1.000 |

**K9 is the clearest gain.** The deliverable recorded "not demonstrated, 4 vs 2 of
24, p = 0.135" — a verdict nobody could rely on, because n=24 could not separate
anything. At 100 gold results across 40 papers the verdict is unchanged and the
confidence in it is not: the effect is small and does not reach significance at
four times the sample. That is the difference between *we cannot tell* and *we
can tell, and the answer is no*, which is what the corpus was built to buy.

**K5 was made untestable by an omission in the generator.** Every one of the 40
papers accepts its model, so `control_constant_decision` scores 1.000 and the
kill criterion becomes "beat 1.000". The old corpus left room at 0.815. Nothing
in the spec or any prompt ever asked for a paper that rejects its model — the
same class of omission as the four missing gold fields, and found the same way,
by trying to use the corpus.

Fixed for future generation: `decision_for()` assigns the outcome deterministically
per bundle at the rate the old corpus had (0.185 not accepted, giving a constant
0.775 that K5 can beat). **The existing 40 papers still accept unanimously** —
making K5 testable needs the nine that should reject to be regenerated.

**K5 and K3c were also reading PDFs with `read_text()`** — binary garbage scored
as a failure to extract, the eighth instance of a symptom one step downstream of
its cause. Fixing it changed K5's verdict from "fails" to "untestable", which is
a different and more useful thing to know.

### Train-set agreement, sampled — 2026-08-07

12 of 30 bundles, 2 scopes each. Confirmatory only: the holdout is the validated
set and the plan never required this.

| measure | train sample | holdout | band |
|---|---|---|---|
| gold precision | **1.000** | 0.986 | 0.95–1.00 |
| same sentence (single-ref) | 0.582 | 0.824 | 0.60–0.85 |
| N/A rate | 0.000 | 0.000 | = 0 |
| gold recall (reported) | 0.798 | 0.850 | — |

2×2: both 67, **gold-only 0**, annotator-only 17, neither 2. Gold claims nothing
the independent annotator does not also see, which is the property that matters
for an answer key.

**The two same-sentence figures are not comparable.** Train was sampled at
`--max-scopes 2 --limit 12` and holdout at `--max-scopes 3` over all ten, to save
about $3. Fewer scopes per bundle means fewer chances for the annotator's pick to
land on one of gold's spans for that scope, which depresses the figure
mechanically. Recording the difference rather than reading it as train being
worse: **the sampling differs, so the number differs, and no comparison is
available without re-running both the same way.**

That is the granularity mistake from earlier in this document, met again at the
level of sampling parameters rather than of measurement basis. It cost nothing
this time only because the holdout is what the corpus is validated on.

### A crash in the reporting path

Splitting selection from gated to reported left the "too clean" warning reading
`BANDS["agree_selection"]`, which no longer existed — so every run raised
`KeyError` **after** printing its verdicts. The numbers were correct and the
process exited non-zero, which reads as a failed check rather than a failed
print.

Fixed with an explicit threshold. The lesson is small and repeats one already
here: **a key that moves between dicts breaks every reader of the old dict**, and
the readers are easy to miss when the value still exists somewhere.

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

### K3c, corrected — 2026-08-08

The first named-entity measurement reported 0.657 / 0.818 and was **wrong twice
over**. Both errors flattered the result, and both were in the measuring
apparatus rather than the extractor.

**The matcher counted fragments.** `names_match` used a symmetric subset test,
which is fine for proper names and catastrophic for the long clauses gold records
as requirement names. Against

> "energy balance artifacts ≤1% and maximum penetration ≤0.02 mm support 8–10 on
> solver control"

the bare word `"balance"` satisfied it. So did `"control"`. `bindsRequirement`
measured **0.387** that way; corrected to a majority-overlap rule it measures
**0.026**.

**The control could not lose.** A constant naming "Computational Model" scores
0.000 on datasets and requirements, because no dataset name is common to all
papers — so "beats the constant" was satisfied by any non-zero recall at all.
Adding a control that competes (the document's most frequent capitalised phrases)
changes the reading of every row:

| property | K3c | constant | freq-NP | verdict |
|---|---|---|---|---|
| `bindsModel` | 0.42 / 0.41 | 0.08 / 0.09 | 0.37 / 0.36 | thin pass |
| `bindsDataset` | 0.09 / 0.16 | 0.00 | 0.02 / 0.00 | weak pass |
| `bindsRequirement` | 0.026 | 0.00 | 0.039 | **fails** |

Names remain the right measure — the same extractor scores 0.133 on exact counts
against 0.42 on names — but **"unblocks three rows" was optimistic**: one row is
a thin pass, one is weak, and one loses to a naive baseline.

**This was the ninth instance of a verdict turning out to be about the tool, and
the first predicted in advance.** The long-clause problem was flagged two steps
before it was tested, from nothing more than looking at what gold had recorded as
a requirement "name". By this point the pattern is reliable enough to use as a
prior: *when a number is better than expected, check the matcher before
believing it.*

### K7, corrected — a number that outlived its corpus — 2026-08-08

Wiring the candidates into a single extractor meant reading each recorded verdict
back off the corpus. Three of four reproduced exactly: K5 still fails at 0.033
against a 0.833 constant, K3c still returns 0.418 / 0.088 / 0.026. K7 did not.

| | recorded | reruns today |
|---|---|---|
| K7 retrieval, train | 15/20 | **9/20** |
| its control (name the term) | 11/20 | **9/20** |
| K7, holdout | 3/4 clean | 4/6 raw — reconciles, unchanged |
| 7009A restraint | 13/14 | 9/10 + 4/4 — unchanged |

The script is untouched since the run: `git log` shows one commit, no working-tree
diff. What moved was the corpus underneath it. K7 was committed at 22:05, and the
train split was regenerated at **22:38, 23:27 and 01:40** — decision variance, a
call-site fix, then entity names in the gold. K7 was never re-run against any of
them, and the margin it was credited with belonged to papers that no longer exist.

The half that survives is the more interesting half. **Restraint reproduces
exactly**: on NASA-STD-7009A, which defines no context of use, K7 returns nothing
on 9 of 10 train and 4 of 4 holdout documents. Knowing when a property does not
apply is a different capability from finding it, it is the one that separates an
extractor from a text generator, and only the retrieval half was stale.

**The pattern, which is #1 in a new dress.** Every earlier instance was a
threshold from one population applied to another. This is a *measurement* from one
population reported against another — the same defect with the arrow reversed, and
harder to see, because nothing about a stale number looks stale. The corpus is a
dependency of every verdict measured on it, and regenerating it silently
invalidates them all.

**What to do about it, cheaply:** the corpus has a content hash. Every candidate's
recorded result should carry the hash of the split it was measured on, and any
verdict whose hash does not match the current corpus should be printed as stale
rather than read as a result. Until that exists, a corpus regeneration means
re-running every candidate, and this one did not.

### "No keyless route" meant "one matcher failed" — 2026-08-08

Three properties were recorded as having no keyless route. Each verdict rested on
a single hand-written pattern matcher — K3c's regexes, K5's section scan, K9's
shape heuristic — while the strongest keyless method in the project, a trained
classifier, had been applied to **one property of nine**. K6 is nothing but TF-IDF
into logistic regression, and it was never tried anywhere else.

`keyless_trained.py` applies it to the other three. No embeddings, no network, no
model call; bundle-level split, controls per stage.

| property | matcher | trained | control |
|---|---|---|---|
| `hasValidationResult` | 0.152 | **0.438** | 0.125 |
| `hasDecisionRecord` outcome | 0.033 | **0.800** balanced | 0.500 |
| `bindsRequirement` | 0.026 | 0.065 | 0.000 |

Two of three now beat their controls. On the five real papers — the anchor —
validation results transfer at 9/24 against a control's 1/24, and 2/7 on the two
papers that are not the generator's seeds.

**The metric was the bigger error.** K5 was scored against a control that answers
"Accepted" every time and scores 0.833, because 34 of 40 papers accept. That
control is unbeatable on accuracy and worthless in use: it never identifies a
rejection, the one outcome the tool exists to catch. On balanced accuracy the
constant is pinned at 0.500 and the classifier reaches 0.800, catching 3 of 5
rejections against 0. This is `control_constant_list` scoring 1.000 in different
clothes — a null model winning because the measure rewards the majority answer —
and it was recorded as a property being unextractable.

**Two of my own defects, found by looking rather than by a test.** The
requirement-name matcher used substring containment, so "Section" scored against
"Section 5 requirements"; fixing it to whole-token containment took the trained
result from 0.323 to **0.065**. And the control labelled "most frequent spans"
was taking the first six in document order. Both flattered the candidate. This is
the *third* time the K3c fragment bug has been written — twice in K3c, once here
— which makes it worth a shared matcher rather than a note.

**A clean negative worth keeping.** Accept/reject reads like a document-level
property, so classifying it from the whole document should delete the weak 0.222
locator. It scores 0.850 / 0.500 / 0.000 — identical to the constant. Given 200+
sentences the classifier learns to always say "Accepted". The signal is localised
and diluting it destroys it, so the two-stage design is required and the locator
is the thing to improve.

**Pattern #8, and it is the one that cost the most.** *A negative result about one
implementation reported as a negative about the task.* Every "no keyless route"
row was one method deep. The fix is procedural: before recording a property as
unextractable, try the method that already works elsewhere in the same codebase.

### Attacking the two bottlenecks: one moved, one was mis-specified — 2026-08-08

Neither improvement came from tuning a ranker. Both came from asking what the
stage *upstream* could reach at all before touching the stage that was failing.

**The decision locator was denied the feature it needed.** The gold decision
sentence sits at median 0.79 through the document, 20 of 34 in the back half, and
a bag of n-grams cannot represent position. Four positional features took top-1
from **0.222 to 0.400**, top-3 to **0.700**, against controls still at 0.000.

Separately, six papers carried no label at all. Their best-matching sentence
scored 0.42–0.53 against a 0.60 gate — the *label* was strict, not the documents
unlabelled. At 0.40 all forty papers label, and the outcome classifier went
0.800 → **0.917** balanced, **0.833 reject recall**, on the larger sample. Five of
six rejections caught, against a constant that catches none.

**The requirement generator was looking for the wrong syntactic category.** Its
ceiling was **0.140**: 86% of gold names were never proposed, so no ranker could
have recovered them and every hour spent on ranking would have been wasted. The
misses were unambiguous —

    a recirculation CSE fraction below 5%
    within the predefined 10% tolerance for central tendency
    peak resultant linear head acceleration
    an NIH not exceeding 0.02 g/100 L at 120 min

A requirement in this literature is a lowercase **acceptance criterion** — a
quantity, a relation, a threshold — not a proper noun. The generator was matching
capital letters.

**Raising that ceiling made the result worse, and that is the finding.** The
broadened generator reached **0.822**. End-to-end recall went **0.065 → 0.032**
and fell *below* its own control, because candidates per paper went from ~400 to
~1,225 and picking six became a harder selection problem than the recall gain
repaid.

This is pattern #7 in a new place. Upstream recall and downstream precision are
not independent, and **a candidate-generation improvement shipped without a
matching selection improvement can be a net loss.** The ceiling diagnostic was
still worth running — it is what proved the ranker was never the problem — but a
ceiling is a bound on success, not a promise of it.

**And the property is mis-specified.** 42% of the gold requirement names do not
appear verbatim in the document, so no extractive method can exceed **0.579** by
construction. `requirements` was already the only entity category that varied
across repeated annotation draws. The gold is a set of paraphrased acceptance
criteria, and asking for them by name asks a question the documents do not
answer. `bindsRequirement` needs its task redefined before any method is chosen.

### bindsRequirement was the wrong property, and the gold said so — 2026-08-08

Every number ever recorded for `bindsRequirement` — K3c's 0.026, the trained
0.032 — was scored against gold that is **81% acceptance-criterion shaped**: a
relation and a threshold, like `a recirculation CSE fraction below 5%`. Only 4%
are cited standards. The vocabulary has always separated the two:

| term | means |
|---|---|
| `bindsRequirement` | "the engineering requirement the model is being trusted to help satisfy" |
| `acceptanceCriteria` | "the bar a factor or claim had to clear, stated before the evidence was weighed against it" |

**The mislabel began at generation.** `generate_seeded_corpus.py` asked the writer
for *"a requirement is an acceptance target the paper states it must meet"* and
filed the answers under `requirements`. The prompt described acceptance criteria
accurately and gave them the wrong name, and every extractor since has been
measured against gold for a property it was not extracting.

**This is the eleventh instance of a number measuring the tooling rather than the
thing, and the first to originate in the gold.** The previous ten were thresholds,
matchers, readers and stale corpora — all downstream of the labels. This one was
in the labels, which is the layer everything else is checked against, so nothing
downstream could have caught it. The tell was available early and went unread:
`requirements` was already known to be *the only entity category that varied
across repeated annotation draws* — recorded as evidence that the category was
indefinite, when it was evidence that the category was wrong.

**What changed.** The 107 labels were re-pointed to `acceptance_criteria` in all
40 bundles, in both `expected_entity_names` and `expected_entities`, and the
generator prompt, K3c's kind table and the trained route follow. `acceptanceCriteria`
was declared in the vocabulary and constrained by no shape, so nothing broke and
a previously unpopulated property now has gold. The v2 corpus keeps its
`requirements` counts: different generator, different lineage, and renaming it
would invalidate measurements taken on it.

**And the property itself is now author-supplied.** Only 30% of papers cite a
standard at all. `bindsRequirement` stays required at `minCount 1` in
`ProfileMinimal` — the requirement a model is trusted for is the point of the
artefact — but it moves out of the extractor, beside `hash` and `signature`. A
required field the source does not contain can only be satisfied by supplying
one, which is the constraint that produced 14 turbomachinery models labelled
"Class II" that validated while honest packages failed. Relaxing the constraint
would have made the number look better and the artefact mean less.

With that settled, **every extractor-facing property in `ProfileMinimal` now has
a keyless route that beats its control**, and a keyless package reaches Minimal
once a human names the requirement — one field, entered once.

### The CI fix that fixed one of two causes — 2026-08-08

`test_llm_baseline_on_the_shipped_corpus` and `test_the_synthetic_corpus_shortfall_rate`
failed in CI earlier in this session. The diagnosis then was that they read
`extracted.xlsx`, which is gitignored, so in CI every loop body was skipped and
the totals came out zero. The rows were frozen to a committed JSON and the fix
was pushed.

They still failed. The frozen fixture was real and necessary and was **one of two
causes**. The second:

    ImportError: cannot import name 'extracted_corpus_by_bundle'
    from 'conftest' (tests/space/conftest.py)

`from conftest import ...` resolves to whichever `conftest` module imported
first, and there are two — `tests/conftest.py` and `tests/space/conftest.py`.
Collect only one and the import works; collect both, as every full run and every
CI run does, and the wrong one can win.

**It survived because every hand-check ran the file alone.** `pytest
tests/test_groundedness.py` does not collect `tests/space`, so the collision
cannot occur, and that is the command anyone runs when checking one test. The
failure needed the whole suite, and the whole suite takes fifteen minutes, so it
was never the loop used while iterating.

Fixed by moving the helpers to `tests/extracted_corpus.py`, a module named for
what it holds, with `conftest` re-exporting them. A guard now fails if any test
imports `conftest` by bare name.

**Two patterns, one new.** #5, a fix applied in one place and not the other, for
the fourth time. And a new one worth naming: **a verification whose cheap form
cannot reproduce the failure.** Running one test file is the fast check and it is
structurally blind to a collection-order bug. When a fix is for a failure that
only appears in the full run, the full run is the only check that confirms it —
and "it passes when I run it" is not that.

### Three CI failures, one cause, and the third instance of the same blindness — 2026-08-08

Pushing the seeded-corpus work to `main` ran its tests in CI for the first time,
and three failed on one line:

    FileNotFoundError: [Errno 2] No such file or directory: 'pdflatex'

`--dry-run` renders one paper from canned content "to prove the
render->measure->gate path". The devcontainer has no TeX toolchain, so the guard
that exists to catch a bad configuration *before anything is billed* was itself
the thing that crashed. **A guard that cannot run is worse than no guard, because
it looks like one.**

Fixed by degrading honestly: without `pdflatex` the dry run prints

    RENDER PROOF SKIPPED: no pdflatex on PATH.
    Planning, scope and the split were checked; the render->measure->gate path was NOT.

and exits 0. The test asserts the proof where the toolchain exists and asserts
**the skip is announced** where it does not — rather than skipping silently,
which would make a green CI mean less than it appears to.

**Verified under the failing condition, not just the passing one.** The fix was
checked by running with a stripped `PATH` containing no `pdflatex`, because "it
passes on my machine" was exactly what let the bug through: this machine has
LaTeX installed and CI does not.

**This is the third instance in one session of the same blindness**, and the
pattern is now unmistakable:

| what CI had that local did not | how it hid |
|---|---|
| no `extracted.xlsx` (gitignored) | local had the paid run's output |
| both conftests collected | local runs one test file, never colliding |
| no `pdflatex` | local has a TeX install |

Every one passed locally and failed in CI, and in every case **the local
environment was richer than CI's**. The lesson is not "run CI more"; it is that
a check whose environment is a superset of the target's cannot falsify anything
about the target. Where a script depends on an external binary, a file outside
the repo, or a module name that could collide, the test must be run **with that
thing removed** — which is cheap, and is the only version of the check that can
fail.
