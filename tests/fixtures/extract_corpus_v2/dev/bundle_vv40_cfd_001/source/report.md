# Credibility Assessment Report — CFD Prediction of Centrifugal Blower Performance (vv40)

Project: DeltaCool CX-450 scroll blower performance model  
Software: Ansys Fluent 2023 R2  
Prepared by: Fluids Engineering Group, Thermal Systems Division  
Date: 2026-08-05

## Executive summary

This report evaluates whether a CFD model of the CX-450 centrifugal blower can be relied upon to generate pressure-rise versus flow curves and efficiency estimates for controller setpoint selection and initial fan sizing. The model uses steady RANS with multiple reference frame (MRF) treatment of the rotating impeller and k–ω SST turbulence closure. We benchmarked the simulation against AMCA 210 chamber tests (42 points across seven speeds) and a single-plane PIV survey in the volute. A mesh independence campaign and a short transient sliding-mesh cross-check were used to interrogate numerical behavior. We quantified the combined uncertainty from numerical, parameter, and test sources and examined sensitivity to key modeling choices and inputs.

Key outcomes:
- Agreement with AMCA 210 pressure rise is within 3.4% RMS over the validated envelope; 39/42 points fall within the computed 95% confidence bands.
- Mesh-induced error on pressure rise at the design point is estimated at 1.8% (fine-grid GCI); temporal effects when switching to sliding mesh are below 0.5% on pressure rise.
- Most influential inputs are the porous loss coefficients for the inlet screen and the turbulence intensity at the inlet bellmouth.
- The model is recommended for use in controller setpoint selection and preliminary fan selection within the tested range (0.6–1.15 Qd, 2400–3300 rpm), contingent on the specified workflow. It is not approved for predicting noise, surge behavior, or off-envelope operation.

A risk-informed argument is provided in the Credibility Synthesis section, culminating in an acceptance decision.

## 1. Background and intended use

The CX-450 is a scroll-type centrifugal blower intended for electronics cooling skids. The engineering question is: For a given speed and flow setpoint, what pressure rise and shaft power are expected at standard conditions? This information feeds the building management system (BMS) commissioning plan, with additional use for shortlist selection in procurement.

- Decision impact: The CFD curves will set initial controller gains and duty points before site testing. Errors at the 3–5% level are acceptable; larger biases might lead to suboptimal efficiency or over/undersizing in early procurement rounds. There is no direct patient or life-safety consequence. We classify the influence of the model on decisions as moderate; the model’s risk is low-to-moderate given downstream checks in the test lab.

- Operating envelope of interest: Volumetric flow from 0.6 to 1.15 times the duty flow Qd (Qd = 1.75 m3/s), speeds 2400–3300 rpm, air at 20–30°C, sea-level conditions, Reynolds numbers above 3×10^5 in the volute.

## 2. Physics idealization and governing approach

- Equations: Incompressible, isothermal steady-state RANS; density fixed at 1.184 kg/m3 (25°C, 1 atm). We justified constant density since maximum Mach number at the impeller exit is under 0.18 at highest speed; compressibility corrections were tested and changed pressure rise by <0.3%.
- Rotational modeling: Rotating reference frame with a frozen rotor interface between the impeller and stationary volute.
- Turbulence closure: k–ω SST; low-Re near-wall treatment with y+ targeted <1 across blades and volute walls. Two-layer all-y+ wall treatment was not used in production but was explored in sensitivity checks.
- Additional elements: The inlet screen is represented as a porous region with linear and quadratic resistance terms (K, C) per vendor data sheet; surface roughness set to 1.6 µm (Ra) on both blades and volute.
- Out of scope: Tones, broadband noise, cavitation, condensation. No thermal coupling to structure.

Rationale: The intended outputs are bulk performance quantities; the selected physics give a reliable balance of turnaround time and fidelity in similar fans previously studied by this group.

## 3. Software and workflow controls

- Solver and build: Ansys Fluent 2023 R2, double precision, pressure-based coupled algorithm, second-order spatial schemes (pressure: second-order; momentum, k, ω: second-order upwind).
- Environment: Runs executed in containerized images pinned to OS libraries; case/replay scripts tracked in Git (repo: cfd-cx450, tag: v1.3.2). Hashes for meshes and boundary condition files are logged in the results manifest.
- QA: Automated regression checks before release: two canonical cases (Poiseuille, turbulent flat plate) must pass tolerance bands. Pre-run sanity checks (mesh quality, negative cell volume detection, boundary-unit consistency) are enforced by CI.
- Hardware: HPC cluster, 2 nodes, 32 Intel cores per node, Infiniband interconnect; repeated run of the design point produced pressure rise within 0.1% and torque within 0.2%, indicating repeatability on the platform.

