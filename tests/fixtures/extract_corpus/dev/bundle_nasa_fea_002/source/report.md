# INTERNAL TECHNICAL MEMO

**To:** Dr. Priya Nambiar, Structures Program Lead
**From:** Marcus Ellroy, V&V Lead, Computational Mechanics Group
**Date:** 14 March 2025
**Re:** FEA Credibility Status — Orbital Docking Adapter Bracket Assembly (ODABA), Pre-CDR Review

---

## Purpose

This memo summarizes the current verification and validation posture for the ABAQUS 2023.HF4 finite-element model of the ODABA primary load-bearing bracket. The intent is to flag where we have reasonable confidence, where gaps remain, and what the team should prioritize before the Critical Design Review scheduled for 28 April.

---

## Model Scope and Application

The model covers the titanium Ti-6Al-4V bracket assembly connecting the docking ring to the spacecraft bus panel. Primary load cases are launch-lock preload (axial, 14,200 N), docking capture shock (lateral impulse, modeled as 80 ms half-sine at 1,800 N peak), and on-orbit thermal soak (-120°C to +95°C delta). The quantity of interest driving design decisions is peak von Mises stress at the lug bore interface and the first three natural frequencies of the assembled bracket.

---

## Code and Solution Verification

The ABAQUS solver version used here (2023.HF4) has been through our group's standard in-house checkout procedure. We ran the Timoshenko beam bending benchmark and the Hertzian contact patch problem from NAFEMS benchmark set R0016; both came within 0.8% of analytical solutions. The contact mechanics implementation (surface-to-surface, finite sliding, penalty stiffness 1×10⁵ N/mm) was separately exercised against a known cylindrical indentation case. No anomalous behavior was observed. I'd call this portion solid.

Mesh refinement was conducted using three successive hex-dominant meshes: coarse (42,000 elements, average edge length ~3.2 mm at the lug), medium (118,000 elements, ~1.6 mm), and fine (310,000 elements, ~0.8 mm). Peak stress at the lug bore changed by 11.4% between coarse and medium, and by 2.9% between medium and fine — suggesting the medium mesh is adequate for design-level decisions but the fine mesh will be used for final margin calculations. No formal Richardson extrapolation was performed; that's on the to-do list before CDR. Modal frequencies were stable to within 0.4% between medium and fine meshes, so we're comfortable there.

---

## Input Data and Material Representation

Material properties (Young's modulus 113.8 GPa, Poisson's ratio 0.342, density 4430 kg/m³, yield 880 MPa) were taken from the coupon test reports provided by the titanium supplier (Timet lot TT-2024-0917). Fatigue data were not incorporated into this model; that's being handled separately by the durability team and is out of scope for this structural margin assessment.

Fastener preloads were specified per the torque-tension correlation from our standard test campaign (bolt lot B-441, coefficient of friction μ = 0.14 ± 0.02). The ±0.02 scatter on friction coefficient was propagated through two bounding runs (μ = 0.12 and μ = 0.16), and the resulting preload variation produced a ±4.3% change in lug bore peak stress — within acceptable bounds.

One area I want to flag: the thermal boundary conditions for the soak case were taken from a preliminary thermal model output that has not yet been formally baselined. The thermal team has indicated values may shift by up to ±12°C at the bracket foot once their updated solar flux inputs are incorporated. We haven't re-run the FEA with those potential updates yet.

---

## Validation Against Physical Test Data

A static pull test was conducted on a bracket engineering development unit (EDU-2) at our Structures Test Lab in February. The test applied axial load in 500 N increments to 16,000 N (112% of design limit load). Strain gauges at four locations were compared to model-predicted strains. Agreement was within 7% at gauges SG-1, SG-2, and SG-4. Gauge SG-3, located near the fillet radius, showed an 18% discrepancy — likely attributable to local geometry idealization in the CAD-to-mesh translation (the fillet was simplified from a 1.5 mm blend to a sharp corner in the mesh). This has been noted as a model limitation; the fillet will be explicitly meshed before CDR.

No dynamic test data are available yet. The modal predictions (first mode at 312 Hz, second at 487 Hz, third at 631 Hz) remain unvalidated against hardware. A modal survey on EDU-2 is planned for early April; results will be incorporated post-CDR if the schedule holds.

---

## Uncertainty and Sensitivity Considerations

Beyond the friction coefficient variation noted above, we ran a limited parameter sweep on the contact stiffness penalty value (varied ±50%) and observed less than 1.2% change in peak stress — so that numerical parameter is not a dominant source of uncertainty. We have not yet conducted a formal sensitivity study across the full input space (geometry tolerances, material lot-to-lot scatter, load uncertainty). That level of analysis is scoped for the Phase C verification plan but wasn't resourced for this cycle.

---

## Intended Use and Decision Context

The model is being used to assess structural margins against NASA-STD-5020 fastened joint criteria and to support mass reduction trade studies (specifically, whether a 10% wall thickness reduction is feasible). For the margin assessment use case, I believe the model has adequate fidelity given the static test correlation described above, with the caveat about the SG-3 fillet discrepancy. For the mass reduction trade, I'd want the full mesh refinement extrapolation and the fillet geometry corrected before drawing conclusions — the stress concentration factor at the lug bore is precisely what changes with that design modification.

---

## Items Not Addressed in This Memo

To be explicit about scope: the following are not covered here and should not be inferred from this document —

- Long-term creep or stress relaxation of fasteners under sustained preload (deferred to Phase C)
- Fracture mechanics / damage tolerance assessment (separate analysis stream, fracture mechanics group)
- Any review of the human-in-the-loop assembly process or torque application procedure from an error-prevention standpoint (this is a computational model assessment, not a process review)

---

## Summary Assessment

| Area | Status |
|---|---|
| Solver benchmarking | Acceptable |
| Mesh refinement | Adequate; Richardson extrapolation pending |
| Static test correlation | Mostly good; SG-3 fillet discrepancy needs resolution |
| Material input data | Acceptable (supplier certs in hand) |
| Thermal BC inputs | Provisional — pending thermal model update |
| Dynamic test correlation | Not yet available |
| Full uncertainty quantification | Deferred to Phase C |

Overall, the model is in reasonable shape for a pre-CDR assessment of the primary load case. I recommend proceeding with CDR with the explicit caveat that the fillet mesh correction and Richardson extrapolation are completed and documented in the CDR data package. The dynamic validation gap is a known open item and should be captured in the risk register.

Please let me know if you'd like me to present this at the April 7th structures working group.

— Marcus
