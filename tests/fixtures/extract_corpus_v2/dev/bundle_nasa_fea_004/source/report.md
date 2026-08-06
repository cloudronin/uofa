To: Lander Structures IPT Lead
From: R. Patel, FEA Lead
Date: 06 Aug 2026
Subject: V&V status for propellant feedline support bracket model (LL-PL-SUPT-02)

Quick take: The finite-element model for the titanium feedline support bracket is in good shape for PDR decisions. We have test correlation, a mesh study, quantified variability, and full traceability of inputs. Residual gaps are minor and called out below.

- What we’re trying to decide: Can the bracket meet strength and stiffness targets for random vibe + quasi-static thrust vectoring, and tolerate the -120 to +70 C gradient without loss of clamp load? Pass/fail is positive margin at the 95th percentile stress and first mode > 350 Hz with the line attached.

- Physics and scope choices: Small-strain linear elasticity for Ti-6Al-4V; geometric nonlinearity enabled only in the preload/contact step. Fatigue and crack growth are out of scope for this phase. No adhesive effects modeled; the stand-offs are dry-contact with friction.

- Geometry coverage: As-designed CAD Rev F used. Threads are represented by pretension sections; fillets ≥ 0.5 mm retained. Chamfers < 0.3 mm suppressed. Feedline represented as a beam with equivalent bending and inertia from the system team.

- Discretization approach: Abaqus/Standard 2023 HF6. Bracket: C3D10I tetra, target edge 1.5 mm; local refinement to 0.6 mm at the bolt pads. Bolts: B31 beams with connector pretension. Contact: surface-to-surface, hard normal, Coulomb tangential.

- How we checked the solver and scripts: Benchmarked against NAFEMS LE10 and VB08; errors < 1.2% for linear elastic stress and < 3.5% for contact patch pressure. Custom bolt-preload Python utilities have unit tests (13 cases) passing; energy balance checked in a simple lap joint.

- Mesh refinement evidence: Three meshes (1.2M, 3.5M, 6.4M elements). Peak von Mises at the inner fillet trends to 655 MPa by Richardson fit; finest-mesh value 648 MPa. Estimated numerical shortfall ~4.1%. Modal frequencies changed < 1.8% between the last two meshes.

- Numerics/settings stability: NLGEOM on during preload and load transfer, off for the linear dynamics step. Convergence tolerances tightened to 5e-4 on force residual; automatic stabilization disabled. No cutbacks or contact chatter observed in the final mesh runs.

- Where the material and joint numbers came from: Ti-6Al-4V AMS 4928 per MMPDS-17; E=114±3% GPa, yield=880 MPa at 20 C, with temperature knockdowns per M&P memo LL-MP-221. NASM fastener stiffness from supplier certs. Friction 0.18–0.24 from coupon tribology (TN-TRIB-042).

- Loads and constraints pedigree: Quasi-static vectoring loads from GN&C Rev C (±5% allocation). Random vibe PSD from Environments Rev G. Thermal gradient from TMM Rev C (node map provided). Fixture boundary condition mimics test stand per STR-TST-018.

- Any numbers adjusted to fit data: None. No backfitting performed; friction range retained as tested. Pretension set to 8.5±0.8 kN per torque-preload curve.

- How it lines up with hardware: Subscale bracket test with attached mass; 12 strain gages. RMS error 6.1% across gages for quasi-static load; worst-case gage off by 9%. First mode predicted 412 Hz vs. 397 Hz measured (+3.8%). Onset of micro-slip within 8% of prediction.

- Handling of variability: Propagated E, friction, pretension, and load scatter through 500 Latin-hypercube samples on the mid-mesh. 95th-percentile peak stress 702 MPa at the hot spot. Using 880 MPa yield, margin = 0.25 at P95. Frequency 5th percentile 386 Hz > 350 Hz target.

- What drives the outputs: Sobol ranking shows friction and pretension dominate stress at the pad (66% combined). Material modulus contributes 11%. Fillet radius shows local effect; ±0.1 mm tolerance moves peak stress by ~3%.

- Where this model is valid: Temperatures -130 to +90 C (per M&P curves), pretension 7–10 kN, friction 0.18–0.24, loads within Rev C/G envelopes. Large plasticity, wear, and fretting are not represented; separate analyses will address those for CDR.

- Behavior across scenarios: Changing solver increment limits and contact enforcement (penalty vs. kinematic) moved peak stress by < 2.5%. With the line mass ±10%, first mode varies ±4.2% and maintains separation to line modes by > 25 Hz.

- Tool and data control: Models and scripts under Git LFS, tag LL-PL-SUPT_R5. Abaqus job files archived to Windchill with checksum. All inputs trace to controlled sources; requirements traced in DOORS module STR-LL-PL-02.

- Documentation trail: Run summaries (RPT-LL-FEA-112 to -117) include meshes, solver settings, and seed values. Postprocessing Python notebooks have embedded metadata and recreate all plots. A parameter map links each figure to the exact job ID.

- People and reviews: Team: 1 PE (12 yrs), 1 senior analyst (8 yrs), 1 early-career (3 yrs). Peer review held 02 Aug; red-team flagged missing pretension scatter in early runs—now addressed. Independent structures panel concurrence 05 Aug with two minor actions closed.

- Prior track record: Similar bracket (LL-AVIO-27) analyzed with the same workflow matched ETU static tests within 5% and flight accelerometer-derived modal IDs within 4% on CLPS-3.

Open items: We will add a spot check with a hexahedral-dominant mesh at the hot spot (ETA 1 week) and rerun the UQ with updated friction CDFs when the second tribology batch lands (ETA 2 weeks). Neither is expected to change the P95 margin trend.

Recommendation: Proceed to PDR with this model as the decision basis, noting the applicability limits and planned follow-ups above.
