# TECHNICAL MEMORANDUM

**To:** Dr. Priya Nambiar, Program Lead — Advanced Cooling Systems  
**From:** V&V Team, Thermal Analysis Group (K. Ostrowski, lead)  
**Date:** 14 March 2025  
**Subject:** Conjugate Heat Transfer Model V&V Status — Turbine Blade Internal Cooling Passages (Rev. C)  
**Reference:** TBL-CHT-2024-077

---

## Purpose

This memo summarizes the current verification and validation standing for the CHT simulation package used to predict internal cooling passage heat transfer in the Stage-1 HPT blade (ANSYS Fluent 2023 R2, double-precision, pressure-based solver). The intent is to give you a concise picture of where we stand before the design-freeze review on 28 March. I've organized this around the areas where reviewers will probe hardest, not in any particular order of importance.

---

## Code Verification and Solver Fidelity

We conducted a suite of manufactured-solution tests on the conjugate solver to confirm that the discretization is behaving as expected before touching any hardware-representative geometry. The energy equation in the solid domain converges at second-order (observed order ≈ 1.94 on a sequence of four systematically refined Cartesian meshes), and the fluid-energy coupling at the solid–fluid interface shows no order degradation down to a cell-size ratio of 0.5. The turbulence model (SST k-ω with low-Re correction) is the same release-verified build used in our pump program; no in-house modifications have been made to the source. Fluent's own regression suite results for this release were reviewed and are on file (TBL-REG-2023R2). We are satisfied the solver arithmetic is correct.

---

## Geometry and Boundary Condition Representativeness

The CAD imported into SpaceClaim is Rev. F of the blade solid model, which matches the investment-cast geometry to within ±0.05 mm per the CMM report (QA-2024-1103). Coolant inlet total pressure and temperature profiles were extracted from the 1D network model (FloMASTER v12) at the design operating point: 41.2 bar, 721 K. The external hot-gas boundary condition is a radially-averaged Nusselt distribution from the Stage-1 aerothermal RANS solution (separate model, not coupled here). We acknowledge this decoupling introduces an approximation — the external BC is frozen at one operating condition and does not respond to blade-metal temperature changes. For the design-point analysis this is judged acceptable; off-design excursions have not yet been assessed.

The coolant properties use a curve-fit to air at elevated pressure validated against NIST data over 600–900 K; maximum deviation from NIST tabulated values is 0.8% in thermal conductivity. Blade alloy (René 80) conductivity as a function of temperature was taken from the material supplier datasheet (Cannon-Muskegon, Lot CM-4471). No independent measurement of this specific lot has been performed — this is flagged as a residual uncertainty.

---

## Mesh Refinement Study and Numerical Uncertainty

A three-level mesh refinement study was completed on the leading-edge impingement sub-region, which is the highest heat-flux zone. Mesh counts were 2.1M, 6.8M, and 19.4M cells (refinement ratio r ≈ 1.48 between levels). The Grid Convergence Index (GCI) was computed following the Roache procedure. Peak metal temperature at the leading edge stagnation point: coarse 1,184 K, medium 1,171 K, fine 1,168 K. GCI on the fine-to-medium interval is 0.9%, indicating we are well into the asymptotic range. The production runs use the medium mesh (6.8M cells) as the cost-performance optimum; the fine mesh result is used as the reference for numerical uncertainty banding (±11 K, 2-sigma equivalent).

Residuals for all transport equations drop a minimum of five orders of magnitude; mass imbalance across the domain is below 0.003%. Convergence was confirmed by monitoring area-averaged wall temperature on three internal surfaces over the final 2,000 iterations — variation less than 0.2 K.

---

## Validation Against Experimental Data

Validation data come from two sources:

