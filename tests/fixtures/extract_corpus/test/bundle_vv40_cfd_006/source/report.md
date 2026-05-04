# Credibility Assessment Report
## CFD Simulation of Centrifugal Pump Stage — Internal Flow and Performance Prediction
### Project: HydroFlow-7 Pump Platform | Revision 2.1 | Date: 2024-03-14

---

## 1. Background and Scope

This report documents the credibility assessment of a Reynolds-Averaged Navier–Stokes (RANS) computational fluid dynamics model developed to predict the hydraulic performance of the HydroFlow-7 single-stage centrifugal pump. The simulation suite was built in ANSYS Fluent 2023 R1 and supports design decisions related to impeller geometry optimization, volute sizing, and off-design operating margin estimation. The pump is rated at 85 m³/h at 42 m head, driven at 1450 RPM, handling clean water at 25 °C.

The assessment framework applied here follows a structured V&V approach consistent with ASME standards for computational simulation credibility. The goal is to provide project stakeholders and the independent technical review board with a transparent, evidence-based evaluation of how much confidence should be placed in simulation outputs across the operating envelope.

The simulation outputs of primary interest are:
- Total-to-total pressure rise (pump head) across the operating range (0.6Q–1.2Q)
- Shaft power and hydraulic efficiency
- Internal velocity field and recirculation onset near the impeller inlet at low-flow conditions

---

## 2. Simulation Pedigree and Code Basis

### 2.1 Software Provenance and Numerical Correctness

ANSYS Fluent 2023 R1 is a commercially distributed, widely used CFD solver. The code has undergone extensive internal testing by the vendor and has been independently exercised against published benchmark cases including the NASA Rotor 37 axial compressor, the ERCOFTAC centrifugal pump test case (Ubaldi et al.), and the FDA benchmark nozzle problem. Within our organization, solver-level correctness was confirmed by running the Taylor–Green vortex decay problem at Re = 1600, verifying that kinetic energy dissipation rates matched the published DNS reference to within 1.8% using second-order spatial discretization. A manufactured solution (MMS) test on a 2D channel with body forces was executed to confirm that the pressure–velocity coupling (SIMPLE algorithm) converges at the expected second-order rate. Observed order of accuracy was 1.94, consistent with theoretical expectations. These exercises provide confidence that the underlying numerical machinery is performing correctly and is not introducing spurious errors into the pump simulation.

### 2.2 Applicability of the Numerical Approach

The pump operates in a regime where the flow is predominantly turbulent (impeller-exit Reynolds number ~4.2 × 10⁶), with strong streamline curvature in the volute and potential for flow separation at off-design conditions. The choice of RANS with the SST k-ω turbulence closure was made after reviewing the literature on centrifugal pump simulation. The SST model has demonstrated reasonable accuracy for adverse pressure gradient flows and mild separation, which are the dominant physical mechanisms here. However, the team acknowledges that at deep part-load (below 0.5Q), unsteady effects and rotating stall may render a steady-state RANS approach inadequate. The current simulation scope is explicitly bounded to 0.6Q–1.2Q, where steady RANS has documented precedent in the pump literature (Gonzalez et al., 2002; Feng et al., 2009). The physical fidelity of the modeling approach — turbulence closure, steady-state assumption, single-passage periodicity — is thus considered appropriate within the declared operating window.

---

## 3. Geometry and Boundary Condition Fidelity

### 3.1 Geometric Representation

The CAD model was imported from the HydroFlow-7 master assembly (SolidWorks 2023, revision 14c). The computational domain includes the full 360° volute, the five-blade impeller modeled as a full-wheel (not single-passage) to capture volute asymmetry effects, and 2D inlet/outlet pipe extensions of 5D and 8D respectively to reduce boundary condition influence. Blade fillet radii of 1.2 mm were retained in the model; previous sensitivity work on a similar pump (HydroFlow-5) showed that removing fillets shifted predicted head by ~0.9% — within acceptable tolerance but retained for accuracy. The wear ring clearance gap (0.35 mm nominal) is explicitly meshed and included, as leakage recirculation has a measurable effect on volumetric efficiency.

### 3.2 Boundary Conditions and Their Uncertainty

Inlet boundary conditions were specified as a uniform total pressure of 101,325 Pa with 5% turbulence intensity and a hydraulic diameter of 0.085 m, consistent with the upstream pipe conditions measured during the experimental campaign (see §5). Outlet conditions were specified as a mass-flow rate boundary, varied to sweep the operating range. Sensitivity to inlet turbulence intensity was assessed by running cases at 3% and 8%; head predictions varied by less than 0.4%, confirming low sensitivity. Wall roughness was set at Ra = 6.3 µm (as-cast surface finish), derived from profilometer measurements on the physical impeller. A ±50% perturbation in roughness height shifted predicted efficiency by 0.7 percentage points — this is documented as a recognized source of parametric uncertainty in the results.

