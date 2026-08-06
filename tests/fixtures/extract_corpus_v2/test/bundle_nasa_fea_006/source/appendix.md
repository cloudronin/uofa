Appendix A. Mesh and Convergence Details

A1. Mesh density and element counts
- Coarse: 210k elements (C3D10), 0.9M DOF; min jacobian > 0.65; average edge length 5.5 mm; fillet seeding 1.5 mm.
- Medium: 420k elements, 1.6M DOF; min jacobian > 0.72; average edge length 3.0 mm; fillet seeding 1.0 mm.
- Fine: 1.05M elements, 3.8M DOF; min jacobian > 0.78; average edge length 1.9 mm; fillet local submodel replaced with 64k C3D20R elements at 0.75 mm sizing.

A2. Contact discretization
- Master/slave pairs assigned to minimize slave distortion; contact pressure convergence criterion 1% between increments.
- Penalty stiffness auto; checked with multipliers 0.5 and 2.0; hotspot stress change <1.3%; slip change <3.0%.

A3. Richardson extrapolation
- Observed order p=1.9 on stress in the submodeled region. Extrapolated stress σ* = 580 MPa; GCI_fine = 1.9% at 95% confidence.
- Displacement extrapolation yielded <1% change from fine, indicating adequate global stiffness capture.

Appendix B. Benchmark Problem Snapshots

B1. NAFEMS LE10 plate bending
- Mesh study shows quadratic tets recover deflection within 0.9% of analytic; shear locking absent at considered thickness ratio t/L > 1/50.

B2. Hertzian line contact
- Abaqus predicted contact half‑width b = 1.82 mm vs. analytical 1.86 mm for E’=140 GPa, P=5 kN per unit length; peak p0 within 2.6%.

B3. Bolt joint pretension
- Single lap joint under axial load; load partition within 3.1% of textbook solutions; joint opening onset matched within 5.4%.

Appendix C. Validation Test Alignment

C1. Scaling and similarity
- The 0.6× test maintained geometric similarity and bolt pattern. Loads scaled by λ^2 for stress similarity; stiffness scaled by λ (λ=0.6). DIC subset size adjusted to retain comparable strain resolution.

C2. Boundary mimicry
- Deck compliance represented by a polycarbonate plate measured FRF; reduced to stiffness over 0–300 Hz. FEM used an equivalent stiffness matrix embedded at the joint interface; difference in low‑frequency dynamic stiffness <3%.

C3. Measurement locations
- DIC virtual extensometers mapped to CAD at 0.4 mm below the surface to match the analysis reporting plane; reduced bias from surface‑stress gradient.

Appendix D. Independent Review Actions

- Action IR‑01: Reduce artificial stabilization from 0.0005 to 0.0002; recheck impact. Closed in v1.3.0; effect on results <1%.
- Action IR‑02: Demonstrate contact penalty robustness. Closed; see Appendix A2.
- Action IR‑03: Cross‑code spot check for preloaded mode. Closed; see main §15.

Appendix E. Scripts and Reproducibility Notes

- preproc_brkt241.py: imports CAD, seeds mesh, assigns sections; deterministic ordering of part/face IDs ensured by name‑based lookup.
- bolt_pretension_map.csv: maps bolt IDs to target clamps with ±10% scatter for parametric runs.
- post_hotspots.py: extracts 0.4 mm subsurface stresses; unit tests compare against golden dataset hashes.
- ci.yml: GitLab CI pipeline that runs medium‑mesh job on each push; stores ODB and CSV outputs with date/time and git SHA.

Appendix F. Limit Checks

Worst plausible combination within stated bounds (μ=0.10, preload −10%, fillet −0.25 mm):
- Hotspot von Mises (fine mesh): 642 MPa (still ≤ A‑basis yield margin +0.45).
- Relative slip: 0.098 mm (below 0.10 mm limit).
- Local plasticity check with elastic‑plastic curve: plastic zone <1% of bracket volume, confined to fillet surface; no load path redistribution.
