Title: Structural FEA Credibility Report — Avionics Tray and Bracket Assembly (Project Orion-SM Avionics Bay)

Revision: R0
Date: 2026-08-06
Analyst: L. Chen (Structures)
Tool: Abaqus/CAE and Abaqus/Standard 2022 HF3

1. Background

This report summarizes the finite-element modeling activities performed to estimate static stress and natural frequencies of the avionics tray for the Orion-SM small satellite bus. The assembly is a bent 5052-H32 aluminum sheet tray (2.5 mm nominal thickness) with four 7075-T6 corner brackets that interface to the primary structure via M4 fasteners (A286, rolled thread). The tray carries COTS avionics, but the payloads themselves are abstracted as lumped masses for the purposes of this study.

Intended use of the analysis:
- Demonstrate that the tray-bracket assembly meets quasi-static load and first-mode requirements to support a PDR-level design decision.
- Provide inputs for the vibration qualification plan (targeted clamp mass, shaker notch management).
- Identify high-risk features (sharp bends, countersinks, bolt pads) that may require design changes.

Acceptance targets for this phase:
- First bending mode of the mounted tray above 120 Hz in the out-of-plane direction (to avoid coupling with the vehicle’s first lateral mode).
- Under 20g equivalent static load in all three axes, computed von Mises stress in 5052-H32 below yield/1.25 and in 7075-T6 below yield/1.25. Localized stress in the first thread is not assessed at this stage.

No nonlinear drop event, fatigue, or acoustic loading is covered here; those will be addressed after CDR when detailed hardware (e.g., harness routing and fastener stack-ups) is frozen.

2. Model Description

Geometry and simplifications:
- The tray is modeled with the as-designed CAD from NX (rev F) excluding embossed logo features and minor fillets (radii < 0.3 mm). Flange bend radii (1.5 mm) are represented.
- Four corner brackets (7075-T6 machined) attach via M4 bolts and alignment pins. Threads are not modeled; the bolt clamping is represented as a pretension section in the shank with tied contact to washers.
- Avionics mass representation: Five distributed point masses (0.08–0.52 kg each) connected to the tray surface through rigid distributed couplings over the intended footprint.

Materials:
- 5052-H32 aluminum sheet: E = 71.7 GPa, ν = 0.33, ρ = 2680 kg/m^3, σy = 193 MPa. Sourced from MMPDS-17, table 3.1.1.0(b), with thickness-specific values near 2.5 mm.
- 7075-T6 bracket: E = 71.0 GPa, ν = 0.33, ρ = 2810 kg/m^3, σy = 503 MPa. MMPDS-17, table 3.2.1.0(c).
- A286 bolt: E = 196 GPa, ν = 0.30, ρ = 7850 kg/m^3.
- Friction coefficient at aluminum-aluminum interfaces assumed 0.20 (dry, cleaned), informed by MIL-HDBK-60.

Connections and restraints:
- Tray-to-bracket contact: surface-to-surface with small-sliding formulation, penalty normal, isotropic friction 0.20.
- Bolt preload: 3.5 kN each, applied via bolt load feature on shank sections, based on torque spec 2.8 N·m and k-factor 0.2.
- Boundary conditions: The four bracket base faces are constrained to represent the interface to the spacecraft panel using multi-point constraints to six reference points whose translational DOFs are fixed. This approximates a stiff base with negligible compliance relative to the tray.

Loading:
- Static: Body force to simulate 20g applied sequentially in +X, +Y, and +Z directions; the maximum stress across these is used for assessment.
- Modal: Unloaded except for pretension, contacts active.

3. Numerical Approach

Element formulation and mesh:
- The tray and brackets are meshed with 10-node quadratic tetrahedra (C3D10). Tray thickness is captured with at least three elements through thickness in flanges and two in the pan region; local mesh refinement near bolt pads and bend roots.
- Bolts are 1D beam elements (B31) with equivalent cross-section; heads/washers are represented as rigid surfaces tied to beam ends.
- Coarse/medium/fine meshes were generated to check stress and modal frequency stability. Element counts: 1.5e5, 4.1e5, 1.2e6, respectively.

Solver settings:
- Static step uses full Newton with automatic time stepping; nonlinear geometry on for bolt load introduction and frictional contact.
- Convergence tolerances tightened from default: residual force norm < 1e-5 of reference for the final increment; contact stabilization at 0.2% of average element stiffness used only during initial bolt closure.
- Eigensolver: Lanczos, 15 modes requested to 600 Hz.

Computing environment:
- Runs executed on a dual Xeon Gold 6330 system (2 sockets x 28 cores, 256 GB RAM). Abaqus/Standard 2022 HF3, parallel execution with 40 threads.

4. Reference Problems and Sanity Checks

To verify that the modeling approach behaves as expected, the following checks were performed prior to the production runs:
- Thin bracket bending (NAFEMS LE10-like plate): A 2 mm thick cantilever plate modeled with C3D10 achieved deflection within 0.8% of the handbook solution at medium mesh density, confirming element formulation is adequate for thin features when through-thickness discretization is respected.
- Bolt preload verification: Axial force in beams post-pretension matched input within 1.5% after a stabilization ramp, indicating the chosen application method is reliable for this assembly.

