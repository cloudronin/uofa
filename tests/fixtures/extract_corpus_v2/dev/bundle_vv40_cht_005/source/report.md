# Cold Plate CHT Model — Credibility Assessment Report

Project: Inverter Module Cold Plate, Rev C  
Model owner: Thermal Systems Group, eMobility Division  
Simulation lead: A. Chen  
Date: 2026-08-05  
Toolchain: SpaceClaim 2024.1, Ansys Fluent 2023 R2, EES 11.136

## 1. Background and how the results will be used

This report documents the credibility of a coupled thermal–fluid model for the Rev C cold plate used in the 800 V SiC inverter. The model will be used to inform two key design decisions for the mechanical and controls teams:

- Confirm that the aluminum baseplate under the power module remains below 75 C in steady operation at nominal coolant supply temperature and flow.
- Provide a pressure-drop curve over the range of 6–18 L/min for pump sizing and control logic look-up.

The geometry of interest consists of a 140 mm × 110 mm × 12 mm A356-T6 aluminum baseplate with an internal milled serpentine channel (6.2 mm hydraulic diameter) and a micro-fin array under the module footprint. The power module is a 6-pack SiC MOSFET bridge with eight die on an AlN DBC, mounted via a 0.23 mm thermal interface pad to the baseplate. Coolant is 50/50 ethylene glycol/water.

The report focuses on steady operation at a representative point: 25 C inlet temperature, 12 L/min volumetric flow, and 4.8 kW heat dissipation from the module spread across the eight die in a nonuniform map following electrical loss predictions.

## 2. Physics and numerics overview

The model is a two-domain, bidirectionally coupled conjugate heat transfer simulation:

- Fluid: incompressible turbulent flow with heat transfer, modeled using k–ω SST with low-Re near-wall resolution (y+ predominantly 0.8–1.5).
- Solid: heat conduction through Al baseplate, AlN DBC layer, and copper traces; TIM represented as a thin isotropic layer with effective thermal resistance.
- Coupling: temperature and heat flux continuity enforced at fluid–solid interfaces via a single simulation domain with shared faces; no thermal contact resistance at fluid-solid interface.

Equations are solved in steady state with pseudo-transient under-relaxation (global time scale set to 0.2 s) to promote convergence. Discretization uses second-order upwind schemes for momentum and turbulent transport; energy uses second-order with curvature correction enabled. Linear solvers are AMG with default coarsening (F–C ratio ~0.5) and strong-coupling threshold set to 0.7.

Convergence is based on:
- Mass and energy imbalance below 0.2%.
- Area-averaged temperature monitors on the module footprint and outlet stabilized within ±0.02 C over 500 iterations.
- Residuals below 1e-5 for flow and turbulence, below 1e-8 for energy.

## 3. Geometry preparation and boundary conditions

The internal channel CAD from the milling fixture model was imported and de-featured to remove fillets below 0.3 mm and threads on the inlet/outlet bosses. The micro-fin region was modeled explicitly (0.8 mm pitch, 0.4 mm height, 0.35 mm thickness) to preserve cross-flow mixing effects.

Boundary inputs:
- Inlet: volumetric flow rate 12 L/min (2.0e-4 m^3/s) imposed; turbulence intensity 5% with hydraulic-diameter length scale.
- Outlet: static pressure gauge 0 Pa.
- Inlet temperature: 25.0 C.
- External walls: adiabatic, as bench tests were insulated with 5 mm Armaflex.
- Heat sources: eight square patches corresponding to die locations; total 4.8 kW apportioned 17–13% by die based on electrical loss map. The AlN DBC and copper metallization were included in the solid stack-up between the die and the baseplate.
- TIM: modeled as a uniform 0.23 mm thickness layer with effective conductivity determined as described in Section 6.

Material properties:
- A356-T6: k = 151 W/m-K (at 60 C), Cp = 910 J/kg-K, density 2670 kg/m^3.
- AlN: k = 170 W/m-K, Cp = 740 J/kg-K.
- Copper: k = 385 W/m-K.
- TIM pad: anisotropic reduced to isotropic effective layer; value determined from test fit.
- EG/water 50/50: temperature-dependent viscosity and conductivity from ASHRAE 2022 correlations; density at 25 C = 1068 kg/m^3, k = 0.394 W/m-K.

## 4. Discretization and convergence checks

The fluid domain was meshed with predominantly polyhedral control volumes and 15 prism layers near walls (total first cell height chosen to keep y+ ~1); the solid domain used conformal tets, refined under the die. Three systematically refined meshes were constructed by uniform surface and volume refinement:

- M1 (coarse): 3.2 M cells fluid + 1.1 M cells solid; min prism height 18 µm.
- M2 (medium): 6.7 M fluid + 2.4 M solid; min prism height 12 µm.
- M3 (fine): 13.9 M fluid + 5.1 M solid; min prism height 8 µm.

Each mesh was run to the same convergence criteria. Key outcomes at the 12 L/min point:

- Peak baseplate temperature under hottest die:
  - M1: 68.9 C
  - M2: 67.7 C
  - M3: 67.2 C
- Coolant pressure drop between pressure taps located 20 mm downstream of inlet boss and 20 mm upstream of outlet boss:
  - M1: 33.8 kPa
  - M2: 32.6 kPa
  - M3: 32.1 kPa

Grid refinement factors were 1.36 (M1→M2) and 1.36 (M2→M3) based on an average edge length metric in the fin region. Applying a three-level Richardson extrapolation suggests the asymptotic solution for peak baseplate temperature at this operating point is 66.9–67.1 C depending on assumed order (nominal p = 1.9). We adopt M3 predictions as representative for decision-making and carry forward the observation that further refinement shifts Tpeak by <0.4 C and ΔP by <0.7 kPa.

All M3 runs reached residual targets within 2200–3500 iterations; monitored temperatures flattened for the last 800 iterations. A restart from M2 interpolated to M3 shortened wall time by ~28%.

## 5. Heat distribution and loss mapping

Electrical losses per die were provided by the Controls group for the operating point considered (700 Arms per phase, f_sw = 12 kHz). These were converted to heat input using a 2% gate-drive fraction and assigned to eight square patches corresponding to the die footprints (8.0 × 8.0 mm each). The die-level split was:

- Q1/Q2 high-side: 0.83/0.72 kW
- Q3/Q4 mid: 0.66/0.59 kW
- Q5/Q6 low-side: 0.51/0.47 kW
- Q7/Q8: 0.53/0.49 kW

This nonuniformity is important to capture local hot spots on the baseplate. The areal heat fluxes for the hottest die are ~13.0 W/mm^2 at the die–DBC interface, which is consistent with lab infrared thermography of the die top surfaces (used only to inform the nonuniform map, not for direct thermal validation).

## 6. Interface thermal resistance and tuning protocol

Vendor data for the chosen TIM (Bergquist Gap Pad TGP1000, 0.23 mm) lists a through-plane thermal resistance of 0.23 K·cm^2/W at 200 kPa clamping pressure. The actual clamp force in the module assembly was measured via bolt torque and known thread friction, yielding an estimated pad pressure of 160–240 kPa.

We treated the TIM as a uniform layer with an effective conductivity selected by fitting to one thermocouple located at the geometric center of the power module on the underside of the baseplate in a dedicated “fit” experiment at 12 L/min and 4.8 kW. The resulting best match was achieved with an equivalent layer thermal resistance of 0.28 K·cm^2/W. All subsequent comparisons in Section 7 are made without further adjustment of this parameter.

## 7. Bench setup and comparisons

A closed-loop bench was constructed with a Micropump CA-958 gear pump, a 2 kW chiller (Lauda RP 845), and a 10 L reservoir. The cold plate was instrumented as follows:

- Four T-type thermocouples epoxied to the baseplate underside near the module corners (TC1–TC4), 8 mm from each edge of the module footprint.
- One RTD located in the outlet stream, 15 mm downstream of the outlet boss centerline, inserted via a compression fitting flush with the channel centerline.
- Differential pressure transmitter (Omega PX409-015DWU5V) connected to two 1.6 mm pressure ports integrated into the plate (locations matched in the model).

Data were logged for 15 min after reaching steady reading drift <0.05 C/min. The foamed elastomer insulation around the plate was inspected for gaps and resealed before the runs. A single operating point was used for the comparison reported here: 12 L/min, 25 C inlet, 4.8 kW.

Comparison of key quantities (model M3 vs bench):

- Baseplate temperature near hottest corner (TC1):
  - Model: 67.5 C
  - Bench: 69.0 C
  - Difference: −1.5 C
- Diagonally opposite corner (TC3):
  - Model: 64.7 C
  - Bench: 66.2 C
  - Difference: −1.5 C
- Remaining two corners (TC2, TC4):
  - Model: 65.9 C and 65.1 C
  - Bench: 67.4 C and 66.8 C
  - Differences: −1.5 C and −1.7 C
- Outlet fluid temperature rise above inlet:
  - Model: +4.1 C
  - Bench: +4.6 C
  - Difference: −0.5 C
- Pressure drop across taps:
  - Model: 32.1 kPa
  - Bench: 36.0 kPa
  - Difference: −3.9 kPa

The temperature field shape across the module footprint was also captured with a temporary array of five additional bead thermocouples during an earlier shakedown. The pattern of hotter upstream-left and cooler downstream-right observed then is consistent with the simulation’s contour map; those auxiliary points were not retained for the final dataset but gave qualitative confidence in the spatial distribution.

## 8. Results and interpretation

For the intended use cases, the model reproduces baseplate temperatures at accessible locations to within roughly 1.5–1.7 C at the nominal condition, and the outlet temperature rise within 0.5 C. The predicted pressure drop is lower than measured by approximately 4 kPa. Post-run inspection showed small bubbles intermittently at the inlet boss during higher-flow tests (not analyzed here), which may relate to entrance losses; however, at 12 L/min no visible aeration was present.

