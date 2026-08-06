# Structural Analysis Credibility Report: LTV Avionics Shelf Bracket FEA

Project: Artemis LTV Avionics Shelf Bracket  
Model: FEA-AVSHELF-23-04, Rev G  
Solver: Abaqus/Standard 2023 HF2 with in-house Python post-processing toolkit “LaminaTools” v1.8.4  
Date: 2026-07-22  
Prepared by: Structures & Dynamics Group, Exploration Systems Division

## 1. Background

The Lunar Terrain Vehicle (LTV) avionics shelf bracket secures two Honeywell HDC610 navigation units and a radiation-tolerant DC-DC converter to the primary equipment deck. The bracket experiences high-cycle vibration during ascent on SLS, quasi-steady loads during pressurized rover operations, and low-temperature thermal soaks during lunar night survival. This report evaluates the soundness of the finite-element model (FEM) used to support flight certification decisions for the bracket. The analysis addresses peak stresses for margin-of-safety calculations, expected fatigue life at fastener interfaces, first mode frequency separation from avionics excitations, and local deformation at connector plugs to ensure clearance.

The intended use is to inform the Preliminary Design Review (PDR) closure and to underpin parts selection and fastener sizing. The model will also be reused—with controlled updates—for the Critical Design Review (CDR) and for lot acceptance of as-built hardware, contingent on the controls described herein.

## 2. Purpose and Acceptable Use

- Decision supported: demonstrate positive margins against ultimate and yield criteria under mechanical load cases derived from the Integrated Loads Report LTV-ILR-25. Demonstrate first natural frequency greater than 150 Hz to avoid avionics self-excitation bands (40–120 Hz). Provide strain predictions at three strain-gauge locations for upcoming correlation tests.
- Permitted contexts: geometry within ±1.5% mass and center-of-gravity envelope; material lot properties within qualified ranges; load spectra consistent with ILR-25 Rev C or later; thermal range −120 C to +60 C.
- Explicitly excluded: crack propagation, micro-buckling in composite sub-elements (none present), detailed fretting at washer interfaces. Separate specialized models, if required, will be developed for those phenomena.

## 3. Model Description and Key Assumptions

- Geometry: The bracket is a machined 7075-T7351 aluminum L-shaped rib with radiused gussets and a top plate with lightening pockets. CAD source: AV-SHELF-ASM v9 in Windchill. Small features below 0.8 mm (chamfers, cosmetic fillets) replaced by sharp edges; bolt head details simplified to rigid washers.
- Elements: Solid elements (C3D10 quadratic tetrahedra) for ribs and gussets; hexahedral (C3D20) in plate patches where mesh mapping was feasible; connector elements for fasteners (CONN3D2) with calibrated axial and shear stiffness to match NAS620-8 performance; shell elements (S8R) for the thin avionics baseplate to capture local bending.
- Contacts: Surface-to-surface small-sliding contacts with friction coefficient μ = 0.2 at bracket-to-deck interfaces; bolt preload represented by temperature-dependence removed (converted to equivalent axial tension via pretension sections at 18 kN per bolt).
- Loads and boundary conditions:  
  - Quasi-static combined accelerations: ±11 g axial, ±7 g lateral, ±5 g vertical, applied as body forces to match ILR-25.  
  - Random vibration: PSD per ILR-25 Section 6, with 0.06 g^2/Hz at 80 Hz plateau, 2-minute duration per axis. Mode-based stress response with 2% modal damping baseline.  
  - Thermal: uniform −120 C and +60 C for differential expansion checks against deck constraint.  
  - Constraints: deck interface nodes fixed in all DOFs via multi-point constraints matching fastener layout; sensitivity on restraint stiffness performed and documented.
