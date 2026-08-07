# Keyless extraction: plan v3

Supersedes v2. Written after the measurement work, because the investigation's
central question turned out to be unanswerable as posed and the useful question
is a different one.

## What is settled, and should not be redone

**Detection F1 is the wrong metric for this task — permanently.** Not a corpus
defect. A credibility assessment enumerates a fixed checklist, so "which factors
are present" is near-constant by the nature of the standard. `control_constant_list`
scores **0.960** on synthetic bundles and **0.971 on real NASA CAS tables**, where
a published assessment scores every factor and uses 0 for "insufficient evidence"
rather than omitting the row. Any eval built on detection ranks a null model at
the top, and three candidates (K1, K4, K6) failed against it while telling us
nothing.

**The sparse campaign is abandoned, and the reason is the finding.** C1 aimed to
push the corpus to 30-60% `not_applicable` so the checklist constant would stop
being unbeatable. Measured, on the only real data we have:

| corpus | bundles | distinct documents | N/A rate | constant precision |
|---|---|---|---|---|
| **real NTRS (Tier 1)** | 13 | **4** | **0.0%** | **1.000** |
| synthetic v2 dev | 54 | 54 | 12.8% | 0.872 |
| synthetic v2 test | 33 | 33 | 10.5% | 0.895 |

Zero N/A across 78 real factor rows — **but those 13 bundles draw on only 4
distinct source document sets**, one of which backs 8 of them (the shared
Elemance/THUMS report, where each bundle is a different model assessed within one
publication). The effective sample is 4 documents, not 13, and an earlier version
of this table reported 13 as though they were independent.

The conclusion survives the correction because it does not rest on sample size:
a published CAS table has one row per factor by construction, so 0% is what the
document type produces. But "4 documents" is the number to quote. The synthetic corpus is *already* more
adversarial to the constant than reality is, and driving it to 45% would
manufacture a property real documents do not have — a detection score that looks
discriminating and transfers to nothing. That is the failure this plan exists to
stop, so the campaign stops instead.

Caveat, stated because it cuts both ways: Tier 1 bundles were *selected* for
publishing a filled CAS table, so 0% is the property of documents that publish a
complete assessment, not of engineering documents generally. The real rate for
unselected documents is unknown. That makes 12.8% a guess — and 45% a bigger one.

**Ground truth over-credits, so 12.8% is itself an upper bound on N/A.** Step B
marks a factor `assessed` from general context. On 1389 rows, 313 (22.5%) have no
content word of the factor name anywhere in the source, and **218 of those are
marked `assessed` anyway**. Lexical absence is a weak proxy — a document may
address a factor purely in paraphrase — so 218 bounds the over-crediting rather
than counting it. Hand-checked on one bundle where the writer genuinely dropped
three factors, Step B marked one. Consequence: recall figures against this ground
truth are optimistic by an unmeasured margin, and only V1 closes it.

**Attribution is the metric that works.** Which factor the evidence belongs to,
scored against `evidence_keywords` on held-out bundles:

    constant  -> K2      0.053
    K1 anchors-> K2      0.353
    K6 classif-> K2      0.615
    sonnet (LLM)         0.946

An 18x spread with a sensible ordering, where every other number in the harness
compresses into a narrow band above a constant.

**The labels are reliable.** Two model families independently annotating the same
documents land on the same sentence for the same factor **89.3%** of the time
(gpt-5 vs claude-sonnet-4-6, 10 bundles). Attribution measures attribution, not
one annotator's taste.

**Detector and extractor are different jobs.** A detector's value is *routing* —
telling the extractor which sentences to read — and that is precisely what a
constant cannot do. Scored in isolation K6 reads "fails, -0.140"; scored as a
router feeding the same extractor it reads **0.615 against 0.058**. They need
not be the same model and the evidence says they should not be.

**The eval scored 1 of 13 required properties**, and the extractor's output
failed the project's own SHACL 82% of the time while the eval reported PASS.
Fixed: schema coverage and validity now run on every batch, with null models for
each property.

