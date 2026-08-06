To:    Flight Avionics Thermal IPT
From:  J. Alvarez, Thermal/Fluids
Date:  2026-08-06
Subj:  CHT model readiness — Avionics Cold Plate Rev B (PAO loop)

Quick take
The current conjugate heat transfer model is fit for preliminary pump sizing and cold-plate geometry freeze for Rev B. Based on comparison with the breadboard test, the model predicts bulk temperatures and pressure loss within ~5%. The main sensitivities are TIM thickness and mass flow. I recommend using this model for PDR closeout decisions, with a follow-on check on radiative exchange before CDR.

What we modeled
- Toolchain: Ansys Fluent 24R1 for flow/energy and steady conjugate conduction; SpaceClaim for CAD cleanup.
- Physics: Single-phase PAO-6 coolant, temperature-dependent properties (per ExxonMobil data), RANS with k-ω SST, low-Re wall treatment (y+ ≈ 0.8–1.2). Solid stack includes 6061-T6 baseplate (k=167 W/m·K), a C110 copper spreader (k=385 W/m·K), and a silicone-based TIM (nominal k=3.0 W/m·K). Radiation neglected for this phase; justification below.
- Loads/BCs: 95 W nonuniform die map across eight components (from board power telemetry, June run). Inlet: 26.0 ± 0.2 C, 0.25 kg/s; outlet static pressure fixed. Surface roughness: 2.5 µm on microchannel walls (supplier spec). Contact resistance between spreader and baseplate set by measured bondline thickness (62 ± 12 µm).

Evidence the numerics are under control
- Mesh refinement: Three unstructured meshes with boundary-layer inflation (3.2M / 6.7M / 12.1M cells). Key outputs changed as follows (coarse → medium → fine):
  - Peak device case temperature: 74.4 → 73.0 → 72.2 C (2.7% then 1.1% change).
  - Cold-plate ∆P: 16.9 → 16.6 → 16.5 kPa (1.8% then 0.6% change).
  The trends are monotonic and variations from medium to fine are below 1.2%. We ran on the fine mesh for validation.
- Iterative behavior: Residuals below 1e-5; net energy balance error 0.3%. Monitors (peak case temp, channel outlet enthalpy) drift <0.2% over the final 500 iterations. Pseudotransient stepping tests did not change outputs beyond 0.1 C.

How it lines up with the bench test
- Hardware: Full-scale breadboard with electric heaters patterned to the same die map; PAO-6 loop with Micropump GJ-N25, Coriolis meter (±0.2% of reading), and 14 K-type TCs (calibrated to ±0.2 C).
- Run matrix: 20, 60, 95, 110 W at 0.20 and 0.25 kg/s, inlet 26 C. We matched the 95 W / 0.25 kg/s point in the model.
- Results at 95 W:
  - Mean baseplate temperature: test 58.9 C vs. model 61.5 C (+4.4%).
  - Hottest device (VR3): test 73.8 C vs. model 72.0 C (−1.8 C). Local underprediction likely tied to thicker-than-nominal TIM near VR3 (witness marks suggest ~90 µm).
  - Loop pressure drop: test 17.3 kPa vs. model 16.6 kPa (−4.0%).
Across the 20–110 W sweep at 0.25 kg/s, errors stayed within ±6% on temperature rise and ±7% on pressure loss.

Input pedigree and checks
- TIM conductivity measured in-house via D5470 fixture: 2.8–3.2 W/m·K over 25–60 C; model used 3.0 W/m·K with linear T slope.
- PAO properties from vendor curves digitized and fit; spot-checked viscosity at 40 C (measured 0.0131 Pa·s vs. fit 0.0130 Pa·s).
- Flow meter and TC calibrations logged week of 2026-07-15; uncertainty propagated to temperature rise is ±0.5 C (2σ).

What matters most (sensitivity snapshots)
- TIM bondline thickness: +30 µm increases VR3 peak by +2.1 C.
- TIM conductivity: −10% reduces spreading, +0.9 C at peak.
- Mass flow: ±5% shifts mean baseplate ~∓0.8 C and ∆P ~±10%.
- Turbulence intensity at inlet (1–5%) made <0.2 C difference on peaks.

Assumptions and where this model applies
- Radiation is neglected; with surfaces near 60 C and an internal bay at ~30 C, estimated radiative heat loss is <1.5 W (gray-body calc, ε=0.1–0.2), which is below our measurement noise. We will recheck if bay air rises above 50 C.
- Validated envelope: 20–110 W, 0.20–0.25 kg/s, inlet 24–28 C. Extrapolation beyond these is not recommended without additional runs.
- Orientation/micro-g effects are irrelevant for single-phase PAO in this geometry.

Peer scrutiny
- Independent check by S. Patel (thermal analyst) on 2026-07-28; comments on near-wall resolution and energy balance addressed. One open RFA: capture measured TIM thickness map in CAD for final CDR run.

Recommendation
Use this model for Rev B pump selection and cold-plate channel geometry lock. Before CDR, incorporate the measured TIM spatial map and perform a quick rerun including a gray-body radiation enclosure at bay temperatures >50 C to bound any late hot-day scenarios. No further hardware testing is required for these updates.
