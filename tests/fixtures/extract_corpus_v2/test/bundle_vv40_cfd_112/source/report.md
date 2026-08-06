# Credibility Review: Axial Fan in Straight Duct — CFD Assessment

Project: AHU-1200 inline axial fan, 400 mm diameter, evaluated at nominal 1800 rpm  
Solver: Pressure-based RANS, rotating reference frame (MRF), SST k–ω  
Scope: Predict static pressure rise, downstream swirl, and shaft power for envelope flows without test data

## 1. Background and Objectives

The facilities team requested a rapid-turn CFD assessment to support silencer placement downstream of an inline axial fan installed in a 408 mm circular duct. The main question is: how far downstream does residual swirl persist at the nominal duty point, and what static pressure recovery can be expected in the first 6–8 diameters? A secondary aim is to estimate shaft power at three flow settings to confirm motor sizing margin for the 0.75 kW motor already specified by procurement.

Schedule constraints limited modeling to steady-state methods. Rotating hardware is represented with a multiple reference frame (MRF) technique rather than unsteady sliding meshes. The duct is straight with a mild instrumentation tap near 5D; minor external features are neglected. The assessment covers three nominal flowrates at fixed fan speed:

- DP1: 1.8 m³/s (restricted flow)
- DP2: 2.4 m³/s (nominal)
- DP3: 3.0 m³/s (unrestricted flow)

Strong emphasis is placed on DP2. The outputs of interest are the static-to-static pressure gain across the fan plane, swirl angle decay with axial distance, and torque-induced shaft power.

## 2. Model Setup Overview

- Physics: Incompressible, isothermal, steady-state RANS.
- Frame handling: MRF in the rotor subdomain, 1800 rpm.
- Turbulence closure: SST k–ω for improved behavior under adverse gradients in the blade passages and hub region; scalable wall functions.
- Numerical schemes: Second-order upwind for momentum and turbulence transport; least-squares cell-based gradient reconstruction; coupled pressure–velocity with pseudo-transient under-relaxation damped at the end of each iteration block.
- Residual behavior: Continuity and momentum residuals targeted below 1e−4; monitors of area-averaged static pressure at ±0.5D bracketing the rotor to check for iterative creep.

The solver was ANSYS Fluent 2023 R2, using poly-hexcore meshing with prism layers at walls. The run environment was a dual-socket workstation (2 × 16 cores, 256 GB RAM). Double-precision was used throughout.

## 3. Geometry and Domain Definition

A native STEP model for the 7-blade axial rotor and stator hub was supplied. The trailing-edge fillet radii were <0.6 mm in places. As these are below the duct boundary layer thickness and below practical mesh resolution for this schedule, fillets and chamfers <1 mm were suppressed. The shaft nut’s hex flats were replaced with a circumscribed cylinder to avoid local mesh skewness.

The computational domain comprises:

- Upstream plenum: 1.0 D axial length.
- Rotating region: 0.28 D length encapsulating the blade span and hub.
- Downstream straight duct: 8.0 D axial length.

Domain extent was inspected by extending the downstream duct to 12 D on the medium grid; the change in static pressure recovery at 6 D was 0.7 Pa, which is within the numerical noise of the runs and did not propagate into torque in a meaningful way.

The fan tip clearance is 1.1 mm in the CAD. That gap is preserved explicitly in the model, despite the coarse near-wall y+ in that region (y+ ~ 40–65 at the tip shroud), because gap leakage contributes to swirl persistence in similar products. Surface roughness was not modeled; walls were treated as hydraulically smooth.

## 4. Boundary Conditions and Operating Points

- Inlet: Volumetric flowrate boundary set to the duty flow (1.8, 2.4, 3.0 m³/s). Turbulence at the inlet specified as intensity 5% with turbulent length scale 0.07D.
- Outlet: Static pressure set to gauge 0 Pa.
- Walls: No-slip, smooth walls.
- Interface between rotating and stationary regions: Frozen rotor (MRF) with conservative flux transfer.

