# Credibility Assessment Report: Conjugate Heat Transfer Model of the LCL-42 Avionics Cold Plate

Project: LCL-42 Power Avionics Thermal Management  
Prepared by: Thermal/Fluids Analysis Group, Flight Systems Division  
Date: 2026-08-06  
Tools: Ansys Fluent 2023 R2 (double precision), Ansys Meshing 2023 R2, ParaView 5.11, Dakota 6.16

## 1. Background and Study Objective

The LCL-42 assembly is a 1.2 kW power electronics module mounted to a liquid-cooled cold plate inside a sealed equipment bay on the reusable LV-9R vehicle. The purpose of the analysis is to demonstrate that the hottest semiconductor junction remains below 95 C with 95% confidence under the “Max-Cruise” environmental case (altitude 10.5 km, bay air 45 C, coolant PAO-4 at 35 C inlet, flow 1.0 L/min), including manufacturing and operating variability.

The model simulates coupled heat transfer in solids and fluid: conduction through the PCB stack, TIMs, device packages, cold plate walls; convection and pressure drop in the serpentine coolant channels; and radiation and natural convection within the bay (minor). We use a steady-state approach for the main case, supplemented by a 200 s transient check for startup overshoot.

Acceptability thresholds defined by the project are:
- Peak junction temperature Tj ≤ 95 C with 95% probability under Max-Cruise.
- Temperature uniformity such that any two MOSFET case temperatures on the same phase leg differ by ≤ 6 C.
- Predicted peak Tj within ±8 C of thermal-rig test measurements for the validation configuration.

## 2. Modeling Approach and Assumptions

Geometry:
- CAD generated from PDM rev LCL42_CP_A3. Includes detailed serpentine microchannels (1.6 mm hydraulic diameter), manifold plenums, eight MOSFET packages per leg (three legs), gate drivers, and copper planes. Fastener preload areas are represented; small fillets (< 0.25 mm) removed after sensitivity check.
- Bay enclosure represented as a control volume with radiative surfaces; ventilation fans not present per design.

Physics:
- Fluid: PAO-4, single-phase, temperature-dependent properties (viscosity and heat capacity from vendor data 20–90 C). Flow assumed incompressible.
- Turbulence: SST k-omega with low-Re near-wall resolution (target y+ < 1 in channels).
- Solid conduction: temperature-dependent thermal conductivities for aluminum 6061-T6, copper, FR-4, and SiC MOSFETs. Anisotropic in PCB.
- Contact resistances at interfaces (device-to-TIM, TIM-to-plate, plate-halves) modeled via specified thermal contact conductance (TCC). Primary value 20,000 W/m2-K for TIM interfaces; uncertainty assessed (see Section 6).

Thermal loads:
- Component dissipation from electrical power budget Rev P: MOSFETs 65 W each at Max-Cruise, gate drivers 3 W each, DC/DC 22 W, miscellaneous 25 W distributed.
- Board-level heat spreading captured via copper pour layers as in stack-up drawing E-2736.

Boundary conditions:
- Coolant inlet: mass flow rate 1.0 L/min ± 0.02 L/min (validation loop calibrated ±0.5%); temperature 35.0 C ± 0.3 C.
- Outlet: fixed pressure at 0 gauge.
- Bay air: still air 45 C; natural convection via h = 3 W/m2-K on outer surfaces substantiated by handbook correlations; radiation with ε = 0.8 for painted surfaces.
- Mounting boss conduction paths into chassis modeled as aluminum standoffs to 45 C sink.

Assumptions and exclusions:
- Steady-state for design points; startup transient checked separately—duty-cycle induced fluctuations are outside this analysis.
- No boiling in PAO-4 (channel wall temperatures remain ≤ 72 C in all runs).
- Fouling/aging of TIMs and coolant not modeled; captured as a future risk item.
- Manufacturing geometric variation limited to channel width ±0.05 mm (machining spec); included in uncertainty ranges.

## 3. Discretization and Solver Controls

Mesh:
- Poly-hexcore for coolant (14.7M cells), conformal hexahedral solids (8.9M cells). Three systematically refined meshes built: Coarse (7.1M total), Medium (16.5M), Fine (31.9M).
- First cell height targets y+ ~ 0.8 across channels; verified with wall function reporting.
- Solid-fluid interface is one-to-one conformal to eliminate projection error.

Solvers:
- Pressure-based coupled solver, second-order schemes for momentum, energy, and turbulence equations. Double precision, segregated energy equation for solids and fluids with fully coupled interface.
- Under-relaxation factors tuned to 0.4–0.7; multigrid with AMG cycles.
- Convergence: residuals < 1e-6 for flow/turbulence, < 1e-8 for energy, and monitor stabilization of key temperatures and mass flow to < 0.02% change over 500 iterations.

