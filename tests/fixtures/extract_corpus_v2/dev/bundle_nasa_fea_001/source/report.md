Title: Credibility Evaluation Report — FEA of Lander Descent Strut Assembly (Model ID: STRUT-FEA-2024R1)

Prepared by: Structures & Loads Group, Exploration Systems
Date: 2026-08-05

1. Background and Purpose
The Descent Strut Assembly supports quasi-static touchdown loads, ground handling, and ascent-offload for the Peregrine-class lunar lander. This report examines whether the finite-element model STRUT-FEA-2024R1 is fit to inform design sizing, margins reporting, and compliance statements for static and low-frequency dynamic environments. The model is implemented in Ansys Mechanical 2024 R1 and managed via the team’s controlled repository (git tag v1.7.3, run manifest STRUT-PRJ/manifest-2024-07-18.yaml).

Context of use
- Decisions supported: component thicknesses, fillet radii, bolt pattern confirmation, and margin-to-yield reporting for CDR.
- Environments covered: static loading envelopes (landing, tipping, umbilical), low-frequency modes (0–300 Hz), and global/local buckling.
- Explicitly excluded: high-frequency shock, vibroacoustics above 500 Hz, and thermal cycling crack initiation. Those will be addressed by separate models.

2. Model Formulation and Idealizations
Geometry and scope
- The strut is a tapered titanium Ti-6Al-4V forging with an integral clevis at the lander interface and a spherical bearing at the footpad end. The model includes the strut body, end fittings, bearing housing, and fastener representations at the clevis (12 M10 bolts). Threads are not resolved; bolts use pretension elements with rigid shanks and CFAST-based head–nut compliance.
- Fillets at the clevis reliefs and midspan tapers are modeled. EDM corner breaks below 0.5 mm are ignored on the global mesh and reintroduced in a local submodel for peak stress estimation.

Physics and constitutive choices
- Linear elastic with temperature-dependent properties for titanium; at 110 K (worst-case landing), E = 122 ± 2 GPa, ν = 0.34, yield = 1,020 ± 30 MPa (coupon data PRJ-MAT-110K-2025, see Appendix).
- Bearing liner modeled with orthotropic elastic properties derived from vendor datasheet LOT-APR25 and coupon compression tests.
- Contacts between clevis/plate and bolt heads/nuts are frictional (μ = 0.12 ± 0.03); bearing-to-housing is bonded (press fit). Contact enforcement uses Augmented Lagrange with normal stiffness auto-calibrated per Ansys default, verified stable through sensitivity sweeps.
- Large-deflection kinematics enabled for buckling and modal pre-stress runs. Damping for modal correlation uses 1.2% structural damping fitted from impact test results.

Boundary conditions and loads
- Landing load cases per ENV-LND-001 Rev D include vertical compression, side load, and a 15° off-axis resultant. Equivalent nodal loads are applied through rigid bodies to simulate load introduction via the lander frame and footpad. Bolt pretension targets are 22 ± 2 kN per fastener. Thermal preload at 110 K is induced via temperature field with CTE mismatch.
- Eight deterministic load cases were examined; combinations per quadratic sum and worst-pair envelopes align with the loads manual.

