To: Ares Inlet IPT Lead
From: CFD V&V Working Group
Subject: Credibility snapshot — S‑duct intake CFD for pressure recovery/distortion, per NASA‑7009B
Date: 2026‑08‑06

Summary
We assessed the RANS-based CFD model used to predict total pressure recovery and DC60 distortion in the service module S‑duct across Mach 0.18–0.32 and angles of attack (AoA) −5° to +10°. The solver is Ansys Fluent 2023 R2 (double precision) on RHEL 8, Intel Xeon 6258R (128 cores). The model configuration (SST k‑ω; second‑order upwind; coupled pressure‑velocity; scalable wall functions with y+≈1 on the fine grid) is judged fit for separated but subsonic internal flow with modest swirl.

Scope and assumptions
The analysis treats air as single‑phase, calorically perfect at 300 K; walls are smooth, adiabatic; no moving surfaces; steady statistics (no URANS/LES). These idealizations, plus omission of surface roughness variability and thermal gradients, bound the context of use to pre‑test design and flow control layout, not final loads or flight clearance.

Inputs pedigree
- Geometry: CATIA V5 Rev D; laser scan of the wind‑tunnel article showed <0.15 mm RMS deviation; fillet radii aligned to Rev D within drawing tolerance.
- Operating conditions: Mass flow 2.3±0.05 kg/s (from system model SMM‑42B); inlet turbulence intensity 0.5%±0.2% (11×11 ft tunnel), confirmed with hot‑wire.
- Fluid properties: NIST REFPROP at 300 K; density 1.184 kg/m³; μ=1.85e‑5 Pa·s.
- Boundary conditions: Velocity inlet with measured profiles applied; pressure outlet corrected for tunnel static.

Solver credibility and software practices
- Vendor documentation covers discretization and regression testing; we did not alter source.
- In‑house UDFs and post‑processing scripts: 86% unit test coverage (pytest); Jenkins CI on merge; code review required.
- Reproducibility: GitLab project MS‑CFD‑INL‑Sduct, tag v1.3.2; containerized environment (Singularity) pins compiler/MPI; SHA256 checksums for meshes and BCs.

Analyst qualifications
Two primary users (J. Patel, E. Romero) completed Fluent advanced turbulence training (Ansys L3, 2025), and have prior internal-duct CFD experience; checklists enforced via peer review.

Solution quality checks
- Mesh refinement: 3.2M / 6.5M / 13.1M poly‑prism cells; y+≈1–2 on fine mesh; residuals <1e‑6; mass imbalance <0.1%.
- Extrapolation: Apparent order p=1.95; GCI on area‑averaged recovery = 1.8% (fine mesh); distortion GCI = 2.4%.
- Iterative/parallel consistency: 2 independent restarts yielded <0.2% variation in key outputs.

Comparison to measurements
- Data source: NASA Ames 11×11 ft tunnel test (Test Log A11‑SD‑042); blockage 3.2% (corrected); uncertainty u95: Cp 2.0%, rake total pressure 1.5%.
- Agreement: Mean absolute error in Cp along centerline = 3.1%; DC60 within 5.4% of test; swirl angle RMS within 1.8 deg. Inlet turbulence intensity adjusted to match facility measurements; no other tuning.

Uncertainty and sensitivity
- Monte Carlo (n=500) over inlet TI, mass flow, and roughness (σ=5 μm) using Latin hypercube: standard uncertainty 4.5% on DC60, 1.9% on recovery; 95% bounds ±9.1% and ±3.8% respectively.
- Screening and Sobol’ analysis: DC60 most influenced by TI (first‑order index 0.41) and wall roughness (0.27); recovery modestly sensitive to mass flow (0.22).

Robustness and range
All cases converged within 2,500 iterations using under‑relaxation αp=0.3; for AoA >10°, intermittent separation oscillations suggested unsteadiness—outside stated use. Recommended envelope: Mach 0.18–0.32; AoA −5° to +10°; ReD 1.1e6–1.9e6.

Test coverage versus needs
Validation spans three Mach numbers, three AoA, and two inlet screens (TI levels). This covers expected pre‑test design space; compressibility effects above M=0.5 were not pursued per plan.

Reasonableness checks
- Integral energy balance ±0.5%.
- Empirical loss (Idelchik elbow K) predicts Δpt within 12% of CFD.
- Alternate solver spot check (STAR‑CCM+ 2022.1, single case) agreed within 2.6% on recovery.

Use history
Similar methodology applied to Orion ESM ducting (2024); test correlation within 8% for recovery, 6% for distortion; lessons learned applied here (TI specification, prism layers).

Data handling and traceability
Inputs/outputs archived in EDMS with metadata, units (SI), and provenance chain; results replicated on a second cluster within ±0.3%. Independent review by Dr. K. Chen (AeroSci) completed 2026‑07‑28; all five findings closed (see CR‑MS‑114 to ‑118).

Plan conformance
V&V Plan VVP‑EDL‑042 Rev B: 28/29 tasks complete; deferred item is high‑Mach check (not in current envelope).

Decision
The CFD setup described above is accepted for pre‑test design decisions and inlet‑rake placement for the S‑duct within Mach 0.18–0.32 and AoA −5° to +10°, subject to using the fine mesh (≥13.1M cells) and documenting inlet TI. It is not approved for final flight loads or certification. Decision made by the Ares Inlet IPT Lead on recommendation of the CFD V&V Working Group.
