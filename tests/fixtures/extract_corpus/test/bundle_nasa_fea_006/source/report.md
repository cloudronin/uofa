# Structural Credibility Assessment Report
## Finite Element Analysis of the Orion-Class Pressure Vessel Skirt Assembly
### Project: OCV-2031 | Document No.: SCA-FEA-0047-Rev C
### Prepared by: Advanced Structures Analysis Group, Meridian Aerospace Engineering
### Date: 14 March 2025

---

## 1. Background and Scope

This report documents the credibility assessment of a finite element analysis (FEA) model developed to predict structural response of the OCV-2031 pressure vessel skirt assembly under combined axial, bending, and internal pressure loading conditions. The skirt assembly interfaces the primary pressure vessel to the aft thrust structure and is a fracture-critical component subject to NASA-class safety requirements.

The FEA model was constructed in Abaqus/Standard 2023.HF4 and encompasses approximately 1.4 million second-order tetrahedral elements (C3D10) with selective use of C3D20R hexahedral elements in the primary load-path regions. The analysis team sought an independent assessment of the model's technical credibility prior to its use in formal design certification.

The scope of this assessment covers: geometric fidelity, material representation, loading and boundary condition adequacy, numerical solution quality, comparison against physical test data, and the suitability of the model for its intended predictive purpose. The assessment framework applied is consistent with established NASA simulation credibility standards for high-consequence structural analyses.

---

## 2. Assessment Methodology

The assessment team reviewed all analysis input decks, pre-processing scripts, post-processing notebooks, and supporting documentation provided by the analysis team. Independent re-runs of selected load cases were performed on Meridian's compute cluster using the same solver version. Physical test data from the OCV-2031 Structural Qualification Test Campaign (SQTC-2029) were obtained from the project test database and used as the primary reference for solution comparison.

Each credibility dimension was evaluated on a four-level scale, where Level 1 indicates minimal or absent supporting evidence and Level 4 indicates rigorous, well-documented, and independently verified evidence. Assessor judgments were made based on documentary evidence, code review, and engineering interviews conducted between 28 January and 7 February 2025.

---

## 3. Intended Use and Question of Interest

### 3.1 Clarity of the Predictive Question

The analysis team provided a written simulation plan (SP-OCV-2031-003, Rev B) that articulates the specific quantities of interest (QoIs): peak von Mises stress at the skirt-to-vessel weld toe, axial load distribution across the four attachment lugs, and first-mode natural frequency of the assembled skirt. The plan specifies acceptance thresholds for each QoI, maps each to a corresponding design requirement, and identifies the load cases of record. The intended decision supported by the model — whether the skirt design meets margin-of-safety requirements without physical redesign — is unambiguous.

The simulation plan also delineates the operating envelope explicitly: internal pressures of 0–34.5 MPa, axial loads of ±2.2 MN, and bending moments up to 850 kN·m. This level of specificity is commendable and provides a clear frame for assessing whether the model is fit for purpose.

**Assessment: Level 4.** The question of interest is precisely stated, decision-relevant, and traceable to requirements documentation.

### 3.2 Scope of Model Applicability

The simulation plan correctly identifies the geometric and loading regimes in which the model is expected to operate and explicitly flags conditions outside scope (e.g., post-yield plastic collapse, fatigue life prediction). The model is not being stretched beyond its documented applicability envelope.

**Assessment: Level 4.**

---

## 4. Geometric and Physical Fidelity

### 4.1 Geometric Representation

The CAD-to-mesh pipeline used Siemens NX 2306 for geometry cleanup and ANSA 23.1.0 for meshing. The as-built drawing set (Rev F) was used as the geometry source. Weld-toe fillets of nominal 3 mm radius were explicitly modeled rather than idealized away — a critical decision given the stress concentration sensitivity at that location. Bolt holes in the attachment lug flanges were represented with full cylindrical geometry.

The assessment team identified one minor discrepancy: the as-built survey for unit S/N 003 shows a measured fillet radius of 2.6 ± 0.3 mm at weld location W-07, versus the nominal 3.0 mm modeled. A sensitivity study was requested; the analysis team provided results showing a 4.2% increase in peak stress at W-07 for the 2.6 mm case, which remains within the margin of safety. This was judged adequate.

**Assessment: Level 3.** Geometry is largely faithful to as-built hardware; the fillet sensitivity is documented and bounded.

### 4.2 Material Property Representation

The skirt body is Ti-6Al-4V (AMS 4928, annealed condition). Elastic modulus, Poisson's ratio, and density were taken from the project material specification (MS-OCV-0012) which references coupon test data from the same material heat used in fabrication. The weld-affected zone (WAZ) was assigned reduced properties per a separate WAZ characterization study (WAZ-RPT-2028-11), which included tensile coupon testing at three locations along representative weld mockups.

Temperature dependence of elastic modulus was included for the thermal-structural combined load cases, using tabular data from the material spec spanning −54°C to +121°C.

