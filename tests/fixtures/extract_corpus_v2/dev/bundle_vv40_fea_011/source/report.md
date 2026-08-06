To: Aerial Imaging Program Lead
From: M. Chen, Structures
Date: 2026-08-06
Subject: FEA credibility memo — gimbal bracket (P/N 41-3721) static load case

Summary
We ran a finite-element assessment for the aluminum camera gimbal bracket to support the 30 N lateral disturbance load at the lens centerline. The goal is to clear preliminary sizing and hole pattern definition for the PDR freeze. The analysis was executed in Ansys Mechanical 2023 R2 on the Rev C CAD (SolidWorks export 41-3721-C.step) with a linear material model for 7075-T6. Results show acceptable stress and stiffness margins for the stated load path using the current mounting scheme.

Model setup
- Geometry: As-designed Rev C bracket with chamfers and the 2.5 mm inside corner fillet retained. Fastener holes modeled at nominal clearance; no thread engagement modeled in the bracket.
- Material: 7075-T6 isotropic, E = 71.7 GPa, ν = 0.33, yield = 505 MPa, Rp0.2 = 503 MPa. No plasticity.
- Elements: Quadratic tetrahedra (10-node), with contact-compatible formulation around the clevis lugs.
- Contacts: Bracket-to-bolt shank treated as frictional (μ = 0.20). Bolt heads and washers represented via rigid pads bonded to bracket surfaces to approximate load spread.
- Loads/BCs: Base flange nodes tied to the mounting plate (all DOF fixed). A 30 N lateral force applied as a pressure over the lens seat annulus (Ø42–Ø46 mm band) at the forward face, aligned with airframe +Y. Two M4 bolts preloaded to 3.0 kN each using pretension sections.

Mesh refinement and numerics
We completed a three-level mesh refinement around the inner fillet and bolt holes:
- Coarse: ~0.85 mm target in critical zones, 0.3 M elements
- Medium: ~0.55 mm target, 0.8 M elements
- Fine: ~0.40 mm target, 1.6 M elements

Peak von Mises at the fillet stabilized within 6.2% between medium and fine meshes; strain energy changed by 2.5% over the same step. Deflection at the optical axis changed less than 1.8% medium-to-fine. We used the sparse direct solver with default convergence criteria; no convergence warnings were issued.

Key results (fine mesh)
- Max von Mises stress at inner fillet toe: 342 MPa
- Secondary peak at bolt hole edge: 298 MPa
- Deflection at optical axis: 0.38 mm lateral
- Relative motion at bolt interfaces remained below 4 µm; no slip predicted with μ = 0.20 and stated preload

These satisfy current internal targets (stress < yield and lateral tip deflection ≤ 0.50 mm).

Bench check
One bracket from CNC lot A was loaded in the Instron 5965 with a printed surrogate lens ring to reproduce the annular pressure footprint. Two strain gauges (EA-06-062AQ-350) at the fillet flank indicated 2120 and 2245 µε at 30 N; the model’s corresponding locations reported 1980 and 2360 µε (−6.6% and +5.1% differences). Tip displacement by laser tracker read 0.41 mm vs 0.38 mm from the model (+7.9%). No tuning was applied between model and test; input properties were per MMPDS.

Parameter check
We perturbed bolt pretension ±20% and friction coefficient between 0.15 and 0.25:
- Peak stress varied −3.8% to +4.6%
- Tip deflection varied −8.1% to +6.7%
The peak stress location did not migrate under these changes. Removing the washer pads (direct head-to-bracket contact) raised local bore stresses by ~11% without moving the critical fillet hotspot.

Assumptions and limitations
- Linear elasticity was assumed; no permanent set anticipated at 342 MPa for 7075-T6.
- The surrogate lens ring is stiffer than the production optic mount; this likely biases the bench deflection slightly low relative to flight hardware.
- Thermal preload from operating temperature is not included in this pass.
- Only the 30 N lateral case was run; torsional and vertical load combinations are pending.

Traceability
The input deck is stored in PDM under 41-3721-C_FE_2026-08-05.apj with subfolder runs/mesh_A/B/C. Postprocessing screenshots with probe IDs match the strain gauge rosettes and are in the same directory. The test report is QA-TR-1861; raw Instron files and gauge calibrations are attached there.

Recommendation and decision
Given the close agreement with the bench readings, the stabilized response under mesh refinement, and the modest sensitivity to bolt preload and friction, this model is accepted for preliminary sizing and for locking the mounting hole pattern at PDR. It is not approved for durability life estimates or off-axis load combinations. Decision by: Lead Structures Engineer (M. Chen) following review with Test (J. Patel) and Design (R. Ortega).

Next steps
- Extend the model to include the optic mount compliance and run the vertical-plus-lateral combined case.
- Add the anticipated thermal gradient once the avionics heat map is available.
- Revisit the washer representation based on vendor stack-up drawings.
