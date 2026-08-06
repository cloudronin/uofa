Title: Credibility Assessment Report — CFD of a Centrifugal LVAD for Pressure–Flow and Blood Damage Predictions

Prepared by: Fluid Systems Modeling Group  
Date: 2026-08-06  
Model ID: LVAD-CFD-hem_v3.4 (Git tag 3.4.7; container hash sha256:c1a7…a9d2)

1. Background and Decision Context

This document records the evidence package supporting use of a computational fluid dynamics model of a rotary blood pump (centrifugal LVAD) to inform two product decisions prior to first-in-human evaluation:

- Primary endpoint for decision-making: predicted pressure rise (head) across the pump versus flow (H–Q map) from 2 to 6 L/min at rotational speeds from 2400 to 3600 rpm, at 37 °C.
- Secondary endpoint: predicted normalized index of hemolysis (NIH) under steady inlet conditions, assessed as a screening tool to rank design variants and set guard bands for verification testing.

How the model is used:
- The engineering team uses the computed H–Q map to set firmware speed-limiter curves and to size the battery pack for worst-case hydraulic load.
- The hemolysis estimate is not used directly for patient risk claims; it is used to prioritize benchtop tests and to determine whether a design iteration proceeds to full ISO 7199 blood loop testing.

Impact of a wrong answer:
- If the H–Q map is off by more than roughly 5%, the controller limits or performance margins could be mis-set, potentially causing insufficient perfusion or unexpected alarms. Downstream clinical consequence is moderate if caught in verification, high if it escaped to use.
- If the hemolysis ranking between nearby designs is mis-ordered, the wrong variant might be selected for testing; the consequence is schedule and cost, and only indirectly affects safety at this stage.

Influence of the model on these decisions:
- H–Q: medium-to-high influence; the map derived here seeds firmware parameters that are confirmed later with water-glycerol rig tests, but this CFD drives which tests are run first and the expected ranges.
- NIH: low-to-medium influence; the CFD result is one input among several (including historical priors and designer judgment) for gate reviews.

Given this risk posture, we adopted mid-to-high rigor for the hydraulic map and mid-level rigor for blood damage, as described below. Acceptability targets were set up front: for the H–Q map, we required less than 3% numerical error at the final mesh, and agreement to within 5% against lab data across the operating window. For NIH, we required monotonic ranking agreement across designs and absolute error less than 30% when compared to lab NIH, acknowledging the limitations of current damage models.

2. Model Formulation and Implementation

Governing physics and closure choices:
- Incompressible, isothermal Navier–Stokes with rotating frame (multiple reference frames, frozen rotor for the H–Q map; unsteady sliding mesh for hemolysis studies at 2400 rpm).
- Blood rheology: Carreau–Yasuda viscosity with μ0 = 0.16 Pa·s, μ∞ = 0.0035 Pa·s, λ = 3.313 s, a = 2, n = 0.3568; hematocrit set to 40% baseline. For sensitivity, we also ran Newtonian at μ = 3.5 cP.
- Turbulence: k–ω SST with curvature correction (Spalart–Shur), low-Re wall treatment. Transitional effects are not explicitly modeled; y+ ≤ 1 on all walls.
- Hemolysis surrogate: scalar transport equation for cumulative damage using the power-law formulation dD/dt = C·τ^α, with C and α taken from Giersiepen et al. (baseline C = 3.62e-7, α = 2.416) and an alternate parameter set (Heuser–Optiz) for model-form sensitivity. Exposure time integration is performed along pathlines with sub-stepping tied to the local strain rate.

Software and numerics:
- Solver: ANSYS CFX 2024 R1 for steady MRF; ANSYS Fluent 2024 R1 for unsteady sliding mesh hemolysis runs (consistency checked; see Section 5).
- Spatial discretization: second-order upwind for momentum and turbulence, bounded central differencing for hemolysis scalar. Pressure–velocity coupling via coupled solver (CFX) or SIMPLEC (Fluent).
- Time integration (hemolysis runs): second-order implicit, Δt chosen to maintain maximum convective Courant number below 2 in the impeller passages (nominal Δt = 1e-4 s at 2400 rpm), with a time-step sensitivity sweep.
- Geometry: production CAD of LVAD Rev E (impeller outer diameter 34.8 mm; blade count 7; volute cutwater angle 12°). Tip clearance set to 80 μm per measured assembly.

