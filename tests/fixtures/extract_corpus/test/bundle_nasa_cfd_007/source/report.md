# INTERNAL TECHNICAL MEMO

**TO:** Dr. Priya Nambiar, Project Lead — Cardiovascular Device CFD Program
**FROM:** Marcus Ellroy, V&V Engineer, Computational Methods Group
**DATE:** 14 March 2025
**RE:** V&V Status Update — Centrifugal Blood Pump CFD Model, Pre-Design Review

---

## Purpose

This memo summarizes the current verification and validation posture for the RANS-based CFD model of the HeartDrive Mk-III centrifugal blood pump ahead of the April design review. I'm flagging several areas where we're in reasonable shape and a few where I think we need honest conversations about what we can and can't claim.

---

## What We're Modeling and Why It Matters

The CFD model covers the full wetted flow path — inlet cannula, impeller passage, volute, and outlet — at operating speeds between 2,400 and 3,600 RPM. The primary outputs driving design decisions are wall shear stress distributions (hemolysis risk), pressure-flow (HQ) curves, and recirculation zone characterization near the impeller shroud. Getting the credibility story right here matters because the FDA submission pathway requires us to document our computational evidence in a way that a reviewer with CFD background can assess.

---

## Code and Solver Verification

ANSYS Fluent 2024 R1 is the solver. The development team ran a standard Taylor-Green vortex benchmark and a backward-facing step case against published DNS data (Le, Moin & Kim, 1997) prior to this project. Residual convergence was confirmed below 1×10⁻⁵ for continuity and momentum in all steady-state runs; transient simulations were run to 10 impeller revolutions with mass-flow imbalance below 0.3% at the outlet plane. These checks give me reasonable confidence that the solver itself is doing what it claims. No custom UDFs are in use, which simplifies this picture considerably.

---

## Mesh Refinement and Numerical Error Estimation

We ran a three-level mesh refinement study on the baseline 3,000 RPM operating point. Mesh counts were approximately 4.2M, 11.8M, and 28.6M polyhedral cells, with a consistent refinement ratio of ~1.44. The Grid Convergence Index (GCI) was computed per the Roache methodology for both the HQ curve pressure rise and the peak wall shear stress on the impeller blade pressure surface.

For pressure rise, the fine-grid GCI was 1.8% — acceptable. For peak WSS, it came in at 6.3% on the fine grid, which is higher than I'd like given that WSS is a primary design criterion. The medium mesh (11.8M cells) is being used for the parametric sweep runs due to computational cost, and the GCI on that mesh for WSS is 11.4%. I want to flag this explicitly: our numerical uncertainty in the hemolysis-relevant output is not trivial, and we should not present the WSS results without the uncertainty bounds attached.

Y+ values on impeller blades averaged 0.8–1.2 with the SST k-ω model, which is appropriate for the near-wall treatment being used.

---

## Turbulence Modeling and Physical Assumptions

SST k-ω was selected based on its track record in rotating machinery and its ability to handle adverse pressure gradients in the volute. We did a spot-check comparison against a k-ε realizable run at the design point — pressure rise agreed within 2.1%, but WSS distributions showed up to 18% local differences in the recirculation zone near the shroud. This is a known limitation of RANS for separated flows, and I think we need to be transparent about it.

The blood rheology is modeled as a Newtonian fluid (μ = 0.0035 Pa·s, ρ = 1060 kg/m³). The non-Newtonian behavior of blood at low shear rates (below ~100 s⁻¹) is not captured. In the high-shear regions of the impeller passage this is probably fine; in the recirculation zones it introduces unquantified physical modeling uncertainty. We haven't run a Carreau-Yasuda comparison yet — that's deferred to Phase 2.

---

## Comparison Against Test Data

This is the area I'm most concerned about heading into the review. We have bench test data from the hydraulic loop at the University of Minnesota (conducted February 2025) covering HQ curves at 2,400, 3,000, and 3,600 RPM. CFD-to-test agreement on pressure rise is within ±4.5% across the tested flow range, which I consider acceptable for this stage.

However, we do not yet have experimental WSS or flow visualization data. The PIV campaign at Minnesota is scheduled for June. Until that data is available, our WSS predictions are validated only indirectly through the HQ agreement — which is a much weaker claim. I want to make sure the design review slides don't overstate this. The model is validated for global hydraulic performance; it is not yet validated for local flow field quantities.

The test conditions used a blood analog fluid (aqueous glycerol, 40% by mass) rather than real blood. The dynamic viscosity match was confirmed at 22°C, but density was approximately 1058 kg/m³ vs. the 1060 kg/m³ modeled — a negligible difference. The inlet turbulence intensity used in the CFD (5%) was estimated from the test rig geometry; it was not directly measured.

---

## Boundary Conditions and Operating Envelope

Inlet boundary conditions were set as uniform velocity profiles derived from measured flow rates. We did not model the upstream cannula geometry in the validation cases, which introduces some inlet condition uncertainty. For the design cases, a 10-diameter straight inlet section was used to allow the profile to develop, which partially mitigates this.

The model has been run at three discrete RPM values. Interpolation to intermediate speeds relies on the assumption of hydraulic similarity, which holds reasonably well for this pump geometry but has not been formally verified across the full operating range.

---

## Uncertainty Quantification — Input Sensitivity

A limited sensitivity study was conducted varying inlet flow rate (±10%), rotational speed (±2%), and blood viscosity (±15%) around the design point. Results showed that pressure rise is most sensitive to rotational speed (as expected) and that WSS peak values are notably sensitive to viscosity — a ±15% viscosity change produced a ±19% change in peak WSS. This reinforces the concern about Newtonian assumption adequacy in low-shear regions.

No formal probabilistic UQ (e.g., Monte Carlo or polynomial chaos) has been performed. The sensitivity study is deterministic and covers only the three parameters listed.

---

## Areas Not Addressed in This Memo

I want to be explicit that the following are out of scope for this memo and will be addressed separately:

- **Software quality and configuration management** for the Fluent installation and run scripts — IT security and the software governance team are handling this under a separate review track. I don't have visibility into their timeline.
- **Independent review of the CFD methodology by an external party** — this was discussed in the project kickoff but has not been scheduled. Given the FDA submission context, I'd recommend we revisit this before the submission package is finalized.
- The question of how well the model results translate to **clinical use conditions** — that's properly a systems-level question outside my lane as V&V engineer.

---

## Summary Assessment

| Area | Status |
|---|---|
| Solver verification (code-level) | Adequate for current phase |
| Mesh convergence / GCI | Acceptable for HQ; marginal for WSS |
| Turbulence model justification | Documented, limitations acknowledged |
| Validation against test data | Partial — hydraulic only, local flow field pending |
| Input sensitivity | Limited deterministic study complete |
| Physical model completeness (rheology) | Known gap, deferred |

My overall read: the model is fit for purpose for hydraulic design decisions at this stage. It is **not** ready to support regulatory claims about hemolysis risk without the PIV validation data and a more rigorous treatment of WSS numerical uncertainty. I'd recommend the design review materials clearly distinguish between what's been validated and what remains predictive.

Happy to discuss before the review prep meeting on the 21st.

— Marcus
