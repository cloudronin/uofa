Title: Credibility Assessment Report — Structural FEA of a Cementless Hip Stem for Preclinical Decision Support (vv40-aligned)

1. Executive summary

- Purpose: Evaluate whether a finite-element model (FEM) of a press-fit titanium hip stem in a composite femur provides decision-grade evidence to down-select design variants and refine test plans prior to bench testing.
- Bottom line: For the defined use (rank-ordering designs and estimating safety margins under ISO 7206-4-like loading and gait-like joint force/moment combinations), the model meets the requested rigor. Numerical checks, solver correctness exercises, and comparisons with benchtop strain data indicate the calculations are sufficiently reliable for the stated decisions and risk posture. Uncertainties and model boundaries are documented, and sensitivity mapping identifies the variables that matter most.
- Key limitations: Anatomical variability, extreme activities beyond validated loads, and bone remodeling over time are outside scope. The model is not intended for per-patient prognosis.

2. Background and use case

2.1 Device and physics
- Device: Cementless femoral stem (Ti-6Al-4V ELI) with a porous proximal coating; size 6, neutral neck, collarless. 
- Host structure: Composite femur (Sawbones fourth-gen left femur, medium) used as the experimental comparator.
- Primary outputs used in decision-making:
  - Peak von Mises stress in the stem at neck/shoulder fillets and proximal lateral face.
  - Max principal strain in the proximal femur cortex near Gruen zones 1 and 7.
  - Relative micromotion at the porous-coated interface under combined load.
- Physics: Quasi-static structural response with contact; small strains for materials, geometric nonlinearity only through contact closure. No fatigue life modeling — handled separately.

2.2 Decision context and risk posture
- Intended use of the model: 
  - Rank-order three stem design variants before fabricating full sets for ISO 7206-4 style mechanical testing. 
  - Set expected safety factors and define instrumentation for bench tests.
- Decision consequence if the model is misleading: Moderate — a poor choice could add one test iteration (~4–6 weeks, ~$80k) and delay verification, though patient risk is mitigated since clinical use requires separate testing and regulatory review.
- Degree to which the model influences the decision: Moderate — it narrows candidates and guides where to gauge, but final selection still requires bench evidence.
- Implication for rigor: Verification and validation activities targeted to mid-to-high levels; numerical errors should be small relative to design margins; comparisons to relevant experiments required under matching boundary conditions.

3. Data and comparators

3.1 Experimental program used for comparison
- Specimens: Five composite femurs nominally identical (Sawbones 3403); each received the same stem variant press-fit to a seating depth within 0.5 mm of the FE geometry. 
- Setup: Distal potting in epoxy (70 mm embedment) in an aluminum cup; load applied through a custom head/neck adaptor at 10° adduction and 9° flexion, following ISO 7206-4 line-of-action guidance.
- Loads: Two static conditions per specimen:
  - Case A: 2300 N axial resultant through the head center (ISO-like).
  - Case B: 3000 N with 20 Nm internal rotation moment to emulate a gait peak lateralization; zero out-of-plane shear.
- Instrumentation: 
  - Six 350-ohm strain gauges on the cortex: anterior and lateral near Gruen 1; medial near Gruen 7; posterior diaphysis reference. Gauge grid size 3.2 mm; aligned to anatomical axes; placement tolerance ±1 mm positioning, ±2° orientation.
  - Two rosettes at the stem shoulder on machined flats; data used qualitatively as the flats are not present in production geometry.
  - Crosshead load cell (0.5% FS), ancillary torque cell (1% FS).
- Environmental control: 21°C, dry; repeatability of seating verified by micro-CT on one specimen.

3.2 Measurement uncertainty and coverage
- Gauge calibration: Factory certified; in-situ shunt calibration verified drift <0.4% FS.
- Strain measurement repeatability: Standard deviation across five repeats per load ≤ 30 με at gauges with peak ~600–800 με.
- Comparator adequacy: The composite femur’s orthotropic layup is known; its modulus distribution is repeatable and published by the vendor. We modeled the same specimen family; see Section 5.3 for orthotropic mapping.

4. Numerics, software environment, and traceability

4.1 Software and QA controls
- Solver: Ansys Mechanical 2023 R2 (static structural), sparse direct solver, augmented Lagrange contact.
- Pre- and post-processing: SpaceClaim 2023 R2 for geometry edits; in-house Python scripts for gauge averaging and micromotion extraction; version-controlled in GitLab (project HSTEM-FEA, tag v1.8).
- Platform: Windows Server 2019, dual Xeon Gold, 192 GB RAM; deterministic solver settings; CPU-only.
- Reproducibility: Three independent reruns of the baseline case produced identical reaction forces and strains to within 0.2%.
- Software health: Internal benchmark suite (12 elasticity problems) executed upon environment update; all within tolerances prior to study start (see Appendix A1).

