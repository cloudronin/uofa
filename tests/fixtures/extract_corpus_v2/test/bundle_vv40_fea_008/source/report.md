# Slide 1 — Project snapshot
- Topic: Structural FEA of a Ti-6Al-4V locking plate and spacer assembly for proximal tibia fractures
- Decision at hand: go/no-go for design freeze before fatigue test lot release
- Acceptance target (internal): peak von Mises stress below 780 MPa at 1.5x nominal bending moment; screw hole edge strain under 0.5%
- Safety relevance: if underpredicted, could drive early crack initiation under AO/ASTM F382-like four-point bending
- Tools noted: Abaqus/Standard (2021HF4) for primary runs; brief cross-check in Ansys Mechanical 2023 R1

# Slide 2 — Geometry, fixtures, and load case
- CAD from Rev D model; fasteners modeled explicitly (M5 locking screws), spacer press-fit into slot
- Plate length 150 mm; thickness 4.5 mm; filleted slots radius 1.25 mm; thread geometry simplified to cylinders with tied DOFs
- Bending rig represented as two 20 mm diameter anvils at 60/140 mm span (four-point equivalent)
- Boundary representation:
  - Early scoping: both outer anvils as encastre surfaces; inner anvils apply 2.4 kN each via rigid bodies
  - Final setup note states: distal anvil allowed sliding in axial direction to avoid parasitic shear (contradiction with “encastre” above)
- Load magnitude: 3.6 kN total to represent 1.5x nominal, applied quasi-statically over a single static step

# Slide 3 — Materials and constitutive choices
- Plate and spacer: Ti-6Al-4V ELI; room-temperature test cert mean E = 114 GPa, ν = 0.34; σ0.2 = 820 MPa; ultimate = 900–930 MPa
- Model variant A: isotropic elastic–plastic with multilinear hardening fit to coupon curve (Ramberg–Osgood α=0.015, n=6.2)
- Model variant B: linear elastic only (used for fast mesh scoping per notebook entry on 2026-05-02)
- Temperature dependence disabled; however, several comparison tests were run at 60 ± 3°C saline (see Slide 9), which may matter
- In the consolidated results table, E is referenced as 110 GPa (earlier slides use 114 GPa) — inconsistent parameterization

# Slide 4 — Contacts, joints, and pretension
- Plate–anvil: surface-to-surface, “hard” contact in normal; friction coefficient initially 0.20 (based on dry titanium–steel)
- Later rerun used frictionless for solver stability; the accompanying figure label still indicates µ = 0.20 (mismatch)
- Screw head–plate interface: tied, no micro-slip modeled; threads not represented, load transfer via bonded cylinders
- Spacer–plate: interference fit modeled with 12 µm radial overbuild; penalty contact, kN/mm = 50; reported peak penetration < 3 µm
- Bolt preload: 1.5 kN per screw in preload step; comment in run log for Case R07 shows preload step skipped due to “equilibrium achieved” — unclear if carried into main step

# Slide 5 — Element types and meshing strategy
- Elements: C3D10 on curved features; C3D8R elsewhere with hourglass control set to enhanced; selective refinement around filleted slots and screw holes
- Nominal element size:
  - Coarse: 1.6 mm global; 0.4 mm in notches; ~310k elements
  - Medium: 1.1 mm global; 0.3 mm in notches; ~520k elements
  - Fine: 0.8 mm global; 0.2 mm in notches; ~930k elements
- Quality: min Jacobian > 0.55; max aspect ratio 9.7; average skew 0.28
- Mesh refinement exercise:
  - Report header claims “<2% change in hotspot stress between last two meshes”
  - Table in notes shows max principal at notch: 742 MPa (Med) vs 796 MPa (Fine) — a 7.3% increase; hotspot location also shifts by 0.6 mm

# Slide 6 — Solution controls and convergence
- Nonlinear geometry:
  - Setup sheet: NLgeom = ON to capture contact-induced stiffening
  - Input deck for Case R07 shows NLgeom = OFF; residual force norms met in 7 increments — conflicting settings
- Incrementation: automatic, initial 0.1, min 1e-5, max 0.2; line search enabled
- Convergence: displacement and force tolerances default; contact stabilization 0.2% of reference force in first increment only
- Riks arc-length was “evaluated but not needed” per summary; no supporting file included
- For cross-check in Ansys: used Newton–Raphson with program-controlled line search; 50 equilibrium iterations total

# Slide 7 — Software pedigree and numeric confidence
- Code pedigree:
  - Primary: Abaqus/Standard 2021HF4; plugin “fe-safe/abaqus” visible but not invoked
  - A figure footer on Slide 10 shows “Abaqus 2023.1” watermark — suggests at least one run executed with a different solver version
- Basic code checks: plate-only coupon passed patch test (membrane/shear); single-element bending test reproduces E within 0.8%
- Known issues: SR-ABQ-11873 (contact chattering with penalty/stiffness scaling) — mitigation via small stabilization as noted
- Hardware repeatability: rerun Case R05 on two machines differed in peak stress by 0.6% (likely mesher randomness from seeding)

