# Credibility Assessment Report
## Finite Element Analysis of a Modular Titanium Spinal Fusion Cage
### Project: LUMBAR-7 Implant System — Structural Integrity Evaluation
**Prepared by:** Biomechanical Engineering Group, Meridian Device Sciences
**Document Ref:** MDS-FEA-CR-2024-041 Rev B
**Date:** 14 June 2024

---

## 1. Background and Purpose

This report documents the credibility assessment of the finite element analysis (FEA) suite developed in support of the LUMBAR-7 modular titanium interbody fusion cage. The device is intended for single-level lumbar fusion (L3–S1) and is subject to regulatory submission under FDA 510(k) pathway. The primary computational tool is Ansys Mechanical 2023 R2, with pre-processing performed in SpaceClaim 2023 R2 and post-processing in EnSight 2023.

The assessment follows the general principles of simulation credibility as applied in medical device FEA practice, consistent with ASME V&V 40-2018 guidance. The purpose of this document is to provide a structured, evidence-based evaluation of the degree to which the simulation results can be trusted to support regulatory and design decisions.

The clinical question being addressed is whether the LUMBAR-7 cage, under physiological loading conditions representative of worst-case lumbar compressive and shear forces, will remain below fatigue-critical stress thresholds across the full range of modular configurations (small, medium, and large footprint variants).

---

## 2. Scope of Use and Decision Context

### 2.1 Intended Use of the Simulation

The simulation outputs are used to:
1. Rank design variants by peak von Mises stress in the cage body and locking tab features.
2. Confirm that maximum principal stresses remain below the endurance limit of Grade 23 Ti-6Al-4V ELI (approximately 550 MPa at 10⁷ cycles per ISO 5832-3).
3. Support the argument that bench testing (ASTM F2077 axial compression fatigue) can be conducted at a reduced number of configurations, with simulation covering the untested variants.

The simulation is therefore being used in a **risk-informing and test-reduction role** — a context that demands high confidence in predictive accuracy. This places the analysis in a demanding credibility tier, where deficiencies in model fidelity or validation evidence would have direct regulatory consequence.

### 2.2 Risk Characterization

Failure of the cage under physiological loading could result in device fracture, subsidence, or loss of fixation, each carrying potential for serious patient harm. The consequence of an incorrect simulation prediction (i.e., predicting acceptable stress when the true stress exceeds the endurance limit) is therefore classified as **high severity**. This risk classification is used throughout the assessment to weight the required rigor of each evidence element.

---

## 3. Geometry and Model Scope

The CAD geometry was imported from the released LUMBAR-7 drawing set (Revision D, MDS-DWG-2024-017). Three configurations were modeled: small (22×32 mm footprint), medium (26×36 mm), and large (30×40 mm). All models include the titanium cage body, the PEEK endplate inserts, and the titanium locking tab assembly. Bone graft cavity geometry is represented as void space; no graft material properties were assigned, consistent with a worst-case (unfused) loading assumption.

The superior and inferior vertebral endplates were represented as rigid analytical surfaces. Contact between the cage endplate teeth and the rigid surfaces was modeled as frictional (μ = 0.4, consistent with published cadaveric data from Oxland et al.). Internal contact between the locking tab and the cage body slot was modeled as frictionless for conservatism.

**Geometric fidelity note:** The as-manufactured chamfer radii on the locking tab slot (0.15 mm nominal per drawing) were explicitly included in the CAD import. A sensitivity study confirmed that omitting these features increased local peak stress by 18–23%, demonstrating their importance to stress concentration prediction. This is documented in internal memo MDS-FEA-MEM-2024-008.

---

## 4. Material Characterization

### 4.1 Titanium Alloy

Ti-6Al-4V ELI properties were assigned as isotropic linear elastic: E = 114 GPa, ν = 0.34. These values are consistent with the material certification data for the specific billet lot (Lot TL-2023-447) used for prototype fabrication. The assumption of linear elasticity is appropriate because the analysis targets fatigue-relevant stress amplitudes well below the yield strength (830 MPa minimum per ASTM F136).

### 4.2 PEEK Inserts

PEEK (Invibio PEEK-OPTIMA Natural) was assigned E = 3.6 GPa, ν = 0.40, consistent with the manufacturer's published datasheet (Invibio DS-001 Rev 5). No anisotropy was modeled; the material is injection-molded and the flow direction relative to loading was not characterized. This is acknowledged as a limitation (see Section 8).

### 4.3 Material Model Appropriateness

