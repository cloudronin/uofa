# Conjugate Heat Transfer Simulation Credibility Assessment
## Turbine Blade Internal Cooling Channel Analysis — GE9X-Class HPT Stage 1

**Prepared by:** Thermal-Fluids Simulation Group, Advanced Propulsion Systems Division
**Document Number:** TFS-CHT-2024-0047 Rev B
**Date:** 14 March 2024
**Classification:** Company Confidential — Distribution List C

---

## 1. Background and Scope

This report documents the credibility assessment for a series of conjugate heat transfer (CHT) simulations performed in support of the High-Pressure Turbine (HPT) Stage 1 blade cooling redesign program. The computational campaign was executed using ANSYS Fluent 2023 R2 with the coupled energy solver, targeting prediction of internal convective cooling effectiveness and external film cooling augmentation for a scaled (1.5×) blade geometry with a five-pass serpentine internal circuit and four rows of shaped film holes along the pressure side.

The simulations are intended to support decisions about coolant flow budgeting and metal temperature distribution for life prediction. Predictions feed directly into a finite-element creep-fatigue model; therefore, the thermal boundary condition accuracy carries significant consequence for downstream structural assessments.

The credibility assessment framework applied here follows the general principles of simulation validation hierarchies and uncertainty quantification as described in accepted aerospace simulation governance documentation. The evaluation covers the full simulation lifecycle from problem formulation through post-processed outputs.

---

## 2. Problem Formulation and Intended Use

### 2.1 Geometric and Physical Fidelity

The CAD geometry was derived from the manufacturing nominal dataset (CATIA V5 file TBL-HPT1-S1-NOM-Rev4). A deliberate decision was made to exclude leading-edge showerhead holes from the current model; this simplification was reviewed and accepted by the aerothermal lead on the grounds that showerhead interaction with the external boundary layer is addressed in a separate RANS campaign. The exclusion is documented in the simulation plan (TFS-SIM-PLAN-0031) and its potential influence on the pressure-side adiabatic effectiveness is bounded by a sensitivity run showing less than 4% change in local Nusselt number distribution when showerhead mass flow is varied ±15%.

The working fluid is air modeled as an ideal gas with temperature-dependent properties (Sutherland viscosity law; polynomial fits to NIST data for Cp and thermal conductivity). The blade substrate is modeled as a directionally solidified René 80 nickel superalloy; conductivity tensor components were taken from the material property database MPD-DS-R80-2019, with anisotropy ratios verified against published literature values (Gayda et al., 1994).

### 2.2 Governing Equations and Solver Configuration

The steady-state Reynolds-averaged Navier-Stokes (RANS) equations are solved with the realizable k-ε turbulence closure, supplemented by enhanced wall treatment. Turbulence intensity at the coolant inlet was set to 5% with a hydraulic-diameter-based length scale. The external hot-gas boundary conditions (total pressure, total temperature, turbulence profiles) were extracted from a full-annulus unsteady CFD solution provided by the aero group (report AER-HGP-2023-112); these profiles were time-averaged before application as inflow conditions, and the adequacy of this averaging is discussed in Section 5.4.

The conjugate coupling between the fluid and solid domains is handled natively within Fluent's coupled wall formulation. Convergence was assessed by monitoring residuals (all below 1×10⁻⁵ for continuity, momentum, and energy) alongside integral quantities: total heat flux through the blade surface, coolant exit total temperature, and pressure drop across each pass. Residual histories are archived in the simulation database (SIMDB entry CHT-2024-0047-A through -F).

---

## 3. Computational Mesh and Discretization Studies

### 3.1 Mesh Generation Strategy

The fluid and solid domains were meshed using ANSYS Meshing with a polyhedral core and prismatic inflation layers. The near-wall resolution in the internal passages targets y⁺ ≈ 1 (achieved mean y⁺ = 0.87 across all internal surfaces; 98th percentile y⁺ = 2.1). External hot-gas path y⁺ mean is 1.3. Mesh generation scripts are version-controlled in the project Git repository (branch `cht-hpt1-cooling-v3`).

