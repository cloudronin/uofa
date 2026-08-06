# Slide 1 — Project context and purpose
- Goal: use CFD to predict the Q–H curve and NPSH behavior of a single-stage, end-suction centrifugal pump (250 mm impeller) for water service at 25 C
- Decisions supported:
  - Select cutwater clearance and wear ring spec before tooling freeze
  - Confirm that head at 1750 rpm meets contract at BEP within 3%
  - Screen cavitation margin; flag if NPSHr at 3% head drop exceeds 4.0 m
- Risk framing:
  - Mis-prediction near shutoff could oversize motor; cavitation underprediction risks warranty returns
  - Validation data available from factory loop (three runs); schedule tight — results needed before week 38 build

# Slide 2 — Operating envelope and acceptance targets
- Simulated map: 0.3–1.3× design flow (Qdes = 0.135 m3/s) at 1750 rpm
- Outputs of interest:
  - Head, shaft torque, best efficiency point, volute tongue static pressure pulsation (rms)
  - NPSHr based on 3% head drop criterion
- Acceptance bands for CFD predictions vs test:
  - Head: ±3% at BEP, ±5% elsewhere
  - Torque: ±4% at BEP
  - NPSHr: ±0.5 m
  - Tongue pulsation: within 30% of probe rms at 0.9–1.1×Qdes
- Note: initial plan stated pressure rise agreement within 2% across the map; later revised after dry-run comparison to ±5% outside 0.8–1.1×Qdes

# Slide 3 — Geometry, clearances, and versions
- CAD source: Pump_250_RevC (impeller, shroud, volute). Nominal wear ring diametral clearance 0.35 mm; cutwater radius 8 mm
- Tip clearance:
  - Built into mesh as 0.28 mm radial gap at front shroud; rear shroud modeled as sealed (no balance holes)
- Small features:
  - Omitted fillet at tongue root (<1 mm) and seal grooves; included shroud chamfer
- Note on revisions:
  - Slide package earlier referenced RevD (with 0.25 mm wear ring); current simulations used RevC geometry exported 2026‑06‑15

# Slide 4 — Physics closures and frame handling
- Rotational modeling:
  - Primary approach: Moving Reference Frame (frozen rotor) for performance map; transient sliding-mesh for two points (0.8× and 1.0×Qdes) to check pulsation
- Turbulence and near-wall:
  - Turbulence: SST k–omega with low-Re correction; y+ target 1–2 on blade suction side
  - Near-wall: four-layer prism with first cell height 15 µm (water, Re ~ 1.2e6 at BEP)
- Cavitation:
  - Initially planned to run Zwart–Gerber–Belamri cavitation with fixed nuclei density; σ swept for NPSH curve
  - For production runs, cavitation model disabled due to convergence stalls; NPSHr inferred by extrapolating single-phase loss trend to 3% head drop
- Note: An alternative run set used realizable k–ε with enhanced wall treatment to speed convergence on coarser grids; those results are used in Slide 9 sensitivity summary

# Slide 5 — Meshing approach and grid checks
- Topology: poly-hexcore in volute; structured O-grid around blade passages; 9 prism layers at solids
- Cell counts:
  - Coarse: 7.4 M cells; Medium: 12.9 M; Fine: 25.6 M (MRF)
- Near-wall resolution:
  - Reported: y+ 0.6–2.3 on blades at BEP; hub/shroud 2–8; volute floor 10–18
  - Note: inspection at tongue shows local y+ peaking at 28 on medium grid at 1.2×Qdes
- Mesh refinement study:
  - Head at BEP: Coarse 57.6 m, Medium 58.4 m, Fine 58.7 m
  - Estimated Richardson extrapolated head 58.9 m; observed order ~1.9; GCI for Medium ~0.7%
- Production choice:
  - Most map points computed on Medium grid to meet schedule; two off-design points fell back to Coarse due to memory limit on SM runs

# Slide 6 — Numerics and solution monitoring
- Discretization:
  - Pressure–velocity coupling: coupled solver; second-order schemes for pressure and momentum; bounded second-order for turbulence
  - Transient SM runs: Δt = 1/350 rotor rev; 8 inner iterations per step; 8 blade passages → 3 rotor revs simulated
- Convergence criteria:
  - Residuals below 1e−4; monitor head changes <0.1% over last 300 iterations; torque oscillation <0.3% rms (MRF)
- Exception notes:
  - To stabilize near-shutoff, momentum scheme switched to first-order upwind for last 500 iterations; residual target relaxed to 5e−4
  - Early dry run described all production points as second-order throughout; final deck mixes first/second order at two points

