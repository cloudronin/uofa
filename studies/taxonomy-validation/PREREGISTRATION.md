# Pre-registration: Group-B taxonomy validation

**STATUS: DRAFT — NOT FROZEN.** Two things must happen before this becomes a
pre-registration rather than a plan, and both are named in §6. Until then no
judge may be invoked against the corpus, because a frame written after seeing
judge output is not a frame.

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

## 6. What is NOT yet frozen — the two blocking items

**(a) The corpus is not pinned.** A16.2 names Liang
`datasetcard_info.parquet` (32,111 cards, 2023-10-01). It is not present in this
repo or on the machine this draft was written on, so its repo revision and row
content hash — the A9.1 artifact pin — are unrecorded. **An unpinned corpus
cannot be pre-registered against:** "32,111 cards" is not a corpus, it is a
description of one, and any figure computed later would be attributable to a
snapshot nobody can retrieve.

**(b) The sample frame's numbers are uncomputed.** Strata sizes by task category,
word-count band and A3 detector outcome; the eval-bearing population; the
no-eval stratum for validating negative calls; and the DIV-07 opportunity count
all come from the corpus. `frame.py` computes them and writes `frame.json`.

**To freeze:** obtain the corpus, run `python studies/taxonomy-validation/frame.py
--corpus <path>`, commit `frame.json` with the pin, change this file's status
line, and hash the directory. Only then may a judge be invoked.

Recording the gap rather than drafting around it: a pre-registration with a
placeholder frame is a plan wearing a pre-registration's name, and the whole
value of the artifact is that it was fixed before the result was visible.