**Blank template rows were being scored as detections.** The workbook template
pre-fills a row for every factor in the pack, and the parser emitted those rows
as extractions whether or not anything was written into them. Six NASA-only
factors had **162 entirely empty rows** across the dev corpus — no level, no
status, no criteria, no rationale — and the report gave all six a detection rate
of 1.00.

| mean overall F1 | all | nasa | vv40 |
|---|---|---|---|
| blank rows credited | 0.920 | 0.928 | 0.912 |
| **blank rows dropped** | **0.853** | **0.793** | 0.912 |

NASA read as *better* than V&V 40 while the extractor was filling 13 of its 19
factors. V&V 40 is unchanged, which is the control for the fix.

This is the checklist-constant problem inside the extractor's own score: naming
a factor is free, so any metric that rewards the name rewards a null model. The
filter lives in the parser rather than the scorer on purpose — putting it in
`score_factors` classes `control_constant_list` (which emits `factor_type`
alone, by design) as blank too, dropping it from 0.960 to 0.000 and
manufacturing headroom for every candidate instead of measuring any.

## The question that replaced the original one

Not *"can a keyless method beat the LLM"* — it cannot, and detection cannot
even measure the attempt. The question is:

> **Where is the boundary?** Which properties can a keyless pipeline fill at
> what quality, and what is left that genuinely needs a model?

Current answer, partial: keyless routing reaches **0.615 attribution against
sonnet's 0.946** — about two thirds of the quality at zero marginal cost, ~5 MB
of coefficients, seconds to train, offline.

## Remaining work

### Corpus, ~$4, mostly running

| | | |
|---|---|---|
| ~~**C1**~~ | ~~Finish sparse convergence~~ | **abandoned** — see above; real N/A is 0% |
| **C2** | Re-extract regenerated bundles, re-score | ~$3 |
| ~~**C3**~~ | ~~Fix 20 colliding bundle ids~~ | **done** — verified 0 collisions, 0 shared documents |

C3 is verified rather than asserted: no bundle id appears in both splits, and no
two bundles across the split hash to the same source content. The value is that
the bundle-level split is now *checkable*, so the eventual held-out figure means
what it says. It does not license using the test set yet — that stays
sentinel-locked, and K6 keeps its within-dev holdout during calibration.

C1 stopped at 54 dev / 33 test bundles (26 sparse specs ungenerated). Two
mechanisms were tried and both are recorded in the generator rather than
deleted, because the second one works and is the right way to build a sparse
corpus if one is ever wanted:

* *Instructed omission* — "at least 40% of the factors must be missing".
  Produced 8-21% across five rounds of escalating wording. Step A is never given
  the factor list, so this asks a writer to subtract a fraction from a set it
  holds only in its head.
* *Structural omission* (`sparse_scope`) — name the ~55% subset the document may
  cover and withhold the rest. Guarantees 46% withheld by construction,
  deterministic per bundle, every factor still covered somewhere. Compliance is
  partial: one dry-run bundle dropped its out-of-scope factors cleanly, another
  covered everything anyway.

The mechanism is retained and tested (`tests/test_sparse_scope.py`); the
campaign it was built for is not worth running.

C3 is a bug I introduced numbering both splits from index 9. No content leaked
(0 of the 20 have identical documents) but an id-keyed split is unverifiable,
which currently forces K6 onto a within-dev holdout.

**Expected outcome of C1/C2, stated in advance:** sparse reaches ~37% N/A but
`complete` bundles are 0.5% and `ambiguous` 4.9% by design, so the overall rate
lands near 16% and the constant still scores ~0.91. Detection stays saturated.
If that projection holds, it confirms the "permanently wrong metric" finding
empirically rather than by arithmetic. If it does not, say so.

### Candidates, ~9h, free

