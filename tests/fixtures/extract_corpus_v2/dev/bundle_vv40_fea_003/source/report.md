# FEA Credibility Readout — Reaction Wheel Bracket (RW-12) for LEO Bus

- Presenter: M. Ortega, Structures
- Date: 2026-08-06
- Model owners: A. Chen (analysis), R. Singh (test)
- Software: Ansys Mechanical 2024 R1; nCode Glyphs for post
- Scope: Static and modal behavior of 7075-T6 reaction wheel bracket with M6 bolt interface

## Slide 1 — What we’re deciding
- Intended use
  - Use the simulation to sign off: (1) first bending mode above 250 Hz, (2) local stress under combined thrust and torque loads within allowables at 23 C
  - Drawing release depends on this; vibe qualification uses this as pre-screen
- Decision question
  - Is this FEA setup reliable enough for release decisions on bracket geometry Rev C without additional rework?

## Slide 2 — Operational context and thresholds
- Service environment
  - LEO thermal range −20 C to +50 C, 50 mN·m wheel torque spikes, radial wheel imbalance loads up to 500 N worst-case
  - Attachment: three M6 class 12.9 bolts into titanium tray inserts; thin shims not modeled
- Acceptance targets for this model
  - First mode prediction within ±10% of bench data (free–free with bolts snug)
  - Peak equivalent stress within ±15% of strain gauge reading at 23 C under 450 N radial force and 0.04 N·m torque
  - Safety factor to yield ≥ 1.5 based on model stress when compared to A-basis 7075-T6 at room temperature

## Slide 3 — Modeling approach (physics and numerics)
- Analysis types
  - Linear static for combined radial load + torque; linear eigenvalue extraction for first five modes
  - Small strain; contact pairs with no separation and 0.2 friction at footpad–tray interface
- Solver controls
  - Static: sparse direct, displacement residual 1e-6 m, force residual 1e-6 N
  - Modal: Block Lanczos, 8 modes requested, consistent mass matrix flagged ON in the setup
  - Note: The batch log from 2024-07-14 shows “automatic mass matrix selection” for job RW12_modal_C2, which enables selective lumping at part interfaces

## Slide 4 — Geometry, constraints, and loads
- Geometry
  - Bracket: 7075-T6 machined; fillet radii 2.5 mm nominal at leg roots; pocketing per Rev C
  - Fasteners: three M6 with modeled shank; threads not represented; head contact modeled
- Boundary conditions and loads
  - Bolt pretension specified as 12 kN per bolt using PRETS179; pad-to-tray contact frictional
  - External loads: 500 N radial at wheel CG node, applied via rigid spider; 0.05 N·m torque about wheel axis
- Notes from test team
  - Torque transducer logs indicate installation torque corresponding to 8–9 kN clamp load; preload relaxation of ~10% after 24 hrs
  - The sensitivity sweep inputs table lists 10 kN as the “baseline” preload for Rev C, while the summary slide references 12 kN

## Slide 5 — Materials and properties
- Primary material
  - 7075-T6: E = 71 GPa; ν = 0.33; ρ = 2810 kg/m^3; σ_y,A-basis = 503 MPa at 23 C (MMPDS-17)
  - Temperature dependence neglected; note from materials: drop in yield ~10% at 50 C, stiffness change < 3%
- Inserts and fasteners
  - Inserts: Ti-6Al-4V, standard data; bolts modeled as steel, E = 200 GPa
- Data provenance
  - Property cards from Vault rev MATS-7075-17; however, the modal-only trial run RW12_modal_C0 (2024-06-28) pulled 6061-T6 from the library (E = 69 GPa), then was used for the early “312 Hz” headline without re-running with 7075

## Slide 6 — Discretization and local detail
- Meshing
  - Quadratic tetra (SOLID187) with midside nodes retained; 1.2 mm elements in filleted legs, 3.5 mm elsewhere; 10 elements across pad thickness
  - Contact augmented with CONTA174/TARGE170; 0.02 penetration tolerance
- Element quality
  - Skewness < 0.7, Jacobians > 0.6 reported; 2% elements flagged with warpage warning in leg–base transition
- Mesh refinement exercise
  - Three levels: 720k, 1.34M, 2.05M DOF; peak stress at fillet reported as 286, 292, 294 MPa respectively (≤ 2.8% change)
  - The appendix plot “mesh_independence_revC.png” shows a 6.1% change between the two finest meshes when the contact stiffness was synchronized; only the coarse-to-medium used the same contact settings

## Slide 7 — Numerical checks and solver stability
- Static runs
  - Nonlinear contact stabilized with small normal stiffness regularization (FKN = 0.3) and two load steps; convergence within 7 iterations per step
  - Reaction force balance within 1.1% of applied resultant
- Modal runs
  - First mode reported at 305 Hz (RW12_modal_C2), 298 Hz (RW12_modal_C1, 6061 trial), and 257 Hz (RW12_modal_boltsFixed) when bolts were fully clamped as fixed constraints
  - Mass participation in first three modes > 85% in primary direction; however, the C2 log shows “reduced mass matrix at contact regions,” which contradicts the setup sheet calling for consistent mass