3. Inputs, Boundary Conditions, and Their Characterization

- Inlet: mass flow rate specified per operating point; inflow turbulence intensity set to 5% ± 2% (triangular distribution), length scale 1 mm. For unsteady hemolysis cases, flow is nominally steady.
- Outlet: static pressure fixed; value adjusted to achieve target flow rates at each speed (matching lab protocol).
- Fluid properties: density 1050 kg/m^3 at 37 °C; viscosity per Carreau–Yasuda with ±10% uncertainty band on μ∞ and ±15% on λ to represent donor variability.
- Wall conditions: no-slip; smooth (Ra < 0.2 μm); rotor–stator interface modeled with frozen rotor for H–Q and transient sliding mesh for hemolysis.
- Manufacturing tolerances: tip clearance sampled at 60–100 μm in uncertainty propagation; blade-to-hub fillet radius ±0.05 mm.
- Rotor speed tolerance: ±10 rpm.

Input uncertainties for propagation were assigned based on metrology reports (clearance), fluid lab sheets (viscosity parameters), and vendor tachometer calibration (speed). Epistemic versus aleatory distinctions were noted: viscosity variations treated as aleatory (donor-to-donor), while coefficients in the damage model were treated as epistemic model-form parameters.

4. Numerical Soundness: Code Checks and Solution Quality

Code-level checks:
- Two manufactured-solution tests were set up in Fluent (laminar manufactured vortex and rotating Couette with source term). Observed spatial order 1.95–2.01 on poly meshes matched expectations for second-order schemes. Time-stepping showed order ≈ 2.0 for the unsteady manufactured field.
- A rotating-frame benchmark (Taylor–Couette, inner cylinder rotation 2000 rpm, gap 0.5 mm) produced torque within 1.2% of the analytical laminar solution at Re = 200.

Solver consistency:
- For a common speed/flow point (3000 rpm, 4 L/min), CFX MRF and Fluent steady sliding mesh produced head within 0.6% on matched meshes. Residuals were reduced by six orders of magnitude and kinetic-energy imbalance < 0.2%.

Mesh and time resolution:
- Three meshes were built from the same CAD with poly-prism topology. Key metrics are listed in Appendix A. Briefly, coarse/medium/fine had 7.9M/14.8M/28.6M cells; minimum orthogonality > 0.18; average y+ 0.7 on the fine grid.
- Mesh refinement study at 3000 rpm, 4 L/min yielded H values of 109.1/110.5/111.0 mmHg. Extrapolated head at zero grid size 111.4 mmHg; observed order p ≈ 1.96. Grid convergence index (95% confidence) computed via Roache’s method gave 0.9% on the fine mesh.
- Time-step sensitivity for hemolysis at 2400 rpm, 4 L/min: with Δt = 2e-4, 1e-4, and 5e-5 s, domain-averaged damage differed by +6.4% and +2.1% relative to the smallest Δt; target set to ≤3% yielded Δt = 1e-4 s as acceptable.

Convergence behavior:
- For steady points, scaled residuals below 1e-6, mass/energy imbalance < 0.1%, and integral H stabilized to <0.05% over 200 additional iterations.
- For transient runs, phase-averaged signals over 12 rotor passes showed repeatability of NIH over the last 4 passes within 1.8%.

5. Comparison Against Physical Tests

