# Credibility Assessment Report — FEA of Reaction Wheel Bracket for 12U SmallSat

Project: RWA-3 Bracket Upgrade  
Code base: Abaqus/Standard 2023 HF4, Python 3.10 pre/post scripts  
Model ID: FE-RWA3-BRK-021, Rev C  
Date: 2026-07-31  
Analyst: L. Peralta (NAFEMS L2, 12 years structural modeling)  
Independent reviewer: J. Carver (PhD, 18 years dynamics), not on design team

## 1. Background and Intended Use

The RWA-3 bracket is a machined Ti-6Al-4V component that supports a 2.1 kg reaction wheel assembly (RWA) on the avionics deck of a 12U SmallSat. The analysis objective is to:

- demonstrate positive margin against yield for quasi-static launch loads per LV-STD-129: 10g axial, 8g lateral, 6g transverse (with NASA-STD-5011 load factors applied), and
- verify that the first local mode of the RWA-bracket subassembly is above 500 Hz to avoid coupling with bus modes,
- provide stress/strain predictions at gage locations to compare with a bench test of a flightlike bracket and mass simulator,
- quantify the impact of key uncertain inputs (bolt preload, friction, fillet radius, Ti properties) on peak stresses.

The model will be used to support flight clearance for a specific bracket lot (S/Ns RWB-052 through -058). It is not intended for predicting permanent set or fatigue life; those topics are addressed in separate work packages.

## 2. Modeling Choices and Shortcuts

Geometry fidelity:
- CAD from P/N RWB-402123 Rev B was defeatured to suppress cosmetic engravings, micro-chamfers < 0.2 mm, and thread profiles. The threaded holes are represented as smooth bores with embedded fastener connectors.
- The avionics deck is represented as an equivalent orthotropic plate region under the bracket footprint with effective bending stiffness tuned to a detailed bus model (extracts provided in CM-TR-561).

Material behavior:
- Ti-6Al-4V E(T) curve and density from MMPDS-17 (A-basis, room temperature). Poisson’s ratio 0.34. Linear elasticity used; geometric nonlinearity off. A sensitivity run with E reduced 3% to approximate hot thermal case is included.
- Fasteners modeled as beam-based connector elements with axial stiffness derived from torque-preload testing data (Section 5).

Contact and joints:
- Bracket-deck interface uses hard contact in normal direction and isotropic Coulomb friction in tangential direction. Nominal friction coefficient μ = 0.18; explored range 0.10–0.25.
- Bolt preload introduced via connector thermal shrinkage equivalent (calibrated to produce 4.5 kN per bolt, ±10%).

Loads and boundary conditions:
- Quasi-static accelerations applied as body forces to the RWA mass proxy and bracket. The deck boundary is fixed at mounting hole rings, consistent with system-level interface definitions for the test fixture.
- Modal analysis performed on the assembled bracket with mass proxy and fasteners; bus flexibility not included (modes reported are local to the bracket).

Known omissions:
- Thread bending and local bearing deformation around holes are not resolved. This tends to redistribute stress away from idealized smooth holes; to compensate, margins are evaluated using A-basis allowables and measured strain comparison.
- Damping is not modeled in modes; frequencies only are used for acceptance.
- Temperature dependence beyond a single E perturbation is not included, as thermal maps predicted <15 C variation at launch; see THM-TR-115.

## 3. Tools, Numerical Methods, and Code Checks

Solver and element formulation:
- Abaqus/Standard 2023 HF4, with C3D10 (quadratic tetrahedron) elements for the bracket and the equivalent plate region meshed with S8R shell elements. Embedded beam connectors for bolts.
- Contact pairs use surface-to-surface small-sliding formulation with penalty tangential behavior and finite friction.

Solver settings:
- Static general step with automatic stabilization off. Increment control: initial 0.1, min 1e-4, max 1.0. Nonlinear tolerances at default (0.5% residual force). Convergence achieved without cutbacks in the final mesh.
- Normal modes extracted via Lanczos, 12 eigenpairs up to 2000 Hz.

Vendor quality and internal checks:
- The features exercised (C3D10, contact, beam connectors, normal modes) have been assessed against NAFEMS benchmarks NAFEMS-R0040 (cantilever beam; displacement and stress), NAFEMS-R0051 (plate with hole), and an internal bolted-joint pull test (BJ-VAL-07). Maximum deviation recorded: 3.4% in mode frequency, 5.8% in stress concentration for coarse tetrahedral meshes. These benchmarks were rerun in 2025 with the same Abaqus build; hashes recorded in VVP-PL-021 Appendix B.
- A patch test (uniform strain) on a custom bracket slice geometry passed within machine precision for all element types used.

