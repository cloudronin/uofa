To:        Priya Shah, Pump Upgrade Program
From:      M. Ortega, Fluids Simulation Lead
Date:      2026-08-06
Subject:   CFD credibility status for Stage-2 centrifugal pump redesign (RANS, water, 2900 rpm)

Executive summary
- We built a steady rotating-frame CFD model of the Stage-2 impeller/volute to inform a minor blade-trim decision. Within the intended operating window (0.09–0.13 m³/s at 2900 rpm), predicted head and efficiency align with the rig data to within ~3% and 1.5 points, respectively. Trends off-design are reasonable but deviate up to ~7% at the low-flow end where the flow is more separated.
- On the numerical side, residuals and imbalances are tight, and a three-level mesh study indicates the head coefficient is within ~2–3% of the asymptotic limit at the design flow. We did not model cavitation or perform transient sliding-mesh runs in this phase; results should not be used for NPSH or blade-passing effects.

What decision this supports
- Decision: proceed/not proceed with a 0.8° blade trailing-edge trim while holding volute as-designed.
- Required fidelity: predict head within ±3% and efficiency within ±2 points across 0.10–0.12 m³/s; capture the shift in the H–Q curve slope after trim.
- Consequence of miss: minor redesign delay and test iteration; no safety impact.

Model setup (STAR-CCM+ 2023.2)
- Physics: incompressible, isothermal, single-phase water at 25 °C; steady RANS in a rotating frame (Frozen Rotor). Turbulence closure: SST k–ω, production limiter on, curvature correction off.
- Geometry: CAD of the current impeller and volute (as-manufactured scan used to set tip clearance of 0.35 mm). No inlet pre-swirl devices modeled.
- Boundaries: total pressure at bellmouth inlet set from tank head (100.8 kPa) with 4% turbulence intensity; mass-flow outlet swept to trace the H–Q curve. Smooth wall assumption with equivalent sandgrain roughness of 30 μm (per vendor finish spec).
- Numerics: second-order upwind for momentum, second-order for turbulence scalars; coupled solver, pseudo-time with CFL ramp up to 50. Convergence to 1e-5 on equation residuals, mass imbalance <0.1%, steady monitor on head flat for 1000 iterations before extraction.

Mesh and convergence checks
- Three poly-prism meshes:
  - Coarse: 3.1M cells, y+ ~2 on blade/volute; 12 prism layers, growth 1.25
  - Medium: 8.7M cells, y+ ~1–1.5; 15 layers, growth 1.20
  - Fine: 18.5M cells, y+ ~1; 18 layers, growth 1.18
- At Q=0.12 m³/s, predicted head (m): 28.2 (coarse), 28.6 (med), 28.8 (fine). Richardson extrapolation yields 29.1 m; GCI at medium level ≈ 2.1% (95% confidence). Efficiency GCI at medium ≈ 1.6 percentage points.
- Time independence: switching to transient with a fixed rotor–stator interface over 0.02 s (20 revs) changed mean head by <0.3%; we therefore retained steady for the map sweep.

Comparison with rig data (water loop, 2900 rpm)
- Instrumentation: calibrated pressure taps (±0.2% FS) and magnetic flow meter (±0.5% of reading). Repeatability on head ±0.25 m.
- Selected points:
  - 0.12 m³/s: CFD 28.6 m vs test 29.4 m (−2.7%); η: CFD 78.9% vs test 80.1% (−1.2 pts)
  - 0.10 m³/s: CFD 30.2 m vs test 31.0 m (−2.6%); η: CFD 79.7% vs test 80.8% (−1.1 pts)
  - 0.08 m³/s: CFD 31.1 m vs test 32.7 m (−4.9%); η: CFD 77.2% vs test 79.0% (−1.8 pts)
- The slope of the H–Q curve around the design point matches within measurement bands. At lower flows, the model underpredicts head as separation strengthens in the tongue region.

Input sensitivity explored
- Inlet turbulence intensity 1–10% changed head by <0.6% at design flow.
- Surface roughness 10–60 μm moved head by ~0.4% and efficiency by ~0.6 pts.
- Tip clearance +/−0.2 mm shifted head by ±1.9% and η by ±0.8 pts; this is the dominant geometric uncertainty for this setup.

Known limitations for this phase
- No cavitation model; do not use for NPSH or cavitation onset.
- Interface is steady (Frozen Rotor); blade–passage pressure ripple and tonal content not represented.
- No inlet pre-swirl or upstream piping disturbances; lab loop had a straightener/honeycomb, so this is consistent with the data used here.
- Off-design below 0.09 m³/s shows larger model–test gaps; rely on rig numbers in that corner.

Next steps (if we proceed with trim)
- Add Schnerr–Sauer cavitation and verify y+ ≤ 1 with refined near-tip layers before NPSH margin work.
- Perform a targeted transient sliding-mesh run at 0.10 and 0.12 m³/s to quantify any interface artifacts on mean head.
- Expand the mesh study to include anisotropy: refine volute tongue and tip-leakage paths independently to isolate local discretization errors.
- Acquire two additional data points between 0.09–0.10 m³/s to tighten comparison where separation onsets.

Bottom line
- For the stated decision and flow window, the current CFD is fit for purpose. Recommend green-lighting the 0.8° trim with the above caveats, and scheduling the cavitation and transient tasks ahead of the NPSH review gate.