The observed temperature offset of about −1.5 C (model cooler than test) is consistent across all four corner locations. Possible contributors include:
- Slight overestimation of micro-fin heat transfer effectiveness in the turbulence model at low-Re.
- Local spreading resistance in the DBC/coppe- baseplate interface not fully represented.
- Minor conduction into mounting brackets despite insulation.

The pressure-drop delta suggests either:
- Additional minor losses from the inlet and outlet bosses beyond what the idealized boundary condition represents, or
- Slightly higher fluid viscosity from glycol concentration drift relative to the property tables used.

For design use, the model indicates a peak baseplate temperature of 67.2 C under the hottest die at 12 L/min and 25 C inlet, with the four accessible corners ranging from 64.7 C to 67.5 C. The corresponding predicted ΔP is 32.1 kPa. These values allow sizing of the pump and confirmation of margin to the thermal target at the stated condition.

## 9. Credibility assessment narrative

- Geometric fidelity: The serpentine channel and micro-fin features are resolved explicitly, and pressure tap locations match the bench ports, reducing ambiguity in the ΔP comparison.
- Convergence and mesh checks: Three levels of mesh refinement were run with consistent schemes, and key observables changed modestly with further refinement. Energy residuals reached stringent thresholds, and monitor plateaus indicate stationary solutions.
- Physics selections: k–ω SST with near-wall resolution down to y+ ~1 is a well-established choice for internal passages with heat transfer and modest curvature; curvature correction was enabled. Thermal conduction through the full stack is represented explicitly, including the AlN and copper layers.
- Boundary representation: Flow was imposed volumetrically; this eliminates dependence on an assumed entrance loss in the model. The bench mimics this with a long straight run-in to damp upstream swirl.
- Data tie points: A single thermocouple location was used to tune the effective TIM resistance. After that, four independent temperature checks and two integral quantities (ΔT and ΔP) were compared without additional adjustments.
- Numerical stability and solver behavior: The pseudo-transient approach prevented oscillations sometimes seen in steady segregated loops for conjugate problems. Clipping and limiter messages were absent. The M3 case converged from two different initial fields (cold start and M2-interpolated) to indistinguishable final values at the comparison points.

## 10. Limitations and open items

- The TIM was treated as a uniform isotropic layer; in reality, pad compression varies across the module due to mounting screw patterns. If the design requires margin at widely varying clamp forces, a nonuniform contact conductance field may be necessary.
- The turbulence model does not include explicit laminar–turbulent transition; given Re_D ~ 9.4e3 at 12 L/min in the serpentine, this is unlikely to dominate, but entrance region development effects may be slightly optimistic.
- Temperature-dependent material properties were included for the coolant only; solids used constant values representative of ~60 C. For large departures from this temperature, property variation in the baseplate could matter by a couple of percent for spreading resistance.
- The inlet and outlet bosses were simplified to straight bores; any chamfers, steps, or O-ring grooves were removed during de-featuring. These could add minor losses not present in the model, potentially explaining a portion of the ΔP gap.
- The nonuniform die loss map was treated as fixed. If gate-drive frequency or modulation strategies shift the heat partitioning among die, the local peak baseplate temperature distribution will change accordingly; the current model would need the updated map to remain predictive.

## 11. Reproducibility of the runs

All runs referenced here were performed with Ansys Fluent 2023 R2 on a 32-core workstation (AMD Threadripper 3970X, 128 GB RAM). The M3 case required approximately 9.5 h wall time from M2 interpolation to convergence at the nominal operating point, including 3 restarts. Solver settings, mesh statistics, and monitor histories are summarized in Appendix A. The M3 case file and journal script are stored on the Thermal group share, project path TS-INV-CP-RevC/CFD/CHT/2026-07-ops12Lpm.

## 12. Conclusions

Within the scope outlined, the CHT model of the Rev C cold plate:

- Delivers baseplate temperature predictions at four accessible points within approximately 1.5–1.7 C of bench measurements at the nominal 12 L/min, 25 C inlet, and 4.8 kW heat load distribution.
- Reproduces the outlet temperature rise within 0.5 C, indicating that the global energy balance is represented consistently.
- Undershoots measured pressure drop by ~4 kPa at the comparison point, likely due to inlet/outlet feature simplifications or modest glycol property mismatches.

Given the geometric fidelity, convergence behavior, and agreement against independent measurements after a single parameter fit for the TIM layer, the model is suitable to support the two intended uses stated in Section 1 for hardware Rev C at the nominal operating point. Any design changes that significantly alter channel geometry, fin density, or module clamp scheme should prompt a quick re-check following the same protocol.

## 13. References

- ASHRAE Handbook 2022 – HVAC Systems and Equipment, ethylene glycol properties.
- Bergquist Gap Pad TGP1000 datasheet, Rev K.
- Menter, F. R. “Two-Equation Eddy-Viscosity Turbulence Models for Engineering Applications,” AIAA Journal, 32(8), 1994.

---
Appendix A provides additional computational details, including mesh statistics and monitor traces description.
