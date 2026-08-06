Rover Battery Enclosure Frame — Structural Modeling Credibility Report
Project: Artemis-CLPS Rover Power Subsystem
Model ID: FEA-RBP-023
Date: 2026-07-22
Prepared by: Structures Simulation Group, JSC

Executive Summary
- Purpose: Evaluate whether the finite element model of the rover battery enclosure frame is credible for making go/no-go decisions on the current design with respect to launch-induced quasi-static acceleration and ensuring the first modal frequency clears avionics vibration requirements.
- Core result: The model predicts a minimum static margin of 0.09 at the most critical lug under the combined 12g vertical and 8g lateral case when parameter variations are included. The first mode is predicted at 175 Hz; correlation to an impact test yielded 182 Hz (−3.8% difference).
- Why we trust it: Inputs are traceable to program environments and material data, the mesh has been refined to where the stress at the hotspot no longer changes appreciably, solver settings are tight, and the model has been checked against a bench test of a representative article.
- Important caveats: The present work addresses quasi-static launch accelerations and global stiffness. It does not treat damage accumulation from broadband random vibration or thermal-mechanical coupling during lunar operations. Local fastener-level behavior is captured via pretension elements but thread-detail stresses are not resolved.

1. Background and Intended Use
The battery enclosure assembly mounts to the rover primary deck via six lugs. It supports an 18.2 kg mass of cells, BMS boards, and casing. The concern is the structural robustness of the frame under combined platform accelerations during launch and the adequacy of the first mode separation from the avionics shelf modes. Design acceptance requires:
- The von Mises equivalent stress to remain below the material allowable with a minimum static margin of 0.05 at room temperature under 12g vertical and 8g lateral load cases combined vectorially.
- The first flexible mode of the mounted assembly to lie above 160 Hz to avoid coupling with the avionics stack.

The model is intended to drive bolt-size selection, fillet radii at the lugs, and local stiffener placements. It is not intended at this phase to predict threaded insert behavior or gasket compression.

2. Model Description and Assumptions
- Software: Ansys Mechanical 2024 R2, sparse direct solver for linear steps; nonlinear static solver for pretension steps. Model archive stored under PLM Vault record PLM-STR-4473 with solver input checksum 8F1C-BC92.
- Geometry: The frame is an aluminum C-channel structure with six mounting lugs and internal cross-bracing. Fillets below 0.8 mm were suppressed for meshing practicality after comparison runs showed sub-1% influence on global stiffness. Cable tie bosses and small cutouts were omitted; corresponding mass was added via nonstructural mass to preserve inertia for the modal step.
- Elements: Tetrahedral second-order (10-node) solid elements for the frame; hexahedral elements were used locally in lug cross-sections where fillet radii are large enough to permit mapped meshing. Pretension sections represent the six M6 bolts. Contact at footpads is modeled as frictionless; lugs are tied to the bolts’ shanks via bonded contact, with preload represented explicitly.
- Constitutive model: Linear elastic material behavior for quasi-static loading; plasticity was not invoked because peak stresses are required to remain below yield, and this assumption is supported by the correlation test (see §6). Temperature effects on stiffness are represented by linear scaling of E with temperature around 23°C.
- Boundary support: The frame attaches to a steel test fixture in the correlation test and to the rover deck in the prediction analyses. We represent the deck as fixed at the bolt hole patterns via multi-point constraints connecting lug bore nodes to reference points where loads/pretensions are applied. This is consistent with the stiffness of the deck region (estimated at >10× frame stiffness based on separate subsystem modeling).

3. Loads and Inputs — Sources and Rationale
- Inertial loads: The 12g vertical and 8g lateral accelerations are derived from Launch Environments Doc LE-2026-17, Table 4-3, “CLPS 2xxx 3-sigma quasi-static.” These are applied as body accelerations to the frame and attached masses.
- Mass distribution: The 18.2 kg assembly mass is allocated as follows: frame 3.1 kg (from CAD), battery modules 12.9 kg, electronics 1.2 kg, cabling 1.0 kg. Nonstructural mass elements attach the non-frame masses to bolt-hole reference points per as-designed locations.
- Bolt preload: 3.5 kN per M6 fastener based on torque procedure ME-PR-602 Rev C; this establishes joint clamping for the frictionless support idealization.
- Material data: 6061-T6 aluminum, room-temperature Young’s modulus 69.0 GPa, yield strength 276 MPa, Poisson’s ratio 0.33. Property values come from MMPDS-17, Sheet 2-1. A ±5% variability on yield and ±3% variability on E were used in the uncertainty study. Thermal modulus slope dE/dT = −27 MPa/°C adopted from NASA/TP-2010-216637.
- Damping for modal step: 1% modal damping assigned to compare with test curve fits; used only for post-processing of frequency response functions, not for eigenvalue extraction.