5. Mesh Refinement Results

We conducted a mesh refinement study focusing on:
- First out-of-plane natural frequency.
- Peak von Mises stress at the most critical region (outer bend root near bolt pad in +Z load).

Results:
- First mode frequency: 138.2 Hz (coarse), 144.9 Hz (medium), 147.0 Hz (fine). Change from medium to fine is 1.5%.
- Peak stress at hotspot under +Z 20g: 128 MPa (coarse), 141 MPa (medium), 146 MPa (fine). Change from medium to fine is 3.5%.

Assuming the fine mesh is near the asymptotic regime, the remaining discretization influence on the first mode is estimated around 1–2 Hz, and on the stress around 4–6 MPa at the hotspot. Stress contours away from the immediate notch show <1% change between medium and fine meshes.

Given turn-around needs for this phase, subsequent sensitivity work used the medium mesh. Final reported stresses and frequencies reference the fine mesh unless stated otherwise.

6. Model Correlation with Test

A bench-top modal survey was conducted on an engineering development unit (EDU) of the tray (rev E geometry, identical to rev F in stiffness-critical areas). The EDU was mounted to a granite table through a stiff adapter plate mimicking the spacecraft panel. Polytec PSV scanned the top surface; excitations applied via an instrumented impact hammer. Temperature 22±1°C.

Measured versus predicted (fine mesh, same boundary conditions, pretension included):
- Mode 1 (global bending, out-of-plane): Test 152 Hz, Model 147 Hz, difference -3.3%.
- Mode 2 (twist): Test 203 Hz, Model 197 Hz, difference -3.0%.
- Mode 3 (in-plane bending): Test 261 Hz, Model 268 Hz, difference +2.7%.

MAC values for the first three modes were 0.94, 0.91, and 0.88, respectively, indicating good agreement in mode shapes. Minor discrepancies are attributed to cable mass and damping tape present during the test that were not modeled.

No test data were available for static stresses; we rely on material property pedigree and connection modeling to bound static predictions.

7. Parameter Sensitivity

We examined the influence of key uncertain inputs on the response (medium mesh used for efficiency, spot-checked on fine for first-order consistency).

Parameters and ranges:
- Friction coefficient at aluminum-aluminum: 0.10–0.30.
- Bolt preload: ±15% around 3.5 kN to represent torque scatter.
- Tray thickness: ±0.10 mm manufacturing tolerance.

Observations:
- First out-of-plane mode varied from 143.8 to 146.1 Hz over the friction range (±0.8%). Preload changes had <0.5% effect on the same mode.
- Under +Z static load, peak von Mises at the bend root shifted from 138 MPa (μ=0.30, high preload) to 147 MPa (μ=0.10, low preload), roughly a 6.5% span. Tray thickness tolerance of ±0.10 mm adjusted the peak stress by ±4–5 MPa.
- Contact slip was confined under worst-case (μ=0.10, low preload) to a 0.04 mm relative displacement at one interface corner; no gross separation was observed.

8. Uncertainty Estimate for Static Stress

Without performing a full stochastic study, we approximated the combined effect of the three parameters above using a local linearization around the nominal point (μ=0.20, 3.5 kN, 2.50 mm). Sensitivities were computed by finite differences on the medium mesh and scaled for the fine-mesh mean. Assumed independent normal spreads:
- μ: mean 0.20, σ=0.05.
- Preload: mean 3.5 kN, σ=0.35 kN (≈10%).
- Thickness: mean 2.50 mm, σ=0.05 mm.

Propagation yields:
- Peak von Mises at hotspot under +Z: mean ≈ 142 MPa, standard deviation ≈ 6 MPa. A 95% coverage (≈mean ± 2σ) lies between 130 and 154 MPa. This range aligns with the mesh refinement estimate of residual numerical influence (a few MPa), giving confidence that discretization and input variability are similar order near the limit state.

9. Results and Assessment

9.1 Modal requirement
- Fine mesh prediction: First out-of-plane bending = 147.0 Hz. Adjusting to account for mesh influence (+1–2 Hz) and test correlation bias (+3.3%), the expected as-built frequency is around 150–152 Hz. Requirement (≥120 Hz) is comfortably met with >25% headroom.

9.2 Static requirement
- Fine mesh, +Z 20g load: Peak von Mises in 5052-H32 occurs at the outer bend root near a bolt pad, 146 MPa.
- Allowable for 5052-H32 at PDR: σy/1.25 = 193/1.25 = 154.4 MPa.
- Nominal margin = (154.4 − 146)/154.4 ≈ 0.054 (5.4%). Considering the ±2σ upper bound of 154 MPa from the local variation estimate, the margin can be near zero in worst plausible conditions. This suggests tightening torque scatter and/or adding a small radius relief could be prudent.

- Stresses in 7075-T6 brackets remained below 230 MPa at all locations, vs allowable 503/1.25 = 402 MPa; margin >40%. Bolts experience peak axial in the 2.9–3.1 kN range post-load; combined with shear, they remain below typical joint task force limits for A286 at room temperature.

