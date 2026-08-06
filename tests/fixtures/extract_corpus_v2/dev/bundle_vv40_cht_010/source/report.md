Project: EV Inverter Cold Plate CHT Model — Credibility Assessment Report
Version: R0.9
Date: 2026-08-06
Prepared by: Thermal Systems Group, Apex e-Motors

1. Background and decision context

The racing variant of Apex’s 3-phase SiC inverter (AIM-800R) uses a brazed copper microchannel cold plate integrated under the power module. For the upcoming endurance events, program management will authorize track use if the model predicts that the maximum device temperature stays below 80 °C when the ambient coolant loop is at 35 °C and the DC bus is fully loaded. This report documents evidence that the conjugate thermal-fluid simulation used for that decision produces results reliable enough for that purpose.

What the model needs to answer:
- Primary: temperature rise from coolant inlet to the hottest point in the module base under steady full-power operation.
- Secondary: associated flow penalty across the cold plate to confirm pump sizing.

Key operating point of interest (agreed with Controls and Vehicle Integration on 2026-07-12):
- Coolant: 50/50 water-ethylene glycol (WEG), 35 °C inlet, 6.0 ± 0.1 L/min total cold plate flow.
- Heat generation: 200 W per half-bridge (400 W per module) continuous; spatially concentrated over two SiC die islands.
- Acceptance threshold: worst-case baseplate temperature ≤ 80 °C with 3 °C headroom at nominal inputs.

The model will not be used to qualify thermal cycling life or transient warm-up; only the steady thermal map and pressure drop at the above condition are in scope.

2. System overview and model description

Hardware
- Cold plate: oxygen-free copper, 3.0 mm thick base with a 10 x 24 array of 0.6 mm wide x 1.2 mm deep straight channels, fin thickness 0.4 mm; serpentine manifold both ends.
- Heat spreader: 6061-T6 aluminum lid (5.5 mm) bonded to module; TIM1: indium solder layer nominal 30 µm.
- Power module: two SiC die groups per phase leg; each group footprint 10 x 25 mm; estimated uniform surface heat flux by layout.

Computational domain
- Fluid: inlet plenum, all microchannels, outlet plenum.
- Solids: copper plate (channels + base) and aluminum lid up to the TIM interface; die-level details are lumped into a uniform flux applied on two pads at the copper base interior surface (conservative for spreading).

Physics and numerics
- Conjugate heat transfer between WEG and copper/aluminum solids; steady-state solution.
- Flow regime: channel Reynolds number ranges 1,100–1,600 at the target flow for WEG at 35 °C. Local turbulence was assessed with a preliminary transitional k-ω run; predicted intermittency remained negligible along most of the channel length. For production runs we used laminar flow with energy equation enabled; this choice is justified further below.
- Properties: WEG density and viscosity evaluated at 35 °C; thermal conductivity and heat capacity at 35 °C. Sensitivity to temperature-dependent properties was checked.
- Radiation and boiling are neglected (surfaces remain below 90 °C; dull copper emissivity ~0.2; driving temperature differences are small).
- Solver/tool: Ansys Fluent 2023 R2, double-precision, segregated pressure-based solver, second-order spatial schemes, coupled energy with under-relaxation 0.9.

Boundary conditions
- Inlet: 6.00 L/min total mass flow rate, temperature 308.15 K.
- Outlet: static pressure = reference (0 Pa gauge).
- Walls in fluid: no-slip; symmetry at side planes of the packaged mid-section to minimize model size (full-width obstruction effects captured by including both end plenums).
- Heat input: two rectangular patches on the copper floor under the die footprints, 200 W each, uniform q" = 0.8 MW/m².
- External heat loss: external faces of the aluminum lid insulated (justified by enclosure foam and small external convection, see Section 6).

Geometry fidelity
- Microchannel dimensions and manifold details derived from STEP provided by Manufacturing Rev B2. Corner fillets approximated as sharp; burrs and roughness excluded in this phase due to missing metrology.

3. Evidence that the numerical solution is stable and grid-independent

Convergence practice
- Residuals for continuity, momentum, and energy reduced below 1e-6. Surface monitors of baseplate hotspot and outlet temperature flattened to <0.01 K change over 2,000 iterations; mass imbalance <0.1%.

