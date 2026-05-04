# Appendix A — Supplementary Mesh and Benchmark Details

## A.1 Mesh Convergence Plots

The convergence behavior of peak von Mises stress with successive mesh refinement follows a monotonic pattern consistent with second-order convergence, as expected for C3D10M elements in smooth stress fields. The observed convergence rate (p ≈ 1.87) is close to the theoretical second-order rate, providing additional confidence that the fine mesh result is in the asymptotic regime.

Local mesh density at the critical strut-to-wall junction was verified by examining stress gradients across the three outermost element layers; the gradient variation between layers was less than 3%, confirming that the local refinement zone is adequate.

## A.2 Contact Algorithm Verification

The surface-to-surface contact formulation (finite sliding, penalty stiffness = 1×10⁵ N/mm) was verified against a simplified flat-on-flat compression problem with known analytical contact pressure. The Abaqus result matched the Hertz solution within 2.1% for peak contact pressure and within 1.4% for contact area. Augmented Lagrange iteration was not required; the penalty method converged within 4 iterations per increment for all production load steps.

## A.3 Material Test Data Summary

| Property | Mean | Std Dev | Specimens | Standard |
|---|---|---|---|---|
| Young's Modulus (GPa) | 114.2 | 2.1 | 10 | ASTM E8 |
| 0.2% Proof Strength (MPa) | 896 | 14 | 10 | ASTM E8 |
| Ultimate Tensile Strength (MPa) | 978 | 18 | 10 | ASTM E8 |
| Elongation at Break (%) | 13.4 | 1.2 | 10 | ASTM E8 |
| Fatigue Limit at 10⁷ cycles (MPa) | 510 | 22 | 8 | ASTM E466 |

All specimens were machined from the same Ti-6Al-4V ELI bar stock batch (NSD-MAT-2023-09) used in prototype fabrication. Surface finish of fatigue specimens was Ra 0.4 µm, consistent with the implant surface finish specification.

## A.4 Note on Omitted Analyses

The following topics were considered during scoping of this assessment but were determined to be outside the current phase boundary:

- **Operator and analyst influence on results** — The effect of different analysts constructing independent meshes and applying boundary conditions was not formally evaluated. A round-robin meshing exercise is planned for Phase 3 to assess this source of variability.
- **Model form uncertainty** — The choice of linear-elastic constitutive model versus an elastic-plastic model with kinematic hardening was not subjected to a formal model-form sensitivity study. Preliminary runs suggested less than 3% difference in peak stress for the load levels of interest, but this has not been documented as a formal study.
- **Input data pedigree review** — A structured review of the traceability and quality of all input data (geometry, material, loads, boundary conditions) against a formal data quality matrix was not completed for this revision. This is identified as a gap for the Phase 3 submission package.

These omissions are noted for transparency and do not affect the conclusions drawn in the main report, given the scope limitations of the current phase.
