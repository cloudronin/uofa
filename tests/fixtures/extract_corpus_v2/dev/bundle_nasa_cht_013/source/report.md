# CHT Model Credibility Assessment Report
Project: Cold Plate for High-Density Power Electronics  
Model ID: CP-CHT-23A  
Date: 2026-08-06  
Prepared by: Thermal/Fluids Analysis Group, Systems Integration Lab

## Executive Summary
We built and exercised a conjugate heat transfer (CHT) model of a liquid-cooled cold plate intended to manage up to 280 W combined waste heat from a cluster of six electronic packages. The analysis supports early design decisions around coolant flow setting, thermal interface selection, and margin to a junction temperature limit of 85 C.

Evidence gathered includes: a mesh refinement study showing temperature changes below 1 K between medium and fine discretizations; numerical convergence with mass imbalance under 0.1% and energy residuals below 1e-5; comparison to bench measurements at two operating points with mean absolute deviation in key temperature metrics under 2 K; input data pedigree described for material properties and instrumentation; and a parametric uncertainty/sensitivity sweep highlighting the dominant contributors to hot-spot temperature. Model configuration and provenance were tracked through versioned case files.

Within the tested range (coolant 20–35 C, 1.2–1.8 L/min), the model predicts maximum device junction temperatures with a 95% confidence interval width under 4.5 K, with thermal contact resistance dominating variance. For the design nominal condition (25 C inlet, 1.5 L/min, 240 W load), the hottest device junction is predicted at 78.6 C on the fine grid; the corresponding bench measurement indicates 79.5 C ± 0.6 C. The evidence is deemed sufficient for go/no-go decisions on cold-plate geometry freeze and TIM selection for the current design phase. Follow-on activities are listed under Limitations.

## 1. Background and Intended Use
The cold plate is a machined 6061-T6 aluminum manifold with eight parallel channels (2.0 mm by 5.0 mm cross-section) arranged in a serpentine layout beneath four GaN inverter modules (55 W each) and two control FPGAs (10 W each). The application is an airborne power conversion unit; allowable junction temperature for qualification is 85 C under worst-case thermal boundary conditions. The present analysis is intended to:

- Screen candidate flow rates and check thermal margin.
- Rank the leverage of uncertain parameters (e.g., interface resistance).
- Provide a predictive tool to select TIM and torque limits on the device clamps.

The current phase focuses on steady operation at sea-level ambient, incompressible coolant, and a fixed inlet temperature. Transient warm-up and altitude effects are not part of this assessment.

## 2. Computational Setup

### 2.1 Geometry and Domains
- Solid domain: cold-plate body, device copper baseplates, solder stacks, and a 0.5 mm-thick thermal interface layer for each device, captured explicitly.
- Fluid domain: internal flow passages from inlet to outlet, including fillets and manifolds; no bypass paths modeled.
- Radiation neglected; a hand calculation using view factors and shiny aluminum emissivity (~0.1) indicates <0.3 K impact at the temperatures of interest.

CAD source: Creo Parametric Rev B (PLM item CP-112-B). Simplifications: M3 screw threads suppressed; fillet radii under 0.25 mm removed in the solid for mesh practicality.

### 2.2 Physics and Numerics
- Governing equations: steady RANS for the coolant; conjugate conduction in solids; thermal contact represented as a volumetric TIM layer.
- Turbulence: k-omega SST with low-Re corrections, wall treatment targeting y+ < 2 along channels.
- Discretization: second-order schemes for momentum and energy; pressure-velocity coupling via coupled solver with pseudo-transient ramping.
- Material properties:
  - Coolant: 60/40 propylene glycol/water, density and viscosity as a function of temperature using ASHRAE tabulated fits over 20–60 C; constant cp and k approximations validated to change <0.5 K in a sensitivity check.
  - Aluminum 6061-T6: k = 167 W/m-K (measured coupon average), provided by in-house materials lab.
  - Copper baseplates: k = 385 W/m-K (literature).
  - TIM nominal: 3.5 W/m-K; thickness 0.5 mm; later varied per Section 5.

### 2.3 Boundary Conditions
- Inlet: mass flow corresponding to 1.2, 1.5, or 1.8 L/min; temperature fixed at test chiller setpoints (25 C and 35 C).
- Outlet: static pressure reference 0 Pa.
- Heat sources: uniform volumetric heat generation per device footprint grown into the solder stack; total 240 W at nominal, 300 W at overload.
- External surfaces: adiabatic (enclosure walls are assumed to suppress external convection).

