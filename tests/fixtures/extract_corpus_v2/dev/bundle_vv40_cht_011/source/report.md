# CHT credibility snapshot — inverter heat sink design gate (Rev A)

- Program: Rack-mounted 10 kW DC/AC inverter, Series X3
- Model owner: Thermal Engineering, Power Electronics Group
- Toolchain: Simcenter STAR-CCM+ 2022.1; ECAD import via ODB++; CAD via NX 1980
- Date: 2026‑07‑28

## Context of use and decision points

- Purpose of the simulation set:
  - Downselect fin pitch and blower operating point for the inverter cold plate + extruded sink assembly
  - Provide thermal margin estimates for layout freeze at M5
- Measures of interest:
  - Baseplate hotspot temperature (T_bp,max) at 35 C intake air
  - Static pressure rise across sink at nominal flow
  - Airflow required to keep T_bp,max under 100 C at 500 W dissipated
- Acceptance targets for this gate:
  - T_bp,max ≤ 100 C, steady operation at 500 W total heat load
  - Δp across heat sink section ≤ 260 Pa at blower setting S3

## What was modeled

- Physical scope:
  - Conjugate domain: aluminum baseplate (10 mm), extruded fins (25 mm), TIM layer, FR‑4 board surrogate (2 mm) carrying discrete heat sources
  - Flow domain: plenum, heat sink channels, blower outlet duct, and an upstream bellmouth
  - Domain bounds: 300 × 200 × 120 mm around the assembly; velocity inlet and pressure outlet on the flow boundaries
- Heat sources:
  - 20 MOSFET packages arrayed 4×5; per‑device heat 25 W nominal (total 500 W)
  - Heat mapped from ECAD placement; uniform within each device footprint
- Coordinate system and symmetry:
  - Full model (no periodic or symmetry planes) to capture global recirculation patterns

## Operating conditions and loads

- Inlet air temperature: 35 C; uniform profile at bellmouth
- Blower:
  - Part: Delta BFB1012HH; operating mode S3
  - Fan curve digitized from datasheet and converted to mass‑flow vs. pressure rise assuming ρ = 1.15 kg/m^3
  - Achieved operating point in model: 0.045 kg/s at Δp ≈ 248 Pa (medium mesh)
- Heat source allocation:
  - Import from ECAD IDF via ODB++; spot-checked three device coordinates against CAD within ±0.3 mm
  - No time variation; constant power per device

## Material data and contacts

- Materials:
  - Extrusion/baseplate: Al 6061‑T6, k = 167 W/m‑K (assumed constant over 20–120 C)
  - Board surrogate: FR‑4, k = 0.3 W/m‑K through thickness
  - TIM: silicone‑based pad, nominal k = 3.2 W/m‑K at 100 kPa assembly pressure
- Interfaces:
  - TIM modeled as a solid layer with thickness = 100 µm on nominal stackup
  - Metal‑to‑metal interfaces tied (no gaps)

## Meshing approach

- Topology:
  - Poly‑hexcore in flow domain with prism layers on fin and baseplate surfaces
  - Conformal polyhedral discretization in solids
- Near‑wall resolution:
  - 10 prism layers, growth 1.2; first cell ~0.15 mm; maintained across fins
- Element counts:
  - Level 1 (coarse): ~2.0 M fluid cells + 1.1 M solid cells
  - Level 2 (medium, baseline): ~6.1 M fluid + 3.4 M solid
  - Level 3 (fine): ~10.5 M fluid + 5.8 M solid

## Mesh sufficiency check

- Quantity monitored for refinement:
  - T_bp,max at the hotspot device footprint
  - Pressure rise across sink (area-averaged planes upstream/downstream)
- Results:
  - Coarse: T_bp,max = 97.9 C; Δp = 230 Pa
  - Medium: T_bp,max = 95.8 C; Δp = 248 Pa
  - Fine: T_bp,max = 95.1 C; Δp = 252 Pa
- Interpretation:
  - Change (medium→fine) for T_bp,max: −0.7 C (−0.7% of 100 C threshold)
  - Change (medium→fine) for Δp: +4 Pa (+1.6% of 248 Pa)
  - We treated the medium grid as grid‑independent for gate decisions; estimated grid sensitivity on T_bp,max ≈ 1–2 C

## Solution controls and convergence

- Coupling:
  - Steady conjugate solve with segregated flow and energy; implicit under‑relaxation (flow 0.4, energy 0.95)
- Spatial discretization:
  - Second‑order for convection and diffusion in both domains
- Convergence indicators:
  - Residual targets: energy < 1e‑6; continuity and momentum < 1e‑4
  - Monitors flattened: T_bp,max drift < 0.1 C over 1,000 iterations; inlet/outlet mass imbalance < 0.5%
  - Recycled from coarse→medium→fine with interpolation; final solves started from converged previous level

## Sensitivity exploration (what moves the needle)

- TIM stackup:
  - Thickness sweep: 50 / 100 / 150 µm → T_bp,max changes: −4.0 C / 0 / +4.1 C
- Blower performance tolerance:
  - Fan curve scaled ±8% on flow rate → T_bp,max shifts of −1.6 C / +1.7 C; Δp shifts ±20 Pa
- Load distribution:
  - Skewed case: +10% power to central four devices (constant 500 W total) → +2.7 C at hotspot
- Layout perturbation:
  - 2 mm lateral shift of hotspot device row → +0.8 C due to altered channeling
- Combined “pessimistic but plausible”: 150 µm TIM, −8% fan, skewed load → T_bp,max ≈ 102.6 C (medium mesh)

## Results versus gate thresholds

- Nominal (medium mesh):
  - T_bp,max = 95.8 C at 35 C inlet; margin to 100 C = 4.2 C
  - Δp across sink = 248 Pa; within 260 Pa target
  - Predicted mass flow = 0.045 kg/s
- Under combined “pessimistic but plausible” inputs (see above):
  - T_bp,max = 102.6 C → exceeds 100 C; implies tighter control on TIM and blower spec if this case is expected
- Design implication:
  - Fin pitch of 2.5 mm and blower setting S3 meet nominal targets
  - To be robust to the combined case, either reduce TIM thickness to ≤100 µm or increase blower to S4

## Caveats and practical notes

- Geometry simplifications:
  - Board modeled as homogeneous FR‑4 slab; copper pours and vias were not individually represented
  - Small fillets and chamfers on fins (<0.5 mm) suppressed
- Boundary condition construction:
  - Inlet treated as uniform total temperature; upstream pre‑heating not represented
- Contact modeling:
  - TIM treated as constant thickness; pressure‑dependent squeeze not modeled
- Numerical:
  - Steady solution only; no pulsation considered from blower drive

## Decision

- Verdict:
  - Accepted for preliminary heat sink fin‑pitch downselect and blower setpoint recommendations at M5, provided intake air is regulated to 35 C and TIM thickness is held at 100 µm nominal
  - Not approved for use in absolute junction‑temperature prediction for reliability sign‑off or warranty calculations
- Authority:
  - Decision recorded by Lead Thermal Analyst (P. Nguyen) with concurrence from PE Design Manager (L. Ortiz)

## Actions to carry forward

- Capture TIM thickness control in the assembly drawing and manufacturing plan
- Include blower setting S3 in the electrical BOM; hold S4 as contingency
- Extend the model to include copper layer representation on the PCB for the next design iteration
