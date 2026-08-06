# Credibility Assessment Report
Project: Static stress evaluation of eVTOL avionics bracket  
Analyst: D. Rao, Structures Group  
Date: 2026-08-05  
Tool: Ansys Mechanical 2024 R1 (build 24.0.3), double precision

## 1. Background and Objectives
This document records the technical basis used to judge whether the finite-element predictions for the eVTOL avionics L-bracket are reliable for preliminary release. The bracket fastens to a rib in the forward fuselage and supports a 6.5 kg radar altimeter located approximately 120 mm off the rib face. The governing design event for this phase is a quasi-static limit load representing a vertical 15 g inertia case with the aircraft parked on ground (no concurrent thermal, acoustic, or vibratory input).

Scope of this report:
- Model setup decisions that most strongly impact predicted maximum stress and tip deflection.
- Evidence that the stress hot spot at the web–flange fillet is adequately resolved by the mesh and element formulation.
- Sanity checks against simplified closed-form estimates for bending and fastener load sharing.
- Selected robustness checks for contact modeling and bolt pretension.

Items outside the present scope include fatigue assessment and acoustic response; those are being handled by separate tasks.

## 2. Geometry and Idealization Decisions
- Source CAD: Bracket model v7 exported from Siemens NX (filename BRKT-ALT-ASSY-001_v7.prt). Key dimensions: flange width 60 mm, nominal thickness 6 mm, web height 120 mm, inner fillet radius 6 mm.
- Removed features: Thread forms, small chamfers (<0.5 mm), and etched ID marks were suppressed. Fastener holes retained at nominal size (7 mm for M6 bolts).
- Symmetry was not used; the mounted unit’s center of gravity is offset in both in-plane directions.
- The avionics unit was not meshed; its mass is represented via a distributed remote force and moment couple applied at its CG located 120 mm from the bracket web and 20 mm above the flange mid-plane.

Rationale: Thread details and sub-millimeter chamfers have negligible influence on the global stiffness and only localize stress around features that are not controlling for the bracket’s first yield in this load case. The fillet blending the web and flange is known to control peak stress; its radius and adjacent thickness transitions were preserved.

## 3. Materials and Constitutive Choices
- Bracket material: 7075-T6 aluminum (AMS 4045). Elastic modulus 71.7 GPa, Poisson’s ratio 0.33, density 2810 kg/m^3.
- Strength data for comparison: yield strength 503 MPa and tensile strength 572 MPa based on MMPDS-17 A-basis room-temperature values.
- Behavior modeled as linear elastic, small strain.
- Fasteners represented as linear elastic steel (E = 200 GPa) for stiffness effects only; no explicit failure checks were performed here.

Rationale: At the expected stress levels, the bracket should remain below first yield for limit load. Plasticity would only be relevant if deflection or stress margins approached allowable limits, which is not indicated by the results summarized below.

## 4. Loads, Restraints, and Contact Interfaces
- Inertial load: 6.5 kg × 9.81 m/s^2 × 15 g = 956 N vertical downward load applied at the avionics CG via a remote force connected to a node set on the bracket’s mounting plane. The load is distributed to the six M5 mounting holes through rigid surface-based MPCs replicating the unit’s baseplate stiffness.
- Bracket-to-rib attachment: Four M6 bolts modeled as pretensioned beam connectors tying the bracket flange to rigid points on the rib surface. Pretension in each fastener: 8 kN (delivered clamp load). The rib is considered rigid for this phase; its compliance is captured in a separate model used to justify this idealization (Ref. RIB-STIF-Note-03).
- Contact: Surface-to-surface contact between bracket flange underside and rib interface surface with µ = 0.2 friction coefficient; augmented Lagrange normal enforcement, default contact stiffness factor.

Assumptions: Preload is sufficient to prevent joint separation at limit load; limited micro-slip can occur depending on friction assumptions but does not dominate bracket stress near the fillet.

## 5. Finite-Element Model and Solver Settings
- Element type: Quadratic tetrahedra (10-node) for solid regions; BEAM188 for bolt shanks; CONTA174/TARGE170 for contact.
- Mesh controls: Hex-dominant swept mesh not feasible due to intersecting fillets; tet-dominant mesh with local size control in the fillet and around bolt holes.
- Nominal element sizing:
  - Fillet hot-spot region: element edge 0.9 mm on the “fine” mesh, 1.2 mm on the “medium,” and 1.6 mm on the “coarse.”
  - Away from hot spots: growth factor 1.3; max edge up to 5 mm.