### 2.4 Software and Compute
- Solver: Ansys Fluent 2023 R1, double precision, Linux build.
- Meshing: Ansys Meshing with sweep-dominated hexa elements in channels; polyhedral conversion not used.
- Compute resource: 2 nodes, 32 cores total (Intel Xeon Gold 6230), typical wall-clock per steady case: 4.5–6.2 hours at medium grid.

## 3. Numerical Quality: Discretization and Convergence

### 3.1 Mesh Refinement Study
Three systematically refined meshes were generated using uniform edge-length reduction with boundary-layer inflation preserved:

- Coarse: 1.2M cells (fluid), 0.8M (solids), 6 prismatic layers (y+ ~ 2–5).
- Medium: 3.8M (fluid), 2.1M (solids), 10 layers (y+ ~ 0.8–2).
- Fine: 11.5M (fluid), 5.4M (solids), 14 layers (y+ ~ 0.5–1.2).

Refinement factor r ≈ 1.5 across characteristic lengths. The monitored QoIs were:
- T_j,max: highest predicted junction temperature among six devices.
- Δp: pressure drop between inlet and outlet plenums.

At the nominal operating point (1.5 L/min, 25 C inlet, 240 W):
- T_j,max: Coarse 79.8 C; Medium 78.9 C; Fine 78.6 C.
- Δp: Coarse 17.1 kPa; Medium 18.6 kPa; Fine 19.2 kPa.

Using a generalized Richardson extrapolation with apparent order p ≈ 1.9 for temperature and p ≈ 2.1 for pressure, the estimated grid-influence on T_j,max at the medium grid is 0.7 K (1.9%), and for Δp is 0.9 kPa (4.8%). The medium grid was used for design sweeps and uncertainty sampling; the fine grid was used to spot-check two points.

### 3.2 Iterative Convergence and Residuals
- Convergence criteria: energy residuals below 1e-5; momentum and turbulence below 5e-5; mass imbalance <0.1%.
- Monitors: running average of T_j,max stabilized to <0.1 K change over 500 iterations before declaring convergence; outlet temperature stabilized within 0.02 C.
- Under-relaxation: default for energy; momentum adjusted to 0.4 during the initial 1000 iterations to suppress oscillations in manifolds.
- Consistency checks: integral heat balance closed within 0.3% across conjugate interface.

## 4. Cross-Check with Hardware Data

### 4.1 Test Setup
A benchtop loop was assembled with:
- Chiller: Julabo FP50, setpoint control ±0.1 C, verified with a NIST-traceable RTD probe (Fluke 1523).
- Flow measurement: Bronkhorst Coriolis mini CORI-FLOW, accuracy ±0.8% of reading.
- Pressure taps: 1/8” NPT ports at inlet and outlet manifolds; differential measured with Validyne DP45 (±0.5% FS over 35 kPa range).
- Temperature: Five Type T thermocouples (Omega SA1-T) bonded to device case tops; DAQ NI-9213, system-level calibration giving ±0.3 C combined uncertainty.
- TIM installed per vendor instructions (Bergquist Gap Pad TGP 3000, 0.5 mm), clamp torque set to 0.9 N·m using a calibrated torque screwdriver.

Two steady points were tested after 30-minute thermal soak:
- Point A: 1.5 L/min at 25 C inlet, 240 W total.
- Point B: 1.8 L/min at 35 C inlet, 300 W total.

### 4.2 Comparison Metrics
The model outputs were post-processed at the thermocouple footprints (solid surface nodes) and at device junctions (1.0 mm below the case surface) to map to measured case temperatures via an estimated junction-to-case rise (from the internal conduction path within the model). Results:

- Point A:
  - Case temperature average (six devices): Measured 71.8 C ± 0.3 C; Predicted 71.2 C (medium), 71.0 C (fine).
  - Hottest junction: Measured 79.5 C ± 0.6 C (derived); Predicted 78.9 C (medium), 78.6 C (fine).
  - Δp: Measured 18.1 kPa ± 0.2 kPa; Predicted 18.6 kPa (medium), 19.2 kPa (fine).

