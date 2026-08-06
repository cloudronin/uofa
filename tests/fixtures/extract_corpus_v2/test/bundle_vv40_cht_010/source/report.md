# Conjugate Thermal-Fluid Credibility Assessment Report
Project: SiC Inverter Power Module Cold Plate (CHT Analysis)
Date: 2026-08-06
Analyst: E. Romero, Thermal-Fluid Engineering Group

## 1. Background

We assessed whether the current cold-plate design for the 800 V SiC inverter power module maintains the baseplate and surrounding structure within thermal limits under representative steady operation. The analysis couples internal coolant flow with heat conduction through the cold plate and module base materials.

Intended use of the model:
- Support design freeze at Gate D by demonstrating margin to a baseplate temperature limit of 85 C at the worst-case steady electrical load per module.
- Guide fin pitch and channel height choices and size the TIM (thermal interface material) stack to balance temperature uniformity against pressure drop.
- Quantify sensitivity of peak temperature to key uncertainties (contact resistance, coolant flow rate, fluid properties).

Operating envelope considered here:
- Module thermal load: 1.5 to 3.0 kW total per module; primary case at 2.5 kW.
- Coolant: 50/50 ethylene glycol–water by volume; nominal inlet 35 C.
- Nominal mass flow rate: 0.033 kg/s per module (2.0 L/min, density at 35 C ≈ 1045 kg/m³).
- Target limit: baseplate peak < 85 C at 2.5 kW and 0.033 kg/s.

The cold plate is an aluminum (AA6061-T6) body with a milled serpentine channel and brazed cover, fed by AN-6 barbed fittings. The module base is copper (C110) with an intermediate TIM (Bergquist Gap Pad HC 1.0). Fasteners preload the stack to a nominal 3.5 MPa.

This report documents how the team built, exercised, and checked a conjugate heat transfer (CHT) model in Ansys Fluent 2024 R1, cross-checked predictions against bench measurements for a prototype unit, and analyzed sensitivities to key uncertain inputs. Work from March–June 2026 is included.

What is not covered in this report:
- We did not run transient warmup or cooldown sequences; those are tracked for the next build.
- We did not explore boiling onset or two-phase regimes; these are out of scope given our temperature margins and chosen coolant.
- We did not execute a manufacturing-variability study on internal roughness or channel geometry; machining drawings were followed, and a representative roughness was assumed as discussed below.

## 2. Methodology

### 2.1 Geometry, Physics, and Boundary Conditions

We imported the as-built CAD of the cold plate (Rev C) into SpaceClaim and performed defeaturing of small (<0.25 mm) fillets in the channel corners to stabilize meshing. The analysis domain includes:
- Coolant volume from 30 mm upstream of the inlet barb to 30 mm downstream of the outlet barb.
- Aluminum cold-plate body and brazed cover.
- Copper module base with 6 die footprints as rectangular heat input zones.
- A uniform, homogenized TIM layer between the module base and plate (modeled as a thin solid zone with effective thermal conductivity).

Boundary conditions:
- Inlet: mass flow 0.033 kg/s, coolant temperature 35.0 C, turbulence intensity 5%, turbulent viscosity ratio 10, using measured hydraulic diameter at the barb throat (7.8 mm).
- Outlet: static pressure 0 Pa gauge.
- External walls: adiabatic, with the exception of radiative loss from the external cold-plate surfaces to ambient at 35 C with emissivity 0.2; radiation handled via surface-to-ambient linearized coefficient (calibrated to yield <2% of total heat rejected; see Assumptions).
- Heat input: six rectangular patches on the copper baseplate, total 2.5 kW distributed according to die map (0.5 kW per die), constant heat flux per patch.
- Contact/TIM: represented as a 75 µm-thick solid layer (see Properties).

Turbulence model and near-wall treatment:
- RANS with k–omega SST.
- Low-Re formulation with y+ in the range 0.8–2.5 on channel walls and fins (verified by postprocessing).
- Automatic near-wall modeling disabled; fully resolved viscous sublayer via 15-layer prism inflation.

