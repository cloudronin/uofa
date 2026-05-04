# INTERNAL TECHNICAL MEMO

**To:** Dr. Priya Nambiar, Project Lead — Centrifugal Pump CFD Program
**From:** Marcus Weld, Senior Analyst, Computational Methods Group
**Date:** 14 March 2025
**Re:** V&V Status Summary — Stage 2 Impeller Flow Simulations (OpenFOAM 10, RANS k-ω SST)

---

Priya,

Following last week's design review I wanted to get you a consolidated picture of where we stand on simulation credibility for the Stage 2 impeller work before the customer milestone on 28 March. This covers the full suite of checks the team has run since January. Bottom line up front: the simulation program is in good shape, but there are two areas I'd flag for senior attention before we release predicted head-curve data to the customer.

---

## 1. Problem Framing and Intended Use

The simulations are intended to predict hydraulic head, shaft power, and internal recirculation onset across 60–120% of best-efficiency-point (BEP) flow for a 250 mm impeller running water at 20 °C, 1450 RPM. The customer will use our output to make go/no-go decisions on volute geometry modifications — this is a design-support role, not a safety-certification role, so the tolerance on head prediction is ±2.5% and on power ±4%. I want to be explicit about this because it sets the bar for everything that follows: we are not claiming these simulations replace prototype testing; they are guiding early design choices.

The physical scenario is well within the class of problems OpenFOAM's pressure-velocity coupling (SIMPLE algorithm, steady MRF) has been exercised on extensively in the open literature, which gives us reasonable prior confidence in the mathematical model selection. The k-ω SST turbulence closure was chosen based on documented performance for attached and mildly separated impeller passage flows; we did not run LES or RSM given the design-support timeline, and that is a documented limitation.

---

## 2. Code Pedigree and Prior Testing

OpenFOAM 10 (ESI fork) is the solver. Before any project-specific work, our group maintains a standing regression suite of 14 benchmark cases that is re-run against every new solver version we adopt. For this release, all 14 cases passed within established tolerances. Relevant to impeller flows specifically, we re-ran the NASA rotor 37 compressor case and the Gülich pump benchmark; predicted total pressure ratio and head coefficient matched published reference data to within 1.8% and 2.1% respectively. This gives us confidence that the solver's core numerics — discretisation schemes, linear solvers, MRF implementation — are behaving as expected. No modifications were made to the solver source; we are running stock binaries, which avoids the need for additional unit-level testing of modified code paths.

I'd note that the regression suite is version-controlled in our GitLab repository (project ID: CMG-OF10-REGR), and the run logs for the current release are archived there. Any auditor can reproduce these results.

---

## 3. Mesh Refinement Study

Three structured-dominant hexahedral meshes were generated in ANSYS Meshing 2024 R1: coarse (~2.1 M cells), medium (~6.4 M cells), and fine (~17.8 M cells). The refinement ratio between successive levels is approximately 1.41 in each spatial direction, giving a consistent refinement factor of ~2.8 in total cell count. Wall y+ on the impeller blade surfaces was maintained below 5 on all three meshes to ensure the SST model's near-wall treatment was engaged correctly.

Grid Convergence Index (GCI) was computed following the Celik et al. (2008) procedure for head coefficient at BEP. The GCI between medium and fine meshes is 0.7%, well below our 2% threshold. The apparent order of convergence was 1.94, consistent with the second-order schemes used. We are using the medium mesh (6.4 M cells) for the production runs on the basis of this study — the fine mesh provides negligible additional accuracy at roughly 2.8× the compute cost.

Residual convergence was also checked: all continuity and momentum residuals dropped at least four decades and were flat for the final 500 iterations of each steady-state run. Integral quantities (head, torque) were monitored and showed variation below 0.05% over the last 200 iterations.

---

## 4. Boundary Conditions and Input Data Fidelity

Inlet boundary conditions were derived from site measurement data supplied by the customer (flow rate from electromagnetic flowmeter, static pressure from a calibrated Kistler transducer, temperature from PT100). The measurement uncertainty on flow rate is ±0.8% (k=2), and we have propagated this through to a ±0.9% uncertainty band on predicted head at BEP — this is the dominant input uncertainty and is clearly within the ±2.5% requirement.

Outlet conditions use a zero-gradient pressure specification at a plane located 4D downstream of the volute exit, confirmed to be sufficiently far from the region of interest by a sensitivity test (moving the outlet plane to 6D changed predicted head by less than 0.1%). Rotational periodicity was applied across the 6-blade impeller passages; full-annulus simulations were not performed but are not considered necessary for the steady design-support purpose.

