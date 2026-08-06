To:     APU Inlet IPT Lead (J. Morales)
From:   CFD V&V Lead (R. Chen)
Date:   2026-08-06
Subj:   Credibility status of S‑duct inlet CFD for distortion predictions at cruise and takeoff conditions

Quick summary
We’ve completed the V&V activities called out in VVP-APU-DFI-011 Rev C for the S‑duct inlet. The model is suitable for pre-PDR decisions on screen design and bleed sizing at M0.3–0.6, α = −2° to +4°, ReD ≈ (4–7)×10^6. For higher incidence or off‑design yaw, treat outputs as trend-only until we expand the validation set. Key QoIs: circumferential distortion DC60 at Aerodynamic Interface Plane (AIP), total pressure recovery, and swirl intensity.

Evidence highlights (ordered by what drove risk)
- What we’re answering: The analysis is used to rank screen geometries and bleed schedules, not to certify final limits. Acceptance bands per SYS-APU-REQ-254: DC60 prediction within ±0.02 absolute, recovery within ±1.5 points.
- Physical content and idealizations: Compressible, steady RANS with k–ω SST; air treated as calorically perfect; no heat soak; smooth walls; transition modeled via γ–Reθ only for clean-duct runs. Roughness sensitivity evaluated separately (see below). Geometry includes the wind‑tunnel trips and rake stems to match validation articles.
- Domain and geometry fidelity: CAD from WT article 42-SD-3 Rev B; screen porosity mapped from manufacturer data; bleed slots modeled with porous-jump coefficients derived from coupon tests. Blockage matches tunnel insert to within 0.3%.
- Inputs pedigree: Inlet total pressure, total temperature, and turbulence intensity profiles pulled from rake/cobra probe surveys (WT log 23-145). Calibrations traceable to NIST; combined standard uncertainty at duct entrance: 0.35% for Pt, 0.2 K for Tt, 0.6% for U. Porous coefficients have ±10% lab uncertainty.
- Numerics and algorithms: Second‑order upwind for convection with limiter, second‑order central for diffusion, coupled pressure–velocity (RhoCentral preconditioned); double precision; segregated energy. Residuals to 1e-6; mass imbalance <0.05%; AIP probe monitors flat for last 3k iterations.
- Mesh refinement study: Three unstructured hybrid grids: 7.1M/19.4M/52.6M cells; wall y+ ≈ 0.8–1.2 on mid‑duct. GCI on DC60 = 0.006 (fine grid, 95% C.I.); observed order p = 1.86 for recovery and 1.72 for DC60. Separating corner region refined with prism layers to maintain Δy+ < 1.
- Iterative/time errors: Steady runs reached asymptotic residual behavior; pseudo‑time stepping reduced CFL from 50 to 5 before final Newton sweeps. Repeatability of DC60 within 0.002 across restarts.
- Code health (verification): SU2 v8.0.2 (tag “Galileo”) with NASA fork hash 9c1f… MMS on 3D Euler recovers p = 1.98 (pressure), 1.96 (velocity). Turbulent channel benchmark matches Spalding law to within 1.5% at y+ = 30–200. Jenkins CI: 187/187 unit tests passing; static analysis clean; IEEE‑754 compliance checked. No open CFD solver bugs affecting RANS/SST in our feature set.
- Software management: Case setup scripted in Python; meshes via Pointwise 2023R2; exact environment captured in Apptainer image cfd_env_2026.07.sif. Git repo “sduct-aip” tagged v1.3; issue tracker closed all PDR‑blocking items; data archived on LUSTRE path /proj/apu/sduct/run_1p3/.
- Comparison with experiments: WT campaigns WT‑SD‑A (M0.3) and WT‑SD‑B (M0.5). Data include AIP 40‑port total pressure rake, five‑hole probes (swirl), and wall pressures; overall tunnel Re matched within 2%. Data uncertainty: DC60 ±0.008, recovery ±0.4 pts, swirl ±0.7 deg. CFD vs test at baseline screen: DC60 error +0.011 at M0.3, +0.017 at M0.5; recovery error −0.9 and −1.2 pts respectively; swirl RMS error 0.9 deg.
- Broader coverage and limits: AoA sweep −2° to +6° tested. Up to +4°, DC60 bias stays within +0.02; at +6° the separation shifts upstream and the error grows to +0.036—flagged as outside current use window.
- Sensitivity checks: One‑at‑a‑time variations show DC60 changes of +0.006 per +5% inlet Tu, +0.004 per +5% porous C2, and +0.008 for +10 μm equivalent roughness. Grid stretching factor ±20% moved DC60 by ≤0.003. Switching to SA‑BCM reduced separation size and cut DC60 by 0.006; SST remains closer to data across cases.
- Uncertainty propagation: LHS with 120 samples over inlet Tu (±20%), porous C2 (±10%), and screen porosity (±3%). On the fine grid, 95% bound for DC60 at M0.5 baseline is 0.292 ± 0.015. Combined uncertainty (GCI ⊕ input) gives total ±0.016, which meets the acceptance band.
- Cross‑solver sanity check: Two cases repeated in ANSYS CFX 2023R1 (SST). DC60 differed by ≤0.009; recovery within 0.6 pts. Meshes mapped via CGNS; same BCs and turbulence options where possible.
- Prior usage: Same workflow was used on the NAC S‑duct study (TN‑NAC‑22‑017) with PIV validation; distortion errors there were within 0.02 across M0.2–0.6.
- People and independence: Primary analyst (5 yrs inlet CFD) executed runs; separate reviewer (A. Gupta, not on design team) performed mesh and BC audits and re‑ran the M0.5 baseline from scratch—matched DC60 within 0.003.
- Plan discipline and traceability: Activities executed per VVP-APU-DFI-011 Rev C; all QoIs traced to SYS‑APU‑REQ‑254 in DOORS. Deviations: DES branch deferred due to queue time; documented in VRR minutes 2026‑06‑28.
- Data integrity and reproducibility: One‑click replay script rebuilds the M0.3 and M0.5 baselines on 64 cores in 14.2 and 19.7 wall‑clock hours; hash of AIP pressure field matches archive to within machine epsilon.
- Residual risk and next steps: Main gap is elevated error at α = +6° tied to larger separation; we have a DES pilot on the 19.4M grid showing improved separation onset but at 8× cost. Proposal: add WT points at α = +6° with refined rake and run DES on two geometries for downselect confidence.

Bottom line
Within the stated operating window, the model delivers the accuracy needed for PDR trades on screens and bleed. For excursions beyond +4° incidence or significant surface roughness (service life), treat outputs as indicative and pair with targeted tunnel data or higher‑fidelity DES before committing hardware changes.
