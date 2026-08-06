# Appendix: Supplemental Details

A1. Mesh and Cell Quality Summary

- Coarse grid:
  - Total cells: 2.4M
  - Min orthogonal quality: 0.19
  - Max non‑orthogonality: 58°
  - Prism layers: 22; first‑cell height 12 µm; y+ target ≈ 2.0; achieved median y+ 1.8
- Baseline grid:
  - Total cells: 4.9M
  - Min orthogonal quality: 0.21
  - Max non‑orthogonality: 55°
  - Prism layers: 28; first‑cell height 8 µm; y+ target ≈ 1.0; achieved median y+ 0.95
- Fine grid:
  - Total cells: 10.2M
  - Min orthogonal quality: 0.22
  - Max non‑orthogonality: 53°
  - Prism layers: 34; first‑cell height 6 µm; y+ target ≈ 0.7; achieved median y+ 0.72

A2. Convergence Histories

- For the baseline grid at U∞=40 m/s, α=2°:
  - Continuity residual dropped from 1.0 to 1.7×10^-5 by 720 iterations; momentum residuals were within 2.0×10^-5.
  - AIP mass‑averaged total pressure stabilized to within ±0.02% after 580 iterations; inner bend wall shear stress monitor flattened after 610 iterations.
- For the fine grid at U∞=55 m/s, α=+6°:
  - Continuity residual reached 2.2×10^-5 by 1340 iterations; a transient plateau occurred around iteration 800 when the solver transitioned to the final under‑relaxation set.

A3. Sensitivity Runs Matrix (Selected)

- Tu∞ sweeps at U∞=40 m/s, α=2°:
  - 0.25% → recovery 0.957; DC60 0.041
  - 0.50% → recovery 0.955; DC60 0.040
  - 1.00% → recovery 0.952; DC60 0.038
- AIP mass flow variation:
  - −1.5% → recovery 0.949; DC60 0.042
  - +1.5% → recovery 0.960; DC60 0.037

A4. Experimental Alignment Notes

- Tunnel blockage corrections applied to the mass flow used for the AIP outlet boundary; correction magnitude <0.3% for all cases.
- Temperature uniformity checks via two thermocouples upstream of the model differed by less than 0.4 K during the matched runs.
- Probe rake traverses were repeated at the baseline condition; repeatability within ±0.4% of mean for recovery.

A5. Figures (Descriptions)

- Figure A1: S‑duct geometry with inner and outer bend Cp tap locations; region of expected separation circled near s/L≈0.6.
- Figure A2: AIP swirl vector maps (experiment vs. CFD) for baseline lip at α=2°; note qualitative agreement in vortex pair placement with CFD exhibiting slightly broader cores.
- Figure A3: Residual plots for baseline and fine grids at α=+6°, highlighting final plateau regions and stabilization of AIP total pressure monitors.

End of Appendix.
