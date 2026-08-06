To:      AITR-3 Project Lead, Power & Thermal Subsystem
From:    L. Rivera, Thermal/Fluids V&V Lead
Date:    06 Aug 2026
Subject: Credibility status of the avionics cold-plate CHT model (STAR-CCM+ v2306)

Bottom line
- The current conjugate heat transfer model of the microchannel cold plate and avionics stack is suitable to answer PDR-level questions on maximum component temperatures and coolant-side pressure drop under worst-case steady operation in vacuum. Predicted peak baseplate temperature at the hottest FPGA is 78.6 C with a 95% interval of ±2.7 C; measured thermal-vac test data fall within this band. We are carrying a 5 C design margin to requirements.

What we compared to hardware
- We ran a thermal-vac chamber test with a flight-like cold plate, 12 RTDs embedded in the baseplate, five thermocouples on daughtercard hot spots, and a coriolis meter on the 50/50 water–glycol loop. Inlet temperature 25.0±0.2 C, mass flow 1.00±0.01 L/min, chamber pressure <1e-4 torr. The model-to-measurement mean absolute temperature difference across all 17 points was 1.4 C; worst case 2.3 C at the card-edge sensor. Pressure-drop error 3.2% against the differential transducer. Instrumentation uncertainties were propagated (RTD ±0.15 C, TC ±0.5 C, flow ±1%).

Physics choices and limits of the approach
- Full CHT: 3D conduction in Al6061 baseplate and chassis, temperature-dependent k(T); convective heat transfer in 36 microchannels (hydraulic D = 0.9 mm); radiation from exposed outer faces to chamber walls with measured emissivity (ε = 0.12 bead-blasted Al).
- Turbulence: k-omega SST with low-Re corrections; near-wall y+ < 1 across the wetted surfaces (12 prism layers, first cell height 8 µm).
- No phase change modeled; analysis is not valid for incipient boiling or gas ingestion. Heat release in FPGA/CPU represented as uniform volumetric sources per board-stack IR mapping; temporal transients >5 s were not addressed in this release.

How the mesh and numerics were checked
- Three systematically refined meshes (3.1M / 6.2M / 12.4M cells) with second-order spatial schemes and coupled solver. Richardson extrapolation of baseplate Tpeak gave a GCI of 2.1% on the production grid (6.2M). Global mass imbalance <0.05% and energy residuals <1e-6 stabilized; double precision and strict under-relaxation used.
- Time step independence for a representative 10 s startup transient showed <0.2 C difference between 5 ms and 2.5 ms steps; steady solution is used for acceptance predictions.

Sanity checks against known solutions
- Internal flow Nusselt number and friction factor at Re ≈ 4200 in a straight surrogate channel matched Gnielinski within 3.8% using the same wall treatment.
- Solid-only conduction benchmark (heater on rectangular slab) reproduced the 1D analytical temperature drop within 0.7%.
- Separate from vendor claims, we ran the project’s advection–diffusion MMS cases on STAR-CCM+ v2306 last year; observed second-order convergence in L2 norm for steady heat conduction and convective heat transfer with errors <0.5% at finest mesh.

Where the inputs came from and how trusted they are
- Material properties: Al6061 k(T) from in-house guarded hot-plate coupons (23–100 C) cross-checked to MatWeb; TIM (Bergquist GAP PAD 1500) effective conductance derived from compression tests at 10, 30, 50 PSI (0.85–1.35 W/m-K equivalent); emissivity measured with IR reflectometer (ε = 0.12±0.02).
- Heat loads from board bring-up logs at 1g worst-case code path plus 10% contingency; pump curve and motor heat leak from vendor P-V data (Parker 25-100).
- Boundary conditions trace to Requirement THR-042 and Power ICD rev E; all values and sources recorded in the run log.

Uncertainty and variability
- We quantified effects from: (a) mesh/truncation (2.1% via GCI), (b) property tolerances [k(Al), TIM, ε], (c) flow meter ±1%, (d) RTD/TC calibration, and (e) heat-load spread. Latin hypercube of 200 samples with Sobol indices: contact conductance at TIM dominates (S1 = 0.46), followed by mass flow (S1 = 0.21). Aggregated 95% interval on Tpeak ±2.7 C.
- Robustness to analyst choices: switching to Spalart–Allmaras with the same y+ shifts Tpeak by +0.8 C; increasing prism layers from 10 to 14 changes Tpeak by <0.2 C.

Team, tooling, and repeatability
- Analysts: two engineers (8 and 12 years CHT experience), STAR-CCM+ certified; code owners different from test operators. Independent review held 19 July; three action items closed (radiation view factors, TIM preload sensitivity, and pressure BC justification).
- Case, mesh, and post-processing scripts are under GitLab with tags (cht-coldplate v0.9.3). Jenkins CI rebuilds the Docker image (RHEL 8, OpenJDK 17, STAR-CCM+ 2306-R8) and replays a smoke test; solver version is pinned. JIRA shows no open defects on this model; two resolved issues relate to unit conversion and a flipped face orientation caught by automated checks.
- Run-time logs, random seeds for LHS, and figure scripts are archived; rerunning the baseline on a second node reproduced Tpeak within 0.1 C.

Prior use and applicability bounds
- The same workflow predicted within 2 C on the NanoLink-3 mission (2022) cold plate; documented in TN-CHT-2217. Current model is valid for steady operation, single-phase coolant, 20–35 C inlet, 0.7–1.2 L/min, and vacuum. Outside this envelope (e.g., microgravity two-phase onset or 60 C inlet), do not apply without rework.

Post-processing integrity and results handling
- Energy balance closes within 0.2% when integrating volume sources against coolant enthalpy rise and solid losses. Python post-processing computes area-averaged wall HTC from wall heat flux and Tw–Tb; cross-checked against STAR reports.

Programmatic controls and documentation
- Credibility/acceptance plan CHT-Plan-006 rev C approved at SDR; risk register tags boiling onset as not-covered. Configuration baseline is frozen for PDR; changes require CCB approval. All assumptions and limitations are listed in the model README and the draft V&V note (TN-CHT-2331 rev B).

Recommended next steps
- Execute short transient cases for 60 s power steps (already meshed, 1 week LOE).
- Add a two-point emissivity sweep (ε = 0.10/0.14) to tighten the upper tail of the uncertainty.
- Defer two-phase features to CDR with a targeted coupon test if requirement THR-059 (faulted pump) remains.