Thermophysical properties:
- Coolant properties from CoolProp 6.6 for 50/50 EGW at 1 atm; temperature-dependent density, viscosity, Cp, and conductivity enabled (polynomial fits over 20–90 C).
- AA6061-T6: k = 167 W/m-K.
- C110 copper: k = 388 W/m-K.
- TIM (Gap Pad HC 1.0): bulk conductivity 1.0 W/m-K; see Sensitivity for thickness and k range.

Solver setup:
- Steady-state solution with pseudo-transient stabilization.
- Pressure–velocity coupling: SIMPLEC.
- Spatial discretization: second-order upwind for energy, momentum, and turbulence; pressure uses second-order scheme.
- Double-precision; segregated solver.

Convergence and monitors:
- Residual targets: 1e-5 for continuity, momentum, and k/omega; 1e-8 for energy.
- Monitors: total heat entering coolant, total heat released by sources, area-averaged outlet temperature, and peak baseplate temperature at TC locations.

### 2.2 Meshing and Mesh Quality

The mesh was generated with Ansys Fluent Mesher:
- Core: poly-hexcore with minimum cell size 0.25 mm in the channels and 0.5 mm in solids.
- Boundary layer: 15 prism layers, growth factor 1.2, first cell height 20 µm, ensuring y+ ≈ 1 at nominal flow.
- Refinement regions around fin leading/trailing edges, turns in the serpentine, and die footprints.

Three systematically refined grids were created:
- Coarse: 3.1 million cells (fluid 1.9M, solids 1.2M).
- Medium: 6.4 million cells (fluid 3.8M, solids 2.6M).
- Fine: 12.8 million cells (fluid 7.6M, solids 5.2M).

Mesh quality:
- Skewness P95 < 0.22; maximum 0.31.
- Orthogonal quality P05 > 0.76.
- Non-orthogonality average 13.5 degrees.

### 2.3 Checks Against Known Solutions

To ensure the numerics and settings produce reasonable heat-transfer behavior before running the full assembly, we exercised two canonical cases:

- Laminar thermal entry region with conjugate conduction: straight channel, Re ≈ 700, uniform wall heat flux with 3 mm aluminum wall thickness. Computed Nusselt numbers along x/D compared to Kays & Crawford correlations with wall conduction coupling. Deviations were within 1.4% in the asymptotic region and 2.8% in the entrance region. This established the correctness of boundary-layer resolution and energy equation coupling.

- Pure conduction cube with internal heat source: 50 mm cube with uniform volumetric heating, Dirichlet 25 C on one face, adiabatic elsewhere. Analytical centerline temperature agreed within 0.7% for the medium and fine grids.

Settings for the production models mirrored those used in the above checks except for turbulence activation in the cold-plate flows.

### 2.4 Bench Experiments for Cross-Check

We built one prototype cold plate to drawing CP-402-REV-C and mounted a copper heater block matching the module base footprint. Nine 36-gauge K-type thermocouples (Omega SA1-K-120) were bonded to the copper surface at predrilled witness marks near the die positions; calibration against a Fluke 7341 bath yielded an uncertainty of ±0.5 C (k=2). Inlet and outlet temperatures were measured with 4-wire RTDs (Class A, ±0.15 C). Flow rate was controlled with a Cole-Parmer gear pump and measured with a Bronkhorst mini CORI-FLOW (±0.5% of reading). Pressure drop was measured with a Validyne DP15 (±0.25% FS). Ambient was 24–26 C in the test lab with minimal air movement.

Test points:
- TP1: 2.5 kW, 0.033 kg/s, inlet 35 ± 0.1 C.
- TP2: 1.5 kW, 0.020 kg/s, inlet 35 ± 0.1 C.
- TP3: 3.0 kW, 0.050 kg/s, inlet 35 ± 0.1 C.

Emissivity for IR spot-checks was set to 0.22 on blacked copper stickers adjacent to thermocouple pads.

### 2.5 Sensitivity and Uncertainty Approach

