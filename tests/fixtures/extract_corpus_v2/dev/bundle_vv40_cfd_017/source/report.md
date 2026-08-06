Title: CFD Credibility Assessment – Cathode Air Manifold for 120 kW Fuel Cell Stack

Date: 2026-08-06
Author: Thermal-Fluid Analysis Group, Power Systems Division

1. Background and Decision Context

The fuel cell program is down-selecting between two manifold layouts for the cathode air supply to a 120 kW stack. The manifold distributes dry, filtered air from a variable-speed blower to eight parallel channels feeding bipolar plates. The present study uses computational fluid dynamics to quantify two quantities:

- Total pressure loss from blower flange to stack header at 200, 300, and 400 standard L/min.
- Distribution uniformity among the eight outlets at the nominal operating point of 300 standard L/min.

The near-term decision is whether Layout B (a compact S-shaped plenum with integrated turning vanes) is acceptable for preliminary packaging with a +/−10% allowance on predicted pressure loss, and whether it yields a flow imbalance less than 8% (ratio of outlet flow standard deviation to mean). The model does not attempt to forecast noise, condensation onset, or transient surge; those items are deferred to later phases.

2. Geometry and Physics Considered

The geometry reflects the current CAD for Layout B as of 2026-07-18 (file: MCAT_ManifoldB_revF.step). The domain extends from the blower outlet flange to the eight outlet stubs on the stack header. Flexible hose, upstream filters, and downstream micro-channels inside the stack are not included; instead, their aggregate resistance is represented at the outlets by fixed static pressures derived from the stack team’s pressure-flow curve at 25 C.

Physical modeling assumptions:

- Air is treated as a single-phase, Newtonian fluid with constant properties at 25 C. Density is set by the standard conditions used by the test team; compressibility is neglected (bulk Mach number < 0.05 throughout).
- Turbulence is represented with a two-equation eddy-viscosity approach. The baseline model is the k-omega SST variant with production limiter active. Wall treatment is fully resolved to the viscous sublayer (target y+ below 1).
- Surfaces are hydraulically smooth except where stated in Section 5; wall adhesion and surface contamination are not modeled.
- Thermal effects (heating of air due to blower work and heat soak from adjacent components) are not represented; temperature is uniform.

3. Solver Setup and Numerics

The simulations were performed in STAR-CCM+ 2022.1 on the Huron cluster (32 cores per run). All cases are steady-state with implicit coupling. Spatial discretization is second-order for momentum and turbulence transport. Pressure-velocity coupling uses the coupled solver with a courant-like stabilization parameter of 8.0 on the final mesh and 4.0 during ramp-up. Gradients are computed with a least-squares method.

Convergence monitoring:

- Scaled residuals were reduced below 1e-5 for continuity and momentum and 1e-6 for turbulence quantities.
- Monitors for total pressure at the outlet header and bulk flow per outlet were observed to flatten, with the last 100 iterations showing less than 0.1% change.
- To reduce startup bias, inflow was ramped from 0 to the target in 200 pseudo-iterations.

4. Grid and Solution Checks

To examine solution sensitivity to mesh resolution and near-wall capture, three meshes were generated from the same CAD with identical meshing recipes except base size:

- Coarse: 2.3 million cells; 9 prism layers with geometric growth 1.2; first cell height targeting y+ ~ 1.2 on the straight sections.
- Medium: 4.7 million cells; 13 prism layers; first cell height targeting y+ ~ 0.8.
- Fine: 9.1 million cells; 17 prism layers; first cell height targeting y+ ~ 0.4.

A poly-hexcore bulk with local refinements at the turning vanes and near the outlet junctions was used. Mesh quality checks showed minimum orthogonality > 0.18, with 99.6% of cells above 0.3. No negative volumes were reported.

For the nominal case (300 standard L/min), the predicted manifold pressure loss was:

- Coarse: 1.92 kPa
- Medium: 1.98 kPa
- Fine: 2.01 kPa

Relative changes:

- Coarse → Medium: +3.1%
- Medium → Fine: +1.5%

The outlet maldistribution index (standard deviation divided by mean of the eight outlet mass flows) showed:

- Coarse: 6.5%
- Medium: 6.2%
- Fine: 6.0%

Relative changes:

- Coarse → Medium: −4.6%
- Medium → Fine: −3.2%

We interpret the diminishing differences as evidence that the computed results are approaching a mesh-insensitive regime for the two quantities of interest. The remaining grid effect for pressure loss is estimated to be on the order of 1–2%. Maldistribution is less sensitive.

