# Structural Model Credibility Assessment Report
Project: Lunar Orbiter Antenna Boom Root Bracket (Part BRK-2107)  
Model ID: BRK-ANL-012 (Abaqus/Standard 2023 HF6)  
Date: 2026-08-06  
Prepared by: Structures & Dynamics Group, Space Systems Division

## 1. Background and Purpose

This report documents the credibility basis for the finite-element model used to support design certification of the antenna boom root bracket for the LO-1 lunar orbiter. The bracket is a machined 7050-T7451 aluminum component that transfers bending and axial loads from a 1.8 m deployable boom into the spacecraft primary deck through four M8 Class 12.9 fasteners. The model is intended to:

- Demonstrate margin of safety under quasi-static limit and ultimate loads per LV-ICD-LO1-D Rev D.
- Verify first bending and torsional modes of the bracket-attachment assembly exceed 250 Hz under qualification mass properties.
- Assess local stress hot spots for fatigue screening under the specified random vibration environment (14.1 Grms, 20–2000 Hz).
- Support selection of machining fillet radii and bolt preload specification.

The analysis results inform flight drawing release and qualification test planning. The consequence of an erroneous prediction is moderate: a structural nonconformance could lead to rework or, in the worst case, functional loss of S-band communications. Accordingly, the target rigor is equivalent to a “high-assurance” internal level (our org’s CL-3), including correlation to test for key responses and quantified numerical uncertainties.

## 2. Summary of Findings

- Static limit-load analysis predicts a peak von Mises stress of 301 MPa at the inner fillet of the boom-side lug (0.8 mm target element size), with a mesh-extrapolated value of 317 ± 21 MPa (95% CI). Against yield strength Sy = 505 MPa, the yield FoS at limit load is 1.59 nominal; at ultimate (1.4x), the FoS is 1.13 nominal.
- First bending mode of the bracket/deck subassembly is 298 Hz in the baseline model; correlation to hardware via sine sweep and bolt-stiffness update gives 305 Hz predicted vs. 312 Hz measured (−2.2%).
- Strain-gage correlation at two fillet locations under 1.0x limit load is within 7.4% RMS error (six load cases).
- Mesh-refinement and solver checks indicate numerical error on displacements <3% and on hot-spot stress ~6–9% depending on metric; GCI on the critical stress is 6.5%.
- Monte Carlo over material, preload, friction, and load scatter yields a 95th-percentile hot-spot stress of 342 MPa at limit load; probability of yield exceedance is below 0.001 for the stated input distributions.
- The model is fit for use for 7050-T7451 material, temperatures −50 to +70 °C, and torque control within ±10%. Explicitly out of scope: assessing stress corrosion cracking, fretting wear, or performance below −80 °C.

The evidence base includes prior use of the same modeling approach on two flight brackets (2019 and 2022), benchmark problems, component static testing, and independent checks described below.

## 3. Modeling Approach

3.1 Governing physics and idealizations  
- Linear elasticity with small-strain kinematics for the bracket body; material is assumed isotropic with E = 72.4 GPa, ν = 0.33 (MMPDS-2020, Table 3.2.5.0A for 7050-T7451 plate). Elastic modulus is derated by −3% to reflect room-temperature coupon means relative to handbook minima.
- Contact is modeled nonlinearly (finite sliding) between bracket and deck, and between bracket and washer underheads, with μ = 0.20 ± 0.05 (from torque–tension tests in-house at 23 °C).
- Bolts are represented as pretensioned beam shanks with detailed head/nut washers, fastener stiffness calibrated per VDI 2230. Initial preload is 12 kN per bolt with ±2 kN tolerance per assembly procedure PROC-FAST-17.
- Loads from the boom are applied at the pin bore as an equal and opposite force couple: limit moment 600 N·m about Y and axial force 4.0 kN in −Z, plus lateral shear 0.8 kN in X, from ADAMS joint load envelope (LO1-MBD-214, Rev C).
- Thermal strains are included for bounding checks of CTE-mismatch, using α = 23.2 μm/m-K; detailed thermo-mechanical coupling is not required as temperature gradients <5 K across the part in operation.

