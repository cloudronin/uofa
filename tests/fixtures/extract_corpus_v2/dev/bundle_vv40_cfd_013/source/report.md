# Slide 1 — Project snapshot

- Topic: CFD of a ducted axial fan in an AHU plenum to predict pressure rise and outlet flow uniformity
- Toolchain: Ansys Fluent 23.2 (double precision), ICEM + Fluent mesher poly-hexcore; post in Tecplot 360
- Decision date: needed for equipment selection by 2026-08-20
- What we must decide: Is the 500 mm fan at 1200 RPM sufficient to deliver 3.0 m^3/s at ≥250 Pa total pressure gain with acceptable downstream swirl?
- Model class: steady RANS with rotating frame (MRF) as baseline; transient sliding-mesh spot-check at the design point
- Out of scope this phase: acoustics, structural response, icing/fog, motor thermal modeling

# Slide 2 — What we are checking (metrics and thresholds)

- Quantities of interest
  - Δp_total across fan and diffuser (Pa)
  - Outlet swirl intensity at the grille plane (dimensionless; RMS tangential / bulk axial)
  - Flow non-uniformity index across grille (max-min)/mean
- Acceptance bands for this downselect
  - Δp_total within ±5% at 3.0 m^3/s; within ±8% at 2.0 and 4.0 m^3/s
  - Swirl intensity ≤0.20 at grille plane
  - Non-uniformity index ≤0.35 at grille plane

# Slide 3 — Geometry and simplifications

- CAD basis: Vendor fan CAD (impeller + shroud) dated 2026-05-11; AHU plenum from project Rev C
- Simplifications
  - Omitted motor casing internal cooling vanes; retained external hub geometry
  - Tip clearance set to 1.5 mm per vendor drawing (tolerance ±0.3 mm not explored yet)
  - Downstream grille modeled as porous jump matched to K-factor 3.1 (pressure drop vs velocity quadratic fit)
  - Small fasteners, fillets <2 mm removed; upstream turning vanes retained
- Domain extents: 5D upstream, 8D downstream to minimize reflection; side panels at real plenum walls
- Checked blockage ratio vs test rig: cross-section and grille porosity matched within 2%

# Slide 4 — Physics choices and rationale

- Flow regime: Low Mach (Ma < 0.15), incompressible; density 1.185 kg/m^3 at 25°C
- Turbulence closure: k-ω SST with low-Re wall treatment; selected for separation capture near hub/shroud
- Near-wall approach: y+ targeted ≈1; 12 prism layers, first cell 0.03 mm, growth 1.2
- Rotation modeling: MRF zone enclosing impeller + shroud; steady-state baseline to cover operating map quickly
- No heat transfer modeled; air treated as isothermal
- No empirical tuning; default model constants retained

# Slide 5 — Boundaries and operating conditions

- Inlet: velocity inlet set to meet mass flow targets (2.0, 3.0, 4.0 m^3/s)
  - Turbulence intensity 5% (varied later 1–10% for sensitivity), length scale 0.05 m
- Outlet: pressure outlet at 0 Pa gauge; backflow TI matched to inlet
- Walls: smooth, no-slip; equivalent roughness 0 μm baseline; sensitivity run at 50 μm
- Rotation: 1200 RPM; sensitivity at 1188 and 1212 RPM
- Reference pressure: 101325 Pa; gravity off (orientation not relevant to Δp across fan)

# Slide 6 — Meshing strategy

- Poly-hexcore with local refinement near blade LE/TE and tip gap
- Three meshes for resolution study (cells after MRF interface merging)
  - Coarse: 1.5 million, min Δx near blade ≈0.6 mm, y+ median 2.8
  - Medium: 4.2 million, min Δx near blade ≈0.35 mm, y+ median 1.2
  - Fine: 12.7 million, min Δx near blade ≈0.18 mm, y+ median 0.6
- Interface: conformal poly-hex across rotating/stationary interface; non-orthogonality <70°, skewness P95 <0.26
- Quality checks: negative volumes none; cell size growth capped at 1.35 in stationary regions

# Slide 7 — Resolution study results (design point 3.0 m^3/s)

- Δp_total (Pa)
  - Coarse: 242.1
  - Medium: 253.7
  - Fine: 258.5
- Apparent order from Richardson fit: p ≈ 1.9
- Estimated grid-induced uncertainty (GCI-style with Fs=1.25) between medium and fine: 1.9% on Δp_total
- Swirl intensity at grille
  - Coarse: 0.24; Medium: 0.20; Fine: 0.19
- Conclusion
  - Medium mesh within 2% of fine for Δp, within 0.01 absolute for swirl metric
  - Medium selected for map sweeps; fine retained for final check at design point

# Slide 8 — Convergence behavior and solver controls

