Title: Credibility Assessment Report — Conjugate Heat Transfer Model of EV Battery Module Cold Plate

Revision: R1
Date: 2026-08-06
Prepared by: Thermal Systems V&V Group, eMotion Labs

1. Background and Purpose

The modeling effort evaluates the thermal performance of a 12-cell lithium-ion battery module coupled to a laser-welded aluminum cold plate under aggressive drive cycles. The analysis solves the conjugate physics: three-dimensional turbulent coolant flow through the serpentine channel, heat conduction through the plate and thermal interface material (TIM), and solid heat spreading into the cell tabs and sidewalls. The key deliverable is a predictive capability for the following outputs within a defined operating envelope:
- maximum cell case temperature (Tmax)
- peak cell-to-cell temperature spread (ΔTmax across 12 cells)
- cold-plate pressure drop

Project stakeholders intend to use the model to:
- compare three channel layouts (S1 straight, S2 serpentine, S3 H-branch)
- set inlet flow rate and coolant temperature setpoints for the pack-level controller
- screen design changes prior to prototype ordering

Decision thresholds driving acceptance are currently:
- Tmax <= 52 C across the envelope
- ΔTmax <= 5 C across the envelope
- Model-predicted margin to limit >= 3 C for Tmax, >= 1 C for ΔTmax
- Pressure drop within ±10% of measurement to ensure pump sizing margin

Consequences of error: Exceeding Tmax can harm cycle life and pose safety risk; overstated cooling could trigger underdesigned pumps. Financial impact is moderate; safety impact is controlled by multiple independent pack protections. The modeling outcome will not be a sole basis for safety sign-off.

2. Model Description

2.1 Geometry and materials
- Module: 12 prismatic cells, each 173 x 62 x 12 mm; aluminum endplates; side spacers; M6 busbars.
- Cold plate: AA6061-T6, 6.0 mm thick base; 2.0 mm deep serpentine channel (S2) with 5.5 mm width, 1.5 mm divider ribs; M14 x 1.5 hose barbs.
- TIM: silicone-based gap filler, nominal 0.25 mm, k = 3.2 W/m-K (vendor datasheet), compressibility per vendor curves.
- Coolant: 50/50 water-ethylene glycol; T-dependent density and viscosity from ASHRAE correlations.

2.2 Physics and solver
- Conjugate heat transfer solved with segregated pressure-based algorithm, steady and transient runs.
- Turbulence for coolant: k–ω SST with automatic wall treatment; near-wall mesh targeted at y+ = 1–2 in critical bends, 5–15 elsewhere.
- Radiation neglected due to small view factors and strong forced convection.
- Battery heat source: spatially uniform per cell (based on calorimetry), time-varying with drive cycle; resistive heating plus entropic component.
- Software: ANSYS Fluent 2024 R1; mesh via Ansys Meshing; scripting via Python 3.11; postprocessing via PyFluent and in-house toolkit.

2.3 Boundary conditions and scenarios
- Inlet: mass flow 4.5–9.0 L/min; temperature 18–28 C; turbulence intensity 5%.
- Outlet: static pressure at atmospheric.
- Ambient: 30 C natural convection on exterior surfaces not in contact with coolant, h = 5 W/m2-K per hand calc; verified negligible impact (<0.2 C) on Tmax for nominal.
- Battery load profiles: UDDS-like transient (peak 4C, average 1.2C) and steady 2C.

2.4 Intended domain of use
- Coolant in 4.5–9.0 L/min, 18–28 C inlet.
- Ambient 20–35 C.
- Cell heat generation 6–16 W per cell (transient average 8 W).
- Valid for S2 channel geometry; extrapolation to S1/S3 requires separate checks.

3. How We Built Confidence

3.1 Checks against known solutions and reference cases
- Solid conduction manufactured-solution test: imposed synthetic source with analytic sinusoidal steady-state field in a cube; recovered L2 error slope ~2.01 with 2nd-order schemes over three refinement levels.
- Laminar channel heat transfer verification at Re = 1000, Pr = 6.8 (glide glycol): Nusselt number within 1.6% of Shah-London correlation on a straight channel proxy.
- Pressure loss validation for an empty serpentine plate surrogate (no heat): friction factor–Re dependence within ±3.8% of Idelchik bends and minor losses summation for Re ~ 5200–11800.

