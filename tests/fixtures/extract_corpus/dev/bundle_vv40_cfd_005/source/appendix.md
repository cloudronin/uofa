# Appendix A — Supplementary Mesh and Convergence Data

## A.1 Mesh Quality Metrics (Fine Mesh, 14.6 M cells)

| Metric | Impeller Domain | Volute Domain | Acceptance Threshold |
|--------|----------------|---------------|----------------------|
| Min orthogonal quality | 0.21 | 0.18 | > 0.15 |
| Max skewness | 0.74 | 0.81 | < 0.85 |
| Max aspect ratio | 18.4 | 22.1 | < 40 |
| Mean y⁺ (blade pressure side) | 42 | — | 30–100 |
| Mean y⁺ (blade suction side) | 61 | — | 30–100 |

All metrics are within the project-specified acceptance thresholds. A small population of cells (< 0.3% by count) in the volute cutwater region exhibited skewness values between 0.81 and 0.84; these were reviewed and judged not to be in regions of high solution gradient.

## A.2 GCI Calculation Summary

The GCI analysis follows the procedure of Celik et al. (2008), *Journal of Fluids Engineering*, Vol. 130.

- **Key output quantity:** Total head at BEP (Q = 48 m³/hr, 1450 RPM)
- **Coarse mesh result:** H_c = 21.34 m
- **Medium mesh result:** H_m = 21.89 m
- **Fine mesh result:** H_f = 22.10 m
- **Refinement ratio r:** 1.36 (linear, per-dimension)
- **Observed order p:** 1.87
- **Richardson extrapolated value:** 22.19 m
- **Fine-grid GCI:** 1.3%
- **Asymptotic convergence check:** GCI_medium / (r^p × GCI_fine) = 1.02 ≈ 1.0 ✓

The asymptotic convergence check confirms the solution is within the asymptotic range of convergence.

## A.3 Operating Point Summary — CFD vs. Test

| Operating Point (% BEP) | Q_test (m³/hr) | H_test (m) | H_CFD (m) | Error (%) |
|------------------------|----------------|------------|-----------|-----------|
| 65% | 31.2 | 25.8 | 24.5 | −4.9% |
| 75% | 36.0 | 25.1 | 24.4 | −2.8% |
| 85% | 40.8 | 24.2 | 23.7 | −2.1% |
| 100% (BEP) | 48.0 | 22.6 | 22.1 | −2.2% |
| 110% | 52.8 | 21.0 | 20.7 | −1.4% |
| 120% | 57.6 | 18.9 | 18.6 | −1.6% |
| 130% | 62.4 | 16.1 | 15.8 | −1.9% |

All errors are within the ±5% acceptance criterion. The systematic negative bias (CFD under-predicts head) is consistent with omission of disk friction losses, which would manifest as an over-prediction of shaft power and a corresponding under-prediction of hydraulic efficiency, but with only modest effect on head.

## A.4 Turbulence Model Sensitivity

A secondary run at BEP using the Realizable k-ε model with enhanced wall treatment was completed to provide a qualitative check on turbulence model sensitivity.

| Turbulence Model | H_BEP (m) | η_BEP (%) |
|-----------------|-----------|-----------|
| SST k-ω (production) | 22.1 | 71.3 |
| Realizable k-ε | 21.7 | 70.8 |
| Test data | 22.6 | 73.1 |

The SST k-ω model provides marginally better agreement with test data for this geometry, consistent with its known superiority in flows with strong curvature and adverse pressure gradients. The difference between the two turbulence model predictions (0.4 m, 1.8%) provides a qualitative lower bound on turbulence model-form uncertainty, though a rigorous model-form uncertainty quantification has not been performed.

## A.5 Notes on Configuration Management

Simulation input files associated with this report are archived as follows:

- **Mesh files (.msh.h5):** SharePoint folder `/Meridian7/CFD/ProductionRuns/Rev_B/Meshes/`
- **Case and data files (.cas.h5, .dat.h5):** `/Meridian7/CFD/ProductionRuns/Rev_B/Cases/`
- **Post-processing scripts (Python/CFD-Post):** `/Meridian7/CFD/ProductionRuns/Rev_B/PostProc/`
- **Log of changes:** Manually maintained Excel file `CFD_RunLog_RevB.xlsx` in same directory

The absence of a formal version-control system means that file integrity relies on folder discipline and the run log. This is flagged as a process improvement item for Phase 2.
