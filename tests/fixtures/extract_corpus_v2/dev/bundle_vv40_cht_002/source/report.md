To: Priya Rao, Powertrain Cooling Lead
From: Daniel Cho, Thermal Simulation
Subject: CHT status for inverter cold-plate layout (Rev B gate driver side)
Date: 2026-08-06

Quick recap
We built a conjugate heat transfer model for the Rev B inverter subassembly to size the coolant flow and confirm spreader geometry before tool release. The goal is to demonstrate that with 3.0 L/min of 50/50 water–glycol at 35 C inlet, the hottest IGBT baseplate stays under 95 C at 500 W module dissipation (equal split across four dies) with the current fin pattern. The model couples 3D conduction through the aluminum spreader, TIM, and ceramic substrate with turbulent flow in the cold plate. Radiation is neglected, and side walls are adiabatic to represent the enclosure.

Inputs and setup highlights
- Geometry: Detailed CAD of the cold plate and fin array from Rev B (as-built minus fillets <0.5 mm). TIM bond lines set at 70 µm nominal; a 4.3 mm Al 6061 spreader; DBC substrate modeled with 0.3 mm Cu / 0.63 mm AlN / 0.3 mm Cu.
- Materials: 6061-T6 167 W/m·K; Cu 390 W/m·K; AlN 170 W/m·K; TIM 3.0 W/m·K; coolant properties for 50/50 mix at 35 C from CoolProp.
- Thermal loads: 500 W across four footprints, uniform per footprint. Heat-sinked screws represented via localized high-k cylinders to mimic shanks into chassis.
- Flow: Inlet mass flow corresponding to 3.0 L/min, fully developed turbulent profile; outlet static pressure fixed. Turbulence: SST with 5% inlet intensity.

Grid sensitivity and numerics
We ran three unstructured meshes with boundary-layer inflation:
- Coarse: 4.2M cells, y+ 25–80 on fin walls
- Medium: 8.4M cells, y+ 12–40
- Fine: 16.8M cells, y+ 7–22

Peak junction-proxy temperature (at the Cu–ceramic interface above the hottest die) was 98.1 C, 97.2 C, and 97.0 C for coarse, medium, and fine, respectively. Using Richardson extrapolation between medium/fine with an observed order near 1.95 for wall heat flux, the estimated numerical error on the hotspot is ~0.6%. We stayed with the fine mesh for result reporting.

Comparison to benchtop measurements
A flow loop test on the Rev B cold plate with cartridge heaters was run at 3.0 L/min and 35±1 C inlet. Six K-type thermocouples were epoxied to the baseplate underside near die locations; channel-wise pressure drop matched the model within 4%. The model overpredicted the average of the six measured baseplate points by 2.5 C (mean absolute deviation), with a worst location error of 4.1 C at the corner die. Spatial trend (hottest near the outlet corner) matched the test. At reduced flow (1.5 L/min), the model-to-test gap widened to ~7 C at the same corner, but that operating point is not the design case for this decision.

Assumptions and simplifications
- Uniform heat density per die footprint; no detailed bond-wire or metallization features.
- Contact at screw bosses represented via elevated conductivity regions instead of explicit threads.
- No radiative exchange or external natural convection; cold plate outer walls treated as insulated, consistent with clamped installation inside the sealed inverter housing.
- Inlet flow is steady; unsteady effects from pump ripple ignored.

Sensitivity runs
We probed three knobs around nominal:
- TIM conductivity varied ±50%: hotspot moved ±1.8 C; average baseplate ±1.1 C.
- Flow rate varied ±10%: hotspot changed ±2.7 C.
- Inlet temperature +5 C: hotspot +5.0 C (near one-to-one, as expected).
These suggest the design is more responsive to coolant-side changes than to TIM property spread, within the ranges exercised.

What this is good for
- Sizing the pump setpoint and confirming fin height for the current module layout at nominal coolant conditions.
- Ranking cooling tweaks around the die field (fin pitch, spreader thickness) before cutting metal.

Gaps and caveats
- The model does not include enclosure-level heat leakage or any heat soak into adjacent hardware.
- Local micro-features in the die attach stack are homogenized; we will miss second-order peak-shaving from copper patterning.
- Only the 35 C inlet case received a bench check with this geometry; flow/temperature pairings outside that vicinity were not exercised against data in this round.

Recommendation and next steps
- For Rev B release, the hottest die sits at 97.0 C in the model on the fine mesh at 3.0 L/min and 35 C inlet, giving 2 C of margin to the 99 C internal limit if you apply the observed 2.5 C high bias from the bench as a simple offset. The sensitivity indicates an extra 0.3 L/min would buy ~0.8 C additional margin if you want breathing room.
- If we expect inlet temperatures above 40 C during summer dyno, plan on either upping flow to ~3.5 L/min or dropping fin pitch by ~0.2 mm; both were screened informally and have similar effect on the hotspot for a small penalty in pressure drop.

Decision
Accepted for pump setpoint selection and fin/spreader sizing for the Rev B inverter at nominal coolant temperature and 3.0 L/min flow. Not approved for addressing off-nominal scenarios outside those exercised here (e.g., transient soak, enclosure losses, or significantly different coolant mixes). Decision recorded by Priya Rao after review with Thermal and Power Electronics on 2026-08-06.
