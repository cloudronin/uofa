Title: Credibility Assessment Report — Conjugate Heat Transfer Model of an Implantable LVAD Motor

Revision: R1.3
Date: 2026-08-06
Prepared by: Thermal-Fluid Modeling Group, CardioMech Devices Inc.


1. Background and Intended Use

We developed a computational model to quantify heat transfer from the brushless DC motor of our left ventricular assist device (LVAD) into the blood stream and surrounding structure. The model predicts:
- Maximum temperature of the titanium housing and polymer stator potting compound
- Local blood temperature near wetted walls and predicted bulk outlet temperature rise
- Heat split between blood-side convection and conduction to adjacent mounts

The analysis informs two decisions:
- Device safety: demonstrate that blood temperature rise remains within 2.0 C and housing external surfaces remain below 41 C under worst foreseeable use
- Design optimization: evaluate whether changes in winding fill or housing thickness alter thermal margin

The model will be used by the design team to justify design-freeze and by the regulatory submission team as supporting evidence. The results are intended to apply to adult patients (55–100 kg) operating the LVAD at 2–6 L/min and 6,000–9,000 rpm, with motor electrical losses between 2.6–3.4 W depending on duty point.


2. What Could Go Wrong and How We Tailor Rigor

A device-induced local blood heating exceeding ~2 C over baseline may elevate hemolysis risk in low-wash regions and can interact with thrombus formation. A surface exceeding ~41 C has tissue burn risk for the percutaneous driveline segment during bench handling and implant prep. Therefore, we treated this as high consequence if wrong.

We set the following performance targets for the model:
- For outlet blood temperature rise: prediction error ≤0.2 C mean bias and ≤0.3 C 95% limit across 2–6 L/min
- For peak housing surface temperature: ≤0.7 C 95% uncertainty
- Demonstrate numerical error under 5% of the total energy input and under 0.1 C on temperature metrics
- Provide coverage across the operating envelope and margin to anticipated patient variability

These targets were reviewed in a design FMEA session (DFMEA-LVAD-THERM-2026-02) with risk owners from systems, quality, and clinical.


3. Model Summary

- Physics: Conjugate heat transfer with incompressible, shear-thinning blood analog (Bird-Carreau) flowing through the pump; conduction through titanium housing and epoxy-potted stator, and thermal contact with aluminum mounting saddle. Blood treated as single-phase continuum; radiative exchange neglected (validated negligible at 37–42 C).
- Turbulence treatment: SST k-ω with transition off (Re based on blade chord ~5×10^4 with strong swirl). Near-wall y+ targeted between 0.3–1.2 on blood-contact walls.
- Rotating machinery: Frozen rotor frame for steady prediction of mean fields; rotating reference frame (RRF) in rotor domain; interface with general grid interface (GGI).
- Heat sources: Volumetric heat generation in copper windings calibrated to measured copper loss vs rpm and torque; iron losses mapped via manufacturer Steinmetz fit. Total electrical loss cases: 2.6 W (low), 3.0 W (nominal), 3.4 W (high).
- Thermal contact: Conductance between housing and mounting saddle modeled as 6,000–15,000 W/m^2-K based on clamp torque and grease spec; baseline 10,000 W/m^2-K.
- Properties: Blood analog at 37 C: ρ=1,060 kg/m^3; μ(γ̇) from Carreau with μ0=0.025 Pa·s, μ∞=0.0035 Pa·s, λ=3.313 s, n=0.3568; k=0.52 W/m-K; cp=3,680 J/kg-K. Titanium Grade 5: k=6.7 W/m-K; epoxy potting: k=0.25 W/m-K; aluminum saddle: k=170 W/m-K.
- Outputs of interest: peak wetted-wall temperature, average housing outer surface temperature, bulk blood outlet temperature (mass-averaged), and fraction of motor loss rejected to blood.

Software: Ansys Fluent 2024R1 for fluid and thermal; mesh generated in Ansys Meshing. Double-precision, segregated solver for energy, coupled pressure-velocity scheme. Steady-state runs with pseudo-transience (CFL ~50) to accelerate convergence. All runs executed on a 24-core Xeon Gold 6338 workstation with consistent compiler and OS images.


4. Numerical Checks and Solution Quality

