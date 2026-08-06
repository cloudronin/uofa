Title: Credibility Assessment Report — FEA of the Starboard Avionics Bracket (SAB) Under Launch Quasi-Static Loads

Document ID: STR-FEA-2319
Prepared by: Structures Analysis Group, Orbital Systems Lab
Date: 2026-07-28

1. Background and Intended Use

The Starboard Avionics Bracket (SAB) supports the Heliostat Navigation Unit and associated cabling on the mid-deck of the vehicle. The bracket is machined from Al 7075-T7351 and fastened to a composite panel via four M8 Class 10.9 bolts and two dowel pins. The finite-element analysis summarized here is intended to inform a go/no-go decision for preliminary release of the bracket geometry for manufacturing and to support loads handoff to the panel team. The specific questions addressed are:
- Are local stress levels at fillets, fastener holes, and interfaces acceptable for quasi-static launch load cases?
- Is the predicted load sharing among fasteners consistent with joint design limits?
- What spread in predicted response arises from plausible ranges in loads and material properties?

The scope of this assessment is limited to static envelope loads representing the upper percentile of the random vibration environment. High-cycle fatigue, detailed dynamic response, thermal distortions, and transport/handling load cases are outside this assessment.

2. Overview of the Computational Model

Software and solver: Abaqus/Standard 2021 HF4, implicit static.

Geometry: The bracket CAD (rev SAB-CAD-r15) includes the primary L-section, a stiffening rib, two lightening pockets, and a 12 mm radius fillet at the knee. The composite panel is idealized as a rigid foundation for the purpose of stress evaluation in the bracket; local compliance of the panel is neglected in this model.

Elements and mesh: The bracket is meshed predominantly with C3D10 (quadratic tetrahedral) elements. The fillet and bore regions use curvature-based refinement with target edge lengths of 0.6–1.0 mm on the finest grid. The remainder of the solid uses 1.5–3.0 mm elements. Bolt shanks are represented by distributed MPC-type connectors with axial and shear stiffnesses fit to equivalent shank/bearing behavior; preload is represented as an initial axial force. Washer stiffness is lumped into the connector properties. Local bonded contact patches represent the washer-to-bracket interface to capture near-field compression.

Boundary conditions: The bolt connectors are grounded to a kinematic reference that stands in for the panel. Two 6 mm dowel constraints fix lateral motion. The instrument mass is represented as a 8.6 kg lumped point with stiffnessless coupling to the mounting face via a rigid body constraint to match the mounting plate behavior. Gravity and equivalent static accelerations are applied at the instrument mass and bracket mass.

Loads: Quasi-static accelerations representing the 99th-percentile envelope of the random environment: 13.8 g axial (vehicle +Z), 11.2 g lateral (+Y), and 9.6 g lateral (+X) applied in three separate loadcases and one combined vector case. Bolt preload target is 16 kN per M8 bolt, achieved through the connector initial force.

3. Modeling Assumptions and Idealizations

- The composite panel is treated as rigid. This is a deliberate simplification for bracket sizing; panel deflection under load is small relative to bracket local deformations for the present load levels, per prior panel compliance estimates (order <10 μm at the joint).
- The joint interface is assumed to be fully clamped with no gross slip; micro-slip is not represented. Contact nonlinearities are not included beyond the bonded washer region, which can suppress local edge lift-off.
- Material behavior is linear elastic up to yield and isotropic; plasticity is not activated. This assumption is adequate for the intended decision (no plastic design).
- Thermal preloads are neglected in the static cases.
- Machining tolerances are not represented explicitly; hole misalignment and surface waviness are not included.

4. Material Properties and Sources

Bracket: Aluminum 7075-T7351 per MMPDS-17 Table 3.3.2.0(c)
- Young’s modulus: 71.7 GPa
- Poisson’s ratio: 0.33
- Yield strength (room temp): 435 MPa
- Ultimate strength (room temp): 505 MPa

