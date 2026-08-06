# Slide 1 — UAV Payload Bracket FEA Summary (Rev B)

- Component: L-shaped 7075-T6 aluminum bracket connecting payload tray to keel frame
- Objectives
  - Survive quasi-static launch load without yielding
  - Tip deflection below 0.80 mm at 11.8 kN axial load
  - First bending mode above 220 Hz
- Toolchain: SpaceClaim geometry, Ansys Mechanical 2024 R1, MAPDL solver; scripts tracked in Git (repo: payload-bracket, tag: v0.9-Beta)


# Slide 2 — What “good” looks like

- Acceptance targets (Structures ICD-42):
  - Margin on yield ≥ 1.20 at critical fillet
  - Lateral tip deflection ≤ 0.80 mm at max service load
  - First natural frequency ≥ 220 Hz with payload mass simulant attached
- Reference test article: Test rig TR-03, 12.5 kN axial pull, torque bias 35 N·m
- Note: Vendor tolerance for bolt preload ±10%


# Slide 3 — Geometry and modeling choices

- CAD basis: BRKT-PA-102.step, dated 2026-05-18
- Details retained:
  - 8 mm web thickness; 14 mm base pad; 3 mm corner reliefs called R2 in drawing
  - 6x M6 through-holes, countersink modeled explicitly (90° x 2.3 mm)
- Simplifications:
  - Threads not modeled; bolts represented by beam elements with pretension sections
  - Fillets below R1.5 suppressed to reduce mesh count
  - Note: Early note states R2 fillets included near the knee; later cleanup script suppresses “small rounds,” which removes some R2 features in the knee region


# Slide 4 — Loads, constraints, and interfaces

- External loading:
  - Axial draw: 11.8 kN applied via rigid payload plate (distributed)
  - Superimposed torque: 35 N·m about bracket vertical axis
  - Gravity ignored during static runs; included for modal
- Supports:
  - Base flange defined as encastre at 6 bolt-hole contact patches
  - Also trialed distributed spring supports (K = 1.6e6 N/m per DOF) to mimic test stand compliance
- Interfaces:
  - Contact between payload plate and bracket: initially frictionless “bonded”; later runs used µ = 0.2 with no-separation
  - Bolt shank to hole: clearance enforced using surface-to-surface contact with small sliding
- Note: The “validation” case cites fixed base; the test fixture used compliant bushings


# Slide 5 — Materials and properties

- 7075-T6 (MatDB: Al-7075-T6-AMS-QQ-A-250-12)
  - E = 71.7 GPa, ν = 0.33, ρ = 2810 kg/m³
  - Yield strength = 503 MPa (Rp0.2), ultimate = 572 MPa
  - Base model: isotropic linear elastic
- Temperature: 23 ± 2°C assumed; cold case data (-20°C, E ≈ 74 GPa) listed but not used
- Alternate material card in Rev A:
  - Bilinear hardening with Et = 1.5 GPa activated for “overload check” only
  - Note: Run notes in 2026-06-19 mention “bilinear on” for the so-called linear check; unclear if this applied to Rev B results


# Slide 6 — Discretization and element choice

- Mesh strategy:
  - Tet10 elements in the web and knee; Hex-dominant sweep in the base pad
  - Target sizing: 1.2 mm in knee fillet, 3.5 mm elsewhere; 0.6 mm around fastener lines
- Quality metrics:
  - Average aspect ratio = 2.7; 93% below 5
  - Hot-spot band has 7% elements with aspect ratio up to 11 (waiver logged)
- Model size (medium mesh): 1.1 M DOF; 186k elements
- Rationale:
  - Tet10 for curvature fidelity; swept hex under bolt pads to capture bearing stresses


# Slide 7 — Refinement exercise (three levels)

- Mesh levels:
  - Coarse: 0.5 M DOF, knee size = 1.8 mm
  - Medium: 1.1 M DOF, knee size = 1.2 mm
  - Fine: 2.4 M DOF, knee size = 0.8 mm
- Peak von Mises at knee (MPa):
  - 462 (coarse), 489 (medium), 497 (fine)
- Tip deflection (mm):
  - 0.93 (coarse), 0.87 (medium), 0.86 (fine)
- Claimed outcome:
  - “Within 2.1% apparent error on stress; deflection converged”
- Caveats:
  - Hot-spot location moves ~1.4 mm between meshes
  - Extrapolated stress (Richardson) ≈ 505–509 MPa depending on r; exceeds yield for “linear” runs
  - Contact status changes between levels (bonded vs µ = 0.2 noted in workbook for the fine run)


# Slide 8 — Solver settings and numerical controls

- Static analysis:
  - Geometric nonlinearity off (small deflection) per control deck
  - Contact enforcement: augmented Lagrange, normal penalty 0.2 default
  - Convergence: force norm 1e-6 N and displacement norm 1e-6 m in Rev A; solver.log for Rev B shows 1e-4 tolerances accepted on substeps 7–9
- Bolt pretension: 8 kN per bolt, ramped in Step-1; external loads in Step-2
- Modal analysis:
  - Lanczos, 0–800 Hz; payload simulant 1.2 kg lumped via MPCs
  - Damping for correlation: 2% critical stated; correlation sheet uses 5% for curve fit


