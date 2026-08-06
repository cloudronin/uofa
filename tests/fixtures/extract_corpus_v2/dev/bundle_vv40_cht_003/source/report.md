# Slide 1 — EV Battery Cold Plate CHT Model: Credibility Readout (M8)

- System under study
  - Aluminum serpentine-channel cold plate (AA6061-T6), 2 mm cover thickness, brazed to baseplate
  - 50/50 ethylene glycol-water coolant; nominal inlet 0.85 kg/s, 35°C; pack dissipates 4.2 kW steady
  - TIM: silicone pad, nominal 0.6 mm, k = 3.0 W/m·K (vendor sheet), Cpk = 1.33 on thickness
- Decision supported
  - Go/no-go for DV freeze on plate geometry and manifold sizing
  - Acceptance criterion: <8°C cell-to-cell spread, peak cell <48°C at 40°C ambient (wind-off)

---

# Slide 2 — Where this model is supposed to be trusted

- Operating window claimed
  - Coolant: 0.6–1.0 kg/s, 30–50°C inlet, Re_channel ≈ 5,500–13,000
  - Heat load: 3.5–5.0 kW uniformly distributed over 0.18 m² footprint
  - Mounting torque 1.8–2.2 N·m per fastener; contact grease used in builds 2–3
- Stretch regions flagged
  - Transients >60 s and ambient crossflow >1 m/s not represented
  - Dry-out and off-nom glycol mix (≤40/60) not in test envelope
- Note: Slide 9 compares to bench tests at 0.8 and 1.0 kg/s; one profile run at 0.6 kg/s exists but was excluded from statistics due to "sensor drift"

---

# Slide 3 — Modeling choices (physics and tools)

- Software: Ansys Fluent 2023 R2 CHT, pressure-based coupled solver; double precision
- Fluid side
  - Turbulence: realizable k-ε with enhanced wall treatment; buoyancy off
  - Properties: temperature-dependent 50/50 EG from NIST; density via Boussinesq (β from 40°C)
- Solid side
  - Conduction in plate and cover; anisotropy neglected
  - Thermal interface modeled via equivalent thin layer (thickness 0.6 mm, k = 2.6 W/m·K in baseline)
- Thermal radiation disabled (emissivity variations across cells are small per IR data)
- UDFs
  - Inlet temperature ramp and pump curve; custom expression for heat map across modules

---

# Slide 4 — Geometry handling and simplifications

- Full serpentine modeled (no symmetry) with manifolds; seals, bolts, and bead features omitted
- Coolant manifold fillets kept; micro-roughness not represented
- Channels: CAD includes 0.25 mm corner radii from broach; mesh resolves radii with 4–5 cells
- Contact pressure distribution not simulated; uniform pressure assumed across TIM patch
- Note: An early run used porous-jump approximation for fins (deprecated; not used in final), but remains referenced in Slide 9 table

---

# Slide 5 — Mesh and near-wall resolution

- Mesh summary (poly‑hexcore with prism layers)
  - Coarse: 5.6M cells; Medium: 11.9M; Fine: 24.7M; prism layers = 15, growth 1.2, first cell target y+ ≈ 0.8
  - Average y+ reported <1.0 on Medium; hotspot region y+ 1.2–1.5
- Independence check
  - Peak cell temperature change: Medium→Fine: 1.9°C; Coarse→Medium: 2.3°C
  - Pressure drop change: Medium→Fine: 1.8%; Coarse→Medium: 5.6%
- Contradiction to note
  - Slide 6 residual plots show wall y+ band 3–7 for 1.0 kg/s case (post-processor overlay), which does not align with the <1.0 claim above
  - Fine grid run used reduced prism count (10 layers) due to memory limits; may explain mismatch

---

# Slide 6 — Numerics and stopping criteria

- Steady-state with pseudo-transient relaxation (Courant 50→5 ramp)
- Convergence gates
  - Residuals for energy to 1e-8, momentum to 1e-5, k/ε to 1e-5 (typical ~1800 iterations)
  - Monitored quantities flat: outlet temperature <0.01°C/500 iters; Δp <2 Pa/500 iters
- Exceptions
  - 0.6 kg/s case terminated at energy residual 3e-6 due to queue limit; ΔT still drifting 0.04°C/500 iters
  - One Fine grid run accepted at 1e-4 on ε due to instability after UDF update
- Solver settings consistency
  - All runs: second-order upwind for scalars; PRESTO pressure; least squares cell-based gradients
  - However, Slide 9 Figure A shows a 0.8 kg/s Medium run with first-order upwind (an oversight during sensitivity sweep)

---

# Slide 7 — Code and setup sanity checks

- Code-level confidence
  - Fluent 2023 R2 with hotfix HF2; vendor verification notes for CHT energy coupling reviewed
  - UDF suite: 7 functions with unit tests (pytest), 94% line coverage
  - One benign compiler warning (implicit cast) persists; impact analysis says "none" but not independently reviewed
- Problem-level checks
  - Manufactured-source test (2D conduction) run to confirm source term sign conventions; error L2 <0.2%
  - Closed-loop energy balance:
    - Net heat into solid vs. out through coolant within 0.7% on Medium; 1.8% on Fine (postprocessing interpolation issue suspected)
  - Simple geometry back-to-back against analytic laminar plate exchange shows 2.5% deviation at Re ~1500 (outside intended turbulent regime)

---

# Slide 8 — Inputs and boundary data

- Coolant properties
  - NIST polynomials used; viscosity clipped below 20°C to avoid divergence
  - Sensitivity run with constant properties at 40°C changes Δp by 9% and peak T by 0.6°C
- Inlet conditions
  - Flow rate per pump curve UDF; mass flow 0.78–1.02 kg/s per test, uncertainty ±2%
  - Temperature: 34.5–35.5°C during tests; model used 35.0°C
