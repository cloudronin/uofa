To: C&DH Thermal IPT Lead
From: J. Aguilar, Thermal/Fluids V&V
Subject: Conjugate heat transfer model status — Avionics Box AFT-2 (ducted cooling)

Quick take
The CHT model is in good enough shape to support layout trades and fan setpoint selection. It reproduces the bench article within the combined measurement/modeling spread and is stable under modest perturbations to key knobs (flow, TIM). I would not use it to argue margins <5 C without more work on interface conductance and inlet flow characterization.

What we modeled
- Geometry: Full 3D of the finned aluminum heat sink (6061-T6), populated PCB (homogenized board, in-plane k=8 W/m-K, through-thickness k=0.45 W/m-K), and the immediate air passage in the ECS duct test fixture. No cabling; card guides lumped as conduction straps.
- Physics: Steady RANS for air with energy equation; k-omega SST. Solid conduction for all metallic and board parts. Turbulent Prandtl set to 0.85. Natural convection and buoyancy ignored due to forced-flow dominance. Thermal radiation not solved; test was in a matte-black shroud with limited view to cold surroundings, and a quick Stefan–Boltzmann check puts radiative heat at <3% of the 200 W load.
- Boundaries: Inlet mass-flow tied to the lab fan curve (nominal 0.020 kg/s at 240 Pa), outlet static pressure at ambient. External walls adiabatic to match the shroud. Contact between PCB and sink via an effective thermal resistance.

Tooling and numerics
- Solver: Simcenter STAR-CCM+ 2022.1, double precision, segregated flow/energy.
- Convergence: Residuals driven below 1e-5 for continuity, momentum, and energy; panel energy balance closes within 0.7% (|Q_in − Q_out|/Q_in).
- Grid sensitivity: Three unstructured poly-prism meshes (8.1M, 14.4M, 26.7M cells). Tmax on the FPGA package changed −3.1% from coarse→medium and −1.2% from medium→fine; pressure drop shifted <1% medium→fine. We ran the medium mesh for all parametrics.

Inputs and where they came from
- Material data: 6061-T6 conductivity 167 W/m-K at 60 C (MIL-HDBK-5J), PCB effective properties from thermal coupon tests last month; uncertainty ~±15% on through-thickness k due to resin fraction variability.
- Interface quality: TIM equivalent resistance 1.5e-4 m^2-K/W (supplier sheet, 70 C, 100 kPa compression). We verified compression via torque and shim checks; still expect ±30% part-to-part.
- Flow: Fan map from Delta BFB1012 (rev E). Our lab pitot survey on the fixture gave 0.019±0.001 kg/s at the target rpm; inlet air measured 25.3±0.5 C.

How it stacks up against the bench article
- Configuration: 200 W heater on the FPGA emulator; four K-type thermocouples epoxied at the PCB copper islands; IR camera (FLIR A655sc) on a calibrated port, emissivity set to 0.92 after dot-tape checks.
- Results: Model predicted heat sink baseplate 64.0 C vs 66.1±0.8 C measured (−3.2%); local hot spot at the emulator 82.0 C vs 85.0±1.0 C IR indicated (−3.5%). Duct pressure drop matched within 5 Pa on a 210 Pa level.
- Scatter: Run-to-run repeatability on the rig was ±0.6 C at the sink and ±0.9 C at the hot spot. If we combine that with TIM and PCB property spread, the model sits inside the 95% band for both metrics.

Reasonableness checks
- One-dimensional thermal resistance stack (sink spreading + TIM + board) estimates a ΔT of ~57–62 C at 200 W; CFD reports 59 C, consistent with the hand calc.
- Air-side h from Colburn j correlations using the measured flow gives 72–78 W/m^2-K; the area-averaged wall heat transfer from CFD is 75 W/m^2-K.

What moves the needle
- If we bump inlet temperature +10 C, hot spot rises +9.2 C.
- ±5% on mass flow changes hot spot ±1.7 C.
- Doubling the contact resistance at the board/sink interface adds +4.8 C to the hot spot; halving it removes −3.9 C. This is the dominant lever.

Where I’m comfortable using it
- Selecting the fan operating line and baffle tweaks to keep parts >5 C away from limit at 200–240 W.
- Ranking TIM candidates and clamp patterns.
- Estimating deltas between design options (relative changes are tighter than absolutes).

Gaps and to-dos
- Interface conductance: We need on-article pull tests or guarded heat flow coupons to collapse the ±30% on TIM/contact. That’s setting our current floor on accuracy.
- Flow characterization: Our pitot map agrees with the fan sheet, but we still assume a flat inlet profile from the upstream plenum; a five-hole probe survey upstream would reduce that assumption.
- Extended environments: We have not exercised high-altitude, low-density air or vibration-loosened clamps. If flight uses those regimes, we should add them before committing margins.

Bottom line
For trades and setpoint selection, we’re fine. For certifying margins tighter than 5 C, I recommend we first pin down the interface resistance and confirm the inlet profile on the as-installed duct.
