# Conjugate Heat Transfer Model Credibility Assessment Report
## Turbine Blade Internal Cooling Channel Simulation — Phase 2 Review

**Document Number:** TBC-CHT-VV-2024-017
**Prepared by:** Thermal Analysis Group, Propulsion Systems Division
**Review Date:** 14 March 2024
**Model Version:** BLADE-CHT-v3.2 (ANSYS Fluent 2023 R2)
**Status:** Draft — Internal Review Only

---

## 1. Background and Scope

This report documents the credibility assessment activities completed for the coupled thermal-fluid simulation of a high-pressure turbine blade internal cooling network. The model, designated BLADE-CHT-v3.2, was developed to predict metal temperature distributions and coolant-side heat transfer coefficients within a five-pass serpentine cooling channel geometry representative of a Stage 1 HPT blade operating at take-off conditions.

The simulation couples a steady-state Reynolds-Averaged Navier-Stokes (RANS) fluid solver with a solid-domain conduction model, exchanging heat flux and wall temperature across the fluid-solid interface at each outer iteration. The primary quantities of interest (QoIs) are:

- Peak metal temperature at the leading edge insert
- Spanwise-averaged Nusselt number distribution along the pressure-side cooling passage
- Thermal gradient across the blade wall at the mid-chord location

The assessment draws on AIAA/ASME best-practice guidelines for thermal simulation credibility and follows the general vv40 framework structure adopted by the program office. This Phase 2 review covers model development through preliminary design; certain assessment activities have been explicitly deferred to Phase 3 and are noted where applicable.

---

## 2. Computational Model Description

The fluid domain encompasses the full five-pass serpentine channel including inlet plenum, turn regions, and film-cooling extraction holes (modeled as mass-flow boundary conditions). The solid domain represents the blade wall, insert, and impingement sleeve as a single conjugate body. Mesh generation was performed in ANSYS Meshing with polyhedral cells in the fluid domain and hexahedral elements in the solid. The baseline mesh contains approximately 14.2 million fluid cells and 2.1 million solid elements.

Turbulence closure is provided by the SST k-ω model with low-Reynolds-number near-wall treatment; y⁺ values were maintained below 1.0 across all solid-fluid interfaces. Inlet boundary conditions were derived from rig test data collected at the Aero-Thermal Test Facility (ATTF) in September 2023, with coolant total pressure of 42.3 bar and total temperature of 688 K.

---

## 3. Code Verification Activities

Prior to application-specific validation, the Fluent 2023 R2 solver was subjected to a series of benchmark exercises to confirm correct numerical implementation of the conjugate coupling algorithm.

A steady laminar channel flow with prescribed wall heat flux was compared against the analytical Graetz solution; the computed Nusselt number at the thermally developing entry length agreed to within 0.4% of the closed-form result. A second benchmark involving a 2D fin array was compared against the NACA TN-3208 reference solution; peak fin-tip temperature deviated by less than 0.8 K across all tested Biot number conditions (Bi = 0.1 to 5.0).

These exercises confirm that the solver correctly implements the governing energy equations and that the conjugate interface coupling does not introduce spurious heat flux imbalances. Residual convergence was monitored; energy equation residuals were reduced by at least six orders of magnitude in all benchmark cases. The code-level verification package is archived in project repository TBC-REPO/VV/code-bench/.

---

## 4. Solution Verification — Mesh Refinement Study

A systematic mesh refinement study was performed on a representative two-pass section of the cooling channel to assess numerical discretization sensitivity. Three mesh levels were generated at refinement ratios of approximately √2 in each spatial direction:

| Mesh Level | Fluid Cells | Peak Wall Temp (K) | ΔT from Fine |
|------------|-------------|---------------------|--------------|
| Coarse     | 1.8 M       | 1,247.3             | +18.1 K      |
| Medium     | 5.6 M       | 1,234.8             | +5.6 K       |
| Fine       | 14.2 M      | 1,229.2             | —            |

