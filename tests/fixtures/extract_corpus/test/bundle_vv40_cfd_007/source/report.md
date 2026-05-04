# INTERNAL TECHNICAL MEMO

**To:** Dr. Priya Nandakumar, Project Lead — Turbomachinery Aero Group
**From:** M. Castellano, CFD Methods & Validation
**Date:** 14 March 2025
**Re:** V&V Status Update — Centrifugal Pump Stage CFD Model (Rev. C)
**Project:** AQUA-7 Pump Stage, Contract 2241-B

---

## Purpose

This memo summarizes the current validation and verification standing for the RANS-based CFD model of the AQUA-7 single-stage centrifugal pump. The model is being used to predict hydraulic efficiency, head rise, and internal flow structure across the operating range (0.6Q_n to 1.2Q_n). A formal review is scheduled for 28 March; this memo captures what we have completed, what is still open, and where I believe the model stands credibly enough to support design decisions at the upcoming gate.

---

## Solver and Setup

All simulations were run in ANSYS Fluent 2023 R2 using the SST k-ω turbulence closure. The computational domain covers the full 360° stage including the volute — no passage periodicity assumption. Rotating reference frame treatment was applied at the impeller–volute interface using the frozen rotor approach at steady-state, with a sliding mesh transient run completed at BEP only for comparison. Inlet boundary condition is a uniform total pressure profile (no inlet swirl), and the outlet uses a mass-flow specification. Wall treatment is standard no-slip with enhanced wall functions (y+ target 30–60, achieved 28–65 across the blade passage).

---

## Grid Sensitivity

A three-level mesh refinement study was completed using hexahedral-dominant grids of approximately 2.1M, 6.8M, and 18.4M cells. The Grid Convergence Index (GCI) was computed following the Celik et al. (2008) procedure for head coefficient (ψ) and hydraulic efficiency (η_h) at the best efficiency point. Results:

- GCI_fine for ψ: 0.9%
- GCI_fine for η_h: 1.4%
- Apparent order of convergence p = 1.87 (theoretical 2nd order; slight degradation attributed to near-wall mesh transitions)

The medium mesh (6.8M cells) was selected for the production runs as the fine mesh offered marginal improvement at roughly 3× the compute cost. Residuals for all transport equations fell below 1×10⁻⁵ (continuity reached 4×10⁻⁶) in all operating-point runs. Mass imbalance across the domain was confirmed below 0.01%.

This gives me reasonable confidence that numerical noise is not a dominant source of uncertainty in the head and efficiency predictions.

---

## Comparison Against Test Data

Physical test data are available from a closed-loop hydraulic test rig operated by the client (Flowserve internal test facility, Raleigh). Test measurements include:

- Pump total head (differential pressure transducers, ±0.3% FS)
- Shaft torque (inline torque meter, ±0.15% FS)
- Volumetric flow rate (electromagnetic flowmeter, ±0.25% FS)

CFD predictions of head rise match test data within 2.1% across the mid-range operating points (0.85Q_n to 1.1Q_n). At low-flow (0.6Q_n), the model over-predicts head by approximately 5.8%, which is consistent with known limitations of the frozen rotor approach and steady-state RANS in the recirculation-dominated regime. The transient sliding mesh result at BEP improved agreement to within 0.8% for head and 1.1% for efficiency compared to the steady frozen-rotor result of 2.1% / 1.7%.

Efficiency predictions show a systematic low bias of roughly 1.2–1.8 percentage points across the range. We believe this is partly attributable to mechanical losses (seal friction, bearing drag) not modeled in the CFD — these are estimated at 0.8–1.1 pp based on the client's empirical correlations. Residual discrepancy after accounting for mechanical losses is within acceptable bounds for this design phase.

**Uncertainty in test data:** The client provided calibration certificates for the instrumentation dated November 2024. Combined measurement uncertainty on efficiency is estimated at ±1.4% (95% confidence, RSS method). This is documented in Flowserve Test Report TR-2241-009.

---

## Applicability of the Model to the Design Condition

The validation dataset covers operating points from 0.6Q_n to 1.2Q_n at the nominal speed (2950 RPM). The design intent for AQUA-7 is operation between 0.9Q_n and 1.05Q_n at 2950 RPM. The model has therefore been exercised across a range that brackets the intended use, and the validation evidence is directly relevant to the conditions of interest. No extrapolation beyond the validated speed range is currently claimed.

The geometry tested at the Flowserve rig is the Rev. B impeller. Rev. C introduces a 2° change in blade exit angle and a 4 mm reduction in impeller outlet width. Engineering judgment (supported by sensitivity runs) suggests these changes will shift head by approximately +3% and efficiency by −0.5 pp — well within the validated operating regime in terms of flow physics. I consider the geometry delta acceptable for applying the model to Rev. C predictions, but this should be noted as an assumption in the gate review package.

---

## Code Verification and Numerical Integrity

The ANSYS Fluent solver has been subject to internal verification by ANSYS through their standard release testing program, and published benchmark comparisons (e.g., NASA Langley turbulence model resource cases) demonstrate correct implementation of SST k-ω for attached and mildly separated flows. For this project, we ran the 2D backward-facing step case (Re = 37,000) as a spot-check of our local installation and boundary condition setup; results matched the Driver & Seegmiller experimental data within 4% for reattachment length. I am satisfied that the solver is functioning as intended for this class of flows.

---

## What Is Not Covered in This Memo

A few areas are explicitly out of scope for this phase and are not addressed here:

- **Cavitation inception prediction:** The client has not yet provided NPSH test data, and no cavitation modeling has been attempted. This is deferred to Phase 2.
- **Thermal / fluid temperature effects:** The working fluid is treated as isothermal water at 25°C. No conjugate heat transfer or viscosity variation with temperature has been considered. Out of scope per SOW Section 3.2.
- **Structural coupling:** Impeller stress and deflection under hydraulic loading are not part of this CFD scope. FEA is handled separately by the structures team.

I want to be explicit that the simulation's treatment of inlet turbulence intensity has not been formally characterized. The test rig inlet condition is not well-instrumented, and we used a default 5% turbulence intensity at the inlet boundary. Sensitivity to this assumption was not systematically evaluated in the current revision. This is a gap I'd like to close before the final report.

---

## Overall Assessment

For the intended use — supporting impeller geometry selection at the preliminary design gate — I believe the model is credible. The mesh refinement study shows numerical errors are small relative to the physical quantities of interest. Comparison with test data shows good agreement in the primary design range, with known and bounded discrepancies at off-design conditions. The solver has been spot-checked for correct behavior. Measurement uncertainty in the reference data is documented and accounted for.

The low-flow regime (below 0.75Q_n) should be treated with caution in any design decisions, and the inlet turbulence sensitivity gap should be addressed before the model is used for detailed loss breakdown analysis.

I am available to discuss before the 28 March review.

— M. Castellano
