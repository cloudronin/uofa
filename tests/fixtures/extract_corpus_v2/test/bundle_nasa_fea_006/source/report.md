Credibility Assessment Report
Project: Lunar Lander Main Gear Fitting BRKT‑241 Finite Element Analysis
Date: 2026‑08‑05
Prepared by: Structures & Loads Group, MoonRise Lander Program

1. Background and Intended Use

BRKT‑241 is the titanium forging that links the primary landing strut to the lander deck. The bracket carries combined vertical, lateral, and fore‑aft loads during terminal descent, touch‑down, and early surface operations, including offloading of cargo. This document evaluates whether our finite element model (FEM) of BRKT‑241 provides a defensible basis for: (a) demonstrating static strength with a minimum margin of safety (MS) of +0.15 on yield and +0.00 on ultimate at 3σ limit loads, (b) verifying the first in‑plane free mode exceeds 120 Hz to avoid co‑excitation with thruster perturbations, and (c) limiting relative slip at the bolted interface to below 0.10 mm under worst‑case landing impulse envelopes.

The FEM is not intended for crash events, thermo‑mechanical gradients beyond −40 to +70 C, nor for life assessment or crack growth; those are addressed by separate fracture control analyses.


2. Summary of the Analysis Approach

- Software and hardware: Abaqus/Standard 2022 HF2, double precision, parallel (32 cores) on JSC‑HPC “Sextant” nodes; Linux kernel 5.4; Intel compilers. Post‑processing in Abaqus/CAE and Python 3.10 with NumPy/SciPy.
- Geometry: CAD from PDM rev D; fillet radii corrected per forging drawing BRKT‑241‑F‑D. Threaded features removed; bolt clamp regions represented by shanks and washer stacks. Local blend radii retained where stress concentration dominates.
- Elements: Predominantly C3D10 (quadratic tetrahedral), with C3D20R conversion solids in fillet hotspots via submodeling. Average global edge length 4.0 mm; refined to 0.75 mm at the critical inner fillet.
- Materials: Ti‑6Al‑4V (MMPDS‑17 A‑basis at 23 C) E=114 GPa, ν=0.34, Rp0.2=930 MPa, Su=990 MPa. Stainless bolt shanks per NAS620, A286, E=196 GPa, Su=1240 MPa. Isotropic elasticity with elastic‑plastic for titanium in nonlinear check cases.
- Contacts and fasteners: Surface‑to‑surface finite sliding with penalty enforcement; nominal friction 0.20 (range 0.10–0.30). Eight bolts modeled with Abaqus pretension sections, nominal 22 kN each, scatter ±10% informed by torque‑tension tests. Washers modeled as rigid plates with compliant foundation springs to capture bedding‑in.
- Loads and boundaries: Landing load set LND‑C3 from Loads ICD v2.7: Fx=4.8 kN, Fy=7.4 kN, Fz=18.2 kN at the strut clevis center, plus bending moment Mx=0.8 kN‑m from strut eccentricity. Deck side constrained at bolt hole diameters with realistic compliance via fastener connectors; deck global‑level stiffness represented through an RBE3‑to‑springs boundary derived from deck modal test (see §5.4).
- Solutions: Static nonlinear with automatic stabilization 0.0002; contact tolerance 1e‑5; line search on, NLgeom=on. Modal analysis (Lanczos) performed on the tangent stiffness about the preloaded state. Submodels run for detailed stress pull‑through at fillets.

3. Decision Criteria and How Results Are Used

- Static strength: MS_yield = (Allowable/Predicted) − 1 ≥ +0.15 at 3σ loads; MS_ultimate ≥ +0.00. Allowables from MMPDS A‑basis; plastic collapse not permitted except as local yielding <2% of volume outside joint lines.
- Slippage: Relative tangential motion at any fastener < 0.10 mm under 3σ lateral/longitudinal loads.
- Dynamics: First in‑plane free mode frequency ≥ 120 Hz with preloads applied.
- Deflection: Relative lateral displacement at strut clevis ≤ 0.25 mm for avionics pointing stability.

4. Model Construction Fidelity: Geometry, Interfaces, and Idealizations