## 4. Numerical behavior: mesh, time, and convergence

We executed a refinement campaign using poly-hexcore meshes with boundary-layer prisms (20 layers, first-cell height for y+≈1, growth rate 1.2):

- Coarse: 3.1 million cells
- Medium: 8.4 million cells
- Fine: 21.7 million cells

At the design condition (Q=Qd, N=3000 rpm), pressure rise Δp was 9.72 kPa (coarse), 9.89 kPa (med), and 9.96 kPa (fine). Extrapolation with Richardson methodology assuming observed order 1.9 yields a fine-grid estimate of 10.00 kPa and a GCI of 1.8% on Δp for the medium mesh. Torque shows a similar trend (GCI 2.1% at medium).

Steady-state iterations used:
- Convergence targets: residuals below 1e-5 for continuity and momentum, 1e-6 for k and ω; integral monitors (Δp and torque) stabilized to within 0.2% over the final 500 iterations.
- Rotational reference frame ramped up over 300 iterations to mitigate transients.

Transient cross-check: A sliding mesh run (time step 1e-4 s, 720 steps per revolution, 6 revolutions for averaging) at Q=0.9Qd gave Δp within 0.5% of the MRF result; the periodic oscillations were small relative to the mean. We concluded steady MRF is adequate for bulk performance over the validated space.

## 5. Reference problems for solver sanity

We ran two standard checks to confirm the solver settings and build reproduce known behavior:

1) 2D laminar channel (manufactured solution added body force): Observed order of accuracy 2.0 ± 0.1 for velocity on uniform refinement; L2 norm errors decreased as expected with second-order schemes.

2) Turbulent flat-plate (Reθ range 300–3000): Predicted Cf matched the White correlation within ±5% across x; k–ω SST settings identical to production. This corroborates wall-modeling and near-wall prism-layer settings.

While not a proof of absolutes, these spot-checks reduce the risk of silent numerical defects in the toolchain.

## 6. Inputs and boundary specifications

- Inlet: Total pressure derived from a calibrated nozzle upstream of the bellmouth; turbulence intensity 2.5% ± 0.5% (from hotwire survey). Velocity direction aligned to the centerline; no swirl at inlet.
- Outlet: Static pressure specified to sweep the flow curve; bellmouth and downstream settling chamber per AMCA 210 A setup are included in the model to avoid ambiguous pressure datum corrections.
- Speed: 2400–3300 rpm set per case using RPM boundary on the rotating zone.
- Material: Air at 25°C; dynamic viscosity 1.849e-5 Pa·s; density fixed at 1.184 kg/m3.
- Porous screen: Linear coefficient K = 3.1e7 1/m2; quadratic C = 680 1/m; vendor tolerances ±10% and ±15% respectively.
- Wall roughness: 1.6 µm Ra mapped to equivalent sand-grain roughness ks=2.5*Ra; roughness modified only in a sensitivity branch to bound uncertainty.

Pedigree: All numerical inputs are either measured in the test rig (nozzle, turbulence) or sourced from vendor-controlled drawings (screen coefficients), with certificates or data sheets attached in the records folder.

## 7. Tuning activities

During shakedown, the porous coefficients for the inlet screen were adjusted within the vendor’s stated tolerances to match a single off-design point (N=2700 rpm, Q=0.85Qd). The adjustments were K+5% and C−7%. No other parameters were tuned to test data. All production comparisons are therefore cross-validation relative to the tuned point.

We documented this activity to ensure users understand where the model may inherit calibration influence.

## 8. Experimental comparators and their uncertainty

Laboratory data were obtained at the Airflow Test Lab using an AMCA 210 A chamber:

- Instrumentation: Differential pressure transducers ±0.25% FS, torque cell ±0.3% FS, tachometer ±0.05% FS, ambient T/P sensors ±0.2°C/±0.5 kPa.
- Flow determination: Nozzle method, ISO 5167 orifice plate calibration; combined standard uncertainty in volumetric flow ±0.9% at coverage factor k=2.
- Test matrix: Seven speeds (2400–3300 rpm in 150 rpm increments); six flow points per speed from near-shutoff to high flow; total 42 points.
- Field data: Planar PIV in the mid-height volute at Q=Qd, N=3000 rpm; uncertainty in in-plane velocities ±0.08 m/s (k=2).

