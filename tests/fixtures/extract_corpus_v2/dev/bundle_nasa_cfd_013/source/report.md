# CFD Credibility Assessment Report — Bleed-Air Mixing Tee for Crew ECLSS
Project: Orion-ECLSS-1042  
Analyst: J. L. Whitaker (Aerosciences and Thermal Group)  
Date: 2026-08-06  
Standard referenced: NASA-STD-7009B (applied as guidance for credibility evidence)

Executive summary: We assessed a steady-state CFD model of a bleed-air mixing tee used in the crew environmental control and life support subsystem (ECLSS). The model predicts two primary quantities for the Phase II design trades: (1) total pressure loss across the tee at nominal and off-nominal flow splits; and (2) a spatial uniformity index of mixed-out temperature at 2 duct diameters downstream of the junction. The simulation setup, inputs, and results were reviewed against internal test data from the ECS Manifold Test Rig (EMTR) at JSC, and against process controls for software, data pedigree, and analyst proficiency. Within the declared operating window (Mach 0.05–0.2, Reynolds 2.0e5–7.0e5 per inlet, dry air, 20–80 °C, no condensation), the model reproduces measured pressure losses within 3.1% and mixed-out temperature non-uniformity within 7.8%. Estimated 95% uncertainty is 6% for pressure loss and 9% for non-uniformity. The model is accepted for pre-PDR performance predictions and design trades as stated in the Decision section.

## 1. Background and Use Case
The mixing tee under study blends warm bleed air with cooler recirculated cabin air and must meet pressure drop and thermal uniformity limits to avoid over-sizing the compressor and to maintain crew comfort. Program-level requirements flow down to two computed metrics:

- Δpt across the tee must be predicted to within ±10% to support compressor margin allocation.
- The downstream mixed-out temperature non-uniformity index (root-mean-square of temperature deviation normalized by mean) must be predicted within ±15% to guide placement of sensors and downstream acoustic liners.

The CFD model serves as a design-analysis tool for the Phase II manifold geometry trade study. It will not be used for certification; instead, it screens design variants and sets priorities for follow-on test articles.

## 2. Geometry, Flow Regime, and Simplifications
- Geometry: CAD Rev. C of the mixing tee (part 221-9113-C), with two inlets (A and B) joining a main outlet. Internal features include a 7° diffuser in the outlet, a 6 mm fillet at the A-branch junction, and one pressure tap boss. Bolted flange details, o-ring grooves, and tiny vent holes are excluded; their volumes are below 0.2% of the wetted volume.
- Surface roughness: Modeled as equivalent sand-grain roughness ks = 30 μm on all internal walls (vendor spec 20–40 μm).
- Physics scope: Subsonic, mildly compressible (M ≈ 0.1), single-phase dry air. Thermal boundary assumed adiabatic; CHT neglected. A heat-leak check (see Section 9) indicates wall heat transfer would shift mixed-out temperature by <1.2% at nominal duty.
- Assumptions: Steady operating point; turbulence fully developed into the junction. No acoustic or unsteady vortex shedding resolution in the baseline model (steady RANS used). An exploratory unsteady run indicates minimal impact on mean quantities (Section 6).

The operating matrix covers mass-flow splits 70/30, 50/50, and 30/70 between A and B, with total flow 0.6–1.3 kg/s.

## 3. Software, Numerics, and Controls
- Solver: ANSYS Fluent 2023 R2, double precision, pressure-based coupled solver. Turbulence modeled with k–ω SST (Menter), curvature correction enabled; low-Re wall treatment with y+ ≈ 1 in all cases. Compressibility effects treated via ideal-gas density.
- Discretization: Second-order upwind for momentum and energy; second-order for turbulence equations. Gradient reconstruction weighted least squares. Pressure-velocity coupling via coupled scheme with pseudo-transient under-relaxation.
- Convergence metrics: Residuals reduced by ≥5 orders of magnitude for all equations; global mass imbalance ≤0.1%; monitored outlet mass-averaged temperature and static pressure stabilized to within 0.1% over 200 consecutive iterations.
- HPC environment: NASA Pleiades (Sierra nodes), Intel Xeon 6148, 240 cores per case, Infiniband HDR. Parallel partitioning by Scotch with 2% load imbalance. All runs logged with solver journal scripts and environment module hashes.
- Solver reliability: The team maintains a standing battery of code checks (lid-driven cavity, Poiseuille, 2D MMS for diffusion) that are rerun on each solver upgrade. For 2023 R2, these checks reproduced published solutions within 0.5–1.2% norms. Vendor’s standard verification suite results were also reviewed; no anomalies were observed for pressure-based flows at the target Mach numbers.

