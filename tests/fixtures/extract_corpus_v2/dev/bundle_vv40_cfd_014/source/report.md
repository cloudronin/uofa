To: Mira Patel, Pump Upgrade Program Lead
From: A. Nguyen, Fluids Simulation
Subject: CFD status for P3-70 pump (RANS, 2900 rpm) — verification/validation snapshot
Date: 06 Aug 2026

Quick take
We can use the current CFD to guide trim decisions near best efficiency point (BEP). Confidence off-BEP is mixed; several setup choices need to be nailed down before we rely on stall-margin predictions. The headline numbers say we’re within 2–3% of the lab curve, but a closer look shows spread up to ~8% depending on BCs and turbulence model.

What we modeled
- Machine: P3-70 single-stage centrifugal pump, 7-blade impeller with 2-vane diffuser, 2900 rpm.
- Operating points: 0.6, 1.0, 1.2 Q_BEP; water at 25 C (ρ≈997 kg/m³, μ≈0.89 mPa·s).
- Geometry: CAD cleaned; fillets <0.25 mm removed; tip clearance set to 0.35 mm (vendor drawing says 0.30±0.05 mm).
- Software: STAR-CCM+ 2022.1; MRF steady-state. We spot-checked one case in Fluent 2023 R2—pressure rise differed by 0.6% at BEP. For surge point we briefly tested sliding mesh (unsteady), but MRF results were used for the numbers below.

Mesh and numerics
- Mesh: poly + prism layers from Pointwise; 2.1M (coarse), 4.2M (baseline), 8.5M (fine). y+ mostly 1–3 on blade suction sides; localized 12–18 at shroud downstream of tongue.
- Convergence: residuals <1e-5 for p, k, ω; mass balance within 0.2% (the 0.6 Q_BEP case leveled at 1.6% until rotating-frame under-relaxation was dropped).
- Grid sensitivity: using head as the metric at BEP, GCI was 1.8% (coarse→baseline→fine). In the roll-up table I noted “<0.5% grid effect”; that was for efficiency at BEP only, not head at off-design. We need to reconcile that statement.

Physics choices
- Turbulence: baseline runs used SST k–ω with curvature correction. We also ran Spalart–Allmaras on the coarse mesh; summary slide says “nearly identical,” but the 0.6 Q_BEP head differed by 7.4% and diffuser loss coefficient by 12%. SAS at BEP matched SST within 1.2% on head.
- Wall treatment: near-wall resolution targets the viscous sublayer (no wall functions). However, in the 8.5M case we allowed automatic switching, so portions of the diffuser used scalable wall functions when y+>11.

Boundary conditions and fluids
- Inlet: total pressure with 5% turbulence intensity; outlet: mass flow. For the BEP calibration run we flipped to fixed outlet static pressure to pin the duty head (this wasn’t reflected in the config log).
- Fluid properties: water at 25 C. The vendor’s acceptance test was run at 30–32 C (reported viscosity 0.75–0.80 mPa·s). We applied a density correction in one sensitivity run but did not adjust viscosity.
- Rotational reference: 2900 rpm; both main and shroud gaps modeled. Leakage through balance holes omitted.

Results vs test
- At BEP: predicted head 17.7 m vs test 17.9 m (–1.1%); efficiency 78.6% vs 79.2% (–0.8%). The emailed “within 2% across the map” claim bundled only head at the three points; efficiency at 0.6 Q_BEP was off by 6.5%.
- At 0.6 Q_BEP: separation at the tongue more extensive in CFD than pressure-tap data suggests; diffuser static pressure recovery 8–10% higher than rig at same flow rate. Note: test Re is lower due to warmer water; our run shows stronger swirl decay—may be apples-to-oranges.

Verification/uncertainty
- Balances: energy defect <0.3% at BEP; mass residuals as above. The unsteady sliding-mesh trial reduced the tongue recirculation but raised torque by ~2%.
- Mesh and model spread: combining GCI with turbulence model spread gives ~3.2% band on head at BEP. The earlier “95% confidence ±3% total” inadvertently double-counted the test uncertainty (4–5% on head) in one variant and ignored it in another.
- Parameter sensitivity: varying inlet turbulence from 3% to 10% shifts head by ≤0.6% at BEP but up to 2.4% at 0.6 Q_BEP. Tip clearance +0.1 mm reduces head by 1.1%.

What’s solid vs shaky
- Solid enough to use: BEP head and shaft power trends with small geometry tweaks; relative ranking of two diffuser trims; qualitative flow features.
- Needs cleanup before sign-off: boundary-condition bookkeeping (mass-flow vs pressure), temperature/viscosity parity with the test, consistent near-wall treatment on the fine mesh, re-run GCI using monotonic metrics, and either commit to MRF throughout or document the unsteady deltas.

Next steps (1–2 weeks)
- Lock the BC set and re-run the three operating points with matched fluid props to the rig.
- Recompute grid study with unified wall treatment; report GCI by quantity (head, torque, diffuser recovery).
- Repeat SST and SA on the baseline mesh at all points; if spread persists >3% at 0.6 Q_BEP, add a short LES-of-a-sector check.
- Update the validation table to reflect test temp and the fixed-pressure BEP calibration run; push the case directories to the cfd-p3 repo (current link in the slide deck is stale).

Bottom line
We can proceed using the CFD for BEP-centric decisions, with caveats at part-load. I do not recommend publishing the “±3% everywhere” figure until the BC and temperature inconsistencies are resolved.