Test-to-test repeatability yielded Δp variations within ±0.5% at fixed setpoints. The chamber correction for kinetic energy at the measurement plane was applied per AMCA.

## 9. Comparison with tests: results and coverage

Agreement with test chamber results:
- Pressure rise: Over the 42 points, the CFD minus test Δp error had a mean bias of +0.4% and RMS 3.4% of the Δp span. Largest deviations occurred near near-shutoff (up to 6.1% high) where recirculation grows.
- Shaft power: Errors were slightly larger in magnitude (RMS 4.2%), with a positive bias (predicted torque tends to overshoot), likely due to wall roughness uncertainty and local separation features near the tongue.
- PIV: Velocity magnitude index-of-agreement 0.91; angular deviation (circumferential flow angle) averaged 2.8°, with a localized peak difference of 7° near the cutwater.

Coverage:
- Speeds: Entire target speed range is exercised; only extrapolation is below 2400 rpm or above 3300 rpm.
- Flow: Tested range 0.55–1.2 Qd; accepted envelope limited to 0.6–1.15 Qd (we trim extremes where comparison deteriorates).
- Environmental: Test temperature and pressure matched modeling assumptions within the ± range specified.

We view coverage as adequate for the stated use—controller setpoints and initial selection—where off-nominal extremes are not primary.

## 10. Sensitivity exploration

We ran one-factor-at-a-time and small factorial sweeps around the baseline to gauge the influence of uncertain quantities and modeling choices:

- Turbulence model: Realizable k–ε with enhanced wall treatment produced Δp within 1.8% of SST at mid flows but diverged up to 3.5% at near-shutoff; SST retained due to better conformity with PIV near the tongue.
- Inlet turbulence intensity: Varying from 1.5% to 3.5% changed Δp by ±0.6% at Qd; effect grows to ±1.4% at high flow.
- Porous coefficients (K, C): Within vendor tolerances, Δp shifts by ±2.1% (combined effect) at mid-flow; most influential among inputs we varied.
- Wall roughness ks: Increasing to 10 µm reduces Δp by ~1.0% and increases torque ~1.3%.
- Mesh growth rate (1.2→1.3) on same cell count increases Δp error by ~0.4%; near-wall resolution degradation (y+≈2→8) yields an additional ~0.6% bias.

Response surfaces built from these samples fed the uncertainty propagation discussed next.

## 11. Uncertainty estimation and propagation

We aggregated contributors as follows:
- Numerical resolution: From the mesh study, we adopted 1.8% (Δp) and 2.1% (torque) as the discretization component on the medium mesh used for production. Temporal contribution estimated at 0.5% on Δp.
- Input variability: K and C modeled as normal with std dev equal to one-third of vendor tolerance; inlet turbulence intensity normal (σ=0.4%); wall roughness lognormal with median 1.6 µm and geometric std dev 1.5.
- Test measurement: Chamber Δp uncertainty 0.6% (k=2), nozzle flow 0.9% (k=2), torque 0.6% (k=2); combined with k=1 approximations for Monte Carlo.

Propagation:
- Monte Carlo with 200 samples at representative operating points (0.7Qd, Qd, 1.1Qd) for two speeds (2700, 3000 rpm). The 95% bands on Δp were ±4.1% at Qd and grew to ±5.2% near shutoff; torque bands ±4.8% typical.
- Empirical coverage: 39 of 42 AMCA points fell within the combined CFD+test 95% intervals on Δp; 37 of 42 on torque.

We judge the uncertainty bands reasonable and near-miss on the 95% nominal coverage is acceptable for the context.

## 12. Applicability and edges of validity

- Approved domain: Air at 20–30°C, sea-level; speeds 2400–3300 rpm; flows 0.6–1.15 Qd; configurations matching the tested casing and impeller geometry; inlet screen model per data sheet.
- Not for: Prediction of acoustic metrics, rotating stall/surge, deep off-design (<0.6Qd), high altitudes (>1500 m), other impeller trims without rerun and spot validation, condensation or non-air gas mixtures.
- Extrapolation rule: Outside approved domain, the model may serve for qualitative trends only, and results must be labeled as unvalidated. Any use beyond ±10% of the validated speed or flow range requires re-assessment.

## 13. Team capability and execution controls

- Analysts: Lead author has 11 years in turbomachinery CFD; two additional team members contributed meshing and post-processing. All trained on Fluent RANS best practices (internal training module CFD-102).
- Execution aids: A runbook checklist is part of the repository; a single-click script regenerates plots and comparison metrics to avoid manual mishandling.
- Traceability: Every case stores a case ID, solver version, mesh ID, and post-processing script hash. The results bundle in the vault includes CAD extracts, meshes (.cas.h5), and post-processing notebooks.

