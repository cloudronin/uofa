# Pre-registration — catalog-lift ablation at n≈60 (`qwen2.5:7b`, raw measures)

Written **2026-05-31, before growing the corpus past 24 and before any n≈60 run**,
so the larger run can falsify the finding instead of being read to fit it. The
n=24 preview and the two-row transcript read motivate it; nothing below is chosen
after seeing n≈60 data (which does not yet exist).

## The finding under test
**Detect-without-meaning is harmful:** giving the model "a weakener fired" *without*
its meaning (`fired_flag`) is worse than giving it nothing (`catalog_ablated`),
because the unexplained flag reads as an *acknowledged risk* and pulls the model
toward `accept-residual-risk` (a dangerous false-OK on block-gold cells). At n=24,
hard-core: `fired_flag` dangerous-error 0.08 vs `catalog_ablated` 0.00.

## Design constraints on the grown corpus (so the test is fair)
- Same discipline: obvious feature points the wrong way; raw measures carry the
  real signal; the hardness invariant (`obvious_posture != gold_posture`) is
  enforced by `build_corpus.hardness_violations()` — nothing easy slips in.
- **Deliberately include confident-once-seen cells** (decisive signal, clear
  posture once spotted), not only maximally-ambiguous ones, so the committed-cell
  base grows rather than the model punting on everything.
- **Target ≥ 20 committed cells** (escalate=False) per condition, so the danger
  and posture reads are not riding on a handful.

## Primary thresholds (decide BEFORE looking)
Let `Δ = dangerous_error(fired_flag) − dangerous_error(catalog_ablated)`, hard-core,
raw measures, n ≥ 50.

- **CONFIRM** the finding if **Δ ≥ +0.04** AND `dangerous_error(fired_flag) > 0`.
- **FALSIFY** (the n=24 inversion was noise) if **|Δ| ≤ 0.02** (they converge).
- **Inconclusive** if `0.02 < Δ < 0.04` → report as inconclusive, do not stand on it.

## Mechanism signature (secondary, must also hold to claim the mechanism)
The harm is "flag → acknowledged-risk → accept-residual-risk," not generic noise.
- **CONFIRM mechanism** if **≥ 50% of `fired_flag`'s dangerous false-OKs are
  `action_class = accept-residual-risk`** (vs other proceed actions).

## The clean read — committed cells, not the aggregate
Escalation is high under every condition, so aggregate danger/posture are
dominated by punts. The load-bearing comparison is on **cells the model committed
on (escalate=False) in BOTH conditions being compared**:
- Report `dangerous_error` and `posture_accuracy` on that paired-committed subset
  for `fired_flag` vs `catalog_ablated` and for `full` vs `catalog_ablated`.
- The finding stands on the committed subset if `fired_flag` committed-cell
  dangerous-error **>** `catalog_ablated` committed-cell dangerous-error, on a
  subset of **≥ 12 paired-committed cells** (else: underpowered, grow more).

## What a clean result looks like either way
- **Confirmed:** Δ ≥ +0.04, the dangerous `fired_flag` cells are majority
  accept-residual-risk, and the committed-subset comparison agrees on ≥12 cells.
  → detect-without-meaning is a real, mechanistic harm; stand on it.
- **Broken:** Δ ≤ 0.02. → the 2-row inversion was noise; the catalog's lift is
  confidence-to-commit only, with no detect-only-is-harmful effect. Learned cheaply.

Recorded read goes in `results/README.md`; raw scorecards in
`results/ablation-raw-n60-*.json`.