- Solver: steady, pressure-based coupled algorithm; second-order spatial schemes (QUICK for momentum)
- Under-relaxation: default for pressure; reduced for turbulent viscosity to 0.6 to stabilize early iterations
- Convergence criteria
  - Residuals below 1e-5 for continuity, momentum, k, ω
  - Monitors: Δp_total flat to within 0.2% over last 2000 iterations; torque on blades stable
- Initialization: hybrid; ramp rotation over first 500 iterations to avoid spikes
- Check on steady vs transient
  - Transient sliding-mesh at design point (2° time step, ~0.00139 s) shows Δp_total = 261.4 Pa vs 258.5 Pa (fine, steady MRF) → +1.1% difference in time-averaged Δp
  - Swirl intensity time-averaged 0.20 (transient) vs 0.19 (steady fine)

# Slide 9 — Model form spot checks

- Turbulence model comparison at design point on medium mesh
  - SST (baseline): Δp 253.7 Pa; swirl 0.20
  - Spalart–Allmaras: Δp 249.2 Pa; swirl 0.22
  - Realizable k-ε: Δp 257.6 Pa; swirl 0.21
- Pattern observations
  - SA under-predicts pressure rise, notable hub separation differences
  - RKE closer to SST for Δp but shows slightly higher swirl
- Choice retained: SST as primary; difference to RKE within 1.5% on Δp but SST better represents tip leakage vortex footprint compared to lab PIV visuals

# Slide 10 — External cross-checks (lab data)

- Reference: AMCA 210 test stand data from vendor (Report F-210-663, 2026-06-07), corrected to 25°C and sea level
  - Uncertainty (coverage ~95%): Δp ±1.5%, flow ±1.0%, RPM ±0.3%
- Comparison of QoI at three duty points (fine mesh at design, medium elsewhere)
  - 2.0 m^3/s: CFD Δp 274.9 Pa vs test 294.0 Pa → −6.5%
  - 3.0 m^3/s: CFD Δp 258.5 Pa vs test 267.0 Pa → −3.2%
  - 4.0 m^3/s: CFD Δp 212.3 Pa vs test 219.0 Pa → −3.1%
- Notes
  - Largest miss at low-flow where stall onset begins; steady RANS expected to be less reliable
  - No direct lab metric for swirl; indirect check via downstream traverse shows similar skewness trend

# Slide 11 — Sensitivity snapshots

- Inlet turbulence intensity (1%, 5%, 10%) at design point
  - Δp shifts by −0.8% (1%) to +1.5% (10%) relative to 5% baseline
  - Swirl intensity varies between 0.18 and 0.22
- Surface roughness (equiv sandgrain 50 μm) on blades and shroud
  - Δp decreases by 0.6%; swirl unchanged within 0.01
- Tip clearance ±0.3 mm around 1.5 mm nominal
  - +0.3 mm → Δp −2.1%; −0.3 mm → Δp +1.7%
- RPM ±1%
  - Δp follows ~quadratic with speed; +1% RPM → +2.0% Δp

# Slide 12 — Data pedigree and run management

- Test data provenance
  - Full report includes rig schematic, calibration sheets for pressure taps and flow nozzle; received as PDF and CSV; units and corrections consistent with our setup
- CFD run tracking
  - Case/mesh pairs and monitors archived with run notes; meshes hash-checked; figures scripted in Tecplot macro for repeatability
- Hardware
  - Medium mesh solves: ~4.5 hours to converge on 16 cores (Intel Xeon Gold 6338), peak RAM 22 GB
  - Fine mesh: 15.2 hours on 64 cores, peak RAM 68 GB

# Slide 13 — Where this leaves the decision

- For the 3.0 m^3/s design point
  - Predicted Δp_total within −3.2% of test; resolution uncertainty ~2%; model-form spread across RANS closures ~3%
  - Swirl intensity at grille 0.19–0.20 (meets target ≤0.20)
- Across operating map
  - Miss grows at 2.0 m^3/s (−6.5% vs test); acceptable per ±8% band but flagged as less robust
  - 4.0 m^3/s within −3.1% vs test; acceptable
- Recommendation
  - Fan model is acceptable for selection with a 5% margin added to required Δp at design point and caution near low-flow stall

# Slide 14 — Known limits and to-dos (if we extend scope)

- Limitations acknowledged
  - Steady RANS near stall under-predicts pressure rise vs test; transient unsteadiness not fully captured
  - Porous-jump grille approximates loss only; does not replicate vane-induced swirl recovery
  - Single temperature, no compressibility; fine for Ma < 0.15
- Next steps if needed
  - Expand sliding-mesh coverage to low-flow case
  - Explore tip-clearance tolerance range more broadly (manufacturing scatter)
  - Acquire targeted PIV downstream to directly quantify swirl metric
- Not pursued now to stay on schedule: acoustic prediction, blade roughness mapping, rotating hub thermal effects
