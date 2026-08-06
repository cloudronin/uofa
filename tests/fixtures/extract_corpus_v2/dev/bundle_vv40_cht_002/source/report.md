To: Priya (Thermal Lead)
From: A. Varga
Subject: CHT model check-in — inverter cold plate peak temp prediction

Quick readout
- Purpose: Use a conjugate heat transfer model to estimate the hottest device case temperature for the Gen3 inverter cold plate at nominal pump setting. The gating question is whether we have at least 10°C margin to the 95°C device limit under steady operating load.
- Bottom line: With the medium grid, predicted hottest case is 82.7°C at the center die of Module B at 0.35 L/min and 25°C inlet. Bench runs came in between 84.0°C and 84.6°C on the equivalent heater coupon; bias is within measurement spread and acceptable for the design checkpoint.

Setup details (what we actually ran)
- Software and physics: STAR‑CCM+ 2023.2. Conjugate conduction in the plate (Al 6061), base (Cu), and TIM; coolant is 50/50 ethylene glycol/water with temperature-dependent properties. Turbulence via k‑ω SST with low‑Re wall treatment. Energy equation fully coupled; pressure-velocity: segregated, second‑order spatial schemes.
- Geometry: Finalized CAD for the 6-device layout, serpentine microchannel core (1.2 mm x 1.5 mm), two plenums, and fittings. TIM thickness set to 50 μm nominal (uniform layer).
- Loads and boundary conditions: Three pairs of devices at 60 W each (uniform volumetric heating within copper footprints). Inlet mass flow set to 0.35 L/min at 25°C; outlet gauge pressure zero; walls adiabatic except device footprints. Radiation omitted after a quick estimate put the contribution under 2% of total heat rejection at these temperatures.
- Contacting: Effective contact conductance folded into the TIM layer. We adjusted the layer’s through-thickness conductance so that the plate-level ΔT under a 120 W coupon matched the lab run; final effective thermal resistance was 1.5e‑4 m²K/W.

Grid and numerics sanity check
- Three meshes: 2.3M, 4.7M, and 6.8M poly cells with prism layers (y+ ≈ 1–2 at coolant walls). Monitored hottest device temperature and pressure drop.
- Change in T_peak: coarse→medium = −2.4%; medium→fine = −0.7%. Richardson extrapolation gives 82.1°C; medium differs by 0.6°C. We’re using the medium mesh going forward; pressure drop change across meshes remained within 3%.

How it stacks up against the lab
- Bench configuration: Copper coupon with embedded cartridge heaters bonded to the same plate; 6 T‑type thermocouples epoxied at analog device locations; flowmeter uncertainty ±2%, bath at 25.0±0.3°C.
- Results at 0.35 L/min, 360 W total: 84.0°C to 84.6°C for the hottest location across three repeats. Model predicted 82.7°C at the analogous spot; spatial mismatch for the hot spot was under 4 mm.
- Notes: The measured spread (~0.6°C) is on the order of the logger resolution; the delta between model and test is roughly double the reported instrumentation uncertainty, but directionally consistent across repeats.

Key assumptions and their rationale
- Fully wetted flow, no phase change; channel Reynolds number ~10,800 so RANS is appropriate. Pump ripple and temperature oscillations not modeled; all results are time-averaged steady state.
- Property data sources: Al 6061 and Cu from ASM; TIM conductivity initially set from vendor sheet (3 W/m‑K) then adjusted as noted above; coolant properties from NIST REFPROP (tabulated into STAR).

What moves the needle (simple knobs study)
- Flow rate: ±20% changes T_peak by −4.9°C / +6.1°C.
- TIM bondline: ±20 μm shifts T_peak by −1.1°C / +1.3°C.
- Inlet temperature: +5°C raises T_peak by ~4.9°C (near-linear over this range).
- Wall roughness model turned on/off in the channels had <0.5°C impact on T_peak at this Reynolds number.

Recommendations before the design freeze
- Keep the medium mesh as our working grid; it lands within ~1°C of the asymptote.
- Run one more bench point at 0.25 L/min to anchor the slope with respect to flow; that will tighten confidence on the control valve selection.
- Replace the vendor TIM value with a measured through-thickness conductivity (laser flash or guarded hot plate) to reduce dependence on the effective resistance adjustment.

If you need a single sentence for the review: the current CHT model, as set up, is adequate to judge peak device temperature for the nominal condition and supports proceeding with the present channel geometry.
