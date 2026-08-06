To:     Mira (Thermal Lead)
From:   R. Patel (CHT Analyst)
Date:   2026-08-06
Subject: CHT status — inverter cold plate + board stack, M5 prototype

Short version
- We are directionally okay to proceed to EVT with a 5–7 C temperature guard band, but I don’t recommend locking the cooling geometry for DVT yet.
- The CFD/CHT set is largely consistent with the bench data, but there are a few modeling loose ends and some bookkeeping issues. Several items look internally inconsistent and need cleanup before the next gate.

What we modeled
- Geometry: Two-pass aluminum cold plate (Al6061) bonded to a copper spreader under four SiC MOSFET modules. TIM-1 between die caps and spreader, nominal 0.10 mm thickness; TIM-2 under spreader to plate, 0.08 mm nominal.
- Coolant: 50/50 water–glycol loop, nominal 2.0 L/min at 25 C inlet from the Sorensen S300 pump. Vendor sheet lists turbulence intensity ≈10% at that Reynolds number; we started with 5% (legacy template) and used 10% in later runs. Outlet at 0 Pa gauge.
- Loads: 180 W total, apportioned 45/45/45/45 W to the four modules. Spreader and plate treated as participating in conduction; board modeled as orthotropic equivalent (kxx=12, kyy=12, kzz=0.8 W/m-K).
- Physics: Ansys Fluent 2023R2, pressure-based coupled solver, SST k-ω for the coolant with curvature correction off. Radiation: off in the baseline (cooled enclosure); however, Run R09 included surface-to-surface radiation by mistake—see notes.
- Properties: Temperature-dependent coolant properties via NIST tables; solids with temperature-dependent conductivity. Note: R01–R02 inadvertently used a fixed viscosity μ=1.5e-3 Pa·s; subsequent runs corrected this.

Numerics and mesh
- Mesh: Poly-hexcore in fluid (8.3M cells), solids (2.1M). Near-wall target was y+≈1 for SST, but the achieved y+ is typically 15–30 along the mid-channel walls; we left scalable wall functions on. A refinement campaign produced three levels: 5.2M / 8.3M / 14.7M cells (fluid+solid).
- Convergence: Energy residuals <1e-6, others <1e-4. Key monitors (hottest die cap, coolant outlet T) flattened to within 0.2 C over 2k iters in most runs. That said, in R08 the hottest node drifted ~0.8 C over the last 500 iters while residuals continued down, suggesting a slow recirc mode.
- Time dependence: We’ve treated the solution as steady. A quick transient check (R10, 0.1 s steps, 3 s total) showed a 1–1.5 C oscillation in the wake of the U-turn; we did not propagate transient results into the baseline.

Evidence vs experiment
- Bench: M5 coupon on the thermal stand, 2.0 L/min, 25 C inlet, 180 W. T-type microbead in each module cap, IR spot check through the window. Hottest cap measured 68.5±0.7 C; coolant rise 3.6±0.2 C.
- CFD: Baseline steady run (R07) predicted 63.2 C hottest cap and 3.2 C coolant rise. That’s ~8% low on peak temperature. Earlier in the slide deck we called this “within 3%” using R05; that number included a one-off with TIM-1 conductivity nudged to 3.8 W/m-K (vendor nominal is 3.0 W/m-K), which we did not carry forward.
- Sensitivities: ±0.2 L/min changes peak by ±1.9 C. Increasing turbulence intensity from 5% to 10% moved hottest cap up by 0.6 C. Including radiation in R09 lowered the predicted peak by ~0.4 C despite the enclosure being nominally non-participating; this is inconsistent with the “radiation off” assumption and suggests we need to recheck BCs in that case.
- Contact behavior: We used a uniform TIM thickness and no explicit contact resistance at the spreader/plate bond. The metrology report (gage pins) shows 0.07–0.12 mm spread for TIM-1; a Monte Carlo of that was deferred. Back-of-envelope: +0.05 mm adds ~1.1 C.

Checks and controls
- Mesh sensitivity: Across 5.2M → 14.7M, hottest-cap prediction shifted 1.2%. However, the wall y+ actually increased on the “finest” mesh in parts of the U-turn due to a blocking artifact, so the monotonicity assumption behind the GCI we quoted (0.5%) is shaky. We need to regenerate the fine level with boundary-layer spacing preserved.
- Solver settings: Double precision throughout except R06 (single precision to test speed), which ran ~12% faster and gave peak T within 0.3 C; we did not include R06 in any rollups.
- Cross-checks: Verified pressure drop against a straight-channel correlation (turbulent) and got within 4%. We also ran a pipe-heating sanity case from White (convective heat-up) and got 0.3% error; relevance to our strongly 3D corner flows is limited.
- Traceability: Inputs and case files for R03–R10 are on Git (tag m5_cht_ev1). R01–R02 were on my laptop during travel; I reproduced the results but the original case files aren’t archived.
- Independence: Peer read by S. Ng (who also created the plate CAD), so not fully independent.

Open items and suggested actions
1) Rebuild the finest mesh with tighter first-layer spacing to actually hit y+<1 near the hotspot region and rerun the triplet for a clean refinement result.
2) Lock inlet turbulence intensity to 10% to match the pump data; rebaseline.
3) Add a transient case with 0.02 s steps for 5 s to quantify the recirculation-driven fluctuation; report peak and cycle-mean temperatures.
4) Calibrate thermal interfaces using the metrology thickness distribution rather than a single nominal; if we keep 3.0 W/m-K, we should document the residual 8% offset to test.
5) Remove radiation entirely for the sealed-enclosure condition (or, if we keep it, align emissivities and enclosure factors with the test rig).
6) Run a quick A/B on constant vs temperature-dependent viscosity to bracket the first-run bias; current belief is the fixed-μ runs were 0.9–1.3 C optimistic.

Bottom line
- With the present knobs set, the model is optimistic by ~5–8% on the hottest location. We can launch EVT builds using the CFD result plus a 7 C margin while we close the mesh/wall-treatment inconsistency and reconcile the turbulence inlet and contact modeling. I do not recommend using R07 as-is for DVT sign-off.
