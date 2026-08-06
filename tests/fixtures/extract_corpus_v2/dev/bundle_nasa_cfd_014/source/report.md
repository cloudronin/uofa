To: A. Ruiz, Inlet IPT Lead
From: J. Park, Aero Performance CFD
Subject: Status memo – S-duct CFD credibility for AIP distortion and recovery
Date: 06 Aug 2026

Quick take
- The current simulations are good enough to downselect the S-duct variant for Q3 wind-tunnel screening. Predicted area-averaged recovery and swirl trends match the Wellborn diffusing S-duct data within stated tolerances.
- Remaining caveats: the flow is separation-dominated; steady RANS is near its limits. We bracketed key uncertainties and ran a mesh study, but a limited URANS check suggests some unsteadiness we are not capturing.

What we ran
- Toolchain: Ansys Fluent 2023R1, density-based coupled solver, second-order spatial, k–omega SST with production limiter; y+ ≈ 0.8 at the AIP collar.
- Operating points: M = 0.60, Re_D = 5.0e6 (duct diameter basis), inlet TI = 1% nominal; isothermal walls, no bleed, no moving parts.
- Geometry: 1:1 with the eVTOL inlet Option C CAD, trimmed just upstream of the AIP. Corner fillets as designed, roughness modeled as k_s = 10 μm equivalent sandgrain.

Mesh and iterative behavior
- Three unstructured meshes: 2.1M / 4.8M / 10.2M cells; wall-normal first layer 6 μm; growth ≤ 1.2. Pressure recovery at the AIP changed by +1.9 percentage points from coarse to fine; monotonic behavior with observed order ~1.8. GCI on recovery at the finest grid is 1.6% (assuming RoA = 1.8).
- Monitor points (AIP centerline and upper quadrant): residuals dropped to 1e-5; plane mass balance within 0.1%. Separation bubble length shifted by <5% of duct centerline length from medium to fine grid.

Comparison to data
- Reference: Wellborn et al. diffusing S-duct measurements at comparable Mach and Reynolds (NASA TM-1993-XXXX; unsteady content minimal in their setup).
- AIP plane metrics: area-averaged recovery error 1.1%; circumferential total-pressure distortion DPCPavg within 0.02; swirl angle RMS error 2.3 deg. Reattachment location predicted 7% downstream of reported mean.
- Cross-check: Realizable k–epsilon (same mesh) shifts recovery by −0.9 points and increases peak swirl by ~3 deg, consistent with expected behavior in separated curvature.

Inputs pedigree and boundary conditions
- Inlet total conditions derived from the tunnel plan: Pt = 101.3 kPa, Tt = 300 K. Turbulence intensity taken from prior facility survey (1% ±0.5%). Outlet static pressure iterated to match the target mass flow rate ±0.2%.
- Wall thermal condition held adiabatic (no thermal coupling to structure in this phase). No-entering secondary flows or upstream swirl imposed.

Uncertainty and sensitivity
- Contributors considered: mesh resolution (1.6% on recovery), turbulence closure choice (0.9 points on recovery), inlet TI (±0.3 points when swept 0.5–5%), outlet back-pressure (±0.6 points for ±200 Pa), and equivalent roughness (±0.5 points for 0–25 μm). Combined (root-sum-square) uncertainty on recovery ≈ 3.2%; for swirl magnitude ≈ 3.0 deg.
- One-at-a-time sweeps confirm robustness of the ranked findings: exit back-pressure and model choice matter most for integrated recovery; TI and roughness mainly affect quadrant asymmetry.

Code checkups
- Baseline solver verified on two manufactured fields (isentropic vortex and source-driven channel). Observed spatial order: 2.0 for pressure, 1.8 for velocity on tetra/prism meshes used here. No anomalous solver behavior noted at Courant numbers up to 10.

Traceability to our decision criteria
- IPT acceptance for this gate: predict recovery within 2.0 points and reproduce swirl orientation and lobe structure. The medium and fine meshes meet both; coarse mesh misses swirl lobe amplitude by ~5 deg and is not recommended.
- Model form caveat documented: steady RANS acceptable for ranking and for preliminary AIP rake placement, not for final certification.

Change control and reproducibility
- Case and data archived under repo cfd/inletC/sduct/AIPv7, tags: mesh_m/f, model_SST_2023R1. Journal files capture all solver options; AIP postprocessing script (PyFluent) included. Runs executed with double precision; report template v2.3 used for figures.

Limitations and next steps
- Known omissions: thermal coupling and inlet lip bleed are excluded; no upstream propulsor effects. Wall roughness only via equivalent height, not discrete paint step modeling.
- Short URANS probe (0.5 ms flow time on medium mesh) indicates 5–10% fluctuation in separation bubble size with negligible shift in mean recovery; we will repeat on the fine mesh if time allows.
- Action items before PDR: refine locally in the first bend upper-corner (target +30% cells in that block), add a TI = 3% run to align with updated facility survey, and prepare AIP rake placement map based on the fine-grid swirl.

Bottom line
- Within the scope above, the analysis is sound and bounded. Recommend proceeding to wind-tunnel article fab and rake layout using the fine-grid SST results, with the noted uncertainty band carried forward.