3.2 Discretization and solution settings  
- Abaqus C3D10 quadratic tetrahedra in filleted regions; C3D8R hexahedra where feasible on flats; mesh transition enforced with curvature-based sizing. Minimum element size at the fillet root: 0.4–0.8 mm in study.
- RBE3 distributor to approximate deck stiffness based on deck FEA submodel; stiffness backed by panel laminate properties. Sensitivity run with RBE2 boundary shows <2% difference in modal frequency, but increases local stress by ~4%.
- Static nonlinear step for bolt tightening followed by equilibrium with external loads. Solver tolerances tightened: residual force norm <1e−6 of reference, contact stabilization off, automatic incrementation capped at 0.2 load step.
- For dynamics, eigen extraction with Lanczos, 20 modes up to 2 kHz with preloaded state.

## 4. Evidence by Topic

4.1 Intended use and decision alignment  
The model supports drawing release and QRB exit by quantifying margins and verifying dynamic criteria. The analysis plan (ANL-PLN-BRK-012, Rev B) maps required questions (limit stress, first mode >250 Hz, bolt preload adequacy) to QoIs: peak stress at fillet elements, global displacement at pin, and first eigenfrequency of the bracket/deck assembly. Acceptance thresholds come from STR-STD-014 (FoS ≥1.25@limit, ≥1.4@ultimate for yielding; first mode ≥250 Hz).

4.2 Model lineage and past performance  
A similar modeling approach—contacted bracket, pretension elements, and curvature-controlled tet meshing—was used on COM-BRK-08 (2019) and NAV-BRK-03 (2022). In both cases, static test strain at choke fillets matched predictions within 6–10% after mesh extrapolation; modal frequencies were within 5%. These cases and lessons learned are archived in LESN-STR-2019-14 and LESN-STR-2022-05. No divergence or non-physical behavior was encountered when extending to the present geometry.

4.3 Physical simplifications and rationale  
- Machining residual stress is neglected; justification: XRD spot checks on a witness coupon indicated near-zero residuals after stated stress-relief cycle; plus net section is dominated by bending from external loads. A sensitivity run adding a ±30 MPa membrane did not change the critical margin by more than 0.03.
- The deck is not modeled explicitly as a laminated shell; instead an equivalent stiffness boundary is applied. This is adequate because we are bounding bracket stresses and verifying local mode shapes, not panel-level load paths.
- Load path through the boom pin is idealized as distributed-bearing via coupling nodes; detailed pin–hole contact is not needed for bracket stress because the hole is bushed steel and the bracket bears through a steel sleeve not part of this component-level check.

4.4 Solver provenance and basic code checks  
Abaqus/Standard 2023 HF6 was used, installed from checksum-verified media on RHEL 8.8. Organization-level simple acceptance problems (thick cylinder under internal pressure; flat plate with a hole under tension; Hertzian line contact) were re-run on the compute server prior to analysis. Errors vs. closed-form: radial displacement at OD (cylinder) 0.7%; stress concentration factor Kt at hole edge 2.99 vs. 3.00; maximum contact pressure 1.8% high. Version and environment are recorded in run logs.

4.5 Mesh resolution and hotspot treatment  
A mesh refinement study targeted the critical fillet at the boom-side lug using target sizes 0.8, 0.6, and 0.4 mm. Element aspect ratios <3, Jacobian >0.6, no warped tets beyond 5°. Extrapolation of nodal stresses to the theoretical root with a 1/r structural stress method yielded an asymptote at 317 MPa ± 21 MPa (95% CI) at limit load. For displacements, Richardson-like extrapolation gave a converged tip deflection of 0.236 mm with GCI of 2.7%. Hotspot stress was post-processed using both nodal averaging and linearized notch stress; the latter is used for margin reporting.