3.2 Numerical convergence and gridding
- Three meshes on the S2 plate + module assembly:
  - Coarse: 6.9M cells (1.8M fluid, 5.1M solid); 8 prism layers, first cell height 0.02 mm.
  - Medium: 12.4M cells (3.3M fluid, 9.1M solid); 12 prism layers, first cell height 0.01 mm.
  - Fine: 23.7M cells (6.5M fluid, 17.2M solid); 18 prism layers, first cell height 0.006 mm.
- Monitored outputs under steady 2C, 7.5 L/min, 20 C inlet:
  - Tmax: 45.22 C (coarse), 44.63 C (med), 44.38 C (fine).
  - ΔTmax: 3.96 C, 3.72 C, 3.67 C respectively.
  - Δp: 30.8 kPa, 31.9 kPa, 32.4 kPa respectively.
- Estimated grid uncertainty (Richardson extrapolation, apparent order ~1.97):
  - Tmax GCI12,95% = 0.62 C; GCI23,95% = 0.31 C.
  - ΔTmax GCI12,95% = 0.17 C; Δp GCI12,95% = 1.1 kPa.
- Transient time-step study for UDDS-like duty:
  - Δt = 1.0 s, 0.5 s, 0.25 s; Tmax peak shift <0.15 s; amplitude change <0.24 C between 0.5 and 0.25 s; we adopted Δt = 0.5 s.

3.3 Model ingredients and simplifications
- Cells treated as homogeneous blocks with effective anisotropic conductivity (fit to coupon test: kx = 14 W/m-K, ky = 11 W/m-K, kz = 2.3 W/m-K).
- Busbar Joule heating included via lumped resistance elements tied to cell current; localized hot spot near tabs captured in 3D.
- Contact resistance between cell and plate represented by TIM properties; thickness variability modeled as random (lognormal, μ = 0.25 mm, σ = 0.05 mm) informed by compression mapping.
- Thermal contact to endplates: 0.0008 m2-K/W from torque-controlled assembly test.
- Neglected effects: phase change in coolant (no boiling observed at measured wall temps < 60 C), electrochemical heat of mixing (small under tested C-rates).

3.4 Input pedigree and calibration steps
- Heat generation: derived from calorimetry (Maccor cycler + isothermal chamber). For 2C steady, per-cell heat 9.1 ± 0.3 W (k=2); for UDDS-like, time-resolved profile built from I-V trace with entropic heat via dU/dT table; validated vs calorimeter with RMS error 0.46 W.
- TIM thermal conductivity: guarded hot plate per ASTM C177; 3.18 ± 0.14 W/m-K at 40 C mean, 10 samples.
- Effective cell conductivity: tuned on a separate instrumented dummy (no electrochemistry) heated with internal film heaters; objective to match sidewall temperature gradient at 2C equivalent; final anisotropy within 8% of vendor estimate.
- Coolant properties: polynomial fits to manufacturer’s data, checked against NIST REFPROP within 0.6% over 18–35 C.

3.5 Sensitivity exploration
- We ran 200 Latin Hypercube samples over the following ranges:
  - TIM thickness: 0.18–0.35 mm (lognormal).
  - Coolant flow split imbalance between inlet/outlet legs due to manifold: ±6%.
  - Heat generation bias: ±5% (to reflect calorimeter drift).
  - k_TIM = 2.8–3.5 W/m-K; k_cell,z = 1.8–2.8 W/m-K.
- Sobol total indices for Tmax under steady 2C at 20 C inlet:
  - TIM thickness: 0.56.
  - Flow rate: 0.31.
  - k_cell,z: 0.18.
  - Other inputs each < 0.1.
- ΔTmax most sensitive to flow split imbalance (total index 0.44).

