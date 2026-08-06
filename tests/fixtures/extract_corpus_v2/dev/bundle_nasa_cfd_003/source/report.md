# CFD Credibility Briefing — S‑Duct UAV Inlet (Rev B)

- Program: eVTOL demonstrator, engine intake S‑duct
- Analyst: Aero Systems CFD Team
- Tools: STAR‑CCM+ 2021.3 (primary), Pointwise V18.4 (meshing), Python 3.10 post
- Scope today: fidelity status for cruise and off‑design yaw/angle‑of‑attack; readiness for preliminary design gate

## Slide 1 — Purpose and Key Questions

- What we need from the model:
  - Predict inlet pressure recovery and swirl distortion at AIP
  - Map separation onset margin for AoA 0–12 deg, M = 0.25–0.5, ReD ≈ 2.7e6
- Decision tie‑ins:
  - Airframe–propulsor integration clearance
  - Fan operability guard bands (DC60/DC90)
- Target accuracy (program goal):
  - Recovery within ±2% absolute; distortion indices within ±10% of tunnel data

## Slide 2 — Geometry and Physics Choices

- CAD: Rev_31 S‑duct with 9% area contraction, 22° centerline bend; AIP plane 0.45 m from lip
- Surface finish: matte composite, nominal Ra 1.6 µm; not modeled explicitly (assumed hydraulically smooth)
- Flow model:
  - Baseline: steady RANS, SST k‑ω with low‑Re correction; compressibility on
  - Wall treatment: y+ near unity target; all walls no‑slip, adiabatic
- Note on alternative runs:
  - For high yaw (≥10°), we also trialed realizable k‑ε + enhanced wall treatment to mitigate solver jitter

## Slide 3 — Boundaries, Operating Envelope, and What We Actually Ran

- Stated envelope:
  - Inlet: total pressure 101.3 kPa, total temperature 293 K, turbulence intensity 2–4%, directional yaw 0–12°
  - Outlet: fixed mass flow 1.15–1.35 kg/s to span target ReD
  - Side plenum: pressure outlet at 0 gauge; farfield 5D upstream, 8D downstream
- Notes from case logs:
  - Early shakedown used velocity inlet with 5% turbulence to match hot‑wire rake; switched to total pressure inlet in production decks
  - For AoA 12–15° engineering screens (not in formal scope), we inverted the BC strategy (mass flow at inlet, static pressure at outlet) to maintain fan face Mach below 0.35

## Slide 4 — Solver Settings and Evidence of Code Behavior

- Discretization:
  - Nominal second‑order schemes for convection and pressure; coupled solver, pseudo‑transient with CFL ramp 1→30
- Code verification spot checks:
  - Manufactured solution (scalar advection) on structured box: observed order 1.98 (velocity), 1.91 (pressure)
  - Laminar lid‑driven cavity (Re=1000) benchmarks matched Ghia et al. centerline velocities within 0.8%
- Stability note from run sheets:
  - Final 400 iterations on several high‑yaw cases were converged using first‑order upwind after divergence events; residuals recovered two orders, monitors moved <0.5%

## Slide 5 — Mesh Topology and Convergence Behavior

- Grids:
  - Coarse: 2.1M poly‑hexcore, 15 prism layers, Δy+ ~ 1.2
  - Medium: 5.3M cells, Δy+ ~ 0.9
  - Fine: 8.7M cells, Δy+ ~ 0.7, minimum orthogonality 0.16, max skewness 0.85
- Refinement study (pressure recovery at AIP, M=0.35, AoA=0°):
  - Coarse→Medium: +1.1%; Medium→Fine: +0.3%; extrapolated “zero mesh” +0.2%
  - Reported GCI on recovery: 0.9% (nominally monotone), swirl RMS changed <0.5 deg
- Convergence metrics:
  - Residuals dropped 3–4 orders; mass imbalance <0.1%; area‑averaged recovery stable within 0.2% over 2k iters

## Slide 6 — Where the Grid Didn’t Behave Perfectly

- Local wall treatment:
  - y+ exceeded 6–8 in separated corner bubble for AoA ≥10° on Medium grid; not fully in viscous sublayer there
- Non‑monotone patch:
  - At M=0.5, AoA=8°, Fine grid predicted slightly lower recovery (−0.4%) than Medium; flow structures differ near inner wall corner
- Quick‑turn meshes:
  - Two AoA=12–15° screens used re‑meshed geometry after storage incident; those meshes show 3.7% lower recovery than archived Medium at same settings

## Slide 7 — Comparison to Test Data (Low‑Speed Tunnel)

- Data source:
  - 0.4‑m rig at AeroLabs (July–Aug 2025); PIV planes at x/D = −0.2, 0.0, +0.8; five‑hole probe rake at AIP; mass flow from calibrated venturi
- Alignment:
  - Geometry match within 0.3 mm; bleed and lip conditions matched; inlet turbulence 3.3% (measured)
