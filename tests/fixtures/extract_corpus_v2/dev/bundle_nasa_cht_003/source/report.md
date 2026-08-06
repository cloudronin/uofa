# CHT Review — Avionics Cold Plate for Guidance Computer (Rev B)

- Model under review: Conjugate heat transfer of aluminum cold plate with embedded microchannels bonded to FR-4 PCB stack, water–glycol coolant loop
- Toolchain: ANSYS Fluent 2023 R2 (pressure-based solver), Ansys Meshing, Python post-processing, Git-LFS for datasets
- Decision context: assess suitability for predicting card-edge and component case temperatures to support layout and margin closure on TVAC test readiness


## Objective and context of use

- Questions the model must answer
  - Predict peak silicon junction proxies (Tcase + Rjc x Q) within ±6 K for power devices >10 W
  - Rank candidate manifold geometries by hotspot mitigation at fixed pump setting
  - Size radiator load for TVAC setup by estimating loop heat rejection within ±5%
- Operating envelope intended
  - Coolant: 30–60 C inlet, 30% PGW mixture; mass flow 0.01–0.02 kg/s
  - On-board dissipation: 150–450 W total; vacuum external environment (σT4 radiation neglected in baseline)
- Claim of model status at entry to review
  - Fully converged steady RANS CHT; boundary layer resolved with y+ < 1 across coolant walls
  - Properties modeled as temperature-dependent throughout fluid and solids


## Physics and modeling choices

- Flow and heat transfer
  - Turbulence: SST k–ω with curvature correction; low-Re wall treatment
  - Conjugate interfaces: two-sided wall coupling with consistent thermal flux; conservative matching across non-conformal grids
  - Thermal contact: thin-layer approximation for TIM; uniform interface conductance used per joint
  - Phase considerations: single-phase only; cavitation off; buoyancy modeled via Boussinesq
- Simplifications
  - Electronics represented as discrete volumetric heat sources within package solids
  - Radiation off; external conduction paths through fasteners omitted (mass-minor)
  - Manifold O-ring lands idealized as perfectly sealed (no bypass leakage)


## Geometry, loads, and boundary specifications

- Hardware abstraction
  - 16 parallel microchannels: 0.8 mm wide x 1.2 mm tall, 74 mm length; 1-to-16 inlet plenum; 6061-T6 aluminum cold plate bonded to PCB with 0.1 mm TIM
  - PCB: eight-layer FR-4 with 1 oz Cu planes; component keep-outs modeled explicitly for six TO-247 devices
- Boundary conditions
  - Inlet: 0.015 kg/s, 40 C; outlet pressure 0 gauge
  - Heat map: six power devices at 35 W each, twelve minor ICs at 2 W each; baseboard background 40 W
  - External: adiabatic outer faces (TVAC assumption)
- Material data cited
  - Aluminum 6061-T6: k(T) per MIL-HDBK-5J curve
  - FR-4 and Cu: IPC-2152 tables
  - 30% PGW: NIST REFPROP mixture properties


## Software, workflow, and analyst experience

- Tool QA posture
  - Double precision, second-order spatial schemes; steady segregated solver
  - Case/replay journals scripted; CI job regenerates figures on Linux RHEL 8
  - Case files and meshes tracked in Git; tag cpCHT_v27
- Analyst credentials
  - Primary analyst: 10 years thermal-fluids, 6 prior CHT programs; Fluent advanced training (2022)
  - Peer review by fluids SME and test lead completed 2026-06-28


## Grid and near-wall resolution

- Mesh construction
  - Poly-prism boundary layers: 20 layers, first-cell height 5 µm; growth 1.15; core poly mesh
  - Final baseline: 18.2 M cells (fluid 12.6 M, solids 5.6 M)
- Refinement study (coarse 9.7 M, baseline 18.2 M, fine 34.5 M)
  - Peak Tcase changed: coarse→baseline −3.1 K; baseline→fine −1.6 K
  - GCI at hotspot estimated 6.3%; domain-average solid temperature GCI 1.4%
- Near-wall actuals (baseline)
  - Coolant side: median y+ ≈ 7; 15% of wetted area 12 < y+ < 25
  - Solid side: wall-conduction gradients well resolved by thickness-based layers
- Note: This contrasts with the earlier assertion that y+ < 1 was achieved everywhere on coolant walls


## Convergence and energy balance

- Residuals and monitors
  - Momentum/energy residuals plateaued at 3e−5/8e−6; mass imbalance <0.1%
  - Peak Tcase monitor flat within 0.2 K over last 1,000 iterations
- Global conservation
  - Net heat input vs outlet enthalpy rise closed to 2.7% in baseline
- Solver controls
  - Under-relaxation lowered mid-run (energy 0.9→0.7) to break oscillations; pseudo-transient off
- Contrast with model status claim of “heat in = heat out within 0.5%”


## Benchmarks and sanity checks

- Internal flow heat transfer check
  - Single-channel surrogate at Re ≈ 2,300 yielded Nu within 3.2% of Gnielinski correlation
- Conjugate slab verification
  - 1D layered slab with TIM matched analytic within 0.8 K across 60 K drop
- Pressure drop
  - Channel-only Δp agrees within 6% against Idelchik minor-loss estimate when using measured plenum K factors


## Test correlation summary (prototype cold plate A)

