# CHT Model Readout — 6x SiC Power Module Cold Plate (Pre-Freeze Review)

- What this is
  - Slide pack to brief design freeze gate on the thermal risk for the inverter cold plate
  - Model toolchain: Ansys Fluent 2023 R2 + SpaceClaim, coupled solid-fluid energy with steady RANS
  - Hardware: six 250 W SiC half-bridge modules on Al6061 serpentine cold plate; total dissipated heat ~1.2 kW
  - Coolant: 50/50 water–ethylene glycol (by volume), corrosion-inhibited, nominal inlet set by pump map

- Decision we need to support
  - Can we sign off the plate design without a re-spin given junction temp limit of 105 C at end-of-life fouling?
  - Acceptable safety margin set by systems: ≥5 C below limit at the 95th percentile across expected tolerances

---

## Operating window and stakes

- Intended use envelope in this analysis
  - Volumetric flow: 5–10 L/min at 25 C coolant; backpressure 30–70 kPa across plate
  - Heat load: 1.0–1.2 kW total steady dissipation under worst aligned phase angle
  - Ambient: 20–45 C; single-phase only (no boiling modeled)
- Consequence of getting it wrong
  - Junction over-temp forces derating >8% system power or field retrofit of TIM stack
  - Schedule impact >10 weeks if we miss the window (casting lead time + bench re-qualification)

---

## Physics choices and simplifications

- Governing pieces
  - Incompressible Navier–Stokes and energy in the fluid, Fourier heat conduction in solids
  - Fluid properties: μ(T) from Dow P200 curve; ρ and cp held constant at 1060 kg/m3 and 3.6 kJ/kg-K
  - Solid properties: Al6061 k=167 W/m-K; copper spreader k=380 W/m-K; module base k=320 W/m-K
- Flow regime treatment
  - Baseline setup used k–ω SST with low-Re wall treatment; target y+ ~1, blended laminar where Re local < 2300
  - Note: an alternate run disabled turbulence entirely based on Re_h ~ 920 in straight sections (see Slide 7)
- Heat transfer couplings
  - Module-to-spreader interface represented as thin resistive film (effective thickness method)
  - Radiation neglected inside the sealed housing (<1 C contribution in a spot-check)

---

## Geometry, interfaces, and property pedigree

- Geometry capture
  - CAD imported from Creo Parametric Rev G; tube-to-plate braze fillets simplified to nominal 0.8 mm radius
  - Micro-fins not present; channel height 3.0 ±0.1 mm; 12 passes serpentine
- Contact stack details
  - TIM: silicone grease (MG 8616) nominal k_bulk 3.5 W/m-K, applied thickness 60–120 μm (target 80 μm)
  - Effective interfacial resistance in model:
    - Early scoping used 2.5e-4 m2-K/W at 80 C (from supplier datasheet)
    - Current runs used 1.5e-4 m2-K/W at 80 C (internal ASTM D5470 coupon at 70–90 C)
- Property sources
  - EG/water μ(T) fit from vendor app note; density from CHEMKIN table; cp constant per 35 wt% EG approximation

---

## Loads and boundary conditions

- Fluid-side inputs
  - Inlet: prescribed mass flow rate equivalent to 8.0 L/min; total pressure reference at outlet
  - Temperature at inlet:
    - Modeling basis (Req Doc THM-019): 25 C at pump discharge
    - Bench test condition used for comparison: 30 C setpoint (see Slide 10)
- Heat loads
  - Six uniform heat flux patches on module footprints; 200 W each for baseline; 250 W stress case
  - Copper spreader includes volumetric loss of 8 W (bus bar joule heating) in sensitivity checks

---

## Meshing, near-wall treatment, and grid sensitivity

- Mesh overview
  - Poly-hexcore with prism layers; 12 layers, first cell height 15 μm, growth 1.2; y+ ~0.6–1.2 on walls
  - Solid: conformal tet/prism in copper and aluminum; refinement under module footprints
- Resolution study
  - Three meshes: 3.1M, 9.6M, and 21.0M cells total (fluid+solid)
  - Max module-case temperature moved by:
    - 3.4 C between coarse and medium
    - 1.3 C between medium and fine
  - Estimated grid sensitivity index at medium vs fine: 2.8% on Tmax
- Practical note
  - Due to schedule, production sweeps (Sections 8–10) were executed on the 3.1M grid; spot-check on 9.6M only

---

## Solver controls and coupling quality

- Numerics and stopping rules
  - Second-order schemes on momentum and energy; PRESTO! pressure, coupled solver
  - Residuals driven below 1e-4 for continuity/momentum and 1e-6 for energy
  - Monitors: module hotspot temperature flat to within 0.2 C over last 500 iterations