### 3.2 Mesh Refinement Study

A systematic mesh refinement study was conducted using three grid levels — coarse (8.4 M cells), medium (22.1 M cells), and fine (58.6 M cells) — with a nominal refinement ratio of approximately 1.4 in each spatial direction. The Grid Convergence Index (GCI) methodology of Celik et al. (2008) was applied to the following quantities of interest (QoIs):

| QoI | GCI_fine (%) | Observed Order |
|---|---|---|
| Span-averaged Nusselt number, pressure side | 1.8 | 2.1 |
| Peak metal temperature (normalized) | 0.9 | 2.3 |
| Coolant total pressure drop, pass 3 | 3.4 | 1.7 |
| Area-averaged film effectiveness, PS row 2 | 4.2 | 1.6 |

The GCI values are below the 5% threshold established in the simulation plan for all primary QoIs. The coarser grid solution exhibits monotonic convergence in all cases. Oscillatory behavior was not observed. The medium grid (22.1 M cells) was selected as the production mesh on the basis of cost-accuracy trade-off; the fine grid results are retained as reference.

---

## 4. Code Verification and Numerical Accuracy

### 4.1 Solver Verification Activities

The ANSYS Fluent 2023 R2 release was subjected to internal verification testing by ANSYS prior to release. The project team performed supplemental verification exercises relevant to the CHT application:

- **Laminar pipe flow with wall conduction:** Analytical solution (Graetz problem with conducting wall) reproduced to within 0.3% in Nusselt number using the same solver settings.
- **2-D fin array:** Temperature distribution compared against the exact fin-efficiency solution; maximum nodal error 0.8°C over a 200°C range.
- **Turbulent channel flow with heat transfer:** DNS data of Moser et al. (1999) used as reference; mean temperature profile reproduced within 4% for Re_τ = 395.

These exercises confirm that the solver implementation of the energy equation and conjugate boundary condition is functioning as intended for the class of problems considered. Results are documented in the verification report TFS-VER-2023-008.

### 4.2 Iterative Convergence

As noted above, all residuals reached 1×10⁻⁵ or below. Integral QoI monitors showed variation of less than 0.1% over the final 500 iterations. Double-precision arithmetic was used throughout.

---

## 5. Validation Against Experimental Data

### 5.1 Validation Hierarchy

The validation strategy follows a building-block approach with three tiers:

1. **Unit problems:** Isolated internal channel geometries (smooth and ribbed rectangular ducts) compared against published correlations (Dittus-Boelter, Webb-Eckert) and experimental data from the open literature.
2. **Benchmark subsystem:** A scaled (2×) five-pass serpentine channel tested in the division's low-speed heat transfer rig (Rig 7B). This benchmark was specifically designed to match the non-dimensional parameters (Re, Pr, Ro) of the HPT application.
3. **System-level:** Full-blade CHT prediction compared against thermocouple rake data from a combustor-exit rig test (Test Series HPT-RIG-2022-03).

### 5.2 Unit-Level Validation Results

For smooth rectangular duct (AR = 2:1), the predicted Nusselt number agreed with the Dittus-Boelter correlation within 6% across Re = 10,000–80,000. For 45° angled rib geometry (e/D = 0.1, P/e = 10), predictions fell within 12% of the Liou and Hwang (1993) experimental data at Re = 30,000. The higher discrepancy for the ribbed case is attributed to the known deficiency of linear eddy-viscosity models in capturing the secondary flow structures behind discrete ribs; this is flagged as a source of systematic bias in the uncertainty budget.

### 5.3 Benchmark Serpentine Channel (Rig 7B)

The Rig 7B test article was manufactured to ±0.05 mm dimensional tolerance from the nominal CAD. Infrared thermometry was used to map the outer wall temperature distribution at 14 operating conditions spanning Re = 15,000–65,000 (coolant side) and heat flux levels of 2–18 kW/m². Uncertainty in the IR measurements is ±2.5°C (95% confidence, per calibration report CAL-IR-2023-04).