## 4. Sources and Quality of Inputs
- Inlet conditions: Each branch mass flow set by test stand Coriolis meters (Micro Motion CMF050), accuracy ±0.5% of reading. Turbulence intensity at inlets set to 5% nominal (range 1–10% in sensitivity). Velocity profiles at inlets assumed fully developed from 25D straighteners; confirmed by pitot rake traverse to within ±2% of centerline maximum.
- Thermal inputs: Branch A temperature 55–65 °C; Branch B 22–28 °C in tests. In CFD, these are imposed as total temperatures. EMTR thermocouples are Type T, ASTM E230 Class 1; we adopt ±0.5 °C measurement error.
- Wall roughness ks = 30 μm with ±25% uncertainty from vendor and profilometer spot checks (three locations).
- Gas properties: Dry air, Sutherland’s law; no humidity modeled. Test facility dew points were below 2 °C; condensation not observed.

All input values are stored in the case logs and summarized in the data book EC-DB-1042-RevA.

## 5. Geometry and Boundary Condition Fidelity Checks
- CAD-to-mesh fidelity: IGES import of Rev. C validated by overlaid cross-sections with <0.05 mm deviation. Pressure tap boss stubs included to match local flow disturbances seen in PIV; tolerance ±0.1 mm.
- Downstream sampling plane: Located 2D after the junction per requirement. Its position matches the PIV laser sheet plane in the EMTR test to within 1 mm, using a coordinate transform documented in TB-EMTR-Alignment-03.
- Branch inflow alignment: The test stand had a 1.2° misalignment of branch A due to flange tolerances; this was reproduced in the CFD by rotating the inlet patch normal.

## 6. Numerical Checks: Iteration, Grid, and Temporal Effects
- Steady solver convergence: All cases reached the residual and monitor criteria described above, with final Courant ~20 for coupled scheme.
- Time dependence assessment: One representative case (50/50 split, total 0.95 kg/s) was rerun as URANS (second-order implicit, 1e-4 s time step, 10 flow-through times). Mean Δpt shifted by 0.7%, non-uniformity by 1.1% relative to steady-state. This supports the steady approximation for mean metrics.
- Mesh refinement study: Three poly-hexcore meshes with 10 prism layers:
  - Coarse: 5.2 M cells, BL first height 8 μm
  - Medium: 9.1 M cells, BL first height 5 μm
  - Fine: 18.4 M cells, BL first height 3 μm
  Extrapolated using Richardson for Δpt yielded an estimated discretization uncertainty of 1.8% (95% CL). For temperature non-uniformity, the observed order was lower (p ≈ 1.7), giving 3.2% estimated numerical error, reflecting sensitivity to small-scale recirculation in the junction.
- Wall resolution: y+ in 0.3–1.5 over 95% of wetted area; limited regions near the junction lip reached y+ ≈ 2.4 on the coarse mesh, reduced below 1.2 on medium and fine.

