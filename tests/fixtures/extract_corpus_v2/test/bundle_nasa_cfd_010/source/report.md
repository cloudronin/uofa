# CFD Credibility Assessment Report — S‑Duct Inlet Distortion Study

Project: Raven S‑Duct Intake for Modular Fan-in-Wing Demonstrator  
Prepared by: Propulsion Aerodynamics Group  
Date: 2026‑07‑29

## 1. Background

We are supporting the preliminary design cycle for the Raven fan-in-wing demonstrator by predicting total pressure recovery and circumferential distortion at the aerodynamics interface plane (AIP) of a tight-radius S‑duct. The intake is expected to operate between Mach 0.16–0.42 with incidence up to 10 degrees. The primary decision user is the inlet design IPT; these results will be used to select a vane package and to set a not-to-exceed distortion envelope for fan operability assessments.

For this phase, the questions we must answer are:
- Does the baseline geometry meet a minimum area-averaged total pressure recovery of 0.965 across the speed range at nominal incidence?
- What is the expected 60-degree sector distortion (DC60) at the AIP for ±6 degrees incidence?
- How sensitive are these predictions to the turbulence closure and modest changes in upstream total pressure?

The present report summarizes the modeling approach, numerical setup, comparisons to subscale measurements, and our judgment on how much weight to place on the predictions for downselect decisions in M3.

Out of scope for M3 are acoustics, broadband fan‑tone interactions, and cross-code comparisons; these will be addressed as resources permit in later phases.

## 2. Modeling Approach

We used Siemens STAR‑CCM+ 2023.3 in double precision with the coupled density-based solver for compressible RANS. The working fluid is air treated as an ideal gas with Sutherland viscosity. Turbulence closure is Menter’s SST k‑ω with shear stress transport; for a sensitivity check, we also evaluated Spalart‑Allmaras (SA) on the medium grid for the baseline incidence case.

Rationale for physics choices:
- Operating Reynolds numbers (based on inlet diameter) are O(3×10^6–8×10^6). Attached turbulent boundary layers with local separation in the inner bend are expected; SST’s enhanced adverse pressure gradient handling is generally appropriate for this regime.
- Transition is handled as fully turbulent. A short test with empirical inlet roughness forcing did not materially change AIP metrics (<0.2% in recovery) and was not pursued further.

The geometry includes the external capture lip, inner and outer bends, a short choke, and a 0.3D axial run to the AIP. The fan and any inlet guide vanes are omitted for this task; the AIP is modeled as a planar station downstream of the last geometric feature.

## 3. Computational Mesh and Numerics

We generated polyhedral volume meshes with prism layers grown from all walls to achieve y+ ≈ 1 at cruise and y+ < 2 at low speed. The near-wall region used 25 layers with first cell height 12 µm, total thickness ~3.5 mm, and a growth rate of 1.2. Wake refinement boxes and curvature-based refinement were applied in the inner-bend separation-prone region.

Three systematically refined meshes were used for grid sensitivity of the primary metrics (AIP area-averaged Pt/Pt0 and DC60):
- Coarse: 6.1 million cells
- Medium: 12.7 million cells
- Fine: 25.4 million cells

Numerical details:
- Spatial discretization: second-order upwind for convective fluxes; second-order central for viscous terms.
- Temporal: steady-state solver with pseudo-time stepping; a follow-on unsteady run (URANS, dual-time stepping, 2000 iterations) was executed for one case to check for large-scale unsteadiness.
- Convergence criteria: density and momentum residuals reduced by at least 4 orders of magnitude from start and leveled; mass imbalance < 0.1%; AIP recovery and DC60 monitors flat to <0.05% over the last 500 iterations.

Grid convergence index (GCI):
- The refinement ratio between coarse→medium and medium→fine was ~1.45–1.52 depending on local refinement.
- For the M=0.35, α=0° case with SST, the extrapolated recovery (Richardson) was 0.973 with GCI of 0.36% (medium→fine) at 95% confidence, assuming observed order p ≈ 1.89. DC60 exhibited a larger GCI of 6.2% relative due to sectorwise gradients.

The URANS spot check at M=0.35, α=6° with SST showed low-amplitude unsteadiness in the inner-bend separation bubble (dominant Strouhal ~0.23 based on duct diameter), but time-averaged AIP metrics differed from steady RANS by <0.3%. We conclude steady RANS is sufficient for mean distortion metrics in this envelope.

## 4. Boundary Conditions and Input Pedigree

