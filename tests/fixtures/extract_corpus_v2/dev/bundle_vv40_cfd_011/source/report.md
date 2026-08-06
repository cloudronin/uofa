To:     Elena Park, Pump Upgrade Program Lead
From:   V&V Team (CFD): R. Shah, L. Nguyen
Date:   2026-08-06
Subject: Credibility memo — Stage A3 pump CFD for head/efficiency predictions

Why we built this model and what decision it supports
- Purpose: Predict head rise, shaft power, and hydraulic efficiency for the Stage A3 centrifugal pump to decide on a 1.5% impeller trim and confirm motor sizing for 2400 rpm service in non-cavitating water.
- Consequence of error: If the model under-predicts head by >5% at low-flow or BEP, we risk trimming too much and missing the contract point; if it over-predicts, we may oversize the motor. Program impact: moderate (schedule/cost) but not safety-critical.

Model setup and key assumptions
- Solver: Ansys CFX 2024 R1, double-precision, steady mixing-plane approach with stage averaging between impeller and diffuser; transient sliding-mesh spot checks at BEP.
- Physics: Incompressible RANS, k–ω SST with curvature correction; fully turbulent assumption. Cavitation and gas entrainment not modeled (NPSHa margin >3 m at test and field points).
- Geometry: As-built impeller/diffuser from blue-light scan (±20 µm) including tip clearance and fillets. Labyrinth leakage path included.
- Fluids/properties: Water at 22 ± 1 °C; ρ = 997 kg/m³; μ = 0.955 mPa·s. Wall roughness from coupon measurement: 3 ± 1 µm equivalent sand.

Software pedigree and code checks
- Vendor regression suite passed; no known solver defects relevant to rotating machinery in R1.
- Our team’s method-of-manufactured-solutions harness (advection–diffusion and rotating frame advection) exercised the build: L2 norm convergence rates 1.94–1.99; asymptotic error <0.4% on refined grids.
- Case automation and I/O scripting unit-tested; checksums recorded for mesh and BC files.

Numerics quality and convergence
- Meshes: 6.2 M / 12.5 M / 25.1 M cells; 30 prism layers; y+ = 0.8–1.5 on both blade sides. High-resolution scheme for momentum, second-order for pressure; robust advection boundedness on.
- Iterative convergence: Residuals <1e-5 (RMS), mass/energy imbalance <0.2%, torque and head monitors flat to <0.1% over last 500 iterations at each flow point.
- Time effects: Transient sliding-mesh at BEP (1°/step, 5 revs) differed from steady stage-averaged head by 0.6% and efficiency by 0.3 points, justifying steady runs for the performance curve.
- Grid sensitivity: Richardson extrapolation between medium/fine yielded observed order 1.95. Estimated mesh-induced effect: 0.7% on head and 1.2% on torque at BEP; similar across 0.6–1.3 Q/QBEP.

Boundary inputs and their pedigree
- Inlet: Total pressure set from calibrated pitot rake (±0.1% FS); turbulence intensity 5 ± 2% from upstream screen correlation.
- Outlet: Static pressure matched to test loop backpressure; diffuser exit swirl target checked against five-hole probe data.
- Leakage rate imposed from bench measurement (0.6 ± 0.2% of main flow). Surface roughness from profilometry reported above.

How it stacks up against test data
- Validation data: Stage A3 rig test (N = 2400 rpm) with 6 flow points (0.6–1.3 QBEP). Instrument uncert.: torque meter ±0.3%, differential pressure transducers ±0.1% FS; flowmeter ±0.4% of reading. Data reduced per ASME PTC 10 procedures.
- Agreement: Mean bias on head −1.8%; max discrepancy 3.2% at 0.6 QBEP; efficiency within 1.5 percentage points at all stations. Diffuser exit swirl within 3° at BEP and 1.1 QBEP. No cavitation observed in tests; spectrograms clean.

Sensitivity, tuning, and variability
- No tuning of turbulence coefficients. Only physical inputs set from measurement (leakage, roughness). No retroactive adjustment to match head.
- Local perturbation and Sobol screening at BEP (Latin hypercube, 80 samples): head most sensitive to leakage flow and roughness (first-order indices 0.38 and 0.22), weakly to turbulence intensity (0.06).
- Propagated input variability (TI, roughness, leakage) gives 95% interval on head of ±1.7% at BEP; combining with mesh effect (root-sum-square) yields ±1.9%. Model–test spread across the curve adds an empirical model-form component; taking the standard deviation of residuals (1.4%) leads to a composite predictive band ≈ ±2.4% on head for the COU.

Where it can and cannot be used
- Supported: Single-phase water, 15–30 °C, μ ≤ 3 mPa·s; N = 2400 rpm; flow range 0.6–1.3 QBEP; NPSHa ≥ NPSHr + 1 m. Wall roughness within 1–5 µm; leakage within 0.3–0.9% of flow.
- Not supported: Cavitating operation, fluids with μ > 10 mPa·s, sand-laden or gas-entrained mixtures, blade damage or significant fouling, off-speed >10% from 2400 rpm, extreme pre-swirl at inlet.

Traceability, reproducibility, and review
- All case files, meshes, scripts, and post-processing live in GitLab repo CFD-PUMP-A3@6b91f6a; solver image pinned (container hash 3f2c…e9). Run cards and checklists completed for each operating point.
- Independent check: J. Alvarez (Turbomachinery CFD, not on project) reproduced BEP result on a separate workstation with OpenFOAM v10 + γ–Reθ transition model; head within 0.9% of our CFX result, lending confidence in model form robustness.
- Analyst competence: Primary solver owner (R. Shah) 10 yrs rotating machinery CFD; peer mentoring log completed. User guide for replaying runs attached in repo.

Decision
Given the demonstrated agreement with rig data across the intended operating window, quantified numerical uncertainty, sensitivity characterization, and clear limits of use, the Stage A3 CFD model is accepted for predicting head, shaft power, and hydraulic efficiency for impeller trim assessment and motor sizing at 2400 rpm in non-cavitating water between 0.6–1.3 QBEP. This acceptance, approved by the V&V Lead (L. Nguyen) and Project Engineering (E. Park), is subject to:
- Using the documented steady stage-averaged setup with y+ < 2 and the specified boundary inputs, and
- Staying within the applicability bounds stated above.
Use outside these conditions is not approved.
