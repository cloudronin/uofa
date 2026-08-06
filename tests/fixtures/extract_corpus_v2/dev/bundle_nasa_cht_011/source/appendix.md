Appendix A: Mesh, Solver, and Case Matrix Details

A.1 Mesh statistics (L2)
- Total cells: 12.4 million
- Fluid domain: 8.7 million cells (poly-hexcore); near-wall prism layers: 12
- Solid domain: 3.7 million cells (polyhedral)
- Minimum orthogonal quality: 0.12; average skewness: 0.21
- Wall y+: mean 0.9; 95th percentile 1.4; minimum 0.3

A.2 Residual and monitor plots
- Energy residual crosses 1e-6 by iteration 1800; SST dissipation at 1e-5 by iteration 2200.
- Mass imbalance: 0.06% at convergence.
- Surface temperature monitors (three hotspots) plateau within 0.02 C over the last 800 iterations.

A.3 Radiation model check
- DO 4×4 angular discretization compared to view-factor on a simplified external geometry: net radiative heat loss differs by 0.17% at 450 W.

Appendix B: Test Matrix and Uncertainty

B.1 Operating points
- Loads: 150, 300, 450 W
- Flows: 0.030, 0.045, 0.060 kg/s
- Inlet temperature: 293 ± 0.2 K
- Chamber liner temperature: 200 ± 1 K

B.2 Instrument accuracy
- PT100 Class A: ±(0.15 + 0.002|T|) K; calibration sheets TR-CLB-PT100-22 appended to test report.
- Coriolis flowmeter: ±0.5% of reading; calibration TR-CLB-FLW-26.
- Differential pressure transducers: ±0.25% FS; zeroed pre- and post-test.

B.3 Data reduction
- Ten-minute moving average over the final 30 minutes; standard deviations captured for RMS calculations.
- Combined uncertainty for baseplate sensor readings: 0.22 K (95% confidence).

Appendix C: Sensitivity and UQ Setup

C.1 Ranges and distributions
- TIM contact resistance: Normal(μ=0.25 K·cm^2/W, σ=0.075)
- PAO mass flow: Normal(μ=0.045 kg/s, σ=0.0009)
- Inlet temperature: Normal(μ=293 K, σ=0.2 K)
- PAO μ: Lognormal with 3% geometric SD
- PAO k, cp: Normal with 3% and 2% SD, respectively
- Emissivity: Normal(μ=0.08, σ=0.01)

C.2 DOE and sampling
- 200-point Latin Hypercube; L1 grid with correction factor to L2 derived from mesh study.
- Regression fit R^2 = 0.93 for peak T vs inputs; heteroscedasticity tested via Breusch-Pagan, p=0.21 (not significant).

Appendix D: Process Artifacts

D.1 Peer review summary (MR-CP02-12)
- Comment: Evaluate transition model — Disposition: tested, ΔT_peak < 0.6 C; no adoption.
- Comment: Increase radiation angular resolution — Disposition: check indicates negligible change; retain 4×4.
- Comment: Assess TIM clamp variability — Disposition: added to UQ; also propose torque spec controls for assembly.

D.2 Change log excerpt
- v1.6 → v1.7 (2026-05-14): Corrected inlet header chamfer; mesh rebuilt; rerun L2 and L1; acceptance recorded.
- v1.5 → v1.6 (2026-05-01): Updated PAO viscosity curve with ThermoLab data; resulted in +0.2 C at nominal.

D.3 Reproducibility
- All post-processing notebooks rerun on 2026-06-01 under environment hash env-3d2a…7b1c; figures regenerated and checksums matched the archived copies.

Appendix E: Cross-Model Comparison

- Thermal Desktop/SINDA network constructed with equivalent channels and UA from Dittus-Boelter correlation adjusted for property variation.
- At 0.045 kg/s, SINDA predicts ΔT_coolant = 8.9 K vs CFD 9.3 K; pressure drop 39.5 kPa vs CFD 37 kPa.
- Differences attributed to 3D entrance/turning losses and nonuniform heat flux capture in CFD.

Appendix F: Acceptance and Use Guidance

- Model may be used for: setting pump flow, verifying component base temperatures, and defining TVAC acceptance windows.
- Not for certification of safe operation under off-nominal events (loss of flow, cold start at 250 K).
- Any geometry revision, fluid change, or TIM swap requires a quick-look impact assessment; if ΔT_peak > 5%, escalate for re-acceptance per CE-CP02-ACC-001.

Appendix G: Acronyms

- CHT: Conjugate Heat Transfer
- DO: Discrete Ordinate
- LHS: Latin Hypercube Sampling
- MLI: Multi-Layer Insulation
- PT100: Platinum Resistance Thermometer
- RANS: Reynolds-Averaged Navier–Stokes
- SINDA: Systems Improved Numerical Differencing Analyzer
- TVAC: Thermal Vacuum