- Inlet boundary: Stagnation pressure/temperature specified based on wind‑tunnel plenum data files. For the primary validation runs, Pt0 was set between 101.3–116.8 kPa and Tt0 between 295–305 K, matching the facility schedule. Turbulence intensity 1.0% and turbulent length scale 1 cm were applied at the inlet plane.
- Outlet boundary (AIP): Static pressure adjusted to achieve the target mass flow from the test matrix within ±0.2%; solver used a back-pressure boundary with specified target.
- Walls: no‑slip, adiabatic.

Geometry inputs came from the CAD released as Raven Inlet Rev D‑3 (dated 2026‑05‑13). We checked the CAD against the as‑built wind‑tunnel model by overlaying measured station diameters (six stations, ±0.15 mm tolerance). Maximum deviation was 0.12 mm at the inner bend; we judged the model fidelity acceptable.

Upstream gas properties were derived from tunnel instrumentation with NIST traceable calibrations (certificates dated 2026‑03). The total pressure perturbation at the plenum was independently recorded by two Baratron transducers; observed differences were within ±0.25 kPa.

Sensitivity to input variations:
- A ±1% change in Pt0 altered AIP recovery by ±0.8% absolute and DC60 by ±3% relative on the medium grid with SST.
- Doubling the inlet turbulence intensity to 2% changed recovery by +0.1% and DC60 by −0.6% relative; thus the metrics are weakly sensitive to the assumed free-stream turbulence, given our current wall treatment and Reynolds numbers.

## 5. Reference Data for Comparison

Validation leveraged a subscale wind‑tunnel campaign conducted at the University of Maryland Low Speed Tunnel (UMD LST) under Task Order RT‑2204. The same Rev D‑3 geometry was tested at three speeds (M=0.2, 0.3, 0.4) and three angles of attack (α=0°, +6°, −6°). Measurements included:
- AIP rake: a 12‑rake array with four Kiel probes per rake, equally spaced around the circumference, located 0.3D downstream of the inner bend exit. Each probe recorded total pressure at 500 Hz.
- Wall static pressure taps: 42 taps along the inner and outer walls.
- Flow angularity at the AIP via a 5‑hole probe at four circumferential positions for α=0° and +6°.

Test data processing details:
- Each point was averaged over 30 s records after steady tunnel conditions were reached.
- Facility uncertainties: Pt measurement ±0.5% (95%); tap positioning ±0.25 mm; incidence accuracy ±0.2°.
- The AIP sector metrics used the SAE ARP1420B algorithm to compute DC60; we adopted the same approach in post‑processing the CFD fields by interpolating to the rake positions and sectors.

The wall tap data were primarily used as a qualitative check on pressure recovery distribution through the bend; quantitative comparison efforts focused on AIP recovery and DC60.

## 6. Results

6.1 Area‑averaged recovery (AIP)

- At M=0.2, α=0°: CFD (SST, fine grid) predicted 0.976; test average 0.974; difference +0.002 (absolute).
- At M=0.3, α=0°: CFD 0.973; test 0.969; difference +0.004.
- At M=0.4, α=0°: CFD 0.966; test 0.960; difference +0.006.

Across incidence:
- M=0.35, α=+6°: CFD 0.963; test 0.958; difference +0.005.
- M=0.35, α=−6°: CFD 0.971; test 0.967; difference +0.004.

Trendwise, CFD slightly overpredicts recovery at higher speeds and positive incidence. The residual bias is within the combination of mesh uncertainty (GCI ~0.4–0.7%) and facility Pt uncertainty (0.5%).

6.2 DC60 distortion

- M=0.3, α=0°: CFD (SST, fine) DC60 = 0.033; test 0.029; +14% relative.
- M=0.3, α=+6°: CFD 0.071; test 0.062; +15% relative.
- M=0.3, α=−6°: CFD 0.045; test 0.041; +10% relative.

The circumferential pattern of low‑recovery sectors in CFD aligns with the rakes in phase and location, but the magnitude is overpredicted. Switching to SA on the medium grid reduced DC60 by 6–8% relative while slightly degrading recovery (−0.1 to −0.2% absolute). Given the GCI on DC60 and the turbulence model sensitivity, the current best estimate remains slightly conservative relative to test.

6.3 Wall static pressure

The pressure coefficient distribution along the inner bend shows the correct adverse gradient and recovery region. The worst point‑wise difference in Cp was 0.037 at the separation onset station for M=0.35, α=+6°. Outer wall distributions matched within ±0.02 Cp for most stations.

