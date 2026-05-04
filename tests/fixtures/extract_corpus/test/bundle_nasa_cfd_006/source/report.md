# Credibility Assessment Report
## CFD Analysis of Centrifugal Pump Stage — Impeller and Volute Flow Simulation
### Project: HYDRA-7 Pump Platform | Document Rev. 2.4 | Prepared by: Fluid Systems Analysis Group

---

## 1. Background and Purpose

This report documents the credibility assessment for the Reynolds-Averaged Navier-Stokes (RANS) computational fluid dynamics model used to predict hydraulic performance of the HYDRA-7 single-stage centrifugal pump. The simulation campaign was conducted using ANSYS Fluent 2023 R1 with the SST k-ω turbulence closure. The primary quantities of interest (QoIs) are total-to-total pressure rise across the impeller stage, shaft power consumption at the design operating point (1,450 RPM, 85 m³/hr flow rate), and meridional velocity profiles at three cross-sections within the volute.

The assessment follows an internal credibility framework aligned with NASA-7009B guidance, adapted for commercial turbomachinery applications. The intended use of the model is to support pump selection decisions for a chemical process facility where off-design performance predictions (60–120% of design flow) must be reliable to within ±8% on pressure head. This report covers all major credibility dimensions; no factors have been deferred to a later milestone.

---

## 2. Intended Use and Applicability of the Model

The simulation domain and physics assumptions were explicitly matched to the intended use scenario. The pump operates on an aqueous solution (density 998 kg/m³, dynamic viscosity 1.003 × 10⁻³ Pa·s) at 25°C. Cavitation was not modeled because the facility NPSH margin exceeds 4.2 m across the full operating range, placing this phenomenon outside the scope of the current assessment.

The model geometry was constructed from the OEM-supplied CAD files (HYDRA-7 Rev. C impeller drawings, received 2024-01-15). Minor geometric simplifications were applied: six impeller blade fillets with radii below 0.3 mm were suppressed, and the mechanical seal cavity was excluded. A sensitivity study (Section 4.3) confirmed these omissions introduce less than 0.4% variation in predicted head. The simulation boundary conditions — inlet total pressure, outlet mass-flow rate, rotational speed — are directly traceable to the facility P&ID specifications and pump data sheet.

The assessment team judged the model's physical scope to be well-matched to the decision it is intended to support. The off-design operating envelope (60–120% of design flow) is covered by the sweep of 11 steady-state operating-point simulations.

---

## 3. Pedigree of the Computational Approach

### 3.1 Software Qualification

ANSYS Fluent 2023 R1 is a commercially maintained solver with an extensive validation history in rotating machinery applications. The solver's pressure-velocity coupling (SIMPLE algorithm), spatial discretization (second-order upwind for momentum and turbulence quantities), and moving reference frame implementation were verified against the NPARC Alliance benchmark suite cases V3.1 and V3.5, which cover confined swirling flows and rotor-stator interactions respectively. Internal regression testing logs (Fluent QA Report QA-2023-R1-017) confirm bit-for-bit reproducibility across solver versions for the relevant physics modules.

The SST k-ω model implementation was additionally cross-checked against the NASA Langley Turbulence Modeling Resource benchmark data for a backward-facing step (Re = 37,500) and a 2D diffuser (Buice-Eaton geometry). Normalized residuals for both cases fell within the published scatter band. No custom user-defined functions were employed in this campaign, which reduces the risk of implementation errors in problem-specific code.

### 3.2 Numerical Scheme Appropriateness

Steady-state RANS with a frozen-rotor (multiple reference frame) interface was used for the bulk of the operating-point sweep. Sliding-mesh unsteady simulations were performed at the design point and at 60% flow to capture rotor-stator interaction effects and validate the steady-state approximation. The unsteady simulations showed that cycle-averaged pressure rise agreed with the steady MRF result to within 1.7%, confirming the steady approach is adequate for the performance QoIs.

---

## 4. Mesh Refinement and Numerical Accuracy

### 4.1 Spatial Convergence Study

A structured multi-block mesh was generated using ANSYS TurboGrid 2023 R1. Three mesh levels were constructed for the impeller passage: coarse (1.8 M cells), medium (5.4 M cells), and fine (14.6 M cells), maintaining geometric similarity through a refinement ratio of approximately 1.67 in each coordinate direction. The volute mesh (unstructured hexahedral-dominant) was refined independently using three levels of 0.9 M, 2.7 M, and 7.4 M cells.

Grid Convergence Index (GCI) analysis following the Celik et al. (2008) procedure was applied to total pressure rise (ΔP_tt) and shaft power (W_shaft). Results are summarized below:

| Mesh Pair | GCI_fine (ΔP_tt) | GCI_fine (W_shaft) | Observed Order p |
|---|---|---|---|
| Coarse→Medium | 3.8% | 4.1% | — |
| Medium→Fine | 1.1% | 1.3% | 2.04 |

The observed convergence order of 2.04 is consistent with the second-order spatial scheme employed. The fine mesh GCI values of 1.1% and 1.3% are well within the ±8% decision threshold. All subsequent simulations used the medium mesh (5.4 M impeller + 2.7 M volute cells) as the production mesh, accepting the ~1.1% numerical discretization uncertainty as a documented contribution to the overall uncertainty budget.

Wall y⁺ values on the impeller blades ranged from 0.8 to 4.2 on the medium mesh, appropriate for the SST k-ω model's low-Reynolds-number near-wall treatment.

### 4.2 Iterative Convergence

All steady-state solutions were run to a minimum of 3,000 iterations. Convergence was declared when all scaled residuals dropped below 1 × 10⁻⁵ and the monitored QoIs (ΔP_tt, W_shaft) showed variation less than 0.05% over the final 500 iterations. These criteria were met for all 11 operating points. The 60% flow case showed the slowest convergence (residuals stabilizing at ~8 × 10⁻⁶ after 4,200 iterations), which is consistent with the incipient recirculation expected at low flow.

### 4.3 Sensitivity to Modeling Assumptions

Turbulence model sensitivity was assessed by running the design point case with the Realizable k-ε model and the standard k-ω model in addition to SST k-ω. Predicted head varied by +2.3% (k-ε) and −1.8% (standard k-ω) relative to SST k-ω. Inlet turbulence intensity was varied from 1% to 10%; resulting head variation was less than 0.6%. These sensitivities were included in the uncertainty budget as modeling form uncertainty contributions.

---

## 5. Validation Against Physical Evidence

### 5.1 Validation Dataset Description

Experimental data were obtained from a dedicated hydraulic test rig operated by the OEM (Flowserve Technical Center, Dortmund) under ISO 9906:2012 Grade 1B conditions. The test fluid was water at 22–24°C. Instrumentation included:

- Differential pressure transducers (Rosemount 3051, ±0.065% full-scale accuracy) at inlet and outlet flanges
- Coriolis mass flow meter (Endress+Hauser Promass 83, ±0.1% of reading)
- Torque transducer on the shaft (HBM T10F, ±0.1% full-scale)
- Five-hole probe traverses at the volute exit cross-section (Section C-C) at design flow

The test data were collected across 15 operating points spanning 50–130% of design flow. Measurement uncertainty was propagated using the ISO GUM methodology; expanded uncertainty (k=2) on head coefficient was ±1.4% and on efficiency was ±1.8%.

### 5.2 Comparison of Predictions to Measurements

At the design operating point, the CFD-predicted total head was 47.3 m versus the measured 46.8 m, a discrepancy of +1.1% (within measurement uncertainty). Shaft power was predicted at 18.7 kW versus measured 18.4 kW (+1.6%). Across the full operating range, RMS error in head prediction was 2.3% and in efficiency was 2.9%, both within the ±8% decision threshold.

Velocity magnitude profiles from the five-hole probe traverse at Section C-C showed good qualitative agreement; the CFD captured the high-velocity jet near the volute tongue and the recirculation zone on the suction side. Quantitative comparison showed RMS velocity error of 4.8% of the local bulk velocity. Some discrepancy in the wake region immediately downstream of the tongue (up to 11% local error) is attributed to unsteady rotor-stator interaction effects not captured by the steady MRF approach; this is noted as a known limitation.

### 5.3 Validation Hierarchy and Generalization

The validation dataset is directly relevant to the intended use: same geometry, same fluid, same operating range. The validation was conducted at a higher level of physical fidelity than any sub-component benchmarks, which strengthens confidence. The assessment team notes, however, that the experimental data were collected by the equipment vendor, introducing a potential source of bias. An independent witness test was not performed due to schedule constraints; this is flagged as a residual risk.

---

## 6. Uncertainty Quantification and Propagation

A structured uncertainty budget was assembled for the primary QoI (total head at design point). Contributions were identified and quantified as follows:

| Source | Type | Magnitude (% of head) |
|---|---|---|
| Spatial discretization (GCI) | Numerical | ±1.1% |
| Turbulence model form | Model | ±2.3% |
| Inlet turbulence intensity | Input | ±0.6% |
| Fluid properties (temperature variation) | Input | ±0.3% |
| Geometric simplifications | Model | ±0.4% |
| Experimental measurement (validation data) | Experimental | ±1.4% |

