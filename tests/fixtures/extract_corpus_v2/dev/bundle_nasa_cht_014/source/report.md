# CHT Model Review — Avionics Bay Cold-Plate Cooling
- Project: Guidance Electronics Thermal Upgrade (GETU)
- Model owner: Thermal/Fluids Group, Bldg 239
- Toolchain: ANSYS Fluent 2023R1 + Icepak coupling; CAD from NX 2206; material props via Granta MI 2022
- Purpose: Predict component temperatures and coolant-side deltas for a 250 W avionics stack tied to an aluminum cold plate with a 24 V brushless fan; assess margin vs 85 C part limit

---

## Geometry and Operating Scenario
- Content
  - Two PCBs (10”×8”) with mezzanine cards, standoffs, and an Al 6061 cold plate (5 mm thickness) with serpentine channels
  - Heat spreaders on U3/U7 ASICs and VRMs; TIM2 modeled as a thin solid layer (100 μm)
  - Fan draws ambient air across board surfaces; cold plate rejects to 25 C EGW coolant loop (0.45 kg/min)
- Operating points
  - Nominal: 245 W electrical dissipation (board-wise map; hotspot 18 W at U3), ambient 23±1 C, cabin pressure 1 atm
  - Acceptance test reference: TVAC with nitrogen purge set at 24 C, fan at 18 V (per test log TL-GETU-042)
  - Note: Early scoping assumed steady loads; later EMC test indicated 10 Hz PWM on fan under flight software

---

## Physical Modeling Choices
- Flow/thermal
  - Conjugate heat transfer: solid conduction (boards, cold plate, heat spreaders) + forced convection in enclosure + coolant convection in channels
  - Air side: steady RANS with SST k-ω; buoyancy via Boussinesq (β=0.0033 1/K)
  - Coolant side: segregated energy/momentum; k-ε realizable for pressure drop correlation consistency with vendor curve
- Radiation
  - Surface-to-surface radiation disabled initially (“forced convection dominant”); later sensitivity run turned on Discrete Ordinates with εboard=0.85, εmetal=0.1
- Contact
  - TIM2: nominal 2.5 W/m-K; bolt pattern compressive map applied (effective k scaled 1.3× under standoff)
  - Card-to-standoff conductance: 1200 W/m²-K (from legacy rack; no new coupon test)
- Time dependence
  - Treated as steady; justification: “fan PWM filtered by inertia of flow and cold plate mass” (see Note under Validation for oscillation evidence)

---

## Solver Settings and Numerics
- Spatial discretization
  - Momentum: second-order upwind; Energy: second-order upwind; Turbulence: second-order
  - Gradient: least-squares cell-based; pressure-velocity coupling: coupled scheme
- Stabilization and stepping
  - Residual targets: 1e-5 for all; overall energy imbalance <0.2% (reported on final iteration)
  - For coolant-side initialization, first-order upwind applied for 300 iterations to damp recirculation in elbows, then switched to second-order
- Turbulence wall treatment
  - Air side: automatic wall functions; coolant side: scalable wall functions
  - Near-wall y+ goal stated as 1–5 for SST; precheck reported median y+ 35 on cold-plate air side in Rev B mesh (see Mesh slide)

---

## Discretization and Near-Wall Resolution
- Mesh summary
  - Poly-hexcore in air volume; trimmed hex in coolant channels; conformal interface at solid-fluid boundaries
  - Cell counts: Coarse 3.1 M / Medium 9.2 M / Fine 18.7 M
  - Inflation layers: 8 on air side (first cell 0.15 mm), 12 in coolant (first cell 0.05 mm); growth 1.2
- Convergence indicators
  - GCI based on U3 junction temperature: 0.8% (Medium→Fine), 1.5% (Coarse→Medium); apparent order p=1.9
  - However, refinement not strictly uniform: Fine uses prism layers doubled vs Medium and altered fan shroud fillet (CAD Rev C), complicating GCI applicability
- y+ observations
  - Analyst note on Rev A Medium mesh: y+ 0.8–2.5 on air-side cold plate, 8–15 on board leading edges
  - QA cross-check on Rev B (used for validation run) showed y+ median ~35 at cold-plate air side due to omitted last three prism layers after mesher crash; not re-run before V&V meeting

---

## Boundary Conditions and Inputs
- Air side
  - Fan modeled via pressure jump with vendor curve at 24 V (Delta BFB1012) and 12 CFM at 0 Pa; swirl disabled
  - Inlet temperature set to 20 C uniform in initial runs; later revised to 23 C following lab ambient log
- Coolant side
  - Inlet mass flow 0.45 kg/min, Tin=25 C; turbulence intensity 5%; roughness 10 μm (as-machined)
  - Pressure outlet to loop header at 1.2 bar
- Heat loads
  - Power map from E3 spreadsheet Rev 5: total 245 W; includes 12 W FPGA idle margin
  - Test article dissipated 210–215 W (measured); FPGA margin not energized per test conductor, but not reflected in baseline CFD case
- Gas properties
  - Air properties (constant ρ=1.184 kg/m³ at 25 C) used for all air-side cases; TVAC purge used N2 (μ+7% vs air), not modeled

---

## Material Data and Thermal Contacts
- Metals
  - Al 6061-T6: k(T) curve from Granta MI; Cu spreaders: k=390 W/m-K constant
- Boards
  - PCB orthotropic: in-plane 35 W/m-K (copper planes), through-thickness 1.2 W/m-K
- TIMs and interfaces
  - TIM2: vendor datasheet gives k=3.0 W/m-K at 100 kPa; we used 2.5 W/m-K to reflect assembly average
  - Board-to-standoff: contact conductance borrowed from 2019 campaign (no retest with new anodize)
