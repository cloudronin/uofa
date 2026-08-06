Title: Credibility Report — CFD of Coronary Stent Hemodynamics to Support Design Freeze

Prepared by: Fluids Group, CardioDesign R&D
Date: 2026-08-05
Software: Ansys Fluent 2024 R1 (double precision), ParaView 5.12, in-house post-processing scripts (Python 3.11)

Executive summary
- Purpose: Use an unsteady CFD model to rank stent geometries by near-wall shear environment and to justify the selected design’s acceptability before tool-up.
- How the results drive decisions: If the predicted 95th percentile oscillatory shear index (OSI95) and time-averaged wall shear stress (TAWSS) distribution for the chosen design remain within the envelope measured in an anatomically matched phantom experiment under matched flow conditions, the design proceeds. Otherwise, iterate geometry.
- Risk if the model is wrong: Moderate. The simulation does not support a clinical performance claim; it informs design selection. An incorrect call could delay development or select a suboptimal pattern but is unlikely to create immediate patient risk because bench, animal, and clinical testing remain gatekeepers.
- Bottom line: The computational predictions meet pre-agreed comparison bars for velocity field and wall-shear-related metrics. Numerical checks (mesh/time refinement, residual control, mass balance) indicate small truncation errors relative to the differences between design variants. Input pedigree, sensitivity to key assumptions (blood rheology, inlet trace, and wall rigidity), and limits-of-use are documented. Independent phantom measurements provide an anchor with quantified uncertainty.

1. Background and how the model informs decisions
The project team is finalizing the lattice of a cobalt-chromium, drug-eluting coronary stent intended for mid-LAD deployment. Prior animal studies and literature point to low and oscillatory shear pockets adjacent to strut crowns as correlates with neointimal hyperplasia. The simulation is used to:
- Compare three candidate patterns (A, B, C) under matched pulsatile flow in a representative curvature.
- For the selected pattern (B), demonstrate that predicted TAWSS and OSI fields in a realistic deployment fall within ranges observed in a controlled in vitro study.

We are not forecasting absolute clinical endpoints; rather, we are using the model to rank options and confirm the design’s hemodynamic footprint is not adverse compared with prior-generation devices.

2. Device and flow model description
- Geometry: Stent B deployed in a silicone phantom of a 3.0 mm diameter, mildly curved (radius 30 mm) coronary segment with 5% oversizing. Phantom was micro-CT scanned at 10 μm voxel size after deployment to capture as-built strut positions and slight recoil. The CFD domain includes 10 diameters upstream and downstream straight sections to minimize boundary effects; total length 120 mm. Strut width 80 μm, thickness 90 μm; connector geometry per drawing CD-B-1421.
- Fluid: For bench comparison, 40% glycerol-water surrogate (ρ = 1050 kg/m³, μ = 3.5 mPa·s at 37°C). For in vivo what-if runs, Carreau–Yasuda representation (μ0 = 0.16 Pa·s, μ∞ = 0.0035 Pa·s, λ = 8.2 s, a = 2, n = 0.64), verified against published rheograms.
- Regime: Reynolds number based on diameter and peak bulk velocity ≈ 350. Flow remains laminar in the parent lumen; local separations occur behind struts.

Governing equations are the incompressible Navier–Stokes system. Walls (stent and phantom) are no-slip, rigid. This rigidity simplification is checked in Section 7 for its impact on wall shear.

3. Software, code checks, and numerics
- Solver and numerics: Second-order spatial discretization for pressure and momentum; second-order implicit time stepping. Pressure–velocity coupling via coupled solver with pseudo-transient continuation. Convergence criteria: scaled residuals below 1e-6 each time step; mass imbalance below 0.1% per time step; monitor points (bulk flow, pressure drop, area-averaged WSS) steady to within 0.5% between time steps.
- Manufactured/analytical tests: Prior to the stent cases, we executed two code checks:
  - Fully developed Poiseuille in a 3D circular pipe: recovered parabolic velocity with L2 norm error < 0.2% on 50k-cell mesh; second-order convergence confirmed when halving mesh spacing (observed order 1.98).
  - 3D lid-driven cavity at Re=1000: compared centerline velocity profiles against literature; deviation < 2.5% on 1.2M polyhedral cells; grid refinement showed expected trend to benchmark values.
- Hardware and determinism: Simulations ran on a 2-socket AMD EPYC 7543 system, 64 cores total, 256 GB RAM. Runs repeated on a separate node produced bitwise-identical residual histories and integrated QoIs.

