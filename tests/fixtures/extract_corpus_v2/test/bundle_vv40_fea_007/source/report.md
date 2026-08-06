To: L. Parsons, Mechanical Lead
From: S. Chao, Simulation
Date: 2026-08-06
Subject: Status check — plate-screw construct FEA vs. bench results (Rev D) 

Short take
- The current nonlinear static model of the L4–L5 lateral plate with 5.5 mm screws is behaving predictably and is close enough to the lab numbers to support design screening and setting a preliminary proof load. Stiffness tracks within 7% of the 4‑point bend fixture data; stress at the screw head fillet is 10–15% below the strain-gage inference. Known gaps are mostly around how we represent screw seating and assembly variability.

What we built
- Geometry: Rev D plate and 28 mm screws from CAD; threads retained on the first five pitches near the head for stress capture, shank threads replaced by an equivalent cylinder. Countersink and head undercut modeled as-designed. No bone blocks or cages in this model; we’re focused on the construct piece-part response in the fixture.
- Materials: Ti‑6Al‑4V ELI (AMS 4930) with E = 114 GPa, ν = 0.34. Plasticity: bilinear kinematic, σy = 910 MPa, tangent modulus = 1.2 GPa. Screws use the same card. All units mm‑N‑s.
- Contacts: plate–screw head undercut and head–countersink frictional (μ = 0.2), augmented Lagrange. Shank–plate clearance contact set to rough (stick) to prevent nonphysical interpenetration in edge cases. Bonded thread engagement at the first five pitches as a practical surrogate.
- Loads/BCs: Four‑point bend mimic per our lab rig: rollers at 20 and 60 mm span; load applied via remote displacement at the upper rollers to 1.5 mm total crosshead travel. No explicit preload in screws. Small‑strain turned on; large deflection off (peak rotation < 1.5 deg).
- Elements/solver: SOLID187 (quadratic tets). Default ANSYS contact stabilization with 0.1 N·mm penalty cap. Nonlinear solution with force convergence 0.5% and 50 substeps max.

Sanity checks on numerics
- Three meshes: M1 (0.82M elems, 0.35 mm min at fillet), M2 (1.64M, 0.25 mm), M3 (3.28M, 0.18 mm).
- Response changes M2→M3: global force–displacement slope −1.9%; peak von Mises at head fillet +3.6%. Displacement field smooth by visual inspection; no element distortion flags. Based on this, M2 was used for parametric runs, M3 for the fixture correlation.

How it stacks up to the lab
- Lab setup: six specimens in our in‑house 4‑point rig, unconditioned, no saline, ambient 23 °C. Mean stiffness 1.42 kN/mm (SD 0.05). Strain gage at underside of the head fillet indicated 610 MPa equivalent stress at 1.5 mm crosshead travel (converted assuming local linear elastic region).
- Model: stiffness 1.33 kN/mm (−6.6% vs. mean). Peak von Mises at the same fillet 545 MPa (−10.7%). Hotspot location in FEA matches gage placement within ~0.8 mm.
- Likely contributors to the residual gap: no screw clamp-up modeled, fixture roller compliance not included, and our bonded-thread surrogate stiffens the joint locally. A trial with μ = 0.25 closed the stiffness delta to −4.9% but pushed contact chattering; we kept μ = 0.2 for stability.

What this is good for right now
- Comparing alternative head fillet radii, countersink angles, or head undercut depths. The stress hotspot is well resolved and moves consistently with geometry tweaks.
- Establishing a provisional proof load: at 1.5× the expected in‑service bending moment (based on prior F1717‑style constructs), the model remains below first yield at the head fillet with 8–12% margin depending on screw length.

Caveats and open items
- Threads beyond the head region are idealized; do not use the current model to comment on flank stresses or galling risk.
- No attempt yet to account for assembly torque, off‑axis load introduction, or fixture compliance; those all push stress up in the lab and would narrow the gap.
- Plastic work is low in the current load range; if we intend to assess post‑yield redistribution, we’ll need to revisit the hardening law with actual coupon data at strain >0.5%.

Traceability
- Model files in PDM: Vault/FEA/Plates/Lateral/RevD/BendRig, item 7‑A3F‑PLT. ANSYS 2024 R1. Material card MC‑Ti64‑BK‑v2. Solver settings saved in WB template tpl‑bend4pt‑2026‑06‑14.wbwx. Lab data set LAB‑4PT‑PLATE‑RIG‑2026‑07‑12.csv.

Recommendation
- Proceed to use the M3 model as the reference for proof‑load setting and for down‑selecting between head geometries. Before we lean on it for absolute safety margins, add screw clamp-up and a compliant roller model, then re‑check against one additional fixture run with measured torque.