- Point B:
  - Case temperature average: Measured 82.9 C ± 0.4 C; Predicted 83.8 C (medium).
  - Hottest junction: Measured 90.7 C ± 0.8 C (derived); Predicted 92.1 C (medium).
  - Δp: Measured 23.7 kPa ± 0.3 kPa; Predicted 24.4 kPa (medium).

Mean absolute deviation across the six case sensors: 0.9 C at Point A, 1.6 C at Point B. The larger discrepancy at Point B is associated with the TIM at Device 3, where post-test teardown showed a slight voiding near the clamp edge; the model assumes uniform TIM thickness and properties.

## 5. Input Data Sources and Sensitivity to Uncertainties

### 5.1 Property Sources and Calibration Notes
- Coolant viscosity and density functions were generated from ASHRAE Fundamentals 2017 correlations. The temperature range of interest (20–40 C) stays within the correlation validity.
- Aluminum thermal conductivity measured on two coupons using laser flash (NETZSCH LFA 467); mean 167 W/m-K, standard deviation 3 W/m-K; model uses mean.
- TIM conductivity per vendor datasheet: 3.0–4.0 W/m-K; model nominal 3.5 W/m-K. Thickness tolerance ±0.05 mm per SPC chart from assembly line trial.
- Instrument calibrations for thermocouples and RTD documented under Metrology Log MTL-CP-07, all current within 6 months of test.

### 5.2 Uncertainty Sweep and Rank Ordering
A Latin Hypercube sample of 120 runs on the medium grid was used to propagate plausible ranges:
- Coolant flow rate: 1.2–1.8 L/min (uniform).
- Inlet temperature: 20–35 C (triangular, mode at 25 C).
- Total heat load: 220–300 W (uniform).
- TIM conductivity: 3.0–4.0 W/m-K (uniform).
- TIM effective contact resistance: 0.8–2.4 K·cm^2/W (uniform; equivalent to 8e-5–2.4e-4 m^2-K/W).
- Aluminum k: 164–170 W/m-K (normal).

Outputs recorded: T_j,max, average case temperature, and Δp. A sparse polynomial chaos approximation (LARS) was fitted to the sample to produce variance decomposition. At the nominal setpoint space:

- For T_j,max:
  - TIM effective contact resistance: 54% of variance.
  - Flow rate: 28%.
  - Total heat load: 12%.
  - Remaining contributors (TIM k, inlet T within the tested span, aluminum k): ≤ 6% combined.

- For Δp: Flow rate accounts for >90% of variance; property variations negligible.

Predicted 95% interval widths:
- T_j,max at nominal plan (25 C inlet, target 1.5 L/min, 240 W): 78.6 C ± 2.1 C when accounting for parameter ranges above.
- Δp: 18.6 kPa ± 1.4 kPa.

These results were used to frame design knobs: tightening control on clamp force (thus contact resistance) produces the best payoff in temperature reduction per unit effort.

## 6. Conceptual Adequacy and Assumptions Review
A structured walk-through with the electrical packaging and test teams verified that the phenomena of interest for this phase are represented:

- Internal conduction path from junction to coolant is explicit, including solder and baseplate.
- Flow maldistribution across parallel channels is permitted by the 3D manifold modeling.
- Heat loss to environment is suppressed by the enclosure in the intended installation; test rig matches this with foam insulation, supporting the adiabatic external wall assumption.
- Buoyancy effects are negligible relative to forced convection at the Reynolds numbers encountered (Re ≈ 2200–3200 based on hydraulic diameter and bulk properties), which straddle the transitional regime; using SST with low-Re treatment is appropriate and was benchmarked on an internal straight-channel case to ensure reasonable friction factors.

A quick what-if inspection of a laminar model at the lowest flow setting showed underprediction of Δp and overprediction of wall temperature by >5 C, supporting the chosen turbulence closure even at the low Reynolds bound.

## 7. Model Configuration, Traceability, and Peer Review
- Case and data files are stored under Git LFS in repository TPG/coldplate-cht, with tags v0.9.2 (medium grid parametric) and v1.0.0 (fine grid spot checks). Commit 9e5a1d1 corresponds to Point A fine grid.
- Boundary conditions, solver controls, and mesh metrics are captured in a templated README per case folder. A run manifest (runs.csv) lists random seeds for Latin Hypercube sampling and links to result artifacts.
- Two-person review of setup was held 2026-07-18 (minutes in Q-REV-CHT-05). Reviewer comments led to increasing the number of near-wall layers from 12 to 14 on the fine mesh and rechecking y+.

