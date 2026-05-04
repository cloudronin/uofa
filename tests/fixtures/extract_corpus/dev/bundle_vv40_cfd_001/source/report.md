# Credibility Assessment Report
## CFD Simulation of Centrifugal Pump Internal Flow
### Project: Cooling Water Pump Stage Analysis — Model Credibility Review
**Document Ref:** CAR-CFD-2024-047-Rev2
**Prepared by:** Simulation Methods Group, Applied Fluid Engineering Division
**Date:** 2024-11-14
**Review Status:** Final

---

## 1. Background and Scope

This report documents the credibility assessment performed on the Reynolds-Averaged Navier–Stokes (RANS) simulation suite developed to characterize internal flow behavior in a single-stage centrifugal pump used in a secondary cooling loop application. The pump operates at a nominal flow rate of 320 m³/h, with a design head of 48 m and a rotational speed of 1480 RPM. The impeller has seven backward-swept blades, and the volute casing is a single-tongue design.

The simulation campaign was executed using ANSYS Fluent 2023 R2. The primary objectives of the simulation are to predict hydraulic efficiency, head-flow curve characteristics, and internal pressure distributions across the operating range (60%–120% of best efficiency point, BEP). Results are intended to inform a design iteration decision and will be used alongside physical test data from a hydraulic test rig.

The credibility assessment framework applied here evaluates the degree of confidence that can be placed in these simulation outputs for the stated engineering decision. This document covers the evidence gathered across all relevant assessment dimensions, organized by topic area rather than any standardized checklist sequence.

---

## 2. Intended Use and Decision Context

The simulation results will be used to rank three impeller geometry variants by predicted hydraulic efficiency and to identify regions of recirculation onset at off-design conditions. The decision supported is a downselect from three candidate geometries to one for prototype fabrication. No regulatory submission is associated with this use; however, the decision carries significant cost implications (prototype tooling cost approximately $280,000).

The engineering team has explicitly bounded the claims: the CFD results are not intended to replace physical testing but to reduce the number of full-scale rig tests required. The team documented this scope in a Simulation Plan (SP-2024-031) prior to analysis execution, which is referenced throughout this report.

The question being answered by the simulation is sufficiently well-posed for the available modeling approach. Predicted quantities of interest (QoIs) are: (1) total-to-total head rise at five operating points, (2) hydraulic efficiency at BEP, and (3) static pressure distribution on the impeller blade suction surface at 80% BEP. These are tractable QoIs for steady-state RANS with the selected turbulence closure.

---

## 3. Governing Equations and Solver Fidelity

The solver implements the incompressible RANS equations with the SST k-ω turbulence model. The choice of SST k-ω is well-justified for this application: the model's blended behavior near walls and in free-shear regions is appropriate for the adverse pressure gradient environment on the blade suction surface, and it is widely validated for turbomachinery internal flows in the open literature. The team reviewed five peer-reviewed validation studies for centrifugal pump flows using the same turbulence closure, documenting agreement within 2–4% for head predictions across comparable specific-speed machines (Ns ~ 25–60 in SI units).

The Multiple Reference Frame (MRF) approach is used to model impeller rotation, which is standard for steady-state pump analysis. The team acknowledged in the Simulation Plan that MRF introduces a modeling approximation at the rotor-stator interface and noted that transient sliding mesh simulations are planned for the final selected geometry in a follow-on phase. This is a reasonable and transparent deferral.

Wall treatment uses scalable wall functions with a target y⁺ of 30–100 on blade surfaces. Actual y⁺ values achieved are reported in §5.3 of the Simulation Report (SR-2024-047). The mean y⁺ on the impeller blades is 52, and fewer than 3% of wall-adjacent cells fall outside the 15–200 range. This is consistent with the requirements of the selected wall treatment approach.

---

## 4. Geometry and Boundary Condition Fidelity

The computational geometry was derived from the CAD master file (release 4.2, dated 2024-09-03) using SpaceClaim. The impeller and volute geometries were imported without simplification. Wear ring clearances of 0.35 mm are explicitly modeled as thin annular gaps; the team confirmed this is important for leakage flow prediction at off-design points.

Inlet boundary conditions are specified as a uniform total pressure of 1.5 bar (absolute) with 5% turbulence intensity and a turbulent length scale of 10 mm, based on upstream pipe diameter. A sensitivity study was performed varying inlet turbulence intensity from 2% to 10%; head predictions changed by less than 0.4%, confirming low sensitivity to this parameter.

Outlet boundary conditions use a mass flow rate specification at the volute exit. Five operating points were simulated: 192, 256, 320, 352, and 384 m³/h. At the lowest flow rate (60% BEP), the simulation team noted that convergence was slower and residuals did not reach the standard 10⁻⁵ threshold for continuity — a point addressed further in §5.

The working fluid is treated as water at 25°C with constant properties (ρ = 997 kg/m³, μ = 8.9×10⁻⁴ Pa·s). No thermal effects are modeled, which is appropriate for this isothermal application.

