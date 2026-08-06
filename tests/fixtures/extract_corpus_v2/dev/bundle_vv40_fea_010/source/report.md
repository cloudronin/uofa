Title: Credibility Report for FEA of a Pedicle Screw–Rod Spinal Fixation Construct under ASTM F1717 Loading

Date: 2026-08-06
Prepared by: Mechanics & Reliability Group, Ortheon Devices, Inc.

1. Executive Summary

This report assesses the trustworthiness of a finite element model used to evaluate a thoracolumbar pedicle screw–rod construct subjected to the vertebrectomy surrogate loading specified in ASTM F1717. The model’s stated purpose is to support engineering decisions on worst-case design selection and to justify material/geometry margin prior to design freeze, with downstream use in test planning. The degree of confidence needed is “moderate-high,” because the model informs design choices and test matrix reduction but does not replace regulatory bench testing.

In brief:

- The computational workflow is implemented in Abaqus/2023.HF3 with a controlled pre/post scripting environment (Python 3.10, numpy 1.26), and has undergone internal code checks against NAFEMS and closed-form benchmarks.
- Mesh and contact resolution studies demonstrate numerical stability and solution monotonicity; grid uncertainty in peak von Mises stress is estimated at 3.2% for the converged mesh.
- Validation is performed against internal static and fatigue tests following ASTM F1717 with gage-length and fixture conditions matched to the model; the comparisons show agreement within 6.5% for static stiffness and 9.1% for maximum displacement at 400 N. Strain distribution patterns agree qualitatively with DIC, and key peak responses match within combined uncertainty.
- Inputs (geometry, material data, torque–preload conversion, friction) are sourced from measured specimens, manufacturer’s traceable certificates, and literature where needed; influential inputs were mapped via global sensitivity.
- Uncertainty propagation (Latin Hypercube, n=500) yields a predicted distribution of construct stiffness with a 95% interval of 28.4–31.7 N/mm around the nominal 30.0 N/mm; this envelope encompasses the test-derived mean of 29.6 N/mm with its measurement uncertainty.

Residual gaps are limited to micro-scale fretting at the set-screw–rod interface (not explicitly modeled) and environmental aspects (temperature/humidity) considered negligible for titanium alloy behavior. These are judged not to materially affect the model’s role in pre-test design screening.

2. Background and Intended Use

2.1 Device and question being answered
The device is a pedicle screw–rod system with Ø5.5 mm Ti-6Al-4V ELI rods, polyaxial tulips, and conical-threaded screws, evaluated in the ASTM F1717 vertebrectomy surrogate configuration. The central engineering questions are:

- Do worst-case geometries (shortest working length, smallest rod diameter, longest screw offset) meet static stiffness and peak stress targets with a minimum 20% margin before physical testing?
- What torque on the set screw is sufficient to avoid microslip under the standard static load case?

2.2 Decision importance and consequence of error
The model informs down-selection of two candidate rod design variants and set-screw torque guidance for test setup. A wrong prediction could delay verification and increase test iterations, but patient safety is not directly affected because regulatory bench testing remains mandatory. Based on internal risk matrices, the modeling decision is categorized as medium impact, requiring substantial evidence but not full formal qualification of the solver.

3. Model Description

3.1 Geometry and features
- Full 3D solid model built from CAD (SolidWorks 2024); features include thread roots at the set screw, dome interface of the rod seat, and the tulip split.
- ASTM F1717 blocks are represented with machined UHMWPE geometry per the standard; only contact patches and fixture screws are modeled in detail to capture local stiffness.

3.2 Materials and constitutive behavior
- Ti-6Al-4V ELI for rod and screw: elastic–plastic with isotropic hardening; E = 113 GPa ± 2 GPa, ν = 0.34, σ0.2% = 860 ± 25 MPa; hardening law from tensile coupons (Appendix A).
- UHMWPE blocks: elastic, E = 0.95 ± 0.1 GPa, ν = 0.40, following supplier certification and in-house compression tests.
- Set screw is the same titanium alloy; potential fretting/wear not resolved at micro-scale; hysteretic energy ignored in quasi-static analysis.

3.3 Discretization and element selection
- Predominantly C3D8I (8-node linear brick with incompatible modes) in metallic components for improved bending performance.
- C3D10 tetrahedra in filleted regions where hexahedral meshing is impractical; maximum aspect ratio < 4, Jacobian > 0.6 verified.
- UHMWPE blocks modeled with C3D8R and enhanced hourglass control.
- Mesh sizes: 0.2 mm nominal at thread roots and rod seat; 0.5–1.0 mm elsewhere; total DOF ~4.1 million.