During solution, additional probes tracked:

- Axial and circumferential velocity profiles at 1D, 3D, 6D.
- Static pressure immediately upstream and downstream of the rotor (±0.5D).
- Torque on the blade surfaces.

## 5. Mesh Construction and Grid Sensitivity

Meshes were generated with a poly-hexcore workflow, targeting reduced numerical diffusion in the shear layers off blade tips while maintaining manageable cell counts.

Near-wall treatment:
- Prism layers: 8 layers, initial height 0.15 mm, growth 1.25, to place non-dimensional wall distance y+ in the 30–60 range over most wetted surfaces, compatible with the wall-function regime of SST k–ω.
- Observed y+ at DP2: 28th percentile 31, median 39, 95th percentile 67 (hot spot at the tip).

Core and wake resolution:
- Hexcore body size tuned to ~4 mm nominal in the bulk duct, contracting near blade passages to 1.5–2.0 mm.

Grids used:
- Coarse: 3.1 million cells.
- Medium: 6.2 million cells.
- Fine: 12.7 million cells.

Convergence characteristics:
- For DP2, medium and fine grids reached residuals <1e−4 within 800–1200 iterations depending on under-relaxation tuning. Mass balance discrepancy at convergence <0.1% for all grids.

Mesh sensitivity (DP2, representative results):
- Static pressure rise across rotor plane (Δp_s):
  - Coarse: 192 Pa
  - Medium: 187 Pa
  - Fine: 185 Pa
- Swirl angle at 1D downstream (area-averaged, arctan of mean tangential over mean axial velocity):
  - Coarse: 18.0°
  - Medium: 17.1°
  - Fine: 16.7°
- Shaft power (from torque × ω):
  - Coarse: 468 W
  - Medium: 455 W
  - Fine: 452 W

Grid refinement from medium to fine changed Δp_s by −1.1% and power by −0.7%. Swirl angle varied by −2.3% absolute (0.4°). These deltas are small relative to typical fan application tolerances and suggest diminishing returns past ~6 million cells for the intended use. No formal error extrapolation was applied.

A boundary-location test with medium grid and 12D downstream duct shifted Δp_s by +0.7 Pa and swirl angle at 6D by −0.2°, well within the variability seen between successive iterations before final stabilization.

Quality metrics:
- Mean non-orthogonality 14°, max 47° (localized at blade leading-edge intersections).
- Mean skewness 0.23, 95th percentile 0.45.
- Face area ratio below 6 for 99.5% of faces; the outliers were screened and did not align with principal flow features.

## 6. Numerical Controls and Convergence Conditioning

The coupled solver employed pseudo-transient ramping with a maximum pseudo-time step of 0.01 s and a Courant target of ~50 in the core flow. Pressure under-relaxation was reduced to 0.3 for the first 200 iterations and restored to 0.6 thereafter. Turbulence equations were under-relaxed at 0.5.

Two initializations were trialed for DP2 on the medium grid: (a) uniform axial guess; (b) mapped solution from DP3. Both converged to indistinguishable Δp_s (within 0.4 Pa) and torque (within 0.3%), supporting that the steady solution is not path-dependent within the explored basin.

Solution monitors (mass flow at outlet, torque, and Δp_s) flattened before residual criteria in several runs; in those cases, iterations were extended 200–400 cycles past the flattening to ensure no slow drift.

## 7. Turbulence Closure Rationale

SST k–ω was chosen due to its track record in separated flows and adverse pressure gradients, which are expected near the blade roots and the downstream wake development. For a single check on model sensitivity, the realizable k–ε model was run on the medium grid at DP2, keeping all other settings identical. The realizable k–ε predicted:

- Δp_s: 178 Pa (−4.8% relative to SST).
- Swirl at 1D: 18.9° (+10.5% relative to SST).
- Shaft power: 445 W (−2.2% relative to SST).

Given the intended use (swirl management and silencer placement), the elevated swirl persistence predicted by k–ε was considered less consistent with the high-diffusivity behavior we’ve seen in similar ducts. SST was retained.

