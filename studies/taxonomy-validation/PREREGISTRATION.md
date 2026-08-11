# Pre-registration: Group-B taxonomy validation

**STATUS: FROZEN 2026-08-11.** Corpus pinned, frame computed, catalog fixed. No
judge has been invoked. Any figure reported from this study is attributable to
the frame below, which was written before the first judge call.

Implements addendum v0.5 (A16). Method discovers, empirics validate, catalog
closes.

---

## 1. The frozen catalog

The rule set under validation, frozen at this commit. A rule not listed here
does not enter the study; a rule listed here is not revised mid-study.

| Rule | Severity | Path | Grounding |
|---|---|---|---|
| W-EV-GEN-02 | High | panel | NIST AI 800-3, benchmark-vs-generalized accuracy |
| W-EV-DET-03 | High | panel | Seahaven TRAP 35 |
| W-EV-NULL-04 | High | panel | Seahaven null-calibration |
| W-EV-COU-05 | Critical / High | panel | V&V40 COU-relevance, applied to eval |
| W-EV-CAP-06 | Medium | panel | Seahaven capability-confound |
| W-EV-DIV-07 | High | panel (sparse, §4) | V&V40 output comparison |
| W-EV-SUB-08 | High | **deterministic** | NASA-STD-7009 configuration control |
| W-EV-COR-09 | Medium | panel | V&V multiple-referent corroboration |
| COMPOUND-EV-01 | Critical | panel | settles only if constituents settle |
| COMPOUND-EV-02 | Critical | panel | settles only if constituents settle |

**Not in the catalog, recorded so the exclusion is deliberate:**

- **W-EV-UQ-01 — withdrawn.** Core's `W-AL-01` already fires on
  `noValue(?result, hasUncertaintyQuantification)` for any `ValidationResult`,
  and this pack runs all core patterns. A parallel rule would report one missing
  standard error twice under two ids.
- **W-AL-01 — core's, not under validation here.** Its firings are correct by
  construction on structured input, and its invariance across a blood-pump CFD
  study and an LLM benchmark is the praxis chapter's demonstration, not this
  study's subject.
- **W-EV-COV-09 — never existed.** An earlier draft named it; the design ruling
  rejected the coverage reading, and the rule that exists is COR-09.

`furnishers.PENDING_EMISSION` is **empty** at freeze, per A16.2. No rule in the
catalog has a structurally always-true firing condition.

## 2. Two settle paths

Per A16.7. Criteria presupposing "a judge reads the card and says whether the
rule was right to fire" apply only where that question is answerable.

- **Panel path** — the rule fires on whether a property is *stated in the card*.
  Precision/recall against adjudicated labels, plus finding-validity.
- **Deterministic path** — the rule's firing is invariant to card content.
  **W-EV-SUB-08** only. It fires on the subject's identity: verified at 1 firing
  per 1 prose node and 10 per 10 furnished nodes, identically. A card-derived
  label and this rule are about different objects, so precision against one is
  undefined in principle. Settles on the A16.5 grounding audit plus fail-once
  fixtures, and does not enter the panel cohort.

## 3. Labeling instruction: section scoping is binding

Gold labels are assigned **only from content under an evaluation heading**. A
sampling setting in "How to use" is not a determinism statement about the
reported scores.

This is not a stylistic preference. Measured across 49 cards: 45% mention a
sampling setting, **4% under an evaluation heading**. A labeler who counts the
former produces gold labels that disagree with the extractor by construction, and
the resulting precision figure measures the disagreement rather than the rule.

## 4. W-EV-DIV-07: declared sparse

The denominator is **opportunities — matched reported/furnished pairs — not
cards.** Dividing by cards would understate the rate by roughly the overlap rate
and make a rarely-triggered rule look like a failing one.

- Expected opportunity count is computed by `frame.py` and recorded in §6 BEFORE
  any judge call, so a small number is a prediction.
- Finding-validity may be adjudicated on single-digit instances, or deferred.
  A rate computed on three firings is not a rate.
- **Second venue named now:** the deep-study cohort, where every model has full
  raidex coverage and opportunities are ~40x richer than a corpus sample at 8%
  overlap. DIV-07 settles on mechanism plus whichever venue yields adjudicable n.

Mechanism is already validated on constructed fixtures (matched-beyond-tolerance
fires, matched-within is silent, unmatched produces no comparison, near-name
collision must not match). DIV-07 has so far fired only on a divergence
constructed by adding 20 points to a furnished score; its field rate is
unmeasured, and that is on the record before the first judge call.

## 5. Thresholds (A16.7, restated so the freeze is self-contained)

A rule settles iff firing precision >= 0.90, recall >= 0.80, finding-validity
>= 0.85, and its grounding line survives the audit. Judge calibration: per-judge
agreement vs gold >= 80%, pairwise kappa >= 0.70. Judges failing calibration are
**replaced, not averaged**.

## 6. The frame, computed and pinned

Source: `Weixin-Liang/AI-model-card-analysis-HuggingFace`, `data/modelcard_info.parquet`
at repo commit `6bcc76fe6142`. Content pin (A9.1 non-HF fallback form):
`sha256:79aa662d94d0112f13043f420d996347...`, 31,620,407 bytes.

**A16.2 named the wrong file.** It said `datasetcard_info.parquet`; the repo
contains `modelcard_info.parquet` (and a separate `model_info.parquet`). Dataset
cards and model cards are different objects, and this pack assesses model cards —
pre-registering against the wrong one would have validated the instrument on a
population it is not for. The row count A16.2 quoted (32,111) matches the model-
card file exactly, so the count was right and only the filename was wrong.

| | |
|---|---|
| Cards | **32,111** |
| Eval-bearing (A3 detector) | **21,181** (65.96%) |
| No-eval stratum | **10,930** |
| DIV-07 opportunity cards | **24** (0.07%) |

Strata (task category x word-count band x detector outcome) are in `frame.json`.

### The DIV-07 number settles its venue

**24 cards in 32,111 name any constituent this furnisher measures — 0.07%.** The
true opportunity count is lower still, since a named benchmark may yield no
extractable score.

This is two orders of magnitude below the 8% measured in
`studies/card-eval-reporting-2026-08`, and the discrepancy is not error: that
study sampled the **most-downloaded models in 2026**, while this corpus is a
**2023-10-01 snapshot**. SimpleQA, StrongREJECT and XSTest largely postdate it.
The two figures describe different populations and the 8% does not transfer.

**Consequence, recorded before any judge call:** the corpus cannot validate
W-EV-DIV-07's field behaviour. Mode 2 is **deferred to the deep-study cohort**,
where every model carries full raidex coverage, rather than adjudicated on a
handful of instances here. DIV-07 settles on Mode 1 (mechanism, already
satisfied) plus Mode 2 in that venue. This is the §4 ruling applied to a measured
number instead of an anticipated one.
