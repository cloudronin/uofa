To: Priya Shah, R&D Thermal Lead
From: J. Kim, V&V Engineering
Subject: Status memo — CHT model for irrigated RF catheter tip
Date: 06 Aug 2026

Summary and intended use
We built a conjugate heat transfer model of the 7 Fr irrigated RF catheter tip to estimate peak metal temperature and outer surface temperature during bench RF delivery. The model is meant to set design margins and acceptance limits for verification tests (not for lesion prediction). Operating window assessed: RF power 5–30 W, saline irrigation 5–30 mL/min, bloodstream velocity 0.05–0.40 m/s, blood 36–38 C. Decision gate was ±3 C (or 10%, whichever larger) accuracy on peak metal temperature at the stated conditions.

Physics and assumptions
- Flow/thermal: steady RANS in the blood domain with k–ω SST; conjugate conduction in tip, braze, and shaft. Saline jets modeled explicitly (12 ports, 0.18 mm each).
- Radiation <0.5% of heat loss and neglected. Blood treated Newtonian above 0.1 m/s; for lower speeds, a viscosity adjustment per Carreau fit was included as a table.
- RF heat deposition represented as volumetric heat in the metal matched to delivered electrical power (measured at the generator terminals); one parameter (effective contact conductance at the braze) was tuned on a small dataset (see below), then held fixed.

Numerics and solver checks
- Discretization: finite volume, second-order in space and time. Near-wall mesh with y+ < 1 at the tip and shaft; 1.8M/3.6M/7.2M cell ladders used for refinement.
- Iterative criteria: residuals < 1e-6, global energy imbalance < 0.2%. For transient ramp/hold cases (0–5 s), Δt = 0.5 ms; halving Δt changed Tmax by 0.3 C.
- Mesh refinement study on 18 operating points: extrapolated peak metal temperature changed <1.5% from medium to fine; GCI on Tmax = 1.3% (95% conf.). Wall heat flux GCI = 2.1%.
- Code-level checks: reproduced textbook solutions for 1D conduction (error < 0.2%) and laminar heated pipe (Nusselt within 0.5% of 4.36). A manufactured-solution case for coupled advection–diffusion showed ~1.98 order in space. Energy conservation across the solid–fluid interface within 0.1% on all runs.

Inputs and traceability
- Geometry from CAD rev E43; step file hashed (SHA-256: e04d…a1c). Tip alloy k(T) and Cp(T) from vendor cert MTL-PI-2207; saline density/viscosity from CRC; blood properties from Sousa et al., 2011. Boundary conditions: power from inline meter (0.2 W accuracy), flow from Alicat Coriolis (±0.5% reading).
- Pre-processing checklist used to unit- and sanity-check all inputs; Python validations throw on out-of-range values. All decks and scripts in Git (repo med-cht-catheter, tag v1.6.2).

Bench comparisons
- Comparator: recirculating loop with bovine blood at 37 C, optical fiber sensors embedded flush with the tip (OSP-FBG, ±0.5 C). Flow conditioned to 0.05–0.40 m/s via Venturi and ultrasound cross-check. Twelve test points (powers 5–30 W, flows 5–30 mL/min, blood speeds 0.1–0.4 m/s) were reserved for model check; four separate points (10–20 W) used earlier to pin the single braze conductance value.
- Agreement on the 12 reserved points: mean absolute percent error on peak metal temperature = 6.4%; slope of predicted vs measured = 0.96, intercept 0.8 C, R² = 0.94. Surface-averaged outer temperature MAPE = 7.1%. No sign bias across the space.

Uncertainty and sensitivity
- Sources considered: numerical (mesh/time), meter accuracies, property scatter (kalloy ±5%, μblood ±10%), power splitting to the braided shaft (±3%), and saline jet targeting (±0.2 mm azimuth). Combined via Latin Hypercube (N=500) on two representative high-power cases; 95% band on Tmax ±2.1 C. Adding GCI in quadrature yields ±2.5 C.
- Global screening (Morris, 12 trajectories) points to RF power and bloodstream velocity as dominant. Secondary effects: braze contact conductance and saline flow split. First-order Sobol on a reduced set confirms ~0.58 contribution from power, 0.27 from bulk velocity.

Relevance of the bench to the use case
- Matched ranges for Re (700–5600) and Pr (6–24) to physiologic; buoyancy negligible (Ri < 0.02). No tissue present in the loop by design; the target metric is tip temperature, not lesion size. The electrical power fed to the metal was measured, so generator losses are not a confounder.

People, process, and independence
- Primary analyst: J. Kim (8 yrs CHT/medical). Independent technical check by L. Romero (Thermal SME, 12 yrs) covered assumptions, mesh studies, and data pairing; comments 7–12 in CR-324 resolved. A second analyst reproduced one test point in STAR-CCM+ within 1.1 C.
- Tools and QA: ANSYS Fluent 2024 R1 (build 24.1.108), Python 3.11 wrappers. CI pipeline (Jenkins) reruns three regression cases on each change. Docker image hash archived with each run; SLURM job logs retained.

Limitations and guardrails
- Below 0.08 m/s bulk speed, the Newtonian approximation starts to break; hold for these low flows is transiently treated but not fully validated. Model not approved to predict tissue temperature or lesion geometry. Use only with the v1.6.2 decks and the provided analyst playbook.

Risk and acceptance
- Hazard review rates an underestimated peak tip temperature as medium severity; acceptance band set at ±3 C (or 10%). With combined uncertainty ±2.5 C and observed bias small (slope 0.96), the model meets the gate in the stated window.

Decision
Approved for use in setting verification limits and design margins for peak metal and outer surface temperature of the irrigated RF catheter tip for 5–30 W RF, 5–30 mL/min irrigation, and 0.10–0.40 m/s blood speeds, subject to using repository med-cht-catheter tag v1.6.2 and the documented workflow. Not accepted for lesion size prediction or for bulk speeds <0.08 m/s. Decision by Priya Shah on 06 Aug 2026.

Next steps
- Add very-low-flow validation points (0.04–0.08 m/s).
- Extend uncertainty propagation across the entire grid using a surrogate to avoid prohibitive HPC cost.
