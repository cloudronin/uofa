# Experiment A — measured error-gap results

Does the surrogate pack's envelope weakener (**W-SURR-03**) actually co-occur with
real surrogate error? Train an honest surrogate on AirfRANS, drive SIP +
`uofa check` over a corpus, and compare true RANS error between cases where
W-SURR-03 **fired** (eval point outside the declared training envelope) and cases
where it didn't. Measurement, not verdict — no threshold, no pass/fail.

## Both extrapolation splits, side by side

| split | fired / unfired | **Cl ratio** | **Cd ratio** | separation |
|---|---|---|---|---|
| **[Reynolds](reynolds_extrapolation/)** (chosen) | 498 / 99 | **2.0×** | **2.2×** | clearer at the median; IQRs still overlap |
| [AoA](aoa_extrapolation/) (second) | 196 / 161 | 1.2× | 1.6× | weak; IQRs overlap heavily |

Fired-case median true error is ~2× the unfired-case error on Reynolds, ~1.2–1.6×
on AoA. **Reynolds is the cleaner separator** — which is exactly why Step 0 chose
it empirically over the AoA default (out-of-envelope Cd-error elevation 2.2× vs
1.6×). The weaker AoA numbers on the non-chosen split are reported honestly, not
oversold; on neither split is this a clean separation (IQRs overlap), it is a
median shift.

## Honest aside settled on AoA

The synthetic generator assumes degradation toward **high-AoA stall**. The real
data says the opposite: out-of-envelope error concentrates on the **low-AoA**
side, and the thickness slice shows it is **broad and worst on thin airfoils**
(Spearman thickness↔error = −0.32), **not** a thick-airfoil outlier confound. See
[`aoa_extrapolation/`](aoa_extrapolation/) for the breakdown. The contradiction of
the synthetic assumption is a genuine finding about the real data, reported as the
numbers show.

## What this does and does not claim

Catches **out-of-envelope inadequacy** — accurate in-envelope, silently wrong
outside it while still returning plausible numbers (165/498 Reynolds, 125/196 AoA
flagged predictions are physically believable yet measurably wrong). Does **not**
measure in-envelope-but-bad surrogates, and W-SURR-03 keys off the *declared*
envelope, so an under-declared envelope reflects the declaration, not reality
(by design — the firewall: the rule checks what's claimed, SIP measures what
happens).

Provenance: AirfRANS, **arXiv:2212.07564**, ODbL-1.0. Raw data is never committed;
the small derived per-case tables here are, with attribution. Reproduce via the
`make airfrans-*` targets.