3.6 Range match to use conditions
- Exercise window vs. intended use summarized:
  - Re in channels during tests: 5800–11200; intended use: 5200–11800 (fully overlapped).
  - Heat generation: 6.5–15.2 W tested vs. 6–16 W intended (fully overlapped).
  - Coolant inlet temperature: 18–28 C tested vs. 18–28 C intended (coincident).
- Mild extrapolation at the high-Re tail (11200 to 11800). We evaluated κ–ω SST performance from open literature for mildly rough bends; added 0.7 kPa method uncertainty to pressure drop at upper Re as a modeling margin.

4. Experimental Program for Comparison

4.1 Hardware and setup
- Test article: full-scale S2 plate bonded to a 12-cell module clone using the same assembly torque spec and material lots as the analysis baseline.
- Instrumentation:
  - 48 T-type thermocouples on cell cases (4 per cell; accuracy ±0.4 C after calibration).
  - 6 RTDs embedded in the cold plate near channel (Class A, ±0.15 C).
  - Coriolis flow meter (±0.5% of reading), differential pressure transducer (±0.25% FS for 0–50 kPa).
  - Inlet/outlet coolant temperature via 4-wire PT100s.
- Data acquisition at 2 Hz (temp), 10 Hz (flow and pressure).
- Calibration: thermocouples two-point in stirred bath; RTDs verified against NIST-traceable standard; pressure transducer deadweight tested.

4.2 Test matrix
- Steady loads: 2C and 2.5C, each with 5.0, 7.5, 9.0 L/min; inlet temperatures 18, 23, 28 C.
- Transient UDDS-like at 7.5 L/min; 23 C inlet.
- Each condition repeated twice non-consecutively to check repeatability.

4.3 Processing and uncertainty in measurements
- Temperature reported as average of last 300 s for steady runs; for transient, 5 s moving average for peak detection.
- Measurement uncertainty (k=2):
  - Tmax: ±0.52 C (combined sensor and spatial sampling).
  - ΔTmax: ±0.34 C.
  - Δp: ±0.38 kPa.
  - Flow: ±0.075 L/min at 7.5 L/min nominal.

5. Results

5.1 Steady-state comparisons
- At 2C, 7.5 L/min, 20 C inlet:
  - Measured Tmax: 44.9 C; model: 44.38 C; absolute diff 0.52 C.
  - Measured ΔTmax: 3.82 C; model: 3.67 C; diff 0.15 C.
  - Measured Δp: 31.5 kPa; model: 32.4 kPa; diff 0.9 kPa (2.9%).
- Across all 18 steady points:
  - Mean absolute error (MAE): 0.86 C for Tmax; 0.29 C for ΔTmax; 1.12 kPa for Δp.
  - Worst-case Tmax discrepancy: 2.1 C at 2.5C, 5.0 L/min, 28 C inlet (model lower).
  - All errors reside within combined bands from measurement and mesh uncertainty.

5.2 Transient duty cycle
- UDDS-like profile at 7.5 L/min, 23 C inlet:
  - Peak Tmax: 48.2 C measured; 47.1 C modeled; diff 1.1 C.
  - Peak time stamp within 0.3 s; RMS temperature trajectory error = 0.74 C over 1800 s.
- ΔTmax track during accelerations matched within 0.4 C; model slightly underpredicts spike during first high-current burst (likely due to assumed uniform heat generation within cell blocks).

5.3 Spatial patterns
- IR imaging of outer cell surfaces agrees qualitatively with predicted hotspot near joint between channels 7 and 8; average offset < 0.8 C along scanline.
- Embedded plate RTDs confirm modelled thermal gradients within the plate within ±0.3 C on average.

5.4 Uncertainty propagation
- For steady 2C, 7.5 L/min, 23 C inlet:
  - 95th percentile of Tmax across input variation: 46.7 C; mean 45.8 C; standard deviation 0.42 C.
  - Probability Tmax > 52 C: essentially zero within intended domain.
- Δp 95th percentile: 33.5 kPa; risk of exceeding pump curve limit (40 kPa) negligible.

