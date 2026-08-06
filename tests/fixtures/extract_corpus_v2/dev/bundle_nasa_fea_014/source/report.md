# LTV-2 Avionics Bracket FEA — Credibility Snapshot (PDR)

- Project: Lunar Terrain Vehicle (LTV-2)
- Component: Avionics bay corner bracket (Al 7075-T7351), P/N LTV2-AVB-003
- Analysis tool: Ansys Mechanical 2024 R1 (Solver Build 24.1.108), Workbench project AVB_24R1_PDR
- Analyst: M. Chen (Structures), peer check: M. Alvarez
- Date: 2026-07-29

## Slide 1 — Why we modeled this part

- Decision supported:
  - Clear bracket for PDR with mass target unchanged and no redesign of the avionics corner stack
  - Establish static strength and stiffness margins for ascent-stage quasi-static and sine sweep loads
- What the model is used for:
  - Predict peak stress and deflection under worst-case combined in-plane shear and out-of-plane bending caused by avionics mass and harness loads
  - Quantify influence of bolt preload and joint friction on stiffness (mounting stack-up tolerance study deferred to CDR)
- Acceptance targets (PDR):
  - Yield safety factor ≥ 1.25 on primary load case
  - Deflection at avionics connector face ≤ 0.40 mm under sine-peak equivalent load
  - No loss of clamp (no net separation at interface under worst preload scatter)

## Slide 2 — Scope and simplifying choices

- Physics included:
  - Quasi-static structural response; geometric nonlinearity OFF (max rotations < 3°)
  - Contact nonlinearity ON (frictional, small sliding) between bracket and base plate; bonded at PCB interface
- What we did not include (by design for PDR):
  - Acoustic random and PSD vib — tracked in dynamics plan, not in this static model
  - Thermal gradients and cooldown preload — flight thermal loads to be added for CDR coupling
  - Fatigue life estimation — will be based on CDR random vib results
  - Manufacturing tolerances and hole ovality — awaiting supplier capability data (CDR)
- Rationale:
  - Load paths dominated by bracket web bending and fillet stresses; elastic response governs connector alignment
  - Thermal and acoustic effects small in PDR configuration trade; verified by back-of-envelope comparisons

## Slide 3 — Geometry, interfaces, and loads

- Geometry source:
  - CAD: LTV2-AVB-003 Rev C (Creo), imported via STEP; fillet radii and chamfers preserved
  - Fasteners: four M5 class 12.9 bolts, 10 mm grip; holes modeled as through with lead-in chamfers
- Interfaces:
  - Bracket-to-base plate: frictional contact, µ = 0.25 nominal; surface finish Ra 1.6 µm
  - PCB-to-bracket: bonded (epoxy layer not modeled explicitly); stiffness contribution negligible (<2% effect in trial)
- Loads and constraints:
  - Bolt preloads: 9.5 kN per bolt (torque 6.0 N·m with K=0.22), applied via bolt pretension elements
  - External: equivalent static from sine sweep: Fx = 1.8 kN, Fz = 2.3 kN applied at avionics CG pad; small My = 120 N·m
  - Base plate boundary: fixed at bolt circle behind bracket footprint (matches test fixture)

## Slide 4 — Elements, mesh controls, and feature capture

- Element technology:
  - SOLID186 (quadratic tets), midside nodes retained on curvature; selective reduced integration OFF
  - Contact: CONTA174/TARGE170, augmented Lagrange, normal penalty factor auto, tangential penalty 0.2
- Mesh details:
  - Global size 2.0 mm; refinements: 0.75 mm around fastener holes and web-to-base fillets; 0.5 mm at the inner corner notch
  - Element quality: Jacobian ratio > 0.55; skewness < 0.75; no negative volumes
  - Through-thickness: minimum 4 elements across web thickness (t=3.5 mm), 6 around fillets
- Reasoning:
  - Stress gradients steep at hole edges and fillet transitions; curvature-based sizing validated by spot checks

## Slide 5 — Mesh refinement study (stress and stiffness)

- Three meshes:
  - Coarse: ~0.9M DOF (min size 1.2 mm at hotspots)
  - Medium: ~1.8M DOF (min size 0.8 mm at hotspots)
  - Fine: ~3.6M DOF (min size 0.5 mm at hotspots)
- Convergence indicators:
  - Tip deflection at connector face: 0.331 mm (coarse), 0.318 mm (med), 0.314 mm (fine) → change med→fine = 1.2%
  - Peak von Mises at inner fillet (nodal): 338 MPa (coarse), 327 MPa (med), 320 MPa (fine) → change med→fine = 2.1%
  - Linear-extrapolated hotspot stress (quarter-point method) from fine: 328 ± 8 MPa
- Decision:
  - Fine mesh adopted for reporting; remaining discretization impact on deflection < 1.5%, on stress < 3%

## Slide 6 — Solver behavior and numerical checks

- Static sequence:
  - Step 1: Apply bolt pretension to targets (ramped), maintain lock
  - Step 2: Apply external loads with 20 substeps, automatic time stepping; force residual target 0.1%, displacement convergence 0.1%
- Health metrics:
  - Contact penetration max 5.8 µm at load peak; contact status stable after substep 7
  - No free rigid body modes detected; pivot checks clean; energy balance within 0.4% at final substep
  - Repeat run with different initial contact status produced identical deflection within 0.2% (reproducibility check)
- Sensitivities to numerics:
  - Doubling normal penalty changed hotspot stress < 1%; switching to pure penalty raised penetration but not global response

## Slide 7 — Materials and where the numbers came from

