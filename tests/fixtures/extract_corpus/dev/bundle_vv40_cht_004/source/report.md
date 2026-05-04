# TECHNICAL MEMORANDUM

**To:** Dr. Priya Nambiar, Program Lead – Advanced Thermal Systems  
**From:** M. Castellano, Verification & Validation Group  
**Subject:** V&V Status Summary – Conjugate Heat Transfer Model, Turbine Blade Trailing-Edge Cooling Insert (Project FALCON-7)  
**Date:** 2024-11-14  
**Distribution:** Restricted – Internal Use Only

---

## Purpose

This memo summarizes the current validation and verification posture for the CHT simulation model developed to predict metal temperatures and coolant-side heat transfer in the FALCON-7 turbine blade trailing-edge cooling insert. The model is implemented in ANSYS Fluent 2023 R2 and covers a representative periodic passage including the pin-fin array and ejection slots. The intent is to give you a frank assessment of where we stand before the Phase 3 design review.

---

## Governing Equations and Physical Scope

The simulation solves the compressible Reynolds-averaged Navier–Stokes equations coupled to the energy equation in both the fluid domain and the solid nickel superalloy insert. Turbulence closure uses the SST k-ω model with low-Reynolds-number damping near the pin surfaces. Radiation is neglected on the basis that coolant-side optical depths are small and the hot-gas boundary is represented as a fixed temperature condition rather than a participating medium — this is a deliberate scope limitation that the team has documented and accepted.

The physical phenomena captured include forced convective cooling in the internal passage, conduction through the blade wall, and film cooling discharge at the trailing edge. Buoyancy-driven secondary flows are not modeled; a separate sensitivity run (described below) confirmed that the Richardson number in the relevant passages stays below 0.04, so this omission is defensible.

---

## Software Qualification and Numerical Integrity

The Fluent solver used here is a commercial code with an extensive published verification history. Our group ran a suite of in-house code-level checks earlier this year: the Nusselt number correlation for fully developed turbulent pipe flow (Dittus-Boelter) was reproduced to within 1.8% at Re = 30,000, and the 2D lid-driven cavity benchmark at Re = 1000 matched Ghia et al. (1982) reference data for all monitored velocity components to better than 0.5%. These exercises confirm that the solver arithmetic and coupling routines are operating correctly for the class of problems we are solving. Solver release notes and patch history were reviewed; no known defects affect the coupled energy solver in this release.

---

## Mesh Refinement and Numerical Uncertainty

Three structured hexahedral meshes were constructed using ANSYS Meshing: coarse (~2.1 M cells), medium (~6.4 M cells), and fine (~18.7 M cells). Wall y+ values on pin surfaces were maintained below 1.0 on all three levels. The Grid Convergence Index methodology (Roache, 1998) was applied using the area-averaged Nusselt number on the pressure-side pin row as the primary output metric. The GCI between medium and fine meshes is 2.3%, which falls within our project acceptance threshold of 5%. All subsequent production runs use the medium mesh as the best compromise between accuracy and runtime. Residuals for all transport equations were converged to below 1×10⁻⁵, and monitored surface temperatures showed variation of less than 0.2 K over the final 500 iterations — we are confident the solutions are well-converged.

---

## Boundary Conditions and Input Uncertainty

Inlet total pressure and total temperature profiles were derived from upstream stage CFD results provided by the aero team (Rev. C, dated 2024-09-03). Coolant inlet conditions were set using rig-measured plenum pressures and temperatures from the TF-9 flow bench; measurement uncertainty on those values is ±0.8% in pressure and ±1.5 K in temperature, as certified by the metrology lab. We propagated these uncertainties through the model using a one-at-a-time perturbation study across the ±2σ range of each input. The resulting spread in predicted mid-chord metal temperature is ±6.2 K, which is small relative to the design margin of ±25 K. Rotational effects are not included in the current model; a note in the boundary condition log acknowledges this and flags it for the next phase when a rotating rig dataset becomes available.

---

## Comparison Against Experimental Data

Validation data come from two sources: (1) the ORNL-style linear cascade rig operated by our external partner, Thermofluids Research Ltd. (TRL), and (2) a dedicated pin-fin channel coupon test conducted in-house on the TF-9 bench.