The CHT simulation of the Rig 7B geometry (using identical solver settings to the production model) predicted wall temperatures within ±8°C of the measured values for 91% of the measurement locations at the nominal operating condition (Re = 40,000, q″ = 10 kW/m²). The root-mean-square error across all locations was 5.3°C. Systematic under-prediction of temperatures near the turn regions (up to 14°C) is consistent with the known turbulence model bias identified at the unit level.

### 5.4 System-Level Comparison

Test Series HPT-RIG-2022-03 provided 23 thermocouple measurements embedded in the blade at mid-span and tip-region locations. Measured metal temperatures (corrected for radiation, per test procedure HPT-TP-2022-03-Rev1) were compared against the CHT predictions at equivalent operating conditions. The simulation predicted temperatures within ±15°C (2σ) for 20 of 23 measurement locations. The three outliers are all located near the trailing-edge slot, where the simplified trailing-edge geometry in the model (slot modeled as a uniform bleed rather than discrete holes) is believed to introduce local error.

The time-averaging of hot-gas inflow profiles (Section 2.2) was assessed by comparing a time-averaged profile simulation against a simulation using the instantaneous profile at peak heat load; the difference in peak metal temperature was 7°C, which is within the overall uncertainty budget.

---

## 6. Uncertainty Quantification and Sensitivity Analysis

### 6.1 Input Uncertainty Propagation

A non-intrusive polynomial chaos expansion (PCE) approach was used to propagate uncertainties in six key inputs:

| Input Parameter | Distribution | ±1σ Range |
|---|---|---|
| Coolant inlet total temperature | Normal | ±3 K |
| Coolant mass flow rate | Normal | ±2% |
| Hot-gas total temperature (inlet) | Normal | ±8 K |
| Blade thermal conductivity (chordwise) | Uniform | ±5% |
| Film hole discharge coefficient | Normal | ±4% |
| Turbulence intensity (hot-gas inlet) | Uniform | 3–8% |

The PCE expansion used third-order polynomials with a sparse quadrature grid (Smolyak level 3), requiring 97 deterministic solver evaluations. The dominant contributor to peak metal temperature uncertainty is hot-gas total temperature (sensitivity index S₁ = 0.61), followed by coolant mass flow rate (S₁ = 0.19). The combined 95th percentile uncertainty in predicted peak metal temperature is ±22°C.

### 6.2 Turbulence Model Sensitivity

Given the identified bias in the ribbed-duct predictions, a supplemental run was performed using the SST k-ω model. The change in span-averaged Nusselt number on the pressure side was +7% relative to the realizable k-ε baseline. This spread is incorporated into the uncertainty budget as a model-form contribution.

---

## 7. Simulation Team Qualifications and Process Controls

### 7.1 Personnel Competency

The lead simulation engineer (L. Okonkwo, Senior Staff) holds a Ph.D. in mechanical engineering with a dissertation focused on turbine film cooling and has eight years of post-doctoral CHT simulation experience. The supporting analyst (R. Theriault) has four years of relevant experience and completed the internal CHT certification program (cert. TFS-CERT-CHT-L2) in 2022. Both analysts attended the ANSYS Fluent advanced turbomachinery training course in October 2023.

### 7.2 Independent Technical Review

An independent review of the simulation setup, mesh quality, and results interpretation was conducted by Dr. M. Vasquez (Principal Engineer, External Aerothermal Group), who was not involved in the simulation campaign. The review covered the simulation plan, mesh metrics report, validation comparison plots, and uncertainty budget. Three findings were raised (minor), all resolved prior to this report revision. Review records are in document TFS-REVIEW-2024-0047.

### 7.3 Configuration Management and Reproducibility

