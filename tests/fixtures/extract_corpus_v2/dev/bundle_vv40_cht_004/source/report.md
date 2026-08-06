To: Priya Shah, CHT Workstream Lead
From: Martin Lopez, Thermal-Fluid V&V
Subject: Credibility summary for EV inverter cold plate CHT model (Fluent 2023 R2)
Date: 2026-08-06

Summary
We evaluated the conjugate thermal-fluid model of the Gen4 inverter cold plate plus IGBT stack for design decisions on fin pitch and TIM selection. The model predicts component case temperatures and plate pressure loss across 20–60 L/h coolant flow with 30% PGW at 25–40 C inlet. Decision impact is moderate (guides cooling layout before tooling) and consequence of a wrong call is moderate-high (risk of junction derating). We targeted error bands ≤5 C on peak case temp and ≤7% on Δp, with supporting evidence summarized below.

Modeling approach and fit for purpose
- Physics: Steady RANS SST (no transition) with conjugate heat in solids. Roughness via equivalent sandgrain ks = 15 µm (Ra = 1.6 µm), scalable wall functions; y+ ~ 1–2 on fins. Radiation neglected; rig heat loss audit shows <0.5% of heater power to ambient.
- Geometry: Full manifold and fin field included; fillets under 0.3 mm removed after sensitivity check (<0.2 C effect). TIM modeled as solid layer, t = 0.2 mm, k = 3 W/m-K; later represented as contact resistance Rc = 1.1e-4 m2-K/W based on coupon tests—both give indistinguishable results at target loads.
- Inputs: Inlet mass flow, 5% turbulence intensity; outlet static pressure. Temperature-dependent properties for PGW from ASHRAE tables; solid conductivities from vendor datasheets (IGBT baseplate k = 180 W/m-K).

Implementation checks and code quality
- Solver: Ansys Fluent 2023 R2, double precision; journaled runs only. User property subroutines unit-tested against tabulated values (max deviation 0.1%).
- Sanity tests: Internal check versus analytic laminar pipe heat transfer at Re = 1200 gave 0.3% error on Nusselt and 0.1% on Δp (same numerics).
- Vendor benchmark suite passed (12/12 cases).

Numerical error control
- Mesh refinement: 2.1M, 6.4M, and 18.7M cells; near-wall inflation to y+ ≈ 1. GCI on peak case temperature 1.8%, on Δp 0.6% (fine grid reference). Residuals <1e-6; energy imbalance <0.2%.
- Robustness: Alternate discretization (QUICK vs second-order upwind) changed Tmax by 0.4 C; Δp by 0.2%.

Comparison to test data
- Rig: Closed-loop setup with 30% PGW, cartridge heaters (500–1500 W), 12 TCs on case, 2 RTDs on coolant, Micromotion CMF for flow, Validyne DP for pressure. Measurement uncertainty: T ±0.3 C (k=2), flow ±0.5%, Δp ±0.25 kPa.
- Mapping: Same plate, same torque pattern on fasteners (preload 6.5 ±0.2 N·m), same glycol mix verified by refractometer.
- Results: Across 18 points (flows 25, 40, 55 L/h; powers 700, 1100, 1500 W; Tin 25 and 35 C), mean absolute error on peak case temperature 1.3 C (max 3.2 C). Δp error 4.0% mean (max 6.1%). No trend in residuals vs. flow or power.

Use of test data and parameter tuning
- One datum (40 L/h, 1100 W, Tin 25 C) used to set Rc from coupon-informed prior (0.8–1.4e-4 m2-K/W); once set, Rc was held fixed. Cross-check on remaining 17 points shows no bias, supporting limited tuning.

Sensitivity and uncertainty
- Input ranges: Mdot ±3%, heater power ±1%, Rc ±20%, ks ±30%, property fits ±2%.
- Screening: One-at-a-time shifts show Tmax slope of −0.06 C/(L/h) and +6.1 C per +1e-4 m2-K/W in Rc at 40 L/h.
- Global study: 250-sample LHS on the validated mesh predicts 95% interval of ±2.0 C on Tmax and ±5.2% on Δp at 1100 W, 40 L/h. First-order Sobol: Rc 0.51, flow 0.33, ks 0.09; others negligible.

Scope and limits
- Applicable when: 20–60 L/h, Tin 20–40 C, 30% PGW, heat 500–1500 W, single-phase liquid, Ra 1–3 µm, no boiling. Extrapolation to DI water or >60 L/h not supported; transition model not exercised; transient startup not covered.

Data management and review
- Reproducibility: GitLab project INV-CHT-042, meshes and journals under tags v1.3–v1.5; Fluent case/data CRCs logged. Hardware: RHEL 8.8, AMD 7713, 64 cores.
- QA: Checklist INV-QA-CHT rev C completed; model changes tracked via MRs. Independent read-across and spot reruns performed by Dr. L. Chen (not on design team); no blocking issues—she requested and verified the added QUICK sensitivity.

Human factors and SOPs
- Analysts certified to internal Fluent Level 2; pre-release checklist enforces wall-function y+ and energy balance checks. Peer handoff instructions included with run scripts.

Risk posture relative to decision
- Model informs fin pitch and TIM selection pre-tooling (influence medium). A wrong call could force heat spreader redesign (consequence medium-high). With validation errors within 3.2 C and quantified uncertainty ±2.0 C at nominal, the evidence meets the rigor we planned for this risk level.

Recommendation
Accepted for design decisions on fin geometry and TIM choice within the applicability stated above, subject to maintaining Rc at or below 1.2e-4 m2-K/W in production and using 30% PGW coolant. Decision recorded by M. Lopez and endorsed by P. Shah.

Next steps
- Add a transient heat-soak case for startup events.
- Extend validation to DI water to cover service variant B.
- Recheck ks once plated parts are available.
