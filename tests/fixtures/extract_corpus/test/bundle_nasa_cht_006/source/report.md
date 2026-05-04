# Conjugate Heat Transfer Model Credibility Assessment Report
## Turbine Blade Internal Cooling Channel Simulation — GE9X-Class Geometry

**Document Number:** CHT-VV-2024-047-R2
**Prepared by:** Thermal-Fluid Analysis Group, Propulsion Systems Division
**Review Date:** 14 March 2024
**Classification:** Internal Use — Pre-PDR Distribution

---

## 1. Background and Scope

This report documents the credibility assessment of a conjugate heat transfer (CHT) computational model developed to predict metal temperature distributions and coolant-side heat transfer coefficients within a first-stage turbine blade internal cooling passage. The geometry is representative of a GE9X-class high-pressure turbine blade, featuring a five-pass serpentine channel with trip-strip turbulators and film-cooling extraction holes. The model is implemented in ANSYS Fluent 2023 R2 using the SST k-ω turbulence closure and a coupled wall boundary condition to resolve conduction through the Inconel 718 blade wall.

The intended use of this model is to support thermal margin assessments during preliminary design review (PDR), providing peak metal temperature predictions with an acceptable uncertainty envelope of ±15 K at the 95th percentile. Secondary outputs include spanwise heat flux distributions and coolant pressure drop across the serpentine passage.

This assessment follows the structured credibility framework applicable to engineering simulation models used in safety- and performance-critical applications. Evidence is drawn from verification studies, validation experiments, and supporting documentation generated between October 2023 and February 2024.

---

## 2. Problem Definition and Intended Application Context

### 2.1 Simulation Purpose and Decision Risk

The model outputs directly inform material life calculations for the blade substrate and thermal barrier coating. Overprediction of metal temperature by more than 20 K could result in unconservative life estimates, potentially affecting airworthiness determinations. The consequence of an incorrect design decision is classified as high, given downstream impacts on certification schedules and fleet safety.

The simulation team and the cognizant design authority have jointly documented the decision-support role of this model in a Model Use Agreement (MUA-CHT-2024-03), which defines acceptable prediction intervals and the specific design parameters the model is permitted to inform. This agreement was reviewed by the chief engineer and the independent V&V lead.

### 2.2 Geometry and Operating Conditions

The coolant inlet conditions are specified at Mach 0.12, total temperature 820 K, and a Reynolds number of approximately 42,000 based on hydraulic diameter. The hot-gas-side boundary is applied as a spatially varying heat flux profile derived from a separate CFD combustor/HPT stage analysis (case ID: CFD-HPT-2023-112). Wall roughness on the internal channel is set to 6.3 μm Ra based on measured surface finish data from the manufacturing process specification.

---

## 3. Computational Model Description

The CHT domain is meshed using ANSYS Meshing with a polyhedral-dominant volume mesh and prismatic inflation layers on all wetted and solid surfaces. The solid domain (blade wall) uses a conformal mesh interface with the fluid domain. Total cell count is approximately 14.2 million elements for the full passage model.

The SST k-ω model was selected based on its established performance in internally cooled passage flows with moderate adverse pressure gradients and ribbed geometries, consistent with published benchmark comparisons (Iaccarino et al., 2002; Bunker, 2013). A low-Reynolds-number near-wall treatment is applied with y+ values maintained below 1.2 on all thermally active surfaces.

Steady-state RANS solutions are converged to residuals below 1×10⁻⁵ for all transport equations. Energy equation residuals are additionally monitored using area-averaged heat flux monitors on both the hot-gas and coolant surfaces, with convergence declared when monitor variation is less than 0.05% over 500 iterations.

---

## 4. Code Verification and Numerical Accuracy

### 4.1 Solver Benchmarking

ANSYS Fluent 2023 R2 has been exercised against the NASA Heat Transfer in Turbine Blade Cooling Channels benchmark suite (NASA-TM-2019-220154). For the ribbed duct case (AR=1, e/D=0.1, P/e=10), the solver reproduced Nusselt number distributions within 4.2% of the experimental reference data and within 2.8% of the published DNS dataset. These results are consistent with the solver's documented verification history and provide confidence that the numerical implementation of the governing equations is correct for this class of problem.

Additionally, a method-of-manufactured-solutions (MMS) test was executed on a simplified 2D conjugate slab geometry to confirm second-order spatial accuracy of the energy equation solver. Observed convergence rate was 1.94, consistent with the theoretical expectation.

### 4.2 Mesh Refinement Study

A structured mesh convergence study was conducted using three systematically refined meshes: coarse (4.1M cells), medium (14.2M cells), and fine (38.7M cells). The refinement ratio between successive levels is approximately 1.72 in each spatial direction, consistent with the requirements for a valid Richardson extrapolation.

