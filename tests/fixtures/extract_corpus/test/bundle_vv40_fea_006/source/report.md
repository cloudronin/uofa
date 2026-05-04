# Credibility Assessment Report
## Finite Element Analysis of a Titanium Alloy Hip Stem Implant Under Cyclic Loading
### Project: OrthoStem-7 Structural Integrity Program
### Document Ref: OSP-FEA-CR-2024-011 | Revision B | 2024-09-18

---

## 1. Background and Scope

This report documents the credibility assessment of the finite element analysis (FEA) model developed to evaluate the structural integrity of the OrthoStem-7 cementless hip stem under ISO 7206-4 fatigue loading conditions. The model was developed by the Computational Mechanics Group (CMG) at Meridian Biomedical Engineering, LLC, and is intended to support a 510(k) regulatory submission as supplementary computational evidence alongside physical bench testing.

The implant is a titanium alloy (Ti-6Al-4V ELI, ASTM F136) tapered wedge stem, available in seven sizes. All FEA work was performed on the Size 4 geometry, which internal risk analysis identified as the worst-case configuration based on cross-sectional moment of inertia. The analyses were conducted in Abaqus/Standard 2023.HF4 (Dassault Systèmes) on a 128-core Linux cluster running RHEL 8.6.

The purpose of this assessment is to evaluate whether the computational model is sufficiently credible to support the intended regulatory decision — specifically, a finding that peak von Mises stress under the ISO 7206-4 loading envelope remains below the material fatigue limit with an appropriate safety margin.

---

## 2. Assessment Framework and Methodology

The assessment follows the ASME V&V 40-2018 framework, adapted for Class II medical device computational modeling. Each credibility factor was evaluated by an independent reviewer (the author) who was not involved in the original model development. Evidence was gathered from the Model Development Report (MDR-OSP-2024-007), raw solver output archives, mesh files, and interviews with the primary analyst.

Factor assessments are presented in order of the reviewer's judgment of their relative influence on the decision of interest, beginning with those most likely to drive uncertainty in the regulatory conclusion.

---

## 3. Results and Credibility Factor Assessments

### 3.1 Relevance of the Question Being Answered

The model's intended purpose is clearly articulated in the MDR: predict peak cyclic stress in the stem neck region under the ISO 7206-4 four-point bending configuration at 2300 N load magnitude. The regulatory decision — whether the design meets a 10⁷-cycle fatigue life requirement — is explicitly linked to this output quantity. The geometry, loading, and boundary conditions were all selected with this specific question in mind, and the scope has not drifted across the three model revisions documented in the MDR.

**Assessment: The question of interest is well-defined and consistently applied throughout the modeling effort. High confidence that the model is solving the right problem.**

---

### 3.2 Geometric and Simulation Input Fidelity

CAD geometry was imported directly from the manufacturing master file (OrthoStem-7_S4_Rev3.STEP) with no simplifications applied to the critical neck region. The distal stem taper was simplified by removing three small chamfer features (< 0.3 mm radius) in regions identified as non-load-bearing based on a preliminary coarse-mesh sensitivity run. Thread features on the proximal collar were suppressed as they are not present in the final device geometry.

Material properties were assigned from coupon-level tensile and fatigue testing on the same heat of Ti-6Al-4V ELI used for prototype fabrication. Elastic modulus: 114 GPa ± 2.1 GPa (n=12 specimens); Poisson's ratio: 0.342; density: 4430 kg/m³. Fatigue limit at 10⁷ cycles: 620 MPa (R = −1), reduced by a surface finish knockdown factor of 0.87 per MMPDS-12 Table 5.3.1.1 to an applied limit of 539 MPa. All material inputs are traceable to calibrated test equipment with current NIST-traceable calibration certificates on file.

The ISO 7206-4 fixture geometry — including the embedding medium (bone cement simulant) and load application angle of 10° from the stem axis — was replicated in the model. Cement simulant was modeled as a linear elastic material (E = 2.5 GPa) with a tied interface to the stem surface below the embedding line.

**Assessment: Model inputs are well-documented and traceable. Minor geometric simplifications are justified and confined to non-critical regions. Material data quality is high.**

---

### 3.3 Numerical Solution Quality and Mesh Refinement Study

A structured mesh refinement study was conducted across four mesh densities, designated M1 through M4, with element counts ranging from 84,000 to 1,240,000 second-order tetrahedral elements (C3D10). The neck fillet region — the location of maximum stress concentration — was refined independently using a bias ratio of 8:1 relative to the bulk mesh.

| Mesh | Elements | Peak von Mises (MPa) | Change vs. Prior |
|------|----------|----------------------|------------------|
| M1   | 84,000   | 487.3                | —                |
| M2   | 218,000  | 511.6                | +4.99%           |
| M3   | 512,000  | 519.4                | +1.52%           |
| M4   | 1,240,000| 521.1                | +0.33%           |

