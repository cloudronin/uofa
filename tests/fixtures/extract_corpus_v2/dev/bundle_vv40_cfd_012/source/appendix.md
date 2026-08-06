# Appendix: Supplemental Technical Details

A1. Mesh Statistics by Level (OP-B, representative)

- Coarse (1.92M):
  - Min orthogonal quality: 0.19
  - Max skewness: 0.86 (0.3% of cells above 0.8)
  - Average y+: 53 on impeller, 61 on volute
  - Inflation layers: 12 in volute, total thickness 4.5 mm

- Medium (3.84M):
  - Min orthogonal quality: 0.21
  - Max skewness: 0.83 (0.6% above 0.8)
  - Average y+: 47 on impeller, 58 on volute
  - Inflation layers: 15 in volute, total thickness 5.5 mm

- Fine (7.21M):
  - Min orthogonal quality: 0.22
  - Max skewness: 0.81 (0.6% above 0.8)
  - Average y+: 44 on impeller, 55 on volute
  - Inflation layers: 19 in volute, total thickness 6.0 mm

A2. Convergence Monitors (OP-B)

- Head (m): Plateaued at 28.5 ± 0.05 over last 250 iterations (fine mesh).
- Torque (N·m): Stabilized at 68.6 ± 0.09 over last 250 iterations (fine mesh).
- Residuals: RMS continuity fell from 1e-1 to 3e-5; momentum components below 5e-5.

A3. Postprocessing Notes

- Reference datum for head calculation: PumpWorks flange-to-flange elevation datum; static head offset removed using the same datum as the lab report.
- Swirl angle derived from arctangent of tangential to axial velocity components at the volute throat; area-weighted averaging applied.

A4. Runtime and Iteration Counts

- Coarse mesh: 900–1200 iterations to converge; runtime 1.6–2.1 hours.
- Medium mesh: 1400–1800 iterations; runtime 4.3–5.2 hours.
- Fine mesh: 2000–2400 iterations; runtime 8.8–10.2 hours.

A5. Visualization Observations

- Streamlines seeded one passage upstream of the tongue reveal a mild corner separation on the shroud near OP-B that grows at OP-C; the separation is anchored about 12 degrees downstream of the tongue and extends 8–12 mm radially.
- Static pressure footprint on the tongue outer surface shows peak Cp around 1.8 at OP-A, dropping to 1.5 at OP-C, which correlates with the observed increase in mixing loss.

A6. Files in Analysis Archive

- Geometry: TK250-50_revC_cleaned.cadpkg
- Meshes: tk250_coarse.cfx5, tk250_medium.cfx5, tk250_fine.cfx5
- Case files: OP-A_med.cfx, OP-B_fine.cfx, OP-C_fine.cfx
- Report: cp_headcurve_report_2026-08-06.pdf (exported from CFX-Post)
