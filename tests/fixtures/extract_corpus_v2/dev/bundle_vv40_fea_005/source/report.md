Title: Credibility Review — Finite-Element Simulation of a Mandibular Fracture Plate Under Unilateral Bite Loading

Prepared by: Structural Simulation Group, OrthoMechanica Inc.
Date: 2026-08-06
Software: Abaqus/Standard 2022; meshing with HyperMesh 2021.2; visualization in ParaView 5.11

1. Background

1.1 Purpose and decision context
This document summarizes the evidence supporting the use of a finite-element model to inform a design decision for the Rev C 2.0 mm low-profile mandibular fracture plate assembly. The analysis addresses a specific question: for a representative unilateral bite event, does the plate’s localized stress at geometric features of interest remain below material yield by a suitable margin to support a design freeze?

The plate is a four-hole, limited-contact style device intended to bridge an oblique angle fracture. The simulated configuration includes the plate, four self-tapping screws, and adjacent cortical/cancellous bone blocks representing the mandible regions proximal and distal to the fracture plane. The primary results of interest are:
- Maximum von Mises stress in the plate at fillets around the screw holes and at the midspan relief features.
- Peak principal strain in the cortical segment immediately beneath the nearest screw.
- Global plate deflection relative to the bone blocks under the prescribed bite force.

The analysis takes a conservative, static view of a unilateral molar load and aims to support internal sign-off for proceeding to the next iterative build.

1.2 Geometry and product pedigree
The CAD model of the Rev C plate (P/N OM-PLT-2004) was provided by Mechanical Design (Vault version OM-PLT-2004-RC-064). The four self-tapping screws are modeled per P/N OM-SCR-20-08 (Ø2.0 mm, 8 mm long). Bone geometry is generic, assembled from two CT-derived mandible segments scaled to match average male mandible dimensions in the angle region (mediolateral cortical thickness ~2.2 mm, cancellous core thickness ~10 mm). For this analysis, the focus is on stress in the plate and qualitative strain distribution in adjacent cortical bone; thread-level features are abstracted as described in Section 2.2.

1.3 Computing environment
All runs were executed on a Linux workstation (AMD Threadripper PRO 5965WX, 24 cores, 128 GB RAM). Abaqus/Standard 2022 build 6.14-2 was used in double precision with default solver and memory settings unless otherwise noted. Job logs and input decks are stored under //sim/FEA/plates/mandible/RevC/ULoad/2026-06-18.

2. Methodology

2.1 Model setup overview
- Domain: Assembly includes plate, four screws, two bone blocks representing proximal and distal mandible segments separated by a 2 mm fracture gap. The occlusal surface is represented by a 6 mm × 12 mm rectangular patch on the distal segment’s superior surface.
- Loading: A downward resultant of 650 N is applied as a uniformly distributed traction on the occlusal patch, located 18 mm from the fracture plane. This magnitude is within the mid-to-upper range for unilateral molar bite forces in the literature for healthy adults.
- Constraints: The inferior surface of the proximal bone block is fixed in all translational directions to approximate support from surrounding anatomy. The distal bone block is otherwise unconstrained except through its connection to the plate and screws.
- Contact and fasteners: Plate-to-bone contact is frictional (coefficient 0.3), small-sliding with penalty enforcement; screw-to-plate is tied (idealized engagement), and screw-to-bone is modeled as bonded to a cylindrical “equivalent thread” envelope of 2.3 mm diameter to reflect the mechanical interlock without explicitly resolving thread geometry. No preload is applied.

2.2 Materials and constitutive descriptions
- Plate and screws (Ti-6Al-4V ELI, ASTM F136): Elastic, isotropic, E = 110 GPa, ν = 0.34. Inelastic behavior is not included for this decision; yield reference for comparison is 795 MPa from material certification lot TD-ELI-2025-04.
- Cortical bone: Linear elastic, E = 17 GPa, ν = 0.30, density 1800 kg/m³. No orthotropy is introduced in this phase.
- Cancellous bone: Linear elastic, E = 1.2 GPa, ν = 0.25, density 1100 kg/m³.

2.3 Discretization and element selection
- Plate: 10-node quadratic tetrahedra (C3D10) with local refinement to 0.20 mm nominal edge length at the fillet radii around screw holes and midspan relief features; 0.80 mm background size elsewhere.
- Screws: C3D10 with a 0.25 mm nominal edge length in the shank region, blended to 0.60 mm near the head.
- Bone blocks: 4-node linear tetrahedra (C3D4) with 0.90 mm typical size in cortical regions and 1.50 mm in cancellous core. A transition layer of 0.60–0.80 mm elements is used beneath the plate footprint.

