Title: Credibility Review — FEA of Avionics Tray Corner Bracket Under Static Limit Load

Author: Structures Working Group, Launch Vehicle Program
Date: 2026-08-06
Reference: SWG-FEA-ATB-2026-04


1. Background and Context

The avionics tray corner bracket (part ATB-17) carries the forward right quadrant of the OBC tray to the instrument deck. The bracket is a machined 7075 aluminum L-bracket with an integral radiused fillet at the tray flange intersection. Primary fasteners are four M6 bolts on the tray leg and three M6 bolts on the deck leg. During the quasi-static load case for stage integration, the structural requirement is to demonstrate margin at 1.25× the operational load (limit load) without yielding, using the governing specification LV-SM-1217.

Decision context: The analysis will be used to approve the geometry of ATB-17 for release to fabrication for engineering development units. Specifically, the model output to be relied on is peak von Mises stress in the fillet region and bolt hole net-section stresses versus handbook material allowables.

Scope: The model addresses the static bracket response for the axial pull-through case (horizontal inertial drag on the tray, resolved at the corner bracket), with the deck considered rigid relative to the bracket. Fastener preload and dynamic environments are not treated in this report.

Software and hardware: Simulations were executed using Abaqus/Standard 2023 HF3 in double precision on a 16-core workstation. Output sets included nodal displacements, element stresses (S, Mises), contact pressures, and reaction forces at constraints.


2. Geometry, Materials, and Contact Treatment

Geometry:
- CAD source: ATB-17 v42 (Inventor 2026); small rounds <0.5 mm suppressed except the primary fillet (R = 6.0 mm).
- Overall leg lengths: 80 mm (tray leg) x 65 mm (deck leg); leg thickness t = 6.5 mm nominal.
- Bolt holes: M6 clearance, Ø 6.6 mm; countersink features removed and replaced by equivalent thickness to simplify local stiffness near holes, consistent with guidance in LV-GD-402.

Material model:
- Aluminum 7075-T73, isotropic, linear elastic for this assessment.
- Elastic modulus: 71.7 GPa; Poisson’s ratio: 0.33; density: 2810 kg/m³.
- Reference yield strength (Rp0.2): 435 MPa at 20°C per MMPDS-18, Table 8.1.3.1, plate 12–38 mm thickness. Thermal effects are not considered for this case; operating temperature is 22 ± 3°C during integration.

Fasteners:
- Represented as rigid beams (MPC tie) connecting opposing hole faces to a reference node; no explicit threads modeled.
- Preload not included. Shear transfer modeled through tied hole faces on the tray side to simulate the clamped interface.

Contacts and constraints:
- Tray-to-bracket interface: bonded (surface-based tie) to represent fully clamped contact post-installation.
- Deck interface: constrained by distributing deck leg hole rings to fixed reference points, representing a stiff deck fitting. A separate load case in Section 5 checks the sensitivity to compliance by replacing fixed points with springs (k = 2.0×10⁷ N/m per bolt) to approximate local deck flexibility.
- Self-contact disabled; minimum distances > 3 mm.


3. Loads and Boundary Conditions

Primary case (Case A — axial pull-through):
- Load magnitude: 12.5 kN applied as a distributed traction on the tray-leg outer face, aligned with the tray plane. This value corresponds to the 1.25× limit based on a 10.0 kN worst-case instrumentation harness drag and tray inertia sum for the quarter-panel share.
- Load distribution: Rectangular patch 50 mm × 30 mm centered on the tray leg, chosen to emulate the tray shear web transfer area.
- Constraints: Deck reference points on the three deck-leg bolt rings fixed in translation and rotation.

Alternate support stiffness case (Case B — compliant deck):
- Same load application as Case A.
- Constraints: Replaced by translational springs at the deck bolt reference points in all three axes, each k = 2.0×10⁷ N/m; rotations fixed. This is intended to bound the impact of non-infinite deck stiffness.

Bolt hole bearing checks:
- Post-processing extracts average surface pressure over the hole arcs in the load direction, compared to bearing allowables (ABMA method per LV-GD-407 inputs). Though simplified with tied constraints, the pressure result provides a consistent indicator across meshes.


4. Meshing Strategy and Quality Checks

Element formulation:
- Second-order tetrahedra (Abaqus C3D10) for the bulk.
- Ten-node wedge elements (C3D15) inserted near the fillet using partition sweeps to improve through-thickness resolution in the curvature region.

Local refinement:
- Fillet hot-spot sizing: target edge length 1.2 mm in the final mesh based on h ≈ R/5 rule-of-thumb for radius stress capture.
- Bolt holes: two element rings through thickness around each hole, minimum edge length 1.6 mm.

Global sizing:
- Coarse: 2.4 mm average; Medium: 1.6 mm average; Fine: 1.2 mm average. Three meshes defined consistently using size fields constrained by partitions.

Quality metrics (Fine mesh):
- Minimum Jacobian: 0.36; average aspect ratio: 2.8 (95th percentile < 4.9).
- Warpage and skewness within Abaqus defaults; no inverted or hourglassed elements reported.

