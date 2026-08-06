# Slide 1 — CFD Credibility Summary: S‑Duct Inlet (APU Bleed Conditions)

- Purpose: Evaluate whether the current CFD setup is fit to estimate mean pressure recovery and swirl at the AIP for an S‑duct inlet
- Code: Ansys Fluent 2023 R2, pressure‑based coupled solver
- Geometry: 0.8 m long S‑duct, area ratio 1.05, gentle double curvature, circular AIP, 0.25 Mach at nominal mass flow
- Team: Aero CFD group, Task MS-07, Rev D
- Decision requested: approve/not approve model for performance roll‑ups in PRELIM-3 gate


# Slide 2 — Context of Use and Stakes

- Intended use:
  - Predict mean total pressure recovery at AIP, PR = P0_out/P0_in, for design mass flow (2.3 kg/s) ±2%
  - Provide sector‑averaged swirl angle and uniformity metrics at AIP for operability screening
- Excluded: high-frequency content (acoustics), crosswind ingestion, water/icing, distortion transfer to compressor map
- Tolerance for decision: ±2% on PR, ±2 degrees on sector‑averaged swirl
- Program pressure: data needed for duct fairing freeze in 3 weeks


# Slide 3 — Geometry, Flow Regime, and Physics Scope

- Reynolds number at inlet: ~2.1e6 (air, 300 K), subsonic, weak compressibility
- Single-phase, dry air, ideal-gas. Energy equation disabled; density via compressibility correction (Fluent “ideal gas” law)
- Turbulence: k‑ω SST for adverse pressure gradient handling (as per analysis plan ANL‑SST‑08)
- Treatment of separation: steady RANS; no transition model
- Note: initial scoping memo mentions Spalart–Allmaras for speed; later plan switched to SST for accuracy


# Slide 4 — Mesh Strategy and Near‑Wall Treatment

- Mesh type: poly‑hexcore via Fluent Meshing; boundary layer prism stacks
- Three grid levels:
  - Coarse: 4.7M cells; Medium: 9.2M; Fine: 18.5M
- Layering: 30 prisms, growth 1.15, target y+ 0.5–1.0 on fine grid for low‑Re SST formulation
- Curvature/proximity controls at lip and inner bend; base size 4 mm refined to 0.6 mm in separation-prone regions
- Reported mesh diagnostics at handoff:
  - Non‑orthogonality P95 < 50 deg; skewness P95 < 0.6
  - Near‑wall spacing “achieved y+ < 1 everywhere on fine grid” (Mesh Log ML‑SDA‑18)


# Slide 5 — Solver Controls and Numerics

- Spatial discretization: second‑order upwind for momentum and turbulence; pressure staggering PRESTO!
- Pressure‑velocity coupling: coupled scheme
- Pseudo‑transient with CFL ~50; under‑relaxation defaults unchanged
- Convergence criteria per run notes:
  - Residuals < 1e‑6 for continuity and momentum; monitors flat for 1,000 iterations
  - Mass imbalance < 0.1%
- Turbulence model in case files:
  - Case templates labeled “sa_pseudoTrans” in the run directory; analyst notes say “SST used”
- Precision and acceleration:
  - Double precision run flag set; AMG GPU acceleration enabled on A100s (cluster queue cfd-gpu)


# Slide 6 — Boundary Conditions and Operating Envelope

- Inlet: total pressure 101.3 kPa, total temperature 300 K, turbulence intensity 5%, length scale 0.05 m
- Outlet: static pressure adjusted to hit 2.3 kg/s; tested ±2% backpressure for slope
- Walls: smooth, no‑slip, adiabatic
- AIP plane defined 0.1 m upstream of flange per rig spec
- Hot‑wire survey from the rig indicates inlet turbulence intensity 1–1.5% (Test Note TN‑HW‑22); CFD used 5% to “cover installation effects”


# Slide 7 — Run Management, Code Quality, and Platform

- Platform: 2 nodes x 2 AMD EPYC 7742, 128 cores total; some reruns on 4 x NVIDIA A100 (AMG)
- Software provenance:
  - Fluent 2023 R2 documented in plan; run logs show 2023 R1 on coarse grid; fine grid on 2023 R2
  - Licensing feature mix identical according to FlexLM logs
- Code checks:
  - Template suite passed internal lid‑driven cavity and Poiseuille benchmarks (L2 velocity error < 1%)
  - Manufactured solution test referenced in V&V plan; execution record not found in run folder
- Mixed‑precision note:
  - GPU AMG with “single precision smoothers” auto‑enabled; solver still set to double precision overall


# Slide 8 — Traceability, Repeatability, and Configuration Control

- Case/mesh versions tracked in GitLab repo “sduct-apu”; tags: mesh_v5, case_sst_v3
- Solver journal seeds fixed; “repeat runs reproduce within 0.1% on AIP PR” (Analyst Log AL‑07)
- Reproduction check (independent machine, same repo tag):
  - PR_medium mesh: 0.9715 vs 0.9627 (+0.9%)
  - Sector 3 swirl mean: 3.2 deg vs 3.5 deg (−0.3 deg)