Key output quantities monitored were: (a) area-averaged Nusselt number on the first-pass trailing wall, (b) total coolant pressure drop, and (c) peak metal temperature at the mid-chord location.

| Mesh Level | Nu (Pass 1, Trail.) | ΔP_total (Pa) | T_metal_peak (K) |
|---|---|---|---|
| Coarse | 284.1 | 4,812 | 1,143.2 |
| Medium | 291.7 | 4,947 | 1,138.6 |
| Fine | 293.4 | 4,971 | 1,137.1 |

Grid Convergence Index (GCI) values computed per Roache (1994): GCI_fine = 1.8% for Nu, 0.9% for ΔP, and 0.6% for peak metal temperature. All values fall within the 5% threshold established in the project V&V plan. The medium mesh (14.2M cells) is selected as the production mesh on the basis of solution accuracy versus computational cost.

---

## 5. Input Characterization and Boundary Condition Uncertainty

### 5.1 Coolant Inlet Conditions

Coolant inlet total temperature and mass flow rate were measured in the rig test campaign (Rig Test Report RTR-CHT-2023-08). The inlet temperature uncertainty is ±3.5 K (k=2), and mass flow rate uncertainty is ±0.8% (k=2), based on calibrated thermocouple and Coriolis flow meter instrumentation. These uncertainties were propagated through the model using a one-at-a-time sensitivity study, yielding a combined contribution of ±4.1 K to peak metal temperature prediction uncertainty.

### 5.2 Hot-Gas-Side Boundary Conditions

The spatially varying heat flux boundary derived from CFD-HPT-2023-112 carries its own epistemic uncertainty, estimated at ±8% in local heat flux magnitude based on comparison of that model with sector combustor rig data. This is the dominant uncertainty contributor to the overall prediction interval and is discussed further in Section 8.

### 5.3 Material Properties

Thermal conductivity and specific heat of Inconel 718 were taken from the ASM Aerospace Specification Metals database, cross-referenced with internal coupon test data (Material Test Report MTR-IN718-2022-04). Temperature-dependent property tables are implemented over the range 400–1300 K. Uncertainty in thermal conductivity is estimated at ±2.5% based on the spread in coupon measurements.

---

## 6. Validation Against Experimental Data

### 6.1 Validation Experiment Description

Validation data were obtained from a dedicated scaled cooling passage rig (scale factor 2.5×) operated at the Propulsion Thermal Laboratory, Building 47. The rig replicates the five-pass serpentine geometry with full trip-strip turbulator features. Liquid crystal thermometry (LCT) was used to obtain spatially resolved surface temperature maps on the pressure-side and suction-side channel walls, with a spatial resolution of approximately 1.5 mm in the scaled geometry (0.6 mm at engine scale).

Thirty-two steady-state test points were acquired across a Reynolds number range of 25,000–65,000, spanning the intended operating envelope. Coolant-to-wall temperature ratios ranged from 0.72 to 0.91.

### 6.2 Comparison Metrics and Results

Nusselt number augmentation ratio (Nu/Nu₀) was selected as the primary validation metric, where Nu₀ is the Dittus-Boelter smooth-tube reference. Comparisons were made at 14 spanwise stations across all five passes.

At the nominal operating condition (Re = 42,000), the model predicts Nu/Nu₀ = 2.41 on the first-pass trailing wall, compared to the experimental value of 2.33 ± 0.09 (k=2). The prediction lies within the experimental uncertainty band. Across all 14 stations, the root-mean-square error between model and experiment is 7.3%, with a maximum local deviation of 14.1% observed near the 180° bend at the first-to-second pass turn. This elevated local error is attributed to the known limitation of RANS closures in capturing the secondary flow structures in sharp U-bends, consistent with published literature.

Coolant pressure drop predictions agree with measurements to within 3.2% at all test points, which is within the experimental uncertainty of ±4.1%.

### 6.3 Validation Coverage and Applicability

The validation dataset spans the full intended Reynolds number operating range. However, the rig operates at a coolant-to-wall temperature ratio up to 0.91, whereas engine conditions may reach 0.78, which is within the tested range. The hot-gas-side boundary condition in the rig is applied as a uniform heat flux rather than the spatially varying profile used in the engine model; this represents a recognized extrapolation that is addressed in the uncertainty quantification (Section 8).

---

## 7. Numerical Uncertainty and Sensitivity Analysis

### 7.1 Turbulence Model Sensitivity

In addition to the baseline SST k-ω model, solutions were obtained with the Realizable k-ε and the v²-f models for three representative operating points. Variation in predicted peak metal temperature across turbulence models was ±9.4 K, which is treated as an additional model-form uncertainty contribution. The SST k-ω model was retained as the baseline based on its superior performance in the ribbed duct benchmark (Section 4.1).

### 7.2 Convergence Monitoring

