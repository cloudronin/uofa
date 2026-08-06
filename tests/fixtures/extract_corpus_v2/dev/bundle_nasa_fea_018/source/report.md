To: Avionics Structures IPT Lead
From: E. Marin, Analysis Group
Date: 06 Aug 2026
Subject: FEA credibility memo — reaction wheel bracket, lander avionics deck

Scope and use case
We built and checked a finite element model of the reaction wheel mounting bracket to support a go/no-go on the current geometry prior to releasing the drawing to long-lead procurement. The immediate question is whether the bracket, as designed, has adequate margin under the quasi-static launch load cases and whether any obvious stress raisers require rework before we freeze the interfaces. This memo summarizes what we did to make the model trustworthy enough for that purpose.

Model build highlights
- Solver and elements: Ansys Mechanical 2023 R1, quadratic tetrahedrals (TET10) in the body; beam elements for bolt shanks where needed for connectivity to the deck.
- Geometry: CAD from PDM rev C. Fillet radii and cutouts retained. Thread details suppressed; bolt holes modeled as plain cylinders.
- Contacts and constraints: Hole-to-bolt shank tied; bracket-to-deck interface tied across the nominal contact patch; no friction modeled. Bolt preload not applied in this pass.
- Materials: Aluminum 7075-T7351, room temperature. E = 71.7 GPa, ν = 0.33, σy = 435 MPa. Values taken from MMPDS-17, Table 2.7.2.8(b).
- Loads: Acceleration fields to represent launch combined loads. Case A: 40 g along bracket Z (wheel spin axis), 10 g X, 10 g Y; Case B: 25 g lateral in Y, 10 g X, 10 g Z. Mass of reaction wheel and bracket represented via body forces using CAD densities; added point mass of 3.1 kg at the wheel CG to match vendor ICD.

Evidence of numerical soundness
- Mesh refinement: Global element size 3.0 mm, with local controls around the inner fillet at the vertical web reduced to 1.0 mm. Two refinements applied at the hotspot: 1.0 mm → 0.75 mm → 0.5 mm edge size. Peak von Mises at the fillet root changed by 7.4% on the first refinement and 2.1% on the second; displacement at the wheel CG changed by 1.3% and 0.4%, respectively. We used the 0.75 mm local mesh for production runs to keep solve time under 6 minutes while staying within 2–3% of the asymptote at the critical location.
- Equilibrium checks: For Case A, summed reactions at deck constraints are within 0.6% of the applied inertial forces and moments derived from the mass properties. Rigid-body modes suppressed as expected.
- Solver controls: Large-deflection off; default weak springs active; iterative convergence tightened to 5e-5 on force residual.

Inputs and loading pedigree
- Mass properties: Bracket mass from CAD: 0.42 kg. Reaction wheel mass and CG from RW-420 vendor ICD rev 5; we verified that the bracket-hole pattern aligns with the ICD drawing.
- Boundary representation: Deck stiffness not included; the deck is represented as fixed at the bolt pattern. To account for some joint softness seen in earlier avionics mounts, a follow-on run included axial springs (1.0e7 N/m) on the bolt beams; this affected peak strains by less than 3% in the area of interest.

Bench check against hardware
We performed a quick load-introduction test on a machined 7075 bracket (proto SN-02) using the structures lab frame. The bracket was bolted to a thick steel plate fixture; a calibrated deadweight system applied an equivalent 40 g vertical load to the wheel interface via a yoke. Two 350-ohm strain gauges were placed at the inner web fillet (one on each face), gauge length 3 mm. The FEA-predicted surface strain at the gauge centerline for Case A was 1520 µε on the accessible face. The measured peak at the corresponding location was 1705 µε, about 12% higher. After adding joint axial compliance in the model (springs as noted above), the predicted strain rose to 1630 µε, narrowing the gap to 4–8% depending on exact gauge location. We attribute the residual difference to fixture stiffness and the absence of preload in the model.

Results summary
- Case A peak stress: 292 MPa at the inner web fillet (0.75 mm local mesh). Using σy = 435 MPa, the local margin to first yield is 1.49. Displacement at wheel CG: 0.21 mm.
- Case B peak stress: 265 MPa at the same fillet. Margin to yield: 1.64.
- No other hot spots exceed 220 MPa; hole edge stresses remain below 200 MPa with tied contact.

Limitations to keep in mind
- No friction or clamp-up modeled at the bracket-deck joint; bolts are represented without thread compliance.
- The deck was treated as rigid at the bolt pattern, which is conservative for deflection but may affect local strain predictions.
- Dynamic content (sine/random) not assessed here; these runs target quasi-static equivalents only.

Recommendation and decision
Given the mesh behavior, the equilibrium checks, and the single-point lab check showing agreement within roughly 10% after accounting for joint softness, this model is accepted for preliminary design decisions on the bracket geometry and for communicating interface loads to the deck team. It is not approved for fastener-level margin sign-off or qualification-by-analysis. Decision recorded by: E. Marin, Analysis Group, with concurrence from the Avionics Structures IPT Lead.

Next steps
- Include bolt preload and friction at the joint once the torque spec is finalized.
- Revisit the hotspot fillet radius with design to add 0.5–1.0 mm if possible; current margin is acceptable but tight for downstream environments.
- Plan full dynamic assessment when the load matrix is baselined.
