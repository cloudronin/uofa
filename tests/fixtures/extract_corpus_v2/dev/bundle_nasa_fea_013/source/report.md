# Structural Assessment Report: Avionics Bracket FEM

Project: LEO rideshare avionics shelf bracket  
Modeling lead: L. D. Kim  
Toolchain: Ansys Mechanical R2024.1 (nonlinear static; eigen extraction)  
Geometry source: STEP export BRK-112A_revD (CAD Team, 2026-05-07)

## 1. Background and Objectives

The BRK-112A bracket supports the inertial measurement unit (IMU) and a power converter on the avionics shelf of the rideshare bus. The component is a machined 7075-T7351 aluminum L-bracket with two ribs and a base flange tied to the avionics deck with four M6 bolts. The bracket must:

- Carry equivalent launch static loads derived from the 20 g vertical and 12 g lateral acceleration envelopes, distributed via the IMU and converter interface footprints, with a load path consistent with the stiffness of the fasteners and baseplate.
- Maintain a first bending/torsional natural frequency above 250 Hz with attached payload masses included as distributed lumped mass.
- Provide a positive margin against yielding at 25 C under combined load, with a minimum design factor of 1.25 on yield for primary structure.
- Limit relative slip at the bolted interface under lateral acceleration to negligible levels for cable strain relief.

The present analysis evaluates linear-elastic stresses, contact behavior, and modal characteristics. Fatigue life, thermal gradients, and manufacturing deviation effects are intentionally deferred to the next planning increment and are not treated in this cycle.

## 2. Modeling Approach

### 2.1 Geometry, Idealizations, and Interfaces

- Geometry: CAD features below 0.6 mm (chamfers, engraving) removed to avoid meshing artifacts. Fillets at base-rib junctions preserved (nominal 2.0 mm).
- Payloads: IMU and converter represented as rigid footprints tied to the upper flange via bonded contact and as distributed nonstructural masses (0.38 kg and 0.46 kg respectively). Centers of mass located per vendor drawings, with offsets of 12–18 mm above the flange.
- Fasteners: Four M6 bolts represented through coupled pretension sections at their shank centerlines; shank stiffness set by nominal core diameter and Young’s modulus of 7075-T73, threads not explicitly modeled. Head-to-bracket contact is frictional; thread engagement to the baseplate is not represented (baseplate modeled as kinematically fixed boundary at bolt hole interfaces).
- Contact: Bracket-to-baseplate (footprint) modeled as frictional surface-to-surface contact with coefficient of friction μ = 0.20 baseline; sensitivity runs varied μ 0.10–0.40. Bolt holes modeled with no-penetration contact to prevent unrealistic interpenetration at the periphery.

### 2.2 Loads and Boundary Conditions

- Equivalent static loads computed from mass scaling of the payloads:
  - Vertical: 20 g acting on the payload masses and bracket own mass; applied via remote mass features.
  - Lateral: 12 g applied orthogonal to vertical; combined with vertical in a single worst-direction envelope per integration of load cases supplied by Load Environments note LE-26-031.
- Bolt pretension: 3.0 kN per fastener nominal; sensitivity ±0.5 kN.
- Constraints: Baseplate attachment ring (12 M6 threaded holes) idealized as a kinematic constraint at the outer edge of the bracket base. Auxiliary analyses with springs (k = 1e8 N/m) added under the base showed <1% change in peak stress; fixed condition retained for simplicity.

### 2.3 Material Models and Data Sources

- Bracket: 7075-T7351, isotropic, E = 71.7 GPa, ν = 0.33, density 2810 kg/m^3. Yield stress in tension at 25 C: 503 MPa (AMS 4124 L/T direction, MMPDS-17 Table 3.7.2.0.1). For margins, 0.2% offset yield used.
- Baseplate: Modeled as rigid foundation; detailed compliance deferred to the next iteration of the global deck model. Justification: deck thickness 8.0 mm and close-in stiffeners provide an order-of-magnitude higher bending stiffness than the bracket over the footprint.

### 2.4 Solver Controls