- Headline agreement (campaign summary):
  - AIP pressure recovery within 2.4% absolute (mean of four points) for AoA=0–8°
  - DC60 within 7–10% of experiment; swirl angle patterns qualitatively similar (clockwise bias captured)

## Slide 8 — The Fine Print on the Validation

- Sensor notes:
  - Venturi recalibration discovered a 1.6% drift post‑campaign; mass flow corrected only for the last two AoA points
- Scatter:
  - At AoA=8°, M=0.5, CFD recovery is 3.8% higher than test; at AoA=0°, M=0.25, CFD is 1.1% low
- Model‑form influence:
  - Switching from SST to realizable k‑ε at AoA=10° reduces predicted DC60 by ~13% relative; tunnel DC60 drop is ~5%
- Conclusion in lab log:
  - “Within ±3%” cited in draft abstract assumes excluding AoA=8° high‑Mach point and averaging over M=0.25–0.35 only

## Slide 9 — Inputs, Assumptions, and Data Lineage

- Inflow turbulence:
  - We used 5% TI and 0.1 m integral length scale for production runs; tunnel rake shows 3.3% and 0.07 m
- Thermophysical properties:
  - Air via Sutherland’s law (μ0=1.716e−5 Pa·s at 273 K); density from ideal gas
- Geometry simplifications:
  - Omitted fastener heads and paint step at lip (0.2 mm nominal); fillets compressed to single radius 2 mm
- Roughness:
  - Not modeled; coupon measurements varied 1.4–3.1 µm; test article cleaned before runs

## Slide 10 — Uncertainty Treatment and Sensitivity

- Stated approach:
  - Global sensitivity with Sobol indices on five inputs (TI, inlet angle, mass flow, wall roughness, lip radius); uncertainty via Monte Carlo (500 draws) for output bands at AIP
- What we executed:
  - Due to HPC allocation limits, performed 32‑sample Latin hypercube; held wall roughness constant at “smooth”
  - Reported 95% intervals assume normality and pooled variance across AoA for each Mach
- Takeaways:
  - One‑at‑a‑time sweeps indicate mass flow dominates recovery variance; TI affects DC60 nonlinearly above 4%
  - Reported ±1.1% recovery band at M=0.35 reflects only inlet TI and mass flow variation

## Slide 11 — Repeatability, Versioning, and Traceability

- Process capture:
  - Meshes, case files, and scripts tracked in Git LFS; tags v0.7.3 through v0.8.1 correspond to the figures herein
  - STAR‑CCM+ journal files parameterize AoA, M, and TI; runs generated via CI pipeline on Cluster‑B (CentOS 8)
- Exceptions:
  - November 12 storage crash on Vault‑02 corrupted Fine grid for AoA=12°; mesh was rebuilt from the meshing recipe but surface curvature controls differ (Pointwise template v18.4.6 vs v18.4.5)
  - AIP probe mask for the July run is missing from the repository; mask was reconstructed from the test report JPEG

## Slide 12 — People, Reviews, and Tool Health

- Team qualifications:
  - Lead analyst: 12 years turbomachinery/inlet CFD; two co‑authors on SST transition correlations
  - New team member prepared the AoA=10–12° decks; onboarding complete but no prior S‑duct experience
- Reviews:
  - Peer check held 2025‑08‑22; two minor findings closed (AIP plane alignment, TI consistency)
- Toolchain status:
  - STAR‑CCM+ 2021.3 patch HF2 applied mid‑campaign for a memory leak; no regression found on baseline case
  - Note from night run logs: several high‑yaw cases were restarted by the new analyst with “first‑order” box checked to get past stalls; flagged for re‑run

## Slide 13 — Applicability and Out‑of‑Scope Use

- Intended use:
  - Design decisions for 0–12° AoA and M=0.25–0.5; steady flow assumption; clean configuration only (no ice, no crosswind gusts)
- Stretch cases executed:
  - AoA=15–18° single‑point screens at M=0.4 included in slide deck backups; used different BC pairing to bound stall
- Limitations:
  - No acoustic coupling to fan; no rotating stall model; no transition model (fully turbulent assumed)
  - Corner separation and secondary flow fidelity uncertain above AoA=10° given y+ excursions

## Slide 14 — Bottom Line and Open Actions

- Summary judgment:
  - For AoA up to 8°, the current deck trends with data and grid behavior is broadly acceptable for pre‑PDR trades
  - Above AoA=8°, credibility is mixed: turbulence model choice, local wall resolution, and BC swaps materially affect DC indices
- Open actions (near term):
  - Re‑run AoA=8–12° with consistent SST, second‑order only, and corrected TI=3.3% to firm up DC60/DC90
  - Recover exact Fine mesh settings post‑crash and re‑tag; document GCI at M=0.5 with uncertainty bars
  - Expand LHS to ≥128 samples or adopt polynomial chaos for two leading inputs; include roughness sweep
  - Close the test data reconciliation (venturi correction applied consistently; publish mask file)
- Go/no‑go suggestion:
  - Use current results for concept ranking at AoA ≤8°; require above actions before committing margins at higher AoA
