To:    Axiom-3 Avionics Cooling IPT Lead  
From:  M. Ramirez, Thermal/Fluids V&V  
Date:  2026-08-06  
Subj:  Credibility memo — CHT model for avionics cold plate sizing (Fluent 2024 R2)

Summary
We evaluated the conjugate heat transfer model used to set the A3 avionics cold plate flow and plate thickness for CDR. The model couples 3D RANS-based coolant flow with solid conduction through the plate and chassis, including interface resistances and radiation to the enclosure. Based on the evidence below, the model is fit for the stated purpose within the specified operating envelope.

Key evidence, by topic
- Intended use and stakes: The simulation informs coolant setpoint (270–280 K), pump schedule, and minimum margin to 358 K allowable junction temperature during worst-case dissipation. Acceptance criterion agreed at SRR: P95 predicted hottest component ≤ 355 K (3 K margin to limit).
- Physics and idealizations: Single-phase water, constant pressure loop; no boiling modeled. SST k-ω with low-Re treatment (y+ ≈ 0.8 on wetted walls). S2S radiation between electronics and inner enclosure (ε = 0.78 boards, 0.12 bead-blast Al). Geometry trimmed for non-participating fasteners; fins and coolant passages are exact CAD. Thermal interface material (Berquist Hi-Flow 225) represented via thin-layer with fitted contact conductance.
- Governing equations/solver details: Ansys Fluent 2024 R2, pressure-based coupled scheme, second-order in space; pseudo-transient with local time-stepping to accelerate convergence. Double precision, GMRES linear solver with 1e-8 inner tolerance.
- Solution quality checks: Three systematically refined meshes (fluid: 3.1M / 7.2M / 14.9M cells; solid: 1.4M / 3.1M / 6.3M tets). Richardson extrapolation on peak component temperature gave 0.9 K estimated remaining grid effect at production mesh; temperature and pressure residuals < 1e-6; global heat in minus heat out within 0.3%.
- Software and configuration control: Case/data, preprocessing scripts, and journal files are in GitLab repo A3-CHT under tag v1.7.2; solver build documented (Fluent 2024 R2 Build 24.2.91). Meshes archived with md5 checksums; automatic CI reruns smoke tests on meshing scripts after each change.
- Code confidence: We relied on vendor QA and ran in-house checks: MMS for steady conduction with an imposed source term (error norms converge second order); laminar duct heat transfer recovers Gnielinski Nusselt within 1.6% on the fine grid.
- Input pedigree: Material properties from NIST REFPROP (water, temperature-dependent), Al6061-T6 conductivity from MMPDS-17, PCB stack per vendor stack-up (CTE, k) with C of C on file. Heat loads trace to EE Rev G power budgets with 10% test-delta included.
- Independent look: External reviewer (J. Oh, IV&V) replicated one operating point on a coarsened grid using STAR-CCM+ 2023.3; hot-spot temperature differed by 1.8 K; flow distribution within 2.5%.
- Benchmarking against data: Thermal-vac chamber test TVC-042 ran a flight-like cold plate with surrogate heaters and calibrated inlet flow/temperature. 14 T-type thermocouples (±0.3 K, ISO 17025) and IR (FLIR A6750sc, emissivity-corrected) provided temperatures. Model-to-test deltas: mean bias +0.7 K; worst-point +2.9 K at low-flow case. Coverage: three flows (0.035/0.045/0.060 kg/s) and two inlets (270/280 K).
- Parameter fitting: TIM conductance set to 9,500 W/m2-K from separate coupon tests (ASTM D5470); no tuning against the system-level TVC-042 data. Remaining inputs fixed from measured values with uncertainties carried.
- Sensitivity: Morris screening followed by variance-based indices showed peak temperature driven primarily by flow rate (first-order 0.58), TIM conductance (0.22), and board emissivity (0.08); others negligible.
- Uncertainty roll-up: Monte Carlo with 500 samples propagated input spreads (flow ±2%, inlet T ±0.2 K, TIM ±15%, emissivity ±0.05). For the hot case (0.045 kg/s, 280 K), peak temperature P95 = 352.9 K; mean 350.8 K; SD 0.7 K.
- Range of validity: Evidence supports 0.035–0.060 kg/s, inlet 270–280 K, single-phase flow, ambient pressure thermal-vac. Extrapolations beyond 320 W total dissipation or any two-phase onset are outside scope.
- Numerical robustness: Restarted from disparate initial fields; all runs converged to the same peak temperature within 0.2 K. Tightened under-relaxation and alternative discretization (QUICK) changed peaks < 0.4 K.
- Test representativeness: Hardware boundary conditions in TVC-042 matched model within measurement error (flow ±0.15 g/s, inlet T ±0.1 K). Surface finishes and coatings matched flight process specs per travelers.
- People and practices: Primary analyst holds Fluent advanced training and has 10+ yrs CHT experience. Modeling guide A3-CHT-MG Rev C followed. All runs undergo two-person review before results release.
- Documentation and traceability: VVUQ plan A3-CHT-VV-PLN Rev B defines acceptance metrics and cases; run matrices, inputs, and post-processing notebooks are stored in Vault with DOORS links to requirements.
- Cross-checks/alternates: A 1-D thermal resistance calc predicted plate-to-coolant temperature drops within 6% of CFD; provides sanity bound on pressure drop and heat pickup.
- Limitations noted: Radiation uses S2S with view-factor clustering; not resolved for small cavities (<2 mm gaps). Contact pressure dependence of TIM not modeled explicitly; captured via tested conductance. No vibration-induced gap changes included.

Decision
The CHT model is accepted for sizing the A3 avionics cold plate and for establishing thermal margins at CDR, provided operation remains within 0.035–0.060 kg/s flow and 270–280 K coolant inlet, and total dissipation ≤ 320 W. It is not approved for any scenario involving boiling or two-phase transients. Decision by Thermal Analysis Lead (L. Park) with concurrence from IV&V (J. Oh). Next steps: lock v1.7.2 for CDR artifacts; open CR to study TIM pressure dependence before QR.
