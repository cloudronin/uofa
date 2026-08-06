# FEA Credibility Brief — Avionics Bracket for Lunar Hopper

- Audience: IPT design, loads & dynamics, mission assurance
- Scope: Structural assessment of the CFRP–aluminum avionics bracket through random vibe, thermal gradient, and bolt preload. Model used for margin sign-off and hardware orientation rules.
- Tools/versions: Abaqus/Standard 2023 HF6; Python post v3.9; CAD from NX 2206; Git repo ms-avionics-bracket
- Decision needed: Is the current finite element model trustworthy for MRD Rev E load cases without additional testing?

## What problem we actually solved

- Geometry: 7075-T7351 aluminum bracket bonded to CFRP deck via four M6 titanium fasteners and epoxy film adhesive (FM300-2); filleted cutouts to reduce mass; 4 strain gauge boss pads
- Load cases analyzed:
  - Random vibration, 20–2,000 Hz, GRMS 9.1, proto-qual profile; 60s/axis
  - Thermal soak: −35 C to +55 C, through-thickness ∆T ≈ 18 C (deck warmer)
  - Bolt preloads per torque target: 8–10 kN per bolt (K=0.2 nominal)
- Outputs used by design: maximum principal at fillets, adhesive peel/shear, local bearing in CFRP insert, fastener axial and slip, first three natural frequencies in mounted orientation

## Modeling details we thought through (and a few we didn’t)

- Simplifications:
  - Omitted avionics box internals; represented as a 1.8 kg rigid body tied to mounting plane; mass/inertia from CAD
  - CFRP deck: homogenized orthotropic shell (ABD from vendor sublaminate test), tied to bracket via cohesive layer
  - Cables and harness clamps ignored; 0.1 kg distributed mass lumped on bracket web
- Contact and fasteners:
  - Surface-to-surface contact between bracket foot and deck; friction coefficient 0.23 (dry Ti–Al per MIL-HDBK-60)
  - Bolts modeled with beam elements and pretension sections; shank shear stiffness matched to Ti-6Al-4V
  - Holes modeled as geometric cutouts; no washer stiffness unless otherwise noted

## How we loaded and constrained it

- Random vibe: Base acceleration PSD on deck nodes; modal-based approach (eigs to 2,500 Hz), then modal dynamic, post via Miles-ish peak estimator; damping 2% structural
- Thermal: Uniform deck warm bias; bracket CTE per material card; adhesive CTE equal to resin
- Preload: Pretension sections set to 9 kN each using bolt load step; then locked prior to dynamic
- Boundary: Deck edges simply supported proxy (SPRING1 k=1e8 N/m translational), rotations free
- Note:
  - For fatigue screening, used von Mises RMS × 3σ peak; not yet rainflow-counted

## Solver strategy and numerical settings

- Steps:
  - Step 1: Pretension (static general), stabilization 0.0002, NLGEOM=ON, auto time stepping
  - Step 2: Frequency extraction (Lanczos), 0–2,500 Hz, 800 modes
  - Step 3: Random response (Modal), 2% modal damping, PSD integration
  - Thermal: separate linear static with temp field; then sequential structural
- Elements:
  - Bracket solid: C3D10, min edge 1.2 mm near fillets, 3.5 mm bulk
  - Cohesive adhesive: COH3D8, 0.18 mm thickness, BK law G_Ic=320 J/m^2, G_IIc=1,100 J/m^2
  - Deck: S8R continuum shells; 4 plies equivalent ABD
- Convergence:
  - NL step force residual < 1e-3; contact enforcement penalty default; no cutback limits hit

## Mesh checks and stress hot-spots

- Initial mesh sensitivity: 0.1–0.4 mm local size at fillet; stress at notch A changed −2.6% between last two meshes (1.92 vs 1.87 of allowables)
- Element aspect ratios < 5; Jacobian > 0.7; 6 elements through adhesive thickness
- Alternate run (5/29 nightly) with smaller stabilization showed 6.7% increase at notch A; team attributed to contact chattering; not yet re-run with refined contact
- GCI not computed; used the “stabilized value” heuristic across three local refinements
- Local averaging with 0.6 mm patch used for reporting; raw nodal maxima 12–18% higher

## Where the numbers came from (materials and joints)

- Aluminum bracket:
  - Material card pulls from MMPDS-17, 7075-T7351, room-temp, mean–3σ; E=71 GPa, σ_y=434 MPa, ν=0.33
  - Temperature knockdowns per MIL-HDBK-5J used above 50 C
- Adhesive:
  - FM300-2 cohesive parameters back-calculated from supplier DCB/ENF at 23 C; rate effects ignored
- CFRP deck:
  - ABD from vendor “Panel Rev C” 0/90/±45s; 2% moisture; shear coupling neglected
- Fasteners:
  - Ti-6Al-4V, coarse thread; preload K-factor 0.18–0.22 spread
- Note:
  - Two property decks exist in repo: mat_v17 (current) and mat_vendor (includes vendor test at 55 C with 7% lower E); last two dynamic runs point to mat_vendor in the .inp include list

