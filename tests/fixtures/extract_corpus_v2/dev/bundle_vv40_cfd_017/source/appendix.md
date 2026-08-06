Appendix A: Selected Numerical Details

- Mesh statistics:
  - Coarse: 2.3M cells; minimum orthogonality 0.18; max skewness 0.82
  - Medium: 4.7M cells; minimum orthogonality 0.22; max skewness 0.78
  - Fine: 9.1M cells; minimum orthogonality 0.25; max skewness 0.75

- Prism layer setup:
  - Fine mesh: 17 layers, growth 1.18, first cell height 0.01 mm on 20 mm hydraulic diameter sections (target y+ ≈ 0.4)

- Residual histories:
  - Typical runs reached residual targets within 2500–4000 iterations; outlet flow monitors flattened earlier, but runs were extended until both residual and monitor plateaus matched.

- Solver controls:
  - Momentum under-relaxation initial 0.4, final 0.7; turbulence 0.5; pressure coupling via coupled scheme with pseudo-time stepping increased during the solve.

Appendix B: Flow Split at Nominal Condition (Fine Mesh)

- Outlet 1: 12.6% of total
- Outlet 2: 12.9% of total
- Outlet 3: 12.4% of total
- Outlet 4: 12.7% of total
- Outlet 5: 12.3% of total
- Outlet 6: 12.5% of total
- Outlet 7: 12.2% of total
- Outlet 8: 12.4% of total

- Mean: 12.5%
- Standard deviation: 0.75%
- Maldistribution index: 6.0%

Appendix C: Bench Comparison Data (Summary)

- Pressure loss at 200, 300, 400 standard L/min:
  - CFD (Fine): 1.21, 2.01, 3.09 kPa
  - Bench:      1.28, 2.13, 3.46 kPa

- Maldistribution at 300 standard L/min:
  - CFD (Fine): 6.0%
  - Bench: 6.8%

Notes

- All standard liters per minute (SLPM) refer to 25 C, 1 atm conditions consistent with internal testing practice.
- CFD and bench comparisons use the same reference density to avoid unit-of-measure discrepancies.
