To: Priya Shah, Program Lead – CardioRF
From: A. Nguyen, Thermal-Fluid Analyst
Date: 06 Aug 2026
Subject: Status memo – CHT model of irrigated RF ablation tip (6-hole vs 12-hole)

Quick recap and purpose
We built a 3D conjugate model in Fluent 2023 R1 to compare two catheter tip designs under a nominal 25 W, 30 s application in 37 C blood. The model includes internal saline jets, metallic tip, polymer shaft, surrounding blood flow, and an 18 x 18 x 12 mm myocardial block with perfusion. Joule heating is represented as a uniform volumetric source in the electrode (6.0e8 W/m^3 to deliver ~25 W). The output of interest is lesion size ranking; we also tracked peak tissue temperature as a safety surrogate.

What looks solid
- Geometry and physics: Full tip fluid passages; tissue conduction with Pennes perfusion (0.005 s^-1); blood domain crossflow at 0.12 m/s; irrigation 17 ml/min at 22 C. Radiation was initially neglected because of the aqueous environment; later runs turned on gray radiation (ε = 0.85) and saw <1 C change in peak tissue temperature.
- Numerics and mesh: Unstructured mesh with 7.2M cells; 10 prism layers at the wall, nominal y+ ≈ 1 on the tip and tissue interface. Energy residuals below 1e-5 each timestep; global heat balance typically within 2%.
- Bench comparison: In 37 C bovine muscle with 0.1 m/s saline-blood surrogate crossflow, IR thermography and three type-T thermocouples recorded peak tissue temps of 83 ± 2 C and lesion depth 4.6 ± 0.3 mm (50 C isotherm, 60 s cooldown). The baseline model predicted 78 C and 4.2 mm. The 12-hole design reduced peak temp by 3–4 C relative to the 6-hole in both test and model.

Items that need attention
- Wall treatment inconsistency: Early notes say scalable wall functions with target y+ ~ 30–40 on the tip; the current mesh report shows y+ near 0.8–1.6 and “enhanced wall treatment.” Results are not materially different across these settings in our spot checks, but it’s unclear which configuration underpins the validation comparison.
- Grid and timestep effects: A two-level refinement (7.2M → 12.5M cells) shifted peak tissue temperature by 2.9% and lesion depth by 0.18 mm. We called the grid “good enough,” citing a 3% GCI on temperature; however, a separate run on the 12.5M grid still moved the hottest point location by ~1 mm. Timestep halving (0.05 s → 0.025 s) changed peak temperature by 4.1% in the first 10 s but <1% by 30 s.
- Operating point mismatch: CFD uses 0.12 m/s crossflow; the bench varied between 0.08 and 0.10 m/s measured with a dye streak method. We did one sensitivity run at 0.09 m/s—lesion depth increased by 0.3–0.4 mm—which narrows the model/bench gap. The memo last week claimed “≤5% error vs test,” but using the actual test velocity the present difference on lesion depth is 9–10%.
- Model choices vs intent: We stated the model serves to rank designs, not to set absolute power/time clinical protocols. Yet the design review deck (slide 14) proposes using the simulated 50 C contour as an absolute predictor for algorithm tuning. Note also that some post-processing used a 55 C cutoff; this alone shrinks the discrepancy to ~5%, but that is not the threshold used in the lab.
- Turbulence sensitivity: Mainline runs used SST k–ω. Switching to realizable k–ε barely moved lesion depth (≤0.05 mm) but shifted peak tip temperature by ~7%. Documentation says “insensitive to turbulence model,” which is true for lesion size but not for the temperature limit we are using as a safety marker.
- Energy balance transient: In several early transients, the solver reported up to 9% energy imbalance during the first 2–3 s with coupled flow–energy; this settles below 2% by 10 s. We did not re-run the bench-match case with improved under-relaxation to confirm the impact.

Takeaways and proposed next steps
- Decision-readiness: The model supports picking the 12-hole design as cooler by several degrees and similar or slightly larger lesion footprint. I’m comfortable using it for relative ranking, with the caveat that absolute lesion predictions still have 5–10% uncertainty tied to flow conditions and post-processing thresholds.
- Short actions (1–2 weeks): 
  1) Align crossflow to the measured 0.09–0.10 m/s and re-run both grids; 
  2) Lock wall treatment (either y+ < 2 with enhanced treatment or y+ ~ 35 with wall functions) and document; 
  3) Standardize the 50 C isotherm for both lab and model; 
  4) Tighten timestep during the first 5 s to address transient energy closure.
- Longer action: If absolute values will drive power-control tuning, add one tissue property sweep (k and perfusion) and expand validation to two more flow rates; otherwise, current evidence suffices for the down-select.
