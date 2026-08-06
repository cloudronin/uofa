Appendix E: Detailed Run Manifest (excerpt)

- Software stack:
  - Ansys Fluent 2023 R2, build 2023.2.17, double precision
  - Ansys Meshing 2023 R2
  - ParaView 5.11.1
  - Dakota 6.16 (sampling and surrogate)
  - Python 3.10.9 with numpy 1.26, pandas 2.1, GPflow 2.8
- Hardware:
  - Cluster A: RHEL8, Intel Xeon 8360Y, 64 cores/node, 256 GB RAM, Infiniband HDR
  - Cluster B: Ubuntu 22.04, AMD EPYC 7H12, 64 cores/node, 256 GB RAM, Infiniband EDR
- Case setup parameters (Medium mesh baseline):
  - Turbulence: SST k-ω; low-Re formulation
  - Discretization: second-order upwind (mom/energy/turbulence)
  - Pressure-velocity coupling: coupled solver
  - Under-relaxation: p=0.4, mom=0.6, energy=0.95, k/ω=0.5
  - Multigrid: AMG, 20 V-cycles max
  - Convergence monitors: peak Tj, average T_out, total ΔP, pump work
- Energy balance:
  - Solid-fluid coupling residual < 1e-8
  - Heat in (electrical) = 1206.4 W; heat removed by PAO = 1205.0 W; net 1.4 W (0.12%)

Appendix F: Data Lineage for Key Inputs

- PAO-4 properties: Manufacturer doc “PAO-4_Thermophys_v3.pdf,” imported via CSV; SHA256 …7f03
- TIM conductance tests: Report RPT-CP-TIM-02 (Instron press, FLIR A655sc); raw CSV available in DataLake; analysis notebook “tim_conductance_fit.ipynb” with regression CI
- MOSFET power table: ELEC-LCL42-LOADMAP-RevP.xlsx; cross-checked with PSU logs from validation rig

Appendix G: Additional Validation Observables

- Outlet temperature: Model 37.4 C; rig 37.6 C ± 0.2 C
- Local wall temperatures at three channel turns within 0.9–1.6 C of IR readings (after emissivity correction)
- Flow maldistribution across parallel branches < 4% (model); confirmed by ultrasonic probe within measurement limits

Appendix H: Risk Register Linkages

- R-TH-17: TIM aging leading to TCC degradation; mitigations: torque spec verification, periodic retorque, thermal margin derating by 3 C.
- R-FL-03: Filter clogging elevating ΔP; mitigations: DP sensors with alert at 35 kPa, maintenance every 200 cycles.

Appendix I: Sensitivity Plots

- Tornado diagram showing TCC dominance, followed by device power and flow rate.
- Probability plot of peak Tj with 95% and 99% lines; 99th percentile at 94.8 C.

Appendix J: Training and Checklists

- CHT setup checklist Rev D attached; items 12–18 cover near-wall thermal resolution, conjugate interface coupling checks, and energy balance verification.
- Analyst training records for R. Zhao and M. Patel stored in LMS; latest vendor course completion dates: 2025-11-03 and 2026-03-21, respectively.

Appendix K: Change Log Summary

- v1.3 → v1.4: Incorporated CN-153 (boss diameter); negligible thermal impact (<0.1 C).
- v1.4 → v1.5: Increased local mesh density near manifold entries; reduced GCI95 by ~0.3 C.
- v1.5 → v1.6: Updated TCC prior based on additional TIM coupons; slight increase in uncertainty width, mean unchanged.

End of appendices.