Richardson extrapolation applied to M3 and M4 yields an estimated asymptotic value of 521.6 MPa, giving a Grid Convergence Index (GCI) of 0.18% for M4. The M3 mesh was selected for production runs as a balance of accuracy and computational cost, with the GCI on M3 of 0.64% — well within the project's stated acceptance threshold of 2.0%.

Element quality metrics for M3: mean aspect ratio 1.84, maximum aspect ratio 6.2 (located in the distal taper simplification zone, not in the critical region), Jacobian ratio > 0.6 for 99.7% of elements.

**Assessment: Rigorous and well-documented mesh refinement study. Numerical discretization uncertainty is quantified and acceptably small relative to the safety margin.**

---

### 3.4 Solver and Code Trustworthiness

Abaqus/Standard 2023.HF4 is a commercially validated finite element solver with an extensive history of use in structural medical device analysis. The CMG maintains an internal software qualification record (SQR-CMG-ABQ-2023) that includes execution of the NAFEMS LE1, LE10, and FV52 benchmark problems, as well as the Hertzian contact benchmark from ASME V&V 10.1. All benchmarks passed against published reference solutions within 1.0% relative error.

Additionally, the solver's linear static stress solution was verified against a closed-form Euler-Bernoulli beam bending solution for a simplified cylindrical stem geometry. The FEA result (peak bending stress: 312.4 MPa) agreed with the analytical solution (310.8 MPa) to within 0.5%.

**Assessment: Code trustworthiness is well-established through both commercial pedigree and project-specific benchmark verification. No concerns identified.**

---

### 3.5 Model Verification — Are the Equations Solved Correctly?

Beyond the code-level benchmarks described above, the CMG performed model-specific verification checks. Reaction forces at the boundary conditions were summed and compared against applied loads: resultant force balance error < 0.01 N (applied load: 2300 N). Moment balance about the load application point was verified to < 0.05 N·m. Strain energy convergence between M3 and M4 differed by 0.21%.

Contact pressure distributions at the stem-cement interface were inspected for non-physical oscillations; none were observed. Symmetry was not assumed (the model is not symmetric under the 10° loading angle), and no symmetry boundary conditions were applied.

**Assessment: Model verification is thorough. The solution appears to be a correct numerical solution to the governing equations as posed.**

---

### 3.6 Validation Against Physical Test Data

This is the most consequential credibility factor for the regulatory submission. Physical bench testing was conducted on three Size 4 OrthoStem-7 specimens instrumented with five rosette strain gauges each, positioned at locations pre-selected by the analyst to correspond to high-stress model predictions.

Gauge positions were registered to the CAD geometry using a coordinate measuring machine (CMM) to within ±0.4 mm. The ISO 7206-4 fixture was assembled and the load applied at 2300 N quasi-statically for the validation test (not cyclic, to allow stable strain readings).

Comparison of predicted vs. measured principal strains at gauge locations:

| Gauge | Predicted (με) | Measured (με) | % Difference |
|-------|----------------|---------------|--------------|
| G1    | 1842           | 1871 ± 23     | −1.6%        |
| G2    | 2104           | 2089 ± 19     | +0.7%        |
| G3    | −1203          | −1244 ± 31    | −3.3%        |
| G4    | 988            | 1023 ± 28     | −3.4%        |
| G5    | 412            | 398 ± 41      | +3.5%        |

All five gauges show agreement within ±4%, which is within the project's pre-specified validation acceptance criterion of ±10% at the gauge locations. The validation was conducted blind — the analyst did not have access to the experimental data until after the model was frozen at M3.

It is noted that the validation was conducted at a single load level (2300 N) and a single specimen geometry (Size 4). Extrapolation of validation confidence to other sizes relies on geometric similarity arguments documented in MDR Appendix D, which the reviewer considers reasonable but not rigorously demonstrated.

**Assessment: Validation evidence is strong for the tested configuration. Limitation acknowledged for size extrapolation.**

---

### 3.7 Uncertainty Characterization and Sensitivity Analysis

A one-at-a-time (OAT) sensitivity study was performed varying the following inputs ±10% from nominal: elastic modulus, Poisson's ratio, cement modulus, load magnitude, and load angle. Results are summarized in Appendix A of this report.

The most influential parameter was load angle: a ±10% variation in the 10° application angle produced a ±6.8% change in peak von Mises stress. Elastic modulus variation produced a ±1.2% change. Cement modulus variation produced a ±3.1% change.

A formal probabilistic analysis (Monte Carlo or polynomial chaos expansion) was not performed. The MDR justifies this by noting that all input variations remain within the ISO 7206-4 fixture tolerance band, and that the OAT study spans the expected physical range. The reviewer concurs that a full probabilistic treatment is not required at this decision risk level, but notes that the load angle sensitivity is non-trivial and should be tracked if the loading protocol changes in future studies.