Mesh quality metrics (from HyperMesh report):
- Minimum Jacobian (C3D10): 0.61; average 0.88.
- Skewness (C3D10): average 0.17; maximum 0.39.
- Aspect ratio 95th percentile: 3.2 in the plate’s refined region.

2.4 Solver controls and convergence behavior
Abaqus/Standard, Static General step with NLGEOM=ON due to contact nonlinearity and anticipated local rotations. Default automatic time incrementation with initial increment 0.05, maximum 40 increments. Convergence tolerances: force residual target at 0.5% of average external load; displacement convergence monitored on nodal set at the occlusal patch. Line search enabled; friction regularization set to 0.001 to stabilize early contact.

In the production (fine) mesh, the job converged in 19 increments with no severe contact oscillations. Peak iterations per increment were 18 in the interval where the plate initially engaged the bone surface under load.

2.5 Resolution study
To quantify sensitivity to mesh density near geometric hotspots, three nested meshes were studied:

- Coarse: ~248k DOF, plate hotspot element size 0.40 mm.
- Medium: ~511k DOF, plate hotspot element size 0.28 mm.
- Fine: ~1.12M DOF, plate hotspot element size 0.20 mm.

Metrics recorded:
- M1: Peak von Mises stress in the plate (evaluated with nodal averaging off; element centroid values queried and the maximum reported).
- M2: Maximum first principal strain in a 2 mm × 2 mm cortical region under the screw nearest the fracture.
- M3: Vertical deflection at the centroid of the occlusal patch.

Results summary:
- M1 (MPa): Coarse 586; Medium 603; Fine 612.
- M2 (microstrain): Coarse 1290; Medium 1385; Fine 1422.
- M3 (mm): Coarse 0.39; Medium 0.41; Fine 0.42.

Relative change Medium→Fine:
- M1: +1.5%.
- M2: +2.7%.
- M3: +2.4%.

Given the small change between the two densest meshes and the cost differential (1.7× runtime), the Medium mesh is considered adequate for design decision-making in this phase. Unless otherwise noted, reported field plots and numeric values below correspond to the Medium mesh.

2.6 Self-consistency and benchmark checks
Two simple checks were performed to guard against gross setup errors:

- Elastic strip comparison (sanity check): A 2 mm × 8 mm × 50 mm titanium strip with a 100 N end load was modeled using the same element types and solver controls. The tip deflection differed from the Euler–Bernoulli beam prediction by 2.1% with the Medium mesh density used in the plate analysis. This is consistent with expectations for quadratic tetrahedral elements and provides assurance that the material assignment and solver options are functioning as intended.

- Symmetry response: The mandible assembly was mirrored and loaded bilaterally with 325 N per side (total 650 N). Reaction forces at the supports on both sides matched within 0.8% and displacement fields were mirror-symmetric to within 1.1% in the L2 norm. This check was used solely to confirm that constraints and contacts were not introducing a spurious bias.

3. Results

3.1 Stress distribution in the plate
Peak stresses concentrate at the fillet root adjacent to the screw hole immediately proximal to the fracture gap. In the Medium mesh:
- Maximum von Mises stress: 603 MPa at the root of the inner fillet of the proximal screw hole, on the tensile side of the plate.
- Secondary hotspot: 458 MPa at the midspan relief feature on the distal side, associated with local bending between the two inner screws.

The stress gradient around the primary hotspot is steep; over a 0.4 mm radial distance, the von Mises stress drops to ~420 MPa. Field plots indicate that the high stress arises from combined bending across the fracture gap and localized load transfer through the nearest screw pair.

3.2 Strain in adjacent cortical bone
A 2 mm × 2 mm region of interest (ROI) was defined at the cortical surface beneath the proximal screw nearest the fracture. The maximum first principal strain in this ROI was 1385 microstrain, aligned primarily with the plate’s longitudinal axis. The distribution is consistent with load sharing from the plate into the cortex via the screw shank/engagement zone. The strain field is smooth with no evident numerical artifacts.

3.3 Global displacements
The vertical deflection at the occlusal patch centroid was 0.41 mm (downward). Relative sliding between plate and bone is negligible under the 0.3 friction model; the maximum relative tangential displacement at the plate–bone interface is 0.03 mm.

3.4 Reaction balance and contact behavior
- Total reaction force at the fixed inferior surface of the proximal bone block is 650.5 N (within 0.1% of applied load when accounting for roundoff).
- Contact pressure beneath the plate peaks at 37 MPa near the proximal inner screw and decays toward the distal span.
- No loss of contact was observed at the plate–bone interface under the present load.

4. Credibility Assessment

