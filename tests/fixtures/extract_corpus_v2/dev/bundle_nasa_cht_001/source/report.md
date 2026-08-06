Conjugate Thermal-Fluid Model Credibility Assessment
Liquid-Cooled Battery Cold Plate for Lunar Rover Avionics Bay

Executive Summary
This report documents the credibility assessment for a coupled thermal-fluid model of the LX-3 battery cold plate assembly installed in the Artemis-M rover avionics bay. The model predicts temperatures, heat fluxes, and pressure drops under steady and slowly varying electrical loads with propylene-glycol/water coolant circulating through machined serpentine channels. The intended use is to support thermal margin allocation prior to PDR and to inform radiator sizing and pump setpoint selection.

We used STAR-CCM+ 2023.2 to solve the conjugate heat transfer problem (solid conduction and fluid convection) with radiation coupling to a simplified bay wall model. Geometry was imported from Creo Parametric (Rev. K). The computational meshes range from 7.4 to 22.6 million cells with 12–18 prism layers and y+ ≤ 1 on all wetted faces. We performed mesh/time-step independence checks, observed second-order spatial accuracy on manufactured conduction problems, and estimated discretization-related temperature error <1.0 C on the finest practical grid. Residuals dropped below 1e-5 for continuity/momentum and below 1e-8 for energy with no oscillatory behavior.

A benchtop rig reproduced key thermal-fluid behaviors: matching channel geometry, same coolant family and concentration, equivalent heat fluxes into representative cell simulators, and measured thermal contact resistances. Across 18 test points spanning flow 3–9 L/min, inlet 5–25 C, and heat loads 1.2–7.8 kW, predicted peak plate temperature deviated from thermocouple readings by mean absolute 1.9 C (RMS 2.4 C), with 95% of points within ±4.8 C. Overall heat balance closure remained within 3% of electrical power. Comparison of pressure drops matched within 7% RMS.

Uncertainty arising from inputs (contact conductance, coolant viscosity, pump curve, surface roughness, and cell heat load variation) was propagated using a 300-member Latin Hypercube ensemble with surrogate fitting; at the worst case (7.8 kW, 5 C inlet, 3 L/min) the 95th percentile of peak plate temperature was 63.2 C, still 11.8 C below the allowable. First-order Sobol indices identify interface conductance and flow rate as dominant contributors to temperature spread.

We exercised configuration controls (Git tags, containerized solver environment) and documented all model runs with scripted pipelines. An independent reviewer re-created two benchmark cases and one validation point with a separately meshed model; differences in peak temperature were within 1.1–2.0 C, and the reviewer concurred with the overall approach.

Verdict: accepted for pre-PDR thermal margin verification and pump/radiator trade studies over the applicability bounds defined in Section 6; not approved for microsecond–second transients, coolant phase change, or operation outside the validated envelope.

1. Background and Context of Use
The LX-3 battery system must maintain cell core temperatures between 0 and 75 C under lunar surface mission profiles that include long idle periods, burst discharge for traverses, and environmental swings from −173 to +127 C at the avionics bay exterior. The cooling subsystem is a closed-loop pump circulating 40–55% propylene glycol-water through an aluminum 6061-T6 cold plate with serpentine channels, interfacing to a panel radiator via a manifold. This model assesses temperature margins and informs pump curve selection and radiator sizing. It is not intended to resolve electrochemical heat generation nuances or freezing behavior; those are handled by separate models and test programs.

2. System and Model Overview
- Geometry: CAD Rev. K of the cold plate with 36 channels, 2.4 mm hydraulic diameter, 1.2 mm wall thickness, and detailed manifolds; 20 battery cell simulators bolted to the plate; O-ring grooves included; fastener holes abstracted as solid cylinders.
- Physics: Steady and slowly varying (quasi-steady) RANS with k-ω SST; segregated flow and coupled energy; buoyancy via Boussinesq for coolant; gray-diffuse surface radiation from plate outer skin to bay wall enclosure. No boiling, no cavitation. Thermal contact modeled via nonlinear conductance vs. preload determined from rig measurements.
- Material data: 6061-T6 with temperature-dependent conductivity (k = 166–180 W/m-K over 20–60 C); gasket elastomer per vendor datasheet; coolant property tables (density, viscosity, Cp, k) from CoolProp v6.4 for 40/50/55% mixtures calibrated against supplier certificates.
- Boundary conditions: Inlet mass flow 3–9 L/min; inlet temperature 5–25 C; downstream pressure per pump curve; cell heat loads assigned per mission profile snapshots (1.2–7.8 kW total) with ±5% across cells to represent maldistribution; external radiation sink at 200–300 K representing bay wall thermal boundary.