Grid refinement and interpolation of key outputs
- Three nested tetra/prism meshes with boundary layers in the channels. Near-wall resolution ensured y+ < 0.3 assuming laminar; first cell height 12 µm; 12 layers with growth 1.2.
- Cell counts: M1=2.1M, M2=4.8M, M3=9.6M.
- Quantity tracked: maximum copper base temperature under either die, copper-averaged pad temperature, and total pressure drop between inlet and outlet plenums.
- Differences between M2 and M3:
  - Baseplate Tmax: 74.7 °C (M2) vs 74.2 °C (M3), change 0.5 °C (0.7%).
  - Δp: 29.0 kPa (M2) vs 28.4 kPa (M3), change 0.6 kPa (2.1%).
- Estimated grid-induced uncertainty using a Richardson-style approach with refinement ratio r ≈ 1.42 yielded 95% confidence bounds of ±0.8% (temperature) and ±2.5% (pressure drop) at M3.

Time dependence screening
- A transient run from a uniform 35 °C field with constant heat input used Δt = 0.01 s; the system approached steady after ~8.5 s with no sustained oscillations. Final steady fields matched the steady solver predictions within 0.1 K and 0.2 kPa.

4. Software checks relevant to this application

We executed two lightweight reference problems to guard against setup or solver option errors that would matter for laminar CHT:
- Straight mini-channel (L=50 mm, D_h=1.0 mm) with constant wall heat flux. Predicted Nusselt number at x/D_h = fully developed region converged to 4.36 ± 0.03, within 0.7% of the analytical limit for laminar constant q" boundary condition.
- Thermal conductivity sanity check: pure conduction through a copper slab with imposed heat flux and known thickness returned temperature drops within 0.2% of hand calculations using k=385 W/m-K.

These checks do not replace exhaustive code certification; they are targeted to the physics and numerics used here.

5. Why the chosen physics is appropriate

- Flow regime: Using WEG at 35 °C, μ ≈ 3.5 mPa·s and ρ ≈ 1,060 kg/m³. With hydraulic diameter 0.86 mm and bulk velocity ~1.7 m/s per channel, Re ≈ 1,380. Inlet and exit expansions could create localized unsteadiness, but the channel core remains in the laminar-to-transitional gray zone. A trial run with transitional k-ω SST (γ–Reθ) resulted in <0.5 K change in hotspot temperature and 0.9 kPa increase in Δp compared to laminar at M2 mesh, which is within the overall acceptance window for our decision. For conservatism on pressure drop, the laminar prediction is slightly lower than transitional; we address this with experimental comparison results in Section 7.
- Material properties: Comparing constant-property runs to temperature-dependent WEG (polynomial fits from DowTherm data) altered Tmax by 0.2 K and Δp by 0.4 kPa at the 35–80 °C range. Given the small thermal gradients, the simplification is acceptable for the decision.
- Radiation and external convection: Estimated external heat loss coefficient on the aluminum lid in the enclosure is ~3 W/m²-K; with a ~10 K difference, this removes <3 W. Neglecting it is conservative for internal hotspot prediction because it slightly raises predicted temperatures.

6. Boundary condition provenance

- Inlet temperature and mass flow: Derived from vehicle loop design point and confirmed with lab equipment (Bronkhorst mini CORI-FLOW M15, ±0.1% RD; PT100 class A at manifold inlet, ±0.15 K).
- Heat input magnitude and area: Electrical load tests on a spare module at 400 V, 200 Arms/phase indicated 386–410 W total dissipation distributed approximately evenly across the two die regions. We used 400 W total and applied uniform flux over the measured die footprint rectangles, which slightly overestimates localized flux because real spreading begins within the die stack.
- TIM and solder layers: For this phase, these are captured as equivalent heat flux boundary condition on the copper interior rather than explicit thin layers. The decision to lump them is supported by separate 1D conduction estimates that suggest <1.2 K drop across combined TIM1+solder at 400 W, which is small relative to the coolant-side temperature rise.

7. Comparison with bench measurements

A purpose-built flow loop was used to test a Rev B2 cold plate mated to a dummy module with embedded heaters and instrumentation.
- Loop details: 50/50 WEG at 35.0 ± 0.2 °C maintained by PolyScience PD15; volume flow 6.00 L/min measured by the same Bronkhorst unit used for input setting; pressure transducers at inlet/outlet flanges (Keller PAA-33X, ±0.25% FS on 0–100 kPa).
- Thermal instrumentation: Six 0.5 mm Type T thermocouples swaged into 0.6 mm holes from the underside of the copper reaching within 0.3 mm of the die footprints; one at a non-heated reference location. IR camera (FLIR A655sc) used for qualitative field checks after black paint emissivity calibration, not for quantitative acceptance.
- Test condition: 400 W total heater power (four resistive mats beneath each die footprint area, 200 W each), sustained for 30 minutes until temperature slopes <0.02 K/min.
- Measured results at steady:
  - Highest copper thermocouple: 75.1 °C; mean of the two peak-adjacent thermocouples: 74.7 °C.
  - Inlet–outlet pressure difference: 29.9 kPa.
