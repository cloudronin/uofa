# CFD Credibility Briefing — S-duct Inlet to AIP Swirl/Recovery

- Project: Mid-fidelity CFD of a 1.5-turn S-duct feeding a small turbofan inlet
- Purpose: Predict area-averaged total-pressure recovery and swirl angle distribution at the Aerodynamic Interface Plane (AIP) for intake operability screening at M=0.30, ReD≈3.2e6
- Codes/Platforms:
  - Primary: STAR-CCM+ 2022.1, double precision, segregated flow solver
  - Secondary spot-check: SU2 v7.5 (for one coarse case)
  - Hardware: 256-core AMD EPYC cluster, 512 GB RAM per node; runs 12–18 h for medium mesh
- Review scope: model setup, numerical practices, comparison to available wind tunnel data, uncertainty discussion, and process hygiene

## Geometry and Flow Regime

- Geometry
  - Parametric S-duct: inlet diameter 0.25 m; centerline offset 0.2D; AIP plane 1.8D downstream of inlet lip
  - Internal bleed slot at 45° from top; slot width 0.005 m (modeled as porous face)
- Conditions
  - Target: M=0.30, Tt,in=288 K, Pt,in=101.3 kPa; nominal inlet turbulence intensity 1%
  - Reported tunnel data set: M=0.30±0.01, 5% turbulence grid upstream of bellmouth
  - Reynolds number based on inlet diameter ReD≈3.2e6; compressibility included

## Computational Setup (summary)

- Governing equations: steady RANS for production runs; density-based solver not used (incompressible assumption with compressibility correction)
- Turbulence models:
  - Baseline: k-omega SST with curvature correction (Spalart–Shur)
  - Sensitivity: SA-neg and SST-Transition Gamma–Theta attempted on coarse mesh
- Wall treatment: integrated to wall (claimed y+<1), 20 prism layers, growth 1.2, total BL thickness ~5 mm
- Discretization: upwind (2nd-order) for convection; central differencing for diffusion
- Convergence criteria: residuals below 1e-5 and flat-lined mass flow and AIP recovery for 500 iterations

## Mesh Topology and Near-Wall Resolution

- Mesh family: polyhedral core with trimmed hexa near bends; prism layers near walls
- Counts:
  - Coarse: 6.3M cells; 12 layers; target y+≈2–3
  - Medium: 14.7M cells; 20 layers; target y+<1 across >95% wall area
  - Fine: 48.9M cells; 26 layers; target y+≈0.4 near guide surfaces
- Quality targets: max skewness <0.85, expansion <1.5; junction refinement at splitter and bleed slot edges
- Note: On the medium grid, post-run audit showed area-averaged y+ at mid-duct ~3.1; downstream of slot peaked at 7.4

## Numerics and Solver Controls

- Linear solver: AMG with ILU(0) preconditioning; pseudo time-stepping ramped to CFL~100 for stability
- Under-relaxation: momentum 0.3, turbulence 0.5, pressure 0.25
- For unsteady tests of swirl unsteadiness: dual-time URANS, Δt=1e-4 s, 15 inner iterations/step, 0.2 s physical time
- Pressure-velocity coupling: SIMPLE for steady; PISO for URANS cases
- Temporal convergence: steady results used for final metrics; URANS used only to inspect AIP swirl RMS

## Mesh Refinement and Convergence Behavior

- Mesh refinement study:
  - Metric: AIP total-pressure recovery (PR), and integrated swirl angle RMS (θRMS)
  - Results (steady) — Coarse/Med/Fine:
    - PR: 0.945 / 0.952 / 0.958
    - θRMS: 6.3° / 5.7° / 5.5°
- Claimed outcome: “variations under 1% indicate grid independence”
- Calculated apparent order (p) from PR: 1.7; GCI95% (Med→Fine) for PR: 0.7%
- Residuals:
  - Momentum residuals reduced below 1e-5 on all three meshes; mass imbalance <0.2%
  - However, AIP PR continued drifting ~0.8% over final 300 iterations on coarse grid
- Note: Internal spreadsheet shows Coarse→Fine PR shift of 1.3% absolute (not <1%); θRMS shift 0.8°

## Domain Extents and Boundary Conditions

- Upstream: 2.0D straight inlet duct added; uniform total pressure/temperature with 1% turbulence intensity; no imposed swirl
- Downstream: 4.0D straight exit to AIP; static pressure outlet tuned to match target mass flow
- Bleed: porous jump with K=2.5e7 kg/m4; calibrated to measured 2% bleed mass fraction
- Wall: hydraulically smooth; no roughness modeled; adiabatic
- Domain reflection: symmetric half-model not used; full 360°
- Note: The SU2 coarse check used only 0.5D upstream and 1.5D downstream due to memory limits
- Inlet turbulence intensity later adjusted to 3% to improve match to rake profiles

## Physical Modeling Choices and Justification

- Turbulence
  - SST selected for separated curvature-influenced bends; curvature correction enabled
  - Transition model runs did not converge on fine grid; coarse grid SA-neg predicted lower θRMS by ~0.4°
