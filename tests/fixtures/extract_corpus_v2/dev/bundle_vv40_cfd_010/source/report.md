# Credibility Assessment Report: CFD of a 300-mm Centrifugal Pump for Head–Flow and NPSHr Predictions

Prepared by: Fluids Modeling Group, HydroSys Engineering  
Date: 2026-08-06  
Software: Ansys CFX 2024 R1 with cavitation model plug-in v3.2 (ZGB), ICEM CFD 2023 R2 for meshing  
Repository: HSE-CFD-PMP-300mm (GitLab internal)

## 1. Background and Intended Use

The modeling effort supports selection and performance assurance for a 300-mm, six-bladed radial pump intended for a municipal water booster station. Decisions to be informed by the analysis:

- Predict head vs. flow near the duty region (0.8–1.2 Qd at 1450 rpm) for water at 25 ± 2 °C
- Estimate the onset of cavitation per the 3% head-drop criterion (NPSHr) for sigma in the range 1.5–3.0
- Rank-order two impeller trims for efficiency at the duty point

Consequences of an incorrect prediction are moderate: a mismatch of >3% in head could drive motor oversizing or unplanned rework; NPSHr underestimation could shorten seal life but is not safety-critical. We rate decision importance as “medium” and therefore set a correspondingly high bar for technical rigor in numerical quality checks and experimental corroboration, while allowing practical trade-offs (e.g., steady RANS suffices in the head-flow region, with targeted unsteady checks for cavitation onset).

The scope excludes erosion prediction, tonal noise, and off-design operation beyond ±30% of Qd.

## 2. Model Setup and Governing Choices

We modeled the full 360° impeller and a 180° volute with a stationary/rotating interface. The flow is assumed incompressible (water at 25 °C, density 997 kg/m³, viscosity 0.89 mPa·s). We used RANS with the SST k–ω model (Menter) and automatic curvature correction enabled. Wall treatment is low-Re (integrated to the wall), no wall functions on the final production mesh.

Cavitation physics were included via a homogeneous mixture approach with the Zwart–Gerber–Belamri mass transfer model. Bubble nuclei density and reference diameter (default 5e8 m⁻³ and 10 μm) were treated as uncertain and explored; the primary prediction set uses 8e8 m⁻³ and 12 μm as motivated later.

Boundary conditions:

- Inlet: total pressure prescribed to match available NPSHa in the test campaign or flat axial velocity for non-cavitating runs. Turbulence intensity at the inlet nominally 4% with 0.05 m length scale.
- Outlet: mass flow rate specified.
- Impeller rotation: 1450 rpm via frozen-rotor approach for steady cases; sliding mesh for select unsteady cavitation checks.
- Surface roughness: uniform equivalent sand-grain roughness ks = 8 μm (cast and bead-blasted stainless, measured Ra ≈ 3.2 μm, converted using ks ≈ 2.5 Ra).

Assumptions and omissions:

- Single-phase liquid, no gas content aside from cavitation nuclei; isothermal.
- No shaft seal leakage modeled; leakage was measured negligible in the test bench and corrected in reported H–Q data.
- Geometric clearances used as-manufactured (impeller–casing radial clearance 0.3 mm); no wear.

## 3. Implementation Controls and Software Discipline

- Tools were locked to specific builds: CFX 2024 R1 build 2024.1.31; ICEM 2023 R2. We archived the installer hashes and license features in the repository.
- Template files for solver settings (turbulence, discretization, relaxation) were used across runs; a team member not involved in setup performed a checklist review before execution.
- Automated sanity checks (Python scripts) parse solver logs to flag runs with residual plateaus >1e-4, mass imbalance >0.2%, or monitor drift over 500 iterations.
- Versioning: meshes, case files, and post-processing notebooks are in a Git repository. Each run is tagged with a semantic version and a metadata .yaml capturing boundary values, solver controls, and mesh identifiers.
- We ran the vendor-supplied regression suite “CFX Turbomachinery Pack” for this build and compared residual trends and key outputs to published baselines; no deltas exceeded vendor tolerances.

## 4. Input Characterization and Data Pedigree

Geometry came from the released CAD (ECO P-300-IMP-2), cross-checked against CMM measurements on the test article. Leading-edge radius and blade thickness deviations were within 0.08 mm of nominal. Surface roughness measurements were made on three impeller blades and the volute tongue; mean Ra 3.2 μm (std 0.6 μm). We adopted ks = 8 μm as baseline and carried ±20% as uncertainty.

Inlet turbulence was not measured on the rig; we inferred it from upstream straight lengths and strainers, setting 4% as nominal. We conducted a parameter sweep from 1% to 8% and found head at Qd varied by ±0.5% across that range.

