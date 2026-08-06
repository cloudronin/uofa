Title: Structural Review of the LG-12 Bracket Using Nonlinear Finite Element Analysis

Author: Structures Team, AeroSystems R&D
Date: 2026-08-05
Software: Abaqus/Standard 2022

1. Executive Summary

We reviewed the LG-12 landing gear attach bracket for the Aurora X3 UAV using a detailed finite element model to assess stress, local plasticity, and deflections under representative touchdown and ground maneuvering loads. The bracket is machined from AA 7075-T6 and attaches to the composite keel with two M8 fasteners and a lateral locating pin. The purpose of this analysis is to inform preliminary sizing decisions for the bracket prior to first-article machining.

Based on the current model and applied load envelopes, the highest equivalent stress occurs at the outboard fastener bore entrance in the touchdown case (Case B), with a von Mises peak of 465 MPa and plastic strain concentration confined to a ~0.2 mm deep annulus at the hole edge. The global tip downwash deflection is 0.43 mm in Case B. Load path checks indicate consistent reaction forces and minimal nonrecoverable energy relative to elastic strain energy (<0.6%). A hand-estimated stiffness, treating the bracket arm as a short cantilever, is within 12% of the finite element prediction.

Given the allowable stress for 7075-T6 at room temperature and the low extent of yielding, the current bracket geometry appears adequate for the evaluated static conditions with a modest reserve. Areas recommended for local improvement include the chamfer transition at the outer bore, where a blended fillet could reduce the peak by ~6–9% according to a targeted geometry variant run.

2. Background and Scope

The LG-12 bracket transmits touchdown loads from the retracting leg to the airframe primary structure. A recent geometry change added a cable pass-through adjacent to the outboard fastener hole, prompting a recheck of load path and stress concentration. This report summarizes the model setup and key outcomes from a set of static, monotonic load cases aligned with the structural design data sheet (SDS-47A Rev C). Dynamic effects, thermal influences, and life estimation are not part of this review. The primary questions to answer are:
- Are peak stresses and permanent deformations acceptable for the defined static service loads?
- Are there apparent geometric issues that should be refined before sending out the manufacturing drawings?

3. Geometry and Model Construction

3.1 CAD and simplifications
- Source geometry: SolidWorks LG-12_Bracket_RevF.SLDPRT dated 2026-06-12.
- Imported as parasolid; small features under 0.4 mm not critical to load path (edge break, engraving) were suppressed.
- The cable pass-through slot was retained. All fillets ≥1.0 mm remained intact. The locating pin boss and both M8 bores are modeled with true diameter and lead-in chamfers per the CAD.

3.2 Element formulation and connectivity
- The bracket is modeled with 10-node tetrahedral solid elements (Abaqus C3D10).
- The two M8 fasteners are represented by tied rigid surfaces with distributed coupling to reference nodes at the bolt axes. This enforces average displacement compatibility over the washer footprints and captures local bearing stress in the lug walls.
- The pin interface is modeled as a cylindrical contact with constrained radial freedom and free axial sliding.

3.3 Contact representation
- Surface-to-surface, small-sliding contact is used between the bracket mounting face and a rigid representation of the keel pad.
- Coefficient of friction is set to 0.20 to reflect anodized aluminum against an epoxy-painted composite pad.
- A normal “hard” constraint formulation is used with automatic stabilization (damping factor 2e-6) to improve convergence in early increments without inflating predicted slip.

4. Materials

Base material: AA 7075-T6 at 23°C.
- Elastic modulus: 71.7 GPa
- Poisson’s ratio: 0.33
- Density: 2810 kg/m³ (not used in static runs)
- Plasticity: Isotropic hardening with yield at 503 MPa and tangent modulus 1.2 GPa up to 4% plastic strain. For strain levels beyond 4%, the curve flattens to 0.3 GPa slope out to 9% strain, taken as a numerical cap to avoid unrealistic work-hardening.

Washers and keel pad are modeled as rigid bodies since their deformations are negligible relative to the bracket thickness in the considered load cases.

5. Loads and Constraints

5.1 Boundary representation
- The keel pad is immobilized in space (reference node fixed in all translational components). The bracket’s mounting face contacts the rigid pad. The two bolt hole surfaces are coupled to bolt-axis reference nodes that carry preload and external shear.
- Bolt preloads are not included because the SDS load sets are defined as net external actions at the bracket interfaces.