Richardson extrapolation was applied to the peak wall temperature QoI, yielding an apparent order of convergence of p = 1.87 (expected ~2 for the second-order scheme). The Grid Convergence Index (GCI) for the fine-to-medium transition is 0.7%, which falls within the program-defined acceptability threshold of ±1.5% for thermal QoIs. Iterative convergence was confirmed by running each mesh to 5,000 additional iterations beyond the apparent steady state; QoI variation over the final 1,000 iterations was less than 0.05 K.

The medium mesh (5.6 M cells) was identified as the production mesh for parametric studies, balancing numerical accuracy and computational cost.

---

## 5. Experimental Data and Validation Basis

### 5.1 Test Data Pedigree and Uncertainty

Validation data were obtained from the ATTF Rig-7 test campaign (September–October 2023). The rig replicates the five-pass cooling geometry at 1:1 scale using a low-conductivity Macor ceramic blade insert to achieve engine-representative Biot numbers. Coolant-side heat transfer coefficients were inferred from transient thermochromic liquid crystal (TLC) measurements on the passage walls.

Measurement uncertainty analysis was performed by the ATTF instrumentation team. Expanded uncertainty (k=2) for the inferred heat transfer coefficient is ±8.3% at 95% confidence, driven primarily by the TLC calibration uncertainty (±1.1°C) and the transient data reduction model. Coolant inlet temperature uncertainty is ±0.4 K; pressure uncertainty is ±0.15%.

The test data pedigree was reviewed and assessed as adequate for primary validation use. Raw data, calibration records, and reduction scripts are archived in TBC-REPO/TEST/ATTF-Rig7/.

### 5.2 Validation Comparison

Spanwise-averaged Nusselt number distributions from the simulation and experiment are compared across all five passes. Agreement statistics:

- Passes 1–3 (straight sections): Mean absolute error = 6.2%, maximum local deviation = 11.4%
- Passes 4–5 (turn-exit regions): Mean absolute error = 14.7%, maximum local deviation = 22.1%

The elevated discrepancy in the turn-exit regions is attributed to the known limitations of the SST k-ω model in capturing streamline curvature effects and secondary flow reattachment. This finding is consistent with published literature (e.g., Bunker, 2009; Han et al., 2012) and has been flagged as a model-form uncertainty contributor. A sensitivity study using the realizable k-ε model showed modest improvement in turn-exit regions (+3.1 pp) but degraded performance in straight passages (−4.8 pp); SST k-ω was retained as the production turbulence closure.

Peak metal temperature prediction: simulation gives 1,229 K versus thermocouple measurement of 1,241 K (−12 K, −1.0%). This falls within the combined experimental and numerical uncertainty envelope.

---

## 6. Uncertainty Characterization

### 6.1 Input Parameter Sensitivity

A one-at-a-time (OAT) sensitivity study was conducted on the following boundary condition inputs:

| Parameter | Nominal | ±Variation | ΔPeak T (K) |
|-----------|---------|------------|-------------|
| Coolant inlet total pressure | 42.3 bar | ±0.15% | ±1.8 K |
| Coolant inlet total temperature | 688 K | ±0.4 K | ±0.4 K |
| Blade wall thermal conductivity (MAR-M247) | 14.2 W/m·K | ±5% | ±6.1 K |
| Film hole discharge coefficient | 0.72 | ±10% | ±4.3 K |

Blade wall thermal conductivity is the dominant input uncertainty contributor to peak metal temperature. The material property data used (MAR-M247 at 1,100–1,300 K) were sourced from the program material database (TBC-MAT-DB Rev. 4); independent verification of these values against published Ni-superalloy data (Touloukian, 1970) showed agreement within 3%.

### 6.2 Model-Form Uncertainty

As noted in §5.2, turbulence model-form uncertainty is the largest single uncertainty source for heat transfer coefficient prediction in the turn regions. A quantitative bound of ±15% on Nu in turn-exit regions was assigned based on the multi-model comparison. This bound has been propagated to the peak metal temperature QoI, contributing approximately ±18 K.

A formal total uncertainty budget combining input, numerical (GCI-based), and model-form contributions yields an expanded uncertainty of ±22 K on peak metal temperature at 95% confidence. The program requirement for this QoI is that predicted peak temperature shall not exceed the material capability limit with a margin of at least 30 K; the current prediction of 1,229 K against a capability limit of 1,310 K provides a nominal margin of 81 K, which exceeds the requirement even under the full uncertainty envelope (1,229 + 22 = 1,251 K < 1,310 K).

