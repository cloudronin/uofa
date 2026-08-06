# Conjugate Thermofluid Analysis Credibility Report
Project: Orion-Derived Avionics Cold Plate (OACP)  
Model/Toolchain: ANSYS Fluent 2023R2 + in-house Python pre/post, Git-LFS for case control  
Date: 2026‑08‑05  
Prepared by: Thermal-Fluid Modeling Group, Structures & Thermal Branch

## Executive Summary

We assessed the trustworthiness of a conjugate thermal-fluid model used to size and margin the Orion-derived avionics cold plate (OACP) for the Gateway suite refresh. The model predicts temperature fields in the aluminum cold plate and pressure/flow behavior in its internal serpentine channels under single-phase forced convection with polyalphaolefin (PAO-6) coolant. The intent is to support two mission decisions: (1) confirm avionics junction temperatures remain below 85 C under worst-case load (500 W distributed, 60 C coolant inlet) and (2) allocate pressure-drop budget within the vehicle thermal loop.

The analysis integrates convective heat transfer and solid conduction, includes interfacial thermal resistance from the TIM layer, and covers the operating envelope 0.015–0.035 kg/s flow, 20–60 C fluid inlet temperature, and 250–500 W heat load. Hardware testing on a bench article was completed at five points across this range. The CHT predictions match measured plate-average temperature within 1.4% and pressure drop within 4.2% across the matrix. Grid sensitivity was controlled to under 3% on the primary metrics, with y+ below 1 along coolant-wetted walls and second-order spatial schemes used throughout. A parameter study and Monte Carlo propagation indicate a combined 95% confidence interval of ±3.1 C on hottest node temperature and ±1.2 kPa on pressure drop at the worst thermal case.

The toolchain is documented and under configuration control, case setups are reproducible via a Git tag and a containerized environment, and inputs (geometry, loads, properties) are traceable to released drawings, test data, or vendor-standard references. A separate team (not the primary analysts) conducted model-to-test comparison and reviewed assumptions; they did not develop or run the simulations. The approach and settings have been applied on three past flight units of similar topology with comparable accuracy.

Key limitations include: no fouling or aging of TIM included; roughness modeled as an equivalent sand grain fit to profilometry but uniform along channels; radiation ignored given limited view factors and measured deltas <0.5 C in a separate sensitivity; and cavitation excluded by design (NPSH margin verified by systems team). Applicability is limited to single-phase, Newtonian coolant (PAO-6) in the noted range. Outside this envelope, results should be considered trends only.

Overall, the evidence base is sufficient for decision use in preliminary and critical design reviews, with caveats noted above.

## 1. Background and Intended Use

The OACP removes heat from a cluster of avionics cards via conduction through an Al6061-T6 base into an internal coolant channel network connected to the vehicle closed-loop PAO system. Design decisions tied to this model:

- Ensure worst-case board-junction temperatures remain below 85 C with 10 C margin at PDR and 5 C at CDR.
- Verify pressure-drop allocation does not exceed 24 kPa at the cold plate at nominal flow (0.025 kg/s), preserving margin for the pump and manifold losses.
- Evaluate impact of TIM selection and contact pressure on hotspot temperature.

The CHT model is used to:
- Produce temperature maps for mechanical-TCS integration and to inform sensor placement.
- Size channel cross-section and serpentine pitch.
- Provide uncertainty-aware predictions for board thermal-vacuum test planning.

Decisions do not include launch loads, micro-meteoroid impact, or two-phase cooling alternatives; these are outside scope.

## 2. Model Formulation and Physics Coverage

- Geometry: CAD-derived cold plate model with 12.7 mm thick Al6061 base, 1.2 mm-deep serpentine channels (width 2.0 mm), inlet/outlet manifolds, and TIM + card footprints abstracted as distributed heat sources matching measured power maps.
- Physics: Steady-state single-phase turbulent flow coupled to conduction. Radiation neglected (validated separately). No buoyancy effects considered; flow is pump-driven with Re 4200–9800. Material properties temperature-dependent.
- Turbulence: k-omega SST with low-Re near-wall treatment; y+ ≤ 1 across walls. Transitional modeling assessed and not used; tests show fully turbulent regime for all runs.
- Interfaces: Thermal contact resistance modeled as an areal conductance; nominal 7,500 W/m²-K with uncertainty ±2,000 W/m²-K informed by coupon tests with the chosen TIM at 0.3 MPa clamping pressure.
- Roughness: Equivalent sand-grain roughness k_s = 10 µm based on stylus profilometry of 3 machined channels; modeled uniformly.
- Fluids: PAO-6 with temperature-dependent density, viscosity, k, and Cp from MIL-PRF-87252C; properties cross-checked with vendor data (ExxonMobil SHC Aware) within 1–3%.