3. Methods Used to Establish Trustworthiness
3.1 Numerical solution quality
- Grid sensitivity: Three systematically refined meshes (7.4M, 12.9M, 22.6M cells) with refinement in channels, fillets, and at contact patches. Near-wall clustering gives y+ in 0.5–1.2 for all cases; 14–18 prism layers achieve y at least 15× smaller than the viscous sublayer thickness.
- Temporal resolution: Quasi-steady ramped loads integrated with Δt = 0.25 s and 0.10 s; results for peak temperature differed by 0.3 C, which is below other uncertainties. Steady runs reached stationary residual and monitor trends.
- Iterative convergence: Residual targets of 1e-5 for continuity and momentum and 1e-8 for energy were always met or exceeded; outlet mass flow variation <0.02% and monitor points stable to <0.01 C over final 500 iterations. No limit cycles were observed.
- Error estimation: Grid convergence index (three-grid method, safety factor 1.25) gave estimated discretization uncertainty of 0.8 C on peak plate temperature at 7.8 kW, 3 L/min; pressure drop discretization uncertainty 1.6%. Observed spatial order for temperature ≈1.9; for velocity magnitude ≈1.6, consistent with second-order schemes on complex geometry.

3.2 Physics and closure choices
- Turbulence: k-ω SST chosen based on channel Reynolds numbers 900–4500; transitional effects examined at 900–1100 with γ-Reθ transition model on two cases showing <0.6 C difference in peak temperature; baseline SST retained for robustness. Wall functions not used.
- Radiation: Viewfactor-based approximation tested versus DOM with 4×4×4 angular resolution; difference <0.3 C, so viewfactor method used in production for reduced cost.
- Interface conduction: Nonlinear conductance fitted to rig-derived measurements (Section 4) as function of clamping force and interstitial grease thickness; sensitivity captured in UQ.
- Fluids: Compressibility neglected (Mach << 0.3); buoyancy small (Grashof < 1e6) yet included; no two-phase phenomena modeled.

3.3 Comparisons to controlled test data
We established a closed-loop test stand with a replica cold plate machined to the same drawing tolerances as the flight design. Key features:
- Instrumentation: 64 type-T thermocouples (±0.5 C after calibration) at plate inlets/outlets and on cell simulator bases; Coriolis flow meter (±0.2% of rate); differential pressure transducer (±0.25% FS); IR camera (calibrated emissivity 0.8) for qualitative maps; load bank with 0.2% power uncertainty.
- Calibration: All sensors NIST-traceable; drift checks after each 8-hr run; IR camera cross-checked with embedded TC at 3 locations.
- Test matrix: 18 points spanning three flow rates (3, 6, 9 L/min), two inlet temps (5, 25 C), and three total heat loads (1.2, 4.5, 7.8 kW); at 6 of these points, we also swapped to 50% mixture and altered clamping torque to create bounding interface conditions.
- Data reduction: Each point run to thermal steady state (<0.05 C/min drift); 10-min averaging windows; uncertainty combined by root-sum-square.

Model-to-data comparison used the as-tested geometry (including measured channel roughness Ra = 2.8 μm) and inlet conditions. Results:
- Temperatures: Mean absolute error 1.9 C (RMS 2.4 C) across all monitored locations; peak plate temperature error averaged 2.1 C; worst case underprediction 5.2 C at 3 L/min, 7.8 kW with lower-than-nominal clamping torque (consistent with fitted conductance curve).
- Pressure drop: RMS deviation 7.0% across the flow range; model slightly overpredicts at 9 L/min by 5–9%, likely due to roughness representation limits.
- Heat balance: Modeled heat rejection vs. electrical input agrees within 3%; coolant energy rise matches within 2.5% after accounting for rig heat leakage.

