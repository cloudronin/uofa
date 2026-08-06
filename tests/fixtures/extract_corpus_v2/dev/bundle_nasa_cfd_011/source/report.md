# Slide 1 — CFD Status: S‑Duct Inlet Distortion for Compressor Face

- Objective: predict compressor‑face pressure recovery and distortion (DC60, swirl intensity) for the 1.2 m dia S‑duct on the XU-43 demonstrator
- Flow regime: M ≈ 0.25 at duct lip, ReD ≈ 5.1e6, sea‑level static conditions, modest inlet swirl from upstream fan bleed
- Decision need: support bleed‑slot sizing and operability screening before the A‑test taxi runs in October


# Slide 2 — What We’re Using the Model For

- Current plan
  - Provide distortion maps and recovery at three throttle points (85/100/115% design mass flow)
  - Screen two bleed schedules and two anti‑ice lip geometries; not intended to set red‑lines
- Note on use boundaries
  - Usable for concept trade selection and to flag gross separation risk
  - We are not certifying against surge limits off of this dataset
- Program note (from last week’s review)
  - Ops asked if these numbers can feed the initial flight clearance; we answered “only as advisory”
  - However, the draft TTO states “CFD‑based margins acceptable for taxi and high‑speed ground run” — needs reconciliation


# Slide 3 — Geometry and Physics Fidelity Choices

- Geometry capture
  - CAD trimmed to include boundary‑layer diverter, bleed ring (2% perimeter slot), anti‑ice lip (two variants)
  - Omitted: fasteners, paint step, and 0.8 mm panel gaps; fillets below 1.0 mm suppressed
  - Statement in kickoff deck said “full 360° geometry modeled”; actual setup uses 180° periodic sector for straight‑through case and full 360° for high‑swirl case
- Flow physics
  - Fully turbulent assumption; transition not modeled
  - Exception: two trial runs employed γ–Reθ to gauge sensitivity to early separation near the inner bend (no conclusive change observed)


# Slide 4 — Turbulence and Solver Setup

- Baseline closure: k‑ω SST with production limiter; steady RANS
- Off‑design near‑stall: SA‑neg attempted; one IDDES run over the inner‑bend separation bubble
  - The IDDES case showed intermittent reattachment and ±1.5% swing in DC60 over 0.1 s windows
- Numerics
  - Coupled density‑based solver, second‑order in space; pseudo‑transient stepping with CFL ramp 5→100
  - Wall treatment note 1: low‑Re resolution targeted (y+ ≈ 1–2) for lip and inner bend
  - Wall treatment note 2 (legacy meshes used in two parametric sweeps): scalable wall functions with y+ ≈ 35–50 were applied to reduce cost — keep in mind when comparing recovery between sweeps


# Slide 5 — Boundaries and Operating Points

- Inlet
  - Total pressure 101.3 kPa scaled to target mass flow; total temperature 300 K
  - Inflow turbulence: TI = 1%, length scale = 0.07D (fan honeycomb assumed effective)
  - For swirl‑on cases: imposed circumferential swirl profile up to 6° peak at 60° azimuth, m=1 mode
- Exit (compressor face)
  - Mass‑flow outlet with target ṁ: 62.5, 73.5, 81.0 kg/s
  - Static pressure monitors at rake plane R1, 0.2D upstream of exit plane
- Facility note from rig correlation slide (see Slide 8)
  - Inlet TI taken as 5% per hot‑wire data from AeroLab West Subsonic Inlet Rig
  - Swirl generator in the rig produced m=2 content not modeled in CFD; impact TBD


# Slide 6 — Meshes, Near‑Wall, and Independence

- Meshing strategy
  - Poly‑hexcore with prism layers (15 layers, growth 1.18); curvature/proximity on lip and bleed slot
  - Cell counts: 12M (coarse), 24M (baseline), 48M (refined)
- Near‑wall
  - Baseline RANS: y+ 0.8–1.6 on lip; 1.5–3.0 inner bend; 5–8 on outer bend shoulder
  - Note: two anti‑ice lip sweeps rerun on a cost‑reduced grid with y+ ≈ 40–60 (wall functions), cell count 9.6M
- Mesh sensitivity (steady RANS)
  - DC60 at 100% flow: 6.8% (12M), 6.5% (24M), 6.6% (48M) — non‑monotonic trend
  - Area‑averaged recovery: 0.982 (12M), 0.986 (24M), 0.985 (48M)
  - Claimed in last sprint note: “grid‑independent at <0.5% for recovery”; recompute gives ≈0.9–1.3% depending on norm


# Slide 7 — Solver Convergence and Numerical Checks

- Residuals and monitors
  - Continuity and turbulence residuals reduced >3 orders; momentum >4 orders on baseline cases
  - Key integrals plateau: mass imbalance <0.1%; recovery change <0.05% over 2k iterations
- Time stepping
  - Majority steady runs; one URANS/IDDES case used Δt = 1e‑4 s, 10 conv. sub‑iters, 0.3 s physical time
  - Early memo stated “time‑step independence verified (Δt: 1e‑4/5e‑5/2.5e‑5 s)”; logbook shows only two Δt levels were actually executed
- Discretization error estimate
  - GCI on recovery between 12/24/48M meshes reported as 0.8% (SST); recalculated with observed order 1.9 yields ≈1.7%
  - For DC60, oscillatory trend implies using envelope; we quote 0.4% absolute (but see Slide 6 non‑monotonicity)