- Compressibility
  - Weakly compressible formulation with density update; M<0.3 limit marginally exceeded locally (Mmax≈0.34)
- Bleed slot
  - Modeled as porous face without internal plenum; loss coefficient tuned to achieve target bleed
- Roughness and leakage
  - Ignored; test article had measured Ra=1.2 μm; panel gaps taped in tunnel

## Comparison to Wind Tunnel Data (Validation Snapshot)

- Data set: AIP rake, 40-probe donut; traversed swirl vanes; reported at M=0.30, ReD=3.1e6–3.3e6, 5% inlet turbulence with screen
- Matching approach: simulation set to M=0.30 by outlet pressure; inlet turbulence initially 1%, later 3%
- Metrics
  - PR (area-avg at AIP): Test 0.955±0.003; CFD (Med) 0.952; CFD (Fine) 0.958
  - θRMS: Test 5.6°±0.2°; CFD (Med) 5.7°; CFD (Fine) 5.5°
  - Sectoral swirl bias (top vs bottom): Test +2.1°; CFD +1.5°
- Note: Internal run log “M030_case07_med” lists converged Mach 0.35 at AIP ring; corrected later by retuning outlet pressure but figures in Slide 6 reflect pre-correction values
- Unsteadiness: URANS predicted low-frequency oscillation at 12 Hz; no corresponding spectral content in test (tunnel fan masking uncertain)

## Sensitivity and Uncertainty Discussion

- Varied parameters
  - Inlet turbulence intensity (1–7%), porous K (±20%), bleed fraction (1–3%), wall roughness (0–20 μm), outlet static pressure (±0.5 kPa)
- Method
  - Claimed: 50-sample Monte Carlo with normal priors; PR mean 0.955, 95% band ±0.006
  - Actually performed: 12-point Latin Hypercube on medium mesh due to cycle budget; linear surrogates used to extrapolate
- Dominant contributors
  - Porous K and bleed fraction explain ~70% of PR spread; inlet TI drives θRMS
- Mesh-induced component
  - GCI propagated as additional variance; combined (RSS) PR uncertainty ±0.9%
- Caveat: Random seeds not fixed; two LHS runs repeated with different sequences produce slightly different surrogate fits

## Tool Pedigree and Numerical Code Checks

- Vendor verification
  - STAR-CCM+ documentation cites MMS for laminar Navier–Stokes and RANS turbulence closure unit tests; observed 2nd-order convergence in smooth flows
- Internal spot-check
  - Manufactured vortex decay assessed in SU2 (coarse, medium): observed order ≈1.95 for velocity L2
  - For STAR-CCM+ duct case, settings toggled to “2nd-order upwind” throughout
- Stability handling
  - For fine grid near bleed, a hidden restart used first-order upwind for 500 iters to damp oscillations; control file shows “convScheme=1st” for steps 1200–1700, then reverted to 2nd
- Takeaway: nominal second-order setup, with transient first-order segments for robustness

## Configuration Control and Reproducibility

- Case files under Git LFS: repo tag “sduct_AIP_v13”
- One-off fixes
  - Porous jump coefficient adjusted in GUI after mesh load; change log captured in slide notes, not in Git commit
  - Compiler flag “-ffast-math” enabled on SU2 build for speed; removed later for final runs
- Regression tests
  - Nightly template case (straight pipe) within 0.1% of reference PR
  - S-duct template not part of regression suite
- Randomness
  - LHS samples generated without preserved seed in first attempt; repeated with fixed seed for last 6 points

## Assumptions and Known Limitations

- No inlet swirl imposed; tunnel used honeycomb/screen but residual swirl unknown
- Bleed plenum flow path not modeled; using porous face can mis-represent local secondary flows
- Steady-state RANS used for reporting, despite observed transient features in URANS
- Wall roughness and surface waviness neglected; matches “as-taped” test condition only approximately
- Geometric fidelity at slot chamfer simplified (sharp edge in CFD vs 1 mm radius in test)

## Open Issues and To-Do

- Re-run medium mesh with fixed M=0.30 and y+ audit; document post-processing consistency
- Add 1D plenum model or CFD coupling for bleed to avoid K tuning
- Incorporate inlet turbulence grid model (TI=5%) to match test inflow better
- Expand sensitivity runs to at least 30 samples and lock seed; include roughness explicitly
- Promote S-duct case to regression suite; log GUI-only tweaks in scripted form

## Bottom Line

- Predictive capability for AIP PR and θRMS looks reasonable on medium/fine grids; differences to test within bands when tuned
- Confidence qualifiers
  - Mesh influence small but not negligible; reported <1% variation conflicts with 1.3% absolute shift noted
  - Boundary conditions partially calibrated (porous K, inlet TI), limiting pure prediction claims
  - Numerical order largely second-order, with intermittent first-order segments for stability
- Readiness: acceptable for preliminary operability screening with caveats; not yet suitable for certification-level margins
