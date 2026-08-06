# Appendix A — Mesh and Element Quality Details

A1. Fillet Region Discretization
- The inner fillet blend between web and flange was partitioned with three concentric bands to enforce graded sizing. Edge sizes were 0.9 mm (inner band), 1.2 mm (middle), and 1.6–2.0 mm (outer). Curvature-based refinement was active with a target of 6 elements across the fillet radius through thickness on the fine mesh.
- Element aspect ratios in the controlling region were kept below 2.0. Warpage metrics indicate <5° across averaged faces.

A2. Global Mesh Statistics
- Coarse mesh: 284,316 solid elements; 11,904 contact/target elements; average element edge 2.4 mm.
- Medium mesh: 507,822 solid elements; 15,268 contact/target elements; average element edge 1.9 mm.
- Fine mesh: 918,441 solid elements; 21,333 contact/target elements; average element edge 1.5 mm.

A3. Node-Averaging Policy
- For stress extraction at the hot spot, nodal averaging was disabled. Path plots used elemental top integration points projected to a curve at the fillet mid-surface to avoid artificial smoothing. Away from the hot spot, default nodal averaging was left enabled for contour readability.

# Appendix B — Hand Calculation Notes

B1. Bending Stress
- Treat the bracket as a rectangular cantilever of width b = 60 mm and thickness t = 6 mm with a tip load F = 956 N applied at distance L = 120 mm.
- Second moment of area: I = b t^3 / 12 = 0.06 × (0.006)^3 / 12 ≈ 1.08 × 10^-9 m^4.
- Distance to extreme fiber: c = t/2 = 0.003 m.
- Bending moment at fixed end: M = F × L = 956 × 0.12 ≈ 114.7 N·m.
- Nominal stress: σ = M c / I ≈ 114.7 × 0.003 / 1.08e-9 ≈ 3.18e8 Pa ≈ 318 MPa.

B2. Tip Deflection
- δ = F L^3 / (3 E I) = 956 × (0.12)^3 / (3 × 71.7e9 × 1.08e-9) ≈ 0.61 mm.

Notes:
- The hand model does not include the stress concentration due to the fillet nor the stiffening effect of the bolted interface. Its primary value is to bound the order of magnitude for stress and displacement. The FEA result of 370 MPa in the fillet is consistent with an expected Kt > 1.1 for this geometry.

# Appendix C — Load and Boundary Condition Implementation

C1. Remote Load Mapping
- A remote point was created at the avionics CG, tied to the contact patch representing the mounting interface via rigid MPCs distributing the tip load evenly to the six M5 holes. The rigid assumption is acceptable because the avionics baseplate is a stiff aluminum casting; even distribution reduces artificial local overloads at a single hole.

C2. Bolt Pretension
- Each M6 bolt was represented by a beam element connecting the bracket flange to a rigid point on the rib surface, with a pretension section defined at mid-length. Target clamp 8 kN was applied using the sequential pretension procedure (pretension step followed by lock-in and external load step).
- Sensitivity runs confirmed that increasing pretension to 10 kN reduced slip but altered peak bracket stress by <0.5%.

C3. Contact Settings
- Contact pair: bracket flange underside (contact) to rib pad (target).
- Algorithm: augmented Lagrange, with normal stiffness autocalculated. Tangential behavior: isotropic Coulomb friction, µ = 0.2 baseline.
- Stabilization: weak damping during the first two substeps to aid convergence; turned off thereafter.

# Appendix D — Run Logs (Extract)

- Coarse mesh: 14 min, 1.6 GB peak memory; 7 equilibrium iterations average/substep; final force norm 3.1e-7.
- Medium mesh: 21 min, 2.8 GB; 6 iterations avg/substep; final force norm 4.6e-7.
- Fine mesh: 38 min, 5.4 GB; 7 iterations avg/substep; final force norm 4.9e-7.

No warnings besides standard contact stiffness messages at substep 1. No singularities detected. Reaction forces balanced to within 0.1% of applied remote load plus constraint forces.

# Appendix E — Reviewer Checkpoints

- Verify that at least five elements span the fillet thickness in the hot region on the selected reporting mesh. Achieved: six to seven elements.
- Confirm that stress extraction location is not at a singular edge or tied MPC node. Achieved: peak located within continuous fillet surface elements, not at a boundary constraint node.
- Validate that the reported peak is not an isolated spike. Achieved: peak region extends over multiple adjacent elements with smooth gradients.

End of appendix.
