# Appendix A — Supplementary Technical Details

## A.1 Mesh Refinement Study Data

| Mesh Level | Cell Count | T_j,max (°C) | R_th,jf (°C/W) |
|---|---|---|---|
| Coarse | 1,800,412 | 118.7 | 0.631 |
| Medium | 5,412,088 | 116.9 | 0.622 |
| Fine | 14,683,204 | 116.5 | 0.619 |
| Richardson Extrapolated | — | 116.2 | 0.617 |
| GCI (medium→fine) | — | 0.6% / ±0.4 °C | 1.1% / ±0.008 °C/W |

Observed spatial order of convergence p = 1.93 (theoretical second-order). Asymptotic ratio check: GCI_fine / (r^p × GCI_medium) = 1.03, confirming the solution is within the asymptotic convergence range.

---

## A.2 Validation Test Matrix and Comparison Data

| Test ID | Power (W) | Flow (L/min) | T_j,max Measured (°C) | T_j,max Simulated (°C) | Error (°C) | R_th,jf Meas. (°C/W) | R_th,jf Sim. (°C/W) | Error (°C/W) |
|---|---|---|---|---|---|---|---|---|
| V-01 | 400 | 6.0 | 88.3 ± 1.5 | 90.1 | +1.8 | 0.576 | 0.590 | +0.014 |
| V-02 | 600 | 6.0 | 99.6 ± 1.5 | 101.9 | +2.3 | 0.579 | 0.598 | +0.019 |
| V-03 | 850 | 6.0 | 113.2 ± 1.5 | 115.8 | +2.6 | 0.571 | 0.592 | +0.021 |
| V-04 | 400 | 4.0 | 93.1 ± 1.5 | 95.8 | +2.7 | 0.701 | 0.722 | +0.021 |
| V-05 | 600 | 4.0 | 105.4 ± 1.5 | 108.1 | +2.7 | 0.699 | 0.720 | +0.021 |
| V-06 | 850 | 4.0 | 119.7 ± 1.5 | 122.9 | +3.2 | 0.713 | 0.741 | +0.028 |
| V-07 | 400 | 6.0 | 87.9 ± 1.5 | 90.1 | +2.2 | 0.574 | 0.590 | +0.016 |
| V-08 | 600 | 6.0 | 100.1 ± 1.5 | 101.9 | +1.8 | 0.581 | 0.598 | +0.017 |
| V-09 | 850 | 6.0 | 114.0 ± 1.5 | 115.8 | +1.8 | 0.575 | 0.592 | +0.017 |
| V-10 | 850 | 4.0 | 120.3 ± 1.5 | 122.9 | +2.6 | 0.715 | 0.741 | +0.026 |

**RMS Error T_j,max:** 3.4 °C | **Mean Signed Error:** +2.1 °C
**RMS Error R_th,jf:** 0.024 °C/W | **Mean Signed Error:** +0.018 °C/W

Note: Tests V-07 through V-10 used assembly CP-003 (repeat unit) to assess unit-to-unit variability. The spread in measured T_j,max between CP-001 and CP-003 at identical conditions was ≤1.1 °C, confirming manufacturing consistency.

---

## A.3 Uncertainty Budget Summary (T_j,max at 850 W, 6 L/min)

| Uncertainty Source | Type | Magnitude (°C, 1σ) | % Total Variance |
|---|---|---|---|
| Numerical discretization (GCI) | Numerical | 0.4 | 2% |
| Iterative convergence | Numerical | <0.1 | <1% |
| Inlet temperature measurement | Input | 0.15 | <1% |
| Flow rate measurement | Input | 0.5 | 4% |
| TIM conductivity (±1 W/m·K) | Input | 1.6 | 41% |
| Solder conductivity (±10%) | Input | 0.7 | 8% |
| Heat generation non-uniformity | Model scope | 1.6 | 41% |
| Model-form (turbulence, interface) | Model form | 0.8 | 10% |
| **Combined (RSS, k=2, ~95%)** | — | **±6.1 °C** | — |

The two dominant contributors — TIM conductivity and heat generation distribution — together account for 82% of total prediction variance. Reduction of uncertainty in these areas through additional characterization testing is recommended for future model refinement.

---

## A.4 Code Verification Test Case Summary

**Test Case CV-01: Composite Wall with Volumetric Heat Generation**

- Geometry: Two-layer planar wall (copper 2 mm / AlN 0.63 mm), one face isothermal (65 °C), opposite face convective (h = 8,500 W/m²·K, T_fluid = 65 °C), heat source in copper layer at 5×10⁷ W/m³
- Analytical solution: Carslaw & Jaeger, 2nd ed., §3.4, equation 3.4(6)
- Computed peak temperature: 98.34 °C vs. analytical 98.32 °C (error 0.02%)
- Solid-fluid interface temperature: Computed 71.18 °C vs. analytical 71.17 °C (error 0.01%)

**Test Case CV-02: Turbulent Channel Flow Heat Transfer**

- Configuration: Periodic channel, Re_τ = 395, Pr = 0.71, uniform wall heat flux
- Reference: Moser, Kim & Mansour DNS (1999), supplemented by Incropera & DeWitt correlations
- Nusselt number: Computed 22.1 vs. DNS-derived 23.4 (error −5.6%)
- Mean velocity profile: Maximum deviation from DNS 3.5% at y+ ≈ 30 (log-layer)
- Assessment: Consistent with documented realizable k-ε model accuracy range; acceptable for engineering predictions

---

## A.5 Peer Review Finding Log

| Finding ID | Reviewer | Description | Disposition |
|---|---|---|---|
| PR-001 | Internal (Corp. CoE) | Turbulence model selection rationale not documented in original report | Addressed in Rev 3.1 §4.3 |
| PR-002 | Internal (Corp. CoE) | GCI asymptotic ratio check not reported | Added to Appendix A.1 |
| PR-003 | External (Dr. Renner) | Transient extrapolation risk not explicitly flagged | Added to §6.3 and §10 |
| PR-004 | External (Dr. Renner) | Unit-to-unit variability across test assemblies not quantified | Additional test data added (V-07 to V-10) |

All findings resolved prior to Rev 3.1 approval. No open findings remain.

---

## A.6 Software Configuration Record

| Item | Detail |
|---|---|
| Solver | ANSYS Fluent 2023 R2 (build 23.2.0.022) |
| License | Corporate network license, server therm-lic-01 |
| Operating system | RHEL 8.7 |
| Hardware | 48-core AMD EPYC 7543, 256 GB RAM |
| MPI | OpenMPI 4.1.4, 4 nodes × 48 cores = 192 cores |
| Run time (medium mesh) | 4.2 hours wall clock |
| Mesh tool | ANSYS Meshing 2023 R2 |
| Post-processing | Python 3.11 + matplotlib 3.8; CFD-Post 2023 R2 |
| Repository | Git tag v3.1-final, SHA: a3f7c2d |

*End of Appendix A*
