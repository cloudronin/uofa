# Credibility Assessment Report
## Conjugate Heat Transfer Simulation of a Liquid-Cooled Power Electronics Module
### Project: THERM-SIM-2024 | Revision 3.1 | Prepared by: Advanced Thermal Systems Group

---

## 1. Background and Scope

This report documents the credibility assessment of a conjugate heat transfer (CHT) computational model developed to predict junction temperatures and coolant-side thermal resistance in a liquid-cooled insulated-gate bipolar transistor (IGBT) power module assembly. The assembly consists of a direct-bonded copper (DBC) substrate, aluminum nitride ceramic insulator, baseplate (Cu-Mo alloy), and a serpentine microchannel cold plate supplied with a 50/50 ethylene glycol–water (EGW) mixture at nominal inlet conditions of 65 °C and 6 L/min.

The simulation was executed using ANSYS Fluent 2023 R2 with the CHT solver coupling the solid conduction domains (IGBT die, solder layers, DBC, baseplate) to the single-phase turbulent flow domain inside the cold plate channels. Turbulence was represented with the realizable k-ε model with enhanced wall treatment. The primary quantities of interest (QoIs) are (a) peak IGBT junction temperature T_j,max, (b) maximum baseplate temperature T_bp,max, and (c) overall thermal resistance R_th,jf from junction to coolant fluid.

The assessment framework applied here follows a structured verification and validation methodology appropriate for thermal-fluid engineering models used in product qualification decisions. Evidence was collected from simulation records, laboratory test reports, and peer review documentation spanning the period January–October 2024.

---

## 2. Intended Use and Decision Context

The simulation outputs are intended to support two engineering decisions: (1) confirmation that T_j,max remains below 125 °C under worst-case continuous operating power of 850 W per module, and (2) selection between two cold-plate channel geometries (baseline rectangular versus enhanced re-entrant fin profile). The consequence of an incorrect prediction leading to an overly optimistic junction temperature is thermal runaway and potential field failure of a traction inverter system. This places the model in a moderate-to-high consequence category.

The simulation team, test engineers, and a domain expert panel convened to define the acceptable prediction uncertainty at ±8 °C for junction temperature and ±0.05 °C/W for thermal resistance. These thresholds were derived from system-level reliability margins and are documented in the project's Model Acceptance Criteria document (MAC-THERM-2024-01).

---

## 3. Problem Formulation and Conceptual Fidelity

### 3.1 Geometry Representation

The CAD geometry was imported from the product PDM system (PTC Creo, release 9.0) and simplified for meshing by suppressing fastener holes, chamfers smaller than 0.1 mm, and solder fillet radii below 0.05 mm. A sensitivity study confirmed that omitting these features changes T_j,max by less than 0.3 °C, well within tolerance. The channel geometry was reconstructed from manufacturing drawings rev. D; dimensional audit against a coordinate-measuring machine (CMM) scan of a production cold plate showed maximum deviation of 0.04 mm on channel width and 0.06 mm on fin pitch — both judged acceptable.

### 3.2 Physics Scope and Modeling Assumptions

The model treats the IGBT die as a volumetric heat source with uniform power density; spatial non-uniformity of heat generation within the die is not represented. A sensitivity analysis varying the assumed heat-generation distribution (uniform vs. edge-concentrated, based on published electrothermal data from Infineon AN2017-04) showed a ±3.1 °C swing in T_j,max. This uncertainty is carried forward as a physics-scope limitation. Radiation exchange between exposed surfaces was evaluated and found to contribute less than 0.4 W to the energy balance at operating temperature; it is excluded from the model with documented justification.

The coolant is treated as a single-phase incompressible fluid. Boiling onset was checked using the Bergles-Rohsenow criterion; the minimum wall superheat margin is 28 °C at worst-case heat flux, confirming the single-phase assumption is valid. This constitutes a deliberate and documented scoping decision rather than an oversight.

### 3.3 Relevance of the Simulation to the Physical System

The team explicitly evaluated how well the computational scenario matches the real operating environment. Inlet flow distribution across parallel modules in the actual inverter stack was characterized by a 1D network model (GT-SUITE), which predicted a ±7% flow maldistribution across the six modules. The CHT model was run at nominal flow (6 L/min) and at the worst-case low-flow condition (5.58 L/min) to bound this effect. The difference in T_j,max between these two runs was 4.2 °C, which is incorporated into the uncertainty budget. Mechanical boundary conditions (mounting torque, thermal interface material compression) were reviewed against assembly specifications; TIM conductivity was modeled at 6 W/m·K (nominal) with a ±1 W/m·K sensitivity band per vendor datasheet (Bergquist GP3000).