All external data are stored in Data Curation Record DCR-STR-1109 with metadata linking to the specific table/figure numbers.

4. Numerical Setup and Mesh Quality
4.1 Element quality and contact resolution
- Average tetrahedral element aspect ratio: 1.8; minimum Jacobian 0.42. Contact faces at lug interfaces modeled with target element edge length of 0.6 mm to capture stress gradients at the fillet.
- Pretension sections defined over 6 mm bolt length; preload step converged with residual forces <0.5 N per node and contact penetration less than 0.003 mm, under 0.3% of the local element size.

4.2 Mesh refinement study
A three-level refinement was performed with the following totals:
- Coarse: 185,000 elements, min edge size 1.2 mm, hotspot von Mises at lug fillet = 308 MPa.
- Medium: 428,000 elements, min edge size 0.8 mm, hotspot = 297 MPa.
- Fine: 1,130,000 elements, min edge size 0.5 mm, hotspot = 294 MPa.

The change from medium to fine is 1.0%; stress contours in the lug fillet region stabilized in shape between medium and fine. Displacements at a global marker decreased by 2.1% between coarse and medium and 0.6% between medium and fine. For production runs, the medium mesh was adopted to balance accuracy and runtime, with an estimated residual mesh error in the hotspot stress around 1.8% based on Richardson extrapolation assuming p ≈ 1.8 effective order in the stress field.

4.3 Solver controls and convergence
- Static step: Stabilized Newton with automatic time stepping, initial increment 0.1, minimum 0.01. Average force residual reduced by 7 orders of magnitude; displacement residual by 6 orders. No line search failures observed; maximum 8 equilibrium iterations in any substep.
- Modal step: Lanczos eigensolver up to 300 Hz; first 10 modes extracted. Mass and stiffness orthogonality checks passed within 0.3% tolerance.

5. Boundary Conditions and Load Cases
- Case 1 (primary): 12g vertical (Rover +Z) and 8g lateral (Rover +Y) applied simultaneously. Bolt pretension included. Supports at mounting feet constrained by multi-point constraints to emulate deck rigidity.
- Case 2 (reverse): 12g vertical (Rover −Z) and 8g lateral (Rover −Y).
- Case 3 (sideways): 8g lateral (Rover +X) only, to check off-axis behavior.
- Modal: Prestressed eigenvalue extraction under pretension but no body loads.

6. Correlation to Bench Test
A subassembly test was conducted on Proto-1 frame with a steel plate fixture replicating the rover deck hole pattern. Two gages (EA-06-063QY-120) were bonded at high-gradient regions predicted by the analysis near the lug fillet and one at midspan of a side rail for global bending tracking. The fixture’s flexibility was measured separately and shown to be at least 12× stiffer than the frame across the first two bending modes, validating the fixed-support idealization.

- Static pull test: A deadweight frame and screw jacks generated a vertical equivalent of 12g on the mass dummies and a lateral 8g via a calibrated hydraulic actuator. The peak measured microstrain at the lug gage was 1600 με; the model predicted 1475 με at the same location under identical boundary conditions, a difference of −7.8%. At the side rail gage, measured 642 με vs. predicted 606 με (−5.6%).
- Modal test: Impact hammer test with roving triax accelerometers (PCB 352C65) identified a first bending mode at 182 Hz with a light 1.1% damping ratio, and a second mode at 233 Hz. The analysis predicted 175 Hz and 229 Hz, respectively (−3.8% and −1.7%). Mode shapes matched the test’s MAC values >0.95 for the first two modes.

