To: Priya Shah, Spine Program Lead
From: M. Ortega, Simulation Team
Subject: Status check — Cage FEA credibility for design freeze gate

Quick recap of how we intend to use the model
- The current finite-element model is meant to answer a narrow question: does reducing the inner pocket radius from 1.0 mm to 0.6 mm on the L4–L5 PEEK interbody cage jeopardize static compressive performance per our internal acceptance metric? It is not being used to make claims about torsion, fatigue, or subsidence into bone analogs; those are separate workstreams.

Model setup and main assumptions
- Geometry: Rev H CAD, pockets and serrations retained; thread features suppressed below 0.25 mm to keep element distortion in check around the fillets of interest.
- Material: Unfilled PEEK per Invibio datasheet; E = 3.6 GPa, ν = 0.36, linear elastic. We are staying in the small-strain regime for the load levels considered here.
- Contacts and loading: Compression between polished stainless platens (ASTM F2077-like). Surface-to-surface contact with a 0.2 friction coefficient; tie constraints at the cage–disc interfaces are not used. Load applied as 0–6 kN ramp, displacement-controlled for robustness.
- Solver and elements: Abaqus 2022, nonlinear static step with automatic stabilization (dissipation ratio target 0.0002). Quadratic tets (C3D10) in fillets and web regions; linear tets for the bulk where gradients are mild.

Numerics sanity checks
- Mesh refinement: three meshes targeted at the radius transition:
  - Coarse: 1.2 mm nominal size; 85k elements; peak von Mises at the inner fillet = 92 MPa.
  - Medium: 0.8 mm; 190k elements; peak = 101 MPa.
  - Fine: 0.5 mm; 480k elements; peak = 103 MPa.
  - Change from medium to fine is 1.9% at the hotspot; we used the fine mesh for all reported values.
- Equilibrium and contact stability: residuals below 1e-6 by the last increment; max penetration under 2 µm; 15–28 iterations to converge across load steps.

Comparison to bench data
- We mirrored our internal static compression fixture (same 25 mm platen radius, same spacer stack-up). Two physical samples (Rev G geometry, 1.0 mm pocket radius) gave axial stiffness of 2.85 and 2.91 kN/mm up to 6 kN. The model predicted 2.95 kN/mm (+3.5% relative to the average test). The deformation mode (web bending with stress concentration at the inner fillets) matches DIC images.
- For the revised 0.6 mm fillet, no test data yet; the model estimates 105 MPa peak von Mises at 6 kN. Given the linear-elastic assumption, the change from 1.0 mm to 0.6 mm radius increases the hotspot by about 4%.

Inputs tug test (what matters)
- Friction coefficient sweep 0.15–0.30: axial stiffness varies by <5%, peak stress by <2%. The hotspot is largely geometry-driven under compression.
- PEEK modulus ±15%: stiffness scales proportionally; peak stress shifts ±6–7%. The qualitative ranking of the two fillet options does not change.

Where this leaves us for the gate decision
- Decision impact: We are not setting clinical limits; we’re down-selecting a minor geometry tweak before tool steel release. Consequence of a wrong call is a tooling rework and a few weeks’ slip, not patient harm.
- Match between model and evidence: For the baseline geometry, predicted force–displacement curve aligns within a few percent of the benchtop data using the same fixture conditions. The model is resolving the stress raiser with a refinements study showing minimal change between the last two grids.
- Limitations to keep in mind:
  - Applicability is limited to straight axial compression in a platen setup. Torsion, subsidence, and cyclic endurance are not covered here.
  - Material is treated as linear elastic; we did not model plasticity or damage initiation. The 6 kN level stays under typical yield for PEEK, which is why we kept it linear for this phase.
  - Contact uses a single friction value; while not critical for this loading mode, we did not attempt a detailed surface roughness model.

Recommendation
- Use the FEA to proceed with the 0.6 mm fillet radius on the inner pocket. The numerics are stable, mesh is sufficiently fine at the hotspot, and the baseline case lines up with our fixture measurements within ~3–4%.
- Please gate this approval to the scope above. Separate analyses/tests will address torsion and fatigue before the design transfer review.
- If we need extra margin, we can add one more local refinement pass (0.35 mm at the radius) and include a quick check with a small plastic hardening curve; that work would take ~2 days and would not change the overall conclusion based on current trends.
