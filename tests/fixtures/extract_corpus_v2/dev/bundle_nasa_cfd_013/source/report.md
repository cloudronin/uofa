Title: Credibility Assessment Report — RANS CFD of NASA Rotor 37 Transonic Compressor for Performance Prediction Near Design Speed

Revision: CAR-ROTOR37-CFD-001, Rev B
Date: 2026-08-06
Analyst: L. Park (Aerosciences), Reviewer: J. McGrath (independent), Approver: H. Diaz (Chief Engineer, Propulsion)

1. Background and Intended Use

This report evaluates the trustworthiness of steady Reynolds-Averaged Navier–Stokes (RANS) simulations of NASA Rotor 37, a single-stage transonic axial compressor, for use in preliminary performance assessments at and near design rotational speed. The predictions will inform margin allocations and map placement at PDR and are not intended for stall boundary mapping or detailed loss decomposition.

Primary figures of merit:
- Mass-averaged total pressure ratio across the rotor
- Adiabatic efficiency
- Choke mass flow and slope near choke
- Spanwise distribution of exit flow angle, Mach number, and total pressure

Acceptability thresholds for PDR use, as agreed with the systems team on 2026-06-11:
- Mean pressure ratio within ±2.0% of test over 98–102% design speed at near-peak efficiency flow rates
- Adiabatic efficiency within ±2.5 percentage points in the same regime
- Spanwise exit flow angle within ±1.5 degrees at 50% and 90% span
- For choke flow, mass flow within ±1.5%

2. Overview of the Computational Setup

- Software: Ansys CFX 2023 R2, double precision, steady RANS, second-order spatial discretization
- Turbulence closure: k–ω SST with curvature correction enabled
- Geometry: NASA Rotor 37 nominal blade, hub, and shroud from NASA TM-1988-xxxx data package; tip clearance set to 0.356 mm (14 mil) based on bench measurements; fillets omitted per test configuration
- Domain: Periodic single-passage sector with mixing-plane interface at 50% axial chord downstream of trailing edge; no stator modeled
- Boundary conditions: Inlet total pressure P0,in = 101.3 kPa ± 0.5%, total temperature T0,in = 288.15 K ± 0.3 K, swirl-free, turbulence intensity 5%; outlet static pressure adjusted to hit target flow points; adiabatic no-slip walls
- Grid: Multi-block hexahedral topology, O4H around the blade; baseline grid 3.4M cells with near-wall spacing to y+ ≈ 1 across 98% wetted area, first layer Δn = 1.2e-6 m, normal growth rate 1.2; tip-gap resolution 28 cells across radial clearance, minimum 35 cells around leading-edge curvature
- Convergence: RMS residuals < 1e-5; mass imbalance across inlet/outlet < 0.02%; mixing-plane flux mismatch < 0.05%; monitored integral quantities steady to < 0.05% over 2000 iterations

3. Sources and Trustworthiness of Inputs

- Geometry pedigree: Blade coordinates and hub/shroud contours originated from NASA Rotor 37 public data set (ref. NASA TM-xxxx). The merge between the 2D blade sections and the 3D stacking law was performed using in-house scripts; spline smoothing stayed within ±8 µm of nominal at any control point, confirmed by surface deviation audit. Tip clearance reference from NASA test log “R37 Bench Cal 1983-04,” scanned and digitized; a second independent transcription agreed within 1 µm RMS.
- Operating conditions: P0,in and T0,in anchored to test cell ambient data (calibrated Rosemount pressure transducers, Type-T thermocouples). Reported instrumentation accuracies: ±0.5% FS for pressure, ±0.3 K for temperature. We applied a 0.38 correlation coefficient between P0,in and T0,in based on concurrent time histories (co-heating in the plenum).
- Boundary-layer state: The test employed polished blades; no trip dots were used in the data of interest. We assumed fully turbulent walls; a trial transitional run (γ–Reθ) shifted losses by <0.3 percentage points and affected shock location by <1% chord; decision: retain fully turbulent assumption for consistency with common Rotor 37 practice.
- Secondary parameters: Turbulence intensity at inlet was not directly measured; a 3–7% range was explored during sensitivity screening; 5% used as nominal.
- Dependencies: Rotational speed and inlet total temperature exhibit mild coupling in the test cell. For uncertainty propagation we applied ρ = 0.21 between speed and T0,in from recorded thermal soak trends.

