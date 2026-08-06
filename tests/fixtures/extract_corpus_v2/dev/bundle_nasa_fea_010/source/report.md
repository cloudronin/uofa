To: Lander Structures IPT Lead
From: P. Nguyen, FEA Lead
Date: 2026-08-06
Subject: Credibility status of landing leg clevis FEA model (LLC-FEA-21) for pre-PDR loads screening

Context
We evaluated the Abaqus/Standard model of the Ti‑6Al‑4V clevis that ties the landing leg to the primary structure under the touchdown load cases (axial crush plus 15° side-load). The current intent is to use this model for pre-PDR trade screening and to bound gapping at the pin-bushing interface.

Summary of evidence
- Geometry and contacts: Model includes full clevis geometry with fillets as-designed (Rev E). Pin is represented as a rigid body with a deformable bushing; surface-to-surface contact, penalty method, μ=0.20. Nonlinear kinematics enabled; automatic stabilization set to 5e‑4.
- Material data: Clevis uses Ti‑6Al‑4V with E=114 GPa, ν=0.34. For yield, the run deck dated 2026‑07‑18 references the MMPDS-17 value of 930 MPa. However, the material card in the same deck lists σy=885 MPa from Vendor Lot 4Q25; tangent modulus 1.2 GPa (bilinear plasticity). Density 4.43 g/cc.
- Loads and supports: Axial load 52 kN with 15° lateral component applied at the pin center; housing constrained by three bolt patterns via coupled DOF to test fixture nodes. Note: the narrative says “base clamped,” but the boundary condition set FIX_3BOLT behaves as pinned about the Y-axis (free rotation).
- Numerical checks: A three-level mesh refinement was attempted (global size 2.5 mm, 1.6 mm, 1.0 mm around the lug eye; quadratic tetra in the bulk, hex in the ligament). The cover memo asserts “<3% change in peak von Mises at the hotspot between last two meshes.” The postprocessor CSV in the archive shows 612 MPa, 664 MPa, 742 MPa at the same probe point, which is a 12% change from medium to fine. Contact penetration reduces from 18 μm to 7 μm across the series.
- Comparison to test: Single-axis bench test on the EDM surrogate (Room Temp, μ unknown) is cited as “within 5% for pin deflection at 30 kN.” The plotted data set in the same folder shows FEA 0.62 mm vs test 0.69 mm at 30 kN (11% low), and strain gage SG-3 peak 820 με (FEA) vs 895 με (test) at 52 kN (9% low). The test used a bonded bushing; the model allows slip.
- Spread due to inputs: A short sweep was run: μ=0.15/0.20/0.30 and σy=885/930 MPa. The slide in “LLC-FEA-21_sensitivity.pptx” quotes “10% total variability in peak stress.” Recreating the cases shows combined effect pushes the hotspot stress from 702 to 812 MPa (16%). Thermal preload is not included; CTE is present in the material but no temperature field is applied. Intended environment is down to −170°C.
- Toolchain and reproducibility: The report cover page states Abaqus 2022HF3; the solver log in the run directory lists 2021x (build 2021.1-6). We could not bitwise reproduce the fine-mesh result; rerun on 2022HF3 yields 736 MPa vs archived 742 MPa. The python pre-mesh script “lug_mesh.py” is not under version control and was modified on a local workstation. Model check is clean; no negative pivots; residual force drops 3 orders of magnitude but one contact constraint hovers at 6.5% of peak.
- People and review: Primary analyst (Nguyen) ran the study; mesh built by summer associate D. Ruiz. Peer review sign-off lists Nguyen as approver and author; an independent check by Loads & Dynamics is scheduled next sprint but is not yet complete. A previous version of this model (LLC-FEA-19) supported hinge trade studies; that version used linear elasticity only.

Observations and gaps
- There is disagreement between the narrative claims of mesh stability (<3%) and the archived probe values (~12%). Hotspot location also drifts 0.4 mm between meshes, which complicates direct comparison.
- The difference between using 885 MPa and 930 MPa yield is not explicitly tracked in the margin summary; yet bilinear plasticity is activated in the current deck while the test correlation slide assumes linear material.
- Boundary conditions in the model (pinned about Y) do not match “base clamped” wording nor the bonded bushing used in the bench test. This likely explains the 9–11% underprediction of gage strains and deflection.
- The total variability quoted as 10% omits temperature and misalignment; prior coupon data show ~20% lot-to-lot scatter in σy for Ti‑6Al‑4V, which would reduce apparent margin.
- Software version inconsistency (2021x vs 2022HF3) and the untracked meshing script limit replayability. The delta in peak stress (742 vs 736 MPa) is small but unexplained.
- Intended use includes cryogenic conditions; no validation or even screening analysis has been done below room temperature.

Provisional margins
- Using the fine mesh and μ=0.20, peak von Mises at the fillet is 742 MPa at 52 kN with the current plastic law. Against σy=930 MPa the elastic-plastic equivalent margin is ~1.25; against 885 MPa it is ~1.19. If the 16% variability observed in the mini-sweep is included and −170°C strength knock-up is ignored, margins could be as low as ~1.02–1.05 in the worst credible combination. These numbers are sensitive to the base restraint.

Recommendation and actions
- Align the boundary conditions with the test (either bond the bushing in the model for comparison, or repeat the test with slip).
- Repeat the mesh study with a consistent hotspot metric (either structural stress at a fixed path or notch intensity), and document GCI-style estimates.
- Lock the toolchain (solver build and scripts) and archive the exact inputs that generated the posted results.
- Expand the sensitivity to include temperature, fixture stiffness, and pin-bushing friction; explicitly propagate into the margin table.

Decision
Given the above, the clevis model is accepted for preliminary design trade screening and relative trend studies, subject to not being used for final margin closure, hardware release, or cryogenic assessments. It is not approved for cert-level decisions. Decision by: Lander Structures IPT Lead, concurred by Chief Analyst.