Assumptions and simplifications:
- No heat generation within the aluminum except card loads; conduction is linear with k(Τ).
- Serpentine bend losses captured by RANS; secondary flows resolved adequately per grid independence results.
- TIM compression uniform over each card area; spatial variation below measurement detection in assembly torque tests.

## 3. Numerical Setup and Health Checks

- Solver: ANSYS Fluent 2023R2, double precision, steady RANS with coupled pressure-velocity scheme, second-order upwind for momentum and energy, pseudo-transient stabilization ramped down in the final 500 iterations.
- Mesh: Poly-hexcore with body-fitted prism layers (12 layers, growth 1.2) in channels; conformal solid-fluid interface. Three grids used: 1.2M/2.5M/5.1M control volumes. Minimum prism first layer thickness set to achieve y+ < 1 at highest Re case.
- Convergence: Energy residuals <1e-8, continuity and momentum <1e-5; monitoring points on outlet temperature and a hotspot node leveled with <0.05% drift over final 1,000 iterations. Mass imbalance <0.02%.
- Discretization effects: Observed order p ≈ 1.95–2.1 on main outputs; Grid Convergence Index (95% confidence) at 2.5M grid is 2.5% for max card-surface temperature and 1.8% for Δp at nominal case; see Appendix A.
- Temporal checks: A transient run with physical time-stepping (Δt = 0.01 s) to reach steady-state produced final temps within 0.3 C of the steady solution, confirming no oscillatory behavior.
- Numerical code checks: Four benchmark tests performed separate from the OACP model: (1) 1D slab conduction against analytic solution (<0.1% error), (2) developing laminar channel heat transfer (Graetz problem) Nusselt within 0.8%, (3) turbulent channel flow friction factor versus Blasius correlation (within 2.2% for matched Re), and (4) conjugate circular pipe with constant heat flux compared against published DNS-based correlations (Choi, 2019) within 3.1%.

## 4. Inputs, Boundary Conditions, and Data Stewardship

- Geometry sourced from released drawing OACP-ASM-2104 Rev C; as-built dimensions for channel width and depth averaged from CMM on the test article (mean width 2.004 mm, σ = 0.006 mm; mean depth 1.198 mm, σ = 0.009 mm). CFD uses as-built dims for validation runs and nominal dims for design sweeps.
- Heat loads from EM-Board power logs; worst-case 500 W distributed across six cards with nonuniform map (peak patch 140 W over 35 cm²). Load map uncertainty ±5% per power supply calibration.
- Coolant inlet boundary: mass flow specified; thermal condition is inlet temperature. Measured swirl and turbulence intensity at manifold entrance are low; CFD used turbulence intensity 5%. Outlet at fixed static pressure to match test-stand backpressure.
- Property tables: PAO-6 T-dependent properties computed via polynomial fits; coefficients stored in the repository with source citations; aluminum thermal conductivity from ASM Handbook with 2% increase to match specific batch certificate. TIM conductance from lab compression tests on the lot used.
- Screening and QA: All input tables include units, ranges, and a script that checks range violations; on load cases outside the defined envelope, the preprocessor halts with an error. A review checklist was executed before releasing runs to the cluster.

Data management and traceability:
- Case files, property tables, and post-processing scripts stored under Git-LFS tag oacp-cht-2026.07; SHA 4fa2…a7c8 archived. Run logs auto-generated with solver version, date, mesh hash, and key settings.
- Container image (Apptainer) used for solver consistency across cluster nodes; image digest archived with run records.

## 5. Correlation with Hardware Testing

A bench article representing a single cold plate was tested in thermal-vac conditions using a PAO loop with controlled inlet temperature and flow. Thermocouples (K-type, ±0.2 C after calibration) were placed at 18 points on the card side and 4 points in the channel wall; an IR camera (FLIR A655sc, emissivity-calibrated) provided surface maps. Differential pressure was recorded with a Validyne DP15 sensor (±0.1 kPa).

Test cases:
- Case T1: 0.015 kg/s, 30 C inlet, 250 W load
- Case T2: 0.025 kg/s, 30 C inlet, 500 W load
- Case T3: 0.025 kg/s, 45 C inlet, 500 W load
- Case T4: 0.035 kg/s, 30 C inlet, 500 W load
- Case T5: 0.025 kg/s, 60 C inlet, 500 W load

Comparison results (CFD vs Test):
- Max card-surface temperature: mean absolute deviation 0.9 C; worst point 1.8 C (Case T5).
- Plate-average temperature: within 1.4% over all cases.
- Pressure drop across inlet-to-outlet ports: mean relative error 3.3%; worst 4.2% (Case T4).
- Temperature field shape matches IR pattern; cross-correlation 0.92 averaged.