Time stepping (for the 200 s startup case):
- 1 s time step, BDF2; time-step independence assessed at 0.5 s.

## 4. Check of Numerics and Implementation

Code-oriented checks:
- We exercised vendor’s conduction and convection modules against canonical problems: 1D slab with convection boundary (analytical), and fully developed turbulent pipe heat transfer (Gnielinski correlation). Our cases reproduced analytical/Nu correlations within 0.7–2.2% on the Fine mesh.
- For conjugate interfaces, we compared a two-material composite with known series resistance; error < 1.5% on Medium mesh.
- Energy balance closes within 0.12% (Fine), 0.41% (Medium), 1.3% (Coarse) for the main case.

Solution-oriented checks:
- Mesh refinement study on peak MOSFET junction temperature and total pressure drop. Observed order p ≈ 1.9 (temperature) using Richardson extrapolation; GCI95 for peak Tj from Medium mesh is 1.4 C (0.9% of value). Pressure drop GCI95 is 3.7%.
- Time-step independence for startup transient yields < 0.5 C difference in peak overshoot between 1.0 s and 0.5 s steps.

Robustness:
- Variations in solver controls (under-relaxation ±0.2, initial fields uniform vs patched) shift peak Tj by ≤ 0.4 C. No oscillations or divergence observed after initial 200 iterations.

Cross-platform repeatability:
- Runs on two clusters (RHEL8, Intel Ice Lake, and Ubuntu 22.04, AMD EPYC) produced identical results to within 0.02 C and 1 Pa after 5,000 iterations, attributable to ordering differences.

## 5. Qualification of Inputs and Data Provenance

Geometry pedigree:
- CAD from mechanical owner; change notices CN-142 and CN-153 incorporated (channel offset correction, boss diameter update). Geometry snapshots tied to run IDs via Git LFS and checksum.

Material properties:
- Aluminum 6061-T6 conductivity from MIL-HDBK-5J, mild temperature dependency included (167 W/m-K at 25 C to 155 W/m-K at 100 C).
- FR-4 anisotropy: in-plane 8.5 W/m-K, through-thickness 0.3 W/m-K, per PCB fabricator datasheet with ±10% tolerance.
- PAO-4 viscosity and Cp from manufacturer’s curve set, fit with 4th-order polynomials (R2 > 0.998).

Contact conductance:
- TCC derived from compression tests on coupon stack (SiC-TIM-plate) at 2 MPa clamp: 20,000 W/m2-K mean, COV 30%. Sensitivity carried (Section 6).

Load mapping:
- Electrical team provided per-component heat loads by duty case; we performed a cross-check by correlating predicted device Vce(on) and switching losses to measured currents in the validation build. Discrepancy < 4%.

Instrument calibration (for validation test):
- Type-K thermocouples calibrated ±0.4 C at 60 C; IR camera emissivity matched per black paint patches. Flow meter accuracy ±0.5% of reading; RTD at inlet ±0.15 C.

## 6. Comparison to Bench Measurements

A hardware thermal rig (Rig ID: CP-VAL-07) replicated the cold plate and a representative board with heater chips in the MOSFET footprints. Conditions: PAO-4 at 35.1 C, 1.00 L/min, bay air 45 C. Total thermal dissipation 1.21 kW. Data captured after 45 min soak.

Results:
- Max device case temperature (TC) measured: 82.3 C ± 0.6 C (95% CI).
- Model-predicted case temp (Medium mesh): 80.9 C; difference −1.4 C.
- Temperature spread among the three phase legs: test 4.9 C; model 4.1 C.
- Channel pressure drop: test 25.3 kPa; model 26.1 kPa (3.2% high).

We ran a sweep on TCC within measured variability (14,000–26,000 W/m2-K) and found best match at 18,500 W/m2-K (within 1σ of measurements). We did not “tune” beyond staying inside the measured range. No other parameter adjustments were made.

Applicability of the test to flight use:
- Flow regime and Reynolds number (Re≈4200) match Max-Cruise within 5%.
- Heat flux distributions mimic component footprints.
- The bay radiation environment in the rig approximated with painted shrouds at 45 C; within known uncertainties.

## 7. Uncertainty, Variability, and Sensitivity

We quantified the combined effect of input variability and modeling scatter on peak Tj. The following inputs were treated as random:
- TCC at device/TIM/plate: mean 20,000 W/m2-K, COV 30%, lognormal.
- MOSFET dissipation: mean 65 W, σ 3.5 W each, correlated ρ = 0.6 within a phase leg.
- Coolant flow rate: mean 1.00 L/min, σ 0.02 L/min, normal truncated at ±3σ.
- Coolant inlet temperature: mean 35.0 C, σ 0.3 C.
- Channel width variation: mean nominal, σ 0.02 mm (per machining spec).