4.1 Code-level confidence
We performed two activities:
- Analytical benchmarks: Pure conduction in a composite slab with internal heat generation (closed-form); Fluent results matched within 0.05 C absolute across ten cases. Forced convection in a heated pipe (Gnielinski correlation) replicated within 2.3% for Nusselt number at Re=10,000–50,000 using the same wall treatment and SST model.
- Community verification case: NASA conjugate cylinder case (HTC on a heated cylinder in crossflow at Re=4,000, Pr=0.7) produced surface-averaged Nu within 3.1% of published LES reference. Although air differs from blood, this checks coupling and wall flux exchange.

We also executed the vendor’s thermal regression suite that ships with 2024R1 and confirmed pass on all 18 heat-transfer-focused cases (report QA-FLU-REG-2024R1-TH).

4.2 Discretization and iteration
We created three meshes of the same geometry using hexa-dominant elements with prism layers:

- M1: 6.2 million cells, 12 prism layers, first layer height 6 μm (y+ ~1)
- M2: 12.8 million cells, 18 prism layers, first layer 4 μm
- M3: 24.6 million cells, 24 prism layers, first layer 2.5 μm

Refinement focused on stator-rotor gap, trailing edges, and thermal gradients in solid. For steady cases at 4 L/min, 8,000 rpm, 3.0 W loss:
- Peak wall temperature: M1=39.12 C; M2=39.05 C; M3=39.02 C. Extrapolated Richardson estimate gives 38.99 C with observed order 1.98; GCI95 on M2 is 0.04 C (0.1% of absolute).
- Bulk outlet temperature rise: M1=0.74 C; M2=0.72 C; M3=0.72 C; GCI95 on M2 is 0.01 C.
- Heat split to blood: M1=84.3%; M2=83.9%; M3=83.8%; GCI95 on M2 is 0.3%.

We ran all production cases on M2. Nonlinear residuals reduced below 1e-6 for energy, 1e-5 for momentum and turbulence. Global energy balance (electrical loss minus sum of enthalpy rise and solid conduction to saddle) closed within 0.3% across all cases.

Time-step sensitivity: A transient check with moving reference frame at Δt=1e-4 s and 5e-5 s over 0.5 s physical time showed cycle-averaged temperatures within 0.03 C of steady, confirming the steady RRF approximation is appropriate for mean thermal metrics.


5. Inputs and Their Uncertainty

The following were treated as variable parameters with uncertainty ranges for propagation:
- Motor electrical loss at given speed/flow: Normal(μ=3.0 W, σ=0.2 W) from bench dynamometer with calibrated power analyzer (0.5% reading + 0.05% FS)
- Thermal contact conductance (housing-saddle): Triangular(6,000, 10,000, 15,000 W/m^2-K) based on clamp torque tolerance and grease coverage inspection
- Blood thermal conductivity: Normal(0.52, 0.02) W/m-K reflecting hematocrit and temperature variation
- Blood cp: Normal(3,680, 120) J/kg-K across patient cohort
- Inlet flow rate (controller setpoint vs actual): Normal with σ=1.5% of reading from clamp-on ultrasonic flow meter calibration

Model form choices (e.g., SST vs realizable k-ε) were evaluated; see Section 8. We did not treat turbulence model coefficients as uncertain; instead, their effect is folded into validation error.


6. Lab Measurements for Comparison

We built a closed-loop mock circulatory rig with a glycerol-saline blood analog at 37.0±0.2 C. The test article was a production-equivalent LVAD (SN: M-THERM-017) with the same housing and potting as the final design. The pump was mounted in an aluminum saddle replicating implant geometry; the saddle’s contact surface was prepared per work instruction WI-THERM-07 (grease spec and torque).

Instrumentation:
- Mass flow: Transonic T201 flow meter, accuracy ±1.5%
- Inlet/outlet temperature: Neoptix T1 fiber optic probes (immune to EMI), ±0.1 C, placed 10D upstream and 10D downstream; sampled at 10 Hz, averaged over 5 min after steady state
- Surface temperature: FLIR A655sc IR camera for full-field mapping (emissivity calibrated on Ti), cross-checked with two PT100s bonded to the housing (±0.1 C)
- Electrical input: Yokogawa WT5000 power analyzer, ±0.05% FS

Test matrix: 8 operating points covering 2, 3, 4, 5, 6 L/min at 7,000–9,000 rpm and motor loss spanning 2.6–3.4 W. For each point we recorded after 20 min stabilization. The working fluid viscosity was tuned to match blood analog shear at relevant rates; Reynolds numbers and Prandtl were within 10% of target.

Data quality controls:
- Two repeated runs at 4 L/min, 8,000 rpm showed repeatability of ±0.05 C for outlet rise.
- Zero drift of probes checked in ice bath at test start and end (±0.03 C).
- Thermal leakage to ambient minimized with insulation; heat loss to air quantified by calorimetry to be 0.08±0.03 W and corrected in energy balance.