The project team reviewed whether creep or viscoelastic behavior of PEEK under sustained loading warranted inclusion. Based on the loading protocol (cyclic, 5 Hz, consistent with ASTM F2077), and the short-duration nature of the fatigue test simulation, rate-dependent material behavior was judged not relevant to the primary stress predictions. This judgment is documented and traceable.

---

## 5. Numerical Methods and Solver Verification

### 5.1 Element Selection and Formulation

All structural regions were meshed with 10-node quadratic tetrahedral elements (SOLID187 in Ansys notation). Regions of expected high stress gradient — specifically the locking tab root and the anterior cage wall — were meshed with hexahedral-dominant swept meshes using SOLID186 elements to reduce volumetric locking artifacts. A minimum of three elements through the thickness was maintained in all thin-walled regions.

### 5.2 Code Verification

The Ansys Mechanical 2023 R2 solver was verified against three benchmark problems prior to use in this project:

- **Benchmark 1:** Thick-walled pressure vessel under internal pressure — comparison against Lamé solution. Peak hoop stress agreement: 0.3% relative error.
- **Benchmark 2:** Cantilever beam with tip load — comparison against Euler-Bernoulli analytical solution. Tip deflection agreement: 0.8% relative error.
- **Benchmark 3:** Hertzian contact between a sphere and a flat — comparison against classical contact mechanics. Peak contact pressure agreement: 2.1% relative error.

These benchmarks confirm that the solver correctly implements the governing equations for the element types and contact formulations employed in the LUMBAR-7 model. Records are archived in MDS-FEA-VER-2024-003.

### 5.3 Mesh Refinement Study

A systematic mesh convergence study was performed on the medium-footprint configuration, which was identified as the geometry most sensitive to stress concentration due to the locking tab geometry. Four mesh densities were evaluated:

| Mesh Level | Elements (total) | Peak von Mises (MPa) | % Change from prior |
|---|---|---|---|
| Coarse | 124,000 | 387 | — |
| Medium | 412,000 | 441 | 13.9% |
| Fine | 1,180,000 | 458 | 3.9% |
| Very Fine | 3,240,000 | 463 | 1.1% |

The Richardson extrapolation estimate of the exact solution is 466 MPa. The fine mesh (1.18M elements) achieves a grid convergence index (GCI) of 1.4% on peak stress, which is considered acceptable for this application. All production runs use the fine mesh density. The coarse and medium meshes were explicitly rejected for production use.

The mesh convergence study was conducted independently by a second analyst (Dr. S. Okonkwo) and peer-reviewed against the primary analyst's results, with no discrepancies identified in methodology.

---

## 6. Loading and Boundary Conditions

### 6.1 Load Definition

Physiological loading was derived from published in vivo lumbar spine load data (Wilke et al., 2001; Sato et al., 1999). Worst-case compressive load was set at 2,400 N axial compression combined with 10 N·m flexion moment, representing the upper bound of reported loads during lifting with trunk flexion. A separate shear load case (400 N anterior shear) was applied independently and in combination with the compressive case.

The loading is applied to the rigid superior endplate surface via a reference point, with the inferior surface fully encastred. This boundary condition represents the physical test fixture used in ASTM F2077 bench testing, ensuring that the simulation boundary conditions are consistent with the validation experiment.

### 6.2 Load Uncertainty

A ±15% variation in the applied compressive load was evaluated parametrically. Peak stress varied linearly (as expected for a linear elastic model), with a ±15% load variation producing a ±15% stress variation. The nominal load case (2,400 N) is therefore used as the reference, with the understanding that the endurance limit margin (466 MPa predicted vs. 550 MPa limit) provides approximately 18% margin above the extrapolated mesh-converged peak stress, which is sufficient to accommodate the load uncertainty band.

---

## 7. Validation Evidence

### 7.1 Validation Experiment Description

Physical validation testing was conducted at Meridian's in-house biomechanical test laboratory (ISO 17025 accredited, Cert. No. ML-2019-0047). Three medium-footprint LUMBAR-7 cages (serial numbers LB7-M-001 through LB7-M-003) were instrumented with 350 Ω foil strain gauges (HBM 1-LY11-6/120) at four locations on the anterior cage wall and two locations adjacent to the locking tab root. Gauges were applied by a certified technician following HBM application procedure AP-001.

Loading was applied via a servo-hydraulic test frame (MTS 858 Mini Bionix) under displacement control, with load cell verification traceable to NIST standards. Three load levels were tested: 800 N, 1,600 N, and 2,400 N axial compression, each held for 30 seconds with strain recorded at 100 Hz.