No near-wall model switch to low-Re formulations was attempted due to y+ being in the wall-function regime.

## 8. Results

Summaries are presented for the three duty points. Detailed velocity contour plots and vector fields were reviewed internally but are not embedded in this write-up.

DP1 (1.8 m³/s), medium grid:
- Δp_s across rotor plane: 231 Pa.
- Shaft power: 428 W.
- Swirl angle at 1D: 18.8°; at 3D: 12.4°; at 6D: 8.3°.
- Axial velocity profile at 1D shows a mild hub deficit; tip region carries higher momentum due to leakage jet re-entrainment.

DP2 (2.4 m³/s), fine grid:
- Δp_s across rotor plane: 185 Pa.
- Shaft power: 452 W.
- Swirl angle at 1D: 16.7°; at 3D: 10.7°; at 6D: 7.0°.
- Pressure recovery between 0.5D and 6D downstream: ~35 Pa. Removing downstream extension from 8D to 6D reduced recovery by 0.9 Pa.

DP3 (3.0 m³/s), medium grid:
- Δp_s across rotor plane: 148 Pa.
- Shaft power: 487 W.
- Swirl angle at 1D: 14.5°; at 3D: 9.8°; at 6D: 6.4°.
- Higher mass flow thickened the wall-adjacent shear layers but did not produce significant separation.

Across all duty points, the area-averaged axial Mach number remained below 0.12 throughout; density variation effects are negligible. The maximum local Mach in the blade passage at DP3 approached 0.18 on the suction side near midspan but did not trigger transonic behavior.

Tip clearance jets are visible in Q-criterion visualizations. They contribute to the elevated tangential velocities near the shroud at 1D. Mixing diminishes the azimuthal asymmetry by 3D, consistent with typical intra-duct decay lengths for this diameter and flow regime.

Mass balance closed within 0.1% for all converged cases. Imbalances were higher (0.3%–0.4%) in pre-converged iterations and reduced with continued cycles, indicating no systemic leakage or accumulation issues in the solver setup.

## 9. Interpretation for Swirl Management and Component Placement

For DP2, the 1D swirl of 16.7° reduces to ~7° by 6D. In practical terms, downstream equipment that is sensitive to incidence (e.g., certain silencer baffles or flow meters) should be placed at ≥5D to avoid overloading from skewed inflow. If a compact layout demands placement at 3D, we expect a residual incidence of around 10°, which may require re-aiming baffles or using swirl vanes.

Static pressure recovered downstream of the rotor is about 35 Pa by 6D at DP2. When combined with the 185 Pa produced across the rotor plane, the net static gain at 6D is ~220 Pa. This favors locating any major flow restriction (e.g., a silencer with distributed pressure drop) further downstream, past the rapid mixing zone, to utilize the natural recovery provided by the duct.

The predicted shaft power at DP2 (~452 W) yields a flow power P_flow = Δp_s × Q ≈ 185 Pa × 2.4 m³/s ≈ 444 W. The ratio suggests a gross hydraulic efficiency in the neighborhood of 0.98 when viewed with the simple Δp_s × Q metric, which is clearly an overestimate because it neglects losses not captured in this idealized calculation as well as motor and transmission losses. A more sensible comparison uses rotor torque-based power, which is what is reported here. The apparent closeness between torque-based power and Δp_s × Q at DP2 is coincidental given the idealized boundaries; the trend across DP1–DP3 shows divergence consistent with internal losses.

## 10. Checks on Model Robustness

Several internal checks were performed to reduce the likelihood that the results hinge on arbitrary numerical choices:

- Domain-size sensitivity: Extending the downstream duct from 8D to 12D barely changed key outputs (Section 5).
- MRF zone thickness: Increasing the rotating region length from 0.28D to 0.36D at DP2 altered torque by +0.6% and Δp_s by +0.3 Pa, indicating the location of the frozen interface is not driving the outcome.
- Initialization path: Different starting fields converged to the same solution on the medium grid (Section 6).
- Near-wall layer resolution: Reducing the first-layer height by 20% (pushing y+ lower by ~15%) changed swirl at 1D by +0.2° and Δp_s by +0.8 Pa.