4. Modeling Assumptions and Their Rationale

- Steady flow: Time-averaged solution assumed sufficient for design-point assessment; unsteadiness from tip-leakage–shock interaction expected to be modest at near-choke and design flow points. We did not model rotating stall or broadband tonal content.
- Single-passage with circumferential averaging: Stator absent, reflecting the rotor-alone rig data set; mixing-plane placed downstream to reduce spurious reflections.
- Adiabatic walls: Justified by short run durations and low Biot number; wall heat flux estimated a posteriori to be <0.5% of total enthalpy flux.
- Gas model: Ideal gas, γ = 1.4, R = 287 J/kg-K; Sutherland’s law for viscosity.
- No roughness: Surface roughness in the rig was below 0.5 µm Ra; roughness sensitivity in a separate run changed efficiency by <0.1 percentage points.

5. Checks on the Solver and Numerics

- Code trust: For compressible flows, CFX 2023 R2 passed the vendor’s regression suite. Internally, our group ran the 2D subsonic/vortex MMS case and inviscid isentropic nozzle benchmarks; observed L2 error reduced at ~1.97 order for linear elements and ~2.85 with curvature-based reconstruction on a series of structured meshes. While not an exact MMS for RANS, these tests establish expected accuracy for the underlying advection–diffusion–pressure coupling. No deviations from the standard solver were made.
- Cross-code comparison: One design flow point replicated in SU2 v8.0.1 (RANS, SST) on a 3.2M-cell grid with matched wall spacing; pressure ratio differed by 0.7%, efficiency by 0.5 percentage points, and exit flow angle by 0.6 degrees at 90% span. Shock location discrepancy < 1.5% chord.
- Unit and sign audits: Automated pre-run QA checks flagged zero inconsistencies across 11 unit conversions and 7 vector directions (e.g., rotation sign, swirl convention).

6. Mesh and Iterative Error Assessment

A three-level grid study was performed at 100% design speed near peak efficiency:
- Coarse: 1.2M cells, first-layer Δn = 2.0e-6 m
- Medium: 3.4M cells
- Fine: 9.1M cells, first-layer Δn = 8.0e-7 m; 52 cells across tip gap; 420 points along blade-to-blade direction

Observed details:
- Global pressure ratio (fine–medium–coarse): 2.106, 2.099, 2.082; estimated apparent order p = 1.95; extrapolated Richardson value 2.110; grid-convergence index (95% conf.) relative to fine grid = 0.85%.
- Adiabatic efficiency (fine–medium–coarse): 0.827, 0.822, 0.809; p = 1.88; GCI = 1.2%.
- Exit flow angle at 90% span: 61.4°, 61.0°, 60.1°; p = 1.74; GCI = 1.6%.
- Tip-leakage vortex core location varied by <0.3% span between medium and fine.
- Residuals reduction: >4 orders in continuity and momentum; turbulence equations >3.5 orders. A restart continuation on each grid confirmed iterative error under 0.1% on integral metrics.

Based on the GCI, numerical discretization uncertainty contributes roughly ±0.9% (pressure ratio) and ±1.2 percentage points (efficiency) at the design condition.

7. Agreement with Experimental Evidence

The following comparisons were made using the NASA Rotor 37 rig measurements at 100% and 98% design speed:

- Operating map near design speed:
  - Predicted peak efficiency flow coefficient φ = 0.505 vs test 0.498 (Δφ = +0.007)
  - Pressure ratio at peak efficiency: CFD 2.099 (medium grid) vs test 2.068 (+1.5%); within target
  - Choke mass flow: CFD 20.83 kg/s vs test 20.56 kg/s (+1.3%); within target
