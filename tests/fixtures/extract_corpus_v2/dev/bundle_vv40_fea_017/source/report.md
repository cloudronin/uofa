To: A. Patel, Airframe IPT Lead
From: D. Kim, Structures/FEA
Subject: Attach Bracket Model — Current Credibility and Decision for Pre-PDR Use
Date: 06 Aug 2026

Summary
We built and solved a solid-model FEA of the nose-gear forward attach bracket to support pre-PDR trades. The intent is to screen bracket geometry and fastener patterns under the nominal landing case and identify whether the current lug/fillet scheme is viable before we freeze the bolt layout. The model captures 3D load flow from the lug into the web and base, with emphasis on peak stress around the inner fillet and edge distance effects at the fasteners.

Model set-up
- Geometry: Imported from NX Rev H. Fillets 1.0 mm and larger were retained; minor chamfers on non-critical edges were suppressed to simplify meshing. Fastener clearance holes are as-designed (8.00 mm for M8).
- Materials: 7075‑T651 aluminum, linear elastic. E = 71.7 GPa, ν = 0.33, density = 2810 kg/m³. Yield used for reference only: 503 MPa (MMPDS-17, Table 3.1.8.0(c), room temp).
- Elements: Quadratic tetrahedra (10‑node, SOLID187 class) in the bracket; rigid beams (RBE2-style) were avoided. Bolts represented by axial-shear connector elements placed colinear with hole axes; pretension is included via initial strain in the connector, 8 kN each for the two inboard bolts, 6 kN each for the two outboard bolts.
- Contact: Lug pin-bracket bore modeled as tied (no slip) to emulate a tight bushing fit; bracket-to-fuselage interface constrained via kinematic coupling at the bolt grip planes. No friction modeled at hole/bolt interface.
- Loading: Nose gear vertical reaction resolved into bracket as 12.8 kN downward through the lug axis and 3.2 kN aft drag (consistent with 1.5g sink and rollout). A small lateral (0.8 kN) was included to avoid singularity from perfect symmetry.

Solver notes
- Static, small-displacement. Augmented Lagrange enforcement on the bolt connectors to hold pretension during load ramp. Equilibrium reached in 7 substeps; peak nonlinear iteration count per substep was 9. Solution stabilized without quasi-static damping.

Grid sensitivity
- Three meshes were exercised in the hot-spot region using curvature-based refinement with min edge lengths of 0.80 mm (coarse), 0.50 mm (medium), and 0.30 mm (fine). Global counts: 0.62M / 1.45M / 3.20M DOF respectively.
- The maximum principal stress at the inner fillet on the lug boss reported 454 MPa (coarse), 436 MPa (medium), 429 MPa (fine). Between medium and fine, the change is 1.6%. Displacement at the lug axis was 0.42 / 0.39 / 0.38 mm across the three meshes (medium to fine delta 2.6%).
- Based on this, we used the fine mesh for all reported values below. No further refinement was pursued due to cycle budget; the remaining mesh sensitivity at the peak is judged small relative to the design margin being considered this phase.

Results of interest
- Peak maximum principal stress at the inner fillet: 429 MPa (fine mesh). The hot zone spans ~1.2 mm along the fillet arc; paths 1 mm off the surface drop to 355–370 MPa.
- Net-section stress around the inboard bolt line: 301 MPa tension on the web side, 218 MPa compression on the base flange side, indicating a slight eccentricity from the current bolt pattern.
- Bolt loads: Inboard pair carry 63% of the shear; max connector shear is 6.2 kN, axial remains compressive due to pretension for all four bolts.
- Deflection at lug center: 0.38 mm downward, 0.05 mm aft.

Assumptions and limitations
- Linear elastic material only; no plastic redistribution captured at the fillet.
- Bore-to-pin tied contact stiffens load transfer vs a true clearance fit. This is conservative for displacement but may underpredict local bearing stresses; we are not using local bearing response for decisions at this stage.
- No thermal loads included; room temperature assumed.
- The bolt shank/bearing compliance is idealized via the connector stiffness values supplied by fastener engineering (kax = 40 kN/mm, kshear = 15 kN/mm). We did not vary these in this pass.

Credibility considerations
- The mesh density study shows low sensitivity in the primary responses (stress hotspot and lug deflection) between the last two levels.
- Connector pretension stabilizes the joint; with pretension removed, the peak fillet stress rises by ~7% and the load sharing shifts further onto the inboard pair (single alternate run). We retained pretension in the baseline because assembly torque is specified in the current build plan.

Recommendation and decision
Given the stable response with mesh tightening and the consistent load path behavior, the model is accepted for pre‑PDR geometry screening and bolt pattern selection, subject to using the fine-mesh setup and the stated pretension values. It is not approved for drawing release, stress allowables, or certification findings. Decision recorded by: D. Kim (Structures) and concurred by A. Patel (Airframe IPT).

Next steps if we carry it forward post‑PDR
- Introduce a true pin/bore contact model with clearance and friction to assess bearing and clamp-up effects on the fillet hotspot.
- Expand the refinement region if we decide to rely on local notch stress for margin.
- Extend the load set to include side‑load taxi and towing cases once those vectors are finalized.