4.2 Solver correctness checks (code-level)
- Patch test: Eight-node hexahedra and ten-node tetrahedra recover constant strain within machine tolerance in a unit cube test.
- Analytical comparisons:
  - Cantilever beam (L=200 mm, E=210 GPa, b=h=10 mm) under end load: tip deflection error 0.6% with quadratic tets (5 elements through length); stress at fixed end within 1.4%.
  - Thick-walled cylinder (ri=10 mm, ro=30 mm, internal pressure 5 MPa): radial stress field matches Lamé solution with <0.8% L2 error.
  - Hertzian line contact (elastic half-space with rigid cylinder): peak contact pressure within 3.2% using augmented Lagrange and refined local mesh; contact patch width within 2.5%.
- Conclusion: Element formulations and contact enforcement produce accurate results for the governing physics.

5. Model setup and assumptions

5.1 Geometry fidelity
- Femur: Reverse-engineered from vendor CAD/CT of the composite medium-size femur; cortical shell thickness matches vendor spec nominal (3.0 mm proximally) with ±0.2 mm tolerance.
- Stem: Native CAD; fillet radii at the neck and lateral shoulder preserved; porous coating represented as a 0.8 mm layer with homogenized properties.
- Alignment: Insertion axis and seating depth set to match jig geometry; femoral anteversion fixed at 15°. A virtual gauge map (see Appendix A2) supports FE-to-experiment location matching by averaging over the 3.2 × 3.2 mm patch.

5.2 Boundary and loading
- Potting: Distal 70 mm of the femur constrained by tied contact to a rigid socket with all DOFs fixed; verified that reaction moments are consistent with lab fixtures.
- Loads:
  - Case A: 2300 N applied at head center through a rigid connector at the neck bore; resultant direction 10° adduction, 9° flexion.
  - Case B: 3000 N resultant plus 20 Nm about the neck axis.
- Contact and press-fit: Stem-to-bone interface with surface-to-surface contact (frictional), initial interference 50 μm (nominal). Contact detection via Gauss-point projection; no artificial damping used.

5.3 Material representations
- Stem: Ti-6Al-4V ELI, E=110 GPa, ν=0.34, density 4.43 g/cc; linear elastic.
- Porous coating: Homogenized isotropic layer, E=8.5 GPa, ν=0.3, based on independent coupon compression tests; calibrated as in Section 7.1.
- Composite femur:
  - Cortical region: transversely isotropic; E_longitudinal=17 GPa, E_transverse=11 GPa, G_LT=3.8 GPa, ν=0.33; fiber direction aligned to femoral axis.
  - Trabecular region: isotropic, E=0.55 GPa, ν=0.2.
- Rationale: Small-strain elastic response is appropriate for the load levels considered; no plasticity observed in bench tests.

5.4 Mesh and solution controls
- Elements: Predominantly 10-node tets (TET10) with selective continuum control; contact surfaces refined.
- Mesh statistics baseline: 
  - Stem/coating: 1.2 million DOF, characteristic edge length ~0.6 mm near fillets and coated surfaces; coarser (1.5 mm) distally.
  - Bone: 0.9 million DOF with 0.8 mm in cortex proximally; 1.5–2.0 mm trabecular.
- Convergence criteria: Force residual 1e-4, displacement change 1e-6 m; contact penetration target <2 μm at closure; maximum equilibrium iterations per substep 25; automatic substepping enabled.

6. Numerical accuracy evaluation (calculation-level)

6.1 Mesh refinement study
- Procedure: Three systematically refined meshes (h, h/√2, h/2) with similar growth controls. The output metrics assessed:
  - Peak stem stress at lateral shoulder (von Mises).
  - Max principal cortical strain at Gruen 7 patch.
  - Micromotion amplitude at the porous-coated band midpoint.
- Observations:
  - Monotonic approach to grid-independent values for all three metrics.
  - Estimated order-of-accuracy ~1.9–2.1 (consistent with quadratic tets and contact).
- Estimated remaining discretization effects (Richardson extrapolation, Case A):
  - Peak stem stress: 2.1% of extrapolated value.
  - Max cortical strain: 3.4%.
  - Micromotion: 5.6% (most sensitive to local contact discretization).
- We adopt the middle mesh (baseline) for parametric studies; corrections not applied but uncertainties propagated.

6.2 Solver robustness and residual checks
- Contact status monotonic after first two substeps; no chattering.
- Energy balance checked: External work minus internal strain energy equals reaction work within 0.5%.
- Reruns under reduced tolerances (stricter) changed outputs less than 0.3% — acceptable.

7. Parameters, pedigree, and estimation