Bolts: Class 10.9 per ISO 898-1
- Effective axial stiffness of each fastener/washer stackup: 14.0 MN/m (fitted from shank length and grip)
- Preload target: 16 kN

Instrument mass: 8.6 ± 0.2 kg (mass property report NAV-HELI-112)

Acceleration environment: Derived from vib acceptance levels ENV-QL-2102; static equivalent factors computed by Loads & Dynamics as 13.8/11.2/9.6 g in the principal axes.

5. Mesh Refinement Study

A four-level refinement sequence was executed, holding the global setup fixed and decreasing the target element size in the high-stress regions:

- M1 (coarse): 142k elements; throat fillet target h = 1.6 mm
- M2: 286k elements; fillet target h = 1.2 mm
- M3: 534k elements; fillet target h = 0.9 mm
- M4 (finest): 1.02M elements; fillet target h = 0.6 mm

We tracked:
- Peak von Mises in the knee fillet under the combined vector case
- Average of principal stresses over a 2 mm path at the gauge lines (see Section 6)
- Connector axial forces

Results for peak von Mises:
- M1: 224 MPa
- M2: 211 MPa
- M3: 203 MPa
- M4: 198 MPa

An observed order-of-accuracy estimate based on Richardson fits across M2–M4 yields p ≈ 1.85 (expected is ~2 for quadratic tets in bending). Extrapolating to zero size predicts 192 MPa. We adopt 198 MPa (M4) for reporting and treat 6 MPa as a numerical discretization contribution to uncertainty for fillet peak stress. Connector forces stabilized to within 1.3% between M3 and M4.

6. Bench Test Comparison

A static pull test was conducted on SAB prototype P/N SAB-001-PT, mounting the bracket to a steel surrogate plate with identical bolt pattern and dowels, with a vertical load applied via a clevis at the instrument interface. Three uniaxial strain gauges (HBM 1-LY41-3/350) were placed at:
- G1: Inside knee fillet, 1.5 mm from fillet toe, 45° orientation
- G2: Rib mid-height, longitudinal
- G3: Near upper bore edge, transverse

Load steps: 1 kN to 6 kN in 1 kN increments; preload set to 16 kN per bolt using a hydraulic tensioner with readback.

Measured vs model-predicted strains (M4 mesh, combined vector direction mapped to vertical for the test configuration by load equivalence; modelling uses equivalent boundary):

At 6 kN:
- G1: Test 1580 με; Model 1710 με (8.2% high)
- G2: Test 620 με; Model 582 με (6.1% low)
- G3: Test 910 με; Model 866 με (4.8% low)

Across all steps and gauges, the mean absolute percentage difference is 6.7%. At low load (1–2 kN), the model slightly overpredicts due to assumed rigid foundation; at 5–6 kN the errors are consistent and monotonic. We note the local near-fillet reading is the largest discrepancy, which is expected given the missing detailed contact representation of the lower clamp region.

7. Sensitivity Exploration

We probed the effect of variations in inputs over anticipated bounds:

- Young’s modulus: 69–74 GPa (manufacturing and temperature spread)
- Bolt preload: 12–20 kN per fastener (scatter from installation)
- Instrument mass: 8.4–8.8 kg
- Axial acceleration: 12.5–15.0 g
- Lateral accelerations: ±1.0 g within nominal envelope
- Friction at washer-bracket interface: treated implicitly in connector model stiffness; the effective tangential stiffness was varied ±30%

Outcome metrics:
- Peak von Mises in knee fillet (combined vector case)
- Max bearing stress next to upper bolt hole
- Maximum single-bolt axial load

Main findings:
- Peak fillet stress scales primarily with axial acceleration and secondarily with preload via local clamping effects that shift load paths. Over the ranges above, peak von Mises varied from 181 MPa to 236 MPa (baseline 198 MPa), with the upper bound occurring at high acceleration and low modulus simultaneously.
- Maximum single-bolt axial force ranged from 17.6 kN to 21.9 kN. Preload did not significantly change the maximum post-load connector force due to the stiffness hierarchy of the joint.
- Bearing stress at the upper bore edge changed within ±9% as a function of lateral acceleration perturbations.

