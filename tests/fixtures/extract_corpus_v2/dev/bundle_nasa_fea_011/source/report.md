# Credibility Assessment Report — FEA of Starlink-GEO Instrument Deck Bracket

Project: STAR-GEO-IPS-Deck Bracket M&S Assessment  
Model: ANSYS Mechanical 2023R2 finite-element model of the Instrument Deck Support Bracket (P/N 32-7412)  
Prepared by: Structures and Dynamics, Lunar Point Systems  
Date: 2026-08-05  
Intended use: Pre-test prediction and design verification of bracket stresses, deflections, and margins under quasi-static launch loads, limit thermal soak, and sine qualification; screening for local buckling and first modal frequency.

## 1. Background and Context

The Instrument Deck Support Bracket (IDSB) is a machined 7075‑T7351 aluminum component that transfers loads from the telescope deck to the central cylinder. The design is weight-critical and carries significant launch loads via four M8 fasteners and two dowel pins. The finite-element model is used to justify the release of the drawing for FAI and to reduce the number of physical test iterations. The decision authority is the Loads & Dynamics Control Board (LDCB).

This assessment documents the evidentiary basis for using the model within a specific decision envelope, in accordance with our program M&S management plan LPS-MSP-014 and the launch provider’s structural verification requirements.

## 2. Model Description and Assumptions

- Platform: ANSYS Mechanical 2023R2, double precision, running on RHEL 8.8, Intel Xeon 6348.
- Elements: Predominantly 10-node tetrahedra with quadratic displacement interpolation (SOLID187). Fasteners represented by pretension beam elements (BEAM188) tied with MPCs; local contact via surface-to-surface augmented Lagrange with friction coefficient 0.2 at the bracket-to-deck interface.
- Material model: Isotropic elastic-plastic with bilinear hardening; E = 71.7 GPa, nu = 0.33, sigma_y0 = 503 MPa, tangent modulus = 1.1 GPa. Thermal expansion coefficient 23.6 µstrain/°C for thermal case.
- Boundary idealizations: Outer cylinder interface constrained via RBE2 to represent a stiff interface; verification of this assumption performed via a sensitivity sweep with reduced interface stiffness factors.
- Geometry simplifications: Fillet radii below 0.75 mm removed; threaded regions replaced by smooth shanks with equivalent diameter. Chamfers retained only where they induce stress risers near load paths.
- Load cases: 
  - LC1: Quasi-static launch load, 25 g axial, 8 g lateral, combined with torque 75 N·m about the cylinder axis, applied as body accelerations and boundary moments.
  - LC2: Thermal soak +55 °C uniform, with differential CTE relative to Ti-6Al-4V deck inserts ignored (justification below).
  - LC3: Sine qualification equivalent static envelope 1.5x limit, 5–50 Hz, simplified to 1.5x LC1 for bolt preload evaluation.
  - LC4: Modal extraction for first three eigenpairs, free-free of bracket-subassembly.

Key suppositions:
- The deck insert’s titanium-to-aluminum CTE mismatch is accommodated primarily in the floating insert assembly; stiffness testing supports this (Appendix A.3).
- Contact stick/slip behavior at 0.2 friction models the as-cleaned, Al-on-Al condition; dry film lubricant is not present on flight surfaces per process spec PPS-AL-19.

## 3. Planning and Governance

- Credibility targets established in CRB-17: 
  - Maximum allowable error in predicted peak von Mises stress at the critical fillet ≤ ±12% relative to test, to maintain a minimum safety margin of 1.25.
  - Frequencies to be within 5% of test for the first bending mode.
  - Provide a quantified mesh refinement demonstration at the stress hotspot with estimated numerical uncertainty ≤ 6%.
- Traceability controlled via GitLab repo M&S-FEA-IDS-32-7412; model configurations tagged v1.0–v1.4. Analysis plan approved in LPS-MSP-014-AnnexC; waivers recorded for omitted preload relaxation simulation during sine dwell (justification: out of scope per load environment).

## 4. Personnel and Roles

