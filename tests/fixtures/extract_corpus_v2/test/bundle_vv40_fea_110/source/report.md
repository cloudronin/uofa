Title: Credibility Assessment Report — Drop/Crush FEA of EV Battery Module Enclosure (Project: BP-ENCL-23C)

Revision: R02
Date: 2026-08-06
Prepared by: Structures Group, Energy Systems Division

1. Background and Purpose

The battery module enclosure (BME) for the M48 electric platform must withstand a one-meter corner drop onto concrete and a 20 kN quasi-static crush without breaching cell compartments or yielding beyond specified margins. This report documents the credibility of our finite-element model used to support design release Gate D. The analysis informs two go/no-go quantities of interest:
- Deformation at the innermost wall adjacent to cells (intrusion) during the corner drop.
- Equivalent plastic strain at baseplate weld toes under compressive crush.

Engineering acceptance thresholds are:
- Intrusion less than 3.0 mm everywhere.
- Local equivalent plastic strain less than 5% at weld toes in the static crush case.
- Fastener axial load below 80% of proof for M8 class 10.9 bolts.
- Peak acceleration at the mass center below 40 g during drop.

These limits align with internal spec ES-5412 and derivative safety rules for cell spacing. Credibility of the analysis is evaluated through multiple checks: model-build traceability, code behavior sanity checks, numerical resolution studies, comparison with physical test data, uncertainty exploration, and independent review.

2. System Description and Intended Use

The BME is a welded 6061-T6 aluminum housing with a 2.0 mm formed sheet cover, 3.0 mm baseplate, twelve M8 bolts fastening to an internal support frame, and intermittent 25 mm stitch welds along longitudinal seams. For the drop case, an empty (no cells) module is instrumented; ballast plates replicate cell mass and inertia. For crush, the assembly is compressed between a flat platen and a stiff support beam.

The FEA is intended for:
- Pre-certification design screening against the limits above.
- Identifying hotspots to guide weld length, rib placement, and thickness adjustments.

Out-of-scope for this analysis:
- Thermal runaway or fire effects.
- Long-term fatigue.
- Fluid-structure interactions (none present).

3. Quantities of Interest and Acceptance Measures

We track:
- Max inward displacement at four designated wall nodes near cell keep-outs (corner, mid-span).
- Averaged von Mises plastic strain over a 2 mm neighborhood around weld toes in the static case (post-peak stabilization).
- Bolt axial forces integrated over shank for all twelve bolts.
- Rigid-body filtered acceleration (CFC60) at the mass center of the module during drop.

Acceptance criteria are enumerated in Section 1 and were agreed at Design Review DR-23C-07 with Safety and Manufacturing.

4. Model Construction and Assumptions

4.1 Geometry and Simplifications
- CAD source: SolidWorks PDM, part files ENCL_V12, BASE_V11, COVER_V09. Feature removal: all fillets below 1.0 mm suppressed except at weld toes in submodels; small mounting brackets not involved in the load path were excluded (<0.2% mass impact).
- Weld representation: For global runs, intermittent fillet welds modeled as tie constraints along stitch regions with equivalent throat area; local submodels include explicit 6 mm fillet geometry with V-notches sized per WPS AL-6061-F-6.
- Bolts: Pretensioned beam connectors (ABAQUS CONN3D2) with axial and rotational stiffness matched to M8x1.25 class 10.9 per VDI 2230. Preload set to 15 kN nominal ±10%.
- Contact: Surface-to-surface penalty formulation between enclosure and concrete floor (μ = 0.25 baseline; range 0.20–0.30). Self-contact enabled between cover and base flanges.

4.2 Materials
- Base material: Aluminum 6061-T6, elastic-plastic with rate sensitivity. Elastic: E = 69.0 GPa, ν = 0.33, ρ = 2700 kg/m^3.
- Plasticity: Johnson–Cook with parameters A = 270 MPa, B = 114 MPa, n = 0.35, C = 0.015, m = 1.0; temperature effects disabled (testing was at 21±2 C).
- Bolts: Steel 10.9, elastic-plastic isotropic hardening, σy = 940 MPa.
- Weld metal: ER4043 filler, σy = 120 MPa, scaling factor for as-deposited hardness 0.85–1.00; baseline 0.92 used; confirmation coupon test results in Appendix A.3.

