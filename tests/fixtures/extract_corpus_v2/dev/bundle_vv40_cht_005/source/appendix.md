# Appendix A — Supplemental computational details

Mesh generation and quality:
- The fluid mesh employed polyhedral cells generated from a surface triangulation with curvature-based refinement. Typical cell orthogonality >0.22; skewness <0.78, with only 0.04% of cells exceeding 0.9 skewness near tight channel bends on the coarse mesh. The final (M3) mesh reduced the high-skewness population below 0.01%.
- Prism layers: 15 layers with growth factor 1.18; total thickness ~1.6 mm, ensuring y+ between 0.8 and 1.5 over the micro-fins and channel walls.
- Solid mesh: tetrahedral with four refinement levels under the module footprint; minimum edge length in copper traces ~60 µm; element quality measured by aspect ratio <12 for 95% of elements.

Solver controls:
- Pressure–velocity coupling: coupled scheme with pseudo-transient option enabled; Courant target 50; under-relaxation 0.3 for momentum, 0.7 for energy, 0.4 for k and ω during early iterations, then ramped to 0.6/0.9/0.6 at 1500 iterations.
- Gradient calculation: least-squares cell-based; flow curvature correction turned on for momentum.
- Thermal coupling: single-domain energy equation with conformal interfaces; checked face mismatch <0.02% by area.

Monitors and residual behavior:
- Residuals decreased smoothly; a short plateau between iterations 900–1200 was observed coincident with k–ω stabilization in the fin region; subsequent lowering of ω under-relaxation by 0.05 resolved the plateau.
- Temperature monitors:
  - “T_outlet_centerline”: area average of 12 faces at the outlet cross-section; stabilized to within 0.02 C from iteration 1850 onward.
  - “T_module_avg” and “T_module_max”: area averages on the baseplate patch beneath the module; stabilized after iteration 2100.
- Mass and energy imbalance dropped below 0.2% at iteration ~1600 and 0.1% by ~2500.

Case management:
- Each mesh level used a consistent boundary condition set with named selections imported from SpaceClaim. A pre-run journal script automatically set the volumetric flow and inlet temperature.
- Thermal material data for the coolant were provided via a tabulated UDF linked to ASHRAE correlations; solids used Fluent material database values for A356 and copper with minor manual edits to match lab data.

Bench replication in the model:
- Pressure tap locations were matched by measuring from the plate edge to the centerline of the ports (20 ± 0.5 mm) and mapping that to the model faces.
- The outlet RTD was oriented tip-upstream; to approximate this, the outlet cross-section post-processing region excluded the outer 0.5 mm annulus to reduce sensitivity to recirculation zones near the wall.

Notes on the TIM fit:
- A series of five short runs adjusted the TIM effective conductivity from an initial value corresponding to 0.23 K·cm^2/W to 0.30 K·cm^2/W in 0.015 steps. A least-squares metric minimized the error at the central thermocouple location over the last 300 iterations of each run. The minimum occurred at 0.28 K·cm^2/W; nearby values changed the corner temperatures by ~0.2–0.3 C.

File locations:
- Meshes: TS-INV-CP-RevC/GeomMesh/2026-07/m1, m2, m3 directories; Fluent .msh.h5 files with corresponding quality reports.
- Solution files: TS-INV-CP-RevC/CFD/CHT/2026-07-ops12Lpm/m3-run03; includes .cas.h5 and .dat.h5 and journal.m3ops12.jou.
- Bench logs and a photo of the instrumentation layout: TS-INV-CP-RevC/Test/Bench/2026-07-CHT-compare.

End of Appendix.