---

## 4. Mesh Quality and Spatial Convergence

### 4.1 Mesh Construction

The mesh was generated in ANSYS Meshing with a hybrid strategy: structured hexahedral layers in the near-wall region (first cell y⁺ < 1 to support the low-Reynolds SST formulation) transitioning to unstructured tetrahedral elements in the volute core. The baseline mesh contains approximately 14.2 million elements. Mesh quality metrics: minimum orthogonal quality 0.31 (well above the 0.1 threshold), maximum aspect ratio 18.4 in the boundary layer (acceptable for wall-resolved RANS).

### 4.2 Mesh Refinement Study

A three-level mesh refinement study was conducted with element counts of 5.1M (coarse), 14.2M (medium), and 38.7M (fine), achieving a refinement ratio r ≈ 1.78 between successive levels. The Grid Convergence Index (GCI) methodology of Roache was applied using the pump head at the design flow rate (85 m³/h) as the primary metric. Results:

| Mesh | Head (m) | GCI (%) |
|------|----------|---------|
| Coarse | 43.81 | — |
| Medium | 42.67 | 2.61 |
| Fine | 42.29 | 0.89 |

The observed order of accuracy p = 2.07, consistent with the second-order scheme. The GCI on the fine mesh is 0.89%, indicating that spatial discretization error is well controlled. The medium mesh was selected for production runs as it provides a favorable accuracy-to-cost balance, with the fine-mesh GCI serving as a bound on remaining spatial error. Efficiency predictions showed similar convergence behavior (GCI_medium = 1.4%).

---

## 5. Experimental Validation

### 5.1 Test Facility and Instrumentation

Physical testing was conducted at the Fluid Machinery Laboratory, Technical University of Dresden, using a closed-loop test rig conforming to ISO 9906:2012 Grade 1 requirements. The test article was a production-intent HydroFlow-7 unit, serial number HF7-003. Instrumentation included:
- Differential pressure transducers (Kistler 4264A, ±0.05% FS) at flanged inlet/outlet taps
- Electromagnetic flowmeter (Endress+Hauser Promag 53, ±0.25% of reading)
- Torque/speed transducer (HBM T40B, ±0.1% FS)
- Water temperature logged at 1 Hz for viscosity correction

Measurement uncertainty was propagated per ISO/IEC Guide 98-3 (GUM). Combined expanded uncertainty (k=2) on head: ±0.38 m; on efficiency: ±0.6 percentage points.

### 5.2 Comparison of Simulation to Experiment

Head and efficiency curves were compared across seven operating points from 0.6Q to 1.2Q. At design flow (Q = 85 m³/h), simulated head was 42.67 m versus measured 42.1 ± 0.38 m — a discrepancy of 1.35%, well within the combined uncertainty band. Hydraulic efficiency: simulated 83.2% versus measured 82.4 ± 0.6% — agreement within experimental uncertainty. At 0.7Q (part-load), the simulation over-predicts head by 3.1%, which is attributed to the onset of incidence-driven separation at the impeller leading edge that the steady SST model handles imperfectly. This known limitation is documented and the 0.7Q–0.6Q predictions carry an advisory flag in the results.

Velocity profiles at the volute tongue region were compared against 2D PIV measurements taken during a separate test campaign (HydroFlow-5 geometry, scaled by similarity). Agreement in mean velocity magnitude was within 8% across the measurement plane, with larger deviations (up to 14%) near the tongue tip where the PIV spatial resolution was limited. This comparison is considered corroborating rather than primary validation due to the geometric difference.

---

## 6. Uncertainty Quantification and Sensitivity

### 6.1 Input Parameter Sensitivity

A structured sensitivity analysis was performed on five input parameters identified as having potential influence on outputs: inlet turbulence intensity, wall roughness height, wear ring clearance, blade surface finish, and fluid temperature (viscosity). A one-at-a-time (OAT) perturbation study (±20% on each parameter) was conducted at design flow. The dominant contributors to head uncertainty were wear ring clearance (±1.1 m head sensitivity) and wall roughness (±0.5 m). These were subsequently treated as uncertain inputs in a Monte Carlo propagation study (N = 500 Latin Hypercube samples), assuming uniform distributions bounded by manufacturing tolerances. The resulting 95th-percentile spread on predicted head at design flow was ±1.8 m, which encompasses the experimental measurement.

