Appendix A: Configuration and Change Log

- Geometry source: CP-4172 Rev C (PDM item 006-CP-4172-C). Key change from Rev B: widened return channel by 0.5 mm to reduce pressure drop; verified in CMM report CMM-CP-4172-07.
- Mesh sets:
  - MESH-A (coarse): 7.2M cells, first layer 35 μm, growth 1.2, generated 2026-06-18.
  - MESH-B (medium): 13.5M cells, first layer 25 μm, growth 1.18, generated 2026-06-20.
  - MESH-C (fine): 26.1M cells, first layer 18 μm, growth 1.15, generated 2026-06-24.
- Solver versions: Fluent 2024 R2 build 2024.2.0-227. Vendor bug note FLT-17922 (surface integral reporting mismatch) checked; not affecting our workflows due to post-processing via volume integrals.

Change log highlights:
- CL-01 (2026-06-10): Initial CHT baseline with realizable k-epsilon; underpredicted Tj by 4.6 K.
- CL-02 (2026-06-15): Switched to k-omega SST; updated near-wall resolution; improved match to data.
- CL-03 (2026-06-22): Corrected inlet turbulence intensity from 1% to 5% to align with pump/manifold characterization.
- CL-04 (2026-06-25): Adopted TIM conductivity to mid-range datasheet value (3.4 W/m·K) from optimistic 3.6 W/m·K.
- CL-05 (2026-06-28): Tightened energy residual target; energy balance improved from 1.2% to 0.3%.
- CL-06 (2026-07-01): Added external convection boundary; negligible effect on Tj, retained for completeness.

Appendix B: Mesh Quality and y+ Distributions

- Coolant channel wall y+ histogram at nominal condition (MESH-B) peaks at 0.9 with 95th percentile at 1.6. Local spikes to ~2.4 near sharp upstream corners after fillet omission; localized refinement reduced these to ≤1.8.
- Maximum cell skewness 0.28; 99th percentile <0.36. Orthogonality minimum 0.72 in tight bends; manual smoothing performed to raise from 0.65.
- Boundary layer resolution: 12 prism layers with total thickness 0.45 mm on coolant walls; y+ maintained below 5 in all regions with high heat flux.

Appendix C: Uncertainty Propagation Details

- Input distributions:
  - TIM thickness: Normal(μ=55 μm, σ=4 μm), truncated [45, 65].
  - TIM conductivity: Triangular(min=2.8, mode=3.4, max=3.6 W/m·K).
  - Inlet temperature: Normal(μ=50 C, σ=0.5 C).
  - Flow rate: Normal(μ=8 L/min, σ=0.2 L/min).
- Sampling: Latin Hypercube, N=100, maximin criterion; random seed fixed for reproducibility (seed=481516).
- Output processing: Peak die temperature extracted via custom Python script that identifies die zones and computes max over combined IR-fused region proxies; cross-validated on three post-processing methods, yielding spread ≤0.3 K.

Experimental Data Notes

- IR calibration: Emissivity of die surface set to 0.84 based on taped reference patches; applying ±0.02 emissivity variation changes apparent temperature by ±0.7 K at 160 C. Correction applied uniformly across dies.
- Repeatability: Day-to-day variation in peak Tj at a fixed condition averaged 0.9 K (std dev), indicating good control of power and flow.

Regression and Reproducibility

- Rerun of SIM-IM-CHT-024 (2.4 kW, 8 L/min) on an alternate workstation (Windows 11, 24 cores) yielded 162.5 C vs 162.1 C on Linux. The 0.4 K difference is within expected roundoff and parallel decomposition effects.
- Archival: Case and data files archived under Git tag CHT-IM-v1.9; SHA 3f2c1d7. Post scripts in tools/post/verify_peak_tj.py with unit tests covering file I/O, zone IDs, and metric computation.

Planned Follow-Ups

- Extend property verification for glycol mixtures to 70 C using vendor CRC tables; currently extrapolated above 65 C.
- Roughness survey on machined channels across three production lots; incorporate into sensitivity by 2026-09-15.
- Additional fine-mesh spot-check at the extreme low-flow/low-temp corner to confirm applicability at Re > 22,000.

Contact Information

- Primary analyst: p.ortega@company.example
- Repository access: https://git.example.com/thermal/cht-inverter (internal)