5.2 External actions
Three service cases are assessed:
- Case A: Ground roll bump
  - Vertical downward force: 1.2 kN applied at the axle clevis pin hole centerline.
  - Longitudinal drag: 0.5 kN rearward, same application point.
  - Transverse side load: 0.3 kN toward fuselage centerline.
- Case B: Firm touchdown
  - Vertical downward force: 1.8 kN at axle clevis.
  - Longitudinal drag: 0.9 kN rearward.
  - No transverse component.
- Case C: Side load taxi turn
  - Transverse side load: 1.1 kN toward fuselage centerline at axle clevis.
  - Small vertical preload: 0.3 kN.
  - No longitudinal component.

All loads act through multi-point constraints to the clevis bore to avoid artificial stress at a single node. Directions align with the bracket’s installed orientation.

6. Meshing and Solution Controls

6.1 Discretization
- Global target element edge length: 4.0 mm.
- Local refinement:
  - 1.5 mm in a 5 mm ring around each M8 bore.
  - 1.0 mm along the cable slot fillet and the outer-lip chamfer where the arm thins.
  - 2.0 mm on the mounting face and clevis fillet.
- Total elements: approximately 1.24 million; total nodes: approximately 2.06 million.

6.2 Step definitions and convergence
- Static general procedure with large-deformation effects enabled.
- Automatic time incrementation starting at 0.01 with a ceiling of 1.0.
- Convergence tested on force and displacement residual norms. Contact damping remains below 0.6% of total strain energy at final increments for all cases.
- Solver defaults for mid-side node treatment and element integration.

7. Results

7.1 Global behavior
- Case A (ground roll bump): The vertical tip deflection at the axle clevis is 0.22 mm. Reaction forces at the bolt reference nodes sum to 1.19 kN vertical and 0.49 kN longitudinal, within 1% of the applied values when including the small frictional shear.
- Case B (firm touchdown): The bracket arm bends downward by 0.43 mm at the clevis. Contact pressure on the mounting face shifts forward, with a peak of 142 MPa under the outboard washer footprint.
- Case C (side load taxi turn): Lateral tip compliance results in 0.36 mm side movement, with the locating pin carrying the bulk of the shear. The mounting face exhibits asymmetric lift-off at the outboard rear corner; the unseated area is small and recontacts as the solution progresses.

7.2 Local responses and hotspots
- Hole edge stress: The outboard M8 bore exhibits the maximum von Mises equivalent stress in Case B. The peak is 465 MPa located at the entry corner where the chamfer meets the bore wall, at the 4 o’clock position relative to load direction. The effective plastic strain at the peak location is 0.3–0.4%, falling to elastic levels within 0.2 mm depth from the edge.
- Cable slot fillet: The cable pass-through fillet has a secondary stress ridge of ~295 MPa under Case B, influenced by the local thickness reduction. No plasticity initiates here.
- Clevis join: The inner fillet of the clevis shows smooth gradients, with maxima of ~255 MPa in combined bending and shear.
- Contact: Maximum penetration across the mounting interface remains under 5 microns. Frictional slip is limited to 15–40 microns at the forward edge of the outboard washer zone in Case B.

7.3 Comparative variant
A simple geometry tweak adding a 0.6 mm blend between the entry chamfer and bore wall at the outboard hole was tried. Under Case B, the von Mises peak reduced from 465 MPa to 428 MPa, and the plastic spot size reduced by roughly one-third in radial depth. Global stiffness changed by less than 1%.

8. Reasonableness Checks

The following checks were performed to confirm the model’s behavior aligns with engineering expectations:
- Load balance:
  - For each case, the vector sum of reaction forces at the mounting interface and coupled bolt nodes matched the applied loads within 1%. Moments about the keel pad centroid closed to within 2% after the contact fully settled.
- Energy accounting:
  - At the final increment of each step, artificial damping energy associated with contact stabilization was less than 0.6% of recoverable strain energy. Plastic dissipation is confined to the vicinity of the outboard hole in Case B, representing ~3.4% of total strain energy. Cases A and C remained essentially elastic.
- Hand approximation:
  - Treating the bracket arm as a non-prismatic cantilever of effective length 42 mm, thickness 9 mm, and variable section modulus (averaged), a back-of-the-envelope calculation yields a vertical tip deflection of ~0.48 mm under the Case B vertical load component. The finite element value is 0.43 mm, a 12% difference attributed to the simplified section and the restraining effect of the mounting face contact.
- Contact state:
  - The pressure map under the outboard washer shows a reasonable shift forward in Case B, with a nearly elliptical footprint, consistent with a tilted pad under combined bending and drag.

