To: R. Patel, Lander Structures Lead
From: M. Ortega, FEA Task Owner
Date: 2026-08-06
Subject: Avionics Shelf Bracket FEA – V&V Status Check (Rev D model)

Short version
We can defend the general deformation trends and bolt load balance, but there are open items around how we treated the material at cryo, how stable the peak stresses are with mesh/contact settings, and whether our boundary conditions really mirror the shaker fixture. I’m comfortable using this model to guide design iteration. I am not yet comfortable using it for flight margin certification without clean-up and a tighter story on correlation.

What we modeled
- Part: Ti-6Al-4V bracket, Rev D CAD (P/N LAV-4123-D), six M6 bolts into an Al honeycomb panel insert pattern; two fillets at 5 mm nominal radius.
- Solver: Abaqus/Standard 2021 HF6. Bracket meshed with quadratic tets (C3D10), min edge 0.8 mm at the upper fillet; bolts represented as connector elements with 12 kN pretension each; contact to panel via surface tie for baseline.
- Loads: Random vibration converted to equivalent static using Miles (4.8 g RMS leading to ~12 g peak), plus a 300 N lateral cable pull. Also ran a separate “8 g quasi-static” case per earlier DDT input.
- Material: Baseline E = 113 GPa, ν = 0.34, σys = 930 MPa. We stated “cryo properties” but mixed sources (see below).

Evidence we have (and don’t)
- Sanity checks on the solver: We recreated a simple cantilever and a bolted lap plate; displacements matched handbook numbers within 2–3%. No formal defect list for the in-house post tools; we used a Python script (pyNodal v0.6) to aggregate bolt forces, and it does not have a unit test suite.
- Mesh behavior: Four meshes (avg size 4.0, 2.0, 1.2, 0.8 mm). The hotspot von Mises at the upper fillet shifted <2% between the last two meshes (M3: 612 MPa; M4: 623 MPa). However, the contact pressure on the panel side increased ~12% between M3 and M4 when we switched from a tied interface to a rough contact with μ = 0.6. Also, the peak stress location moved ~8 mm along the fillet when we enabled bolt preload relaxation.
- Loads and constraints fidelity: Baseline assumes rigid panel (encastre at insert faces). In a sensitivity run we swapped to elastic springs (1.0e7 N/m per bolt DOF); first mode dropped from 155 Hz to 142 Hz. Our test note (Shaker A, 5/28) lists the first mode measured at 142 Hz, so the elastic support looks closer. Yet, the summary in the slide deck still claims “<3% modal difference,” which only applies if you use the rigid-boundary model.
- Input pedigree: We cited MMPDS-17 cryogenic data (E ~ 123 GPa at −150 C) during the design tag-up, but the baseline deck actually uses room-temperature E = 113 GPa from the CMTR. One sensitivity used an orthotropic layup card (holdover from a composite run) by mistake—caught and fixed—but a few early plots labeled “cryo” were produced with the room-temp set. Stress deltas were ~5–9% across these swaps.
- Test/analysis comparison: Strain gauge G2 and G5 on the coupon bracket from the 6/10 bench run are within 18–22% of the finite element predictions under the 12 g Miles case if we use the rigid support. With the elastic support and μ = 0.3 friction, the gap narrows to ~11–13%. The current CDR summary slide says “<10% at gauges,” which is optimistic given what’s actually in the run logs.
- Scatter and knobs: A small parameter sweep (friction 0.2–0.6, preload 10–14 kN, fillet radius ±0.5 mm) changed peak stress by up to 14% and moved the hotspot. We also reported a “3% overall uncertainty” number in the May memo; that was a back-of-envelope combination and not a Monte Carlo.

People, tools, and versioning
- Analysts: Rahul (6 yrs) and Kim (1 yr) built/runs; I reviewed the inputs and signed off on load mapping. Peer review with S. Dev on 6/24 flagged the boundary mismatch to the test. Follow-up is not fully closed.
- Config control: Two models exist named “bracket_revD_v7b” and “bracket_revD_v7b_fix,” with different material cards. The shaker article was Rev C geometry (0.5 mm larger chamfer at the upper fillet). Our model is Rev D. This likely contributes to the gauge differences.

What I recommend before CDR closeout
- Rebaseline to elastic panel support (spring representation) and document it as the default, since that’s what the test sees. Keep the rigid case as a bounding check only.
- Lock the cryogenic property set (E = 123 GPa, ν = 0.34, σys per MMPDS at −150 C) and purge room-temp cards from the model library.
- Repeat the refinement study with contact active and preload relaxation on, and track not just stress magnitude but hotspot stability. Add one more level (~0.6 mm min edge) locally at the fillet.
- Run a short friction/preload sweep (μ = 0.2/0.4/0.6; 10/12/14 kN) and show bands on the stress plots. That will replace the hand-wavy “3%” with something defensible.
- Align geometry with the test article (Rev C) or update the test report to note differences; rerun the modal and gauge cases with the correct chamfer.
- Put pyNodal under basic unit tests and freeze the script version used for CDR plots.

Bottom line
- For internal design decisions: adequate.
- For hardware sign-off: hold until we reconcile the support model with test, lock the material set, and show mesh/contact stability under the finalized setup. Risk to margins if we proceed now: medium.