3.4 Contact and fastener modeling
- Surface-to-surface finite sliding, penalty formulation; default Abaqus tangential behavior with μ = 0.15 ± 0.05 (titanium–titanium), μ = 0.2 for titanium–UHMWPE, sensitivity checked.
- Set-screw preload imposed via bolt load feature calibrated against measured elongation at 6.0 N·m torque using torque–tension testing; nominal preload 6.5 ± 0.8 kN.

3.5 Boundary conditions and loading
- Fixture screws into UHMWPE constrained per ASTM F1717; lower block fully constrained; upper block displacement-controlled in the vertical (Y) direction.
- Static displacement ramp to 6 mm at 6 mm/min equivalent rate; quasi-static assumption validated via negligible inertia effects (KE/IE < 0.5%).
- For fatigue life context, only static and small-amplitude elastic cycles are considered; high-cycle fatigue assessment references S–N curves externally and is not part of predictive scope.

4. Toolchain and Numerical Practices

4.1 Software and hardware
- Abaqus/Standard 2023.HF3 on RHEL 8.8, Intel Xeon Gold 6338N nodes, 256 GB RAM.
- Pre/post via Python 3.10 scripts; environment reproducible with conda lockfile (hash: 2fe1c0c…).
- Parallel runs with 16 cores per job; repeated runs show deterministic reproducibility (max numerical jitter in peak stress < 0.1%).

4.2 Integrity controls
- Inputs and meshes versioned in GitLab; model package tagged v1.7.3 (commit e1a8ab5).
- Continuous integration executes unit checks on scripts (flake8, pytest coverage 82%) and runs a smoke simulation on a small specimen mesh.
- Peer review checklist completed by a separate analyst prior to final runs.

4.3 Solver settings and convergence
- Nonlinear geometry on; automatic stabilization off; NL solver: full Newton; convergence tolerances: residual norm < 1e-6, displacement increment < 1e-5 mm.
- Contact stabilization factor tuned via penalty scaling study; final normal penalty selected at 10× nominal stiffness to limit penetrations < 0.5 μm.

5. Numerical Checks and Code Verification

- Element behavior confirmed with an internal patch test: linear elasticity reproduces constant stress state error < 0.3%.
- Three benchmark problems run:
  - Thick cylinder under pressure (Lame solution): hoop stress at r_i within 0.8% of analytical for 0.25 mm mesh.
  - Hertzian contact (sphere–flat): peak contact pressure within 4.5% of theory after mesh densification beneath footprint.
  - NAFEMS benchmark LE10 (bending of a plate): deflection difference 1.2%.
- Contact formulation sanity checks: two-block compression with known compliance to validate penalty scaling; model reproduces measured stiffness within 3.8%.

6. Solution Robustness and Discretization Adequacy

6.1 Mesh refinement
- Nested meshes M1/M2/M3 created by halving element sizes at hot spots:
  - M1: 0.32 mm at threads, DOF ~1.9M
  - M2: 0.23 mm, DOF ~3.1M
  - M3: 0.16 mm, DOF ~6.0M
- Peak von Mises at set-screw root (critical location):
  - σ_vm: 934 MPa (M1), 962 MPa (M2), 972 MPa (M3)
  - Extrapolated using Richardson with observed order p ≈ 1.85; estimated grid error at M2 is 1.0% and at production mesh (0.20 mm local) is 3.2% relative to asymptotic value.
- Construct vertical stiffness:
  - k: 28.8 N/mm (M1), 29.7 N/mm (M2), 29.9 N/mm (M3); changes < 0.7% from M2 to M3.

6.2 Time increment and solver studies
- Quasi-static steps with automatic incrementation; max increment 0.1 mm. Halving the increment caps changes peak stress by < 0.2%, confirming negligible temporal discretization error.

6.3 Contact parameter sensitivity
- Varying normal penalty by ×0.5 and ×2 shifts peak stress by −1.9% and +1.1% respectively; interface slip remains below 2 μm in all cases.

7. Assumptions and Model Form Choices

- Geometry includes thread roots and tulip slit; micro-roughness is not included.
- Friction coefficients are constant and Coulomb-type; no velocity dependence.
- UHMWPE is modeled as linear elastic; viscoelastic effects at the quasi-static rate are considered negligible; validated by rate-sweep data (Appendix B).
- Residual stresses from manufacturing are neglected based on XRD measurements on representative parts indicating < 30 MPa mean tensile bias, small compared to operating stresses.
- Symmetry is not leveraged due to asymmetric load path and tulip offset; full construct simulated.

