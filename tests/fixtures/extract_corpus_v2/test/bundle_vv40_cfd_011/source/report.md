To: Priya Shah, VAD Program Lead
From: J. Ortega, CFD Lead
Subject: Status memo — pump-stage CFD credibility for Q4 gate

Short version: The current CFD model of the LVAD pump stage is good enough to guide the 2700 rpm design decision on hydraulic performance and to flag gross shear hotspots. It meets the tolerance bands we set with you in May. Below are the specifics you’ll need for the gate review.

What we checked first (does the model answer the right question):
- Intended use: predict head vs flow at 2700 rpm over 3–7 L/min and provide volumes of fluid experiencing elevated shear for a design screen. This informs impeller trim and diffuser vane angle before the next bench build.
- Decision stakes: medium. We still run bench loops before any clinical-facing decisions, but we want to avoid cutting the wrong blades. We agreed a ±5% accuracy window on head and a qualitative/no-regrets screen on shear maps.

Numerics and setup in plain English:
- Software: Ansys Fluent 2023 R2, double precision, pressure-based coupled solver, second-order spatial and temporal schemes.
- Physics: incompressible, isothermal RANS with k–ω SST (+curvature correction). Steady MRF for the rotating region. Working fluid set to match the water–glycerol test mix (μ = 3.5 mPa·s, ρ = 1040 kg/m³). A Carreau–Yasuda law was used only for the exploratory blood shear postprocessing; it did not feed back into the head–flow predictions.
- Geometry: CAD from the latest Rev D model. Tip clearances and balance holes were included. Tip gaps measured on the Rev C article by CMM (mean 85 μm) informed the nominal; we ran ±30 μm in sensitivity.
- Boundary data: inlet total pressure fixed to ambient; outlet mass flow specified per test point; rotor speed 2700 rpm. Temperature fixed at 25°C (as in the loop).

Did we chase down numerical error:
- Three-grid study with poly-hexcore meshes: 3.1M / 8.2M / 17.5M cells; y+ ≈ 0.7 at the finest. Head at 5 L/min changed by 2.1% (coarse→medium) and 0.9% (medium→fine); Richardson extrapolation gives an estimated remaining bias of 0.6% on head and 1.3% on torque at the fine mesh. Time step for pseudo-transient MRF ramp was 1e−4 s; halving it changed head by <0.2%.
- Convergence: residuals <1e−5 and flatlining of head/torque monitors to <0.1% over 500 pseudo-iterations. No backflow flags or non-orthogonality warnings.
- Solver pedigree: our team’s manufactured-solution runs on a rotating Couette case recover ~2nd order velocity convergence (slopes 1.95–2.1) with this Fluent build. We also matched the NAFEMS turbomachinery benchmark TM01 within 0.8% head using the same numerics last month.

Did we ground it with data:
- Comparator: closed-loop water–glycerol bench at 25°C (μ = 3.5 mPa·s). Same Rev D wetted geometry; same speed. Flow meter ±0.5% of reading; differential pressure transducers ±0.25% FS; repeatability 0.8% (1σ).
- Agreement: At 3/5/7 L/min, CFD head differed from test by +2.4%, +1.1%, and −1.8%, respectively. Combined experimental uncertainty on head is ±1.7% (k=2); the normalized discrepancy sits inside the acceptance band we set. Predicted shaft torque is within 3–4% of dynamometer readings; note that motor/bearing parasitics are not modeled, so this is a fair outcome without tuning.
- No parameter fitting was done to chase the curve; we only aligned viscosity and speed with the loop.

How touchy are the outputs:
- One-at-a-time sweeps: ±10% viscosity shifts head by ∓0.5–0.7%; inlet pressure offset of ±200 Pa moves head by <0.1%; tip gap +30 μm drops head 0.8% and grows the >150 Pa shear-volume by ~12%.
- Model form check: swapping to realizable k–ε changes head by −1.5% at 5 L/min; DES barely moved head (−0.6%) but increased near-blade shear extremes. We are holding SST for performance predictions, noting the shear-map caveat.
- Propagating input scatter: a 200-sample Latin hypercube over viscosity (±8%), tip gap (±30 μm), and outlet instrumentation bias (±0.5%) yields a 95% band of ±2.6% on head at 5 L/min on the medium mesh. Mesh-induced spread (from the refinement study) was combined in quadrature.

Are we comparing apples to apples:
- Flow regime and speed match the loop. The model includes the same balance-hole leakage paths and vane count. Temperature control in the loop kept viscosity within ±3% of nominal; we mirrored that in the uncertainty bounds. No pulsatility in either model or test.

People, process, and tooling hygiene:
- Fluent journal files and meshing scripts are under Git (repo CFD-Pump-RevD, tag v23R2_2024-06-14). Runs archived in our S3 bucket with containerized environment (Ubuntu 22.04, driver 535.54, Fluent 2023 R2 build 20230628). Nightly regression on two standard pump cases passed after this change set.
- Two-analyst review used the turbomachinery checklist (REV_7). Independent read-through by M. Kline (CFD Fellow) on 7/29; his only note was to report the DES shear outlier, which we now do.
- Traceability: bench dataset BL-0424; CMM report CMM-REV-C-011; this memo ties to JIRA CFD-2879.

Where it’s good enough vs where it isn’t:
- For the Q4 gate: the head–flow curve prediction satisfies our ±5% tolerance across 3–7 L/min with quantified numerical and input contributions. Use it to finalize blade trim.
- For blood damage: treat the shear maps as a screen only. We have not cross-checked against hemolysis data; plan is to run the bovine loop in September before locking a claim. Also, do not extend to pulsatile inlet or off-design speeds without rerunning the checks.

Bottom line: Green for hydraulic performance decisions at 2700 rpm; yellow for any claims involving blood trauma until validation is extended. Let me know if you want the run directory; it’s about 6 GB and I can share the S3 link.
