To: Lina (CFD Lead)
From: P. Nguyen, V&V Coordinator
Subject: Status memo — fan module CFD credibility check-in (vv40 alignment)

Context and claims we intend to support
We use steady RANS to screen an in-duct axial fan for electronics cooling. The model is intended to predict pressure rise and shaft power for 0.12–0.24 kg/s mass flow at 2400–3600 rpm, ambient air at 25 C. Decisions: fan selection and operating point; consequences of a wrong answer are lower thermal margin but no safety hazard, so we’re targeting “design guidance” grade, not certification. Quantities of interest: Δp across the fan and torque (for power). Success criteria set up-front with the thermal team: within 5% on Δp and within 7% on power over the stated operating envelope.

Model setup and assumptions
- Geometry comes from the production CAD with tip clearance measured at 0.38 mm; fillets under 0.2 mm were suppressed.
- Flow is treated as incompressible, isothermal; Re ~3e5. No acoustics or tonal content assessment is claimed.
- Rotor handled with an MRF approach; no transient blade-passage resolution.
- Turbulence: k–ω SST with curvature correction. We ran two spot checks with Spalart–Allmaras; bias was ≤2.5% in Δp, which we capture as model-form spread.
- Upstream and downstream ducts are included at 4D and 6D respectively to minimize end effects. Outlet set to fixed static pressure, inlet uses total pressure and 3% turbulence intensity. Wall roughness set to 12 μm from profilometer data (not a tuning knob).

Numerics, reproducibility, and solver hygiene
- ANSYS Fluent 2024R1, double precision, second-order upwind for convection; pressure–velocity coupled scheme with pseudo-transient ramp.
- Residuals reduced 3–4 orders; mass/torque monitors leveled to within 0.1% over the last 800 iterations.
- Three grids: 6.1M, 12.4M, 24.8M cells; y+ ≈ 1 on the fine grid. Extrapolated Δp shows monotonic behavior; grid-induced uncertainty on Δp is 1.1% (power 1.9%). Iterative remainder estimated at <0.2% from restart tests.
- We sanity-checked the toolchain on canonical cases (laminar pipe, backward-facing step, rotating cavity); results match references within published tolerances. For one operating point we cross-ran OpenFOAM v10; Δp difference 1.8%.

Evidence against data
- Bench testing per ISO 5801 on the E-14 rig at Gantt Lab. Static taps at ±0.25% FS; mass flow via calibrated orifice plate; RPM via optical tach (±0.2%). Data uncertainty: 1.5% for Δp, 1.2% for power across the envelope.
- We reserved 3200 rpm at 0.18 kg/s as a hold-out not seen during setup. Across nine operating points, RMS difference is 3.2% for Δp and 4.6% for power; worst case is 5.6% on power near the low-flow end, where inlet swirl is more pronounced.
- Comparison method: we use percent error on QoIs and an error-normalized score combining model and test uncertainty; no re-scaling or offsetting. No post hoc tuning besides measured roughness.

Input fidelity and sensitivity
- Inputs trace to measurement: RPM from controller readback vs tach checked to within 0.1%; tip gap from CMM; ambient density from lab barometer/thermometer.
- One-at-a-time sweeps show Δp is most sensitive to RPM (∂Δp/∂RPM ≈ 1.7 Pa/rpm) and tip clearance (+0.2 mm increases leakage and drops Δp ~2.1%). Inlet turbulence intensity from 1–5% shifts Δp by <0.8%. These spans bracket expected shop-floor variability.
- We propagate contributions: grid + iteration (≈1.3%), model-form (2.0% from SST vs SA), and inputs (2.1% dominated by tip gap). Combined (root-sum-square) is ~3.2% on Δp. This underlies the acceptance argument.

Scope limits and applicability notes
- Do not use beyond 0.10–0.26 kg/s or outside 2300–3800 rpm; we did not include stall modeling or acoustic predictions. Cavitation is out of scope.
- The long ducts mitigate boundary recirculation; at the very lowest flow point, minor asymmetry in the test rig likely explains the observed power miss.

Process controls and independence
- Meshes, case files, and scripts are under Git LFS with tags; solver settings are captured in a run card. We can rebuild any figure from the repository in <2 hours.
- OS: RHEL 8.8; solver hardware: dual EPYC 7543, 256 GB. We log solver version and checksum for UDFs.
- An internal reviewer (A. Carver, not on the project) ran the checklist and spot-checked two meshes. The lab team collected validation data blind to our mid-course results.
- Team competency: analysts are SST-MRF fluent; two have completed Fluent advanced turbomachinery training. New hires follow an onboarding playbook for boundary setup and y+ targeting.

Bottom line
Given the modest decision risk and the achieved match to ISO 5801 data (within targets across the envelope), plus demonstrated mesh and input robustness, I judge the model fit for its stated purpose. The caveats on stall and acoustics are explicit; if the use case shifts toward near-stall operation or tonal noise, we will need transient URANS/LES and new validation data.
