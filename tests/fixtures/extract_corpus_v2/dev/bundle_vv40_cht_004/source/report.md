To: RFA Tip Program Lead
From: CHT V&V Team
Date: 2026-08-06
Subject: Credibility status for the irrigated RF ablation tip CHT model (vv40 alignment)

Summary of how the model will be used
- Purpose: Predict peak tissue temperature at 2 mm depth and lesion depth after 30–60 s RF delivery to support labeling (thermal safety margin and recommended power/flow envelope). Not for direct patient-specific planning.
- Decision impact: Moderate consequence if wrong (risk of steam-pop or under-treatment), model has medium-to-high influence on labeling claims alongside bench tests.
- Targeted credibility: “High” for numerics and data pedigree; “Moderate-to-high” for biological parameters and external validity.

Model description and physics choices
- Conjugate heat transfer between flowing blood/saline and tissue. Fluid: incompressible, k–ω SST; Re ≈ 300–900 near tip. Solid: transient conduction in platinum-iridium tip and myocardial tissue with Pennes perfusion term. RF power deposition approximated as a volumetric heat source informed by separate EM analysis (500 kHz) and calibrated to fixture measurements.
- Assumptions: Isotropic tissue conductivity; no boiling phase change (usage bounded to <65 °C at 2 mm). Tip–tissue contact modeled via a conformal gap determined from applied force; no slip in fluid; radiation neglected.
- Energy balance check: Interfacial heat flux continuity satisfied to within 0.2% in all runs.

Software quality and implementation checks
- Tooling: Ansys Fluent 2024R1, double precision; UDF for time-varying heat source (code reviewed, unit tests with 100% branch coverage; CI pipeline includes regression tests on 9 cases).
- Code-level checks: Method of manufactured solutions on transient conduction and a coupled slab case produced second-order L2 convergence (1.98–2.05) for temperature; UDF returns analytic source within 0.1%.
- Reproducibility: Same case on two clusters (AMD EPYC vs Intel Xeon) matched peak T within 0.05 °C.

Numerical solution quality
- Mesh refinement study: 1.2M / 2.4M / 4.8M cells with y+ < 1 at tip; 12 prism layers. Peak tissue T2mm changes: +1.9% (coarse→mid), +0.7% (mid→fine). Richardson extrapolation yields GCI 95% ≈ 1.1% for T2mm; lesion depth GCI ≈ 1.6%.
- Time step sensitivity: Δt = 1 ms baseline; halving to 0.5 ms changes T2mm by 0.8% and lesion depth by 0.5%. Backward Euler with second-order transient option tested; iterative residuals <1e-6 (energy <1e-8); 12 inner iterations per step ensures stable norms.
- Solver cross-check: One operating point repeated in STAR-CCM+ 2023.3; T2mm within 1.4% and lesion depth within 0.9%.

Geometry, boundary data, and parameter pedigree
- Geometry: 3.5 mm irrigated tip (CAD from vendor rev D); fixture myocardium block from CMM scan; tolerances ±0.1 mm on dome radius and port diameters.
- Boundary conditions: Blood crossflow 0.10–0.30 m/s (37 °C), saline irrigation 17–30 mL/min, RF power 20–35 W; contact force 10–25 g. All measured per test protocol; traceable calibrations (NIST-traceable mass and flow benches).
- Materials: Tissue conductivity 0.52–0.72 S/m (temp dependent), k = 0.53 W/m-K; perfusion 0.004–0.012 s^-1. Priors from literature; posterior estimates from calibration below.

Calibration and sensitivity
- Parameter tuning used six independent gel-phantom runs at 25 W to set EM-to-thermal source scaling factor; resulting factor uncertainty 4.2% (95% CI).
- Global sensitivity (Morris screening, confirmed with Sobol on top three): dominant contributors to T2mm are perfusion rate (μ* = 0.31), contact force surrogate gap (μ* = 0.27), and RF source scale (μ* = 0.22). Flow speed is secondary (μ* = 0.12).

Validation evidence and comparators
- Bench testing: 12 ex vivo porcine myocardium runs spanning 20/25/35 W and 0.10/0.20/0.30 m/s; n=3 repeats each. Thermocouples (Type T, 40 AWG) at 2 mm depth; IR camera for surface mapping. Instrument uncertainties: ±0.3 °C (TC), ±0.2 °C (IR); spatial placement ±0.2 mm.
- Test–model similarity: Péclet and Biot numbers within 7% of in silico values; saline jet Reynolds within 10%. Tip force and insertion angle matched to ±2 g and ±3°, respectively.
- Agreement: Across 12 points, mean absolute error in T2mm = 0.9 °C (RMSE 1.1 °C). Lesion depth at 60 s within 0.6 mm MAE (8.4%). No systematic bias with power or flow (p>0.2).
- Coverage vs intended use: Planned labeling envelope 20–35 W, 0.10–0.30 m/s blood speed, 10–25 g force, 17–30 mL/min irrigation is fully bracketed by validation matrix; extrapolation is not claimed outside these ranges.

Uncertainty propagation and decision metric
- Inputs treated as random per measured distributions; 200 Latin hypercube samples on the mid mesh with correction from mesh study.
- 95% interval for T2mm at worst-case within envelope (35 W, 0.10 m/s, 10 g, 17 mL/min): 61.8–64.9 °C; probability of exceeding 65 °C < 2%. Lesion depth 4.7–6.1 mm (95%).
- Combined uncertainty budget includes instrument error, placement tolerance, and source-scale uncertainty; validation-data noise folded into posterior predictive checks.

Governance, independence, and limitations
- Configuration managed in Git (tag v1.6.2; Fluent case hash 0x7b1a…); run logs and postprocessing scripts archived in DVC.
- External review: Dr. L. Chen (CHT SME, not on dev team) audited the setup and three case files; comments resolved (see CR-142).
- Known gaps: No boiling or steam-pocket modeling; patient-specific vascular geometries not included; tissue anisotropy neglected. Not for use above 65 °C at 2 mm or for atypical flows (>0.5 m/s).
- Repeatability: Triplicate runs vary <0.3 °C in T2mm with identical inputs.

Bottom line
- For the stated context of use, the evidence base supports deploying the model as a primary line of evidence alongside bench testing. Remaining risk is dominated by biological parameter variability and the no-boiling assumption; both are bounded by the operating envelope and validation results. No blocking issues for labeling submission were identified; recommend proceed, with the above limitations stated explicitly.
