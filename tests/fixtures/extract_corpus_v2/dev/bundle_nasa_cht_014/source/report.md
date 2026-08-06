# Slide 1 — CHT Model Credibility Check: Avionics Bay Cooling, Rev D

- System: pressurized crew module avionics bay, ducted air over heat-sinked boards with conduction into chassis rails
- Purpose: predict hottest device junction temperature and fin/root heat flow for layout trades and fan sizing
- Tools: Ansys Fluent 2023 R2 (pressure-based steady solver), SpaceClaim prep; post in PyFluent; geometry from CATIA V5 export (Rev G)
- Physics captured: forced convection in air, solid conduction in Cu/Al/FR-4, contact resistances, radiation between internals
- Runs reviewed here: Case IDs ABAY-CHT-RD-021 to -033 (June–July)
- Team: T. Valdez (lead analyst), J. Chao (test), M. Riaz (model setup), reviewed by S. Ng (thermal SME)


# Slide 2 — Scenario, Boundaries, and What’s Not in the Box

- Scope: one bay (0.65 m x 0.45 m x 0.22 m) with 6 cards and two 60 mm blowers; upstream plenum and downstream return idealized as pressure boundaries
- Inlet: total temperature 297–301 K; total pressure 102.2 kPa nominal; turbulence intensity 5%; direction prescribed by duct normal
- Outlet: static pressure 101.3 kPa; backflow suppressed
- Heat loads: per-board maps from ET50 power audit; peak board 72.5 W; total 248.1 W
- Radiation:
  - Earlier runs ABAY-CHT-RD-021..026: surface-to-surface gray, emissivity 0.8 (paint), 0.1 (bare Al), space view-factor to panel treated as adiabatic
  - Later runs ABAY-CHT-RD-030..033: radiative exchange turned off “negligible relative to convection” per note in case file
- Outside wall thermal path: sidewalls tied to cabin air via h=h_cabin=6 W/m^2-K and T=296 K; rails bonded to chassis frames per drawing TH-2219


# Slide 3 — Geometry and Materials

- Solids: Al 6061-T6 for chassis/rails; FR-4 core with 2 oz Cu per side; heat sinks Al extruded fins (10 fins, 20 mm height, 1.8 mm pitch)
- Material data sources:
  - FR-4 conductivity: 0.29 W/m-K in-plane (IPC-4101C), 0.21 W/m-K through-thickness (supplier A)
  - Copper: 385 W/m-K; Aluminum: 167 W/m-K (MatWeb values)
  - Thermal interface material (TIM): pad k=3.2 W/m-K per vendor sheet at 20% compression
- Contacts:
  - Board-to-heat-sink TIM thickness 0.20 mm (assembly intent)
  - Heat-sink-to-rail gap filled with grease; modeled as 0.05 mm film, k=1.0 W/m-K
  - Note: in ABAY-CHT-RD-031, all contacts switched to bonded to “stabilize residuals,” then switched back in -032


# Slide 4 — Solver Setup and Controls

- Flow regime: RANS, k-omega SST; near-wall y+ target <1 on heat-sink fins; scalable wall functions on smooth chassis walls
- Energy equation enabled; compressibility effects neglected (Ma < 0.15)
- Steady-state with pseudo-transient ramping; 2000 iterations typical
- Convergence criteria:
  - Residuals dropped 3 orders (1e-3) for continuity and momentum, 1e-6 for energy claimed in summary
  - BUT several cases show energy residual plateaus at 5e-4 while area-weighted outlet temperature still drifting <0.2 K/500 iters
- Under-relaxation: 0.3–0.7 for momentum; 0.7 for energy in -021..-028; 0.9 for energy in -029..-033 per journal notes


# Slide 5 — Mesh and Independence Checks

- Mesh topology: poly-hexcore in fluid (~8.1M cells), conformal tets in solids (~2.4M); prism layers 12 thick, growth 1.2; min first height 0.05 mm
- Refinement sets:
  - Coarse: 5.2M fluid / 1.1M solid (ABAY-CHT-RD-022)
  - Medium: 8.1M / 2.4M (baseline, -025)
  - Fine: 13.6M / 3.9M (-026)