Convergence behavior:
- Nonlinear geometry off; analysis remains in the small-strain regime for both cases.
- Contact/tie constraints produce no overclosures exceeding 0.02 mm. Solver residuals decreased below 1e-8 equilibrium tolerance within 12 iterations for both cases.


5. Supporting Checks

Force and moment balance:
- Total reaction at deck reference points sums to 12,497 N (error 0.02% relative to applied 12,500 N) in Case A. Moments about tray-leg centroid negligible within numerical noise.

Sanity check via closed-form estimate:
- Treat tray leg as a cantilever plate strip of width b = 30 mm, thickness t = 6.5 mm, subject to resultant shear V = 12.5 kN and bending due to offset e = 14 mm (approximate from traction centroid).
- Peak bending stress σ ≈ 6Ve/(b t²) = 6×12,500×0.014/(0.03×0.0065²) ≈ 340 MPa at the inner radius. This back-of-envelope value is within 5–7% of the medium/fine mesh FEA von Mises hot spot discussed in Section 6, lending confidence that load paths and stiffness are modeled reasonably.

Hot-spot resolution trial:
- A local submodel was created with the fillet split into three layers through thickness and with target edge length 0.9 mm. Boundary displacements were interpolated from the medium mesh. The submodel peak von Mises differed from the fine global model by 2.1% at the hot-spot node set, and the stress gradient normal to the surface decreased by approximately 13%, indicating additional smoothing rather than a new peak. This suggests the fine mesh adequately resolves the fillet stress concentration for the reported use.


6. Results

6.1 Case A — Axial pull-through, rigid deck

- Peak von Mises stress in the inner fillet: 358 MPa (Fine), 361 MPa (Medium), 372 MPa (Coarse). Relative change Medium→Fine: −0.8%; Coarse→Medium: −3.0%.
- Estimated asymptote by two-point Richardson on Medium/Fine pair: ~352 MPa; inferred remaining discretization effect < 3%.
- Max principal stress at the same location: 405 MPa (Fine). Stress triaxiality remains low (dominantly bending plus in-plane shear).
- Deflection at tray leg center: 0.68 mm (Fine). Deck-leg reference rotations negligible due to fixity.
- Average bearing pressure at the leading tray hole arc: 96 MPa (Fine). No local spikes > 140 MPa observed with current simplifications.

Material comparison:
- Against 7075-T73 yield of 435 MPa, the von Mises peak yields FoS ≈ 1.22. If compared to 0.2% offset compressive yield (similar for this temper), FoS remains comparable. Utilization therefore ~82% at the worst location.

6.2 Case B — Axial pull-through, compliant deck supports

- Peak von Mises stress in the inner fillet: 371 MPa (Fine). Increase of ~3.6% relative to Case A as the bracket experiences minor load redistribution and additional leg bending.
- Deflection at tray leg center: 0.91 mm (Fine).
- Reaction distribution per deck hole reference shows the forward-most hole increases share by 4%, with the aft hole decreasing proportionally.

Sensitivity to load patch size:
- Re-running Case A with a reduced patch 40 mm × 24 mm (same total load) increases the fillet peak by ~2.9% (Fine mesh), consistent with a more localized application and slightly higher local bending.


7. Interpretation for Decision-Making

- The stress levels approach but do not exceed the elastic limit for the specified material temper, with a worst-case hot spot von Mises of 371 MPa under the compliant deck scenario. Using the rigid deck case as the workhorse (consistent with the stiff deck assumption in the integration fixture analysis), the fine mesh hot spot is 358 MPa.
- The mesh refinement sweep indicates diminishing returns between medium and fine meshes, with less than 1% change at the hot spot, and corroborated by the submodel trial. For this context (go/no-go release for machining), the fine mesh values are taken as representative.
- Displacement magnitudes are small relative to bracket thickness (0.68–0.91 mm), and geometric nonlinearity is not implicated for this load case.
- The sanity check calculation via strip theory estimating ~340 MPa peak provides an independent cross-check on the FEA order of magnitude and suggests that the model is capturing the primary bending and shear behavior of the leg-filleted corner.


8. Credibility Discussion

The following considerations were weighed in concluding whether the analysis results are reliable enough for releasing ATB-17 for machining of engineering development units:

- Problem framing and intended use: The analysis asks a narrow question (elastic margin at static limit load in a specific load direction during integration). The modeled physics (linear elastic, small-strain) match that question, and the applied loading envelope is traceable to the integration load book for this installation.

- Geometry treatment: Small fillets and chamfers not implicated in primary load transfer were suppressed to keep the mesh manageable. The primary stress raiser (R = 6.0 mm inside corner) is preserved with focused refinement. Bolt details are simplified consistently.

- Load and restraint realism: Load direction and distribution reflect the tray geometry and load path; the deck is treated as rigid in the main case, which aligns with the fixture design. The alternate case with support springs bounds changes due to compliance and shows a modest increase in local stress that does not change the decision.

- Numerical evidence from mesh sweeps: Two consecutive mesh refinements reduced the hot-spot stress by about 3% and then 0.8%. An extrapolated estimate suggests the fine-mesh result is within a few percent of the asymptote. The submodel check concurs.