- Spanwise profiles at rotor exit plane (x/Cax = 1.5):
  - Total pressure: within ±1.5% over 10–90% span; slight overprediction near 90–95% span coincident with stronger modeled tip-leakage re-energization
  - Flow angle: within ±1.2° at 50% and 90% span; larger deviation (1.8°) at 20% span where hub corner separation is marginally under-resolved on medium grid
  - Mach number: shock-strength prediction matched to ±0.03 in peak M; shock location ahead of data by ~2% chord near midspan
- Boundary of applicability: At 95% speed approaching stall, the RANS model underpredicts blockage growth; efficiency deviation increases to 3.3 percentage points and the shock moves upstream by ~4% chord relative to data. These off-design points are outside the agreed use case.

Validation data handling:
- Raw data digitized from NASA reports and cross-checked against tabular appendices; barometer drift corrected using logged plenum measurements.
- Uncertainty bands from the test (e.g., ±0.8% for pressure ratio) are shown in the analysis record; CFD predictions were compared against centroids with due attention to these intervals.

8. How Inputs Affect Outputs

We explored the impact of uncertain inputs on outputs using Latin Hypercube Sampling (250 samples) centered about nominal conditions:
- Input ranges and distributions:
  - Tip clearance: 0.356 ± 0.02 mm (uniform)
  - Inlet T0: 288.15 ± 0.6 K (normal)
  - Inlet P0: 101.3 ± 0.7 kPa (normal), correlated with T0 (ρ = 0.38)
  - Turbulence intensity: 3–7% (triangular, mode 5%)
  - Blade chordwise offset (manufacturing clocking): ±0.02° (normal)
- Surrogate construction: Gaussian process regressor trained on 120 sample runs (medium grid), 5-fold cross-validated R2 = 0.985 for pressure ratio and 0.972 for efficiency
- First-order Sobol-like indices from the surrogate:
  - Tip clearance: 0.56 (pressure ratio), 0.49 (efficiency)
  - Inlet T0: 0.18, 0.22
  - Turbulence intensity: 0.14, 0.19
  - P0 (conditional on T0): 0.07, 0.05
  - Manufacturing clocking: <0.02, <0.02
- Nonlinear interactions (notably clearance × turbulence intensity) contribute ~0.07 on efficiency

Propagated uncertainty at design speed (95% confidence):
- Pressure ratio: 2.099 ± 0.031 (includes numerical + input + surrogate error)
- Adiabatic efficiency: 0.822 ± 0.021

9. Analyst Qualifications and Use History

- The analyst has 9 years’ experience with turbomachinery CFD and authored two internal best-practice notes on transonic compressors. Toolchain used here was also applied to NASA Stage 35 and the ERCOFTAC T3 cases, with documented performance: pressure ratio errors <2% in six prior compressor validation cases.
- The same solver setup (SST, y+ ~1) has been used in three concept studies that proceeded to wind tunnel testing; average discrepancy to rig data on pressure ratio and flow angle were 1.7% and 1.1°, respectively.

10. Process Control, Traceability, and Reproducibility

- Version control: All meshes, case files, and scripts tracked in GitLab project “cfd-rotor37” (repo ID 3841), tag v1.3.2 corresponds to the results in this report. Mesh generator commit 7fdc4a9; CFX definition files commit 2c33b54.
- Configuration management: A manifest file (YAML) captures solver version, turbulence options, convergence criteria, and post-processing operations. A CI pipeline validates the manifest before runs are dispatched.
- Platform: Runs executed on “HERA” cluster; Intel Xeon Gold 6338N, 2.2 GHz, 128 cores per node; CFX in double precision; MPI OpenMPI 4.1.5. Solver run logs, hardware info, and job scripts archived under /project/rotor37/runs/car_revB.
- Reproducibility check: An independent rerun of the design-point case on different nodes produced pressure ratio within 0.03% and efficiency within 0.05 percentage points of the archived result.

