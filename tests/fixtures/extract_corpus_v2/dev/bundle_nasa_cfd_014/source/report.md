To:    A. Romero, Propulsion IPT Lead
From:  M. Chen, CFD Task Owner
Date:  06 Aug 2026
Subj:  V&V status for UAV intake-duct CFD predictions (pressure recovery and AIP distortion)

Context and scope
We used RANS to estimate inlet total-pressure recovery and flow non-uniformity at the Aerodynamic Interface Plane for the Block-3 UAV intake at M=0.30–0.40, Re ≈ 2×10^6 based on lip chord. The analysis supports preliminary aerodynamic and installation trades; not intended for acoustics or icing scenarios.

Modeling approach
- Solver: ANSYS Fluent 2023R2, pressure-based coupled scheme, ideal-gas density with Sutherland viscosity. Spatial schemes set to second-order upwind for momentum and turbulence.
- Turbulence and near-wall: Primary runs with Spalart–Allmaras (wall-resolved). Initial shakedown used the γ–Reθ transition model; final dataset reverted to SA with full turbulence at the inlet.
- Geometry: Clean intake with representative bellmouth and 3 downstream duct bends; no bleed or roughness. Adiabatic walls.
- BCs: Inlet total pressure 101.3 kPa, total temperature 288 K. Turbulence length scale 3 mm. Notes show 0.5% TI at the inlet; the final run cards list 3% TI to match wind-tunnel conditions.

Discretization and convergence
- Mesh: poly/prism hybrid; coarse 2.1M cells, medium 4.3M, fine 8.6M. 20 prism layers, first cell height targeting y+ ≈ 1–2 (measured 0.8–3.4 across the lip).
- Convergence: Residuals typically dropped below 1e-5 with mass imbalance <0.2%. Two off-design cases plateaued at ~3e-3; however, pressure recovery monitors were flat to 0.1% over 2k iterations.
- Grid sensitivity: Between medium and fine, area-averaged pressure recovery at AIP changed by 1.8% at M=0.30; coarse-to-medium changed by 2.2%. An earlier sweep (before prism-layer thickening) showed a 3.9% medium-to-fine difference for the same metric at identical conditions.

Results compared to tests
- Reference data: Company rig RE-27 (duct-only), corrected for blockage; nominal recovery 0.985 ± 0.010 at M=0.30, α=0°; swirl intensity 5–6%.
- Agreement: Our final medium-grid results at M=0.30 gave 0.986 recovery (within 0.1 absolute of rig mean) and 7.8% swirl. At M=0.40 we predicted 0.972 recovery vs rig 0.979; 7% low-side.
- Note on consistency: A separate post-run check using the fine grid and 0.5% TI yielded 0.978 recovery at M=0.30 after 5k iterations, which is outside the earlier “within 0.1” statement. The test team later reissued RE-27 with a blockage correction update; with that version our 0.986 is 2% high relative to the revised mean.

Numerical repeatability and settings sensitivity
- Platform-to-platform: Re-running the M=0.30 case on the Pleiades dev queue (Intel) and the local AMD workstation produced recovery values within 0.2%. When switching AMG preconditioner settings per the default “aggressive” profile, the same case shifted by 1.5%.
- Method settings: One setup used incompressible density with variable Cp (legacy template) and differed by 1.2% in recovery from the ideal-gas setup at M=0.40.

Limitations and open items
- No wall heat transfer, no surface roughness/contamination, no boundary-layer bleed.
- SA everywhere with fully turbulent inlet; the intermittent use of γ–Reθ was discontinued. Separation behavior in the third bend is sensitive to inlet TI; we did not bracket TI beyond the two stated values.
- We present a rough cut of total prediction uncertainty as 3–5% for recovery based on mesh changes and inlet TI choices; we have not derived a formal uncertainty bound.

Assessment
- Strengths: Geometry fidelity is representative; y+ mostly within the wall-model intent; mesh refinement reduced changes below ~2% for the primary metric at M=0.30; recovery trends versus Mach are monotone and physically plausible.
- Concerns: Conflicting inlet turbulence specifications (0.5% vs 3%) materially affect separation and swirl. The earlier mesh sweep and the fine-grid rerun do not fully support the “<2%” statement across all points. Agreement with rig data depends on which correction set is used. A subset of cases relied on residual plateau criteria rather than strict residual drop.

Decision
By concurrence with IPT Leads (Propulsion and Aero), the current CFD setup is accepted for preliminary estimates of AIP total-pressure recovery at M=0.30–0.40 and α within ±3°, provided the medium-grid template and the 3% inlet turbulence level are used. The model is not approved for swirl distortion predictions or for off-nominal TI outside the documented settings.

Next steps (not on critical path for this gate)
- Re-run the fine grid at the agreed 3% TI for M=0.30 and 0.40 to reconcile the 0.978 vs 0.986 discrepancy.
- Introduce a heat-transfer-on case to bound wall thermal effects on near-wall behavior.
- Confirm AMG settings and solver density formulation across all runs before release to downstream consumers.
