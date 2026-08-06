To:     Lunar Comms Avionics IPT Lead
From:   J. Serrano, Structural Analysis
Date:   2026-08-06
Subject: Credibility memo — avionics tray corner bracket FEA (Abaqus) for PDR stress sign-off

Context and model scope
We built a finite-element model of the LT-AV-TRAY-03 corner bracket to support PDR stress margins under the quasi-static load cases in Load Set B (max lateral shear and uplift from harness tension). The model is intended to predict bracket-level von Mises stress, fastener loads, and local strain at the strain-gage location used in the bench check. It is not being used for crack-growth or vib fatigue at this gate.

Modeling details and assumptions
- Geometry: CAD Rev F, with all as-designed fillets retained except small chamfers (<0.3 mm) omitted. Holes modeled at nominal size.
- Material: 7075-T73 plate, 6.0 mm nominal thickness. Isotropic linear elastic, E=71.1 GPa, ν=0.33, density 2810 kg/m^3. No plasticity modeled; we are using yield allowables for margin checks.
- Fasteners: Four M5 bolts represented with pretension sections and rigid kinematic couplings at the head-to-bracket interface; threads not modeled. Substrate tray region under the bracket represented by a rigid surface (conservative for bracket stress).
- Boundary/loading: Bolt shanks tied to a grounded reference to represent a stiff tray. Pretension set to 6.5 kN each. External shear 2.5 kN applied through the cable clamp footprint as a distributed load; 0.9 kN uplift applied at the outboard ear.

Numerics
- Solver: Abaqus/Standard 2022. Subroutine-free model; native material.
- Elements: Mostly C3D10 (quadratic tets). Target element edge 1.0 mm near fillets and hole edges; 3–4 mm elsewhere. Hourglass control and contact not applicable.
- Convergence criteria: Default Newton residuals (8% cutback observed on load step 1), line search on.

Mesh refinement check
We ran three meshes focused on the fillet at the outboard ear:
- Coarse (min h=2.0 mm): peak stress 218 MPa at fillet root.
- Nominal (min h=1.0 mm): peak stress 242 MPa.
- Fine (min h=0.5 mm): peak stress 251 MPa.
Change from nominal to fine was +3.7% at the hotspot; reaction loads and bolt forces changed <1%. We used the fine-mesh result for margins and kept the nominal mesh for the variability study to keep turnaround under one hour per run.

Data pedigree and loads
- Material properties: M&P database entry MP-7075-T73-PLT-6mm v3, consistent with supplier certs from Kaiser lot KZ-4812.
- Bolt preload: Per fastener spec FS-M5-ALY v2, torque-to-tension correlation from tech note TN-FAST-019; used mean value.
- External loads: From Systems load deck LDB-LS-B-2026-04, case LS-B-07.

Comparison with bench check
A static pull on an engineering unit bracket (CNC from plate, no anodize) was run at JSC Lab 14. Gage G3 was 9.5 mm from the outboard fillet on the tension side. Test applied 2.5 kN lateral and 0.9 kN uplift via the clamp fixture.
- Measured strain at G3: 780 microstrain at peak.
- Model prediction at gage rosette location (averaged over three adjacent elements): 760 microstrain.
- Difference: -2.6% (model low relative to test).
Bolt #2 axial force from the load cell washer was 5.8 kN vs. 6.0 kN in the model (within 3.5%).

Variability and drivers
We explored the influence of main tolerances and assembly scatter with a 200-sample Latin hypercube on the nominal mesh:
- Parameters: preload ±10% (uniform), thickness 5.8–6.2 mm (uniform), E ±3% (normal), fillet radius at the outboard ear 1.5–2.5 mm (uniform), hole position offset ±0.15 mm radial (uniform).
- Result: 95th-percentile hotspot stress 274 MPa; mean 248 MPa.
- Sensitivities (local): decreasing fillet by 0.5 mm increases peak stress ≈ +8–10%; -10% preload increases peak stress ≈ +2–3%. Thickness dominated bolt load sharing but had <4% effect on the hotspot.

Margins and interpretation
- Allowable: 7075-T73 yield 435 MPa, using FoS 1.25 at PDR.
- Criterion: peak elastic stress compared to yield/FoS = 348 MPa.
- Fine-mesh deterministic hotspot: 251 MPa (margin to criterion ≈ +38%).
- Variability 95th percentile: 274 MPa (margin to criterion ≈ +27%).
Model strain aligns within 3% of the bench check at the same load path. The mesh study indicates remaining discretization impact at the hotspot on the order of 3–5%, which is small relative to available margin. The parameter study shows the fillet radius is the main lever; drawing already calls out 2.0 mm min and we analyzed down to 1.5 mm.

Limitations to note
- No plasticity, residual stress, or surface treatment effects included; anodize-induced property changes not modeled.
- Threads and joint slip not represented; substrate tray idealized as rigid, which is conservative for bracket stress.
- Random vibration and fatigue life not addressed here; tracked under separate analysis.

Decision
Based on the above, the bracket FEA is accepted for bracket sizing and stress sign-off at PDR for the LS-B quasi-static cases, subject to maintaining a minimum 2.0 mm fillet at the outboard ear and achieving the specified bolt preload. Decision by the Structures Subsystem Lead (A. Kim), with concurrence from the Avionics IPT Lead.