- Static analysis: Large-deflection effects turned off after trial runs showed geometric nonlinearity accounted for <1.5% change in hotspot stress and <0.03 mm difference in deflection at the bracket tip. Augmented Lagrange contact with automatic normal stiffness; penetration tolerance 0.5% of element edge length. Convergence achieved with force residuals <0.2% of applied load and contact chattering eliminated via normal stiffness capping.
- Modal extraction: Block Lanczos; 12 modes requested to ensure capture of the first bending and torsion families.

## 3. Discretization and Quality Checks

- Element types: Dominantly 10-node tetrahedra (SOLID187) with quadratic displacement interpolation. Contact surfaces meshed with compatible quadratic faces.
- Local refinement: Feature-based sizing constrained maximum element edge length to 1.2 mm at fillet roots and bolt hole edges; 2.5 mm elsewhere on the bracket; 0.5 mm prism layers at contact interfaces.
- Mesh density sweeps:
  - Coarse: 176k elements; 3.0 mm global; 1.8 mm at fillets.
  - Medium: 352k elements; 2.0 mm global; 1.2 mm at fillets. (Baseline.)
  - Fine: 798k elements; 1.2 mm global; 0.8 mm at fillets.
- Convergence metric: Peak von Mises stress sampled at a path 1.0 mm away from the fillet root to mitigate the singularity tendency under contact/geometry intersection. Displacements and bolt load shares also tracked.

Mesh convergence outcome:
- Peak stress: 214 MPa (coarse), 201 MPa (medium), 209 MPa (fine) at the base inner fillet under combined load. Monotonicity not perfect due to contact patch evolution; Richardson extrapolation not applied. A grid-spacing-based index computed using generalized GCI yields 3.8% for medium→fine at p = 1.8 effective. Chosen mesh (medium) sits within ~4% of the apparent asymptote.
- Tip displacement under vertical: 0.334 mm (coarse), 0.319 mm (medium), 0.317 mm (fine).
- Bolt load distribution (largest): 28.7% (coarse), 29.3% (medium), 29.1% (fine) of total shear in the most loaded bolt.

## 4. Physical Check: Bench Loading of a Single Article

A quasi-static bench test was performed on a single machined bracket (serial BRK-112A-05) to exercise the dominant load path. The setup clamped the base flange to a steel platen using through-bolts to replicate the boundary condition footprint. A vertical load of 2.50 kN was applied upward at the IMU mounting pattern centroid via a clevis and load cell. Two 120-ohm strain gauges (gage factors provided by the vendor) were placed:

- SG-1: 2.0 mm above the base inner fillet on the rib, aligned with principal stress direction (per the FEA pretest map).
- SG-2: On the upper flange, 5.0 mm from the outer edge, longitudinal orientation.

Measured strains at peak load: SG-1 = 820 microstrain, SG-2 = 410 microstrain (±5 µε instrumentation accuracy, ±1% load cell). The medium mesh model under the same boundary and load conditions (material at room temperature, E per Section 2.3) predicted 780 µε (SG-1) and 435 µε (SG-2). Errors: -4.9% and +6.1%, respectively. The differences are within the combined measurement and modeling uncertainty bounds discussed in Section 6.

Note: The bench did not include lateral load simultaneously, and threads into the platen were not representative of the flight baseplate. However, for the vertical bending-dominated state targeted by this check, the setup exercises the primary bracket stiffness and hotspot location.

## 5. Results Summary

### 5.1 Stresses and Deformations (Baseline Medium Mesh)

- Combined g-load case:
  - Max von Mises stress: 201 MPa at the base inner fillet/rib intersection on the inboard side.
  - Secondary hotspot: 156 MPa around the first bolt hole periphery due to shear transfer.
  - Tip deflection at the outboard flange corner: 0.319 mm vertical, 0.046 mm lateral.
- Factor of safety against yield (per 503 MPa): 503 / 201 = 2.50. Meets the 1.25 minimum with ample margin.
- Contact status: The bolted interface remained mostly stuck under combined acceleration; slip predicted at the far corner under the 12 g lateral load remained below 7 microns when μ = 0.20. No gross separation observed; minor lift-off (≤ 2 microns) at one edge under lateral-only load does not persist in the combined case with pretension.