One area I want to flag: the surface roughness of the impeller passages was assumed to be hydraulically smooth (ks = 0) in all production runs. The customer's manufacturing spec allows Ra up to 6.3 μm on wetted surfaces. We ran a single sensitivity case at ks = 50 μm (a conservative equivalent sand roughness) and found a 1.1% reduction in predicted efficiency. This is not negligible relative to our 4% power tolerance and I recommend we either obtain actual roughness measurements from the customer or bracket the predictions with a roughness sensitivity band in the deliverable report.

---

## 5. Comparison Against Physical Test Data

We have pump curve data from a factory acceptance test (FAT) conducted by the OEM on a geometrically identical unit in December 2024. The test rig was calibrated to ISO 9906 Grade 1 standards. Across seven operating points from 65% to 115% BEP, the CFD-predicted head deviates from test data by –0.3% to +2.1% (mean absolute error 1.1%), and predicted shaft power deviates by –1.8% to +2.6% (mean absolute error 1.7%). Both are within the stated requirements.

The largest discrepancy (2.1% on head at 65% BEP) occurs in the part-load recirculation regime. This is expected: RANS/SST is known to underperform in strongly separated internal flows. We have flagged in the uncertainty budget that predictions below 70% BEP carry higher uncertainty and should be treated with additional caution in design decisions.

Residual plots, comparison tables, and velocity contour overlays against PIV data from a 2022 internal study on a similar impeller are included in the project SharePoint folder (CMG/Stage2/Validation_Evidence/). The PIV comparison is qualitative — the geometry is not identical — but the flow structure in the blade passages (jet-wake pattern, secondary flows at the shroud) is reproduced well.

---

## 6. Uncertainty Quantification Summary

A formal uncertainty budget was assembled following ASME V&V 20-2009. Contributions include: numerical (discretisation) uncertainty from the GCI study (±0.7% on head), input data uncertainty from flowmeter calibration (±0.9%), and model-form uncertainty estimated from the FAT comparison scatter (±1.2% at BEP, larger at off-design). Combined expanded uncertainty (k=2) on predicted head at BEP is ±2.0%, within the ±2.5% requirement. At 65% BEP the combined uncertainty widens to ±3.4%, which technically exceeds the requirement — this should be communicated to the customer.

---

## 7. Reviewer Independence and Human Factors

The simulation setup, mesh generation, and post-processing were performed by two engineers (T. Okafor and S. Lindqvist). An independent check of the boundary condition setup, mesh quality metrics, and post-processing scripts was conducted by myself on 7 March 2025. I found one minor issue: the reference pressure datum in two early runs had been set to gauge rather than absolute, which affected the absolute pressure field output but had no effect on differential quantities (head, torque). This was corrected and the affected output files were re-generated. No other discrepancies were found.

The post-processing Python scripts (version-controlled in GitLab, CMG-OF10-STAGE2/scripts/) include input validation checks that flag physically implausible values (e.g., negative head, mass imbalance > 0.1%). These were triggered correctly in testing and provide a layer of protection against operator error in future runs.

I want to be transparent that all simulation work was performed within our group — there has been no external independent review of the CFD methodology. For a design-support application this is acceptable, but if the customer later wishes to use these results in a regulatory submission, an external audit would be warranted.

---

## 8. Applicability and Extrapolation Limits

The validation evidence base (FAT data, Gülich benchmark, internal PIV) is directly relevant to the Stage 2 impeller geometry and operating regime. I am comfortable with the claim that the simulation methodology is validated for head and power prediction in the 70–115% BEP range for this specific impeller class.

I am less comfortable extrapolating to: (a) significantly different specific-speed designs without re-validation, (b) fluids other than clean water at near-ambient conditions, or (c) transient phenomena such as surge or water hammer. These are not in scope for the current program, but I want the record to be clear.

---

## 9. Outstanding Items Before 28 March Deliverable

1. **Roughness sensitivity** — obtain customer roughness data or agree on bracketed reporting approach (owner: T. Okafor, due 21 March).
2. **Part-load uncertainty communication** — draft customer-facing language clarifying the wider uncertainty band below 70% BEP (owner: M. Weld, due 24 March).
3. **Regression suite archive link** — ensure the GitLab regression logs are accessible to the customer's nominated reviewer per the contract data-sharing agreement (owner: S. Lindqvist, due 18 March).

Overall I believe the simulation program meets the credibility bar for its intended design-support purpose in the 70–115% BEP operating window. The two flagged items are manageable and do not, in my view, invalidate the current results — they need to be communicated clearly in the deliverable.

Happy to discuss at Thursday's team call.

Marcus

---
*Attachments referenced: CMG/Stage2/Validation_Evidence/ (SharePoint); CMG-OF10-REGR (GitLab); CMG-OF10-STAGE2/scripts/ (GitLab)*