The assessment team notes that no account was made for potential anisotropy introduced by the forging process for the lug forgings (AMS 4928 bar stock, longitudinal vs. transverse grain direction). The analysis team acknowledged this gap but argued, with supporting literature references, that for the stress states present the anisotropy effect is below 2%. This argument is reasonable but not independently verified by coupon test.

**Assessment: Level 3.** Material data are well-sourced and heat-traceable; the forging anisotropy gap is acknowledged and bounded by literature.

---

## 5. Numerical Solution Quality

### 5.1 Mesh Refinement Study

A systematic mesh convergence study was conducted across three refinement levels. The coarse mesh contained 340,000 elements; the medium mesh 890,000 elements; and the production (fine) mesh 1,400,000 elements. Global element size was halved between refinement levels in the critical weld-toe region. The QoI (peak stress at W-07) changed by 8.3% between coarse and medium, and by 1.9% between medium and fine, indicating approach to convergence. Richardson extrapolation was applied to estimate the discretization error at approximately 0.8% relative to the fine-mesh solution.

A grid convergence index (GCI) calculation was performed following Roache's method. The reported GCI for the fine-to-medium pair is 2.1%, providing a conservative bound on numerical error. The mesh refinement documentation is thorough and independently reproducible.

**Assessment: Level 4.**

### 5.2 Solver and Numerical Configuration

Abaqus/Standard's direct sparse solver (PARDISO) was used for all static load cases. Convergence tolerances were left at Abaqus defaults (force residual norm ≤ 0.5% of reaction forces), which the assessment team confirmed are appropriate for this linear-elastic analysis. No nonlinear geometry effects (NLGEOM) were activated; the analysis team justified this based on maximum computed deflections being less than 0.3% of characteristic structural dimensions, which is acceptable.

Contact at the lug-to-bracket interfaces was modeled using small-sliding surface-to-surface contact with a penalty stiffness formulation. The assessment team reviewed contact pressure distributions and found no evidence of spurious contact oscillation or pressure spikes that would indicate numerical instability.

**Assessment: Level 4.**

### 5.3 Code Verification Activities

The analysis team performed a set of benchmark problems to confirm that Abaqus/Standard produces correct results for the element types and formulations used. Benchmarks included: (a) thick-walled cylinder under internal pressure (Lamé solution), (b) cantilevered beam with end load (Euler-Bernoulli), and (c) a modal analysis of a simply supported plate (analytical eigenvalue solution). In all cases, the FEA solution matched the analytical reference to within 0.5%.

Additionally, the Abaqus 2023.HF4 release notes and verification manual were reviewed to confirm no known defects affect C3D10 or C3D20R elements under the loading conditions present.

**Assessment: Level 4.**

---

## 6. Comparison with Physical Test Data

### 6.1 Test Data Pedigree and Traceability

The SQTC-2029 test campaign was conducted at Meridian's Structural Test Facility using a hydraulic load frame calibrated to NIST-traceable standards. Strain gauges (Vishay CEA-06-250UN-350) were installed at 22 locations on the skirt assembly, including four gauges within 10 mm of the W-07 weld toe. Load cells and displacement transducers were independently calibrated within 12 months of the test. Test data are archived in the project PDM system with full chain-of-custody records.

The assessment team reviewed the calibration certificates and confirmed traceability. Test uncertainty was formally quantified using a Type B uncertainty analysis per ASME PTC 19.1, yielding a combined standard uncertainty of ±1.8% on strain measurements and ±0.9% on applied load.

**Assessment: Level 4.** Test data are of high pedigree with documented uncertainty.

### 6.2 Model-to-Test Comparison

Predicted strains were extracted at the 22 gauge locations and compared to measured values under three load cases: (LC-1) pressure-only at 34.5 MPa, (LC-2) axial compression at 2.2 MN, and (LC-3) combined pressure + bending. Results are summarized in Appendix A.

For LC-1 and LC-2, predicted-to-measured strain ratios ranged from 0.94 to 1.07 across all gauge locations, with a mean ratio of 1.01 and a standard deviation of 0.033. For LC-3, the mean ratio was 1.03 with a standard deviation of 0.041. These results indicate good predictive accuracy within the test uncertainty bounds.

The peak stress at W-07 was not directly measurable by strain gauge due to the steep gradient; however, the nearest gauge (G-14, located 12 mm from the weld toe) showed a predicted-to-measured ratio of 0.97, providing indirect confidence in the local stress field representation.

**Assessment: Level 4.** Quantitative comparison demonstrates good agreement across multiple load cases and gauge locations.

### 6.3 Uncertainty Quantification in Predictions

A parametric uncertainty analysis was conducted using a one-at-a-time (OAT) sensitivity study varying: elastic modulus (±5%), applied load magnitude (±2%), fillet radius (±15%), and WAZ property reduction factor (±10%). The resulting spread in peak stress at W-07 was ±7.3% relative to the nominal prediction. A Monte Carlo propagation (5,000 samples, Latin Hypercube Sampling) was also performed, yielding a 95th-percentile stress of 412 MPa versus the nominal 389 MPa — a 5.9% exceedance, well within the 20% margin of safety.