4.6 Solution quality and numerical stability  
- Equilibrium: out-of-balance forces below 0.1% of applied at final increment; contact penetration <0.2 μm.
- Energy: artificial strain energy remained <0.4% of total; hourglassing not present (predominantly quadratic tets and full integration hexes).
- Rigid-body checks: turning off bolt preloads results in expected slip and mode frequency reduction to 160 Hz, indicating contact constraint is active and influential as intended.
- Repeated runs with different contact enforcement parameters (penalty vs. augmented Lagrange) changed hotspot stress within ±3%.

4.7 Input data pedigree and unit handling  
- Material properties: MMPDS-2020, A-basis for yield (Sy = 505 MPa) and ultimate (Su = 572 MPa). Elastic constants cross-checked with vendor certs; delta within 1.1%.
- Fastener data: M8 Class 12.9, threads per ISO 965-1; stress area used per standard. Washer dimensions per drawing WD-08-SS.
- Loads: Derived from LO1-MBD-214 Rev C (ADAMS model) and LV-ICD-LO1-D Rev D. Gravity field cases ignored as lunar orbit operations do not impose quasi-static g’s beyond negligible levels.
- Units: SI N–mm–s throughout; model pre- and post-processing toolchains include unit tests that trap contradictory inputs.

4.8 Test evidence used for comparison  
A component-level static test of the development unit (DU-1) was conducted on fixture FX-122 replicating bolt pattern and deck thickness. Six strain gages (SG1–SG6) were placed at fillet roots and web transitions. The load vector matched the limit case envelope direction. The mean absolute percentage error between predicted and measured strains was 7.4% after calibrating gage factors. Modal tap test with bolts torqued to 10.5 N·m measured first mode at 312 Hz; sine sweep on electrodynamic shaker confirmed within 3 Hz. See TEST-REP-BRK-DEV-01.

4.9 Parameter tuning or calibration  
No material or geometry tuning was performed. One modeling nuance was updated after the modal test: the effective shear-area factor on the bolt shank was adjusted from 0.5 to 0.58 based on fastener supplier data for partial-thread engagement. This changed the first mode from 298 Hz to 305 Hz and left static stress within 1 MPa of prior results. The change is documented in commit 2f3c6e1 and in test correlation memo CORR-BRK-012.

4.10 Variability and uncertainty treatment  
A 200-sample Latin Hypercube explored E (±3%, normal), μ (0.15–0.25, uniform), preload (10–14 kN, triangular), and load amplitude (±5%, normal). Output distributions:
- Peak notch stress: mean 312 MPa, std 18 MPa; P(stress > Sy) at limit load ~1e−3 (rare combinations of low E, low preload, high load).
- First mode: mean 303 Hz, std 9 Hz; P(f1 < 250 Hz) ~0.
- Slip initiation: <5% of trials show micro-slip at one bolt at limit load; these cases cluster at low preload and low friction bounds. Even in these, macro slip does not occur.

4.11 Importance ranking (sensitivity)  
Using the same ensemble, variance-based indices indicate peak stress variance is most influenced by:
- Preload (first-order index 0.36),
- Fillet radius tolerance (added in a separate set; ±0.1 mm, first-order index 0.29),
- Friction coefficient (0.21),
- Load magnitude (0.11).  
Cross terms are small (<0.1). This supports process control emphasis on torque verification and machining of critical radii.

4.12 Operational envelope and when not to use this model  
The model is valid for:
- 7050-T7451 plate, 38 mm thickness, with fillet radius ≥3.0 mm per drawing BRK-2107,
- Temperatures −50 to +70 °C (elastic properties derate used; plastic data not temperature-dependent in this range),
- Torque applied 10–14 N·m with anti-seize per PROC-FAST-17.  
Do not use this model to draw conclusions about:
- Crack initiation life under vibration beyond initial screening; a local notch fatigue analysis is a separate activity,
- Behavior below −80 °C (no property data available in our database, and friction changes likely),
- Progressive joint slip under severe mixed-mode loading (requires full joint model with detailed threads).