**Source 1 — In-house impingement rig (Rig A, ambient pressure, scaled geometry):** A 3× scaled aluminum model of the leading-edge channel was tested at the Thermal Test Facility (TTF) using heated air at 340 K inlet temperature. Forty-two thin-film RTD sensors were embedded in the model wall. The CHT model was run at matched Reynolds number (Re_D = 24,500). Predicted wall temperatures agree with measurements to within ±8 K (RMS) across all sensor locations. The largest local deviation is 19 K at sensor S-17, near a trip-strip junction — this is attributed to manufacturing imperfection in the rib geometry documented in the rig inspection report (TTF-2024-088). This rig test is considered a unit-level validation of the impingement heat transfer physics.

**Source 2 — Literature benchmark (Han et al., ASME J. Turbomachinery, 2019, rotating ribbed channel):** We matched the reported geometry and boundary conditions and reproduced the reported Nusselt number distribution to within 12% on the pressure side and 9% on the suction side. This is consistent with published SST k-ω performance on ribbed channels. The benchmark provides confidence in the rib-channel physics at engine-representative rotation numbers (Ro = 0.24).

No full-engine or full-blade validation data exist for this specific geometry at engine conditions. This is the primary gap in the validation hierarchy.

---

## Uncertainty Quantification and Sensitivity

A formal uncertainty propagation study was performed using a one-at-a-time (OAT) sensitivity sweep across six input parameters: coolant inlet pressure (±2%), coolant inlet temperature (±5 K), external HTC (±10%), alloy conductivity (±5%), coolant mass flow split between passages (±3%), and turbulence intensity at inlet (±2 percentage points). The dominant driver of peak metal temperature uncertainty is the external HTC boundary condition (sensitivity coefficient 0.61 K/K), followed by alloy conductivity (0.28 K/K). Combined RSS uncertainty on peak metal temperature is ±34 K at 95% confidence. This is larger than the numerical uncertainty alone and should be factored into the thermal margin assessment.

No Monte Carlo or polynomial-chaos expansion has been performed; the OAT approach may underestimate interaction effects. This is noted as a limitation for future phases.

---

## Review Process and Independent Checks

The simulation setup, boundary condition logic, and post-processing scripts were reviewed by an independent analyst (T. Bergström, not part of the original modeling team) in February 2025. The review covered mesh topology, BC assignments, material property tables, and the GCI calculation spreadsheet. Two minor issues were identified and corrected: an incorrect reference area in the Nusselt normalization and a stale material property table that had not been updated to René 80 Rev. F values. Both were resolved before the production runs reported here. The corrected results differ from the pre-review values by less than 3 K in peak temperature — within numerical noise. No issues with the solver setup itself were identified.

The simulation plan and validation strategy were also reviewed at the program-level design review in January 2025. Feedback from that review (action items TBL-AI-024 through TBL-AI-031) has been incorporated; all action items are closed.

---

## Applicability to the Intended Use Case

The model is intended to support two decisions: (1) confirm thermal margin at the design operating point, and (2) screen candidate trip-strip configurations for a potential redesign. For decision (1), the validation evidence at unit level and the uncertainty analysis are judged sufficient, with the caveat that the external BC decoupling introduces unquantified error at off-design. For decision (2), the model is being used in a relative-ranking mode — absolute accuracy matters less than the ability to discriminate between configurations. The rig validation and literature benchmark give reasonable confidence in this discriminating capability, provided Reynolds number stays within the validated range (Re_D 18,000–35,000).

Use of these results outside this Re range, or for transient thermal cycling predictions, is not supported by the current validation evidence and would require additional work.

---

## Summary Assessment

Overall, the CHT model is in a mature state for design-point thermal margin assessment. The principal residual uncertainties are (a) the frozen external BC assumption, (b) the absence of lot-specific alloy conductivity data, and (c) the lack of a full-blade validation case at engine conditions. These are documented and bounded to the extent possible. The model is recommended for use in support of the 28 March design-freeze review, with the stated limitations clearly communicated to downstream users.

Questions or requests for additional detail should be directed to K. Ostrowski (ext. 4-7823) or T. Bergström (ext. 4-6610).

---

*Distribution: P. Nambiar, T. Bergström, J. Hollis (Chief Engineer), V&V Records Archive*
