Cold Plate CP-02 Conjugate Heat Transfer Model — Credibility Assessment Report (per NASA-7009B intent)

1. Executive Summary

This report evaluates the trustworthiness of the CP-02 cold plate conjugate heat transfer (CHT) model used to inform design decisions for the Lunar Avionics Module thermal management system. The model predicts coolant-side and structure-side thermal performance, including maximum component baseplate temperature and temperature uniformity, under thermal-vacuum conditions with polyalphaolefin (PAO) coolant. Results are used to:

- size the pump and set nominal flow,
- verify that baseplate temperatures remain below the 85 C requirement with 450 W electronics dissipation, and
- define acceptance criteria for thermal vacuum testing.

Evidence assembled includes: model build documentation, input provenance and handling, solver setup and numerical checks (grid and timestep dependence), experimental comparison, sensitivity and uncertainty analyses, review records, and configuration traceability. The analysis team concludes the model is suitable for preliminary and critical design decisions within the specified operating envelope (Section 10), with quantified margins and known limitations.

2. Background and Intended Use

The CP-02 cold plate is an Al6061-T6 billet with embedded serpentine channels bonded under a 1.5 mm lid, removing heat from a high-density avionics stack. The Lunar Avionics Module operates within a vacuum environment; conductive and radiative heat paths dominate externally, while forced convection inside the channels removes the majority of heat.

The CHT model is used to:
- predict the peak steady-state baseplate temperature at 450 W total dissipation,
- evaluate temperature gradients across the mounting face (<8 C goal),
- assess flow maldistribution risk across parallel channel branches, and
- explore transient warm-up to inform heater control.

The model will not be used to certify flight safety; rather, it guides design choices and test planning. A formal acceptance memo from the Chief Engineer authorizes use for CDR-level decisions provided fidelity evidence in this report remains valid and any changes follow the configuration process (Section 9.3).

3. Physical Model and Simplifications

3.1 Geometry and physics
- Domains: fluid (PAO) within channels and manifolds; solid (Al6061-T6 base and lid; localized copper heat spreaders; titanium inserts); TIM layer (Bergquist Gap Pad TGP 0.5 mm equivalent) as an interface with prescribed thermal contact conductance.
- External environment: thermal-vacuum chamber at 10^-5 torr; radiation exchange between cold plate external surfaces (ε = 0.08 for passivated aluminum) and chamber liner (effective sink at 200 K), view factors computed by solver’s surface-to-surface method.
- No external gas conduction modeled.

3.2 Flow and thermal regimes
- Nominal flow: 0.045 kg/s PAO at 293 K; pressure outlet to reservoir at 0 gauge.
- Reynolds number at channel entrance ≈ 5,400 (hydraulic diameter 2.8 mm), weakly turbulent. SST k-ω with y+ ≈ 0.8 on the refined case resolves the near-wall region.
- Fluid properties temperature-dependent from 293 to 363 K (density, viscosity, cp, k).

3.3 Idealizations and omissions
- Channel wall roughness neglected (Ra < 1.6 µm per vendor spec); represented as hydraulically smooth.
- TIM modeled via a uniform interfacial conductance rather than explicit microstructure.
- Coolant dissolved gas effects ignored; degassed PAO assumed per test configuration.
- No cavitation modeling; pump NPSH ensured by system design above 4 m.
- Steady-state for primary design point; a separate transient is used for warm-up.

4. Inputs: Origin, Quality, and Treatment

4.1 Geometry and materials
- CAD derived from CP-02 Rev C; STEP exported on 2026-04-18, hash 4fd2…a9e2; neutral format imported into ANSYS Fluent Meshing 2023 R2.
- Al6061-T6 conductivity vs temperature from ASM Data Set 11, verified ±5% against MatWeb.
- Copper inlay properties from C110 manufacturer spec.
- TIM: Bergquist Gap Pad TGP 0.5 mm; vendor nominal bulk k = 3.0 W/m-K; test-derived interfacial conductance converted to a thermal contact resistance (Section 7.3).

4.2 Fluid properties
- PAO (Brayco Micronic 889) property curves from supplier (Sheets 889-TDS-2025). Independent lab (ThermoLab) viscosity and thermal conductivity measurements on Lot L26-PAO confirm within ±3% over 293–343 K.
- Uncertainty applied as distributions: k ±3% (normal), cp ±2% (normal), μ ±3% (lognormal).

4.3 Loads and boundary conditions
- Heat map from electronics FEA: 24 hotspots between 5–30 W each on a 180×140 mm footprint. For steady-state, heat applied at the TIM interface with spreading to adjacent regions via conduction; for transient warm-up, power ramp step from 0 to 450 W over 90 s.
- Radiative sink at 200 K established by chamber characterization; emissivity from coupon test: ε = 0.08 ± 0.01.