We identified the following quantities as the dominant contributors to uncertainty in predicted baseplate temperatures:
- TIM thickness: compressible pad with thickness between 50–100 µm depending on local preload; nominal 75 µm.
- TIM conductivity: datasheet nominal 1.0 W/m-K at 25 C; effective conductivity under compression in the range 0.8–1.2 W/m-K.
- Flow rate: ±1.5% setpoint error plus 0.5% reading error from the Coriolis meter.
- Coolant property variations with mixture ratio: ±2 vol% EG variation permissible in maintenance; accounted by property perturbation.
- Surface roughness in the channel: equivalent sandgrain roughness between 5–20 µm due to milling marks and brazing.

Two analysis modalities were performed:
- One-at-a-time perturbations around the nominal model to develop local sensitivities.
- A Latin hypercube sample (50 runs on the medium grid) within the above ranges to estimate output spread (peak baseplate temperature and pressure drop) for the primary condition (2.5 kW, 0.033 kg/s, 35 C inlet).

## 3. Results

### 3.1 Numerical Convergence and Mesh Effects

For each mesh, residual targets were met, and global energy balance closed to within 0.17% (fine), 0.21% (medium), and 0.29% (coarse). Mass flow imbalance across the interfaces was <0.05% on all grids.

Peak baseplate temperatures at the thermocouple pad locations (interpolated to sensor spots) for the nominal operating point:

- Coarse: 79.6 C (max), 76.9 C (average of 9 pads).
- Medium: 78.9 C (max), 76.3 C (average).
- Fine: 78.5 C (max), 76.1 C (average).

Observed order of accuracy estimated from the three-grid sequence yielded p ≈ 1.85 for temperature, consistent with second-order discretization and mixed grid topology. Extrapolated asymptotic peak temperature is 78.2 C. Using 3% safety factor, the grid convergence index (Richardson extrapolation based with Fs = 1.25) for the medium grid is 1.2% on the peak temperature. Based on this, the medium grid was used for parametric and validation work.

Pressure drop converged similarly:
- Coarse: 18.7 kPa.
- Medium: 18.1 kPa.
- Fine: 17.9 kPa.

### 3.2 Comparison to Bench Measurements

At TP1 (2.5 kW, 0.033 kg/s):
- Predicted outlet temperature rise: 19.8 C; measured 20.2 ± 0.3 C.
- Predicted peak baseplate TC spot: 78.5 C; measured 79.8 ± 0.5 C.
- Spatial variation across the 9 TCs (max-min): predicted 3.6 C; measured 4.1 C.
- Predicted pressure drop (inlet barb throat to outlet barb throat): 18.1 kPa; measured 19.4 ± 0.2 kPa.

At TP2 (1.5 kW, 0.020 kg/s):
- Predicted peak: 73.2 C; measured 74.1 ± 0.5 C.
- Predicted drop: 9.7 kPa; measured 10.5 ± 0.2 kPa.

At TP3 (3.0 kW, 0.050 kg/s):
- Predicted peak: 79.9 C; measured 81.0 ± 0.5 C.
- Predicted drop: 29.3 kPa; measured 31.1 ± 0.3 kPa.

Discrepancies are within 1.5–1.8 C for baseplate temperatures and 1.8–2.0 kPa for pressure drop. The cooler prediction for pressure drop likely reflects our assumed roughness being slightly lower than as-built; a sensitivity to roughness (see below) indicates that a 10 µm increase in equivalent sandgrain roughness increases pressure drop by ~1.1 kPa for this geometry.

Qualitatively, the model reproduces the hotspot pattern: higher temperatures near downstream fins and at the die nearest to the last bend. IR spot-checks showed matching contours after emissivity adjustment.

### 3.3 Sensitivities and Spread

Local sensitivities around the nominal TP1 condition (medium grid):
- TIM thickness: +3.2 C per +0.10 mm increase (linear to first order for 50–100 µm).
- TIM conductivity: −0.9 C per +0.2 W/m-K increase.
- Flow rate: −0.45 C per +0.005 kg/s increase near 0.033 kg/s.
- EG content: +0.3 C for +2 vol% EG at fixed mass flow due to higher viscosity and lower Cp.
- Channel roughness: negligible effect on baseplate temperature (<0.2 C across 5–20 µm) but strong on pressure drop (+1.1 kPa per +10 µm roughness increment).

