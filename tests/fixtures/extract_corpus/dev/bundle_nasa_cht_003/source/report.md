# CHT Simulation Review: Turbine Blade Internal Cooling Passages
## Credibility Assessment Slide Deck — Aero-Thermal Systems Group
### Program: NGV-4 Next-Generation Vane Cooling | Review Cycle: PDR+6 months

---

## Slide 1 — Purpose and Scope

- **What this review covers**
  - Conjugate heat transfer (CHT) model of the NGV-4 first-stage nozzle guide vane
  - Internal serpentine cooling channels (3-pass configuration) + external film cooling rows A–D
  - Steady-state thermal predictions used to size TBC thickness and set metal temperature margins
- **What this review does NOT cover**
  - Transient thermal-mechanical fatigue cycling (separate FEA workstream)
  - Combustor exit profile uncertainty (treated as a boundary input here)
- **Simulation tool chain**
  - ANSYS Fluent 2023 R2 (solver), SpaceClaim + ICEM CFD (geometry/meshing), MATLAB post-processing scripts
  - Material properties from vendor database MatWeb + in-house alloy characterization (CMSX-4 substrate, YSZ TBC)
- **Review team**
  - Lead analyst: Dr. R. Okonkwo (Aero-Thermal)
  - Independent checker: Dr. S. Lindqvist (Methods & Standards)
  - Program representative: T. Ferreira (Systems Engineering)

---

## Slide 2 — Governing Equations and Physical Fidelity

- **Fluid domain**
  - Reynolds-Averaged Navier-Stokes (RANS) with realizable k-ε turbulence closure
  - Enhanced wall treatment activated; y⁺ target ≤ 1 on all wetted surfaces (achieved: mean y⁺ = 0.87, max y⁺ = 2.1 near leading-edge stagnation)
  - Compressible ideal-gas assumption; Mach < 0.15 in internal channels so low-Mach approximation valid
- **Solid domain**
  - Anisotropic thermal conductivity tensor for directionally-solidified CMSX-4 (longitudinal k = 14.2 W/m·K, transverse k = 11.8 W/m·K at 950 °C)
  - TBC modeled as a shell conduction layer; contact resistance at bond coat interface set to 2.4×10⁻⁴ m²·K/W (literature-derived, not measured for this lot)
- **Coupling strategy**
  - Flux-based coupling at all fluid-solid interfaces; convergence declared when interface temperature residual < 0.5 K between coupling iterations
  - 12 coupling iterations observed to reach convergence; plateau confirmed by monitoring 6 thermocouple-equivalent probe locations
- **Concerns flagged at this stage**
  - Turbulence model choice (realizable k-ε) is known to under-predict heat transfer in strongly curved passages — SST k-ω sensitivity run planned but not yet completed
  - Film cooling modeled with discrete-hole injection; coolant jet interaction with mainstream not validated for this specific hole geometry (fan-shaped, 7° lateral spread)

---

## Slide 3 — Geometry Fidelity and Representativeness

- **CAD source**
  - Nominal design intent geometry from CATIA V5 release 14c (frozen for PDR)
  - Cooling channel as-cast tolerances NOT incorporated — wall thickness nominal ±0.15 mm per drawing, but casting variability study deferred to CDR
- **Simplifications made**
  - Pedestals in pass-2 modeled as smooth cylinders; actual casting has slight draft angle and fillet radii (r ≈ 0.3 mm) — estimated effect on pressure drop < 3% based on prior correlations
  - Trailing edge slot discharge simplified to a uniform slot; actual geometry has 14 discrete slots (pitch 1.8 mm)
  - **This simplification is flagged as potentially non-conservative** — local hot-spot risk at slot lands not captured
- **Domain extents**
  - Hot-gas path: 0.5 chord upstream, 1.0 chord downstream; periodicity applied at pitch boundaries (confirmed symmetric loading within 1.2% of full-passage run)
- **Representativeness of operating point**
  - Nominal take-off condition: TIT = 1,820 K, coolant inlet T = 820 K, coolant-to-mainstream pressure ratio = 1.045
  - Part-power and hot-day conditions NOT modeled in this cycle

---

## Slide 4 — Mesh Refinement Study (Discretization Sensitivity)

- **Mesh family**
  - Three structured hexahedral meshes generated in ICEM CFD:
    - Coarse: 4.2 M cells | Medium: 11.7 M cells | Fine: 31.4 M cells
  - Prism layer growth ratio 1.2 on all solid walls; 20 prism layers on cooling channel walls
- **Key output quantities monitored**
  - Area-averaged Nusselt number on pass-2 floor (Nu_avg)
  - Peak metal temperature on suction-side external wall (T_peak)
  - Coolant total pressure drop, pass-1 inlet to pass-3 exit (ΔP_cool)