All production runs demonstrate monotonic residual convergence. Heat flux monitor histories confirm that energy balance closure is achieved to within 0.12% across the conjugate interface, satisfying the project criterion of <0.5%.

---

## 8. Uncertainty Quantification and Prediction Interval

A structured uncertainty budget was assembled combining contributions from: (1) numerical discretization (GCI-based, ±0.6% in peak temperature), (2) input boundary condition uncertainty (±4.1 K from coolant conditions, ±8% local heat flux from hot-gas boundary), (3) material property uncertainty (±2.5% thermal conductivity), (4) turbulence model-form uncertainty (±9.4 K), and (5) validation comparison error at the nominal condition (3.2% in Nu).

The combined prediction uncertainty for peak metal temperature, computed using root-sum-of-squares combination of independent contributors, is ±17.3 K at the 95th percentile confidence level. This marginally exceeds the ±15 K target established in the MUA. The primary driver is the hot-gas-side boundary condition uncertainty, which the team has flagged for reduction through a planned higher-fidelity coupled stage analysis in the next program phase.

---

## 9. Model Pedigree and Prior Use History

The CHT modeling approach employed here is directly derived from the validated framework used in the PW1100G cooling analysis program (internal reference: PW-CHT-VV-2019-031), where the same solver, turbulence model, and meshing strategy were applied to a three-pass cooling geometry. That prior model was validated against engine thermocouple data with a mean absolute error of 11.2 K across 24 blade locations. The current model inherits the validated workflow and adapts it to the GE9X-class geometry, with the specific validation activities described in Section 6 providing geometry-specific evidence.

---

## 10. Software Quality and Configuration Management

ANSYS Fluent 2023 R2 is maintained under the division's software quality management system (SQMS-2024-001). The software version is locked for this program, and all simulation input files, mesh files, and case/data files are archived in the program PDM system (Windchill 12.1, project tree: PRJ-CHT-2024-047). A simulation log capturing solver version, hardware configuration (48-core AMD EPYC 7742 cluster node), and run timestamps is maintained for each production case.

Input deck review was performed by a second analyst (peer check documented in PeerCheck-CHT-2024-047-02), confirming that boundary condition assignments, material property table entries, and turbulence model settings are consistent with the analysis plan.

---

## 11. Reviewer Independence and Qualification

The V&V activities described in this report were conducted by analysts with a minimum of seven years of turbomachinery thermal-fluid simulation experience. The independent review of validation comparisons and uncertainty budgets was performed by Dr. M. Okonkwo (Principal Engineer, Thermal Sciences), who was not involved in the model development activities. Dr. Okonkwo's review findings are documented in Independent Review Record IRR-CHT-2024-047.

The experimental data used for validation were acquired and processed by the Propulsion Thermal Laboratory team, organizationally separate from the simulation group, ensuring independence between the model developers and the validation data providers.

---

## 12. Limitations and Recommended Actions

1. **Hot-gas boundary condition uncertainty** remains the dominant uncertainty contributor, exceeding the ±15 K target. A coupled HPT stage CHT analysis is planned for the CDR phase to reduce this contribution.

2. **U-bend local accuracy**: The 14.1% local error near the first-to-second pass bend is acknowledged. For life calculations sensitive to this region, a conservative local correction factor of +12 K is recommended pending higher-fidelity LES analysis of the bend geometry (planned for Q3 2024).

3. **Film cooling extraction**: The current model does not resolve film-cooling hole flow physics; these are represented as mass sink boundary conditions. This approximation is considered acceptable for bulk thermal margin assessment but should be revisited if local film effectiveness is required.

4. **Transient effects**: The steady-state assumption is appropriate for cruise and climb operating points. Transient thermal analysis for engine start and shutdown cycles is outside the scope of this model and is addressed in a separate analysis (CHT-TRANS-2024-009).

---

## 13. Summary Assessment

The CHT model for the GE9X-class turbine blade internal cooling passage has been assessed across the full range of credibility dimensions relevant to its intended decision-support role. Numerical accuracy is well-characterized through systematic mesh refinement and solver benchmarking. Validation against scaled rig data demonstrates agreement within acceptable bounds across the operating envelope, with identified local limitations at U-bend features. The uncertainty budget is complete and traceable, though the combined prediction interval of ±17.3 K marginally exceeds the program target, with a clear path to reduction identified.

The model is assessed as **suitable for use in PDR-phase thermal margin assessment** with the conservative local correction applied at the first-to-second pass bend region. Continued use at CDR is contingent on completion of the coupled stage analysis to reduce hot-gas boundary condition uncertainty.

---

*Report prepared by: J. Harrington, Senior Thermal Analyst*
*Independently reviewed by: Dr. M. Okonkwo, Principal Engineer*
*Approved for release by: T. Vasquez, Chief Engineer, Propulsion Systems*