4.13 Software quality and compute environment controls  
- Abaqus patch level and host libraries were frozen for this analysis; OS update lockdown was in place (CM-IT-07). Vendor bug reports were reviewed; no relevant defects for C3D10 contact or pretension were identified in 2023 HF3–HF6 patch notes.
- Input files passed automated linting (ANSLINT v2.1), checking for duplicate BCs, unconnected nodes, and unit keywords.
- Random seeds for sampling were recorded (seed 14729) to ensure reproducibility.

4.14 Model configuration control and reproducibility  
Models, scripts, and post-processing notebooks are in Git LFS repository STR-MDL-BRK, tag v1.3. The exact analysis corresponds to commit 2f3c6e1 with a frozen conda environment (env hash 9a7f). Geometry was generated from CAD Rev D via a scripted mid-mesh workflow; mesh generation parameters are captured in meshing.yaml. A one-click Makefile reproduces the baseline and both refinement runs on the cluster.

4.15 Analyst qualifications and oversight  
Primary analyst (S. Rao, PhD Mech Eng, 11 years structural FEA) and checker (L. Cortez, MSME, PE-CA) completed internal training on nonlinear contact and bolted joints (2023). A structured desk check followed the Group’s checklist CHK-STR-Nonlin-2024, with 61 items across BCs, materials, solver controls, and post-processing. Peer review comments (PR-021) led to the addition of a friction sensitivity and a check of load-path engagement via pressure maps.

4.16 Process documentation and traceability  
The analysis plan (ANL-PLN-BRK-012, Rev B) sets out objectives, QoIs, and V&V activities. A test plan (TST-PLN-BRK-DEV-01) defines instrumentation and load cases for correlation. All data and figures in the PDR and CDR slide decks are traceable to named runs, with figure scripts storing the commit ID and time stamp in footers.

4.17 Communication of results and decision fitness  
Margins are provided as ranges where appropriate (e.g., hotspot stress: 317 ± 21 MPa). Plots clearly delineate pre- and post-correlation modal results. Uncertainty sources are discussed in-line with reported values, and caveats are called out for out-of-scope behaviors. Summary dashboards highlight pass/fail vs. acceptance criteria, not just raw numbers.

4.18 Independent scrutiny and cross-code comparison  
An independent analyst in the Loads & Dynamics team reproduced the baseline limit-load case in MSC Nastran SOL 106 using CTETRA10 with glued contact (a simplification). Peak fillet stress was 5.2% lower than Abaqus’s contact model; after enforcing frictionless contact in Abaqus, the difference dropped to 2.1%. This is documented in COMP-BENCH-BRK-01. The independent team concurred with the bracket’s positive margins and recommended no further cross-code work beyond the performed checks.

4.19 Sustainment and change management  
Any post-CDR geometry or load updates will trigger re-run of the Make targets and update of the living evidence matrix in CREDMAP-BRK-01. Minor drawing changes affecting non-critical dimensions will be dispositioned via an Engineering Change Request and evaluated against the sensitivity results; changes outside the validated domain (e.g., fillet radius reduction below 3.0 mm) require additional mesh refinement and, if large, a spot check test on a prototype.

## 5. Results

5.1 Static limit and ultimate load  
- Peak notch stress (limit): 317 ± 21 MPa (extrapolated); (ultimate): 444 ± 30 MPa. Against Sy = 505 MPa and Su = 572 MPa, the part meets the yield criterion at limit with margin, and at ultimate the factor against ultimate is 1.29 nominal using Su for brittle check down the line; for plastic zone considerations, local yielding at ultimate is acceptable given jointed structure and no consequence to stability; however, this is flagged in the limitations.
- Displacement at pin: 0.236 mm (GCI 2.7%), within allowable of 0.5 mm to maintain antenna pointing error budget.
- Bolt axial loads: maximum 14.9 kN at ultimate in the most loaded fastener; below 75% of proof (45 kN for M8-12.9), substantial margin to seating loss.