Independent experiments:
- Hydraulic tests per ISO 7199 were performed on the Rev E pump with a water–glycerol mixture tuned to match the Carreau model’s high-shear viscosity at 37 °C (3.5 cP). Flow rates 2, 3, 4, 5, and 6 L/min at 2400, 3000, 3600 rpm. Pressure rise measured with Rosemount 3051 differential transducers (±0.075% span); flow via Transonic clamp-on (±2%).
- Blood loop hemolysis tests used bovine blood at Hct 38–42%, run at 2400 rpm and 3, 4, 5 L/min for 2 hours with standard sampling; NIH computed per ASTM F1841. Triplicates were run on separate days. Lab temperature 36.8–37.2 °C.

Mapping model-to-measure:
- For hydraulic comparison, CFX simulations were run with Newtonian μ = 3.5 cP to match the rig fluid used for H–Q; this alignment avoids rheology confounding. For hemolysis, the CFD used the Carreau model; in post-processing, residence-time-weighted shear histories were converted to plasma free hemoglobin increase via the power-law surrogate, then to NIH for direct comparison to the bench metric.

Validation results:
- Hydraulic: Across 15 operating points, mean absolute percentage error (MAPE) of head was 2.7%; worst case 4.9% at 2 L/min/2400 rpm, attributed to low-Re transition not fully captured. Slopes of H–Q curves matched within 3%. Repeat test-day variability in the lab was 1.3% (1σ).
- Hemolysis: Using the baseline Giersiepen coefficients, CFD-predicted NIH overestimated lab NIH by 24% on average (RMSE 0.010 g/100 L), with correct ranking across three design variants (Rev D, E, and E+ with larger tip). Using the alternate coefficient set reduced the bias to +12% but slightly worsened ranking confidence at 5 L/min. Error bars accounting for viscosity and tolerance variations encompassed the measured NIH in 5 of 9 test conditions.

Acceptance criteria and pre-specification:
- Targets were declared prior to any comparison: For head, each point to be within 5% and overall MAPE < 4%; both were met. For NIH, absolute error < 30% and correct ranking across designs; both were met on average, though two points at 5 L/min marginally exceeded 30% with the baseline coefficient set.

6. Coverage of the Intended Operating Space

The intended application window is 2–6 L/min and 2400–3600 rpm with blood rheology consistent with Hct 35–45% and temperature 36–38 °C. Validation coverage:
- Hydraulic map: all speeds and flows tested; model-to-rig mapping was one-to-one using matched reference viscosity.
- Hemolysis: tested at 2400 rpm and mid-to-high flows; lower and upper speeds were not tested in blood due to sample limitations. Extrapolation is modest with respect to Reynolds number but involves uncertainty in the damage law’s exponent at different shear/higher residence times.

Similarity assessment:
- Non-dimensional groups in CFD vs tests: impeller Reynolds number within ±5% across matched points; blade tip Mach < 0.005 everywhere; Strouhal based on blade passing for transient runs < 0.02; these suggest comparable flow regimes.
- Geometry used in CFD matches the as-tested parts; CMM reports showed differences < 30 μm on key features, incorporated into the tolerance sweep.

7. Sensitivity and Uncertainty Propagation

Parameter importance:
- A Morris screening on 12 inputs identified three dominant contributors to H: tip clearance, viscosity at high shear, and rotor speed. For NIH, dominant factors were tip clearance, damage exponent α, and the intermittency of high-shear zones near the blade trailing edge as mediated by turbulence model constants.
- A variance-based analysis (Sobol’) on a surrogate built from 220 CFD points (Gaussian process with leave-one-out error 1.1% for H and 9.2% for NIH) quantified first-order indices: for H at 4 L/min, S_tip ≈ 0.41, S_μ ≈ 0.27; for NIH, S_α ≈ 0.38, S_tip ≈ 0.31, S_μ ≈ 0.14.

Uncertainty propagation:
- Using a Latin hypercube of 300 runs on the coarse mesh with correction factors for discretization error (from GCI) and a model-form spread (hemolysis coefficient sets spanning literature), the 95% interval for head at 3000 rpm/4 L/min is [108.2, 112.7] mmHg with a median 110.4 mmHg. This interval width is dominated by tip clearance and viscosity assumptions; discretization contributes < 1%.
- For NIH at 2400 rpm/4 L/min, the 95% interval is [0.026, 0.044] g/100 L with median 0.035; experimental triplicates were 0.029, 0.031, 0.032. The CFD interval includes both literature coefficient sets weighted equally; reweighting using our calibration (Section 8) narrows the upper tail by ~15%.