4.3 Loads and Boundary Conditions
- Drop: 1 m effective free-fall, corner first, orientation per internal drop spec DS-115. The floor is modeled as rigid analytic surface with normal stiffness 1e9 N/mm, penalty contact. Initial velocity 4.43 m/s, gravity included. Ballast mass 18.5 kg attached via distributed coupling to match inertia tensor of full module.
- Crush: Displacement-controlled platen travel 15 mm at 1 mm/s; lower support beam rigid. Lateral motion constrained to mimic test fixture guides.
- Preload: Bolt pretension applied and equilibrated before load application.
- Damping: For drop, structural damping omitted; material rate effects capture most dissipation; contact damping coefficient 0.2 in baseline model; sensitivity evaluated.

4.4 Mesh and Element Technology
- Global model: Reduced-integration hexahedra C3D8R for baseplate and ribs; shells S4R for cover; connectors for bolts. Typical element edge length: 7 mm baseline; coarser 10 mm and finer 5 mm used in the mesh study. Hourglass control enhanced stiffness turned off; default visco provided; monitored via energy ratio.
- Local submodel: 3D solid refinement of weld toes and adjacent plates, target 1 mm elements at notch; kinematic coupling boundary nodes extracted from global solution.

5. Numerical Approach and Solver Configuration

- Software: Abaqus/Explicit 2024 HF2 for drop; Abaqus/Standard 2024 HF2 for quasi-static crush and submodeling. Double precision. Solver logs and input decks archived.
- Time integration: Explicit central difference for drop, stable increment auto; mass scaling factor limited to keep KE/IE ratio below 5% after contact. Peak stable δt around 2.4e-7 s; total simulation time 15 ms.
- Contact parameters: Penalty with 0.25 friction; hard contact pressure-overclosure. Surface smoothing 0.1 applied to the floor to mitigate chatter.
- Convergence: For crush, arc-length not required; NLGeom on; automatic stabilization set to 0.0002 with energy dissipation tracked below 1% of external work at final load.
- Hardware: HPC cluster node, 32 cores, Intel Xeon 8358, 256 GB RAM. Parallelization via domain decomposition for explicit, multi-threaded solver for implicit.

6. How We Checked the Model

6.1 Software Behavior Checks (Code Confidence)
- Vendor QA: Abaqus 2024 HF2 release notes reviewed; no open SPRs affecting explicit contact for metallic impact at the time of run. License diagnostics confirmed.
- Internal mini-benchmarks: 
  - Single-element uniaxial and simple shear run to verify stress/strain sign convention; results matched analytic within 0.2%.
  - Bending patch test on a 10x10 shell panel S4R with uniform pressure; slope and curvature matched classical plate theory within 1.5%.
  - Elastic wave speed check: drop test of an aluminum bar compared to cL = sqrt((E(1-ν))/((1+ν)(1-2ν)ρ)); arrival times within 3%.

6.2 Numerical Resolution and Robustness
- Mesh refinement study:
  - Three global meshes (10 mm, 7 mm, 5 mm) run for the drop. Max intrusion at the critical corner was 2.92, 2.78, and 2.73 mm respectively. Change from 7→5 mm was 1.8%. Energy balance and contact force time histories showed converging peak values (within 2.4%).
  - For crush, the averaged weld-toe strain at 10 mm vs 7 mm changed 6.1%; 7 mm vs 5 mm changed 2.3%. Local submodel with 1 mm elements reduced notch discretization bias; peak localized strain averaged over a 2 mm path was 3.8% vs 4.1% in the globally refined model; difference attributed to geometry fidelity at the toe.