---

## 7. Applicability of Validation Data to Simulation Conditions

The ATTF Rig-7 test conditions were designed to match engine Reynolds number and Biot number simultaneously. However, the rig operates at sub-atmospheric coolant pressure (0.8–1.2 bar) compared to the engine condition of 42.3 bar. The validation team has assessed that the relevant non-dimensional groups (Re, Bi, Nu) are preserved to within 4% across the operating range, and that compressibility effects at the engine pressure condition are negligible for this internal cooling application (Mach < 0.08 throughout).

One area of concern is the absence of rotation effects in the rig. The HPT blade operates at 12,400 rpm, inducing Coriolis and centrifugal buoyancy forces that are known to alter heat transfer in radial cooling passages (rotation number Ro ≈ 0.18 at engine conditions). The current simulation does not include rotational body forces, and no rotating rig data are available for this geometry at this phase. This represents a recognized limitation and is **deferred to Phase 3**, where a rotating rig campaign is planned at the Oxford Osney Thermofluids Laboratory.

---

## 8. Intended Use and Fitness for Purpose

The BLADE-CHT-v3.2 model is intended for use in preliminary design decisions regarding cooling passage geometry and inlet flow splits. It is **not** cleared for final lifing calculations or certification-basis thermal predictions, which require the Phase 3 rotating validation data and a full probabilistic uncertainty quantification (UQ) study.

Within its intended scope, the model is judged adequate for:
- Comparative evaluation of passage geometry variants (relative ranking)
- Identification of high-temperature risk regions requiring design attention
- Boundary condition sensitivity screening

The model should not be used to predict absolute metal temperatures in the turn regions with better than ±20 K confidence, nor to support film-cooling effectiveness predictions (film hole modeling fidelity has not been separately validated).

---

## 9. Limitations and Deferred Activities

The following items are explicitly out of scope for this Phase 2 assessment and will be addressed in subsequent reviews:

1. **Rotating effects validation** — deferred to Phase 3 (rotating rig campaign, Q3 2024)
2. **Probabilistic UQ / Monte Carlo propagation** — deferred pending Phase 3 data
3. **Transient thermal cycling analysis** — not required at preliminary design; deferred to detailed design phase
4. **External hot-gas-side boundary condition coupling** — current model uses prescribed external HTC map from a separate CFD analysis; fully coupled external-internal CHT is planned for Phase 3

Note: Assessment of the model development process and team review documentation (including peer review sign-off records) was not completed within the Phase 2 timeline due to competing program milestones. These process-level records will be compiled and reviewed as part of the Phase 3 credibility package.

---

## 10. Summary Assessment

| Assessment Area | Finding | Confidence |
|----------------|---------|------------|
| Code-level verification (benchmark tests) | Satisfactory — analytical agreement <1% | High |
| Mesh refinement / discretization sensitivity | GCI = 0.7%, within threshold | High |
| Experimental data quality and uncertainty | Adequate; ±8.3% on HTC | Moderate-High |
| Validation comparison (straight passages) | MAE = 6.2%, within uncertainty | Moderate |
| Validation comparison (turn regions) | MAE = 14.7%; turbulence model limitation identified | Moderate-Low |
| Input uncertainty characterization | OAT study complete; conductivity dominant | Moderate |
| Total uncertainty budget (peak metal temp) | ±22 K; margin requirement met | Moderate |
| Applicability to engine conditions (non-rotating) | Non-dimensional matching adequate | Moderate |
| Rotation effects | Not assessed — deferred | Not assessed |

The model is recommended for release at **Credibility Level 2** (suitable for design guidance and comparative analysis) pending program office concurrence. Advancement to Level 3 (suitable for design verification) is contingent on completion of Phase 3 rotating validation activities and the process documentation review noted in §9.

---

*Prepared by:* Dr. S. Marchetti, Senior Thermal Analyst
*Reviewed by:* T. Okonkwo, Lead V&V Engineer (pending)
*Approved by:* — (pending program office sign-off)