Rationale: These simplifications aim to capture the load path and stress hot spots relevant to static F1717 performance while avoiding nonessential complexity. Their influence has been probed by sensitivity checks where feasible.

8. Input Data Pedigree and Uncertainty

- Geometry: Directly from CAD with as-built verification on 5 parts using a CMM; max deviation at rod diameter +0.03/−0.01 mm.
- Material properties: Tensile coupons from the same heat lot as test constructs; 10 coupons tested per ASTM E8; mean and standard deviation used for parameter distributions. Plasticity curve fitted with a Voce law; R^2=0.998; no overfitting evident.
- Preload: Torque–tension curve obtained from 8 assemblies with a calibrated torque wrench and ultrasonic bolt elongation; linear fit slope 1.14 kN/N·m (R^2=0.93); scatter modeled as normal with 0.8 kN SD.
- Friction: Based on literature for Ti–Ti and Ti–UHMWPE and two ring-on-disc measurements; assigned uniform ranges [0.10, 0.20] and [0.15, 0.25] respectively.
- Boundary conditions: ASTM fixture dimensions measured; block gage length 76 ± 0.2 mm; hole positions within ±0.1 mm.
- Measurement uncertainty (for validation): Load cell ±0.25% FS, LVDT ±0.02 mm, DIC strain uncertainty ~75 με.

9. Sensitivity Exploration

A Sobol global sensitivity analysis (Saltelli sequence, 2,000 model evaluations using a response surface surrogate validated to RMSE 7.8 MPa for peak stress and 0.14 N/mm for stiffness):

- Most influential on peak stress:
  - Set-screw preload (first-order index 0.43)
  - Friction μ (Ti–Ti) at rod-seat interface (0.22)
  - Rod diameter tolerance (0.18)
- Most influential on vertical stiffness:
  - UHMWPE modulus (0.36)
  - Construct working length (from rod seating depth) (0.31)
  - Friction μ (Ti–UHMWPE) (0.15)

Interactions between preload and friction contribute an additional 0.11 to total variance for peak stress. This mapping guided tolerance tightening and prompted direct measurement of UHMWPE modulus per batch.

10. Comparisons with Bench Tests

10.1 Test description
- Static compression bending per ASTM F1717 on MTS 858 frame, displacement control at 6 mm/min to 6 mm travel; five specimens per variant; instrumentation: load cell (20 kN), dual LVDTs, and DIC for strain field on tulip exterior.
- Fatigue tests at R=0.1 with 25–65% of static ultimate load; up to 5 million cycles; used for qualitative trend confirmation rather than direct life prediction by FEA.

10.2 Alignment between model and test
- Fixtures and boundary conditions replicated; gage length within tolerance; set-screw torque applied to 6.0 N·m using a calibrated wrench, matched to preload in the model via ultrasonic verification.
- Construct working length and rod seating verified and recorded; feeds model inputs.

10.3 Metrics and outcomes
- Vertical stiffness (slope over 0.5–3.0 mm travel):
  - Test mean: 29.6 N/mm (SD 0.7)
  - Model nominal: 30.0 N/mm
  - Difference: +1.4% (within combined uncertainty of 3.0%)
- Displacement at 400 N:
  - Test: 13.5 mm (due to compliance in fixtures and UHMWPE)
  - Model: 12.3 mm
  - After correcting for measured UHMWPE batch modulus (0.92 GPa vs assumed 0.95 GPa), model displacement adjusts to 12.8 mm; residual difference 5.2%, consistent with predicted uncertainty range.
- Peak strains at tulip crown (DIC vs model surface strains):
  - Qualitative hotspot location matches; quantitative peak differs by 8.4% on average; DIC uncertainty bounds encompass 4–6% depending on speckle quality.
- Load to 2% offset in construct bending:
  - Test mean: 980 N (SD 22)
  - Model predicted: 1,012 N
  - Difference: +3.3%; attributable primarily to assumed plasticity onset; within combined test+model uncertainty estimated at 5.1%.

10.4 Coverage
The test matrix covers:
- Two rod diameters (5.5 mm, 6.0 mm); model intended for 5.5 mm worst case.
- Working length 76 mm by design; small deviations recorded and fed into simulations for specific comparison runs.
- Preload window 5.0–7.0 kN observed; simulated range includes this spread.

11. Uncertainty Propagation and Confidence Intervals

A Latin Hypercube sample of 500 runs was conducted on a response surface validated against 50 high-fidelity FEA runs to limit computation. Inputs varied within their measured distributions:

- Predicted distribution of vertical stiffness: mean 30.1 N/mm, 95% interval 28.4–31.7 N/mm.
- Predicted peak von Mises at set-screw root at 400 N: mean 782 MPa, 95% interval 736–828 MPa.
- Fraction of runs exceeding 0.2% offset at 400 N: 0% (consistent with elastic regime).

