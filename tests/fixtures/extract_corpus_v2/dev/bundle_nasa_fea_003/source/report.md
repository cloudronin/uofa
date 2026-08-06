# Gateway Avionics Mount Bracket FEA — Credibility Slide Deck (Rev C)

## 1) What we analyzed and why
- Component: Ti-6Al-4V L-shaped bracket mounting the EPS avionics box to the HALO rack
- Mission scenario: launch and on-orbit vibration; no re-entry or landing loads
- Primary questions:
  - Will local hot spots at the filleted corner and bolt pads exceed allowable during random vib?
  - Are first three modes clear of payload tone bands by at least 10%?
  - Do fasteners maintain clamp load with predicted joint slip kept negligible?

## 2) Geometry and level of detail
- CAD source: PTC Creo model HALO-PWR-AV-BRKT-1203, Rev H; imported via STEP AP214
- Features kept:
  - 0.5–1.5 mm fillets at internal corners; M5 through-holes with countersink
  - Electronics box mounting face scallops
- Features removed:
  - Cosmetic chamfers <0.25 mm; emboss text; surface scratches
- Note:
  - Early precheck stated “all fillets retained”; however, two stress plots show “<1 mm fillets suppressed” labels used for a quick run on 5/10 — those are not in the final archive but the images remain in the deck

## 3) Physics and analysis types
- Linear modal analysis (free–free and fixed-base) for first six modes
- Random vibration (PSD) response with Miles equivalent to check RMS stress and bolt slip risk
- Static checks: 1g orthogonal gravity with avionics mass simulant; cold-stow thermal not modeled as load
- Contact: frictional surface-to-surface at bracket–rack and bracket–box interfaces; μ = 0.2 assumed
- Temperature:
  - Stated goal: isothermal at 23 C
  - One parametric run used 80 C to gauge material softening (not carried into the reported margins)

## 4) Material data and sources
- Base alloy: Ti-6Al-4V, annealed plate, thickness 4.0 mm
- Elastic:
  - Slide 6 backup: E = 114 GPa, ν = 0.34 (MMPDS-17, Room Temp)
  - Materials note in calc log: E = 110 GPa used “to be conservative” (Abaqus material import)
- Plasticity:
  - Bilinear hardening: σy = 930 MPa, tangent = 1.2 GPa (from coupon test ATB-0423)
  - Stress–strain curve in Ansys library screenshot shows σy = 880 MPa at 0.2% offset
- Density: 4,430 kg/m^3; CTE not used in final loads
- Comment:
  - We did not include strain-rate effects; welds are absent; threaded inserts modeled as titanium with same properties

## 5) Discretization and element technology
- Meshing:
  - Bracket body: 10-node tetra (Ansys SOLID187), target size 1.5 mm; local 0.6 mm at fillets
  - Box and rack tie plates: 8-node hex where possible; transition via pyramids
  - Bolts: beam elements with pretension sections
- Element checks:
  - Jacobian > 0.6 for tets; aspect ratio < 5 in hot zones
  - Contact pair augmentation with small-sliding option enabled
- One sensitivity run used linear tets for speed on 4/28; not used for final results
- Contradiction to note: slide 9 caption states “Quadratic hex throughout”; that was true only for the coupon submodel, not the bracket assembly

## 6) Mesh refinement study
- Three nested meshes:
  - Coarse: ~220k DOF; Medium: ~680k DOF; Fine: ~1.45M DOF
- Reported changes (Medium → Fine):
  - First mode: +1.6%
  - RMS von Mises at fillet F2: +1.9% (from 184 MPa to 187 MPa)
- However:
  - Hotspot principal stress at bolt pad P3 changes +7.4% between Medium and Fine in the run tagged “Abaqus_6.14_Test,” which isn’t the final solver of record
  - The convergence plot on slide 11 shows <2% everywhere; the backup table in the calc log includes the 7% outlier
- Decision: proceed with Medium mesh for production runs due to schedule; fine mesh archived but not rerun with latest BCs

## 7) Loads, boundary conditions, and damping
- Mounting:
  - Six M5 fasteners to rack; four M5 to avionics box; 8 kN pretension each (per torque table)
- Vibration:
  - Spec: 20–2,000 Hz, 0.05 g^2/Hz flat from 80–350 Hz; overall 9.0 g RMS
  - Model input file comment block shows overall 7.5 g RMS; engineer note says “pre-qualification level” — inconsistency unresolved
- Modal damping:
  - Assumed ζ = 1% for modes 1–3, 0.5% otherwise
  - Test correlation slide states 1.5% used to match the 3rd mode peak
- Thermal:
  - Text claims isothermal; one figure labeled “+50 K gradient” appears in appendix A results, not in final margin calc

## 8) Software, run settings, and provenance
- Primary solver: Ansys Mechanical 2023 R2; sparse direct solver; single precision
- Secondary checks: Abaqus/Standard 6.14 for two cases (mesh study and modal spot-check)
- HPC: 16 cores, 128 GB RAM; wall time ~1.3 hr (modal), 3.8 hr (random vib)
- Traceability:
  - Param scripts in Python (PyANSYS) stored in GitLab repo HALO-AV-BRKT with tag v0.9.3
  - The exact production .dat for the random vib has hash mismatch vs v0.9.3 tag; local working copy used
- Quality gates:
  - Peer review documented for the preprocessor script only; no independent rerun performed end-to-end