3. Software, Platform, and Reproducibility
- Solver and environment: Ansys Mechanical 2024 R1 on RHEL 8.8, Intel oneAPI MKL, double precision. Jobs executed on HPC cluster “Sagan” (2×24-core Xeon Gold 6438 per node). CPU affinity and Ansys job settings (sparse solver, pivot check = program controlled) recorded in run manifests.
- Container image sha256:ba9c… holds the pre/post-processing scripts, ensuring OS/library consistency. Material cards and connector definitions are under config control (repo directory configs/).
- All runs stored under STRUT-FEA-2024R1/runs/* with UUIDs; postprocessing notebooks (Jupyter) are included with frozen dependency versions. A fresh “clone and run” trial by an independent analyst reproduced key results within numerical noise on a different node.

4. Numerical Discretization and Solver Controls
- Element types: SOLID187 (quadratic tetra) for the strut and clevis plates; SOLID186 hexa for the submodel hotspot regions; CONTA174/TARGE170 for contact; PRETS179 for bolt preload.
- Mesh density: 3.0 mm nominal in high-gradient zones (fillets, bearing seat), 12 mm in low-interest regions. Final global mesh count: 2.1M DOFs. Local submodel: 1.3M DOFs with 1.0–1.5 mm hex elements near the clevis root.
- Solver settings: non-linear solution with line search on, auto time stepping, min substep 1e-3, convergence targets: force residual 0.5%, displacement 0.5%, and contact penetration < 0.5% of element size. For eigen-extraction, Block Lanczos with 30 modes requested.

5. Evidence from Numerical Checks (code and solution)
- Vendor pedigree: Ansys SQA statements (QTP-2024R1) cover SOLID187 patch tests and contact verification. We reviewed the QA summary and matched issue list to our usage; no open defects affected our features.
- Internal sanity tests: 
  - Constant-strain patch: a linear load on a prismatic bar returned exactly uniform strain within 0.2% (quadratic tet).
  - Classical plate-with-a-hole benchmark (Kt = 3.0): submodel with mapped hex elements yielded Kt = 2.98 at the notch for ν = 0.3, in line with theory; tet-only mesh showed 2.94 at coarse level and 2.99 after refinement, establishing expected convergence trend.
  - Single-bolt joint micro-model: pretension plus shear matched closed-form head/nut compliance within 3.1%.
- Mesh refinement study on the full assembly for the worst case (LC-7: 15° resultant, cool-down): four meshes (1.1M, 1.6M, 2.1M, 2.9M DOFs). Max von Mises in the clevis root converged monotonically; Richardson extrapolation gave 1.8% estimated discretization error at 2.1M DOFs. Energy norm error indicator reported 1.5% between last two levels. Local submodel refinement cut the stress gradient error to below 1.2% based on strain energy change.
- Nonlinear/contact robustness: contact status histories are stable; no chattering. Sensitivity to contact stiffness ±50% changed max stress < 1.9% and did not alter load paths materially.

6. Comparison to Physical Test Data
- Hardware: An engineering development unit (EDU) strut was loaded at Marshall (STRUT-EDU-TEST-01, May 2026). Test matrix included 1.0× and 1.2× design vertical/side loads and combined resultant; 22 strain gauges (gage factor calibration ±0.2%) and DIC for displacement fields. A separate impact hammer test (roving accelerometer) measured first five modes with 0.6–1.4% modal damping.
- Correlation metrics:
  - Strains: RMS error across gauges at 1.0× loads is 4.9%; max absolute deviation is 12.4% at the inner clevis gauge G14 (predicted compression higher than measured). At 1.2× loads, RMS increases to 6.1%. Updated contact friction to μ = 0.10 for the test (as-measured slip evidence) reduces G14 discrepancy to 9.7%.
  - Displacements: DIC midspan deflection under combined load: test 1.84 mm; model 1.78 mm (−3.3%). Clevis opening measured 82 μm; model 87 μm (+6.1%).
  - Modal: first bending 126 Hz (test) vs 123 Hz (model), −2.4%. Second bending 207 Hz vs 201 Hz, −2.9%. Mode shapes match with MAC > 0.93 for first four modes.
- Domain of similarity: load magnitudes, directionality, temperature soak (110 K in a thermal chamber) mirror the intended operational envelope. Gauge coverage includes both tension and compression fibers near high-gradient zones.

7. Data Sources and Their Trustworthiness
- Materials: Titanium property curves from project-specific coupons (lot STRUT-TI-FORGE-APR26), tested at 293 K and 110 K per ASTM E8/E111. Measurement uncertainties: E ±2 GPa, yield ±30 MPa, ultimate ±45 MPa. Liner properties from vendor with in-house compression verification (±6%).
- Fastener data: M10 Class 12.9 bolts; torque-preload correlation from torque wrench calibration and nut factor K = 0.18 ± 0.02, leading to pretension of 22 ± 2 kN at 25 N·m nominal.
- Geometry: CMM measurements on the EDU confirm thicknesses within +0.08/−0.03 mm of nominal and fillet radii within ±0.15 mm. Those tolerances informed the uncertainty analysis.
- Environmental inputs: Temperature field bounded by 110 ± 10 K from thermal analysis handoff (TH-ENV-2026-07). Gravity vector uncertainty negligible for static cases.

8. Uncertainty and Sensitivity Characterization
- Treated sources: E, yield, thickness at clevis fillet, bolt pretension scatter, friction coefficient, liner stiffness, and temperature. We separated measurement scatter (aleatory) from lack of knowledge (epistemic) where applicable; epistemic ranges are conservative envelopes of available data.
- Propagation: 200-run Latin Hypercube sampling. Each sample updates geometry (fillet radius/thickness), material cards, contact properties, and pretension to evaluate peak von Mises stress in the clevis root and global first mode frequency.
- Results:
  - Peak von Mises stress at worst case LC-7: mean 577 MPa, 95th percentile 612 MPa. Allowable at 110 K with 1.25 factor on yield: 816 MPa. Reliability index β ≈ 3.2 for yield exceedance by FORM approximation, consistent with Monte Carlo zero failures out to 95th percentile.
  - First mode: mean 121.6 Hz; 5th percentile 118.7 Hz, above the 90 Hz requirement with significant margin.
- Drivers: Sobol first-order indices for peak stress: clevis thickness (0.41), bolt pretension (0.23), friction (0.17), E (0.11), temperature (0.05), others negligible. For frequency: E (0.38) and clevis thickness (0.29) dominate.

9. Applicability, Limits, and Assumptions
- Simplifications: Threads idealized; surface roughness not modeled; micro-yield in bolt heads not included explicitly (covered via allowable definitions). Adhesive wicking not present in this assembly. Bearing liner nonlinear compression neglected; validated linear range shown adequate up to 1.2× loads.
- Range of validity: Verified from 0.8× to 1.2× design loads at 110 K; use at higher loads is extrapolation. For temperatures below 90 K or above 300 K, material models have no test backing. Contact friction is assumed within 0.07–0.15; operations using non-standard lubricants could violate this.
- Out-of-scope: Shock (pyro), random vibe above 500 Hz, and very low cycle fatigue. A different model set will address those phenomena.

10. Prior Experience and External Benchmarks
- The same modeling approach (bolt connector treatment, contact enforcement choices, submodeling of hotspots) was applied to the CLPS Navigation Mast Bracket (2024), where static strain correlation RMS was 5.6% and modal frequency errors <3%. A Nastran SOL 106 cross-check for that program agreed within 2–4% on deflections and margins.
- For this strut, a cross-tool check with MSC Nastran SOL 600 on LC-1 produced midspan deflection 1.81 mm vs 1.78 mm in Ansys (−1.7%) and peak von Mises 562 MPa vs 571 MPa (+1.6%), indicating tool independence.

11. Configuration Management and Traceability
- All model artifacts (geometry, mesh scripts, material cards, solver settings, load definitions) are tracked via Git; every analysis run has a manifest capturing input hashes, job options, random seeds for sampling, and environment fingerprint. The EDU test dataset includes raw and processed forms with calibration files attached and DOIs minted internally.
- Change control: proposed edits open pull requests with reviewer assignment; merges require at least one independent reviewer approval.

12. Analyst Qualifications and Reviews
- Primary analyst: J. Alvarez, PhD (NAFEMS Professional Simulation Engineer—Structures), 12 years experience, Ansys Certified Professional.
- Peer reviewer: L. Kim, MSME, 15 years, NASA MAPDG contributor, certified in Nastran non-linear analysis.
- Independent check: D. Ren (Loads & Dynamics), reproduced LC-3 and LC-7 results on separate hardware; differences <0.5% for displacements and <1.2% for peak stresses.
- Training logs for contact modeling and submodeling (Ansys 2024) are current. A formal review meeting was held 2026-07-22 with action items closed by 2026-07-30.

13. Reasonableness Checks and Physical Insight
- Load path visualizations show compressive axial flow along the strut with secondary bending from the off-axis resultant, consistent with free-body assessments. Bolt load distribution is near-linear across the row with edge bolts carrying 10% higher load—aligned with CFAST predictions.
- Simple beam equations for a tapered member under combined load predict 1.9–2.0 mm tip deflection; FEA predicts 1.78–1.84 mm across load factors—consistent after accounting for 3D stiffness from the clevis geometry.

14. Credibility Summary by Evidence Theme
- Problem definition and acceptance criteria are explicit in ENV-LND-001 Rev D and STRUT-REQ-2026; criteria flowed down to analysis checks (Section 16).
- Mathematical/numerical aspects are supported by patch tests, mesh refinement, and cross-solver comparison. No indications of coding or setup errors remain after review actions.
- Physical modeling is supported by test-to-analysis correlation across strains, displacements, and modes, within 3–6% typical discrepancies, worst outlier ~10–12% at a single gauge with an understood cause.
- Input quality is backed by project-specific coupons, calibrated pretension, and measured geometry; uncertainties are quantified and propagated to outputs relevant to decisions.
- Process control, reproducibility, and user competence are documented; independent replication succeeded.

15. Limitations and Open Issues
- The model has not been exercised against shock or high-frequency acoustics; do not apply it to pyroshock sizing or random vibe. Different solvers and material/damping models will govern that domain.
- Yielding in bolt threads is idealized via allowable; for assessments approaching ultimate strength or combined thermal–mechanical cycling, a micro-model should be employed.
- Friction can drift with lubrication and cleanliness; if μ < 0.07 is expected, the joint may slip earlier than modeled. This is tracked as risk R-STRUT-007; mitigated by torque verification and witness marks.
- Only one EDU was tested; lot-to-lot material variability beyond sampled uncertainty could widen spreads. Additional coupons are planned in FY27.

16. Results Against Decision Criteria
- Static strength: At 1.0× design loads and 110 K, peak von Mises in the clevis root is 571 MPa nominal (95th percentile 612 MPa); allowable is 816 MPa. Margin to yield > 0.34 at 95th percentile.
- Local exceedance allowance: regions above 0.95× yield occupy <0.3% of volume in submodel; requirement allows up to 2% in secondary regions—passes.
- Global and local buckling: Linear eigenvalue analysis yields the first buckling factor 2.1. Nonlinear Riks with an initial imperfection equal to 0.2% of thickness gives collapse at 1.68× design load—exceeding the 1.5× requirement.
- Low-frequency dynamics: First bending mode 121.6 Hz mean (5th percentile 118.7 Hz) vs >90 Hz requirement—passes with margin. Correlation to test is within −2.9%.
- Robustness: No solver failures across eight load cases and 200 UQ samples; contact penetration and residuals meet targets.

17. Management, Planning, and Governance
- The modeling and assessment activities followed plan M&S-PLN-112 Rev B, with defined roles, schedule, and review gates (Pretest Prediction, Posttest Correlation, Final Disposition). Risk items (friction variability, liner ortho-properties) were tracked in the project risk register, with mitigations executed (coupon tests, torque calibration). All planned activities for CDR scope are complete.

18. Independent Oversight
- The Structures Technical Authority reviewed this work on 2026-08-01. The review package included run manifests, correlation plots, and UQ results. The TA requested an additional mesh check on the submodel and a contact stiffness sweep; both were performed with negligible impact on conclusions.

19. Decision
Based on the assembled evidence, the Structures & Loads Group and the Structures Technical Authority jointly decide:

The model STRUT-FEA-2024R1 is accepted for design sizing, margins reporting, and compliance statements for static load cases, low-frequency modal characteristics up to 300 Hz, and global/local buckling in the Peregrine-class lander strut context, subject to the limitations listed in Section 15. It is not approved for pyroshock or high-frequency acoustic environments.

Decision owners: Chief Engineer, Descent Stage (A. Patel) and Structures Technical Authority (M. Ortega), recorded in decision log DEC-STRUT-2026-08.

20. References
- ENV-LND-001 Rev D: Landing Load Envelopes.
- STRUT-REQ-2026: Strut Requirements.
- M&S-PLN-112 Rev B: Modeling and Simulation Plan.
- PRJ-MAT-110K-2025: Titanium Coupon Test Report.
- STRUT-EDU-TEST-01: EDU Static and Modal Test Report.
- QTP-2024R1: Ansys SQA Summary for 2024 R1.
- CFAST-JOINT-2019: Bolt/Joint Compliance Handbook.

Appendix
See appendix.md for load case definitions, mesh convergence plots, and UQ input ranges.
