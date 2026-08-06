To: A. Patel, Pump Program Lead
From: J. Nguyen, CFD V&V
Date: 06 Aug 2026
Subject: Credibility check on LV-23 blood pump CFD for P–Q screening

Context and scope
We assessed the current CFD model of the LV-23 centrifugal pump against our risk-informed expectations for using it to screen design variants on head–flow performance at 2400–3200 rpm. The same setup has been informally used to estimate shear exposure as a proxy for hemolysis; that use is included here only insofar as we can judge its trustworthiness.

Model setup (summary, with issues called out inline)
- Geometry: CAD of Rev D impeller, shroud, and volute as-built (laser scan aligned via best-fit). No rotor–stator clearance variability modeled; nominal 120 μm gap applied everywhere.
- Fluid: Newtonian water–glycerol mix intended for μ = 3.5 cP at 37 C. Note: the bench log for the “validation” run shows μ = 4.2 cP at 35 C on Day 2; this mismatch is not reflected in the CFD inputs, which assume 3.5 cP and 37 C throughout.
- Turbulence/near-wall: The deck header states k–ω SST with integration to the wall; target y+ ≈ 1. However, two postprocessing notebooks (runs LV23_021 and _022) reference “realizable k–ε, scalable wall functions” and report y+ = 35–60 on blades. Residual plots match the k–ε solver settings for those runs. It is unclear which settings generated the performance curves cited below.
- Motion and numerics: Frozen rotor between impeller and volute for throughput runs. Solver notes say Fluent 2023 R1, coupled pressure–velocity. The journal files in the run directory are tagged 2022 R2 and use SIMPLE. This likely matters for separation in the tongue region.
- Boundary data: Inlet fixed mass flow, outlet static pressure. Turbulence intensity assumed 5% at inlet; the bench pitot survey notes 2% ±0.5% at the loop entrance. We did not propagate that difference.

Mesh and solution behavior
- Three meshes: 2.1M / 4.2M / 8.3M cells, poly-hexcore, prism layers aiming for y+ < 1 (but see note above).
- Convergence: Momentum residuals drop ~3 orders; head stabilizes within 0.8% over the last 400 iterations on the medium grid. Backflow is present at the outlet in the coarse case at 2400 rpm.
- Mesh refinement check: Reported GCI for head at 2800 rpm is 1.7% (fine vs. medium). However, the coarse-grid run labeled 2800 rpm used 2700 rpm (journal shows rpm=2700). That undercuts the nominal order estimate. Additionally, time step differs across grids (0.5 ms coarse, 0.25 ms medium, 0.2 ms fine), so purely spatial effects are confounded.
- Sensitivity blip: A one-at-a-time test on the blade tip gap (±40 μm) changed predicted head by 4.8% at 3200 rpm; this is not reflected in the uncertainty budget table, which lists geometry tolerances as “negligible.”

Comparison to bench data
- Data set: Recirculating loop, Coriolis flowmeter (factory cal last year; field check shows +5% drift), two differential pressure taps across the pump. Four points taken per speed, but the plot in the report shows three points at 2400 rpm; one run was discarded for bubbles.
- Agreement: Using the runs we could confidently match, predicted head is within 6% mean absolute at 2400–3200 rpm for Q = 2.5–4.5 L/min. At 2000 rpm, underprediction is 12–15%, and the model sometimes exhibits a weak recirculation near the tongue that is not seen in dye visualization.
- Hardware differences: The loop used a 3/8 in ID cannula; the CAD and CFD still assume 10 mm ID pipes. The team notes this as “minor,” but the added minor-losses shift the operating curve and muddle back-calculated pump head.

Shear/hemolysis proxy
- We used a scalar exposure integral with constants from Giersiepen. A sweep of the C coefficient ±20% changes the cumulative exposure by 15–22% for a nominal duty point, contradicting the slide deck statement that “RBC model selection is not material.” No comparison against any hemolysis rig data was performed.
- The Newtonian assumption may be fine at >100 s−1, but near-stall and in recirculation pockets we see shear <50 s−1. The claim in the kickoff notes that “non-Newtonian effects are out-of-scope and immaterial” is not supported.

Traceability and repeatability
- Case setup is scripted (journal + Python driver) and in Git (tag v0.9.3). HPC run cards reference a license feature that expires in Sept; reruns last week fell back to a different solver flavor, leading to the version inconsistency noted earlier. We could replay the medium grid at 2800 rpm; the fine grid stalled on a queue change.

Acceptance thresholds and risk framing
- The initial plan of record says “within 5% on head and 5% on flow at 2400–3200 rpm.” In the sign-off slide for Sprint 18 the tolerance is quoted as “10% band acceptable for downselect.” We have not documented a rationale for relaxing that bar.
- For hemolysis, the Sprint 18 slide says “rank-order only,” but the memo to QA last month states “absolute predictions expected within ±25%.” Those two intents conflict.

Bottom line
- Strengths: Within the 2400–3200 rpm window, the model captures the pump curve trend and magnitude to about 6–8% against available data, provided we accept the fluid-property and loop-geometry mismatches. Automation is decent, and the mesh is reasonably resolved where it matters on the blades.
- Weak spots: Mixed messages on turbulence model and wall treatment; mesh study not clean due to operating-point drift; bench comparison confounded by viscosity and tubing ID differences; acceptance criteria not consistently stated; shear-based damage estimates vary more than advertised.

Decision
By agreement of the CFD lead (J. Nguyen) and the product owner (A. Patel), the current CFD setup is accepted for ranking design variants on head–flow performance at 2400–3200 rpm, subject to a 10% performance tolerance and using Newtonian μ = 3.5 cP in both model and bench. It is not accepted for predicting absolute hemolysis or for operation at 2000 rpm and below. Revisit after: (1) reconcile turbulence model/wall treatment, (2) rerun mesh refinement at fixed rpm and time step, and (3) align bench fluid properties and tubing with the CAD.