3.4 Treatment of input data and their variability
- Data provenance: Material properties sourced from MMPDS and vendor datasheets; coolant properties from CoolProp validated against supplier certificates; pump curve supplied by vendor test with ±3% tolerance; channel roughness measured on 5 coupons; contact conductance fitted from 24 clamp/load tests.
- Bounds and distributions: Interface conductance modeled as lognormal with median 7,200 W/m2-K and GSD 1.25; flow rate normal with σ = 0.12 L/min around setpoint control; coolant viscosity uncertainty ±5% (triangular); pump speed-to-head curve with ±3% (uniform); per-cell heat load uniform ±5% around scenario averages.
- Correlations: Weak positive coupling between flow and pump curve error included (ρ = 0.3).
- Screening: Morris method pre-screening indicated negligible impact from emissivity and bay wall temperature variation within ±10 K band; these were fixed for production UQ.

3.5 Sensitivity studies
- Local perturbations: ±10% changes to interface conductance and to flow yielded peak temperature moves of −3.0/+3.6 C and −4.1/+3.8 C, respectively, at 7.8 kW; turbulence model switch to realizable k-ε caused −0.7 C change in peak temperature and +4% in pressure drop, reinforcing SST choice.
- Global analysis: First-order Sobol indices at the worst-case operating point: interface conductance 0.44, flow rate 0.29, viscosity 0.13, pump curve 0.09, per-cell load imbalance 0.05; second-order terms small (<0.06).
- Adjoint checks: Discrete adjoint for steady energy equation confirmed spatial locations of highest sensitivity coincide with contact patches near inlet manifolds.

3.6 Software and workflow controls
- Toolchain: STAR-CCM+ 2023.2; meshing with STAR-CCM+ and snappyHexMesh cross-check; scripting in Python (PyFoam-like workflows) and Java macros; postprocessing in ParaView 5.11 and in-house pandas scripts.
- Platform: HPC cluster Orion-05: Intel Xeon Gold 6348 (Ice Lake), 2.6 GHz, 2×40 cores/node, 256 GB RAM; Infiniband HDR; CentOS 8; runs distributed over 160–320 cores; solver double precision.
- Reproducibility: Singularity container with pinned OS and library stack; Git repository with tag v1.7.3 for this assessment; each run tracked by commit hash and run manifest; no solver randomness in steady cases.
- Regression checks: Three benchmark cases (laminar channel Nusselt 4.36; conjugate plate/coolant slab; radiation cavity) run weekly; last 12 weeks show invariant results to within roundoff. Vendor patches 2023.2.2 evaluated against benchmarks before adoption.

3.7 Analyst and process
- Team: Lead engineer (8 years CFD/CHT, STAR-CCM+ Certified Professional) and thermal analyst (12 years space thermal design); both completed vendor training on conjugate heat transfer and turbulence in last 24 months.
- Procedure: Model Description Document (MDD-LX3-CHT-002, Rev. C) describes geometry, physics, and limitations; Test-Analysis Correlation Plan (TACP-LX3-014, Rev. B) defines the validation matrix; Uncertainty and Sensitivity Plan (USP-LX3-006, Rev. A) records distributions and sampling.
- Review: Independent review by Dr. A. Johansson (Thermal Systems Group) with two re-created cases and mesh built independently; results presented at internal CHT Peer Review #3 (minutes in PRM-CHT-003).

3.8 Traceability and documentation
- All input files, CAD derivatives, property tables, and scripts stored under M-FILES vault MF-LX3-CHT with lifecycle state control; run logs include STAR-CCM+ journal, residual histories, monitor CSVs, and convergence snapshots.
- Figures and tables in this report link back to run IDs and commit hashes; a run book (RB-LX3-CHT-2024Q2) enumerates 64 production runs.

3.9 Applicability envelope
This model is intended for:
- Coolant: 40–55% PGW mixture by volume
- Flow: 3–9 L/min delivered at the cold-plate inlet manifold
- Inlet temperature: 5–25 C
- Heat load: 1.2–7.8 kW total across 20 cells, per-cell imbalance up to ±5%
- Environment: Avionics bay wall effective radiative temperature 200–300 K
- Dynamics: Quasi-steady variations slower than 0.5 C/s at plate sensors

It is not designed for:
- Freezing/thawing behavior or any two-phase flow
- Startup/shutdown transients faster than a few seconds
- Operation below 3 L/min or above 9 L/min
- Different coolant families without revalidation

4. Results
4.1 Benchmarked behaviors
- Manufactured conduction: On a 3D block with a prescribed polynomial temperature field, measured L2 error decreased with grid spacing at observed order 2.01; confirms energy equation discretization is behaving as designed.
- Channel heat transfer: Fully developed laminar case matched analytical Nusselt = 4.36 to within 0.9%; transitional case recovered Shah-London correlation within 3.1%.
- Radiative exchange: Parallel plate test case matched analytical solution within 0.5% on net heat flux.

