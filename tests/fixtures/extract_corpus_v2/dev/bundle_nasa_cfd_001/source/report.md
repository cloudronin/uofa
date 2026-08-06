# Credibility Assessment Report
CFD Prediction of ONERA M6 Wing Performance for Transonic Cruise Conditions

Prepared by: Aero Simulation Group, Vehicle Environment and Loads Branch  
Date: 2026-08-06  
Software: OVERFLOW 2.2d (primary), FUN3D v13.6 (independent check)

## 1. Background and Intended Use

This assessment covers a Reynolds-averaged Navier–Stokes (RANS) analysis of the ONERA M6 reference wing under transonic cruise conditions. The purpose is to determine whether the current analysis workflow is reliable enough for:
- estimating lift and drag at near-cruise angles of attack,
- locating shock positions on the wing,
- generating pressure distributions for loads mapping,

to support pre-PDR aerodynamic performance predictions for swept-wing concepts whose spanwise and planform characteristics are similar to M6. The decision criteria (established in M&S Plan ECL-VEH-AERO-MSP-042 Rev B) are:
- mean absolute error in CL ≤ 3% versus tunnel data,
- drag error ≤ 15% of total CD (recognizing CD sensitivity),
- shock location agreement within 2% of local chord at the three classical span stations,
- documented numerical uncertainty and data provenance sufficient for audit.

The intended range of applicability is Mach 0.78–0.90, Re = 6–20 million per reference chord, α from –1° to 4°, clean wing, steady flow without control surface deflections. Use of the model outside these limits is not addressed by this report.

## 2. Model Formulation, Assumptions, and Scope

- Governing equations: compressible RANS solved using OVERFLOW 2.2d, cell-centered finite volume with a second-order upwind scheme for convective fluxes (Roe-approximate Riemann solver), and second-order central differencing for viscous terms.
- Turbulence closure: Spalart–Allmaras (SA) with compressibility corrections enabled.
- Gas model: calorically perfect air, γ = 1.4, R = 287 J/kg-K, Sutherland viscosity.
- Wall boundary condition: no-slip, adiabatic; boundary-layer tripping specified to mirror the experiment (fixed trips at 5%–10% chord where documented).
- Far field: characteristic inflow/outflow; freestream turbulence intensity prescribed per tunnel data (0.5% nominal).
- Geometry: standard ONERA M6 wing (AGARD AR-138), truncated tip at 0.95 span as in the data set used here.
- Not modeled: aeroelastic deflection, surface roughness beyond fixed trip, humidity effects, and unsteady buffet. The solution is treated as steady; time accuracy is not claimed.

Known limitations: SA underpredicts shock–boundary layer interaction in cases with incipient separation near the tip; drag prediction is particularly sensitive to mesh resolution in the wake and tip vortex core.

## 3. Data Sources and Provenance

- Geometry: Wing coordinates and span stations from AGARD AR-138; independently re-digitized and cross-checked against NASA TM X-561.
- Test conditions: Target case M = 0.84, Re = 11.72×10^6 (based on reference chord), α = 3.06°. Source: measurement set B from AR-138. Angle-of-attack calibration uncertainty ±0.03°, Mach ±0.0008, Re ±1.5%.
- Pressure data: Pressure tap distributions at η = 0.20, 0.44, and 0.80; calibration certificates scanned to repository path /data/AR138/ptaps/certs with traceability to device serials.
- Trips: Documented grit-strip placement applied to CFD as fixed transition strips via wall-function switch region. Trip height translated to an equivalent SA eddy-viscosity source per OVERFLOW best practice note OFLOW-TIPS-031.
- Input verification: All inputs passed a two-person check (analyst and independent reviewer) using geometry overlays, condition consistency checks, and a script that flags out-of-range flow properties (commit cf3d17e).

## 4. Computational Setup

- Mesh families: Unstructured overset hybrid grids generated with Pointwise 18.4R4.
  - Coarse: 2.1M cells, y+ ≈ 1.5 at 20% span, 40 layers in BL, Δs+ ≈ 80 on wing surface.
  - Medium: 6.4M cells, y+ ≈ 1.0, 60 BL layers, refined wake block to 0.01c extent.
  - Fine: 22.8M cells, y+ ≤ 0.9 over 90% span, 80 BL layers, tip vortex refinement region.
- Convergence criteria: L2 density residual < 1e-6 (5+ orders reduction) and forces stabilized to within 0.5 counts over 500 iterations.
- Parallel runs on Pleiades (Broadwell nodes, Intel Xeon E5-2697 v4, Intel MPI 2021.8); double precision; runs repeated with GCC 12.3 to test compiler sensitivity.

## 5. Numerical Method Checks

Code-level testing:
- OVERFLOW 2.2d regression suite: 162/162 tests passed (report archived at /qa/reports/overflow-2.2d-reg-2026-07-12.pdf).
- Manufactured-solution results reviewed for laminar compressible flow: observed order p = 1.98–2.05 for conserved variables (internal memo QA-MMS-019).
- FUN3D v13.6 compiled with Intel 2021.8; regression status 98% pass (3 geometry import tests skipped due to missing vendor mesher license).

