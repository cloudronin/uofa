# INTERNAL TECHNICAL MEMO

**To:** Dr. Priya Nambiar, Project Lead — Turbomachinery CFD Program
**From:** J. Castellano, CFD Methods & Validation Group
**Date:** 14 March 2025
**Subject:** V&V Status Summary — Centrifugal Pump Stage CFD Model (Rev. C)
**Reference:** TMCFD-2024-047, Solver: ANSYS Fluent 2023 R2

---

## 1. Purpose

This memo summarizes the current verification and validation standing for the centrifugal pump stage CFD model developed under contract TMCFD-2024-047. The model is intended to support design decisions on impeller geometry and volute sizing for a 450 kW process pump operating at 1,480 rpm. I'm writing ahead of the PDR gate review next month so the team has a clear picture of what's solid, what needs attention, and where we still have open items.

---

## 2. Solver Integrity and Numerical Housekeeping

Before getting into physics comparisons, I want to flag that we did run the solver through our standard code-health checks. Fluent 2023 R2 was exercised against the ASME V&V 20 benchmark suite (backward-facing step, lid-driven cavity) and our in-house manufactured-solution test for incompressible RANS. Residuals for the manufactured solution converged to machine precision, confirming the implementation is consistent with its published discretization scheme. No anomalous behavior was observed; the solver behaves as documented. This is largely a formality given Fluent's maturity, but it's worth noting for the record.

---

## 3. Mesh Refinement Study and Numerical Uncertainty

Three structured hexahedral meshes were generated using ANSYS Meshing: coarse (~2.1M cells), medium (~6.8M cells), and fine (~18.4M cells). The refinement ratio between successive levels is approximately 1.45 (volumetric). We used the Grid Convergence Index (GCI) methodology per Celik et al. (2008) to estimate numerical uncertainty on the primary QoI — pump total head at the best-efficiency point (BEP).

Results: GCI_fine = 1.8% on total head, with an observed order of convergence p ≈ 1.92, close to the formal second-order accuracy of the pressure-velocity coupling scheme. The solution is judged to be in the asymptotic range (GCI ratio = 1.03). We are satisfied that spatial discretization error is well-characterized. Temporal discretization is not applicable here as steady RANS (MRF) was used.

---

## 4. Turbulence Modeling and Physical Fidelity

We evaluated three turbulence closures: standard k-ε, realizable k-ε, and SST k-ω. Head-flow curve predictions at BEP showed the SST k-ω model within 2.3% of experimental data from our in-house test loop (see §6), while standard k-ε overpredicted head by ~7% at off-design conditions. The SST model was selected as the production closure. Wall y+ values on impeller blade surfaces were maintained between 30–60 for the wall-function treatment, consistent with the model's intended usage range.

It is worth noting that we have not run LES or SAS-SST to bound turbulence model form error — this was descoped from the current phase due to computational budget constraints. The SST selection is well-supported by literature for this class of pump geometry, but the team should be aware there is an unquantified modeling uncertainty contribution here beyond what the GCI captures.

---

## 5. Boundary Conditions and Operating Envelope

Inlet boundary conditions were derived from upstream pipe measurements provided by the test facility (total pressure profile, turbulence intensity ~4.2%, length scale 0.012 m). These are considered high-quality inputs. The outlet was set to a mass-flow boundary with a static pressure correction applied iteratively to match the measured sump level.

The model has been exercised across seven operating points from 60% to 115% of design flow. Boundary condition sensitivity was checked at BEP by varying inlet turbulence intensity ±50% — head prediction shifted by less than 0.4%, indicating low sensitivity at this condition. Off-design behavior near shut-off was not fully explored and is flagged as a limitation.

---

## 6. Experimental Comparisons and Validation Evidence

Validation data comes from two sources: (a) our own pump test loop at the Hannover facility, and (b) published impeller performance data from Gülich (2008) for a geometrically similar specific-speed machine (Ns ≈ 28 metric).

**Test loop data:** Head, shaft power, and efficiency were measured at seven operating points. Instrumentation uncertainty was formally quantified per ISO 9906 Grade 1: ±0.8% on flow, ±0.5% on head, ±1.1% on efficiency. CFD head predictions fall within the combined experimental + numerical uncertainty band at five of seven operating points. The two outliers are at 65% and 110% of design flow; at 65%, CFD underpredicts head by 4.1% (outside the uncertainty band), which we attribute to recirculation onset that the steady RANS model handles poorly.

