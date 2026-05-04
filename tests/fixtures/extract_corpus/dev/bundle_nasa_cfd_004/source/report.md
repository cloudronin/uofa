# TECHNICAL MEMORANDUM

**To:** Dr. Priya Nandakumar, Project Lead — Turbomachinery Aerodynamics Group
**From:** Marcus Ellenbogen, CFD Methods & Validation
**Date:** 2024-11-14
**Subject:** V&V Status Summary — Centrifugal Compressor Stage CFD Model (CCSIM-4.2)
**Distribution:** Restricted — Internal Use Only

---

## Purpose

This memo summarizes the current verification and validation posture of the CCSIM-4.2 Reynolds-Averaged Navier-Stokes model used to predict aerodynamic performance (pressure ratio, isentropic efficiency, surge margin) in the Stage-7 centrifugal compressor. The simulation framework is being considered for design-of-record decisions in the next development phase, so a structured assessment of its technical credibility is warranted before that transition.

---

## Computational Framework

CCSIM-4.2 runs within ANSYS Fluent 2023 R2 using the SST k-ω turbulence closure. The computational domain spans the full impeller passage (36-blade periodic sector with one-passage periodicity enforced), the vaneless diffuser, and the volute. Inlet boundary conditions are derived from rig instrumentation at Station 1 (total pressure, total temperature, and flow angle from five-hole probe traverses). The outlet uses a radially-averaged static pressure boundary condition matched to the downstream plenum measurement.

The simulation team consists of three engineers with backgrounds in turbomachinery CFD. Two have more than eight years of relevant experience; one is a junior analyst in her second year. All work is conducted under the group's documented CFD Practices Standard (CPS-Rev-F), which specifies required solver settings, convergence criteria, and output checklists.

---

## Code Pedigree and Prior Testing

Before discussing case-specific results, it is worth noting that ANSYS Fluent has an extensive history of independent testing across the turbomachinery community. The SST k-ω implementation in particular has been validated against numerous NASA and DLR benchmark compressor cases (Rotor 37, SRV2-O, and others). Our group additionally ran a series of internal code-correctness checks earlier this year: manufactured-solution tests for the compressible RANS solver confirmed that spatial discretization converges at second order in smooth regions, consistent with the scheme's formal accuracy. These checks were performed on simplified channel and pipe geometries before any compressor-specific work began. No anomalies were identified.

---

## Mesh Refinement Study and Numerical Uncertainty

A three-level mesh refinement study was completed on the impeller-only subdomain using a constant refinement ratio of √2 in each coordinate direction, yielding cell counts of approximately 1.8 M, 5.1 M, and 14.4 M elements. The Grid Convergence Index (GCI) methodology (Roache, 1998) was applied to the stage total-to-total pressure ratio at the design operating point (N/√T = 95%, ṁ = 4.62 kg/s). Observed order of convergence was 1.87, consistent with the second-order scheme. The GCI on the fine-to-medium pair was 0.41%, indicating that numerical discretization error is well below the measurement uncertainty band (±1.1% on pressure ratio from the rig). All subsequent production runs use the medium mesh (5.1 M cells) as the baseline, with the fine mesh reserved for sensitivity checks at off-design points.

Residuals for continuity, momentum, and energy were driven below 10⁻⁵ for all reported cases. Mass imbalance across domain interfaces was confirmed below 0.05% in every run. Iterative convergence was additionally verified by monitoring the running average of efficiency over the final 500 iterations; variation was less than 0.1 efficiency points.

---

## Comparison Against Experimental Data

The rig test campaign (conducted at the Hannover Turbomachinery Test Facility, October 2023) provided the primary validation dataset. Measurements include stage total pressure ratio, total temperature ratio, and shaft power at nine speed lines between 60% and 100% corrected speed, with approximately 7–12 throttle points per speedline. Uncertainty quantification on the rig measurements was performed by the test team using the ASME PTC 10 methodology; combined standard uncertainties are ±0.8% on pressure ratio and ±0.4 efficiency points.

