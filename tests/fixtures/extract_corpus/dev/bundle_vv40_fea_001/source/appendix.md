# Appendix A — Supporting Documentation Index

**Project:** LUMBAR-7 Modular Titanium Spinal Fusion Cage
**Document Ref:** MDS-FEA-CR-2024-041 Rev B — Appendix

---

## A.1 Referenced Internal Documents

| Document Number | Title | Revision | Status |
|---|---|---|---|
| MDS-DWG-2024-017 | LUMBAR-7 Released Drawing Set | D | Released |
| MDS-FEA-MEM-2024-008 | Chamfer Radius Sensitivity Study — Locking Tab | A | Released |
| MDS-FEA-VER-2024-003 | Solver Benchmark Verification Records | A | Released |
| MDS-FEA-VAL-2024-011 | Validation Domain Coverage Argument — LUMBAR-7 | B | Released |
| MDS-FEA-REV-2024-015 | Independent Model Review Records | A | Released |
| MDS-SMP-2024-007 | Simulation Management Plan — LUMBAR-7 FEA | C | Released |
| MDS-MET-2024-022 | CMM Metrology Report — LB7-M-001 through LB7-M-003 | A | Released |
| MDS-IVT-2024-009 | Ansys Mechanical 2023 R2 Installation Verification | A | Released |
| MDS-PROC-0034 | FEA Practitioner Qualification Procedure | 5 | Released |
| MDS-IT-0012 | Computational Platform Qualification Procedure | 3 | Released |

---

## A.2 External References

1. Wilke, H.J. et al. (2001). "New in vivo measurements of pressures in the intervertebral disc in daily life." *Spine*, 24(8), 755–762.
2. Sato, K. et al. (1999). "Biomechanical study on the clinical significance of the lumbar facet joint." *Spine*, 24(23), 2517–2521.
3. Oxland, T.R. et al. (1996). "The relative importance of vertebral bone density and disc degeneration in determining the in vitro compressive properties of the human lumbar spine." *Spine*, 21(22), 2558–2569.
4. ASTM F2077-22: *Test Methods for Intervertebral Body Fusion Devices.*
5. ASTM F136-13: *Standard Specification for Wrought Titanium-6Aluminum-4Vanadium ELI Alloy for Surgical Implant Applications.*
6. ISO 5832-3:2021: *Implants for Surgery — Metallic Materials — Part 3: Wrought Titanium 6-Aluminium 4-Vanadium Alloy.*
7. Invibio DS-001 Rev 5: *PEEK-OPTIMA Natural Material Datasheet.* Invibio Biomaterial Solutions.
8. HBM AP-001: *Strain Gauge Application Procedure.* HBM GmbH.
9. ASME V&V 40-2018: *Assessing Credibility of Computational Modeling through Verification and Validation: Application to Medical Devices.*

---

## A.3 Mesh Convergence Supporting Data

The following figure descriptions correspond to plots archived in the project repository (MDS-FEA-LUMBAR7/mesh_convergence/).

**Figure A.1 — Mesh convergence plot:** Von Mises peak stress vs. inverse square root of element count, showing asymptotic convergence to Richardson extrapolated value of 466 MPa. All four mesh levels plotted; fine and very fine meshes fall within 1.1% of each other.

**Figure A.2 — Stress contour comparison:** Side-by-side von Mises contour plots for medium and fine mesh at 2,400 N load case. Stress distribution pattern is qualitatively identical; peak location is consistent between mesh levels (locking tab root, anterior-superior corner).

**Figure A.3 — GCI bar chart:** Grid convergence index values for each mesh transition, showing monotonic reduction from 18.2% (coarse-to-medium) to 1.4% (fine-to-very-fine). Oscillatory convergence was not observed.

---

## A.4 Validation Experiment Supporting Data

**Figure A.4 — Gauge location photograph:** Annotated photograph of instrumented LUMBAR-7 medium-footprint cage (serial LB7-M-002) showing all six gauge positions relative to cage geometry features.

**Figure A.5 — Load-strain linearity plots:** Strain vs. applied load for all six gauges across three load levels (800 N, 1,600 N, 2,400 N). All gauges show R² > 0.999, confirming linear elastic behavior of the test article and validating the linear elastic material model assumption.

**Figure A.6 — Simulation vs. experiment scatter plot:** Measured strain (x-axis) vs. simulated strain (y-axis) for all six gauges at all three load levels (18 data points total). Linear regression: slope = 0.978, intercept = 14.2 με, R² = 0.997. The slope near unity and high R² confirm the simulation captures the dominant load-transfer mechanisms without systematic bias.

**Table A.1 — Experimental uncertainty budget:** Breakdown of measurement uncertainty contributions including load cell calibration (±0.5%), gauge factor tolerance (±1.0%), temperature compensation (±0.3%), data acquisition resolution (±0.2%), and specimen-to-specimen variability (±3.1%). Combined expanded uncertainty (k=2): ±3.4% on strain measurement.

---

## A.5 Analyst Qualification Summary

**J. Marchetti, M.Sc. Mechanical Engineering (Politecnico di Milano, 2016)**
- 8 years FEA experience, 6 years in medical device structural analysis
- Internal certification: MDS-PROC-0034 Level III (recertified March 2024)
- Previous projects: hip stem fatigue analysis (MDS-FEA-2022-018), bone screw pullout simulation (MDS-FEA-2021-009), spinal rod bending analysis (MDS-FEA-2023-031)
- External training: Ansys Mechanical Advanced Structural (2022), ASME V&V 40 Practitioner Workshop (2023)

**Dr. S. Okonkwo, Ph.D. Computational Mechanics (Imperial College London, 2012)**
- 12 years FEA experience, specialist in contact mechanics and fracture
- Internal certification: MDS-PROC-0034 Level IV (Senior Reviewer)
- Served as independent technical reviewer for this project; no involvement in original model development

---

## A.6 Uncertainty Sensitivity Tornado Chart Description

A tornado chart was generated to rank uncertainty sources by their contribution to peak stress variability (archived as MDS-FEA-LUMBAR7/uncertainty/tornado_peak_stress.png). Ranked by absolute effect on peak stress:

1. Applied physiological load (±15%): ±69.9 MPa
2. Locking tab root geometric tolerance (±0.10 mm): ±29.8 MPa
3. Endplate contact friction coefficient (±0.1): ±14.9 MPa
4. Mesh discretization error (GCI bound): +6.5 MPa (one-sided, conservative)
5. Ti-6Al-4V elastic modulus (±3 GPa): ±5.6 MPa
6. PEEK elastic modulus (±0.4 GPa): ±3.7 MPa

The chart confirms that load uncertainty and geometric manufacturing tolerance are the dominant drivers of prediction uncertainty, and that material property uncertainty is a secondary contributor. This prioritization should guide future uncertainty reduction efforts — specifically, tighter manufacturing tolerance on the locking tab root radius would provide the most efficient reduction in stress prediction uncertainty after the load variability itself.

---

*End of Appendix A*
