# RF Ablation Catheter Tip CHT Model — Credibility Slide Pack (vv40-oriented)

## 1. What this model is for
- Goal: predict peak tissue temperature and lesion dimensions for a 7F open‑irrigated RF ablation catheter in left‑atrial blood flow
- Decisions this will inform:
  - Draft power/irrigation tables for labeling (35–50 W, 8–30 mL/min) and pullback timing
  - Screening of new tip hole patterns prior to in‑vivo
- Risk posture:
  - Slides 3 and 12 argue the output could be used for labeling limits (moderate–high consequence)
  - Kickoff memo (M-CHT-017) states “exploratory concept down‑select; not for clinical claims” — not yet reconciled

## 2. Physics and scope at a glance
- 3D conjugate heat transfer:
  - Fluid: saline jets through 6 radial ports mix with atrial blood; flow around 3.5 mm platinum–iridium tip
  - Solid: tip and shaft conduction; myocardium anisotropic conduction; tissue perfusion sink (Pennes)
  - RF heating: volumetric Joule heating in tissue from 500 kHz source; catheter electrode resistive heating included
- Interaction specifics:
  - Strong two‑way coupling of fluid convection and solid/tissue conduction; temperature‑dependent electrical conductivity in tissue
- Flow regime assumption:
  - Model setup notes: laminar with low‑Re transition (Re_tip ≈ 950)
  - Solver deck v22c enables k‑ω SST with y+ target 1.0 for near‑wall treatment — inconsistent with “laminar” note
- Contact conditions:
  - Nominal 20 g force, 15° tip tilt; dry tissue contact (no vapor cap model)

## 3. Geometry, materials, and operating conditions
- CAD: native NX model of 3.5 mm hemispherical tip with 6× 0.5 mm ports; 0.1 mm edge fillets retained
- Tissue block: 25×25×20 mm porcine myocardium slab; anisotropy ratio 2:1 (fiber:cross‑fiber)
- Blood: 37 °C, μ = 3.5 cP; bulk flow 0.2–0.5 m/s across tip (parabolic inlet)
- Saline: 0.9% NaCl at 22–37 °C; 8–30 mL/min
- Key thermal/electrical properties (nominal):
  - Tissue k = 0.56 W/m‑K (±25%), ρc_p = 3.6 MJ/m³‑K; σ_elec(T) = 0.28 + 0.015(T−37 °C) S/m
  - Tip k = 71 W/m‑K; epoxy shaft k = 0.22 W/m‑K
  - Perfusion ωρc_p = 8–18 kW/m³‑K (two distinct values used across runs; see Slide 8)

## 4. Numerics, solvers, and plumbing
- Tools: Ansys Fluent 2024 R1 (pressure‑based, transient, coupled energy), in‑house tissue EM heater (EMHeat v1.3), co‑simulation via MpCCI 2022.3
- Discretization: second‑order in space; bounded second‑order implicit in time
- Coupling strategy: staggered; 5 inner iterations per 0.01 s step; under‑relaxation 0.6 (T), 0.4 (u,v,w)
- Hardware: most runs on 32‑core AMD nodes (128 GB) with Intel MPI; however, v22c time‑step halving test was executed on a developer laptop due to queue constraints
- Software hygiene:
  - Git repo CHT-RF-Model; tags v22a–v22d; Jira tickets for changes
  - Two mesh files (Grid-3b, Grid-4) were edited locally and not committed; provenance partially reconstructed

## 5. Code checks and numerical soundness
- Implementation checks:
  - Unit tests for EMHeat heater source on canonical 1D slab: energy conservation within 0.2%
  - Analytic manufactured case for steady conduction (no perfusion) executed in tissue solver: L2 error < 0.5% at 4× refinement
- Coupling layer:
  - Slide 2 of the internal verification note claims MMS “not feasible for co‑simulation”; reliance on vendor’s regression suite for Fluent/MpCCI
- RF power deposition:
  - Electric field solution is not explicitly solved in Fluent; imported as a pretabulated volumetric heat source vs. contact geometry from COMSOL v6.1 — interpolation routine spot‑checked at 10 points

