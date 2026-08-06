# Slide 1 — Project snapshot and decision we’re supporting
- Scenario: flow through a 23 mm tissue aortic valve mounted in an ISO 5840-style pulse duplicator (rigid acrylic root, saline–glycerin blood analog).
- Why we’re modeling: screen whether the new leaflet-trim geometry passes the bench acceptance gate for hydrodynamic performance before committing to tooling changes.
- Decision trigger: proceed-to-DV if predicted cycle-averaged pressure gradient at 5.0 L/min stays below 15 mmHg with comfortable margin.
- Stakes: moderate—failure costs ~6–8 weeks and ~$120k in rework; no patient risk at this stage (bench-only claim).

# Slide 2 — What we’re trying to quantify
- Target outputs:
  - Cycle-averaged transvalvular pressure drop (Pd_avg) over 3 consecutive cycles.
  - Peak systolic centerline speed at +10 mm downstream of the leaflet tips (V10_pk).
  - Jet core half-width at +10 mm at peak flow.
- Acceptance bands (engineering targets):
  - Pd_avg < 15 mmHg (preferred < 13 mmHg).
  - V10_pk between 3.5–5.5 m/s (to avoid excessive spray or underexpanded jet).
  - Jet half-width 2–5 mm at V10_pk timepoint.

# Slide 3 — Geometry, fluid, and flow regime notes
- Geometry: laser scan of the assembled valve in the test fixture; leaflets captured in “frozen-open” pose from high-speed video at peak flow; aortic root straight section length = 60 mm downstream.
- Fluid: Newtonian surrogate, μ = 3.5 cP, ρ = 1056 kg/m³ at 22 °C (matching lab fluid).
- Flow regime: peak Reynolds ~ 5500 based on orifice diameter; Womersley ~ 13.8; dominant features are an axisymmetric jet with annular shear layer, intermittent vortex shedding.

# Slide 4 — Numerics overview
- Software: STAR-CCM+ 2023.2, double precision, segregated flow, pressure-based solver.
- Turbulence treatment: unsteady RANS with SST (Menter) + curvature correction; all y+ ~ 1 near walls with 12 prism layers (growth 1.15).
- Spatial discretization: second-order upwind for momentum, bounded central for turbulent viscosity.
- Time advancement: second-order implicit; main runs Δt = 1.0e-4 s (~8500 steps per cardiac cycle).

# Slide 5 — Boundary/initial conditions and how they tie to the rig
- Inlet: velocity waveform derived from the bench flow meter (5 L/min mean at 70 bpm). Applied as a fully developed turbulent profile in the pre-valve pipe.
- Outlet: time-varying static pressure traced from the distal pressure tap in the pulse duplicator to preserve phase and compliance effects seen in the rig.
- Walls: no-slip, rigid; temperature uniform (isothermal).
- Start-up: 2 cycles to wash out transients; data collected on cycles 3–5.

# Slide 6 — Mesh strategy and what changed with refinement
- Grid topology: poly-hexcore with local refinement around the vena contracta and first 30 mm downstream; 12-layer prism near walls, target first cell height 25 μm.
- Three levels:
  - Coarse: 4.1 M cells
  - Baseline: 8.3 M cells
  - Fine: 16.7 M cells
- Observations (Pd_avg at 5 L/min):
  - Coarse → Baseline: -3.4% change
  - Baseline → Fine: -1.1% change
  - Extrapolated asymptote suggests ~2.8% numerical uncertainty on Pd_avg at baseline.
- Jet features: V10_pk changed by 1.9% from Baseline → Fine; jet half-width shifted <0.2 mm.

# Slide 7 — Convergence behavior and temporal resolution
- Residuals: RMS for continuity and momentum below 3e-5 each inner iteration; typical 10–15 inner iterations per time step.
- Monitors: mass flow imbalance < 0.2%; Pd instantaneous traces repeatable to within 0.4 mmHg between cycles 3–5.
- Time-step sensitivity (Baseline mesh):
  - Δt = 2.0e-4 s → Pd_avg increases by 0.5 mmHg vs 1.0e-4 s.
  - Δt = 5.0e-5 s → Pd_avg decreases by 0.2 mmHg vs 1.0e-4 s.
  - Selected Δt = 1.0e-4 s as balance of stability and resolution.

# Slide 8 — Lab campaign used as our reality check
- Bench setup: ISO 5840-compliant pulse duplicator with matched compliance/resistance; 22 °C working fluid.
- Measurements:
  - Pressure: proximal and distal taps across the valve; 1 kHz, ±0.5 mmHg accuracy.
  - Velocity fields: planar PIV on symmetry plane at z = -5, +10, +20 mm; 1.5 kHz; in-plane velocity uncertainty ~0.03 m/s after phase averaging.
- Test points: 4.0, 5.0, and 6.0 L/min at 70 bpm; 30 cycles per point.

# Slide 9 — How the comparisons stacked up
- Pressure drop over the cycle at 5 L/min:
  - RMSE between predicted and measured: 1.7 mmHg; peak timing offset < 6 ms.
  - Cycle-mean difference: model lower by 0.9 mmHg.
- Velocity profiles:
  - At +10 mm, phase-averaged centerline speed within 6.4% of PIV at peak; shear layer thickness overpredicted by ~0.4 mm.
  - At +20 mm, decay of jet centerline velocity matched within 9.1%.
- Outliers:
  - Early systolic acceleration shows slightly flatter top-hat jet than PIV; likely due to frozen-leaflet pose not capturing transient opening.

# Slide 10 — Exploring input variability and its effect on Pd_avg
- Inputs varied:
  - Flow waveform scale ±10% around nominal 5 L/min.
  - Viscosity uniform between 3.0–4.0 cP (to cover day-to-day fluid prep).
  - Effective open area ±5% to emulate deployment tolerance from the fixture.
- Sampling: 60-run Latin hypercube on the Baseline mesh, Δt = 1.0e-4 s, single cycle after spin-up.
- Result for Pd_avg at nominal condition:
  - Mean 11.8 mmHg; 95% interval ±2.3 mmHg across the sampled space.
  - V10_pk varied within ±0.42 m/s across samples at the peak.

# Slide 11 — Where this analysis applies (and where it doesn’t)
- Intended scope: support the bench gate decision only—predicting hydrodynamics for the exact fixture/fluid/waveform family used in the lab.
- Similarity mapping:
  - Reynolds, Womersley, and orifice area ratios in the model cover the tested ranges (4–6 L/min, 65–75 bpm).
  - Downstream geometry in simulation matches the rig length; no aortic arch included.
- Known gaps:
  - Leaflet motion not solved; geometry fixed to the observed open pose at peak—acceptable for Pd_avg but less faithful during acceleration.
  - Rigid-wall assumption tracks the acrylic test section; not intended for in vivo claims.

# Slide 12 — Takeaways and open items before design gate
- Confidence summary:
  - Mesh/time refinement suggests small numerical influence on Pd_avg at Baseline settings.
  - Agreement with lab pressure traces is within a couple mmHg; velocity fields line up well in the core region.
  - Variability study indicates comfortable margin to the 15 mmHg screen at 5 L/min.
- Open items (defer or address next sprint):
  - Acquire additional PIV at +5 mm to better constrain initial jet shear for the frozen-leaflet pose.
  - Repeat 6.0 L/min point with fresh fluid viscosity verification to reduce spread in the upper-flow bound.
  - If DV proceeds, consider a moving-leaflet model for transient jet formation to refine early-systole behavior.