- Geometry handling: The forging model retains all machined fillets down to R=0.75 mm at the lug blend, where peak stresses occur. Pedestal holes are simplified to smooth bores; threads removed and replaced by shank contact surfaces. Non‑load‑carrying cosmetic features (logo cavities, tool bosses) suppressed.
- Interfaces: Fastener clamping modeled with pretension sections and contact pairs; bearing at bores is explicit (no tied constraints). Deck compliance is not assumed rigid; an impedance model from deck modal testing provides realistic boundary softness. This is essential to match joint load transfer and modal predictions.
- Idealizations and their justifications:
  - Temperature fixed at 23 C for structural verification; environmental swings treated separately for fit‑up, not strength.
  - Material anisotropy ignored (forging is considered near‑isotropic per supplier coupon scatter).
  - No fretting fatigue, no wear modeling; not part of this deliverable.
  - Damping only implicit from stabilization; not needed for quasi‑static strength or free‑free frequency.

5. Source and Quality of Inputs

- Materials: MMPDS‑17 A‑basis values for Ti‑6Al‑4V and A286; temperature derating negligible at 23 C. Plastic curve for titanium taken from supplier tensile coupon average with conservative offset (−1σ).
- Friction: Nominal 0.20 using clean, dry contact; range 0.10–0.30 explored; basis: MA‑TN‑311 bolt strip test with same surface prep.
- Bolt preload: 22 kN target derived from torque/preload calibration on representative hardware with Skidmore‑Wilhelm device; COV ≈ 8%.
- Loads: Landing envelopes from GNC Monte Carlo (LND‑C3), 3σ vectors supplied with covariance; used worst‑case composite magnitude and direction.
- Deck compliance: Extracted from deck modal survey (DIC and accelerometers). FRFs reduced to a 6×6 stiffness at the joint plane; R^2=0.97 fit to low‑frequency range (<300 Hz) relevant for our mode check.

Traceability is maintained in the BRKT‑241 Git repository (tag v1.3.2) with references to ICDs and test reports.

6. Numerical Approach and Solver Settings

- Element selection justified with a patch test and a thick‑to‑thin transition check; quadratic tets accepted due to geometric complexity; localized hexahedral submodel addresses stress gradient capture at fillets.
- Nonlinear convergence criteria: Residual force norm < 1e‑6 of reference load; max 40 iterations per increment; automatic increment control (0.05 initial, min 1e‑5, max 0.2).
- Contact: Penalty stiffness auto‑scaling validated to avoid over‑closure; independence checks run with factor ×0.5 and ×2.0.
- Modal extraction: 10 modes to 600 Hz; preloads carried over via linear perturbation.

7. Code Checks and Reference Problems

To build confidence in the solver and element formulations for our use case:

- NAFEMS LE10 plate bending: C3D10 mesh achieved mid‑span deflection within 0.9% of closed‑form; energy norm error 1.4% on fine mesh.
- Hertzian contact benchmark: Cylinder‑on‑flat contact half‑width and pressure peak within 2.6% of theory at ν=0.3; sliding with μ=0.2 reproduced expected stick‑slip segmentation.
- Bolt pretension sanity: Single‑bolt joint verified load path and shortening vs. handbook solutions within 3.1%.
- Patch test with mixed element topology (tets adjacent to hex submodel) passed to machine precision in elasticity.

Results and input decks for these checks are archived under repo path qa/benchmarks/.

8. Refinement and Convergence Work

A three‑level mesh study was performed for the nonlinear landing load case:

- Coarse: 0.9M DOF; hotspot von Mises = 612 MPa; contact slip at worst bolt = 0.07 mm.
- Medium: 1.6M DOF; hotspot = 596 MPa; slip = 0.065 mm.
- Fine: 3.8M DOF; hotspot = 588 MPa; slip = 0.064 mm.

Richardson extrapolation (observed order p≈1.9 for stress in the submodeled region) yields an asymptotic stress of 580 MPa; Grid Convergence Index for the fine mesh is 1.9% at 95% confidence. Contact patch area changed less than 1.5% between medium and fine. Reaction force equilibrium closed to 0.06% on all meshes. Modal frequency converged from 181 Hz (coarse) to 186 Hz (fine); change <3%.

9. Sensitivity and Influencers