6.4 Robustness to numerical settings

- Reducing under‑relaxation for turbulence from default to 0.3 and switching convective flux limiter to a more dissipative scheme altered DC60 by <3% relative on the medium grid; recovery changed by <0.2% absolute.
- Increasing prism layers from 25 to 35 at constant total cells made negligible difference in AIP metrics (<0.1% absolute), indicating boundary layer resolution is in a satisfactory regime for these outputs.

## 7. Confidence Considerations

7.1 Suitability for the stated question

The analysis targets mean pressure recovery and sector distortion at the AIP for a single duct geometry. The modeled physics (compressible steady RANS with SST) are appropriate for mean flow separation and diffusion in subsonic S‑ducts. The outputs align with the data collected in the wind‑tunnel campaign (AIP pressures and wall taps), providing a like‑for‑like comparison.

7.2 Numerical convergence and discretization

We conducted a mesh refinement study with three systematically refined grids and reported GCI for both AIP recovery and DC60. The primary decision metric (recovery) is well‑behaved with low GCI (<1%). Distortion has higher GCI (~6%), consistent with its sensitivity to sector gradients and localized recirculation. Residuals, monitor flattening, and mass balance criteria are met. A URANS spot check showed no large bias relative to steady RANS for time‑averaged metrics.

7.3 Input quality and boundary conditions

The inlet total conditions are tied to calibrated facility data. Geometry fidelity to the as‑built tunnel model is within measured tolerances. We probed sensitivity to plausible uncertainty in Pt0 and turbulence intensity. A ±1% variation in Pt0 brackets the residual bias for recovery; distortion is more responsive but remains within the combined modeling and measurement uncertainty for this phase.

7.4 Agreement with experiment

Recovery trends and absolute levels agree to within 0.2–0.6% absolute across the explored matrix. DC60 is consistently overpredicted relative to test by 10–15% relative. Given the wind‑tunnel measurement uncertainty and the model sensitivity, we regard the distortion output as conservative but usable to set preliminary fan operability margins, with a caveat noted below.

7.5 Prior performance of the approach

The same solver and turbulence closure have been used by this group on the E‑3 low‑boom demonstrator intake and on an internal S‑bend reference at D=0.2 m, where recovery was captured within 1% absolute and DC60 within 20% relative of test data. Those cases had similar Reynolds numbers and diffusion factors, lending confidence that our configuration is in the known-good regime for mean pressure predictions.

7.6 Toolchain control and reproducibility

- Software: STAR‑CCM+ 2023.3 build 17.06.009 (Linux), license server pluto‑lm1.
- Hardware: Pleiades‑like cluster, AMD EPYC 7742 nodes, 256 GB RAM per node; typical run uses 128 cores for medium grid (wall time ~7 h to converge), 256 cores for fine grid (wall time ~11 h).
- Runs are scripted with Python (ccm+ batch) and Slurm job files under Git tag raven‑sd‑m3‑r2. Meshes, case files, and post‑processing scripts are stored in the project Git LFS. Each run directory contains a manifest.yml with solver settings and hashes of input files.
- We re‑executed the M=0.3, α=+6° SST fine‑grid case on a different node group; variations in AIP metrics were within 0.03% absolute (recovery) and 0.4% relative (DC60), attributable to parallel decomposition differences.

7.7 Assumptions and simplifications

- Fully turbulent assumption; no explicit transition modeling.
- Adiabatic walls; no roughness model beyond numerical law‑of‑the‑wall treatment implicit in SST with y+~1.
- No upstream swirl or fan face boundary layer ingestion from the vehicle; the tunnel blockage and screens are not modeled.
- No vane pack, IGV, or fan rotor/stator; the AIP is an empty plane.

These are consistent with the test article and the design question for M3.

## 8. Limitations and Deferred Work

- Turbulence model dependence: SST and SA give similar recovery but differ in DC60 by up to ~8% relative on the medium grid. We did not pursue transition models or hybrid RANS‑LES for this phase due to schedule. For the final operability assessment (M5), we recommend at least one DDES run at M=0.35, α=+6° to bound distortion magnitude.
- Facility uncertainty propagation: The current comparison treats the 0.5% Pt channel uncertainty as independent; a formal propagation combining test and CFD uncertainties has not been executed. We plan a simple Monte Carlo on Pt0 ±1% and incidence ±0.2° to put error bars on the comparison plots.
- AIP angularity: While qualitative comparison of flow angles was performed at four circumferential positions, we did not calibrate the 5‑hole probe models ourselves; the limited angularity dataset reduces the strength of any bias claims for swirl angle. Angularity is out of scope for the current decision.
- External flow incidence: The tunnel’s approach flow uniformity is assumed. For flight cases with significant upwash from the wing, separate CFD is required; we have not chained an external CFD solution into the intake boundary condition here.
- No fan interaction: Distortion in the presence of the rotor can be altered by the potential field. This interaction is left for the fan–inlet integrated analysis planned after M3.