## Slide 8 — Bench comparison and test tie-outs
- Test configurations
  - Free–free modal hammer test on Rev C bracket mounted via three M6 bolts torqued to 9 N·m; tri-axial accelerometers near leg roots; room temperature 23 C
  - Strain gauge (rosette) at inner fillet of one leg; static load via pulley to 450 N and 0.04 N·m torque
- Results
  - First bending mode: test 312 ± 5 Hz; FEA C2 (7075) reports 305 Hz (−2.2%); early C0 run reported 312 Hz but used 6061; “boltsFixed” configuration yielded 257 Hz (−17.6%), not comparable to free–free test
  - Strain at gauge: measured 820 µε; FEA predicted 700–760 µε depending on contact settings (−7% to −15%); summary page cites “within 5%,” which reflects a single step at 400 N, not 450 N
  - Damping not modeled; test Q ~45; not used in modal correlation

## Slide 9 — Input sensitivity and spread
- Parameters varied
  - Bolt clamp load: 8–12 kN; friction coefficient 0.15–0.3; leg fillet radius ±0.25 mm; pad thickness ±0.5 mm
- Observations
  - Frequency sensitivity: ~12 Hz/kN to preload from 8→10 kN, flattening above 10 kN; ~−18 Hz per −0.5 mm pad thickness
  - Stress sensitivity: +28 MPa per −1 kN preload; +35 MPa per −0.25 mm fillet radius
- Takeaways
  - Initial readout slide states “preload dominates frequency,” but the tornado diagram in the workbook shows pad thickness as the largest contributor to frequency swing in the analyzed range
  - Combined input uncertainty (assuming independent normals) yields ±9% for stress, ±6% for first mode; the cover sheet quotes ±5% global uncertainty for both without showing the preload variance used

## Slide 10 — Software controls, repeatability, and review
- Toolchain and configuration control
  - Ansys 2024 R1; element formulations locked via APDL snippets saved under Vault AE-RW12-SUPP-RevC
  - Scripts for load cases in Git tag rw12_release_c; solver logs archived
- Checks and peer review
  - Sanity check: standard cantilever beam benchmark matched closed-form within 1.2%
  - Peer check: geometry and BCs reviewed by J. Patel on 2024-07-18; noted missing pretension release step; comment resolved in C2
  - Exception: job RW12_modal_C2 ran on workstation WS-17 using a local contact stiffness macro not in the repo; re-run with repo macro pending
- Traceability
  - Input deck hash recorded in change log; one early modal result in slide deck references a run for which the hash does not appear in the log

## Slide 11 — Limitations, scope boundaries, and extrapolation
- Not modeled / out of scope for this readout
  - Thermal dependence beyond 23 C; micro-slip under random PSD excitation; thread compliance; shim plates between pad and tray
  - Plasticity and mean stress correction for fatigue; only elastic response considered
- Applicability notes
  - The opening context slide states “modulus stable across flight range,” yet materials note shows up to 3% E variation and ~10% yield drop at 50 C
  - Residual stresses from machining ignored; surface finish of fillet measured Ra 1.8 µm not used in notch factor
  - Extrapolation to vibe qualification is not supported here; separate vibe model planned

## Slide 12 — Summary of evidence and open items
- Strengths
  - Geometry and BCs largely reflect test; modal free–free correlation within about 2–3% when like-for-like
  - Static strain predictions bracket test within ~7–15% when preload is matched to measured
  - Sensitivity mapping identifies key levers (preload, pad thickness, fillet)
- Weaknesses and contradictions to resolve
  - Early headline modal number tied to a run with 6061 properties; inconsistent mass treatment noted in logs
  - Mesh comparison claims <3% but contact settings differed between meshes; unrefined contact stiffness biases stress by ~5–6%
  - Baseline preload stated as 12 kN in setup while tests and ranges center on 8–10 kN; acceptance bands in cover sheet assume lower preload variance than observed
  - One run used a local macro outside version control; traceability gap

## Slide 13 — Recommendation and decision
- Recommendation from Structures
  - Accepted for predicting first bending frequency within ±10% and bracket elastic stresses within ±15% at room temperature for loads up to 500 N radial and 0.05 N·m torque, subject to:
    - Using 7075-T6 property set MATS-7075-17 and consistent mass in modal
    - Setting bolt pretension to 10 kN in the model unless measured clamp load is available; report sensitivity with ±1 kN band
    - Re-running RW12_modal_C2 with repository contact macro and posting updated log/hash before drawing release
  - Not accepted for thermal derating, fatigue life, or random vibration sign-off
- Decision
  - Approved for use in design release of Rev C for the above-stated context of use; decision by Chief Engineer (S. Alvarez), contingent on posting the re-run logs and hashes noted
- Next steps
  - Close the two open items by 2026-08-12; initiate separate vibe model set-up (not part of this credibility readout)