Thermophysical properties were set from IAPWS at 25 °C. Speed was fixed at 1450 ± 0.2% rpm in both test and CFD. Flow rate is imposed in CFD; in tests, it is controlled via a calibrated valve and turbine meter (±0.5%).

Cavitation parameters (nuclei density and diameter) lack direct measurement; literature ranges for clean water give 10⁷–10⁹ m⁻³ and 5–50 μm. We treated these as calibration knobs constrained by non-design data, as explained in Section 7.

## 5. Numerical Quality: Grid, Time, and Solver Behavior

Meshing strategy used a multi-block hexahedral topology in the blade passages and prism layers at walls. We generated three systematically refined meshes:

- L1: 2.1 million cells, y+ ≈ 5 on blades and volute.
- L2: 4.5 million cells, y+ ≈ 0.9 on blades, 1.2 on volute.
- L3: 9.4 million cells, y+ ≈ 0.5 across all walls.

Refinement maintained near-uniform growth ratios (≤1.2) and resolved tip gap with ≥12 cells across clearance at L3.

At Qd, the predicted head differed by 3.0% between L1 and L2, and 1.7% between L2 and L3. Using Richardson extrapolation (apparent order 1.92) we estimate numerical uncertainty on head at Qd of 0.9% for L2 and 0.5% for L3. We chose L2 as the production mesh for parametric studies and uncertainty propagation based on the diminishing returns at L3.

Steady cases used second-order upwind for advection, bounded central differencing for turbulence variables. Residuals dropped below 1e-5 for continuity and momentum and below 1e-6 for turbulence scalars; global mass imbalance <0.1%. Monitors of head and torque flattened within 0.2% over the last 800 iterations.

For cavitating flows near sigma ≈ 1.8–2.0, we ran unsteady calculations to ensure the steady approximation did not conceal oscillatory behavior. Time step 0.5°/step (720 steps/rev) with second-order time integration. A refinement to 0.25°/step changed the mean head by 0.6% and the onset of 3% head drop by 0.12 m of NPSHa; we carry 0.2 m as temporal resolution uncertainty.

## 6. Response to Inputs: Screening and Ranking

We applied a one-at-a-time sweep around Qd on the L2 mesh:

- Inlet turbulence intensity 1–8%: head shift ±0.5%; NPSHr shift 0.08 m
- Roughness ks 6–10 μm: head shift ±0.7%; NPSHr shift 0.05 m
- Bubble diameter 8–20 μm: negligible effect on head in non-cavitating regime; NPSHr shift up to 0.4 m

Then, we performed a Morris screening on five factors (flow, ks, inlet TI, bubble diameter, nuclei density) for the cavitating condition sigma ~2.2. The largest elementary effects were bubble diameter and flow rate for the NPSHr metric, and flow rate and roughness for head.

This ranking informed the uncertainty propagation choices (Section 9) and guided which parameters merited refined priors and calibration.

## 7. Tuning Activity and Partitioning of Data

We used a single off-design data point (0.9 Qd at sigma = 3.0, non-cavitating) to select between two turbulence options: SST with vs. without curvature correction. The variant with curvature correction reduced overprediction of head from 3.8% to 2.1%. No coefficients in the turbulence model were altered.

For cavitation, we adjusted the bubble diameter within literature bounds to reproduce the measured 3% head drop at 1.1 Qd and sigma = 2.5 on L2. The selected value was 12 μm. This datum was not used in subsequent validation comparisons; all other validation points were held independent.

We recorded these adjustments with a calibration log and tagged the setup as PMP300-SSTcc-ZGB-b12um. The decision to calibrate only to a single point mitigates the risk of overtuning and preserves the integrity of the validation set.

## 8. Experimental Comparisons

The manufacturer tested the pump on a closed-loop stand following ISO 9906 Grade 2B. Instrumentation:

- Head: differential pressure transducers, ±0.25 m expanded uncertainty (k=2), temperature-compensated
- Flow: turbine meter, ±0.5% of reading
- Speed: optical tachometer, ±0.2%
- NPSHa controlled via suction tank pressure and measured via static taps at 2D upstream

Data sets considered:

- H–Q at 1450 rpm, sigma ≥ 6 (non-cavitating), 0.8–1.2 Qd in 0.05 Q increments; 3 repeats each. Combined uncertainty on head: 0.35 m.
- NPSHr determination per 3% head-drop criterion at 1.0 Qd and 1.1 Qd; stepwise decrease of NPSHa in 0.2 m increments until 5% head loss.

We assessed test quality:

- Repeatability: stdev in head <0.3% across repeats near Qd; <0.6% at 0.8 Qd
- Rig corrections: leakage and mechanical losses were measured and corrected; corrections were <0.5% of head
- Geometric match: the test article was the same impeller and volute pair as modeled; clearances and roughness within measured bounds

Comparison metrics:

- For H–Q: mean absolute percentage error (MAPE) over 0.8–1.2 Qd
- For NPSHr: absolute difference in NPSHa at 3% drop

Results:

- H–Q: mean bias +1.7%, MAPE 2.0% on L2; within combined numerical + experimental uncertainty band at all six flows
- NPSHr at 1.0 Qd: CFD predicted 4.3 m; test 4.5 m ± 0.3 m; difference −0.2 m
- NPSHr at 1.1 Qd: CFD 5.1 m; test 5.0 m ± 0.3 m; difference +0.1 m

Residuals showed no systematic drift across the flow range. At 0.8 Qd, the turbulence model slightly underpredicts recirculation, yielding a 2.9% head overprediction; still within acceptance for stated decisions.

## 9. Applicability to Field Use

The plant installation downstream piping is longer than the test rig (10D vs. 5D), and includes a single 90° elbow 6D upstream of the pump. We modeled inlet as uniform without swirl; thus, swirl-induced non-uniformity is not represented. Field measurements on a similar line showed inlet swirl could shift efficiency by ~0.3 points and head by ~0.5%. We consider this a small effect relative to other uncertainties but note it as a limitation (Section 13).

Fluid properties, speed, and working fluid match the test conditions. The operating envelope of interest (0.8–1.2 Qd, sigma 1.5–6) lies within the validation space, with only mild interpolation for cavitation onset. Extrapolation to lower sigma (<1.5) or to throttled operations beyond 1.2 Qd is not supported.

## 10. Accounting for Uncertainty in Outputs

We combined multiple sources:

- Numerical resolution: from mesh/time studies, ±0.9% on head at L2, and ±0.2 m on NPSHr
- Experimental uncertainty: per ISO 9906, ±0.35 m on head and ±0.3 m on NPSHr, used for validation residual weighting only
- Inputs:
  - ks ~ Uniform[6, 10] μm
  - Inlet turbulence intensity ~ Triangular(3, 4, 6) %
  - Bubble diameter ~ Triangular(8, 12, 20) μm
  - Nuclei density fixed at 8e8 m⁻³; sensitivity found sub-dominant in our regime

We executed 60 Latin hypercube samples on the L2 mesh over these input distributions for non-cavitating H–Q and for NPSHr at 1.0 Qd. The response surfaces are approximately linear in the small neighborhoods sampled.

Combined output uncertainty (one sigma):

- Head at Qd: ±1.5% (dominated by numerical resolution and roughness)
- NPSHr at 1.0 Qd: ±0.28 m (dominated by bubble diameter and temporal resolution)

We provide 95% confidence intervals by scaling assuming normality: ±3.0% for head; ±0.56 m for NPSHr. These envelopes encompass the observed discrepancies with test data.

## 11. Documentation, Reproducibility, and Traceability

We produced a run ledger listing:

- Mesh IDs (L1, L2, L3) with cell counts and y+ statistics
- Boundary values and turbulence parameter selections
- Solver control summaries
- Commit hashes for all case files

Post-processing was scripted in Python with PyVista; all figures are re-creatable by running make figures after cloning the repository. Two team members reproduced the Qd L2 run from scratch on different hardware (Windows workstation, Linux cluster); differences in head were <0.2%.

Change control: any modification to solver settings or geometry requires an issue ticket and sign-off. The calibration decision in Section 7 went through this process; a deviation record links the adjusted bubble diameter to the excluded calibration data point.

## 12. Human Use and Operational Process

Analysts performing these runs completed internal training on turbomachinery CFD and cavitation modeling. We used a pre-flight checklist to ensure:

- Adequate wall resolution (target y+ < 1)
- Correct rotating frame setup and interface placement
- Proper mapping of NPSHa when cavitation is on
- Convergence criteria met (residuals, mass balance, monitor stability)

A second person audited the setup and run logs for the validation points. Interpretation of results followed a template: report H–Q curves with uncertainty bands, report NPSHr at 3% head drop with uncertainty, discuss deviations and likely causes.

## 13. Results Summary