| Mesh    | Nu_avg | T_peak (K) | ΔP_cool (Pa) |
|---------|--------|------------|--------------|
| Coarse  | 187    | 1,143      | 4,820        |
| Medium  | 203    | 1,128      | 5,010        |
| Fine    | 207    | 1,124      | 5,055        |

- **GCI analysis**
  - Grid Convergence Index (Roache method) computed for T_peak: GCI_fine = 0.8%, GCI_medium = 3.2%
  - Apparent order of convergence p = 1.94 (close to theoretical 2nd order for scheme used) ✓
  - Medium mesh selected for production runs as cost-performance optimum; fine mesh used for spot-checks at 3 critical locations
- **⚠ AMBIGUITY NOTE (for reviewers)**
  - Executive summary (Slide 12) states "mesh independence confirmed on fine mesh with GCI < 1%"
  - However, the production runs documented throughout this deck use the **medium mesh** (GCI_medium = 3.2%)
  - This inconsistency was identified during independent check — the 3.2% figure should propagate into uncertainty budgets but does not appear to do so in Slides 8–10

---

## Slide 5 — Code Verification Activities

- **Unit-level checks**
  - Fluent's built-in conjugate interface verified against analytical Biot-number solution for flat-plate with internal convection (error < 0.3%) — documented in Methods Note CHT-MN-2022-04
  - Turbulent channel flow (Dittus-Boelter regime, Re = 24,000) reproduced to within 4.1% of correlation — acceptable for RANS
- **Regression testing**
  - Fluent 2023 R2 results compared against Fluent 2021 R2 baseline on identical mesh and BCs; maximum deviation in T_peak = 0.6 K — version change introduces negligible numerical drift
- **Known solver limitations acknowledged**
  - Pressure-velocity coupling via SIMPLE algorithm; convergence monitored via scaled residuals (target 10⁻⁵ for energy, 10⁻⁴ for momentum) — energy residual plateau observed at 2×10⁻⁵ on medium mesh
  - **The energy residual not reaching target threshold is noted in the solver log but is NOT called out in the main body of this deck** — independent checker flagged this as a concern; analyst response pending
- **No independent re-implementation** of governing equations performed; verification relies entirely on ANSYS validation suite and in-house flat-plate case

---

## Slide 6 — Comparison Against Physical Test Data (Solution Validation)

- **Available experimental datasets**
  - Dataset A: Scaled (3×) perspex model of pass-2 channel, liquid crystal thermography, University of Stuttgart (2019) — Re-matched, adiabatic walls
  - Dataset B: Full-scale engine test, NGV-3 predecessor vane, 14 embedded thermocouples, proprietary (Turbotech GmbH, 2021)
- **Dataset A comparison**
  - Nu distribution along pass-2 floor: simulation within ±9% of measurements at 18 of 22 spatial stations
  - Discrepancy at turn-around bend (stations 19–22): simulation over-predicts Nu by 14–18% — attributed to Dean-flow secondary vortex not well-captured by realizable k-ε
  - **Validation uncertainty not formally quantified** — no experimental uncertainty bars provided in Stuttgart report; analyst assumed ±5% instrument uncertainty but this is not traceable to a calibration record
- **Dataset B comparison**
  - NGV-3 geometry differs from NGV-4 in pass-3 aspect ratio (AR 3.1 vs. 2.4) and hole count (film row C: 22 vs. 18 holes)
  - Despite geometric differences, team uses Dataset B as primary validation evidence for T_peak predictions
  - **⚠ AMBIGUITY / CONCERN**: Slide 9 (Results) states "validated against engine hardware" — this is technically accurate but potentially misleading given the geometric dissimilarity; the independent checker recommends a qualification statement be added
  - Thermocouple data shows mean bias of +12 K relative to simulation (simulation runs cool); analyst attributes this to TBC spallation in the test article — plausible but unconfirmed

---

## Slide 7 — Boundary Conditions and Input Uncertainty

- **Coolant inlet conditions**
  - Total temperature: 820 ± 15 K (from cycle deck, 2σ)
  - Total pressure: 42.3 ± 0.8 bar (from cycle deck, 2σ)
  - Turbulence intensity at coolant inlet: assumed 5% — no measurement available; sensitivity not assessed
- **Hot-gas mainstream**
  - Combustor exit radial temperature profile (RTDF = 0.14) applied as inlet BC; circumferential distortion NOT modeled (uniform in pitch)
  - RTDF uncertainty: ±0.02 (engine-to-engine variation) — propagated into T_peak via ±1% TIT perturbation study giving ΔT_peak = ±18 K