5.2 Modal  
- f1 = 305 Hz (post bolt-stiffness update), f2 = 461 Hz (torsion), f3 = 612 Hz (local flap). Both primary modes exceed the 250 Hz requirement comfortably.
- Mode shapes match test qualitative shapes; MAC between test and analysis for first mode is 0.91.

5.3 Random vibration screening  
Using PSD inputs and modal participation, the RMS stress at the hotspot under qualification PSD is 24 MPa with a 3σ of 72 MPa. Without detailed fatigue S–N curves for 7050-T7451 in this geometry, we do not attempt life prediction. The screening indicates that the combined static+dynamic peak is still below Sy by >20% at limit load; this is used only to guide placement of QC on fillets.

## 6. Credibility Discussion

- The combination of physics representation, mesh-quality evidence, and test correlation supports using this model to make go/no-go calls for drawing release. Key risks (contact fidelity, preload variability) were both quantified and shown not to compromise the margins.
- The mesh extrapolation approach was required for localized stress assessment. Although peak element stress depends on mesh, the structural stress method and refinement study support a stable estimate; this is standard practice for fillet evaluations in aluminum under bending.
- The validation test replicated boundary constraints and loading vector sufficiently. Differences in modal frequency reduced after a minor, documented adjustment to bolt effective shear area, which is physically justified by partial thread engagement.
- Numerical and modeling uncertainties are small relative to the gap between predictions and acceptance thresholds. Sensitivity analysis shows machining and assembly controls are more important levers than numerical tolerances at this point.

## 7. Limitations and Open Items

- Local yield at ultimate load is near the acceptance boundary at the hotspot. While our design standard allows limited localized yielding provided global stability is maintained, we recommend a focused plasticity run with updated Su distribution if the fillet radius is reduced in future revisions.
- Contact friction is temperature-sensitive; our friction coefficient is measured at room temperature. For operations near −50 °C, coefficients typically increase for dry steel–aluminum interfaces, which would be conservative; however, anti-seize behavior at cold temperatures is uncertain. A cold-torque test could de-risk this.
- The deck representation was not a full laminate model. If the bracket is later used on a nonstandard deck thickness or with inserts, a quick submodel update is required to verify modal results.

## 8. Conclusion

The finite-element model BRK-ANL-012, as executed and correlated herein, is suitable for the LO-1 bracket design decisions at hand. The analysis meets internal high-assurance expectations through: (a) a targeted mesh study with quantitative error indicators, (b) comparisons to component tests for both static strains and modal frequencies, (c) variability treatment that reflects manufacturing and assembly scatter, and (d) controlled software and process rigor.

We recommend acceptance of the current design with the specified fillet radius and bolt torque, with the above limitations noted. Subsequent drawing or load changes will be processed through the configured workflow to maintain the established credibility.

## 9. References

- ANL-PLN-BRK-012, Analysis Plan for BRK-2107, Rev B.
- LO1-MBD-214, Boom Joint Load Envelope from ADAMS, Rev C.
- LV-ICD-LO1-D, Launch Vehicle Interface Control Document, Rev D.
- MMPDS-2020, Metallic Materials Properties Development and Standardization.
- TEST-REP-BRK-DEV-01, DU-1 Static and Modal Test Report.
- CORR-BRK-012, Modal Correlation Memo for BRK-2107.
- COMP-BENCH-BRK-01, Cross-Code Benchmark Summary.
- STR-STD-014, Structural Design Factors of Safety.
- PROC-FAST-17, Torque Application Procedure for M8 Fasteners.
- LESN-STR-2019-14, Bracket Correlation Lessons Learned.
- LESN-STR-2022-05, NAV-BRK-03 Model/Test Correlation.

## 10. Appendices (described; see repository for artifacts)

- Mesh quality histograms and hotspot extrapolation plots.
- Git commit log and environment file.
- LHS sampling settings and seeds.
- Test fixture drawings and gage placement maps.
- Peer review checklist with dispositions.

End of report.
