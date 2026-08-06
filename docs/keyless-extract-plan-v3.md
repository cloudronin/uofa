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
| **C1** | Finish sparse convergence | running, 78/97, ~$1 |
| **C2** | Re-extract regenerated bundles, re-score | ~$3 |
| **C3** | Fix 20 colliding bundle ids between dev and test manifests | free, ~30 min |

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

### External validity, ~2h, free — the highest-value item left

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