11. Independent Scrutiny

- Internal review: A cold-eyes review was performed by the Aerodynamics Methods Working Group on 2026-07-02. Two actions were raised: (1) justify fully turbulent assumption, (2) quantify inlet turbulence sensitivity. Both are addressed in Sections 3 and 8; actions closed on 2026-07-15.
- External check: A separate engineer (not part of the project team) reproduced a single design-point case in SU2 (Section 5). Review sign-off (Doc R37-IND-CHK-2026-07) is attached to the record.
- Human error mitigation: A pre-run checklist is used to prevent common pitfalls (unit mismatches, rotational direction, shroud boundary definition). No deviations recorded in this campaign.

12. Data Screening and Correlation Handling

- Measurement noise: The test plenum exhibited low-frequency drift in P0 and T0. We applied a moving-average filter (window 1 s) to align CFD steady-state comparisons with quasi-steadied rig values.
- Dependence modeling: Joint variations in P0 and T0 were included in the uncertainty propagation. In the validation comparisons, we used synchronized P0–T0 pairs from the test timeline to set the CFD inlet state.
- Outliers: Two data points at 98% speed and low flow exhibited anomalous torque readings; these were flagged in the test documentation and excluded from CFD comparison as non-representative.

13. Robustness to Modeling Choices

- Turbulence model swap: SA-BCM model increased efficiency by +0.9 percentage points relative to SST and moved the shock 1.1% chord downstream; pressure ratio change +0.6%. SST retained due to better agreement with spanwise loss trends.
- Numerical scheme variations: Switching to bounded high-resolution advection altered pressure ratio by +0.2% and efficiency +0.1 percentage points. Gradient limiter off produced minor oscillations near the shock; limiter on retained.
- Boundary condition perturbations: ±0.3% change in back-pressure changed pressure ratio by ±0.25%; pressure-slope near choke matched test trendline within uncertainty.

14. Limits of Applicability

- Flow regimes near stall (φ < 0.46 at 100% speed) are not adequately captured by steady RANS; unsteady separation and rotating structures are not represented. Predictions in this regime exceed the PDR error budget.
- Surface heat transfer and conjugate effects were not modeled; not relevant to the intended use but pertinent for thermal-margin studies.
- Manufacturing deviations beyond ±0.05 mm in tip clearance or leading-edge bluntness are outside the explored uncertainty ranges.

15. Results Summary Relative to Use Case

- For 98–102% design speed at near-peak efficiency flows:
  - Pressure ratio within +1.5% of rig data
  - Efficiency within +2.1 percentage points
  - Exit flow angle within ±1.5° at specified spans
  - Choke mass flow within +1.3%
- Combined uncertainty bands (95%) overlap test intervals for all primary metrics. Numerical error contribution is subdominant to tip-clearance uncertainty.

16. Documentation Completeness

- This report, the V&V plan (VV-PLN-ROTOR37-2026-01), the mesh-convergence memo (MESH-ROT37-2026-02), and the independent review note are stored in the project SharePoint “Propulsion CFD/Rot37” folder and mirrored in the GitLab wiki. Scripts to reproduce figures, together with raw and processed datasets, are in the repo under /postproc. Each figure in the internal slide deck links back to the source data via a persistent file hash.

17. Decision and Acceptance for Use

Given:
- Direct comparisons to high-quality rig data within the agreed margins for the intended operating window,
- Quantified numerical and input-driven uncertainties,
- Sensitivity analysis demonstrating dominant drivers are understood (tip clearance, inlet state),
- Stable and reproducible numerics,
- Independent replication and peer scrutiny,

we judge the CFD results to be fit for PDR-level performance estimates in the stated domain of use. Use beyond that domain (stall proximity, off-design speeds below 95%) requires additional unsteady simulation and likely LES/RANS hybridization.

18. Open Issues and Risk Items

