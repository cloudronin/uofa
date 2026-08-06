Appendix A — Supplemental Details

A.1 Mesh statistics and wall resolution

- Grids:
  - G1: 0.9 M cells; 18 prism layers; layer coverage 98%; min y = 0.045 mm; y+ mean ≈ 1.6
  - G2: 3.4 M cells; 20 prism layers; layer coverage 99%; min y = 0.03 mm; y+ mean ≈ 1.1
  - G3: 13.7 M cells; 20 prism layers; layer coverage 99%; min y = 0.03 mm; y+ mean ≈ 1.0
- Quality metrics across all grids: non-orthogonality < 55°, max aspect ratio in prisms < 100; skewness mode < 0.3.

A.2 Convergence monitors (representative, G3)

- Total pressure drop (Pa): stabilized at 262 ± 0.2 Pa over last 1000 iterations.
- Worst-register UI: stabilized at 0.089 ± 0.0002.
- Field residuals: continuity and momentum < 1×10⁻⁵; k and ω < 5×10⁻⁶.

A.3 Mesh refinement results (selected outputs)

- Δp_total (Pa):
  - G1: 270
  - G2: 265
  - G3: 262
- Worst-register UI (−):
  - G1: 0.095
  - G2: 0.092
  - G3: 0.089

A.4 Turbulence model screening (G2 only)

- Realizable k-ε:
  - Δp_total = 257 Pa
  - Worst-register UI = 0.079
- k-ω SST:
  - Δp_total = 265 Pa
  - Worst-register UI = 0.092

A.5 Sensitivity runs (G2, SST)

- Inlet turbulence intensity:
  - 1%: UI = 0.088; Δp = 265 Pa
  - 5%: UI = 0.092; Δp = 265 Pa
  - 10%: UI = 0.098; Δp = 262 Pa
- Inlet swirl (solid-body, ±3° equivalent):
  - −3°: UI = 0.086; Δp = 264 Pa
  - 0°: UI = 0.092; Δp = 265 Pa
  - +3°: UI = 0.106; Δp = 266 Pa
- Roughness:
  - k_s = 5 μm: Δp = 263.3 Pa; UI = 0.092
  - k_s = 30 μm: Δp = 266.9 Pa; UI = 0.093

A.6 Experimental notes

- Venturi calibration sheet indicates ±0.5% of reading (k=2). Temperature compensated to 20°C.
- Hot-wire probe calibration performed before and after traverses; drift < 0.6%. Probe aligned normal to register plane within ±0.5° using laser alignment tool.

A.7 Case management

- Repository: git@gitlab.internal:hvac/CFD-ELB-021.git
- Tag: v1.3 (commit 8f3d2c9)
- Scripts: post/compute_UI.py; post/extract_dp.sh
- Solver: OpenFOAM v10 (foam-extend not used). Build hash recorded in metadata.txt.

End of appendix.
