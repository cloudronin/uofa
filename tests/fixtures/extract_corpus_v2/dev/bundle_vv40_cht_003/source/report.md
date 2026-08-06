# Slide 1 — Context and purpose
- Project: 2U telecom line card, 400-mm board with ducted airflow; main heat source is a 55 W ASIC under an extruded aluminum heat sink
- Analysis type: steady conjugate heat transfer (air + solid conduction) with forced convection
- Decision gate: Is the current heat sink and TIM stack-up viable for EVT, with a 35 C inlet-mass-flow environment spec?
- What we need from the model:
  - Upper bound on junction temperature at 55 W and 0.08–0.09 kg/s air mass flow
  - Guidance on fin pitch strategy before ordering tooling
  - Indicative pressure drop across the card for fan sizing

# Slide 2 — What the model actually computes
- Tools: Ansys Fluent + SpaceClaim; pre-processing in Ansys Meshing; post in CFD-Post and Python
- Physics toggles:
  - Conjugate: copper spreader + TIM + aluminum heat sink + FR-4 + air domain
  - Turbulence: stated as k-omega SST with low-Re wall treatment and wall y+ ≈ 1
  - Thermal radiation: initially said “neglected due to low ΔT,” but result exports show ε=0.8 and radiation contributing 4–6% of total heat removal
- Solver: steady RANS; SIMPLEC; second-order spatial, bounded central for energy
- Contact interfaces: two thermal contact resistances (die-to-lid and lid-to-sink), both modeled as thin layers

# Slide 3 — Geometry and fidelity choices
- Full 3D of heat sink and immediate fins; adjacent cards represented as porous baffles (K, C2 from fan-curve fit)
- TIM layer included as a 50 μm volume; GPU package lid as copper
- Fan modeled upstream as a uniform-velocity inlet; swirl and hub blockage not represented
- Vent holes in chassis panel blanked out “for now”; effect assumed negligible at <3% flow bypass
- Symmetry NOT used (unsymmetrical duct inserts), but downstream cable bundle omitted

# Slide 4 — Operating conditions and loads
- Base case:
  - Inlet mass flow: 0.085 kg/s at 35 C (RH not modeled)
  - Outlet: 0 Pa gauge
  - Board power map: ASIC 55 W, nearby regulators 7 W total (applied as volumetric heat sources)
  - Inlet turbulence: slide 2 notes 3% intensity; setup sheet in the run folder states 5%; one sensitivity run varied 10%
- Heat sink emissivity:
  - BOM: black anodized (ε ≈ 0.86); early runs used ε=0.2 (clear aluminum) per a default in the material library

# Slide 5 — Material data provenance
- Copper: k = 385 W/m-K (constant)
- Aluminum (6063-T5): k = 201 W/m-K
- FR-4: k⊥ = 0.3 W/m-K, k∥ = 1.2 W/m-K; density and Cp per IPC-2152
- TIM:
  - First two runs used vendor flyer value 3.5 W/m-K at 25 C
  - Procurement update notes final part is 1.8 W/m-K at 60 C; no temperature dependence entered in model
- Air: Sutherland viscosity, temperature-dependent Cp; density via ideal gas

# Slide 6 — Numerical controls and “sanity checks”
- Residuals target: 1e-5 for energy, 1e-4 for others; however, job logs show several runs stopped at 1e-3 on continuity “due to wall-clock limit”
- Under-relaxation tuned to damp oscillations near fins; pressure correction 0.3; energy 1.0
- Code-level checks:
  - Conduction cube with imposed heat flux reproduced analytical ΔT within 0.3%
  - Laminar pipe heat-transfer case within 1.5% of Nusselt correlation at Re=1200
- Reproducibility harness: Python script (runner.py) launches parameter sweeps; CSV output archived with SHA-256 stamps

# Slide 7 — Grid and near-wall resolution
- Three unstructured meshes with prism layers:
  - Coarse: 3.1M cells, 6 prisms, first-layer 0.05 mm, y+ reported 25–60 on fin surfaces
  - Medium: 6.4M cells, 10 prisms, first-layer 0.01 mm, y+ reported 8–20
  - Fine: 12.9M cells, 14 prisms, first-layer 0.004 mm, y+ mostly 1–5
- Heat sink base-to-air average HTC change:
  - Coarse→Medium: +2.9%; Medium→Fine: +1.7%
- Reported “mesh independence within 2%,” yet base slide stated “wall y+ ≈ 1 for all runs”; the coarse run contradicts this
- Time step: not applicable (steady), but a spot-check URANS with Δt=0.001 s ran 0.2 s physical time to assess unsteadiness; averaged HTC within 1.1% of steady

# Slide 8 — Contact resistances and joints
- Die-to-lid and lid-to-sink as explicit layers:
  - TIM thickness: 50 μm (drawing); assembly note allows 30–80 μm range
  - Spreader-to-sink flatness ignored; no micro-gap distribution
- Bolt preload assumption: uniform, 0.4 mm compression on TIM from M2 screws (no structural coupling)
- Quick perturbation: TIM thickness 80 μm increased ASIC ΔT by 6.4 K (medium mesh)

# Slide 9 — Bench measurements for cross-checking
- Test rig: open-loop blower set to 0.085 kg/s (Coriolis meter), inlet air 35.2 C
- Instrumentation:
  - 6x TCs: on sink base, fin tip, PCB near ASIC; IR camera (FLIR A655sc) with matte tape for emissivity control
  - Calibration sheet claims ±0.5 C absolute; lab log later notes ±2 C after refit and emissivity not re-verified
