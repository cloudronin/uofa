To: Avionics Thermal IPT Lead
From: CHT Modeling Team (Propulsion & Thermal Analysis)
Subject: CHT model credibility snapshot — Docking Computer Cold Plate (Rev C geometry)

Purpose and context
We built a conjugate heat transfer model to size the water–glycol loop and check peak board temperatures for the docking computer cold plate. The specific question was: with 0.5 bar available pump head and a 55/45 glycol mix at 25°C, do on-board electronics remain below 85°C at 900 W total dissipation? The model’s outputs will inform the pogo-valve setting and mounting stackup details for CDR.

Model setup highlights
- Geometry: Native CAD from Rev C (PDM vault 6/28), including channel taps and manifold chamfers. We kept the O-ring grooves but represented the gasket as a thin thermal layer.
- Physics: Steady RANS with SST k-omega for the coolant; conjugate conduction in the Al 6061 plate and four copper heater blocks standing in for boards. Near-wall resolution y+ < 1 on all wetted walls, enhanced wall treatment for heat transfer.
- Materials: Coolant properties from CoolProp at 55/45 by mass, evaluated at local temperature; aluminum and copper temperature-dependent conductivity from ASM. Thermal grease modeled as a 30 μm layer at k = 3.2 W/m-K.
- Boundaries: Inlet mass flow 1.8 L/min; outlet fixed to 0 gauge pressure; inlet turbulence intensity 5%. Each heater block assigned 225 W with uniform volumetric heating to approximate FPGA spreaders.
- Numerics: STAR-CCM+ 2022.1, coupled energy and segregated flow. Converged when energy residuals fell below 1e-5 and mass/energy imbalances were under 0.1%.

Grid and numerics checks
We ran three meshes: 2.3M, 4.7M, and 9.8M poly cells with prism layers (10 layers, total thickness 0.5 mm). Hottest fin-base temperature changed by 0.7°C from medium to fine; coolant pressure drop changed by 1.4%. We adopted the medium mesh for turnaround reasons, carrying 0.7°C as a discretization margin on peak temperature. Doubling the under-relaxation for energy and reducing it for momentum didn’t alter peak temperatures by more than 0.2°C.

Inputs sensitivity
- Flow rate: Varying 1.5 to 2.2 L/min shifts the maximum board-contact temperature by roughly 6.1°C across the range; the slope is near-linear (≈ 10°C per L/min).
- Interface quality: Increasing the contact layer thickness from 20 to 40 μm raises the hot-spot by 1.9°C. This remains the dominant non-hydraulic lever.
- Turbulent heat flux: Adjusting the turbulent Prandtl number from 0.85 to 0.90 moves the hot-spot by 0.8°C.

Comparison with bench data
We compared predictions to the Thermal Rig TR-041 (7/17), which used four copper heater blanks and the flight-like plate, same loop mixture and nominal 1.8 L/min. Twelve thermocouples were bonded to the heater tops and two in the fluid header. The model’s board-contact proxy (underside of heater block) and the measured top-of-heater temperatures track within 3.2°C RMS. The hottest location is 81.4°C predicted vs 83.0°C measured at the slow-flow corner. Predicted loop pressure drop is 23.5 kPa vs a measured 25.1 kPa from differential transducer across the plate.

Assumptions and limitations
- Heat generation is assumed uniform within each heater block; no per-component map was applied. This tends to smear gradients and likely under-predicts local peaks by ~1–2°C.
- We treated the O-ring grooves as adiabatic except where wetted; any minor bypass leakage is neglected.
- Steady operating point only; no ascent transient or pump speed dithering modeled.

What’s still risky
- The model is sensitive to bondline thickness. We have not yet incorporated assembly tolerance statistics; current results reflect nominal stackup.
- The bench used heater blanks, not populated boards; spreading resistance on actual boards may differ.

Verdict against need
Our need is to show margin to an 85°C limit under nominal flow. With the medium mesh and current interface assumptions, the hottest board-contact location is 81.4°C. Accounting for the 0.7°C mesh margin and the 3.2°C RMS model–test gap, we still have approximately 0.9–3.5°C of margin at 1.8 L/min. The pressure drop prediction aligns with measurement within 1.6 kPa, supporting the pump head budget.

Recommendation
Accepted for CDR use in sizing the docking computer cold plate and setting the nominal loop flow, subject to maintaining bondline thickness at or below 30 μm in assembly work instructions. Decision by: Thermal IPT Lead and CHT Modeling Lead, 08/06.

Next actions (not gating this decision)
- Re-run with board-level heat maps once available from the FPGA vendor.
- Repeat the sensitivity sweep including ±10% coolant mix and a 5°C inlet temperature rise to bracket late-summer pad conditions.