Stopping criteria were tightened on the coarse mesh to rule out false convergence; repeating the coarse run with 50% smaller relaxation factors altered the results by <0.3%.

5. Boundary and Material Inputs

Inlet boundary:

- Blower outlet is modeled as a mass-flow inlet set to achieve the program’s three operating points: 200, 300, and 400 standard L/min at 25 C. The area-averaged inlet flow was matched to within 0.05% via STAR-CCM+ target control.
- Turbulence at inlet: turbulence intensity assumed 5% with a length scale equal to 7% of the hydraulic diameter, consistent with short upstream ducting and a compact blower volute.

Outlet boundary:

- Each of the eight outlets was assigned a fixed static pressure representing the downstream stack header and plates at the corresponding flow condition (values from the Stack Team correlate to 0.57, 0.88, and 1.22 kPa at 200, 300, and 400 standard L/min respectively). The eight outlets use identical target values, representing current balance manifold design assumptions outside the scope of this model.

Wall roughness:

- As-built polymer manifold surfaces are expected to be smooth; we used an equivalent sand-grain roughness of 15 microns based on vendor finishing specs.

Material properties:

- Air properties at 25 C: density 1.184 kg/m^3, viscosity 1.85e−5 Pa·s. Reference density was applied consistently between CFD and test correlation via the standard conditions used in the flow bench.

6. Comparison with Bench Measurements

We compared CFD predictions to data from a room-temperature flow bench set up to evaluate Layout B. The bench consists of a blower, test article, and a downstream adjustable orifice pack to emulate the stack resistance. The downstream headers and micro-channels are not present; their effect is collapsed into the orifice adjustment. The bench team supplied total pressure drop across the article and the per-outlet volumetric flows at 200, 300, and 400 standard L/min.

Aggregate pressure loss:

- 200 L/min: CFD (Fine) 1.21 kPa vs. bench 1.28 kPa (−5.5% difference)
- 300 L/min: CFD (Fine) 2.01 kPa vs. bench 2.13 kPa (−5.6% difference)
- 400 L/min: CFD (Fine) 3.09 kPa vs. bench 3.46 kPa (−10.7% difference)

Outlet balance at 300 L/min:

- Bench maldistribution index: 6.8%
- CFD (Fine) maldistribution index: 6.0% (absolute difference 0.8 percentage points)

Outlet flow split patterns (relative ranking of high/low outlets) align between CFD and bench for 6 of 8 outlets; the two most downstream stubs show a 1–2% absolute discrepancy in fractional share.

Observations:

- The underprediction of pressure loss increases with flow rate. The shape of the delta-P vs. Q curve matches the expected quadratic trend, but the CFD curve lies systematically below the bench curve. This behavior is consistent with low-amplitude surface roughness or minor leak paths not captured in the model, or with a slightly different effective downstream resistance realized by the bench orifice pack compared to the assumed outlet static pressure targets.
- The outlet maldistribution estimate tracks bench measurements well enough to support geometry ranking. CFD indicates that the turning vanes in Layout B suppress the secondary flows that were present in the earlier S-curve prototype.

7. Sensitivity Probing

We evaluated the impact of key modeling choices and uncertain inputs on the outputs of interest at 300 standard L/min:

- Turbulence model family: Spalart–Allmaras and realizable k–epsilon were run on the medium mesh. Pressure loss varied by +1.6% (SA) and −2.1% (k–epsilon) relative to k–omega SST; maldistribution varied by less than 0.3 percentage points. The SST model was retained because it consistently produced the lowest scatter in outlet split during iterations and the most stable wall shear patterns near the turning vanes.
- Inlet turbulence intensity: varying from 1% to 10% shifted pressure loss by less than 0.7% and maldistribution by less than 0.2 percentage points.
- Surface finish: increasing equivalent roughness from 0 to 50 microns increased pressure loss by roughly 3.2%, with minimal impact on maldistribution. This scale of effect alone is insufficient to close the pressure gap at 400 L/min, suggesting additional contributors (e.g., small bleeds or coupling with upstream blower swirl) in the bench setup.
- Outflow resistance representation: perturbing the target outlet static pressure by ±50 Pa altered maldistribution by ~0.9 percentage points and total pressure loss by <1%. This indicates the predicted flow split is more sensitive to downstream balance than total loss is.

We also ran a transient startup for 0.2 seconds (pseudo-transient, fixed blower speed ramp) to look for memory effects. The time-dependent results settled to the same steady solution obtained by the steady run, and no persistent oscillations were evident.

8. Results Summary