# Slide 9 — Quick code checks and sanity tests

- Benchmarks executed prior to bracket runs:
  - Cantilever beam tip deflection (classical solution): error 0.3% with Tet10
  - NAFEMS plate with a hole (LE10): hoop stress at hole within 1.4%
- Internal consistency:
  - Energy balance within 0.7% on medium mesh (contact off)
  - With contact on, work balance grew to 3.9% in Rev B fine mesh run


# Slide 10 — Physical test correlation (TR-03)

- Setup:
  - Bracket bolted to steel fixture with neoprene bushings; 12.5 kN axial pull; 35 N·m torque applied
  - Strain gauges at SG1 (knee outer radius), SG2 (web mid-height), SG3 (base edge)
- Measured peak microstrain at 12.5 kN: SG1=3100, SG2=2150, SG3=980 με
- Analysis predictions (medium mesh):
  - At 10.0 kN, linear elastic run: SG1=2750, SG2=2290, SG3=1015 με
  - Scaling to 12.5 kN yields SG1=3437, SG2=2863, SG3=1269 με
- Reported “error <5%” note is based on 10.0 kN comparison, not the 12.5 kN test level
- Fixture mismatch:
  - Model used fixed pads; test used compliant bushings (~0.25 mm lateral play), softening strains by ~8–12% per quick sensitivity run


# Slide 11 — Frequency targets

- Model result with payload mass simulant:
  - f1 (bending about long axis) = 238 Hz
  - f2 (torsion) = 366 Hz
- Test shaker sweep (light preload):
  - First peak at 226–232 Hz depending on boundary tightness
- Influence factors:
  - ±10% bolt preload shifts f1 by ~6%
  - µ from 0.0 to 0.3 shifts f1 by ~3%
- Acceptance: Meets 220 Hz threshold with margin; note that damping in fit used 5%, while spec assumes 2%


# Slide 12 — Sensitivity highlights and input pedigree

- Parameter probes (one-at-a-time on medium mesh):
  - Friction µ = 0.0 → 0.2 → 0.3: peak stress 476 → 489 → 494 MPa (~4% swing)
  - Bolt preload 7.2 → 8.0 → 8.8 kN: peak stress −3%/0%/+2%; f1 +/− ~6%
  - E = 69 → 71.7 → 74 GPa: deflection +4%/0%/−3%
- Aggregate uncertainty (rough): 8–12% on strain prediction when combining fixture compliance and material tolerance
- Input sources:
  - Material: MMPDS-17 and supplier cert 24-18577 (heat 7Z)
  - Torque applied with Norbar 100 (calibrated 2026-04-10)
  - Preload inferred from torque–tension; k-factor assumed 0.18; no direct DTI measurements


# Slide 13 — Data management and reproducibility

- Configuration:
  - Model Rev B: commit 6f2c9d1; scripts in /scripts/run_b_static.py and /scripts/run_b_modal.py
  - Solver logs archived in /results/RevB except fine-contact run (log overwritten on 2026-06-22; only summary remains)
- Traceability:
  - Workbook “BRKT_Results_RevB.xlsx” records 18 runs; 3 rows tagged “superseded” but still referenced in Slide 7 plot
- Environment:
  - Ansys 2024 R1 HF1 on Linux; one fine run executed on Windows (build 2024 R1 base), mixing minor versions


# Slide 14 — Review process and ownership

- Review sessions:
  - SME check on meshing and contacts by M. Salazar, 2026-06-20
  - Load path discussion with Test Eng (R. Duan), 2026-06-24
- Independence:
  - Peer reviewer (Salazar) authored the contact modeling script; independence limited
  - External read-across from Payload Bracket Rev A used by same analyst
- Actions:
  - Align boundary conditions with test fixture for apples-to-apples strain checks
  - Clarify whether bilinear hardening was active in Rev B static set


# Slide 15 — Bottom line and open items

- Against targets at 11.8 kN:
  - Yield check: Peak stress 489–497 MPa vs 503 MPa allowables; implied MoS ≈ 1.01–1.03 on “linear” assumption; extrapolated value crosses yield
  - Deflection: 0.86 mm predicted vs 0.80 mm limit → exceeds by ~7.5%
  - First mode: 238 Hz predicted → passes 220 Hz criterion
- Conflicting evidence flags:
  - Base support stiffness in model vs test; contact treatment varies across meshes
  - Solver tolerances relaxed in Rev B log; “linear” material runs possibly used bilinear card
  - Claimed <5% correlation relies on reduced load case not matching the 12.5 kN test
- Next steps (1 week):
  - Re-run with test-stand compliance and consistent µ; tighten solver tolerances to 1e-6; freeze linear material
  - Repeat mesh study with consistent contact; anchor hot-spot location via local refinement
  - Directly preload bolts via bolt-force calibration or DTI; re-baseline correlation at 12.5 kN
  - If peak stress remains at/above yield, consider R2.5 knee radius or 10 mm web thickness change and re-check modes
