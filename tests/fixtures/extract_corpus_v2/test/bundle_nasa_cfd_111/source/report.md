# CFD Credibility Briefing — Centrifugal Pump Stage (Head–Capacity Curve)

- Context
  - Purpose: predict head rise and efficiency for a 7-blade radial pump with 12-vane diffuser and single-volute at 3600 rpm, water at 25 C
  - Operating map: 70%–120% of best efficiency point (BEP), target Q_BEP ≈ 0.112 m³/s, expected H_BEP ≈ 32 m, η_BEP ≈ 78%
  - Deliverable: pre-test performance prediction to guide impeller trim and diffuser cutback decisions

- What physics we tried to capture
  - Rotating machinery with mixed blade loading (LE incidence at off-design), secondary flows in the diffuser, and volute tongue interaction
  - Single-phase, isothermal, incompressible water; cavitation and two-phase effects deferred to a later phase
  - Turbulence handled with two-equation eddy-viscosity approach; transition not modeled explicitly
  - Tip leakage and mechanical seal leakage paths neglected to simplify scope, although runner–casing gap exists in the hardware nominally at 0.20 mm

- Toolchain and solver settings
  - Meshing: Pointwise 18.4 R3 for blade passages; trimmed hexa-prism in volute; periodic sectors assembled in STAR-CCM+
  - Solver: STAR-CCM+ (coarse grid: 2022.1; fine grid: 2023.2), pressure-based segregated, steady MRF for rotating region
  - Turbulence model: k-omega SST; curvature correction off; production limiter on
  - Linear solvers: algebraic multigrid for pressure; second-order upwind for momentum and turbulence variables

- Geometry and boundary conditions
  - Geometry: full wheel + diffuser + volute modeled; fillets included at blade LE/TE; hub-shroud fillets simplified
  - Inlet: total pressure = 101.3 kPa, T = 298 K, turbulence intensity 5%, length scale 3 mm (from upstream straightening section)
  - Outlet: static pressure ramped to hit target flow; verified with alternate mass-flow outlet for three set points
  - Rotational speed: 3600 rpm nominal; sensitivity run at 3450 rpm (vendor test speed) referenced but not used in main curve fit

- Near-wall treatment and mesh notes
  - Targeted y+ < 1 on blades for low-Re SST; first cell height 6 µm in passages; 22 prism layers, growth 1.15, total BL thickness ~0.8 mm
  - Achieved y+ at BEP: 35–80 on suction sides, 10–25 on pressure sides; solver auto-switched to scalable wall functions where y+ > 30
  - Volute walls: y+ 120–250; prism layers reduced to 10 due to cell count limits
  - Mesh counts (passage + diffuser + volute):
    - Coarse: 1.2M cells, Medium: 3.1M, Fine: 7.8M
    - Note: a separate mesh sweep logged as 1.2M / 2.4M / 3.0M for quick-look at BEP only

- Iterative behavior and stopping rules
  - Residuals dropped to 1e-4 for momentum and turbulence; continuity stabilized at ~2e-3 on fine grid
  - Monitors: head rise and torque varied less than 0.5% over the final 800 iterations
  - However, head still exhibited a slow drift of ~3% over extended runs at 120% of BEP; we stopped at 4000 iters per point to maintain schedule

- Mesh and solution independence checks
  - Three-grid refinement at BEP:
    - Head predictions: H_coarse = 31.1 m, H_med = 31.9 m, H_fine = 32.4 m
    - Apparent order p ≈ 1.7; estimated fine-grid uncertainty ≈ 0.6% (Richardson extrapolation)
  - At 80% of BEP, the separate sweep (1.2M/2.4M/3.0M) indicated a much larger spread: 7.5% between coarse and “fine”
  - A second pass GCI using the 3.1M/7.8M pair gave ~2.6% for head at BEP when assuming p = 2.0; this was accepted for the summary plot

- Unsteady effects and rotating–stator interaction
  - One transient sliding-mesh case at BEP (time step = 1.2e-4 s, 60 inner its, 3 blade-pass periods) showed periodic head oscillation of 8–12% peak-to-peak at the volute gauge location
  - Despite the above, the steady MRF approach was retained for the performance map based on cycle-averaged head within 1.5% of the transient mean
  - CFL during transient reached 12 in the tongue region; a smaller time step was flagged as desirable but not executed this sprint

- Input data pedigree and operating envelope
  - Fluid properties taken from CRC at 25 C: ρ = 997 kg/m³, μ = 0.89 mPa·s; no temperature rise modeled (pump heat rise < 4 C per vendor)
  - Test rig conditions provided: 3000 rpm acceptance test, same impeller/diffuser, water at 27–29 C; suction pressure sufficiently high to avoid cavitation
  - Although cavitation is deferred, a back-of-envelope NPSHr estimate (Bernoulli + σ_thres) was annotated on the H–Q plot as “advisory only”