- Modeled results at the same settings (M3 mesh, laminar):
  - Predicted max copper base temperature: 74.2 °C.
  - Predicted Δp: 28.4 kPa.

Agreement:
- Temperature: model is 0.9 K lower than the highest thermocouple (1.2% relative to 75.1 °C). Considering the 0.5 K estimated conduction gradient between thermocouple tip and copper interior surface and the ±0.3 K thermocouple uncertainty, the bias is within the combined band.
- Pressure drop: model is 1.5 kPa lower (5% of measured Δp). This is consistent with neglecting surface roughness and mild entrance losses; adding a 15 µm equivalent sand-grain roughness in a sensitivity run increased Δp by ~1.2 kPa with negligible temperature change.

No special adjustments were made to the model between prediction and comparison; the same inputs listed in Section 6 were used during both phases.

8. Influence of key inputs and uncertainty bounds

To understand how input scatter would affect the decision variable, we explored one-factor perturbations and a small Monte Carlo run around the nominal case.

Local sensitivities (evaluated about the baseline)
- Coolant flow rate: ±5% change results in ∓1.3 K hotspot temperature change and ±2.4 kPa in Δp.
- Heat load (total 400 W): ±5% results in ±3.9 K hotspot temperature change; negligible effect on Δp.
- Inlet temperature: ±0.5 K shifts hotspot approximately ±0.5 K (near-unity gain).
- Copper thermal conductivity (±5%): ∓0.4 K on hotspot.
- Channel height (±10 µm, i.e., ±0.8%): approximately ∓0.6 K on hotspot and ±0.9 kPa on Δp.
- Assuming laminar vs transitional treatment: +0.8–1.0 kPa on Δp and +0.1–0.2 K on hotspot (from the trial in Section 5).

Monte Carlo screening
- 300 samples with Latin hypercube draws on the above parameters using normal distributions truncated at ±3σ: flow (σ=1%), inlet temperature (σ=0.1 K), heat load (σ=1.5%), copper k (σ=2%), channel height (σ=5 µm), and a Bernoulli flag for roughness presence (20% chance of 15 µm equivalent roughness).
- Resulting 95th percentile hotspot temperature: 76.1 °C; 99th percentile: 76.8 °C.
- Resulting 95th percentile Δp: 31.2 kPa.

Numerical discretization contribution
- From Section 3, add ±0.5 K (95% bound ~±0.6%) to thermal results and ±0.7 kPa to Δp as solution resolution effects.

Combining measurement and model sources (root-sum-square with independence assumption), the overall 95% bound on predicted hotspot at the decision point is approximately ±1.7 K relative to the baseline 74.2 °C. This leaves ~4.1 K margin to the 80 °C threshold.

9. Suitability for the intended decision

- The question asked of the model is limited: steady hottest point temperature and flow penalty at a single duty point.
- The physical features controlling the answer (laminar microchannel convection and conduction through a copper base) are well represented in the toolchain used.
- Confidence in numerics is supported by residual behavior, grid study, and a check that transient artifacts do not persist.
- Agreement with hardware data at the condition of interest is within 1.2% on temperature and 5% on pressure drop, with the latter explainable by known, unmodeled roughness and entrance effects. The error directions are conservative relative to the thermal limit (model tends slightly low on Δp and low on temperature by <1 K).
- Input variability and fabrication tolerance studies show that the 95th percentile temperature remains at least 3.2 K below the acceptance threshold for the tested configuration.

Given these points, we judge the model reliable enough to support the release decision for track testing under the specified inlet temperature and flow rate, with the caveats listed below.

10. Limitations and deferred items

