To: Mira Patel, Power Electronics Cooling Lead
From: J. Alvarez, Thermal/Fluids
Subject: V&V status for inverter module CHT model (fan-cooled, board-level rig)

Summary
We built a conjugate heat transfer model of the Gen4 inverter module in STAR‑CCM+ 2310, spanning the heatsink, baseplate, TIM, device package, PCB, and the surrounding airflow inside the test shroud. Steady RANS with SST k–ω was used; radiation was included via gray-body S2S. The intent is to support the heat sink fin geometry downselect and TIM screening at 1.5 m/s nominal duct speed.

What looks solid so far
- Match to lab data: Against the bench with a Delta FFB0412VHN fan running at 12 V and 1.6 m/s inlet speed, the model predicts die-center temperature of 83.7 C vs. 85.0 C measured (Type‑T TC glued near die cap; IR camera FLIR A655sc cross-check within 0.6 C after emissivity correction at 0.86). Heatsink base midline: 71.9 C vs. 75.0 C measured. Duct pressure drop across the sink: 160 Pa predicted vs. 151 Pa measured (AMCA 210 correction applied to fan P–Q).
- Grid study: Three meshes (3.1M, 6.2M, 12.4M cells; 15 prism layers, first-layer y+ ≈ 0.8–1.5) show the die temperature shifting by 1.9 C from coarse to fine. Estimated observed order ~1.9; GCI on the medium grid ≈ 2.8% for die temperature and 4.1% for pressure drop. We used the 6.2M mesh for trade studies; the fine grid is too slow for param sweeps (15.5 h vs. 6.3 h per run on 32 cores).
- Convergence behavior: Residuals <1e‑4 for energy and turbulence scalars; continuity/momentum to 3e‑4. Key monitors (die heat flux, die-center temperature, fan mass flow) flat within 0.1 C and 0.5% respectively over the last 500 iterations using coupled solver with pseudo‑transient under‑relaxation.
- Model choices: 
  - Turbulence: SST k–ω with all‑y+ wall treatment; near‑wall resolution validated by y+ statistics. 
  - Radiation: S2S with 5 view-factor sweeps; sensitivity shows <0.7 C effect on die for emissivity 0.80–0.90.
  - Fan: Implemented as a pressure-jump boundary with the vendor’s quadratic P–Q fit; swirl neglected after a check with a rotating-frame patch showed <1% change in flow rate at our test point.
- Inputs pedigree: 
  - TIM thickness (50 ± 10 µm) measured by micrometer post‑assembly; effective k = 3.0 W/m‑K from supplier laminated sheet spec.
  - Contact conductance between baseplate and sink fitted from a squeeze‑flow coupon test series: 6×10^3–1.2×10^4 W/m^2‑K over the applied torque range. 
  - Aluminum k(T) curve (6061‑T6) from MatWeb; board stackup and via fill fractions per ECAD export.
- Sensitivity checks: Moving contact conductance across its measured range changes die temperature by +3.4/‑2.7 C. TIM thickness ±10 µm shifts die by ±1.1 C. Inlet turbulence intensity from 5% to 10% changes die by 0.3 C. Surface emissivity 0.80–0.90 changes die by 0.6 C. These results point to interface quality as the dominant lever.
- Composite uncertainty (first‑order perturbation): ~±2.3 C on die temperature combining contact, TIM, emissivity, and measurement calibration (±0.5 C for T‑type and ±1% emissivity).

Scope notes and gaps
- We did not perform a full stochastic UQ; only local perturbations were run. 
- Only steady conditions are analyzed. A 60 s power pulse trial run shows <0.8 C lag vs. steady assumptions, but we did not carry transient through the mesh refinement set.
- The applicability domain is the current test shroud at 1.2–1.8 m/s. We have not checked the 2.5 m/s corner or alternative fan SKUs.
- Contact resistance was inferred from coupons, not the assembled stack; we may be optimistic if bolt preload in the rig is lower than in the coupons.
- Post‑processing scripts and STAR scene files are in the “gen4_inverter_cht” repo under /cases/2310/meshB; run logs include mesh counts, residual histories, and monitor plots.

Recommendation
For heat sink and TIM downselect at the bench point, the model has enough backbone: grid sensitivity is under control, solution behavior is well‑posed, and the numbers track the rig within ~2 C at the die. Before using it to sign off the thermal budget for vehicle‑level airflow or for higher‑speed regimes, we should:
- Re‑run validation at 2.0–2.2 m/s to check fan curve extrapolation.
- Measure assembled contact conductance via transient thermal test or IR inversion to retire the largest sensitivity.
- Execute one transient case on the refined mesh to confirm no hidden time‑scale issues.

Please advise on priority between the contact measurement vs. higher‑speed validation; we likely only have time for one before M5.