- Temporal resolution:
  - In explicit runs, the KE/IE ratio after first rebound remained under 3.2%. Sensitivity with halved mass scaling showed <1% change in intrusion, <0.5 g change in peak acceleration.
- Element formulation checks:
  - Swapping C3D8R to C3D8I in a 100 mm cube proxy under compression changed peak contact force by 0.7%. In the full model, C3D8I was computationally expensive with no meaningful benefit given hourglass energy stayed <4% total internal.
- Contact robustness:
  - Varying solver penalty stiffness by ±50% changed maximum contact pressure by <2% and intrusion by <0.1 mm, indicating insensitivity in the converged regime.
- Solution pathologies:
  - No negative volumes or excessive element distortion observed. Min aspect ratio >0.35. The worst hourglass energy fraction was 3.6% at impact; flagged but acceptable.

6.3 Comparison Against Physical Tests

We conducted two test campaigns at Lab 17, both certified to ISO/IEC 17025, with NIST-traceable instruments.

- Corner Drop Test:
  - Configuration: Empty BME with ballast plates; drop height 1.00±0.01 m; orientation verified with laser plumb line. Floor material: C30/37 concrete pad, surface roughness Ra ~0.6 mm.
  - Measurements: Three triaxial accelerometers (PCB 356A45) at mass center and two corners; one 350 Ω strain gauge rosette near a weld toe; high-speed video (Phantom VEO 710) with DIC speckle for dent depth at two panels. Uncertainty: ±0.5 g for acceleration, ±50 µε for strain, ±0.1 mm for dent depth. Data processing CFC60 for acceleration; 2 kHz for strain.
  - Observations: Peak mass-center acceleration 36.1 g; peak corner acceleration 52.4 g; DIC-measured inward deflection at the critical panel 2.9±0.1 mm. The strain rosette reported 1.8% equivalent strain at the toe region for a brief 0.5 ms window.
  - Model correlation: Simulated mass-center peak 35.4 g (−2.0%); corner peak 50.8 g (−3.1%); intrusion 2.78 mm (−4.1% vs DIC). The strain at the measurement point in the model (averaged over 2 mm) was 1.7% vs 1.8% test. Phase alignment within 0.3 ms. Residual dent shape agreed within ±0.2 mm across gauges.

- Quasi-Static Crush:
  - Configuration: Platen displacement to 15 mm at 1 mm/s. Bolt preloads verified with ultrasonic elongation (Sonelastic) at 14.6–16.3 kN range.
  - Measurements: LVDT mid-span deflection; strain around weld toe; load cell. Uncertainty: ±0.02 mm deflection, ±0.5% load.
  - Observations: Peak load 22.1 kN with mild nonlinearity past 10 mm travel. Averaged toe strain at 15 mm travel was 3.9%.
  - Model correlation: Predicted load 21.5 kN (−2.7%); mid-span deflection within 0.18 mm; averaged toe strain 3.8% (−2.6%).

These results support that the model reproduces the test response within measurement uncertainty and acceptable engineering margins for the specified use.

6.4 Input Data Pedigree and Calibration

- Materials:
  - 6061-T6 coupons (3 samples, flat tension, 4 mm thick) tested at 0.001/s and ~100/s with Split Hopkinson setup to estimate Johnson–Cook C. The adopted C = 0.015 lies between the measured 0.013–0.017. Full curves and calibration residuals in Appendix A.3.
  - Weld metal assumed at 0.92× base 6061-T6 yield based on microhardness HV0.5 mapping across three samples; ranges incorporated in sensitivity bands.
- Friction:
  - Static/dynamic friction coefficients between anodized aluminum coupon and broom-finished concrete measured via inclined plane; μd ~0.24±0.02. Baseline μ = 0.25; varied 0.20–0.30 in the study.
- Bolt preload:
  - Installation torque scatter converted to preload range using k-factor 0.20±0.02; validated via ultrasonic elongation on three specimens.

No empirical parameter was tuned to match test outcomes; ranges come from independent measurements and literature.