4.4 Source pedigree and traceability
- All inputs stored under Git tag CP02_CHT_v1.7 with checksum files; DOORS links map each input to requirement IDs T-CP02-SS-001 (temperature limit), -002 (gradient goal), and -004 (mass flow range).

5. Software and Computing Platform

- Solver: ANSYS Fluent 2023 R2, pressure-based coupled solver, double precision.
- Meshing: Fluent Meshing 2023 R2, poly-hexcore topology with prism layers at walls (12 layers, growth 1.2).
- Radiation: Discrete Ordinate (DO) model with 4×4 angles; view-factor cross-check performed on simplified case.
- Turbulence: SST k-ω with low-Re correction; transitional model evaluated on L1 grid and found to shift peak T by <0.6 C; SST retained for robustness.
- HPC cluster “Orion”: 2× Intel Xeon Gold 6348 per node, 48 cores/node, Infiniband HDR; RHEL 8.6; Intel MPI 2021.8. QA: installation verified with Fluent benchmark case RANS_Comb_03 and thermal regression suite TR-CHT-07; results within vendor tolerances.

6. Numerical Approach and Solution Quality Checks

6.1 Discretization and convergence practices
- Spatial discretization: second-order upwind for momentum and energy; bounded second-order for DO radiation intensity; pressure staggering PRESTO!.
- Relaxation factors default; under-relaxation tuned only for transient startup (energy 0.9 to 0.7).
- Convergence criteria: scaled residuals below 1e-5 for all equations; outlet mass balance within 0.1%; stability of monitored points (ΔT < 0.05 C over 1,000 iterations).

6.2 Mesh density exploration
Three nested grids were prepared by global core size and prism thickness changes while preserving y+:

- L1: 5.3 million cells; average y+ = 1.4; minimum 0.5.
- L2: 12.4 million cells; average y+ = 0.9; minimum 0.3.
- L3: 28.9 million cells; average y+ = 0.75; minimum 0.25.

Peak baseplate temperature at nominal conditions:
- L1: 80.9 C
- L2: 80.2 C
- L3: 79.9 C

A three-point Richardson extrapolation suggests the asymptotic limit at 79.6 C; the estimated mesh-induced effect at L2 is approximately 0.6 C (about 0.8%). Wall heat flux distributions are visually indistinguishable between L2 and L3 at the hotspots.

6.3 Temporal resolution (transient warm-up)
- Fixed timestep 0.1 s; CFL in channels ~ 2–5; five timesteps per thermal RC of the thinnest fin segment. Halving timestep to 0.05 s changed peak transient overshoot by 0.12 C (non-material for controller tuning).

6.4 Energy balance and auxiliary checks
- Net electrical input (450 W) minus coolant enthalpy rise and radiative loss yields a residual <0.7% on L2; residual shrinks to 0.4% on L3.
- Pressure-drop comparison to analytical laminar-turbulent correlation for rectangular ducts shows <6% discrepancy at nominal Re.

7. Comparison to Experiment

7.1 Test article and setup
- CP-02 thermal vacuum test (TVAC) conducted 2026-05-10 to -05-13 in Chamber TV-3B.
- Instrumentation: 12 PT100 class A sensors (±0.15 K), three Type-K thermocouples (±1.0 K) on coolant lines, one Coriolis mass flowmeter (±0.5%), and two 0–2 bar differential pressure transducers (±0.25% FS).
- Loads: 150 W, 300 W, and 450 W steady states; flows 0.030, 0.045, and 0.060 kg/s; inlet temperature maintained at 293 ± 0.2 K via chiller.

7.2 Data processing
- Sensors time-averaged over last 10 minutes after stabilization; radiation sensor-verified chamber liner temperature at 200 ± 1 K.
- Uncertainty combined via root-sum-square, accounting for calibration drift and data logger resolution.

7.3 Model-test alignment
- Geometry deviations: measured lid thickness +0.05 mm vs CAD; applied as-is to the model since effect is negligible (<0.1 C).
- TIM interface: contact resistance inferred from a separate flat coupon squeeze test: 0.25 K·cm^2/W at 0.3 MPa contact pressure, ±30% 2σ; used unchanged in the validation runs. No parameter fitting to match CP-02; sensitivity explored separately.

7.4 Results
At 450 W and 0.045 kg/s:
- Measured peak baseplate temperature (from five sensors near hotspots): 81.2 C (mean of cluster), standard deviation 0.7 C.
- Model (L2 grid) predicted 80.2 C at the nearest node to the sensor; local gradient-corrected interpolation yields 80.5 C.
- RMS difference across all 12 baseplate sensors: 1.2 K.
- Maximum absolute difference: 2.7 K (sensor S9 near manifold turning region).

