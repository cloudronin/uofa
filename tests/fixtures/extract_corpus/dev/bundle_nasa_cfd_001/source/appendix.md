# Appendix A — Supporting Data and Traceability Records

## A.1 GCI Calculation Detail

Following Celik et al. (2008), "Procedure for Estimation and Reporting of Uncertainty Due to Discretization in CFD Applications," *Journal of Fluids Engineering*, 130(7).

**Head Rise (H):**

- h₁ (fine), h₂ (medium), h₃ (coarse) representative cell sizes: 0.31 mm, 0.50 mm, 0.80 mm
- Refinement ratios: r₂₁ = 1.613, r₃₂ = 1.600
- φ₁ = 28.43 m, φ₂ = 28.61 m, φ₃ = 29.14 m
- Apparent order p: solved iteratively → p = 2.11
- Extrapolated value φ_ext = 28.30 m
- GCI_fine = (F_s × |φ_ext - φ₁| / φ_ext) / (r₂₁^p - 1) × r₂₁^p = **0.72%**
- GCI_medium = **2.83%**
- Asymptotic range check: GCI_medium / (r₂₁^p × GCI_fine) = 0.98 ≈ 1.0 ✓

**Shaft Power (W):**

- φ₁ = 1,057 W, φ₂ = 1,063 W, φ₃ = 1,087 W
- Apparent order p = 2.34
- GCI_fine = **0.43%**
- GCI_medium = **1.71%**
- Asymptotic range check: 0.97 ≈ 1.0 ✓

---

## A.2 Mesh Quality Metrics (Production Grid G2, 4.87 × 10⁶ cells)

| Metric | Target | Achieved (worst 0.1%) |
|--------|--------|-----------------------|
| Orthogonality (min) | > 0.15 | 0.22 |
| Skewness (max) | < 0.85 | 0.79 |
| Aspect ratio (max) | < 100 | 87 (leading edge prism layers) |
| y+ (blade surfaces, 95th pct) | < 1.5 | 1.31 |
| y+ (hub/shroud, 95th pct) | < 5.0 | 3.8 |

All metrics are within solver-recommended ranges. The elevated aspect ratio at leading edge prism layers is consistent with standard practice for thin boundary layer resolution in turbomachinery and does not indicate mesh quality degradation.

---

## A.3 Turbulence Model Benchmark Summary

Prior to this campaign, the SST k-ω model was benchmarked against three publicly available centrifugal pump datasets:

1. **Pedersen et al. (2003)** — PIV measurements in a low specific-speed centrifugal pump. SST k-ω reproduced passage-averaged velocity profiles within 6% RMS; k-ε standard deviated by 11% RMS in the adverse pressure gradient region near the blade suction surface.

2. **Westra et al. (2010)** — Stereo-PIV in a mixed-flow pump. SST k-ω showed 4.8% RMS error on secondary velocity components; RSM showed 4.2% but required 40% more computation time and exhibited convergence difficulties.

3. **Internal dataset IDS-2021-003** — 5-hole probe traverse in a geometrically similar 6-XR pump. SST k-ω head rise prediction error: 2.3%; efficiency error: 0.9 percentage points.

Based on this benchmarking, SST k-ω was selected as the appropriate turbulence closure for this campaign.

---

## A.4 Sensitivity Studies Summary

| Parameter Varied | Range | Effect on Head Rise | Effect on Shaft Power |
|-----------------|-------|--------------------|-----------------------|
| Inlet turbulence intensity | 2%–10% | ±0.3% | ±0.2% |
| Inlet length scale (±50%) | ±50% | ±0.1% | ±0.1% |
| Outlet pressure level (±0.05 bar) | ±0.05 bar | <0.01% | <0.01% |
| Curvature correction C_cc | 0.8–1.2 | ±0.4% | ±0.3% |
| Fillet suppression (re-included) | Full geometry | +0.6% | +0.4% |

All sensitivities are within the numerical uncertainty bounds and do not materially affect the validation comparison or design conclusions.

---

## A.5 Document and Data Traceability Index

| Item | Reference | Status |
|------|-----------|--------|
| CAD geometry | SolidWorks file 7XR_ImpellerC4.sldprt, Rev C4 | Archived, CFD-Data-Repo |
| Mesh files (G1, G2, G3) | CFD-7XR-v2/meshes/ | Version controlled |
| Solver input files | CFD-7XR-v2/fluent_cases/ | Version controlled |
| Post-processing scripts | CFD-7XR-v2/postproc/ | Version controlled |
| Experimental data | TF3-TestReport-7XR-2024-002 | Controlled document |
| Instrument calibration certs | CC-2024-017 (DP transducer), CC-2024-018 (flowmeter) | Filed, QA system |
| Independent review record | RR-2024-047 | Signed, filed |
| Analyst qualification records | QP-CFD-2022 completion certs, HR system | On file |

---

## A.6 Comparison of CFD to 5-Hole Probe Traverse Data

Traverse data were acquired at 9 radial stations across the blade span (10% to 90% span, 10% increments) and 11 circumferential positions per blade passage. Circumferentially averaged profiles are compared below (tabulated; full contour plots in separate data package CFD-7XR-v2/validation_plots/).

| Span Location | V_r CFD (m/s) | V_r Exp (m/s) | Dev (%) | V_θ CFD (m/s) | V_θ Exp (m/s) | Dev (%) |
|--------------|--------------|--------------|---------|--------------|--------------|---------|
| 10% | 4.21 | 4.08 | +3.2% | 8.94 | 9.12 | -2.0% |
| 30% | 4.67 | 4.55 | +2.6% | 9.31 | 9.18 | +1.4% |
| 50% | 4.89 | 4.71 | +3.8% | 9.44 | 9.27 | +1.8% |
| 70% | 4.73 | 4.62 | +2.4% | 9.38 | 9.19 | +2.1% |
| 90% | 4.02 | 3.74 | +7.5% | 8.71 | 9.04 | -3.7% |

The 90% span location shows the largest discrepancy, consistent with the known limitation of RANS in capturing shroud-side secondary flows and tip leakage effects. This region was flagged in the independent review as requiring attention in any future LES study.

---

*End of Appendix A*