---

## 4. Numerical Solution Quality

### 4.1 Mesh Refinement Study

A systematic spatial refinement study was conducted using three structured hexahedral meshes: coarse (1.8 M cells), medium (5.4 M cells), and fine (14.7 M cells), maintaining a constant refinement ratio of approximately 1.44 in each spatial direction within the fluid domain. The Grid Convergence Index (GCI) methodology of Roache was applied. For T_j,max, the GCI between the medium and fine meshes was 0.6%, corresponding to a numerical uncertainty of ±0.4 °C. For R_th,jf, the GCI was 1.1%, giving ±0.008 °C/W. The observed order of convergence was 1.93, consistent with the second-order spatial discretization scheme employed. All production runs used the medium mesh (5.4 M cells) as the accepted discretization, with the fine-mesh GCI bound applied as a numerical error estimate.

Wall y+ values in the fluid domain ranged from 0.8 to 4.2 across the channel walls, consistent with the enhanced wall treatment requirements. Spot checks at 12 locations confirmed y+ compliance.

### 4.2 Iterative Convergence

Residual convergence was monitored for continuity, momentum (x, y, z), energy, k, and ε equations. All residuals dropped at least five orders of magnitude from their initial values. The energy residual reached 1×10⁻⁹ by iteration 2,400. QoI monitors (T_j,max and R_th,jf) were additionally tracked and showed variation of less than 0.05 °C and 0.001 °C/W over the final 500 iterations, confirming iterative convergence independent of residual behavior.

### 4.3 Solver and Code Verification

ANSYS Fluent 2023 R2 was used under a validated software configuration controlled through the project's software quality plan (SQP-2024-003). The CHT capability was verified against the analytical solution for a two-layer composite wall with internal heat generation (Carslaw & Jaeger §3.4) using a purpose-built test case. The computed temperature profile agreed with the analytical solution to within 0.02% at all comparison points, confirming correct implementation of the energy equation coupling at solid-fluid interfaces. Additionally, the turbulent channel flow module was benchmarked against the DNS dataset of Moser, Kim & Mansour (1999) at Re_τ = 395; the realizable k-ε model reproduced the mean velocity profile within 3.5% and the wall heat transfer coefficient within 6.2%, consistent with known model limitations documented in the Fluent Theory Guide.

---

## 5. Input Data and Parameter Characterization

### 5.1 Material Properties

Thermal conductivity values for all solid materials were obtained from traceable sources: DBC copper layers from ASTM E1461 flash diffusivity measurements performed by the materials lab (report ML-2024-047), ceramic AlN from vendor certificate of conformance (Rogers Corp., lot 2024-Q2), and solder (SAC305) from published literature (Lalena et al., 2007) with ±10% uncertainty applied. Coolant properties (density, viscosity, specific heat, conductivity) were taken from ASHRAE Fundamentals 2021 for 50/50 EGW at 65 °C; these are considered well-characterized with negligible parametric uncertainty.

### 5.2 Boundary Condition Uncertainty

Inlet coolant temperature was measured during validation testing with a calibrated PT100 RTD (±0.15 °C, NIST-traceable calibration). Flow rate was measured with a Coriolis meter (±0.5% of reading). Power input to each IGBT was controlled by a programmable load bank and measured via a precision shunt resistor (±0.3% accuracy). These measurement uncertainties were propagated through a Monte Carlo analysis (10,000 samples) to quantify their contribution to QoI uncertainty, yielding a combined input-driven uncertainty of ±1.8 °C for T_j,max.

---

## 6. Validation Evidence

### 6.1 Experimental Configuration and Instrumentation

Validation testing was conducted on three production-representative cold plate assemblies (serial numbers CP-001, CP-002, CP-003) using a purpose-built thermal test bench. Junction temperatures were measured using on-die temperature-sensitive electrical parameters (TSEP method, calibrated per JEDEC JESD51-14) with an estimated accuracy of ±1.5 °C. Baseplate temperatures were measured with five type-K thermocouples per module, calibrated against a NIST-traceable reference; accuracy ±0.5 °C. Thermal resistance was derived from the TSEP and power measurements.

### 6.2 Comparison Metrics and Results