- Material models:  
  - 7075-T7351 aluminum: elastic-plastic with isotropic hardening; E = 71.7 GPa ±3%, ν = 0.33, σy0 = 480 MPa, ultimate = 540 MPa; Ramberg-Osgood fit based on MSFC coupons (lot MSFC-AL-7075-23B). Temperature dependence applied via Abaqus material table.  
  - Fasteners: linear elastic steel (A286), E = 200 GPa.  
  - Baseplate: 6061-T6 aluminum, linear elastic.
- Simplifications:  
  - Avionics units represented as lumped masses on the baseplate; connector stiffness approximated as 300 N/mm in each lateral direction (based on vendor finite element macro-model).  
  - Gasket compliance neglected; separate sensitivity run with a smeared 1 mm silicone layer shows <2% effect on global modes.

## 4. Provenance of Inputs

- Loads origin: ILR-25 Rev C, produced by the Loads & Dynamics IPT, tracing to ascent and rover operation environments; uncertainties ±10% on acceleration magnitudes acknowledged by IPT.  
- Materials: mechanical property database compiled from 19 room-temperature and 6 cold-soak coupon tests (−100 C) at MSFC Test Lab. Confidence intervals at 95% reported; outliers screened via ASTM E8 procedures.  
- Geometry: PDM-controlled CAD models; change history from v7 to v9 includes 0.5 mm relief under connector overhang and fillet radius increase from 2 mm to 3 mm at gusset toe. These modifications reanalyzed.  
- Fastener stiffness: derived from NAS620-8 manufacturer data and NASA-HDBK-5 material properties; cross-checked with a simplified bolt-column model.

All sources are checked into the project GitLab under repo fea-avshelf with immutable tags (tag revG_datafreeze_2026-06-29). Each file has a manifest entry with checksum.

## 5. Numerical Methods and Software Practices

- Solver: Abaqus/Standard with direct sparse solver for static and frequency extraction; modal superposition for response spectra. Requested precision: single run tolerances set to residual force < 0.5% of reference, displacement increment < 1e-6 m for final increment.  
- In-house scripts: LaminaTools v1.8.4 handles result extraction (peak von Mises, margin calculations, envelope PSD-to-RMS conversions). Python unit tests cover 93% of functions; CI via GitLab runners executes regression tests on all merge requests.  
- Software pedigree: Abaqus 2023 HF2 hash verified against Dassault baseline; the HPC cluster runs RHEL 8.8 with Intel OneAPI MKL 2023.2. Environment captured in job scripts archived with results.  
- Code verification: the group maintains a suite of 17 benchmark problems (NAFEMS LE10 thick-plate bending, NL2 large-deformation cantilever, CF1 contact patch, and three internal cases). For this update, we ran LE10 and CF1 using identical solver settings; stress and displacement errors were within 1.2% of published references. This guards against inadvertent changes due to updates/hotfixes.

## 6. Mesh Strategy and Discretization Checks

- Baseline mesh: ~1.25 million DOF, element edge sizes 0.5–2.5 mm; three elements across minimum thickness (3 mm) in the rib.  
- Local refinement: 0.5 mm tets around fillet radii and near fastener holes; mapped 20-node bricks in the flat plate span with 1 mm edges for modal accuracy.  
- Quality metrics: element aspect ratio < 4 for 95% of elements, Jacobian > 0.6 for all. Hourglass control not applicable (no reduced-order solids except S8R shells with default hourglass stabilization checked).  
- Convergence study: three levels (coarse, baseline, fine). Peak von Mises at gusset toe for combined-g load case: 213 MPa (coarse), 229 MPa (baseline), 233 MPa (fine). Richardson extrapolation gives asymptotic stress 236 MPa; Grid Convergence Index (95% confidence) on stress = 3.5%. The first natural frequency: 178.3 Hz (coarse), 175.4 Hz (baseline), 174.7 Hz (fine) — GCI = 0.6%. Baseline retained as it offers <4% estimated discretization error with tractable runtime (3.2 hours on 24 cores).

## 7. Solution Controls and Nonlinearities