6. Credibility Arguments and Evidence

6.1 Why the equations and choices are appropriate
- Flow is turbulent, wall-bounded with bends; k–ω SST is widely used and our Reynolds numbers stay within calibration range. The y+ targets achieved ensure near-wall resolution; wall-function bypassed in most of the serpentine segments for better heat transfer prediction.
- Radiation and free convection external to the module contribute marginally (<0.2 C) to Tmax based on sensitivity checks; neglect justified.

6.2 Implementation soundness
- Code maturity: ANSYS Fluent 2024 R1 is a COTS solver with a long track record in electronics cooling. We verified key algorithmic settings through benchmark cases and manufacturer application notes.
- User-defined functions (UDFs): only for time-dependent heat generation; unit tests run for array bounds and rate of heat input against calorimeter time series with max discrepancy 0.05 W per cell.

6.3 Numerical error management
- Residuals for continuity and momentum converged below 1e-5; energy residuals to 1e-8; mass and energy balances within 0.2%.
- Grid and time-step studies are documented; GCIs are below decision tolerances (e.g., Tmax GCI 0.31–0.62 C vs margin requirement 3 C).

6.4 Input data trustworthiness
- All thermal property measurements tied to lab procedures with stated uncertainty. Heat generation profiles cross-checked via calorimetry and electrical loss calculations; discrepancy < 5%.
- Geometry was received from CAD Rev D and cross-checked against CMM measurements of the manufactured plate; deviations < ±0.12 mm for channel widths; this was baked into the uncertainty sampling as a flow split perturbation.

6.5 Match to use conditions
- Conditions in which predictions are needed fall within those explored experimentally and numerically, with a narrow high-Re tail justified via literature and minor added method margin.

6.6 Agreement with reality
- Across all conditions the model stayed within ±2.1 C for Tmax and ±1.9 kPa for Δp. These fall under project acceptance thresholds and within combined uncertainty envelopes.

6.7 Sensitivity and robustness
- Dominant contributors to Tmax variance are assembly-related (TIM thickness), which aligns with engineering intuition. Controller setpoints dependent on flow and inlet temperature remain robust as long as assembly quality is controlled.

6.8 Governance, traceability, and repeatability
- Simulation runs tracked in GitLab with commit tags v1.7.3–v1.8.1; meshes and cases stored in Artifactory with SHA-256 hashes.
- All scripts and setup files are containerized (Docker image emo-cht:2024.1). A full rerun by an uninvolved engineer reproduced the steady 2C, 7.5 L/min case within 0.12 C for Tmax and 0.4 kPa for Δp.

6.9 Team competency and independent review
- Primary analyst: 9 years in electronics CHT; coauthor on two SAE papers about battery thermal paths.
- Peer review by Dr. C. Nguyen (not part of the design team); findings included adding a time-step convergence study and verifying k–ω SST near-wall treatment at elbows. Both addressed, with documented changes.

6.10 Tool control and QA
- Solver version is frozen for this assessment; no beta or custom patches used. Hardware environment: dual Xeon 8352Y nodes, RHEL 8.8, Infiniband interconnect; no reproducibility issues due to parallel nondeterminism observed beyond 0.03 C on Tmax.

6.11 Acceptance targets and how we judged them
Before testing, we set quantitative gates:
- For Tmax and ΔTmax, MAE ≤ 1.5 C and ≤ 0.5 C respectively over the matrix.
- For Δp, relative error ≤ 10% per point.
- Grid-induced uncertainty contributing less than one-third of the decision margin.
- The above are met: MAE 0.86 C (Tmax), 0.29 C (ΔTmax), Δp errors 2.9–7.1% across points, and GCIs are well below margins.

6.12 Limits and caveats
- Model assumes uniform volumetric heat generation within each cell block. During fast transients, spatial nonuniformity could lead to underpredicted local wall hot spots. Evidence: 0.4 C underprediction during first surge. For intended decisions (steady operation and controller setpoint), the impact is immaterial.
- Extrapolation to alternate channel layouts (S1, S3) is not warranted without re-validation; flow structures at junctions differ.
- If coolant contains inhibitors that change viscosity beyond ±8% from the current curve set, update is required.

