# CFD Credibility Assessment Report
Project: Transonic ONERA M6 Wing Loads Prediction  
Software: NASA FUN3D v14.1 (SA-neg, k-ω SST)  
Analyst: L. Cardenas (CFD Group, Aero Sciences Branch)  
Dates: 2026-04-08 to 2026-06-24

## Executive Summary
We evaluated a steady RANS setup in FUN3D to predict aerodynamic coefficients and distributions on the ONERA M6 wing at transonic conditions representative of the AGARD validation case (M∞ = 0.84, Re = 11.72×10^6 based on mean chord, α ≈ 3.06 deg, T∞ = 297 K). The model uses ideal-gas air, adiabatic wall assumption, and fully turbulent boundary layer unless otherwise noted. Three systematically refined meshes were used to quantify numerical error; iterative convergence was tightened to remove solver-induced scatter. Calibration was not employed for lift/drag; a small adjustment was applied only to match wind-tunnel blockage for a consistency check, with both adjusted and unadjusted results reported.

Against high-quality wind-tunnel data, the setup predicts shock location and Cp distributions along key spanwise stations within expected error for RANS with algebraic/eddy-viscosity turbulence closures. The estimated uncertainty at 95% confidence for CL is ±0.006 (combined), and for CD is ±0.0006, dominated by turbulence-model form. Grid-induced uncertainty on the fine grid contributes about 0.2% of CL and 1.5–2.3% of CD.

The workflow is under configuration control with pinned software versions, scripted pre-/post-processing, and stored inputs/outputs. Code-level checks (MMS/regression) and solution-level checks (residual and force histories, y+ audits, and GCI) were completed. The case was peer-reviewed independently. The intended decision is preliminary load sizing for a transonic wing concept; a range-of-validity statement is provided.

Overall, the analysis is appropriate for design guidance and risk reduction at the current stage, with caveats for flow regimes featuring strong shock-induced separation or laminar-transition effects outside the validated envelope.

## 1. Background and Intended Use
The ONERA M6 wing case is a canonical transonic benchmark. We used it to qualify our RANS setup before applying the same modeling choices to an in-house swept-wing planform for early-stage loads and control-surface schedule development. The analysis must:

- Capture shock position and strength enough to avoid mis-sizing torsional stiffness and hinge moments.
- Produce CL and CD within a tolerance of about 2% and 5%, respectively, for preliminary trade studies.
- Support exploration of α in [2.5, 3.5] deg and M∞ in [0.82, 0.86] with a stated reliability.

Consequences of misuse include overweight structures if drag is biased high or insufficient margins if lift/pressure gradients are underestimated. To mitigate, we defined the physical and numerical scope, applied standard quality gates, and compared predicted loads against a trusted dataset of similar flow physics.

## 2. Physical Model, Assumptions, and Applicability
- Physics: Steady compressible RANS with ideal-gas air, single-phase, no heat transfer to the wall (adiabatic), no aeroelastic coupling, no discrete roughness or ice.
- Near-wall treatment: Low-Reynolds number resolution with target y+ ≤ 1 on the fine grid (95% of faces under 1.2; max 1.6 near the root).
- Turbulence closures:
  - Baseline: SA-neg (Spalart–Allmaras with negative-clipping fix).
  - Cross-check: k-ω SST with production limiter.
- Transition: Nominally fully turbulent. A sensitivity run with γ–Reθ intermittency model indicates CL changes by +1.2% and CD by +2.8% at these conditions; full transition modeling was not adopted for baseline but is flagged as a limitation.
- Flow regime: Attached to mildly separated bubble possible at outboard sections near shock. The SA-neg model is known to be adequate for attached or mildly separated transonic flows but may under-predict separation onset.

Range-of-validity declaration:
- Aerodynamic coefficients and pressure distributions are supported for M∞ ∈ [0.82, 0.86], α ∈ [2.5°, 3.5°], Re within ±15% of nominal, clean wing without deployables, small control deflections (<3°). Outside this, increased model-form error is likely.

## 3. Software and Numerical Methods
- Solver: FUN3D v14.1, commit 1cc0f1e (tagged build), double precision, Roe/Turkel flux split with Venkat limiter, second-order spatial reconstruction, dual-time stepping for pseudo-steady convergence.
- Linear solver: Point-implicit with ILU(0) preconditioning; multigrid V-cycle enabled (3 levels).
- Parallelization: MPI across 192 ranks (NAS Pleiades, Haswell nodes). Repeat runs across 96, 192, 384 ranks showed coefficient repeatability within 0.05 counts in CL and 0.2 counts in CD.
- Discretization and wall spacing: Prism layers (30 layers, growth 1.2), minimum first-cell height 4.2e-6 m, unstructured tetrahedral core.
- Time advancement: Pseudo-time CFL ramp to 300; 12,000–18,000 iterations to reach tight residual targets on fine grid.

