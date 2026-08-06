To:    C&DH Thermal IPT Lead  
From:  J. Alvarez, CHT V&V Focal  
Subj:  Credibility memo — Avionics Bay Conjugate Thermal-Airflow Model (v3.2, Fluent 2023R2)  
Date:  06 Aug 2026

Summary
The conjugate heat transfer model of the NAVBUS-2 avionics bay is suitable for pre-PDR design trades and thermal margin allocation when used within the stated operating envelope. Evidence below covers modeling intent, numerical checks, comparison against test, input pedigree, uncertainty/sensitivity, controls/traceability, and user readiness.

Intended use and performance targets
- Purpose: predict card-edge and component case temperatures, and bulk air temperature/pressure drop to support fan sizing and 15 K thermal margin allocation.
- Acceptance thresholds (agreed in T-VV-127 Rev C): temperature RMSE ≤ 3 K with max error ≤ 7 K at thermocouple sites; pressure drop error ≤ 10%; 95% CI on peak case temp ≤ ±5 K for expected input variability.
- Applicability: forced convection in sealed bay, inlet 20–55 C, air speed 0.5–4 m/s, altitude sea level–10 kft; not for purely buoyant regimes or altitudes >10 kft without recheck.

Inputs and their provenance
- Geometry: native CAD from PLM drop 2026-06-10; vents/fan grill simplified by ≤2% open area difference (logged in change note CN-84).
- Power map: electronics team PWRMAP_0626, Line Replaceable Unit (LRU) total 410 W steady; ±5% uncertainty acknowledged.
- Materials: FR-4 orthotropic k measured by lab coupon test (T-LAB-332): in-plane 0.87 W/m-K, through-thickness 0.29 W/m-K; aluminum 6061-T6 k(T) from ASM; TIM contact resistance 1.1e-4 m^2K/W from squeeze-film test (T-INT-019).
- Boundary conditions: fan P-Q curve digitized from Delta BFB1012; curve fit goodness R^2 = 0.996; inlet air temperature from ECS model, ±1.5 C; emissivity 0.85 ± 0.05 from tape pull test.

Numerical setup and checks
- Solver: Ansys Fluent 2023R2, pressure-based coupled solver, double precision, transient ramp to steady.
- Grid: 8.6M poly-hexcore cells; 8 prism layers, y+ = 0.6–1.2 over heat sinks; wall orthogonality >0.14, skewness <0.28.
- Convergence: residuals <1e-5 (energy <1e-7); mass imbalance <0.3%; monitored peak case temp flat to <0.05 K over 1000 iterations.
- Refinement study: 4.1M/8.6M/17.3M cells; GCI (Richardson, p=1.9 observed) = 1.9% for peak case temperature, 3.2% for local h on fin tips; time-step study at 1e-3/5e-4/2.5e-4 s yields <0.3 K change at targets.
- Run-to-run repeatability: identical results across three nodes (AMD EPYC 64c) within 0.02 K; case/data CRC logged.

Physics choices and rationale
- Turbulence/heat transfer: SST k-ω with low-Re near-wall, fully resolved viscous sublayer; verified y+ treatment enables conduction–convection coupling on fin bases.
- Radiation: surface-to-surface (DO) included; delta on peak case temp <0.6 K but retained for completeness.
- Contact modeling: bonded interfaces for card-to-rail; explicit thermal resistance elements for TIMs per measured values.
- Air properties: temperature-dependent (Cunningham tables); PCB anisotropy enabled.
- Approximations: cable bundles homogenized as porous inserts with K = 3e-9 m^2 (from pressure drop bench), impact on bay Δp < 2%.

Comparison against hardware test
- Fixture: full-scale bay mockup in Thermal Lab Cell 2; 12 T-type thermocouples (±0.3 K, NIST cert), FLIR A655sc IR mapping (±2% emissivity corrected), MKS pressure taps (±0.25% FS).
- Test points: 22–50 C inlet, 1.0/2.5/3.5 m/s face velocity, total 9 conditions.
- Agreement: pooled RMSE 2.1 K, worst-case 5.4 K at a shadowed BGA; pressure drop error 6.0% mean; heat balance closure 98–101%.
- Data handling: TC-to-CAD registration documented; IR spots co-registered to within 1.5 mm; raw data stored in DMS-CHT-511 with calibration files.

Uncertainty and sensitivity
- Input variation study: 120-run Latin hypercube on inlet T, fan curve, TIM resistance, power split, emissivity; Sobol indices show TIM resistance (0.42) and inlet T (0.28) dominate peak case temp.
- Model choices sensitivity: switching to realizable k-ε (enhanced wall) changes peak by +1.4 K; disabling radiation +0.5 K; these are included in the error budget.
- Combined 95% interval on the critical component case temperature: ±3.8 K at nominal 2.5 m/s, meeting the ±5 K target.

Controls, people, and records
- Configuration: Git LFS repo CHT-NAVBUS with case/data, pre/post UDFs; tag v3.2, commit 9f2c7ab; solver build 2023R2 b306, container hash logged.
- QA: automated regression suite (15 canonical CHT cases) clean; JIRA trace links from requirements to runs; independent checklist I-REV-77 signed.
- Team: two analysts (Alvarez, Singh) with >1000 h each on electronics CHT; methods peer-reviewed by T. Nguyen (independent SME).
- Prior use: approach previously matched Orion avionics tray within 3 K (Ref: ORN-CHT-21).

Limitations and allowed uses
- Valid within geometry perturbations ≤5% open area and ≤2 mm heat sink height; larger deviations require rerun.
- Not approved for natural convection-only scenarios or operation above 10 kft without re-benchmarking.
- Post-processing scripts enforce consistent emissivity and TC mapping rules; users shall not override without reissue.

Decision
The model v3.2 is accepted for pre-PDR design trades and thermal margin allocation in the NAVBUS-2 avionics bay within the stated operating envelope, subject to maintaining configuration v3.2 inputs and staying within the defined geometry and environment bounds. It is not approved for flight certification or off-envelope predictions. Decision made by the Thermal IPT Lead following this memo and I-REV-77.