- Equilibrium and kinematics: Reaction sums match applied loads to within 0.02%. Displacement fields are smooth, and the stress gradient through the fillet thickness behaves as expected for bending-dominated loading.

- Engineering cross-check: A simplified hand estimate arrives at a peak stress close to FEA values, building confidence that the structural idealization is reasonable.

- Material data: Assumed properties correspond to typical handbook values for the specified temper and thickness range. The analysis remains within the linear range for the reported decision (no plasticity invoked).

Risks and mitigations within this scope:
- The absence of fastener preload can slightly overstate relative motion tendencies at the interface, but with bonded constraints on the tray side and fixed deck references, the shear path is anchored. The bolt modeling approach is sufficient to capture gross stiffness and force paths for the present question.
- Deck stiffness variation affects hot-spot stress by a few percent in the explored range; using the rigid-deck assumption for approval of bracket geometry on the tray side is therefore reasonable.

Collectively, these elements support relying on the model outputs, for the specific decision at hand, with an understanding that margins are modest but positive for the selected material temper.


9. Limitations and Considerations Outside This Assessment

- Residual stresses from machining and surface treatments are not represented; these can shift local yield onset slightly and will be addressed during process planning if needed.
- Through-thickness grain structure and anisotropy of 7075-T73 plate are neglected; for 6.5 mm thickness and the stress state here, the isotropic approximation is common practice.
- Countersink details and local fretting at the tray interface are omitted; a bolted joint specification with proper installation torque and washer selection will be enforced by ME procedures to reduce risk.
- Thermal differentials across the bracket are negligible during the integration event and were not included.
- The analysis treats the deck as either very stiff or with a lumped spring; it does not include detailed deck cutouts or neighboring reinforcement. Changes to the deck design should be checked for their effect on bracket stress prior to flight release.
- This report does not cover other load directions (vertical shock, out-of-plane loads) or dynamic environments. A broader structural package will address those environments before qualification.


10. Reproducibility Notes

- Model build start point: ATB-17 v42 CAD, partitioned in Abaqus/CAE 2023.
- Element types: C3D10 globally, C3D15 in the fillet sweep zone.
- Mesh sizes: Coarse 2.4 mm, Medium 1.6 mm, Fine 1.2 mm at the fillet; bolts with 1.6 mm local sizing.
- Boundary conditions: Three deck bolt-ring reference points fixed (Case A) or connected to springs (Case B, k = 2.0×10⁷ N/m); tray face traction 12.5 kN over 50×30 mm patch along tray plane.
- Output sets: S, Mises; S, Max Principal; U; CF at reference points.
- Post-processing: Max stress probed over a path around the inner fillet; average hole-arc pressure for bearing indicator.

Note: The above is included to facilitate a re-run by a colleague if needed; it is not a step-by-step instruction. For full field recovery, use identical mesh partitions and size controls; minor deviations in local hot-spot values (±3–5%) are expected if the mesh topology differs.


11. Results Summary

- Peak von Mises at fillet (Fine): 358 MPa (rigid deck), 371 MPa (compliant deck).
- Utilization vs 435 MPa yield: 82% (rigid deck), 85% (compliant deck).
- Deflections: 0.68–0.91 mm at tray leg center.
- Reaction force error: <0.05%.
- Mesh refinement effect on hot spot: −3.0% (Coarse→Medium), −0.8% (Medium→Fine).


12. Decision

Based on the evidence presented in Sections 6–8, the finite element model of ATB-17 is accepted for:
- approving the bracket geometry for machining of engineering development units, and
- establishing elastic stress margins for the axial pull-through limit load during integration,

subject to the following conditions:
- use the fine or medium mesh settings described in Section 4 when rerunning the model for drawing changes; and
- maintain material selection as 7075-T73 (or higher-yield temper with equivalent E, if procurement so dictates).

This decision does not extend to environments or load directions not analyzed here.

Decision made by: Jane Park, P.E., Structural Analysis Lead, Launch Vehicle Program.


13. Distribution

- Program Chief Engineer
- Manufacturing Engineering, Machining Cell
- Systems Integration, Stage 1
- Quality Engineering, Materials and Processes


14. References

- LV-SM-1217, Structural Margin Requirements for Stage Integration
- LV-GD-402, Simplification Guidelines for FEA of Small Brackets
- LV-GD-407, Bearing Stress Evaluation in Bolted Joints
- MMPDS-18, Metallic Materials Properties Development and Standardization, 2024 Edition


15. Appendix — Selected Plots (described)

- Figure A1: Von Mises stress map on bracket, Fine mesh, Case A, showing inner fillet hot spot with a maximum of 358 MPa, smooth decay along the leg away from the corner.
- Figure A2: Displacement magnitude plot, Fine mesh, Case B, highlighting increased tip deflection to 0.91 mm relative to Case A.
- Figure A3: Mesh detail near fillet for Coarse, Medium, and Fine meshes; the Fine mesh shows three elements through thickness in the fillet with wedge elements aligned to curvature.
- Figure A4: Reaction force versus iteration plot, Case A, plateauing within 12 iterations; no oscillations indicative of unstable contact.

End of report.