---

## 5. Numerical Solution Quality

### 5.1 Mesh Refinement Study

A formal mesh convergence study was conducted using three systematically refined hexahedral-dominant meshes generated in ANSYS TurboGrid. Mesh sizes were approximately 2.1 million, 6.8 million, and 18.4 million cells, with a nominal refinement ratio of approximately 1.65 per level (close to the recommended factor of √2 per dimension). The Grid Convergence Index (GCI) methodology following Roache (1994) and Celik et al. (2008) was applied.

For the primary QoI (total head at BEP), the GCI values were:
- Fine-to-medium: GCI₂₁ = 0.8%
- Medium-to-coarse: GCI₃₂ = 2.7%

The observed order of convergence was p = 1.93, consistent with the second-order spatial discretization used (second-order upwind for momentum and turbulence quantities). The asymptotic convergence ratio (GCI₂₁ / r^p · GCI₃₂) was 1.04, confirming the solution is within the asymptotic range. All subsequent production runs used the medium mesh (6.8M cells) as a balance between accuracy and computational cost, with the GCI-based numerical uncertainty reported as ±0.9% on head predictions.

For the blade surface pressure distribution QoI, the fine and medium meshes showed good agreement (maximum point-wise difference < 1.5%), while the coarse mesh showed localized deviations of up to 6% near the leading edge. The medium mesh is considered adequate for the stated purpose.

### 5.2 Iterative Convergence

Residuals for all transport equations were monitored to 10⁻⁵ or better at all operating points except the 60% BEP condition, where the continuity residual stabilized at approximately 4×10⁻⁴. At this condition, the team also monitored the head rise and shaft torque as solution monitors; both showed variation of less than 0.2% over the final 500 iterations, which the team used as a supplementary convergence criterion. This approach is reasonable and documented, though the residual plateau at low flow is noted as a limitation.

### 5.3 Discretization Scheme Consistency

All transport equations use second-order upwind differencing. The SIMPLE pressure-velocity coupling algorithm is used with standard under-relaxation factors (momentum: 0.7, pressure: 0.3, turbulence: 0.8). No first-order schemes were used in production runs. The team confirmed that initial runs with first-order schemes for turbulence quantities showed head predictions 1.8% higher than second-order, indicating the discretization order choice is non-trivial for this application.

---

## 6. Code Verification and Software Qualification

The ANSYS Fluent 2023 R2 installation used for this project is maintained under the organization's software configuration management system (SCMS-2024). The software version is registered, and the installation was validated against a suite of canonical benchmark cases maintained by the simulation group. These benchmarks include lid-driven cavity flow (Re = 1000, 3200), backward-facing step (Re = 800), and a turbulent pipe flow case (Re = 50,000 with SST k-ω). Results from the current installation match published reference values to within expected tolerances.

The team also ran the ANSYS Fluent internal verification test suite (V&V Suite v23.2) on the compute cluster nodes used for production runs; all 47 test cases passed. This provides confidence that the compiled binaries and numerical libraries are functioning correctly on the specific hardware environment.

User-defined functions (UDFs) were not used in this simulation campaign; all physics are handled by native Fluent models, reducing the risk of implementation errors.

---

## 7. Comparison with Physical Test Data

### 7.1 Validation Dataset

Physical test data were obtained from a hydraulic performance test conducted on a geometrically similar pump (impeller diameter 310 mm vs. 315 mm in the simulation geometry) at the organization's pump test facility. Testing followed ISO 9906:2012 Grade 1B procedures. Measured quantities include head, flow rate, shaft power, and efficiency at 11 operating points from shutoff to 120% BEP.

The geometric difference between the tested and simulated impeller (1.6% diameter difference) introduces a scaling consideration. The team applied affinity law corrections to map test data to the simulated geometry, which is a standard and defensible approach. The corrected test data are used as the validation reference.

### 7.2 Comparison Results

Head predictions at BEP show agreement within 1.2% (simulated: 49.4 m, corrected test: 48.8 m). Across the full operating range, head predictions are within 3% at all points except 60% BEP, where the simulation over-predicts head by 5.8%. The team attributes this to the known limitation of steady-state RANS in capturing the recirculation onset at low flow, which is consistent with the literature. Hydraulic efficiency at BEP is predicted at 83.1% versus a measured value of 82.4% (difference: 0.7 percentage points).

The team computed a validation metric using the approach of Oberkampf and Barone (2006), accounting for both experimental uncertainty (estimated at ±1.5% on head from ISO 9906 Grade 1B) and numerical uncertainty (GCI-based, ±0.9%). At BEP, the validation comparison metric indicates the model is within the combined uncertainty band, supporting the claim that the simulation adequately represents the physical system at the primary operating condition.

### 7.3 Experimental Uncertainty Characterization