Validation was performed at five operating points spanning 400–850 W total module power and two flow rates (4 L/min and 6 L/min). The simulation-to-experiment comparison for T_j,max showed a mean signed error of +2.1 °C (simulation slightly over-predicts) and a root-mean-square error of 3.4 °C across all ten test conditions. For R_th,jf, the mean signed error was +0.018 °C/W and the RMS error was 0.024 °C/W. Both QoIs fall within the MAC-defined acceptance thresholds of ±8 °C and ±0.05 °C/W respectively.

The validation comparison was conducted using the approach described by Oberkampf and Bayes factor-style reasoning: the combined experimental uncertainty (accounting for measurement error, unit-to-unit variation across three assemblies, and repeatability) was estimated at ±2.8 °C for T_j,max. The simulation numerical uncertainty (GCI-based) is ±0.4 °C. The model-form and input uncertainty together contribute approximately ±4.5 °C. The total combined uncertainty of ±5.3 °C (RSS combination) is comfortably within the ±8 °C threshold, supporting a positive validation finding.

### 6.3 Validation Domain Coverage

The validation dataset covers the interpolation region of the intended operating envelope well. However, transient thermal cycling conditions (pulse power up to 1,200 W for <500 ms) are outside the validated domain. The simulation team documented this as an explicit extrapolation risk; transient predictions carry a higher uncertainty flag and should not be used for qualification decisions without additional validation data.

---

## 7. Uncertainty Quantification and Sensitivity Analysis

A structured uncertainty budget was assembled combining: (a) numerical discretization error (GCI), (b) iterative convergence error, (c) input parameter uncertainty (Monte Carlo), (d) model-form uncertainty estimated from the validation residuals, and (e) the physical scope uncertainty from the non-uniform heat generation assumption. The total expanded uncertainty (95% confidence) for T_j,max at the worst-case 850 W condition is ±6.1 °C. This is within the ±8 °C acceptance criterion. A tornado chart of sensitivity contributions shows that TIM conductivity and inlet flow rate are the dominant drivers of prediction uncertainty, together accounting for 61% of total variance.

---

## 8. Peer Review and Independent Oversight

The simulation methodology, mesh quality, and validation comparisons were reviewed by two independent subject matter experts: one from the corporate thermal sciences center of excellence and one external consultant with CHT modeling experience in power electronics (Dr. A. Renner, Thermal Analytics GmbH). Both reviewers confirmed that the modeling approach, boundary condition specification, and validation scope are appropriate for the intended use. Minor recommendations were issued regarding documentation of the turbulence model selection rationale; these were addressed in revision 3.1 of this report. A formal review record is archived in the project document management system (DMS reference: PRJ-2024-THERM-REV-003).

---

## 9. Documentation and Reproducibility

The simulation input files, mesh files, material property tables, post-processing scripts, and this report are archived in the project repository (Git repository: therm-sim-2024, tag v3.1-final). A simulation log capturing software version, license server, hardware platform (48-core AMD EPYC 7543 cluster node, 256 GB RAM), and run timestamps is included. A third-party analyst confirmed that the simulation could be re-executed from archived inputs and reproduced T_j,max within 0.1 °C of the reported value, confirming reproducibility. The model documentation package meets the requirements of the project's configuration management plan (CMP-2024-007).

---

## 10. Summary Assessment

| Dimension | Finding | Confidence |
|---|---|---|
| Physical scope and conceptual fidelity | Well-defined with documented assumptions and sensitivity checks | High |
| Numerical solution quality | GCI <1.1%, iterative convergence confirmed | High |
| Code correctness | Verified against analytical solutions and DNS benchmarks | High |
| Input characterization | Traceable, uncertainty-quantified | High |
| Validation breadth | 10 test conditions, 3 units, RMS error within acceptance | High |
| Uncertainty budget | Complete, RSS combination within threshold | High |
| Independent review | Two reviewers, findings addressed | High |
| Documentation/reproducibility | Archived, independently reproduced | High |

**Overall Credibility Finding:** The CHT simulation of the liquid-cooled IGBT module is assessed as credible for its intended use — predicting steady-state junction temperature and thermal resistance within the validated operating envelope (400–850 W, 4–6 L/min EGW at 65 °C inlet). The model is **not** currently validated for transient pulse conditions and should not be used for that purpose without additional experimental support.

---

*Report prepared by: Advanced Thermal Systems Group, THERM-SIM-2024 project*
*Approved by: Chief Engineer, Power Electronics Thermal Management*
*Date: October 28, 2024*
