# Experiment A — second split (AirfRANS AoA extrapolation)

The **non-chosen** split, reported alongside Reynolds for completeness and to
resolve one open question from selection. Same treatment as the Reynolds result;
**weaker, as expected** — AoA was the less clean separator (selection: 1.6× vs
Reynolds' 2.2×), and that weaker number on the non-chosen split is the honest
outcome, not a problem.

## Headline (full corpus, vs RANS ground truth)

| coefficient | fired median | unfired median | **fired ÷ unfired** | IQR overlap |
|---|---|---|---|---|
| Cl | 0.0614 | 0.0512 | **1.2×** | heavy ([0.032, 0.129] vs [0.025, 0.106]) |
| Cd | 0.0223 | 0.0137 | **1.6×** | heavy ([0.011, 0.042] vs [0.006, 0.023]) |

- Group sizes: **196 fired**, **161 not-fired** (357 cases; more balanced than Reynolds' 498/99).
- The Cd ratio (1.6×) matches the selection-pass proxy; the Cl ratio (1.2×) is
  marginal. **The IQRs overlap heavily** — on AoA the envelope weakener separates
  high- from low-error cases far more weakly than on Reynolds. Do not oversell it.
- Full distributions in [`gap_report.txt`](gap_report.txt).

## Resolved: the low-AoA asymmetry is real, NOT a thickness confound

Selection showed AoA degradation concentrating on the **low**-AoA side, opposite
the synthetic generator's stall assumption. The full solver-truth run confirms it,
and the thickness slice ([`asymmetry_slice.txt`](asymmetry_slice.txt)) settles
*why*:

- **low-AoA fired** (n=111): median Cd error **0.0288** — higher than
  **high-AoA fired** (n=85): **0.0180**. The low side is genuinely worse.
- **It is not the thickness confound.** Slicing the low-AoA fired cases by thickness:

  | thickness band | n | median Cd error |
  |---|---|---|
  | thin (5.2–9.7%) | 37 | **0.0401** |
  | mid (9.8–15%) | 37 | 0.0213 |
  | thick (15–20%) | 37 | 0.0198 |

  Error **rises as airfoils get thinner**, not thicker. Spearman(thickness, err_cd)
  = **−0.32**; dropping the *thickest* third *raises* the median (0.0288 → 0.0320)
  rather than collapsing it; thin (<10%) median 0.0386 vs thick (≥15%) 0.0198.
  The elevation is **broad across the low-AoA cases and concentrated on thin
  airfoils** — the inverse of the thick-outlier confound we were guarding against.

So the finding stands as a real contradiction of the stall assumption: on this
data the surrogate degrades most at **negative AoA on thin airfoils**, not toward
high-AoA stall. A plausible (un-verified) mechanism is leading-edge separation on
thin sections at negative incidence being harder to emulate; we report the
measured asymmetry, not the mechanism.

## Scope & method

Identical to the Reynolds result (see `../reynolds_extrapolation/README.md`):
honest in-envelope-only surrogate, declared envelope = train-split bounds
(`aoa ∈ [−2.48°, 12.45°]`, the documented band; Reynolds left wide so firing is
AoA-driven), W-SURR-03 fired-flag read from the real `uofa check`, RANS as the
sole arbiter, no LLM, no verdict.

## Files

| file | what |
|---|---|
| `per_case.csv` | 357-case table incl. `g1` (camber) + `g2` (thickness) for the slice |
| `gap_report.txt` | rendered error-gap report |
| `asymmetry_slice.txt` | low/high-AoA fired sliced by thickness tercile + confound diagnostic |
| `declared_envelope.json` | the AoA-split declared envelope |

Reproduce: `make airfrans-train AIRFRANS_TASK=aoa && make airfrans-corpus AIRFRANS_TASK=aoa && make airfrans-gap`, then
`python -m harness slice --table dev/build/airfrans-exp/per_case.jsonl --param aoa`.
Data: AirfRANS, arXiv:2212.07564, ODbL (raw data never committed).