### 6.2 Numerical Uncertainty Budget

The total numerical uncertainty budget at design flow is estimated as follows: spatial discretization (GCI-based) ±0.38 m, iterative convergence (residual drop to 10⁻⁵, monitored outlet pressure oscillation < 0.05%) ±0.05 m, round-off (double precision) negligible. Combined numerical uncertainty ±0.39 m.

---

## 7. Solution Behavior and Convergence

All production simulations were run to a minimum of 3,000 iterations. Continuity residuals reached 10⁻⁵ and momentum residuals reached 10⁻⁶ or better in all cases. Outlet mass-flow imbalance was below 0.01%. Monitored quantities (head, shaft torque) were tracked iteration-by-iteration; at convergence, the variation in head over the final 500 iterations was less than 0.02 m, confirming that the solution had reached a stable steady state. No anomalous behavior (divergence, oscillatory non-convergence) was observed across any of the 28 production run cases. The simulation team reviewed residual histories and quantity monitors for all cases prior to post-processing; this review is documented in the simulation log (HF7-SIM-LOG-001).

---

## 8. Model Pedigree and Prior Use

The modeling approach employed here (full-wheel RANS, SST k-ω, sliding mesh interface, SIMPLE pressure-velocity coupling) has been applied by this team on three prior centrifugal pump programs: HydroFlow-3 (2019), HydroFlow-5 (2021), and an industrial wastewater pump for a third-party client (2022). In all cases, head predictions at design flow agreed with test data within 3%. The accumulated experience with this workflow, including lessons learned regarding near-wall mesh resolution requirements and interface treatment at the rotor-stator boundary, has been incorporated into the team's internal CFD practice standard (Document IPS-CFD-004, Rev 3). This institutional history provides additional confidence in the methodology beyond the formal V&V activities conducted for this specific model.

---

## 9. Intended Use and Extrapolation Risk

The simulation is intended to support: (1) impeller geometry trade studies at design flow ±20%, (2) volute cut-water position optimization, and (3) identification of recirculation onset flow rate. It is explicitly NOT intended for: cavitation inception prediction (no multiphase model), transient pressure pulsation analysis (steady-state only), or operation below 0.6Q. Any use of these results outside the stated operating window should be subject to additional review. The simulation team has provided guidance to the design engineering group on appropriate interpretation of results, including a one-hour briefing session on 2024-02-28 (attendance recorded in project file HF7-PROJ-002).

---

## 10. Limitations and Outstanding Items

1. **Turbulence model limitation at part-load:** As noted in §5.2, the steady SST model shows increasing deviation from experiment below 0.8Q. Users should apply a 5% head uncertainty adder for operating points in the 0.6Q–0.75Q range.

2. **PIV validation geometry mismatch:** The velocity field validation data (§5.2) was collected on the HydroFlow-5 geometry. A dedicated PIV campaign on HydroFlow-7 is planned for Q3 2024 and will provide more direct validation of internal flow structure.

3. **Wear ring clearance sensitivity:** Manufacturing tolerance on the wear ring gap (nominal 0.35 mm, tolerance +0.15/-0.05 mm) is the single largest contributor to head prediction uncertainty. Tighter tolerance control or direct measurement of the test article gap would reduce this uncertainty.

4. **Thermal effects:** The simulation assumes isothermal operation at 25 °C. For applications above 60 °C, a re-assessment of viscosity and density effects on performance prediction is recommended.

---

## 11. Overall Credibility Summary

Based on the evidence assembled in this report, the HydroFlow-7 CFD model is assessed as having **high credibility** for its primary intended use (head and efficiency prediction at design and near-design flow rates). The following factors support this assessment:

- Code-level correctness confirmed via MMS and benchmark comparisons
- Spatial convergence demonstrated with GCI < 1% on fine mesh; medium mesh used with documented error bound
- Boundary conditions grounded in measured experimental data with quantified uncertainty
- Validation against ISO-grade test data shows agreement within combined uncertainty at design flow
- Iterative convergence is robust and well-documented across all production cases
- Institutional experience with equivalent workflows on prior programs
- Sensitivity and uncertainty analysis performed; dominant uncertainty sources identified

Areas of reduced confidence (part-load below 0.8Q, internal velocity field structure) are explicitly flagged and carry appropriate uncertainty advisories. The model is recommended for use in its stated scope of application.

---

*Prepared by: CFD Methods Group, HydroFlow Engineering*
*Reviewed by: Independent Technical Review Board, Session 7 (2024-03-10)*
*Document Number: HF7-VV-RPT-002 Rev 2.1*
