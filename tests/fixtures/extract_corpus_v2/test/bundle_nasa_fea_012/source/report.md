To: LTV Structures IPT Lead
From: R. Mendez, FEA Lead
Subj: Credibility status — avionics shelf bracket model (A-211) for PDR
Date: 2026-08-06

Summary
We built and checked the finite-element model of the Ti-6Al-4V avionics shelf corner bracket (A-211) used to tie the shelf to the primary deck. The analysis supports PDR decisions on material, bolt pattern, and allowable load envelope. Below is what we did to make sure the numbers can be trusted and where the limits are.

Model overview and scope
- Intended use: predict peak von Mises stress, interface forces, and local safety margins for quasi-static combinations representing launch and worst-case landing handling. Not for high-cycle fatigue or pyroshock.
- Geometry: native CATIA v5 R30 import, as-built 7.00 mm wall nominal. Tolerances ±0.25 mm modeled via envelope study; small fillets (<0.6 mm) omitted except at the bolt countersinks.
- Physics captured: linear elastic Ti-6Al-4V (E=114 GPa, ν=0.34) with nonlinear contact at bolt interfaces and pretension. Small-strain kinematics; no plasticity or creep.
- Solver: Abaqus/Standard 2022 HF4, double precision, static general with automatic incrementation; convergence tolerances tightened to 10^-6 on force residuals.

Evidence supporting credibility
- Mesh quality/refinement: 10-node tets (C3D10M) with local refinement at the countersink edge and internal corner. Global size 2.0 mm; two uniform refinements to 1.0 and 0.5 mm gave hotspot stress change of 3.5% (1.0→0.5 mm) and reaction force change of 0.8%. Element Jacobians >0.6, aspect ratios <4 in refined regions. Secondary cross-check with swept hexes in a submodel (<3% stress difference).
- Sanity tests on the setup: hand calc for an L-bracket in pure bending and a bearing-stress check on the bolt hole matched FEA within 2–4%. Boundary constraints independently flipped (pin vs MPC equivalent) to check spurious stiffening; deflection within 1.2%.
- Code confidence: vendor patch test suite for quadratic tets reproduced with our install; our internal verification set (cantilever, thick cylinder, Hertz contact) matches closed forms/handbooks within 1–3%. No open SPRs from Dassault affecting contact or pretension in this release.
- Inputs pedigree: material from MMPDS-17, B-basis at -60 C; lot-specific coupon tests (lot 17A) showed E=114±3 GPa, σy=880±10 MPa (10 specimens). Friction μ for Ti/steel fastener stack taken as 0.20±0.05 (ECSS-E-HB-32-23A, verified by two torque-tension checks). Preloads measured 10.0±0.2 kN on the test article; same values used in the model.
- Boundary loads: load set derived from GN&C envelope for handling/landing and quasi-static launch accelerations; traceable to Dynamics ICD Rev D. We assessed extrapolation only up to 1.2× these envelopes; beyond that the bracket would require plasticity modeling.
- Correlation to hardware: a single bracket with identical bolt pattern instrumented with 8 strain gauges around the countersinks. Test on MTS frame to 12 kN resultant produced average gauge agreement 3.2%, worst 6.7% (FEA high at the inner countersink). Back-calculation showed 0.18 friction best fits the set; we did not tune beyond documented μ-range.
- Sensitivity and what really matters: screening DOE on 24 high-fidelity runs (μ, preload, lateral load split, hole diameter) feeding a quadratic response surface; Sobol indices show yaw load split (0.43) and μ (0.31) dominate hotspot stress; preload (0.12) and hole size (0.09) are secondary.
- Uncertainty propagation: 150 Latin-hypercube samples on the surrogate spanning documented ranges gave 95% interval on peak stress 612±28 MPa at the inner countersink under the design load. All realizations remained below yield with margin >1.3; P99 remains <700 MPa.
- Robustness checks: small geometry perturbations (±0.25 mm wall, +0.1/–0.0 mm hole) change max stress <2.5%; swapping to tied contact at the countersink (worst plausible) raises hotspot by 5.8%—still acceptable margin.
- Range of validity: temperatures –120 to +70 C (E and σy adjusted per MMPDS tables). Not valid for dynamic shock, fatigue, or conditions with galling/μ<0.12.
- Traceability/configuration: model, scripts, and result images in Windchill vault A-211/v3.5; inputs locked via Git LFS tag a211_pdr_3p5. Abaqus journal enables one-click reruns. Units audit run (N, mm, MPa) and naming conventions documented in README.md.
- People and process: work performed by two analysts (NAFEMS L2/L3; 14 and 9 yrs exp). Independent check by J. Kline (separate reporting chain) covered model form, contact choices, and convergence; 7 comments closed, 1 RFA resolved (fillet omission near bolt #3).
- Prior use history: same workflow and contact/preload approach matched test data on the PLSS avionics bracket (2024) within 5%. Lessons learned (refinement near countersinks, preload scatter handling) applied here.
- Documentation and reviews: requirements mapping to structural ICD in DOORS; peer review held 2026-07-28 with sign-offs captured in CR-1187. All figures include scale bars, units, and callouts; no orphan results.
- Limitations/open items: acoustic/shock environment not yet analyzed; a modal/dynamic pass (SOL 103/111 equivalent) will follow. If late-cycle mass growth pushes loads >1.2× current, we will extend the material model to include plasticity and revalidate.

Bottom line
For its intended decision use at PDR, the model is well grounded: mesh behavior is stable, inputs are traceable, and bench-top measurements substantiate the stress field at key locations. Within the stated operating window, we judge the current analysis ready to support design closeout and bolt-pattern freeze, with the caveats noted above.