8. Calibration Separation and Model-Form Considerations

We fit the damage coefficient C on an older Rev C pump dataset (n = 6 points) not used in validation, using least squares on log(NIH) versus log(∫τ^α dt) with α fixed at 2.416. The fitted C differed by +9% from the literature value; cross-validation showed no overfit (RMSE within 5% of the holdout). This adjusted C was applied in a sensitivity branch but not in the primary validation reporting above to preserve independence. The adjusted value marginally improved agreement at 3 L/min and degraded 5 L/min by < 5%.

We also ran a one-off LES (WALE model) on a 42M-cell mesh at 3000 rpm/4 L/min to examine coherent structures unresolved by RANS. The time-averaged H matched RANS within 0.8%; peak instantaneous shear 5–10% higher in tip leakage, suggesting that the RANS-based hemolysis could slightly under-predict tail risk in damage exposure. We included this as model-form uncertainty by inflating the upper NIH interval by 10% on points dominated by tip leakage.

9. Software Quality, Reproducibility, and Independence

- Version control: All meshes, case files, and post-processing scripts are under Git LFS and DVC; the exact states are pinned by tag 3.4.7. The CAD snapshot is Vault rev E-17.
- Automation: Cases are generated from a Python driver (PumpRunner 2.3). The run pipeline is containerized (Ubuntu 22.04 base) with exact solver patches documented; Slurm scripts for HPE Apollo nodes using Intel MPI are archived. A nightly regression uses a reduced geometry to check for drift in head and torque.
- Peer checks: A separate analyst (not the case set-up author) reran the 3000 rpm/4 L/min point from scratch using an independently meshed grid (snappyHexMesh). Head matched within 1.1%; shear hotspot locations were similar by visual comparison and by a Dice coefficient of 0.83 on iso-τ=300 Pa surfaces.
- Human review: A senior fluid SME external to the LVAD program reviewed the mesh strategy, y+ maps, and convergence metrics and provided two change requests (increase near-shaft prism layers; adopt curvature correction). Both were implemented before final runs.
- Hardware determinism: Runs were repeated on two clusters with different compilers (Intel oneAPI 2024 vs GCC 12); results differed by < 0.2% in head and < 3% in NIH, within post-processing stochastic noise due to particle seeding in the pathline integrator.

10. Evidence Traceability and Records

- Data package index: See Appendix C. This includes case setup sheets, boundary condition rationales, lab calibration certs, experiment raw CSV files, and CFD residual histories. Each plotted point in this report is linked to an artifact ID.
- Acceptability thresholds, pass/fail results, and change logs are recorded in JAMA Connect item J-COU-032 with immutable history. Any deviations (none for H–Q; one for NIH ranking tie-breaker at 5 L/min) are documented with justification.
- All scripts to reproduce figures and statistics are in the repo under /analysis/lvad_v3p4 with a Makefile target “make paper”.

11. Limitations and Residual Concerns

- Transitional flow at the lowest speed and flow is not explicitly captured by the RANS closure; this is the worst outlier in H–Q. If the controller is extended to operate below 2 L/min, additional model updates (γ–Reθ transition model) should be considered.
- Hemolysis modeling via single-parameter power law does not capture sublethal damage accumulation, platelet activation, or margination. The model is used for ranking only, with explicit acknowledgment of model-form bias; clinical claims will rely on in vitro and in vivo data.
- Cavitation is not modeled. Based on NPSHr calculations, margin to cavitation inception at 6 L/min/3600 rpm is > 30 kPa at 37 °C, so omission is acceptable in current COU; if lower inlet pressures are contemplated, the model needs extension to a cavitation-capable formulation.
- Thermo-viscous heating is neglected (single-temperature assumption). With measured temperature rise < 0.5 °C over 2 hours in bench tests, this is not expected to affect viscosity materially.
- Only one turbulence closure was used for production (SST-CC). The single LES spot check suggests a possible high-shear tail; we accounted for this as an uncertainty inflation for NIH only.