### 7.2 Simulation-to-Experiment Comparison

Simulated surface strains at the gauge locations were extracted and compared to measured values. The following table summarizes the comparison at 2,400 N:

| Gauge Location | Measured (με) | Simulated (με) | % Difference |
|---|---|---|---|
| Anterior wall, superior | 1,842 ± 67 | 1,910 | +3.7% |
| Anterior wall, inferior | 1,654 ± 54 | 1,701 | +2.8% |
| Locking tab root, left | 2,218 ± 112 | 2,089 | −5.8% |
| Locking tab root, right | 2,195 ± 98 | 2,104 | −4.1% |
| Lateral wall, mid | 987 ± 41 | 1,023 | +3.6% |
| Posterior wall | 612 ± 29 | 588 | −3.9% |

All six gauge locations show agreement within ±6%, which is within the combined experimental and numerical uncertainty budget. The locking tab root gauges show the largest discrepancy (approximately −5%), which is attributed to minor geometric variation between the as-built prototypes and the nominal CAD geometry used in simulation. Metrology data (CMM report MDS-MET-2024-022) confirmed a 0.08 mm deviation in the tab root radius on all three prototypes relative to the nominal drawing dimension, which is consistent with the observed underprediction of strain at that location.

### 7.3 Validation Domain Coverage

The validation experiment covers the medium-footprint configuration only. Extrapolation of validation confidence to the small and large footprint variants is supported by:
- Geometric similarity analysis confirming that the locking tab geometry (the critical stress concentration feature) is identical across all three variants.
- A sensitivity study showing that footprint size has less than 4% influence on locking tab peak stress under equivalent loading.
- An independent hand calculation confirming the stress scaling behavior.

The validation domain is therefore judged to be adequately representative of all three production configurations, with the above supporting arguments documented in MDS-FEA-VAL-2024-011.

---

## 8. Uncertainty Quantification and Sensitivity Analysis

A structured uncertainty inventory was compiled, covering:

| Source | Type | Magnitude | Effect on Peak Stress |
|---|---|---|---|
| Applied load | Aleatory | ±15% | ±15% (linear) |
| Ti-6Al-4V elastic modulus | Epistemic | ±3 GPa (±2.6%) | ±1.2% |
| PEEK elastic modulus | Epistemic | ±0.4 GPa (±11%) | ±0.8% |
| Friction coefficient (endplate contact) | Epistemic | ±0.1 | ±3.2% |
| Geometric tolerance (tab root radius) | Aleatory | ±0.10 mm | ±6.4% |
| Mesh discretization | Numerical | GCI = 1.4% | +1.4% (conservative bound) |

The dominant uncertainty source is the applied physiological load, which is an inherent aleatory uncertainty arising from inter-patient and activity variability. The combined uncertainty (RSS of all sources) is approximately ±17% on peak stress. The predicted peak stress of 466 MPa combined with a +17% uncertainty bound yields an upper bound of 545 MPa, which is marginally below the endurance limit of 550 MPa. This narrow margin is flagged as a **credibility concern** and is addressed in the limitations section.

---

## 9. Operator Qualification and Process Controls

The primary FEA analyst (J. Marchetti, M.Sc. Mechanical Engineering, 8 years FEA experience in medical devices) holds internal certification per Meridian procedure MDS-PROC-0034 (FEA Practitioner Level III). Model setup, meshing, and post-processing were conducted under a controlled simulation management plan (MDS-SMP-2024-007), which specifies file naming conventions, version control (Git repository MDS-FEA-LUMBAR7), and required peer review checkpoints.

A second independent analyst reviewed the model setup file, boundary condition definitions, and post-processing scripts prior to production runs. Review records are in MDS-FEA-REV-2024-015. No critical errors were identified; three minor comments were raised and resolved (contact pair definition clarification, load application reference point location confirmation, and unit system verification).

The simulation management plan also specifies that all input files, mesh files, result files, and post-processing scripts are archived at project closure, ensuring reproducibility of results. This archive was verified as complete by the project configuration manager on 10 June 2024.

---

## 10. Software and Computational Environment

Ansys Mechanical 2023 R2 (Build 2023.2.0.3847) was used on a validated computational platform (Dell PowerEdge R750, 2× Intel Xeon Gold 6348, 512 GB RAM, RHEL 8.7). The software installation was qualified per Meridian IT procedure MDS-IT-0012, including installation verification testing (IVT) with documented pass/fail criteria. The IVT report (MDS-IVT-2024-009) confirms that the installed software produces results consistent with the vendor's published benchmark suite.