- Reported outcome (slide pack Rev 1): maximum device junction changed <0.7 C between medium and fine; inferred mesh sensitivity “acceptable”
- Detailed numbers in run logs:
  - Peak junction, board 4 U17: 96.8 C (coarse), 95.9 C (medium), 97.4 C (fine) — non-monotonic shift suggests unresolved near-fin gradients
  - y+ histogram: 65% of fin surfaces at y+ 0.5–1.2; 12% of trailing edges y+ 3–6 in -026 after local remesh was disabled


# Slide 6 — Inputs and Data Lineage

- Fan/Blower performance:
  - Prelim input: 0.12 kg/s at 420 Pa per pair from catalog curve at 12 V (used in -021..-027)
  - Bench measurement with installed duct (Test T-BLOW-07): 0.09±0.01 kg/s at 385 Pa at 11.7 V
  - Model run -033 claims to use measured curve, but case summary still notes m_dot=0.12 kg/s in boundary setup
- Heat load pedigree:
  - ET50 audit rev B: includes derating under idle; however, -029 applies 100% duty on all ASICs “worst case”
  - Transient spikes from FPGA not modeled; average power used over 300 s window
- Material properties:
  - TIM conductivity at operating compression (15%) is 2.6 W/m-K per vendor chart; runs -021..-032 used 3.2 W/m-K


# Slide 7 — Comparison to Bench (Thermal Table TVAC-13)

- Test config: single bay in instrumented wind tunnel, cabin air 295–298 K, fans at 11.7 V, 250 W total, thermocouples at device lids and board edges
- Correlation summary (snapshot from slide pack Rev 1):
  - “Model within 1.5 C of test at all 9 points; flow straighteners not required to capture trend”
- Underlying data from T-BENCH-13-02:
  - Board 4 U17: test 100.9 C; -025 predicts 95.9 C; delta 5.0 C
  - Board 1 U3: test 84.3 C; -025 predicts 87.2 C; delta -2.9 C
  - Rail temperature: test 51.2 C; -025 predicts 46.8 C; delta 4.4 C
- Notes:
  - Runs -030..-033 (radiation off) reduce rail delta to 1.1–1.6 C but increase U17 delta to 6.2–6.8 C
  - Probe locations in the model for U17 were on heat-sink base, not device lid, in -021..-028; corrected in -029


# Slide 8 — Sensitivity and What-Ifs

- One-at-a-time variations on -025 baseline:
  - m_dot -10%: +3.6 C at U17; +0.8 C average boards
  - TIM k -20%: +1.9 C at U17
  - Rail grease thickness +0.05 mm: +0.6 C at rail; +0.4 C at U17
- Two-parameter sweep (DoE-lite) on -032:
  - m_dot ±10%, TIM k 2.6–3.2 W/m-K: U17 shifts 1.1–5.9 C; modest interaction observed
- Contrast with findings in trade-study memo TS-AV-18:
  - Memo states “fan curve uncertainty has minimal effect (<1 C) on peak junction,” assuming linearized h estimate; not borne out by CFD deltas above


# Slide 9 — Numerical Quality Indicators

- Global balances: energy imbalance <0.4% in -025, <0.2% in -026; but increases to 0.9–1.3% in -031 after switching to bonded contacts then reverting
- Monitor points: outlet static temperature flattening; U17 base still drifting 0.15 C at stop in -033
- Pressure-velocity coupling: coupled scheme in -021..-023; switched to SIMPLEC in -024 onward for stability near fan inlets
- Time effects:
  - Although declared steady, -028 introduced 0.05 s physical time step for 40 steps to “stir” recirculation near board 5; final reported temps taken after the stirring phase without further steady reconvergence


# Slide 10 — Process Controls and Traceability

- Case management:
  - All cases under Git LFS at repo thermal/abay/cht, tags v1.3.2–v1.3.7; run scripts in Python with YAML configs
  - Exception: -027 and -031 were launched from GUI; journal shows manual edits; run notes say “overwrote prior -026 directory” before copying results out
- Software QA:
  - Fluent 2023 R2 build 20230620 used; -021 cites “2023 R1” in header but solver printout indicates R2
  - Meshing: Watertight Meshing with custom size functions preserved in -025; -026 fine mesh created with local body sizing that was not checked into repo until after review
- Peer review:
  - SME checklist signed by S. Ng; however, checklist references slide pack Rev 1 which does not include the -030..-033 reruns without radiation


# Slide 11 — Team Experience and Use History