Uncertainty budget for outlet temperature rise combined Type A and B sources to ~±0.12 C (k=2). Surface temperature mapping uncertainty was ±0.2 C when cross-referenced with PT100s.


7. Model-to-Test Comparison

We aligned boundary conditions and motor loss to match measured electrical loss at each operating point (no free tuning). The contact conductance was set to 10,000 W/m^2-K (midpoint of expected), and sensitivity around this chosen separately.

Agreement metrics:
- Outlet temperature rise (ΔTout): Mean absolute deviation over 8 points = 0.08 C; maximum deviation = 0.19 C (at 2 L/min, 9,000 rpm). Model tended to underpredict slightly at lowest flow.
- Peak housing surface temperature: Mean absolute deviation = 0.31 C; maximum = 0.48 C at 6 L/min, 9,000 rpm.
- Spatial patterns: IR maps showed same hot-spot location near stator leads; model reproduced the gradient alignment within 6 mm.

We used error normalized by measurement uncertainty: for ΔTout, 7/8 points had |error| < 1σmeas; 1/8 point at low flow had 1.6σ. For surface temperature, all points within 2σ.

We did a single-parameter adjustment exercise to avoid overfitting: allowing only the contact conductance to vary within its measured range, a best-fit value of 9,200 W/m^2-K reduced mean bias on surface temperature by 0.07 C without materially changing outlet ΔT. For prediction, we held it at the midrange 10,000 W/m^2-K and treated the spread as uncertainty rather than calibration.


8. Model Structure Choices and Alternatives

- Turbulence closure: SST k-ω chosen for better wall heat transfer accuracy in adverse pressure gradient regions. We compared with realizable k-ε on M1 at 4 L/min. k-ε underpredicted HTC leading to +0.06 C higher wall temperatures; ΔTout difference was +0.03 C. Given validation data favored SST, we retained SST for all runs.
- Blood rheology: Bird-Carreau model versus Newtonian at μ=3.5 mPa·s. Newtonian assumption shifted ΔTout by less than 0.02 C at ≥4 L/min but up to 0.08 C at 2 L/min. Since intended use includes low-flow, we kept shear-thinning.
- Radiative exchange: Estimated <0.01 W using view factors; neglected.
- Rotor treatment: We tested steady frozen rotor versus transient sliding mesh on a trimmed geometry. Time-averaged ΔTout differed by 0.03 C; steady approach adopted for computational expediency.

Assumptions not modeled: Micro-scale near-wall RBC migration and thermal boundary layer modification, and patient tissue conduction outside the saddle (non-wetted surfaces), as the decision focuses on blood thermal rise and pump exterior temperatures in air/electronics lab conditions and in-blood environment. For in vivo external tissue, separate FEM shows tissue interface temperatures well below concern due to perfusion; that is out of scope here.


9. Sensitivity and Dominance

We screened influences using the Morris method with 40 trajectories on the M1 mesh, followed by a targeted Sobol analysis (500 samples with polynomial chaos surrogate validated to R^2=0.995 on 60 holdouts). At the nominal operating point (4 L/min, 8,000 rpm):
- ΔTout: First-order sensitivities S1: flow rate 0.61; motor loss 0.28; blood cp 0.07; conductivity 0.03; contact conductance <0.01. Interaction terms small (ST for flow 0.67).
- Peak surface temperature: S1: motor loss 0.54; contact conductance 0.31; flow rate 0.10; conductivity 0.03.

These results confirm controller set flow is the dominant driver for blood heating, while mounting quality is critical to housing temperature peaks. This breakdown informed our propagation in Section 10 and highlights where process controls (clamp torque, grease coverage) have the most leverage.


10. Propagating Variability and Reporting Bounds

We ran a Monte Carlo on the M2 mesh using 300 Latin Hypercube samples per operating condition, spanning the distributions in Section 5. Numerical error from Section 4.2 was injected as additive Gaussian noise with σ equal to GCI/2 for each metric.

Illustrative results at 3.0 W loss:
- 2 L/min: Predicted ΔTout median 1.06 C; 95% interval [0.87, 1.27] C. Peak surface temperature 40.1 C median; 95% [39.4, 40.8] C.
- 4 L/min: ΔTout median 0.72 C; 95% [0.60, 0.84] C. Peak surface 39.1 C; 95% [38.4, 39.7] C.
- 6 L/min: ΔTout median 0.50 C; 95% [0.41, 0.59] C. Peak surface 38.6 C; 95% [37.9, 39.2] C.