- Contact robustness: penalty stiffness calibrated via a Hertzian contact patch test; penetration below 0.3% of local element size at peak load. Contact stabilizations disabled after initial ramp; no chattering observed.  
- Plasticity: small plastic zones predicted only in emergency off-nominal case (+20% load); in nominal load cases, max plastic strain < 0.1%, well within material’s elastic range.  
- Modal damping: 2% structural damping assumed; sensitivity runs at 1% and 3% bound the response; peak stress RMS varies by ±6%.

## 8. Experimental Correlation and Model Suitability

- Coupon-level: material curves match MSFC test data via Ramberg-Osgood fit (R^2 = 0.997).  
- Subcomponent test: a development bracket (Rev E) underwent sinusoidal sweep and static pull at JSC Bay 7 in May 2026. Strain gauges SG-1, SG-3, SG-5 placed at rib midspan, gusset toe, and near a bolt hole.  
  - Static pull at 10 g axial: measured strains at SG-1 = 720 με; model predicted 698 με (−3.1%); SG-3 = 940 με test vs 987 με model (+5.0%); SG-5 = 450 με test vs 471 με model (+4.7%).  
  - Modal: first mode measured at 176.1 Hz; model (Rev G) predicted 174.7 Hz (−0.8%). Mode shapes visually correlated; MAC values between test and model > 0.94 for first three modes.  
- Fixture fidelity: test used the same bolt pattern but with stiffer steel deck; we accounted for this by comparing a model with increased boundary stiffness; sensitivity shows <1.5% difference in first mode.  
- Outcome: residual discrepancies are within the uncertainty bands from materials and loads. No tuning factors were applied to match test data; only the boundary stiffness variant was explored to bracket the physical setup.

## 9. Sensitivity and Uncertainty

- Parameter scans:  
  - Material modulus ±3%: peak stress change ±2.7%; first mode ±1.5%.  
  - Fastener pretension 16–20 kN: stress at holes varies ±4.2%; interfacial slip negligible throughout.  
  - Coefficient of friction 0.15–0.25: local shear at interface varies ±7%; overall bracket stress < ±1.5%.  
  - Damping 1–3%: RMS stress for PSD case ±6%.  
- Combined uncertainty: Monte Carlo (200 samples) varying E, μ, preload, and load magnitudes (per ILR-25 uncertainties) yields a 95th percentile peak stress of 247 MPa for combined static case, versus the baseline 229 MPa. Mean first mode 175.1 Hz with 2.3 Hz standard deviation.  
- Margins considering variability: using A-basis allowable for 7075-T7351 (σy,A = 457 MPa) and 95th percentile stress 247 MPa, yield margin remains positive: MSy = (457/247)^2 − 1 = 0.72 for combined axial/lateral/vertical. For fatigue, Goodman-corrected alternating stress at the critical gusset toe is 61 MPa RMS; with S-N curve parameters from MIL-HDBK-5, life > 3e7 cycles at 50% reliability; factor of 10 usage margin against 3e6 mission cycles.

## 10. Boundaries of Applicability

- Geometry tweaks beyond the tolerance envelope (e.g., reducing gusset radius < 2.5 mm) can increase peak stress by >10% based on our design-of-experiments runs; any such change requires rerunning the model.  
- Temperature below −130 C not supported by current material tables; extrapolation is not allowed.  
- Loads outside ILR-25 frequency content (e.g., broadband excitation above 500 Hz) not evaluated; if introduced, the model must be extended with higher modal density and smaller time steps.

## 11. Track Record and Reuse

This modeling approach (solid elements for the bracket, connector elements for fasteners, penalty contact at interfaces) mirrors methods used on the VIPER avionics mounts (2019) and the Gateway PPE battery trays (2021). In both programs, correlation between measured and predicted first modes was within 2%, and strain at hot spots within 5–8%. The same LaminaTools pipeline generated margins for those efforts. Lessons learned (contact stiffness calibration and boundary compliance modeling) have been incorporated here.