- Radiation properties
  - When radiation was enabled, emissivity set uniformly; later review suggested conformal coating ε ~0.6, not 0.85

---

## Checks on the Implementation (Code/Setup)
- Model build
  - Geometry and mesh scripted in Fluent Meshing journal; case setup via Scheme macros; param IDs mapped to Power Map Rev 5
- Software pedigree
  - Fluent 2023R1; license features verified; double precision enabled; HPC 64 cores
  - One param sweep (TIM k ±20%) was executed in 2022R2 due to queue availability; results folded into sensitivity plot without note on version change
- Sanity tests
  - Energy balance across solids and fluids within 0.2% on final reported state
  - Fan jump reproduced vendor curve within ±3% at 12 V and 24 V in clean duct model
- Exceptions
  - “Quick turn” scenario: analyst adjusted fan curve to 18 V by scaling the 24 V curve linearly outside the repository; not pushed to Git before validation comparison

---

## Comparison with Hardware Data
- Test description
  - TVAC, nitrogen purge at 24 C; fan commanded 18 V constant; coolant at 25 C, 0.45 kg/min; 6 thermocouples (T3–T8) on component cases; 2 on cold-plate inlet/outlet; IR spot checks for board backside
  - Run time: 2.5 hours to steady; observed low-frequency fan tonal (~8–10 Hz) in accelerometer trace
- Results (CFD vs Test)
  - U3 case: CFD 78.4 C (Medium mesh, radiative off), Test 82.1±0.5 C → −3.7 C difference
  - VRM bank: CFD 74.0 C, Test 72.6 C → +1.4 C
  - Cold-plate ΔT (water): CFD 2.3 C, Test 2.5 C → −0.2 C
  - Board ambient thermistor: CFD 35.2 C (20 C inlet case), Test 31.7 C
- Additional notes
  - In Rev C rerun with radiation on and 23 C inlet, peak delta dropped to 2.1 C at U3; however T12 (board corner) deviated by 12 K vs test; flagged as “sensor lift-off likely”
  - Summary slide claims “within 3% on all key points”; detailed comparison table shows up to 11% at T3 when normalized to ΔT above inlet

---

## Sensitivity, Margin, and What-Ifs
- Knob turning
  - Varied TIM k: ±20% changed U3 by −1.8/+2.0 C
  - Contact conductance at standoffs: ×0.5 increased U3 by 1.1 C
  - Fan voltage scaling 18→24 V (linear curve assumption): −2.6 C at U3; pressure drop decreased 12%
- Uncertainty treatment
  - Monte Carlo (200 samples) on TIM k, contact conductance, and heat load partition gave 95% interval of U3 at 78.4±2.7 C (baseline 245 W, 24 V fan)
  - Radiation and gas species not included in randomization; a separate bounded case with radiation on lowered U3 by 1.6 C
- Operating margin
  - Against 85 C limit: nominal CFD suggests 6.6 C headroom; using test condition (N2, 18 V, 210 W) headroom in chamber was 2.9 C
  - Fan PWM noted in EMC test (10 Hz, 30–100%); not reflected in steady CFD; thermal time constant estimated 200 s, assumed to wash out oscillation

---

## Data Management, Reviews, and Analyst Experience
- Configuration
  - GitLab repo GETU-CHT with tags v0.9–v1.2; mesh Rev B tagged; Rev C mesh generated locally after mesher crash, not yet tagged
  - Power Map Rev 5 in repo; Rev 6 (removes FPGA idle margin) exists in email, not merged
- Peer review
  - Two-person check: numerics and setup reviewed by J. Hall (email approval); mesh QA checklist partly completed (y+ line item left “TBD”)
  - Design review deck states “peer review complete”; checklist spreadsheet indicates “pending verification of near-wall criteria”
- Team skillset
  - Lead analyst: 8 years CHT experience, Fluent certified
  - Meshing performed initially by summer intern; lead corrected negative volumes but kept prism layers count due to schedule

---

## Key Takeaways and Open Questions
- What looks solid
  - Energy balance closure is good; coolant-side predictions line up with measured ΔTwater
  - Overall ranking of hot spots matches test; CFD peak temps are conservative vs test in most locations
- Items needing closure
  - Steady-state assumption vs observed 8–10 Hz fan tone: re-run a transient slice to confirm negligible thermal ripple
  - y+ nonconformance on the air-side cold plate in Rev B validation mesh undermines SST fidelity; confirm with corrected mesh
  - Boundary fidelity: N2 vs air, 18 V vs 24 V fan, and 210 W vs 245 W power map — align CFD with test for a clean validation point
  - Radiation: evidence suggests a few degrees effect; include or justify omission with quantified bound
  - Version control hygiene: fold all “quick-turn” cases into the repo with traceable tags before final sign-off

---

## Proposed Next Steps (2-week sprint)
- Rebuild Medium mesh with enforced prism layers to achieve y+ ≤ 2 on air-side cold plate and ≤ 10 elsewhere; repeat GCI for Rev C geometry only
- Transient test: 10 Hz fan PWM over 600 s with duty cycle 30–100%; monitor U3, VRM temps; verify thermal ripple <1 C
- Validation rerun matching test: N2 properties, 18 V fan curve (nonlinear), 210–215 W measured power map (Rev 6); include radiation
- Quick UQ update: add emissivity spread (0.6–0.9) and nitrogen viscosity ±5% into Monte Carlo
- Close review items: finalize mesh QA checklist; tag all cases v1.3–v1.4; update comparison table to remove inconsistent normalizations

---