When combining with validation residuals via additive model discrepancy (Gaussian with σ equal to the RMSE of the model-to-test differences), the 95% bounds expanded by about 0.05–0.08 C for ΔTout and 0.1–0.15 C for surface temperature. Even with this, all scenarios remained comfortably below the 2.0 C blood rise and 41 C surface criteria.


11. Scope, Boundaries, and Where Caution Is Needed

- Operating domain: 2–6 L/min and 6,000–9,000 rpm. Extrapolation below 2 L/min is not advised without additional validation; the model underpredicted low-flow heating slightly.
- Fluids: Human blood properties vary with hematocrit and temperature; we bracketed cp and k. Viscosity uncertainty is less impactful on thermal metrics than on shear.
- Contact: The mounting saddle conductance is process-driven. Procedure WI-THERM-07 must be followed to ensure the assumed envelope.
- Environment: Air-side cooling during benchtop prep is not directly modeled in the in-blood runs; a separate set of air tests are used when assessing external handling conditions.
- Device variants: The model geometry is final design Rev D; changes in wall thickness >0.2 mm or potting material substitution would require a brief revalidation (we provide a reduced case plan in the appendix).


12. Comparability of Bench and In-Use Conditions

We matched relevant non-dimensional groups insofar as possible:
- Reynolds numbers at rotor exit and stator passages were within 10% of in vivo flow at equivalent setpoints using viscosity-matched analog.
- Prandtl number of the blood analog at 37 C was 21.4 vs 20.7 nominal for blood; impact on Nu scaling insignificant for our uncertainty.
- Heat generation placement mirrored the real motor via distributed body source based on winding layout.

Geometric fidelity: The test pump was production-equivalent, and the saddle surface finish and grease were controlled to the same work instruction. Instrument intrusiveness was minimized; fiber probes were well upstream/downstream to avoid disturbing local HTC around the pump.

Given these alignments, we consider the test rig suitably representative for thermal prediction of the target outputs.


13. People, Process, and Tools

- Team expertise: The analysis lead (S. Kim, PhD) has 12 years in rotating machinery CHT; two analysts (A. Nunez, M. Eng.; P. Rao, MS) executed meshing and postprocessing. All are trained on biomedical device modeling practices, including biothermal properties and hemocompatibility concerns.
- Peer review: A separate internal group (Structures & Reliability) reviewed the plan and results (IRR-CHT-2026-04). We also solicited an external SME (Prof. M. Hart, Univ. of Michigan) to comment on turbulence and HTC treatment; feedback incorporated in Section 8.
- Software configuration: Solvers and scripts tracked via Git (repo LVAD-CHT, tag v1.3.2). Case files, meshes, and post scripts have immutable SHA digests recorded in the run log RL-CHT-017. Fluent journal files ensure button-for-button repeatability.
- Quality management: This work follows SOP-MOD-007 (Simulation Controls and Records). All data files are stored in the validated PLM system under item SIM-THERM-LVAD-R1.3 with access control and audit trail.


14. Evidence of Numerical Robustness and Reproducibility

Five randomly chosen Monte Carlo samples were re-run on a different compute node (AMD EPYC) and with the realizable k-ε closure to check sensitivity to platform and closure. Temperatures differed by less than 0.06 C relative to the baseline SST runs on Xeon, attributable to closure differences rather than platform. Reruns on the same platform reproduced within 0.01 C, confirming determinism of journals and environment.


15. Traceability and Record-Keeping

- Each figure in this report has a source path embedded in the caption and is reproducible from the main postprocessing script post_therm.py (commit 4a6d2b9).
- Test data sets carry lot numbers for probes and fluid compositions; calibration sheets are attached. The linkage between test case IDs and simulation IDs is captured in Table A1 (appendix).
- Assumption logs (AL-CHT-2026-03) record the rationale for neglected radiative effects and for using SST k-ω.

A change control entry (CCN-THERM-71) documents the switch from M1 to M2 mesh after the convergence study, and the impact statement shows no safety conclusions altered.


16. Limitations and Future Work

- Flow physics at very low rates (<2 L/min) could enter transitional regimes where both turbulence models perform less reliably. Additional targeted validation is planned for 1.5 L/min with a lower-Re analog fluid.
- We did not model hemolysis or protein denaturation directly. While temperature is a proxy metric with accepted thresholds, coupling to a damage model would be a next step for a fully integrated hemocompatibility assessment.
- The contact conductance distribution was inferred from process parameters rather than measured on the exact assembled joint; we partially mitigated this by bracketing and sensitivity analysis.
- Uncertainty in blood cp and k is patient dependent; although covered statistically, extreme outliers (e.g., severe anemia or hyperthermia) were not explicitly simulated.