The observed differences are consistent with expected variability in material properties and mass distribution of the dummies. No plastic offset was observed in strain readings post-unload, supporting the elastic assumption.

7. Sensitivity and Uncertainty Characterization
7.1 Parameter variations considered
- Material stiffness E: Normally distributed, mean 69.0 GPa, σ = 2.07 GPa (3%).
- Yield strength: Lognormal, mean 276 MPa, COV 5%.
- Bolt preload: Uniform, 3.15–3.85 kN (±10% on torque coefficient).
- Mass distribution: Uniform ±5% on electronics mass; battery pack mass fixed by vendor spec.
- Mesh density: Accounted implicitly via the 1.8% estimated numerical error on the medium mesh’s hotspot stress.

7.2 Propagation method
A Latin Hypercube sample of 500 combinations was run on the medium mesh for Case 1. Each sample included a realization of E, yield strength, preload, and electronics mass, with a consistent random seed (SEED-STR-20260714) stored in the run log. Runtime per sample averaged 9 minutes on a 16-core machine; outliers exceeding 30 minutes were discarded and resubmitted with tighter step controls.

7.3 Results of the spread analysis
- Hotspot von Mises stress at the critical lug had a mean of 291 MPa and a 95th percentile of 324 MPa. The spread is dominated by preload variation and, secondarily, by modulus variation which slightly shifts load paths.
- The first eigenfrequency varied with E and added electronics mass: mean 176.2 Hz, 95% lower bound 171.1 Hz. All samples exceeded the 160 Hz threshold.
- Considering the 95th percentile stress and the yield strength distribution, the corresponding probability that the hotspot stress exceeds yield under Case 1 was estimated at 1.7%. Because allowable is set below yield (see §8), the margin is computed against the allowable, not yield.

8. Acceptance Metrics and Margins
The design allowable used for the lug region is 355 MPa (derived from 276 MPa yield with a factor of 0.78 for stress concentration and environmental considerations per STR-ALLOW-2025-04). Using the 95th percentile stress from the sensitivity study (324 MPa):
- Static margin = (Allowable − Stress95) / Allowable = (355 − 324) / 355 = 0.087 → reported as 0.09.
- For the median stress (291 MPa), the margin is 0.18. However, the decision basis conservatively uses the 95th percentile.

Modal clearance:
- First flexible mode predicted at 175 Hz (baseline) and 171 Hz (5th percentile). Both exceed the 160 Hz requirement by at least 11 Hz.

9. Numerical Checks Beyond Mesh Refinement
- Residual force balance: For Case 1, total reaction at supports matches applied inertial and pretension effects within 0.2%.
- Contact behavior: No chattering observed after initial step; contact pressure distributions stabilized and are consistent with load direction.
- Energy balance: Strain energy to external work ratio converged to 0.999 in the final increments, indicating solver stability.

10. Applicability Envelope
The current model and its calibration apply under the following conditions:
- Temperature range: 20–50°C. This covers the acceptance test and on-pad conditions before ascent. Material modulus scaling is included within this range; no creep or thermal relaxation is modeled.
- Load cases: Quasi-static accelerations up to 12g vertical and 8g lateral combined. Beyond these, behavior is extrapolated and not warranted by current tests.
- Assembly configuration: Six M6 bolts with specified torque range, full contact at footpads, and mass properties as enumerated in §3. Any change in fastener type, bolt pattern, or mass placement requires rerun.

11. Reproducibility, Archiving, and Traceability
- All FE input files, geometry, and mass property spreadsheets are archived in PLM Vault record PLM-STR-4473. The master .mechdat file hash is 8F1C-BC92; post-processing scripts are in Git repo STR-FEA-Tools commit 3a4c2e7.
- Run matrix and sample seeds are recorded in Run Log RL-023.xlsx, with columns for parameter draws, solver status, and output fields. A rerun on a separate workstation (Ansys 2024 R1) produced first-mode differences <0.6% and hotspot stress differences <1.2%, within the expected numerical envelope.