## 7. Benchmarks Against Testing
- Facility: EMTR at JSC, ambient pressure, adjustable heaters upstream of branch A, 16 static taps per leg, and planar PIV at 2D downstream in the outlet. Test report TR-EMTR-2026-07 documents procedures and calibrations.
- Pressure loss: CFD Δpt vs measured for nine operating points produced a mean absolute deviation of 3.1%. The worst case was 30/70 split at the low-flow condition, with a 4.8% high bias from CFD.
- Temperature mixing: Mixed-out temperature non-uniformity (rms/mean) from CFD vs PIV-derived scalar proxy (after bias correction) agreed within 7.8% on average. The comparator applied a scalar transport equation in postprocessing for PIV intensity-to-temperature mapping; the mapping uncertainty is included in the error bars (±5%).
- Flow features: Predicted recirculation bubble length at the junction matched PIV within 6 mm (measured 34 ± 3 mm; CFD 30–33 mm). Peak swirl angle at 2D downstream was within 1.9 degrees of hot-wire anemometry.
- No case-specific tuning was applied; the same turbulence model and wall roughness setting were used across the matrix.

## 8. Sensitivity and What-If Probes
- Inlet turbulence intensity varied 1–10% resulted in <0.6% change in Δpt and up to 4.1% change in non-uniformity, with the largest effect at 30/70 split.
- Wall roughness varied ±25% shifted Δpt by ±1.5% and non-uniformity by ±0.9%.
- Turbulence model substitution from k–ω SST to Spalart–Allmaras (with rotation/curvature correction) changed Δpt by −2.4% and increased non-uniformity by 3.5% on average. Flow structures remained consistent; SA underpredicted junction separation slightly.
- Thermal boundary: Applying a constant heat-flux of 100 W/m2 (representative upper bound from mounting brackets) increased mixed-out non-uniformity by 1.2% and reduced Δpt by 0.3%.
- Mesh growth rate varied from 1.15 to 1.25 altered results by <0.8% relative to the baseline medium mesh, within the discretization error estimate.

The ranking of influential knobs on the target metrics is: turbulence model choice and inlet turbulence intensity (most), then wall roughness, then remaining numerical settings (least).

## 9. Uncertainty Accounting
We combined contributions assuming independence and used coverage factor 2 for a 95% confidence statement:

- Numerical discretization: 1.8% (Δpt), 3.2% (non-uniformity).
- Iteration/steady vs unsteady: 0.7% (Δpt), 1.1% (non-uniformity).
- Input variations (propagated via one-at-a-time probes and local linearization): 2.0% (Δpt), 4.3% (non-uniformity).
- Measurement uncertainty in validation data (contributes to validation error bars only): 1.0% (Δpt), 5.0% (non-uniformity via PIV mapping).

Net model predictive uncertainty (excluding test measurement terms) is 6.0% for Δpt and 9.0% for non-uniformity. Combined model-to-test comparison including test uncertainty envelopes supports the observed agreements in Section 7.

## 10. Process Control, Traceability, and Toolchain Quality
- Configuration control: Geometry Rev. C and all meshes, cases, and post-processing scripts are under GitLab project orion-eclss-tee-cfd, tag v1.3.2. CI pipelines rebuild meshes (snappyHexMesh legacy workflow to Fluent via mesh conversion) and execute a smoke test on Pleiades. SHA-256 hashes of journals and mesh files are recorded in the run logs.
- Reproducibility: A fresh checkout executed on a separate account reproduced the 50/50 case within 0.2% for Δpt and 0.4% for non-uniformity.
- Software QA: The team uses a software bill of materials (SBOM) and scans for version drift monthly. Fluent 2023 R2 was frozen for this study; a waiver was documented to defer 2024 R1 until this trade study closes.
- Data handling: All test data were assigned dataset IDs with immutable checksums; the test-to-CFD mapping script (align_emtr_plane.py) is peer-reviewed and unit-tested (pytest coverage 91%).

## 11. People, Oversight, and Prior Usage
- Analyst qualifications: J. L. Whitaker, 12 years in internal aerothermal flows; certified internal user for Fluent and STAR-CCM+; completed NASA CFAST training modules in 2016 and annual refreshers. Secondary analyst M. Zhao cross-checked postprocessing.
- Independent review: Two peer reviewers (A. Gomez, IV&V; P. D’Souza, Thermal Systems) held a formal walkthrough on 2026-07-29. Action items were closed (see CR-TEECFD-17) including rerun with adjusted inlet misalignment and an added SA-model comparison.
- Separation of roles: Test campaign led by different personnel (R. Kline, JSC Propulsion Test Branch). The CFD team did not handle PIV calibration; alignment between datasets was audited by IV&V.
- Prior use: The same workflow (SST on poly-hexcore, y+ ≈ 1, Richardson grid study) has been used on three previous ECS junction analyses (projects 2019-112, 2020-087, 2024-031), with average Δpt agreement of 4–6%. Lessons learned from those efforts (importance of matching inlet turbulence levels) were applied here.