# Slide 8 — Comparison to Rig Data (AeroLab West)

- Test article: matched geometry with removable bleed ring; 36‑port Kiel rake at R1; 16 static taps; 5‑hole probe for swirl
- Conditions
  - Facility log: ReD = 4.7e6 (±3%), M = 0.23; inlet TI measured 4.5–5.2% without honeycomb
  - Our CFD cases generally set TI = 1% at inlet (Slide 5) except two “rig‑match” runs at 5%
- Metrics at 100% flow (baseline lip, bleed off)
  - Recovery: CFD 0.986 vs. test 0.979 (Δ = +0.7%); alternate note in draft V&V sheet lists test recovery as 0.982 — need to align data source
  - DC60: CFD 6.5% vs. test 7.1% (Δ = –0.6% absolute)
  - Swirl intensity (rms at 0.8R): CFD 3.2° vs. test 4.0°; m‑mode content differs (rig had m=2 energy)
- Scaling
  - We stated “Re matched within 2%”; per test sheet B, mismatch is closer to 8% at 85% flow due to fan map shift


# Slide 9 — Sensitivities and What Drives the Outputs

- Parameter variations (one‑at‑a‑time on 24M grid, SST)
  - Inlet TI 1→5%: recovery –0.3%; DC60 +0.5%
  - Bleed mass fraction 0→1%: recovery +0.4%; DC60 –1.1%
  - Lip variant A→B: recovery –0.2%; DC60 +0.3% (on low‑cost mesh with wall functions)
- Combined effects
  - A short Latin hypercube (N=24) was planned; instead we executed a 2‑level fractional factorial (k=3) due to queue limits
  - Draft sensitivity report references a kriging surrogate; that fit used the five DOE points and two legacy cases — not robust for extrapolation
- Turbulence model spread
  - SST vs SA‑neg at 85% flow: Δrecovery = –0.4%; ΔDC60 = +0.7%
  - IDDES (coarse 12M+DES) at 100% flow: recovery 0.983; DC60 7.0%


# Slide 10 — Data Handling, Tools, and Repeatability

- Software and hardware
  - Primary solver: Ansys Fluent 2023R1; meshing in Pointwise 18.5; post in Tecplot 360 EX 2022 R2
  - Cluster: JPL‑Ceres (Skylake nodes), 256 cores per case typical; 21–36 h walltime for 24M steady RANS
  - Two early scoping runs were done in OpenFOAM v10 on a local workstation; settings close but not bitwise comparable
- Workflow controls
  - Case templates and journals under GitLab repo “sduct‑cfdbeta,” tag v0.7; meshes stored on PFS with md5 checksums
  - Exception: anti‑ice lip sweep on the wall‑function mesh was generated outside the repo by an intern script; no tag, settings pasted into slide notes
- Analyst experience
  - Lead: 8 years CFD; second analyst: 2 years, new to bleed modeling; paired reviews conducted each Friday


# Slide 11 — Uncertainty and How to Use the Numbers

- Components considered
  - Numerical (grid + iterative): ±1.7% on recovery, ±0.4% abs on DC60 (envelope)
  - Input BCs: TI ±2% absolute and swirl ±1° yield ±0.5% on DC60
  - Model form (turbulence): take spread SST vs SA‑neg vs IDDES as bias, ~0.7% DC60, 0.4% recovery
- Aggregation
  - We initially reported an overall 1.1% recovery uncertainty (RSS of numerical + BC only)
  - In the draft tech note, a 3.5% total recovery uncertainty is quoted, citing “dominant turbulence closure” — this includes model‑form as expanded uncertainty; choose convention before release
- Usage guidance
  - Treat DC60 within ±0.8% absolute and recovery within ±0.6% as indistinguishable across the two lip variants under current evidence
  - Do not infer surge margin; unsteady content in IDDES suggests potential broadband fluctuations that steady RANS cannot capture


# Slide 12 — Gaps, Risks, and Next Steps

- Gaps to close before A‑test
  - Align inlet TI and swirl content with rig (add m=2 mode); repeat baseline at 24M grid
  - Reconcile recovery numbers (0.979 vs 0.982 test reference) and ensure same rake calibration assumed
  - Re‑run anti‑ice lip variants on y+≈1 mesh to remove wall‑function inconsistency
- Deferred items
  - Surface roughness and insect accretion not included; transition model only probed, not adopted
  - Bleed ring discharge coefficient measured at 0.86±0.04 in bench test — currently assumed ideal in CFD
- Commitments
  - Deliver updated distortion maps and uncertainty bounds by Sept 9
  - Freeze solver version (Fluent 2023R1) in repo tag v0.8; migrate all journals from ad‑hoc runs


# Backup — Prior Use on Similar Ducts

- Last year’s S‑duct (XD‑17) at M=0.3 showed strong correlation: recovery error within 1% and DC60 within 0.5% across three flow points
- Separate internal read‑across memo notes “2–3% recovery bias and 5–7% DC60 under‑prediction” for XD‑17 due to excessive smoothing of inner‑bend scallop
- Conclusion
  - We likely need to revisit geometry clean‑up and BCs to match the rig topology before leaning on prior performance claims