Software controls:
- Version control in GitLab; solver, scripts, and meshes tied to a release tag (CFD-O6-TRN-R1).
- Regression test suite: 812 tests passed on this build (including SA MMS and sub-/transonic cases).
- Jenkins CI pipeline recorded pass/fail and artifacts; reproducer scripts archived.

## 4. Geometry, Boundary Conditions, and Inputs
- Geometry source: ONERA M6 public IGES, verified against AGARD AR-138 coordinates. Small fairing gaps were sealed using pointwise spline patches (<0.05% planform area change).
- Domain: C-grid-like unstructured volume, outer boundary at 20 chords.
- Inflow/outflow: Farfield Riemann BC with target M∞ by static pressure and temperature spec; turbulence intensity 1% with length scale = 1% of mean chord for SST case; SA requires ν~ via standard initialization.
- Wall: No-slip, adiabatic. Surface roughness neglected.
- Reference conditions: Re via μ(T) from Sutherland’s law; Prandtl numbers default.
- Angle-of-attack: Geometric rotation about quarter-chord axis; α tuned to match normal-force component per AGARD reference α = 3.06°.

Input pedigree and checks:
- Farfield conditions drawn from AGARD data set; tunnel wall interference not modeled directly, but a one-pass correction applied in a sensitivity study (Section 8). This yields small improvements in shock location agreement; baseline remains uncorrected to maintain model independence.
- Mesh generation with Pointwise 18.4R2. Independent meshing by a second engineer replicated key y+ and growth metrics; differences in CL < 0.3%.

## 5. Quality Management and Traceability
- Planning: Analysis plan AP-CAS-ONERA-06 v1.3 approved before runs. It specified objectives, acceptance bands, and review gates.
- Configuration management: DOORS Next used to map objectives to cases, meshes, and solver settings. All files under immutable artifact storage with checksum (SHA-256) logging.
- Personnel: Primary analyst certified per team’s CFD competency matrix (Level 2). Secondary reviewer (Level 3) performed spot checks.
- Process adherence: Pre-run checklist (32 items) and post-run checklist (18 items) completed; exceptions documented (none open).

## 6. Code-Level Checks (Solver Mathematics)
- Manufactured-solution test: FUN3D SA MMS case “SA_3D_MMS_A1” executed on 4 successively refined tetrahedral meshes (0.53M → 17.1M cells). Observed order of accuracy:
  - L2 velocity: 1.97 ± 0.05
  - L2 eddy viscosity: 1.88 ± 0.07
- Energy/entropy consistency: Monitored across refinement; no anomalies within 0.1% of analytic MMS values.
- Unit and regression tests: 812/812 pass. No local modifications to turbulence closures.

These checks provide confidence that the discretization and SA implementation behave as designed.

## 7. Solution-Level Checks (Convergence and Discretization)
Mesh refinement study:
- Coarse: 4.3M cells (28 wall layers), medium: 8.7M, fine: 17.5M; refinement ratio r ≈ 1.23 in characteristic cell size near the wing and in wake.
- Iterative convergence: L2 residuals of continuity and momentum dropped by >6 orders; lift/drag histories flat to within 0.0002 for final 1,000 iterations. Force oscillations correlated with multigrid cycles damped below 0.03 counts.
- Monitors: Cp at shock foot on y/b = 0.44, 0.65 stabilized within ±0.008.

Grid-induced uncertainty (GCI, 95%):
- Extrapolated CL∞ = 0.2719; fine-grid CL = 0.2714; GCI_fine(CL) = 0.20%.
- Extrapolated CD∞ = 0.01611; fine-grid CD = 0.01646; GCI_fine(CD) = 2.3%.
- Shock x/c at y/b = 0.65: 0.425 (fine), 0.419 (medium), 0.408 (coarse); apparent order p ≈ 1.9.

y+ audit:
- Fine grid median y+ = 0.73; 95th percentile 1.2; local pockets up to 1.6 near junctions. SA-neg acceptable under these values.

Repeatability:
- Two independent restarts from different initializations produced CL within 0.0003 and CD within 0.0005 on the fine grid.

