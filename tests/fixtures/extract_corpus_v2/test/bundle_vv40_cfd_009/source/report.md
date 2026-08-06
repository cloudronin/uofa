To: Project Lead, LVAD Program
From: CFD/Verification Lead
Subject: Status update on pump-flow CFD credibility for hemolysis downselect

Short version
- We are on track to use the current CFD workflow to rank impeller/volute variants for mean hemolysis and head–flow performance in the adult operating band. With the present evidence, the risk of a wrong decision at this stage is low-to-moderate and within the program’s tolerance.
- The model’s output uncertainty on normalized hemolysis (NIH) at 4 L/min, 1500 rpm is roughly ±25% (95% coverage) after combining numerics and inputs. Acceptance rule for downselect is met: the upper 95% bound for the lead design stays below 0.012 g/100 L.

What we built and why
- Decision context: Screen designs before bench builds; no patient labeling or final claims. If CFD mistakenly promotes a poor design, the consequence is wasted prototype cost and schedule (~moderate).
- Question of interest: Predict head–flow curve and blood-damage metrics for steady conditions representative of 3–5 L/min at 1400–1700 rpm.
- Model form: Transient sliding-mesh RANS with SST (curvature correction), double precision; non-Newtonian Carreau–Yasuda rheology applied below 100 s^-1 and switched to Newtonian above (sensitivity run covers both). Hemolysis computed using a Giersiepen-type power law applied to Lagrangian particle tracks with scalar exposure accumulation.

Evidence that the math and numerics hang together
- Code checks: Fluent 2023R2; gradient and pressure–velocity coupling verified on laminar MMS cases (Poiseuille and manufactured rotating lid) with observed ~2.0 order in L2 norm. Energy and angular momentum balances checked on a rotating pipe case (error <0.4%).
- Solution quality: Poly-hexcore meshes at 3.2M, 9.6M, and 22M cells; y+ ≈ 1–2 along blades and shroud. Time step 1.1e-4 s (~1° rotation at 1500 rpm); sub-iteration residuals fall ≥3 orders; mass imbalance <0.1%. Grid/time study gives GCI of 0.8% on head rise and 3.5% on pathline-averaged shear exposure; time refinement (×2) shifts NIH by 2.1%.

Are we solving the right geometry and boundaries?
- Geometry: CAD includes fillets down to 0.2 mm; tip clearance set to 150 ± 30 μm based on CMM of a prior build; volute tongue and leakage paths represented. No shaft flexibility (FSI) in baseline; a spot check with a 10 μm deflection field altered NIH by 2.7%.
- Operating points: Inlet flow 3/4/5 L/min; outlet pressure tuned to 70 mmHg at 4 L/min; inlet turbulence intensity 5% (measured at loop entrance during PIV); fluid properties matched to 40% Hct equivalent at 25°C.

Tie to data from the lab
- Bench comparisons:
  - Performance: Head–flow curve from CFD matches pump loop within ±3% across 3–5 L/min at 1500 rpm.
  - PIV: Refractive-index-matched glycerol-water in transparent volute; planar fields at impeller exit and mid-volute. RMSE of speed = 0.18 m/s vs 1.8 m/s mean (10%); swirl angle bias 4.1°. PIV uncertainty ±0.05 m/s; calibration documented.
  - Hemolysis: ASTM F1841 loop; NIH measured 0.009 ± 0.002 g/100 L at 4 L/min, 1500 rpm. CFD median 0.008; falls within test band without tuning to those data.
- Calibration: Hemolysis constant set from literature Couette datasets (not from our pump tests) to 1.75e-6 with 10-fold cross-check on nozzle data; no post hoc fitting at pump level.

Uncertainty, sensitivity, and scope
- Inputs and spread: Viscosity ±5%, tip gap ±30 μm, rotor speed ±0.5%, inflow turbulence intensity 3–7%, rheology transition rate ±20%. Latin hypercube (n=60) with multi-fidelity surrogate gives NIH 95% interval of ±22%; numerics add ~10% in quadrature to yield ~25%.
- Drivers: Total-effect Sobol indices—tip gap 0.41, turbulence model variant 0.22, hemolysis coefficients 0.18, bulk viscosity 0.12; others <0.1.
- Applicability: Adult operating band only (1400–1700 rpm, 3–5 L/min). Extrapolation to pediatric or pulsatile support is not endorsed. Cavitation excluded; NPSH margin in tests >4 m, and vapor fraction monitoring in a high-speed LES spot run was <1e-6.

Process discipline and independence
- Reproducibility: Runs scripted (Python/Fluent journals) and versioned (Git tag pumpCFD-v0.8). HPC environment, solver build, and mesh generation recipes archived; post-processing in signed Jupyter notebooks. Rerun of the 4 L/min case reproduced NIH within 1.3%.
- Review: Independent internal review by M. Liang (not on the analysis team) resulted in an outlet BC correction in rev B; sign-off recorded. External SME readout scheduled next sprint.
- Traceability: Requirements and acceptance bands tracked in Confluence with links to datasets and run IDs. All raw/processed lab data stored with calibration reports.

Odds and ends
- A single-wall-modeled LES check (8 impeller revolutions, 40M cells) produced NIH 8% lower than RANS, within the stated uncertainty.
- User qualifications: Primary analyst is a licensed PE with 12 years turbomachinery CFD; lab team calibrated PIV and hemolysis rigs to current SOPs.

Bottom line
- For the intended decision (ranking designs), the evidence shows the workflow is reliable enough. We will maintain the current acceptance rule (upper 95% bound on NIH < 0.012 g/100 L and head error <5%) and proceed with the next geometry set. Open items: complete the external review and add a second LES spot check at 5 L/min to retire model-form residual risk.
