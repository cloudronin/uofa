# Conjugate Thermal-Fluid Model Credibility Report
Project: PCU Cold Plate for EPS Rack  
Model tag: CP-CHT-v1.6  
Date: 2026-08-05  
Analyst: Thermal-Fluid Group, Avionics Systems

## 1. Background and Intended Use

The purpose of this analysis is to estimate component junction temperatures and coolant-side pressure drop for the Power Conditioning Unit (PCU) cold plate under representative orbital heat loads. The results inform mechanical layout and pump sizing and will be used to set guardbands on allowable inlet temperature and flow rate for the thermal-fluid loop.

The model represents a single cold plate module hosting six IGBTs and ancillary drivers mounted to a copper baseplate, which is bolted to a machined aluminum serpentine-channel cold plate. The working fluid is a 50/50 ethylene-glycol/water mix. Downstream system-level effects (e.g., heat exchanger performance, pump speed control) are not included; those are addressed in separate system models.

Scope:
- Steady-state thermal-fluid performance at three load cases: 300 W, 450 W, 600 W total die power.
- Flow rates between 0.08 and 0.20 kg/s, inlet temperature between 10 C and 35 C.
- Conjugate conduction through solids with turbulent coolant flow.

Excluded from the present phase are radiation to the environment, thermal cycling fatigue, and off-nominal coolant compositions.

## 2. Model Overview

Toolchain and versions:
- CAD preparation in Siemens NX 2306; defeatured geometry exported as Parasolid.
- Meshing and solution in STAR-CCM+ 2023.1.2 (build 17.06.007).
- Post-processing in ParaView 5.11 and in-house Python 3.11 scripts (repo: thermal-tools/cp-cht).

Domain and physics:
- Conjugate heat transfer: 3D conduction in solids coupled to RANS in the coolant passages.
- Turbulence model: SST k-omega with low-Re wall treatment.
- Fluid properties: temperature-dependent density, viscosity, Cp, k for EGW 50/50 using ASHRAE correlations, evaluated at local T.
- Solid properties: k(T) for 6061-T6 aluminum and C110 copper; vendor datasheet values for TIM and dielectric pads.
- Interfaces: bonded contacts except for TIM interfaces, which use specified thermal contact conductance.

Geometry fidelity:
- Realistic channel geometry and plenum details retained; fillets and chamfers <0.5 mm suppressed to reduce cell count.
- Fastener holes capped and represented as isothermal constraints on bolt axes were not needed; mechanical preload effects on contact conductance are captured via measured Hc values.

Boundary conditions:
- Inlet: mass flow rate (0.08–0.20 kg/s) and temperature (10–35 C).
- Outlet: pressure outlet at 0 Pa gauge.
- Heat loads: six uniform volumetric heat sources mapped to die footprints, consistent with electrical bench.
- External walls: adiabatic.

## 3. Approach

3.1 Mesh and numerics
- Poly-hexcore mesh with prism layers (10 layers, growth 1.2) on all fluid–solid and solid–solid interfaces.
- Near-wall resolution targeted at y+ ≈ 0.8 on coolant side at nominal case (0.12 kg/s, 20 C inlet).
- Three mesh levels (coarse/medium/fine) for grid sensitivity: 11.2M / 18.7M / 31.4M cells total; fluid region 60–65% of total.
- Spatial discretization: second-order upwind for momentum and turbulence, second-order for energy; coupled solver for pressure–velocity.
- Convergence criteria: normalized residuals <1e-5 for all equations; mass imbalance <0.2%; energy imbalance <0.1%.

3.2 Input data development
- Material properties collected from vendor datasheets and literature; temperature dependence incorporated where available.
- Thermal interface material (TIM) conductance measured in-house using a guarded heat flow meter at 40, 60, and 80 C under 0.3 MPa clamping force; interpolated to analysis conditions.
- Heat loads per die set from electrical bench power map (12.5 V bus), including 5% overhead for gate drive losses.
- Coolant properties functions cross-checked against NIST REFPROP values at select temperatures.

3.3 Comparison-to-test
- A coupon-level cold plate with the same channel layout was instrumented with 12 surface thermocouples (K-type, 36 AWG) at die corners and two in-line RTDs for coolant temperatures; inlet/outlet pressures via 0–3 bar transducers.
- Tests at three flow rates (0.09, 0.12, 0.16 kg/s) and two power settings (300, 450 W); inlet temperature ~20.0±0.3 C.
- Emissivity-corrected IR thermography used to cross-check two TC locations.