## 12. Applicability Envelope and Exclusions
- Valid for: Air as working fluid; Mach 0.05–0.2; total mass flow 0.6–1.3 kg/s; inlet temperature difference up to 40 °C; wall temperature within ±15 °C of mixed air; internal roughness 20–40 μm; no liquid water present; no active acoustic excitation.
- Not covered: High-humidity or condensing conditions; extreme off-design with flow reversal in a branch; vibratory loading that could drive unsteady resonance; ice accretion.
- Extrapolation: Use beyond these bounds increases uncertainty. If applied outside, at minimum repeat the sensitivity study (Section 8) and include larger uncertainty margins.

## 13. Results at Key Operating Points
- Nominal 50/50 split, 0.95 kg/s:
  - Predicted Δpt = 2.06 kPa (±0.12 kPa, 95% model U)
  - Mixed-out non-uniformity index = 0.073 (±0.007, 95% model U)
  - Agreement with EMTR: Δpt +2.4%; non-uniformity −6.1% relative to test central values
- Off-nominal 70/30 split, 1.10 kg/s:
  - Predicted Δpt = 2.61 kPa (±0.16 kPa)
  - Mixed-out non-uniformity = 0.089 (±0.008)
  - Agreement with EMTR: Δpt +3.3%; non-uniformity −7.8%
- Off-nominal 30/70 split, 0.70 kg/s:
  - Predicted Δpt = 1.41 kPa (±0.09 kPa)
  - Mixed-out non-uniformity = 0.081 (±0.008)
  - Agreement with EMTR: Δpt +4.8%; non-uniformity −5.2%

Plots and contour snapshots are stored in the repository under results/plots.

## 14. Credibility Discussion Mapped to Evidence
This section distills the evidence across key dimensions that underpin confidence:

- Fit for purpose: The model targets mean Δpt and mixed-out temperature uniformity for a mixing tee; the physics included are directly tied to those metrics, and the acceptance thresholds are documented at project level.
- Problem framing: Flow regime and simplifications (no condensation, steady mean, adiabatic walls) are justified by sensitivity checks and facility observations.
- Mathematical form: RANS with SST is standard for subsonic internal mixing flows; an alternative model was tested to gauge model-form sensitivity, with modest deltas in the outputs.
- Software soundness: The chosen solver passed internal code checks and vendor verification suites for similar flow classes; no red flags observed for this application.
- Numerical practices: Unsteady effects were probed; residuals and global balances converged; a three-level mesh study produced quantifiable estimates of numerical error with acceptable observed order.
- Input pedigree: Inlet mass flows and temperatures come from calibrated instruments with stated accuracies; roughness informed by vendor data and spot profilometry; inlet turbulence levels bounded by measurements.
- Geometry and boundary condition fidelity: The computational domain reflects the test article, including tap bosses and inlet misalignment; sampling planes are co-located with PIV planes.
- Comparison to reality: Across nine operating points, errors against test values for both target metrics fall well within program tolerances and within the model’s uncertainty bands.
- Data quality in tests: EMTR measurement uncertainties are quantified; conversion of PIV intensity to temperature proxy is bias-corrected and included in error bars.
- Parameter influence: Sensitivities identify turbulence specification and model choice as most influential; expected for mixing problems and captured in uncertainty bounds.
- Combined uncertainty: A defensible uncertainty budget, separated into numerical and input contributions, yields 6% (Δpt) and 9% (non-uniformity) at 95% coverage.
- Robustness: Re-running with a different turbulence model and adjusting wall roughness within plausible ranges did not produce response swings that would alter trade decisions.
- Traceability and repeatability: All inputs, meshes, runs, and scripts are under version control; a clean-room reproduction matched primary results within small tolerances.
- Process governance: A freeze on software versions, CI checks, and a documented waiver for upgrades are in place; journals capture solver settings to avoid undocumented tweaks.
- People and training: Experienced analyst with recurring training; cross-checks and IV&V oversight completed; separate teams for testing and simulation avoid unintentional bias.
- Prior track record: Similar ducts and tees analyzed with this workflow show comparable accuracy; methods are not novel or unproven for this class of problems.
- Scope edges: Clearly stated operating envelope and exclusions; conditions requiring additional physics (e.g., condensation) are called out.
- Independence of review: External reviewers not involved in model building audited the work; action items resulted in concrete reruns and are closed.
- Documentation and archiving: A data book, test report, run logs, and this assessment are archived; pointers to repositories assure future maintainability.