4. Discretization checks (mesh/time) and iterative convergence
- Surface resolution: Polyhedral core with 6.0 million cells; 12 prism layers adjacent to all solid surfaces, first cell height 2 μm, growth rate 1.15, ensuring y+ < 0.8 everywhere.
- Grids for refinement study:
  - Coarse: 2.1M cells, 6 prism layers
  - Medium: 6.0M cells, 12 prism layers
  - Fine: 14.8M cells, 18 prism layers
  Refinement was uniform in strut-adjacent and recirculation-prone zones; streamwise edge length reduced proportionally.
- Time step study: Δt = 2.0 ms (coarse), 1.0 ms (baseline), and 0.5 ms (fine). Simulations run for 8 cardiac cycles; last two cycles analyzed after periodicity confirmed (cycle-to-cycle change in integrated WSS < 0.3%).
- Error indicators:
  - Global pressure drop across the stented section: observed order p ≈ 1.9; extrapolated Richardson estimate indicates 2.6% bias on the medium mesh at peak flow.
  - Area-averaged TAWSS over the stented length: GCI on the fine grid 3.8% (comparing fine-to-medium with factor of safety 1.25). Medium-grid GCI 6.9%.
  - OSI95: mesh-induced variation (fine vs. medium) 4.5%; time-step-induced variation (Δt 1.0 vs. 0.5 ms) 2.1%.
  - Local wall shear at crown-adjacent hotspots: peak value changes < 6% between medium and fine grids; spatial location of hotspots shifts < 0.1 mm.

Given the design-ranking use and the agreement with experiment (Section 8), we accept the medium mesh and Δt = 1.0 ms for production runs, reserving the fine grid for spot checks.

5. Inputs, boundary conditions, and geometry pedigree
- Inlet waveform: For the bench-matched runs, the measured pump trace (Transonic TS410) was sampled at 200 Hz. The inlet boundary condition is a prescribed volumetric flow rate with 1% RMS tracking error after filtering. Inlet turbulence intensity set to 1% (non-impactful under laminar regime; sensitivity tested).
- Outlet: Fixed static pressure at the distal plane, tuned to achieve the measured mean pressure drop across the test section (validated within 2%).
- Geometry fidelity: Micro-CT segmentation done in Mimics 26.0; STL smoothing with a 10 μm tolerance to remove voxel staircasing while preserving edge sharpness. A metrology comparison of the triangulated surface to the raw point cloud shows 95th percentile deviation of 8 μm and max 22 μm.
- Fluid properties: Density and viscosity measured with oscillatory rheometer (Anton Paar MCR 302), uncertainty ±0.5% for μ and ±0.2% for ρ at 37°C.
- Solver settings management: All case and journal files tracked in Git LFS with hashed IDs. Key settings (relaxation factors, discretization schemes) templated to prevent drift between analysts.

6. Sensitivity and uncertainty budget
We probed how outputs of interest respond to plausible perturbations:
- Blood rheology: For the bench fluid, Newtonian is exact by construction. For in vivo what-ifs, switching from Newtonian (μ = 3.5 mPa·s) to Carreau–Yasuda changed TAWSS by −4.1% on average in strut wakes and −1.3% elsewhere; OSI95 changed by +0.9%. These shifts are materially smaller than design-to-design differences (pattern A vs. B ΔTAWSS = +12%).
- Inlet trace phase: ±10 ms phase shift relative to Womersley peaks altered OSI95 by ±1.5%.
- Stent positioning: Random perturbations of strut radial position ±10 μm and rotation ±2° (based on deployment tolerances) impacted local peak shear by up to 4% and had negligible impact (<1%) on integrated metrics.
- Wall rigidity assumption: See Section 7; effect bounded using a compliant-wall 1D surrogate and literature.
- Mesh/time discretization: Carried forward from Section 4.
- Experimental measurement noise: PIV velocity uncertainty estimated at 3.0% (Section 8), which propagates to roughly 9–12% uncertainty in wall shear gradients (finite difference near the wall).

Combining independent contributions (root-sum-square) for TAWSS area-average yields about 8–10% total uncertainty on the simulation side under bench conditions, excluding model-form simplifications that are handled via comparison to data.

7. Physical model selection and assumptions
- Flow state: Laminar solver used for all runs. Justification: Reynolds number is below classic laminar-turbulent thresholds; PIV spectra in the phantom show no broadband energy cascade indicative of turbulence (TKE below 0.002 m²/s² everywhere). Behind-strut recirculation and reattachment are time-dependent but not turbulent in the classical sense under these flow rates. A comparison with SST k–ω (low-Re formulation) at peak flow shows area-averaged TAWSS differs by 5.6%; OSI95 differs by 1.8%. Given experiment-model closeness with laminar and the laminar-consistent PIV, we selected the laminar model for production.
- Wall behavior: Rigid-wall assumption adopted. Coronary compliance in the mid-LAD is modest; a back-of-envelope estimate using a 1D elastic tube model (compliance 1.5% per 100 mmHg) suggests <5% modulation in near-wall shear for the flow amplitudes examined. Literature (e.g., Morbiducci 2009) supports weak sensitivity of TAWSS to small-area compliance at Re < 500. Residual risk captured in the uncertainty section.
- Thermal effects: Isothermal at 37°C; PIV and CFD both maintained temperature control within ±0.5°C.

