# Appendix

## Appendix A. Input Uncertainties and Sources

- Heat per die: 8.75 W ± 0.18 W (Type A from repeated electrical tests, Type B from instrumentation).
- TIM thickness: 52 ± 7 µm (optical profilometry, Mitutoyo QV-Elite).
- TIM conductivity: 2.5 ± 0.3 W/m·K (Hot Disk TPS; 5 repeats at 40–60°C).
- Flow rate: ±1.5% of reading (Krohne OPTIFLUX 4300 calibration #K-24-118).
- Inlet temperature: ±0.2 K (Pt100 in mixing chamber, 3-point calibration).
- Glycol mass fraction: 50% ± 2% (density and refractometer cross-check).

## Appendix B. Validation Summary (Selected Points)

- 1.5 L/min, 35°C, 1.4 kW
  - Measured Tj,max: 124.6°C; Predicted: 123.1°C; Δ = −1.5 K.
  - Measured Δp: 18.4 kPa; Predicted: 17.2 kPa; Δ = −6.5%.
- 3.0 L/min, 40°C, 2.1 kW
  - Measured Tj,max: 145.1°C; Predicted: 142.6°C (post-calib); Δ = −2.5 K.
  - Measured Δp: 49.2 kPa; Predicted: 47.1 kPa; Δ = −4.3%.
- 4.5 L/min, 55°C, 2.1 kW
  - Measured Tj,max: 149.8°C; Predicted: 147.2°C; Δ = −2.6 K.
  - Measured Δp: 82.1 kPa; Predicted: 84.9 kPa; Δ = +3.4%.

RMS across all 16 points: Tj,max 2.2 K; Δp 6.7%.

## Appendix C. Mesh and Solver Configuration Hashes

- Medium mesh (.msh): SHA256 7b1e9c91e43a…  
- Fluent case (.cas): SHA256 12a6f438be72…  
- Fluent data (.dat): SHA256 55d2be90a2f1…  
- Container (fluent-2023R2.sif): SHA256 a1c3e2d09f4b…

## Appendix D. Reproducibility Note

Independent rerun by J. Kaur on cluster “Zephyr” (AMD EPYC 7H12, 64 cores, CentOS 8) reproduced:

- Tj,max = 142.54°C vs 142.60°C (primary).
- Δp = 47.3 kPa vs 47.1 kPa (primary).

Journal and post-processing scripts (MATLAB) are in /scripts with commit 9f2b7e1.

## Appendix E. Energy Balance

At 3.0 L/min, 40°C, 2.1 kW:

- ṁ = 0.051 kg/s (EG/W 50/50 at 40°C), cp ≈ 3.57 kJ/kg·K.
- Predicted ΔTbulk = 11.6 K → ṁ cp ΔT = 2.11 kW.
- Applied heat: 2.08 kW (net after electrical to thermal conversion efficiency and fixture losses).
- Closure: 1.2%.

## Appendix F. Assumption Checks

- Radiation off: Adding S2S radiation with ε = 0.9 on all solids changed Tj,max by 0.3 K at the nominal case. Negligible relative to other uncertainties.
- Transient vs steady: A transient run from cold start to steady (pseudo-transient off, physical time step 0.01 s for 2 s) resulted in steady Tj,max within 0.4 K of the steady-state solution.

## Appendix G. Sensitivity Plots

- Tornado diagrams for Tj,max and Δp at the nominal condition show TIM thickness and conductivity dominating thermal uncertainty; flow rate dominates hydraulic uncertainty. Plots are in /figures with filenames: tornado_Tjmax.png, tornado_dP.png.

## Appendix H. Peer Review Comments (Excerpts)

- “Confirm interface temperature continuity residuals <0.05 K” — addressed; measured 0.02 K.
- “Add external check of manifold K-loss values” — addressed via CoolFlow AB.

End of appendix.
