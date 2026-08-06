Title: Appendix — Data, Tables, and Additional Evidence for S2 Cold Plate CHT Credibility

A1. Mesh Statistics and Quality

- Coarse mesh:
  - Total cells: 6.9M; min orthogonality 0.21 in sharp elbow, average 0.86.
  - Fluid first-layer y+ distribution (P10/P50/P90): 0.9 / 2.6 / 7.4.
- Medium mesh:
  - Total cells: 12.4M; min orthogonality 0.25, average 0.89.
  - y+: 0.8 / 1.9 / 5.3.
- Fine mesh:
  - Total cells: 23.7M; min orthogonality 0.28, average 0.91.
  - y+: 0.6 / 1.4 / 3.1.

Mesh transition zones near manifold entries were checked for cell skewness < 0.78; no solver instability observed.

A2. Residuals and Imbalances

- Converged steady run (2C, 7.5 L/min, 20 C inlet):
  - Continuity and momentum residuals < 1e-5 by iteration 1423.
  - Energy residual < 1e-8; area-weighted wall heat flux change < 0.01% over last 250 iterations.
  - Net heat in – heat out – dQ/dt = 0.13% of total power.

A3. Manufactured Solution for Solid Conduction

We imposed T(x,y,z) = T0 + A sin(πx/Lx) sin(πy/Ly) sinh(πz/Lz) on a 10x10x10 mm cube with k = 10 W/m-K, volumetric source q derived analytically. Using second-order schemes:

- h = 1.0, 0.5, 0.25 mm grids yield L2 errors 2.9e-3, 7.3e-4, 1.8e-4; observed order ~2.01.

A4. Pressure-Loss Check Case

Straight channel surrogate of 1 m, Dh = 3.7 mm, Re = 1000–10000:
- fRe deviations from Blasius correlation stayed within ±2.2%.
- With three 180-degree bends and two 90-degree elbows: total K minor losses recovering within ±3.8% of Idelchik tabulated estimates.

A5. Experimental Data Excerpts

Steady points (averages of last 300 s):

- 2C, 5.0 L/min, 28 C inlet:
  - Tmax measured 47.3 C (σrep 0.24 C); model 45.2 C; diff −2.1 C.
  - ΔTmax measured 4.8 C; model 4.3 C; diff −0.5 C.
  - Δp measured 22.4 kPa; model 23.0 kPa; diff +0.6 kPa.
- 2.5C, 9.0 L/min, 18 C inlet:
  - Tmax measured 48.7 C; model 48.0 C; diff −0.7 C.
  - ΔTmax measured 3.6 C; model 3.5 C; diff −0.1 C.
  - Δp measured 42.1 kPa; model 43.5 kPa; diff +1.4 kPa.

Transient peak (UDDS-like, 7.5 L/min, 23 C inlet):
- Time of peak: 756.5 s measured vs 756.8 s modeled; amplitude 48.2 vs 47.1 C.

A6. Instrumentation and Calibration Certificates (summary)

- Thermocouples:
  - Batch TC-2026B; calibration date 2026-06-14; corrected offsets applied; residuals vs standard bath < ±0.15 C over 20–60 C.
- RTDs:
  - Class A, Model PR-11; calibration 2026-06-13; expanded uncertainty ±0.11 C.
- Pressure transducer:
  - Model Kistler 4264; deadweight test on 2026-06-15; linearity within 0.18% FS; zero drift < 0.02 kPa over 2 h.

A7. Sensitivity and UQ Details

- Latin Hypercube of 200 samples; sampling seeds recorded in UQ-Runlog-2026-07-18.
- Emulator checks: low-degree polynomial response surface for post hoc Sobol index confirmation matched within 5% of variance attribution.
- Output distributions:
  - Tmax mean 45.8 C, SD 0.42 C; skew 0.31 (right); kurtosis 3.1.
  - Δp mean 31.6 kPa, SD 0.9 kPa.

A8. Independent Reproduction

- Engineer B. Patel reran steady 2C, 7.5 L/min case using provided Docker; reported Tmax 44.44 C vs archived 44.38 C; Δp 32.0 kPa vs 32.4 kPa.
- Differences attributed to minor CPU floating-point library variants; within tolerance.

A9. Change Log for Review Findings

- RFI-CHT-07: Add time-step convergence for transient — addressed 2026-07-19; Δt swept; criterion defined and documented.
- RFI-CHT-09: Confirm y+ in elbows — addressed 2026-07-20; mesh locally refined; updated stats in A1.

A10. Risk Mapping

- Decision metrics and margins:
  - We require ≥ 3 C margin to Tmax limit; worst-case measured-model disagreement is 2.1 C at hot/low-flow point; combined with GCI (0.62 C) still below margin.
  - Pressure drop near pump limit only at 9.0 L/min; model slightly conservative at high Re due to added 0.7 kPa method margin.

A11. Reproducibility Package Contents

- CAD: S2Plate_RevD.step; ModuleAssembly_AsterionRevC.step.
- Meshes: S2_Coarse.msh.h5; S2_Medium.msh.h5; S2_Fine.msh.h5.
- Case files: s2_2C_7p5Lmin_20C.cas.h5; s2_transient_udds_23C.cas.h5.
- Scripts: gen_heat_profile.py; cht_setup.py; post_metrics.py.
- Documentation: runbook_RS-CHT-17.md; validation_matrix.xlsx; testdata/ folder with raw CSVs.

End of Appendix.