9. Interpretation Relative to Design Intent

- Yielding: The highest local equivalent stress slightly undercuts the nominal yield of 7075-T6, and where small-scale plasticity is observed, the extent is limited and well away from net section. Given the static nature of the load sets evaluated, this is acceptable for preliminary go/no-go.
- Stiffness: Tip deflections remain under 0.5 mm in all cases; the cable slot does not introduce unexpected softness. The locating pin correctly shares lateral load in Case C, reducing eccentricity on the bolts.
- Load path: The assessed contact pressure fields and bolt reactions indicate that the bracket primarily bears against the keel pad near the outboard fastener, in agreement with free-body expectations.

10. Recommendations

- Modify the outboard bore entry detail by replacing the sharp chamfer junction with a blended radius of 0.5–0.8 mm to depress the peak von Mises by up to ~9%. This can be done without affecting bolt fit or washer seating.
- Maintain the current clevis fillet size; it is not the limiting feature in the assessed cases.
- For the cable pass-through, if electrical clearance allows, consider a gentle 0.2–0.3 mm increase to the fillet radius to further flatten local stresses, though this is not currently a driver.
- Retain the installed frictional condition at the mounting face via surface treatment control to limit slip under drag loads.

11. Model Files and Reproducibility Notes

- Primary analysis model: LG12_bracket_revF_static.inp
- CAD source: LG-12_Bracket_RevF.SLDPRT, parasolid export timestamp 2026-06-12 14:07Z.
- Material curve file: Al7075T6_iso_plasticity_2025Q4.csv.
- Load case definitions embedded as separate analysis steps A, B, C in the primary model.

12. Credibility Discussion

The predicted behavior is technically consistent with the part geometry and the specified load paths. Force closures, contact states, and deformation shapes align with expectation:
- The small region of nonlinearity at the outboard hole under the highest vertical/drag pairing is qualitatively where one would anticipate the maximum, due to combined bearing and bending near a thickness transition.
- Reaction force partitioning between the two bolts shifts by ~11% between Case A and B, driven by altered contact pressure distribution; this behavior mirrors the free-body logic of a rocking interface.
- The pin carries >70% of the side load in Case C, which is by design; the model’s kinematic coupling correctly routes load into the pin-bearing region, easing shear on the bolts.

An independent stiffness estimate supports the order of magnitude of the computed deflections. The contact stabilization energy is negligible, indicating that numerical aids did not overly influence the solution. Local mesh refinement was concentrated at geometric discontinuities of concern, and gradients there are smooth away from singular edges, which suggests the resolved peaks are not numerical noise.

13. Limitations and Caveats

- The present work addresses monotonic static service loads only. Impact transients, wheel shimmy, or rebound events are not covered.
- Temperature effects and material aging (e.g., T6 temper degradation) are not represented.
- Manufacturing tolerances, thread strip criteria, and washer conformance are not included; bolts are idealized as nominal.
- The keel pad is rigidized; any compliance in the surrounding structure is neglected here.
- Corrosion, coatings build-up, and wear at the contact interface are not within the scope of this analysis.

14. Conclusion

Under the assessed static load cases, the LG-12 bracket, as currently modeled, shows acceptable stress and deformation with a narrow margin in the vicinity of the outboard bolt bore during the firm touchdown scenario. The local design refinement at the bore entry is a practical mitigation that reduces the peak without affecting overall dimensions or assembly interfaces. No gross stiffness or load-path irregularities were observed. The analysis supports proceeding to drawing release with the recommended local edit and subsequent standard design checks.

Appendix A: Additional Observations

- Convergence characteristics:
  - Case A completed in 17 increments; Case B in 29 increments; Case C in 24 increments. No cutbacks were triggered by contact instability once initial seating occurred.
- Reaction vs. applied:
  - For Case B, vertical applied load 1.8 kN; recovered at constraints 1.79 kN vertical plus 0.01 kN vertical from frictional coupling. Longitudinal applied 0.9 kN; recovered 0.88 kN at bolt references and 0.02 kN in friction tractions.
- Plastic strain footprint (Case B):
  - Continuous around approximately 45 degrees of arc at the outboard bore entrance, concentrated toward the loading direction. Depth into the bore wall ~0.2 mm, surface length along bore ~1.7 mm.

Figures and plots referenced in this report (stress contours, contact pressure maps, and deformed shapes at 2x exaggeration) are stored with the analysis output under the project drive: \\AeroSystems\Projects\AuroraX3\FEA\LG12\revF\plots.

End of Report
