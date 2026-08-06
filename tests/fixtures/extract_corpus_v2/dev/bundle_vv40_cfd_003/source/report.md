# CFD Credibility Slide Deck — Cleanroom Supply Diffuser Study (vv40-aligned)

## 1. Purpose and Decision Question
- Objective: Use CFD to rank diffuser layout options in a Grade B cleanroom bay (10.6 m × 5.2 m × 3.0 m) for recovery time and velocity uniformity over a 1.2 m × 2.4 m work zone.
- Decision it informs:
  - Select diffuser arrangement for the next prototype build before committing to ductwork changes.
  - Gauge whether expected average downflow at 1.0 m above floor meets 0.45 m/s ± 20% guidance.
- Claimed decision impact: Moderate — model informs equipment placement and ceiling grid cutouts; final ISO-14644 compliance still tied to room test.
- Note on scope: Not modeling particle transport; airflow only.

## 2. Geometry, Physics, and Key Assumptions
- Geometry:
  - Five 600 mm square perforated diffusers, ceiling-mounted; four return grilles near floor. Representative racks modeled as porous blocks.
  - Ceiling light troffers omitted; sprinkler droppers simplified to cylinders.
- Physics model:
  - Air at nominal 20°C; constant density (buoyancy neglected) due to weak ∆T (<2 K).
  - Flow taken as steady with turbulence; no transient events (door openings) simulated.
- Turbulence treatment:
  - Early scoping: SST k-ω for near-wall fidelity.
  - Production runs: realizable k-ε with scalable wall functions to reduce cost.
- Potential modeling gaps:
  - Door leakage not represented; returns idealized as fixed static pressure.
  - No filter media resistance in diffusers; perforation modeled as uniform porous jump.

## 3. Software, Numerics, and Code Health
- Solver: Ansys Fluent 2023 R2; double precision; pressure-based segregated algorithm.
- Spatial discretization:
  - Pressure: second-order.
  - Momentum/turbulence: QUICK on scoping runs; first-order upwind used in final batch to ensure convergence at maximum flow.
- Linear solver: AMG with default coarsening; pressure-velocity coupling via coupled scheme in ~30% of cases to accelerate.
- Code checks:
  - Sanity tests on canonical cases: laminar Poiseuille and a backward-facing step yielded expected trends; observed ~1.9 order on grid halving for velocity in Poiseuille.
  - One patch applied (hotfix HF-2023R2-19) mid-campaign; no change log effect noted on segregated solver but coupled scheme residual norm behavior changed.

## 4. Boundary Conditions and Operating Envelope
- Inlets:
  - Target total supply: 1.20 kg/s at 20°C (equivalent ~1.02 m^3/s).
  - Per-diffuser split: nominally even at 0.204 kg/s; in two scenarios redistributed 30/20/20/15/15% to mimic damper misbalance.
  - Upstream turbulence: 5% intensity and 0.1 m length scale assumed from AHU data.
- Outlets:
  - Four returns held at -8 Pa relative to room; sensitivity case at -12 Pa conducted.
- Walls: No-slip; standard wall functions unless y+ < 1 achieved (see grid discussion).
- Ambiguity to flag:
  - Some runs documented 1.00 kg/s total supply in the CSV headers while the slide subtitle states 1.20 kg/s; see Slide 10 notes.

## 5. Grid, Near-Wall Resolution, and Iterative Controls
- Mesh:
  - Unstructured hex-dominant with prism layers.
  - Three levels: 1.2M, 3.8M, and 7.5M cells; prism first height 0.8 mm; growth 1.2.
- Near-wall:
  - Stated target y+ < 1 in work zone; achieved y+ ≈ 0.6–2.4 on 7.5M case.
  - However, production runs used realizable k-ε with wall functions giving y+ ≈ 28–45 across most floor area.
- Convergence:
  - Residual targets: 1e-5 (momentum), 1e-6 (continuity). Final runs relaxed to 1e-4 for momentum to reach closure.
  - Monitor points (12 probes at 1.0 m height) plateaued to <0.3% drift over last 500 iterations.
- Mesh influence:
  - Velocity at probe P7 changed by 3.1% from 3.8M to 7.5M; P3 changed by -0.4%.
  - Non-monotone trend at P11 (1.2M: 0.47 m/s; 3.8M: 0.43 m/s; 7.5M: 0.45 m/s).

## 6. External Data for Reality Check
- Test setup:
  - Full-scale mockup bay; same diffuser model (AeroClean ACF-24) with 45% open-area perforated plate; grid of hot-wire anemometers at 1.0 m height.
  - Room held at neutral buoyancy; nominal 20°C, 101 kPa.
- Measurement details:
  - 16 probe locations in work zone; each averaged over 60 s; repeatability std dev ~0.02 m/s.
  - Flow bench certified diffusers at 0.204 kg/s ± 2% per unit.
- Potential mismatch:
  - Test logbook lists ambient 24–25°C for the first two runs due to AHU recalibration; CAD indicated 9 mm plenum height difference from model at two locations.
  - One diffuser grille replaced with near-identical 48% OA variant during test 3; not reflected in the simulation geometry.

## 7. Comparison Outcomes (CFD vs. Measurements)
- Metrics:
  - Primary target: zone-average velocity at 1.0 m; uniformity index (std dev / mean).
  - Secondary: proportion of probes within ±20% of mean; recovery time not validated (no transient test).
- Reported agreement:
  - Early summary slide: mean absolute error 6% across 16 probes for the best layout; 88% of probes within ±20%.
  - Detailed table (engineering notebook): MAE 11.8% including all probes; 75% within ±20%. Two outliers (P2, P13) excluded in the 6% roll-up due to “suspect anemometer alignment.”
