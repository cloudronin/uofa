# Slide 1 — CHT model overview: avionics power card cooling

- Purpose: predict worst-case device junction temperatures for a 10‑device MOSFET array on an aluminum heat spreader with finned extrusion, forced air through an avionics bay plenum
- Decision supported: select heat sink variant and blower setpoint to keep Tj below 115 C at 30 C inlet air
- Tools and build:
  - Geometry from CAD (NX export), defeatured small fillets <0.3 mm
  - CFD/CHT in Ansys Fluent 2023 R2, steady RANS, segregated pressure-based solver
  - Conduction in copper planes, FR‑4 board, aluminum spreader and fin pack; convection in air
- Primary outputs: device junction temperatures, fin pack surface temperatures, board hot spot map, thermal margin to limit


# Slide 2 — Operating scenario and acceptance bar

- Inlet: 2.1 m/s uniform velocity at 30 C, turbulence intensity 5%
- Outlet: static pressure = 0 Pa at bay exit, zero backflow temperature
- Power map: 10 devices at 7.5 W each (75 W total) with 2.5 W distributed in nearby passives; heat partitioned via JEDEC θjc fractions
- Target: 115 C maximum junction temperature under steady bay flow; 30‑minute soak assumed
- Why it matters: device derating curve breaks sharply above 120 C; exceeding 115 C leaves insufficient margin for altitude effects and component variability
- Risk posture: medium — an optimistic prediction could lead to selecting an undersized fan, causing thermal throttling during climb


# Slide 3 — Physics and key simplifications

- Flow: incompressible air, density via Boussinesq for buoyancy; k‑ω SST turbulence with low‑Re near-wall treatment
- Heat transfer:
  - Solid conduction solved concurrently (conjugate), copper treated isotropic at 385 W/mK (no fiber weave anisotropy)
  - Thermal interface material (TIM): 150 µm thickness, conductivity nominal 4 W/mK; contact resistance folded into TIM property
  - Radiation neglected inside bay; quick check with gray‑diffuse DO (ε=0.9) changed worst Tj by −0.6 C; not pursued further this phase
- Geometric edits: screw threads, chamfers <0.5 mm, and via barrels removed; total removed volume <0.8%
- Out of scope for this milestone: dust fouling, fan curve drift, and TIM pump‑out over life


# Slide 4 — Boundary and material data pedigree

- Air properties: Fluent built‑in at 1 atm; viscosity Sutherland; cross-check against NIST within 1%
- Heat loads: from SPICE dissipation under steady-load profile; lab power analyzer cross-check within ±3%
- TIM data: vendor datasheet (Laird Tflex HD series) nominal 4 W/mK; no in-house compression curve yet (planned M02)
- Surface roughness: fins 1.6 µm Ra; board copper planes assumed smooth for conduction
- Contact pressure at TIM estimated 200–250 kPa from screw preload calc; no pressure mapping used
- Sensitivity to these inputs explored — see Slide 9


# Slide 5 — Numerics and solver controls

- Discretization: second-order upwind for momentum/energy, second-order for turbulence; coupled energy-solid with full coupling every iteration
- Convergence:
  - Residuals <1e−5 for all equations
  - Global heat balance closure within 0.8% (solid source vs. convective removal at outlet)
  - Area-averaged fin base temperature plateaued to <0.05 C change over last 500 iterations
- Wall modeling: inflation layers (15 layers, growth 1.2) targeting y+ ≈ 1–2 on fins and board; smooth transition to core grid
- Under-relaxation default, with momentum 0.5 for stability around fin leading edges; pseudo-transient with 0.01 s time step to assist convergence (no physical transient results reported)


# Slide 6 — Grid strategy and temperature sensitivity to cell count

- Meshes generated in Fluent Meshing; poly-hexcore with boundary prisms
  - Coarse: 1.1M cells, base size 2.2 mm, min prism thickness 0.02 mm
  - Medium: 2.4M cells, base size 1.4 mm
  - Fine: 5.3M cells, base size 1.0 mm
- Quality: max skewness <0.86; non-orthogonality <68 deg
- y+ statistics on fins (medium mesh): mean 1.4, 95th percentile 2.3
- Junction temperature of hottest device:
  - Coarse 111.8 C, Medium 109.6 C, Fine 108.9 C
  - Extrapolated (Richardson) 108.5 C with estimated grid-induced uncertainty ±0.7 C (k=2)
- Decision: medium mesh used for parametric runs; fine mesh used to spot-check two cases; temperature deltas within 0.8 C


# Slide 7 — Bench setup and measurements used for comparison