- Test setup (TVAC breadboard)
  - Deionized water loop at 30% PG; coriolis meter (±0.5%), RTDs on inlet/outlet (class A), 12 thermocouples on baseplate
  - Heat applied with ceramic heaters mapped to board footprint
- Comparison results at 0.015 kg/s, 40 C inlet, 250 W
  - Average baseplate temperature within 5.1%
  - Max local deviation: 11.8 K high at TC7 near manifold corner (≈12%)
  - Outlet temperature rise underpredicted by 0.9 C (4.8%)
  - Pressure drop overpredicted by 18% vs transducer reading
- Note: “within 5%” statement above refers to average; local bias is larger than claimed elsewhere in pre-briefs


## Inputs pedigree and error bars

- Where numbers came from
  - Copper plane k: IPC-2152, temperature-adjusted; used constant 385 W/m-K in model at 40 C
  - Aluminum k: MIL-HDBK-5J curve used; implemented as piecewise-linear over 20–80 C
  - TIM joint conductance: coupon tests gave R” = 1.5e−4 m2K/W; baseline model used 5e−5 m2K/W citing “process improvement”
  - PGW mixture: REFPROP tables sampled; however, properties exported at 40 C and held fixed in runs cpCHT_v27
- Uncertainties applied
  - Flow rate ±2%; heater power ±3%; R” ±50% explored; kAl ±5%; kCu ±10%
- The earlier statement that all properties were temperature-dependent does not match the constant-property decks used in reviewed runs


## What moves the needle (sensitivity)

- One-at-a-time sweeps about baseline
  - +50% R” raises peak Tcase by +6.9 K; −50% lowers by −4.7 K
  - Flow ±10% changes peak Tcase by ∓2.1 K; outlet ΔT tracks within ±0.6 C
  - Inlet T +10 C raises all solid temps ≈ +9.5 C (near-linear)
  - Switching SST→k–ε Realizable increases hotspot by +2.8 K; impacts Δp −4%
- Sobol proxy (screening via Morris)
  - R” and local heat map concentration dominate (>70% of variance on hotspot metric)


## Where we think it applies

- Supported operating window based on tests and sweeps
  - Flow: 0.6–1.2 L/min; Total board power: 150–450 W; Inlet temperature: 20–60 C
  - Geometry family: same manifold topology; TIM thickness 75–125 µm
- Usage outside the above occurred in scenario S4 (mission hot case)
  - 0.4 L/min, 500 W, 85 C inlet was analyzed without new calibration runs
  - Boiling margin evaluated qualitatively only; single-phase model retained
- This exceeds the empirically supported region described in pre-brief


## Repeatability, traceability, and controls

- Reproducibility posture
  - Meshes, cases, and scripts stored under tag cpCHT_v27; post-processing notebooks hash-locked
  - Two hotfix runs (HF1/HF2) launched from GUI during review week; modified under-relaxation and turbulence limiter—changes not yet merged to repo
- Configuration diffs
  - HF1 used contact R” = 1.0e−4 m2K/W to match TC7; HF2 restored baseline but adjusted plenum loss coefficients
  - Case naming for HF1 doesn’t reflect altered R” (may mislead reuse)
- Prior use
  - Similar workflow used on Gateway EPS cold plate (2024); no formal cross-project validation dossier imported here


## Known gaps and risk items

- Remaining discrepancies
  - Local hotspot near manifold corner not captured within ±6 K target
  - Energy balance closure at 2–3% is marginal for heat-rejection sizing
- Model form limits
  - Radiation neglected; may matter >60 C inlet
  - No fouling or gas ingestion model; TVAC purge transients not represented
- Data gaps
  - Contact conductance variability not mapped across board; single coupon result
  - No test points above 60 C inlet, yet S4 relies on 85 C prediction


## Recommendation and decision

- Summary of credibility posture
  - Strengths: geometry-faithful CHT; mesh study completed; channel heat transfer benchmarked; average temps align within ~5%; sensitivity shows expected drivers
  - Concerns: wall resolution below intent (y+ up to 25); properties held constant despite earlier claim; contact conductance in model diverges from coupon; local temp bias ~12%; range-of-use exceeded in S4
- Decision by Thermal Working Group (2026-07-02)
  - The model is accepted for
    - Ranking manifold options and estimating board-average and outlet temperatures for 20–60 C inlet, 0.6–1.2 L/min, and 150–450 W total heat, provided contact resistance is bracketed ±50% in reports
  - The model is not accepted for
    - Predicting worst-case local component temperatures or any case with inlet temperature >60 C, flow <0.6 L/min, or total heat >450 W; not approved for boiling margin assessment
- Conditions for use
  - Update property decks to be temperature-dependent; re-run fine mesh to reduce hotspot GCI below 3%; reconcile TC7 discrepancy with targeted test or detailed contact mapping before expanding range
- Disposition owner: Thermal Working Group chair, with concurrence from Test Lead and Fluids SME


# Backup slides (for discussion only)

- Proposed corrective actions and schedule
  - Implement temperature-dependent property hooks (1 day); rerun fine mesh (2 days, 128 cores)
  - Targeted TIM mapping via IR thermography coupon (1 week)
  - TVAC re-test point at 60 C and 0.8 L/min (next chamber availability)
- Potential impact on TVAC readiness
  - Average heat load sizing unaffected; hotspot uncertainty may require +10 K margin on sensor thresholds until resolved
