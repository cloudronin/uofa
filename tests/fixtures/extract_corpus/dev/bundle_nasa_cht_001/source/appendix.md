# Appendix A — Validation Data Summary and Uncertainty Budget

**Supporting Document for TFS-CHT-2024-0047 Rev B**

---

## A.1 Rig 7B Measurement Uncertainty Breakdown

The IR thermometry system used in Rig 7B (FLIR X8500sc, calibrated against a blackbody reference source at 400°C, 600°C, and 800°C) contributes the following uncertainty components to the wall temperature measurement:

| Source | Contribution (°C, 95% CI) |
|---|---|
| Calibration reference uncertainty | ±0.8 |
| Emissivity correction (ε = 0.92 ± 0.02) | ±1.4 |
| Spatial resolution / pixel averaging | ±0.6 |
| Ambient reflection correction | ±1.1 |
| **Combined (RSS)** | **±2.1** |

The reported ±2.5°C figure in the main report includes an additional ±1.3°C allowance for surface preparation variability (paint thickness non-uniformity), applied as a uniform additive per the calibration procedure.

---

## A.2 PCE Convergence Verification

The polynomial chaos expansion was verified for convergence by comparing the PCE-predicted mean and variance of peak metal temperature against a 500-sample Monte Carlo (MC) reference. Results:

| Statistic | PCE | MC (500 samples) | Difference |
|---|---|---|---|
| Mean peak T_metal (°C) | 1,147.3 | 1,148.1 | 0.8°C |
| Std. dev. (°C) | 10.9 | 11.2 | 0.3°C |
| 95th percentile (°C) | 1,168.6 | 1,169.4 | 0.8°C |

The PCE and MC results are in close agreement, confirming that the third-order expansion is adequate for this application.

---

## A.3 Mesh Quality Metrics — Production Mesh (22.1 M Cells)

| Metric | Internal Fluid | External Fluid | Solid |
|---|---|---|---|
| Max skewness | 0.71 | 0.68 | 0.41 |
| Mean skewness | 0.18 | 0.21 | 0.09 |
| Min orthogonal quality | 0.31 | 0.34 | 0.62 |
| Mean orthogonal quality | 0.82 | 0.79 | 0.91 |
| Cells with skewness > 0.85 | 0 | 0 | 0 |

All mesh quality metrics are within the thresholds specified in the simulation plan (max skewness < 0.85, min orthogonal quality > 0.25). No negative-volume cells were detected.

---

## A.4 Validation Comparison Plots — Rig 7B Nominal Condition

*[Figure A.4-1: Contour map of measured (IR) vs. predicted outer wall temperature, pressure side, Re = 40,000, q″ = 10 kW/m². Color scale 350–650°C. Predicted contours overlaid as isolines.]*

*[Figure A.4-2: Scatter plot of predicted vs. measured temperature at 847 surface locations. Dashed lines indicate ±8°C and ±15°C bounds. 91% of points fall within ±8°C band.]*

*[Figure A.4-3: Spanwise-averaged Nusselt number distribution along chord, passes 1–5. Comparison between realizable k-ε, SST k-ω, and Rig 7B measurements with error bars.]*

Note: Figures are embedded in the simulation database visualization report (SIMDB-VIS-2024-0047). Hard copies are available on request from the data steward.

---

## A.5 Independent Review Finding Summary

| Finding ID | Description | Severity | Resolution |
|---|---|---|---|
| IR-001 | Turbulence length scale at coolant inlet not documented in simulation plan | Minor | Added to simulation plan Rev C; sensitivity run confirmed <1% effect on QoIs |
| IR-002 | Emissivity value used in IR correction not traceable to calibration record | Minor | Calibration record CAL-IR-2023-04 retrieved and linked in SIMDB |
| IR-003 | GCI calculation used arithmetic mean refinement ratio rather than volume-based ratio | Minor | Recalculated; GCI values changed by <0.2%; table in main report updated |

All findings closed. No major or critical findings were identified.

---

## A.6 Software and Hardware Configuration Record

| Item | Details |
|---|---|
| Solver | ANSYS Fluent 2023 R2 (build 23.2.0.22720) |
| OS | Red Hat Enterprise Linux 8.7 |
| MPI | OpenMPI 4.1.4 |
| Hardware | 12 × Dell PowerEdge R750xa, 2× Intel Xeon Platinum 8380 (40c), 512 GB RAM |
| Interconnect | HDR-100 InfiniBand |
| Typical wall-clock time (production case) | 14.2 hours (384 cores, 500 iterations) |
| Post-processing | Python 3.11, NumPy 1.25, Matplotlib 3.7; scripts in `/postproc/` directory |

---

## A.7 Boundary Condition Summary — Production Cases

| Boundary | Type | Value / Source |
|---|---|---|
| Coolant inlet (all passes) | Mass flow inlet | 0.0312 kg/s total; T_t = 823 K; Tu = 5%, L = D_h |
| Hot-gas inlet | Pressure inlet | P_t = 18.3 bar; T_t = 1,748 K; profiles from AER-HGP-2023-112 |
| Coolant exit (pass 5) | Pressure outlet | P_static = 16.1 bar |
| Film hole exits | Interior faces (coupled to external) | Computed by solver |
| Blade tip | Adiabatic wall | — |
| Blade root (platform) | Specified temperature | 1,050 K (from platform thermal model) |
| External periodic boundaries | Rotational periodicity | Pitch angle 18.0° |

---

*End of Appendix A*