**Assessment: Uncertainty characterization is adequate for the regulatory context. The OAT approach is proportionate to the decision risk. Load angle sensitivity is flagged for monitoring.**

---

### 3.8 Applicability to the Intended Use Population

The model represents a single idealized loading scenario per ISO 7206-4. Clinical loading on hip implants is highly variable, encompassing gait, stair climbing, stumbling events, and patient weight variation. The MDR acknowledges this gap and explicitly states that the ISO 7206-4 test is not intended to replicate in-vivo loading but rather to provide a standardized comparative benchmark consistent with regulatory precedent.

The reviewer notes that this framing is appropriate and consistent with FDA guidance on computational modeling for orthopedic implants (FDA-2021-D-0728). The model does not claim to predict in-vivo performance directly; it claims to demonstrate compliance with a standardized test protocol, which is the correct framing for the intended regulatory use.

**Assessment: The relationship between the model's loading scenario and real-world use is clearly and correctly characterized. No overreach in claims.**

---

### 3.9 Documentation Quality and Reproducibility

The MDR (MDR-OSP-2024-007, Rev B) is comprehensive and well-organized. It includes: model description, input file listings, material property tables with traceability, mesh quality reports, solver settings (including convergence criteria: force residual < 10⁻⁵, displacement correction < 10⁻⁶), and results with uncertainty bounds. All Abaqus input files are archived in the CMG version control system (Git repository OSP-FEA-2024, commit hash 3f8a1c2).

An independent analyst within CMG performed a model rebuild from the MDR documentation alone and reproduced the M3 peak stress result to within 0.4% — confirming that the documentation is sufficient for independent reproduction.

**Assessment: Documentation is exemplary. Reproducibility has been actively demonstrated.**

---

### 3.10 Risk-Appropriate Level of Rigor

The OrthoStem-7 is a Class II medical device with a moderate-to-high consequence of failure (implant fracture leading to revision surgery). The CMG's credibility planning document (CPD-OSP-2024-002) assigned this model to a "high" consequence / "moderate" model influence tier, corresponding to a required credibility level that demands validation against physical data, quantified numerical uncertainty, and documented sensitivity analysis. The evidence assembled in this report satisfies those requirements.

**Assessment: The rigor of the modeling effort is well-matched to the risk level of the application. The credibility planning process was conducted before model development, not retrospectively.**

---

## 4. Summary of Findings

The FEA model of the OrthoStem-7 hip stem under ISO 7206-4 loading is assessed as **highly credible** for its intended regulatory use. Key findings:

- Peak von Mises stress in the neck fillet region: **519.4 MPa** (M3 mesh), with a GCI-corrected upper bound of **521.6 MPa**
- Applied fatigue limit (with surface finish knockdown): **539 MPa**
- Nominal safety margin: **3.4%** above the fatigue limit — this is acknowledged as a relatively thin margin
- Validation agreement: all gauges within ±4% of measured values
- All credibility factors assessed as meeting or exceeding the project's pre-specified acceptance criteria

The thin safety margin (519.4 MPa vs. 539 MPa limit) is the primary engineering concern and is flagged for the regulatory team. While the model is credible, the physical margin is narrow enough that the physical fatigue test results (to be reported separately under OSP-TEST-2024-018) should be reviewed jointly before the 510(k) submission is finalized.

---

## 5. Limitations and Recommendations

1. **Size extrapolation:** Validation was performed only on Size 4. Geometric similarity arguments for other sizes should be supplemented with at least one additional strain gauge validation on Size 2 (smallest, highest stress concentration) before claiming broad applicability across the product family.

2. **Load angle sensitivity:** The ±6.8% stress sensitivity to load angle warrants a tolerance study on the physical test fixture to confirm that the ISO 7206-4 setup angle is controlled to better than ±0.5°.

3. **Single-load-level validation:** The validation was conducted at 2300 N only. A secondary validation at 1500 N would strengthen confidence in the linear elastic regime assumption across the loading range.

4. **Probabilistic gap:** If the regulatory submission is challenged on uncertainty grounds, a targeted Monte Carlo study on the two most influential inputs (load angle, cement modulus) could be completed in approximately two weeks of additional analyst effort.

5. **Cement interface assumption:** The tied (no-slip) interface between stem and cement simulant is conservative for stress prediction in the stem but may not represent the worst case for interface debonding. This is outside the current model's scope but should be considered in a future fatigue-life model.

---

## 6. Reviewer Attestation

This assessment was conducted independently of the model development team. The reviewer has no financial interest in the outcome of the regulatory submission. All source documents reviewed are listed in Appendix B.

**Reviewer:** Dr. A. Kowalczyk, PE — Independent Computational Mechanics Consultant
**Date:** 2024-09-18
**Signature:** *[on file with document control]*

---