17. Conclusions Relevant to Decisions

- Under expected and high-loss conditions, predicted outlet blood temperature rises are well below 2.0 C across 2–6 L/min. Including numerical, input, and model-form discrepancy contributions, the 95% upper bound at 2 L/min is 1.35 C for 3.4 W loss.
- Maximum exterior housing temperature in blood environment remains under 41 C with 95% confidence; typical values range 38.4–40.8 C depending on flow and loss.
- Numerical solution quality is high: mesh refinement and solver checks show negligible discretization bias relative to the decision thresholds.
- Bench comparisons support the model: deviations are small and mostly within measurement uncertainty, with a modest underprediction tendency at the lowest tested flow.
- Sensitivity analysis highlights process knobs: ensuring flow accuracy and maintaining proper saddle contact are the largest levers for margin.

With these findings, the model is suitable for use in design sign-off and as supportive evidence in the regulatory package for thermal safety, provided use stays within the stated operating envelope and assembly controls are enforced.


18. References and IDs

- DFMEA-LVAD-THERM-2026-02, Rev A
- SOP-MOD-007, Simulation Controls and Records, Rev D
- WI-THERM-07, Saddle Mount Thermal Interface Procedure, Rev B
- IRR-CHT-2026-04, Internal Independent Review
- QA-FLU-REG-2024R1-TH, Fluent Thermal Regression Results
- RL-CHT-017, Run Log and SHA digests
- CCN-THERM-71, Mesh Upgrade Impact Statement

Appendix A: Details and supplemental figures



Appendix A. Supplemental Detail

A1. Mesh and Case Mapping
- M1: 6.2M cells; M2: 12.8M; M3: 24.6M. Scripts: mesh_gen_wb.wbjn; mesh IDs: M1_20260410_01, M2_20260415_03, M3_20260420_02.
- Operating points and mapping to test cases:
  - Sim S1 (2 L/min, 7k rpm, 2.6 W) ↔ Test T1 (log: 2026-05-02-14:32)
  - S2 (2 L/min, 9k rpm, 3.4 W) ↔ T2 (2026-05-02-16:07)
  - S3 (3 L/min, 8k rpm, 3.0 W) ↔ T3 (2026-05-03-09:41)
  - S4 (4 L/min, 8k rpm, 3.0 W) ↔ T4 (2026-05-03-12:05)
  - S5 (5 L/min, 8k rpm, 3.2 W) ↔ T5 (2026-05-03-14:22)
  - S6 (6 L/min, 9k rpm, 3.4 W) ↔ T6 (2026-05-03-16:10)
  - S7 (4 L/min, 7k rpm, 2.8 W) ↔ T7 (2026-05-04-10:15)
  - S8 (6 L/min, 7k rpm, 2.6 W) ↔ T8 (2026-05-04-12:50)

A2. Solver Settings
- Pressure-velocity: Coupled, pseudo-transient with initial pseudo-time step 1e-3 s; relaxation factors: pressure 0.3, momentum 0.7, energy 1.0
- Turbulence: SST with curvature correction off; production limiter on
- Wall treatment: Automatic near-wall; resolved viscous sublayer
- Solid–fluid coupling: One-way iterative coupling within the monolithic solver, fully coupled energy equation

A3. Instrument Calibrations
- Neoptix T1 probes calibrated 2026-04-15, cert CAL-NEO-2026-0415, traceable to NIST
- Transonic T201 flow meter calibration curve fit RMSE 0.7% of reading
- FLIR emissivity calibration: εTi=0.30 with black tape reference; validation to PT100 difference ≤0.12 C

A4. Additional Plots (not embedded here)
- Residual histories and energy closure plots for all M2 runs (see folder figs/residuals/)
- IR thermograms vs CFD surface temperature contours (figs/ir_vs_cfd/)
- Sobol indices by operating point (figs/sobol/)

A5. Quick Re-run Instructions
- Checkout repo LVAD-CHT at tag v1.3.2
- Execute python prepare_cases.py — this will generate M2 mesh and journal per operating point
- Launch Fluent in batch: fluent 3d -g -i journals/run_Si.jou
- Postprocess: python post_therm.py; results will populate results/ with CSV and PNG files

End of Report