- Friction coefficient: μ=0.10 → hotspot +7.2%; μ=0.30 → hotspot −6.1%; slip increases to 0.094 mm at μ=0.10, decreases to 0.041 mm at μ=0.30.
- Bolt preload: −10% preload → hotspot +3.4%, slip +18%; +10% preload → hotspot −2.9%, slip −15%.
- Titanium yield scatter: Using A‑basis already covers material variability; if B‑basis used, MS would increase by ~0.06.
- Fillet radius tolerance (−0.25 mm): hotspot +9.5%.
- Deck stiffness ±20%: frequency shifts ∓6 Hz; hotspot stress changes less than 2.0%.

A Sobol screening (10k Latin hypercube samples using response surface fit) ranks fillet radius and friction as dominant at the hotspot; preload ranks third for slip metrics.

10. Combined Spread and Error Bands

Assuming independent inputs for μ, preload, and fillet radius within the ranges above, plus numerical uncertainty from the GCI, the aggregated 95% bound on hotspot stress at 3σ loads is 627 MPa. The 95th percentile slip is 0.089 mm. A Bayesian update using subscale test strain data (see §11) narrows μ’s effective range to 0.15–0.25, reducing the 95% stress bound to 615 MPa.

11. Check Against Physical Tests

Two data sources anchor the model to reality:

- Coupon‑level friction/preload: For the exact surface prep and washer stack, torque‑tension tests on three bolt assemblies yielded μ_equiv=0.19±0.03 (1σ). Clamp loss after 10 load cycles was <2%. These numbers informed the input ranges used in §5 and §9.
- Subscale bracket test (0.6× geometry): MSN TR‑526 documents a photogrammetry/DIC test with bolts torqued to equivalent clamp ratios and matched load ratios. Result: strain at the scaled inner fillet reached 1620 με at the target scaled load; the analysis predicted 1540 με at the same gage location and load—difference −4.9%. Deflection at the clevis line matched within 3.1%. Contact slip trend with lateral load matched slope within 8%. No gross discrepancies in load path were observed.

Test‑to‑model comparability was preserved by reproducing the boundary softness (scaled deck stiffness matrix) and the bolt pattern. Minor differences include slightly smoother forgings in the test article (Ra reduced by ~10%), potentially explaining 1–2% of the strain gap.

12. Applicability Limits

- Valid for −40 to +70 C (elastic properties temperature insensitivity assumed over this band); not valid for cryogenic or high‑temperature operations.
- Load vectors within the LND‑C3 envelope; out‑of‑plane torque beyond +/−1.0 kN‑m not supported.
- Hardware tolerance stack within drawing limits (fillets no smaller than nominal −0.25 mm; hole position tolerance per GD&T).
- Not suitable for predicting long‑term wear, fretting, or fatigue damage accumulation; separate fatigue design will use this model’s static stresses but includes additional phenomena.
- Not valid for post‑yield redistribution or gross plastic collapse.

13. Results Against Criteria

- Hotspot equivalent stress at fine mesh, nominal inputs, 3σ loads: 588 MPa; with 95% bound including uncertainties: 615 MPa. MS_yield = 930/615 − 1 = +0.51 (meets +0.15). Ultimate check not limiting (MS_ult > +0.60).
- Maximum relative slip: 0.064 mm nominal; 95th percentile 0.089 mm (meets <0.10 mm).
- First in‑plane free mode: 186 Hz (meets >120 Hz).
- Lateral deflection at clevis: 0.09 mm nominal (meets <0.25 mm).

14. Reproducibility and Trace

- All input decks, Python scripts for mesh seeding and post‑processing, and parametric studies are under Git (hosted on on‑prem GitLab) with tag brkt‑241‑ana‑v1.3.2; CI pipeline runs Abaqus non‑graphical jobs and publishes artifacts.
- Abaqus job files include machine, compiler, and environment hashes for deterministic behavior; seeds are irrelevant for deterministic static runs but solver logs are archived.
- A change log captures geometry updates (rev C→D added a 1.0 mm fillet increase on the lug blend), rationale, and impacts; no other changes after v1.2.9 affected the hotspot.

15. Independent Scrutiny

- A red‑team review by S. Kline (JSC/ES4) on 2026‑06‑14 examined model form, boundary conditions, and convergence. Findings: recommended reducing artificial stabilization by 50% and re‑checking contact sensitivity. Actions closed in v1.3.0; results changed <1%.
- Cross‑code spot check: The linearized, preloaded stiffness case was exported and run in MSC Nastran SOL103/106 by a separate analyst. First mode matched within 2.1%; linear static displacements within 2.5% when using equivalent fastener elements.

