# Appendix: Additional Details

A1. Mesh Quality Metrics (Medium Grid)
- Min orthogonal quality: 0.14 in manifold elbows; elsewhere >0.22.
- Max skewness: 0.86 localized at channel-to-manifold junction; limited impact verified by sensitivity case with localized refinement.
- Prism layer total thickness: 0.6 mm; growth rate 1.2; first cell height 15 µm to achieve y+ ~1.

A2. Solver Settings Snapshot (Nominal Case)
- Pressure-velocity coupling: Coupled; pseudo-transient CFL starting at 5, ramping to 50 over 2000 iterations.
- Discretization: Second-order for momentum and energy; second-order upwind for turbulence.
- Convergence behavior: Energy residual plateau observed around 500 iterations, reduced below 1e-5 by 2800 iterations; total iterations to convergence ~4200.

A3. Instrumentation Uncertainty Budget (Temperature)
- Type T thermocouple sensor uncertainty: ±0.2 C.
- DAQ resolution and linearity: ±0.1 C.
- Junction-to-case inferencing error (from model path): ±0.5 C (estimated).
- Combined (RSS): ±0.6 C.

A4. Material Property Snapshots
- Coolant (60/40 PGW) at 25 C: ρ = 1038 kg/m^3; μ = 3.2 mPa·s; k = 0.38 W/m-K; cp = 3.6 kJ/kg-K.
- Aluminum 6061-T6: k = 167 W/m-K (measured); ρ = 2700 kg/m^3; cp = 0.9 kJ/kg-K.
- Copper: k = 385 W/m-K; ρ = 8960 kg/m^3; cp = 0.385 kJ/kg-K.

A5. Data and File Provenance
- Repository: git@stash.company.local:TPG/coldplate-cht.git
- Tags:
  - v0.9.2: Medium grid LHS set (120 runs), run manifest includes random seed 842113 for sampling.
  - v1.0.0: Fine grid spot-checks at Points A and B.
- Key case files:
  - cp_nominal_med.cas.h5 (commit 2f1a83c).
  - cp_pointA_fine.cas.h5 (commit 9e5a1d1).
  - post/pointA_compare.ipynb for bench/model overlay plots.

A6. Bench Photo and IR Note
- A single FLIR A655sc snapshot at Point A (not used quantitatively) shows hotter center modules consistent with model contours. Emissivity set to 0.95 for gap pad areas; 0.2 for exposed aluminum.

A7. Quick Sensitivity to External Heat Loss
- A back-of-envelope calculation assuming 10 W/m^2-K external convection on the outer walls (0.03 m^2 area) yields ~0.3 W parasitic loss, translating to <0.1 C change in case temperatures at nominal; supports the adiabatic outer wall assumption.

End of appendix.
