To: Maria Chen, R&D Lead
From: D. Patel, Simulation
Date: 2026-08-06
Subject: FEA status for 5.5 mm Ti screw–rod construct against ASTM F1717-like setup

Short version
- The current model reproduces frame stiffness within 7% of our two-bay fixture tests and shows the same hot spot at the rod-to-screw fillet as the failed parts.
- Mesh refinement around the fillet appears adequate; stress moved less than 3% between the last two meshes.
- Results are moderately sensitive to the assumed screw–tulip friction; less so to the elastic modulus.
- Items we did not get to this sprint: fatigue-life prediction, geometric tolerances, and set-screw seating torque variation.

What we ran
- Geometry: CAD from PDM rev G. Threads represented as smooth cylinders; fillet radii preserved. The set screw is included as a solid.
- Materials: Ti‑6Al‑4V E = 114 GPa, ν = 0.34; plastic hardening not active for the main runs (kept linear) because measured strains were under 0.3%. A check case with bilinear plasticity (E_tan = 2 GPa, σ_y = 880 MPa) shifted peak stress by +4% at the fillet but did not change stiffness in the linear range.
- Elements: 10‑node tets (Abaqus C3D10). Contact: surface-to-surface, penalty, isotropic friction set to μ = 0.15 between rod–tulip and tulip–screw head. Set screw to rod contact also active.
- Loads and supports follow the two-post frame arrangement. The lower block is fixed. Upper block is driven to 6 mm vertical displacement via a reference point and coupling. Lateral guides allowed per the fixture.
- Solver: static, large‑deflection on. Automatic time stepping with default stabilization off.

Mesh study
- Three meshes: coarse (global 1.2 mm, 0.5 mm local near fillets), medium (0.9/0.35 mm), fine (0.7/0.25 mm). Element counts: 0.86M, 1.54M, 2.78M respectively.
- Quantity checked: peak von Mises at the rod fillet under 6 mm actuator travel, and frame force at 2 mm travel (linear stiffness proxy).
- Changes relative to medium: coarse→medium: stress −6.3%, stiffness −1.8%; medium→fine: stress −2.1%, stiffness −0.4%. We stayed with the medium mesh for sweeps; spot‑checked one fine run to confirm.

Bench comparison
- Two physical frames assembled with the same parts as the model (rod length 120 mm, screw spacing 40 mm). Displacement applied at 1 mm/min to 6 mm; force read by load cell (Instron 5967).
- Measured force at 2 mm: 1.82 kN and 1.86 kN (avg 1.84 kN). Model with μ = 0.15 gave 1.71 kN (−7.1% from average).
- Failure observations from a separate over‑load: first plastic marking initiated at the rod fillet adjacent to the proximal screw; the FEA’s highest stresses/strains localize at that same radius on the inner bend.
- We did not model thread engagement or preload from the set screw; see Sensitivities below for the effect of contact friction.

Sensitivities and what moves the needle
- Friction: μ = 0.10 → force at 2 mm = 1.63 kN; μ = 0.20 → 1.77 kN. Peak fillet stress shifts by +5% (low μ) to −3% (high μ) relative to μ = 0.15.
- Modulus: E = 108–120 GPa (per supplier cert range) changes the 2 mm force by ±2.6%; stress follows by ±1.9%. This does not close the full gap to the test on its own.
- Contact formulation: switching penalty to kinematic at the tulip–rod interface increases the predicted stiffness by ~3% and slightly reduces contact slip. We kept penalty to avoid over‑constraint.
- Plasticity: enabling bilinear hardening at the rod under the 6 mm pull adds ~0.2% compliance; negligible for the stiffness metric of interest.

What this means for the decision at hand
- For early design screening of fillet shape and rod diameter, the present setup is giving the right neighborhood for both stiffness and stress location. The 7% stiffness under‑prediction is consistent across two frames and is largely attributable to the friction assumption and the choice of contact enforcement.
- The hot spot alignment with the observed initiation site increases confidence in using the model to rank design variants by relative stress.

Gaps and next steps
- Fatigue life was not addressed; the lab data we have are single‑pull only. We will add a simplified strain‑life estimate once we have cyclic test points.
- Manufacturing variation (rod diameter tolerance ±0.05 mm, fillet radius tolerance ±0.1 mm) and set‑screw torque scatter were not explored; both could move contact slip and local stress.
- We did not include clamp bar deformation in the upper block; a solid model of the fixture may close some of the stiffness gap. We have the CAD but did not have time to mesh it.

Files and trace
- Abaqus/CAE 2022 HF2. Model: “F1717_frame_revG_dp27.cae”. Runs on “sim-node-04”. Pre/Post in HyperMesh 2023. Results plots exported to Vault under “/FEA/FrameRevG/2026-08-05”.

Ask
- Green‑light using this model for comparing the two pending rod fillet options (r = 1.0 vs 1.5 mm). I’ll keep μ = 0.15 and report relative changes; absolute stiffness deltas can be rescaled if needed once we tune contact to the fixture.
