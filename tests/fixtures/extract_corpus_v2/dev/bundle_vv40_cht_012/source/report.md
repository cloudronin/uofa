To: C. Nguyen, Ablation Program Lead
From: L. Serrano, CHT Modeling
Subject: Status memo — irrigated RF catheter CHT model credibility for preclinical use
Date: 2026-08-06

Scope and intended use
We built a coupled flow/thermal model for a 7F open-irrigated RF ablation tip to support selection of power/time and hole patterns before the next bench series. The question it is meant to answer is whether a proposed irrigation layout keeps electrode surface temperatures below 80 C while achieving target lesion depth under nominal left-atrial flow. It is not aimed at patient-specific planning.

Model and numerics
- Software: Ansys Fluent 2023R2 for the fluid and heat transfer; tissue heat source mapped from a circuit model using recorded power and impedance drop.
- Equations: Blood modeled as incompressible with SST k-omega; saline jets treated as laminar. The tissue uses a bioheat term for perfusion. We solved the transient heating problem with 0.1 s steps out to 30 s. For the production runs we converged steady solutions at each power step and integrated temperature histories from those states.
- Geometry: 3.5 mm hemispherical tip, 6 holes (0.4 mm), 20×20×20 mm blood block, and 15 mm thick tissue slab. Contact patch is 2.5 mm diameter circle at 10 g normal force.
- Mesh: 3.1M cells hybrid poly/prism; y+ ≈ 1 at the tip with 12 inflation layers. Two finer meshes (4.8M and 7.2M) showed <1.5% change in max tip temperature at 25 W. However, for 35 W the energy residuals stalled at 2×10^-3 and the tip temperature monitor was still drifting by ~0.3 C over the last 200 iterations.

Inputs and assumptions
- Blood: density 1050 kg/m3; viscosity 3.5 mPa·s at 37 C; inlet velocity 0.10 m/s uniform at the upstream face. In the test matrix we treated the surrounding blood as quiescent aside from saline entrainment to isolate irrigation effects.
- Saline: 17 mL/min total through all holes; 25 C at entry; laminar assumption (Re ≈ 700 per hole). We also toggled transitional modeling for the jets in a few runs and saw negligible difference.
- Tissue: k = 0.53 W/m·K, c = 3600 J/kg·K, ρ = 1060 kg/m3; perfusion term 0.005 s^-1. An early material card used k = 0.47 W/m·K and blood viscosity 3.2 mPa·s; the results quoted below reflect the values in the repo’s “v3” folder.
- Heating: volumetric deposition in tissue fit to power and measured impedance trajectory for the 20 W cases; the same mapping was applied to 30–35 W.

Benchmarks and results
- Data sources: Flow-channel tests with porcine myocardium under 0.1 m/s bulk flow, 17 mL/min irrigation, and 20/30/35 W for 30 s (n=5 each). Tip thermocouple and IR camera for surface, TTC staining for lesion depth.
- Agreement: For 20 W, predicted tip temperature at 30 s was within 1.5 C RMS of the thermocouple across all replicates. For 30 W, RMS grew to 2.1 C. Two outliers at 35 W show 3–4 C high bias despite the summary line in the draft report stating “<1.5 C across the board.”
- Lesion metrics: Predicted depth averaged 5.2 mm (20 W) and 6.8 mm (30 W) vs measured 5.0±0.5 mm and 6.4±0.7 mm, respectively. At 35 W, the model overshot by ~1.1 mm on two of five runs.
- Sensitivity: ±50% in blood speed shifted tip temperature by ~2 C; ±20% in perfusion moved depth by ~0.6 mm. Saline flow variation ±3 mL/min altered surface peak by ~1 C.

Execution controls
Runs are scripted (Fluent journal + Python post) and tracked in Git (repo: rf_tip_cht). Note: the 7.2M mesh differs in growth rate near the holes from the committed mesher script; that tweak lived only on a local workstation during the mesh study.

Open items and limitations
- Mixed use of transient language vs steady sequencing needs to be reconciled in the write-up; the production methodology used steady solves per power/time point.
- The blood boundary condition is described both as uniform inflow (0.10 m/s) and as quiescent aside from saline entrainment in different places; only the uniform inflow cases were used for the quantitative comparisons above.
- Material properties were updated mid-stream; k=0.53 W/m·K is the current basis, but some early figures in slides still reflect 0.47 W/m·K.
- No clot/coagulum model; no catheter motion; homogeneous tissue; RF deposition not recomputed from field equations.
- For 35 W, solver convergence was marginal and the bias suggests either the heat-source mapping is over-aggressive or jet breakup physics matters more at that level.

Decision
The Thermal Modeling Review Board has accepted the model for: (a) ranking irrigation-hole layouts, and (b) setting power/time combinations for benchtop builds in the specified flow channel at 20–30 W, subject to using the updated property set (k=0.53 W/m·K, μ=3.5 mPa·s) and documenting the steady-sequencing workflow. The model is not accepted for predicting absolute lesion depth at 35 W, and not approved for clinical-use temperature or lesion predictions in patients. A re-run of the 35 W cases with corrected boundary descriptions and resolved convergence will be required before expanding the approved use.