### 5.2 Modal Behavior

- With distributed masses representing the IMU and converter:
  - First bending mode: 318 Hz (out-of-plane bending about the base).
  - First torsion: 367 Hz (twist about the vertical).
  - Higher-order local bracket flange modes: > 520 Hz.
- The 250 Hz target is exceeded with at least 27% headroom.

## 6. Sensitivity and Uncertainty Exploration

### 6.1 Parameter Influence

A one-at-a-time sweep around the baseline assessed the influence of modeling choices and design parameters:

- Fillet radius at rib-base (±0.5 mm about nominal 2.0 mm): Changing from 2.0 mm to 1.5 mm increased peak stress by +12%; increasing to 2.5 mm decreased it by -9%.
- Bolt preload (2.5–3.5 kN): Peak von Mises changed by ±2.3%; contact slip decreased with higher preload but was low in all cases.
- Friction coefficient μ (0.10–0.40): Peak stress variation ±3.1%; localized slip expanded at μ = 0.10 but did not alter the global load path.
- Baseplate compliance: Replacing fixed support with a submodel that included an 8 mm deck plate and ribs changed peak stress by +1.7% and reduced the first bending mode by 6 Hz; differences are within the convergence and property uncertainty envelope.

Ranking of sensitivity (local slope normalized): fillet radius dominates, then friction, then bolt preload; boundary stiffness is small given the relative thickness.

### 6.2 Propagation of Input Scatter

To examine the robustness of results under plausible variability, a Latin hypercube sampling run with 200 draws propagated the following distributions through the baseline model (medium mesh):

- Young’s modulus E ~ Normal(mean 71.7 GPa, COV 3%).
- Vertical g-level ~ Normal(mean 20 g, COV 8%, truncated at ±3σ).
- Lateral g-level ~ Normal(mean 12 g, COV 8%, truncated at ±3σ).
- Friction coefficient μ ~ Triangular(min 0.10, mode 0.20, max 0.40).
- Bolt preload per fastener ~ Normal(mean 3.0 kN, σ 0.3 kN), independent between bolts.

Outputs tracked: peak von Mises at the base fillet and maximum interface slip magnitude. For each sample, solver convergence criteria matched the baseline.

Results:
- Peak stress distribution: mean 213 MPa; standard deviation 18 MPa; 95th percentile 246 MPa. Compared to yield 503 MPa, the one-sided reliability index assuming Gaussian tail behavior is comfortably > 10 for yielding, acknowledging that material yield also has variance not included here.
- Slip magnitude: 95th percentile < 12 microns at the most critical node. No gross slip regime encountered within the sampled space.

This analysis supports that the bracket’s safety margin is insensitive to reasonable fluctuations in loads and key contact parameters.

## 7. Credibility Considerations

This section collates the particulars that anchor confidence in the results.