Across nine operating points:
- Mean bias: model low by 0.6 K.
- 95th percentile discrepancy: 2.3 K.
- Pressure drop versus flow curve within 8% across the range; offset attributed to entrance contraction losses not fully represented in the CAD (laser-cut edge radius measured post-test at 0.2 mm).

Coverage: The validation envelope spans 150–450 W and 0.030–0.060 kg/s, bracketing the intended operating region. Extrapolation beyond 0.070 kg/s is not supported.

8. Sensitivity and Uncertainty Analyses

8.1 Local one-at-a-time sweeps
- Thermal contact resistance: ±30% shift changes peak T by ±3.2 C.
- PAO mass flow: ±10% changes peak T by ∓2.6 C.
- Emissivity: ±0.01 changes peak T by ±0.2 C at 450 W.
- Turbulence intensity at inlet: 1–5% shifts peak T by <0.3 C.
- Property uncertainty bundles (k, cp, μ) maximum combined effect ±0.9 C.

8.2 Global propagation
- Latin Hypercube Sampling, 200 samples on L1 grid with response correction from L2/L3 mesh study.
- Inputs varied: TIM contact resistance (normal, μ = 0.25 K·cm^2/W, σ = 0.075), flow (normal, σ = 2%), inlet temperature (normal, σ = 0.2 K), PAO properties as above, emissivity (normal, σ = 0.01).
- Output: distribution of peak baseplate temperature at 450 W, 0.045 kg/s: mean 80.9 C, standard deviation 1.8 C; 99th percentile 85.1 C.
- With 85 C requirement, probability of exceedance ≈ 0.8% at nominal flow; at 0.060 kg/s, exceedance probability falls below 0.1%.

8.3 Drivers
- Standardized regression coefficients rank: TIM resistance (0.56), mass flow (-0.41), PAO viscosity (0.19 via heat transfer coefficient coupling), emissivity (0.05), inlet temperature (0.03).

9. Model Development Controls and Traceability

9.1 Documentation and archiving
- Full simulation deck, meshes, user-defined functions, and post-processing scripts preserved in the CP02_CHT repository (GitLab project TL-THRM-CP02) with LFS storage for large meshes. Tag CP02_CHT_v1.7 corresponds to the results in this report; SHA-256 manifest included.
- Post-processing performed in Python 3.11 with Jupyter notebooks; environment pinned by conda-lock; notebooks produce figures and tables in this report.

9.2 Change control
- Change requests reviewed at weekly thermal working group; impacts captured in CHANGELOG.md. From v1.6 to v1.7, inlet header cross-section corrected (CAD fix) yielding 0.4 C change in peak T and 3% change in pressure drop; peer review sign-off recorded (MR-CP02-12).

9.3 Review, independence, and acceptance
- Two-person peer review (thermal SME and CFD specialist not on the project) completed 2026-05-22; comments addressed (see Appendix).
- Cross-check with a 1D network model in Thermal Desktop/SINDA for pressure drop and average UA shows agreement within 7–10% depending on flow.
- Chief Engineer memo CE-CP02-ACC-001 (2026-05-27) authorizes the model for design decisions within validated bounds and requires re-approval on any geometry or fluid property change >5% effect on peak T.

9.4 Team competence
- Lead analyst: 10 years electronics cooling; ANSYS Fluent advanced training (2024), authored internal best practices for CHT.
- Supporting analyst: test correlation experience; certified in ASME V&V 20 short course.
- Both completed the division’s M&S rigor training aligned with NASA-7009B expectations.

9.5 Software quality assurance
- Commercial solver with vendor verification suite; internal smoke tests run per release.
- Cluster resource management via Slurm; job reproducibility verified by repeating two key runs on a second node set (bitwise-identical results with fixed parallel decomposition).
- Backups: nightly mirror to on-prem repository; quarterly archive to long-term storage.

10. Applicability and Boundaries

The model is applicable for:
- Flow rates: 0.030–0.060 kg/s,
- Heat loads: 150–500 W (validated at 450 W; linearity to 500 W verified by UQ runs and material property ranges),
- Inlet temperature: 288–303 K,
- Vacuum environment with radiative sink ~200 K and surface emissivity 0.08 ± 0.01,
- TIM contact pressure ~0.3 MPa and gap pad thickness 0.5 mm.

Not covered:
- Vibration-induced contact variation (dynamic TIM conductance),
- Micro-fouling or long-term fluid property drift,
- Freezing or low-temperature startup below 273 K,
- Cavitation or gas ingestion.

The validation campaign covers the decision space with modest extrapolation at 500 W; risk is mitigated by margin at nominal flow and an available setpoint increase to 0.060 kg/s.

11. Results Summary

