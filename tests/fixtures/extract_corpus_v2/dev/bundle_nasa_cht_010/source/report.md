To: Lunar Lander Avionics IPT Lead
From: Thermal/Fluids Analysis Team
Subject: CHT V&V status — LL-PDU cold plate Rev C
Date: 06 Aug 2026

Purpose
We assessed the credibility of the conjugate heat transfer model used to size the liquid-cooled cold plate for the Lander Power Distribution Unit (PDU). The model predicts peak device junction temperatures and loop pressure drop across the expected mission envelope.

Summary
The current analysis set (Rev C) supports design decisions for Re ≈ 3,500–9,000, total heat input 0.6–1.5 kW, and PAO-6 coolant inlet temperatures 15–45 C. Predicted P95 peak junction temperature under worst credible inputs is 78.9 C vs an 85 C limit. Evidence below addresses geometry treatment, physics choices, numerical quality, data pedigree, and independent scrutiny.

Key evidence and status
- Physics and closure models: 3D CHT with RANS turbulence (k–ω SST, low-Re formulation) and near-wall resolution at y+ < 1. Solid regions include Al 6061-T6 base (k = 167 W/m·K), Cu heat spreaders (k = 385 W/m·K), and TIM layers modeled as thin resistances. Radiation to a 250 K sink (ε = 0.8) included; buoyancy neglected (microgravity and high Re dominate).
- Geometry representation: CAD defeatured per TFA-23 guideline. Fillets <0.3 mm, embossed logos, and non-wetted screw threads removed; microchannel lands, manifold splitter radii, and device footprints retained. Comparison to as-built CMM shows dimensional deviations < ±0.05 mm in flow passages.
- Boundary conditions: Inlet mass flow 0.12–0.24 kg/s (pump-controlled), inlet T 20–35 C; outlet static pressure set via loop map. Heat loads per device from electrical characterization (±1% meter uncertainty). External faces either adiabatic or radiating to chamber shroud; vacuum 10^-4 Pa.
- Input data pedigree: PAO-6 thermo-physical properties from AFIT dataset, verified by bench viscometer/densitometer to within 2%. TIM are Shin-Etsu X23; through-thickness resistance measured on coupons: 0.2 ± 0.04 K·cm^2/W. Surface emissivity measured with portable IR reflectometer (ε = 0.78–0.82).
- Numerical quality: Poly-hexcore meshes at 2.1M/4.8M/9.6M cells. Second-order spatial/temporal discretization; residuals below 1e-6; global energy imbalance <0.1%. Grid refinement yields GCI of 1.8% for peak device temperature and 3.5% for pressure drop. Iterative error <0.2 K based on last-decade slope.
- Transients: Startup transient checked with 0.1 s and 0.05 s steps; peak overshoot difference 0.6 K. Steady-state used for sizing; time resolution limits documented.
- Solver trustworthiness: ANSYS Fluent 2024R1 under our SQA plan SP-CHT-004. We re-ran a heated turbulent channel (Reτ ≈ 395) and a canonical plate-to-fluid CHT case, matching literature Nusselt to within 2.3% and 3.1%, respectively.
- Test correlation: Cold plate breadboard tested in TVAC with 27 type-T thermocouples (±0.5 K after in-situ calibration) and IR camera (FLIR A6750sc). At 1.2 kW, 0.18 kg/s, 25 C inlet: mean device temperature error 1.5 K; max local error 3.2 K. Loop ΔP prediction within 5%. Two TC channels drifted; excluded after calibration check.
- Separation of tuning and check-out: Only TIM resistance was adjusted within measured uncertainty bounds using coupon data, not the system test. No post-hoc “fitting” to the TVAC dataset.
- Uncertainty propagation: Latin Hypercube, 500 samples over measured input ranges: flow (±2%), heat (±1%), materials (k_Al ±5%, k_TIM ±20%), surface ε (±0.05), roughness (Ra 1–5 µm). P95 peak device temperature 78.9 C; TIM accounts for 61% of variance, flow 24%.
- Sensitivity and margins: Sobol indices flag TIM, flow rate, and channel roughness as dominant. A degraded-pump case (−10% flow) keeps peak below 82.5 C.
- Applicability bounds: Valid for single-phase PAO, Re 3.5k–9k, inlet 15–45 C, total heat ≤1.5 kW. Not assessed for g-loads >2 g, off-nominal cavitation, or coolant contamination; no boiling modeled.
- Cross-code check: OpenFOAM v2312 (chtMultiRegionFoam) reproduced Rev C case within 2.7 K peak and 7% ΔP using matching wall treatment.
- Post-processing hygiene: Area-weighted film coefficients, wall y+, and local Biot numbers monitored; no unphysical negative HTC observed. Balance checks archived.
- Team capability: Two analysts with 8–12 years CHT experience; Fluent and OpenFOAM advanced training certificates on file. Calc-checklist completed and signed by a different engineer.
- Independent review: Aero-Thermal Red Team (not on the design line) conducted a walkthrough; they caught an erroneous emissivity assumption early (fixed before TVAC). Action items closed.
- Configuration control: Meshes, case files, and post-processing scripts in GitLab (tag LL-PDU-CHT_RevC), with DOORS links to thermal requirements. CI pipeline re-runs smoke cases on commit.
- Traceability and reproducibility: TVAC raw data (NI TDMS), calibration sheets, and solver decks archived in Windchill; Monte Carlo seeds recorded. Replays on a different workstation matched within 0.1 K.

Limitations and next steps
- Plan a system-level thermal balance test with the full avionics stack to confirm device-to-base contact modeling and enclosure radiation paths.
- Extend UQ to include pump wear-out drift and possible filter fouling.
- Evaluate a low-roughness coating option to reduce ΔP while preserving HTC.

Overall assessment
Within the stated operating window, the analysis set provides defensible predictions for temperature and pressure drop with quantified numerical and input uncertainties, independently reviewed and tied to relevant test data. No open red flags for CDR.
