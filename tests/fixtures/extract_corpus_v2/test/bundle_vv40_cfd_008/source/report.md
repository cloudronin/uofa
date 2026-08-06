# CFD Elbow Project — Credibility Slide Deck (v0.7)

## 1) What we’re deciding
- Purpose: estimate pressure loss and outlet flow uniformity through a 300 mm 90° elbow with two turning vanes, to pick a vane count for the pilot build.
- Decision hook: if the loss coefficient stays below 0.85 at 8–12 m/s and outlet maldistribution index stays under 0.12, we green‑light the two‑vane option.
- Claimed scope of use:
  - Early design screening and sizing of the elbow/vane set.
  - Not intended for certification or spec sign‑off without additional testing.
- Note: Ops requested to use these results to release final vane count to procurement this week.

## 2) System and physics scope
- Geometry: 90° elbow, R/D = 1.5, 300 mm ID; two 4 mm thick aluminum vanes, 25° at midspan; trimmed corner radius 20 mm.
- Flow regime: air, nominally incompressible; inlet bulk speeds 8, 10, 12 m/s; Re ≈ 3.2e5 to 4.8e5 based on diameter at 20 °C.
- Surface finish: bead‑blasted aluminum; equivalent sand‑grain roughness k_s = 50 μm (assumed).
- Thermal effects neglected; density and viscosity taken constant.

## 3) Software, numerics, and hardware
- Solver: Ansys Fluent 2023 R2, pressure-based coupled solver; least-squares cell-based gradients.
- Floating point: double precision enabled on cluster nodes; restart files written every 200 iterations.
- Turbulence: baseline runs use k–ω SST with curvature correction; one scale‑resolving (SBES) check at 10 m/s.
- Linear solvers: AMG with default coarsening; pressure under‑relaxation 0.3 (steady), 0.2 (transient).
- Hardware: 2 x 32-core nodes (AMD EPYC), 256 GB RAM per node; typical wall time 3–9 hours per case.
- Note: Two exploratory runs at 12 m/s used single precision due to a memory limit on the rental node; outputs later converted to double during post.

## 4) Geometry prep and simplifications
- CAD trimmed to fluid volume; fillets < 2 mm suppressed; bolt heads and gaps sealed; no vane leading‑edge chamfer modeled.
- Vane‑to‑wall gaps set to 0.5 mm constant (as-manufactured drawing shows 0.5 ± 0.2 mm).
- Comparison to bench article: CMM scan indicates an as‑built 0.9 mm gap locally near the intrados; not included in the base model.

## 5) Grid construction and near‑wall treatment
- Unstructured polyhedral core with 12 prism layers; growth 1.18; first cell height for y+ ≈ 1 at 12 m/s using SST.
- Three mesh levels for steady RANS:
  - Coarse: 1.2M cells, 6 prism layers, target y+ ≈ 30–100 (standard wall functions).
  - Medium: 3.6M cells, 12 prism layers, y+ ≈ 0.8–2.5 across most of the walls.
  - Fine: 9.8M cells, 15 prism layers, y+ < 1 almost everywhere.
- Quality: min orthogonal quality 0.13 (fine), 0.09 (coarse); max skewness 0.85 (coarse elbows near vane tip).
- Alternate mesh plan (early draft) referenced realizable k–ε with enhanced wall treatment for the coarsest grid.

## 6) Run control and convergence behavior
- Steady runs:
  - Iterations: 2500–3800 until residuals drop below 1e‑5 for momentum and turbulence; continuity typically at 2e‑5.
  - Mass balance: < 0.2% for 8 and 10 m/s; 0.5% for 12 m/s medium grid.
  - Monitors: area‑averaged outlet static pressure and sector velocities; last 500 iterations flat within ±0.3%.
- Notes on stragglers:
  - At 12 m/s on fine grid, residuals plateaued at ~3e‑3 for k and ω despite stable outlet pressure; accepted after 1200 more iterations with no drift in loss coefficient.
  - An early 10 m/s coarse run terminated at residuals 1e‑4 due to time slot limit on the queue; loss was within 1% of the restarted run.

## 7) Time dependence checks
- Rationale: visualizations showed shedding behind the vane trailing edge at 10–12 m/s; assessed whether unsteadiness impacts mean losses.
- URANS test: Δt = 1e‑3 s, 5 inner iterations, 2000 steps; means taken over last 0.5 s.
- Outcome: time‑averaged pressure drop at 10 m/s increased by 6% relative to steady solution; outlet maldistribution decreased from 0.11 to 0.09.
- Position taken for baseline: steady solutions considered adequate for screening; transient used only to bound potential bias.

## 8) Boundary conditions and inputs
- Inlet:
  - Target: measured axial profile from a 10D straight pipe upstream (Pitot rake), TI ≈ 1%, length scale 0.07D.
  - Implemented: profile imported as a table for the 8 and 10 m/s medium/fine grids.
  - Cycle‑3 12 m/s cases used a uniform inlet with TI = 10% as the profile file was not available when queued.
- Outlet: static pressure adjusted to hit the measured flow rate in the rig during correlation runs; otherwise set to zero gauge.
- Walls: no‑slip; roughness k_s = 50 μm, Cs = 0.5.
- Fluid properties: air at ρ = 1.204 kg/m³, μ = 1.825e‑5 Pa·s (20 °C). The lab thermistor read 25.3 ± 0.4 °C during the 8 m/s tests.

