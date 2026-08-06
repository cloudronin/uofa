To: M. Ortega, Air Systems Lead
From: P. Han, CFD/Performance
Subject: Status memo — fan-plenum CFD credibility for PDR
Date: 2026-08-06

Quick take
The current CFD of the axial fan and plenum is in good enough shape to support preliminary design decisions about pressure rise and outlet flow uniformity at the 2.0–2.8 kg/s operating range. The model has been stress-tested on grid density and basic boundary choices. It aligns with the bench data within a few percent at the target flow. Caveats: it is a steady RANS treatment with a frozen-rotor (MRF) fan; anything dominated by unsteady tip leakage dynamics or broadband noise is out of scope for this issue.

What we modeled and why
- Objective quantities: total pressure rise across the fan module and uniformity of the exit plane velocity (UI = 1 – σ/μ over the 0.45 m × 0.45 m outlet).
- Geometry: vendor fan rotor-stator stack inside the sheet-metal plenum including the turning vane and screen; no cable trays or harnesses.
- Solver: Ansys Fluent 2023R2, double precision, steady MRF for rotating parts; pressure-based coupled scheme.
- Turbulence closure: k–ω SST with low-Re near-wall treatment; wall y+ from 0.6 to 1.8 on blades and 2–12 on plenum walls; scalable wall functions disabled.
- Discretization: 2nd-order for pressure, QUICK for momentum; gradient via least-squares cell-based.

Convergence and balance checks
- Residuals fell below 1e-5 for continuity and momentum, 1e-6 for turbulence equations.
- Mass imbalance <0.1% across all control surfaces; shaft torque changed <0.2% over the last 500 iterations.
- A cold restart from a perturbed solution converged to the same pressure rise within 0.2%, which is a good sanity check on solver path-independence for this case.

Mesh density sweep
- Grids: 0.9M, 1.8M, and 3.5M cells (poly-hexcore with prism layers on blades and walls). Refinement targeted the tip gap, wake regions, and turning vane leading edges; minimum prism height 0.08 mm, growth 1.18.
- Using r ≈ 1.4 between levels, the GCI on total Δp at 2.4 kg/s is 2.1% (fine grid as reference). For the outlet UI, GCI is 3.4%.
- Pressure rise changed from 416 Pa (0.9M) → 421 Pa (1.8M) → 422 Pa (3.5M) at 2.4 kg/s. The extrapolated asymptote is 425±9 Pa by Richardson fit.

Boundary assumptions
- Inlet: prescribed mass flow; top-hat mean profile with 5% turbulence intensity and 0.05 m length scale to match the bellmouth rig.
- Outlet: zero gauge static pressure; backflow suppressed with TI = 5%.
- Walls: smooth no-slip; no roughness modeled on the perforated screen (treated as resolved geometry).
- Rotational speed: 1840 RPM nominal, from the vendor curve; shaft power extracted from the solution is 1.83 kW on the fine mesh.

Comparison to bench results
- At 2.4 kg/s: measured Δp = 410 Pa (averaged over three runs, standard deviation 3 Pa); CFD on the fine grid = 422 Pa, bias +2.9%.
- Outlet velocity uniformity: PIV-derived UI = 0.82±0.01; CFD = 0.79 on the fine grid (slightly more peaky near the vane wake).
- Across 2.0–2.8 kg/s, the slope of the system curve from CFD overlays the measured trend; mean absolute deviation in Δp is 3.6%.

Model-form spot check
- A quick rerun with Spalart–Allmaras (same mesh/settings) gave Δp = 415 Pa at 2.4 kg/s (−1.7% vs SST). The outlet UI difference was +0.01. This brackets the turbulence-model sensitivity for our QoIs at roughly ±2%.

Uncertainty budgeting (high level)
- Combine: grid-induced spread (from GCI), inlet mass flow repeatability (±0.5% on the rig translates to ±1.2% on Δp by local sensitivity), and inlet TI variation (±2% around nominal shifts Δp by ~0.4%).
- Rolled up as RSS, the 95% band on Δp prediction at 2.4 kg/s is about ±2.8% relative to the fine-grid mean.

What this is good for
- Selecting the turning vane angle and deciding whether the screen can be moved 50 mm downstream without compromising UI.
- Estimating fan operating point on the installed curve within a few percent, with explicit evidence that the mesh is not the dominant limiter.

Known limitations
- Steady MRF: no capture of rotating blade–row interaction tones or stall precursors; any acoustic inference should use separate methods.
- The harness bundle, motor mounts, and small lip seals are not in the current CAD; we will only include them if we see >5% discrepancy at CDR.
- We did not explore off-design turbulence states (e.g., very low inlet TI) or distorted inflow; those could degrade uniformity more than shown here.

Next steps (if approved)
- Lock turbulence model as SST and retain the 3.5M grid for design sweeps.
- Add one targeted local refinement in the tip gap to evaluate if the UI GCI can be nudged below 3%.
- Run a single transient sliding-mesh case at 2.4 kg/s to quantify any steady-to-unsteady bias on Δp.

Data drop
- Case and results: SharePoint > AirSystems > FanPlenum > CFD > 2026-08-05_SST_MRF_fine.cas.h5/.dat.h5.
- Plots and comparison figures: same folder, “PDR_pack_v03.zip”.
