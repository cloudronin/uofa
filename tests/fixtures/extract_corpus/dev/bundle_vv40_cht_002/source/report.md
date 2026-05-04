# INTERNAL TECHNICAL MEMO

**To:** Dr. Priya Nambiar, Program Lead – Thermal Management Systems
**From:** J. Ostergaard, Simulation Engineering
**Date:** 14 March 2025
**Subject:** V&V Status Update – CHT Solver Assessment for Blade Cooling Channel Model (Rev 2)
**Project:** NGT-7 High-Pressure Turbine Cooling, Phase IIB

---

Priya,

Following last week's design review I wanted to get you a written summary of where the simulation credibility work stands before the milestone gate. The short version: we're in reasonable shape on the thermal side, less so on the flow side, and there are a few areas we simply haven't touched yet because the vendor test data hasn't come in.

---

## 1. What the Model Is Doing

The model in question is the ANSYS Fluent 2024 R1 conjugate heat transfer setup for the NGT-7 serpentine cooling channel. It couples the compressible RANS flow solution (SST k-ω, wall y⁺ held between 1 and 5) with a solid conduction solve in the Inconel 718 blade wall. Inlet total pressure is 2.41 MPa, coolant inlet temperature 623 K, and we're running at three representative corrected mass flow rates (0.041, 0.055, and 0.071 kg/s) that bracket the expected operating envelope. The outputs of interest are: (a) peak metal temperature at the pressure-side leading edge, (b) spatially averaged Nusselt number along the first pass, and (c) pressure drop across the full serpentine.

---

## 2. Intended Use and Scope

I want to be explicit about scope because it matters for how to read the rest of this memo. This model is being used to support a **design screening decision** — specifically, whether the current channel geometry keeps peak metal temperature below 1,143 K under worst-case inlet conditions. It is NOT being used to certify hardware or replace rig testing. The rig campaign is still planned for Q3. This distinction is relevant when assessing how much rigor we need right now versus what we can defer.

---

## 3. Governing Equations and Physical Fidelity

The solver uses the standard compressible Navier-Stokes equations with the energy equation fully coupled to the solid domain via a conforming mesh interface — no thermal resistance is assumed at the fluid-solid boundary, which is appropriate given the geometry. Buoyancy effects are neglected (Richardson number < 0.04 at all three operating points), and radiation is excluded. We did a quick order-of-magnitude check: at these temperatures and optical depths, radiation contributes less than 0.8% to total heat flux. Both exclusions are documented in the model assumptions register (MAR-NGT7-CHT-002).

One concern I flagged to the team: the SST k-ω model is known to overpredict turbulent heat transfer in strongly curved passages. We ran a brief sensitivity sweep using the Realizable k-ε model as an alternative, and the peak metal temperature prediction shifted by +17 K. That's not negligible at our margin. I'd recommend we flag this as an open uncertainty item rather than close it out.

---

## 4. Code Verification and Numerical Behavior

We ran the standard Fluent manufactured-solution test for the energy equation in the solid domain using an in-house Python script (repo: `ngtvv/cht_mms_solid_v3.py`). Observed order of accuracy was 1.94 on a structured hex mesh, consistent with the expected second-order behavior. Residuals in the coupled solve drop to below 1×10⁻⁶ for all equations before we declare convergence; we also monitor the surface-averaged heat flux at the fluid-solid interface and require it to stabilize to within 0.1 W/m² over the last 500 iterations. Both criteria are met at all three operating points.

---

## 5. Mesh Refinement Study

We ran a three-level mesh study on the nominal operating point (0.055 kg/s). Coarse: ~2.1M cells; medium: ~5.8M cells; fine: ~14.2M cells. The Grid Convergence Index (GCI) for peak metal temperature between the medium and fine meshes is 0.7%, which is acceptable. For the first-pass Nusselt number the GCI is 2.1%. Pressure drop GCI is 1.4%. All three quantities show monotonic convergence. We are running production cases on the medium mesh as the best balance of accuracy and turnaround time. The fine-mesh solution is archived.

---

## 6. Comparison Against Reference Data

This is the area with the most work still to do. We have two sources of comparison data currently available:

**Literature correlations:** The Dittus-Boelter and Gnielinski correlations were applied to the straight inlet section (hydraulic diameter 3.2 mm, Re range 18,000–42,000). The Fluent predictions for the Nusselt number in that straight section agree with Gnielinski to within 4.3% across all three flow rates. That's reasonable but not a rigorous validation — the geometry is much more complex downstream.

**In-house rig data (partial):** We have legacy pressure-drop measurements from a 2019 water-flow rig test of a geometrically similar (not identical) channel. The current model overpredicts pressure drop by approximately 11% relative to that legacy dataset at the middle flow rate. We believe the discrepancy is partly attributable to the geometry differences (the 2019 rig had a slightly larger turn radius at the 180° bend), but we haven't formally quantified that contribution. Until the Q3 rig data comes in, this comparison has limited conclusive value.

I want to be honest: we do not yet have a rigorous, like-for-like experimental dataset against which to validate the thermal predictions. The Nusselt comparisons above are encouraging but insufficient to claim validated thermal accuracy. This should be called out clearly in the gate review.

---

## 7. Uncertainty Quantification

We performed a basic sensitivity study on the three inputs with the largest expected variability: inlet total pressure (±1.5%), inlet temperature (±8 K), and wall roughness height (±30%). Using a one-at-a-time approach, the combined effect on peak metal temperature spans approximately ±28 K relative to the nominal prediction of 1,097 K. This is a rough bound, not a formal UQ analysis — we haven't done a proper variance decomposition or Monte Carlo propagation. Given the design screening purpose, I think this is sufficient for now, but if the model gets promoted to a higher-fidelity use case we'll need to revisit.

---

## 8. What We Haven't Addressed

A few items are deliberately out of scope for this phase and I want to name them explicitly so they don't look like oversights:

- **Software quality and configuration management for the solver itself** — we're relying on Fluent's internal QA and the site license validation. No independent SQA review has been done by our team. This is standard practice for commercial solvers at this program phase but worth noting.
- **Reviewer independence** — the mesh study and code verification checks were done by the same engineer who built the model (T. Harlowe). We haven't had an independent technical review of the simulation setup. This is on the schedule for Phase III.
- **Long-term stability / transient behavior** — the model is steady-state only. Transient start-up and hot-streak migration are deferred to a separate effort.

---

## 9. Summary Assessment

| Area | Status |
|---|---|
| Physical model justification | Adequate for screening; turbulence model sensitivity is an open item |
| Code numerical behavior | Satisfactory (MMS, convergence criteria met) |
| Mesh independence | Satisfactory (GCI < 2.2% for all QoIs) |
| Validation against experiment | Incomplete — partial pressure-drop comparison only; thermal validation pending Q3 rig |
| Input uncertainty bounds | Preliminary (one-at-a-time sensitivity; formal UQ deferred) |
| Intended use alignment | Clearly defined; appropriate for design screening |

My overall read: the model is credible for its stated screening purpose, but should not be used beyond that without the Q3 rig data and a more rigorous validation exercise. I'd recommend the gate review acknowledge the open thermal validation gap explicitly rather than treating the Nusselt correlation comparison as closure.

Let me know if you want me to present any of this live at the Thursday session.

— J. Ostergaard
Simulation Engineering, Ext. 4-7823