## 8. Sensitivity to Modeling Choices and Inputs
- Turbulence model:
  - SA-neg baseline CL = 0.2714, CD = 0.01646.
  - k-ω SST: CL = 0.2698 (−0.6%), CD = 0.01678 (+1.9%). Shock x/c shifts aft by ~2% chord at mid-span. Cp RMS error slightly worse with SST at inboard stations.
- Transition modeling (γ–Reθ):
  - With estimated Tu = 0.5%, Reθcrit default, CL = 0.2747 (+1.2%), CD = 0.01693 (+2.8%). Shock location nearly unchanged; pressure recovery near TE slightly altered.
- Flow condition perturbations:
  - Δα = ±0.2° yields ΔCL ≈ ±0.019, ΔCD ≈ +0.0004/−0.0003.
  - ΔM∞ = ±0.005 yields ΔCD ≈ ±0.00022; CL weakly sensitive (±0.0015).
- Numerical schemes:
  - Switching to HLLC flux and Barth–Jespersen limiter changes CD by +0.00018; CL within 0.0006.
- Wall interference correction:
  - Applying a single-parameter correction to emulate tunnel blockage (per AGARD note) moves shock x/c forward by ~0.005 and reduces CD by ~0.0001, improving match at outboard stations. Baseline remains uncorrected for independence.

These studies indicate turbulence closure and small AoA offsets dominate variability for target outputs.

## 9. Experimental Reference and Its Quality
Reference data: AGARD Report AR-138 and supplemental datasets curated by the AIAA Drag Prediction Workshop (DPW-III) for the ONERA M6.

- Measurements: Pressure taps along spanwise stations, force balances for CL/CD, and Schlieren images for shock visualization. Reported uncertainty: σ(Cp) ≈ 0.01–0.02, σ(CL) ≈ 0.003, σ(CD) ≈ 0.0003.
- Facility: Cryogenic-capable pressurized tunnel not required here; standard atmospheric tunnel used historically. Flow quality measured: Tu ≤ 0.5% in test section.
- Relevance: Exact geometry match, Reynolds and Mach near nominal within measurement bands. Wall interference present; published corrections available.

Data handling:
- Digitized Cp curves verified by cross-check against original tables. Independent re-digitization by reviewer resulted in max Cp difference of 0.007.
- Only data segments with documented sensor health were used; two outlier taps at y/b = 0.65 excluded per AR-138 errata.

## 10. Comparison to Test and Validation Metrics
Global coefficients (fine grid, SA-neg, uncorrected tunnel effects):
- CL_pred = 0.2714 vs. CL_test = 0.2720 → Δ = −0.0006 (−0.22%)
- CD_pred = 0.01646 vs. CD_test = 0.01620 → Δ = +0.00026 (+1.6%)

Pressure distributions:
- RMS error in Cp along x/c for y/b = 0.44: 0.036; y/b = 0.65: 0.041. Shock location error ≤ 0.015 in x/c.
- Peak pressure undershoot upstream of shock within 0.04 in Cp; post-shock plateau slightly over-predicted, typical of SA behavior.

Validation metrics:
- Using area-weighted L2 norm of Cp error across all stations: E2_norm = 0.039.
- Whitney–Coleman type validation ratio VR for CL with combined uncertainty: VR = 0.42 (passes threshold τ = 1).
- For CD: VR = 0.86 (passes but indicates tighter margins than for CL).

Integral loads and distributions are in family with DPW-III RANS baselines and fall within the interquartile band for SA-based submissions.

## 11. Uncertainty and Error Budget
We combined numerical, input, and model-form components in a root-sum-square sense to obtain approximate 95% bounds:

- Numerical (from GCI): u_num(CL) = 0.00055; u_num(CD) = 0.00037.
- Input (α, M∞, T, μ): u_in(CL) = 0.0032, u_in(CD) = 0.00021 based on perturbation studies and sensor specs.
- Model form (turbulence/transition): u_mod(CL) = 0.0048, u_mod(CD) = 0.00048 derived from closure comparisons and literature spread for similar flows.

Combined:
- U95(CL) ≈ ±0.0060
- U95(CD) ≈ ±0.0006

Dominant contributors: turbulence closure and AoA setting. Numerical uncertainty is the smallest slice on the fine grid.

## 12. Robustness, Repeatability, and Edge Cases
- Robustness across operating points: The solver converged reliably for α ∈ [2.5°, 3.5°], M∞ ∈ [0.82, 0.86]. For α > 3.8° at M∞ = 0.86, mild shock-induced separation emerged; residuals plateaued higher, and solution sensitivity to limiter choice increased—flagged as out-of-scope for the baseline method.
- Initialization robustness: Uniform field and potential-flow initializations both converge to indistinguishable solutions within the uncertainty bands.
- Post-processing repeatability: Two analysts using independent ParaView pipelines obtained the same CL/CD within 0.0001, Cp curves within 0.003.