- Observations at 55 W:
  - Max sink base TC: 83.5 C; IR spot on fin tip: 75–78 C
  - Pressure drop across card: 140 Pa (pitot). A separate log (Run 07) lists 110 Pa with the same blower setting
- Comparison to model (medium mesh, ε=0.86):
  - Predicted sink base: 81.9 C (−1.6 C from TC)
  - Predicted Δp: 126 Pa (between the two measured values)

# Slide 10 — Sensitivity and margins explored
- One-at-a-time sweeps around baseline:
  - Inlet temperature: +5 C → +4.7 C at sink base
  - Mass flow: −10% → +5.9 C at sink base
  - TIM k: 3.5→1.8 W/m-K → +7.8 C at sink base
  - Emissivity: 0.2→0.86 → −1.1 C at sink base (but radiation was said “off” earlier)
- Combined worst-case (−10% flow, +5 C inlet, TIM 1.8): predicted base 96–98 C
- No formal propagation of uncertainty; tornado plot used qualitatively

# Slide 11 — Toolchain traceability and environment
- Solver build listed in slides: Fluent 2023 R2, double precision
- Job metadata in the run folders show:
  - Baseline run: 2023 R1, single precision on a workstation (16 cores)
  - Fine-mesh run: 2023 R2, double precision on the cluster (64 cores)
- Mesh files named with date but not the git commit of the geometry; geometry stored in PDM but link not embedded in case files
- Post-processing scripts versioned; input decks partially versioned (BC .jrn files missing for two runs)

# Slide 12 — What we did not include (and why)
- No fan swirl or hub blockage modeling: vendor did not release blade CAD; assumed negligible impact on fin HTC at current Reynolds number
- No thermal interface roughness modeling: would need profilometer data; deferred to DVT
- No aging of TIM or surface oxidation: outside EVT window
- No moisture effects on FR-4: not expected to change k materially at 35 C

# Slide 13 — Results snapshot
- Baseline prediction (medium mesh, ε=0.86, TIM=3.5 W/m-K, 0.085 kg/s, 35 C):
  - ASIC junction estimate: 92–94 C (die-to-lid conduction path included via thin layers)
  - Heat sink base: 81.9 C; fin tip: 74.2 C
  - Card Δp: 126 Pa
- Alternate with procurement TIM (1.8 W/m-K) lifts junction by ~8–9 C
- URANS spot-check did not materially change averages, but showed 10–15% fluctuation in local HTC near leading fin edges

# Slide 14 — Consistency check (findings that don’t line up)
- Wall treatment vs y+: claimed wall-resolved y+≈1 on “all runs,” but coarse/medium meshes report y+ up to 60/20 respectively
- Radiation: slides say “neglected,” yet result tables allocate 4–6% of heat removal to radiation and emissivity sweeps affect temperature
- Inlet turbulence: described as 3% in the overview, 5% in the setup sheet, 10% in one sensitivity; no clear basis for the chosen value
- TIM conductivity: 3.5 W/m-K used in baseline, but procurement selected 1.8 W/m-K; temperature dependence not applied
- Solver version/precision: text cites R2 double, baseline appears to have been run in R1 single precision; not re-run for consistency
- Bench data uncertainty: calibration sheet ±0.5 C contrasts with lab note ±2 C and uncorrected emissivity on IR; pressure drop logs disagree (110 vs 140 Pa)

# Slide 15 — Strengths and gaps
- Strengths:
  - Conjugate modeling of key solids; anisotropic FR-4
  - Three-level mesh check with <3% change in HTC from medium→fine
  - Bench cross-checks roughly bracket model predictions for Δp and temperatures
  - Automated run harness and partial configuration control
- Gaps/risks:
  - Inconsistent physics toggles (radiation on/off) and wall treatment claims
  - Property pedigree for TIM unsettled; biggest driver in sensitivity
  - Mixed solver versions/precision undermine repeatability
  - No structured uncertainty propagation; only local sensitivities

# Slide 16 — Applicability statement
- Suitable for:
  - Ranking heat sink concepts and fin pitch variants at EVT
  - Estimating pressure drop to within ~10–20% for fan selection short-listing
- Not suitable for:
  - Final sign-off of junction temperatures against component limits
  - Warranty/reliability calculations, or compliance documentation
  - Capturing effects of fan swirl, contact unevenness, or TIM aging

# Slide 17 — Recommendations
- Re-run baseline and fine meshes in the same solver build (2023 R2, double), confirm y+<1 where low-Re wall treatment is claimed
- Lock emissivity and radiation choice: either document “off” with justification or include consistently
- Update TIM to 1.8 W/m-K with temperature dependence; bracket thickness per assembly tolerance
- Standardize inlet turbulence (5% with length scale from duct hydraulic diameter) and document rationale
- Repeat bench run with re-validated sensors; resolve Δp discrepancy; record IR emissivity method

# Slide 18 — Decision
- Verdict by Thermal Review Board (M. Chen, M. Trotta, M. Singh), 2026-08-05:
  - The current CHT model is accepted for preliminary heat sink screening and estimating trends at EVT, subject to documenting the selected inlet turbulence and fixing the TIM property to the procured part
  - The model is not accepted for absolute junction temperature predictions used in final sign-off, derating, or compliance reports until the inconsistencies on radiation, solver versioning, and wall treatment are resolved and revalidated
