To: A. DeLeon, Thermal Subsystem Lead
From: R. Park, Thermal-Fluid Analyst
Subject: CHT model check-in — avionics cold plate for PDU tray
Date: 06 Aug 2026

Quick readout on where we are with the conjugate heat transfer model for the PDU tray cold plate. The model’s primary purpose is to substantiate pump setpoint and manifold geometry before CDR by showing ≥10 C thermal headroom at worst-case load.

Scope and physics
- Geometry includes the machined aluminum cold plate with 1.2 mm × 2.0 mm channels, PEEK manifold inserts, the copper base slug under the MOSFET bank, and the PCB stack-up (FR-4, copper pours, TIM, device lids). Fluid is 50/50 propylene glycol-water; heat is applied to 16 devices totaling 600 W.
- Flow regime is turbulent (bulk Re ≈ 6200 at 2.0 L/min), so we ran steady RANS with SST turbulence and full solid-fluid coupling. No boiling regime modeled; all surfaces remain >10 C below saturation in our envelope.

Inputs and simplifying choices
- TIM resistance was set to 0.22 K·cm²/W per vendor D5470 data; we bracketed it 0.10–0.40 in a sweep.
- Wall roughness for the channels was initially taken as hydraulically smooth; we later ran a case with 5 µm equivalent sandgrain roughness to gauge pressure losses.
- Coolant properties are temperature-dependent via CoolProp; copper at 385 W/m-K (coupon measurement), 6061-T6 per ASM.

Numerics and consistency checks
- Mesh: polyhedral fluid with prism layers (first cell y+ ≈ 0.8 near walls), and conformal hex-dominant solids. Coarse/medium/fine: 8.1M / 12.4M / 20.7M cells. The hotspot on the copper slug moved by −1.9 C (coarse→medium) and −0.6 C (medium→fine) at 600 W, 2.0 L/min, Tin=28.5 C. We took the 12.4M case forward.
- Residuals to 1e-5 for energy and 1e-4 for momentum; area-averaged inlet/outlet enthalpy rise matched input electrical heat within 0.4% after stabilization. Solid-side conduction balance closed to within 0.7%.

Bench comparison
- We built a single-cold-plate rig with cartridge heaters under a copper spreader, 50/50 PGW at 0.033 kg/s, Tin=28.5±0.2 C. Instrumentation: 8 K-type thermocouples epoxied to the plate underside, one RTD on inlet/outlet, and a FLIR A615 for surface maps; dP via 0–50 kPa differential transducer.
- Results at 600 W: model predicted the max device-lid temperature 2.6 C higher than measured; mean of the 8 TC points was +1.3 C vs test. Spatial pattern (hotter leading devices) matched the IR qualitatively. Predicted pressure drop was 10–12% lower than measured; introducing 5 µm roughness closed half the gap.

Sensitivity highlights
- TIM dominates: 0.10→0.40 K·cm²/W increased the worst-case device lid by ~4.3 C.
- Flow rate: ±10% changed the hotspot by −2.1/+2.4 C, roughly consistent with Nu ∝ Re^0.8 scaling.
- Inlet temperature mapped nearly one-for-one to device lids (0.95–1.00 C per 1 C), confirming we’re mostly convection-limited at the interface, not deep in the solid stack.

Margin picture and uncertainty
- Using the medium mesh and nominal inputs at 2.0 L/min, Tin=28.5 C, we get 81.7 C at the top-of-silicon proxy node (via calibrated conduction path), versus a limit of 95 C. Aggregating measurement noise (±0.8 C TC, ±0.5 C IR), emissivity uncertainty (±0.02 translates to ~±1.5 C on the IR peaks), and model param variation (TIM ±0.12 K·cm²/W, roughness 0–5 µm) with a root-sum-square approach gives ~±3.2 C on the hotspot at 95% confidence. That still leaves >10 C margin in the tested configuration.

Odds and ends
- We did a one-off cross-check with a 1D network (FloTHERM PACK approach replicated in Python): it underpredicts the copper slug drop and therefore gives ~3 C colder lids; we’re not using it for acceptance, only for trend sanity.
- Known gaps: we are not capturing manifold secondary flows perfectly; a quick unsteady RANS run suggested <1 C impact on peaks, so we stayed steady for now. Also, we haven’t modeled contact pressure variation across the TIM; that’s rolled into the resistance range.

Ask
- For CDR, I recommend we carry 2.0 L/min as the baseline setpoint and cite ±3.2 C as the analysis band on the worst device. If program chooses to derate flow to 1.6 L/min, we’ll need to absorb ~+2.5 C on the peaks or tighten the TIM spec.