- Quality: Min Jacobian ratio > 0.6; skewness < 0.8 in hot region.
- Solver: Sparse direct solver; force convergence tolerance 1e-6 of reference norm; contact penetration target < 1% of local element size with auto-adjust during the first five substeps. Single load step with 10 automatic substeps for contact stabilization.

Run environment: RHEL 8.8, 8 physical cores @ 3.1 GHz, 64 GB RAM. Medium mesh run time ~21 min; contact active after substep 2.

## 6. Mesh Refinement Study
Objective: Demonstrate that the reported maximum von Mises stress at the web–flange fillet and the tip deflection are not materially affected by further refining the mesh.

Three systematically refined meshes were analyzed:

- Coarse: 0.28 M solid elements, 0.41 M nodes
- Medium: 0.51 M solid elements, 0.73 M nodes
- Fine: 0.92 M solid elements, 1.34 M nodes

Results summary (hot-spot von Mises and tip deflection at the avionics CG):
- Max stress (MPa): 352 (coarse), 364 (medium), 370 (fine)
- Tip deflection (mm): 0.66 (coarse), 0.64 (medium), 0.63 (fine)

Using Richardson-style extrapolation based on the medium-to-fine trend, the apparent asymptotic stress is ~377 MPa. The estimated relative difference between the fine mesh and the asymptotic value is about 1.9%. For deflection, the corresponding estimate is below 1%. Based on this, the medium mesh is sufficient for most parametric studies; the fine mesh is preferred for final reporting. All stress results refer to the fine mesh unless otherwise noted.

Local convergence check: Stress contours in the fillet region show smooth isostress patterns with no abrupt element-to-element jumps. Path plots along the fillet midline are nearly indistinguishable between the medium and fine meshes except within 0.5 mm of the geometric corner, where numerical gradients are expected.

## 7. Element Formulation and Alternative Discretizations
To reduce the risk that results are an artifact of element choice, one additional model was constructed:

- Hex-dominant mesh in the fillet block using 20-node bricks (SOLID186) with mapped meshing feasible after introducing a small partition around the fillet. The remainder of the volume remained tet-dominant with transition elements.

Outcome: The alternative mesh produced a peak stress of 361 MPa and deflection of 0.65 mm for equivalent local sizing (approximately similar computational cost to the medium tetra mesh). The difference relative to the fine tet mesh was 2.4% for stress and 3.2% for deflection, which is within the expected variation considering that brick elements tend to be slightly more diffusive around curved fillets at comparable sizing. This offers confidence that the identified hot spot is not mesh-type dependent.

## 8. Contact and Fastener Modeling Sensitivity
Two parameters were perturbed to test robustness:

- Contact normal stiffness factor varied by ×0.5 and ×3 from the default. Peak stress changed by −1.1% and +1.8%, respectively. Slip at the outer bolt pair changed by less than 0.02 mm.
- Friction coefficient varied between 0.15 and 0.3. Peak stress changed by +0.7% and −1.6%, respectively. Contact status remained fully engaged; no gross separation occurred in any case.

A separate run removed pretension (bolts free, no clamp). In that artificially conservative configuration, the joint opened under the 15 g load, and bracket stress rose by ~8%, confirming the importance of capturing preload in the model for realism.

## 9. Solver Convergence and Numerical Health
- Equilibrium iterations stabilized within 6–8 iterations per substep once contact settled; final force residual below 5e-7 of the reference external load.
- No negative pivot warnings or hourglassing were reported.
- Energy balance showed internal-to-external work ratio within 0.2% at the end of the step.
- Contact penetration under 5 µm in the fillet-adjacent flange region on the fine mesh.

These indicators suggest the solution is numerically well-behaved.

## 10. Bench Checks Against Simplified Calculations
A back-of-the-envelope bending estimate treated the bracket as a rectangular cantilever (width 60 mm, thickness 6 mm) with a tip load of 956 N at L = 120 mm. Using σ = Mc/I with c = t/2 and I = b t^3 / 12, the nominal bending stress at the fixed end is approximately 317 MPa. The fine-mesh FEA peak was 370 MPa located slightly offset into the fillet throat. The ~17% elevation from the simplistic beam estimate is consistent with a 3D stress concentration from the curved geometry and local load paths into the joint. The corresponding deflection estimate using δ = FL^3/(3EI) gives ~0.61 mm; the FEA value (0.63 mm) aligns closely, lending confidence to the global stiffness representation.