## 6. Discretization and run‑time controls
- Grids: unstructured poly‑hexcore; prism layers at tip and tissue interface
  - G1: 1.2 M cells (y+ ≈ 12 at tip, first layer 0.04 mm)
  - G2: 2.4 M (y+ ≈ 6, first layer 0.02 mm)
  - G3: 5.1 M (y+ ≈ 1.5, first layer 0.005 mm)
  - G4: 9.8 M (y+ ≈ 0.7, first layer 0.0025 mm)
- Time step: Δt = 0.01 s nominal; one check at 0.005 s
- Reported summary:
  - “Grid‑insensitive within 2% for peak tissue T and <0.2 mm for lesion depth (G3 vs G4)”
- What the numbers show (20 g, 40 W, 17 mL/min, 60 s):
  - Peak T: 84.1 °C (G3) vs 88.7 °C (G4) [+5.5%]
  - Depth to 50 °C isotherm: 3.42 mm (G3) vs 3.71 mm (G4) [+8.5%]
  - Δt halved (G3): peak T +6.2%; lesion depth +0.3 mm
- We computed a GCI using the three finest meshes assuming observed order p ≈ 1.7; estimates suggest 6–10% uncertainty in peak T — not reflected in Slide 10 acceptance claims

## 7. Inputs: how they were chosen and how shaky they are
- Direct measurements:
  - Irrigation flow: calibrated Coriolis meter (±1% of reading)
  - Contact force: Ensite CF mock controller (±2 g), n=12 placements
  - Blood bulk velocity: rotameter estimated; back‑calculated from pressure drop; ±20% likely
- Literature/assumptions:
  - Tissue perfusion: 8 kW/m³‑K taken from Wissner (acute atrial), 18 kW/m³‑K from Choi (chronic porcine); both used in different “nominal” runs inadvertently
  - Tissue thermal conductivity temperature‑dependent vs. constant 0.56 W/m‑K: two decks differ (v22b constant; v22d linear with 0.0015 W/m‑K/°C slope)
- Contact mechanics:
  - Real contact area estimated via Hertzian normal pressure with epoxy compliance; no slip heating
- Saline temperature:
  - Assumed 25 °C in early runs (label on bag); thermistor log shows 32–34 °C at luer lock in later tests

## 8. Bench comparison setup (for reality checks)
- Flow loop: 5 L reservoir, 37±0.3 °C via PID; heparinized porcine myocardium slabs clamped; superfused with 0.2–0.5 m/s flow via 12×50 mm channel
- Instrumentation:
  - 6× 36‑gauge thermocouples at depths 1, 2, 3 mm under tip centerline; ±0.2 °C calibrated in water bath
  - Thermal camera for surface, 640×480, emissivity 0.96 (epoxy)
- Protocol:
  - 40 W for 60 s, force 20 g, irrigation 17 mL/min; repeat n=6
- Alignment:
  - Time zero based on power‑on; model and bench synchronized within 0.2 s
- Note: tip tilt was ~10–15° in bench; model uses 15°

## 9. How well the numbers line up with the bench
- Claimed headline in draft summary: “within 5% for lesion depth and 2 °C for peak surface T”
- Actual overlays (run set R‑40‑17‑20, v22d vs. bench mean ±1σ):
  - 50 °C depth at 60 s: model 3.71 mm; bench 3.25±0.18 mm [model high by 14%]
  - Surface Tmax under tip: model 72.5 °C; bench 64.1±1.9 °C [+8.4 °C]
  - Thermocouple at 2 mm: RMSE 3.7 °C over 0–60 s
- Acceptance bar movement:
  - Early protocol: ±10% for lesion metrics, ±3 °C pointwise
  - Later slides cite ±5% / ±2 °C without revision to results — mismatch not addressed
- Calibration:
  - No parameter tuning performed other than setting saline inlet temperature to match log
  - Droplet evaporation and vapor cap not modeled; outliers with audible pops in bench runs excluded (n=1)