- Residual model-form uncertainty in shock–tip-leakage interaction may still bias spanwise loss near 90% span. Planned action: a focused unsteady RANS test at one design-point case by M6 FY26 Q4.
- Validation breadth at 102% speed is limited to three flow points. If map coverage is expanded at this speed, we will add two more points for comparison.
- Tip-clearance uncertainty dominates. Coordination with test leads to narrow the clearance tolerance would most effectively reduce total prediction uncertainty.

19. Compliance and Governance Items

- Roles and responsibilities documented in the V&V plan; analyst and reviewer were independent; approver not directly involved in execution.
- Training: The analyst completed “CFX for Compressible Turbomachinery” (Ansys, 2025) and internal best-practice refresher (2026).
- Risk acceptance: The Chief Engineer’s memo (CHENG-PROP-2026-15) records acceptance of residual risks for PDR use.

20. Key Numbers at a Glance

- Medium-grid cell count: 3.4M; y+ ≈ 1
- Convergence: mass imbalance <0.02%
- Grid-convergence uncertainty: PR ±0.85%, η ±1.2 p.p.
- Validation errors (design window): PR +1.5%, η +2.1 p.p., choke +1.3%
- 95% output uncertainty (propagated): PR ±0.031, η ±0.021
- Dominant sensitivity: tip clearance accounts for ~56% of PR variance

21. Methodological Notes and Rationale

- Why SST with curvature correction: Better captures adverse pressure-gradient separation and shock-induced boundary-layer thickening than SA in our prior compressor studies; curvature correction suppresses spurious production in swirling regions.
- Why steady RANS: Time-averaged outputs are the target metrics; unsteady effects primarily modulate instantaneous loads and broadband spectra, out of scope for PDR performance mapping.
- Why mixing plane: Avoids circumferential periodicity artifacts downstream of the rotor and provides a consistent averaging surface for exit quantities; suitable for rotor-alone comparisons.

22. Evidence Map (Where to Find What)

- Mesh refinement details and residual plots: repo /mesh_study/design100p/ and memo MESH-ROT37-2026-02
- Validation overlays to rig data: repo /validation/overlays/ and fig scripts /postproc/plot_validation.py
- UQ and sensitivity notebooks: /uq/rotor37_uq.ipynb with run manifest uq_manifest.yaml
- Independent replication log: /indep_check/su2_compare/log.md

23. Summary Judgment

- Soundness of the physical representation: Adequate for the intended operating conditions; assumptions are explicit and supported by sensitivity trials.
- Numerical soundness: Verified via grid refinement, balance checks, and limited code-to-code comparison; no signs of iterative contamination.
- Data foundation: Inputs and validation data are well-documented, quality-controlled, and appropriately synchronized; known correlations are included.
- Governance: Roles, reviews, and configuration control are in place, and the trail from requirement to result is auditable.

24. Recommendations

- For CDR-level credibility, expand the validation matrix at 102% speed and add at least one unsteady RANS point near the design flow to further quantify shock–tip-leakage effects.
- Reduce dominant uncertainty by tightening tip-clearance tolerance in forthcoming tests or by measuring it more precisely during runs and conditioning CFD inputs accordingly.
- Consider a limited DES at high span to calibrate the modeled mixing and refine the spanwise loss prediction, if schedule permits.

Appendix A: Quick Checklist of Common Pitfalls and Their Status

- Rotation sign and magnitude aligned with geometry: Checked
- Frame change at mixing plane: Conservative flux treatment verified
- Hub/shroud boundary set to no-slip adiabatic: Confirmed
- Inlet reference frame for swirl: Stationary, no pre-swirl: Confirmed
- Blade count and pitch: 36 blades, 10° sector with periodicity: Confirmed
- Inlet turbulence intensity and length scale: 5%, 0.1Cax: Set
- Units for clearance and chord: mm vs m cross-checked: Confirmed
- Post-processing planes matched to rig rake locations: Confirmed
- Convergence judged on forces and integral metrics, not residuals alone: Confirmed

End of Report