- Repo commit for final fine mesh run: v4.1‑dirty (uncommitted change in turbulence options file)


# Slide 9 — Solution Quality Checks (Iterations, Monitors, and Grid Study)

- Convergence observed:
  - Residuals reached 1e‑4 (continuity 9e‑5, momentum ~2e‑4) on fine grid; last 600 iters show flat force monitors
  - Mass imbalance 0.08%
- Grid refinement:
  - PR: coarse 0.965, medium 0.968, fine 0.973 (extrapolated 0.977)
  - Quoted GCI (fine vs medium): 0.8% assuming p=2
  - Note: limiter active in separated corner; local order effectively ~1 there
- Near‑wall review (post‑run):
  - y+ histogram at inner‑bend corner: mode ~18, 90th percentile 32 on medium mesh
  - Fine mesh patching reduced 90th percentile to 12, still above the low‑Re target in separation zone


# Slide 10 — Experimental Comparison (Wind‑Tunnel Rig GT‑SD‑03)

- Test conditions: 101 kPa, 295–302 K, 2.3 kg/s ±0.02 kg/s; AIP rake and 5‑hole probe, calibration June 2025
- Reported measurements:
  - PR_meas = 0.968 ± 0.006 (95%); sector‑averaged swirl 2.0–4.5 deg depending on sector
- CFD overlay:
  - Summary slide shows PR_CFD(fine) = 0.973 (within 0.5% of mean)
  - Swirl: CFD peak sector 6.1 deg vs probe 4.2 deg; sector averages within ±2 deg in 3/4 sectors
- Plot detail (Validation Pack VP‑SDA‑D):
  - PR trace on AIP arc indicates 0.962–0.966 in inner‑bend sectors on fine mesh
  - Temperature held at 300 K in CFD; test logs show 295 K; density difference ~1.7% not corrected in overlay


# Slide 11 — Sensitivity and Uncertainty

- Sensitivities (one‑at‑a‑time):
  - Inlet TI: 1% → 5% increases PR by +0.3 to +0.4%; swirl spread narrows by ~0.5 deg
  - Backpressure +2%: PR decreases by ~0.5%; peak swirl +0.8 deg
  - Turbulence model SA vs SST: PR −0.2%; swirl −0.6 deg (SA)
- Combined uncertainty (stated):
  - Numerical (grid + iteration): 0.8%
  - Input (BCs, TI, temperature): 1.1%
  - Experimental (per TN‑HW‑22): 1.5%
  - Reported total: 2.0% (RSS)
- Note: adding 0.8%, 1.1%, and 1.5% in RSS yields ~2.1%; modeling bias not included


# Slide 12 — Prior Use and Analyst Experience

- Template lineage: derived from inlet study INL‑S‑17 (accepted in 2024 for preliminary design)
- Similar geometry cases: 3 prior ducts with comparable curvature; typical PR error 0.5–1.5% vs tests
- Analyst: 8 years CFD, 3 on inlets; first project using GPU‑accelerated AMG on this cluster
- Peer review: two SMEs conducted desk check; comments resolved in Rev D; no independent rerun documented


# Slide 13 — Known Limitations and Open Items

- Low‑Re SST intent not met near inner‑bend corner (y+ > 10 locally on fine grid)
- Residual targets in plan (<1e‑6) not achieved on final fine run; monitors flat but minor oscillations remain
- Inlet turbulence intensity: test shows ~1%; CFD used 5% — sensitivity non‑negligible for swirl
- Validation overlays not corrected for temperature drift (295 K vs 300 K); effect on PR small but nonzero
- Case file labeling indicates SA in early templates; final settings reported as SST with cross‑diffusion — commit history shows “dirty” change
- GPU AMG uses single‑precision smoothers; double precision setting elsewhere — potential numerical noise
- Instrument calibration: 5‑hole probe cal expired 2 weeks before GT‑SD‑03; lab note states “within historical drift”


# Slide 14 — Recommendation and Decision

- Evidence for use:
  - Mean PR on fine grid close to test average in topline summary (0.973 vs 0.968); grid trend mild; sensitivities modest
  - Sector‑averaged swirl mostly within ±2 deg target except one sector; trends with backpressure plausible
- Concerns:
  - Conflicting turbulence model indications (SA labels vs SST claim)
  - Wall treatment not fully consistent with low‑Re intent in separated corner
  - Convergence and GCI reporting optimistic given limiter and residuals
  - Inlet TI mismatch with rig surveys; validation overlay temperature mismatch
  - Reproducibility off by ~0.9% in PR on different hardware; commit “dirty”
- Decision (by CFD Lead, 2026‑08‑06):
  - The model is accepted for estimating mean pressure recovery at design mass flow ±2% for PRELIM‑3 roll‑ups, subject to:
    - Re‑run fine mesh with inlet TI = 1–1.5% and corrected near‑wall spacing in inner‑bend patch (target y+ < 2)
    - Update validation overlay with density correction for 295 K and document final turbulence model setting in clean commit
  - The model is not approved for swirl acceptance metrics at sector level; use test data directly or rerun after addressing above items