- **Wall roughness**
  - Internal cooling channels: equivalent sand roughness ks = 8 μm (investment casting estimate); external surface: ks = 2 μm (machined)
  - Sensitivity to roughness: ±50% variation in ks produces ±3.5% change in Nu_avg — deemed acceptable
- **Material properties**
  - CMSX-4 conductivity values from MatWeb at discrete temperature points; interpolated with cubic spline
  - TBC contact resistance value (2.4×10⁻⁴ m²·K/W) sourced from open literature — **not specific to this TBC deposition process or lot**; program materials team has been asked to provide measured values but data not yet available
  - **⚠ AMBIGUITY**: Section 3.2 of the companion analysis report (not included in this deck) states the contact resistance was "measured in-house at 1.8×10⁻⁴ m²·K/W" — this contradicts the value used in the simulation; the discrepancy (25%) has a non-trivial effect on predicted T_peak (estimated ±22 K swing)

---

## Slide 8 — Sensitivity and Uncertainty Aggregation

- **Sensitivity drivers ranked (Tornado plot, ΔT_peak)**
  1. TBC contact resistance: ±22 K
  2. Mainstream TIT (RTDF uncertainty): ±18 K
  3. Turbulence model (k-ε vs. SST k-ω, estimated from literature): ±15 K
  4. Mesh discretization (GCI_medium): ±9 K
  5. Coolant inlet temperature: ±7 K
  6. Wall roughness: ±4 K
- **Combined uncertainty (RSS, assuming independence)**
  - Total ΔT_peak ≈ ±33 K (1σ equivalent)
  - **Note**: turbulence model sensitivity is estimated, not computed — SST run still outstanding
  - Contact resistance ambiguity (see Slide 7) means the central value itself may be shifted by up to 22 K, independent of the ±33 K spread
- **Margin status**
  - Predicted T_peak (medium mesh, nominal BCs) = 1,128 K
  - Material limit (CMSX-4, 10,000 hr creep life criterion) = 1,165 K
  - Nominal margin = 37 K; with 1σ uncertainty, margin narrows to ~4 K
  - **This is considered insufficient margin at PDR; program has been notified**

---

## Slide 9 — Results Summary (Thermal Map)

- **Suction-side peak temperature: 1,128 K** (medium mesh, nominal)
- **Pressure-side mean temperature: 1,082 K**
- **Cooling effectiveness (η_overall)**
  - Pass-1: η = 0.61 | Pass-2: η = 0.58 | Pass-3: η = 0.54
  - Film cooling rows A–B: η_film ≈ 0.32 (blowing ratio M = 1.1)
  - Film cooling rows C–D: η_film ≈ 0.28 (M = 1.3, over-blown condition flagged)
- **Hot-spot locations**
  - Leading edge pressure-side shoulder: ΔT above mean = +44 K (driven by stagnation heating, film coverage gap)
  - Pass-2/Pass-3 turn-around: ΔT above mean = +31 K (secondary flow heating, consistent with Dataset A discrepancy)
- **Stated conclusion in this slide**: "Simulation validated against engine hardware; thermal margins acceptable with standard design knockdowns applied"
  - **⚠ This conclusion is inconsistent with Slide 8** which shows margin narrows to ~4 K under uncertainty — "acceptable" is not supported without qualification
  - Independent checker has requested revision of conclusion language before final issue

---

## Slide 10 — Applicability to Design Decisions

- **Intended use of these results**
  - TBC thickness sizing (primary use): results directly feed TBC design tool
  - Coolant flow allocation (secondary use): ΔP_cool used to set orifice diameters
  - Life prediction input (tertiary use): T_peak feeds creep-fatigue model
- **Scope of applicability**
  - Valid for: nominal take-off condition, clean combustor profile, new TBC (no spallation)
  - NOT valid for: part-power, hot-day, degraded TBC, or off-nominal coolant pressure ratio
  - **Extrapolation risk**: life prediction team has requested results at 5% over-temperature condition — analyst has provided these by linear extrapolation; this extrapolation is not validated and should be treated with caution
- **User guidance**
  - Post-processing scripts (MATLAB, v2.3) require manual input of mesh file path — no automated input checking; incorrect path produces silently wrong output (known issue, tracked in JIRA CHT-112)
  - **⚠ CONCERN**: the JIRA ticket has been open for 4 months with no assigned owner — this represents a latent human-factors risk in the analysis workflow; any analyst running the scripts without awareness of CHT-112 could use erroneous post-processed data without detection

---

## Slide 11 — Documentation and Configuration Control