## 12. Model Management, Traceability, and Change Control

- Configuration control: FEMs, scripts, and result sets are under GitLab with semantic versioning. Rev G branched from Rev F to incorporate fillet changes and updated ILR-25 load PSD. Merge requests require at least one reviewer not associated with the originating discipline (cross-IPT review).  
- Traceability: an index (TRACE-AVSHELF.xlsx) maps each requirement (frequency, margin, deflection limit) to model entities, load cases, and post-processing equations. Plots and tables in the report link to the exact job ID and solver log checksum.  
- Reproducibility: job submission scripts capture module versions, CPU model, thread count, and random seeds (for Monte Carlo). We have rerun the Rev G baseline on two clusters (Skylake and Ice Lake) and observed identical results within numeric noise (<0.1%).

## 13. Quality Safeguards and Independent Oversight

- Review process:  
  - Pre-briefs with Loads & Dynamics to confirm mapping from ILR-25 load cases into the FEM (body loads, directions, combination rules).  
  - Peer review by a separate senior analyst (not on the LTV IPT) covered: element selection, contact formulations, mesh quality, solver settings, and the reasonableness of the simplifications.  
  - External check: NESC liaison conducted a spot audit of mesh refinement and documentation completeness; action items (clarify friction coefficient basis, add fixture-stiffness sensitivity) are closed.
- Software QA: The scripts that compute margins have unit tests; we used frozen dependencies (numpy 1.24.4) with pip hash checking. Abaqus job files and message logs are archived.  
- Data protection: Windchill holds CAD masters; only exported mid-surface and cleaned solids are used downstream. FEM ETL steps are captured in a Jupyter notebook that is part of the repo.

## 14. Results Summary

- Static combined-g case:  
  - Max von Mises in gusset toe: 229 MPa baseline; with discretization-corrected estimate 236 MPa. Yield margin MSy = (σy/σmax)^2 − 1 = 3.4 at mean properties; using A-basis and 95th percentile stress, MSy = 0.72 (still positive).  
  - Deflection at connector plug location: 0.18 mm, below the 0.5 mm clearance threshold.  
- Random vibration:  
  - RMS stress at critical node 61 MPa; Von Mises maxima under 3-sigma envelope do not exceed 210 MPa.  
  - With damping ±1% variation, RMS changes ±6%, within acceptable range.  
- Modal: first three modes at 174.7 Hz (torsion), 204.3 Hz (bending about Y), 238.5 Hz (bending about X), all above the 150 Hz requirement. MAC vs test > 0.94.

## 15. Credibility Discussion by Topic

Note: the following are not formal scores; they are qualitative appraisals of the evidence supporting use of the model in the stated context.

- Physics and scope: The formulation captures the essential load paths (solid elements through gussets and ribs, realistic boundary stiffness via fasteners and deck), includes contact where slip could localize stress, and uses appropriate plasticity for off-nominal cases. Assumptions are documented and sensitivity to key approximations (friction, boundary stiffness) has been quantified.

- Input quality: Load definitions trace to a disciplined process with stated uncertainty; material curves are based on recent, program-specific testing, not legacy datasheets. Fastener parameters come from recognized sources and have been sanity-checked.

- Numerical verification: Alongside factory-level code correctness established by the vendor, we ran targeted benchmarks to detect setup- or environment-induced issues. The GCI on stress and frequency indicates the mesh is adequately resolved for the intended metrics.

- Agreement with reality: Subcomponent testing shows strain and modal predictions aligned within approximately 1–5%. No after-the-fact parameter tuning was required to “make the model fit,” which raises confidence in forward prediction.

- Variability characterization: Single-parameter and combined Monte Carlo studies quantify how uncertainties in loads and properties propagate to stress and frequency. The resulting probability distributions are used to claim margins with stated confidence.

- Robustness of conclusions: Model predictions are insensitive to small perturbations in damping, friction, and preload; qualitative behavior (location of hot spots, mode shapes) does not change across the examined range.