While none of these checks substitute for a full unsteady treatment or exhaustive parameter sweeps, the pattern suggests the reported values are not fragile.

## 11. Credibility Discussion

On the numerical side, the model shows:

- Iterative stability with monotonic residual decay to 1e−4 or better.
- Diminishing changes with grid refinement from 6.2M to 12.7M cells, indicating the main features have adequate resolution for the intended decisions.
- Minimal sensitivity to domain truncation and MRF interface position.
- Physically plausible behavior across the flow envelope: Δp_s decreasing with flowrate and swirl angle decreasing with distance.

On the physics side, the selected turbulence model is appropriate for attached and mildly separated flow through axial turbomachinery at this Reynolds number. The steady MRF approach cannot capture rotating stall, blade passing interactions, or coherent structures that require transient resolution. However, for swirl decay and mean pressure fields in a straight duct away from the rotor, many prior internal studies have found MRF sufficient to rank scenarios and to support component spacing decisions.

The moderate y+ values and the use of wall functions are consistent with industry practice for time-constrained evaluations of fans in smooth ducts. Regions of high curvature and secondary flow near the hub may benefit from lower y+ in a deeper-dive study; the current meshes aim for broad coverage rather than resolving near-wall anisotropy.

## 12. Limitations and Next Steps

- The use of steady-state MRF removes all time-accurate wake shedding and rotor–stator interactions. If tonal noise or transient loading is of interest, a sliding-mesh transient study would be necessary.
- Wall roughness was neglected. For galvanized or lined ducts with measurable roughness height, swirl decay and pressure recovery can shift; future sensitivity to roughness could be informative for specific installations.
- The hub fillet removal and nut simplification were judged harmless for global swirl and pressure; if hub recirculation zones become design drivers, these features should be restored and locally refined.
- The tip clearance was respected, but near-wall mesh at the tip did not target low-Re resolution. Tip-leakage vortex structure is, therefore, smeared. If blade-end loading is ever under scrutiny, a local y+ < 1 approach should be adopted with an appropriate low-Re model or hybrid RANS–LES.
- Only one turbulence closure was used for the main conclusions. The single comparison to realizable k–ε indicates model-form variability at the few-percent level for Δp_s and more for swirl angle; more comprehensive exploration would add confidence when swirl is the key design quantity.

Recommended follow-up, if time allows:
- A targeted transient run at DP2 with sliding mesh to check swirl decay rates at 1D and 3D.
- A roughness sweep to bracket installations using insulated or perforated linings.
- A hub-focused local refinement to examine the persistence of secondary flows that can affect sensor readings in tight layouts.

## 13. Conclusions

For the inline axial fan operating in a straight, smooth duct, the steady RANS model with MRF and SST k–ω predicts:

- Static pressure rise across the rotor plane ranging from ~231 Pa at 1.8 m³/s to ~148 Pa at 3.0 m³/s, with 185 Pa at the nominal 2.4 m³/s.
- Shaft power from ~428 W (low flow) to ~487 W (high flow), with ~452 W at nominal.
- Swirl angles at 1D downstream between ~14.5° and ~18.8° across the flow envelope, decaying to ~6–8° by 6D.

Grid sensitivity, domain extent checks, and numerical robustness exercises indicate that these values are stable against reasonable modeling choices at the level of fidelity used. The results provide a sound basis for silencer placement and for preliminary motor sizing sanity checks in the current design phase.

The analysis is suitable for early-stage decision-making on duct component spacing and is not intended to serve as a definitive characterization of blade-resolved unsteady phenomena or noise. If the project proceeds to detailed design where small changes in swirl or pressure recovery have high cost implications, the follow-up steps outlined above should be budgeted.

---
Prepared by: CFD Applications Group  
Date: 2026-08-06
