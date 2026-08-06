To: Priya Mehta, Product Development Lead
From: Elena Torres, Structural Simulation Lead
Date: 06 Aug 2026
Subject: V&V status memo — femoral stem FEA used for design freeze decision

Quick take
- The analysis package for the new collared Ti-6Al-4V femoral stem meets the evidence bar we set for this decision. Model outputs align with bench data within 10% on strain metrics, and margins to our clinical safety targets are preserved under quantified uncertainty. Residual limits and applicability notes are listed below.

How the model is being used and how much it matters
- Purpose: support design freeze by demonstrating cortical stress/strain and stem–bone micromotion under immediate post-op single-leg stance are acceptable. The analysis is not used to predict long-term remodeling or fatigue life.
- Consequence if wrong: an under-prediction could elevate periprosthetic fracture risk. Based on our hazard analysis, this ranks as medium-high impact but with mitigations via subsequent bench testing before first-in-human.
- Because of that risk posture, we executed a mid-to-high rigor plan: targeted experiments, solver checks, mesh studies, and uncertainty propagation tied to the quantities we actually use in the decision.

Model setup and assumptions
- Physics: small-strain nonlinear contact FEA (Abaqus/Standard 2023.HF2, double precision). Implant: Ti-6Al-4V E=110 GPa, ν=0.34. Bone: subject-specific, heterogeneous elastic moduli mapped from CT (Keyak-type calibration; cortex 16–22 GPa, trabecular 0.1–1.5 GPa). No time-dependent behavior; no remodeling. Interface modeled as frictional surface-to-surface contact; nominal μ=0.17 with uncertainty.
- Loads/BCs mirror our fixture: hip joint load 2.2 kN at 20° in the frontal plane plus abductor force 0.5 kN; distal constraint via potting block; stem seating consistent with surgical spec.
- Known limitations: no cyclic fatigue, no impaction damage, no osteolysis. Valid for BMI 20–35, normal bone (T-score > −2.0), and immediate post-op.

Solver and software quality
- Implementation vetted with element-level tests: linear patch test error <0.5%, three-point bending vs Euler-Bernoulli <1.0% on coarse-to-fine meshes; Hertzian contact pressure distribution within 3% of analytic.
- Jobs run on CentOS 8 nodes (Intel Xeon Gold 6338, ifort 2021). Identical results reproduced on Windows 11 workstation within 0.2% at hotspots. All models tracked in Git (repo MD-StemFEA, tag v1.6.2); Jenkins CI runs unit problems after each commit. External reviewer (A. Nguyen, PhD, not on design team) completed code/process audit on 23 Jul 2026; no open actions.

Discretization and nonlinear solution behavior
- Mesh: C3D10 elements; 0.30 mm near fillets/collar and bone calcar; 1.2 mm bulk; 1.8M elements total. Contact surfaces refined to limit overclosure <1 μm at convergence.
- Mesh refinement study at the calcar and distal stem shoulder: 0.8M/1.8M/4.2M elements yielded peak von Mises 88.3/92.1/93.4 MPa. Richardson extrapolation ≈94 MPa; fine-mesh GCI ≈2.2% (p≈1.8). Primary QoIs (medial principal strain, interface micromotion) varied by <3% across the two finest meshes.
- Nonlinear solution controls: NR residual <1e-6, contact stabilization off; final contact penetration 0.3–0.9 μm; energy balance error <0.6%.

Experimental comparison (are we matching reality?)
- Five cadaveric femurs tested in our lab, instrumentation per ISO 7206-4 analog: 12 strain gauges (medial/lateral cortex) and digital image correlation (DIC) in the calcar region. Same loading angles and potting as the model; fixture compliance measured (0.12 mm/kN) and included.
- Measurement uncertainty: ±5 με (gauges), ±3% (DIC); alignment errors <0.5° verified by photogrammetry.
- We tuned only the friction coefficient using two pilot bones (μfit=0.17) and then locked it; validation used the remaining five specimens.
- Results: model-to-test for medial calcar principal strain — RMS error 7.4%, mean signed error +1.2%; lateral cortex RMS 9.1%. Coefficient of determination 0.93 across all gauges. Interface micromotion from DIC vs nodal relative slip — MAPE 8.6%. No bias with load level detected (p=0.41).

Uncertainty and sensitivity
- Latin hypercube, 500 samples: varied E_cortex [16–22 GPa], E_trab [0.1–1.5 GPa], μ [0.12–0.22], stem varus/valgus ±1 mm and rotation ±1°, load magnitude ±10%, CT-to-modulus slope ±10%.
- Outputs: 95th percentile peak cortical von Mises = 105 MPa; acceptance limit 120 MPa (margin ≈12%). Interface micromotion 95th percentile = 41 μm versus target <50 μm.
- Influence ranking (first-order Sobol): stem placement variance 0.41, cortical modulus 0.33, friction 0.16; others <0.1. This justifies ongoing emphasis on surgical alignment controls.

Data representativeness and traceability
- Test articles match our CT density range and geometry within the intended cohort. All loads/BCs used in simulation duplicate the rig configuration; no free parameters except μ (tuned then frozen).
- All inputs and outputs are unit-checked (SI) and linked: Lab dataset LD-ORS-2026-07, model configs MC-Stem-v1.6.x, and run logs RL-2026-07-19 through RL-2026-08-01.

What this means for the decision
- For the specific immediate post-op use and stated population, the model’s predictions are consistent with physical tests within ~10%, mesh and solver errors are small relative to margins, and uncertainty propagation shows margins are preserved. We recommend design freeze with the following guardrails:
  - Do not reuse this model for fatigue or osteoporotic cases without new data.
  - Re-verify if geometry changes exceed 1% at collar/shoulder or if surface finish alters friction expectations.
  - Repeat spot validation if moving to a different CT-to-modulus calibration.

Open items and next steps
- Plan a two-specimen spot-check on the final production grit-blast to confirm μ within 0.17±0.03.
- Archive full provenance package and reviewer sign-off in Windchill by 12 Aug 2026.