Uncertainty in friction and preload dominates the tail behavior for peak stress; UHMWPE modulus governs stiffness spread. The model-to-test residual bias is small compared to these spreads and was accounted for in risk discussion.

12. Traceability and Reproducibility

- Each validation comparison is linked to a unique run configuration file (YAML) with hashes of input meshes and material cards; cross-referenced to test IDs.
- An independent analyst reproduced the primary validation case on different hardware (Windows 11, Abaqus/2023) and obtained peak stress within 0.7% and stiffness within 0.4% of the original.
- All raw data (FEA outputs, test logs, DIC images) archived in the PLM system (Agile PLM) with immutable audit trails.

13. Analyst Qualifications and Independence

- Lead analyst: Ph.D. in Mechanical Engineering, 12 years in orthopedic FEA; completed Abaqus Advanced Nonlinear course (2024).
- Test lead: P.E., 15 years in ASTM orthopedic testing.
- Cross-review performed by a modeling specialist not involved in geometry preparation; comments and dispositions captured in the review log.

14. Results Synthesis and Credibility Argument

- Numerical soundness: Mesh and contact resolution are appropriate; grid-induced error for critical responses is a few percent and bounded. Benchmarks and patch tests indicate the solver and element types behave as expected for the physics at hand.
- Physical relevance: The model reproduces the load path and compliance of the F1717 setup, including dominant interfaces; assumptions (e.g., linear UHMWPE) are justified by rate-insensitive behavior in the tested regime.
- Input quality: Geometrical and material inputs are largely measured from the same production lots used for testing; where data come from literature (friction), they are supported by spot measurements and explored across realistic bounds.
- Comparator quality and alignment: The validation tests adhere to the same configuration as simulated; instrumentation uncertainties are characterized; comparisons use both point metrics and field correlation.
- Predictive envelope: The propagated uncertainty bands overlap test results with low residual bias; sensitivity mapping identifies which inputs control decision-relevant outputs and shows limited risk of unexpected behavior outside the tested ranges.
- Process rigor: Version control, CI checks, peer review, and reproducibility exercises reduce the chance of user-induced or software-induced defects; documentation allows auditing end-to-end.

Assessment versus needed confidence: For the model’s intended role (pre-test screening and guidance), the combined evidence—calibrated inputs, mesh/contact studies, tight alignment with static tests, and uncertainty treatment—is sufficient. Remaining gaps (e.g., microslip and potential fretting under cyclic loading) are not decision-critical here, as they are addressed during physical fatigue testing and are not within model scope.

15. Limitations and Open Items

- Micromechanics at the rod–tulip interface under cyclic loads are not represented; the model should not be used to predict fretting wear or long-term loosening.
- Only the vertebrectomy configuration is covered; applicability to other standards (e.g., F1798 for subsystems) is not established by this report.
- Environmental conditions (temperature, moisture) are assumed nominal laboratory; while negligible for titanium elasticity, they can marginally affect UHMWPE stiffness; this is mitigated by batch-specific measurements when available.
- The fatigue comparisons were used qualitatively; no life prediction was attempted from FEA. A future extension could parameterize a notch-based fatigue approach, but this would require additional validation data.

16. Conclusions

The pedicle screw–rod FEA model provides reliable estimates of static stiffness and stress distributions for the ASTM F1717 vertebrectomy surrogate within a few percent of bench measurements, with quantified numerical and input uncertainty. The verification practices, test alignment, and sensitivity/uncertainty analyses collectively support using the model to make pre-test design decisions and to prioritize physical tests.

Approval to use this model for its stated purpose is recommended, subject to:
- Maintaining the same software version and solver settings documented here, or re-running a subset of verification checks if upgraded.
- Using measured inputs (UHMWPE modulus, set-screw preload) for each test batch where possible.
- Keeping interpretations within scope: no direct inference on fretting wear or fatigue life without additional, dedicated model development and validation.

17. References

- ASTM F1717-21. Standard Test Methods for Spinal Implant Constructs in a Vertebrectomy Model.
- Abaqus 2023 Documentation, Dassault Systèmes.
- Voce, E. The relationship between stress and strain for homogeneous deformation. J. Inst. Metals (1948).
- NAFEMS Benchmarks: Selected tests for linear/nonlinear elasticity and contact.

Appendices (see attached): 
- A. Material coupon data and plasticity curve fits
- B. UHMWPE modulus rate-sweep
- C. Detailed mesh statistics and quality metrics
- D. Validation run configurations and test IDs