Model form and numerical scatter:
- Validation mismatch treated as additive Gaussian noise with σ_model = 2.0 C derived from five validation points (rig runs at 0.8/1.0/1.2 L/min and 30/35 C inlet).

We used Latin Hypercube Sampling (N=200) on the Medium mesh with surrogate-assisted sampling (Gaussian process built from 120 runs, leave-one-out R2=0.995). Key outcomes:
- Peak junction temperature distribution: mean 87.4 C; 95th percentile 92.6 C.
- Probability Tj < 95 C: 98.3% under Max-Cruise.
- Top contributors to variance (Sobol indices): TCC 0.42, device power 0.28, flow rate 0.17, channel width 0.08, inlet temperature 0.04. Cross terms (TCC×power) 0.06.

We propagated uncertainties to pressure drop and found 95th percentile = 28.4 kPa, within pump capability.

## 8. Scope of Validity and Extrapolation

The model has been exercised across:
- Coolant flow 0.7–1.4 L/min.
- Inlet temperature 30–45 C.
- Bay air 25–55 C.
- Power 0.9–1.3 kW.

Outside these bounds, notably below 0.6 L/min or inlet above 50 C, we have not demonstrated adequate heat transfer margin or ensured absence of thermal runaway; boiling still not expected due to PAO-4 properties, but viscosity changes increase pumping penalties. Orientation dependence was checked (gravity vector flipped): natural convection in bay changes less than 1 C on external surfaces; negligible on junctions.

## 9. Prior Use and Operational Track Record

A similar methodology and solver stack were used on the Pathfinder avionics cold plate in 2022. There, the predicted max case temperature at 1.1 kW was within +5.2 C of test (N=6 points across flow/temperature), and in flight telemetry, thermistor readings matched predictions within 6–8 C after accounting for sensor placement lag. The same analysts and verification workflow were applied.

We also reused validated PAO property polynomials from the AFT-23 pump loop project (peer-reviewed, 2025), eliminating re-fit risk.

## 10. Analyst Experience and Human-System Considerations

Personnel:
- Lead analyst (R. Zhao): 12 years in thermal/fluid simulation; internal Level-3 CHT certification.
- Secondary analyst (M. Patel): 5 years; completed vendor STAR/Fluent advanced heat transfer courses; authored internal near-wall thermal modeling guide.
- Thermal test engineer (K. Nguyen): 9 years, owns rig calibration.

Quality gates:
- Analysts use a 54-point CHT checklist covering units, frame of reference, y+ targets, energy balance, and probe definitions. Peer checks performed before milestone reviews.

## 11. Governance: Planning, Reviews, and Traceability

Plan:
- The M&S Credibility Plan (doc CP-MSC-42) was approved at SRR; gates defined for geometry freeze, V&V minimums, and uncertainty targets. The plan references agency guidance and tailors rigor to Class B decision impact (vehicle-level thermal margin).

Configuration management:
- All models, meshes, scripts, and results stored in GitLab with protected branches; large files in Git LFS; runs tracked with unique IDs. Dakota inputs and random seeds versioned for reproducibility. Docker container (Fluent 2023 R2 + Python 3.10 stack) archived to Artifactory.

Independent review:
- A peer panel of two SMEs outside the project reviewed model formulation, interfaces, and validation on 2026-06-18. Action items (five total: TCC range justification, y+ verification near manifolds, radiation sensitivity, IR emissivity confirmation, pressure drop post) were closed by 2026-07-02.

Software quality:
- Vendor code is COTS; we rely on vendor’s QA plus our in-house acceptance tests as noted. No custom UDFs aside from a property table reader (unit tested). Scripts for postprocessing have pytest coverage (82%).

Reproducibility:
- Exact solver settings captured in a “run manifest” including machine architecture, core count, solver version, and environment hashes. A rerun on a clean node replicated key temperatures within 0.03 C.

## 12. Presentation of Results and Decision Support

We report:
- Temperature fields across solids and fluid, annotated with probe locations at all device junctions and cases.
- Streamlines with temperature to show maldistribution risks.
- A table of the five hottest devices with mean and 95th percentile Tj, compared to limits.
- Pressure drop vs flow curve with uncertainty bands.
- A concise statement: “For Max-Cruise, the predicted 95th percentile Tj is 92.6 C, providing 2.4 C margin to the 95 C criterion.”

