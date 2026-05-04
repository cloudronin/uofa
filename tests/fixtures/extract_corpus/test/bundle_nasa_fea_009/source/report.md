# INTERNAL TECHNICAL MEMO

**TO:** Dr. Priya Nambiar, Structural Analysis Lead
**FROM:** M. Calloway, V&V Engineer, Loads & Dynamics Group
**DATE:** 14 March 2025
**RE:** FEA Credibility Status — Composite Fuselage Frame Section, Rev C Model
**DISTRIBUTION:** Restricted — Program Core Team Only

---

## Purpose

This memo summarizes the current verification and validation standing for the Rev C finite-element model of the aft fuselage frame assembly (Frame Stations 447–512), developed in ABAQUS/Standard 2023.HF4. The model is being used to predict peak interlaminar shear stress and out-of-plane deflection under combined pressure and inertial loading. A formal board review is scheduled for 28 March; this memo captures where we stand and flags areas that need attention before that date.

---

## Background on the Analysis

The frame is a hybrid carbon-fiber/titanium insert assembly. The FEA model contains approximately 1.4 million elements, predominantly C3D8R continuum bricks with enhanced hourglass control in the laminate regions and C3D6 wedge elements at ply drop-offs. Two loading cases are under active review: (1) limit pressure differential of 9.1 psi with 2.5g vertical inertial load, and (2) a ground handling case at 1g with asymmetric point loads from cargo handling equipment. The Rev C model differs from Rev B primarily in the contact treatment at the titanium fastener holes — we switched from tied constraints to small-sliding surface interactions, which changed peak stress predictions by roughly 14% in the fastener neighborhood.

---

## What the Model Is Supposed to Do

The intended use is stress certification support for a specific structural zone, not a full-vehicle loads analysis. The geometry is bounded: we are not modeling global fuselage bending, only the local frame response with prescribed displacement boundary conditions transferred from a separate global model. This scope limitation is important context for everything that follows — several of the concerns raised below would look different if the model were being used for a broader purpose.