12. Overall Credibility Judgment Relative to Intended Use

- For the hydraulic performance map, the body of evidence meets the pre-declared thresholds for numerical accuracy, comparison quality, and operating space coverage. The model is fit for the purpose of setting firmware guard bands and prioritizing rig points, with low residual risk.
- For hemolysis ranking and approximate magnitude, the model performance and quantified uncertainties are adequate for screening. The limits of the surrogate physics are prominent; it should not be used to set absolute limits or clinical safety margins.

13. Summary of Key Numbers

- Mesh convergence: fine-grid GCI for head 0.9% (95%); time-step error for NIH 2.1%.
- Agreement to hydraulic tests: MAPE 2.7% (max 4.9%).
- Agreement to blood-loop NIH: bias +24% with baseline coefficients; improved to +12% with alternate fit; ranking preserved across three designs.
- Dominant uncertainties: tip clearance, viscosity parameters, damage exponent.
- Reproducibility: independent redo within 1.1% for H; solver change impact on NIH < 3%.

Appendices

Appendix A. Mesh and Solver Quality Highlights
- Coarse: 7.9M cells, 9 prism layers, first layer 5 μm, average y+ 1.2, min orthogonality 0.18, max non-orthogonal 64°.
- Medium: 14.8M cells, 13 prism layers, first layer 3 μm, average y+ 0.85, min orthogonality 0.21, max non-orthogonal 59°.
- Fine: 28.6M cells, 17 prism layers, first layer 2 μm, average y+ 0.7, min orthogonality 0.24, max non-orthogonal 54°.
- Residual histories: momentum and continuity dropped below 1e-6; turbulence equations below 1e-6; hemolysis scalar below 1e-7.
- CPU hours: fine steady point 420 core-hrs; transient hemolysis point 5600 core-hrs (0.1 ms time step, 0.6 s physical time with 12 passes).

Appendix B. Experimental Data Quality
- Pressure transducers calibrated within 30 days before test; as-left check within 0.02% span. Flowmeter factory calibration traceable to NIST.
- Repeatability: hydraulic H across three days at 3000 rpm/4 L/min varied by 0.9% (1σ). NIH triplicates CV 6.1%.
- Temperature control ±0.2 °C; degassing performed to 40% saturation; no visible bubbles in the loop.

Appendix C. Traceability Map (selected)
- CFD run ID HQ_3000_4.0_med → artifact ACFD-221; mesh M-14p8; commit 7d32e1b.
- Rig dataset HQ_3000_4.0_day2 → artifact ARIG-114; raw CSV R-2026-06-15-2.csv.
- NIH CFD transient run NIH_2400_4.0_t1e-4 → artifact ACFD-309; postproc script hem_proc_v12.py.
- Blood loop dataset NIH_2400_4.0_day1 → artifact ABLD-093.

Appendix D. Pre-Specified Acceptance Targets
- Numerical: H GCI < 3%; NIH time-step error < 5%.
- Comparisons: H pointwise < 5%, MAPE < 4%; NIH absolute < 30% with correct ranking.
- Coverage: at least three flow rates per speed in hydraulic; at least two flows for NIH at one speed; similarity checks within 10% on Re.

Change Log
- v3.3 → v3.4: added curvature correction; updated prism layers; added independent analyst rerun; added LES spot check.
- Deviations: none for H–Q; NIH ranking between Rev E and E+ at 5 L/min was statistically indistinguishable in CFD; decision deferred to lab data (tie broken by bench, favoring E+).

Concluding Note

The presented evidence reflects our best current understanding of the pump’s fluid mechanics and the practical limits of hemolysis surrogates. The results are reproducible, traceable, and anchored to relevant experiments. The model is appropriate for the intended engineering decisions when used within the documented bounds and with the stated caveats.
