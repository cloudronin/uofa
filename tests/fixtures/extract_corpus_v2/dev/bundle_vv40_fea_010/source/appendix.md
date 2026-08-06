A1. Mesh and solver details

- Mesh statistics (nominal):
  - Total elements: 1,253,418 (C3D10)
  - Stem elements: 412,037; Bone elements: 841,381
  - Min/mean/max edge length in contact zone: 0.26 / 0.34 / 0.49 mm
  - Contact facet count: 46,128
- Refinement levels:
  - Coarse: 751,209 total, contact zone target size 0.45 mm
  - Fine: 2,403,771 total, contact zone target size 0.22 mm

Convergence samples (S3 gait-like):
- 95th-percentile interface relative motion (µm):
  - Coarse: 116.1
  - Nominal: 112.0
  - Fine: 110.2
  - Estimated asymptote: 108.8 (Richardson fit, observed order ~1.7)
- 99th-percentile stem von Mises (MPa):
  - Coarse: 541
  - Nominal: 517
  - Fine: 507
  - Estimated asymptote: 500 (observed order ~1.9)
- Residual norms:
  - Final force residual ratios: 1.9e-6 (coarse), 6.2e-7 (nominal), 4.8e-7 (fine)

A2. Mapping of test ROIs to model patches

- Landmarks: lesser trochanter tip, femoral head center, lateral flare point.
- RMS alignment error between DIC ROI centroids and model patch centroids: 1.2 mm.
- Sensitivity to 2 mm misalignment: micromotion 95th-percentile changes by +1.1% in S4.

A3. UQ sampling details

- 150-point Latin hypercube in five dimensions (μ, Ez, Ecancellous, interference, load, plus small alignment angle jitter).
- PCE fit diagnostics:
  - Cross-validated RMSE: micromotion 2.8 µm; stress 11 MPa.
  - Leave-10%-out validation: R² = 0.981 (micromotion); 0.987 (stress).
- Surrogate residual histograms approximately normal; no significant heteroscedasticity.

A4. Alternative solver cross-check (ANSYS)

- Elements: 2nd-order tetrahedra (TET10); comparable mesh density in contact zone.
- Contact: augmented Lagrange with μ = 0.42.
- S5 ISO 7206-4:
  - Neck axial strain at G1: Abaqus 1640 µε; ANSYS 1601 µε (−2.4%).
  - Max stem stress: Abaqus 521 MPa; ANSYS 509 MPa (−2.3%).

A5. Peer review comments and dispositions

- Comment 1 (composites vs cadaveric): Add Ez scatter per literature; addressed by adding Normal(σ=1.2 GPa). Additional cadaveric-specific validation deferred to D4.
- Comment 2 (hardware reproducibility): Completed; EPYC + OpenBLAS run within 0.2% of Intel + MKL.
- Comment 3 (tuning separation): Adopted; S1–S2 for tuning, S3–S5 for comparison.

A6. Change log relevant to this assessment

- c7a9f5f: Final scripts; UQ surrogate training; nominal runs updated after minor bug fix in ROI mapping.
- 9f28c03: Corrected potting length for ISO 7206-4 from 70 to 80 mm after reviewer note; re-ran S3–S5.
- 2bb3a44: Introduced tapered interference; improved micromotion agreement on S1–S2.

A7. Acceptance criteria rationale

- 150 µm micromotion threshold derives from a synthesis of Carter et al. (1988) and newer porous coating ingrowth studies; we use it as a conservative pre-screen level recognizing contact-only modeling tends to slightly underpredict stick-slip.
- 600 MPa stress level selected to keep away from the Ti-6Al-4V fatigue knee for R = 0.1 with expected surface finish, providing headroom before full HCF analysis.

End of appendix.
