Appendix A — Verification Logs and Mesh Metrics

A1. Manufactured Solutions and Regression Tests

- Inviscid vortex:
  - Grids: 64×64, 128×128, 256×256 (structured for MMS harness)
  - L2 error norms decrease by factors ~4 when doubling resolution, matching 2nd-order.
  - Observed orders: rho 2.01, u 2.00, v 1.99, p 2.02.
- Laminar channel with source:
  - Hex grids with Δx halved each level.
  - Observed orders: u 1.98, p 1.95.
- Boundary condition MMS:
  - Farfield BC mirrors analytic decay; no spurious reflections detected beyond machine epsilon.
- Regression suite summary:
  - 65 canonical cases executed post-build; all PASSED.
  - Compiler: Intel 2024.1; MPI: OpenMPI 5.0; Flags: -O3 -fp-model precise -qopt-zmm-usage=high.

A2. Grid Convergence and GCI

- SA-neg at M=0.85, α=2.0°:
  - CD coarse=0.0249, medium=0.0238, fine=0.0234.
  - Apparent order p≈2.1; refinement ratio r≈√4.
  - GCI95 (medium) ≈ 6.7 counts; extrapolated CD≈0.0232.
- SST at same condition:
  - CD coarse=0.0256, medium=0.0245, fine=0.0241.
  - p≈2.0; GCI95 (medium) ≈ 9.4 counts; extrapolated CD≈0.0238.
- Iterative error:
  - Extra sweeps changed CD <0.2 counts; CL <0.0001.

A3. Mesh Quality Checks

- Near-wall spacing:
  - First cell height: 3.2e−6 m (fine), 5.8e−6 m (medium), 1.2e−5 m (coarse); y+ mean 0.7 on medium (SA-neg).
- Growth rates:
  - Prism growth ≤1.2 to 45 layers, total thickness ≥0.015 m covering boundary layer and part of wake.
- Surface mesh:
  - LE and TE clustering with target Δs/c ≤ 0.002 at LE; TE spacing ≤ 0.003 c.
- Volume mesh metrics:
  - Min angle ≥30°; skewness P95 ≤0.28; orthogonality ≥0.15.
- Farfield distance:
  - 20 c baseline; 10 c sensitivity run showed <1 count CD difference.

A4. Boundary Conditions and Trips

- Farfield setup:
  - Riemann invariants with extrapolated back pressure; sponge layer in last 2 c reduces reflections.
- Symmetry:
  - Plane at z=0; odd/even variable handling confirmed.
- Wall:
  - No-slip, adiabatic; alternative isothermal wall at 300 K changed CD by ~1–2 counts.
- Trip emulation:
  - Roughness-equivalent patch ks+=60 from x/c=0.05–0.10 on suction and pressure sides; spanwise strips at η=0.2–0.9 with 0.02 c width.
  - Sensitivity: shifting strip by +0.5% c changed CL by 0.0004, CD by 1 count.

A5. Validation Data and Comparisons

- ETW data provenance:
  - Run 3154, Sections S07–S13; pressure taps calibrated within ±0.004 Cp.
  - Balance calibration applied; wall interference correction per ETW procedure doc R3154-WIC.
- FUN3D vs ETW:
  - Cp at η=0.5: shock at x/c=0.42 (ETW 0.41); Cp plateau error +0.015 (SA-neg), +0.010 (SST).
  - η=0.8: shock at x/c=0.53 (ETW 0.52); suction peak difference ±0.02.
  - Force polars: dCL/dα = 0.097/deg (ETW 0.095/deg); CD@CL=0.5 offset +6 counts (SA-neg), +14 counts (SST).
- OVERFLOW cross-check:
  - 24M H-grid with wall y+≈0.9; SA model; M=0.85, α=2.0° yields CD=0.0239 vs FUN3D SA-neg 0.0238; CL within 0.001.

A6. Sensitivity and UQ Details

- Local derivatives computed via central differences with Δα=0.1°, ΔM=0.002.
- LHS set-up:
  - 200 samples; pseudo-random seed 18273; bounds: α ±0.05°, M ±0.003, Re ±1%, Ti ±0.2%.
  - Response surfaces: quadratic in α and M; linear in Re and Ti; separate fits for SA-neg and SST.
- Model-form treatment:
  - Half the difference between SA-neg and SST best estimates taken as epistemic half-width; one DDES run at α=2°, M=0.85 yielded CD=0.0237, within SA–SST bracket, supporting this approach.

A7. Process and Traceability Artifacts

- Repository tags:
  - geom: crm-v3.2@a78b3e
  - mesh: crm_mesh_sa_2026-07-10@9f21d9; crm_mesh_sst_2026-07-12@b1c3ac
  - inputs: fun3d_inputs_nominal@5a0e77
  - post: postproc_2026-07-20@c7d0ff
- Run manifest includes:
  - Solver build hash: 4b2c6af
  - Module stack: intel/2024.1, openmpi/5.0, hdf5/1.14
  - Node types: 2×Intel Xeon 8358 per node; interconnect HDR InfiniBand
- Reproducibility:
  - Scripts: make all-plots regenerates all figures/metrics; tested on clean VM with same modules.

Appendix B — Risk and Applicability Notes

- Decision impact:
  - For loads, the ±3% target is met; the CFD uncertainty contributes less than structural sizing margins at PDR.
  - For performance, the ±10-count 95% interval leaves ≥20-count margin to the PDR drag target.
- When to revisit:
  - If AoA envelope extends beyond 3°, turbulence-model limitations necessitate unsteady RANS or DES.
  - If nacelles/pylons are added, wake–wing interactions and potential separation require revalidation.
  - If high-altitude, low-Re conditions are in scope, transition modeling is required; current fully turbulent assumption would bias results.

Appendix C — Contacts and Data Access

- CFD: cfd_support@aero-lab.gov
- Loads: loads_group@aero-lab.gov
- ETW data liaison: testdata@aero-lab.gov
- Repository: git@gitlab.aero-lab.gov:AERO/CRM-2026.git (request read access)
- Archive location: /project/AERO/CRM-2026 (immutable)