- Base material: Aluminum 7075-T7351 plate, 6.35 mm stock, cut and machined
  - Elastic: E = 71.7 GPa (±1.2 GPa, lot data), ν = 0.33
  - Yield (0.2%): 435 MPa; Ultimate: 505 MPa (MMPDS-17, Table 3.7.2.0(b))
  - Plasticity: bilinear kinematic hardening, tangent modulus 1.3 GPa for overload checks (not engaged in PDR limit loads)
- Data pedigree:
  - Mill cert for Heat 7A-26 included; tensile coupon test (3 samples) from sister plate: E = 72.1±0.8 GPa, Fy = 442±6 MPa
  - Temperature: 20–60 C variation tested in sensitivity; E drop ~1.5% max; yield knockdown not applied at PDR
- Fasteners: ISO 898-1 Class 12.9 properties; flange washers per ISO 7089; friction coefficient from NASA-HDBK-5080, conservative µ=0.25

## Slide 8 — Benchmarks and sanity checks on the setup

- Reproduced NAFEMS LE10 “plate with a hole” tension case:
  - Modeled quarter symmetry with SOLID186; nominal K_t = 3.00; obtained 2.98 at fine mesh (0.7% low)
- Cantilever beam tip deflection (closed-form):
  - 200×25×5 mm beam, E=70 GPa; analytical δ = 9.14 mm for 500 N; model gave 9.11 mm (0.3% low)
- Contact sanity test:
  - Cylinder-on-flat compression compared to Hertz solution; coarse mesh off by 8%; refined contact patch to 0.3 mm elements reduced error to 2.5%
- Conclusion:
  - Element formulation and contact settings reproduce textbook responses within a few percent

## Slide 9 — Comparison to subcomponent test (static pull)

- Test article:
  - Single bracket mounted to a 12 mm 7075 base plate; preload with calibrated torque wrench; loads applied via adapter at avionics CG pad
  - Instrumentation: 4 strain gauges around inner fillet (G1–G4), LVDT at connector face
- Measured vs predicted:
  - Load–deflection slope: Test 7.24 kN/mm; Model 7.52 kN/mm (+3.9%)
  - Strain at G1 (peak): Test 3,120 µε; Model 3,250 µε (+4.2%)
  - Onset of local yielding by DIC: Test at 27.0–27.5 kN; Model plasticity onset at 27.5 kN (bilinear fit)
- Notes:
  - Preload variation across bolts measured 9.1–10.0 kN (ultrasonic meter); model used uniform 9.5 kN
  - Friction estimated from slip test at 0.23–0.28; model nominal µ=0.25 aligns with mean value

## Slide 10 — What matters most (parameter sweeps)

- Varied one at a time around nominal:
  - Bolt preload ±10%: connector deflection changes ±2.0%; hotspot stress ±1.3%
  - Friction µ = 0.15 → 0.35: connector deflection −0.8%; hotspot stress −6.1% over the range
  - Elastic modulus −2%: deflection +2.0%; stress −1.5% (load-controlled)
  - Chamfer tolerance (±0.2 mm) at fillet root: local stress ±3.5% (geometry sensitivity)
- Combined case (Latin hypercube, 250 samples):
  - Inputs: E N(71.7,1.2), µ U(0.20,0.30), preload N(9.5,0.7), fillet radius N(2.0,0.1)
  - Outcomes: deflection mean 0.316 mm, 95th percentile 0.329 mm; hotspot stress mean 322 MPa, 95th percentile 336 MPa

## Slide 11 — Margins and decision readout

- Against yielding (limit load, fine mesh):
  - Predicted von Mises at critical fillet node: 320 MPa; Allowable: 435 MPa / 1.00 (elastic) → FoS_y = 1.36
  - Including 95th percentile from sweep: 336 MPa → FoS_y(95%) = 1.29
- Stiffness requirement:
  - Deflection at connector face: 0.314 mm < 0.40 mm limit (nominal); 0.329 mm (95th) still below limit
- Joint integrity:
  - Minimum contact pressure under load remains positive across interface (>4.2 MPa), indicating no local lift-off
- Recommendation:
  - Bracket acceptable for PDR with current geometry; keep µ ≥ 0.22 and torque ≥ 5.5 N·m in assembly work instructions

## Slide 12 — Model tracking, reproducibility, and independent eyes

- How to re-run:
  - Workbench project: AVB_24R1_PDR.wbpj, stored in Git LFS at repo structures/ltv2/avionics_bracket, tag v0.9-PDR
  - Mesh recipe saved as Named Selections and Local Sizing set; solution controls exported (xml)
  - Solver logs archived with checksum; input deck CRC32: D3A4-9F11
- Reviews:
  - Cross-check by M. Alvarez: re-meshed with slightly different hotspot sizing (0.6 mm) → stress within 2.4%, deflection within 0.6%
  - Comments addressed: added contact sanity test; documented penalty sensitivity
- Traceability:
  - CAD Rev C; material lot 7A-26; Ansys 2024 R1; contact settings v2; all referenced in Model Register MR-AVB-003-PDR

## Slide 13 — Gaps and CDR to-dos

- Out of scope in this package:
  - PSD/random vibration and modal correlation — covered by dynamics team, CDR deliverable
  - Thermal preload and cooldown — requires flight thermal map; to be included in coupled load case set
  - Fatigue and fretting at hole edges — will use stress-life with surface finish and notch sensitivity after vib environment fixed
  - Manufacturing deviations (hole position, ovality, surface finish) — awaiting supplier process capability; will roll into statistical study
- Data we still need:
  - Direct friction measurements for the actual washer-lube stack intended for flight
  - Final torque–tension scatter with production tooling
- Suggested risk burn-down:
  - Run one additional subcomponent test with instrumented bolts to lock down preload distribution
  - Perform spot-check with a hexahedral-dominant mesh around fillets to confirm hotspot behavior within ±3%