Discretization and iterative error:
- Richardson extrapolation based on coarse–medium–fine sequence yields:
  - Observed order p ≈ 1.93 for CL; p ≈ 1.85 for CD.
  - Estimated grid-induced uncertainty (95% CI) on fine grid: u_g(CL) = ±0.0040 (≈ 1.4% of CL); u_g(CD) = ±0.00050 (~8% of CD).
- Iterative uncertainty: u_it(CL) = ±0.0003; u_it(CD) = ±0.00005, from restart cycling and convergence window analysis.
- Mesh independence declared for surface Cp distributions; local shock movement with refinement ≤ 0.6% chord between medium and fine grids.

## 6. Cross-Code and Repeatability Checks

- FUN3D on the medium grid predicted CL within +0.003 of OVERFLOW; CD differed by 1.1 drag counts. Shock position at η = 0.44 differed by 0.8% of chord relative to OVERFLOW.
- Repeated OVERFLOW runs with different initial conditions (freestream, SA field from coarse solution) converged to the same force levels within ±0.2 counts CD and ±0.0015 CL.

## 7. Validation Against Experiment

Primary comparison at M = 0.84, Re = 11.72×10^6, α = 3.06°:
- Measured: CL = 0.282 ± 0.005; CD = 0.0260 ± 0.0006.
- OVERFLOW (fine mesh): CL = 0.287; CD = 0.0274.
  - Bias vs measurement: ΔCL = +0.005 (1.8% high); ΔCD = +0.0014 (5.4% high; ~1.4 counts).
- Cp distributions align well at η = 0.20 and 0.44; shock location within 0.7% chord of taps. At η = 0.80, predicted λ-shock slightly outboard with post-shock plateau ~0.03 Cp deeper than measured; consistent with SA’s tendency to under-resolve tip separation.
- Additional points validated at α = 2.00° and α = 0.00° (same Mach and Re):
  - Max CL deviation across the three α values was 2.4%; CD deviation max 7.8% (drag more sensitive to wake resolution and farfield extent).

Validation data quality:
- Tunnel blockage corrections and α calibration included in the published dataset; our audit confirmed the corrections applied in the cited curves. Tap calibrations and uncertainty budgets posted in repository; overall experimental uncertainty estimated as u_exp(CL) = ±0.005; u_exp(CD) = ±0.0006; Cp uncertainty ±0.005.

## 8. Input Uncertainties and Sensitivity

We propagated plausible variation in freestream and facility parameters to aerodynamics on the medium mesh using Latin Hypercube sampling (N = 200):
- Inputs and ranges: α ±0.05°, M ±0.003, Re ±2%, inflow TI 0.2–0.6%. Uniform distributions for simplicity; correlation between α and M ignored (negligible in this setup).
- Output scatter: σ(CL) = 0.0032; σ(CD) = 0.00035; 95% intervals roughly ±2σ for linear regimes.
- Variance-based sensitivity (Sobol first-order indices):
  - CL: α 0.72; M 0.18; Re 0.05; TI 0.03; residual 0.02 (interactions).
  - CD: M 0.55; α 0.25; Re 0.10; TI 0.05; interactions 0.05.

The study indicates that calibration of α and Mach control is the largest payoff for reducing predictive spread in CL and CD respectively.

## 9. Parameter Setting and Tuning

No adjustment of turbulence model constants was performed. Two items were set to align with the test environment:
- Boundary-layer trips implemented where grit strips were applied in the tunnel; trip extents tuned on a single case (α = 2.00°) by matching the onset of increased skin friction from published oil-flow maps.
- Freestream turbulence intensity fixed at 0.5% and length scale ~0.02c, derived from facility characterization in AR-138.

These selections were then frozen for all validation points. Cross-checking at α = 0.00° and 3.06° showed no overfitting artifacts (errors remained within acceptance limits).

## 10. Software Quality, Configuration, and Traceability

- Version control: All scripts, meshes, and case files in GitLab group aero/m6-study, tag v1.6.3. Commits signed; protected branch; issues logged.
- Build reproducibility: Container images (Apptainer) for OVERFLOW and FUN3D stored at /containers with SHA256 digests; Dockerfiles archived.
- CI: Jenkins pipeline validates environment hash and runs smoke tests (double wedge, flat plate) upon each mesh or solver update. Last run passed on 2026-07-29.
- Run metadata captured in YAML sidecars: solver version, compiler flags, node type, wall time, and random seeds (if any). DOIs minted for final result bundles via the Center’s data catalog.

## 11. Staff Qualifications and Oversight

- Lead analyst: R. Martinez, PhD (aero), 12 years in transonic RANS, author of OFLOW-TIPS-031.
- Secondary analyst: K. Duong, MS, 5 years in turbulence modeling and meshing.
- Peer review: Independent review by S. Natarajan (FUN3D team) and J. Kwon (Applied Aero Test Group). Review comments addressed in disposition matrix QA-REV-M6-2026-08, including stronger wake refinement and explicit report of shock-position metrics.
- Tool training: Both analysts completed OVERFLOW 2.2 user certification in 2025; training certificates archived.