Taken together, these items provide sufficient depth to assign high confidence for the stated use.

## 15. Limitations and Open Risks
- Model form uncertainty: While SST is appropriate, it cannot capture fine-scale scalar mixing as well as LES. The observed 7–8% differences against PIV-derived uniformity indicate residual model-form error. For certification-level predictions of scalar dispersion, scale-resolving approaches may be warranted.
- Thermal environment: The assumption of adiabatic walls is acceptable for current trades but may understate temperature smear if significant external heating arises in flight-like packaging.
- Upset conditions: Flow reversal or surge-like events are not modeled; predictions under such abnormal conditions would not be reliable.
- Measurement proxy: PIV scalar proxy involves a mapping to temperature that introduces 5% uncertainty. Direct hot-wire or multi-point thermocouples could refine the validation for future campaigns.

## 16. Decision
By authority of the Orion ECLSS Aerothermal Subsystem Lead (S. R. Patel) and following the technical review on 2026-08-02:

- The CFD model described herein is accepted for pre-PDR design trades and performance predictions of pressure loss and mixed-out temperature uniformity for the mixing tee, approved for use in the operating envelope defined in Section 12.
- Use outside this envelope is not approved without additional analysis and updated uncertainty estimates.
- This acceptance is subject to maintaining the documented toolchain (Fluent 2023 R2, meshes at or above the medium resolution) and preserving the modeling choices summarized in Sections 2–3. Any substantive deviation (e.g., solver upgrade, novel turbulence closure) requires a quick-look re-assessment.

Signatures on file in EDMS: SRP-Decision-Note-2026-08-02.

## 17. References and Artifacts
- TR-EMTR-2026-07, EMTR Test Report for ECLSS Mixing Tee, JSC, 2026.
- EC-DB-1042-RevA, ECLSS Mixing Tee CFD Data Book, 2026.
- CR-TEECFD-17, Peer Review Action Item Closure, 2026-07-31.
- GitLab: orion-eclss-tee-cfd (tag v1.3.2), includes meshes, cases, journals, and postprocessing.
- TB-EMTR-Alignment-03, Test-CFD plane alignment method note, 2026.

## 18. Replication Notes
To reproduce the 50/50 baseline case:
- Checkout orion-eclss-tee-cfd at tag v1.3.2.
- Load module stack: ansys/2023r2, intel/19.1, mpi/intel-2019.5.
- Execute journal run_tee_case_5050.jou with 240 ranks; ensure env var FLUENT_SCOTCH=1.
- Postprocess using post/mix_uniformity.py; verify hash against expected output in results/checksums.txt.

Expected outputs are documented in the repository and in EC-DB-1042-RevA, Appendix B.

## 19. Closing Remarks
The presented body of evidence supports the suitability of the model for its intended purpose in the current design phase. The approach balances practicality with rigor: steady RANS with quantified numerical errors, transparent validation against high-quality test data, and disciplined process controls. Future phases contemplating certification or operations in conditions outside Section 12 should revisit model form and may benefit from scale-resolving simulations or conjugate heat transfer modeling.

End of report.
