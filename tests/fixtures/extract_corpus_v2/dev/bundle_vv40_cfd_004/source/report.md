To: P. Nguyen, Project Lead – Pump Upgrade Program
From: A. Romero, CFD Lead
Subject: Credibility memo for the impeller–volute CFD used to screen the Rev-B centrifugal pump redesign
Date: 2026-08-06

Purpose and decision context
We used steady-state CFD to predict the head–flow curve and hydraulic efficiency for the Rev‑B impeller/volute at 1450 rpm, water at 25 °C. The analysis informs go/no‑go for machining the prototype and trimming the outlet blade angles. Target accuracy for head is ±5% over 0.6–1.2×BEP, with higher tolerance at the extremes. If the prediction is wrong by more than that, we risk ordering tooling that won’t meet contract points (cost/schedule hit but low safety impact). We rate the decision risk as moderate and set acceptance at demonstrated uncertainty ≤5% near BEP and ≤7% at the curve ends.

How we compared to reality
- Benchmarks: The model was checked against our 2023 shop test of the Rev‑A pump (same frame size, similar blade count; D2 +1.5% vs Rev‑B). Eleven test points (0.5–1.3×BEP). The CFD for Rev‑A (same workflow and options) reproduced head within 3.0% at BEP and within 4.9% at low flow; efficiency within 2.8% absolute near BEP.
- Domain match: Reynolds numbers (based on D2 and tip speed) differ by <4% between Rev‑A and Rev‑B at 1450 rpm; same fluid and temperature; surface roughness measured on Rev‑B is within the Rev‑A range.
- Additional physics check: One transient sliding‑mesh run at BEP showed time‑averaged head within 0.7% of the steady MRF result, indicating that steady modeling is adequate for the QOIs here.

Numerics and setup quality
- Solver and build: Ansys CFX 2024 R1, double precision. Continuity and momentum residuals <1e‑5; mass imbalance <0.1% of inlet flow.
- Mesh discipline: Three poly‑hexcore meshes with y+ ≈ 1 on blades and volute: 2.1M, 4.8M, 9.5M cells. Richardson extrapolation on head gave an observed order 1.95; GCI on the fine mesh is 1.8% at BEP and ≤2.6% across the curve.
- Algorithms: Second‑order upwind for advection with bounded corrections; coupled solver. Steady Multiple Reference Frame for rotor–stator.
- Code testing: Vendor SQA is on file; in‑house regression includes a laminar manufactured‑solution case and the 2‑D backward‑facing step. Both show ~second‑order trend in L2 norms when we halve Δx, consistent with expectations for our schemes.

Physics choices and assumptions
- Turbulence closure: SST k–ω with curvature correction; transitional effects neglected (fully rough behavior not expected at our Re).
- Fluid model: Incompressible water, ρ=997 kg/m³, μ=0.89 mPa·s at 25 °C from IAPWS‑IF97. No cavitation modeled; vapor phase excluded from current scope.
- Geometry and clearances: CAD Rev‑B (PDM vault tag PUMP‑RB‑0819). Tip clearance set from drawings, 0.35±0.05 mm; leakage path represented as a fixed pressure loss via a minor‑loss coefficient estimated from the seal ring annulus correlation (not fitted to test data).

Inputs pedigree and traceability
- Inlet total pressure and turbulence intensity derived from the test loop: 0.5% pressure gauge uncertainty (cal log TL‑2026‑07), TI assumed 5% based on upstream bend and screen; verified via hot‑wire on Rev‑A loop (4.2–6.1%).
- Wall roughness from CMM: 15±5 µm on blades, 25±7 µm on volute.
- All runs scripted; case archives, meshes, and reports under Git commit 3f7a9b2 on the CFD‑Pump repo; solver journal and machine image hashes attached.

Sensitivity and what drives the outputs
- Roughness varied 10–40 µm shifts head by 1.2% at BEP.
- Inlet TI from 1% to 10% changes head <0.5%; outlet swirl backflow treatment on/off changes head 0.4%.
- Turbulence model change (SST vs RNG k–ε with scalable wall functions y+~30) changes head 1.1% at BEP and 2.3% at 0.6×BEP.
- Tip clearance ±0.05 mm moves head ±0.9%.

What we did and did not tune
- No curve‑fitting to test data. We selected roughness within measured bounds and used seal‑loss correlations from Idelchik. A posteriori check shows predicted shaft power within 3.5% of dynamometer data, consistent with not overtuning.

Uncertainty on the predictions
- We combined: numerical resolution (from the mesh study), model choice spread (SST vs RNG), and input estimates (roughness, clearance) using root‑sum‑square.
- Total 1‑σ on head: 3.2% at BEP, 4.6% at 0.6×BEP, 4.1% at 1.2×BEP. Using 95% coverage, that’s ~±6.3% worst case at the low‑flow end, ±3.9% at BEP.

Software hygiene and review process
- Two‑person setup review using the rotating machinery checklist (Rev 5). Independent rerun by J. Patel on a separate node reproduced BEP head within 0.3%.
- All post‑processing scripted in PyFluent; figures regenerated from source. Calculation environment logged (RHEL 9.2, Intel oneAPI 2024.1).

Scope limits and applicability
- The workflow is applicable for water at 20–40 °C, 1200–1600 rpm, flows 0.6–1.2×BEP. Not configured for cavitation, acoustics, or sand‑laden service.
- Prior use on three similar pumps in 2022–2024 showed head errors 2–5% near BEP, aligning with the above uncertainty budget.

Decision
Given the demonstrated mesh convergence, reproducibility, match to prior test data on a closely related design, and quantified uncertainty, this CFD is accepted for design screening of the Rev‑B head–flow curve and efficiency within the stated operating window. It is not approved for cavitation assessment or acoustic predictions. Decision by P. Nguyen, 2026‑08‑06.

Attachments on request: mesh study table, residual histories, comparison plots, regression test summaries, and configuration manifests.
