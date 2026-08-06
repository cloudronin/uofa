# Appendix

## Appendix A — Mesh and Element Metrics

- Meshes:
  - M1: global target size 4.0 mm; fillet control 1.0 mm; 0.9M DOF.
  - M2: global 3.0 mm; fillet 0.7 mm; 1.8M DOF.
  - M3: global 2.2 mm; fillet 0.5 mm; 3.7M DOF.
- Element quality:
  - Tetra corner angles: 98% within [25°, 130°]; worst 19° at one transition near pad fillet; addressed with local smoothing.
  - Hex aspect ratio: median 1.6; max 3.2 in benign web regions.
- Hotspot mesh:
  - Three elements across the R3.0 fillet thickness in M3. Convergence of stress peak as a function of 1/h shows near-linear trend, justifying extrapolation.
- Contact discretization:
  - Overclosure < 0.01 mm at equilibrium; contact pressure patch size consistent across meshes.

## Appendix B — Validation Details

- Lug coupon:
  - FEA boundary replicated pin-supported conditions; lubricant modeled via low μ = 0.05. FEA strain at 45° gage: 1760 με vs measured 1880 ± 50 με (−6.4%).
- Static press curves:
  - Reaction vs actuator stroke overlays show near-linear response up to 6.5 g; FEA slope within 3% of test.
  - Strain-vs-load plots: slopes agree within 5%; slight divergence near ultimate attributed to onset of localized plasticity in FEA earlier than in test due to batch yield alignment.
- Residual check:
  - Energy balance: external work 1.47 kJ; plastic dissipation 0.23 kJ; damping energy 1.1 J (stabilization), confirming negligible artificial damping influence.

## Appendix C — Uncertainty Propagation and Sensitivity

- Sampling:
  - 240-point LHS; stratified across 6 dimensions; correlation between preload of two bolts captured with ρ = 0.65 from installation data.
- Surrogate correction:
  - Linear response surface fitted on 40 M3 anchor runs; R^2 = 0.986 for peak stress; cross-validated RMSE 6.9 MPa. Remaining 200 samples run on M2 and corrected to M3 via surrogate.
- Sensitivity:
  - Morris screening with 16 trajectories indicated μ has a modest effect; confirmed by Sobol first-order indices (yield 0.47, fillet radius 0.29, preload 0.15, μ 0.07, load 0.02).
- Combined uncertainty:
  - Treating mesh convergence uncertainty as independent and Gaussian is conservative; sensitivity to that assumption is low because input variance dominates.

## Appendix D — Change History

- RevA (2026-05-10): Initial model; linear elastic only; no contact at pads. Rejected due to poor correlation (strain under-prediction 18%).
- RevB (2026-05-24): Added elastoplastic 7075; early mesh refinement near lug. Improved correlation to 9–12%.
- RevC (2026-06-15): Introduced pad contact and bolt preload; converged within 6–8%.
- RevD (2026-07-15): Finalized mesh study, UQ, and broader validation; meets acceptance targets.

## Appendix E — Peer Review Actions

- Action 1: Justify stabilization usage. Response: quantified damping energy fraction and compared stabilized vs unstabilized results; retained due to negligible effect and runtime reduction.
- Action 2: Confirm bolt preload distribution source. Response: Added instrumented installation data (n=8) and captured correlation between bolts.

## Appendix F — Reproduction Instructions

- Prereqs: Abaqus/Standard 2022 HF4; Python 3.10; pyAster-bridge v3.2; repo STRUT-FEA tag v1.4.2.
- Steps:
  - Run 01_prep/mesh_build.py with config RevD.yaml.
  - Solve 02_solve/solve_nominal.py; then 03_solve/solve_mesh_study.py.
  - Execute 04_validate/make_plots.ipynb to regenerate validation charts.
  - For UQ, run 05_uq/run_lhs.py; expect ~4.5 h wall time on AMC-02.

All datasets and scripts are self-contained under /projects/uas17/strut_fea/RevD.