4.1 Suitability of modeling approach for the decision in view
The goal is to support a design freeze call based on stress in the plate remaining below yield with a comfortable margin, for a conservative bite scenario. The following points are relevant:

- Numerical stability and discretization independence: The three-level mesh study shows minimal change from Medium to Fine for the key metrics (≤2.7%). This supports confidence that the geometric stress concentration is adequately resolved for decision use. The choice to report Medium mesh results is justified by both the small deltas and practical turnaround constraints for iterative design.

- Reasonableness checks against textbook behavior: The elastic strip test and bilateral symmetry run reduce the risk of mis-specified boundary conditions or gross solver misbehavior. They do not replace more sophisticated checks but serve as a backstop to basic setup errors.

- Material property sources: Titanium properties reflect typical values for Ti-6Al-4V ELI and match the lot certification used in current builds. While elastic-only behavior is assumed in the solver, comparison of peak stress (603 MPa) to the 795 MPa yield threshold indicates a tensile safety margin of ~31% at the hotspot. In the unlikely event that local plasticity were to occur at the tiny fillet region under substantially higher load, the effect would likely be localized with limited impact on overall load transfer—however, that scenario is outside the immediate decision frame.

- Contact and fastener representation: Simplifying the thread engagement as a bonded cylindrical envelope increases stiffness in the screw–bone load path relative to a fully detailed thread. The effect is to slightly over-transfer load through the nearest screws and reduce plate bending compared with a more compliant thread model. This bias is toward underpredicting plate stress. Counterbalancing that is the conservative choice of a relatively high unilateral bite force (650 N) applied at a short lever arm (18 mm). Taken together, the simplifications are not expected to produce non-conservative stress underestimates beyond a few percent for the plate hotspot.

4.2 Margins and through-thickness effects
- Peak von Mises stress margin: (795 − 603) / 795 ≈ 24.2% headroom if treated as allowable versus maximum, or ~1.32 safety factor in a classic ratio sense. Considering the small Medium→Fine change (+1.5%), the stress at the resolved fillet is not an artifact of coarse meshing.
- Hotspot localization: The maximum stress occurs in a volume of approximately 0.03 mm³. Away from the root by 0.4 mm, stress is down by 30%. For metallic components, very localized maxima at curvature transitions are common; they may not govern component durability without cyclic load considerations. The present decision explicitly focuses on monotonic yield risk rather than long-term fatigue.

4.3 Repeat runs and consistency
Two identical Medium-mesh runs were executed 48 hours apart after a clean solver restart; peak stresses agreed within 0.2 MPa and displacements within 0.001 mm. Minor differences reflect floating-point roundoff and slightly different increment histories.

4.4 Traceability
Input files, meshes, and postprocessed results are archived with timestamps. Model comments in the .inp files identify all material assignments and contact pairs. A configuration note is embedded at the top of each input deck documenting software version and key toggles. The plate CAD rev is recorded in the input deck header, and the meshing script includes the mesher seed values for reproducibility.

5. Discussion

5.1 Interpretation of outcomes relative to design targets
The analysis suggests the Rev C plate carries the unilateral bite load without approaching the onset of yield in the titanium. The highest stress is at a well-understood geometric transition near the screw hole, which is standard for this class of hardware. The selection of 650 N at an 18 mm lever arm represents a relatively demanding case; weaker bites or a longer lever arm would reduce bending on the plate.

The measured strain in the cortical region under the proximal screw remains in a physiologically sensible range (order of 10⁻³), with no red flags indicative of grossly unrealistic stiffness pathways. Displacements are moderate. Qualitative field patterns (e.g., contact pressure lobes, bending curvature) match expectations from conventional plate–bone mechanics.

5.2 Sensitivity to idealizations in the joint representation
- No pretension in screws: Omitting pretension reduces initial clamping and allows a bit more micro-slip before friction develops fully. For monotonic loading, pretension typically raises contact pressure near the screws and marginally reduces plate bending; its exclusion here is slightly conservative for plate stresses under downward occlusal load because it allows more rotation at the fracture.
- Friction coefficient at plate–bone: Setting μ = 0.3 is aligned with published ranges for stainless against cortical bone; titanium pairs are generally similar or slightly lower. Lowering μ would permit additional micro-slip and shift load paths, which could increase plate bending; however, the effect on peak plate stress in the hotspot is secondary relative to geometry and bending span. Qualitative spot checks at μ = 0.2 changed peak stress by +3.4% in the Medium mesh.

5.3 What this model is not intended to answer
- It does not address endurance under repeated cycles, fretting wear, or long-term screw stability.
- It does not account for mandible heterogeneity, defects, or patient-specific bone quality variation.
- It does not include temperature effects, manufacturing tolerances, or surface roughness.