**TRL cascade data:** Infrared thermography of the blade pressure and suction surfaces at three coolant-to-mainstream blowing ratios (M = 0.5, 1.0, 1.5). Predicted surface temperatures agree with IR measurements to within ±8 K (RMS) at M = 1.0, which is the design-point condition. At off-design conditions (M = 0.5 and M = 1.5), the model over-predicts temperatures by up to 14 K and under-predicts by up to 11 K respectively. The team attributes the M = 0.5 discrepancy to separation at the ejection slot lip, which SST k-ω is known to handle poorly in strongly adverse pressure gradients. This is a documented model-form limitation.

**TF-9 coupon data:** Pressure drop and overall Nusselt number measured across the pin-fin array at five Reynolds numbers spanning Re = 8,000–45,000. Model predictions fall within the experimental uncertainty bands (±7% in Nu, ±4% in ΔP) at all five conditions. This is the strongest quantitative validation evidence in the package.

Uncertainty in the experimental reference data itself was evaluated. TRL provided calibration certificates for the IR camera (FLIR X8500sc) and reported a combined measurement uncertainty of ±3.5 K for surface temperature. The TF-9 bench pressure transducers (Kistler 4045A) carry a certified accuracy of ±0.15% full scale. These figures were factored into the validation comparison.

---

## Sensitivity and Scenario Coverage

Beyond the boundary condition perturbation study, we ran targeted sensitivity analyses on two modeling choices that carry significant epistemic uncertainty: (a) turbulence model selection and (b) the thermal contact resistance at the insert-to-blade interface. Swapping SST k-ω for the realizable k-ε model changed predicted peak metal temperature by 9 K — meaningful but within the design margin. Varying the interface contact resistance over the range reported in the literature (0.5–2.5 × 10⁻⁴ m²K/W) produced a 17 K swing in local hot-spot temperature; the nominal value used (1.2 × 10⁻⁴ m²K/W) is based on a supplier data sheet for the brazing alloy and is considered the best available estimate.

The model has been exercised across the full operating envelope specified in the FALCON-7 design requirement document (DRD-F7-022 Rev. B): four corrected mass-flow conditions and two turbine inlet temperature levels. No numerical instabilities or convergence failures were observed across this matrix of 8 runs.

---

## Process and Configuration Control

All simulation files, mesh databases, and post-processing scripts are stored in the project GitLab repository (falcon7-cht, branch `release/v2.3`) with commit hashes logged in the run manifest. Each production run is associated with a unique run ID and a signed checklist confirming input file version, solver settings, and reviewer sign-off. The model configuration has been reviewed by two engineers outside the development team — Dr. S. Okonkwo (thermal) and P. Lindqvist (CFD methods) — who confirmed that the setup is consistent with project requirements and that no undocumented manual interventions were made to the solution.

A formal review of how the simulation outputs are used in downstream design decisions was conducted with the blade design team. We confirmed that the temperature maps feed directly into the lifing calculation (Larson-Miller approach) and that the analysts using those outputs understand the ±6–14 K uncertainty range and its implications for predicted blade life. No misinterpretation of model output scope was identified during this review, and the design team confirmed they are not using the model to predict suction-side film effectiveness — a capability outside the current validation envelope.

---

## Summary Assessment

| Area | Status |
|---|---|
| Solver qualification | Satisfactory |
| Numerical convergence and mesh sensitivity | Satisfactory (GCI < 5%) |
| Boundary condition traceability | Satisfactory |
| Input uncertainty propagation | Satisfactory |
| Validation against coupon data | Satisfactory |
| Validation at off-design cascade conditions | Acceptable with documented limitations |
| Sensitivity / scenario coverage | Satisfactory |
| Configuration management | Satisfactory |
| Downstream use review | Satisfactory |

The overall package supports confident use of the model for design-point temperature prediction within the validated operating range. Off-design use at low blowing ratios should be treated with added conservatism (recommend a 15 K temperature margin adder) until the slot-lip separation behavior is better characterized, either through higher-fidelity LES or additional targeted experiments.

Please let me know if you need the full run manifest or calibration certificates before the Phase 3 review.

---

*M. Castellano*  
*Senior V&V Engineer, Thermal Systems Group*  
*Ext. 4-7823 | m.castellano@falcon-engineering.int*