4.2 Validation summary
- Temperature fields: Corner regions under cell simulators 2, 11, 19 approached 58–60 C at 7.8 kW worst case; the model captured the hotspot structure seen in IR images. Peak differences remained aligned with torque variations applied during test; when torque is set to nominal 2.0 N·m in both model and test, deviations dropped to 1.4 C RMS.
- Pressure drops: Predicted Δp across plate rose from 7.2 kPa at 3 L/min to 58 kPa at 9 L/min; measured values 7.0 and 54 kPa, respectively.
- Heat rejection: Coolant temperature rise matched within 2.5%; small discrepancies traced to manifold heat leak differences between rig and model, noted in MDD.

4.3 Propagated variability and risk
- Ensemble outcomes: At the worst case scenario, P50 peak temperature 58.9 C, P95 63.2 C; at nominal 4.5 kW and 6 L/min, P95 is 45.6 C; for low load 1.2 kW, P95 is 28.1 C.
- Margin picture: Even at P95 worst case, the 75 C ceiling leaves 11.8 C margin; minimum margin across the assessed matrix is 9.7 C.
- Decision drivers: Interface conductance and flow control emerge as levers; a 10% flow increase yields a 3.8 C margin improvement at high load.

5. Synthesis of Evidence and Credibility Perspective
- Numerical correctness: Grid/time independence, observed second-order behavior on designed tests, and small GCI values suggest numerical errors are small relative to thermal margins. Solver residuals and monitors indicate well-converged solutions.
- Physics adequacy: The chosen closures reflect the flow regime and thermal environment. Radiation treatment was checked against a higher-fidelity DOM option. Transitional effects were probed and deemed negligible for the margin questions at hand.
- Data pedigree: Materials and coolant properties are traced and temperature-dependent. Interfaces are characterized via targeted clamp tests and incorporated as fitted curves. Pump and flow instrumentation uncertainties are accounted for.
- External grounding: The 18-point comparison campaign provides a credible anchor. Errors are low and pattern-consistent with measured torque variations. Pressure drops track vendor and rig data to within engineering expectations.
- Variability and sensitivity: Major uncertainties have been propagated, and a clear picture of influencer ranking is available, enabling targeted risk management (e.g., torque specifications, flow control performance).
- Management of the modeling effort: Inputs and outputs are versioned; scripts and containers enforce repeatability. Independent replication by a separate analyst strengthens confidence. Team competencies and documented processes reduce the chance of operator error.
- Applicability: Stated limits align with both the test matrix and physics assumptions. We have avoided extrapolation beyond validated ranges in drawing conclusions.

6. Limitations and Open Items
- No two-phase: Freezing, boiling, or cavitation are not represented. Operations near 0 C inlet or pump cavitation onset require a dedicated two-phase analysis and testing.
- Rapid transients: Start-up spikes on the order of seconds or less are not in-scope; the quasi-steady assumption breaks down when thermal capacitances dominate.
- Roughness model: Channel roughness is represented by a uniform equivalent sand-grain height; spatial variability may introduce small Δp errors at high flow rates. This is not temperature-critical but should be revisited if pump power margins tighten.
- Manifold leakage: Differences between the rig’s insulation and the model’s idealized adiabatic manifold may explain a small bias in heat balance; future runs will include measured manifold leakage for completeness.
- Validation extent: While 18 points provide reasonable coverage, additional points at intermediate inlet temperatures (10–15 C) would better characterize nonlinearity in coolant properties; planned for 2026-Q1.
- Software updates: Adoption of STAR-CCM+ 2024.1 is deferred pending re-execution of regression benchmarks; until then, analyses supporting decisions will use 2023.2.2.

7. Decision
Based on the evidence in Sections 3–5, the LX-3 conjugate thermal-fluid model is accepted for:
- pre-PDR thermal margin assessments of the battery cold plate assembly,
- radiator sizing trades that require steady-state heat rejection estimates,
- pump setpoint selection within 3–9 L/min,
- operational scenarios with 40–55% PGW coolant, 5–25 C inlet, and total heat loads 1.2–7.8 kW.

The model is not approved for:
- predicting behaviors involving coolant phase change (freezing/boiling),
- start-up or shutdown transients faster than a few seconds,
- conditions outside the applicability envelope in Section 3.9.