The design is most sensitive to the acceleration vector magnitude and modulus; preload scatter exerts a secondary influence on bracket stress but matters for joint limit checks.

8. Aggregate Uncertainty Estimate

We combined three contributors: numerical resolution, load magnitude, and material stiffness. Using a simple sampling approach (Latin Hypercube, 200 samples) over the ranges listed above, holding geometry fixed (M4 mesh), we computed:
- 95th percentile of peak von Mises: 252 MPa
- 99th percentile of peak von Mises: 267 MPa

For bolt axial forces:
- 95th percentile maximum among the four bolts: 22.4 kN

We treat these quantiles as characteristic high-end responses for the intended decision. The sampling did not include any plasticity or contact nonlinear behaviors; results are conditional on the linear assumptions described earlier.

9. Robustness Checks

The M4 model was re-solved with:
- Double-precision vs default mixed precision: identical results to within 0.2 MPa at the fillet peak.
- Different linear solver tolerances (1e-8 vs 1e-10 residual): stress differences <0.3%.
- Threading variations (1 vs 8 threads): minor differences in element-by-element ordering produced max stress changes <0.5%.

Re-running on a second workstation (Xeon 6258R vs i9-12900K) produced bitwise-identical connector force outputs and nodal reactions; nodal displacement fields differed in the fifth decimal place only due to floating-point summations.

10. Results Summary

- Baseline combined-vector case, M4 mesh:
  - Peak von Mises in fillet: 198 MPa
  - Max bearing stress at upper bore: 265 MPa
  - Max single-bolt axial force: 21.3 kN

- High-end estimate (95th percentile from sampling):
  - Peak von Mises in fillet: 252 MPa
  - Max single-bolt axial force: 22.4 kN

- Allowables and margins:
  - Yield allowables (static): 435 MPa / 1.25 = 348 MPa -> margin at 95th percentile stress: (348/252) − 1 = 0.38
  - Ultimate for joint: For Class 10.9 M8, typical proof 45 kN; using a design limit 0.75×proof = 33.8 kN, margin on max 22.4 kN: (33.8/22.4) − 1 = 0.51

The bracket meets the static stress criteria with comfortable but not excessive margins when uncertainty is accounted for. The joint axial load margins are also adequate under the assumed stiffness representation.

11. Credibility Considerations

- Model-to-test agreement at instrumented points is within approximately 7% on average at relevant load levels. The largest discrepancy is at the fillet where geometric detail and contact effects are most pronounced but remains within 9% at the test upper step. For our purpose—evaluate elastic stress levels—the observed alignment increases confidence that the model captures the dominant load paths.

- The mesh refinement sequence demonstrates clear trend-to-convergence for peak stresses and fastener forces. The residual change from M3 to M4 is small relative to the decision margins; nonetheless, we retained the finest grid for reported values and treated the residual as a contributor to the uncertainty band.

- The uncertainty exploration shows that when expected variability in load levels and modulus is carried through the model, the 95th percentile stress remains comfortably below the adjusted yield limit. This directly addresses the decision margin under plausible perturbations.

- Joint behavior is treated via equivalent connectors tuned to elastic shank and bearing behavior without micro-slip or separation. While sufficient for bracket sizing, this idealization can under-represent peak edge stresses at the washer footprint and will not capture non-linear hysteresis under vib loads. Our check with test strains indicates the simplification does not mask gross errors for the static decision.

- The bracket is analyzed as if mounted to a rigid base. For static sizing of the bracket itself, prior panel stiffness sketches support this as reasonable; if panel cutout growth or local compliance is significant in future revisions, coupling with a submodel would be warranted.

12. Limitations and Deferred Work