All simulation input files, mesh files, and post-processing scripts are stored under version control (Git, internal GitLab server, project `cht-hpt1-cooling`). The simulation database (SIMDB) records the software version, hardware platform (12-node HPC cluster, 384 cores, Intel Xeon Scalable Gen4), and wall-clock run time for each case. A designated simulation data steward (P. Nakamura) is responsible for maintaining archive integrity. Reproduction of any result from archived inputs was verified for one representative case (CHT-2024-0047-C) by a team member not involved in the original run; the reproduced peak metal temperature differed by less than 0.1°C from the archived result, confirming bit-reproducibility.

---

## 8. Applicability of Validation Evidence to the Prediction Context

### 8.1 Conditions Matching

The validation evidence was assessed for its relevance to the actual HPT operating conditions. The Rig 7B benchmark operates at matched Reynolds and Prandtl numbers but at a pressure of 1 atm rather than the engine condition (~18 bar). Compressibility effects are therefore not captured in the validation database. A separate analysis using a 1-D compressible flow model suggests that density ratio effects introduce a systematic shift of approximately +3% in convective coefficient; this correction is applied as a bias adjustment in the production predictions.

The hot-gas temperature in the rig test was 980 K versus the engine condition of approximately 1,750 K. Radiation heat transfer, while included in the rig test correction procedure, contributes less than 2% of total heat load in both environments; its exclusion from the CHT solver is judged acceptable.

### 8.2 Extrapolation Confidence

The prediction domain (engine operating line at take-off, climb, and cruise) partially extrapolates beyond the validated Re range for the internal passages at climb condition (Re_internal ≈ 72,000 versus Rig 7B maximum of 65,000). The extrapolation margin is modest and the trend in Nusselt number with Re is well-established; the simulation plan documents this as an accepted risk with a 10% conservatism margin applied to the coolant-side heat transfer coefficient at climb.

---

## 9. Results Summary and Fitness for Purpose

The CHT simulation suite predicts a peak metal temperature of 1,147°C (normalized: 0.94 T_melt) at take-off conditions, with a 95th percentile upper bound of 1,169°C when input uncertainties are propagated. The life prediction model requires temperatures accurate to ±25°C for acceptable creep life uncertainty; the combined simulation uncertainty of ±22°C (95%) meets this requirement.

Film cooling effectiveness predictions on the pressure side (rows 1–3) are considered adequately validated for the intended purpose. Row 4 (near trailing edge) carries higher uncertainty due to the geometric simplification noted in Section 5.4 and should be treated with caution in the life model.

---

## 10. Limitations and Recommended Future Work

1. **Trailing-edge geometry fidelity:** The current discrete-hole simplification introduces local temperature prediction errors up to 14°C. A higher-fidelity mesh of the trailing-edge slot is recommended for the next design iteration.
2. **Compressibility validation gap:** No high-pressure rig data exist for the internal passages. Acquisition of even a limited dataset at 3–5 bar would substantially reduce extrapolation uncertainty.
3. **Transient effects:** The steady-state assumption is appropriate for cruise but may not capture thermal ratcheting during rapid throttle transients. A transient CHT run for the standard mission cycle is recommended before certification.
4. **Rotating frame effects:** The serpentine channel rotation number (Ro ≈ 0.12 at take-off) is within the range where Coriolis-induced secondary flows affect heat transfer. The current stationary-frame model does not capture this. A sensitivity study using a rotating reference frame is in progress (TFS-CHT-2024-0051).

---

## 11. Overall Assessment

Based on the evidence assembled in this report, the CHT simulation suite for the HPT Stage 1 blade cooling redesign is assessed as **fit for the stated purpose** of coolant flow budgeting and metal temperature boundary condition generation for life prediction, subject to the limitations noted in Section 10. The simulation team has demonstrated appropriate technical depth, followed a structured validation hierarchy, quantified key uncertainties, and subjected the work to independent review. The trailing-edge region predictions carry elevated uncertainty and should be flagged accordingly in the downstream structural analysis.

---

*End of Report TFS-CHT-2024-0047 Rev B*