## 12. Planning and Control of the Effort

- The activity followed M&S Plan ECL-VEH-AERO-MSP-042 Rev B, including milestones for grid development, method checks, cross-code audit, validation rehearsal, and formal review gate C.
- Risks logged: potential misplacement of trips, inadequate tip vortex resolution, and compiler-induced differences. Mitigations implemented (grid blocks, fun3d cross-check).
- Schedule adherence: All planned tasks completed by R10 date; one-week slip for adding the fine-mesh wake block.

## 13. Results Summary and Error Budget

For the primary condition (M 0.84, Re 11.72×10^6, α 3.06°), OVERFLOW fine-grid results:
- CL = 0.287, CD = 0.0274. Shock location errors: η = 0.20: 0.4% c; η = 0.44: 0.6% c; η = 0.80: 1.4% c.
- Estimated uncertainties (95% level), combined by root-sum-square of discretization (u_g), iterative (u_it), and propagated input variability (2σ from LHS):
  - CL: u_tot ≈ sqrt(0.0040^2 + 0.0003^2 + (2×0.0032)^2) ≈ ±0.0073 (~2.5%).
  - CD: u_tot ≈ sqrt(0.00050^2 + 0.00005^2 + (2×0.00035)^2) ≈ ±0.00083 (~3.0% absolute; ~11% of CD).
- Combined experimental uncertainty is smaller than modeling uncertainty for CL and comparable for CD. Errors versus data fall within the acceptance thresholds defined in Section 1.

## 14. Robustness, Reproducibility, and Platform Suitability

- Hardware suitability: Pleiades Broadwell nodes demonstrated stable performance; node-to-node runtime variance ±4%. No numerical anomalies from MPI domain decomposition changes.
- Compiler sensitivity: Intel vs GCC builds produced force differences below 0.3 counts CD and 0.001 CL after convergence, satisfying our reproducibility criterion.
- Archive and re-run: Independent re-run by reviewer Kwon on Pleiades Skylake nodes reproduced CL within 0.0012 and CD within 0.4 counts using the archived container and input deck.

## 15. Applicability and Boundaries of Confidence

Based on the physics approximations and validation envelope, we judge the current setup to be applicable to:
- Clean transonic wings without significant control deflection.
- α ∈ [–1°, 4°], M ∈ [0.78, 0.90], Re ∈ [6M, 20M].
Not recommended for:
- Buffet onset prediction or unsteady shock motion characterization.
- High-lift configurations (slats/flaps) or large separations.
- Aeroelastic twist and deflection effects unless separately coupled.

## 16. Documentation and Audit Trail

All material necessary to reproduce this assessment is archived:
- Inputs, meshes, solver decks: doi:10.55504/m6cfd.inputs.v1.6.3
- Results and post-processing scripts: doi:10.55504/m6cfd.results.v1.6.3
- Reviews and checklists: /qa/reviews/2026/m6-cfd
- This report and disposition matrix: /docs/reports/M6-CFD-Cred-2026-08

## 17. Limitations and Open Issues

- Drag sensitivity to grid and turbulence modeling remains higher than lift; within limits for intended use but should be monitored for designs where CD margin is tight.
- SA may misplace the tip λ-shock under strong three-dimensional relief. If future concepts exhibit significant sweep/twist differences, local revalidation is advised.
- Farfield boundary at 25c showed no measurable influence on forces; however, wake sampling for induced drag is still marginal on the medium grid—favor the fine grid for CD studies near design trades.

## 18. Credibility Assessment

Evidence assembled across theory–numerics consistency checks, mesh dependence, input provenance, solver QA, staff competency, and direct comparison to high-quality wind tunnel data supports the following confidence levels relative to our acceptance criteria:
- Aerodynamic performance (CL, shock positions): agreement within 2% and 2% chord respectively across the validated α points; numerical and input-based uncertainty quantified and small enough not to mask bias.
- Drag: within 5–8% of data at the validated points; combined uncertainty ~11% of CD. Meets the 15% threshold for the specified context.
- Process control and traceability: complete, reproducible, and independently reviewed; toolchain maturity is high.

## 19. Decision

By authority of the Vehicle Environment and Loads Branch chief (D. A. Green), the described CFD approach using OVERFLOW 2.2d with the specified meshing and post-processing workflow is accepted for:
- predicting lift, pressure distributions, and shock locations,
- comparing drag trends and estimating drag at the accuracy level stated,

to support pre-PDR aerodynamic performance predictions for clean transonic wing configurations similar to ONERA M6 within M 0.78–0.90, Re 6–20 million, and α –1° to 4°. The method is not approved for buffet onset, high-lift, or aeroelastic-coupled analyses. Acceptance is subject to maintaining the documented process controls, archiving all case metadata, and flagging any out-of-envelope conditions for additional review.

Signed:  
D. A. Green, Branch Chief, Vehicle Environment and Loads  
R. Martinez, Lead Analyst  
Date: 2026-08-06