- Dynamic vib response and associated high-cycle fatigue life are not assessed here. The static envelope treatment is appropriate for plasticity avoidance but insufficient for durability checks.
- Thermal gradients and bolt preload changes induced by temperature cycles are not captured. If the mounting environment includes significant thermal swings, a combined thermo-mechanical model would be advisable.
- Manufacturing tolerances (hole location errors, surface flatness, fillet radii departures) are not included. Tolerance stack-up analysis may adjust local peak stress predictions.
- Plasticity and contact nonlinearity are not enabled. The assessment is limited to the elastic regime. For ultimate load checks or if higher loads are later required, a non-linear material/contact run should be performed.
- The bench test used a steel surrogate plate with very high stiffness. The actual composite panel may introduce small differences in clamping compliance; these are judged small for the static problem but should be revisited if panel stiffness is reduced in later designs.

13. Discussion

The analysis addresses the key questions for preliminary bracket release under static launch loads. The mesh refinement work constrains numerical error in the hotspot, and the gauge-based comparison gives a reasonable calibration of the model’s ability to capture strains in critical regions. The spread analysis quantifies how much headroom exists when main input uncertainties are acknowledged.

The model exhibits the expected qualitative behavior: the knee fillet is the hotspot; loads flow from the instrument interface through the rib and into the bolt group; connector forces distribute unevenly with the upper bolts taking the largest share in the combined vector case. This is consistent with free-body sketches and with gauge ratios. The quantified margins on yield (0.38 at the 95th percentile) and on fastener loads (0.51 with respect to design limit) indicate the bracket, as modeled, is appropriately sized for the intended operation.

Assumptions that simplify the interface—chiefly, the rigid panel and bonded contact approximations—tend to make the bracket slightly stiffer and can shift local strain distributions. The test shows the model is slightly conservative in the knee region at low loads and slightly non-conservative at higher loads within the stated error bounds; overall, the error bias is small relative to margins and does not alter the conclusion for static stress allowables.

14. Conclusion

- The finite-element model of the SAB produces stress and joint load predictions that are consistent with bench strain data at multiple locations and loads to within approximately 7% on average.
- Mesh refinement reduces hotspot stress by ~13% from coarse to fine and indicates remaining numerical error on the order of 3% at the fillet peak.
- When reasonable scatter in loads and material stiffness is considered, the 95th percentile stress remains below the adjusted yield threshold with a margin of 0.38; joint loads remain below their design limits with a margin of 0.51.

15. Recommendation and Decision

Decision: The SAB finite-element model and its results are accepted for sizing the bracket against quasi-static launch loads and for release of Rev r15 geometry to manufacturing for prototype build. This acceptance is for elastic stress and joint axial load assessments only.

Conditions:
- The model is not approved for evaluating dynamic vib fatigue, thermal preload effects, or plastic collapse. Those evaluations must be performed with models that explicitly include the relevant physics before CDR.
- If panel stiffness changes by more than 25% or if the bolt pattern is altered, the analysis should be repeated with updated boundary representation.

Decision authority: Structures Analysis Lead (M. K. Santoro), with concurrence from Loads & Dynamics Lead (R. J. Fedor).

Appendix A: Detailed Node and Element Statistics
- M4 element count: 1,018,432; node count: 1,562,044
- Max element aspect ratio at fillet region: 1.9
- Minimum Jacobian across mesh: 0.76 (Abaqus quality metric)

Appendix B: Gauge Location Coordinates (in bracket local CSYS)
- G1: x = 28.4 mm, y = 14.2 mm, z = 6.0 mm
- G2: x = 42.0 mm, y = 0.0 mm, z = 9.5 mm
- G3: x = 60.7 mm, y = −7.3 mm, z = 12.1 mm

Appendix C: Solver Settings
- NLGEOM off; step time 1.0; automatic stabilization off
- Contact: bonded constraints at washer footprints only
- Convergence criteria: residual force 1e-8 of reference; displacement 1e-9 m absolute
