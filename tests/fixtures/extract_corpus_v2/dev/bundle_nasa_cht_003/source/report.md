# Slide 1 — CHT model scope and decision context
- Project: liquid-cooled avionics module for Orion-B rack; heat rejected to 50/50 EGW loop
- Purpose: predict board-level hot spots and cold plate ΔT at 120–160 W total dissipation for design go/no-go before EVT
- Decisions supported:
  - Select fin geometry (straight vs. wavy microchannels) and TIM stackup
  - Size pump setpoint to keep worst-case component case temp under 85 C at 28 C bay ambient
- Toolchain: Ansys Fluent 2023R2 (pressure-based, segregated), Ansys Mechanical for solid conduction; fully coupled via CHT solver

# Slide 2 — Physical model at a glance
- Conjugate setup: RANS for coolant + energy eq.; conduction in Al 6061 cold plate, Cu heat spreaders, PCB stack
- Radiation neglected for baseline; later sensitivity assumed ε=0.8 on top cover (see Slide 10)
- Coolant: 50/50 EGW, IAPWS properties; density and viscosity from polynomial fits vs. T
- Heat sources: 6 components (Q1–Q6) mapped as volumetric heat gen; nominal total 120 W, skewed 35:20:15:15:10:5 percent

# Slide 3 — Geometry and simplifications
- Full-length cold plate solved; manifold elbows included; quick-connects dropped (pressure loss accounted by lumped Δp)
- PCB modeled as homogenized orthotropic solid (kxx=18, kyy=9, kzz=0.8 W/m-K); graphite heat spreader approximated isotropic at 300 W/m-K
- TIM: 150 μm bondline; fillets not modeled; contact set as “perfect” for baseline, later a thermal jump added (Slide 6)
- Enclosure: top cover present for conduction path; side panels treated as adiabatic in baseline (but test had free convection; see Slide 8)

# Slide 4 — Numerics and turbulence modeling
- Solver: steady-state, second-order upwind for momentum/energy; SIMPLEC; pseudo-transient enabled (default 0.5 s)
- Turbulence: k-ω SST with automatic wall treatment
  - Target y+ < 1 on fins; measured y+ spanned 5–60 on baseline coarse grid
  - A later note states “enhanced wall functions acceptable for y+ ~30–100,” which conflicts with the initial low-Re intent
- Coupling: two-way CHT with tight thermal coupling (under-relax 0.5), residuals to 1e-5, energy to 1e-8; mass imbalance <0.2%

# Slide 5 — Grid development and stability checks
- Three CFD meshes for fluid domain; conformal imprint to solids:
  - G1: 2.4M cells; min fin cell 0.25 mm
  - G2: 6.8M cells; min fin cell 0.12 mm
  - G3: 14.2M cells; min fin cell 0.07 mm
- Monitors (Q=140 W, Tin=20 C, 2.0 L/min), predicted peak case temperature:
  - G1: 78.6 C; G2: 75.8 C; G3: 74.9 C
  - Slide note says “<1% change from G2→G3,” yet 75.8→74.9 C is 1.2% on peak, 1.4% on ΔTmax; also G1→G2 is 3.6%
- Final design runs used G2 “to stay within overnight walltime,” despite G3 showing non-negligible shift in hotspot magnitude
- Solid conduction mesh: 1.1M tets; local refinement under Q1/Q2; no explicit element distortion report, but one solver log flags “max skewness 0.92” on a fillet

# Slide 6 — Materials and thermal interfaces
- Metals from ASM data: Al 6061-T6 k=167 W/m-K; Cu k=387 W/m-K; PCB through-thickness measured 0.9 W/m-K at 25 C
- TIM property treatment:
  - Early runs assumed kTIM=5.0 W/m-K uniform, no pressure dependence
  - Vendor sheet for the chosen pad shows 3.1 W/m-K at 100 kPa, dropping to 2.4 W/m-K at 50 kPa; assembly torque targets 0.5 N·m suggest closer to 50–70 kPa
  - Later sensitivity added a 0.25 K·cm²/W contact resistance, but bill of materials calls for phase-change film, not pad, on Q1/Q2
- Specific heat and viscosity tables for EGW came from CoolProp; an older input deck references “water at 25 C” for one correlation run

# Slide 7 — Loads and boundary settings
- Inlet: mass flow to match 2.0 L/min; nominal Tin=20.0 C; outlet pressure fixed at 0 Pa gauge
- Heat loads:
  - Electrical team notebook (04/13) lists 135 W total at high-mode, with Q1 duty cycling ±15%
  - CFD deck uses 120 W constant, uniform per-component splits for “comparability across design options”
