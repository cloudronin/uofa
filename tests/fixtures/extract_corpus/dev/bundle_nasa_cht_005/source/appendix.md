# Appendix A — Supporting Figures and Supplementary Data

## A.1 Wall y+ Distribution (Production Mesh M2)

Contour plots of y+ on the cooled internal surfaces were extracted from the Rev4 solution file. Summary statistics:

- Pressure-side wall (pass 1): mean y+ = 2.8, max y+ = 6.1 (localized at the impingement jet stagnation points — acceptable for enhanced wall treatment)
- Suction-side wall (pass 1): mean y+ = 3.1, max y+ = 5.4
- First 180° bend inner radius: mean y+ = 1.9, max y+ = 3.8
- Pass 2 straight section: mean y+ = 2.6, max y+ = 4.9

No regions of y+ > 30 were identified on the thermally active surfaces. The outer shroud and non-cooled endwalls show y+ values up to 48 in localized corner regions; these surfaces are not part of the primary QoI and the elevated y+ is judged acceptable.

---

## A.2 Residual Convergence History

Convergence monitoring was performed over 8,000 iterations. Scaled residuals for all equations reached the following final values:

| Equation | Final Residual |
|----------|----------------|
| Continuity | 4.2 × 10⁻⁶ |
| x-momentum | 8.7 × 10⁻⁶ |
| y-momentum | 6.1 × 10⁻⁶ |
| z-momentum | 9.3 × 10⁻⁶ |
| Energy (fluid) | 3.1 × 10⁻⁸ |
| Energy (solid) | 2.4 × 10⁻⁸ |
| k (turbulent KE) | 7.8 × 10⁻⁶ |
| ω (specific dissipation) | 8.2 × 10⁻⁶ |

Mass flow imbalance: inlet 0.2847 kg/s, outlet 0.2846 kg/s (imbalance 0.035 g/s, 0.012%). The area-averaged temperature on the pressure-side wall monitoring surface was stable to within ±0.2 K over the final 500 iterations.

---

## A.3 Thermocouple Comparison Detail — LX-5 Rig

The table below provides the full comparison between simulation predictions and LX-5 rig measurements at the 42 thermocouple locations. Measurement uncertainty is ±4 K (k=2) based on the calibration certificate for the rig instrumentation (Type K thermocouples, calibrated against NIST-traceable reference).

*[Full 42-row data table available in supplementary spreadsheet `LX7_CHT_CA_007_TC_Comparison.xlsx` — not reproduced here for brevity]*

Summary: 38/42 predictions within ±4 K. The four outliers (TC-31, TC-33, TC-35, TC-38) are all located in the pass-3 trip-strip region. The maximum discrepancy is TC-35 at +9.2 K (simulation overpredicts). As noted in §5.1, this is attributed to the trip-strip augmentation factor modeling approach.

---

## A.4 GCI Calculation Detail

The GCI calculation followed the procedure of Celik et al. (2008) with a safety factor of 1.25.

For peak metal temperature (T_peak):

- φ₁ (fine, M3): 1082.9 K
- φ₂ (medium, M2): 1087.0 K
- φ₃ (coarse, M1): 1105.4 K
- r₂₁ (refinement ratio M3/M2): 1.37 (based on cube root of cell count ratio)
- r₃₂ (refinement ratio M2/M1): 1.45
- Apparent order p: 2.14
- GCI₂₁ (fine-to-medium): 0.71%
- GCI₃₂ (medium-to-coarse): 3.84%
- Asymptotic range check: GCI₂₁ / (r₂₁ᵖ × GCI₃₂) = 0.97 ≈ 1.0 ✓ (confirms asymptotic convergence)

The M2 mesh result of 1,087 K is used as the production prediction. The GCI-based numerical uncertainty on this value is ±7.7 K (0.71% of 1,087 K).

---

## A.5 Material Property Verification

Thermal conductivity of Rene 80 as implemented in the model (`MAT_R80_TC_v3`) was spot-checked against ASM Handbook Vol. 2 tabulated values at five temperatures:

| Temperature (K) | ASM Value (W/mK) | Model Value (W/mK) | Difference |
|----------------|------------------|--------------------|------------|
| 300 | 10.4 | 10.6 | +1.9% |
| 500 | 12.8 | 13.0 | +1.6% |
| 700 | 15.3 | 15.5 | +1.3% |
| 900 | 18.1 | 18.2 | +0.6% |
| 1100 | 21.4 | 21.2 | −0.9% |

All values within the stated ±2.1% tolerance. The polynomial fit slightly overestimates conductivity at lower temperatures, which would tend to marginally underpredict metal temperature gradients in cooler regions — a conservative direction for the primary QoI.

---

## A.6 Note on Independent Review Scope

Dr. Lindqvist's independent review (conducted 28 February – 8 March 2024) covered the mesh refinement study, the solver verification test case, and the LX-5 data comparison. Her written comments are archived in `LX7-CHT-CA-007-Lindqvist-Review.pdf`.

Dr. Lindqvist noted that the assessment documentation does not address the process by which the simulation team's results are reviewed internally before release, nor does it describe the qualifications or training background of the analysts who built and ran the model. She recommended that this process documentation be compiled and reviewed before the CDR credibility assessment. This recommendation is accepted and is carried as an open action item (Action LX7-CA-007-A01, owner: P. Nakamura, due: CDR-4 weeks).

Dr. Lindqvist also noted that the uncertainty quantification approach (OAT sensitivity) is appropriate for PDR but should be upgraded to a variance-based method (e.g., Sobol indices or polynomial chaos expansion) for CDR, particularly given the nonlinear interaction expected between the hot-gas-side boundary condition and the coolant Reynolds number at off-design conditions.

---

*End of Appendix A*