- Test article: same board + heat sink assembly in a ducted rig; ambient 30±0.4 C controlled
- Airflow: vane anemometer upstream, 2.1±0.05 m/s; honeycomb straightener ahead of inlet
- Instrumentation:
  - 8 thermocouples (Type‑K, 36 AWG) bonded to fin base; calibration ±0.6 C (NIST traceable)
  - IR camera (FLIR A655), lens 25°; emissivity taped patches; absolute accuracy ±2 C; used for qualitative surface fields
  - Junction temperature inferred via device internal diode method on two devices; accuracy per vendor ±1.5 C
- TIM: new pads installed for each test; nominal 4 W/mK; 0.15 mm thickness feeler-verified
- Soak: 35 minutes per condition; last 5 minutes averaged for reported values


# Slide 8 — Model-to-lab comparison and residuals

- Matching conditions: inlet speed, ambient temperature, and power per device aligned within measurement tolerances
- Hottest junction:
  - Model (fine grid): 108.9 C
  - Lab (diode method): 111.5 C ±1.5 C
  - Delta: −2.6 C (model colder), within expanded combined uncertainty (~±2.9 C)
- Fin base thermocouples:
  - Mean absolute deviation model vs. TC: 1.1 C
  - Max local difference: 2.4 C near leading edge of center fin
- Flow visualization: smoke probe indicates recirculation bubble length close to CFD streaklines; no separation-induced surprises
- Conclusion for this use case: agreement acceptable; bias toward optimistic by ~2 C noted


# Slide 9 — Input variability and what drives temperature swing

- Approach: Latin Hypercube (200 trials on medium mesh) varying:
  - Inlet speed: normal, μ=2.1 m/s, σ=0.3 m/s (±~15%)
  - TIM conductivity: uniform 2–6 W/mK
  - Device power: normal, μ=7.5 W, σ=0.375 W (±5%)
  - Contact conductance multiplier: lognormal with median 1.0, GSD 1.2
- Outcome metric: peak junction temperature
  - Mean 110.4 C; 95th percentile 114.2 C; 99th percentile 116.1 C
- Sensitivity (Sobol total indices from surrogate fit):
  - Inlet speed: 0.48
  - TIM conductivity: 0.31
  - Device power: 0.17
  - Contact conductance multiplier: 0.09
- Implication: holding airflow within ±5% stabilizes Tj below 115 C for most realizations even with mediocre TIM lots


# Slide 10 — Applicability limits and extrapolation cautions

- Validated range: 1.8–2.4 m/s inlet speeds at 30 C; new analyses required for different bay temperatures or blocked flow
- Radiation neglected is acceptable for ΔT<90 C and enclosed geometry; above that, expect additional 1–2 C relief
- Board internal copper assumed isotropic; for heavy weave stackups or anisotropic laminates, lateral spreading may change by ~0.5–1 C
- Not addressed yet: flow maldistribution from upstream harnesses, altitude air property changes, and aging of TIM under vibration
- Extrapolating to 55 C inlet (DO‑160 ground hot) is not recommended without rerun; rough estimate adds +25 C to all numbers


# Slide 11 — Reproducibility and configuration tracking

- Model artifacts:
  - Journal files and meshing scripts committed to repo: thermal-avx-card.git at commit 7f3c2a9
  - Solver: Fluent 2023 R2 (build 23.2.91), double precision
  - Mesh files: coarse/med/fine under /meshes/ dated 2026‑06‑28
- Environment:
  - Cluster nodes: 2x Intel Xeon Gold 6248R; 192 GB RAM; RHEL 8.8
  - Runs performed with 24 cores; medium mesh walltime ~1.6 h; fine mesh ~4.7 h
- Postprocessing: Python 3.10 with PyFluent API v0.15; figures auto‑generated from journal
- Replayability status: end‑to‑end runbook in README passes on clean checkout; two users reproduced within ±0.2 C for reference case


# Slide 12 — Gaps, decisions, and next steps

- Decision for this gate: proceed with heat sink Variant B and blower setpoint delivering ≥2.1 m/s; predicted worst‑case Tj margin to 115 C ≈ 0.8–2.1 C depending on assumptions
- Known gaps (deferred):
  - No formal manufactured‑solution test of the solver this project; relying on vendor documentation and internal sanity checks
  - Radiation only spot‑checked; full participating media not relevant, but enclosure view factors could be added
  - No independent peer review conducted yet; targeted before CDR
  - TIM property vs. compression not characterized in‑house; lab fixtures being assembled (M02)
  - Operating envelope beyond 30 C inlet and 1.8–2.4 m/s not covered in test; extended matrix planned
- Planned actions:
  - Re‑run CHT at 55 C inlet and 0.8/3.0 m/s to bracket DO‑160 extremes
  - Measure contact resistance using pressure‑controlled rig; update distributions
  - Add radiation model with gray surfaces for sensitivity quantification
  - Conduct additional fine‑mesh confirmation for the low‑flow corner case