## 14. Previous usage and consistency with related efforts

This workflow was used in two prior fan families (BX-320, DX-510). Retrospective analyses showed RMS Δp errors of 3.1% and 3.7% respectively over similar test suites, lending confidence that the present performance is consistent with past experience using the same choices (SST, MRF, prism-layer counts).

## 15. Independent review

A senior CFD specialist from an unrelated product line (Dr. K. H. Levy) reviewed the case and issued findings (review-2026-06-22):
- Confirmed mesh strategy and solver settings are consistent with published best practices for scroll-type blowers.
- Requested a transient spot-check (since added, Section 4).
- Suggested making the porous coefficient adjustments explicit and bounding their effect (addressed in Sections 7 and 10).
All items were addressed before this report.

## 16. Credibility synthesis

We organize the available evidence against the needs of the decision:

- Decision context: Moderate influence on commissioning; low-to-moderate consequence of a few percent bias, caught later in lab and site testing. Target accuracy band: ±5% on Δp and power within the validated domain.

- Fit-for-purpose physics: Governing equations and closures match the flow regime; compressibility effects bounded and negligible for the intended outputs.

- Numerics: Mesh and temporal studies show controlled discretization effects; convergence is robust by both residuals and integral monitor criteria; code-level checks passed.

- Inputs: Boundary conditions and material properties are grounded in measurement or vetted vendor data; the single tuning action is confined within supplier tolerances and is transparently documented.

- External comparators: AMCA 210 data and PIV provide both bulk and local checks; RMS errors and coverage indicate the model achieves the accuracy target in the operational window of interest.

- Sensitivity and uncertainty: Major drivers are identified; propagated uncertainty bands reasonably capture the majority of lab data; deviations near shutoff are acknowledged and cordoned off from the approved domain.

- Controls and reproducibility: Versioning, CI checks, runbooks, and independent review reduce human and process error risk.

On this basis, the collective argument supports using the CFD model to inform controller setpoints and selection in the stated range. It does not support extrapolated use for acoustics, deep off-design, or other impeller trims.

## 17. Limitations and open items

- Near-shutoff behavior: The discrepancy increases as recirculation strengthens; while still within a few percent, we do not endorse using the model for control settings at ≤0.6Qd. A transient resolving diffuser stall dynamics might be explored in the future.
- Roughness treatment: Roughness is a surrogate for manufacturing and surface finish effects; collecting as-built roughness on production parts would reduce uncertainty in torque predictions.
- Porous element fidelity: The inlet screen model is a lumped element; adding a resolved geometry version for a subset of cases could tighten the input-related uncertainty and reduce the need for any tuning.
- Thermal/altitude effects: Current model is isothermal and at sea-level; higher-altitude deployments will require reassessment of density treatment or weak compressibility and a light revalidation sweep.

## 18. Decision

Disposition: accepted for use in controller setpoint generation and preliminary fan selection for the CX-450 within the validated operating window (air at 20–30°C; 0.6–1.15 Qd; 2400–3300 rpm), subject to:
- Using Ansys Fluent 2023 R2 with the k–ω SST model, double precision, and poly-hexcore meshes at or finer than the “medium” density outlined herein (8.4M cells, y+≈1).
- Applying the documented runbook and version-controlled scripts.
- Lab cross-check of 2–3 points at mid and high flow during commissioning; if deviations exceed ±5%, pause use and notify the Fluids Engineering Group.

The model is not approved for predicting acoustics, surge/sheet separation behavior at deep off-design, or any condition outside the envelope defined in Section 12.

Decision authority: Head of Thermal Systems (M. M. Raines) upon recommendation of the Fluids Engineering Group and review sign-off by the independent specialist.

## 19. References and records

- AMCA 210-16 Laboratory Test Results, Report AFL-2026-027
- PIV Survey, Planar Field in Volute Mid-Height, Report PIV-2026-009
- Vendor Data Sheet: Inlet Screen Loss Coefficients, VS-IX-450 Rev B
- Repository: cfd-cx450 (internal Git), tag v1.3.2
- Mesh IDs: cx450_m3p1M, cx450_m8p4M, cx450_m21p7M
- Review note: review-2026-06-22 (KHL)

Appendix materials (not repeated here) include mesh quality histograms, residual histories, GCI workups, uncertainty propagation notebooks, and detailed comparison plots for all 42 AMCA points.