Validation range: The five points span the design envelope in flow, load, and temperature. Extrapolation beyond these is not supported by test data.

## 6. Uncertainty and Sensitivity

- Input uncertainties characterized as:
  - TIM conductance: normal, μ = 7,500 W/m²-K, σ = 1,000 W/m²-K.
  - Channel dimensions: normal per CMM stats; applied as spatially uniform offsets case-by-case.
  - PAO-6 property fits: uniform ±1.5% on k and Cp; ±2% on μ.
  - Heat map: normal ±5% per patch, correlated within each card.
  - Inlet temperature: normal ±0.2 C; flow rate: normal ±0.5% of reading.
- Uncertainty propagation: Latin Hypercube sampling with N = 200 for Case T5; metamodel-assisted expansion to N = 1,000 using a kriging surrogate trained on 200 points (cross-validated R² = 0.996 for max temperature, 0.992 for Δp). Results:
  - 95% interval on max card-surface temperature: ±3.1 C around the nominal prediction.
  - 95% interval on pressure drop: ±1.2 kPa.
  - Dominant contributors: TIM conductance (48% of variance on temp), channel width (22%), and PAO viscosity (12%); for Δp, channel width (41%) and roughness (27%) dominate.
- Local sensitivities: One-at-a-time perturbations ±5% produce ΔTmax of +2.4 C/-2.2 C for TIM; Δp of +1.9 kPa/-1.8 kPa for channel width.

## 7. Robustness, Stability, and Range of Validity

- Solver robustness: Across 30 design and validation runs, no divergence was observed; residual stagnation resolved by reducing pseudo-transient Courant from 200 to 50 in two cases.
- Discretization robustness: Switching to least-squares cell-based gradient reconstruction altered Tmax by 0.4 C; first-order upwind increased Tmax by 2.9 C and Δp by 3.6%—first-order not used for deliverables.
- Turbulence model sensitivity: Realizable k-ε yielded Tmax within 0.8 C and Δp within 2.1% of SST; SST retained for better near-wall treatment.
- Range of validity: Single-phase, Re 4,000–10,000; Tin 20–60 C; Pinlet > 120 kPa absolute; no flow reversal. Outside this space, confidence decreases; especially for lower Re where transitional effects could matter.

## 8. Toolchain Quality and Configuration Control

- Software pedigree: ANSYS Fluent 2023R2 has passed vendor QA; a NASA software inventory record exists (SW-INV-CHT-2023-14). License and binaries are managed by OCIO; hash-checked nightly.
- Scripts and preprocessors: In-house Python 3.11 utilities (mesh QA, BC assignment, post-processing); unit tests for 82% line coverage; CI via GitHub Actions; code review required for merges.
- Case control: Git-LFS repository stores meshes and case files with descriptive YAML run manifests recording geometry, BCs, solver settings, and post-processing metrics. Run manifests stamped with analyst name and timestamp.
- Reproducibility: A Makefile target rebuilds the case from raw CAD and CSV property tables; two analysts independently reproduced Case T2 within 0.2 C/0.3 kPa of baseline.

## 9. Personnel Competency and Independence

- Analysts: Two primary analysts (9 and 6 years CHT experience) with prior flight program support (Orion ECLSS cold plates, PPE avionics cooling), both trained on SST best practices and uncertainty methods. Training records in SATERN updated 2026-03.
- Reviews: A separate reviewer from the Systems Thermal Panel (not involved in case setup) conducted a red team assessment of assumptions, boundary conditions, and the test correlation. The reviewers did not run the simulations. An external SME from the vendor (channel machining expert) reviewed the roughness assumptions and provided profilometry data.

## 10. Prior Use and Benchmarking

- Method heritage: The same RANS-based CHT approach with SST and similar near-wall resolution was used on three previous avionics plates (ORION-CP-15, ORION-CP-19, PPE-TCS-07). In those efforts, predicted vs. test max-surface temperature RMSE was 1.2–1.9 C and Δp within 5%. Lessons learned on TIM characterization were carried into this project.
- Cross-code check: A subset case (T2) was replicated in STAR-CCM+ 2022.3 by a partner team; Tmax differed by 0.6 C and Δp by 1.1 kPa after matching near-wall treatment, bolstering confidence in solver-independence of the result.

## 11. Documentation and Run Records

All runs are documented with:
- Pre-run checklist completion (inputs in range, units checks, mesh quality metrics: skewness <0.92, non-orthogonality <35 deg).
- Solver settings snapshot and final residual plots stored as PNG.
- Post-processed scalar outputs (Tmax, Tavg, Δp) with percent differences to adjacent grid; automatically published to the internal dashboard.
- Validation comparison plots overlaying CFD and test data by sensor location.

