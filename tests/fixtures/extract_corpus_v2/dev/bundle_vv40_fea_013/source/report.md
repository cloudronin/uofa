# Slide 1 — Project overview and objective
- Topic: Structural FEA of a cementless femoral stem press-fit into a synthetic femur
- Decision needing support: show predicted bone–implant interface slip stays under 40 µm during early gait loading for Design Rev F vs Rev D
- Primary output metric: peak relative micromotion at medial–lateral proximal interface; secondary: stem von Mises stress and stem–bone contact pressure distribution
- Tools: Abaqus/Standard (primarily 2021 HF7; a subset on 2022 due to license queue), Python post-processing, in-house meshing scripts using HyperMesh 2020

# Slide 2 — How results will be used
- Claimed use (proposal): acceptance decision for Rev F based on absolute micromotion thresholds and safety margin > 20%
- Day-to-day practice: comparative ranking across candidate broach fits (S, M, L) and stem knurl patterns; not intended to set final clinical limits
- Risk posture: “moderate” patient risk per internal RPN 7×6; however, slide deck prepared for the gate review states “low impact” since surgeons can downsize intra-op
- Scope boundary: single-leg stance and heel-strike load cases only (3.0 kN joint reaction, 1.2×BW abductors); no torsional stumble, no dynamic oscillations

# Slide 3 — Geometry and physics encoded
- Geometry: CT-derived femur (DigitalFemur-42), Rev F Ti-6Al-4V stem with porous spray, press-fit 50 µm interference in proximal region
- Material models (as implemented):
  - Femur cortical: isotropic E = 15.5 GPa, ν = 0.32; cancellous: E = 420 MPa, ν = 0.3
  - Stem: Ti-6Al-4V; early model runs: linear elastic (E = 110 GPa, ν = 0.34); final runs note “bilinear plastic: yield 880 MPa, tangent 1.2 GPa” for stress stabilization
  - Liner not modeled; acetabular effects represented by applied loads
- Interface:
  - Stated plan: surface-to-surface contact, finite sliding, μ = 0.30; penalty normal stiffness auto-calibrated
  - Stability workaround in validation case: proximal third tied, distal two-thirds frictional (note contradicts “full-friction” statement in Methods)

# Slide 4 — Loads and constraints
- Loads:
  - Heel-strike: 3.0 kN joint reaction, oriented 20° anterior, 10° medial; abductor force 1.2×BW acting on greater trochanter patch
  - Bending moment at knee plane: 25 N·m applied through reference coupling (to represent ground reaction couple)
- Constraints:
  - Distal femur encastred over 40 mm length in some runs; others use elastic foundation springs (5 kN/mm) at condyles based on potting resin tests
- Nonlinearity:
  - Stated: NLGEOM on for contact and large rotations
  - Preprocessing note on RunSet_12: “Small strain OK; deactivates geometric stiffness for speed” (inconsistent with above)

# Slide 5 — Solver pedigree and code status
- Solver: Abaqus/Standard static general; full Newton with line search; default contact stabilization 0.0002 used in some runs
- Code-level test:
  - Vendor verification: linear elasticity, Hertz contact, and cantilever benchmarks passed in our 2021 install (max 0.6% error)
  - User material: UHMWPE UMAT mentioned in template but not used here; however, a custom field subroutine (USDFLD) used to grade porous layer stiffness—no dedicated unit test documented
- Version control:
  - 31 of 44 production runs on 2021 HF7; 13 runs on 2022 GA due to license server outage; “no impact expected” note without side-by-side confirmation

# Slide 6 — Mesh and element formulation
- Elements:
  - Stem: 10-node tets (C3D10) with minimum edge 0.6 mm near fillets; bone: C3D10, growth to 2.5 mm in diaphysis
  - Contact surfaces: quadratic facets; midside nodes retained
- Mesh sizes:
  - Coarse: ~480k elems; Medium: ~1.15M; Fine: ~2.9M
- Hourglass and distortion: not applicable (no reduced-integration solid elements used)
- Jacobian checks: 0 elements with negative volumes; 98 elements with aspect ratio > 5 near calcar—kept due to time constraints

# Slide 7 — Mesh refinement evidence
- Claimed in Methods: “peak micromotion change < 3% from Medium to Fine; acceptable”
- Convergence snapshots:
  - Peak micromotion (µm): 44.1 (Coarse), 40.7 (Medium), 37.4 (Fine)
  - Change Medium→Fine: 8.1% decrease, not 3%
  - Stem peak stress (MPa): 732 (Coarse), 789 (Medium), 846 (Fine)
- Reported GCI summary (heel-strike, Richardson p = 1.8 assumed):
  - Early slide notes say GCI = 1.8% for micromotion
  - Calculations in notebook show 6.8% using same datasets and p = 1.92 fit
- Decision: proceeded with Medium for sampling runs; Fine used only for headline plots

