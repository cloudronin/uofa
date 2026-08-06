# Appendix: Run Matrix and Supporting Details

This appendix summarizes the run configurations and select numerical indicators for traceability. It is intended to aid reproduction of the results described in the main report.

## A1. Run Matrix

- Case IDs
  - CRM-M085-AngleSweep-Fine: M∞ = 0.85; α = [-1.0, 0.0, 1.0, 2.0, 3.0] deg; Re = 5e6/ft; fine mesh (34.5M).
  - CRM-M085-AngleSweep-Medium: Same as above; medium mesh (17.2M).
  - CRM-M085-Alpha2-Coarse/Medium/Fine: M∞ = 0.85; α = 2.0 deg; used for mesh study.
  - CRM-M085-Alpha2-FF50: M∞ = 0.85; α = 2.0 deg; far-field at 50 c_ref; fine-level spacing in near-field retained.
  - CRM-M085-Alpha2-Trip5pct: M∞ = 0.85; α = 2.0 deg; transition forced at 5% chord on wing using source-term toggle.

## A2. Mesh Quality Snapshots

- y+ statistics at α = 2.0 deg (fine mesh):
  - Mean y+ over wing: 0.83
  - 95th percentile: 1.48
  - Max: 1.7 (near wing kink, upper surface)
- Skewness (Tet):
  - 90th percentile: 0.78
  - Max: 0.91
- Aspect ratio (Prism layers):
  - Near trailing edge layers: up to 400; acceptable due to alignment with wall-normal gradients.

## A3. Iterative Convergence Notes

- Residual behavior:
  - Density residuals dropped from O(1e-1) to O(1e-5) in 7,500–10,500 iterations depending on α.
  - Momentum residuals showed late-iteration stalls only when α ≥ 3.0 deg; mitigated by reducing CFL from 200 to 120 for the last 1,000 iterations.
- Force monitors:
  - Standard deviation over last 500 iterations at α = 2 deg (fine mesh):
    - σ_CL = 0.0003
    - σ_CD = 8.2e-06 (≈ 0.08 counts)
    - σ_CM = 1.1e-04

## A4. Manufactured and Benchmark Details

- Manufactured case definition: Velocity and temperature fields defined by trigonometric polynomials with amplitude 0.2 and wavenumber 2π/L; body force derived analytically to balance the RANS equations without turbulence production (SA equation source terms disabled).
- Observed orders (uniform triangular meshes, Nx × Ny = 64² → 512²):
  - L2(u): 1.98–2.01
  - L∞(p): 1.72–1.85 (drop due to limiter near extrema; acceptable)
- Flat-plate check:
  - Domain length 2 m; inflow M = 0.2; SA tripping disabled.
  - c_f at x = 1.5 m within 1.7% of Blasius.
  - Wall y+ ≈ 0.9 at first layer; 30 layers; growth 1.2.

## A5. Boundary Condition Summary

- Far-field:
  - Pressure: p∞ = 101.3 kPa
  - Temperature: T∞ = 298 K
  - Turbulent eddy viscosity ratio: 0.03 (baseline), sensitivity 0.01 and 0.1.
- Wall:
  - No-slip, adiabatic.
- Symmetry:
  - Zero normal velocity and gradients.

## A6. File and Build Trace

- Mesh files:
  - crm_wb_coarse.pwmesh, md5: 0c2c7f6d3f2e1a04
  - crm_wb_medium.pwmesh, md5: 1f77a9a52c0d43bc
  - crm_wb_fine.pwmesh, md5: e3b4a58d9c7f09de
- FUN3D executable:
  - fun3d_13.9_skx_dp, build date: 2025-12-06, local patch: fb9c3e7
- Input decks:
  - fun3d.nml (baseline), rev: a12
  - bcmap.surfmap, rev: a03

## A7. Notes on Differences vs. Test Data

- The comparison uses raw RANS results without attempting to replicate tunnel hardware or surface roughness. This explains a portion of the drag shortfall.
- Fully turbulent assumption was selected to align with a tripped wind-tunnel model; if trip details differ from the assumed 5% chord, remaining biases may persist.

End of appendix.