Contributions were combined using root-sum-square (RSS) assuming independence, yielding a combined simulation uncertainty of approximately ±2.7% (k=1) on predicted head. This is comfortably within the ±8% decision threshold, providing adequate margin for the intended use.

Sensitivity coefficients for each input parameter were computed using a one-at-a-time finite-difference approach. A full Monte Carlo propagation was not performed; the linear sensitivity assumption was judged adequate given the relatively small input variations and the smooth response surface observed in the parameter sweeps.

---

## 7. Qualification of the Analysis Team and Processes

### 7.1 Personnel Competency

The lead analyst (Dr. A. Mertens, P.Eng.) holds a Ph.D. in turbomachinery aerodynamics and has seven years of experience conducting RANS simulations of centrifugal pumps and compressors. Two supporting analysts participated in mesh generation and post-processing; both completed ANSYS Fluent certification training (Level 2 Rotating Machinery, 2023). The team's prior work on a comparable pump platform (HYDRA-5 series) was reviewed during the project kickoff to ensure lessons learned were incorporated.

### 7.2 Process Controls and Review

The simulation campaign followed the organization's CFD Simulation Procedure SP-CFD-004 Rev. 7, which mandates independent peer review of mesh quality, boundary condition setup, and results interpretation. Peer review was conducted by Dr. L. Okonkwo (senior CFD specialist, not involved in the analysis), and all review comments were formally dispositioned. A pre-analysis plan was documented before any production simulations were run, specifying the QoIs, acceptance criteria, and the mesh convergence strategy. This plan was not modified after data collection began.

### 7.3 Configuration Management

All simulation input files, mesh files, case files, and post-processing scripts are stored in the project's version-controlled repository (GitLab, project HYDRA7-CFD, tag v2.4-release). A complete audit trail of changes is maintained. The final production results are locked under document control number DC-HYDRA7-CFD-0042.

---

## 8. Applicability of Supporting Data and References

Physical property data (fluid density, viscosity) were taken from NIST WebBook (accessed 2024-02-10), which is an authoritative and traceable source. Pump geometry data originated from OEM engineering drawings with revision control. Turbulence model constants used the standard SST k-ω values from Menter (1994); no tuning of model constants was performed, which preserves the generality of the validation evidence.

Literature references used to support turbulence model selection (Menter 1994; Bardina et al. 1997; Smirnov & Menter 2009) are peer-reviewed publications appropriate to the application. The benchmark validation cases (NPARC V3.1, V3.5; NASA Langley TMR) are publicly available and widely accepted in the CFD community. No proprietary or unverifiable reference data were used.

---

## 9. Limitations and Residual Risks

1. **Steady-state approximation**: Rotor-stator interaction is not fully captured. Local velocity errors up to 11% were observed near the volute tongue. For the global performance QoIs this is acceptable; for any future use requiring local flow field fidelity, unsteady LES or SAS-SST simulations should be considered.

2. **Single vendor test data**: The validation dataset was provided by the equipment manufacturer. Independent experimental confirmation would further strengthen confidence.

3. **Cavitation exclusion**: The model is not valid for operating conditions where NPSH margin falls below 2 m. Any future use at reduced inlet pressures requires a separate cavitation-enabled simulation campaign.

4. **Fluid scope**: The model was validated for water. Application to fluids with significantly different viscosity (e.g., process slurries, viscous polymers) requires re-validation.

5. **Monte Carlo uncertainty propagation**: The RSS approach assumes linearity and independence. For highly off-design conditions (below 60% flow), nonlinear interactions between turbulence model uncertainty and flow separation may cause the RSS estimate to understate combined uncertainty.

---

## 10. Overall Credibility Summary

Based on the evidence assembled in this report, the HYDRA-7 CFD model is assessed as having **high credibility** for predicting total head and shaft power across the 60–120% design flow range, for the specified fluid and operating conditions. The model's intended use is clearly defined, the numerical errors are quantified and bounded, validation against relevant experimental data shows agreement within the decision threshold, and the analysis process was conducted under appropriate quality controls.

The most significant residual uncertainties are the turbulence model form error (±2.3%) and the single-source nature of the validation data. These are judged acceptable given the ±8% decision margin available. The model should not be used outside the documented scope without a supplementary credibility assessment.

---

*Report prepared by: Fluid Systems Analysis Group*
*Review completed: 2024-03-18*
*Next scheduled review: Prior to any scope extension or geometry change*