- No plasticity model was used; evaluation is strictly elastic.

9.3 Contact behavior
- With μ=0.20, no gross slip was observed at any interface under 20g in any direction; relative tangential movement remained under 0.015 mm at load completion for nominal preload. Normal contact pressures are well distributed, with concentrations near bolt pads as expected.

10. Documentation and Traceability

Model files and scripts are stored in the team Git repository (Orion-Structures/FEA/TrayBracketPDR). Key artifacts:
- CAD import and clean-up: tray_revF_clean.x_t, brackets_revB.step.
- Abaqus input: tray_brkt_PDR_fine.inp, tray_brkt_PDR_med.inp.
- Load cases: lc_static_XY Z.inc, lc_modal.inc.
- Contact and pretension setup documented in setup_notes.md.
- Commit hash for the run set used in this report: 7f32c9a (tag v0.9-PDR).
- All results generated using run script run_tray_pdr.py with environment check logging solver version and thread count.

A second analyst (J. Patel) performed a checklist-based deck review focusing on boundary conditions, units, and material assignments. Issues found (a mis-assigned ν on bolts and a reversed MPC direction at one bracket) were corrected and rerun prior to finalization.

11. Credibility Considerations

Strengths of the current evidence:
- The mesh density study demonstrates that both first-mode frequency and the critical stress are approaching stability with refinement. The medium-to-fine change is within 3.5% for stress and 1.5% for frequency, indicating solution quality is not dominated by discretization artifacts.
- Agreement with a shop-floor modal tap test (within 3% on frequencies, MAC >0.88 for the first three modes) increases confidence in the structural stiffness representation of the tray and bracket features, as well as in the boundary realism of the support.
- Material properties are drawn from an industry-accepted compendium and apply to the thickness range in question, reducing doubt on elastic predictions.
- Contact and bolt modeling choices were prodded with parameter sweeps; the spread in static response remained within a manageable band. The first mode is especially insensitive to joint friction, which is favorable for requirement compliance.
- The modeling workflow is repeatable; solver version, hardware, and scripts are fixed and recorded. Deck review by an independent analyst reduced the chance of unit errors or oversight in BCs.

Areas that diminish confidence or require caution:
- The static stress outcome is close to the allowable when taking into account a plausible spread in joint parameters and thickness; small changes in geometry (e.g., a tighter bend radius due to manufacturing) could nudge the max stress upward.
- The use of 3D solid tets for a mainly sheet-metal component does capture through-thickness behavior but increases sensitivity to local mesh density around tight radii. Absent feature-specific plasticity or notch fatigue evaluation, local peak stresses should be interpreted carefully.
- The EDU modal correlation is on a near-identical but not identical revision (rev E vs rev F). While stiffness-critical features match, changes in minor cutouts and harness clip bosses were not tested. We mitigated this risk by re-running modal with mass attachments; however, a dedicated correlation on the flight-like unit would be preferred.

12. Limitations and Next Steps

Out of scope for this report:
- No drop impact, shock response spectrum, or random vibration response computations are included. A future campaign will address these with transient dynamics and frequency response analyses.
- Joint micro-slip energy dissipation and potential wear or fretting are not modeled.
- Plastic deformation is not considered; allowables are applied in a strictly elastic evaluation. If future analyses show margins eroding, elasto-plastic modeling at the bend root may be needed to check localized yielding implications.
- Thermal preload variation and CTE mismatch effects were not included; for the current room-temperature requirement, this is acceptable.

Planned follow-on:
- Small geometry change to the critical bend: introduce a 0.5 mm radius relief and widen the flange by 2 mm in the vicinity of the bolt pad. Re-evaluate stress and margin with the same mesh protocol.
- Tighten controls on torque application in the assembly procedure (e.g., lubricated threads with known k-factor or direct tensioning) to reduce preload scatter.
- Conduct a higher-fidelity modal test on the rev F tray with avionics dummies installed to refine the first three modes and verify support representation.

13. Conclusions

- The modal target is exceeded with comfortable margin. Prediction and measured data are in good alignment, supporting the credibility of the stiffness representation and boundary conditions.
- Static stress in the 5052-H32 tray under 20g worst-case is below the PDR allowable with a nominal 5–6% margin. Considering parameter variability and residual numerical influences, the worst plausible value approaches the allowable. Design tweaks and assembly process controls are recommended to increase robustness ahead of CDR.
- The analysis model, solver configuration, and results are documented and reproducible. Benchmark checks and peer review were conducted. While not every aspect of the final verification and validation campaign is complete at this stage, the evidence assembled here is suitable for PDR decisions on geometry changes and test planning.

Appendix: Key Numbers (for quick reference)
- First mode (fine): 147.0 Hz (MAC 0.94 vs test mode)
- Peak von Mises at bend root under +Z 20g (fine): 146 MPa
- Allowable 5052-H32 (yield/1.25): 154.4 MPa
- Sensitivity band for peak stress (95%): 130–154 MPa
- Mesh change (medium→fine): stress +3.5%, mode +1.5%
- Friction range effect on peak stress: ~6.5%
- Bolt preload target: 3.5 kN (±15% explored)

End of report.
