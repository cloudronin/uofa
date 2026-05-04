# INTERNAL TECHNICAL MEMO

**To:** Dr. Priya Nambiar, CHT Program Lead
**From:** J. Hollenbeck, Thermal Analysis Group
**Date:** 14 March 2025
**Subject:** V&V Status — Conjugate Heat Transfer Model, Turbine Blade Cooling Passages (Rev. B)
**Distribution:** Restricted — Program Technical Staff Only

---

## Purpose

This memo summarizes where we stand on the credibility of the ANSYS Fluent 2024R1 conjugate heat transfer model developed for the HPT Stage-1 blade cooling channel geometry (Project Icarus, Contract NNX-8841). The model couples internal convection through the serpentine cooling passages with conduction through the Inconel-718 blade wall and external hot-gas film. Review is scheduled for 28 March; this memo flags gaps and what I think we can and cannot defend.

---

## What the Model Is Supposed to Do

The simulation predicts wall temperature distributions and coolant exit conditions under take-off power settings (TGT ~1,740 K, coolant inlet at 720 K, 4.2% bleed fraction). The outputs feed a low-cycle fatigue life estimate. Getting the peak metal temperature wrong by even 15 K in the leading-edge region meaningfully shifts predicted life, so the stakes here are real.

---

## Geometry and Mesh

The blade CAD was imported from the OEM-supplied STEP file (Revision 14c). The internal cooling passage geometry was simplified — the film cooling holes were capped and modeled as a lumped boundary condition rather than resolved explicitly. This is a known fidelity limitation and was a deliberate scope decision made in October.

We ran a three-level mesh refinement study on the passage cross-sections and the leading-edge impingement zone. Coarse (~1.8M cells), medium (~5.1M cells), and fine (~12.4M cells) grids were evaluated. The Richardson extrapolation-based GCI for peak wall temperature came out at 1.3% between medium and fine, which I'd call acceptable. We're running on the medium grid for the parametric sweeps given compute budget. Wall y+ values are held between 30 and 60 on the hot-gas side, consistent with the chosen k-ω SST wall treatment. The internal passages use a low-Re mesh with y+ < 1 at the passage walls.

---

## Solver and Numerical Behavior

We're using the coupled pressure-velocity solver with second-order upwinding on all transport equations. Residuals drop to below 1×10⁻⁵ on energy and 1×10⁻⁴ on momentum; we also monitor coolant exit bulk temperature and leading-edge heat flux as convergence indicators — both flatten to within 0.1% over the final 500 iterations. No unusual convergence behavior observed.

---

## How the Code Was Checked

ANSYS Fluent is a commercial solver with a long track record. We did not perform independent line-by-line code review — that's not practical for a commercial tool. However, we ran the solver against two published benchmark cases: (1) the AGARD-AG-333 internal duct flow with heat transfer, and (2) a pin-fin array case from Han & Park (1988) that has been used in prior program work. Agreement on Nusselt number within 8% and 11% respectively. These are not tight comparisons, but they give some confidence the energy coupling is behaving correctly. The turbulence model selection (k-ω SST) is consistent with prior blade cooling work in the literature, though we acknowledge that SST can overpredict heat transfer in strong curvature regions — something worth flagging for the review board.

---

## Comparison to Physical Test Data

This is the part I want to be direct about: our validation dataset is thin.

We have one legacy test case — a simplified 2-pass rectangular channel rig from the 2019 Icarus Phase-I campaign (test article IC-04). The rig used the same coolant supply conditions but a simplified rectangular cross-section, not the actual airfoil geometry. We matched that dataset to within 6% on exit temperature and 12% on local heat flux at five instrumented stations. The 12% local heat flux discrepancy at Station 3 (the 180° turn) is not fully explained; we attribute it to flow separation effects that SST handles poorly in tight bends.

No test data exists for the current Rev-14c blade geometry. The OEM was supposed to provide rig data from their 2023 cascade test but that has not materialized. We have been told to expect it "before CDR" but I would not count on it for the 28 March review.

The validation coverage is therefore limited to a geometrically dissimilar precursor test. This is a real gap and should be called out explicitly in the review package.

---

## Sensitivity and Uncertainty

We ran a modest parameter sweep varying coolant inlet temperature (±30 K), mass flow rate (±5%), and the external hot-gas temperature profile (±2% of radial profile shape). Peak wall temperature varied by up to 22 K across the sweep, which is non-trivial given the fatigue sensitivity. A formal uncertainty propagation (e.g., Monte Carlo or polynomial chaos) has not been done — that was deferred to Phase III per the original SOW. What we have is essentially a manual sensitivity table, not a rigorous uncertainty band.

I want to be clear that the 22 K spread does not represent a full uncertainty estimate. It's a partial sensitivity result and should not be reported as a ±22 K confidence interval.

---

## Intended Use and Applicability

The model is intended for relative comparison of cooling channel design variants at take-off conditions only. It has not been evaluated at cruise or ground idle, and extrapolating these results to off-design conditions would require additional validation. The fatigue life team should be aware that they are receiving a point-condition result, not an envelope.

---

## What We Have Not Addressed

A few items are explicitly out of scope or deferred:

- **Oxidation and thermal barrier coating degradation:** not modeled; blade is treated as bare Inconel-718. TBC effects are deferred to a separate materials analysis.
- **Rotating frame effects:** the model is in a stationary reference frame. Coriolis and buoyancy effects in the rotating passages are not captured. This is a known simplification — prior literature suggests up to 15% effect on local Nusselt number in the radial passages.
- **Software configuration and version control:** I have not documented the specific Fluent solver patch level or the UDF versions used for the film-cooling boundary condition in a formal configuration log. This needs to be fixed before the review. The files exist on the shared drive but are not formally archived.

---

## Summary Assessment

| Area | Status |
|---|---|
| Geometry fidelity | Acceptable with noted simplifications |
| Mesh quality / refinement | GCI < 2%, defensible |
| Solver verification (benchmarks) | Partial — two cases, modest agreement |
| Experimental validation | Weak — one geometrically dissimilar legacy case |
| Uncertainty quantification | Incomplete — sensitivity only, no formal UQ |
| Intended use documentation | Adequate for current phase |
| Software configuration records | Not yet formalized — action item |

Overall, I would characterize this model as suitable for design screening comparisons but not yet at a level I'd be comfortable defending as a standalone predictive tool for life certification. The validation gap is the primary concern.

Happy to discuss before the 28th.

— J. Hollenbeck