7. Methodology Summary

- We planned the assessment around the real question of design screening at the module level with specific thermal limits. We then:
  - Verified the solver behavior through manufactured and correlation-based checks.
  - Quantified discretization impacts via mesh/time-step studies and reported GCIs.
  - Measured inputs or inferred them from targeted tests with uncertainty ranges.
  - Built an experimental campaign matching the decision envelope, including repeatability and calibrated sensors.
  - Compared model to data using pointwise and aggregate metrics and set thresholds upfront.
  - Explored sensitivity and carried variability through to outputs for risk awareness.
  - Ensured the process is audit-ready with configuration records and third-party review.

8. Credibility Assessment and Rationale

Putting the strands together:
- The mathematical and numerical side shows second-order behavior and controlled residuals; mesh and time-step errors are an order of magnitude below decisions.
- The physics included are those that matter in this regime, with reasonable simplifications tested by sensitivity study; omitted phenomena are shown negligible within the envelope.
- Input data come from lab procedures with quantified uncertainty; the most uncertain input (TIM thickness) is accounted for and its impact on outputs is characterized.
- The dataset used for checking predictions covers the operating window, employs independent instrumentation, and has repeatability quantified.
- Agreement against measurements meets previously stated metrics, including the most safety-relevant output (Tmax).
- Our team and process accounts for human error via scripting, code review, and independent reruns. The software stack is stable and its configuration is locked.

Residual risks:
- Minor underprediction of peak spikes in fast transients due to uniform heat source approximation; we judge this not to affect screening of steady setpoints or layout choices.
- Limited evidence at very high Reynolds number ends (Re ~ 11800); we added a small pressure-loss margin for pump sizing there.

9. Limitations and What This Does Not Cover

- Not a pack-level simulation: no manifold dynamics, no coolant loop thermal mass.
- Not valid for freeze-thaw cycles, coolant aeration, or flow-induced vibration.
- Not applicable for faulted cells or thermal runaway behavior.
- Not approved for certifying end-of-life degradation limits; only new cells within tested parameter space.

10. Decision

Based on the evidence outlined, the S2 cold-plate conjugate heat transfer model implemented in ANSYS Fluent 2024 R1 is accepted for:
- ranking design variants within the S2 family,
- establishing module-level cooling controller setpoints within the tested envelope (coolant flow 4.5–9.0 L/min, inlet 18–28 C, ambient 20–35 C, cell heat 6–16 W/cell),
- and sizing the pump with an added pressure-drop margin of 0.7 kPa for the top 5% of the flow range.

The model is not approved for:
- alternate channel topologies (S1, S3) without new validation,
- safety certification or predictions outside the stated domain.

Decision made by: Chief Thermal Engineer (M. Alvarez) upon recommendation from the Thermal Systems V&V Group and concurrence by the independent reviewer.

11. Actions and Conditions for Continued Use

- If TIM thickness distribution changes (material or assembly procedure), re-run a 50-sample uncertainty propagation to reconfirm margins.
- For any change in coolant chemistry that shifts viscosity more than ±8% in the 18–28 C band, re-check Δp vs bench test before release.
- For Q1 next year, extend the model to include nonuniform intra-cell heat distribution if controller design requires transient spike mitigation; update validation accordingly.

12. Document Control and Reproducibility

- All case files, meshes, CAD, and scripts archived under Project Asterion, folder 05-CHT-Validation, snapshot tag “S2-CHT-R1”. Docker image digest: sha256:3b9c…ac12. Test data workbook: TDW-CP-S2-RevB.xlsx with calibration sheets.
- To reproduce the headline steady run: see runbook step RS-CHT-17; expected wall-clock 6.3 h on 32 cores; results match criteria if Tmax within 0.5 C and Δp within 0.7 kPa of stored baselines.

Appendix references are provided in appendix.md, including raw comparison tables, sensor calibration certificates, mesh images, and detailed error budgets.