- At 300 standard L/min, the fine-mesh simulation predicts 2.01 kPa pressure loss. The medium mesh gives 1.98 kPa, representing a 1.5% difference that is within the observed mesh sensitivity. Against bench measurements, the CFD underpredicts by 5–6% at 200–300 L/min and by ~11% at 400 L/min.
- Predicted outlet balance at the nominal point is 6.0% maldistribution, meeting the program’s target of <8%. The measured value on the bench is 6.8%.
- The contribution of turns and junctions dominates loss; straightening vanes reduce secondary motion that was previously creating localized over- and under-feeding. The most downstream outlets remain slightly flow-starved (by 1–2% of total), consistent between CFD and bench, and likely attributable to curvature-induced pressure gradients despite the vanes.

9. Confidence and Known Gaps

Items that support confidence:

- The mesh refinement exercise indicates limited sensitivity of the target outputs to further grid densification, with changes of about 1–2% for the key metric (pressure loss). Outlet split is even less sensitive to grid.
- Two alternative turbulence closures provide similar outputs, bounding the model-form influence to within a couple percent for our quantities of interest.
- Trends with flow rate obey expected scaling and match the bench curve shape, even if the absolute level is low by a few percent.

Known gaps:

- The CFD consistently underpredicts total pressure loss compared to the bench, and the gap grows with flow rate. The cause was not isolated in this phase.
- The representation of downstream resistance is lumped into outlet static targets and may not mirror how the bench or the actual stack distribute loss among micro-features.
- Thermal effects (e.g., blower warming air, heat transfer to the manifold) are omitted. While these would marginally alter air properties, the current results assume isothermal conditions.
- The analysis did not include upstream blower swirl or nonuniformity at the flange; the inlet is prescribed as uniform in velocity and turbulence statistics, which may be optimistic.
- The flow bench does not include the actual stack header and micro-channels; it is a surrogate with an adjustable orifice pack. This may mask interactions that could become relevant in full system configuration.

10. Limitations and Use Boundaries

- The conclusions are limited to room-temperature, dry air at the flow rates stated. Condensation or humidified operation and hot soak were not addressed.
- The present geometry omits flexible hose and clamps; if downstream packaging changes introduce new tight bends upstream or downstream, these results may not carry over.
- Acoustic pulsations, blower surge margin, and transient behavior are out of scope.
- The eight-outlet assumption of equal backpressure stands; scenarios where plate-to-plate variations exceed a few percent could shift the predicted maldistribution.

11. Methodological Notes

- Default wall functions were not used; near-wall viscous sublayers were resolved. This choice required additional layers and a finer first cell height but reduced ambiguity in wall shear modeling for the compact turns in Layout B.
- Solver robustness was monitored via both residuals and integral monitors (total pressure and outlet flows). Runs exhibiting slow drift in outlet splits were extended until the last 100 iterations were flat within 0.1%.
- The choice of the k–omega SST model was based on its acceptable performance across multiple internal manifold studies and its relative insensitivity to mesh stretching in near-wall regions for this class of flows.

12. Recommendations for Follow-On

- Acquire additional bench data at 500 standard L/min to test the observed growing gap at higher flow; if the underprediction trend persists, include a targeted test with an upstream swirl generator to mimic blower discharge.
- Perform a short study with measured surface roughness on a 3D-printed sample and in-CFD roughness sweeps to estimate whether manufacturing variations can account for the pressure offset.
- Replace outlet static targets with pressure-dependent outlet curves drawn from a reduced model of the stack micro-channels to better mirror the downstream physics while retaining computational tractability.
- If late-stage acceptance requires tighter agreement, consider a hybrid approach: retain steady RANS for screening, and run a scale-resolving case on a trimmed sub-domain that includes the key turn to check for unsteady separation.

13. Decision

By concurrence of the Power Systems CFD Lead (A. Ramirez) and the Fuel Cell Manifold Subsystem Owner (J. Patel), the Layout B CFD model and results described herein are accepted for preliminary manifold design selection and blower sizing with a 10% design margin on predicted total pressure loss and an 8% cap on outlet maldistribution at 300 standard L/min. The model is not accepted for final stack certification, compliance documentation, or safety analyses. Any use beyond the stated flow range or operating conditions requires additional analysis and data correlation.

14. Distribution

- Fuel Cell Program Manager
- Manifold Subsystem Team
- Power Systems CFD Lead
- Test Lab Supervisor

15. References

- CFD case files: //huron/projects/fuelcell/manifoldB/CFD/2026Q3/STAR-CCM-2022R1
- CAD source: MCAT_ManifoldB_revF.step (PLM vault ID 8F3A-77D2)
- Flow bench report: ManifoldB_FlowBench_Summary_2026-07-25.pdf