**Published data:** Agreement with Gülich reference curves is qualitatively consistent; this comparison is used as a secondary plausibility check only, not a primary validation metric.

Overall, the validation evidence is considered adequate for design-support use at and near BEP. Extrapolation to off-design conditions, particularly below 70% of design flow, carries elevated uncertainty.

---

## 7. Relevance of the Validation Experiments to the Prediction Case

The test loop pump is a 1:1 scale replica of the design geometry — no scaling corrections are required. Operating conditions (rotational speed, fluid temperature, density) match the design intent within 1.5%. The primary difference between the validation case and the prediction case is that the production pump will use a slightly modified volute tongue geometry (tighter cutwater clearance, 3% reduction). This geometric delta has not been explicitly validated and introduces a degree of extrapolation that the team should factor into confidence statements.

---

## 8. Uncertainty Quantification and Confidence in Predictions

A formal uncertainty budget was assembled combining: (a) numerical/spatial discretization uncertainty (GCI-based, 1.8%), (b) inlet boundary condition uncertainty (propagated via ±10% variation in turbulence length scale, yielding <0.3% on head), and (c) experimental measurement uncertainty (ISO 9906, ~0.9% combined on head). Turbulence model form error was not formally quantified (see §4 caveat).

The total combined uncertainty on BEP head prediction is estimated at ±2.5% (k=2, 95% confidence). This is considered acceptable for the current design phase. Efficiency predictions carry higher uncertainty (~4%) due to torque sensitivity.

---

## 9. Model Pedigree and Prior Use

The meshing strategy, solver settings, and post-processing workflow are based on a validated template previously applied to two similar pump programs (TMCFD-2021-031 and TMCFD-2022-019), both of which passed independent technical review. The current model inherits that pedigree with documented modifications for the new geometry. Configuration control is maintained in GitLab (repo: tmcfd-047, tag: RevC-PDR). All mesh files, case files, and results are archived per our data management plan.

---

## 10. Independent Review and Peer Scrutiny

The Rev. B model (predecessor to this revision) was reviewed by Dr. F. Hartmann (external, TU Braunschweig) in January 2025. His primary comments concerned the volute mesh density near the tongue, which has since been addressed in Rev. C (cell count in that region increased 2.4×). A written response to all review comments is on file. Rev. C has not yet received a formal external review — this is planned for the post-PDR phase. Internal peer review by A. Osei (senior CFD engineer, not on the project team) was completed 28 February 2025 with no major findings.

---

## 11. Intended Use and Applicability Boundaries

The model is sanctioned for: (a) relative comparison of impeller blade angle variants at BEP ±15%, (b) volute sizing sensitivity studies, and (c) estimation of hydraulic efficiency trends. It is **not** currently sanctioned for: absolute prediction of NPSH margin (cavitation modeling not included), transient pressure pulsation analysis, or performance below 70% design flow. These limitations are documented in the model's scope-of-use register (TMCFD-047-SUR-Rev1).

---

## 12. Open Items Before Gate Review

| # | Item | Owner | Due |
|---|------|-------|-----|
| 1 | Quantify turbulence model form error (SST vs. SAS-SST at BEP) | Castellano | 30 Apr |
| 2 | Validate volute tongue geometry delta | Nambiar/Test | Post-PDR |
| 3 | External review of Rev. C | Hartmann (TBC) | Post-PDR |
| 4 | Extend operating range validation to 115% flow point | Castellano | 15 Apr |

---

## 13. Summary Assessment

In my judgment, the Rev. C model is in good shape for PDR-level design support at near-BEP conditions. The mesh refinement study is thorough, the experimental comparisons are well-instrumented and properly uncertainty-quantified, and the solver has been checked for correctness. The main gaps are the unquantified turbulence model uncertainty and the unvalidated volute tongue modification. Neither is a showstopper for PDR, but both need to be resolved before the model is used for final design sign-off.

Please let me know if you want me to present the full GCI tables and validation plots at the pre-PDR team meeting.

— J. Castellano