7. Sensitivity, Ranges, and Uncertainty Considerations

We explored the spread in outputs due to plausible variation in inputs via a hybrid approach: local one-at-a-time sweeps around the baseline and a 60-run Latin hypercube for the most influential three inputs. Inputs varied:
- μ (0.20–0.30)
- Weld strength scale (0.85–1.00 of baseline)
- Sheet thickness tolerances (cover 2.0±0.1 mm; base 3.0±0.1 mm)
- Bolt preload (13.5–16.5 kN)
- Johnson–Cook C (0.013–0.017)
- Mass distribution error in ballast (±2%)

Key findings:
- Drop intrusion sensitivity: μ had the largest effect; moving μ from 0.25 to 0.20 increased intrusion by 0.12 mm; to 0.30 reduced it by 0.09 mm. Thickness reduced/increased intrusion by ~0.06 mm per 0.1 mm thickness change in cover.
- Peak acceleration sensitivity: dominated by ballast mass distribution; ±2% inertia skew changed peak g by ±0.9 g.
- Crush toe strain sensitivity: weld strength scale had a near-linear impact; 0.85 scale increased average toe strain to 4.4%; 1.00 scale reduced to 3.5%. Bolt preload varied strain by ±0.1% absolute.

A simple additive error budget was constructed:
- Numerical resolution: based on mesh/time sensitivity, ±0.07 mm intrusion, ±0.2% toe strain.
- Material model: based on calibration residuals, ±0.05 mm intrusion, ±0.3% toe strain.
- Contact/friction: ±0.12 mm intrusion.
- Test measurement: ±0.1 mm DIC intrusion, ±0.5% load.

Combined (root-sum-square) predicted 95% uncertainty on intrusion is ~0.18 mm; on toe strain ~0.45% absolute in crush.

8. Applicability Envelope and Model Form Adequacy

- Valid scenarios: Drop heights up to 1.2 m onto concrete or steel plate; crush up to 25 kN; temperature 0–40 C; empty module with ballast representing cells (cell-level compliance not modeled).
- Out-of-envelope conditions: Drops onto highly compliant media (wood, dirt), elevated temperatures beyond 60 C (rate parameters change), presence of battery cells (changes internal stiffness and mass distribution), corrosion or weld defects beyond porosity Grade C.
- Physics completeness: The model includes large deformation, plasticity with modest rate effects, frictional impact, and contact separation. It excludes microcracking, anisotropy in the sheet due to rolling texture, and detailed weld metallurgy gradients. Given QOIs and comparison with tests, omissions are not decision-critical for this gate.

9. Evidence of Quality Controls and Traceability

- Versioning:
  - FE decks: Git LFS repo mech-bp/BME-DROP, commit 7d3c4a2 (tag R02). Change log lists geometry updates and parameter sets. Input and output files archived on SharePoint with immutable link IDs.
  - Software: Abaqus build 2024.HF2.145; run reports saved; environment file captured; seed for random number generator for Latin hypercube recorded.
- Pre- and post-processing:
  - Pre-processing steps scripted (Python 3.10, Abaqus Scripting Interface) with deterministic meshing seeds.
  - Post-processing via a validated pipeline using pyNastran/abaqus odbAccess; QOIs extracted by node sets named at CAD import to avoid redefinition drift.
- Data lineage:
  - Material tests: Lab notebook pages 17–24, Test IDs AL6061-RS01..RS03 (rates), AL6061-QS01..QS03 (quasi-static). Raw CSVs provided.
  - Instrument calibration certificates attached (Appendix A.4).

10. Independence and Peer Review

- Model build: Lead analyst P. Chen. Independent checker: L. Grady reviewed assumptions, inputs, math setup, and reran the drop case on a separate machine using the same commit (checksum verified). Results matched within 0.5% for intrusion and 0.6 g for peak g.
- External SME: Short consult with Prof. I. Narayan (impact mechanics) on friction modeling and use of contact damping; notes archived. No conflict of interest identified.