## 8. Results and Interpretation

### 8.1 Temperature Margins
For the design nominal:
- T_j,max (fine): 78.6 C; (medium): 78.9 C. Margin to 85 C limit: 6.1–6.4 C.
- Considering uncertainty bounds (Section 5), the upper 95% bound is 80.7 C, still ~4.3 C below the limit.

At the overload case (300 W, 35 C inlet, 1.8 L/min):
- T_j,max (medium): 92.1 C, exceeding the limit by ~7.1 C. This is not a qualification point but informs fault tolerance; model indicates the flow boost to 1.8 L/min is insufficient alone under this heat load without lowering inlet temperature.

### 8.2 Flow and Pressure
- Predicted Δp at 1.5 L/min: 18.6–19.2 kPa (medium–fine). The small bias high versus measured (18.1 kPa) is consistent with minor as-built roughness not in the CAD and potential pressure tap placement differences. Even with ±1.4 kPa uncertainty, the pump specification (50 kPa head at 2 L/min) is comfortably met.

### 8.3 Spatial Maps
Temperature maps show the hottest regions under the two center GaN modules where channel proximity is greatest but flow maldistribution creates a slightly warmer plume. The effect is accentuated at the higher inlet temperature. This agrees with IR snapshots taken during testing (qualitative only), which show the same pattern after emissivity compensation.

## 9. Credibility Discussion
The line of evidence assembled—grid convergence with quantified changes, stable numerical solution, direct comparison with two test points, and a structured uncertainty propagation—provides a defendable basis to use the model for the immediate design choices:

- The mesh study demonstrates that the QoIs are not strongly mesh-sensitive in the operating window; the GCI-like figures are under 2% for temperature.
- Solver convergence behavior is well-behaved, and integral balances close.
- Agreement with bench measurements is within instrumentation and modeling tolerances at nominal load; the bias at elevated inlet temperature and overload aligns with physical non-idealities (TIM defects), suggesting the model is neither fortuitously right nor systematically mis-specified.
- Input datasets for properties and boundary conditions are traceable, with measured values for key conductivities and calibrated instruments.

The residual uncertainty is primarily driven by mechanical assembly quality (contact resistance). The sensitivity study provides a practical lever to reduce spread: torque control and TIM selection. For the stated context of use, the prediction accuracy and demonstrated behavior are suitable to inform geometry freeze and pump sizing.

## 10. Limitations and Planned Follow-On
- The model assumes steady operation; no soak/warm-up transients are studied here. A transient check is planned once the controller thermal duty cycle is finalized.
- Radiation and external convection are neglected; while justified for the current enclosure and temperature range, a corner-case analysis for an unenclosed lab unit is not included.
- The turbulence model choice (SST) is standard for internal cooling channels, but transitional effects at the very low end of flow may be imperfectly captured; a verification against a laminar-turbulent transition correlation could be added if the mission profile extends further downward in flow.
- TIM uniformity is assumed. Device-level metrology indicates occasional voiding, as observed on teardown; incorporating a spatially variable contact resistance field could refine hot-spot predictions if needed.
- The uncertainty propagation used a medium grid surrogate. While the grid impact on T_j,max is small, propagating on the fine grid would further reduce numerical contamination of the variance estimate; this is deferred due to compute budget.

## 11. Conclusions
Given the quantitative checks performed and the fit to bench data, we assess that the CHT model is appropriate for:

- Making selections among candidate flow rates within 1.2–1.8 L/min.
- Evaluating expected temperature margin to the 85 C junction limit under nominal boundary conditions.
- Prioritizing interface improvements (clamp torque, TIM spec) based on their influence on hot-spot temperature.

The model should not be used, in its current state, to make pass/fail judgements at overload conditions beyond the specified envelope, nor to predict transient thermal responses. With these caveats, the analysis provides credible guidance for the current design milestone.

---
Prepared by:  
S. Ahmed (thermal analyst), B. Cortez (CFD engineer)  
Reviewed by:  
R. Li (test engineer), P. Nguyen (packaging lead)
