# Appendix: Supplemental Details

## A1. Mesh Levels and Selected Metrics

- Coarse (1.2 M cells)
  - Avg y+: 1.6
  - Max skewness: 0.91
  - Head at BEP: 23.52 m
  - Residuals: 1×10^-6 achieved in 1,850 iterations
- Medium (3.2 M cells)
  - Avg y+: 1.1
  - Max skewness: 0.87
  - Head at BEP: 24.08 m
  - Residuals: 1×10^-6 in 1,220 iterations
- Fine (7.5 M cells)
  - Avg y+: 0.8
  - Max skewness: 0.84
  - Head at BEP: 24.27 m
  - Residuals: 1×10^-6 in 1,540 iterations

Observed order (from head between Medium and Fine): p ≈ 1.93. Extrapolated infinite-resolution head: 24.45 m.

## A2. Transient Sliding-Mesh Duty-Point Checks

- Time step: 2°/step → Δt = 1.148×10^-4 s
- Revolutions: 3 total; statistics taken over last revolution
- Mean head: 24.31 m
- Std dev of head over revolution: 0.09 m
- Tightened time step to 1°/step: mean head 24.33 m; std dev 0.06 m

## A3. Influence of Assumptions

- Inlet turbulence intensity 4–6%: head varies by ±0.4% around BEP.
- Volute roughness ks ±0.6 μm: head varies by ±0.6%.
- Tip gap ±0.05 mm: head varies by ±0.35%.
- Fluid temperature ±0.5°C: head change <0.05%.

## A4. Experimental Data Quality Notes

- Pressure transducers: ±0.25% FS, calibrated July 2026; drift <0.05% over test period.
- Flowmeter: ±0.1%, density-compensated Coriolis; verified with weight tank.
- Temperature: four RTDs averaged; maximum spatial spread 0.2°C.

## A5. Run Management

- Repository: ssh://git.int/pumps/v24r1_cfx_bench (tag v1.3)
- Mesh files: stored in LFS, hashes recorded in manifest.yaml
- Command line to reproduce BEP Medium case:
  - snakemake -j 64 run_bep_medium
- Checkpoint/restart files stored every 200 iterations; last restart archived.

## A6. Peer-Review Comments and Responses

- Comment: “Refine at volute tongue; high gradients suspected.”  
  Action: Added refinement box; improved stability and reduced head sensitivity by ~0.2%.
- Comment: “Torque convergence criterion should be stricter than 0.1%.”  
  Action: Tightened to 0.05%; no change in final head but better repeatability across MPI layouts.
- Comment: “Clarify head definition vs test data reduction.”  
  Action: Added explicit note on area-averaging planes and pressure components.

## A7. Known Code Limitations (Vendor)

- CFX High Resolution scheme tends to clip gradients in strong adverse pressure gradient regions; RSM mitigates but increases compute cost.
- Interface flux conservation is robust, but non-matching interface coarsening can introduce local dissipation; we minimized ratio to <3.

## A8. Nondimensionalization Cross-Check

- Coefficient of head at BEP: ψ = gH/(U2^2) ≈ 0.78, consistent with typical six-blade, medium-specific-speed designs.
- Flow coefficient at BEP: φ = Q/(πD2b2U2) ≈ 0.095, matches vendor family curves.

## A9. Conservation and Sanity Checks

- Global mass residual < 0.08%.
- Angular momentum balance: impeller torque from control-volume balance vs solver report differ by 0.3%.
- No negative absolute pressures detected; minimum static pressure at impeller eye remains > 40 kPa absolute, well above vapor pressure at 25°C.

## A10. Risk Register (Modeling)

- Low-flow operation unsteadiness: mitigated by transient check; recommend using transient predictions for this range when making margin calls.
- Cavitation: excluded; must not use results near NPSHr assessments.
- Geometry deviations beyond measured: not propagated; next build should include CT-scan variance where practical.
