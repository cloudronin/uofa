# CHT model readout — Avionics Rack Fin Stack in ECS Duct

- Purpose
  - Predict air-side temperature rise and board junction temperatures for the ARA-22 avionics module using a finned heat sink in a 120 mm x 80 mm duct
  - Support go/no-go for thermal margin at cabin inlet temps 22–40 C and aircraft altitude 0–10 kft
  - Toolchain: Ansys Fluent 2023 R2, steady RANS with solid-fluid coupling

---

## Geometry and heat map

- Hardware
  - Extruded aluminum heat sink (6061-T6): base 6 mm, fins 25 mm tall, 1.0 mm thick, 2.0 mm pitch, 300 mm length
  - Duct segment length modeled: 0.55 m (0.1 m upstream plenum, 0.35 m downstream)
  - Printed circuit assembly bonded via graphite pad to base, planform 220 x 150 mm
- Material properties at 35 C
  - Aluminum: k = 167 W/m-K (datasheet 155–180 W/m-K)
  - Graphite gap pad: nominal k = 5 W/m-K; thickness 100 µm ± 25 µm
- Power distribution
  - Total board heat = 230 W
  - Non-uniform map: three hotspots at 38 W, 31 W, 27 W in 25 x 25 mm areas, remainder uniform
  - For the first two runs, a uniform heat flux was used to accelerate meshing (now deprecated)

---

## Operating envelope and inputs

- Airflow and conditions
  - Fan module: Delta BFB1012H (OEM variant); fan curve digitized from vendor PDF Rev C
  - Modeled mass flow = 0.48 kg/s at 95 kPa, 30 C; turbulence intensity 5% at inlet
  - Tests T2–T4 reported 0.60 kg/s after fan replacement; See correlation slide for handling
- Thermo
  - Air: ideal gas, temperature-dependent Cp
  - Humidity: neglected (treated as dry air)
  - External surfaces of duct adiabatic, except heat sink base exchanging with air
- Limits
  - Stated avionics board allowable: 80 C max at worst-case ambient 40 C

---

## Physics choices and rationale

- Flow and heat transfer
  - RANS k-omega SST with low-Re near-wall treatment
  - 15 prism layers, first cell height for y+ ≈ 1.2; inflation growth 1.2; total thickness ~3.5 mm
  - Conjugate conduction in heat sink and base, solid-fluid coupling with tight under-relaxation
- Radiation
  - Initial scoping suggested radiative exchange <1% of total heat; radiation disabled in baseline
- Contacting and roughness
  - Interface modeled as thin solid (graphite pad), uniform thickness 100 µm
  - No explicit fin roughness; hydraulically smooth assumption

---

## Numerical setup and grid

- Mesh
  - Poly-hexcore in fluid (~2.4 M cells), hex-dominant in solid (~0.8 M cells) → Baseline 3.2 M
  - Coarse: 1.1 M; Fine: 9.6 M (fluid 7.9 M with 25 prism layers)
  - Max skewness 0.82; average 0.23; non-orthogonality 14 deg average
- Solver
  - Steady coupled solver, pseudo-transient ramp with dt = 1e-3 s for start-up
  - Energy and momentum residuals driven below 1e-5; mass flow imbalance <0.3%
  - Monitors: three board diode proxies and air outlet temperature

---

## Progress on mesh independence

- Three-level refinement
  - Board hottest spot (HS1) temperature:
    - Coarse: 73.9 C
    - Baseline: 72.8 C
    - Fine: 72.4 C
  - Monotonic trend; difference baseline→fine = 0.4 C (0.55% of rise), taken as acceptable for PDR
- Extrapolation
  - Richardson-based estimate suggests asymptotic HS1 ≈ 72.1–72.3 C; observed within 0.3 C
- Note
  - A prior exploratory run used scalable wall functions at y+ ≈ 30; those results were discarded

---

## Solver behavior notes

- Convergence oddities
  - While residuals fell below 1e-5, HS1 monitor drifted 0.5 C over the last 500 iterations on the fine mesh
  - Switching from segregated to coupled energy on the fine mesh altered outlet ΔT by ~2.1 C
- HPC execution
  - 192 cores, 36 GB RAM footprint; one job preempted and restarted from autosave (no divergence indicated)
- Under-relaxation
  - Momentum 0.5, energy 0.95, turbulence 0.5; tighter coupling required to suppress oscillations near the fin tips

---

## Benchmarks and code confidence checks

- Sanity checks
  - Heated pipe with constant wall heat flux: predicted Nusselt 4.42 vs. theory 4.36 at Re ≈ 10,000 (1.4% high)
  - Flat plate turbulent heat transfer (isothermal plate): Stanton correlation within 2.1% at Reθ ≈ 1600