7.1 Parameters with empirical tuning
- Porous coating modulus (8.5 GPa) was inferred by matching compression stiffness of coated coupons measured in a separate test (n=6). Calibration used only coupon data; no tuning against femur strains or micromotion to avoid circularity.
- Friction coefficient μ between coating and composite cortex:
  - Literature range 0.3–0.6 for porous Ti to polymer composite analogs.
  - A dedicated push-out test on coated plugs in composite shells (n=5) produced μ=0.42 ± 0.06 (mean ± SD). We set μ baseline=0.42; uncertainty propagated.

7.2 Inputs from standards and vendor data
- Ti-6Al-4V E, ν from ASTM F136 specs and internal QA coupons.
- Composite femur orthotropy from vendor data sheet; verified by ultrasonic C-scan on one sample (Appendix A3).
- Press-fit interference 50 μm from reamer size vs stem gauge; jig tolerance ±10 μm understood.

8. Sensitivity and uncertainty treatment

8.1 Sensitivity ranking (global and local)
- Parameters examined: μ (0.3–0.55), cortical E_longitudinal (14–20 GPa), trabecular E (0.3–0.8 GPa), coating modulus (6–10 GPa), load angle (±3°), seating depth (±0.5 mm), interference (30–70 μm).
- Method:
  - 200 Latin hypercube samples across the ranges above using a kriging surrogate trained on 60 high-fidelity FE runs; cross-validated RMSE <3% for QoIs.
  - Sobol indices computed on the surrogate.
- Results (Case A, primary metrics):
  - Max cortical strain: dominant drivers μ (S1=0.42), cortical E_longitudinal (S1=0.31); smaller effects from load angle (S1=0.12).
  - Peak stem stress: load angle (S1=0.36), seating depth (S1=0.22), cortical E (S1=0.18).
  - Micromotion: μ (S1=0.57), interference (S1=0.17).

8.2 Propagated variability
- Using the same surrogate, we propagated uncertainties:
  - Cortical strain 95% interval: ±9.1% around baseline.
  - Peak stem stress 95% interval: ±6.4%.
  - Micromotion 95% interval: ±14.3%.
- These bounds include mesh-induced variability via additive variance (Section 6) and include experimental comparator uncertainty in the model-to-test comparison (Section 9).

9. Comparison to bench measurements

9.1 Matching conditions and mapping
- Geometry: Virtual gauge areas in FE taken as the area-average over the 3.2 × 3.2 mm patch projected along the gauge orientation.
- Boundary conditions: Potting boundary and load vectors aligned to lab coordinate frames; a rigid link replicates the neck adaptor stiffness (100 kN/mm) — sensitivity showed negligible effect at this level.
- Cases A and B simulated as in Section 5.2.

9.2 Agreement metrics
- For cortical gauges (five locations used for scoring):
  - Case A (2300 N):
    - Mean absolute percentage difference (MAPD) across gauges: 6.8%.
    - Normalized root-mean-square error (NRMSE) relative to gauge peak magnitude: 8.9%.
    - All gauge sign/direction matched.
  - Case B (3000 N + 20 Nm):
    - MAPD: 9.7%.
    - NRMSE: 11.8%.
- Uncertainty handling:
  - Combined model uncertainty and measurement error computed via standard error propagation; the 95% prediction interval from the model enveloped 83% of observed gauge means across specimens.
- Stem shoulder rosette:
  - Qualitative only due to geometry differences; principal directions aligned within 7°, magnitudes within 12%.

9.3 Coverage and relevance
- The chosen loads represent the main design evaluation conditions (ISO-like mid-stance and a higher combined load). The validated regime spans 2.3–3.0 kN resultant forces and torque up to 20 Nm at the neck; extrapolations beyond this are flagged in reporting scripts.

10. Applicability and extrapolation boundaries

- Applicable devices: The evidence directly supports the assessed stem geometry family (sizes 5–7 scale similarly). Designs with collars or substantially different neck offsets are outside the current scope.
- Host anatomy: Composite femur only. Human cadaver variation is not represented in the current validation comparison.
- Activities/load cases: 
  - In-scope: ISO 7206-4-like positioning; static equivalents of mid-stance and stair-descent peaks.
  - Out-of-scope: Impact events, jogging (~4–5×BW), extreme torsion beyond 20 Nm, post-operative bone remodeling effects.
- Geometry tolerances: Seating depth shifts >1 mm or varus/valgus malalignment >5° degrade applicability unless re-checked.

11. Independent checks and human process controls

- Model development followed a written analysis plan (ADP-ORTHO-022, rev B).
- Peer review: A separate analyst reviewed the mesh, contact definitions, and load mapping; comments resolved in issue tracker (14 items, all closed).
- External SME review: A 2-hour session with a biomechanics consultant reviewed validation methodology and comparator appropriateness; no critical deficiencies identified.
- Traceability: All inputs, meshes, and scripts archived; model run manifests include software versions, solver options, and checksums.