Parallel solver settings used 32 cores for all production runs. A repeatability check was performed by re-running the medium-footprint fine mesh on 16 cores and 64 cores; results agreed to within 0.01% (floating-point round-off level), confirming solver determinism under varying parallelization.

---

## 11. Credibility Summary

The following table summarizes the assessed credibility level for each major evidence area, using a four-level scale (1 = minimal, 4 = comprehensive):

| Evidence Area | Assessed Level | Basis |
|---|---|---|
| Clarity of simulation purpose and decision context | 4 | Well-defined clinical question, risk classification documented |
| Geometric and model scope fidelity | 4 | As-manufactured features included, sensitivity study performed |
| Material property traceability | 3 | Ti alloy lot-specific; PEEK anisotropy not characterized |
| Solver and code verification | 4 | Three benchmarks, archived records |
| Mesh convergence and numerical error | 4 | GCI study, Richardson extrapolation, independent peer review |
| Loading and boundary condition justification | 4 | Literature-based, consistent with physical test setup |
| Validation experiment quality | 3 | ISO 17025 lab, NIST-traceable, single configuration tested |
| Validation domain coverage | 3 | Supported by similarity arguments, not direct testing of all variants |
| Uncertainty quantification | 3 | Structured inventory; upper bound marginally within limit |
| Analyst qualification and process controls | 4 | Certified analyst, SMP, peer review documented |
| Software qualification | 4 | IVT completed, repeatability confirmed |

**Overall credibility assessment:** The simulation suite demonstrates strong evidence across most areas. The primary concerns are (a) the narrow margin between the uncertainty-adjusted peak stress and the endurance limit, and (b) the absence of direct validation for the small and large footprint configurations. These concerns are not disqualifying but should be explicitly addressed in the regulatory submission narrative.

---

## 12. Limitations and Recommended Actions

1. **Stress margin concern:** The combined uncertainty upper bound of ~545 MPa approaches the 550 MPa endurance limit. It is recommended that either (a) the applied load uncertainty be reduced through more precise patient population loading data, or (b) the design be modified to increase the stress margin to at least 20% above the uncertainty-adjusted peak. Alternatively, direct fatigue testing of the worst-case configuration should be used to supplement the simulation argument.

2. **PEEK material anisotropy:** The injection-molded PEEK endplate inserts were modeled as isotropic. If flow-direction data from the molder (Nypro Medical, Galway) can be obtained, a transversely isotropic material model should be evaluated. Preliminary sensitivity analysis suggests this could affect PEEK insert stress predictions by up to 12%, though the PEEK inserts are not the fatigue-critical component.

3. **Single-configuration validation:** Direct strain gauge validation was performed only on the medium-footprint cage. While the similarity argument is well-supported, FDA reviewers may request additional validation data for the large-footprint variant, which experiences the highest absolute compressive load in clinical use due to its larger contact area and typical use in heavier patients. A targeted validation test of the large-footprint variant is recommended prior to submission.

4. **Bone graft modeling:** The void-space representation of the graft cavity is conservative for stress in the cage body but may not be representative of post-fusion load sharing. If the simulation is later extended to address long-term remodeling questions, a poroelastic or continuum damage graft model should be considered.

5. **Dynamic loading not addressed:** The current simulation addresses quasi-static and cyclic fatigue loading. Impact loading (e.g., from patient falls) is outside the current scope and would require a separate transient dynamic analysis.

---

## 13. Conclusions

The FEA suite supporting the LUMBAR-7 spinal fusion cage regulatory submission has been assessed as credible for its stated purpose, with the caveats noted in Section 12. The simulation methodology is technically sound, the validation evidence is of high quality within its domain, and the uncertainty analysis is thorough. The narrow stress margin relative to the endurance limit is the single most significant credibility concern and should be the focus of additional engineering effort or testing before final regulatory submission.

This assessment was conducted by the Biomechanical Engineering Group and reviewed by the Quality and Regulatory Affairs function. It is approved for inclusion in the 510(k) submission package, subject to resolution of Recommended Action items 1 and 3 above.

---

*Report prepared by:* J. Marchetti, Sr. FEA Engineer
*Technical reviewer:* Dr. S. Okonkwo, Principal Engineer
*Quality review:* R. Flanagan, Quality Engineering Manager
*Approved by:* Dr. A. Petrov, VP Engineering, Meridian Device Sciences