- Head–flow curve near the duty region: CFD tracks test data within 2% MAPE; numerical uncertainty plus input variability accounts for observed differences. The SST model with curvature correction is adequate for this geometry and flow regime.
- Cavitation onset: Predicted NPSHr at 1.0 Qd and 1.1 Qd matches tests within 0.2 m. The sensitivity to bubble diameter is notable; we constrained it with one non-validated point and literature.
- Mesh/time adequacy: L2 mesh and 0.5° time step (for unsteady checks) deliver stable, grid/time-adequate solutions. Using L3 would marginally reduce numerical error at a significant cost. 
- Software discipline: run-to-run reproducibility verified; vendor regression tests passed; internal QA procedures followed.
- Applicability: context-of-use is well covered by the validation campaigns; small deviations in upstream piping swirl are unlikely to materially change conclusions for head and NPSHr.

## 14. Credibility Appraisal Against Decision Needs

Given the medium consequence of error, our internal acceptance targets were:

- Head–flow: within ±3% of test over 0.8–1.2 Qd; uncertainty bands clearly reported
- NPSHr: within ±0.6 m of test at 1.0 Qd; sensitivity to nuclei characterization understood
- Numerical checks: mesh/time independence with less than 2% change across finest two grids; solver monitors well-behaved
- Data relevance: same hardware, same fluid, matching rpm; measurement uncertainty quantified
- Model physics: equation set and closures appropriate for attached/tip-leakage-dominated turbomachinery flow with mild cavitation
- Process: auditable runs, trained users, and documented steps; independent review performed
- Calibration discipline: limited tuning without contaminating the validation set
- Uncertainty treatment: quantified and propagated dominant sources; combined bands provided

Evidence gathered meets or exceeds these thresholds. The two most influential uncertainties are wall roughness (manufacturing variability) for head and bubble size for NPSHr; both were bounded and propagated. The validation comparisons are within the combined uncertainty at all examined points.

## 15. Limitations and Caveats

- The RANS approach with steady MRF is not suited for resolving detailed cavitation structures or blade-passing pressure oscillations. We do not recommend using this model for erosion risk or noise prediction.
- Extrapolation outside 0.8–1.2 Qd or sigma below 1.5 has not been substantiated. Strong backflow at 0.7 Qd, for example, is poorly captured by SST without transition modeling.
- Upstream swirl and non-axisymmetric inlet profiles are not modeled; field installations with elbows immediately before the suction flange could show different incidence and small shifts in H–Q and NPSHr.
- Bubble nuclei properties were not directly measured; although constrained, they remain a leading source of epistemic uncertainty in NPSHr. 
- Results rely on specific software builds; porting to another solver or version should repeat the basic verification steps.

## 16. Independent Technical Review

An external SME from FlowMetrics LLC reviewed the mesh strategy, solver choices, and the validation comparison plots. The reviewer concurred with the choice of SST with curvature correction and the adequacy of L2 for the presented metrics. Recommendations (implemented) included adding an unsteady cavitation check for NPSHr and reporting combined uncertainty bands on H–Q curves.

## 17. Methodology in Brief

- Built three meshes with systematic refinement and performed a mesh refinement study; computed observed order and estimated numerical uncertainty on L2 and L3.
- Checked time step adequacy for cavitation onset with a refined step; included temporal discretization effects in uncertainty for NPSHr.
- Performed sensitivity screening to prioritize uncertain inputs; used these to define distributions for uncertainty propagation.
- Calibrated a single cavitation parameter against an excluded data point; froze the parameter before validation.
- Compared CFD predictions to ISO 9906 test data with known measurement uncertainty; used simple metrics (MAPE, absolute differences) and visual overlays with error bars.
- Tracked all runs and ensured reproducibility via repository, templates, and peer review.

## 18. Decision

Based on the body of evidence, the pump CFD model described herein is accepted for:

- Predicting head vs. flow for water at 25 ± 2 °C at 1450 rpm in the range 0.8–1.2 Qd, with reported ±3% uncertainty (95% confidence)
- Estimating NPSHr at 1.0–1.1 Qd per the 3% head-drop criterion, with ±0.6 m uncertainty (95% confidence)
- Ranking two impeller trims by efficiency near the duty point

The model is not accepted for erosion risk, noise, or operation outside the validated envelope (sigma < 1.5 or flow outside 0.8–1.2 Qd). Acceptance was decided by the HydroSys Engineering Modeling Review Board on 2026-08-06.

## 19. References and Data Access

- ISO 9906:2012, Rotodynamic pumps—Hydraulic performance acceptance tests
- Menter, F.R., Two-Equation Eddy-Viscosity Turbulence Models for Engineering Applications, AIAA Journal, 1994
- Zwart, P.J., Gerber, A.G., Belamri, T., Two-phase flow model for predicting cavitation dynamics, 5th Int. Conf. Multiphase Flow, 2004
- Repository: gitlab.hsesys.local/hse-cfd/PMP300 (access restricted; request via Modeling Group)

Appendices (mesh statistics, run logs, and comparison plots) are available in the repository under docs/.

---