Software configuration:
- Abaqus license server LMVER 11.19, feature codes documented in SW-QA-102. No open SPRs affecting C3D10 or connector behavior per Dassault KB review as of 2026-06-15.
- Pre/post scripts versioned in GitLab repo M&S/fea-rwa3, tag v2.3.1. Execution environment: Windows 10 22H2, Intel Xeon W-2295; solver output reproducibility verified across two machines (checksum of ODB result fields identical to 8 significant digits).

## 4. Geometry and Mesh Quality

Discretization:
- Three systematically refined meshes were generated by advancing curvature-based sizing around fillets and hole edges:
  - M1 (coarse): 118k elements, 212k nodes.
  - M2 (medium): 462k elements, 801k nodes.
  - M3 (fine): 1.78M elements, 3.05M nodes.
- Quality metrics: minimum corner angle > 27°, Jacobian > 0.5, aspect ratio median 1.8 (95th percentile 4.2). Contact master surfaces refined to target 0.4 mm edge size; fillet zones to 0.25 mm.

Mesh independence:
- Peak von Mises stress at the inner fillet adjacent to Bolt B3 under the 10g axial case converged monotonically M1→M3. Richardson extrapolation with observed order p = 1.83 yields a grid convergence index (95% CI) of 5.6% for that hotspot on M3. Global strain energy varied <0.9% between M2 and M3.
- Reaction forces at supports matched applied inertial loads within 0.2% across all meshes, indicating good force balance.

Modal discretization:
- First local mode shape (out-of-plane bracket flap) frequency stabilized by M2; M3 shifted by +1.1% relative to M2, consistent with refined fillet compliance.

## 5. Inputs and Where They Came From

- Ti-6Al-4V material: MMPDS-17 Table 2.3.1.0(b), A-basis tensile yield 827 MPa at 22 C. Elastic modulus mean 114 GPa, coefficient of variation 3%. We used mean E in the baseline, A-basis strength for allowables.
- Mass simulator: 2.10 kg ± 0.02 kg, inertia matrix matched to RWA spec (RWA-DWG-812), verified by torsional pendulum test; uncertainty negligible for static loads.
- Bolt preload: 4x M5 x 0.8 class 12.9, target torque 7.5 N·m per NASA-STD-5020 guidance. Torque-to-tension correlation (k factor 0.20 ± 0.03) measured on five samples with ultrasonic elongation; resulting preload mean 4.5 kN, 1σ = 0.45 kN.
- Interface friction: Default μ = 0.18 derived from treated Ti-Ti with Alodine per ECSS-Q-70-71A; test coupons in our lab showed μ in 0.14–0.22 range under 4–5 kN clamp. We carried 0.12–0.25 in uncertainty propagation.
- Load factors: Quasi-static equivalents per LV-STD-129, with 1.4x limit loads for strength margin calculations. Orientation cases per ICD-AV-113.

All values are cataloged in the input ledger INP-RWA3-015, with citations and file paths. Where possible, A-basis or conservative tails were selected.

## 6. Bench Testing and Cross-Checks

A static pull test and a modal tap test were conducted on a dedicated fixture that replicates the deck boundary. The test article is a production bracket (S/N RWB-053) with production fasteners and Alodine surface finish. Instrumentation included:

- Two 3-element strain rosettes: G1 at the fillet near Bolt B3, G2 on the outer web.
- Triax accelerometer on the bracket ear for modal extraction; impact hammer with force transducer.
- Ultrasonic bolt elongation monitoring for preload confirmation.

Static test:
- Bracket with mass proxy subjected to a 210 N vertical load (approx. 10g) applied through the RWA CG with load applicator; load cell accuracy ±1%.
- Measured principal strain at G1: 1820 με ± 36 με (2%); model predicted 1755 με on M3 with test-preload settings (4.3% low). At G2: measured 680 με ± 14 με; model 703 με (+3.4% high).
- No visible slip or seating after two load-unload cycles; residual strain < 10 με at both gages.

Modal test:
- First local mode measured at 620 Hz ± 6 Hz, with a clear single-dof peak. Model (M3) predicted 603 Hz with production preload and μ = 0.18 (−2.7%). Mode shapes qualitatively matched.

These comparisons anchor the model and inform the uncertainty bounds in Section 8.

## 7. Solution Behavior and Numerical Health

