To:      Lander Aero Subsystem Lead
From:    CFD Team (Aero/Fluids Group)
Date:    2026-08-06
Subject: Status memo — Supersonic backshell CFD credibility for PDR

Purpose and decision context
- We ran a focused set of supersonic, cold-flow CFD analyses for the 0.3‑scale backshell model to support PDR loads and base heating margins. The immediate decision is whether these results are fit to anchor the drag and base-pressure numbers in the PDR data book and to scope the heat-flux uncertainty for TPS pre-sizing.
- Working thresholds set with loads/TPS: drag coefficient within ±5% of the Langley 20‑Inch Mach 2.5 tunnel measurements; mean base pressure within ±10%; centerline Stanton number within ±25%.

Model setup highlights
- Solver: FUN3D v13.7 (double precision), compressible RANS, k–ω SST with compressibility correction; fully turbulent wall treatment with y+ ≈ 0.8–1.2 in the first prism layer; adiabatic backshell for force/moment runs and isothermal wall at 300 K for heating comparisons.
- Facility reproduction: Inflow Mach 2.50±0.01, ReD = 6.0×10^6±2%, T0 = 295±2 K, P0 = 185±1 kPa per tunnel card 27‑032. Nozzle boundary layer thickness from facility calibration was imposed as a momentum-thickness proxy at the inflow.
- Geometry: CAD derived from the latest Rev D backshell surfaces; sting and support simplified per test hardware drawings; pressure tap and gauge cutouts represented only by local roughness patches, not resolved holes.

Numerics and mesh conditioning
- Unstructured hybrid grids with layered prisms at walls; three levels: 3.2M / 9.6M / 28M cells (growth ratio ~1.2 normal to wall). Farfield at 30 D.
- Convergence: Density residuals dropped 4–5 orders; force monitors flat to <0.1 drag counts for last 2k iterations on the medium and fine meshes.
- Mesh refinement study: CD decreased monotonically across refinements; observed order ~1.9 for drag. Extrapolation indicates ~1.5% numerical uncertainty on CD and ~2–3% on area‑averaged base Cp. Stanton number is more sensitive; estimated ~10–12% from grid effects.

Solver correctness checks
- Sanity checks against the NACA M6 wing and SARC channel cases run under the same build showed expected trends and matched team baselines. MMS residual norms exercised in CI caught no regressions relative to v13.6.

Comparison with wind-tunnel data
- Force balance: Predicted CD is 3.2% above the mean of runs 27‑032‑A through ‑C at nominal incidence. Scatter across repeats is ±0.7%.
- Base pressure: Area‑averaged Cp_base differs by +7% relative to the 32‑tap rake average; radial distribution shape is captured, with a small underprediction at r/R≈0.6.
- Heating: Centerline Stanton on the isothermal wall is 18–22% low versus thin‑film gauge data (gauge calibration uncertainty ~8%). The shortfall is consistent with SST’s known bias in massively separated shear layers at this Mach.

Input pedigree and test conditions
- Test inputs came directly from the facility data system (exported by test engineer J. Wong, 2026‑06‑18). Facility uncertainties: Mach ±0.3%, total temperature ±0.7 K, ReD ±2%. We propagated these as inflow bounds in “perturbed” runs.

Sensitivity exploration
- Turbulence closure: Switching to SA‑BCM raises Cp_base by ~3% and reduces Stanton by ~5% versus SST; drag impact <1%.
- Wall condition: Introducing an equivalent sand‑grain roughness of 30 µm (to mimic tape seams and gauge wiring) increases centerline Stanton by ~12% with negligible effect on CD.
- Incidence: ±0.5 deg angle-of-attack shifts CD by ~0.6% and moves the base pressure peak laterally as observed in the tunnel when the sting flexed.
- Facility temperature: ±1% in T0 changes Stanton ~±1.5%; forces largely unaffected.

Uncertainty picture (for PDR use)
- Combining mesh-induced effects, facility bounds, and model-form spread (SST vs SA‑BCM as a proxy) by root-sum-square gives U95 estimates of ~4.7% for CD, ~11% for Cp_base, and ~24% for centerline Stanton. These align with our acceptance thresholds for forces and base pressure; heating is at the edge.

Reproducibility and configuration control
- Case setup is scripted (YAML + Python driver) and archived in the mission GitLab under tag backshell_M25_PDR_v1 (commit 0f4c9a2). Runs executed in a Singularity container fun3d:13.7‑cuda11.4 (SHA256: 6e8d…b1a).
- Execution environment: Aitken skl nodes, 64 cores per case, 128 GB RAM; medium grid wall clock 7.8 h, fine grid 22.4 h. Jenkins job cfd-backshell-025 runs nightly smoke tests on the medium grid.

Independent cross-check
- A second analyst (A. Patel) reproduced the medium‑grid CD within 0.4% and Cp_base within 1.2% using the same container and scripts. Post‑processing (Tecplot macro v2023R1) yielded identical integrated quantities when rerun from raw volumes.

Scope limits and next steps
- Current results are applicable for M = 2.4–2.6, zero to ±0.5 deg incidence, smooth backshell, and cold-wall assumptions. They are not intended for unsteady buffeting or for detailed local hot spots near protuberances.
- For CDR, we recommend: (1) a targeted DES on the medium grid for heating shape factors, (2) incorporation of measured roughness maps from hardware, and (3) a higher-fidelity wall heat-transfer model to tighten the Stanton uncertainty to <15%.

Bottom line
- We judge the present CFD suitable to anchor PDR drag and base pressure. For TPS pre-sizing, use the heating numbers with the stated margin; plan on an update post‑DES before freezing CDR allocations.