11. Results Summary

- Drop case (baseline):
  - Max wall intrusion 2.78 mm at the impacted corner panel.
  - Mass-center peak acceleration 35.4 g; corner peak 50.8 g.
  - Bolt axial loads peaked at 22.3 kN (fastener #4), 68% of proof load. No loss of preload predicted.
  - Energy check: At 10 ms, KE/IE = 2.9%; total energy drift <0.5%.

- Crush case (baseline):
  - Peak load 21.5 kN at 15 mm displacement.
  - Averaged equivalent plastic strain at weld toe 3.8%; submodel local maximum 4.1% with 2 mm averaging.
  - No elements exceeded critical plastic strain of 12%. Load path through ribs as expected; minor flange lip yielding near guides.

All acceptance thresholds met with margin:
- Intrusion 2.78 mm < 3.0 mm limit with ~0.18 mm uncertainty.
- Toe strain 3.8–4.1% < 5% limit, even at low weld strength scale of 0.85 the toe strain remained below 4.5%.
- Bolt forces <80% proof across all runs.

12. Limitations and Open Items

- Rate dependence parameters for 6061-T6 are based on limited SHPB data (n=3). More specimens at intermediate strain rates (10–50 1/s) would reduce model-form uncertainty for impact.
- Weld representation in the global model uses tied constraints. While conservative for load transfer, detailed local stress gradients rely on submodeling; complex multi-axis stress states in real weld roots are simplified.
- Concrete floor roughness and compliance variability were not characterized beyond Ra ~0.6 mm; nonuniform asperities can alter local friction transiently.
- Future work if design changes:
  - If cells are installed, include internal structures and foam pads; recalibrate acceptance metrics accordingly.
  - Elevated temperature drops (−20 to 60 C) may change rate sensitivity; add temperature-dependent parameters.
  - Expand Latin hypercube to include five inputs and 200 runs for more robust global sensitivity estimates if the envelope broadens.

13. Reproducibility Statements

- The entire workflow is scripted. Running python run_all.py —case drop —mesh 7mm reproduces the baseline drop case; a separate script run_submodel.py builds the weld-toe submodel from the global ODB automatically.
- Results in this report are traceable to commit 7d3c4a2. A digital fingerprint (SHA256) of the ODB files is stored in repo checksums.txt.
- A containerized environment (Singularity image abaqus2024hf2.sif with Python packages pinned) ensures consistent dependencies; image hash 5c1b7…9ad.

14. Decision and Credibility Assessment

Given:
- The numerical solution has been demonstrated stable and sufficiently resolved through mesh/time refinement and element sensitivity checks.
- Material, friction, and preload inputs are derived from measured data with documented uncertainties; no parameter fitting to tests was performed.
- The model predictions match independent laboratory measurements for both dynamic impact and static crush within pre-established tolerances.
- The workflow is traceable, repeatable, and reviewed by an independent analyst.

We assess that the model provides reliable evidence for the stated QOIs within the defined operating envelope. It is appropriate for design release Gate D decisions on the BME with respect to drop and crush performance. Use beyond the envelope (e.g., with cells installed, different surfaces, or higher temperatures) requires additional updates and checks.

15. References

- ES-5412 Rev C, “Battery Module Enclosure Structural Requirements.”
- DS-115 Rev B, “Drop Test Configuration for Enclosures.”
- VDI 2230, “Systematic Calculation of High Duty Bolts.”
- Johnson, G.R., and Cook, W.H., “A constitutive model and data for metals subjected to large strains, high strain rates and high temperatures,” 1983.
- Abaqus 2024 Documentation, Analysis User’s Guide and Verification Manual.

Appendices (in appendix.md):
- A.1 Mesh statistics and element quality metrics for each refinement.
- A.2 Test configuration diagrams and sensor layouts.
- A.3 Material test curves and calibration residual plots.
- A.4 Calibration certificates and equipment lists.
- A.5 Sensitivity study input matrix and output summaries.
