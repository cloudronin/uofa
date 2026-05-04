# Appendix A — Supporting Details and Supplementary Data

## A.1 Element Formulation Notes

All solid volumes (implant stem, cortical shell, cancellous core) were discretized using quadratic tetrahedral elements (Abaqus C3D10). The choice of quadratic over linear elements was deliberate: linear tetrahedra (C3D4) are known to exhibit volumetric locking in nearly-incompressible materials and produce overly stiff bending responses. Quadratic elements recover bending behavior accurately and are well-suited to the irregular geometry of the femoral canal.

Contact surfaces between the stem and bone were meshed using compatible surface facets derived from the solid element faces; no separate shell or interface elements were introduced. The contact formulation used finite-sliding, surface-to-surface contact with a penalty stiffness method. Augmented Lagrange enforcement was applied at the distal frictionless interface to control penetration.

A single-element patch test was performed for the C3D10 element under pure bending and pure shear loading to confirm correct implementation in the Abaqus version used. Results matched analytical solutions to within 0.3%.

---

## A.2 Load Case Summary

Three load cases were analyzed:

| LC | Description | Peak Force (N) | Angle (frontal/sagittal) | Cycles (×10⁶) |
|----|-------------|----------------|--------------------------|----------------|
| LC1 | Normal walking (ISO 7206-4) | 2,300 | 10° / 9° | 10 |
| LC2 | Stair climbing (OrthoLoad 85th %ile) | 2,780 | 14° / 12° | 1 |
| LC3 | Stumble/recovery (OrthoLoad peak) | 3,850 | 18° / 15° | 0.01 |

LC1 governs fatigue assessment. LC3 governs yield safety factor evaluation. Peak von Mises stress under LC3: 498 MPa, yielding a yield safety factor of 1.77 against the Ti-6Al-4V ELI 0.2% proof stress (880 MPa).

---

## A.3 Convergence Iteration History

Newton-Raphson convergence was achieved in all load increments. Maximum number of iterations required in any single increment: 6 (occurring at initial contact establishment under LC3). Force residual norm at convergence: < 1×10⁻⁴ of the reference force. Displacement correction norm: < 1×10⁻⁵. No convergence difficulties or cutbacks were observed in LC1 or LC2.

---

## A.4 Strain Gauge Test Protocol Reference

Physical testing was conducted per internal test procedure TP-IMPL-0042, Rev. A. Gauge type: Vishay CEA-06-062UW-350, nominal resistance 350 Ω, gauge factor 2.085 ± 0.5%. Data acquisition: National Instruments cDAQ-9174 chassis with NI-9237 bridge module, sampled at 1 kHz. Load application rate: 50 N/s quasi-static ramp to peak load. Three repeat measurements were taken at each gauge location; reported values are the mean of three replicates.

---

## A.5 Material Property Traceability Summary

| Material | Source | Test Standard | Lot/Batch | Date |
|----------|--------|---------------|-----------|------|
| Ti-6Al-4V ELI (stem) | Arcam AB supplier CoC + in-house tensile | ASTM E8/E8M | TiELI-2023-Q4 | Nov 2023 |
| Cortical bone (surrogate) | Reilly & Burstein (1975); Cowin (2001) | Literature | N/A | — |
| Cancellous bone (surrogate) | Carter & Hayes (1977); CT-derived | Literature + CT | Sawbones 3406 | Dec 2023 |

Note: No independent mechanical testing of the Sawbones surrogate bone material was performed in this program. The Sawbones manufacturer's published mechanical properties (Composite Bone Catalog, 4th Ed.) were used to cross-check the CT-derived values; agreement was within 8% for cortical modulus and 12% for cancellous modulus at matched density.

---

## A.6 Items Explicitly Deferred from This Assessment

The following credibility-relevant topics were identified during scoping but are not addressed in this report. They are documented here to provide a complete audit trail of known gaps:

1. **Analyst-to-analyst reproducibility:** No round-robin or blind re-analysis exercise was conducted. A second analyst independently reviewed mesh setup and boundary condition inputs but did not independently construct the model from scratch. Full reproducibility assessment is planned for Phase 3.

2. **Solution verification under dynamic loading:** All analyses are quasi-static. Modal analysis to confirm that the fundamental natural frequency is well above the loading frequency was not performed in this phase. This is considered low-risk given the quasi-static nature of walking loads but should be confirmed for impact scenarios.

3. **Sensitivity to contact stiffness penalty parameter:** The penalty stiffness at the distal contact interface was set to the Abaqus default (based on underlying element stiffness). Sensitivity of results to this parameter was not evaluated. Given that the distal interface carries a small fraction of total load, this is judged to be a low-priority item.

4. **Independent review of post-processing scripts:** Python scripts used to extract and tabulate stress and strain results from the Abaqus ODB files were written by the primary analyst. These scripts have not undergone independent verification. Manual spot-checks of five output locations confirmed agreement with Abaqus/CAE graphical output to within 0.1%.

---

*End of Appendix A*
