# Experiment A — measured error-gap (AirfRANS Reynolds extrapolation)

The hard number for the surrogate pack: on a real AirfRANS extrapolation split,
cases where the envelope weakener **W-SURR-03 fired** have substantially higher
true surrogate error (vs RANS ground truth) than cases where it did not. The
pack catches *out-of-envelope inadequacy* — a surrogate competent in-envelope
but silently wrong outside it while still returning plausible numbers.

This is a **measurement, not a verdict**. No threshold, no pass/fail. The
engineer decides; the harness reports the gap.

## Headline

| coefficient | fired median | unfired median | **fired ÷ unfired** |
|---|---|---|---|
| Cl | 0.1461 | 0.0722 | **2.0×** |
| Cd | 0.0471 | 0.0215 | **2.2×** |

- Group sizes: **498 fired**, **99 not-fired** (597 evaluation cases).
- **Invisible-danger trap:** 165 / 498 flagged predictions are finite *and* in a
  believable Cl/Cd range, yet their median Cd true error is 0.0148 —
  plausible-looking, measurably wrong.
- Full distributions (median / mean / IQR) are in [`gap_report.txt`](gap_report.txt).

The gap is real and clear at the median; the IQRs overlap, so this is reported
as a measured ~2× median ratio, not a clean separation. That is the honest shape
of the effect.

## Split selection (Step 0) — chosen empirically

Default was **AoA** on physical grounds, but both band-in-the-middle tasks were
measured and **Reynolds was chosen** because its out-of-envelope error is more
uniformly elevated (see [`split_selection.txt`](split_selection.txt)):

| task | out-of-envelope Cd-error elevation (out/in median) |
|---|---|
| **reynolds** (chosen) | **2.2×** |
| aoa | 1.6× |

**Honest asymmetry finding:** on the AoA task, out-of-envelope degradation
concentrated on the **low-AoA side** (median Cd error 0.029, n=111) — *higher*
than the high/stall side (0.018, n=85). That is the **opposite** of the
stall-dominated asymmetry one might assume; the data is the arbiter, and the
full-split numbers are reported with neither side dropped.

## Scope (what this does and does not show)

Measures out-of-envelope inadequacy specifically — accurate in-envelope, silently
wrong outside it. It does **not** measure in-envelope-but-still-bad surrogates;
that is a different check.

## Method (one line per stage)

1. **Surrogate** — a plain sklearn `MLPRegressor` over (Reynolds, AoA, camber,
   thickness) → (Cl, Cd), trained **only** on the in-envelope Reynolds train
   split (3.02–5.02e6), not tuned for extrapolation. The degradation is the
   experiment, not a bug.
2. **Envelope** — declared = the train-split bounds exactly (no test-range
   leakage); see [`declared_envelope.json`](declared_envelope.json).
3. **Per case** — SIP `interrogate` → signed bundle → v2 reader → real
   `uofa check --pack surrogate`; **W-SURR-03 fired?** is read from the
   structured check output, never recomputed. RANS Cl/Cd is the ground-truth
   arbiter; true error = |pred − RANS|.
4. **Gap** — mechanical partition by `w_surr_03_fired`; pure arithmetic.

No LLM anywhere in the harness. RANS is the only arbiter.

## Files

| file | what |
|---|---|
| `per_case.csv` | 597-case table: eval point, fired flag, pred/ref Cl·Cd, true error |
| `error_vs_parameter.csv` | Step-0 error-vs-parameter for both tasks (aoa, reynolds) |
| `declared_envelope.json` | the surrogate's declared train-split envelope |
| `gap_report.txt` | the rendered error-gap report (distributions + plausibility) |
| `split_selection.txt` | the empirical split choice + AoA-asymmetry note |

## Provenance & reproduction

- **Data:** AirfRANS (Bonnet et al.), **arXiv:2212.07564**. Licensed **ODbL-1.0**
  (share-alike). The raw dataset is **never committed** (gitignored, pull-on-demand);
  only this small derived per-case result is checked in, with attribution.
- **Reproduce:**
  ```
  pip install -e '.[interrogate-corpus]'
  make airfrans-pull        # ~9.3 GB ODbL download into UOFA_AIRFRANS_DIR
  make airfrans-select      # Step 0: confirm the split empirically
  make airfrans-train AIRFRANS_TASK=reynolds
  make airfrans-corpus AIRFRANS_TASK=reynolds
  make airfrans-gap
  ```
  Determinism: fixed seeds for the i.i.d. 80/20 train/holdout split and the MLP.