# Slide 8 — Boundary/contact behavior checks
- Contact pressure footprint compared qualitatively to ink-transfer from bench press-fit; general shape consistent proximally
- Slip hotspots:
  - FEA shows medial–proximal strip 30–45 µm; bench DIC shows peaks laterally at 25–35 µm
- Normal penalty:
  - “Auto” used in most runs; one stability run set kn = 1.0e8 N/mm, reducing predicted slip by ~22% vs auto (undiscussed in main text)
- Friction:
  - μ = 0.30 cited from literature; calibration sheet indicates μ adjusted 0.22→0.34 to match insertion force in Rig B

# Slide 9 — Comparison with physical tests
- Test setup: synthetic femur (Sawbones 3403), potting at distal 45 mm, Rev F stem, 2 kN axial plus abductor cable; DIC stereocams at 7 µm/pixel
- Validation metric: RMS micromotion over 8 markers at the proximal interface
- Results:
  - Document headline: FEA within 7% of mean DIC across both load cases
  - Detailed table (heel-strike only): FEA 38.6 µm vs DIC 45.5 µm (−15%); single-leg stance: FEA 26.2 µm vs DIC 28.4 µm (−7.7%)
- Independence:
  - Slide 3 states “independent dataset”; lab log shows same rig/operator used to tune μ from insertion force also ran the DIC comparison two days later

# Slide 10 — Inputs and parameter sourcing
- Bone properties:
  - Sourced from literature (Reilly, Carter): cortical 14–18 GPa; we selected 15.5 GPa; cancellous 0.3–0.6 GPa; we used 0.42 GPa
  - Alternative orthotropic set trialed (E1/E2/E3 = 12/15/19 GPa) in RunSet_07; not carried forward due to meshing pipeline limits
- Interference fit: nominal 50 µm proximal based on broach–stem drawings; QA found ±20 µm tolerance not modeled
- Loads: hip contact vector from Bergmann dataset downsampled; we used static peaks only

# Slide 11 — Sensitivity and uncertainty exploration
- Plan in protocol: Latin hypercube, N = 100, varying E_cortical, E_cancellous, μ, interference, abductor force ±15%
- Actual executed:
  - One LHS with N = 28 on Medium mesh (25 completed due to solver divergence at high μ)
  - “Corner” checks: 4 deterministic extremes
- Reported summary:
  - Slide note: “95% interval on peak micromotion ±12% about mean”
  - However, the 25-run set (filtered) shows coefficient of variation 9.6% and min/max excursions of −18%/+21% vs baseline; bootstrap 95% half-width = 14–16%
- Model-form sensitivity:
  - Tying proximal third shifts micromotion mean −19% compared to full friction; not included in the above UQ

# Slide 12 — Model credibility and applicability window
- Where it’s reliable:
  - Ranking changes between designs (Rev D vs Rev F vs Rev F-knurl tweak) under the same assumed μ and bone moduli
  - Qualitative footprint of contact pressure and slip zones for single-leg stance and heel-strike
- Where caution is warranted:
  - Absolute micromotion vs 40 µm threshold: mesh and contact-penalty dependence not fully bounded
  - Plasticity in stem: some runs used bilinear plastic; others purely elastic—peak stress comparisons across runs are not like-for-like
  - Distal constraint variant (encastre vs elastic supports) shifts micromotion by ~8–12%

# Slide 13 — Process control, files, and auditability
- Reproducibility:
  - All input decks and Python scripts archived in Vault PDM rev tags FEA-HIP-RevF-r3 to r7
  - Param sweeps tracked in MLFlow; 3 runs missing postproc artifacts due to disk quota
- Change log highlights:
  - r5: switched to 2022 due to license; r6: reinstated 2021; r7: activated bilinear plasticity above 880 MPa for stem only
- Peer review:
  - Internal read-across performed by Dr. C. Len; he authored the contact sensitivity section and recused from final sign-off per QA note, though his name appears on the approval slide

# Slide 14 — Open issues and next steps
- Resolve contradictions:
  - Standardize on either full frictional contact or remove tie constraints; re-run validation with consistent settings
  - Lock solver to a single version; repeat 5 key cases to quantify any drift
  - Complete mesh study with consistent p-fit; aim for <3% change Medium→Finer for micromotion
- Data separation:
  - Acquire a truly independent DIC dataset (different operator/day) after fixing μ via insertion-only tests
- UQ completion:
  - Execute planned N = 100 LHS on Medium and spot-check on Fine; propagate model-form options (contact penalty strategy) as a factor
- Decision use:
  - Until above are closed, position model as comparative only; do not use for pass/fail against the 40 µm criterion

# Slide 15 — Takeaways for the gate review
- The model captures general trends and can rank design variants under consistent assumptions
- There are inconsistencies between method claims and what was actually run (mesh independence, contact treatment, solver settings)
- Validation shows decent order-of-magnitude agreement, but absolute errors up to 15% exist in the higher-load case
- Recommendation: proceed with comparative design down-select, hold on absolute acceptance until the cleanup actions are complete