Uncertainty is carried into the margin statements. We distinguish modeling scatter from physical variability and indicate that the limiting factor is interfacial conductance.

## 13. Numerical Stability and Edge-Case Behavior

We explored off-nominal solver setups:
- Coarser near-wall spacing (target y+≈2.5) increased max Tj by 0.9 C; still within GCI bands.
- Switching to Standard k-ε with enhanced wall treatment produced a 1.8 C lower Tj and 5% lower ΔP; rejected due to under-resolved thermal gradients—SST retained.
- Increased orthogonal quality smoothing led to the same Tj within 0.2 C; mesh metrics above recommended thresholds (min orthogonal quality 0.24, max skewness 0.62).

## 14. Limitations and Outstanding Risks

- Time-varying loads: we only assessed a 200 s startup with constant duty; rapid 1–10 s spikes could momentarily push Tj. A follow-on transient campaign is planned, pending power profile finalization.
- Long-term aging: TIM pump-out and surface oxidation not represented; margins could erode by 2–5 C over life. Reliability to address with derating policy.
- Fouling and microchannel blockage not modeled; we recommend filter maintenance intervals sized to keep ΔP under 35 kPa.
- Structural-to-thermal coupling: we applied measured clamp loads implicitly; a load-relaxation study through an FEA preload map is on the backlog.

## 15. Summary of Evidence Against Acceptance Thresholds

- Thermal target: With quantified uncertainties, P(Tj < 95 C) = 98.3% at Max-Cruise. The median and 95th percentile values are 86.8 C and 92.6 C, respectively. Validation mismatch at calibration points is within ±2 C without out-of-range tuning.
- Uniformity: The model estimates a 4.3 C spread between the hottest devices on a phase leg; measured was 4.9 C. This meets the ≤ 6 C requirement.
- Pumping margin: Predicted ΔP 26.1 kPa (mean), 95th percentile 28.4 kPa against a 45 kPa pump capability at 1.0 L/min; 16.6 kPa margin.

Based on the above, we assess the model as suitable for the intended decision with clearly documented boundaries and uncertainty.

## 16. References and Data Access

- LCL42_CP_A3 CAD (PDM link; SHA256 ending …c19a).
- CP-MSC-42 M&S Plan, Rev B.
- Fluent case/data archives: runs 42_210 to 42_286 in GitLab group “lcl42-cp-cht”.
- Validation run logs and raw DAQ: “val_cp07_2026-06-11” in DataLake/thermal/rigs.

---

## Appendix A: Mesh Quality and Residual Traces (highlights)

- Medium mesh: 16.5M cells; min orthogonal quality 0.26; max skewness 0.61; average y+ 0.84 in channels.
- Residuals reached 1e-6 for continuity, k, ω; 1e-8 for energy by 4,300 iterations. Monitors for Tj stabilized within 0.01 C thereafter.

## Appendix B: Validation Case Matrix

- Points: (Flow, Tin) = (0.8 L/min, 35 C), (1.0, 35), (1.2, 35), (1.0, 30), (1.0, 40).
- Mean absolute deviation in case temps across points: 1.9 C (N=5).

## Appendix C: Sensitivity Highlights

- A ±20% shift in TCC moves 95th percentile Tj by +3.8/−3.2 C.
- ±0.1 L/min on flow changes 95th percentile Tj by −1.1/+1.2 C.
- ±5 W on each MOSFET increases 95th percentile Tj by +2.4 C.

## Appendix D: Review Closure Notes

- Action A1 (TCC evidence): Added coupon test report RPT-CP-TIM-02; maintained lognormal prior.
- Action A2 (y+ manifolds): Local refinement added; y+ < 1 throughout serpentine entries/exits.
- Action A3 (radiation sensitivity): h and ε variation results in < 0.6 C change at devices.
- Action A4 (IR emissivity): Black-paint calibration factor documented; emissivity set to 0.95 ± 0.02.
- Action A5 (ΔP correlation): Reported uncertainty bands; vendor pump curve cross-check added.

## 17. Concluding Statement

The LCL-42 cold plate model is a mature CHT simulation with demonstrated numerical soundness, faithful input data, and direct comparison to hardware. Uncertainty and sensitivity are quantified such that decision-makers can assess margin with transparency. Use outside the tested envelope requires additional checks, particularly for transient power excursions and long-term degradation phenomena. Within the specified operating box, evidence supports its use for the upcoming CDR and thermal margin certification.

## 18. Contact

Primary: R. Zhao, Thermal/Fluids Analysis Group  
Email: r.zhao@flight-systems.example  
Secondary: K. Nguyen (Thermal Test), M. Patel (CHT Modeling)

---