- Nonlinear iterations per static case: ≤6 for the three orthogonal acceleration directions. No contact chattering detected; tangential slip indicator zero at nominal preload and μ ≥ 0.14 under all three directions. A low-friction extreme case (μ = 0.10) produced localized micro-slip near Bolt B1, but stresses at the critical fillet changed by <2%.
- Kinetic energy fraction remained <0.3% of strain energy, confirming quasi-static behavior.
- Reaction force balance error <0.2% in all runs. No negative eigenvalues in the linear stiffness matrix for preloaded state.

## 8. Which Knobs Matter and How Uncertain Are We?

We explored input variability using a Latin hypercube sample of 200 realizations on M2, spanning:
- Bolt preload per bolt: Normal(4.5 kN, 0.45 kN), truncated at 3.3–5.7 kN.
- μ: Uniform(0.12, 0.25).
- Fillet radius at the hotspot: Normal(1.50 mm, 0.15 mm) per machining tolerance stack.
- E: Normal(114 GPa, 3.4 GPa).
- Load magnitude: Normal(210 N, 3 N).

Outputs tracked:
- Peak von Mises stress at the G1 fillet,
- Principal strain at rosette locations,
- First local mode frequency.

Findings:
- For the 10g axial case, peak von Mises stress mean = 260 MPa, standard deviation = 18 MPa. The 95th percentile is 289 MPa. Cumulative contribution by standardized regression coefficients: preload 51%, fillet radius 29%, μ 12%, E 7%, load 1%.
- For the first local mode, frequency mean = 607 Hz, standard deviation = 9 Hz; none of the samples dropped below 590 Hz. Preload dominates (61%).
- Adding the mesh-convergence estimate (5.6% at hotspot) in quadrature with input variability produces a combined coefficient of variation ~7.0% for peak stress.

Uncertainty on test comparison:
- Test gage uncertainty (2%) and modeling error (bias −4.3% at G1) suggest a small conservative bias. We did not explicitly bias-correct the model; instead, we carry the observed discrepancy into the total uncertainty budget.

## 9. Results Summary for Decision Makers

- Strength: Under 1.4x 10g limit (294 N body force), the predicted 95th percentile peak stress at the hotspot including mesh and input variability is 404 MPa. Using A-basis yield of 827 MPa, the strength margin = (827 / 404) − 1 ≈ +1.05. Even with a hypothetical 10% downward shift in allowable (temperature or lot variability), margin remains > +0.9.
- Stiffness: The first local mode of the bracket-RWA subassembly is predicted at 603 Hz nominal; test measured 620 Hz. Across input variability, the 5th percentile exceeds 590 Hz; requirement 500 Hz is met with headroom.
- Interface behavior: No gross slip at the interface at nominal or low-μ corners; joint remains clamped under all quasi-static orientations studied.

## 10. Boundaries of Valid Use

- This model covers the RWA-3 bracket in the as-designed geometry (Rev B), with Ti-6Al-4V per MMPDS-17, and four M5 fasteners at the specified pattern. Deviations in material (e.g., Ti-6Al-2Sn-4Zr-2Mo) or fastener class are out of scope.
- Load envelopes: 0–12g quasi-static body forces and local modes up to 1000 Hz. Not applicable to pyroshock, landing loads, or sustained high-temperature flight phases.
- Temperature: Implicitly near room temperature. If operational temperature deviates beyond −30 C to +60 C, update E(T) and recheck margins.
- Manufacturing tolerances: Fillet radius outside 1.2–1.8 mm, hole positional tolerance exceeding ±0.15 mm, or surface condition altering friction beyond 0.10–0.25 require reassessment.

## 11. Track Record of This Approach

- The beam-connector and frictional interface approach was applied to the Aurora-4 CubeSat reaction wheel bracket (2019), with measured-vs-predicted strains agreeing within 8% and local mode within 4%. The same modeling playbook (documented in MTHD-017) has supported five flight units without in-service anomalies.
- NAFEMS and internal verification problems routinely run in CI pipelines on commit; failures block tags. The last 24 months show zero regressions on the element types and features used here.

## 12. People and Process

Analyst qualification:
- Lead analyst completed Abaqus advanced contact and bolted-joint modeling courses (certificates on file), and maintains NAFEMS Level 2 credential in structural analysis.

Peer scrutiny:
- Independent reviewer (not part of the design team) performed a cold read and a targeted model recreation using M2 mesh, different contact discretization (node-to-surface), and verified that hotspot location and magnitude were within 6% of reported values. Review comments and closure responses recorded in CR-REV-441.

Planning and oversight:
- A modeling plan (MVP-PL-342 Rev A) defined acceptance criteria (strain within 10% of test, mode within 5%, mesh GCI < 10% at hotspot). All criteria met. Schedule and resource allocations tracked in Jira EPIC M&S-RA-120; no late waivers.