The uncertainty characterization is thorough and the methodology is appropriate for the analysis class.

**Assessment: Level 4.**

---

## 7. Model Pedigree and Development Rigor

### 7.1 Documentation and Configuration Control

The analysis model is maintained under configuration control in the project's Windchill PDM system. The input deck, material property files, and post-processing scripts are all versioned and linked to the analysis report. A change log documents all modifications from Rev A through the current Rev C model. The assessment team was able to reproduce the production results from the archived input deck without modification.

**Assessment: Level 4.**

### 7.2 Personnel Qualifications and Review Process

The lead analyst holds a Ph.D. in structural mechanics and has 11 years of experience with Abaqus-based pressure vessel analysis. A peer review was conducted by a senior engineer (18 years experience) who independently reviewed the mesh, boundary conditions, and result interpretation. The peer review checklist (PR-OCV-2031-FEA-01) was completed and signed. An independent technical review was also conducted by the project chief engineer.

**Assessment: Level 4.**

### 7.3 Software Quality and Tool Qualification

Abaqus/Standard 2023.HF4 is a commercially validated finite element solver with extensive aerospace heritage. The specific installation used on Meridian's HPC cluster was verified against the Abaqus benchmark suite (SIMULIA QA suite, 487 benchmark problems) with a pass rate of 100%. The post-processing Python scripts (using NumPy 1.26 and Matplotlib 3.8) were independently reviewed and unit-tested against known analytical results.

**Assessment: Level 4.**

---

## 8. Applicability of Previous Work and Supporting Data

The OCV-2031 skirt geometry is an evolution of the OCV-2028 design, for which a validated FEA model also exists. The analysis team appropriately referenced the OCV-2028 model validation data as supporting context but did not rely on it as a substitute for new validation. The degree of geometric similarity (approximately 85% common geometry by volume) was documented, and differences in load path and material specification were explicitly identified and addressed.

Literature references for weld-toe stress concentration factors (Hobbacher, IIW-2259-15) were used to provide additional context for the W-07 stress predictions. These references are peer-reviewed and appropriate for the application.

**Assessment: Level 3.** Supporting data are relevant and properly qualified; the team appropriately distinguished between supporting context and primary validation evidence.

---

## 9. Limitations and Open Items

1. **Forging anisotropy:** As noted in §4.2, the effect of Ti-6Al-4V forging texture on lug stiffness has not been experimentally characterized for this specific heat and geometry. Recommend coupon testing in a future phase if the design margin narrows.

2. **Fatigue life prediction:** This model is explicitly not validated for fatigue life assessment. Any future use for fatigue analysis would require separate validation activities including crack initiation and propagation test data.

3. **Post-yield behavior:** The model is linear-elastic only. Use for any load case that drives the skirt material beyond yield (estimated at approximately 140% of design limit load) is outside the validated envelope.

4. **Dynamic transient loading:** The modal analysis was validated against test; however, full transient response under pyrotechnic shock events has not been validated and is outside the current model scope.

---

## 10. Overall Credibility Summary

| Assessment Dimension | Level | Rationale |
|---|---|---|
| Clarity of predictive question | 4 | Precisely stated, decision-linked, traceable |
| Model applicability scope | 4 | Envelope explicitly defined and respected |
| Geometric fidelity | 3 | Faithful to as-built; minor fillet discrepancy bounded |
| Material representation | 3 | Heat-traceable data; forging anisotropy gap acknowledged |
| Mesh convergence | 4 | GCI documented; Richardson extrapolation applied |
| Solver configuration | 4 | Appropriate settings; contact behavior verified |
| Code verification | 4 | Benchmark suite passed; known defects reviewed |
| Test data pedigree | 4 | NIST-traceable; uncertainty formally quantified |
| Model-to-test comparison | 4 | Quantitative agreement across multiple load cases |
| Uncertainty quantification | 4 | OAT + Monte Carlo; 95th-percentile stress bounded |
| Documentation / configuration control | 4 | Versioned; reproducible from archive |
| Personnel qualifications | 4 | Peer and independent reviews completed |
| Software qualification | 4 | Benchmark suite; post-processing scripts verified |
| Supporting data applicability | 3 | OCV-2028 heritage used as context, not substitute |

**Overall Assessment: The OCV-2031 skirt FEA model is assessed as having HIGH credibility for its stated intended use.** The model is suitable to support design certification decisions for the load cases and quantities of interest defined in SP-OCV-2031-003 Rev B, subject to the limitations documented in §9.

---

## 11. Signatures

| Role | Name | Date |
|---|---|---|
| Lead Assessor | Dr. K. Oduya, P.E. | 14 Mar 2025 |
| Review | J. Hartmann, Sr. Structures | 14 Mar 2025 |
| Approval | M. Castellanos, Chief Engineer | 14 Mar 2025 |

---