16. Analyst Competence and Process Discipline

- Lead analyst holds NAFEMS PSE in Structural Analysis; 12 years aerospace experience; prior bolt‑joint modeling training (Abaqus advanced contact course).
- Secondary analyst peer‑checked the input deck and results extraction. All scripts include docstrings, unit checks, and pytest unit tests where applicable.

17. Managing Data and Software

- Configuration control: Abaqus version locked to 2022 HF2 for this project; upgrades require re‑run of the three reference problems and one production case to qualify the environment.
- Data storage: PDM Windchill hosts drawings and load cases; raw and processed data stored on EDMS with metadata (owner, date, hash). All retained through CDR+5 years.

18. Presentation of Results and Clarity

- Hotspot stresses are reported at a distance of 0.4 mm off the surface to mitigate singular edge artifacts, consistent with company practice.
- Plots include units, legends, and deformed‑undeformed overlays at appropriate scales. Von Mises contours overlaid with principal stress vectors near fillets to reveal multiaxiality.
- Key figures and tabulations cite the exact model hash and load case.

19. Compatibility of Test and Model for Validation Purpose

- Boundary mimicry: The subscale test used a polycarbonate plate to represent deck compliance; its stiffness matrix, scaled to similarity, was implemented in the FEM. Instrumentation points in DIC were mapped back to the CAD surfaces used in the analysis to avoid location bias.
- Load introduction: Both analysis and test used a clevis pin with the same offset and a belly band to ensure load line passes through the designed datum.

20. Residual Gaps and What We Didn’t Do

- We did not simulate micro‑slip energy dissipation or bolt bending under off‑axis loads explicitly; our connector approach matches measured joint stiffness but not local shear in the shank. This is acceptable for strength and slip metrics but not for fretting assessments.
- Surface roughness variations were bracketed implicitly via friction ranges but not modeled geometrically.
- Thermal preloads from differential contraction at −40 C were not included; the decision was to address them in the interface control document as separate fit‑up loads.

21. Conclusions

The BRKT‑241 finite element model provides a credible basis for the intended decisions. The analysis is grounded in vetted inputs (materials, loads, joint behavior), uses appropriate element technology and solver controls, demonstrates stable mesh behavior with quantified numerical error, and is cross‑checked against both reference solutions and a subscale physical test. Sensitivity studies identify friction and fillet radius as the dominant knobs; uncertainty propagation shows sufficient design margin remains when these vary within realistic ranges.

The model may be used to sign CDR exit criteria for static strength, slip control, and modal detuning for the main gear fitting, limited to the domain and assumptions spelled out above. Any design changes that reduce fillet radii beyond nominal −0.25 mm, introduce coatings that significantly alter friction, or shift the deck stiffness envelope must trigger re‑analysis.

Appendix A lists the mesh study details, benchmark problem summaries, and the independent review action closure status.


Limitations and Recommendations

- The current model should not be repurposed for life/fatigue calculations without explicitly addressing contact microslip and mean stress corrections. A separate durability model is being prepared.
- If the hardware process changes (e.g., lubrication added, coating applied), re‑characterize friction and update the model; slipping margin is sensitive to μ.
- If on‑vehicle modal test identifies substantial differences in deck joint stiffness, repeat the mode check with the updated joint impedance.
- Consider a limited nonlinear material run to confirm that in the worst plausible case (μ=0.10, preload −10%, fillet −0.25 mm), local yielding remains confined; preliminary run showed <1% plastic zone at the fillet with no redistribution.

Acknowledgments

We acknowledge the Loads & Dynamics team for the LND‑C3 envelopes, the Structures Test Lab for the subscale bracket DIC data, and Software QA for managing the GitLab CI pipelines.

References

- MMPDS‑17, Metallic Materials Properties Development and Standardization.
- BRKT‑241 Forging Drawing Rev D and Machining Spec.
- Loads ICD v2.7, MoonRise Lander Program.
- MSN TR‑526, Subscale BRKT‑241 DIC Test Report.
- MA‑TN‑311, Torque‑Tension Calibration for A286 NAS620 Fasteners.
- Abaqus 2022 Theory and Analysis Guides.
