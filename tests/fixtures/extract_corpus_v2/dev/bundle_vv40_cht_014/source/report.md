To:    Dr. K. Alvarez, Program Lead
From:  CHT V&V Team
Subj:  Credibility status for RF ablation catheter heat-transfer model (Sprint M6)

Quick take
- We are using the model to set safe power/irrigation envelopes for a 7F open-irrigated RF ablation catheter in the left atrium, with the esophagus 3–5 mm posterior. Decision metric: peak tissue temperature at 3 mm depth and lesion depth/width after 30–60 s. Consequence of a wrong call is high (thermal injury), and the model materially informs limits (medium–high influence). We therefore targeted aggressive evidence thresholds in the plan.

What we actually built
- Physics: 3D conjugate thermal-fluid model of blood, saline jets, electrode, epoxy, and myocardium. Incompressible flow with temperature-dependent properties; laminar assumed but bracketed with SST k-omega for sensitivity. Joule heating represented as a volumetric source in tissue and electrode via a quasi-static electric field solution; temperature-dependent electrical conductivity (0.43–0.8 S/m). Tissue perfusion via Pennes term outside the near-surface ablation zone.
- Geometry: Electrode, tip holes, and shaft from vendor CAD; myocardium block 20×20×15 mm; esophageal wall as an isothermal boundary 37.0±0.2 C at 4 mm posterior. Catheter contact angle 15°. Contact pressure 10–20 kPa producing 0.2–0.5 mm indentation (from benchtop).
- Boundary conditions: Blood inflow 0.15–0.30 m/s, 37 C; outlet zero gauge; irrigation 17–30 mL/min at 22 C; applied RF power 25–50 W with PI control matching generator logs.

Verification highlights
- Code-level checks: The custom heat-source UDF and perfusion toggle were exercised against an artificially forced benchmark (closed-form temperature field with a tailored source). Energy residual over the control volume was <0.2% at steady state. Unit tests for UDF I/O and mapping pass CI on each commit.
- Numerical error: Four meshes (1.2M to 9.6M cells) with local refinement at the electrode/tissue interface (min cell 20 µm). Second-order discretization, coupled solver; steady flow + transient heat. Spatial refinement study gives observed order 1.96 for peak temperature; extrapolated discretization effect 3.8% on peak temp and 2.6% on lesion depth. Time-step halving from 5 ms to 2.5 ms shifts peak temperature by 0.6 C; 5 ms retained. Residuals <1e-6; monitored integral energy plateaus within 0.3% over last 10 s.

Comparison to data
- Calibration: Only the thermal contact resistance and micro-gap conduction multiplier were tuned using three training cases (35/45/50 W at 17 mL/min, 0.2 m/s). Posterior mean contact conductance 7.5 kW/m^2-K (95% CI: 5.8–9.3). Model frozen thereafter.
- Validation set: 12 benchtop perfused-myocardium tests (porcine) at 25–45 W and 17–30 mL/min, two blood speeds (0.15, 0.25 m/s), fiber-optic probes at 3 and 5 mm. Lesion dimensions from 7T MRI (0.2 mm voxel). Measurement uncertainties: temp ±0.3 C (k=2), lesion dims ±0.2 mm, flow ±1%.
- Agreement: Mean absolute temperature error at 3 mm = 2.1 C; 95th percentile 4.0 C. Normalized RMS error on lesion depth = 9%; width = 11%. After accounting for both model and test uncertainty, all cases fall within a 95% total-error band set in the plan. One outlier at 45 W/0.15 m/s under-predicts depth by 15%, likely due to a char layer observed post-test (not represented in the model).

Uncertainty, sensitivity, and scope
- Inputs and ranges: Tissue thermal/electrical properties (±15% about literature), contact pressure (10–20 kPa), blood speed (0.15–0.30 m/s), irrigation (17–30 mL/min), esophageal wall temp (36.8–37.2 C). Latin Hypercube (N=200) propagated through the verified mesh/time step.
- Drivers: Global Sobol screening flags contact pressure (S1≈0.42), micro-gap thickness (0.23), and blood speed (0.18) as primary. Turbulence model choice (laminar vs SST) shifts peak temperature by <1.2 C; we include this as a model-form bracket in intervals.
- Applicability: The intended clinical envelope (25–45 W, 17–30 mL/min, atrial blood speed 0.15–0.25 m/s, contact force 10–30 g) sits inside the tested/validated space. We explicitly do not claim fidelity for steam pops, charring, or highly trabeculated surfaces.

Process controls and independence
- Software pedigree: Ansys Fluent 2023 R2; UDF Git tag rfcht-v1.7 (commit 9f4a1b2); run scripts in a Singularity container (hash 3c7…9a1). Input decks, meshes, and outputs tracked by DVC with SHA links to raw data.
- Test data handling: Lab team provided blinded validation files after we froze the model; we retained the three training runs solely for tuning. Instrument calibrations attached; bath and probe logs archived.
- Review: External SME (Dr. R. Ghuman) performed a red-team read and re-ran one case from scratch on a different workstation; reproduced peak temperature within 0.9 C and lesion depth within 0.3 mm. Action items (two minor doc gaps) are closed.

Bottom line
- For our risk posture (high consequence, medium–high model influence), the current evidence meets or exceeds the targets set in the modeling plan: robust grid/time-step studies, independent data with quantified test error, separation of tuning vs checking, uncertainty propagation with sensitivity to the key knobs, and reproducibility under configuration control.
- Remaining limitations: no steam/char physics; homogeneous myocardium (no fiber anisotropy); simplified esophageal representation. We propose retaining a 5 C safety margin on the 3 mm temperature threshold pending completion of two in vivo checks next quarter.

Ask
- Approve use of the model to inform the IFU power/irrigation table within the validated envelope, with the stated margin and caveats. We will maintain the containerized workflow and add the two in vivo points to the next validation update.