## 9. Credibility Summary for M3 Decisions

- For area‑averaged recovery, we judge the predictions reliable enough to support geometry downselect. Evidence: agreement with test within 0.2–0.6% absolute, low mesh sensitivity (GCI <1%), modest sensitivity to Pt0, and previous successful applications of the same approach.
- For DC60, the predictions are consistently high relative to wind‑tunnel values by ~10–15% relative. Given the mesh sensitivity and turbulence model dependence, we recommend treating the SST value as a conservative upper bound for setting fan operability margins. A simple correction factor based on the SA comparison (−6–8% relative) could be invoked if conservatism is too penalizing, but we prefer to carry the SST numbers as-is with clear caveats.
- The computational setup is controlled and repeatable. Case management and run manifests provide end‑to‑end traceability from geometry release through post‑processing. The hardware/software environment is documented, and reruns on alternate nodes produce the same answers within negligible differences.

## 10. Detailed Methodology

10.1 Post‑processing

AIP data were interpolated from the CFD field to virtual probe locations matching the 12 rakes (radial coordinate and azimuth from the test). Total pressure recovery is reported as the ratio of local Pt to the inlet Pt0, averaged over the AIP area; DC60 is computed per ARP1420B using the same 60° sectors as the test. All scripts are under tools/post in the repository; the primary post‑processor is aip_metrics.py (SHA1: 7cdd9d9…).

10.2 Grid sensitivity metrics

The extrapolated recovery versus 1/Ncells^(2/3) is linear across the three grids, indicating a consistent order for the dominant discretization error source. Distortion shows curvature across the grids—consistent with sectorwise peak/valley shifts—so we report GCI rather than a naive Richardson extrapolation for DC60.

10.3 Solver controls and stability

We began all cases with lower Courant numbers (CFL ~3–5), stepping to CFL ~30–60 after initial stabilization. Turbulence equations used default production limiter; switching off the limiter slightly increased DC60 (+2–3% relative), with no material change to recovery.

## 11. Results at a Glance

- Minimum recovery threshold 0.965 is met for α=0° across the examined Mach range; at α=+6°, M=0.4, recovery is ~0.963 (SST), slightly below the nominal threshold, but within the known model/test combined uncertainty—this will be discussed with the IPT.
- DC60 grows approximately linearly with incidence from ~0.03 at α=0° to ~0.07 at α=+6° (SST). SA reduces the magnitude modestly but preserves trend.

## 12. Conclusions

The CFD analysis of the Raven S‑duct using steady RANS with SST on systematically refined meshes reproduces area‑averaged recovery in close agreement with subscale measurements and yields conservative estimates of circumferential distortion. The boundary conditions are tied to calibrated facility data, the numerical setup is converged and documented, and limited sensitivity studies bracket the expected variation due to upstream total pressure and turbulence model choice.

We recommend the IPT proceed with geometry downselect using the recovery values reported here and treat the DC60 values as conservative bounds. For M5, augment the dataset with:
- One or two hybrid RANS‑LES cases at the worst incidence/speed.
- A modest uncertainty propagation on Pt0 and α.
- An expanded angularity comparison if swirl becomes a gating requirement.

Appendices with run manifests, mesh images, and comparison plots are available in the repository under reports/m3/raven_sd.

## 13. References

- Menter, F. R., “Two‑Equation Eddy‑Viscosity Turbulence Models for Engineering Applications,” AIAA Journal, 1994.
- SAE ARP1420B, “Gas Turbine Engine Inlet Flow Distortion Guidelines,” SAE International, 2015.
- UMD LST Test RT‑2204, “Raven S‑Duct Subscale Test Data Book,” Rev A, 2026‑06‑22.

## 14. Acknowledgments

We thank the UMD LST team for timely provision of processed rake data and calibration sheets. Internal reviewers in the Propulsion Aerodynamics Group provided helpful feedback on mesh strategy and post‑processing scripts.

## 15. Distribution

This report is intended for internal use by the Raven IPT and associated stakeholders. Do not distribute outside the project without authorization.

---
End of report.