- Analysts:
  - Lead has 12+ years electronics cooling experience; 3 prior avionics bays; recent CHT course (June)
  - Junior analyst 1 year Fluent experience; first time using S2S radiation model
- Prior applications:
  - Similar bay on Project X achieved test-match within 2 C after calibration on TIM thickness and fan curve
  - Current project reused scripts from X; but fan hardware is different (dual blowers vs centrifugal)
- Known model limitations from prior efforts:
  - Recirculation behind tall connectors underpredicted with RANS; LES not feasible for trade timelines


# Slide 12 — Intended Use and Limits

- Current stated context of use:
  - Select fan voltage setpoint and rank layout options for boards 2–5
  - Estimate margin to 105 C junction limit for U17 under cabin temperature excursions 294–302 K
- Declared out-of-scope here:
  - Detailed vibration-induced contact gap variation
  - Transient power spikes shorter than 10 s
- Caveat:
  - Validation test T-BENCH-13-02 at 1 atm; cabin environment is 1 atm flight-like
  - Slide pack Rev 1 also claims “model appropriate for vacuum cases,” but present setup uses only convection and internal radiation; external radiative sink not configured


# Slide 13 — Uncertainty and Confidence

- Reported in slide pack Rev 1:
  - “Overall temperature uncertainty ±2 C (95%) combining input, solver, and test sensor errors”
- Component estimates gathered from notes:
  - Fan flow rate ±0.01 kg/s maps to ±2.5–3.6 C at U17 (from Slide 8)
  - TIM conductivity ±0.6 W/m-K adds ±1.9 C at U17
  - Thermocouple calibration ±0.5 C; placement error ±0.7 C
  - Mesh effect from Slide 5 suggests ±0.8 C non-monotonicity
  - Quadrature of above already exceeds ±4 C (not including contact resistances or radiation on/off choice)
- Conclusion: the quoted ±2 C envelope is inconsistent with propagated contributors


# Slide 14 — Summary of Strengths and Issues

- Strengths:
  - Detailed CHT with solid conduction and air flow captured
  - Geometry fidelity high; heat loads from audited ET50; scripting improves repeatability on most runs
  - Sensitivity work identifies dominant drivers (fan curve, TIM)
- Issues and inconsistencies:
  - Radiation treatment toggled across runs with no documented rationale while claiming “negligible”
  - Mesh independence not convincingly shown; non-monotonic temperature shift at fine mesh
  - Boundary condition mismatch: catalog fan curve used despite available bench data; case notes inconsistent
  - Correlation to bench is mixed; headline “within 1.5 C” conflicts with 4–6 C pointwise deltas
  - Process control gaps: two GUI runs, overwritten directory, late check-in of fine mesh


# Slide 15 — Decision

- Decision by: Thermal Working Group (chair: L. Ortiz), 6 Aug
- Verdict:
  - The CHT model is accepted for early-phase ranking of ventilation options and for estimating relative changes due to board swaps and fan setpoints, subject to re-running with the measured fan curve and consistent inclusion of internal radiation.
  - The CHT model is not accepted for certifying maximum junction temperatures or for establishing absolute margin to limits without additional reconciliation to test and a defensible mesh/solution independence demonstration.


# Slide 16 — Follow-ups and Actions

- Immediate:
  - Re-run baseline (-025) and fine (-026) with measured fan curve and radiation on; fix probe at device lid; hold URFs at energy 0.7; ensure steady reconvergence after any stirring
  - Document contact models and reapply non-bonded contact with mesh refinement near fins/edges
- Before next gate:
  - Perform formal mesh and, if needed, time-step refinement with monotonic sequences; report GCI-style bands in temperature
  - Update uncertainty roll-up; target explicit contributors aligned with sensitivity results
  - Refresh peer review on Rev 2 slide pack including -030..-033 and re-runs


# Slide 17 — Appendix Pointers (not included in this deck)

- Run logs and journals: repo thermal/abay/cht/logs/ABAY-CHT-RD-0xx
- Test data: vault QA/Test/T-BENCH-13-02, sensor map v3
- Geometry: CATIA export Rev G; neutral format STEP ABAY-BAY1-REVG.step
- Scripts: tools/run_case.py; tools/post_u17_delta.py
- Material source PDFs: vendors/TIMx3_datasheet.pdf; IPC-4101C extract
