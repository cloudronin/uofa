# INTERNAL TECHNICAL MEMO

**To:** Dr. Priya Nandakumar, Project Lead – Structural Integrity Program
**From:** Marcus Tollefsen, Computational Mechanics Group
**Date:** 14 March 2025
**Re:** V&V Status – Tibial Tray FEA Model (Revision 3), Pre-Design-Freeze Review

---

Priya,

Here's a quick summary of where things stand on the finite-element work for the tibial tray before Thursday's design-freeze gate. I'll flag the gaps openly so you can decide what needs to close before we sign off.

---

## What the Model Is Doing

The ANSYS Mechanical 2024 R1 model represents a cobalt-chrome tibial tray under worst-case ISO 14879-1 loading: 2,600 N axial with 10 Nm torsion applied at the stem tip, fully constrained at the cortical shell interface. We're using second-order tetrahedral elements (SOLID187) throughout, with contact pairs at the tray-polyethylene interface modeled as frictional (μ = 0.04, Lagrange multiplier enforcement). The purpose is to support a design claim that peak von Mises stress stays below 450 MPa under the envelope load case.

---

## Mesh Refinement Study

We ran three mesh densities on the stem-keel junction region, which is where we expected the worst stress concentration. Global element sizes were 2.0 mm, 1.0 mm, and 0.5 mm; the junction zone was additionally refined with a 0.25 mm local sizing in all three cases. Peak von Mises at the keel fillet went from 387 MPa → 412 MPa → 419 MPa across the three levels. Richardson extrapolation gives an estimated converged value of ~422 MPa, with a grid convergence index (GCI) of 1.8% between the two finest meshes. We're calling the 0.5 mm mesh adequate for the design claim; the margin to the 450 MPa limit is thin (roughly 6% on the extrapolated value) but acceptable given the conservatism already in the load case. No further refinement is planned before freeze.

---

## Solver and Code Checks

The ANSYS solver version in use (2024 R1, build 24.1.0.3) has been validated against in-house benchmark cases — specifically a thick-walled cylinder under internal pressure and a cantilevered beam with tip moment — as part of our lab's annual software qualification cycle (SQC-2024-11, on file). Both benchmarks matched analytical solutions to within 0.3%. We also ran a simple patch test on the SOLID187 element formulation to confirm that the element passes constant-strain reproduction; it does. I'm satisfied the solver itself isn't introducing errors we haven't accounted for.

---

## Comparison to Physical Test Data

Here's where I want to be transparent about a limitation. We do not yet have coupon-level or component-level test data from the current tray geometry. The comparison we can offer is against a prior-generation tray (Revision 1, different keel geometry, same alloy) tested under ISO 14879-1 last year. That model predicted peak strain at the anterior flange within 8% of the measured rosette gauge reading. That's a reasonable analogy but it is not a direct validation of this geometry. The physical testing program for Rev 3 is scheduled for Q3 2025 — well after design freeze. I'd flag this as the most significant open item from a credibility standpoint.

---

## Input Loads and Boundary Conditions

The 2,600 N / 10 Nm load case comes from the biomechanics team's envelope analysis (report BM-2024-47), which itself draws on instrumented implant data from the OrthoLoad database. I reviewed BM-2024-47 and the derivation looks sound; the 95th-percentile stair-descent case drives the axial load, and the torsion component is a conservative bound. Boundary condition sensitivity hasn't been formally documented for this revision — we spot-checked a fully-bonded vs. frictional stem-bone interface and saw a 14% difference in stem peak stress, which is non-trivial. I'd recommend at least a one-page sensitivity note be added to the model record before freeze.

---

## Material Properties

Elastic modulus and Poisson's ratio for the CoCr alloy (ASTM F75) are taken from the material certificate for Lot 2023-CoCr-114 (E = 210 GPa, ν = 0.30). These are consistent with published ranges. The model is linear-elastic; we are not capturing any plasticity, which is appropriate given that the design intent is to stay well below yield (550 MPa UTS-adjacent). No temperature-dependent properties are included — the analysis is isothermal, which is standard for this load case.

---

## What We Haven't Addressed Yet

A few things are explicitly out of scope for this memo and this model revision:

- **Fatigue life estimation** is deferred to the post-freeze phase. The current model gives peak stress for a static envelope case only. Cycle-dependent damage accumulation will require a separate S-N or fracture-mechanics sub-model and is planned for Q2 2025.
- **Uncertainty quantification on material scatter** — we've used nominal Lot 114 values, but we haven't propagated the inter-lot variability (±5 GPa on E across our supplier's historical certs) through the model. This was descoped due to schedule pressure.
- **Independent review of the modeling choices** (contact formulation, constraint approach) by someone outside our group has not happened for Rev 3. The Rev 1 model went through a peer check; Rev 3 changes were treated as incremental. I'd suggest at minimum a checklist review by someone from the implant mechanics group before we submit to the notified body.
- **Software configuration management** records for the specific ANSYS installation used on the cluster nodes are pending IT confirmation. We believe we're running 2024 R1 consistently, but the formal CM record hasn't been closed.

---

## Bottom Line

The mesh convergence is solid and the solver is qualified. The structural result (419 MPa peak, ~6% margin) is defensible but tight. The main credibility gap is the absence of Rev 3 physical test data — the analogy to Rev 1 is reasonable but not airtight. I'd recommend we document the boundary condition sensitivity formally and flag the test-data gap explicitly in the submission package rather than burying it.

Happy to discuss Thursday before the gate meeting.

Marcus

---
*Computational Mechanics Group | Orthopaedic Device Division*
*File ref: FEA-TIB-REV3-VV-MEMO-001*
