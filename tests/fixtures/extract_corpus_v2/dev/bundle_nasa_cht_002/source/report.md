To:     C&DH Thermal IPT Lead  
From:   J. Ortega, Thermal/Fluids Analyst  
Date:   06 Aug 2026  
Subj:   CHT status for rover compute-module cold plate (Fluent 2023 R2)

Summary
We used a conjugate model to predict junction temperatures and coolant pressure drop for the compute module cold plate assembly. The model is intended to support CDR by showing component peak temperature margin against the 85 C derating limit with realistic spreads and by flagging the primary knobs we can adjust (TIM stack-up and flow rate). Bottom line: under the test-like operating point (0.8 LPM, 35% PG/water at 25 C inlet, 130 W total board power), the analysis predicts 78–82 C on the hottest FPGA case, depending on TIM thickness. The bench correlation at the same point shows a 2.7 C high bias versus prediction for that device, which keeps us inside limit with a small but non-zero risk if the TIM stack drifts high.

What we modeled
- Toolchain: Ansys Fluent 2023 R2, steady RANS with SST and full conjugate heat transfer through TIMs, copper spreader, and Al6061 cold plate. Fluid properties for 35% PG/water pulled from CoolProp (temp-dependent), solids from vendor datasheets (kCu = 385 W/m-K, kAl = 167 W/m-K, TIM nominal = 3.0 W/m-K).
- Geometry: Latest CAD of the cold plate and manifold; PCB represented with detailed copper planes and component footprints for the three hottest packages. Small fillets (<0.2 mm) and mounting bosses outside the heat path were suppressed.
- Loads/BCs: Power map applied at component bases (two FPGAs at 35 W each, four converters at 8 W each, remainder distributed to reach 130 W). Inlet mass flow fixed; outlet static pressure zero; coolant at 25 C. No radiation modeled for this phase.

Numerics and convergence
- Mesh: Poly-hexcore with seven prism layers, y+ ~ 0.8 on fluid walls. Three grids: 3.1M / 6.4M / 12.7M cells. Peak FPGA case temperature changed 3.1 C (coarse→medium) and 1.9 C (medium→fine). We retained the 6.4M grid; extrapolated change from medium to an effectively doubled cell count is ~0.8 C. Residuals < 1e-5; heat in vs. out across fluid–solid interface matched within 0.7%.
- Sanity checks: 1D slab conduction patch problem matched analytic within 0.4 C; developing-channel Nusselt numbers in a simplified straight-run variant were within 6% of Gnielinski.

Bench comparison
- Single-board rig with the production cold plate, Coriolis meter for flow, type‑T thermocouples at FPGA cases, IR for pattern checks. At 0.8 LPM and 25 C inlet: model predicted 78.4 C on the hot FPGA vs. 81.1 C measured; board-average 62.0 C vs. 64.3 C; predicted ΔP 18.6 kPa vs. 19.4 kPa measured. No test-based tuning was applied to the model.

What drives temperature
- We perturbed likely variables one at a time around the nominal: TIM thickness (50–125 µm), inlet flow (±20%), inlet temperature (+5 C), and interface pressure (affects contact resistance proxy). The TIM stack dominated: going from 75 µm to 125 µm raised the hot FPGA by ~7.9 C; trimming to 50 µm lowered it ~5.2 C. Flow changes of ±20% shifted the hot FPGA by −3.8/+4.4 C. Inlet temperature mapped nearly 1:1 to device temperature, as expected.

Spread estimate
- A 200‑point Latin hypercube treated power (±5%), TIM thickness (±25 µm), coolant viscosity (±7% lot‑to‑lot variability), and interface pressure (±20%) as random. The hot FPGA showed a 95% band of ±3.2 C around the median at 0.8 LPM. This is dominated by TIM variation (~52% of variance) and flow (~28%).

Assumptions and limits
- Flow is single-phase; no boiling expected in our envelope. Manufacturability-driven manifold roughness was not explicitly modeled; friction factor was indirectly captured via SST and wall resolution. Radiation and purge airflow are excluded here and will be addressed in the thermal-balance model of the full avionics bay.
- The comparison data and the model both cover 0.6–1.0 LPM with 35% PG/water between 20–35 C. Use outside that window (other coolants, much colder inlets, pump transients) is not supported by this run set.
- TIM modeled as a uniform layer plus contact proxy; we did not include voiding or pump-out.

Configuration control
- Project files are in Git LFS under rover_therm/cht_coldplate, tag cp_cht_v0.9. Mesh scripts and case settings stored alongside. The solved case and report are attached in Windchill (4123-THM-CP-AN-01).

Recommendations for CDR
- Lock the TIM process to target 75 µm with verification at assembly; otherwise we lose margin quickly.
- For worst‑case reviews, carry the +3.2 C spread on the hot FPGA and the observed +2.7 C test‑minus‑model bias; combined, this still keeps us below 85 C at 0.8–1.0 LPM, but with little headroom if inlet temperature drifts above 25 C.
- Extend the bench matrix to 0.6 LPM and 35 C inlet to bracket the spec; incorporate radiation for vacuum‑thermal testing in the next increment.
