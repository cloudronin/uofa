# Appendix A — Stumble Load Case Results and Additional Sensitivity Studies

**Document Number:** SCA-FEA-2024-0047-R2 / Appendix A
**Revision:** 1
**Date:** 2024-06-14

---

## A.1 Stumble Load Case

Following the independent reviewer's recommendation (Section 6.2 of main report), a stumble event load case was added to the simulation campaign. The stumble load is defined as 4× body weight (3,200 N × 4 = 12,800 N resultant) applied at 20° adduction per Bergmann et al. (2001) stumble data. This represents an infrequent but biomechanically significant event.

**Results summary (M3 mesh, single stumble cycle):**

| QoI | Stumble Result | Gait Result (reference) |
|-----|---------------|------------------------|
| Peak von Mises stress, stem neck (MPa) | 712 | 441 |
| Max principal strain, cortical bone (με) | 3,210 | 1,934 |
| Interface micromotion, distal (µm) | 148 | 65 |

The stumble peak stress of 712 MPa exceeds the Ti-6Al-4V yield strength of 880 MPa by a comfortable margin (no yielding predicted). The cortical strain of 3,210 με approaches but does not exceed the commonly cited fracture threshold of approximately 25,000 με (Reilly & Burstein, 1975). Interface micromotion of 148 µm is just below the 150 µm osseointegration threshold, indicating the design is at the edge of acceptable performance under stumble loading.

The stumble case does not change the overall credibility assessment but is noted as a design sensitivity that should be re-evaluated if any geometry changes are made to the distal stem profile.

---

## A.2 Neck Angle Sensitivity

The HS-400 series is available in standard (132°) and high-offset (127°) neck-shaft angle configurations. The main report results correspond to the standard configuration. A parametric study was conducted by modifying the CAD-derived geometry for the 127° configuration and re-running the M3 mesh under the standard gait load.

| Configuration | Peak Stem Stress (MPa) | Micromotion (µm) |
|---------------|------------------------|------------------|
| 132° (standard) | 441 | 65 |
| 127° (high-offset) | 468 | 71 |

The 6.1% increase in peak stress for the high-offset configuration remains within the fatigue endurance limit (prior to surface finish knockdown). The same surface finish risk item identified in the main report applies to the high-offset configuration with slightly reduced margin.

---

## A.3 Element Formulation Sensitivity Check

A secondary check was performed to confirm that the choice of C3D10M elements in the implant does not introduce significant formulation-dependent bias. A subset model of the stem neck region was re-meshed using C3D20R (20-node quadratic hexahedral) elements and solved under the gait load case. The C3D20R result for peak neck stress was 445 MPa, compared to 438 MPa for C3D10M on the equivalent mesh density — a difference of 1.6%. This is within the expected range of inter-formulation variation for this geometry class and provides additional confidence that the tetrahedral mesh is not introducing systematic stiffness error.

---

## A.4 Contact Algorithm Verification

The finite-sliding surface-to-surface contact formulation was verified against a small-scale benchmark: a rigid cylinder pressed into a deformable flat (Hertz contact). Contact pressure distribution and peak pressure matched the Hertz analytical solution to within 2.1%. Additionally, the production model was re-run with the contact formulation switched to node-to-surface to assess sensitivity; peak stem stress changed by less than 0.9% and micromotion changed by 3.2%. The surface-to-surface formulation is retained as it is more accurate for curved contact geometries per Abaqus documentation.

---

## A.5 Fatigue Life Estimation Methodology

Fatigue life at the stem neck was estimated using the Goodman mean stress correction applied to the alternating and mean stress components extracted from the cyclic gait loading. The stress ratio R for the gait cycle was computed as −0.12 (compressive reversal during swing phase). Using the modified Goodman diagram constructed from the manufacturer's S-N data (R = −1 baseline, corrected for mean stress):

- Alternating stress amplitude at peak location: 218 MPa
- Mean stress: 223 MPa
- Goodman-corrected allowable alternating stress: 231 MPa

This yields a fatigue usage factor of 218/231 = 0.94, indicating the design is within the infinite-life regime for the gait load case prior to surface finish correction. After applying the 0.85 surface finish knockdown to the allowable, the corrected allowable drops to 196 MPa, giving a usage factor of 218/196 = 1.11 — confirming the negative margin noted in the main report.

It is emphasized that this fatigue assessment is based on the simulation stress field and the manufacturer's coupon-level material data. It does not substitute for physical fatigue testing per ASTM F2996, which is being conducted in parallel and will be reported separately.

---

## A.6 Model Archival and Reproducibility Statement

The complete simulation package — including geometry files, mesh files, material property tables, boundary condition scripts, Dakota uncertainty quantification input decks, and post-processing scripts — has been archived to the organization's validated document management system (Windchill 12.1, archive record AR-HS400-FEA-2024-047). The archive includes a README file with step-by-step instructions sufficient for an independent analyst to reproduce all results reported herein. A reproduction check was performed by a third analyst (not involved in the original work) who successfully reproduced the M3 gait load peak stress to within 0.1% (rounding in output file) following only the archived instructions.

---

*End of Appendix A*