| | | Kill criterion |
|---|---|---|
| **K3** entity patterns | `bindsModel` / `bindsDataset` / `bindsRequirement` | beat `control_constant_entity` on **counts**, never coverage |
| **K5** section extraction | `hasDecisionRecord`, `acceptance_criteria` | beat `control_constant_decision` |

Both are extractors, so both need their own correctness measure: groundedness
cannot see a *selection* error, where the wrong model or the wrong decision is
lifted verbatim.

### V1 — run, and it found something upstream of what it was aimed at

**Status: done, with a caveat about who did it.** V1 was specified as *human*
annotation. This was annotated by Claude, which is weaker — but the loop V1
exists to break is that gpt-5 both wrote and labelled the synthetic corpus, and
the NTRS documents are human-written and published, so the check still bites.
Annotation was written before any extractor was run against the document.

**The real corpus is 4 documents, not 13** (one report backs 8 bundles), and
only 2 of the 4 are extractable prose:

| document | form | usable |
|---|---|---|
| elemance | 45pp report | yes |
| opensim | 12pp journal article + supplemental | yes |
| ared | 1pp conference poster | no — columns interleaved |
| imm | 32 slides, 43 words/slide | no — bullet fragments |

**The finding: the PDF reader was destroying 92% of sentences.** Thirteen
evidence spans were annotated on the OpenSim paper — the sentence a reviewer
would cite for each factor. Against the pipeline's own reader:

    extract_text()                1/13 contiguous  ( 8%)
    extract_text(layout=True)     1/13 contiguous  ( 8%)
    per-column extraction        12/13 contiguous  (92%)

Token recall was ~1.00 throughout. The words were all present; the sentences
were not. `page.extract_text()` reads in raster order, so on a two-column page
it joins the left column's line to the right column's line — every sentence
becomes two halves of unrelated paragraphs. Invisible to any word-level metric
and fatal to everything the pipeline actually does: quoting, classifying and
attributing *sentences*.

It survived this long because the synthetic corpus is markdown, where the
question never arises. Only real documents were affected — which is exactly
where the transfer claims live.

Fixed in `readers/pdf_reader.py` by detecting the gutter (a vertical band no
body word crosses, measured after dropping full-width running heads and
captions) and reading each column separately. Measured separation is wide —
two-column pages 0.000–0.010, single-column 0.056–0.071 — so the 0.03 threshold
is not finely tuned. Both single-column prose documents split on zero pages,
which is the side that matters: a false positive would cut every line in half.

**A second layer of the same bug.** `sentences()` splits on newlines before
punctuation — correct for markdown, where a line is a logical unit; wrong for a
PDF, where a newline is where the typesetter ran out of column. So even after
the columns were recovered, sentences were still delivered as line fragments.
Unwrapping in the reader took the OpenSim document from 989 fragments to 539
sentences. Both layers were invisible on markdown and fatal on PDF, which is the
pattern worth remembering: **the sentence-level toolchain assumes markdown line
semantics, and real evidence is PDFs.**

**The first real-document attribution number, and it is 0.000.** A lexical
router — the honest zero-training keyless baseline — scores **0/7** against the
hand annotation, below the 0.30 kill threshold. The reason is more useful than
the number: it routes *every* factor to the abstract's sentence enumerating the
eight credibility factors, because that is where the factor names are densest.
That sentence is a citation of the standard, not evidence for anything. The
findings are 200 sentences later in the Results section.

This is the checklist-constant phenomenon once more: the document contains the
checklist, and naive methods find the checklist rather than the assessment.

**Scope of that result, stated precisely.** What was measured is the lexical
baseline on 7 factors of 1 document. **K6 — the trained detector whose 0.615 is
the headline keyless figure — has still not been run on a real document.** The
plan's kill criterion is about the K6→K2 pipeline, so it is not yet triggered.
What changed is that the measurement is now possible, and the baseline it must
beat on real text is 0.000 rather than unmeasurable.

### Original V1 framing, kept for the record

