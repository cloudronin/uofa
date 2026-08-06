# Appendix: Supplementary Material

A1. Run Matrix
- Grids: C1 (1.3M), C2 (5.1M), C3 (20.7M)
- Angles of attack: 2°, 3°, 4°
- Models: SA-neg (all), SST (C2 at 3°)
- Farfield: 25 span lengths (all), sensitivity at 15 spans (C2 3°)
- Convergence criteria: residual drop ≥ 1e−5; force monitors steady to within 0.0002 in CL and 0.00004 in CD over last 2000 iterations

A2. Representative Plots (descriptions)
- Figure A2-1: CL vs α at M=0.85, Re=5M. CFD (C3 SA-neg) overlaid with NTF data; slope within 2%. Error bars show ±1.8% band from Sec. 9.
- Figure A2-2: CD vs α at M=0.85, Re=5M. CFD underpredicts by 4–10 counts; SST point at α=3° sits in between CFD SA-neg and WT.
- Figure A2-3: Wing upper-surface Cp at η=0.7 for α=3°. CFD shock at x/c ≈ 0.48; WT shock centered at 0.49. RMS Cp delta ≈ 0.034.
- Figure A2-4: Convergence history at α=3°, C3. Residuals and force monitors shown; final steady region highlighted.

A3. Sensitivity Coefficients (local)
- Computed via ±1% finite differences around the α=3° baseline. Perturbations applied one-at-a-time with 300–500 pseudo-timesteps to re-equilibrate.

A4. Reproducibility Checklist
- Container hash: sha256:7c13f2b... (full string in repository)
- Git commit: 8f6c1d2
- Postprocess script: postprocess_crm_v3.py, checksum 2f91a… (recorded in results manifest)

A5. Known Pitfalls
- Using SA-neg on too-coarse grids can hide small separation zones; ensure use of at least C2 for any drag-sensitive study.
- Farfield distance below ~10 spans can contaminate pressure recovery; we observed negligible effect above 15 spans.

A6. Data Availability
- Wind tunnel slices digitized from NASA TM-2010-216807 figures; integrated forces pulled from tabulated appendices where available. Digitization scripts and calibration notes included in /data/NTF_CRM.

End of Appendix.
