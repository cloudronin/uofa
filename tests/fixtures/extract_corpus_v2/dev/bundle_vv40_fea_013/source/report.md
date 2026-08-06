# Antenna Bracket FEA Credibility Review — Slide Deck

## Overview and scope
- Component: Ti-6Al-4V additively manufactured antenna bracket (topology-optimized, machined interfaces)
- Use-case: justify launch static and random vib loads; support sizing and print acceptance
- Tools and workflow:
  - Preprocessor: SpaceClaim 2023R2; Solver: Ansys Mechanical R2023 R2 (Sparse direct)
  - Parametric scripts: Python 3.10, ACT workbench journals (git rev fe4a7a)
- Decision asked: can we rely on the current model for preliminary flight sizing and vib notching?

## What the model is intended to answer
- Peak stresses in legs and fillets under combined axial + lateral launch accelerations (±35 g axial, ±15 g lateral)
- Load transfer at M6 bolted pads into the deck; check pull-through risk and pry-out
- First three natural frequencies against payload shaker limit (target > 200 Hz for mode 1)
- Identify hotspots for CT scan focus post-print
- Not in scope: fatigue life, thermal gradients in orbit, micrometeoroid shock

## Physics captured and simplifications
- Linear elastic Ti-6Al-4V; no plasticity modeled in primary runs (with a spot-check nonlinear case)
- Bolted pads modeled as pretensioned fasteners with rigid washers; threads idealized by bolt-to-nut beam
- Contact:
  - Bracket-to-deck: frictional with tangential slip allowed
  - Internal topology cavities removed; printed lattice not explicitly modeled (replaced by equivalent solid)
- Damping: viscous equivalent for modal extraction (Rayleigh α,β tuned to ~1% at 200 Hz)
- Thermal effects ignored during launch; room-temperature moduli at 22°C

## Geometry, loads, and supports
- CAD revision: ANT-BRK-019_G
- Interfaces:
  - Four M6 pads to deck; two M5 pads to antenna foot; 2 mm dowel pins omitted (fit too tight to represent reliably at this stage)
- Loads:
  - Quasi-static: g-load vectors applied as body accelerations; antenna mass 1.8 kg at foot CG via remote mass
  - Bolted joint preload: 8 kN per M6, 4 kN per M5
- Supports: deck modeled as rigid via MPC to ground
- Note: slide 9 shows an earlier run with 6 kN per M6 (superseded but retained for traceability)

## Material inputs and pedigree
- Nominal: Ti-6Al-4V Grade 5, E = 110 GPa, ν = 0.34, σy = 880 MPa, UTS = 950 MPa (EOS datasheet)
- Coupon tests (lot A, L-PBF, 40 µm layer, stress-relieved, machined): E = 102 ± 3 GPa, σ0.2 = 965 ± 25 MPa, UTS = 1040 ± 20 MPa, anisotropy < 4%
- Density: 4.43 g/cc; damping loss factor assumed 1% for correlation
- Which set used:
  - Prelim meshes (M1–M2): vendor datasheet
  - Final mesh (M3): note says “updated to coupon E = 102 GPa”, but the solver input file lists E = 110 GPa (see config slide)
- Surface roughness and pores not modeled; accounted via 10% safety margin in hand calc cross-checks

## Meshing approach and quality checks
- Elements: tetrahedral 2nd order (SOLID187); wedge transition near fillets; 10 elements across pad thickness
- Target size: 1.2 mm global; 0.4 mm at fillet radii (r = 1.0–1.5 mm); Jacobian > 0.6, aspect ratio < 4
- Refinement sweep:
  - M1: 0.8M nodes (global 1.8 mm), M2: 1.6M nodes (1.2 mm), M3: 3.1M nodes (0.9 mm)
- Stress change at hotspot (near antenna foot fillet):
  - Slide note states “<3% between M2 and M3”, but recorded max von Mises: 612 MPa (M2) vs 667 MPa (M3) → +9.0%
- Displacement at antenna tip: 0.32 mm (M2) vs 0.33 mm (M3) → +3.1%
- Commentary: we likely have a local peak sensitivity to tiny radius; trimmed CAD versus as-printed may differ

## Contacts, solver controls, and convergence behavior
- Contact formulations:
  - Foot-to-bracket: bonded (machined interface)
  - Bracket-to-deck: frictional; µ = 0.2 per design note BRK-INT-05
- Augmented Lagrange, normal stiffness program-controlled; 15 contact iterations cap; line search on
- Residual targets: force < 1e-4, displacement < 1e-5
- Nonlinearity:
  - Primary results presented from linear static with preload followed by acceleration step
  - One nonlinear run with plasticity/large-deflection flag ON shows 1.6% increase in tip deflection and 18 MPa reduction in max stress due to redistribution
- Inconsistency: in the modal model, interface uses µ = 0.05 to preserve symmetry with test fixture notes, but static set kept µ = 0.2; not harmonized

## Code and model sanity checks
- Element behavior spot-checks:
  - Patch test plate passes to within 0.5% strain energy error on SOLID187
  - Hourglass control N/A (higher-order tets)