3.4 Sensitivity and uncertainty
- One-at-a-time local sensitivities: varied inlet temperature, flow rate, TIM conductance, and turbulence model constants within accepted ranges; recorded impact on peak junction temperature and pressure drop.
- Probabilistic analysis: Latin Hypercube Sampling (LHS) with 200 runs on medium mesh, uncertain inputs as follows:
  - Inlet temperature N(20 C, 0.5 C)
  - Mass flow N(0.12 kg/s, 0.006 kg/s), truncated at ±2σ
  - TIM conductance lognormal with median 14,000 W/m²-K, GSD 1.15
  - Aluminum conductivity k_Al ~ N(167 W/m-K, 5 W/m-K) to reflect batch variability
  - Die power per IGBT N(75 W, 3 W), correlated ρ=0.6 across devices

3.5 Reproducibility
- Pre-processing and solver settings scripted (STAR-CCM+ Java macros) committed at tag cp-cht-1.6.0.
- All input decks, property files, and boundary condition spreadsheets under version control (Git LFS); archived results on the project SharePoint with hash checksums.

## 4. Findings

4.1 Thermal performance
- Nominal case (450 W, 0.12 kg/s, 20 C inlet): predicted maximum die junction temperature 78.4 C; average coolant temperature rise 2.9 C.
- Temperature non-uniformity across dies within ±2.1 C; hottest location on die D3, consistent with local flow maldistribution seen in velocity contours.

4.2 Hydraulic performance
- Predicted pressure drop from inlet plenum to outlet plenum at nominal: 18.7 kPa; scales approximately with square of flow rate as expected.

4.3 Behavior over envelope
- Over the studied range, peak junction temperature changes approximately linearly with inlet temperature (slope ~0.98 C/C) and decreases sublinearly with mass flow (−23 C per +0.1 kg/s at 450 W).
- The model indicates diminishing returns above ~0.18 kg/s due to near-saturation of convective coefficients in the microchannels.

## 5. Evidence Supporting Trust in the Results

The following items document why the outputs are suitable for early design decisions.

5.1 Geometry and physics choices
- The main heat-flow paths are explicitly resolved: die → solder → copper baseplate → TIM → aluminum cold plate → coolant.
- Electronic packaging details not influencing the dominant resistance network (e.g., silkscreen, small fillets) were removed to reduce mesh burden; sensitivity trials confirmed <0.5 C impact on T_max when reinstating a representative subset.
- The SST k-omega model with low-Re treatment was selected based on canonical literature for channel flows at Re≈2×10⁴, providing robust heat transfer predictions without wall functions.

5.2 Grid and solver behavior
- Mesh refinement study at nominal conditions produced the following peak die temperatures:
  - Coarse: 79.5 C
  - Medium: 78.7 C
  - Fine: 78.4 C
  Extrapolation using a monotonic convergence assumption yields an estimated asymptotic value of 78.2 C; the change from fine to extrapolated is 0.2 C (~0.26%), which we take as a measure of residual grid sensitivity.
- Pressure drop changed by 0.8 kPa between medium and fine meshes (4.1%).
- Residuals reached 1e-5 for all equations, with flattened trends over 2,000 iterations; energy balance error under 0.1% for all runs in the envelope.

5.3 Code-level checks
- A separate conduction-only model of a 1-D slab with imposed heat flux matched the analytical temperature profile within 0.1 C.
- At the fluid–solid interface, integrated heat flux on the coolant side matched the solid-side heat transfer within 0.15% at convergence, verifying interface coupling consistency.

5.4 Input pedigree and traceability
- TIM conductance values were obtained via in-house measurement under application-representative clamping, rather than taken solely from vendor brochures; raw data and calibration certificates are stored in the lab QA folder; analysis used the interpolated value at 65 C and 0.3 MPa (Hc = 14,200 W/m²-K).
- Coolant properties were parameterized from published correlations; spot-check at 20 C produced μ = 3.5 mPa·s vs REFPROP 3.46 mPa·s (1.2% delta).
- Die power distributions were based on measured currents with ±1% meter accuracy; the mapping per die matches the test harness configuration.

5.5 Test comparison
- For the six instrumented die corners, the average absolute difference between model-predicted and measured surface temperatures at the 450 W, 0.12 kg/s test was 1.9 C; the largest single-point deviation was 3.4 C at the upstream corner of D2.
- The predicted and measured pressure drops at the same test point were 18.7 kPa and 19.6±0.5 kPa respectively (4.6% low).
- At 300 W, 0.09 kg/s, the model overpredicted the hottest TC by 2.3 C; at 0.16 kg/s, agreement tightened (<1.5 C average), consistent with flow being more fully developed.