# Slide 7 — Boundary conditions and operating points
- Inlet: total pressure and 5% turbulence intensity based on rig pitot tree upstream of suction bell; flow rate controlled by outlet static pressure ramp
- Outlet: static pressure specified to hit target flow within ±0.5%; backflow prevented by volute bleed
- Shaft: angular speed specified at 1750 rpm; rotor-stator interface is GGI with conservative flux transfer
- Thermal: isothermal at 298 K; density via incompressible water (ρ = 997 kg/m3); no buoyancy
- Clarifications:
  - Early plan called for mass-flow inlet to match test loop; actual deck uses pressure inlet because test upstream stabilization length unknown
  - NPSH study: initial spec stated cavitating inlet with varying total pressure; in practice, single-phase inlet adjusted and NPSHr inferred (Slide 4)

# Slide 8 — Software pedigree and quick code checks
- Solver: ANSYS Fluent 2024 R1, double precision, pressure-based solver
- Code behavior spot-checks:
  - Internal lid-driven cavity (Re=1000): grid doubling (64→128→256) shows ~1.95 order for centerline velocity peak
  - Straight pipe (k–ω SST, y+≈1): friction factor within 2% of Blasius correlation for Re = 1e5
- Documentation:
  - Vendor claims formal second-order accuracy for the chosen schemes; precision and parallel reduction reproducibility not independently audited
- QA notes:
  - Team QA checklist shows “peer review completed”; calendar indicates review moved to next sprint; comments from prior baseline not yet dispositioned

# Slide 9 — Mesh and model sensitivity highlights
- Grid effects:
  - Medium→Fine head shift at BEP: +0.5 m; torque +0.8%
  - Tongue rms pressure (SM, 1.0×Qdes): Medium 4.2 kPa vs Fine 4.5 kPa (7% gap)
- Turbulence model swap (MRF, Medium):
  - SST vs realizable k–ε at BEP: head differs by 1.9%; k–ε converges 30% faster; near-shutoff separation suppressed with k–ε, raising head by ~5%
- Surface roughness:
  - Baseline smooth walls; adding 60 µm equivalent sand roughness cuts head by 0.6 m at BEP
  - Note: BEP match to test improves when 60 µm roughness is used, though factory spec indicates Ra ~ 20 µm; roughness value effectively tuned
- Clearance sensitivity:
  - Tip gap +0.1 mm reduces head by 0.9 m; torque +1.3% at BEP
- Cavitation:
  - Single-phase σ-sweep proxy suggests NPSHr ~ 3.7 m; earlier plan with ZGB predicted 3.4 m in a pilot case before model was disabled

# Slide 10 — Comparison to factory loop measurements
- Test rig:
  - 300 mm suction bell with honeycomb straightener; calibrated magnetic flowmeter (±0.5% of reading), differential head cell (±0.25% FS), torque meter (±0.2% FS)
  - Water temperature 24–27 C; barometric pressure logged
- Data alignment:
  - Three repeats at 1746–1752 rpm; CFD at 1750 rpm used as nominal
- Agreement summary:
  - BEP (1.02×Qdes): CFD head 58.4 m (Medium, SST), test 58.1 m → +0.5%; torque +1.2%
  - 0.6×Qdes: CFD overpredicts head by 9–12% depending on mesh; tongue rms 35% lower than probe
  - 1.2×Qdes: Head within 4%; volute exit swirl angle underpredicted by ~6°
- Note: Early executive brief stated “within 2% across map”; detailed overlays show larger deviations at low flow; test rpm not exactly matched at those points

# Slide 11 — Variability and uncertainty treatment
- Input variation considered:
  - Flowmeter bias ±0.5%, head cell ±0.25% FS, rpm ±0.2%; water temperature ±1.5 C
  - Geometry: tip gap ±0.05 mm; wear ring clearance ±0.05 mm
- Propagation method:
  - Draft plan: Monte Carlo with 500 samples on a fast surrogate from six CFD support points
  - Executed: Latin hypercube with 30 samples due to compute budget; surrogate trained on four MRF points (coarse/medium) and one SM point
- Reported spreads:
  - Head 95% interval at BEP: ±1.2 m; NPSHr ±0.4 m (inferred single-phase method)
- Caveat:
  - Surrogate trained on mixed numerics (first/second order) and two turbulence models; consolidation pending

# Slide 12 — Traceability, independence, and open items
- Reproducibility:
  - All case setups, meshes, and post scripts in GitLab repo PUMP250_CFD (tag v1.7); mesh generated via GUI journal with environment export
  - Postprocessing for Slide 10 overlays partly done in Excel using copied CSVs; not fully scripted
- Independence and review:
  - Peer review scheduled for next sprint with rotating machinery SME; current review checklist only partially signed
- What’s left to improve confidence:
  - Re-run low-flow points with sliding mesh and consistent second-order schemes
  - Re-enable cavitation model for at least three σ points to avoid inference-based NPSHr
  - Close the loop on roughness and clearance measurements from as-built parts (RevD vs RevC discrepancy)
  - Complete a consistent mesh independence on the transient cases (target GCI < 2% for tongue rms)
- Bottom line:
  - Predictions near BEP appear decision-ready; low-flow behavior and NPSHr remain qualified with caveats noted above