A full package is archived under OACP-CHT-VV-2026, including this report, appendices, and a readme for re-running validation cases.

## 12. Limitations and Caveats

- TIM aging, pump-induced temperature ripple, and particulate fouling are not modeled; these could increase Tmax by several degrees over mission life. Program plans include aging tests to refine TIM conductance distribution for FM.
- Radiation is small in this geometry but nonzero; a sensitivity run with a simple gray-diffuse model changed Tmax by ≤0.3 C. Detailed radiative coupling to adjacent hardware is outside current scope.
- Roughness is uniform in the model; localized tool marks could cause higher local shear and minor Δp increases. Current profilometry suggests this is bounded by the uncertainty budget.
- Extrapolation beyond Re < 3,500 (off-nominal low-flow contingency) may require transitional modeling; current model may overpredict heat transfer slightly in that regime.
- Validation data are from a bench article; minor differences from the flight build (fitting geometry) exist but are not expected to change internal flow significantly.

## 13. Summary Assessment

The CHT model for OACP is built on a transparent and reproducible workflow, includes the relevant physics for the intended use, and shows strong correlation against targeted hardware tests spanning the design space. Numerical error is bounded via mesh studies, and uncertainties from key inputs are propagated to decision metrics. The team and processes meet expectations for rigor, and independent review, while internal, provides a separate check on conclusions. The model’s applicability limits are stated, and the main sources of residual uncertainty are understood and, where feasible, quantified.

Recommendations:
- Proceed to use the model for PDR/CDR decisions with the uncertainty bands indicated.
- Prior to flight certification, incorporate results from planned TIM aging tests and update the uncertainty distributions.
- Maintain the current configuration control and run-record practices; extend cross-code checks to one additional validation case if resources permit.

---

### Appendix A. Grid and Numerical Details (excerpt)

- Grids:
  - G1: 1.2M cells; min wall-normal Δy = 9 µm; y+ up to 1.6 locally near bends.
  - G2: 2.5M cells; min Δy = 6 µm; y+ ≤ 1.0 everywhere.
  - G3: 5.1M cells; min Δy = 4 µm; y+ ≤ 0.6.
- Observed orders:
  - Tmax: p = 2.03 (G1→G3); Richardson-extrapolated limit 60.1 C at Case T2; G2 result 60.6 C; GCI95% = 2.5%.
  - Δp: p = 1.98; extrapolated 18.1 kPa; G2 result 18.4 kPa; GCI95% = 1.8%.
- Residual trends: Energy residual dropped steadily to 7e-9; oscillations damped by pseudo-transient switch to 50 and under-relaxation 0.7 for k and ω near convergence.

### Appendix B. Validation Data Coverage

- Flow: 0.015, 0.025, 0.035 kg/s—covers low, nominal, high ends.
- Tin: 30, 45, 60 C—covers full temperature span.
- Load: 250, 500 W—covers nominal and worst.
- Instrumentation: 18 thermocouples on card side (grid across hotspots), 4 at channel wall; a 320x240 IR map at 5 Hz; DP and flow measured continuously.

### Appendix C. Assumption Review Log (excerpt)

- Single-phase Newtonian flow: Verified against cavitation criterion and NPSH; program holds ≥ 40 kPa absolute margin at pump inlet over all cases.
- Radiation neglected: Separate quick-look run with ε = 0.85, view to ambient at 30 C altered Tmax by <0.3 C.
- Uniform TIM compression: Assembly torque calibration shows ±8% variation in pressure, equivalent to ±600 W/m²-K conductance; captured in the uncertainty model.

### Appendix D. Configuration and Reproducibility

- Repository: git@int.nasa.gov:tfs/oacp-cht.git, tag oacp-cht-2026.07, SHA 4fa2d9c…a7c8.
- Container: ghcr.io/tfs/ansys-fluent:2023R2-apptainer, digest sha256:9d…f3.
- Reproduction trial: Analyst B followed README; rebuilt Case T2 in 6.4 hours walltime on 16 cores; obtained Tmax 60.7 C (baseline 60.6 C) and Δp 18.5 kPa (baseline 18.4 kPa).

### Appendix E. Credentials

- Analyst A: MSME, 9 yrs; courses in turbulence modeling, UQ; lead on PPE-TCS-07.
- Analyst B: MSME, 6 yrs; focus on electronics cooling; Ansys Certified Professional.
- Reviewer: PhD, 15 yrs in spacecraft thermal; authored internal guide on CHT best practices.

### Appendix F. Reference Data

- MIL-PRF-87252C: PAO-6 properties.
- ASM Handbook Vol 2: Aluminum properties.
- Choi, H., 2019: Conjugate heat transfer in turbulent pipe flow—DNS-based correlations.

End of report.
