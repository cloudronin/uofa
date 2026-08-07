# Seeded corpus: specification

Generate credibility-assessment papers seeded on the five real ones, to lift the
evaluation corpus off a five-document floor.

The previous synthetic corpus was not merely optimistic — **it inverted the
ranking between two methods**, and every candidate evaluated on it had to be
re-evaluated. So this spec starts from why that happened, and every requirement
below is a property the old corpus lacked, measured against real documents.

## Why this is worth doing at all

Three objections were raised against seeded generation and all three were tested:

| objection | result |
|---|---|
| output will look like markdown, not a paper | **refuted** — 47% sentence-like vs the real 46%, old corpus 25% |
| entity counts will be definite by construction | **refuted** — models and datasets stable in *both*, requirements unstable in *both* |
| gold written in the same pass will be circular | **refuted** — 76.9% vs 71.4% independent reproduction, Fisher p = 1.000 |

**The old corpus failed by being tidy, not by being fake.** Its documents were
clean markdown with one model, thirteen clean findings, no tables, and a 0%
not-applicable rate that happened to be right for the wrong reason. Prose realism
was never the problem, which is why seeding on real prose does not by itself fix
anything.

## The generator must produce the mess

Each requirement names the failure it prevents and the real-corpus figure it is
measured against.

### R1 — Two-column PDF, not markdown

Render to PDF with two columns, justified text, hyphenation at line breaks, a
running head, and a figure caption or two spanning both columns.

*Prevents:* the five extraction faults having only five documents of evidence
behind them. Two-column raster order destroyed 12 of 13 evidence spans; lost
inter-word spaces caused two documents to be discarded; hyphenation split
0.7–14% of lines. Each fix currently rests on anecdote.

*Acceptance:* the reader's gutter detector fires on ≥80% of body pages; the
document's span-survival rate through `read_pdf` is ≥90%.

### R2 — Several models across several mechanisms

Each paper assesses **2–3 models × 2–4 mechanisms**, scoring every factor
separately for each, as the real papers do. Ground truth is per
**(model × mechanism × factor)**.

*Prevents:* the defect that appeared four times. Selection went 3/6 → 5/6 once
the model was named; the D1 agreement check manufactured a 1/6 disagreement by
withholding scope; K8 still fails on Morrison's two contexts of use. One
generated bundle being one model is why none of that was catchable.

*Acceptance:* ≥2 models and ≥2 mechanisms per paper; a scope-blind extractor
scores measurably worse than a scope-aware one on the same paper.

### R3 — A summary table that restates the prose findings

Include a per-factor table giving each factor's level and a one-line rationale,
where the *same* finding is also stated in the body with the figures.

*Prevents:* the annotation bias D1 found. All 12 of my Bologna spans came from
Table 1 rather than the prose it summarised, which is only possible in a document
that has both. It also gives the furniture filter something to be wrong about.

*Acceptance:* ≥60% of factors have their finding in both table and prose; the
furniture filter removes the table rows and retains the prose.

### R4 — The standard's gradation rubric, reproduced

Reproduce the V&V 40 or NASA CAS gradation definitions verbatim, as real papers
do — `a. A single sample was used. b. Multiple samples were used...`

*Prevents:* rubric definitions surviving segmentation as standalone sentences
that outrank findings. This is the fifth extraction pathology and was found only
in Nagaraja.

*Acceptance:* ≥20 rubric definition sentences; all removed by
`document_furniture` before routing.

### R5 — Omitted and ambiguously reported factors

**This is the one difference the tests actually found.** The seeded paper
reported a clean finding for all 13 factors; real papers do not.

* 15–30% of factors: **no finding at all** — named in the table, absent from the
  prose
* 10–20%: reported **ambiguously** — a passing mention that a careful reader
  might or might not count as evidence

*Prevents:* flattering coverage while leaving the harder judgement untested. 8 of
the 51 real factor pairs sit in exactly this ambiguity, and it is where an
independent annotator disagrees.

*Acceptance:* **factor-selection agreement between two independent annotators
lands at 85–95%, not 100%.** Real documents give 92.0%; the seeded paper gave
100%, and that gap is the target.

### R6 — Non-standard values, stated confidently

Every real paper deviates from the standard somewhere, and none of them flag it
as a deviation:

* an input **renamed** — Bologna's *regulatory impact* for model influence
* an input **given an undefined value** — TAVI I's *"deemed significant"*
* a **compound** result — Morrison's *"Low-medium (level 2)"*, Nagaraja's
  *"High-Medium"*
* a **numeric scale the standard does not define** — TAVI I's 1–5

*Prevents:* K8 passing on documents that all use textbook vocabulary. At least
one deviation per paper, drawn from these four kinds.

*Acceptance:* a validator that indexes the standard's table naively must return
`not_derivable` rather than a value.

### R7 — Evidence stated once, obliquely, and far away

The finding for a factor appears **once**, in the body, phrased without the
standard's vocabulary, hundreds of sentences from where the factor is named.

*Prevents:* the reason ARED routes at 0.86 recall@5 while journal prose routes at
0.33 — its evidence lines *begin with the factor name*. A corpus of labelled
evidence measures nothing.

*Acceptance:* median distance between a factor's name and its evidence ≥100
sentences; ≤2 of 13 findings contain the canonical factor name.

### R8 — Every factor scored, none omitted from the table