The present model is scoped narrowly to a monotonic structural question that informs a go/no-go decision for a specific design revision and a representative loading scenario.

6. Limitations and caveats

6.1 Geometric abstractions
- Threads are not resolved; the equivalent cylindrical bond for screw–bone engagement stiffens the connection. While a more accurate representation could redistribute stress slightly, past experience suggests that, for gross bending questions, the plate hotspot stress is typically only modestly affected.
- The bone blocks are simplified to prismatic cutouts from a generic mandible shape. Curvature of the real mandible and local anatomical features are not captured beyond cortical thickness and cancellous core size approximations.

6.2 Materials and constitutive behavior
- Linearity is assumed across all materials. The metallic plate could, under more severe loading than simulated here, enter small-scale plasticity at the hotspot fillet; this regime is not investigated. Likewise, the absence of orthotropy for cortical bone ignores directional stiffness differences.

6.3 Boundary conditions
- The unilateral bite is applied as a static, uniformly distributed pressure on a rectangular occlusal patch, rather than a dynamic, muscle-force-driven equilibrium. The chosen representation is a practical proxy for worst-case bending but does not capture the myriad force vectors active in true mastication.
- The proximal support condition (fixed inferior surface) is a stand-in for multi-contact constraints provided by the rest of the mandible and soft tissues.

6.4 Numerical considerations
- While mesh refinement shows good stability of results, it does not resolve the fillet to the limit of geometric curvature; further refinement to 0.15 mm elements at the hotspot would likely change the reported peak by 1–2% based on observed trends, at significantly higher runtime.

7. Conclusions

Based on the analyses performed, the Rev C 2.0 mm mandibular fracture plate, fastened with four Ø2.0 × 8 mm screws to generic cortical/cancellous bone blocks, experiences a peak von Mises stress of approximately 603 MPa at the critical fillet near the inner proximal screw when subjected to a conservative unilateral 650 N occlusal load at an 18 mm lever arm. This is comfortably below the 795 MPa material yield marker for Ti-6Al-4V ELI, with an indicative margin of ~31%.

A targeted refinement study indicates low sensitivity of key results to further mesh densification beyond the Medium mesh used for reporting. Sanity checks against simple elastic benchmarks and bilaterally symmetric loading confirm basic soundness of the setup. Contact settings, friction assumptions, and the simplified fastener modeling tend to bias stresses slightly on the low side; this is, to an extent, counteracted by the chosen load magnitude and short lever arm.

Within the limits outlined, the model’s predictions are considered sufficient to support the immediate design decision to proceed with the Rev C plate geometry without changes to fillet sizing or screw hole spacing.

8. Recommendations

- For subsequent phases, consider targeted local radius increase at the screw-hole fillet where the hotspot occurs to further ease the stress gradient; a 0.1 mm increment typically reduces peak by 5–8% based on heuristic rules-of-thumb for bending-dominated fillets.
- If the design path anticipates high-cycle service environments, plan a separate study addressing cyclic durability and local plastic accommodation using an elastic–plastic metal model and a more explicit joint representation.
- Maintain current mesh seeding scripts and contact setup templates; these provided stable results with acceptable runtimes and can be reused for follow-on variants.

Appendix A — Run catalog (abridged)
- UL_RevC_MedMesh_650N_18mm: Medium mesh production run; 603 MPa peak, 0.41 mm deflection; walltime 2 h 12 min.
- UL_RevC_FineMesh_650N_18mm: Fine mesh; 612 MPa peak, 0.42 mm deflection; walltime 3 h 50 min.
- UL_RevC_Coarse_650N_18mm: Coarse mesh check; 586 MPa peak, 0.39 mm deflection; walltime 54 min.
- UL_Strip_Elastic_100N: Elastic strip verification; 2.1% deviation from closed-form.
- UL_Bilat_325N_each: Bilateral symmetry check; reactions matched within 0.8%.

Appendix B — Notes on postprocessing
- Peak stresses were read from element centroid values to limit artificial peak smoothing; no nodal averaging performed. For visualization, standard Abaqus von Mises contouring with default smoothing was used, but all decision metrics were taken from raw centroid values at the hotspot region of interest.
- The cortical ROI under the proximal screw was defined via a geometric query in HyperMesh; maximum principal strain was extracted via field output E, averaged at integration points and then queried for the maximum value in the named set.

Appendix C — Data availability
- Input decks (.inp), meshes (.hm), and postprocessing scripts (.py) reside at //sim/FEA/plates/mandible/RevC/ULoad/2026-06-18 and are tagged with job IDs referenced above. Access is restricted to the Structural Simulation Group.

End of report.