Acceptance is subject to adherence to the stated configuration (STAR-CCM+ 2023.2.2, container image CHT-2024Q2) and input bounds. This decision was made by the Thermal Systems Lead (J. Morales) with concurrence from the CHT Peer Review Board on 2026-08-01.

8. References
- MDD-LX3-CHT-002 Rev. C: LX-3 Cold Plate Conjugate Analysis Model Description
- TACP-LX3-014 Rev. B: Test-Analysis Correlation Plan for LX-3 Cold Plate
- USP-LX3-006 Rev. A: Uncertainty and Sensitivity Plan
- PRM-CHT-003: Minutes of CHT Peer Review #3
- RB-LX3-CHT-2024Q2: Run Book with manifests and links to artifacts
- CoolProp v6.4: Properties of Propylene Glycol-Water Solutions
- Vendor Pump Curve: Model P-47, Rev. D, test report VP-47-TR-2025-11

Appendix A: Additional Detail on Grids and Manufactured Case Outcomes
A.1 Grids and near-wall treatment
- Coarse: 7.4M cells, average y+ = 1.1, min prism thickness 3.2e-5 m, 12 layers, growth 1.2
- Medium: 12.9M cells, average y+ = 0.84, min prism thickness 2.1e-5 m, 16 layers, growth 1.18
- Fine: 22.6M cells, average y+ = 0.62, min prism thickness 1.5e-5 m, 18 layers, growth 1.15
Refinement concentrated at channel bends (fillet radius 0.8 mm) and beneath cell contact patches.

A.2 Manufactured case
We used a 3D block (0.1×0.02×0.005 m) with imposed temperature T(x,y,z) = T0 + Ax + By + Cz + Dxyz and corresponding source terms. With second-order convection and diffusion discretization, the observed error reduction rates were:
- L2 norm: p = 2.01 (temperature), 1.95 (heat flux)
- Linf norm: p = 1.88 (temperature)
Residuals converged to machine precision for energy.

Appendix B: Independent Review Summary (Dr. Johansson)
The reviewer built an independent poly-hexcore mesh (14.8M cells) with 15 prism layers (first cell height 2.3e-5 m) using a different meshing strategy. Cases replicated:
- Validation case V-09: 6 L/min, 25 C inlet, 4.5 kW. Reported peak plate T = 42.7 C (ours: 43.6 C). Delta = −0.9 C.
- Worst-case W-03: 3 L/min, 5 C inlet, 7.8 kW. Reported peak plate T = 60.4 C (ours: 61.5 C). Delta = −1.1 C.
- Benchmark channel Δp at 9 L/min: Reviewer predicted 55.8 kPa (ours: 57.1 kPa). Delta = −1.3 kPa.
Reviewer comments:
- Agree with choice of k-ω SST and near-wall resolution.
- Suggest consider transition model if future tests indicate early laminarization at low Reynolds; current evidence does not require a change.
- Commend the use of containers and run manifests; reproducibility is strong.
- No blocking issues noted.

Appendix C: Run Manifest Excerpt
Each production run includes:
- Git commit hash (e.g., 4f2a9c7), container tag (CHT-2024Q2-1.3), STAR-CCM+ version (2023.2.2)
- CAD derivative ID (CREO-LX3-K-der4)
- Property files (CoolProp-PGW40.tab, PGW50.tab)
- Journal scripts (solve_energy_coupled.jou), macros (monitor_peak_temp.java)
- Convergence plots (residuals.png, monitors.png)
- Postprocessing scripts and outputs (peak_map.csv, dp_curve.csv)
These are archived at MF-LX3-CHT:/runs/2026Q2/* with read-only after sign-off.

Appendix D: Test Rig Notes
- Torque control: Torque applied to cell simulators verified with calibrated wrench (±0.05 N·m). When deliberately set to 1.2 N·m, interface temperatures rose by 3–5 C; model captures trend with conductance curve.
- Emissivity: Plate emissivity measured 0.82 ±0.03; sensitivity to emissivity was negligible for in-bay radiation exchange since dominant path is conduction to coolant.

Conclusion
The collected body of work—careful numerics, bounded and tested physics, structured variability analysis, and a replicable workflow—supports the declared context of use. The stated exclusions are important; as long as those are respected, decision-making on thermal margins can safely rely on this model.