- Fit to decision context: The model captures the required phenomena for the current gate — static strength and stiffness under combined launch-like accelerations and a modal check. Fatigue and thermal behavior are intentionally deferred; the conclusions stated here are restricted to room-temperature, single-application loading.
- Approximations made: The baseplate is represented as a rigid constraint, justified by local stiffness ratio checks and corroborated by a submodel trial (Section 6.1). Threads are not explicitly captured; this is mitigated by using pretension elements calibrated to shank stiffness and by monitoring interface slip. Geometry small features that do not carry primary load were removed; primary fillets were retained and locally refined.
- Source and quality of inputs: The material strength values are drawn from MMPDS-17 for 7075-T7351; the modulus distribution used for uncertainty analysis reflects supplier cert data from the same billet family (COV ~ 2–3%). Load levels trace to LE-26-031; the use of an equivalent static envelope is standard for sizing exercises at this stage and is consistent with bus-level dynamic characterization to be performed.
- Discretization effects: Three meshes were checked. While contact-driven hotspots do not produce a perfectly monotonic trend, displacements and bolt forces are within 1% between medium and fine. A simple grid-based index suggests the baseline mesh falls within about 4% of an asymptote for the reported stress metric. Hotspot evaluation avoids the singularity-affected surface line by using a path 1 mm off the root.
- Numerical robustness: Contact stabilization parameters were tuned to eliminate chattering without artificially stiffening the interface; penetration remains a small fraction of element edge length. Geometric nonlinearity is shown to have minimal influence for the present loading; solution residuals and iteration histories are archived with the run.
- Physical cross-check: A single-article bench load provided two-strain comparisons with errors of -4.9% and +6.1%. Though the fixture differs from the flight deck and only the vertical branch was exercised, the correlation supports the stiffness and stress mapping in the targeted region.
- Sensitivity and variability: The design is mainly sensitive to fillet geometry; plausible ranges in friction and pretension have small impact on peak stress. The 200-sample study indicates the 95th percentile peak stress remains below half of the yield limit under combined scatter in loads and interface parameters.
- Reproducibility and traceability: All model files, including geometry cleanup scripts, contact definitions, and parameterized load templates, are archived in the mission repository under tag MECH-24Q3-BRK-07. The sampling study records the random sequence seed (83427) and the exact solver build. Postprocessing macros capture the locations of stress readouts and modal shape animations, reducing operator-dependent variability.

Collectively, these points indicate the model and results are adequate for the current downselect and drawing release, provided the limitations below are observed.

## 8. Limitations and Open Items

- No plasticity modeled: The current check is strictly elastic. While margins to yield are large, localized plastic strains at micro-features (tool marks, sharp edges) are not assessed. This will be addressed only if subsequent inspections reveal edge conditions tighter than the drawing spec.
- Fatigue and durability: The model does not evaluate life under random vibration-induced stress cycles. A separate effort will use the deck-level dynamic environment to compute stress PSDs and perform a durability screen; the bracket fillets identified here will serve as candidate locations.
- Thermal strain: Temperature excursions during on-orbit operations and on the pad are not included. The bracket is aluminum and co-bolted to an aluminum deck; differential expansion with the payloads could produce bias loads but is not expected to change the launch case results. Thermal-mechanical coupling is deferred to the on-orbit load case review.
- Deck compliance fidelity: The baseplate is simplified as kinematically fixed in the primary runs. Although a submodel perturbation shows small influence, the final vehicle deck finite element model will provide a better capture of local flexibility. A quick-check with that deck model is recommended before CDR to confirm the 250 Hz target remains met with bus-level coupling.
- Manufacturing and tolerance buildup: The sensitivity study includes fillet radius variation, but other deviations (hole position, flatness, and surface waviness) are not included. Drawing tolerances should be verified to keep the fillet radius at or above 2.0 mm in the critical region.
- Limited test scope: The bench check exercised only the vertical load path and one article. Additional spot-checks (e.g., lateral-only) are recommended opportunistically if a second part is available; however, such testing is not on the current schedule.

## 9. Recommendations

- Accept the BRK-112A geometry for release to manufacturing with a callout to maintain a minimum 2.0 mm fillet at the rib-base intersection. If practicable, increase to 2.5 mm to reduce stress by approximately 9% with negligible mass impact.
- Retain the 3.0 kN pretension spec and surface finish consistent with μ ≈ 0.20 at the bolted interface; do not rely on friction for shear transfer — the design is stable even for μ = 0.10.
- Before CDR, run a quick modal and combined-load check using the integrated deck model to confirm mode placement and stress levels with global flexibility present.
- Document the two strain-gage locations on the as-built drawing as potential health-monitoring witness points for any future coupon or subcomponent characterization.

## 10. Data and File Inventory

- FE model: BRK-112A_revD_medium.cdb (Ansys input), mesh seed macros, and contact definitions in folder /structures/avionics/brk112a/fea/2026Q3.
- Postprocessing: APDL macro pp_brk_hotspot.mac plots the 1 mm offset-path stress; modal shape export macro pp_modes_brk12.mac.
- Bench test: Test notes and raw strain files TST-BRK112A-05-QL01, including photos and gauge placement sketches. Load cell calibration sheet appended.

End of report.