## 9) Mesh refinement outcomes and estimated numerical bias
- Three‑level refinement used for 8 and 10 m/s with SST:
  - Loss coefficient at 10 m/s: 0.846 (coarse), 0.827 (medium), 0.821 (fine); observed order p ≈ 2.1; Richardson‑extrapolated 0.818; estimated discretization band ≈ 1.8%.
  - Outlet maldistribution index converged non‑monotonically; used trend on medium/fine only; span ±0.02.
- 12 m/s could not complete on the fine mesh without divergence in ω; extrapolated using coarse–medium only with assumed p = 2.0; provisional numerical band ~3.5%.
- Cell‑to‑cell pressure jump histograms improved with refinement; persistent hotspot at vane tip in all levels.

## 10) Bench comparison results
- Test article: same nominal CAD, two vanes; straight‑through bench with calibrated orifice meter; barometric correction applied.
- Reported measured pressure losses (Δp) and predicted values (steady SST unless noted):
  - 8 m/s: test 160 Pa; CFD 154 Pa (−3.8%); outlet uniformity index 0.90 (test 0.92 via five‑point grid).
  - 10 m/s: test 255 Pa; CFD 262 Pa (+2.7%); SBES mean 278 Pa (+9.0% vs test).
  - 12 m/s: test 370 Pa; CFD 420 Pa (+13.5%); uniformity index CFD 0.13 (test 0.11).
- Stated earlier in the kickoff summary: “agreement within 5% across the speed range”; note that the 12 m/s result exceeds this.
- Measurement uncertainty:
  - Pressure: ±2% of reading (orifice and transducer combined).
  - Flow rate: ±1.2% based on ISO 5167 traceability.

## 11) Sensitivity and what matters most
- Vane angle: ±3° at midspan changes loss by +2.3/−1.9%; outlet maldistribution shifts by ±0.015.
- Surface finish: doubling k_s to 100 μm raises loss by 5–7% depending on speed.
- Inlet swirl: ±5° solid‑body superposed on the profile increases maldistribution from 0.10 to 0.14 at 10 m/s; loss +3%.
- Turbulence model swap: realizable k–ε with enhanced wall treatment produced a loss within 0.5% of SST on the medium grid at 10 m/s, but with y+ ~70–120 on parts of the intrados.

## 12) Where it does and doesn’t apply
- Covered:
  - Reynolds number range 3e5–7e5; two‑vane configurations with the specified chord and stagger.
  - Smooth walls with roughness ≤ 100 μm; negligible compressibility.
- Not covered or weakly supported:
  - Gapped vanes > 0.5 mm along more than 20% of span.
  - Severe upstream swirl or crossflow; pulsatile intake.
- Usage guidance:
  - Intended as a design‑screening tool, not as final acceptance evidence. However, the team plans to proceed with releasing two‑vane hardware based on these runs unless the 12 m/s discrepancy is resolved.

## 13) Traceability, configuration, and QA items
- Case setup tracked in Git (repo “elbow‑vane‑cfd”), tag v0.7; input decks and post scripts under /cases/steady/SST.
- Solver version documented in run logs; mesh generator versions captured in the header.
- One “hotfix” run for 12 m/s (medium grid) executed on a rental node outside the managed filesystem due to queue limits; results later copied in via scp and renamed to match the scheme.
- Repeatability:
  - Re‑running 10 m/s medium grid reproduced Δp within 0.2% and outlet metrics within 0.01 (same binary, same hardware).
  - The single‑precision exploratory 12 m/s run differed from the double‑precision restart by 1.1% in loss.
- Basic solver check:
  - Plan called for a pipe friction factor sanity test and lid‑driven cavity benchmark; pipe case completed (f match within 1.5% at Re = 1e5). The cavity case was deferred to save schedule and has not been run.

## 14) Review status and independence
- Two‑person review on 2026‑07‑29: mesh strategy, monitors, and postprocessing scripts checked by J. Ortega (Thermo‑Fluids group, not on elbow project).
- A follow‑up internal read‑through by the elbow subteam on 2026‑08‑01 approved using results for design screening.
- Open question from review: justification for accepting steady residual stalls at 12 m/s; action captured to run a tighter URANS with Δt = 5e‑4 s.

## 15) Key takeaways and actions
- Confidence is reasonable at 8 and 10 m/s: mesh trend is clear; comparison with the bench is within a few percent; sensitivities make physical sense.
- 12 m/s mismatch is material and coincides with less rigorous BCs (uniform inlet, higher TI) and non‑converged turbulence residuals.
- Actions before treating 12 m/s as credible for decisions:
  - Re‑run 12 m/s with measured inlet profile and double precision on the fine grid; tighten ω solver controls.
  - Include the as‑built 0.9 mm gap near the intrados in a what‑if geometry.
  - Repeat the URANS at 12 m/s with half timestep; extend averaging window to 1.0 s.
  - Acquire a second bench point at 11 m/s to check trend continuity.

---
Back‑pocket notes on apparent inconsistencies to reconcile
- Temperature: simulations at 20 °C properties vs lab at 25 °C; estimate effect on Re and Δp is < 2%, but close the gap by matching properties on reruns.
- Inlet profile usage: stated “measured” in several places; actually uniform + TI = 10% on the 12 m/s cycle‑3 jobs.
- Precision mode: cluster runs in double; two 12 m/s jobs in single due to RAM pressure.
- Turbulence model: baseline is SST; one plan and one sensitivity used realizable k–ε on the coarse grid; ensure the final comparison table labels model choices explicitly.
