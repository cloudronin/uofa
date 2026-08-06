# Slide 1 — AVB-21 Bracket FEA Overview
- Component: AVB-21 avionics tray bracket (aluminum L-bracket with two mounting ears)
- Use case: launch vehicle avionics stack; quasi-static g-loads and qualification vibe
- Aim: confirm yield margin at stress hot-spots around bolt holes and fillets; check first three modes clear of payload bay lines
- Toolchain: Abaqus/Standard 2023 HF7 on RHEL 8; CAD from NX 2206 (STEP AP242). Some early meshes run in Abaqus/Standard 2022 HF4 (see Slide 11)
- Units: mm–N–s
- Team: structures (E. Chen), test (J. Patel), CAD (R. Diaz)
- Note: detailed bolt thread geometry, safety wire holes, and logo deboss removed from analysis model

# Slide 2 — Loads, Constraints, and How We Mounted It
- Primary static equivalent accelerations:
  - 15 g axial (aligned with bracket leg); 8 g lateral
  - Mass of avionics tray 2.4 kg; four-bolt interface; load shared 60/40 front-to-rear by stiffness
- Fasteners and joint representation:
  - Four M5 class 12.9 bolts; design torque 5.7 N·m → ~8 kN pre-tension per bolt
  - In the nonlinear run: pretension section in Step-0; friction coefficient 0.2; contact set “steel-on-aluminum”
  - For linear modal runs: all contacts simplified as “tied” (no slip)
- Boundary conditions:
  - Base feet constrained to a rigid plate; plate fixed at four launcher rails
  - A symmetry plane was used across bracket midline to reduce model size
- Note: The vibe fixture used during test did not employ symmetry; it used the full bracket (see Slide 8)

# Slide 3 — Geometry Choices and What We Left Out
- Simplifications:
  - Fillet radii preserved ≥1.0 mm; micro-chamfers <0.3 mm removed
  - Bolt threads, helicoils, and washer crowns not modeled; bolts represented by beam connectors to pretension sections
  - Cable tie bosses and nameplate bosses kept to preserve local stiffness
- As-built differences:
  - Test article included stainless helicoils and Belleville washers; drawing calls for helicoils optional (“if thread wear expected”), not in analysis CAD
- Tolerances:
  - Hole diameters nominal 5.5 mm; measured 5.62–5.66 mm on test lot; FEA uses nominal

# Slide 4 — Material Behavior and Data Sources
- Base material: AA 7075‑T6 (AMS 4045), room temperature properties:
  - E = 71.7 GPa; ν = 0.33; σy = 503 MPa; σu = 572 MPa
- Plasticity:
  - Nonlinear run uses a bilinear kinematic curve fit to in-house coupons (ASTM E8), Etan ≈ 1.2 GPa
  - Ramberg–Osgood n = 8.7, α calibrated to 0.002 at σy
- Temperature remarks:
  - Environmental spec −20 to +50 C; we used temperature‑independent data in the static runs
  - Slide 10 notes “temperature‑dependent elastic modulus used for modes,” which was based on MIL‑HDBK‑5 tables at 20/40 C
- Contrary note in the static results summary on Slide 12 references “linear elastic stress,” which omits the above plastic fit

# Slide 5 — Meshing Strategy and Two Paths We Tried
- Elements:
  - Primary mesh: quadratic tets (C3D10M), curvature control on holes and fillets
  - Alternate trial: hex‑dominant mesh around the web with pyramid transitions near bolt pads (abandoned due to poor Jacobians near pad steps)
- Local refinement:
  - Target sizes: 0.5 mm at hole edges and 1.0 mm at 1 mm fillets; 2.5–3.0 mm on web
- Convergence study:
  - Coarse: ~78k elems, peak von Mises at lower bolt hole = 238 MPa, tip deflection 0.74 mm
  - Medium: ~164k elems, peak = 226 MPa, tip = 0.71 mm
  - Fine: ~512k elems, peak = 241 MPa, tip = 0.71 mm
- Statement: “Monotonic convergence achieved; stress change fine-to-medium <2%.” Note the coarse/medium/fine peak values above are not monotonic and differ by up to ~6%
- Extrapolated zero-size stress via Richardson fit: 244 MPa (based on medium/fine only)

# Slide 6 — Contacts, Nonlinear Controls, and Cutbacks
- Contact modeling:
  - General contact for bracket-to-rail interface; bolt pretension introduced before external loads
  - Near-hole contact surfaces faceted on the coarse mesh; smoothed on fine
- Solution controls:
  - Static, general; automatic stabilization 1e−4 used for two increments to suppress contact chattering, then turned off
  - Large‑deflection flag: ON for static load step
  - However, early runs reported in the internal log show “NLGEOM=NO to improve convergence” for the medium mesh
- Preload note:
  - A side note in run deck v3.2: “Preload effects ignored after step 2 due to divergence; kept bolts tied.” That contradicts the pretension description above

# Slide 7 — Dynamic Characterization (Modes)
- Modal analysis assumptions:
  - Linear perturbation about prestressed state (Step‑1) with tied interfaces
  - E(T) used: 71.7 GPa at 20 C; 69.9 GPa at 40 C (for hot case sweep)
- Predicted (20 C): f1 = 912 Hz (first bending), f2 = 1183 Hz (torsion), f3 = 1640 Hz
- With joint slip allowed (trial model): f1 dropped to 828 Hz
- Acceptance line: payload bay notch at 750 Hz minimum separation 10% → predicted clear by 21% (using 912 Hz)