Real assessments enumerate the full checklist and score absent evidence **0**
rather than dropping the row. The real corpus N/A rate is **0.0%**.

*Prevents:* re-manufacturing a property real documents do not have. An earlier
campaign spent a day trying to force 30–60% not-applicable into the old corpus
before this was measured.

*Acceptance:* N/A rate 0%; `control_constant_list` scores ~1.000, as it does on
real documents. **The constant being unbeatable is correct and must not be
"fixed".**

### R9 — Standard-conditional properties

7009A papers must **not** state a context of use or model risk; V&V 40 papers
must state both, with rationale. Measured: 0/1 mentions in the two 7009A
documents against 39/33/50 in the three V&V 40 ones.

*Prevents:* a candidate returning a value where the property cannot exist. Any
non-null `modelRiskLevel` on a 7009A document is fabrication.

*Acceptance:* the split reproduces, per standard.

## Acceptance: the corpus is checked before it is used

A generated corpus is **not usable** until its profile matches the real one.

Implemented as [`corpus_profile.py`](../dev/tools/scripts/corpus_profile.py),
which exits non-zero out of tolerance.

| measure | real | tolerance |
|---|---|---|
| sentence-like fraction | 0.46 | 0.36–0.56 |
| furniture-filter retention | 0.35 | 0.25–0.45 |
| run-together tokens (>20 chars) | ~0.05% | <0.5% |
| two-column pages | 0.73 | ≥0.60 |
| hyphenated line ends | 0.049 | ≥0.02 |
| **words per paper** | **10,994** | **≥5,000** |
| **distinct types per paper** | **1,613** | **≥1,200** |
| gold span survival through the reader | ≥0.90 | — |
| factor-selection agreement, 2 annotators | 0.92 | 0.85–0.95 |
| same-sentence agreement, 2 annotators | 0.71 | 0.60–0.85 |
| N/A rate | 0.000 | = 0 |
| entity counts over 5 draws | models, datasets stable; requirements not | — |

Agreement *above* 0.95 means the papers are too clean, not that the corpus is
good. Length and vocabulary breadth are new rows: the old corpus ran 1,341 words
and 513 types per document, and a paper that short cannot satisfy R7 at all.

### Diversity: what calibration changed

The plan proposed failing above 0.60 mean pairwise cosine / 0.85 max. Measuring
first — as the plan required — showed all three parts of that were wrong.

**The thresholds were far too loose.** Real papers sit at mean 0.141, max 0.261.

**Full-text cosine reads length, not sameness.** Uncapped, it rated the corpus
that inverted the K6/K4 ranking as *more varied* than five real papers under two
standards, because the real ones are 8× longer and long documents share more
terms. Capping every document to its first 1,500 words restores the true
ordering: real 0.141, old synthetic 0.202.

**Two of the three measures grow with corpus size on their own.** Subsampling one
generator 200× at each n: mean pairwise is flat (0.137 → 0.138 from n=5 to 87),
but max pairwise gains 59% and mean nearest-neighbour 40%. A ceiling calibrated
on five papers would have **failed a 40-paper corpus exactly as diverse as the
real ones**, and that spurious failure would have read as generator collapse. The
two size-sensitive thresholds are therefore scaled by the measured drift.

**No average can be the duplication gate.** Mean pairwise is blind to it — three
exact twins hidden among thirty papers move it 0.162 → 0.166. Mean
nearest-neighbour is better but still dilutes: those same six duplicated papers
failed to lift it past its own threshold, because a mean hides a minority. So the
gate is a **count**: papers whose nearest neighbour is ≥ 0.60. It must be 0. The
margin is wide — the closest genuine pair anywhere in this project is 0.404
(opensim/elemance, same group and scenario) and the closest of 87 template-
generated papers is 0.391.

| measure | real | gate |
|---|---|---|
| mean pairwise (size-stable, twin-blind) | 0.141 | ≤ 0.18 |
| max pairwise | 0.261 @ n=5 | ≤ 0.29 × drift(n) |
| mean nearest-neighbour | 0.213 @ n=5 | ≤ 0.24 × drift(n) |
| **papers with a twin ≥ 0.60** | **0** | **= 0** |

Validated in both directions: the gate passes the five real papers and rejects
the old synthetic corpus (exit 1, five rows out of tolerance). It does *not* fail
the old corpus on diversity, which is correct — those 87 papers are genuinely
distinct parameter variants. Their defect was tidiness and length, not repetition.

## What this corpus is and is not for

**For:** scaling routing and extraction evaluation past five documents;
regression tests for the five reader fixes; exercising scope handling; giving
underpowered rows (K7, K5, K3c) an n at which a result means something.

**Not for:** replacing the real documents. The five real papers stay the
**held-out anchor** and are never used to tune a generator, a prompt, or a
threshold. A method that wins on the seeded corpus and not on the five is a
method that learned the generator — that is precisely the failure this whole
line of work uncovered, and the only defence is keeping the real set clean.

**Every headline figure is reported on both**, synthetic and real, side by side.
If they disagree, the real number is the number.

## Contamination rules, unchanged

* `evidence_keywords` may never seed a matcher — legitimate only as training
  labels under a bundle-level split, or as evaluation reference on held-out
  bundles.
* Generation must never see the real corpus's ground truth, only its documents.
* Bundle-level split, asserted rather than assumed.