## 10. Sensitivity sweeps and uncertainty roll‑up
- Screening:
  - One‑at‑a‑time sweeps on 7 inputs: blood speed, saline rate, perfusion, tissue k(T), contact force, saline T, heater placement
  - Peak tissue T most responsive to blood speed (−0.22 °C per +0.01 m/s) and contact force (+0.35 °C per +1 g)
- Global treatment:
  - Latin hypercube, 200 samples (stated originally as 1000, reduced due to walltime); Δt = 0.01 s, Grid G2
  - Outputs: peak T, 50/60/70 °C isotherm depths at 60 s
  - 95% intervals (R‑40‑17‑20): peak T 78.4–92.1 °C; 50 °C depth 3.05–3.98 mm
- Variance drivers (standardized regression):
  - Contact force (β ≈ +0.46), blood speed (β ≈ −0.41), perfusion (β ≈ −0.18)
  - Tissue k(T) flag had small effect on coarse grid; on G3 its effect roughly doubles — interaction with discretization unresolved
- Not propagated:
  - Numerical uncertainty from mesh/time step not folded into intervals
  - RF heater source interpolation uncertainty not sampled

## 11. Transfer from bench slab to the actual heart
- Where the setup matches:
  - Temperature range, irrigation/power window; oblique flow across tip
- Where it doesn’t:
  - In vivo wall motion, trabeculation, variable contact patch, blood hematocrit
  - Saline injection mixing patterns near pulmonary vein ostia differ from straight channel used
- Statement drift:
  - Slide 1 and 12 say results can “support proposed labeling tables”
  - Risk log RSK‑CHT‑07 says “for design guidance only until in‑vivo validation” — needs alignment
- Extrapolation controls:
  - No correction factors applied; qualitative rationale listed but no quantitative mapping

## 12. People, roles, and guardrails
- Team:
  - Primary modeler: S. Patel (CHT); EM heater: L. Nguyen; experiments: J. Reyes
- Review:
  - Technical review recorded by “R. Singh” in Q‑note QN‑2026‑013
  - R. Singh is also the author of the mesh study note — independence unclear
- Training:
  - All users completed internal Fluent co‑sim training; no formal ASME V&V course
- Peer input:
  - One brown‑bag with clinical advisory panel; no external modeling peer review yet

## 13. Configuration control and traceability
- Trace matrix:
  - Decision questions → outputs (peak T, lesion metrics) → model inputs/settings → datasets
- Repro:
  - Reran v22d on compute node: matched within 0.3 °C and 0.05 mm to archived results
  - Two early runs (v22b Grid‑3b) missing journal files; noted as “local test” executed off‑VPN
- Toolchain status:
  - Corporate ISO 13485 QMS covers analysis workflows
  - However, Fluent 2024 R1 patch HF2 applied by analyst outside IT ticketing; no formal software impact assessment logged

## 14. Known gaps and near‑term plan
- Turbulence treatment:
  - Resolve laminar vs. k‑ω SST choice; carry both through to assess impact on jet breakup and near‑wall cooling
- Discretization:
  - Repeat grid/time‑step study with harmonized settings (same turbulence model, same URFs), compute observed order and interval; include numerics in UQ
- Bench comparison:
  - Add runs at 30 W/25 mL/min and 50 W/30 mL/min; tighten alignment on saline inlet temperature and tip tilt
- Inputs:
  - Lock perfusion model choice; document temperature‑dependent tissue k consistently
- Governance:
  - Independent reviewer outside modeling team; lock acceptance criteria and stick to them

## 15. Executive takeaways
- Strengths:
  - Credible physics coupling; reasonable experimental apparatus; basic code checks in place; sensitivity trends make physical sense
- Weak spots (blocking for claim of labeling‑grade use):
  - Non‑negligible mesh/time‑step sensitivity contradicts “grid‑insensitive” claim
  - Comparison to bench exceeds stated tolerances in multiple metrics
  - Mixed messages on turbulence model, intended use, and acceptance thresholds
  - UQ omits numerical components; sample size reduced without updating confidence statements
  - Configuration management lapses (untracked meshes; ad‑hoc patching)
- Bottom line:
  - Appropriate for design screening and relative comparisons among tip hole patterns
  - Not yet defensible for setting clinical labeling limits without addressed actions above