# Slide 8 — Physical test program used for comparison
- Test rig: four-point bending per modified ASTM F382; fixture spans 60/140 mm; Instron 8872 with 25 kN load cell
- Instrumentation: 6 strain gauges around critical slot; 1 DIC view at 5 MPx, subset 21; thermocouple on plate midspan
- Protocol:
  - Room temperature tests at 23 ± 2°C and humidity 40–55% RH
  - A separate set ran in 60°C saline to evaluate worst-case (creep/softening); loading rates 5–10 N/s
- Data handling: strain filtered with 50 Hz low-pass; image calibration 13.2 px/mm; 3 out of 22 runs excluded due to gauge debond
- Note: the “validation matrix” tab labels the saline runs as “not used,” yet plotted overlays on Slide 10 include saline data curves

# Slide 9 — Agreement between simulation and measurements
- Global response:
  - Load–deflection slope predicted within 3.5% of mean test slope at room temperature (FEA 1.82 kN/mm vs test 1.88 kN/mm)
- Local fields:
  - At gauge G3 (slot edge): FEA strain 0.41% vs test 0.44% at 3.6 kN, −6.8% difference
  - At gauge G5 (opposite surface): FEA 0.12% vs test 0.09%, +33% difference
  - Summary line on this slide states “all gauges within 5%,” which contradicts the G5 delta above
- Peak stress:
  - FEA (Fine mesh, plastic): 796 MPa at inner radius; corresponding test-based hotspot estimate via Neuber gives ~720–760 MPa
  - The alternative elastic-only model underpredicts by ~12% vs plastic model at the hotspot but matches far-field strain better
- Spatial pattern: DIC hotspot aligns within 0.8 mm of FEA max; saline tests show +8–10% strain vs room temp; FEA did not include temp effects

# Slide 10 — Input variability and influence
- Considered scatter:
  - E ~ N(114 GPa, 3% COV) per certs; µ plate–anvil assumed U[0.15, 0.25]; preload per screw N(1.5 kN, 10% COV)
  - Spacer interference U[6 µm, 18 µm]; anvil placement tolerance ±0.5 mm
- Sampling:
  - Latin hypercube, 120 samples on medium mesh; response surface fit R^2 = 0.92 for peak stress, 0.88 for G3 strain
- Sensitivities:
  - Ranked (most to least): µ, preload, interference, E, anvil span offset
  - Slide footnote says “E dominates peak stress” — inconsistent with Sobol indices in the workbook (µ first, total index 0.47)
- Propagated outcome:
  - 95th percentile hotspot stress 835 MPa (plastic model, medium mesh)
  - A separate panel lists “P95 = 790 MPa” without clarifying that value comes from the elastic-only sweep — mixed provenance

# Slide 11 — Scope alignment and how far we extrapolate
- Intended use: rank margin to yield for static bending; inform go/no-go before running 10M-cycle fatigue
- Model limitations stated:
  - Threads omitted; head–plate bond idealized; no micro-slip, no fretting wear
  - No residual stress from machining or anodize; no corrosion pits
  - Thermal effects not included though warm saline tests exist; rate dependence ignored
- Representativeness:
  - Fixture friction and compliance partially captured; yet boundary condition slide earlier toggles between fixed and sliding anvils
  - Geometric tolerances applied only as scalar offsets; no hole ovalization modeled

# Slide 12 — Evidence strength, reviews, and traceability
- Internal peer review on 2026-06-19: “suitable for preliminary decision-making; revisit contact and mesh near slot”
- Checklist completed (rev C), hyperlinks to two run folders resolve; third link “R07_fine_NL_on” broken
- Risk posture:
  - Summary states “medium consequence, low likelihood” if FEA underestimates stress
  - Hazard log HL-27 cites “uncertain BC fidelity” as open item; classification pending — tension between these two statements
- Reproducibility: seed files attached for medium mesh; fine-mesh seeding script missing; software version watermark inconsistency noted

# Slide 13 — Bottom line and actions
- Confidence call:
  - Global stiffness match is solid
  - Local stress/strain match is mixed; some gauges exceed the stated 5% window; mesh trend not fully monotonic
  - Inputs and fixtures require tighter definition (contact, preload carryover, anvil constraint)
- Near-term fixes (2 weeks):
  - Lock solver settings (NLgeom ON); re-run fine mesh with µ = 0.20 and with frictionless to bracket; ensure preload step completion
  - Add one finer mesh level at 0.15 mm notch sizing; compute stress extrapolation vs 1/√N
  - Align material E to 114 GPa across all decks; enable temperature-dependent E for 23°C and 60°C what-if cases
  - Resolve software version drift; archive .inp and .odb with hashes
- Gate decision recommendation: proceed to limited fatigue screening but do not freeze geometry until BC and mesh findings are resolved