# Slide 8 — What the Lab Saw and How Close We Are
- Shaker test setup:
  - Full bracket (no symmetry) with mass simulator; four bolts torqued to 5.7 N·m; washers and helicoils installed per process sheet
- Measured modes (ambient, 21 C):
  - f1 = 770 ± 8 Hz; f2 = 1130 Hz; f3 = 1592 Hz
  - Report summary states “within 5% of prediction.” Compared to 912 Hz model, f1 differs by ~18% (or 7% vs the joint‑slip trial at 828 Hz)
- Static pull test:
  - Strain gage SG‑03 at lower hole quadrant: test 310 με at 15 g equivalent; FEA (fine mesh, linear elastic) 285 με → 8.1% low
  - With plasticity on, local strain 342 με; correlation worsens at that location but improves at SG‑07 on the web (test 190 με vs FEA 195 με)
- Fixture/model mismatch:
  - Lab used Belleville washers; model used flat washer disks; likely adds compliance

# Slide 9 — Sensitivity and What Moves the Needle
- Parameters varied one‑at‑a‑time on medium mesh:
  - Bolt torque ±10% → peak stress ±6%, f1 ±3%
  - Fillet radius −0.2 mm → peak stress +7% at pad edge
  - E −5% (temperature or batch variability) → f1 −2.6%, strain +3.1%
  - Contact friction 0.2 → 0.1 → peak stress +4%, slip increases; with bonded tie, peak stress −9% but unrealistic load path
- Noted interaction:
  - Combining lower torque with lower friction produced convergence issues unless stabilization retained

# Slide 10 — What We Assumed and What We Didn’t
- Assumptions:
  - No fretting fatigue or wear considered; check is static margin and modal spacing only
  - Joints treated as dry; no oil contamination modeled
  - Thermal gradients neglected in static runs; modes swept with temperature‑dependent E (contradiction with Slide 4 “temperature‑independent data in static runs” statement acknowledged)
- Out of scope for this phase:
  - Random vibration response; to be addressed in Q4 with updated joint model
  - Shock environment; separate COTS bracket qualified by vendor

# Slide 11 — File Hygiene, Repeatability, and Version Gaps
- Model provenance:
  - Master CAE: AVB21_brkt_v3p2.cae; solver decks exported as job “avb21_nl_PT” and “avb21_modes”
  - Python build script (build_avb21.py) regenerates geometry cleanup, partitions, seeds, and steps
  - One exception: hole‑edge seed near lower pad set manually to 0.45 mm in the GUI for the fine mesh (not captured in script)
- Software versions:
  - Most nonlinear runs in Abaqus/Standard 2023 HF7; early coarse/medium convergence points came from 2022 HF4 (material card uses the same data, but contact stabilization defaults differ)
- Results vault:
  - Results and scripts stored in Git LFS (commit 7f1a9c3); test data in SharePoint “AVB21 Vibe Q3”
  - The slide deck’s summary table was composed from a mix of 2022 and 2023 runs; see note on Slide 6 about NLGEOM flag difference

# Slide 12 — What the Numbers Say (and Caveats)
- Static margins:
  - Using linear elastic peak stress (fine): 241 MPa vs σy = 503 MPa → “FoS = 2.09”
  - Using plasticity with local strain criterion (Neuber‑style hot‑spot): equivalent to 1.55 on yield at the lower hole
  - The executive summary line in the draft says “minimum FoS 1.35 at fillet,” which appears to reference the joint‑slip trial and not the baseline fine mesh
- Modal spacing:
  - Predicted f1 912 Hz vs measured 770 Hz; clearance to 750 Hz payload line only 2.7% by test, not 21% as implied by analysis
- Mesh stance:
  - Tip deflection converged acceptably; stress not strictly monotonic. Extrapolated 244 MPa suggests we are close, but element type consistency (tets throughout) should be verified since early coarse run notes mention a “hex trial”
- Contact and preload:
  - Documentation claims pretension carried through; a separate run deck shows bolts tied after step 2. This choice affects both stress and modes by O(5–15%)

# Slide 13 — Recommendations Before Design Freeze
- Unify the run set:
  - Re-run coarse/medium/fine in 2023 HF7 with identical options (NLGEOM, stabilization off after Step‑0), and document meshes with screenshots
  - Remove symmetry for a one‑to‑one modal correlation with the shaker setup
- Joints:
  - Include Belleville washers in the model (spring elements) and helicoil compliance; calibrate friction using torque‑tension coupon if available
  - Keep pretension active through load steps; avoid “bonded” shortcuts in production runs
- Validation:
  - Update correlation tables; don’t state “within 5%” unless comparing equivalent configs. Include joint‑slip model results alongside test
- Decision points:
  - If FoS based on linear stress remains >2.0 but modal test shows <5% clearance to payload line, consider local stiffener at web or accept lower clearance with waiver
- Documentation:
  - Fold manual mesh seed into build_avb21.py; lock solver version; tag a clean commit and archive

# Slide 14 — Open Items and Owner List
- Reconcile material model usage across runs (linear vs bilinear) — E. Chen
- Repeat modal with no symmetry and with washer springs — E. Chen + J. Patel
- Refresh convergence study with consistent settings — E. Chen
- Pull torque‑tension data from fastener lab — R. Diaz
- Update slide summaries to remove mixed‑run claims — PMO