## Comparison to reality (bench data)

- Modal tap test on EQM stack (bracket + dummy mass), free-free: 
  - Measured: 1st bending 82 Hz, 2nd torsion 146 Hz, 3rd bending 241 Hz
  - Model (with added mass 1.8 kg): 96 Hz, 152 Hz, 232 Hz
- Correlation comments:
  - Within 5% declared for 2nd mode; 1st mode high by 17% until we added 0.12 kg epoxy mass at cable boss in model; that brought it to 87 Hz
  - 3rd mode within 4% if deck springs reduced by 30% (softer boundary)
- Static pull at bolt #3 (bench): strain at boss pad 710 µε at 5 kN; model predicted 665 µε (−6.3%)
- Random vibe: no shaker data yet; compared PSD peaks to past JPL bracket data set; qualitative similarity only

## Sensitivity sweeps and what moves the needle

- One-at-a-time sweeps:
  - Bolt K-factor 0.18–0.22 changes peak stress at notch A by ±4%
  - Adhesive shear modulus ±20% changes peel max by ∓8%
  - Damping 1–3% shifts RMS response by ±12%
- Stochastic runs:
  - Slide deck (rev C) cites 50-point Latin Hypercube on 6 variables; archive shows 12 samples actually completed due to queue limits; spread in notch A stress ±9.5% 95th perc
- Screening indicates boundary spring stiffness and added cable mass dominate below 200 Hz

## Assumptions and caveats that actually matter

- Linear material behavior for aluminum up to 0.8 σ_y; no plasticity in random response
- Small sliding contact for foot–deck interface in dynamic; tie constraints at bolt grip
- Sequential thermal-structural (no full thermo-mechanical coupling)
- Adhesive failure not propagated; damage used for initiation only
- Harness mass represented as distributed shell load; no local clamp stiffening

## Process controls and traceability

- Versioning:
  - Git tags: fea_bracket_v1.3 (used for plots); however, last-minute bolt preload tweak (8.5→9 kN) on local workstation not pushed before run 230605_01
- Tools QA:
  - Abaqus/Standard 2023 HF6 validated via textbook plate bending; RMS error < 2% vs closed form
  - Solver deck checked by checklist (Rev B); 2 of 24 items deferred (cohesive traction law sign, damping units)
- Reproducibility:
  - Run matrix stored in runs.yaml; but two runs (230529_03, 230605_01) missing the exact PSD file hash
- Independent review:
  - Peer walkthrough held 6/2; assigned to Structures (D. Shah). Due to travel, sign-off annotated by model owner; formal IV&V rescheduled to next gate

## Are we inside the lane of intended use?

- Geometry: Current model matches CAD Rev G; fillet relief added in Rev H not included (reduces stress by ≈3% per hand calc)
- Loads: Using proto-qual PSD; flight acceptance PSD is 15% lower; margins reported against proto-qual
- Environment extrapolation: Used room-temp properties in random response; thermal knockdowns applied in separate run; combined effect not re-checked
- Mounting: Model assumes flat deck; TVAC shows 0.15 mm deck warp near bolt #2; not yet represented

## What looks solid vs what needs help

- Looks solid:
  - Contact/bearing trends vs static pull test within ~7%
  - Element quality reasonable; fillet stress pattern consistent with notch theory
  - Mode shapes rank-ordered reasonably with tap test after added cable mass
- Needs help:
  - Conflicting material include (mat_vendor vs mat_v17) across runs
  - Nonlinear step used for pretension; dynamic step sometimes run with NLGEOM=OFF (see 230529_03)
  - Mesh sensitivity inconclusive at notch A due to stabilization dependence
  - UQ sampling count inconsistent with slide claim; tails underexplored
  - Preload sources disagree: measured clamp loads not yet used; torque-based placeholders remain

## Actions before we bet the mission on this

- Re-run mesh refinement with contact stabilization ≤1e-4 and local h=0.08 mm at notch A; document GCI-like estimate
- Lock material deck (mat_v17) or justify vendor deck; ensure temperature-dependent E in dynamic or bound with two runs
- Update bolt preload to measured values from torque–turn test (K from instrumented bolt), not nominal
- Finish 40 additional LHS samples or revert to deterministic margins with explicit conservatism
- Add Rev H fillet relief; check margin shift
- Complete independent review with someone not on the modeling team; freeze inputs with Git tag fea_bracket_v1.4 and archived PSD hash

## Backup: quick numbers the team keeps asking for

- Margins (proto-qual, current model):
  - Peak principal at notch A: 1.87 × allowables (with 0.6 mm averaging); raw nodal 2.08 ×
  - Adhesive: max peel 0.62 × GIc-based onset; shear 0.55 × GIIc onset
  - Bolt axial (pretension + dynamic): 11.4 kN peak vs 21 kN proof
- First three modes (mounted):
  - 96, 152, 232 Hz (model); 82, 146, 241 Hz (test free-free proxy)
- Sensitivity ranking (qualitative): boundary stiffness > harness mass > damping > preload > adhesive Gc