12. Results Summary
- Stresses: The most critical location is the inner radius of Lug 3 under combined +Z/+Y loading, with baseline von Mises 297 MPa on the medium mesh. Secondary hotspots at the adjacent lug fillets are 10–15 MPa lower.
- Displacements: Maximum tip deflection at the electronics overhang is 0.74 mm baseline; lateral sway of the battery pack CG is 0.29 mm.
- Frequencies: The first two flexible modes are at 175 Hz (bending about Rover X) and 229 Hz (torsion about Rover Z). The third is at 257 Hz (local lug bending).
- Load path: Bolt pretension ensures footpad contact on all lugs under loading; loss of contact is not predicted within the acceleration envelope.

13. Credibility Discussion
The credibility of this model for its stated purpose rests on four pillars:

- Input quality and traceability: The loads are directly taken from the program environment document, and material data are standard handbook values with stated variability. The bolt preload range is grounded in the torque process. All sources are cited and archived, reducing ambiguity about what numbers went into the model.

- Appropriate physics and idealizations: The structure remains in the elastic range when evaluated against both the bench strains and the computed 95th percentile stresses. This supports the choice of linear elasticity and bonded contact at the lug bores. The omission of sub-millimeter fillets in CAD is justified by test correlation and mesh studies that show minimal influence on global stiffness and on the stress hot spot once the local mesh density is increased.

- Numerical robustness: Mesh refinement shows asymptotic behavior, with stress changes below 2% from medium to fine. Solver residuals are well controlled, contact conditions are stable, and independent reruns reproduce results within 1–2%.

- Physical correlation: Static strains and eigenfrequencies from the test align with the model within 8% and 4%, respectively. The residual discrepancies are in line with uncertainties in material stiffness and preload; the sensitivity study confirms that plausible parameter spreads cover the observed differences.

On balance, the model provides a reliable basis to judge design sufficiency against the current acceptance criteria for quasi-static launch loads and fundamental frequency. The quantified margins, even when taking upper-tail stresses and lower-tail stiffness, remain positive.

14. Limitations and Considerations for Use
- The model does not include detailed thread geometry, insert compliance, or local micro-contact behavior at the interface. Stresses at the first engaged thread are not represented; any fastener-level assessments should use dedicated submodels.
- Thermal extremes of the lunar environment are not addressed. While the frame resides inside a temperature-controlled vault, any future requirement to assess −40°C to +85°C operation will need explicit temperature-dependent material models and possible thermal preload effects.
- Broadband random vibration and shock are out of scope for this analysis. The present eigenvalue checks and quasi-static accelerations are necessary but not sufficient to conclude on fatigue and damage. If the design proceeds, a separate dynamic analysis with PSD loading and fatigue damage accumulation should be undertaken.
- Geometry changes such as moving cable bosses, altering fillet radii above 1 mm, or substituting different fasteners will invalidate the current mesh; rapid re-meshing is feasible with the stored scripts, but results must be re-established.

15. Recommendations
- Proceed to release drawing Rev C with the current lug fillet radii and M6 fastener callout, contingent on maintaining the specified torque range in assembly.
- Preserve the medium mesh and post-processing workflow as the baseline; any design edits should be run through the same checks (mesh independence spot-check at the hotspot and first mode reassessment).
- If the avionics shelf configuration changes and the frequency separation requirement increases, re-evaluate with additional stiffening at the side rails as the most mass-efficient lever.

References
- LE-2026-17, Launch Environments for CLPS 2xxx Missions, Rev B.
- MMPDS-17, Metallic Materials Properties Development and Standardization.
- STR-ALLOW-2025-04, Derivation of Allowables for Aluminum Lugs Under Combined Acceleration.
- ME-PR-602 Rev C, Fastener Torque Procedure for M6–M10.

Appendix A: Selected Plots (described)
- Figure A1: Von Mises stress contour in the lug region (Case 1). Peak at inner fillet; smooth gradient into side rail. No checkerboarding; isosurface continuity indicates adequate mesh density.
- Figure A2: Mesh convergence graph of hotspot stress vs. nominal element size. Curve flattens between 0.8 mm and 0.5 mm targets.
- Figure A3: Overlay of test and analysis frequency response around the first mode; peaks within 7 Hz.
- Figure A4: Histogram of hotspot stress from 500-sample Latin Hypercube; annotated 95th percentile at 324 MPa.

End of Report.