12. Results summary relevant to decision-making

- Rank-ordering outcome (not the focus of this report): Variant B showed 6–9% lower proximal cortical strains and 3–4% lower shoulder stress than Variant A, with micromotion reduction of ~18% under Case B; Variant C exhibited a local stress raiser at the neck fillet due to a sharper blend and was deprioritized.
- Margins: Under the validated load envelope, predicted peak stem stress remains <280 MPa with 95% upper bound <300 MPa (Ti-6Al-4V yield >800 MPa) — adequate static margin. Strain levels in cortex remain below typical compressive yield for composite; measured values corroborate.
- Confidence: With numerical and comparator uncertainties accounted for, the model supports the intended narrowing of design space and test instrumentation planning.

13. Credibility discussion (vv40-aligned, plain language)

- Use clarity and decision linkage:
  - The question being answered (design screening under ISO-like loads) is clearly defined. The model’s outputs map directly to where gauges were installed, and the same load path is used. The degree of reliance is moderate, with experimental testing to follow.
- Solver correctness and numerical health:
  - Element behavior and contact enforcement were exercised on well-understood problems. Mesh sensitivity was quantified; remaining numerical effects are small relative to design differences and are explicitly included when comparing to data.
- Physics and modeling choices:
  - Elastic, small-strain assumptions are appropriate for the composite and metal at these load levels; contact nonlinearity is included, as is press-fit interference. The porous coating is treated via homogenization supported by coupons. These selections are justified by measurement and by the limited scope of use.
- Input pedigree and estimation:
  - Material properties draw from vendor sheets and standards; two key quantities (coating stiffness and friction) were tied to independent tests with documented uncertainty. Seating depth and load angle tolerances reflect fixture setup capabilities.
- Sensitivity and uncertainty:
  - Parameters that move the needle were identified and varied. A surrogate model enabled adequate exploration without overfitting, and uncertainty bounds on QoIs were produced and used in comparisons.
- Agreement with physical tests:
  - Under matching conditions, model-predicted strains are within ~10% on average; sign and trends match. The coverage of the comparison aligns with how the model will be used; extrapolation warnings are embedded in the post-processing.
- Applicability limits explicit:
  - The model is not asserted to cover patient-specific anatomy or extreme loading. Users are cautioned, and conditions for safe extrapolation are spelled out.
- Human and process factors:
  - Analysts used version-controlled scripts, followed a checklist, and documented solver settings. Independent review steps are recorded; computations are reproducible.

14. Limitations and open items

- Anatomy and biology:
  - The composite bone analog is not human bone; anisotropy and damping characteristics are different. Validation against cadaver specimens is planned for the next program phase if clinical-relevant predictions are needed.
- Long-term behavior:
  - No time-dependent phenomena (e.g., bone remodeling, interface osseointegration) are modeled. Micromotion predictions are short-term indicators only.
- Load envelope:
  - Activities with combined high torsion and high axial force exceed the demonstrated comparison window; use caution beyond 3.0 kN resultant and 20 Nm torsion.
- Geometric variance:
  - Only one size and neck option were exercised; other sizes are expected to scale but are not explicitly re-validated here.

15. Conclusions

- For the specific, bounded decision of design down-selection and test planning under ISO-like static loads, the FEA evidence base is adequate. Numerical errors are characterized and small; solver behavior is vetted; key inputs are tied to independent tests; and comparisons to a relevant benchtop setup show good agreement with quantified uncertainty.
- The model should not be used for patient-specific risk assessment, fatigue life predictions, or extreme activity analysis without additional evidence. A roadmap for broader applicability is outlined in Appendix A4.

16. Recommendations

- Proceed with Variant B and A to mechanical testing; instrument cortex at Gruen 7 and 1 and along the lateral shoulder with rosettes guided by the FE hotspot map.
- Maintain the current modeling workflow for regression against new design tweaks. If design scope expands (e.g., collared stems), plan a limited benchtop program to re-baseline interface behavior and rerun the comparison steps.
- For future phases targeting clinical-relevant questions, extend validation to cadaver femurs and include higher load cases; add fatigue crack initiation modeling once coupon-supported.

17. References

- ASTM F136, Standard Specification for Wrought Titanium-6Aluminum-4Vanadium ELI Alloy.
- Sawbones Model 3403 datasheet and orthotropic property appendix.
- ISO 7206-4:2010, Implants for surgery — Partial and total hip joint prostheses — Part 4: Determination of endurance properties of stemmed femoral components.
- Johnson KL, Contact Mechanics, Cambridge University Press.

Appendix mapping

- A1: Internal solver benchmark summaries and tolerances.
- A2: FE-to-gauge area mapping approach and registration screenshots.
- A3: Orthotropic property verification via ultrasound on composite femur coupon.
- A4: Evidence maturation plan for extended use-cases.