- Energy balance and interface continuity
  - Global energy imbalance reported <0.5% in baseline 200 W/module case
  - At 250 W/module stress, imbalance of 3.1% observed with same controls; not pursued further due to time

---

## Regime check: laminar vs turbulent handling

- Back-of-envelope
  - Hydraulic diameter in straights: 3.0 mm; mean velocity at 8.0 L/min: ~1.2 m/s
  - Re_h ~ 1600 at 30 C → transitional; local accelerations in U-turns up to Re ~ 2300
- Two modeling paths trialed
  - SST RANS with low-Re walls used for all validation plots
  - A single laminar-only run at 8.0 L/min predicted Tmax lower by 2.6 C vs RANS on the medium grid
- Selection rationale
  - Kept SST for conservatism on secondary flows in bends; no time to run transitional models

---

## Parameter tuning and what was locked

- What we adjusted during model shakeout
  - TIM effective resistance updated from 2.5e-4 to 1.5e-4 m2-K/W after internal coupon arrived
  - Emissivity set to 0.85 in IR post-processing; not used by the CFD
- What we did not touch for validation
  - Flow rate fixed at 8.0 L/min per pump curve at 60% duty
  - Heat load held at calorimeter-measured 1.18 kW (±2%)
  - No case-by-case retuning against individual thermocouples

---

## Bench comparison (single-point check)

- Hardware setup
  - Chiller setpoint 30 C; actual inlet stabilized at 30.2 ±0.3 C
  - Flow 8.0 ±0.1 L/min; pressure drop 54 kPa across the plate
  - 12 TCs (Type T, calibrated ±0.5 C) embedded at 0.5 mm below module bases; IR map for surface sanity check
- Model-to-measurement deltas (medium grid, SST)
  - Mean bias across TC set: +1.8 C (model hotter)
  - Max absolute deviation: 4.1 C at U-turn-adjacent module
  - Percent difference on hotspot: 3.2% relative to rise above inlet
- Notes
  - No per-location correction factors applied
  - Laminar-only variant underpredicts the same hotspot by 0.9 C vs data

---

## Variability study and drivers

- Inputs varied (Latin Hypercube, N=120 on coarse grid)
  - Flow rate ±10% (uniform)
  - TIM thickness 60–120 μm (triangular, mode 80 μm)
  - Heat load ±5% (normal, σ=1.7%)
  - Inlet temperature 25–35 C (uniform)
- Outputs
  - 95th percentile of module-case Tmax: 101 C at 25 C nominal inlet
  - First-order effects (Sobol-like using rank surrogate):
    - TIM thickness dominates (~0.62)
    - Flow next (~0.28)
    - Inlet temperature (~0.10)
- Stress note
  - In a separate sweep at 30 C inlet, P95 Tmax reported at 107 C with the same spread assumptions

---

## Where this model is valid (and where it isn’t)

- Validated use
  - Single-phase EG/water 50/50, 5–10 L/min, inlet 20–35 C, no particulate fouling
  - Module heat flux uniform across footprints; baseplate flatness within spec (≤30 μm)
- Not covered here
  - Boiling onset or vapor entrapment in U-turns
  - Long-term fouling/roughness growth beyond +15 μm equivalent sandgrain
  - Flow maldistribution due to upstream manifold asymmetry

---

## Readout and recommendations

- Readout
  - With SST on the medium grid, model overshoots TC data modestly; grid sensitivity suggests ≤1.3 C residual
  - Under expected spreads at 25 C, P95 Tmax fits under 105 C by ~4 C
  - At 30 C inlet, the sweep indicates P95 above limit (107 C), conflicting with earlier 101 C summary
- What to do next (1–2 week effort)
  - Re-run variability set on medium grid to remove coarse-grid bias
  - Harmonize inlet temperature basis (25 C vs 30 C) with system requirement owners
  - One transitional model trial (γ–Reθ) on the U-turn-heavy geometry
  - Repeat the energy balance check on the 250 W/module case with tightened under-relaxation
- Provisional decision support
  - Proceed to tooling with caution tag: “inlet ≤27 C or flow ≥8.5 L/min” until re-sweep confirms margin

---

## Appendix snapshots (visuals available in the live deck)

- Temperature field
  - Hotspot located at second U-turn; module 3 sees +9.6 C above average
- Velocity vectors
  - Dean vortices at turns sustained; secondary motion captured with SST; laminar run shows weaker recirculation
- Mesh cut through U-turn
  - 12 prism layers hugging walls; transition to hexcore ~0.6 mm off wall; min orthogonality 0.18

---

## Known gaps and deferrals

- No dedicated transitional-turbulence model study completed
- Single validation point only; multi-point (flow, inlet temperature) matrix deferred to M4
- Coarse grid used for the stochastic sweep due to compute slot limits
- Contact resistance measurement limited to coupons; no assembled-stack D5470 on production surface finish yet