- Pattern:
  - Bias low under stronger return suction (-12 Pa) by ~0.05 m/s; overpredicts near return corners.

## 8. Sensitivity Exploration
- Factor screening:
  - Varied supply split, return static pressure, porous resistance of racks (±30%), and diffuser loss coefficient (±25%).
- Observations:
  - Diffuser coefficient dominates variance of zone-average velocity (claimed 62% contribution in FAST screening).
  - Return pressure second; rack resistance minor except near aisle edges.
- Note:
  - Screening performed on 3.8M mesh with realizable k-ε; no re-check with SST k-ω.

## 9. Uncertainty and Variability Treatment
- Approach described:
  - Latin Hypercube with 300 draws across four inputs; 95% spread of zone-average velocity estimated.
- What was actually run:
  - Batch folder shows 30 samples completed (jobs 01–30), 8 failed on HPC queue; post-processed 28 after filtering two nonconverged runs.
- Results:
  - Reported 95% band: 0.39–0.53 m/s around nominal; coverage check against test data “>90% of probes inside band.”
  - Engineering log recalculation shows only 72% of probe readings fall within the propagated band when using the 11.8% MAE baseline.
- Epistemic vs aleatory:
  - Diffuser coefficient treated as random, though it reflects model-form lumping rather than true unit-to-unit variability.

## 10. Operating Point Consistency
- Flow rate:
  - Slide 4 stated 1.20 kg/s total supply for the validated case.
  - Test run “R2” used for comparison shows blower setpoint giving 1.00 kg/s total on the rotameter (operator note, 15:42:10).
  - CFD case label “CASE_R2_1p2kgps” implies 1.20 kg/s; however, mass flux integration over inlets in the output file sums to 1.01 kg/s.
- Turbulence seeding:
  - Assumed 5% inlet TI; AHU spec sheet indicates 1–2% downstream of HEPA in laminar flow modules.

## 11. Reproducibility and Run Management
- Version control:
  - Case and journal files on GitLab; tags v1.3 through v1.7; v1.5 introduced wall-function switch.
- HPC:
  - 48 cores per job; two runs restarted with different under-relaxation factors and relaxed residual targets to finish overnight.
- Post-processing:
  - Scripts in Python 3.11; unit-tested probe extraction and stats; a hotfix corrected a units mismatch (Pa vs inH2O) in return pressure logging after first five runs.

## 12. Where the Model Can Be Trusted (and Where Not)
- Expected valid range:
  - Total supply 0.9–1.3 kg/s; return pressure -6 to -12 Pa; diffuser type ACF-24 with 45–50% OA; room temperature 18–26°C.
  - Geometrically similar bays; same rack porosity within ±30%.
- Known weak spots:
  - Near returns and behind the last rack row — tendency to over-smooth recirculation with k-ε and wall functions.
  - Scenarios with heated equipment (>400 W per rack) not addressed; buoyancy not modeled.
- Applicability note:
  - Slides 3 and 5 emphasize y+ < 1 intent; most production results used y+ ~30–45 with wall functions, so near-floor gradients may be less reliable.

## 13. Risk and Review
- Use consequence:
  - If wrong by ~15–20%, diffuser choice could lead to one extra iteration of ceiling rework; cost impact moderate, schedule impact 2–3 weeks.
- Oversight:
  - Internal peer review by two CFD practitioners; no external audit.
  - Vendor (AeroClean) provided loss coefficient curve; no raw bench data shared.

## 14. Summary Assessment (Plain Language)
- Strengths:
  - Geometry fidelity for major features; multiple layouts examined under consistent workflow.
  - Basic solver checks and probe-based convergence monitoring in place.
  - Some physical test data at the right scale and in the actual mockup room.
- Concerns:
  - Mismatch between stated and implemented numerics (first- vs second-order, turbulence model switch).
  - Inconsistent operating point between CFD and test (1.2 vs 1.0 kg/s) and possible temperature mismatch.
  - Uncertainty analysis claims do not reflect the number of runs actually processed; coverage overstated.
  - Validation roll-up excludes outliers without a defensible instrument error analysis.

## 15. Decision
- Verdict by Cleanroom Upgrade CCB on 2026-08-05:
  - The CFD model is accepted for ranking diffuser layouts and rough-order estimates of zone-average velocity in the specified bay, subject to the conditions below.
  - The CFD model is not accepted for demonstrating compliance with ISO-14644 airflow criteria or for predicting local velocities within 0.1 m/s near returns or racks.
- Conditions for use:
  - Stick to realizable k-ε with the documented wall-function setup and mesh ≥3.8M cells.
  - Match blower mass flow in CFD within ±2% of the as-tested value and document it in the case header.
  - Report both the 6% and the 11.8% MAE figures with a clear statement on probe inclusion criteria.
  - Do not use the current UQ coverage claim; rerun at least 100 LHS samples before extending to other rooms.

## 16. Next Steps
- Short-term:
  - Align CFD operating point to the exact test flow and retabulate error metrics including all probes.
  - Run 50 additional UQ samples on the 3.8M mesh; re-evaluate coverage vs. probe data.
- Medium-term:
  - Evaluate SST k-ω on a subset near returns; compare to hot-wire profiles at P2/P13.
  - Add buoyancy for heated-rack scenarios planned in Phase 2.

## 17. Slide Appendix Notes
- File references:
  - Case bundles: GLB-CRBAY-DFR-v1.7/cases/CASE_R2_1p2kgps, …/CASE_R3_balanced.
  - Test logs: LabBook_CRBAY_May2026_pages_14–23.
- Contacts:
  - CFD: M. Jernigan; Test: S. Patel; CCB Chair: L. Ortega.
