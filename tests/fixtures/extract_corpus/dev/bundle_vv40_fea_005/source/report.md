# Finite Element Analysis Credibility Assessment Report
## Structural Integrity Evaluation — Titanium Spinal Fusion Cage (TiSFC-7 Implant)
### Project: NeuroSpine Dynamics Ltd. — Lumbar Interbody Device Program
### Report Reference: NSD-FEA-CR-2024-041 | Revision B

---

## 1. Background and Scope

This report documents the credibility assessment activities performed on the finite element analysis (FEA) model developed to support the structural integrity evaluation of the TiSFC-7 titanium alloy spinal fusion cage. The device is intended for single-level lumbar interbody fusion at L3–L5, and the FEA model was constructed to predict stress distributions, fatigue life estimates, and subsidence risk under physiological loading conditions.

The primary simulation tool is Abaqus/Standard 2023.HF4 (Dassault Systèmes), with pre-processing conducted in SIMULIA fe-safe 2023 for fatigue post-processing. The model geometry was derived from the as-manufactured CAD file (NSD-CAD-TiSFC7-Rev4), and all material properties were sourced from in-house tensile coupon testing of Ti-6Al-4V ELI bar stock (Batch NSD-MAT-2023-09).

The scope of this assessment covers the primary structural simulation only. Osseointegration modeling, thermal effects during implantation, and patient-specific bone property variation are explicitly deferred to Phase 3 activities and are **not addressed in this report**.

---

## 2. Intended Use and Question of Interest

The simulation is intended to answer the following engineering question: *Does the TiSFC-7 implant meet minimum structural integrity requirements under worst-case compressive and shear loading representative of a 95th-percentile patient activity profile, as defined in ASTM F2077-22?*

The output quantities of interest (QoIs) are:
- Peak von Mises stress in the cage wall (compared against 0.2% proof strength of 880 MPa for Ti-6Al-4V ELI)
- Fatigue safety factor under 10-million-cycle loading at 2,400 N axial compression with ±5° tilt
- Maximum subsidence displacement at the endplate contact interface

The loading conditions and boundary constraints were reviewed against the ASTM F2077-22 test protocol by a senior biomechanical engineer (Dr. R. Okonkwo, NSD), and the team confirmed that the simulated load cases bracket the physical test conditions. This alignment between the computational scenario and the physical test program gives reasonable confidence that the model is being asked an appropriate and well-bounded question.

---

## 3. Model Development and Code Verification

### 3.1 Software and Element Formulation

Abaqus/Standard has an extensive published verification history and is routinely used in Class III medical device submissions. For this application, the cage geometry was meshed with 10-node modified tetrahedral elements (C3D10M), chosen for their robustness with curved surfaces and their resistance to volumetric locking in near-incompressible contact regions.

Internal code verification checks were performed by running three Abaqus benchmark problems relevant to the current analysis:
- Hertzian contact between a sphere and flat plate (Abaqus Benchmark 1.1.11) — peak contact pressure within 1.8% of analytical solution
- Thick-walled pressure vessel under internal load — hoop stress within 0.6% of Lamé solution
- Cantilever beam under tip load — tip deflection within 0.4% of Euler-Bernoulli solution

These checks confirm that the solver is performing correctly for the element types and contact formulations used in the TiSFC-7 model. No anomalous solver behavior (negative eigenvalues, excessive pivot warnings) was observed during production runs.

### 3.2 Mesh Refinement Study

A structured mesh convergence study was conducted using three successive refinements. Global seed sizes of 0.8 mm, 0.5 mm, and 0.3 mm were evaluated. The stress concentration region at the internal strut-to-wall junction (identified as the critical location in preliminary runs) was additionally refined using a focused mesh zone with a minimum element size of 0.12 mm at the 0.3 mm global level.

| Mesh Level | Elements | Peak von Mises (MPa) | Change vs. Prior |
|---|---|---|---|
| Coarse (0.8 mm) | 142,300 | 634 | — |
| Medium (0.5 mm) | 387,100 | 701 | +10.6% |
| Fine (0.3 mm) | 891,400 | 718 | +2.4% |

The Richardson extrapolation estimate of the grid-converged stress is 724 MPa, and the fine mesh result falls within 0.8% of this value. The mesh convergence index (analogous to GCI in fluid simulations) was calculated as 1.3%, which is considered acceptable for this application. All production results reported herein use the fine mesh.

---

## 4. Material Representation

Material properties were assigned based on tensile coupon data from Batch NSD-MAT-2023-09 (10 specimens). The measured mean 0.2% proof strength was 896 MPa (σ = 14 MPa), and Young's modulus was 114 GPa (σ = 2.1 GPa). These values are consistent with published ranges for Ti-6Al-4V ELI per ASTM F136.

An isotropic linear-elastic constitutive model was used for the primary stress analysis. This is a recognized simplification; the material exhibits mild nonlinearity above approximately 800 MPa, but peak stresses in the converged model remain below this threshold under nominal loading, supporting the use of a linear model. Fatigue properties (S-N curve) were derived from the same material batch using rotating-beam specimens per ASTM E466.

The bone analog material (UHMWPE blocks per ASTM F2077) was assigned properties from published data (E = 1.17 GPa, ν = 0.46) rather than direct measurement. This introduces some uncertainty in contact pressure distribution but is considered acceptable given that the bone analog serves as a load-transfer medium rather than a primary structural component of interest.

---

## 5. Uncertainty and Sensitivity Considerations

A one-at-a-time sensitivity study was conducted on the three parameters judged most influential: applied axial load magnitude (±15%), friction coefficient at the cage-endplate interface (μ = 0.2–0.6), and Young's modulus of the bone analog (±20%). Results are summarized below:

- **Axial load ±15%:** Peak stress varies from 611 MPa to 825 MPa — the dominant driver of output uncertainty.
- **Friction coefficient:** Peak stress changes by less than 4% across the full range; contact pressure distribution is more sensitive.
- **Bone analog modulus ±20%:** Peak stress changes by less than 6%.

No formal probabilistic uncertainty quantification (e.g., Monte Carlo or polynomial chaos expansion) was performed at this phase. The sensitivity study provides bounding estimates but does not yield a probability distribution over the QoI. This is noted as a limitation.

The team also recognizes that loading direction variability (patient gait asymmetry, off-axis loading) was not fully explored; only the ASTM-specified tilt angle of ±5° was examined. Broader loading envelope analysis is deferred to the Phase 3 assessment.

---

## 6. Validation Against Physical Test Data

### 6.1 Test-Analysis Correlation

Physical compression testing of three TiSFC-7 prototype units was conducted at NSD's in-house mechanical test laboratory using an MTS 858 Mini Bionix II test frame. Axial stiffness and yield load were measured and compared against FEA predictions.

| Metric | FEA Prediction | Test Mean (n=3) | Discrepancy |
|---|---|---|---|
| Axial stiffness (kN/mm) | 18.7 | 17.9 ± 0.6 | +4.5% |
| Load at 0.5 mm subsidence (N) | 3,820 | 3,650 ± 190 | +4.7% |

The FEA model consistently over-predicts stiffness and load capacity by approximately 4–5%, which is within the team's pre-specified acceptance criterion of ±10%. The systematic over-prediction is likely attributable to minor geometric idealization (fillet radii simplified from 0.15 mm to 0.2 mm in the CAD-to-mesh conversion) and the assumption of perfectly bonded contact at the bone analog interface in the elastic regime.

### 6.2 Validation Scope Limitations

Validation was performed only under monotonic axial compression. Fatigue validation (cyclic loading to 10 million cycles) is in progress and results are not yet available. The fatigue safety factor reported in Section 7 is therefore based entirely on the analytical S-N approach and has not been directly validated against physical fatigue test data. **This is the most significant credibility gap in the current assessment.**

Validation against in vivo or cadaveric data is outside the scope of this program phase.

---

## 7. Results Summary

Under the worst-case loading condition (2,400 N axial compression, +5° tilt, μ = 0.2), the fine mesh model predicts:

- **Peak von Mises stress:** 718 MPa at the internal strut-to-wall junction (location S-7 in the model). This represents 80.1% of the measured proof strength (896 MPa), yielding a stress ratio of 1.25 against yielding.
- **Fatigue safety factor:** 1.41 at 10 million cycles, based on the fe-safe Morrow mean-stress correction with the measured S-N data.
- **Maximum subsidence displacement:** 0.31 mm at the superior endplate contact face under peak load, well within the 1.0 mm design threshold.

These results suggest the TiSFC-7 geometry meets structural integrity requirements under the simulated conditions, with the caveat that fatigue predictions carry higher uncertainty pending physical fatigue test correlation.

---

## 8. Credibility Summary and Gaps

The following table summarizes the assessment team's judgment on the major credibility dimensions evaluated in this report. Scoring is qualitative (High / Moderate / Low / Not Yet Assessed).

| Dimension | Assessment | Basis |
|---|---|---|
| Alignment of simulation question with engineering need | High | Reviewed against ASTM F2077-22; load cases bracket physical test |
| Mesh adequacy | High | Richardson extrapolation; GCI < 2% |
| Code correctness for this application | High | Three benchmark problems; no solver anomalies |
| Material property fidelity | Moderate | Direct measurement for Ti alloy; published data for bone analog |
| Monotonic validation against test data | Moderate | 4–5% over-prediction; within ±10% criterion |
| Fatigue prediction credibility | Low / Not Yet Assessed | No fatigue test correlation available |
| Sensitivity and uncertainty characterization | Moderate | One-at-a-time study; no probabilistic analysis |
| Loading envelope coverage | Moderate | ASTM-specified cases only; off-axis loading deferred |

---

## 9. Limitations and Deferred Items

The following items are explicitly outside the scope of this assessment and will be addressed in Phase 3:

1. **Fatigue test correlation** — Physical cyclic testing is ongoing; results expected Q2 2025.
2. **Patient-specific loading variability** — Probabilistic load analysis using patient motion capture data is deferred.
3. **Osseointegration and bone remodeling** — Not modeled; requires coupled biological-mechanical framework.
4. **Thermal effects during surgical implantation** — Out of scope for structural integrity assessment.
5. **Long-term creep of bone analog** — Material model does not include time-dependent deformation.

The assessment team recommends that the current simulation results be used to support design decisions and physical test planning, but that regulatory submission not proceed until fatigue test correlation is complete and the fatigue credibility gap is resolved.

---

## 10. Conclusions

The TiSFC-7 FEA model demonstrates acceptable credibility for the purpose of structural stress and subsidence prediction under monotonic loading conditions. The mesh convergence study, code verification benchmarks, and test-analysis correlation collectively support confidence in the primary stress results. Material properties for the titanium alloy are well-characterized from direct measurement.

The principal limitation is the absence of fatigue validation data. The fatigue safety factor of 1.41 is encouraging but should be treated as a preliminary estimate until physical cyclic test results are available. Additionally, the sensitivity study, while informative, does not constitute a full uncertainty quantification, and the loading envelope explored is limited to the ASTM standard cases.

Subject to completion of the deferred items identified in Section 9, the model is considered fit for its intended use at the current program phase.

---

*Report prepared by: FEA Analysis Group, NeuroSpine Dynamics Ltd.*
*Technical reviewer: Dr. R. Okonkwo, Senior Biomechanical Engineer*
*Date: 14 November 2024*
*Document status: Approved for internal distribution*