8. Experimental dataset and comparison protocol
We partnered with FlowLab LLC (independent lab) to acquire a controlled dataset:
- Setup: Silicone phantom (same geometry) seeded with 10 μm particles; laser sheet thickness 1 mm; TR-PIV camera (Phantom VEO) at 500 fps; phase-locked acquisition with pump signal.
- Index matching: Working fluid refractive index tuned to 1.413 to minimize wall reflections. Residual glare near struts reduced via image masking; affected area < 2% of wall length.
- Calibration: Plate with 10 μm dot spacing; calibration residuals < 0.1 pixel. Spatial resolution 32 μm per vector after windowing (32×32 px, 50% overlap).
- Uncertainty: Velocity uncertainty ±3% (standard), assessed via correlation peak ratio method; near-wall gradient uncertainty estimated by least-squares fit in the first 150 μm off-wall, yielding ~10–12% for shear stress proxies.
- Data products: Phase-averaged velocity fields across 40 bins over the cardiac cycle; derived wall shear indices via extrapolation from near-wall velocities (masking within 50 μm of wall to avoid bias).

Comparison rules of engagement:
- Registration: CFD wall coordinates and PIV plane registered using fiducial markers; RMS alignment error 35 μm.
- Metrics:
  - Velocity profiles at 10 cross-sections: normalized RMS difference target ≤ 10% at peak flow, ≤ 12% at mean flow.
  - Pressure drop across stented segment: within 7%.
  - TAWSS and OSI maps: spatial correlation coefficient ≥ 0.85; distributional comparison via Kolmogorov–Smirnov statistic with p > 0.1 and difference in medians < 15%.
- Data clipping: Regions with PIV confidence < 0.6 excluded from both datasets.

Results:
- Velocity: nRMSE 7.1% (peak), 9.3% (mean); bias −1.8% relative to PIV.
- Pressure drop: CFD higher by 3.2% vs. transducers (Validyne DP45).
- TAWSS map: Pearson r = 0.89; median difference −6.4%; KS test p = 0.21.
- OSI map: Pearson r = 0.86; median difference +4.9%; KS test p = 0.18.
- Hotspot localization: 93% of top 5% OSI regions co-located within 0.2 mm.

9. Applicability and interpolation/extrapolation bounds
- Geometric scope: Patterns with strut width 70–90 μm, pitch within ±15% of Pattern B, and curvature radii 25–50 mm. Larger curvature (tighter bends) may induce secondary flows not represented; separate analysis required.
- Flow rates: Mean flow 50–90 mL/min; heart rate 60–90 bpm; Womersley number 1.6–2.3. Outside this band, oscillation phase behavior may deviate.
- Material boundary: Rigid phantom and stent captured. For fully patient-specific coronary compliance or microvascular coupling, the present model does not apply without augmentation.
- Wall thickness and surface finish: Phantom wall thickness uniform; in vivo vessel roughness and microtexture are not included. Prior studies suggest sub-2% impact on bulk WSS in these regimes.

10. Results and acceptance rationale
For Pattern B, under bench-matched conditions:
- All velocity and pressure comparison targets met (Section 8).
- TAWSS and OSI maps meet the pre-agreed closeness bar. The predictive spread from numerical approximations (Section 4) and input variations (Section 6) is small enough that the experiment–CFD discrepancies fall within combined uncertainty.
- Design ranking: Pattern B shows a 10–14% reduction in low-TAWSS area (TAWSS < 0.4 Pa) compared with Pattern A and a 7–9% reduction compared with Pattern C on the same medium mesh and inlet trace. These differences exceed the summed uncertainties, supporting a robust ranking.

Acceptance threshold definition and rationale:
- The go/no-go bar was set based on the consequences of use (moderate risk), historical variability in comparable PIV datasets, and typical CFD truncation errors for near-wall metrics in similar stented flows. We targeted ≤10% velocity field error and ≤15% median difference for shear-related maps, with strong spatial correlation, so that geometry ranking remains stable. These targets were defined at project kickoff and reviewed by the device safety board.