The test facility calibration records were reviewed. Flow measurement uses an electromagnetic flowmeter (Endress+Hauser Promag 10W, DN200) with a stated accuracy of ±0.5% of reading, last calibrated 2024-06-15. Pressure measurements use Kistler 4260A transducers, calibrated 2024-08-01. The team computed combined experimental uncertainty in head measurement as ±1.5% (95% confidence), consistent with ISO 9906 Grade 1B requirements. This characterization is adequate and traceable.

---

## 8. Sensitivity Analysis and Input Parameter Uncertainty

A one-at-a-time (OAT) sensitivity study was performed on the following input parameters: inlet turbulence intensity, fluid viscosity (±5% to represent temperature uncertainty), wear ring clearance (±0.05 mm manufacturing tolerance), and surface roughness (Ra 3.2 µm ± 50%). Results are summarized in Table 3 of the Simulation Report.

The most influential parameter was surface roughness, which affected BEP efficiency predictions by up to ±0.9 percentage points across the range tested. Wear ring clearance had a secondary effect on off-design head predictions (±1.1% at 60% BEP). Fluid property variations and inlet turbulence intensity had negligible effects (<0.5% on all QoIs).

The team did not perform a formal probabilistic uncertainty propagation (e.g., Monte Carlo or polynomial chaos expansion), noting this was outside the project scope. The OAT study is considered sufficient given the linear-to-weakly-nonlinear response observed for all parameters tested.

---

## 9. Operator and Analyst Qualification

The simulation was set up and executed by a senior CFD analyst (8 years of turbomachinery CFD experience) and reviewed by a principal engineer (15 years experience, including 6 years in pump hydraulics). The simulation plan, mesh generation approach, and post-processing procedures were all documented before execution and reviewed by the principal engineer prior to run submission. A peer review of the setup was conducted using the organization's internal CFD checklist (Form SIMQ-07, Rev 3).

Post-processing scripts (Python, using Fluent's PyFluent API) were validated against manual extraction of the same quantities for two representative cases, confirming no scripting errors. The team followed documented data management procedures; all case files, mesh files, and result databases are archived on the project server with version control.

---

## 10. Applicability and Extrapolation Considerations

The validation data were obtained at conditions closely matching the simulation scenario (same fluid, similar geometry, overlapping operating range). The primary geometric difference (1.6% diameter scaling) is well within the range where affinity law corrections are considered reliable. The operating conditions (Reynolds number ~2×10⁶ based on impeller tip speed and diameter) are within the range covered by the validation dataset.

The simulation results are being used to rank three impeller variants; two of the variants have geometric changes (blade outlet angle modification of ±3°) that are modest relative to the validated baseline. The team assessed that these changes do not move the simulation outside the applicability domain of the validated model, though they noted that the validation confidence is strongest for the baseline geometry.

Extrapolation to significantly different operating conditions (e.g., two-phase flow, elevated temperature, or substantially different specific speed) is explicitly out of scope and flagged in the Simulation Plan as requiring separate validation.

---

## 11. Summary Assessment

Based on the evidence reviewed, the simulation suite demonstrates strong credibility for the stated intended use. Key findings:

- The problem is well-posed, with clearly defined QoIs and decision context documented prior to analysis.
- Mesh convergence is formally demonstrated with GCI < 1% for the primary QoI on the production mesh.
- Iterative convergence is satisfactory at four of five operating points; the low-flow condition is a documented limitation with adequate supplementary monitoring.
- The turbulence model selection is well-supported by literature and appropriate for the flow physics.
- Validation against physical test data shows agreement within combined uncertainty bands at BEP; larger deviations at off-design (60% BEP) are physically explained and acknowledged.
- Experimental uncertainty is characterized and traceable.
- Software qualification is current and documented.
- Analyst qualifications and review processes are appropriate.
- Sensitivity to key input parameters has been assessed; surface roughness is identified as the most influential uncertain parameter.

The simulation results are considered credible for supporting the impeller geometry downselect decision at and near BEP operating conditions. Use of these results at 60% BEP or below should be accompanied by explicit acknowledgment of the increased prediction uncertainty at those conditions.

---

## 12. Limitations and Recommended Actions

1. **Low-flow convergence:** The residual behavior at 60% BEP warrants attention. If off-design performance is a critical discriminator between variants, transient sliding-mesh simulations at this condition should be considered before final downselect.
2. **Surface roughness:** Given its sensitivity influence, the as-manufactured surface roughness of prototype impellers should be measured and used to update the simulation inputs for final validation.
3. **Scaling correction:** The 1.6% geometric difference between the validation test article and the simulation geometry introduces a minor but non-zero source of comparison uncertainty. Testing of the actual simulated geometry at a later phase would further strengthen the validation basis.
4. **Probabilistic uncertainty propagation:** For future phases involving regulatory or contractual deliverables, a more rigorous uncertainty propagation method is recommended.

---

*End of Report*

*Attachments: Simulation Plan SP-2024-031, Simulation Report SR-2024-047, Mesh Convergence Study Data Package, Test Facility Calibration Records, Peer Review Checklist SIMQ-07*