**However, there is a scope ambiguity that needs to be resolved.** Early in the program (see email thread archived under PDM ticket #FEA-0091), the model was described as supporting both certification and a fatigue life screening study. The Rev C model documentation (Section 1.2) explicitly states the model is *not* validated for cyclic loading assessment, yet the fatigue group's latest analysis plan (Rev D, dated 6 Feb 2025) lists this model as the stress input source for their Goodman diagram calculations. Either the fatigue team needs a different model, or the validation scope needs to be extended. This discrepancy has not been resolved.

---

## Numerical Accuracy and Mesh Behavior

A mesh refinement study was completed in January using three successive mesh densities (coarse ~340K elements, medium ~820K, fine ~1.4M). The quantity of interest was peak in-plane principal stress at the ply drop-off radius. Richardson extrapolation gives an estimated discretization uncertainty of approximately ±4.2% on that quantity at the fine mesh level, which is acceptable for our purposes.

**Inconsistency flagged:** The mesh refinement study report (Doc FEA-VER-009, Rev A) states that the medium and fine meshes are "in good agreement, with less than 2% difference in peak stress." However, the raw output tables in Appendix B of that same document show a 7.3% difference between those two meshes for the out-of-plane shear stress component, which is actually the more safety-relevant quantity for delamination prediction. It is unclear whether the 2% figure refers only to in-plane stress or whether there was a data transcription error. This needs to be clarified before the board review.

Software verification checks were performed per our standard checklist: patch tests passed, the built-in ABAQUS benchmark cases for C3D8R elements under bending were reproduced within 0.1%, and a hand-calculation cross-check on a simplified single-ply coupon gave agreement within 3%. The ABAQUS solver itself is a commercial code with extensive independent verification history; we are relying on that pedigree and have not conducted independent line-by-line code review, which is standard practice for commercial FEA tools in this program.

---

## Comparison to Physical Test Data

Validation against hardware is the area of greatest concern right now. We have coupon-level test data from a 2022 test campaign (12 specimens, quasi-isotropic layup, three-point bending) that were used to calibrate the interlaminar shear strength allowables. The model predictions for those coupon tests are within ±8% of measured failure load, which is reasonable.

**The problem is at the component level.** A full-scale frame section test (Test Article TA-03) was conducted in November 2024. That test produced measured deflections at three gauge locations. The Rev C model predicts deflections that are 6–11% lower than measured at all three locations, consistently. The Rev B model, which used tied constraints at fastener holes, actually showed better agreement with TA-03 (within 3%). The switch to small-sliding contact in Rev C improved theoretical fidelity at the fastener holes but degraded agreement with the component test. The team's current hypothesis is that the prescribed displacement boundary conditions from the global model are not accurately capturing the actual load introduction in the test fixture, but this has not been confirmed. Until the source of this discrepancy is understood, I would characterize the component-level validation as incomplete and the confidence in the Rev C predictions as lower than the Rev B baseline — which is an uncomfortable position to be in heading into a board review.

---

## Input Data and Material Properties

Material properties were drawn from the program material database (MatDB v4.1), which sources lamina properties from MIL-HDBK-17 basis values combined with in-house coupon testing. The database is configuration-controlled and has been through an independent data quality review. No concerns with the material input data itself.

Boundary conditions from the global model were transferred via a Python extraction script. The script has been reviewed by one engineer (T. Okafor) but has not gone through formal peer verification. Given that the boundary condition transfer is a plausible explanation for the TA-03 discrepancy mentioned above, this is a gap.

---

## Sensitivity and Uncertainty

A limited sensitivity study was run varying the interlaminar shear modulus G₁₃ by ±15% (the property with highest reported test scatter). Peak out-of-plane shear stress changed by approximately ±9%, confirming this is an important parameter. No broader uncertainty propagation has been done — the team cited schedule pressure as the reason, intending to address this post-board if the design is not changed. That is a defensible decision given the timeline, but it should be documented explicitly as a known gap rather than left implicit.

---

## Independent Review and Oversight

The model and its documentation have been reviewed by one independent structural analyst (Dr. F. Marchetti, external consultant) who examined the mesh quality metrics and the contact formulation. His review memo (dated 22 Feb 2025) concluded the model is "technically sound with no fundamental errors identified." He did not, however, review the validation data comparisons or the boundary condition transfer script — his scope was limited to the numerical formulation. A second independent reviewer with V&V background has not been assigned, which is a gap relative to the program's stated V&V plan.

---

## Summary Assessment

| Area | Status |
|---|---|
| Intended use / scope clarity | **OPEN** — fatigue use conflict unresolved |
| Mesh refinement / numerical accuracy | **CONDITIONAL** — 2% vs 7.3% discrepancy in mesh study report needs resolution |
| Software verification | **ACCEPTABLE** — commercial code pedigree, standard benchmarks passed |
| Coupon-level validation | **ACCEPTABLE** — ±8% agreement |
| Component-level validation | **CONCERN** — Rev C shows worse agreement than Rev B; root cause unknown |
| Material input data | **ACCEPTABLE** |
| Boundary condition transfer | **GAP** — script not formally verified |
| Uncertainty quantification | **PARTIAL** — single-parameter sensitivity only; broader UQ deferred |
| Independent technical review | **PARTIAL** — formulation reviewed; V&V-focused review not yet assigned |

---

## Recommended Actions Before 28 March Board

1. Resolve the 2% vs 7.3% discrepancy in Doc FEA-VER-009 Appendix B. Determine whether the mesh refinement conclusion holds for out-of-plane shear stress specifically.
2. Formally document the fatigue use conflict and get a decision from the program office: either expand validation scope or direct the fatigue team to a different model.
3. Investigate the TA-03 deflection discrepancy. At minimum, document the leading hypothesis (BC transfer error) and confirm or refute it with a sensitivity run using perturbed boundary conditions.
4. Assign a second independent reviewer with V&V background prior to the board.
5. Add a formal documented statement to the model report acknowledging the deferred UQ scope.

I am available to discuss any of these items. The situation is manageable but requires deliberate action in the next two weeks.

— M. Calloway