Configuration and traceability:
- All inputs captured in a parameter file (params.yml) with hash; solver jobs launched via a reproducible Python driver (run_case.py). Model revision FE-RWA3-BRK-021 Rev C is immutable and archived with solver outputs in the project vault. Any future use must declare the revision ID in the system engineering drawing tree.

Data handling:
- Test data, including raw strain time series and FFTs, are stored in SharePoint LIB-STR-2026 under “RWA3 Bracket Test,” with calibration certificates. A data lineage map links each plot in this report to a source file path and checksum.

## 13. How the Results Make Physical Sense

- The dominant stress arises at the inner fillet nearest the bolt aligned with the acceleration vector. Load path: body force on RWA mass produces a shear through the bracket ears into the deck; bolts B2/B3 carry higher shear and clamp the interface, creating a local bending moment about the fillet. The observed gage strains confirm this distribution.
- Frequencies respond to preload and fillet radius as expected: higher preload stiffens the interface, nudging mode shapes upward; larger fillet softens the local region and lowers the first mode. Both trends were borne out in parametric sweeps.

## 14. Limitations and Risk Residuals

- Without explicit threads and bearing, micro-scale stress states near hole edges are not resolved. This is acceptable for bracket-level yield margins but limits applicability for predicting fretting or fatigue initiation. Separate coupon tests and a notch fatigue model will be used for life assessment.
- No bus-level flexibility is included in local mode predictions; system modes could introduce coupling effects below 500 Hz, but that is addressed in the integrated finite element model (IFEM) at the spacecraft level.
- Friction behavior under vibration may differ from static values; however, strength margins are not friction-critical in this configuration, and static test showed no seating shifts.

## 15. Reproducibility and Repeat Runs

- A clean rerun on a second workstation (AMD Threadripper PRO 3975WX) using the same tagged inputs produced identical mesh statistics and stress fields within 0.3% of the original, after aligning random seeds for the Latin hypercube generator. ODB file checksums differ due to time stamps, but extracted result vectors match to 8 significant digits.

## 16. Summary Credibility Discussion

Evidence supporting confidence in the predictions includes:
- Independent checks: Reviewer’s parallel model locked onto the same hotspot and stress levels within 6%, and all acceptance criteria were satisfied.
- Numerical quality: Mesh convergence demonstrated with quantified error bars; solver residuals and energy metrics are well-behaved; patch/benchmark tests passed.
- Empirical tie-in: Strain gage and modal measurements agree within 4–5% of predictions at critical locations. Measurement uncertainty is small relative to the observed differences.
- Sensitivity knowledge: We know which inputs the outputs depend on most (preload and fillet radius), and those inputs are either measured (preload) or tightly toleranced (fillet).
- Data sources: Material properties and joint behavior derive from aerospace-standard references and in-house measurement campaigns, with conservative selections where ambiguity exists.
- Process discipline: Version control, documented plan, and immutable archives ensure repeatability and auditability. Toolchain stability is verified, and solver features used are mainstream and previously vetted.

Residual concerns are limited to areas not central to the present decision (fatigue, micro-slip under vibration), which are explicitly out of scope and handled elsewhere.

## 17. Next Steps

- Finalize and release FE-RWA3-BRK-021 Rev C as the controlling analysis for flight clearance in DOC-CLR-719.
- Feed the measured preload distribution and fillet radius inspection results from the actual flight lot into the parameter file and regenerate margins as part of as-built acceptance.
- Transfer the hotspot stress-strain field and uncertainty bounds to the fatigue analysis team for life predictions, with a caution about the joint-level simplifications.

## 18. Appendix: Key Numbers (for quick reference)

- Peak von Mises at hotspot (1.0x 10g): 260 MPa mean; 289 MPa at 95th percentile. Combined with load factor 1.4 gives 404 MPa at 95th percentile.
- A-basis yield (Ti-6Al-4V): 827 MPa at 22 C.
- Margin against yield at 1.4x: +1.05 (95th percentile).
- First local mode: 603 Hz prediction; 620 Hz test.
- Mesh GCI at hotspot: 5.6% (M3).
- Strain comparison at G1: model 1755 με vs test 1820 με (−4.3%).
- Dominant sensitivities: preload (51%), fillet radius (29%).

All supporting artifacts are linked in the project index file INDEX-RWA3-CL, including model archives, test reports, and review records.

---
Prepared by:  
L. Peralta, Structures and Mechanisms Group

Reviewed by:  
J. Carver, Dynamics and Loads Group (independent)