- Heat map
  - Uniform 4.2 kW in baseline; alternative pattern +15% on center modules used in one validation run
- Interface resistance
  - TIM modeled as 0.6 mm at k=2.6 W/m·K (adjusted from vendor 3.0 W/m·K due to compression tests)
  - Contradiction: Slide 9 states "no tuning" vs. M7 lab note shows k lowered post-hoc to match IR at 1.0 kg/s by ~12%; thickness also set to 0.5 mm in Run V-07 though BOM says 0.6 mm

---

# Slide 9 — Bench comparison (what matches and what does not)

- Test rig
  - Calorimeter loop, Coriolis meter (±0.5%), 12 T-type thermocouples across cell tops (±0.5°C), FLIR A6750 IR (emissivity 0.93 assumed)
  - Builds: B2 (no grease), B3 (thin grease), both with torque wrench 2.0 N·m
- Results overview (selected)
  - 0.8 kg/s, 35°C in, uniform heat:
    - Model–Test peak cell ΔT: +2.3°C (model hotter), spread within 6.9°C (both)
  - 1.0 kg/s, 35°C in, uniform heat:
    - Model–Test peak cell ΔT: −0.4°C (model cooler), spread within 7.1°C model vs. 8.0°C test
  - 0.8 kg/s with center bias heat:
    - IR hotspot: model −8% vs. test
- Caveats and inconsistencies
  - Slide 4 early porous-jump fin model appears in one "sanity" comparison table with a 4.5% better Δp match; not used elsewhere
  - "No parameter tuning" stated in summary; however, TIM conductivity reduction and thickness change were introduced between V-05 and V-07 prior to the 1.0 kg/s comparison
  - One Medium grid case used first-order upwind (Slide 6); matches test within 1.5°C yet is not methodologically consistent

---

# Slide 10 — What drives outputs (sensitivity and uncertainty)

- Screening
  - Morris method on 8 inputs (m_dot, T_in, TIM k, TIM t, k_Al, heat map skew, emissivity, manifold roughness)
  - Top three by influence on peak cell T: TIM thickness, flow rate, heat map skew
- Quantification
  - Latin hypercube intended at N=200; actually executed N=60 due to cluster queue limits
  - Reported 95% interval on peak cell T at 1.0 kg/s: ±1.1°C (from N=60)
  - Assumed inputs independent; but compression tests suggest TIM k and t are correlated (thinner pads test at higher k_meas)
- Contradiction
  - Main deck states "500-sample Monte Carlo"; only 60 runs archived in Perforce and referenced in appendix; 500 appears to include earlier coarse-grid surrogate runs not used in final statistics

---

# Slide 11 — Does the physics regime line up?

- Dimensionless groups (nominal)
  - Re_channel ≈ 9,000–12,000; Pr ≈ 40–60; Pe ≈ 3.6e5; fully turbulent assumption defensible
- Junction Boiling Number << 1 (no phase change expected)
- Wall treatment check
  - Claimed y+ <1 supports enhanced wall treatment; see Slide 5 vs. Slide 6 mismatch in actual y+ band on Fine
- Thermal contact
  - Uniform pressure assumption may underplay edge cooling; torque-to-pressure mapping not included

---

# Slide 12 — Software practice, traceability, independence

- Configuration control
  - Perforce depot //cooling/plateA/v23R2; tags M6, M7, M8; input decks and meshes hashed
  - Run logs auto-captured; two runs missing machine logs due to Slurm outage (M8-W12)
- Peer review
  - Two design reviews held; mesh setup and post-processing scripts reviewed by a different analyst
  - Test–model comparison compiled by same engineer who owned the rig; limited separation
- Toolchain quality
  - Fluent release notes checked; no known defects in CHT coupling for R2 HF2
  - UDFs lack formal regression tests across Fluent point releases; one run (Fine, V-08) compiled with -O0 due to crash under -O2

---

# Slide 13 — What we are not covering (and why)

- Not included in current model
  - Transient drive cycles and pump speed control logic (next phase: M9)
  - Ambient crossflow and radiation exchange with pack lid (planned CFD–CHT co-sim)
  - Degradation of TIM over life (aging tests ongoing; data expected Q3)
  - Manifold deformation under pressure (FEA coupling deferred)
- Not enough time/data
  - Full 500-sample UQ on Medium grid; cluster allocation shortfall
  - Independent replication of IR emissivity calibration; camera only available one day

---

# Slide 14 — Bottom line and asks

- Readout against decision needs
  - Peak cell temp under nominal: model within 0.4°C of B3 test at 1.0 kg/s; spread criterion met in model, borderline in test
  - Pressure drop within 3% of measurements at 1.0 kg/s; at 0.8 kg/s, mismatch 6–8%
- Credibility qualifiers
  - Mesh independence not fully demonstrated (Medium→Fine delta 1.9°C; y+ inconsistency)
  - Evidence of post-hoc adjustment to TIM properties despite "no tuning" statement
  - UQ sample size short of plan; correlation between TIM k and thickness ignored
  - Mixed-order discretization used in one validation run (first-order), yet included in summary
- Recommendation
  - Conditional proceed for DV freeze limited to 0.8–1.0 kg/s, 35–40°C inlet; require:
    - Re-run Fine grid with 15 prism layers to close y+ gap; document GCI-like estimate
    - Lock TIM properties to independent compression/guarded-hot-plate data and rerun comparisons
    - Execute additional 140 UQ samples or justify statistical sufficiency; incorporate k–t correlation
    - Independent reviewer to own test–model comparison package
- Risks if unaddressed
  - Underestimated peak temps by ~2°C in corners; torque variability may widen spread beyond 8°C in field