**Status: superseded by the above.** Sequencing decision taken 2026-08-06: K3 and K5 run
first. The argument for doing V1 first was made and not accepted, which is a
legitimate call — it trades earlier candidate coverage against later validation.

**The consequence, recorded so it is not lost:** until V1 runs, every figure in
this plan is synthetic-only. By this plan's own rule that puts all of them in
the middle band — *"continue, but re-label every synthetic figure as
real-document transfer unverified"* — including K3's and K5's when they land.
That label belongs on the numbers in any write-up, not just in this paragraph.

**V1. Hand-annotate 2-3 real NTRS bundles** at sentence level.

Everything above rests on synthetic documents. 89.3% agreement says the labels
are reproducible, not that they are correct, and the 13 Tier 1 bundles carry no
sentence-level annotation because published CAS tables do not mark which
sentence evidences which factor.

Until this exists, every attribution number means "agrees with a model consensus
about a generated document". After it, they mean something about extraction.

#### V1 is asymmetric, and the plan must say so

Two or three bundles is **30-50 judgments**. That sample is large enough to
falsify and far too small to confirm:

* **A bad result is conclusive.** If attribution on real documents collapses --
  say below 0.30 for the pipeline that scores 0.606 on synthetic ones -- then
  the synthetic labels do not transfer, and every number in this plan describes
  a closed loop. That kills the line, and 40 judgments are enough to know it.
* **A good result proves very little.** 0.60 on three hand-annotated bundles is
  three documents, one annotator, no confidence interval worth quoting. It
  licenses continuing; it does not license claiming the method works on real
  reports.

The asymmetry is the reason to do it, not a reason to discount it. It is the
cheapest possible falsification of the most load-bearing assumption, and it is
the only item here that can invalidate everything above it.

**Kill criterion — the only one in this plan that stops the whole line, not one
candidate:**

> Annotate 3 real bundles. If pipeline attribution on them is **< 0.30**, stop
> the keyless investigation and report that the synthetic corpus does not
> transfer. Between 0.30 and 0.60, continue but re-label every synthetic figure
> in the write-up as "synthetic only, real-document transfer unverified".
> Above 0.60, continue and say the sample is 3 bundles every time the number is
> quoted.

The stopping rule exists because this is the item most likely to be quietly
skipped: it is unglamorous, it is manual, and a bad answer is expensive to have
found. Those are the conditions under which work does not get done, so it gets
a written threshold rather than an intention.

## The deliverable

The **hybrid ceiling**, reported as a named table, never a fraction — nine of
thirteen covered is a useless sentence when the remaining four carry the
substance:

| Property | Keyless fills it? | At what quality | Needs a model? |
|---|---|---|---|
| rationale routing | K6 -> K2 | attribution 0.615 vs 0.946 | for the last third |
| `hasCredibilityFactor` | any detector | unmeasurable — constant scores 0.96 | — |
| `bindsModel/Dataset/Requirement` | K3, untested | — | ? |
| `hasDecisionRecord` | K5, untested | — | ? |
| `modelRiskLevel`, `required_level` | no route proposed | — | **yes, judgment from risk** |
| `hasValidationResult` | not attempted | — | ? |

The rows where no keyless route exists are the finding. If `modelRiskLevel` and
`required_level` need a model, the shape of the answer is "keyless handles the
extractive properties, a model is still required for the judgment ones", and
that is a cost floor rather than a defeat.

## Open risks, stated plainly

**Synthetic labels.** Addressed by V1 and by nothing else.

**`required_level` is near-uniform within a bundle** — 60 of 97 vary at all, and
a control predicting the bundle's modal value would score near 100%. Measure it
on the real bundles, where the IMM assessment carries three distinct thresholds
across eight factors. Treat the synthetic figure as coverage only.

**K6 trains on the corpus it is tested on** (different bundles, same generator).
It has never seen a real document. Its 0.615 is an upper bound on what it would
do in the field, and the gap is unmeasured until V1.
