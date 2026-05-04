# INTERNAL TECHNICAL MEMO

**To:** Dr. Priya Nambiar, Project Lead — Centrifugal Pump CFD Program
**From:** Marcus Teel, Computational Methods Group
**Date:** 14 March 2025
**Re:** V&V Status Update — Pump Stage Flow Solver, Pre-CDR Snapshot
**Distribution:** Restricted (CFD Team + Systems Integration)

---

## Purpose

This memo summarizes where we stand on credibility of the RANS-based flow solver results for the Stage 2 impeller discharge analysis ahead of the Critical Design Review. I'm flagging areas where confidence is reasonably high, areas where work is still thin, and a couple of things we simply haven't gotten to yet. Not everything is covered here — the inlet recirculation sub-model assessment and the turbulence model sensitivity sweep are both deferred to Phase 3 per the updated SOW.

---

## Solver and Configuration

We're running ANSYS Fluent 2023 R2 with the realizable k-ε turbulence closure on a structured hexahedral mesh generated in ICEM CFD. Operating point of interest is 1450 RPM, 85 m³/hr flow rate, with a total pressure rise target of 310 kPa. The computational domain spans from inlet flange to volute exit, including the full 360° impeller wheel (no periodic simplification at this stage). Wall functions are applied at y⁺ ≈ 35–55 across most blade surfaces.

---

## Code Pedigree and Prior Use

Fluent 2023 R2 has an extensive record of use in rotating machinery applications within our group. We ran the predecessor campaign (Stage 1 analysis, 2022) with Fluent 2022 R1 and validated against the vendor pump curve data from Sulzer. That prior work established baseline confidence in the solver's handling of rotor-stator interfaces using the frozen rotor approximation. The current configuration inherits those setup practices. No new numerical schemes have been introduced relative to that baseline, so we consider the underlying solver implementation adequately characterized for this class of problem. One caveat: the volute geometry in Stage 2 is substantially different from Stage 1 (asymmetric tongue geometry), and we have not yet re-evaluated whether the frozen rotor treatment introduces meaningful error at the new interface location. That's a known gap.

---

## Mesh Refinement Study

A three-level mesh refinement study was completed using cell counts of approximately 4.1M, 9.8M, and 22.4M cells. The refinement ratio is roughly 1.53 between levels (volumetric). We computed the Grid Convergence Index following the Roache procedure. For total pressure rise at the design point, GCI values between the medium and fine meshes came in at 1.8%, which we consider acceptable. Velocity profiles at the volute tongue cross-section showed somewhat higher GCI (~4.1%) but are within our internal threshold of 5%. The medium mesh (9.8M cells) was selected for production runs on the basis of this study. We did not perform a formal Richardson extrapolation estimate of the "true" solution, though the trend is monotonically convergent.

---

## Iterative Convergence

All production runs were carried to residual levels below 1×10⁻⁵ for continuity and momentum equations. Mass imbalance across the domain was confirmed below 0.01% in all cases. We monitored total pressure rise and radial force on the impeller as solution monitors; both stabilized to less than 0.2% variation over the final 500 iterations before declaring convergence. This is consistent with our standard convergence criteria documented in the project QA plan.

---

## Comparison Against Physical Test Data

Experimental measurements were obtained from the pump test loop at our Hannover facility in February 2025. The test covered five flow rates from 60 to 110 m³/hr. At the design point (85 m³/hr), the CFD-predicted total pressure rise is 307 kPa versus the measured 312 kPa — a discrepancy of approximately 1.6%. This is within the stated simulation acceptance criterion of ±3%. At off-design conditions (60 m³/hr), the discrepancy grows to roughly 6.3%, which exceeds our threshold. We believe this is related to the inlet recirculation regime that the realizable k-ε model handles poorly, but a formal sensitivity study has not been done. The off-design performance is flagged as a limitation but is not in scope for CDR sign-off.

Uncertainty in the experimental measurements was characterized using the facility's calibration records. Pressure transducer uncertainty is ±0.8 kPa (k=2), and flow rate uncertainty is ±0.5 m³/hr. These are small relative to the design-point discrepancy and do not change the conclusion.

---

## Input Data and Boundary Conditions

Boundary conditions were drawn from the system hydraulic model maintained by the Hannover integration team (document HYD-2024-117, rev C). Inlet total pressure, temperature (293 K), and turbulence intensity (3.5%) were specified. The outlet boundary uses a mass flow rate condition. Fluid properties (water at 20°C) are from standard NIST tables. No sensitivity analysis on boundary condition uncertainty has been performed for this memo — that work is planned but not yet executed.

---

## Documentation and Traceability

Simulation input files, mesh files, and convergence logs are archived in the project Confluence space under CFD/Stage2/Production_Runs. Run scripts are version-controlled in GitLab (tag: CDR_snapshot_v1.4). Post-processing was done in CFD-Post and Tecplot 2023; macros are stored alongside the run scripts. A senior engineer (not the analyst who ran the cases) reviewed the setup files against the documented run plan — discrepancies found were minor (a boundary condition label mismatch on one inlet patch, corrected before production runs). We consider the documentation trail adequate for this review milestone.

---

## Items Not Addressed in This Memo

The following topics are explicitly out of scope for this update and will be addressed in Phase 3 or a separate deliverable:

- **Turbulence model sensitivity:** No comparison between k-ε, SST k-ω, and any scale-resolving approach has been completed. Given the known sensitivity of volute flow predictions to turbulence closure, this is a real gap that reviewers should note.
- **Inlet recirculation sub-model:** Assessment deferred per SOW amendment 3.
- **Uncertainty propagation from manufacturing tolerances:** The as-built impeller geometry deviates from CAD by up to 0.15 mm on blade trailing edges (per CMM report QC-2025-044). The effect of this on predicted performance has not been evaluated.

---

## Summary Assessment

At the design operating point, confidence in the CFD predictions is moderate-to-good. The mesh refinement study is solid, iterative convergence is well-established, and agreement with test data is within acceptance criteria. The code has a reasonable track record for this class of problem. The primary weaknesses going into CDR are the lack of turbulence model sensitivity data and the unquantified effect of as-built geometry variation. Off-design prediction quality is poor and acknowledged. I'd recommend the project proceed to CDR with these limitations formally noted in the model use justification.

Reach out if you want me to run through any of this in the pre-CDR walkthrough.

— Marcus
