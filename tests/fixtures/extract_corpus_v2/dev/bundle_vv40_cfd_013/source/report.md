# Slide 1 — Purpose and decision context
- Objective: estimate pressure losses and branch split for a round 600 mm T‑junction at 2.5 m/s inlet to support fan sizing and damper selection for Line C.
- Deliverable: predicted total pressure drop main‑inlet→downstream leg, and flow allocation to side branch, for use in a pre‑bid package.
- Acceptance band for use: ±10% on pressure loss across the fitting and qualitative assessment of recirculation extent.

# Slide 2 — Geometry and operating point
- Geometry: Schedule 20 round duct, 600 mm ID main run; 600×600 T with sharp internal corner, branch centerline orthogonal to main flow.
- Downstream leg: 3D after tee before gauge tap; branch: 4D after tee to tap; upstream straight: 8D.
- Air: 20°C, 1 atm; density 1.204 kg/m³; dynamic viscosity 1.81e‑5 Pa·s; incompressible.
- Nominal inflow: 2.5 m/s at main inlet → Q ≈ 0.707 m³/s (Re_D ≈ 99,500).
- Wall condition: commercial steel, equivalent sand‑grain roughness k_s = 0.15 mm.

# Slide 3 — Flow modeling choices
- Turbulence closure: k‑ω SST with automatic blending; rationale: adverse pressure gradients and separation bubbles expected near the tee lip.
- Wall treatment: low‑Re formulation with prism layers; target y+ ≈ 1–2 to resolve viscous sublayer where feasible.
- Continuity/momentum coupling: pressure‑based segregated solver, SIMPLE with Rhie‑Chow interpolation; second‑order schemes for all transport.
- Steady solution assumed; no buoyancy, no particulates, isothermal.

# Slide 4 — Boundary conditions
- Main inlet: uniform axial velocity 2.50 m/s; turbulence intensity 5%; turbulent length scale 0.07×D.
- Downstream outlet and branch outlet: static pressure 0 Pa (gauge) with backflow turbulence copied from domain.
- No‑slip walls; roughness height k_s = 0.15 mm, roughness constant 0.5 applied via equivalent sand‑grain model.
- Pressure taps emulated as area‑weighted averages over 50 mm discs flush to wall at specified D locations.

# Slide 5 — Mesh details
- Meshing approach: poly‑hexcore with local refinement near the tee intersection and within separation zones; 12 prism layers, first layer 0.1 mm, growth 1.2.
- Three levels for grid sensitivity:
  - Coarse: 1.2M cells, min y+ ≈ 0.8, max skewness 0.84.
  - Medium: 2.8M cells, min y+ ≈ 0.7, max skewness 0.80.
  - Fine: 6.5M cells, min y+ ≈ 0.6, max skewness 0.78.
- Quality checks: non‑orthogonality < 70°, cell aspect ratio < 35 in core, < 120 in near‑wall prisms.

# Slide 6 — Solver controls and monitors
- Pressure–velocity coupling under‑relaxation tuned: p=0.3, U=0.7, k/ω=0.6; multigrid on pressure.
- Residual targets 1e‑5 for all equations; achieved 2e‑6 to 7e‑6 on medium/fine runs.
- Additional convergence checks:
  - Mass imbalance < 0.2% domain‑wide on final 500 iterations window.
  - Monitored Δp between taps stable within ±0.5 Pa over final 200 iterations.
  - Velocity at branch plane mean stable within ±0.02 m/s.

# Slide 7 — Grid sensitivity and observed order
- Quantity of interest 1 (QoI1): total pressure drop main inlet → downstream tap (Δp_main).
- Quantity of interest 2 (QoI2): branch takeoff flow rate (Q_branch).
- Using uniform refinement ratio r ≈ 1.53 (coarse→medium) and r ≈ 1.53 (medium→fine) in the tee region via size fields.
- Results (Δp_main, Pa): 152.8 (coarse), 147.1 (medium), 145.2 (fine).
  - Estimated asymptotic order p ≈ 1.98 for Δp_main.
  - Richardson extrapolation Δp* ≈ 144.3 Pa; approximate grid‑induced error on fine ≈ 0.6% (GCI_fine ≈ 1.2% with Fs=1.25).
- Results (Q_branch, m³/s): 0.282 (coarse), 0.291 (medium), 0.295 (fine).
  - Observed order p ≈ 1.76 for Q_branch.
  - Extrapolated Q* ≈ 0.299 m³/s; estimated grid effect on fine ≈ 1.3% (GCI_fine ≈ 2.5%).

# Slide 8 — Sensitivity to inlet turbulence and wall roughness
- Inlet turbulence intensity varied 1% → 10% (medium grid):
  - Δp_main changed by −0.8% to +0.6%; Q_branch within ±1.1% of baseline.
- Wall roughness k_s varied 0.00 → 0.25 mm:
  - Δp_main increased up to +7.8% at 0.25 mm; Q_branch shifted −2.4% relative to baseline.
- Implication: loss dominated by wall friction and separation control near the tee edge; upstream flow “quality” less critical within tested range.

# Slide 9 — Inlet profile realism check (swirl and skew)
- Constructed two additional inlet profiles (medium grid):
  - Swirl number ≈ 0.20 with solid‑body core to 0.3D and decaying shear layer; kept bulk velocity at 2.5 m/s.
  - One‑sided skewed profile peaking at 1.2× mean on top half, matching typical elbow‑upstream condition.
- Effects:
  - Swirl case: Q_branch rose to 0.302 m³/s (+3.8% vs baseline), Δp_main +2.1%.
  - Skewed case: Q_branch dropped to 0.284 m³/s (−2.0%), Δp_main +1.4%.
- Conclusion: maldistribution at takeoff is sensitive to secondary motion; recommend maintaining ≥6D straight approach in layout where possible.

# Slide 10 — Key results and use in design
- Recommended values (fine grid, baseline BCs):
  - Pressure drop main inlet → downstream tap: 145 Pa.
  - Branch flow: 0.295 m³/s (≈ 41.7% of total).
- Apply ±10% band on Δp_main if roughness or approach flow is uncertain beyond provided ranges.
- Recirculation length along the dead‑leg wall ≈ 1.1D; peak turbulence kinetic energy ~ 22 m²/s² at the branch lip.

# Slide 11 — Visuals (described)
- Streamlines colored by speed show separation bubble anchored at the branch lip, with reattachment ≈ 0.9D downstream.
- Wall shear stress map highlights elevated τ_w around the inner corner; consistent with friction‑driven loss component.
- Velocity profiles at 1D downstream of branch show M‑shaped distribution in the main leg; branch entry exhibits off‑axis peak due to turning.

# Slide 12 — Assumptions and modeling limits (for downstream users)
- Steady‑state only; potential low‑frequency unsteadiness not captured.
- Single‑phase, dry air; no condensate film modeled.
- Thermal effects neglected; density held constant.
- No vibration‑induced surface roughness growth considered; fixed k_s used throughout.
- Elbows, dampers, and screens outside the 8D/3D/4D segments not included; apply additional system losses separately.

# Slide 13 — Next actions
- If branch throttling is expected, repeat at 30%, 50% damper positions using same setup and re‑use fine mesh blocks.
- Provide CAD of the upstream layout if swirl likely exceeds S=0.1 so that approach flow can be modeled explicitly.
- If surface condition differs (lined duct or aged galvanization), refine roughness bounds and re‑compute impact on Δp_main.