- Roughness and burrs: No surface profilometry is available for Rev B2 channels; we treated the walls as smooth. Sensitivity suggests Δp could be underpredicted by ~1–2 kPa; effect on temperature is minor. We recommend metrology on production parts and, if roughness is consistently above 10 µm, inclusion in future models.
- Manifold maldistribution: The current model includes both end plenums and preserves the serpentine path but assumes uniform inflow at the plenum entrance. If the upstream T-fitting skews flow by >10% between manifold legs, local temperature nonuniformity could increase. A full-assembly simulation including the inlet tee and hoses is not in this phase’s budget.
- Die-level heat map: We used a uniform heat flux over each die group footprint. Layout-based nonuniformity (bond wire losses, gate driver islands) could produce ±1–2 K local variation. A fine-scale map can be integrated when available from the electrical team.
- External heat rejection: The insulated lid assumption is valid for the enclosed inverter. In bench tests with the lid exposed to lab air, small additional cooling would act in the safe direction.
- Property data scope: WEG properties were taken at 35 °C. If future operation at 15 °C inlet is contemplated, viscosity increase may push local Reynolds numbers lower and raise Δp; the laminar model remains applicable but acceptance margins should be rechecked.

11. Methods details

Meshing
- Workflow: SpaceClaim defeaturing, Ansys Meshing with CutCell for plenums and swept prisms in channels; inflation layers grown from channel walls, growth rate 1.2, target n+ ≤ 0.5 at the wall for laminar resolution.
- Mesh quality: minimum face angle 23°, skewness < 0.72, aspect ratio < 120 in boundary layer; no negative volumes.

Solver controls
- Pressure–velocity coupling using SIMPLE with body-force-weighted pressure; second-order upwind for momentum and energy; pseudo-transient with CFL ramp 1.0 → 50.0 over 1,000 iterations.
- Under-relaxation coefficients: momentum 0.7, pressure 0.3, energy 0.9.

Postprocessing
- Hotspot extraction performed on the copper–fluid interface patch; area-weighted statistics used for die pad averages; pressure taps at the same plenum locations as the lab sensors.

12. Results synopsis

- Baseline prediction at 6.00 L/min and 400 W:
  - Max copper base temperature: 74.2 °C.
  - Average copper over die patches: 72.8 °C (left), 73.1 °C (right).
  - Coolant outlet temperature: 38.1 °C (rise 3.1 K).
  - Pressure drop: 28.4 kPa.
- Grid independence indicated minimal additional lowering of temperature with finer meshes; Δp stabilizes to within ±0.6 kPa between the two finest.
- Validation with hardware supports the hotspot prediction to within 1 K and Δp within 1.5 kPa.

13. Risk-based interpretation

The governing risk for this decision is overheating the SiC module during track operation, which could trigger derating and a DNF. The model’s prediction sits ~5.8 K below the limit with an estimated ±1.7 K 95% uncertainty, i.e., the upper credible value is ~75.9–76.2 °C depending on combination of inputs. Even with plausible maldistribution or inlet temperature drift of +0.5 K, the thermal headroom remains above 3 K. Therefore, the probability of exceeding 80 °C under the specified conditions is low.

14. Recommendations

- Approve the model for use in the go/no-go decision for track testing at the 35 °C, 6 L/min operating point.
- For production release at wider ambient ranges, extend the validation to 25 and 45 °C inlets to confirm property variation handling remains adequate.
- Acquire representative surface roughness metrics on brazed channels; if Ra > 10 µm, include a wall roughness model for pressure drop predictions intended for pump sizing.
- If the electrical team provides detailed die heat maps, run a targeted case to bound additional local hot spots; we do not expect a change in the decision variable by more than ~1 K.

15. Closing statement

Within the narrow context of a steady-state, single-point evaluation of the cold plate’s thermal capacity and flow penalty, the assembled evidence indicates the model is trustworthy. The practices documented—physics selection appropriate to the Reynolds number, grid scrutiny, simple but targeted software checks, and a like-for-like comparison with bench data—provide adequate assurance that the result is not an artifact of numerics or an unjustified assumption. The identified gaps are noted and, where they could shift Δp, they do not compromise the thermal headroom that governs the release decision.

Appendix: key numbers at a glance
- Mesh M3: 9.6 million cells, y+ < 0.3, residuals < 1e-6.
- Baseline outputs: Tmax,copper = 74.2 °C; Δp = 28.4 kPa.
- Lab comparison: 75.1 °C and 29.9 kPa.
- Sensitivity: +5% flow → −1.3 K; +5% heat → +3.9 K.
- Combined 95% uncertainty on hotspot: ±1.7 K.

Contact: Thermal Systems Group (thermal@apexemotors.com)
