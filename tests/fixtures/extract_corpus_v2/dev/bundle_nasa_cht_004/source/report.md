To:    CHT IPT Lead, Power Avionics Thermal Subsystem
From:  J. Kim (Thermal-Fluids), D. Ortega (Test), S. Patel (SQA)
Date:  06 Aug 2026
Subj:  Credibility status for the Cold Plate CHT model supporting PSB-2 design gate

Purpose and decision context
- Model predicts worst-case junction temperature and coolant pressure drop for the 6-die MTRX-500 power module cold plate used in the Node-3 avionics rack. Pass/fail rule for PSB-2: Tj,max ≤ 85 C at inlet 20 ± 0.6 C, flow 0.12 ± 0.004 kg/s, and 540 W total heat.

What we modeled and key assumptions
- Full conjugate heat transfer: aluminum 6061-T6 baseplate, copper spreader, TIM layers, stainless fittings, and 50/50 water–glycol coolant with temperature-dependent properties.
- Steady-state only; transient checks show time constants > 300 s, while decision criteria are steady limits. No boiling expected; operating pressure 2.3 bar(g) with local wall Ts — Tw,min margins > 30 C.
- RANS with k–ω SST, low-Re treatment, y+ < 1 at all wetted walls; radiation neglected (ΔT to surroundings small; view factors near zero in enclosed rack).

Geometry, loads, and boundary conditions pedigree
- CAD pulled from PDM Rev C; fillets < 0.5 mm suppressed except at TIM/wall contacts; O-ring grooves retained.
- Heater map from electrical spec (6 dies, 60/100/80/120/100/80 W). Load split validated by bench electrical measurements (±2%).
- Inlet flow 0.12 kg/s and 20 C from JSC Thermal Loop spec; flowmeter is Micro Motion CMF025 (±0.5% of rate); thermocouples Type T, NIST-traceable, ±0.3 C (1σ).
- TIM conductivity measured via laser flash (mean 3.4 W/m-K, COV 18%); contact resistance estimated from clamping torque and vendor data, cross-checked via a coupon test (Rc = 1.1e-4 m2-K/W ± 30%).

Software, numerics, and checks
- STAR-CCM+ 2023.3, double precision; in-house scripts for setup/post in Python 3.11. Git LFS repo tag coldplate-cht_v1.7; all meshes, journals, and reports archived.
- Code confidence: weekly regression suite (15 cases) includes manufactured solutions for heat conduction and lid-driven cavity; no deltas this quarter.
- Solution quality: three meshes (4.2M, 8.6M, 17.3M cells). Max die-surface temperature changes: M1→M2: 1.6 C; M2→M3: 0.5 C. GCI-style estimate for Tj,max = 1.8%. Iterative residuals < 1e-6; mass/energy balance within 0.1%/1.2%.
- Solver settings locked in environment module file; runs are bitwise repeatable on Pleiades (ICX) and on lab cluster (EPYC) within 0.2 C (non-bitwise due to BLAS).

Comparison against hardware
- Purpose-built fixture at GRC Thermal Lab with identical flow path and fixture stack-up. 26 thermocouples on die caps and cold plate; IR camera (FLIR A655sc, emissivity painted 0.95±0.02).
- At 0.12 kg/s and 540 W, average of three steady tests: Tj,max,test = 81.9 C (σ = 0.5). Model predicts 83.7 C on matched sensor locations (+1.8 C bias); RMSE across all sensors 2.1 C. Pressure drop test 24.6 kPa vs model 25.9 kPa (+5.3%).
- Cross-check at off-nominal 0.10 kg/s: bias increases to +2.6 C; still within pre-set ±5 C band for acceptance of correlation.

Uncertainty and sensitivity
- Propagated uncertainty with 200-point Latin hypercube over: flow (±3%), inlet T (±0.6 C), TIM k (±20%), Rc (±30%), heat split (±10%), turbulence intensity (1–5%). Includes numerical spread from mesh study as a fixed additive variance.
- 95% interval for Tj,max at nominal spec: 83.7 C median; [81.9, 86.1] C. Exceedance probability for 85 C is 0.28 under spec distributions.
- Sobol analysis: TIM properties (first-order 0.41) and flow rate (0.37) dominate. Contact resistance and heat split secondary; turbulence intensity negligible.

Scope of use and margins
- Intended use limited to 0.10–0.14 kg/s and inlet 18–22 C. This overlaps the test matrix fully for flow and partially for inlet T (tests at 19.5–21.0 C). Extrapolation for 18 C assessed with additional runs; model trends align with Dittus-Boelter within 3%.
- Decision margin: baseline configuration violates the 85 C limit in 28% of plausible conditions; with TIM upgrade to 5 W/m-K (available COTS), exceedance probability drops below 5%.

People, process, and independence
- Analysts: J. Kim (PhD, 12 yrs CHT), peer review by M. Rios (not on design team), and test lead D. Ortega (15 yrs instrumentation). Two-person rule used for BCs and units; pre-run checklist signed.
- External eyes: independent review by the TX40 Analysis Advisory Team on 18 Jul; action items (radiation check, Rc coupon) closed 01 Aug.
- All artifacts linked to requirements in DOORS; checklist aligns with our VVUQ plan dated 10 May.

Computing environment and QA
- Runs on Pleiades ICX nodes (256 cores, 8 h wall per design point). Containers (Apptainer) pin OS and libraries; SHA256 of images recorded. License and solver patch level frozen at 2023.3.1.
- Post-processing scripts compare virtual sensor points to test locations; automated unit checks and a residual sanity gate. Energy closure criterion 98–101% enforced in CI.

Limitations and next steps
- No boiling model; if program considers higher heat fluxes, separate model needed. Radiation remains neglected; spot check showed <0.4 C effect.
- We will execute 3 more validation points at 18.0 C inlet to remove residual extrapolation and re-baseline the UQ; due 23 Aug.
- Recommendation: proceed to PSB-2 with a requirement to adopt higher-k TIM or increase minimum flow to 0.13 kg/s; both are within subsystem trades.

Bottom line
- The CHT model is technically sound, traceable, and repeatable. It reproduces lab data within ~2 C and quantifies the chance of violating the thermal limit. Present configuration lacks comfortable margin; remedies are identified and analyzed.