- Primary analyst: M. Trivedi (MSME, 12 years structural FEA; ANSYS Certified Professional).
- Checker: R. Kim (PE, 15 years launch structures; not in the design team; no edit permissions to model branch).
- Independent reviewer: J. Adebayo (PhD, UQ focus), from the Systems V&V group, not reporting to Structures.

Analyst training records include ANSYS 2023R2 advanced contact course (Cert# AMEC-34922) and in-house bolted-joint modeling workshop (Feb 2026).

## 5. Software and Configuration Controls

- ANSYS Mechanical verified against vendor’s verification suite; all 218 regressions passed on this workstation image. Key solver options locked via Mechanical APDL scripts to prevent unintended changes.
- External scripts (Python 3.10) for post-processing and result extraction are under version control with unit tests (pytest) covering 92% of lines. CI pipeline executed on each commit; no failing tests at tag v1.4.
- Hardware/OS image captured; solver build hash 2023R2-21.4.0.27 stored in run log. Randomization features disabled; contact stabilization parameters explicitly written in .inp to ensure deterministic reruns.

## 6. Numerical Checks

### 6.1 Code-level confidence
- Patch tests conducted for linear elasticity (cantilever beam under end load; analytical deflection 4.167 mm; FE predicted 4.162 mm at 50k DOF). 
- Contact pressure distribution on Hertzian sphere/flat reproduced within 3% of analytic maximum pressure for coefficient 0.2, using the same contact formulation as the bracket model.
- Bolt pretension verification: 10 kN target produced 9.98–10.02 kN across mesh densities; linearity preserved.

### 6.2 Solution quality controls
- Mesh refinement study focused on the fillet F3 (R=1.5 mm) adjacent to the highest load path. Four meshes: 
  - M1: 0.8 mm target size, 0.35M elements; 
  - M2: 0.6 mm, 0.58M; 
  - M3: 0.45 mm, 0.94M; 
  - M4: 0.35 mm, 1.32M.
- Richardson-type extrapolation applied to local stress with quadratic fit in element edge length; estimated asymptotic peak stress at hotspot: 316 MPa. Predicted peaks: M2 307 MPa, M3 312 MPa, M4 314 MPa. Extrapolated mesh-induced uncertainty on M4: ±2.1% at 95% confidence.
- Contact penetration tolerances tightened from default 1e-3 m to 1e-6 m; sensitivity study showed <0.5% change in peak stress between tolerances 1e-5 and 1e-6 m.
- Nonlinear convergence: force residual ≤ 0.5% of reference per substep; arc-length controls disabled; automatic time stepping with min substep 1e-3. No cutbacks observed post-tuning.

## 7. Data Provenance and Parameter Estimation

- Geometry: From CATIA V5 master model Rev F; simplified via ANSYS SpaceClaim script sc_clean_v7.py. All defeaturing steps logged.
- Material: Allowables drawn from MMPDS-17 for 7075‑T7351; plastification curve adjusted using in-house coupon tension tests (n=6) performed May 2026, lot-matched to the forging billet used for the bracket. The bilinear hardening parameter identified via least-squares fit to 0.2–1.0% plastic strain range (R^2=0.997).
- Friction coefficient: Based on tribometer test TRIB-AL-20 (Al-on-Al, solvent-cleaned), mean 0.22, SD 0.04, under 2 MPa normal pressure; selected value 0.20 is conservative for slip initiation.
- Bolt preload: Specified at 9 kN per M8 fastener using torque-tension relation with K=0.22; we back-calculated initial strain for BEAM188 pretension sections. A cross-check with strain-gaged bolt test (n=3) yielded achieved loads 8.7–9.3 kN.

All input datasets have recorded sources, calibration certificates (for tribometer and extensometer), and lot numbers in the repository folder data/pedigree.

## 8. Comparison with Bench and Subassembly Tests

Two rounds of physical tests were run on the bracket-subassembly:

- Static pull test (Subassy SN-003): Applied axial 25 g equivalent load via a hydraulic frame with a load cell (class 0.5). DIC recorded strain field near fillet F3. Measured peak von Mises inferred via calibrated strain-to-stress mapping: 321 ± 10 MPa.
- Modal tap test (Subassy SN-002): First bending mode at 463 Hz, second at 611 Hz; LMS Scadas, 1,024 lines, 0.5% coherence cutoff.

Correlation:
- LC1: FEA peak at fillet F3 (mesh M4) 314 MPa vs measured 321 MPa; absolute error 2.2%; within target. Spatial placement of peak within 2.1 mm of DIC maximum.
- Modes: FEA predicts 452 Hz and 602 Hz; deviations −2.4% and −1.5%, within goal. MAC values 0.96 and 0.91, indicating shape agreement.
- Load path verification: Bolt shear load split 28/24/24/24% in FEA; strain-gage rosette indicated 29/24/23/24%.

Validation coverage:
- The tested load magnitude matches LC1; lateral component was not applied separately, but combined vector magnitude was matched within 1.5%. Thermal case has no direct test; proxy coupons validated CTE and modulus over the temperature band. Discussion of this gap is in Section 11.

## 9. Uncertainty and Error Budget

We decomposed contributors to prediction spread for the LC1 stress response at F3:

- Numerical resolution (mesh): ±2.1% (Section 6.2).
- Material curve fit: Propagated via Monte Carlo (10k samples) from parameter covariance; ±3.2%.
- Friction coefficient: Uniform 0.18–0.24; yields ±1.8% on hotspot stress.
- Bolt preload scatter: Normal with SD 0.3 kN; ±0.7%.
- Boundary stiffness idealization: Sensitivity run with interface stiffness scaled 0.5×–2× resulted in ±2.5%.

Assuming weak correlations (checked pairwise via Sobol’ indices), the combined one-sigma uncertainty is approximately 5.1%. A conservative 95% bound is ±10%. This fits inside the 12% target set by the board.

For eigenfrequencies, mesh density and joint stiffness dominate; aggregate uncertainty estimated ±3.6%, corroborated by correlation with the tap test.

## 10. Sensitivity and Robustness

- Local mesh density and fillet radius dominate the stress outcome. A 0.1 mm reduction in the F3 radius increases peak stress by ~6.5%; this matches CAD tolerance analysis. 
- Slip onset: With mu reduced to 0.12, local micromotions occur around 75% of LC1; at mu ≥ 0.2, no slip predicted. Even when slip is allowed, bolt loads remain within allowable shear.
- Load-case perturbations: Applying a ±10% variation to the lateral component changes peak stress by ±3.7%. The model behaves smoothly with respect to load scaling; no numerical oscillations noted.
- Extrapolations: Beyond 1.8× LC1, tangent stiffness reduces due to plasticity; model remains convergent to 2.2× LC1. This is outside the stated envelope, offered only as a robustness check.

## 11. Applicability and Limits

The model is intended for pre-test prediction and verification at ambient to +55 °C only. It does not account for:
- Time-dependent preload relaxation during multi-minute sine dwell. We provide rationale: bench measurements at 25 °C showed <2% preload decay over 20 min. For flight acceptance, a separate bolted-joint life analysis will be performed.
- CTE mismatch with Ti inserts under thermal gradient. For uniform soak, relative slip is restrained by the insert design; our thermal case applies uniform temperature. Non-uniform thermal states are out of scope and would require a joint contact thermal-mechanical analysis.
- Surface roughness effects on contact compliance. The current stiffness assumption matches measured joint stiffness from the static test.

Use bounds:
- Acceleration up to 1.5× LC1 and temperatures −10 to +55 °C.
- Geometry variations within current dimensional tolerances and material lot properties per MMPDS-17.

## 12. Prior Application History

A predecessor bracket (P/N 32-6301) was analyzed with the same modeling approach and validated against static and modal tests in 2024; frequency prediction error was −3.1%, stress at comparable fillet within 6.8% of test. Three subsequent flight units passed qualification without structural nonconformances. The same analyst and checker team conducted those analyses.

## 13. Review and Oversight

- A structured technical interchange meeting occurred on 2026-07-12 with Systems V&V and Materials. Action items included expanding the mesh refinement to a fourth level (completed) and adding a joint stiffness perturbation study (completed).
- The independent reviewer reran the model on a separate machine using the archived input files and reproduced LC1 within 0.6% on peak stress; small deviations attributed to BLAS library differences.
- An external peer from the Launch Vehicle Partner inspected the load paths and bolt modeling choices; no findings.

## 14. Reproducibility, Traceability, and Audit Trail

- Every result figure is generated by scripts that read the ANSYS result file and write the report images with embedded metadata (commit SHA, solver build hash, run date).
- The CAD-to-mesh pipeline is scripted and deterministic; random seed not used for tetrahedralization.
- The test correlation notebook includes raw DIC images, calibration grids, and processing code. Snapshots of instrument calibration for the load cell and accelerometer used in modal test are included.

## 15. Results Summary

- LC1 peak von Mises at F3 on mesh M4: 314 MPa, with a 95% total uncertainty bound of ±10% considering all identified sources. The minimum yield margin using 503 MPa is (503 − 314)/503 = 0.376; even at the upper uncertainty bound (+10%), margin is 0.25, above the program-required 0.20.
- LC2 thermal: Maximum thermal stress 42 MPa; negligible relative to yield; deflection at the deck interface 0.11 mm consistent with CTE-based estimate.
- LC3 sine-equivalent: No bolt rotation or separation predicted; contact pressures remain compressive with minimum 7.4 MPa.
- Modal: First two modes 452 Hz and 602 Hz; both exceed the 400 Hz minimum requirement with comfortable margin.

## 16. Credibility Synthesis

The body of evidence supports use of this model for the stated decisions:

- The numerical behavior has been interrogated: mesh refinement and contact tolerance sweeps indicate stable convergence and small residual numerical error at the point of interest.
- Physical fidelity is grounded in relevant tests: static and modal subassembly data align with predictions within the predefined acceptance windows. While thermal validation is indirect, the physics involved are linear-elastic and well characterized.
- The inputs are traceable and reflect the as-built and as-tested hardware. Adjustments (e.g., material curve) were data-driven and transparently documented.
- Uncertainty has been gathered into a quantitative error bar that propagates dominant sources and leaves sufficient design margin.
- The team executing and reviewing the work have documented qualifications, the analysis plan was followed, and the work product is under configuration control.
- The modeling approach has a track record on closely related hardware.

Caveats remain around long-duration preload relaxation under temperature and combined environments with thermal gradients. These are explicitly outside the accepted envelope below.

## 17. Limitations and Open Work

- No direct test correlation for uniform thermal soak on the assembled joint. A planned environmental chamber test during TRR will give a cross-check; not required for the present release to manufacturing.
- We did not simulate fretting or wear at the contact surfaces; the intended use does not depend on life prediction.
- The bolt torque–tension relation uses K=0.22 based on a limited test set (n=3). Additional torque-tension characterization could reduce preload uncertainty.
- Nonlinear material behavior beyond 1% plastic strain is approximated by a bilinear curve; for qualification-by-analysis of extreme off-nominal loads, a multi-linear fit may be warranted.

## 18. Decision

By authority of the Loads & Dynamics Control Board (LDCB), the ANSYS Mechanical model of the Instrument Deck Support Bracket, configuration tag v1.4, is accepted for:
- predicting stresses, deflections, and load paths under LC1, LC2, and LC3 as defined herein, and
- demonstrating compliance with the first-mode frequency requirement,

subject to the following conditions:
- it is approved for use in the acceleration and temperature ranges described in Section 11 only, and
- any geometry changes exceeding the current tolerance envelope or material lot substitutions require re-review.

This decision was recorded in LDCB minutes LDCB-2026-07, agenda item 5. The model is not approved for life prediction, fretting analysis, or combined thermal gradient plus dynamic environments beyond the envelope described.

## 19. References

- LPS-MSP-014, Modeling & Simulation Management Plan, Rev C.
- MMPDS-17, Metallic Materials Properties Development and Standardization.
- ANSYS Mechanical 2023R2 Verification Manual.
- Test reports: STAT-IDS-003 (static), MOD-IDS-002 (modal), TRIB-AL-20 (friction).
- Internal scripts repository: M&S-FEA-IDS-32-7412 (tag v1.4).

---
Appendices with detailed meshes, test matrices, and sensitivity results are provided separately.