- **Simulation records**
  - Case files archived in Teamcenter PLM under document number NGV4-CHT-2024-003 Rev B
  - Mesh files, solver settings, and post-processing scripts version-controlled in GitLab (repo: aero-thermal/ngv4-cht, tag: PDR_release_v2)
  - Input boundary condition file: BC_takeoff_nominal_v4.csv — version history maintained; previous versions retained
- **Traceability gaps**
  - Material property database (MatWeb extract): snapshot taken 2023-11-14; no formal configuration item — if MatWeb updates values, re-run not automatically triggered
  - Stuttgart Dataset A: provided as PDF scan; raw data not available; no formal data use agreement on file
- **Review and approval status**
  - Analyst self-check: complete
  - Independent technical review (Dr. Lindqvist): in progress — 6 open comments, 2 classified as major (energy residual plateau; conclusion language on Slide 9)
  - Program-level approval: PENDING resolution of major comments
- **Change history**
  - Rev A (2024-03-10): initial issue
  - Rev B (2024-05-22): updated TBC contact resistance, mesh refinement table corrected — **note: the executive summary was not updated at Rev B and still reflects Rev A mesh selection rationale**

---

## Slide 12 — Executive Summary (as written by analyst)

> *"The NGV-4 CHT simulation has been completed using industry-standard RANS methodology with conjugate coupling in ANSYS Fluent. Mesh independence has been confirmed on the fine mesh with GCI < 1%. The model has been validated against engine hardware (NGV-3 test campaign) and scaled laboratory data (University of Stuttgart). Predicted peak metal temperature is 1,128 K, providing a 37 K margin against the creep life limit. Results are considered suitable for use in TBC thickness sizing and coolant flow allocation at PDR."*

- **Independent checker's annotation:**
  - "GCI < 1% applies to fine mesh; production runs use medium mesh (GCI 3.2%) — statement is misleading"
  - "Validation dataset is geometrically dissimilar; 'validated against engine hardware' overstates confidence"
  - "37 K margin does not account for the combined uncertainty of ±33 K quantified in the sensitivity analysis"
  - "Contact resistance discrepancy between this deck and companion report not resolved — central value uncertain"
  - **Recommendation: Executive Summary must be revised before program distribution**

---

## Slide 13 — Open Items and Path Forward

| Item | Description | Owner | Target |
|------|-------------|-------|--------|
| OI-01 | Complete SST k-ω sensitivity run | Okonkwo | 2024-07-15 |
| OI-02 | Obtain measured TBC contact resistance (this lot) | Materials (Chen) | 2024-07-30 |
| OI-03 | Resolve contact resistance discrepancy (deck vs. companion report) | Okonkwo + Chen | 2024-07-30 |
| OI-04 | Revise executive summary language | Okonkwo | 2024-06-28 |
| OI-05 | Assign owner and resolve JIRA CHT-112 (post-processing script path bug) | TBD | 2024-07-15 |
| OI-06 | Obtain Stuttgart Dataset A raw data and calibration records | Lindqvist | 2024-08-01 |
| OI-07 | Assess trailing-edge slot simplification hot-spot risk | Okonkwo | CDR |
| OI-08 | Model part-power and hot-day operating points | TBD | CDR |

- **Overall assessment (independent checker):**
  - Current state: **conditionally credible for scoping purposes only**
  - Not recommended for final TBC thickness commitment until OI-01 through OI-04 resolved
  - Margin situation (4 K under uncertainty) warrants program-level risk discussion

---

## Slide 14 — References and Data Sources

- ANSYS Fluent Theory Guide, Release 2023 R2, ANSYS Inc.
- Roache, P.J. (1998) *Verification and Validation in Computational Science and Engineering*, Hermosa Publishers
- University of Stuttgart Internal Report ST-LTT-2019-07 (Dataset A) — restricted distribution
- Turbotech GmbH Engine Test Report TG-NGV3-2021-EX-004 (Dataset B) — proprietary
- MatWeb Material Property Database, extract 2023-11-14, www.matweb.com
- Methods Note CHT-MN-2022-04, "Verification of Conjugate Interface in ANSYS Fluent," Aero-Thermal Systems Group
- CMSX-4 Alloy Data Sheet, Cannon-Muskegon, Rev 2020
- Program document NGV4-CHT-2024-003 Rev B (this document), Teamcenter archive

---

*Document status: DRAFT — Under independent review. Do not use for design commitment without program approval.*
*Prepared by: R. Okonkwo | Checked by: S. Lindqvist (in progress) | Approved by: PENDING*
*File: NGV4-CHT-2024-003_RevB_slides.md | GitLab tag: PDR_release_v2*