LHS (50 samples) ranges:
- Inputs sampled: TIM thickness U[0.05, 0.10] mm; TIM k U[0.8, 1.2] W/m-K; flow rate N(0.033, 0.0006) kg/s (truncated); EG vol% U[48, 52]; roughness U[5e-6, 2e-5] m.
- Outputs: peak baseplate temperature mean 78.7 C; standard deviation 0.8 C; 95% interval [77.2, 80.3] C.
- Pressure drop mean 18.3 kPa; 95% interval [16.9, 19.9] kPa.

The temperature spread is dominated by TIM thickness variability (≈68% of variance by Sobol’ main effect estimate from a separate screening run with 200 Sobol’ points). Flow rate contributes ≈22%; other factors minor.

### 3.4 Design Margin and Acceptance

For the primary decision point—confirming the baseplate remains under 85 C at 2.5 kW with nominal cooling—the evidence indicates:
- Nominal prediction: 78.5 C peak.
- Accounting for mesh uncertainty (~1.2%), measurement uncertainty (±0.5 C), and input variability (95% up to 80.3 C), we retain ≈4.7 C of margin to the 85 C limit at the upper end of the plausible range.

Even at 3.0 kW with elevated flow (0.050 kg/s), the measured peak remained below 82 C, suggesting additional headroom exists. The caveat remains that the module die heat map may be more peaked than our uniform-per-die assumption, addressed in Limitations.

## 4. Credibility Discussion

This section synthesizes the above into a view of how much decision-makers can rely on the analysis for the stated purpose.

- Physics and model form: The chosen turbulence model (k–omega SST) with low-Re wall treatment is consistent with the Reynolds number regime in the channels (Re ≈ 2500–4200 across the envelope). The solid/fluid coupling is standard for conjugate problems, and property temperature-dependence is included. The model does not consider micro-scale roughness-induced augmentation of heat transfer; given the small influence of roughness on temperature found in the sensitivities and the agreement with test data, this is acceptable for steady-state.

- Numerical soundness: The mesh independence study and near-wall y+ control provide evidence that resolution is adequate for both hydraulics and thermal boundary layers. Energy balance closes tightly, and the pressure and energy equations converge with conservative targets.

- Comparisons with reality: The lab setup reproduces the intended thermal loading and flow path with measured uncertainty bounds. Across three operating points, temperatures and pressure drops align within about 2 C and 2 kPa, respectively. The model consistently predicts slightly lower pressure drop, consistent with conservative roughness assumptions. Temperature biases are small and do not trend with flow, indicating that the model form is not missing a dominant process in the validated range.

- Input quality and assumptions: The dominant uncertain input is TIM thickness, which is not monitored in-situ in the product. We bracketed this input and showed that reasonable assembly tolerances keep the baseplate temperature variation within about ±1 C around nominal. The coolant composition variation also matters, but is within maintenance control and monitored by the plant.

- Sensitivity and robustness: The design’s thermal margins are not excessively sensitive to the hydraulic side; a 15% flow shortfall (e.g., pump degradation) raises peak temperature by about 1.3 C. This supports robustness in service.

- Applicability window: Evidence is strong for steady-state operation in the range tested (1.5–3.0 kW, 0.02–0.05 kg/s, 35 C inlet). We have not demonstrated transient behavior (rapid load steps) or performance at significantly different inlet temperatures. The model likely remains valid across 25–45 C inlet temperatures given property modeling, but we have not cross-checked that explicitly.

- Reproducibility: Simulations were re-run from scratch on the medium grid with different initial fields and reproduced peak temperatures within 0.1 C and pressure drop within 0.2 kPa. The bench test TP1 was repeated on a different day with reassembled TIM stack; measured peaks differed by 0.7 C, consistent with TIM variability.

In short, for the Gate D decision to lock the cold-plate geometry, we judge the analysis to provide reliable, quantitative predictions of baseplate temperature and pressure drop for steady conditions, with uncertainties quantified and shown not to eat into the acceptance margins.

## 5. Limitations and Open Items

- Transients and thermal capacitance: We did not analyze or test step-load transients or pump trips. The module’s thermal mass, baseplate, and coolant are expected to buffer short-duration events, but this remains to be demonstrated. Action: perform a 60–0% power step test with 1 Hz logging and compare to a transient CHT run.