## 13. Human and Organizational Controls
- Training: Primary analyst completed FUN3D user course (NASA Langley) and internal turbulence modeling seminar. The reviewer has authored prior DPW contributions.
- Checklists: Human-factors review ensured that angle-of-attack definition, reference area, and sign conventions were consistent across solver and post-processor. No discrepancies found.
- Independence: The reviewer and the person who prepared the mesh were not involved in downstream design decisions. Peer review notes and responses are archived (PR-ONERA-06-REV1).

## 14. Computational Platform and Reproducibility
- Hardware: NAS Pleiades, Haswell nodes (2× Intel E5-2680v3 per node), Infiniband FDR, RHEL 7.8, Intel MPI 2019.7, GCC 10.2.
- Determinism: FUN3D’s reductions lead to round-off level variations across MPI layouts; observed impact on CL/CD is negligible (Section 3).
- Reproducibility: A single “make-run.sh” script provisions the environment, fetches tagged inputs, executes, and validates outputs against expected checksums. A dry-run mode verifies pathing without launching the solver.

## 15. Documentation, Traceability, and Community Practices
- Self-contained package includes geometry, meshes, control files, solver build info, run scripts, and post-processing notebooks (Jupyter, Python 3.10).
- Decision log: Any deviations from the plan or additional runs are captured in JIRA (CFD-ONERA-214 through 224).
- External benchmarking: Results compared with DPW-III archives and FUN3D verification examples; our coefficient predictions sit in the midrange of RANS submissions using SA.

## 16. Limitations and How They Affect Use
- Lack of explicit wall interference modeling means slight bias in CD may persist relative to tunnel-corrected values; for flight conditions this bias is not expected, but when comparing to test it should be considered.
- Absence of transition modeling in baseline limits fidelity for lower Tu environments or laminar pockets; sensitivity indicates at most a few percent swing in coefficients at this condition.
- Shock-induced separation is only lightly validated; for α or M∞ beyond the stated envelope, error may grow nonlinearly.
- Model updates (e.g., curvature-corrected SA or Reynolds stress closures) were not included in this qualification, pending schedule; adoption would require rerunning Sections 7–11.

## 17. Conclusions for Decision Makers
- The current CFD setup satisfies the needs of preliminary design for transonic wing loads in the stated operating envelope. Agreement with well-characterized experiments is good for lift and acceptable for drag.
- Numerical errors are small relative to model-form and input uncertainties; convergence and mesh studies were completed with due rigor.
- The analysis package is repeatable, documented, and under configuration control, with independent review complete.

Recommendation: Proceed to apply this workflow to the in-house wing for α ∈ [2.5°, 3.5°], M∞ ∈ [0.82, 0.86]. For conditions indicating possible massive separation or transition sensitivity, plan to augment with scale-resolving methods or incorporate transition models, and refresh the validation evidence.

## 18. Evidence Map to Credibility Elements (informal)
- Purpose and consequences: Clear statement of intended decisions and off-ramps.
- Physical adequacy: Governing equations and assumptions match the flow regime.
- Software soundness: Code-level tests (MMS/regression) passed on the frozen build.
- Numerical quality: Mesh/iteration studies with quantified error bars (GCI).
- Data lineage: Geometry and test conditions trace to AGARD, with handling documented.
- Boundary/IC suitability: Farfield and wall models consistent with physics; AoA cross-checked.
- Model-form scrutiny: Turbulence and transition sensitivities explored.
- Sensitivity/uncertainty: Dominant contributors identified and propagated to output intervals.
- Test correlation: Quantitative metrics against pressure and forces.
- Robustness and repeatability: Multiple runs, MPI layouts, and post-processing pipelines agree.
- Human/organizational: Training, checklists, and independent review complete.
- Configuration and documentation: Artifacts, scripts, and logs archived; reproducible runs demonstrated.
- Applicability statement: Operating window specified; limitations highlighted.
- External acceptance: Alignment with community benchmarks (DPW) and literature.

## 19. Action Items
- For drag-critical trades, consider including wall-interference corrections when comparing to tunnel data.
- If extending to α > 3.5° or M∞ > 0.86, plan additional validation with separated-flow references or switch to RANS–DES hybrid.
- Evaluate curvature-corrected SA or v2-f for outboard shock-induced separation if encountered on the in-house wing.

End of report.