5.6 Sensitivity insight
- Local derivatives at the nominal point:
  - ∂T_max/∂T_in ≈ +0.98 C/C
  - ∂T_max/∂ṁ ≈ −230 C·s/kg (equivalently −23 C per +0.10 kg/s)
  - ∂T_max/∂Hc_TIM ≈ −0.00012 C·m²·K/W (i.e., a +10% increase in Hc reduces T_max by ~0.17 C)
- Pressure drop sensitivity to flow is near quadratic as expected; turbulence-model constant variations within widely cited ranges changed T_max by ≤0.6 C.

5.7 Probabilistic outcomes
- For the 200-sample LHS at 450 W, 0.12 kg/s nominal means and distributions as defined:
  - 90th percentile of T_max: 81.1 C
  - Mean T_max: 78.9 C; standard deviation: 0.95 C
  - Pressure drop 90th percentile: 20.3 kPa
- Main contributors to T_max spread (Sobol index approximation from rank regression):
  - Inlet temperature: ~61%
  - Mass flow: ~27%
  - TIM conductance: ~9%
  - Material property variances: remainder
  These indicate inlet temperature control is the primary lever.

5.8 Applicability boundaries
- The model is exercised and compared-to-test within 300–450 W total power at 20 C inlet; extrapolation to 600 W uses the same physics but is not yet bench-verified.
- Valid for mass flow in 0.08–0.20 kg/s and inlet temperatures 10–35 C; beyond this, the turbulence model choice and property fits should be revisited.
- Geometry variations beyond ±2% channel width or altered plenum manifolds are out-of-scope for this calibration.

5.9 Reproducibility and configuration control
- The exact state used for this report is tagged (cp-cht-1.6.0). Re-running runset “rs-450W-012kgps-20C” on the reference Linux node (RHEL 8.8, dual EPYC 7513) reproduces the T_max within 0.05 C and pressure drop within 0.2 kPa.
- Any changes to die power mapping or TIM properties require updating two files (powers.yaml, tim_hc.csv). The macros report file hashes at solver launch; mismatches are flagged in the run log.

## 6. Limitations and Open Items

- Test coverage: The comparison-to-test is currently limited to two power points (300 and 450 W) at ~20 C inlet. The 600 W case and colder/hotter inlets will be exercised in the next thermal bench window; the model’s predictions in those corners carry higher uncertainty until then.
- Radiation and parasitic convection are ignored; in the sealed rack and at the studied Re, these are expected to be minor, but they will matter for off-flow scenarios (pump spin-down).
- Contact pressure distribution under bolt preload is represented through a single effective conductance; a more detailed contact mechanics analysis could refine local hot spots.
- Roughness of microchannels was set to 10 μm uniformly; the actual as-machined roughness has not been measured on the prototype. A ±10 μm sweep shifts pressure drop by ±1.1 kPa and T_max by ±0.3 C.
- Turbulence model alternatives (e.g., realizable k-ε with enhanced wall treatment) were checked on the medium mesh at nominal; they produced T_max within 0.8 C but higher pressure drop by ~5%. We held SST as the baseline; full re-tuning was not pursued.

## 7. How to Use These Results

- For early pump sizing, use pressure drop = 18.7 kPa at 0.12 kg/s and scale with square of flow rate within 0.08–0.20 kg/s; add 10% margin for manufacturing variability.
- For thermal limits, treat the predicted T_max as mean values; add 2.5 C to cover input variability at 90% confidence, based on the LHS results.
- When using inlet temperatures outside 10–35 C, perform a spot simulation to confirm property fits hold.

## 8. Data Availability

- Geometry, meshes, solver settings, and result fields are in SharePoint/thermal/pcu-cp/v1_6 with SHA-256 checksums documented in manifest.txt.
- The bench test report, raw thermocouple time histories, and DAQ calibration sheets are in LabData/CP-CHT/BenchA/2026Q2.
- STAR-CCM+ macros and Python post-processing scripts are in git at thermal-tools/cp-cht, tag cp-cht-1.6.0.

## 9. Conclusion

Within the exercised envelope and with the stated assumptions, the cold plate CHT model predicts junction temperatures to within ~2 C of measured values and pressure drop within ~5%. Mesh sensitivity is small at the fine level used for results, energy and mass balances are tight, and input data are tied to measured or widely accepted sources. Sensitivity and probabilistic analyses indicate inlet temperature control dominates thermal risk, with mass flow as the primary secondary lever. The model, as configured, is appropriate for design trades on channel geometry and for preliminary pump sizing, with additional test points planned to extend confidence to higher power and broader inlet temperatures.

Appendix A provides supplementary plots and run logs excerpts supporting the above.
