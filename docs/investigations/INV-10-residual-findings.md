# INV-10 residual — raw vs adjudicated audit outside the H2 section

Status: **CLOSED — no A9 re-run list; v2.0 adds a second label to the same pass**
Date: 2026-08-16 (addendum same day, against `UofA_Unified_Repair_Spec_v2_0.md`)
Feeds: parent A9, A4, A5

---

# ADDENDUM — re-investigated against parent spec v2.0

v2.0 §A9 clause 2 states the residual scope in terms that match this finding
exactly:

> INV-10 status: the shipped H2 section reports raw performance with nulls; **audit
> remaining citations elsewhere in the manuscript and apply the split.**

Confirmed: 7 citations already labelled, 11 unlabelled-but-raw, 0 unknown, re-run
list empty. The recommendation stands at ~45 minutes.

**One addition.** GATE-H2 (§0.1) now requires figures to be *"Reported per corpus:
the 50-bundle synthetic set (30 dev + 20 held-out) and the real annotated corpus
(A10)."* Several bucket-2 citations quote a figure without naming which corpus it
came from — `docs/extract_eval_v1.md`'s 0.964/0.954 pair is synthetic;
`README.md`'s recall@5 0.458 and groundedness 0.988 are real-document. **The
labelling pass should carry two labels, not one:** *raw / adjudicated* **and**
*synthetic / real*. Same 45 minutes, done once.

**And one caution.** A5's null-control row requires every headline metric to appear
beside its null. Bucket-2 citations vary here: `metrics-spec-r6-u8.md:69-70` and
`README.md`'s real-paper table both carry their controls; `docs/extract_eval_v1.md`'s
headline table (:45-47) does not, though the document states the null's implication
in prose at :24-26. The three publicly-facing documents flagged in the original
recommendation are the ones to fix, and adding the null column is a larger edit than
adding a label — call it 90 minutes total rather than 45 if A5 conformance is folded
into the same pass, which it should be.

Nothing here changes the bucketing or reopens the re-run list.

---

# ORIGINAL FINDING (v1.1-based, retained for the record)

## Headline

**The re-run list is empty, and for a structural reason worth stating in A9's text
rather than treating as luck: the extraction eval never had an adjudication step.**

Every extraction-quality figure cited outside `ch4-h2-section.md` is scored
programmatically against committed ground truth. There is no pipeline stage in
which a human corrects extractor output before it is scored, so there are no
blended figures and no lost pre-adjudication outputs. A9's *"if raw
pre-adjudication outputs were not preserved for any run, re-run extraction"*
clause does not fire anywhere.

The residual issue is not blending. It is that **most citations carry no label at
all** — they are raw, but they do not say so, and several sit next to genuinely
adjudicated numbers in the same document.

## Bucketing

Buckets per the item: (1) labelled correctly, (2) unlabelled but raw (label cheap
to add), (3) unlabelled and adjudicated-or-unknown.

