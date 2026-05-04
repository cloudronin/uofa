# INTERNAL TECHNICAL MEMO

**TO:** Dr. Priya Nambiar, CHT Program Lead
**FROM:** Marcus Telle, Computational Methods Group
**DATE:** 2024-03-14
**RE:** V&V Status — Turbine Blade Cooling Channel Simulation (TBCS-3 Model), Pre-CDR Assessment
**CC:** Validation Working Group

---

## Background

This memo summarizes the current verification and validation posture for the TBCS-3 conjugate heat transfer model ahead of the Critical Design Review scheduled for April 18. The model covers internal serpentine cooling passages in a first-stage high-pressure turbine blade, implemented in ANSYS Fluent 2023 R2 with a custom UDF for temperature-dependent conductivity of the IN-738LC substrate. The primary quantities of interest (QoIs) are wall temperature distribution on the pressure-side surface and bulk coolant exit temperature under representative takeoff conditions (inlet total pressure 4.2 MPa, coolant-to-mainstream temperature ratio 0.62).

I want to be upfront: this is a sparse status summary. Several aspects of the assessment are still pending vendor data or have been deferred to the post-CDR phase per the program schedule. I've flagged those gaps where relevant.

---

## What We've Done So Far

### Governing Equations and Physical Fidelity

The solver uses the realizable k-ε turbulence closure with enhanced wall treatment, applied to the coolant-side RANS equations. Conjugate coupling at the fluid-solid interface is handled via Fluent's native coupled wall boundary condition — no explicit interface resistance is assumed, which is appropriate given the surface finish data we have from the manufacturing drawings. The solid domain uses temperature-dependent conductivity from a curve fit to published IN-738LC data (NIST SRD 81 source); the fit residual is below 0.4% across the 400–1200 K range.

One concern I want to flag here: the realizable k-ε model is known to underpredict heat transfer augmentation in tight-radius turns (bend angle > 135°). Passage 3 of the serpentine has a 180° hairpin. We ran a limited LES comparison on a 2D periodic duct analog at Re = 28,000 and found the k-ε model gives Nu values roughly 12% low relative to the LES at that turn. This discrepancy has been documented in the model assumptions register (MAR-TBCS-007) but has not yet been corrected with a curvature correction term. The program lead is aware.

### Grid Sensitivity

A three-level mesh refinement study was completed on the full blade passage geometry. Mesh counts were 2.1M, 6.8M, and 19.4M hexahedral-dominant cells (Mosaic meshing). The pressure-side peak temperature converged to within 1.8 K between the medium and fine grids, which represents less than 0.3% of the absolute temperature. GCI (Grid Convergence Index per Roache's method) on the exit bulk temperature was computed at 0.7%, well within our 2% acceptance threshold. The coarse mesh is retained only for sensitivity sweeps; all production runs use the medium grid.

Wall y+ values on the coolant-side walls ranged from 0.8 to 3.2 across the medium mesh, consistent with the enhanced wall treatment requirements. No significant y+ exceedances were observed.

### Code Behavior and Numerical Checks

We performed a basic sanity check on the solver implementation by running the NIST benchmark case for laminar pipe flow with conjugate wall heating (Nusselt correlation: Nu = 3.66 for fully developed flow). Fluent returned Nu = 3.71, a 1.4% deviation, which we attribute to entry-length effects in the short pipe used for the benchmark. This is acceptable. Additionally, global energy balance was verified: the net heat flux into the solid domain agrees with the convective enthalpy rise of the coolant to within 0.2% for all converged solutions.

Residual convergence criterion is set at 1×10⁻⁵ for all equations. All production runs achieved this criterion within 2,400 iterations. Spot-checks of mass imbalance per passage confirmed values below 0.01%.

### Comparison Against Test Data

Validation data comes from the NASA Glenn Research Center cascade rig dataset (GRC-HT-2019-04), which covers a geometrically similar (but not identical) blade cooling passage at matched Reynolds and Buoyancy numbers. We mapped the GRC geometry onto our passage coordinates using a non-dimensional arc-length parameterization and compared predicted Nu distributions along the leading and trailing edges of passage 2.

Agreement is reasonable on the trailing edge (mean absolute error 8.3%) but degraded on the leading edge (MAE 17.6%), which we believe is partly attributable to geometric differences in the inlet plenum that we could not fully replicate. This comparison is treated as a qualitative anchor, not a formal validation closure. A dedicated rig test using flight-representative geometry is planned for Q3 2024 but results will not be available before CDR.

The 17.6% leading-edge discrepancy is the most significant open item in the validation posture. It has been entered into the risk register (RISK-TBCS-022, severity 3, likelihood 2).

### Uncertainty in Boundary Conditions

Inlet total temperature and pressure profiles were derived from the upstream combustor CFD (a separate model, COMB-7 v2.1). The combustor model carries a stated ±3.5% uncertainty on total temperature at the turbine inlet plane, per that team's own assessment. We propagated this through the TBCS-3 model using a one-at-a-time parameter sweep (±1σ variation on T_inlet, P_inlet, and coolant mass flow rate). The resulting spread on peak blade wall temperature is ±14 K (k=1), which is within the ±25 K design margin.

I should note that we have not yet performed a full Monte Carlo or polynomial chaos expansion on the combined input space. The one-at-a-time approach likely underestimates the tail risk if inputs are correlated. This is deferred to the post-CDR phase.

---

## What Is NOT Covered in This Memo

The following areas are either out of scope for this review cycle or pending information we don't yet have:

- **Software quality and configuration control:** The Fluent license and version tracking is managed by the IT/CAE infrastructure team. I don't have documentation on their formal QA process for solver builds, and this was not part of our tasking for this memo. The program office should confirm this is covered elsewhere in the CDR package.

- **Operator and analyst training records:** We have not assembled documentation on the qualifications of the analysts who ran these simulations. This was flagged as a gap in the January readiness review and is being addressed by the workforce development office separately.

- **Independent review of the UDF source code:** The temperature-dependent conductivity UDF (tbcs_ksolid_v3.c) has been reviewed informally by two members of the team but has not gone through a formal independent code review or been subjected to unit testing against analytic solutions. This is a known gap.

- **Applicability to off-design conditions:** All validation comparisons and uncertainty analyses above apply to the takeoff operating point only. Cruise and descent conditions have not been assessed. Deferred to Phase 2.

---

## Summary Assessment

The mesh refinement and energy balance checks give reasonable confidence in the numerical solution quality at the takeoff point. The primary concern is the 17.6% discrepancy at the leading-edge passage, which remains unexplained and unresolved before CDR. The turbulence model limitation at the hairpin turn is documented but not corrected. Boundary condition uncertainty propagation is preliminary (one-at-a-time only).

My recommendation is that the TBCS-3 model is suitable for design guidance at the current fidelity level, but should not be used for final margin certification until the Q3 rig test data is incorporated and the leading-edge discrepancy is resolved. The model's outputs should carry an explicit caveat in the CDR package that the validation basis is partial.

Please let me know if you want me to expand any section or prepare a slide deck version for the review board.

— Marcus