11. Reproducibility, traceability, and configuration control
- Repeatability: Independent analysts (JD and ML) reproduced the baseline Pattern B run using the same mesh and BCs. Key outputs (pressure drop, TAWSS mean, OSI95) matched within 0.8%.
- Versioning: Geometry (STL), meshes (Fluent .msh), and case/data (.cas/.dat) files are archived to the corporate vault with SHA-256 hashes. The CFD case is tagged cd-stentB-v37. The PIV dataset is stored as hdf5 with metadata in an ISA-Tab manifest.
- Audit trail: A run log records dates, hardware, solver build ID, and any deviations. Peer review checklists (numerical settings, y+ maps, residuals, monitors) are attached.
- External independence: Phantom manufacturing and PIV were executed by FlowLab LLC to avoid confirmation bias. Registration and comparison scripts were developed in-house but reviewed by a separate team not involved in design selection.

12. Human and process considerations
- Personnel: Lead analyst has 12 years of cardiovascular CFD experience; supporting analyst 6 years. Both completed the internal CFD QA curriculum (last refresher April 2026).
- Reviews: Two-step reviews performed: a midstream review after mesh/time studies and a final sign-off including a cold-eye review by an analyst from the aero team focusing on numerics.
- Checklists: Pre-departure and arrival checklists for each run (units check, BC alignment, mesh quality metrics: skewness < 0.85, aspect ratio < 50 in prisms, orthogonality > 0.2).
- Tools QA: Python scripts unit-tested (pytest coverage 88%); baseline comparison functions validated on synthetic datasets with known differences.

13. Credibility discussion aligned to decision risk
We scale the depth of evidence to the weight the model carries in decision making:
- Consequence of a wrong call: Moderate (design iteration cost, potential schedule slip), not directly patient risk at this phase.
- Influence of the model on the decision: High for ranking, medium for acceptance. Bench testing and physician design review are parallel inputs.
- Evidence provided:
  - Numerics: Three-level mesh and three-level time refinement; residual control; periodicity checks; mass conservation—all quantitative.
  - Software/code checks: Canonical flows to demonstrate solver correctness and analyst competence.
  - Input pedigree: Measured fluid properties, CT-based geometry with quantified segmentation fidelity, matched inlet traces.
  - Assumption checks: Laminar vs. SST k–ω comparison; rigid-wall impact bounded.
  - Comparison to independent data: PIV-based velocity and near-wall metrics with uncertainties; formal statistics for closeness, no tuning beyond BC matching.
  - Sensitivity: Rheology, phase shift, positioning tolerances; demonstrates robustness of ranking.
  - Applicability: Clearly stated bounds on geometry and flow conditions; out-of-scope cases identified.

On balance, the evidence package is commensurate with the model’s role. All acceptance targets have been met with margin, and the residual uncertainties are small compared to the observed design-to-design differences.

14. Limitations and open items
- Rigid walls: While estimated impact is small, a follow-on study could include a thin-wall FSI check for highly compliant vessels or tachycardic conditions.
- Out-of-plane flows: The PIV plane is a 1 mm sheet; secondary motions may be partially missed. Stereo-PIV or tomo-PIV would reduce this limitation if higher accuracy on 3D structures is needed.
- WSS from PIV: Wall gradients are extrapolated, carrying higher uncertainty than velocity. Our acceptance thresholds account for this, but more direct wall shear probes (micro-PIV very near-wall or TIRF) would be stronger.
- Non-Newtonian rheology: In bench runs, Newtonian is exact. For in vivo scenarios, while a Carreau–Yasuda case is included, further validation against hemorheology data at low shear rates could refine predictions in very low-flow zones.
- Patient specificity: The current model corresponds to a representative curvature and size. Patient-specific calcification and eccentricity are not represented.

Conclusions
The CFD model, as configured and bounded, provides reliable discrimination among candidate stent geometries and demonstrates that the selected pattern’s hemodynamic footprint agrees with an independent phantom measurement within pre-specified tolerances. Numerical and input-related uncertainties are quantified and small relative to design effects. The model is acceptable for the stated decision use and within the declared limits.

References and data availability
- Fluent 2024 R1 Theory Guide.
- Morbiducci U. et al., “Mechanistic analysis of the influence of torsion and curvature on hematic helicity in human aorta,” J Biomech, 2009.
- Augst A. et al., “Stent-induced hemodynamics,” Ann Biomed Eng, 2004.
- FlowLab LLC Test Report FL-2026-042.
- Data and case files: Corporate vault path //RND/CFD/CorStent/PatternB/Release_v37; request access via R&D PMO. Hashes and manifests included.

Appendix pointers
- Appendix A: Mesh quality histograms and y+ maps
- Appendix B: Grid/time refinement plots and GCI calculation details
- Appendix C: PIV processing workflow and uncertainty propagation
- Appendix D: Sensitivity tornado plot for TAWSS and OSI95
