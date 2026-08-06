# Appendix — Selected Technical Details

A1. Mesh quality snapshots
- Skewness: 95th percentile 0.28 (medium mesh), max 0.65 at the tongue; no negative volumes.
- Orthogonal quality: minimum 0.13 confined to blade trailing-edge gap cells, acceptable per solver guidelines.

A2. Convergence traces
- Design point (Q=Qd, N=3000 rpm): Residuals fell below 1e-5 by 1100 iterations; Δp plateaued after 900 iterations with <0.2% drift; torque stabilized similarly.

A3. Sliding mesh setup
- Time-step sensitivity: 1e-4 s vs 5e-5 s changed time-averaged Δp by 0.2%; 6 to 8 revolutions averaging changed mean by 0.1%.
- Interface: GGI; periodicity enforced across blade passages.

A4. Comparison metrics
- Pressure rise metric: Percent error relative to AMCA: 100*(CFD−Test)/Test.
- PIV angle comparison: Local flow angle θ=atan2(Vθ, Vr); statistics computed over the PIV domain excluding a masked region at the wall within 2 mm of the surface.

A5. Uncertainty propagation notes
- Latin hypercube sampling used for 200 Monte Carlo samples at each point.
- Combined 95% intervals derived from sample standard deviations assuming approximate normality; validated by bootstrapping (1000 resamples) with consistent interval widths within 0.2%.

A6. Sensitivity screening
- Morris method with 8 trajectories highlighted K and C as the dominant parameters; normalized elementary effects for K and C were 2.1 and 1.6, respectively; turbulence intensity was 0.4; wall roughness 0.7.

A7. Repository structure
- cases/: Fluent .cas.h5 files per operating point with embedded mesh.
- scripts/: Python and Scheme scripts to launch cases and extract monitors.
- post/: Jupyter notebooks for plotting, uncertainty analysis, and report figures.
- ci/: Regression test definitions and target bands for canonical cases.

A8. Independent review closure
- All three reviewer comments resolved; closure evidence committed under PR #118 with before/after plots and added transient cross-check results.

A9. Operating envelope summary
- Speeds: 2400–3300 rpm (approved); <2400 or >3300 rpm requires reassessment.
- Flows: 0.6–1.15 Qd (approved); ≤0.55 or ≥1.2 Qd not supported.
- Working fluid: Air, 20–30°C; altitude ≤1500 m; humidity not modeled.

A10. Contacts
- Technical owner: L. A. Nguyen (Fluids Engineering)
- Repository admin: S. P. Dorsey (DevOps for Engineering)
- Test lab liaison: J. C. Patel (Airflow Test Lab)
