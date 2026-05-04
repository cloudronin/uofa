# Appendix A — One-at-a-Time Sensitivity Study Results
## OrthoStem-7 FEA Credibility Assessment | OSP-FEA-CR-2024-011

---

### A.1 Sensitivity Study Setup

All sensitivity runs used the M3 mesh (512,000 elements, C3D10) with the nominal Abaqus/Standard 2023.HF4 solver configuration. Each parameter was perturbed ±10% from its nominal value independently. The output quantity of interest in all cases is peak von Mises stress in the neck fillet region (element centroid of the highest-stress element, confirmed consistent across all runs).

Nominal peak von Mises: **519.4 MPa**

---

### A.2 Results Table

| Parameter | Nominal Value | −10% Result (MPa) | +10% Result (MPa) | Max |ΔS| (MPa) | % Sensitivity |
|-----------|--------------|-------------------|-------------------|----------------|---------------|
| Ti-6Al-4V elastic modulus | 114 GPa | 513.2 | 525.6 | 6.2 | ±1.2% |
| Poisson's ratio | 0.342 | 517.8 | 521.0 | 1.6 | ±0.3% |
| Cement simulant modulus | 2.5 GPa | 503.3 | 535.5 | 16.1 | ±3.1% |
| Applied load magnitude | 2300 N | 467.5 | 571.3 | 51.9 | ±10.0% |
| Load application angle | 10° | 483.9 | 554.7 | 35.3 | ±6.8% |

---

### A.3 Notes on Load Magnitude Sensitivity

The ±10.0% sensitivity to load magnitude is expected and essentially linear (the problem is linear elastic), confirming that the model is behaving correctly. This sensitivity is not a concern because the ISO 7206-4 load magnitude is a controlled test parameter, not a source of physical uncertainty.

### A.4 Notes on Load Angle Sensitivity

The load angle sensitivity (±6.8% for ±10% angle variation, i.e., ±1° variation from the nominal 10°) is the most practically important finding. ISO 7206-4 specifies the load angle to ±1°, which corresponds to approximately ±6.8% stress variation. At the upper bound (10° + 1° = 11°), the predicted peak stress would be approximately 554 MPa — which exceeds the applied fatigue limit of 539 MPa. This finding was communicated to the project team on 2024-08-14 (email thread archived as OSP-COMM-2024-0814-AK). The test laboratory has confirmed that their fixture controls the angle to ±0.3°, which corresponds to a stress variation of approximately ±2.0%, keeping the upper bound at approximately 529.8 MPa — still within the fatigue limit.

This fixture tolerance confirmation is critical to the safety case and should be formally documented in the test report (OSP-TEST-2024-018).

---

# Appendix B — Documents Reviewed

| Ref | Document Title | Rev | Date |
|-----|---------------|-----|------|
| [1] | Model Development Report — OrthoStem-7 FEA | B | 2024-08-30 |
| [2] | Credibility Planning Document — OSP FEA Program | A | 2024-05-15 |
| [3] | Software Qualification Record — Abaqus/Standard 2023 | A | 2023-11-01 |
| [4] | Material Test Report — Ti-6Al-4V ELI Coupon Testing | C | 2024-03-22 |
| [5] | ISO 7206-4:2010 — Implants for surgery — Bone and joint replacement | — | 2010 |
| [6] | FDA Guidance: Reporting of Computational Modeling Studies in Medical Device Submissions | — | 2021-12 |
| [7] | MMPDS-12: Metallic Materials Properties Development and Standardization | — | 2017 |
| [8] | ASME V&V 40-2018: Assessing Credibility of Computational Modeling | — | 2018 |
| [9] | CMM Calibration Certificate — Zeiss Contura G2 | — | 2024-01-15 |
| [10] | Strain Gauge Validation Test Raw Data — OSP-TEST-2024-009 | A | 2024-07-31 |
| [11] | Git Archive: OSP-FEA-2024, commit 3f8a1c2 | — | 2024-08-29 |
| [12] | Independent Rebuild Verification Memo — CMG-IVR-2024-003 | A | 2024-09-05 |

---

# Appendix C — Mesh Quality Visualizations

*[Figures C-1 through C-4 are embedded in the digital version of this report. Print version: contact document control for high-resolution exports.]*

- **Figure C-1:** M3 mesh overview — full stem geometry, isometric view
- **Figure C-2:** M3 mesh detail — neck fillet region, showing bias refinement
- **Figure C-3:** Jacobian ratio distribution — M3 mesh (color map, range 0.6–1.0)
- **Figure C-4:** von Mises stress contour — M3 mesh, ISO 7206-4 loading, 2300 N

---

# Appendix D — Strain Gauge Location Documentation

Gauge positions were selected by the analyst prior to model solution (pre-test prediction protocol) to avoid confirmation bias in gauge placement. Locations were chosen to span: (a) the peak stress prediction zone (G1, G2), (b) the compressive side of the neck (G3), (c) the mid-stem transition (G4), and (d) a low-stress reference region (G5) to verify baseline calibration.

CMM registration confirmed all gauge centers within ±0.4 mm of the CAD reference coordinates. The registration uncertainty contributes an estimated ±1.2% to the predicted-vs-measured comparison at G1 and G2 (highest stress gradient), and less than ±0.5% at G3–G5. This positional uncertainty is included in the ±10% acceptance criterion budget.

---

*End of Appendix*
