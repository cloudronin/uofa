To: A. Patel, Thermal Program Lead
From: L. Nguyen, CHT Analyst
Subject: CHT status for VRM/FPGA heat sink on 1U server blade — readiness for EVT exit

Summary
The current conjugate heat-transfer model of the VRM + FPGA assembly on the 1U blade predicts component case temperatures within 1–2 C of lab measurements at the nominal airflow setpoint. The analysis supports using the model to down-select fin geometry and TIM stackups, with caveats on contact resistance and fan variability. Items out of scope for this phase: startup thermal transients, enclosure-level recirculation, and supplier-to-supplier variation of PCB copper distribution.

What we modeled
- CAD: Extruded 6063-T5 heat sink (92 × 62 × 15 mm, 24 straight fins, 1.0 mm thick, 4.0 mm pitch) mounted over a VRM (30 W) and an adjacent FPGA (15 W). Four M3 screws preload across a 0.2 mm silicone pad plus 3 W/m·K grease. Local board under the sink includes a 2 mm copper slug; the rest of the FR‑4 is homogenized.
- Flow path: Axial 80 mm fan delivering 1.2 m^3/min at 20 C. Inlet specified as uniform 3.2 m/s at the fan plane; outlet as pressure opening to ambient.
- Physics and numerics: Fully coupled solid-fluid solution in Fluent 2024R1; SST k–ω with low-Re near-wall treatment (target y+ ≈ 1–3 on fins), second-order spatial schemes. Solid conduction in aluminum (k = 201 W/m·K), FR‑4 (k = 0.35 W/m·K homogenized), copper (k = 385 W/m·K). Surface-to-air radiation omitted; hand calc suggests <1 W net at these temperatures and view factors.

Grid and solver checks
- Cells: Poly-hexcore with inflation on fins and around components. Three meshes: 4.1M, 6.8M, and 9.6M cells. The change in VRM case temperature is −2.9 C (coarse→medium) and −0.6 C (medium→fine). Pressure drop shifts <3% between medium and fine.
- Convergence: Residuals below 1e−5 for energy and 1e−4 for momentum/turbulence; area-averaged exhaust temperature flat to within 0.05 C over the last 500 iterations. Net heat to air equals applied 45.0 W within 3.1% (control surfaces around sink and outlet).
- Sanity test: Ran a 1D composite slab with convection on one side; the numerical wall heat flux matched the textbook solution within 0.4%.

Assumptions with impact
- Heat sources treated as uniform over their packages. Including die-level spreading would likely lower peak case temps by ~1 C; deferred.
- Contact between sink and devices lumped as a single thermal resistance based on vendor data for the pad and grease. No explicit bolt preload modeling; see sensitivity.
- Board copper outside the local slug area was homogenized; trace-scale vias and cutouts ignored.

Comparison to bench data (steady)
- Setup: Open-bench channel, intake air 20.0 ± 0.3 C, volumetric flow 68 CFM measured with a calibrated pitot rake, VRM at 30.1 W and FPGA at 14.8 W (inline DC meters, ±2%). Three K-type thermocouples epoxy-bonded: VRM case, FPGA case, fin tip. One T-type at exhaust.
- Results at nominal: Model vs measurement
  - VRM case: 83.4 C predicted vs 85.1 C measured (−1.7 C)
  - FPGA case: 71.2 C predicted vs 72.0 C measured (−0.8 C)
  - Fin tip: 62.0 C predicted vs 63.2 C measured (−1.2 C)
  - Exhaust: 26.8 C predicted vs 28.1 C measured (−1.3 C)
- Measurement uncertainty: ±1.0 C for thermocouples; flow ±3%.

What moves the needle
- TIM/contact: Varying the lumped interface from 0.2 to 0.6 K·cm^2/W shifts VRM case by +5.5 C across the range. This is the dominant contributor to spread at fixed airflow.
- Fan curve: ±10% change in bulk velocity modifies VRM case by ±3.2 C. The model tracks roughly linearly over ±15%.
- Material properties: ±10% on copper conductivity alters VRM case by <0.7 C; aluminum fin conductivity change of ±10% yields ~0.4 C effect.
- Radiation on/off at these conditions: <0.5 C impact on component cases; leaving it out is acceptable for nominal.

Use guidance and limits
- Good for: Ranking fin pitch and height variants, TIM stack comparisons, and setting a minimum airflow requirement for EVT exit. At nominal, the model is slightly optimistic; applying a +2 C guard band to component cases covers both mesh and bench scatter.
- Not covered in this cycle: Transient warm-up, screw torque variability, enclosure-induced recirculation, or dust loading on the fan. These will be addressed in DVT with enclosure-level CFD and an expanded test matrix.

Next steps
- Capture contact resistance more explicitly: test two pad vendors and add a torque strip study (target range 0.2–0.6 K·cm^2/W).
- Extend the mesh study to verify pressure drop stability on a taller fin variant (goal: ΔT change <0.5 C between medium and fine).
- Add one low-flow point (−20%) to the bench run for better slope matching in the airflow sensitivity.

Ask
Approval to use the current model as the basis for selecting the 15 mm vs 18 mm fin height option and to proceed with the TIM vendor A/B test. Risk is low provided we maintain the +2 C conservatism noted above.
