# INTERNAL TECHNICAL MEMO

**To:** Dr. Priya Nandakumar, Project Lead – Thermal Systems Group
**From:** Marcus Ellerbee, V&V Engineer
**Date:** 14 March 2025
**Re:** CHT Simulation Credibility Status – Turbine Blade Trailing-Edge Cooling Insert (Rev B model)

---

## Background

This memo summarizes the current verification and validation posture for the conjugate heat transfer simulation of the trailing-edge cooling insert used in the Stage-1 turbine blade assembly (program designation: TE-Cool-Rev-B). The ANSYS Fluent 2023 R2 solver is being used to predict metal temperature distributions and coolant pressure drop under engine representative conditions. I'm writing ahead of the CDR gate to flag what we have, what we're still missing, and where I think the risk sits.

---

## What We've Done So Far

**Grid independence work.** We ran a three-level mesh refinement study using element counts of approximately 2.1M, 6.4M, and 17.8M cells. The coarse-to-medium and medium-to-fine comparisons show less than 1.8% variation in peak blade metal temperature and roughly 2.4% variation in total pressure drop across the insert. Richardson extrapolation gives a GCI of about 0.9% on the temperature metric. I'm comfortable calling discretization error well-controlled at the medium mesh level, which is what we're using for all production runs.

**Solver behavior and residual convergence.** All steady-state runs converge to residuals below 1×10⁻⁵ on energy and 1×10⁻⁴ on momentum/continuity. We've also monitored outlet bulk temperature and a representative thermocouple-proxy location; both flatten to within 0.05 K over the last 500 iterations. No oscillatory behavior observed.

**Turbulence modeling sensitivity.** We compared SST k-ω against realizable k-ε for the internal coolant passages. The two models agree within 4% on Nusselt number distribution along the pressure-side rib array, which is the region of greatest thermal gradient. This is consistent with prior literature on similar rib-roughened channel geometries (Han et al., internal reference TG-2019-04). We're using SST k-ω as the baseline.

**Comparison to experimental data.** We have access to a rig dataset from the 2022 Oxford Turbine Research Facility campaign (test series OX-TRF-44) that used a scaled acrylic model at matched Reynolds number (Re ≈ 28,000 based on hydraulic diameter). Simulated Nusselt number profiles along three spanwise measurement lines show agreement within ±9% of the measured values. Peak temperature predictions at the five thermocouple-equivalent locations are within 11 K of rig measurements, against a maximum measured value of ~840 K in the scaled-equivalent mapping. I'd characterize this as acceptable for this class of problem but not excellent — the discrepancy at the trailing-edge cutback region is consistently on the high side (model overpredicts local heat flux), which I think is a geometry fidelity issue in the simplified fillet representation.

**Boundary condition sourcing.** Inlet total temperature and total pressure are drawn from a 1D cycle deck (GasTurb 14 output, cycle point CP-03-HPC-exit). Coolant inlet conditions are from the same deck. I've confirmed the values are consistent with the test rig scaling relationships used in OX-TRF-44. The combustor exit temperature profile (radial distortion) is applied as a mapped boundary condition interpolated from a separate CFD solution of the combustor domain — that upstream solution has its own V&V lineage which I'm not covering here.

**Sensitivity to material properties.** We ran a brief parameter sweep varying the blade alloy thermal conductivity (IN718 baseline at 11.4 W/m·K) by ±10% to bracket manufacturing and temperature-dependent uncertainty. Peak metal temperature shifts by approximately ±14 K, which is non-negligible. The coolant-side heat transfer coefficient is less sensitive to this parameter than I initially expected.

---

## What's Not Covered in This Memo

A few areas fall outside the scope of this phase or have been deferred:

- **Oxidation and thermal barrier coating degradation effects** on effective conductivity are not modeled. The program has decided to treat TBC as a fixed resistance layer; a separate lifing analysis will address degradation. This is a known limitation for long-dwell mission profiles.

- **Unsteady effects** — the simulation is steady-state. Blade passing frequency interactions and potential hot streak migration are not captured. The program's position is that time-averaged predictions are sufficient for the current design phase, but this should be revisited before final certification modeling.

- **Uncertainty quantification on turbulence model form error** has not been formally conducted. We've done the two-model comparison noted above, but a structured UQ treatment (e.g., eigenspace perturbation or Bayesian calibration against the rig data) is not yet done. This is on the backlog for Phase 2.

- **Code verification against a manufactured solution** for the CHT coupling specifically has not been performed. ANSYS Fluent's CHT capability is treated as a commercial black-box here; we're relying on the vendor's published verification suite and the grid study as indirect evidence. I recognize this is a gap.

---

## Overall Assessment

The simulation is in reasonable shape for a CDR-level review. The mesh refinement study and experimental comparison give me reasonable confidence in the bulk thermal predictions. The trailing-edge cutback region remains the highest-uncertainty zone, and I'd recommend flagging that in the CDR package with the ±11 K band as the stated prediction interval.

The main credibility risks I see are: (1) absence of formal UQ on turbulence model uncertainty, (2) reliance on vendor verification for the CHT coupling rather than in-house manufactured solution testing, and (3) the steady-state assumption, which may not be conservative for the most thermally loaded operating points.

Happy to discuss at the pre-CDR walkthrough Thursday.

— Marcus

---

*Distribution: P. Nandakumar, T. Osei-Bonsu (Thermal Analysis), CDR Review File*
*Classification: Program Confidential – Internal Use Only*