At design speed, CCSIM-4.2 predicts pressure ratio within 0.9% of the measured mean and isentropic efficiency within 1.1 points — both within the experimental uncertainty band. At 80% speed, the pressure ratio agreement degrades slightly to 1.7% deviation; this is attributed to stronger secondary flow structures at part-load that the SST k-ω model is known to handle less precisely. At near-surge conditions, the model over-predicts pressure ratio by 2.4%, which exceeds the measurement uncertainty. The team has flagged this as an area requiring further investigation, potentially through LES or Scale-Resolving Simulation (SRS) at the near-surge point. These discrepancies are documented in the model's limitation register.

Validation coverage spans the full intended operating envelope defined in the Stage-7 requirements document (SR-0041-Rev-C). No extrapolation beyond the validated speed range is currently claimed.

---

## Sensitivity to Boundary Conditions and Model Inputs

A structured sensitivity study was performed to assess how prediction uncertainty propagates from input uncertainties. Inlet total pressure and total temperature were each varied by ±2σ of their measured uncertainty distributions. Turbulence intensity at the inlet was varied from 1% to 5% (the rig value is estimated at 2–3% but not directly measured). Surface roughness on the impeller blades was varied between hydraulically smooth and Ra = 3.2 µm (the as-manufactured tolerance). Across all these perturbations, stage efficiency sensitivity was less than 0.6 points — smaller than the experimental uncertainty — which gives reasonable confidence that the model's predictions are not unduly driven by uncertain inputs. The inlet flow angle, however, showed a sensitivity of 1.2 efficiency points per degree of angle deviation; this motivated tighter tolerance requirements on the five-hole probe alignment procedure for future rig entries.

---

## Applicability to the Intended Use Case

The primary intended use of CCSIM-4.2 is to support impeller blade redesign studies targeting a 2-point efficiency improvement while maintaining surge margin. The physics captured by the model — compressible RANS with rotating frame treatment, mixing-plane interfaces at the impeller-diffuser junction — are appropriate for this purpose. The model does not resolve tip clearance vortex dynamics at the sub-millimeter scale; tip gap is represented as a fixed 0.35 mm uniform clearance. For the redesign application (which is not expected to change tip clearance), this simplification is acceptable. If future use cases involve tip clearance sensitivity studies, the model scope would need to be revisited.

The team has explicitly documented in the model's scope statement that CCSIM-4.2 is not intended for acoustic noise prediction, transient surge event simulation, or ice ingestion scenarios. These exclusions are appropriate given the current validation evidence.

---

## Team Competency and Process Controls

The CFD group operates under CPS-Rev-F, which mandates peer review of all case setup files before a production run is submitted. Each analysis package undergoes a two-person review: one reviewer checks boundary conditions and mesh quality metrics (y+ distribution, aspect ratio, skewness), and a second reviews post-processing scripts and result interpretation. A third-party audit of the process was conducted by the company's Independent Technical Review Board in September 2024; no major findings were issued, and two minor observations (related to version control tagging of mesh files) were closed before this memo was written.

The junior analyst's work on the off-design speedlines was independently reproduced by a senior engineer using a parallel setup to confirm results — a practice the group adopted after a mesh-import error caused a one-month delay on a previous project. Documentation of all runs, including input decks, mesh files, and post-processing notebooks, is maintained in the group's GitLab repository under project CCSIM-4.

---

## Summary Assessment

On balance, CCSIM-4.2 presents a credible simulation capability for the intended impeller redesign application. The mesh refinement study demonstrates that numerical errors are well-controlled. Validation against the October 2023 rig dataset shows acceptable agreement across most of the operating envelope, with clearly documented discrepancies at near-surge conditions. Input sensitivity is understood and bounded. The team's process controls and experience level are appropriate for the complexity of the task.

The near-surge prediction gap (2.4% pressure ratio error) should be tracked as a model limitation in any design decisions that involve operating points within 5% of the surge line. I recommend the team complete the planned SRS study at the near-surge point before CCSIM-4.2 is used for any surge-margin-critical design decisions.

No blocking issues are identified for using the model in the impeller blade profile redesign study.

---

*Marcus Ellenbogen*
*Senior CFD Engineer, Turbomachinery Aerodynamics Group*
*Ext. 4-7823 | m.ellenbogen@aero-eng.internal*