- Predicted peak baseplate temperature at nominal operating condition (450 W, 0.045 kg/s, Tin = 293 K) is 80.2 C on L2 grid; uncertainty from numerical resolution ~0.6 C; combined aleatory and epistemic sources yield a 99th percentile near 85 C.
- Temperature uniformity across the 180×140 mm footprint: 6.4 C (95th percentile across sensors), meeting the ≤8 C goal.
- Pressure drop: 37 kPa at 0.045 kg/s, within pump head margin.
- Transient warm-up: time to 80 C is 320 s from cold-without-load initial condition at 293 K; overshoot under a step turn-on is <0.4 C when the control ramp is 90 s.

12. Evidence Against Credibility Dimensions

This section collects the main strands that underpin confidence.

- Problem framing and fidelity to the decision: The model encapsulates the heat removal mechanisms relevant to a vacuum environment and the internal forced convection in the channels. The decision pivots on meeting an 85 C limit; the model resolves the local hotspots and pressure drop to inform both temperature and pump head.

- Assumptions and their justifications: Choices like smooth-wall assumption and uniform interface conductance are argued via manufacturing roughness data and separate squeeze tests. Radiation treatment reflects chamber characterization. No parameters were tuned against CP-02 data.

- Input reliability and management: Geometry from controlled CAD, material properties from vetted sources, with uncertainties quantified and carried into UQ. Flow and temperature inputs match test conditions. All inputs trace to requirements via DOORS.

- Solver and numerics: The solver is established, with default settings adapted per best practice. Mesh and timestep dependence studies constrain numerical error contributions. Energy balance checks close within 1%.

- Code credibility and software QA: Vendor verification, internal regression cases, and cross-runs on separate nodes confirm computational determinism and expected performance. No compiler or library anomalies were found.

- Validation thoroughness: The comparison spans matrix points around the operating set. Agreement is within a couple of kelvin; where differences exist (S9), plausible physical explanations (manifold turning loss representation) exist. No hindsight parameter tweaking was performed.

- Sensitivity exploration and margins: TIM contact resistance and flow rate dominate output variability; design levers exist (pump setpoint and assembly torque). UQ indicates a small chance of exceeding the limit at nominal flow; operating at 0.050–0.060 kg/s suppresses that tail.

- Robustness: The solution is insensitive to initial conditions for steady runs; small geometry or inlet turbulence changes leave peak T essentially unchanged. The model converges across grids and with different core decompositions.

- People, process, and oversight: Qualified analysts followed an internal plan aligned with NASA-7009B guidance, including peer reviews and documented acceptance by the engineering authority.

- Traceability and reproducibility: Complete repository snapshot, scripts, and environment locks allow reruns that reproduce the reported numbers to within roundoff on the same platform.

13. Limitations and Open Items

- TIM contact resistance dominates uncertainty. While a separate squeeze test informs the value, there remains assembly-to-assembly scatter. We will collect in-situ clamp load data during flight hardware build and update the distribution.

- The transitional nature of the flow sits near the RANS/transition boundary. While SST showed best stability and acceptable accuracy, dedicated transition modeling did not materially change temperatures in scoping checks; nonetheless, higher-fidelity calibration could be pursued if future anomalies appear.

- Manifold entrance rounding likely causes a slight underprediction of pressure drop at higher flows. The post-test geometry measurement will be rolled into the next geometry revision.

- Radiation model: DO with a coarse angular set was sufficient given low external temperature and limited view complexity; a view-factor method confirmed similar net radiative load. If external MLI is added, the model must be reworked.

14. Conclusions and Recommendation

The CP-02 CHT model, as configured in CP02_CHT_v1.7, is fit for informing CDR-level decisions about cold plate performance in vacuum for flows between 0.030–0.060 kg/s and loads up to 500 W. The model’s predictions agree with thermal vacuum test measurements within roughly 1–3 K across the matrix, numerical uncertainties are constrained by mesh and timestep exercises, and dominant physical uncertainties are identified and propagated.

Recommendation:
- Use the model to select a nominal pump setpoint of 0.050 kg/s to maintain ≥2 C margin to the 85 C limit at the 99th percentile.
- Carry the uncertainty distribution into the system-level thermal budget.
- Maintain configuration control; any changes to geometry, fluid properties, or TIM specification that move peak temperature by more than 5% require re-acceptance.

15. Key References

- ASM Handbook Data Set 11: Thermal Properties of Aluminum Alloys (Accessed 2026-03-04).
- Vendor TDS: Brayco Micronic 889 Properties (Rev. 2025-09).
- ANSYS Fluent 2023 R2 Theory and Verification Manuals.
- Internal Test Report: TVAC-CP02-2026-05, Rev A.
- Internal Memo: CE-CP02-ACC-001, Model Acceptance for Design Use.

Appendices listed in appendix.md contain mesh statistics, test matrices, review comments, and the change log excerpt referenced above.