- Die-level heat distribution: We modeled 0.5 kW per die with uniform flux. In reality, gate-drive timing and switching losses may create gradients within a die and among dies. The comparison to the heater block test (which reproduces the die map but not die internals) cannot uncover sub-die hotspots. Action: coordinate with the device team to supply a per-die heat map with higher fidelity or impose a conservative peak factor.

- Roughness and brazed seam details: The channel surfaces include a brazed joint with local protrusions not captured in the CAD. We approximated with equivalent roughness; pressure drop results suggest the real part has higher effective roughness. Action: measure surface profiles and update roughness; consider a localized loss coefficient at bends if warranted.

- Radiation: We lumped radiation into a small linearized loss term and showed its contribution is <2%. If external surfaces are painted black during integration, radiative losses will slightly increase, lowering baseplate temperature by about 0.3–0.6 C. No action required for worst-case analysis.

- Coolant degradation: Long-term glycol degradation changes properties. This was not modeled; maintenance intervals and property checks should maintain performance within our assumptions.

- Manufacturing tolerance study: We did not perform a statistical analysis of channel width/height tolerances and their effect on pressure drop and heat transfer. This is an opportunity area if the supplier’s process capability is marginal.

- Scope and schedule constraints: Only one prototype was available during the analysis window, limiting the breadth of validation. Additional units may show slightly different behavior due to assembly variability.

## 6. Detailed Notes

### 6.1 Near-Wall Resolution

Wall y+ histograms for TP1 (medium grid) show:
- Channel floors and ceilings: median y+ 1.1, P95 1.9.
- Fin sides: median y+ 0.9, P95 1.6.
This supports the use of the low-Reynolds k–omega approach without resorting to wall functions.

### 6.2 Monitors and Stability

- The peak temperature monitor asymptoted monotonically over 1500–2500 iterations depending on mesh, with the last decade of residual drop producing <0.05 C change.
- Pseudo-transient Courant number was ramped from 1 to 20 to assist pressure–velocity coupling near the outlet plenum.

### 6.3 Property Implementation

CoolProp calls were used to generate property tables at 5 C increments for 25–95 C, then curve-fitted. Validation case TP3 (higher flow) exercises viscosity in the lower range; the agreement on pressure drop provides indirect confirmation of viscosity fidelity.

## 7. Conclusions

- The CHT model of the Rev C cold plate, using Fluent 2024 R1 with k–omega SST and y+ ≈ 1 resolution, predicts steady-state baseplate temperatures and pressure drop within ≈2 C and 2 kPa of bench measurements across three operating points, including the worst-case design point.

- Grid sensitivity is under control; the medium grid (6.4M cells) yields a peak temperature GCI of ≈1.2% relative to the asymptotic estimate.

- The dominant uncertain input is the effective TIM thickness; even at the unfavorable end of the plausible range (0.10 mm, k=0.8 W/m-K), the peak baseplate temperature at the nominal operating point remains below 82 C.

- The analysis supports proceeding to Gate D with the existing channel geometry and fin spacing. For productionization, small adjustments to surface finish targets may be warranted to reduce pressure drop scatter.

- Follow-on work should address transient behavior and refine the die heat map to ensure adequacy under dynamic loading and to verify no localized sub-die hotspots emerge.

## 8. References

- Incropera, F. et al., Fundamentals of Heat and Mass Transfer, 7th ed.
- Kays, W. M., Crawford, M. E., and Weigand, B., Convective Heat and Mass Transfer, 4th ed.
- Menter, F. R., Two-Equation Eddy-Viscosity Turbulence Models for Engineering Applications, AIAA Journal, 1994.
- CoolProp 6.6 Documentation.

## 9. Appendices (selected data excerpts)

- TC pad coordinates (relative to module datum): available upon request.
- CAD change log from Rev B to Rev C: added 0.25 mm fillets at the last turn, increased channel depth by 0.3 mm, changed barb angle from 30 to 25 degrees.
- Solver run IDs and wall-clock times: medium grid cases solved in 9.5–11.8 hours on a 24-core workstation (Xeon Gold 6248R), 64 GB RAM.

End of report.
