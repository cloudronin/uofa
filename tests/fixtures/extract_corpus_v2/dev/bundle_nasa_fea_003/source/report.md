# Slide 1 — Purpose and scope
- Subject: Finite-element stress assessment of the LP-AB deployable antenna boom bracket for launch and on-orbit thermal exposure
- Goal: determine whether the current structural model is suitable to support bolt sizing, allowables roll-up, and protoflight test planning
- Context of use: pre-CDR sizing and selection of test load cases; not a fracture-certified record analysis
- Hardware: 7075-T73 machined bracket with Ti-6Al-4V inserts and four M6 fasteners into the boom hinge plate

# Slide 2 — What the model is (and isn’t)
- Geometry source: Bracket_RevE.step from PDM “Orionette/Structures/LP-AB/Rev E” dated 2026-03-17
- Modeling choices:
  - 10-node tetrahedra in the bracket (C3D10-type), bonded contact to inserts, tied constraints to bolt heads; preload represented as equivalent thermal shortening
  - Linear static for limit load cases; frequency extraction for first three modes
  - Local mesh densification around fillets R1.5 mm and underhead regions
- Exclusions: thread-detail omitted; adhesive shim layer approximated as 0.1 mm solid with 1.5 GPa E; thermal stress included only as uniform ΔT
- Intended outputs: von Mises at critical radii, bolt axial/shear, interface reaction loads, first mode > 350 Hz

# Slide 3 — Tools and solver setup
- Pre/post: Abaqus/CAE 2022HF3 on RHEL8; solver: Abaqus/Standard with NLGEOM=OFF for statics; Lanczos eigensolver
- Element formulations: quadratic tets (in bracket and inserts), beam elements for fastener shanks where load path is dominant
- Contact: tied constraints at countersink surfaces; no sliding contact modeled at insert-bracket interface
- Convergence criteria: residual force < 1e-6 of applied; max 50 iterations (not reached)
- Note: single precision runs used for quick sweeps; final results reported from double precision

# Slide 4 — Loads, boundary conditions, and materials
- Interface constraints: mounting flange nodes at the hinge plane fully fixed; symmetry not used
- Load cases:
  - Quasi-static launch: 22 g lateral, 11 g axial, per ICD LP-AB-ICD-22, applied as equivalent inertia to attached mass (0.94 kg)
  - Random vibration: converted to PSD-derived pseudo-static per NASA-HDBK-7004, envelope RMS 9.2 g; used only to derive bolt preload check
  - Thermal: ΔT = −85 C relative to assembly reference for cold survival sizing
- Materials:
  - 7075-T73 bracket per in-house coupon program TM-STR-2026-014: E = 73.8 GPa at −100 C, ν = 0.33, σy = 405 MPa
  - Ti-6Al-4V inserts per MMPDS-19, room temp: E = 113.8 GPa, σy = 880 MPa
  - Adhesive shim (epoxy): E = 1.5 GPa, ν = 0.35

# Slide 5 — Numerical checks (coarse/fine comparison)
- Mesh levels:
  - Level A: 46k nodes / 28k elements, min size 0.6 mm at fillets
  - Level B: 191k nodes / 120k elements, min size 0.25 mm at fillets
  - Level C: 412k nodes / 260k elements, min size 0.15 mm at fillets
- Metric: change in peak von Mises at R1.5 fillet under 22 g lateral
  - A → B: +2.7%
  - B → C: +1.9%
- Gradient recovery error indicator averaged over hot region: 3.2% at Level C
- Interpretation: mesh sensitivity appears acceptable; further refinement deferred due to runtime (C ~38 min)

# Slide 6 — Comparison with component load test (April)
- Static pull test at GSFC Bldg 7 on EM bracket, fixture 7-AB-FIX-03; load applied at tip adapter via whiffletree
- Correlation results:
  - Interface reactions (Fx): model 4.42 kN vs. test 4.56 kN (−3.1%)
  - Peak bracket strain at gage SG-3 (fillet): model 1880 με vs. test 1945 με (−3.3%)
  - First bending mode: model 412 Hz vs. experimental modal test 403 Hz (+2.2%)
- Acceptance gates for model-to-test: within ±5% for primary metrics — stated as met

# Slide 7 — Sensitivity and margins picture
- One-at-a-time sweeps:
  - Fillet radius ±0.25 mm: peak von Mises −7.8% / +9.4%
  - Insert stiffness ±20%: bolt axial load share −3.2% / +3.9%
  - ΔT range −120 C to −50 C: bracket stress +4.1% to +1.2% vs. baseline −85 C
- Short Monte Carlo (200 runs, Latin hypercube):
  - Variables: E_bracket (±3%), preload (±10%), fixture stiffness (±25%), mass (+5%/−0%)
  - 95th percentile peak von Mises at hot fillet: 362 MPa; mean margin on yield (MoS) = +0.10
- Bolt checks (NASGRO-like bearing/bypass not modeled): MoS (axial) +0.28, (shear) +0.41 under combined loading

# Slide 8 — Range of conditions we’re willing to claim
- Geometry applicability: valid for Bracket Rev E only; hole diameters and countersink angles per Dwg 11-210983 Rev D
- Environments covered:
  - Quasi-static combined accelerations up to 25 g resultant
  - Temperature from −120 C to +70 C modeled as uniform field
  - Mass growth up to +5% included via sensitivity bounds
