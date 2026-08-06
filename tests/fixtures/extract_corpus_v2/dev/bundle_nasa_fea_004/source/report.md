To: LTV Structures Lead
From: M&S Working Group – FEA Subteam
Subject: Credibility summary for the LTV Avionics Shelf Bracket static strength model (Abaqus/Standard 2022 HF6)

Context of use
We intend to use the bracket FEA to close yield and ultimate margins for quasi-static launch/landing load cases up to 12 g resultant, ambient temperature, no thermal gradients. Buckling, fatigue, and vibroacoustic response are handled in separate analyses and are out of scope for this memo.

Model setup and simplifying choices
- Geometry: CAD from PDM rev D; fastener holes and fillets modeled as-built. Thread detail omitted; bolt shanks represented with solid cylinders and connector elements for preload.
- Elements: C3D10 in fillets and hole nets; C3D8R elsewhere with hourglass control. Contact between bracket and shelf modeled with small-sliding, μ = 0.2 (dry anodized Al-on-Ti).
- Material: Ti-6Al-4V per MMPDS-17, room temperature; elastic–plastic with isotropic hardening used for the 1.25× limit checks; linear elastic for allowables at 1.0× limit.
- Loads/constraints: Interface to the chassis modeled as fixed at bolt patterns per ICD-421; pretension of 7.5 ± 0.75 kN per fastener; applied shear and tension consistent with Dynamics load card LTV-STAT-012.

Numerics and solution behavior
- Mesh refinement: Three grids (0.8 mm/0.5 mm/0.35 mm target in hotspots; 160k/430k/1.18M elements total). Peak von Mises at the fillet converged monotonically; Richardson estimate gives 2.4% numerical uncertainty; total strain energy change <1% between last two meshes.
- Solver controls: Full Newton with line search; max residual <1e-6; contact penetration <0.5% of element size; no cutbacks at 1.0× loads; at 1.25× loads 2 cutbacks, final equilibrium reached.
- Code confidence: We ran internal benchmarks (cantilever, plate with a hole, Hertzian contact). Errors vs. closed form: 0.7%, 2.2%, and 1.9% respectively on refined meshes. Vendor QA notes (SIMULIA QA report 2022HF6) on element patch tests are on file.

Data pedigree
- Mechanical properties: MMPDS-17 A-basis; confirmed with supplier cert 24-117 (heat 7X31). Density and CTE from same source.
- Joint data: Torque–tension scatter from shop tests on NAS6205-xx with Al spacer stack; R2 = 0.94; used slope to set preload tolerance.
- Loads and environments: Provided by GNC/Dynamics Rev C; uncertainty of ±3% on combined load per their memo.

Comparison to hardware
We tested a flight-like bracket (print B) with 12 g resultant quasi-static using the MSFC 100-kN frame. Eight strain gauges (Vishay CEA-XX) and DIC measured strains and deflection. After adopting the test-measured preloads, the model-to-measurement deltas were:
- Strains: mean bias +3.1%, worst-case +7.8% at G5; acceptance limit ±10%.
- Tip deflection: +4.6% high vs. DIC; acceptance limit ±10%.
No damage or yielding observed in the test; visual inspections and post-test dimensional checks were nominal.

Variability and drivers
- Input spread: E ±5%, preload ±10%, friction 0.15–0.25, load ±3%.
- Propagation: 500-run LHS on a quadratic response surface fit to seven high-fidelity FE runs. 95th percentile hotspot stress at 1.0× loads is 612 MPa; margin to yield = 0.18 using 724 MPa. Coefficient of variation in peak stress ≈ 4%.
- Influence ranking (Morris screening): Preload and friction dominate hotspot stress; elastic modulus weakly influential.

Process, people, and records
- Analysts: Lead (R. Shah) 12 yrs nonlinear FEA; peer (C. Nguyen) 8 yrs; both completed Abaqus 2023 training and NASA-7009B refresher this spring.
- Independent check: Red-team review (J. Ortega, G. Patel) complete 12 July; comments on bolt modeling and contact stiffness addressed in rev G.
- Planning and traceability: Analysis plan AP-STR-087 approved 30 May; success thresholds set there. Inputs, scripts, and ODBs are under Git LFS tag v1.7; solver version locked; run logs and machine info archived.
- Execution environment: JSC Hera cluster, RHEL 8.8, Intel OneAPI 2023; runs repeated on a Windows workstation matched within 0.5% on key metrics.

Boundaries you should assume
- Valid only for 15–35 °C and dry interface; no galvanic layer modeled.
- Not to be used for fatigue life, random vibe response, or post-yield redistribution beyond 1.25× limit.
- Geometry allowable per PDM rev D; any hole resizing or surface treatments require recheck.

Documentation and prior use
- Full report STR-FEA-1159 rev G, test report TEST-STAT-221, and correlation notebook are posted in Windchill. Similar bracket family analyses on CLPS lander (2022) showed comparable test-match quality.

Decision
Based on the above, the FEA model is accepted for demonstrating positive yield and ultimate margins for the LTV avionics shelf bracket under quasi-static combined loads up to 12 g within the stated environmental bounds. It is not approved for fatigue, dynamics, or thermal problems. Decision by the LTV Structures Lead and the M&S Working Group on 06 Aug 2026.