- Ambient:
  - Baseline assumes adiabatic side panels and top cover; test article sat in 28 C still air; later a 6 W/m²-K external convection was added ad hoc
- Conflicting note: Test rig data sheet cites Tin=23.1±0.3 C; the correlation slide labels Tin as 20.0 C for the same run ID (EVT-CP-07)

# Slide 8 — Bench setup for correlation
- Coolant loop: chiller setpoint 20 C; Coriolis meter on supply; PD pump; bay ambient 28±1 C
- Instrumentation: 10× K-type thermocouples on board; 2× RTDs on inlet/outlet; FLIR A655sc IR on board topside (emissivity tuned 0.92)
- Flow conditions: target 2.0 L/min; logged 1.86–1.91 L/min over 30 min dwell in the first series; a later slide cites “2.0 L/min flat” without the drift band
- Mounting: silicone pad under top cover to avoid shorts; not in model; introduces extra conduction path

# Slide 9 — Comparison with hardware
- Aggregated metrics at the “same” nominal point (Tin ~20–23 C, Q~120–135 W, 2 L/min):
  - Outlet temperature rise: model 2.9 C (G2), test 3.1–3.4 C
  - Peak case (Q1): model 76–78 C (depending on grid), IR 72–74 C after emissivity tuning
  - Hotspot location: model underestimates lateral spread at Q2 by ~6 mm; likely tied to anisotropy simplification
- Slide caption claims “within 2 K on critical nodes,” whereas the table footnote shows Q1 offset of 4.6–6.2 K when test Tin=23.1 C is used as the reference
- Transient warm-up:
  - CFD steady state reached in ~700 iterations using pseudo-transient; test shows 6–8 min to stabilize; a later transient run (50 s physical) was used “to aid solver stability,” then reported as steady-state

# Slide 10 — Sensitivity and uncertainty exploration
- DOE: one-at-a-time sweeps on Tin (20→28 C), flow (1.5→2.5 L/min), kTIM (2.4→5.0 W/m-K), and board kzz (0.6→1.2 W/m-K)
  - Peak temp sensitivity: −3.2 C per 0.5 L/min; +1.1 C per +2 C Tin; +2.8 C between kTIM=2.4 and 5.0
- A slide header states “200-sample Monte Carlo with Latin Hypercube,” but only 20 points are plotted; seed and PDFs not archived
- Radiation:
  - Baseline stated “ignored”; sensitivity later reports “including surface-to-ambient with ε=0.8 reduces peak by 1.3 C,” yet side panels remained adiabatic
- Uncertainty bounds:
  - Final chart shows ±2 C total uncertainty without decomposition; an earlier draft allocates ±1.5 C to inlet temp alone

# Slide 11 — Software QA, versioning, and team experience
- Solver build: Fluent 2023R2 HF2; Mechanical 2023R1; material library file “matlib_2023-02-07.json”
- Change control:
  - Material library updated on 05/02 to “matlib_2023-05-02.json” (TIM and PCB revisions); some correlation runs predate the update
  - CAD rev B switched fin fillet radius; mesh G2 for “final” used rev A fluid volume (mismatch acknowledged)
- Reviews and training:
  - Internal peer check on setup checklist (04/28); no independent replication due to schedule
  - Analyst has 6 years CFD background; first time applying full CHT workflow on EGW mixture
- Automation:
  - Journal files archived; but two “manual fix” steps are noted for boundary relabeling; reproducibility could be affected

# Slide 12 — Applicability, gaps, and next steps
- Current model intended for 1.5–2.5 L/min, Tin 20–28 C, total load 100–160 W
- Known limitations:
  - Assumed isotropic graphite; neglected connector conduction and cover pad
  - Mixed wall treatment vs. low-Re intent; y+ not consistently near 1 on all fins
  - Bench conditions not matched exactly (Tin, flow drift, ambient convection)
- Planned actions before CDR:
  - Re-run G3 on CAD rev B; enforce y+ < 2 everywhere; add external convection and cover pad
  - Align loads with electrical high-mode (135 W, duty cycle) and log Tin at RTD during runs
  - Replace single-value “±2 C” band with budgeted contributions; publish seeds and PDFs if Monte Carlo retained
- Decision note:
  - Despite mismatches, ranking of fin concepts remained consistent across all runs; absolute margins to 85 C spec are slim (2–6 C depending on assumptions)