- Exclusions from claim:
  - No explicit modeling of slip or gapping at insert interface; not intended to predict fretting or wear
  - Random vibration stress response not predicted (pseudo-static substitution only)
  - Not suitable for crack initiation or life analysis

# Slide 9 — Data pedigree and bookkeeping
- Inputs trace:
  - Loads from LP-AB-ICD-22 Rev B (signed 2026-02-12)
  - Material curves stored in vault under “TM-STR-2026-014” with temperature sweep CSVs (−140 C to +25 C)
  - Mass properties from CAD BOM “LP-AB-Assy Rev F”
- Configuration management:
  - FEA deck “LPAB_Bracket_CDR_v1.4.inp” tagged and frozen on 2026-05-02; results folder hash 6b3a… verified
  - Post-processing scripts in Git tag “lpab-fea-1.4” (Python 3.10, Matplotlib 3.7)
- Review artifacts: model checklists and run logs attached to JIRA STR-982, STR-1004

# Slide 10 — Independent review and team qualifications
- Reviewers: D. Morales (loads), S. Huang (structural analysis), K. Patel (test)
- Cross-check activities:
  - Hand calc of bracket as curved beam with notch Kt = 2.6 → peak stress 335–360 MPa at 22 g lateral
  - Second model built from CAD mid-surfaces by reviewer (shell-solid hybrid) reported peak stress within 6%
- Analyst experience: primary modeler has prior flight heritage on ORCA-2 deployment latch; Abaqus certified
- Independence: Review claimed as “independent” per project plan; conducted within the same structural group

# Slide 11 — What looks strong vs. what needs work
- Strengths:
  - Test correlation on key metrics appears near targets; first mode above requirement
  - Mesh refinement study indicates small change in hotspot stress across two refinements
  - Sensitivity runs bound the effect of reasonable tolerances and thermal shifts
  - Inputs and results labeled and stored with hashes; reproducibility largely demonstrated
- Gaps / to-do:
  - Insert-bracket interface modeled as tied; no check on potential local contact nonlinearity
  - Random vib treated as quasi-static; no stress PSD or fatigue screening
  - Only one fixture compliance value tried in “final” runs
  - Preload implementation as thermal trick not benchmarked against bolt elements for all cases

# Slide 12 — Inconsistencies observed by the panel
- Software/tool identification:
  - Slide annotations in Results_Ansys_2024R1.png cite “Ansys Mechanical 2024R1”, while this deck states Abaqus/Standard 2022HF3
- Mesh refinement evidence:
  - Earlier slide cites B→C hotspot change of +1.9%; an attached memo (STR-1004-attach2) reports energy-norm difference of 9.8% over the same region
- Material property usage:
  - Slide 4 claims −100 C coupon data (E = 73.8 GPa), but Figure “E_curve_roomtemp.png” used in SG-3 strain back-calc shows E = 71.0 GPa at 20 C from MMPDS, not cryo test
- Model-to-test fit:
  - Slide 6 summarizes within ±5%; the detailed correlation spreadsheet shows SG-5 residuals of +7–12% over the load sweep and a 5.5% bias in interface moment
- Boundary/fixture representation:
  - The static model boundary is fully fixed at the hinge plane per Slide 4; the test-correlation model notes six spring elements (k = 2.5 MN/m each) to mimic fixture flex
- Configuration control:
  - CM notes say “LPAB_Bracket_CDR_v1.4.inp” is frozen; some plots reference “Bracket_v1_FINAL_new2.cae” which is not present in the vault

# Slide 13 — Credibility bottom line (panel view)
- Intended use fit:
  - For sizing and establishing test levels, the current model is directionally correct, with adequate frequency and reaction predictions
- Where uncertainty bites:
  - Hotspot stress may be understated if tied contact hides local stress amplification; mixed E-values across figures affect strain matching
  - Energy-norm disagreement suggests discretization error could be larger than the von Mises delta implies
- Risk posture:
  - Margins near zero in Monte Carlo tails, combined with property inconsistency, argue for caution in using peak stress as a go/no-go metric
- Mitigations proposed before FRR:
  - Re-run with contact-enabled insert interface and bolt pretension elements for the top three load cases
  - Harmonize material curves to a single temperature set matching the test; re-do the strain correlation
  - Resolve tool/version discrepancy; regenerate all plots from the frozen deck and archive

# Slide 14 — Decision
- Decision: The LP-AB bracket finite-element model is accepted for preliminary design decisions and for setting protoflight static test levels, subject to the mitigations listed being completed before FRR. It is not accepted for final stress sign-off or for fracture/LCF assessments.
- Authority: Decision recorded by the Structures Working Group (chair: S. McKenzie) on 2026-06-21
- Conditions for later approval for use in certification:
  - Deliver a contact-enabled model with bolt pretension, show mesh study via energy norm ≤ 5% in hotspots
  - Reconcile material property temperature; repeat the model-to-test comparison with consistent E and documented fixture stiffness
  - Eliminate the tool/version mismatch; all figures must trace to the controlled input deck and hash