- Energy balance and reaction checks:
  - Sum of base reactions under body load within 0.7% of m·a
  - However, run ANTB3_M3_2024-06-19 shows 3.9% mismatch before final convergence pass (saved erroneously; not used for plots)
- Scripts and reproducibility:
  - Preload and load sequencing encapsulated in JN_run_112.py; seeds materials via YAML
  - Git tag fe4a7a corresponds to the M3 mesh; but “materials.yaml” in that tag still lists E=110 GPa

## Correlation to test (shaker and static bench)
- Modal tap test (fixture replicates M6 bolt pattern; bolts torqued to 8 kN target):
  - Measured modes: 1st = 212 Hz, 2nd = 283 Hz, 3rd = 401 Hz
  - Model (bonded foot, µ=0.05 at base): 1st = 207 Hz (−2.4%), 2nd = 251 Hz (−11.3%), 3rd = 392 Hz (−2.2%)
  - Slide 2 summary “within 3% for first three modes” conflicts with the 2nd mode difference above
- Static bench (mass block 1.8 kg, 15 g lateral):
  - Strain at gage SG-2: test 412 µε; model 396 µε (−3.9%)
  - Out-of-plane tip deflection: test 0.34 mm; model 0.33 mm (−2.9%)
- Damping used in correlation:
  - Modal run notes say 1% critical; correlation log shows 2% to fit decay at 280 Hz

## Sensitivity exploration and margins
- Parameters varied one-at-a-time on M2 mesh:
  - µ = 0.1–0.3 → bolt axial load redistribution changes ±6%; hotspot stress ±5%
  - Bolt preload 6–10 kN → hotspot stress −4% to +3%; foot uplift risk suppressed above 7 kN
  - E = 100–110 GPa → tip deflection +3% to −3%; stresses nearly unaffected (<1%)
  - Fillet radius +0.25 mm → −8% hotspot stress; −0.25 mm → +12% hotspot stress
- Combined case (µ=0.15, preload=7 kN, r−0.25 mm) gives +14% in hotspot stress relative to baseline
- Reported safety margin (elastic, vs 0.9·σy) on M3: 0.9·σy/σmax = 1.24 using σy=880 MPa
  - If coupon yield 965 MPa is used, margin improves; however, M3 stress value depends on unresolved mesh sensitivity (+9%)

## Configuration control and traceability
- Model IDs:
  - ANTB3_M1_2024-05-29, ANTB3_M2_2024-06-05, ANTB3_M3_2024-06-19
- Software and licenses: Ansys Mechanical R2023 R2 build 23.2.0; sparse solver
- Inputs under version control:
  - Geometry ANT-BRK-019_G (Step file hash 6f8b0); scripts and workbench archive tracked
  - Known inconsistency: “materials.yaml” in tag fe4a7a not updated to coupon E despite slide claim; correction staged but not merged at time of review

## Limitations and open items
- No explicit surface defect modeling; roughness and porosity not in the mesh
- Fillet peak stress still rising under further local refinement; potential notch-like behavior
- Contact friction not aligned between static and modal models; needs unification per test evidence
- Damping assignment not consistently documented; 1% vs 2% discrepancy remains
- Boundary conditions: dowel pins ignored; likely stiffen certain modes slightly
- As-built vs as-designed: CT scan-based model pending (print lot B due next week)

## Credibility summary (plain-language)
- Strengths:
  - Reaction/mass-acceleration checks close; displacements well behaved
  - Static strain/deflection agree within ~5% at instrumented points
  - Mode 1 and 3 are close to test; overall frequency targets met
- Weaknesses and contradictions that erode confidence:
  - Material stiffness in final runs appears to be 110 GPa while slides state 102 GPa from coupons
  - Mesh independence claim (<3%) not supported by numbers at the hotspot (+9%)
  - Contact friction differs between static (0.2) and modal (0.05) with no clear rationale
  - Summary slide claims “<3%” across modes, but mode 2 is off by ~11%
  - Bolt preload values vary across slides (6 vs 8 kN); only 8 kN matches current torque spec
- Residual risk:
  - Local peak stress could be understated by unresolved mesh and as-built radius
  - If µ is closer to 0.1 (oily anodized deck), load path changes enough to affect bolt loads

## What we will do next if approved
- Harmonize contacts and damping across all models; use test-inferred µ ≈ 0.12–0.15
- Update materials.yaml to coupon E and rerun M3; add localized r=0.25 mm mesh band
- Import CT from lot B for as-built fillet radii; re-evaluate hotspot with same loadcases
- Expand shaker correlation to include operational deflection shapes for the 2nd mode

## Decision
- Verdict by Structures V&V Board (6 Aug 2026):
  - The current FE model is accepted for preliminary antenna bracket sizing and for generating inspection focus regions, subject to:
    - Unifying contact parameters and damping to match test evidence
    - Repeating the fine-mesh run with corrected elastic modulus and local refinement at the foot fillet
  - The model is not approved for final flight release stress reports or drawing sign-off until the above items are closed and the mode 2 correlation gap is resolved