Fastener shear load sharing, estimated via a rigid-base approximation, predicts outer bolts taking ~27% more shear than inner bolts. Connector force output from the FEA showed a 24–29% spread depending on friction, which is consistent with expectation and suggests the joint idealization is reasonable for bracket stress purposes.

## 11. Results and Interpretation
- Peak von Mises stress: 370 MPa (fine mesh), occurring in the web–flange internal fillet on the tension side.
- Secondary hot spots: Mild stress risers (~290–310 MPa) by the bolt hole edges nearest to the load application point; these do not govern.
- Tip deflection at avionics CG: 0.63 mm downward.
- Contact state: No separation under the pretensioned case; micro-slip limited to <0.03 mm near the outer bolt pair.
- Fastener axial forces: Pretension maintained; incremental axial load increases <2% of preload.

Interpretation: For the specified limit event, the bracket remains in the linear elastic regime with a comfortable margin to first yield using 7075-T6 A-basis data. The critical region is well understood geometrically (inner fillet), and mesh refinement indicates remaining numerical uncertainty on the peak stress is below ~2–3%. Predicted deflection is small relative to allowable avionics connector misalignments.

## 12. Data Traceability and Reproducibility
- Master model archive: //fs/Projects/EVTOL/AVL-BRKT/FEA/2026-08-05/BRKT_ALT_v7_Mech24R1.zip (contains .mechdb, solver input, and post-state).
- Randomized features: None. Contact stabilization was deterministic given fixed seed; default stabilization settings used.
- Postprocessing workflow: APDL path plots and nodal averaging disabled near the hot spot to avoid artificial smoothing; results exported as CSV with node IDs preserved.

A readme.txt in the archive lists the parameter values for each named run (“coarse,” “medium,” “fine,” and sensitivity variants), aiding replication.

## 13. Peer Review
A two-person internal review was conducted focusing on:
- Adequacy of local mesh density in the controlling fillet.
- Justification of using linear elastic material behavior for limit load.
- Reasonableness of the bolt pretension value relative to M6 torque recommendations.

Action items addressed:
- Increased fillet mesh density by 20% compared to the initial setup.
- Confirmed pretension selection corresponds to ~75% of proof for typical property class 10.9 M6, which is conservative for aluminum joint seating.

## 14. Credibility Synthesis
Drawing together the items above:

- The modeled physics are aligned with the design event of interest (single, quasi-static 15 g vertical loading). Key load paths and restraint conditions are represented explicitly (bolt clamp, frictional interface, realistic CG offset).
- The discretization has been shown to be sufficiently fine in the hot region, with a convergent trend and two alternative element topologies returning stress within ±3%.
- Simplified analytical estimates for both stress and displacement bracket the FEA predictions as expected; the difference for stress is rationalized by 3D concentration.
- Perturbations to contact and friction parameters produced small changes to governing stress and deflection, indicating result stability to reasonable modeling choices.
- Solver health metrics were within tight bounds; no red flags from convergence or contact penetration.

Given the above, the structural predictions for the specified context are fit for preliminary release and for use in downstream tasks such as bracket topology cleanup and rib compliance assessment. The numerical uncertainty on the reported peak stress is judged to be small relative to material strength variability at this stage.

## 15. Limitations and Next Steps
- The analysis is limited to room-temperature, static loading in the vertical direction with the avionics modeled as a rigidly attached mass. It does not encompass coupled thermal effects, dynamic response, or spectrum loading.
- Fastener threads and local bearing stresses within the rib substrate were not resolved; a separate joint-level model is recommended if those become design drivers.
- The rib was treated as rigid; a forthcoming coupled model with the rib substructure will re-check bracket stress if significant flexibility is present.
- Nonlinear material behavior was not included. If later load cases require excursions near or above first yield, a bilinear hardening law and, if necessary, local plastic strain limits will be introduced.

Planned follow-up:
- Integrate the bracket and rib into a single assembly model with measured rib stiffness to confirm joint load flow.
- Explore a slight increase in fillet radius from 6 mm to 8 mm to reduce the hot-spot stress and improve manufacturability.

## 16. Summary of Key Numbers
- Limit load: 956 N at 120 mm offset
- Peak von Mises stress (fine mesh): 370 MPa at web–flange fillet
- Estimated remaining mesh-induced error on peak stress: ~1.9%
- Tip deflection at avionics CG: 0.63 mm
- Sensitivity to contact stiffness and friction: ≤2% on governing stress
- Brick vs tet mesh stress difference: 2.4%

Prepared by:  
/s/ D. Rao, Lead FEA Engineer

Reviewed by:  
/s/ A. Nguyen, Senior Structures Analyst
