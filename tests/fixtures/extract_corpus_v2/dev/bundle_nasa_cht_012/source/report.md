To:     LTV Avionics Thermal IPT Lead
From:   R. Santos, CHT Analysis
Date:   2026-08-06
Subj:   Snapshot of CHT model credibility — rover avionics cold plate with Li-ion pack

Summary
We ran a coupled thermal–fluid model of the avionics bay cold plate that pulls 650 W steady from the battery pack and motor controller during high-rate comm passes. At nominal loop conditions (35% PGW, 22 °C inlet, 0.48 kg/s commanded flow), the model predicts:
- Peak cell can temperature: 46.1 °C
- Controller heat sink base: 58.4 °C
- Coolant outlet: 28.7 °C

On balance, the model reproduces the bench rig within a few degrees on average, with localized hotspots not fully captured. Key drivers appear to be contact conductance and bypass leakage at two O-ring grooves.

Geometry and physics choices
- Solid: full-fidelity cold plate with 0.9 mm serpentine passages; battery module simplified to homogenized blocks per sub-pack with embedded heat sources mapped from the electrical team’s power trace.
- Fluid: incompressible coolant, temperature-dependent viscosity and Cp. Turbulence initially planned as k–ω SST with low-Re wall treatment (target y+ < 1); wall conjugation across copper, TIM, aluminum.
- Thermal joints: nominal bondline 65 µm; initial thermal contact resistance set to 2.5e-4 m²·K/W based on coupon data. No tuning to match test data was performed.
- Boundary conditions: inlet mass flow fixed at 0.48 kg/s and inlet total temperature 22 ± 0.5 °C; outlet treated as fixed static pressure at 0 barg tied to the vented reservoir.

Discretization and solver behavior
- Mesh: 6.1M poly elements (solids + fluid) with five prism layers in the channels. Two refinement passes were executed: 3.2M → 6.1M → 11.8M cells. Between the last two, peak cell-can temperature shifted by 0.7 °C (≈1.5%), coolant ΔT by 0.03 °C. Wall y+ was < 1 over 92% of wetted length; a narrow entry region reached y+ ≈ 3.
- Convergence: steady segregated solver; energy residuals to 1e-8, momentum to 2e-5. Area-averaged outlet temperature flat over last 400 iterations.
- Turbulence model actually used for the final run was realizable k–ε with enhanced wall treatment to mitigate intermittent divergence in the serpentine elbows.

Bench test correlation
- Instrumentation: 14 T-type thermocouples on cell cans, 6 on the controller base, 2 in coolant (in/out), IR snapshots through the viewport (emissivity 0.85 used).
- At 650 W, test showed peak cell-can 47.5 °C, controller base 66.2 °C, coolant outlet 29.1 °C. Model-to-test differences: -1.4 °C, -7.8 °C, and -0.4 °C respectively.
- Hotspot at the controller corner (TC-B4) ran 9.7 °C above model; elsewhere mean absolute error across all TCs was 3.1 °C.

Inputs and boundary realism
- The pump map (Micropump GJ-N23) indicates 0.46–0.49 kg/s across the expected loop head for 40% PGW at 24 °C; we imposed a total pressure inlet consistent with the map and set outlet mass flow to 0.48 kg/s to match the setpoint.
- Power deposition used the electrical team’s Phase B trace averaged over 180 s; heater back-calculation from coolant ΔT matches within 2.2% of commanded.

Sensitivity and uncertainty snapshot
- One-at-a-time sweeps show controller base temperature changes by +5.4 °C per +1e-4 m²·K/W increase in its TIM resistance; cell-can peak moves +2.1 °C per -10% drop in flow.
- A short Latin hypercube (N=60) varying TIM (±40%), flow (±15%), inlet T (±1 °C) yields a 95% band of [44.2, 49.6] °C for peak cell-can temperature; Sobol-like screening puts TIM at ~0.58 importance, flow at ~0.31.
- We claim the mesh is effectively independent on targets of interest (<1% change run-to-run), and remaining spread is dominated by joint conductance uncertainty.

Credibility readout and caveats
- The model captures bulk coolant behavior and average component temps reasonably. The controller corner miss suggests either a local gap not represented or anisotropy in the heat sink base not included.
- The choice of turbulence model is serviceable for the Reynolds number (~3,800 at 22 °C), but the intended low-Re k–ω SST would better honor the y+ distribution we achieved; we did not observe material differences in coolant ΔT between the two.
- Contact resistances were set from independent metrology; however, a trial with 3.5e-4 m²·K/W reduces the controller base error to ~3 °C, hinting at possible assembly variation in the rig.

Next steps before design freeze
- Re-run with transition-capable k–ω SST and the same mesh to bound any model-form effect on wall heat transfer.
- Add a narrow-slot leak path at the suspect O-ring to test the bypass hypothesis.
- Acquire clamp load data for the controller fasteners and re-center the TIM resistance prior for the uncertainty sweep.

Please advise if you want this model released for preliminary hardware sizing now, or held until the turbulence and leak-path checks are in hand. Turnaround for the two checks is ~3 days CPU plus 1 day analysis.