- Comparison with available measurements
  - Vendor curve (3000 rpm) scaled to 3600 rpm via affinity laws for preliminary check; predicted H_BEP within +3% of scaled target; η_BEP underpredicted by ~4 percentage points
  - For three points tested at 3000 rpm, direct comparison (without affinity scaling) shows head discrepancies of 8–10% and flow mismatch up to 6% due to dissimilar outlet controls (mass-flow vs pressure)
  - Diffuser static pressure taps trend matches shape, but magnitude offset ~5 kPa at 90% of BEP; geometry in test includes 0.20 mm tip clearance and 0.5 mm shroud bow not in model

- Assumptions and their implications
  - Steady-state assumed adequate for map generation despite observed blade-passing content in the tongue; justification based on averaged values
  - Wall roughness set to hydraulically smooth in CFD; test hardware roughness Ra ≈ 1.6 µm noted but not applied
  - Ignored tip leakage path and seal leakage; yet conclusions about part-load recirculation mention leakage-driven secondary structures qualitatively

- Sensitivity and uncertainty sketch
  - One-at-a-time sweeps at BEP:
    - Inlet turbulence intensity 1–10%: head changed < 0.7%
    - Rotational speed ±1%: head changed ±2.0% (consistent with affinity)
    - Diffuser–volute mesh growth 1.15→1.25: head decreased 1.3%
  - Claimed overall predictive spread “about 2%” for head at BEP; does not include model-form bias from turbulence or missing tip clearance
  - No formal global sensitivity or input distribution propagation performed; schedule limited

- Software control and reproducibility
  - Case dictionaries and meshes tracked in Git (repo pump-cfd, tag v0.3-preCDR); run scripts archived
  - Solver version inconsistency: coarse/medium grids run with STAR-CCM+ 2022.1; fine grid and transient with 2023.2; SST default options differ between releases
  - A peer check found the initial run had impeller rotation direction reversed; corrected before the mesh sweep; note remains in the logbook
  - Post-processing performed in Tecplot 360 2022 R1 and ParaView 5.10; one figure regenerated with Fluent’s report file for a separate study (label not updated)

- Readiness assessment (informal)
  - Geometric representation: acceptable for concept trade, but missing tip/seal gaps and measured shroud bow reduce fidelity near surge
  - Numerics: mesh sufficiency mixed; blade passages acceptable, volute wall resolution marginal; steady solver adequate for averaged map, less so for local metrics at tongue
  - Physics models: RANS SST reasonable baseline; lack of transition and leakage modeling likely sources of bias at off-design
  - Benchmarks: comparison to scaled vendor curve encouraging at BEP; direct point-by-point comparisons uneven due to test condition mismatch
  - Data/traces: most inputs and setups documented; solver version drift and alternate outlet BCs reduce repeatability

- What we will change before CDR
  - Add tip clearance and nominal leakage representation; incorporate measured roughness
  - Extend time-accurate runs at BEP and 80% BEP with reduced time step (target CFL < 2 in tongue) to quantify unsteadiness influence on mean head
  - Reconcile mesh study into a single, consistent triplet (e.g., 2M/4M/8M) and repeat GCI for head and torque; document near-wall y+ across blades and volute
  - Align validation: rerun at 3000 rpm with mass-flow outlet to match test rig; include diffuser tap comparisons and uncertainty bars
  - Lock solver version (2023.2) and freeze model options; update repository tag v0.4 with run manifests and hashes

- Backup slides (selected numbers)
  - Head rise summary at 3600 rpm (steady MRF, fine grid):
    - 80% BEP: 34.7 m; 100% BEP: 32.4 m; 120% BEP: 28.9 m
  - Efficiency (excluding mechanical losses): peak 74% at 0.108 m³/s; note vendor hardware reported 78% including test corrections
  - y+ histograms:
    - Blade suction sides: median 42, 95th percentile 78
    - Volute: median 180
  - Unsteady head oscillation at BEP: 11.2% p–p at tongue probe; mean within 1.3% of steady result

- Key caveats called out during review
  - Two different mesh triplets cited in notes lead to inconsistent GCI values (0.6% vs 2.6%)
  - Steady-state assumption conflicts with observed blade-passing content; justification based on averages may not hold at off-design
  - Boundary condition strategy alternated between pressure outlet and mass-flow outlet across runs; impacts direct comparison to rig data
  - “No cavitation modeled” stated, yet an advisory NPSHr line appears on H–Q plot, which may be misconstrued as predictive
  - Solver version change between grids; SST defaults not harmonized; could affect turbulence production near separation

- Ask from stakeholders
  - Accept current map for preliminary design trending with ±5% guardband at BEP and ±10% at off-design
  - Fund the transient + clearance update and aligned 3000 rpm validation runs before committing to detailed casing modifications
  - Provide test data with documented inlet turbulence, roughness, and leakage estimates to reduce model–test mismatch