- Workflow reliability: Automation scripts are tested and versioned; solver and environment are documented; results can be reproduced deterministically on different hardware with the same software stack.

- Execution oversight: Multiple rounds of review, including an out-of-team look, and closure of resulting action items, were completed. This adds independence and reduces the chance of analyst bias.

- Documentation: Inputs, outputs, and post-processing equations are traceable; all plots and numbers can be tracked back to a model and run ID.

- Analyst proficiency: Primary authors have 8–15 years of experience with similar hardware on VIPER and PPE; both have completed the 24-hour Abaqus advanced training and internal modeling standards course.

- Past use and maturity: The same approach has a track record on two NASA programs with good test correlation. This provides a baseline for expected performance on the current bracket.

- Operational constraints: We provided clear guardrails on when the model can be applied and when it cannot (temperatures, geometry bounds, load spectra). These constraints are essential for responsible reuse.

## 16. Limitations and Open Items

- Thermal gradients through thickness are not modeled; thermal cases assume uniform temperature. If avionics self-heating introduces significant gradients, an updated model with thermo-mechanical coupling should be created.

- Fretting and micro-slip at the interface under vibration are represented by a Coulomb model with a single friction coefficient. If wear or fretting fatigue becomes a primary life driver, a separate detailed contact model with cyclic slip tracking is needed.

- Manufacturing deviations (e.g., surface finish at gusset toe) are not directly parameterized. As-built metrology should be checked against sensitivity ranges; if deviations exceed analyzed bounds, rerun is required.

- High-frequency content above 500 Hz is not covered in the modal density of the current model; any new environments in this band will require additional modes or direct transient analysis.

- The fatigue assessment uses standard S-N curves adjusted for surface finish and mean stress; it does not include notch plasticity at micro-scale. For mission expansion scenarios with >3e7 cycles, a local strain approach should be considered.

## 17. Recommendations

- Accept the Rev G model for PDR closure and for use in release notes for part manufacturing, with the caveats on geometry and environment stated above.

- Proceed with the dedicated correlation test planned for September 2026 on the Rev G build (updated fillets). Use the same gauge locations; update the validation section with direct comparisons.

- Maintain the automated nightly regression that re-runs a reduced set of cases to detect environment or dependency drifts.

- Before CDR, expand the uncertainty campaign to include variability in bolt torque to clamp load mapping (based on torque-tension tests) and evaluate a slightly larger friction range reflecting possible contamination.

## 18. References and Artifacts

- ILR-25 Rev C, Integrated Loads Report, LTV Loads & Dynamics IPT, 2026-05-11.  
- MSFC-AL-7075-23B, Mechanical Properties 7075-T7351 Coupon Test, MSFC Materials Lab, 2026-03-08.  
- NAFEMS Benchmark Manual, Volume LE10 and NL2 cases, 2015 Edition.  
- Repo fea-avshelf, tag revG_datafreeze_2026-06-29, GitLab internal server.  
- JSC Subcomponent Test Report TR-AVSHELF-RevE-2026-05, JSC Bay 7.

## 19. Appendices (summarized)

- Mesh convergence plots and extrapolation math.  
- Sensitivity tornado charts for E, μ, preload, damping.  
- Checklist used in the independent review (mesh, BCs, contacts, materials).

---

## 20. Credibility Snapshot

- Intended application clearly stated, with limitations.  
- Inputs have traceable origin and quantified uncertainty.  
- Numerical procedures vetted via benchmarks and mesh checks.  
- Test comparison supports the model’s predictive ability without retrofitting parameters.  
- Uncertainty quantification performed; decisions grounded in distributions, not single-point values.  
- Governance in place: version control, reproducibility, and independent review.

This body of evidence supports using the FEA results to make design and acceptance decisions for the LTV avionics shelf bracket within the specified bounds. Any substantial changes in geometry, environments, or materials should trigger re-validation following the same workflow.
