# Appendix A: Supplemental Details

A1. Mesh density summary
- Coarse: 176,234 elements, 268,901 nodes; 3.0 mm global; 1.8 mm fillet sizing. Peak element aspect ratio < 5; average Jacobian ratio 1.25.
- Medium (baseline): 352,481 elements, 532,774 nodes; 2.0 mm global; 1.2 mm fillet sizing; 3 prism layers at contact with growth 1.2. Peak aspect ratio < 4; average Jacobian ratio 1.19.
- Fine: 798,052 elements, 1,180,332 nodes; 1.2 mm global; 0.8 mm fillet sizing. Peak aspect ratio < 4; average Jacobian ratio 1.17.

A2. Load case composition
- Combined acceleration case applied as:
  - Vertical: +20 g along +Z to IMU and converter masses and bracket self-weight.
  - Lateral: +12 g along +Y, same application points.
  - Pretension: 3.0 kN per bolt, applied prior to accelerations, then locked.

A3. Strain-gage mapping
- SG-1 predicted principal strain (FEA): 780 µε at 2.50 kN vertical load. Orientation angle 12 degrees from bracket rib axis.
- SG-2 predicted principal strain (FEA): 435 µε at 2.50 kN vertical load. Orientation parallel to flange edge.

A4. Material data notes
- 7075-T7351 per MMPDS-17:
  - Tensile strength Su ≈ 572 MPa (L), 524 MPa (T).
  - Yield strength Sy ≈ 503 MPa (L), 469 MPa (T).
  - The billet certification for the flight lot reports E = 71.4–72.1 GPa (n=8 coupons), ν not measured; density per typical handbook value.

A5. Modal shapes snapshot
- Mode 1 (318 Hz): Out-of-plane bending, antinode at flange tip.
- Mode 2 (367 Hz): Twist about Z; nodes near midspan of the rib.

A6. Uncertainty sampling seed and ranges
- Random seed: 83427.
- Ranges as stated in Section 6.2 of the main report. Correlations between vertical and lateral g-loads ignored at this stage; to be revisited with vehicle-level environment characterization.

A7. Contact behavior checkpoints
- Maximum penetration: 2.3 microns at the outer corner under lateral-only loading on the medium mesh, within 0.5% element edge guideline.
- Stick-slip transition isolated; no oscillatory chatter after normal stiffness tuning.

End of appendix.