## 9) Benchmarks and basic checks
- Patch test: bracket coupon submodel recovers uniform stress within 0.4%
- Rigid body modes: 6 free–free modes ~1e-6 Hz residual; OK
- Energy balance: contact work fraction <5% of total; OK
- Unit problems: simple cantilever beam reproduced closed-form within 2.1%
- Note: The cantilever was run in Abaqus example deck; not repeated in Ansys due to time

## 10) Correlation with shaker data
- Hardware: development bracket Rev F with mass simulator; 6 accelerometers on box, 2 strain gauges near fillet F2
- Sine sweep (fixed-base):
  - 1st bending mode: Test 318 Hz; Model 305 Hz (−4.1%)
  - 2nd mode: Test 512 Hz; Model 486 Hz (−5.1%)
  - 3rd mode: Test 731 Hz; Model 642 Hz (−12.2%)
- Random vib:
  - RMS strain at SG-2: Test 178 με; Model 166 με (−6.7%)
  - PSD peak at 340 Hz underpredicted by 14% unless damping raised to 1.5%
- Acceptance criterion in plan was “within 10% for first three modes”; slide 4 summary says “meets target,” but the 3rd mode misses that threshold

## 11) Inputs pedigree and handling
- Mass simulant: 5.2 kg per test; model uses 5.0 kg lumped mass for avionics box
- Preload torque: 5.5 N·m used in build; model used 5.0 N·m equivalent pretension
- Friction μ = 0.2 from legacy trade study; no on-article measurement
- Fastener stiffness from NASA-HDBK-1002; washers idealized as rigid
- CAD mismatch:
  - Test article had two extra wire tie holes near the leg; model omitted; effect assessed as negligible without quantification

## 12) Sensitivity sweeps and uncertainty notes
- One-at-a-time sweeps on:
  - μ from 0.1 to 0.3 → RMS hotspot stress changes −4% to +6%
  - Pretension ±15% → joint slip reserve varies by ±9%
  - E from 110 to 114 GPa → first mode shifts by +1.7%
- Monte Carlo not performed; tolerances on hole position and thickness not propagated
- Thermal variation:
  - Claimed “no effect at isothermal,” but the +50 K gradient run shifted mode 1 by −2.3% and raised fillet stress by 5% in that off-nominal case

## 13) Domain of use and limits
- Intended use:
  - Qualification and protoflight levels for this bracket geometry, Ti-6Al-4V, 4.0 mm thickness
  - On-orbit micro-vib excluded
- Not covered:
  - Shock (pyro) environment; acoustic loads; thermal-stress interaction during eclipses
  - Nonlinear plastic collapse not pursued beyond bilinear estimate
- Applicability caveat:
  - Results rely on the 9.0 g RMS environment; current model deck encodes 7.5 g RMS in one run — this must be reconciled before use for pass/fail

## 14) Results and safety margins
- Peak von Mises (RMS × 3 for 3σ check):
  - At fillet F2: 187 MPa RMS → 561 MPa at 3σ; below yield by 37% (using σy = 880 MPa)
  - If σy = 930 MPa (coupon), margin increases to 43%
- Bolt slip:
  - Minimum slip safety factor = 1.4 using μ = 0.2 and 8 kN preload
  - Alternate slide references 1.25 when μ = 0.15 is assumed; text summary cites “≥1.4”
- Modes vs tone bands:
  - Minimum separation 8% from a 500 Hz tone if using modeled 486 Hz second mode; with damping 1.5% the amplification criterion is still met

## 15) Assumptions and simplifications to track
- Interfaces are clean, dry; μ constant and unaffected by vib
- Avionics box treated as rigid with lumped mass; no internal flex
- All bolt holes perfectly round; no ovalization under load
- No preload loss due to embedment during random vib
- Two fillets <1 mm may be suppressed if using the legacy mesh; ensure latest mesh is used

## 16) Data management and reproducibility
- Inputs, meshes, and scripts stored at: EDMS Vault path HALO/AV-BRKT/FEA/RevC
- Run IDs:
  - Modal: MECH2023R2_RUN_0419_Med
  - Random vib: MECH2023R2_RUN_0508_Med (hash mismatch to tag v0.9.3)
- Repro steps documented in README.md; one step refers to Abaqus plugin for modal export that is not in the repo

## 17) Independent look and process checks
- Design peer (M. Patel) reviewed meshing strategy and boundary conditions checklist on 5/12
- No red-team independent model build due to schedule; plan deferred to CDR
- Shaker test plan reviewed by dynamics group; fixture resonance at 1,260 Hz noted but accepted

## 18) Open items and to-dos before CDR
- Resolve 7.5 g vs 9.0 g RMS discrepancy in the PSD load input and re-run the Medium mesh
- Lock down E and σy values; align solver library to MMPDS or to coupon but not both
- Reproduce the mesh-convergence study entirely in Ansys to avoid solver cross-talk
- Update damping to match test-derived ζ for the 3rd mode and assess impact on RMS strains
- Verify that all sub-1 mm fillets are indeed in the final mesh; purge legacy plots from the deck
- Recreate production run from a tagged commit and capture the run hash in EDMS

## 19) Bottom line for this review
- Strength:
  - Workflow mostly transparent; test data available; first two modes within ~5% of test
  - Hotspot stresses show reasonable stability between Medium and Fine meshes in Ansys
- Gaps/ambiguities:
  - Mixed solver evidence for mesh behavior at one hotspot
  - Conflicting material properties and damping
  - Load level inconsistency (7.5 vs 9.0 g RMS)
  - 3rd mode ~12% low vs test; acceptance summary in slide 3 is overly optimistic
- Recommendation:
  - Treat current results as preliminary; do not finalize margins until the above open items are closed