| # | Citation | Figure | Bucket | Note |
|---|---|---|---|---|
| 1 | [docs/ch4-h2-section.md:20-23](docs/ch4-h2-section.md) | dev 0.9637 / test 0.9544 mean F1, per-factor 1.000, 0 crashes | **1** | The compliant section; out of scope, listed for completeness |
| 2 | [docs/ch4-h2-section.md:61-64](docs/ch4-h2-section.md) | extractor 0.9035/0.8909 vs null control 0.9637/0.9544 | **1** | Labelled against its control, which is the stronger disclosure |
| 3 | [docs/ch4-h2-section.md:136](docs/ch4-h2-section.md) | *"adjudication rests on six disagreements"* | **1** | Explicitly adjudicated and says so |
| 4 | [docs/metrics-spec-r6-u8.md:69-70](docs/metrics-spec-r6-u8.md) | same four F1 numbers + delta over null (+0.0000) | **2** | Raw. Unlabelled, but the null-control column makes the point the label would. |
| 5 | [docs/metrics-spec-r6-u8.md:191](docs/metrics-spec-r6-u8.md) | *"disagreement adjudication, real — 6 rows"* | **1** | Labelled |
| 6 | [docs/extract_eval_v1.md:45-47,74-81,127-131,179-189](docs/extract_eval_v1.md) | 0.964 dev / 0.954 test; per-factor F1 1.000; overfit gap 0.010 | **2** | Raw scoring against `ground_truth.json`. **The largest unlabelled cluster.** Also carries its own withdrawal note at :24-26 (the null control scores 0.004 below the headline). |
| 7 | [README.md:513-525](README.md) | *"used to report F1 = 1.000 … 0.973 … 0.964 dev / 0.954 test"*, then the retraction | **1** | Model self-correction: the numbers are named, the reason they were misleading is given, and the 37-of-45 SHACL failure is stated alongside. Nothing to add. |
| 8 | [README.md:~530](README.md) | five real papers, gpt-5: recall@5 11/24 (0.458); groundedness 83/84 (0.988); levels 65/65; 5/5 validate vs null 0 | **2** | Raw. Already carries two cautions (*"groundedness is not correctness"*). One clause would close it. |
| 9 | [docs/credibility-inspector.md:235-236](docs/credibility-inspector.md) | held-out 0.9544, dev 0.9637 + per-factor triples | **2** | Raw |
| 10 | [docs/credibility-inspector.md:244-249](docs/credibility-inspector.md) | *"Earlier revisions of this page gave 0.8909 and 0.9035 … without [context]"* | **1** | A dated correction of a prior citation of the same figures |
| 11 | [docs/corpus-construction-findings.md:1178-1184](docs/corpus-construction-findings.md) | the same retracted headline + 37-of-45 | **1** | Carries the retraction |
| 12 | [docs/valid-package-spec.md:669-671](docs/valid-package-spec.md) | groundedness 0.988; the 0.964-vs-37-of-45 warning | **1** | |
| 13 | [docs/valid-package-spec.md:541](docs/valid-package-spec.md) | `hasValidationResult` recall@5 0.438 vs 0.125 | **2** | Raw, routing metric |
| 14 | [docs/keyless-extract-plan-v4.md:48,99,141](docs/keyless-extract-plan-v4.md) | K6 0.829 recall@5; K4 routing 0.38; deltas +0.334→+0.160→+0.019 | **2** | Raw, keyless route |
| 15 | [docs/keyless-hybrid-ceiling.md:30,83](docs/keyless-hybrid-ceiling.md) | RRF routing 0.357 recall@5, 0.607@20 | **2** | Raw |
| 16 | [docs/seeded-corpus-spec.md:149](docs/seeded-corpus-spec.md) / [docs/real-corpus-supply-survey.md:205](docs/real-corpus-supply-survey.md) | ARED 0.86 recall@5 vs journal prose 0.33 | **2** | Raw |
| 17 | [docs/message-to-claude-code-attribution-plan.md:12](docs/message-to-claude-code-attribution-plan.md) | 0.9637/0.9544 vs 0.9035/0.8909 | **2** | Raw; working note |
| 18 | [site/src/content/docs/research/nafems-2026.md:21](site/src/content/docs/research/nafems-2026.md) | COU 1 = 11 weakeners / 5 patterns; COU 2 = 18 weakeners / 6 patterns incl. 2 COMPOUND-01 | **n/a** | **Not an extraction figure.** Deterministic C3 rule-engine output on hand-authored packages. Raw/adjudicated does not apply; the label to check here is *hand-authored*, which the page states at [nafems.mdx:145](site/src/content/docs/demo/nafems.mdx). |
| 19 | `site/src/content/docs/**` (24 further files) | — | **n/a** | **No extraction-quality figure appears anywhere else on the site.** Verified by grep for `F1`, `recall@5`, and each specific value. |

**Counts: bucket 1 — 7 · bucket 2 — 11 · bucket 3 — 0.**

## Why bucket 3 is empty

Traced rather than assumed. Two questions had to be separated:

**Q1: is there an adjudication step in the extraction eval?** No. The eval scores
extractor output against committed `ground_truth.json` files
(`tests/fixtures/extract_corpus_vv40/*/ground_truth.json`,
`tests/fixtures/extract_corpus_real/`, `tests/fixtures/extract_corpus_seeded/`).
The ground truth is authored once, in advance, and versioned; scoring is
programmatic (`src/uofa_cli/eval_scoring.py`). Nothing rewrites extractor output
between running and scoring. So "raw AI performance" and "post-adjudication
performance" are the same number, and no third figure exists to be blended in.

**Q2: where does human judgement actually enter?** In three places, none of which
touches a reported extraction figure:

| Site | What | Reported as |
|---|---|---|
| Ground-truth authoring | The author writes the gold labels the extractor is scored against | The eval's premise, and the right place for A9's protocol (A7) disclosure. **Not** an adjudication of results. |
| Attribution/groundedness disagreements | 6 real rows adjudicated | Labelled at [ch4-h2-section.md:136](docs/ch4-h2-section.md) and [metrics-spec-r6-u8.md:191](docs/metrics-spec-r6-u8.md) |
| Credibility Inspector step 3 | The user confirms/corrects factor statuses before the report renders | A *product* step, not a measurement step. The Space passes `factor_edits` into `finalize()` ([space/pipeline.py:881](space/pipeline.py)); no eval figure is computed downstream of it. |

The third is the one A9 cites as its concrete artifact. Worth noting for A9's text:
**the Inspector's confirmation step never enters a reported number**, which is
exactly what makes it a clean illustration — human judgement is visible, bounded,
and demonstrably outside the measurement path.

## Recommendation

**Not a re-run list — a labelling pass.** For the eleven bucket-2 citations, add
one clause at first mention per document: *"raw extractor output, scored against
committed ground truth; no adjudication step."* Estimated **45 minutes** across
9 documents. This is A9 item 2's requirement satisfied by annotation, not by
re-measurement.

Three of those documents deserve slightly more than a clause because they sit
closest to shipped text:
- `docs/extract_eval_v1.md` — the largest cluster and the origin of the retracted
  headline
- `docs/credibility-inspector.md` — publicly facing
- `README.md` §"With a model" — publicly facing, and already carrying two cautions
  that the raw label would sit naturally beside

## Escalation

The criterion was *"the re-run list includes any figure already in shipped chapter
text."* **Not triggered — the re-run list is empty.**

One adjacent observation, offered rather than escalated: several of these figures
have already been **retracted or re-contextualised** in place (README:513-525,
credibility-inspector:244-249, corpus-construction-findings:1178-1184,
ch4-h2-section:75). That is a strong pattern and A4's audit trail should cite it
directly — a project that names its own withdrawn numbers beside the reason is
making exactly the disclosure A4 exists to make. It is more persuasive evidence for
must-have 5 than the raw/adjudicated split itself.

## Coverage statement

**Searched.** Enumerated extraction-quality figures by value rather than by
location, so the search could not miss a citation in an unexpected file: repo-wide
grep for `0.9637`, `0.964`, `0.954`, `0.9035`, `0.9544`, `0.988`, `0.458`,
`recall@5` across `docs/`, `site/src/`, `studies/`, `README.md`; plus greps for
`F1` and `f1\b` across `site/src/content/docs/`, `README.md`,
`docs/ch4-h2-section.md`, `docs/metrics-spec-r6-u8.md`, `docs/extract_eval_v1.md`.
Grep for `raw|adjudicat|confirm|corrected|human` across the H2 section and the
metrics spec. Full file listing of `site/src/content/docs/` (24 content files) and
`site/src/components/` (7). Both NAFEMS pages read for numeric claims.
`space/pipeline.py` traced for where `factor_edits` enters and whether any figure is
computed downstream. Fixture corpora enumerated
(`tests/fixtures/extract_corpus_{real,vv40,seeded}/`).

**Search terms derived from the item's own definition** (an extraction-quality
figure = a number describing how well extraction performed): `F1`, `recall`,
`precision`, `crash`, `groundedness`, `recall@5`, plus each literal value — rather
than searching only where such figures were known to appear.

**NOT searched / not verified.**
- **The manuscript `.docx` was checked for extraction figures and has none to
  bucket.** Ch4's H2 subsections are skeletons: `[fill from extract eval: F1 vs
  50-bundle corpus + manual baseline]` (scoring table T14.R2), *"Results to report:
  F1 by field family on the held-out test set"* (¶443). **So the shipped-chapter
  risk is prospective, not present** — when those placeholders are filled, they must
  be filled with labelled figures. Worth a line in A9's checklist.
- `docs/archive/` and `docs/handouts/` were not swept.
- `src/uofa_cli/eval_scoring.py` was located but not read line by line; the
  no-adjudication-step conclusion rests on the corpus structure (committed
  `ground_truth.json` per bundle) and on finding no correction stage in the pipeline,
  not on reading the scorer's internals. **A 20-minute read of that file would
  convert Q1 from strongly-evidenced to verified**, and is the one cheap thing that
  would harden this finding.
- Deployed uofa.net content was not fetched; the site audit is against
  `site/src/content/` at this worktree's HEAD, which may lag or lead the live site.