- Conjugate test case
  - Aluminum plate with internal heater, air cross-flow: initial runs deviated ~6% on Nu due to wall y+ mismatch; rerun with y+ ≈ 1 brought error to 2.8%
- Software state
  - Fluent 2023 R2, double precision, second-order schemes; no user-defined scalars
  - A hotfix applied between coarse and fine runs (build 2023R2.1 → 2023R2.2) to address energy equation linearization

---

## Hardware test correlation

- Wind tunnel calorimetry (WT-03)
  - Controlled inlet T = 30.0 ± 0.2 C; flow 0.49 ± 0.01 kg/s (dry air)
  - Measured UA implied outlet ΔT = 3.81 C at 230 W; model predicted 3.71 C (2.6% low)
  - Board thermistor at HS1: 73.9 C test vs. 72.8 C model (1.1 C low)
- Installed bench (IB-02) in avionics bay
  - Ambient 34.5 ± 0.7 C; measured flow 0.60 ± 0.03 kg/s (post-fan swap, 50% RH reported)
  - Model-to-test gap in HS1 widened to 7–12 C depending on sensor; condensation risk flagged in log though model used dry air
- Calibration note
  - To match WT-03 within 0.5 C, an analyst trialed contact conductance equivalent to 12,000 W/m2-K; baseline deck uses 8,000 W/m2-K from coupon tests

---

## Sensitivities and uncertainty treatment

- Parameter sweep
  - Gap pad thickness 75–125 µm: HS1 shifts +1.9/−1.4 C
  - Fan curve ±7% flow: HS1 shifts −2.1/+2.5 C; outlet ΔT scales roughly inversely with ṁ
  - Aluminum k 155–180 W/m-K: HS1 within ±0.6 C
- Monte Carlo (200 samples)
  - Inputs: pad thickness (normal, µ=100 µm, σ=15 µm), ṁ (normal, µ=0.48 kg/s, σ=0.03), TIM k (uniform 4.5–5.5 W/m-K)
  - 95th percentile HS1 at 76.2 C for ambient 35 C
- Radiative effects
  - A trial with discrete ordinates and ε = 0.86 on black-anodized fins changed HS1 by +1.5 to +2.3 C depending on view factor setup
  - Radiation remains OFF in baseline results presented earlier

---

## Data provenance and process control

- Configuration control
  - Model and meshes in Git LFS (repo: tps-avx-cht), branches tagged wt03_baseline and ib02_eval
  - Run metadata tracked in MLflow with environment hashes
- Exceptions
  - One case directory labeled “final_final3.cas.h5” exists outside repo; used for a presentation plot only
  - Contact resistance values appear in both W/m2-K and m2-K/W in separate notes; conversions double-checked in current deck
- Human review
  - Cross-check performed by S. Patel on solver settings; peer sign-off pending for IB-02 comparison
  - A junior analyst temporarily enabled radiation for a subset of runs without updating the case register

---

## Applicability and caveats

- Where the model is strongest
  - Dry-air conditions, 0.45–0.50 kg/s, uniform upstream profile; fin conduction and air-side convection dominant
  - Predicting outlet ΔT and ranking changes across fin geometries
- Where extra caution is needed
  - Post-fan replacement regime (≥0.58 kg/s) and humid conditions; inlet turbulence and psychrometrics not captured
  - Sensitivity to contact conductance is nontrivial; installation torque and pad squeeze not parameterized
- Margins
  - Using baseline deck: HS1 remains <75 C at 35 C ambient and 0.48 kg/s
  - Program requirement slide elsewhere calls 80 C absolute max; see recommendation

---

## Open items before CDR

- Reconcile IB-02 discrepancy
  - Update model to 0.60 kg/s and include humidity to assess density/heat capacity changes
  - Instrument audit: two thermistors read 3–4 C higher than co-located RTDs
- Firm up contact interface
  - Confirm pad thickness under clamp via micro-CT or pull-apart; adopt measured thickness in deck
- Clean up physics toggles
  - Decide on radiation treatment; if included, adopt consistent emissivity and view factors
- Mesh and convergence
  - Address HS1 late-iteration drift on fine mesh; consider tighter coupling or pseudo-transient marching
- Documentation
  - Eliminate stray “final_final3” case; ensure all figures traceable to repo commits

---

## Recommendation snapshot

- For PDR-level risk screening
  - Use the baseline results for dry-air, 0.48–0.50 kg/s cases; predicted margins to 75 C appear defensible
- For design freeze or flight rules
  - Defer until IB-02 alignment is resolved and contact conductance is substantiated by measurement
  - Provisional operational cap: 75 C at HS1 until humid-air behavior and higher flow regime are modeled or tested
- Next steps (2 weeks)
  - Rerun with 0.60 kg/s, include humidity and radiation as a bounding case
  - Perform a short unsteady run to check for fan-induced periodicity; document impact on junction temps
  - Complete peer review and update case register with final toggles
