# Credibility Assessment Report
## Turbomachinery Stage CFD Analysis — Centrifugal Pump Internal Flow
### Project: Meridional Passage Flow Simulation for Model 7-XR Pump
**Document Number:** VA-CFD-2024-047-R2
**Prepared by:** Computational Methods Group, Applied Fluid Systems Division
**Review Date:** 14 March 2024
**Classification:** Internal Use — Distribution List B

---

## 1. Background and Purpose

This report documents the credibility assessment of a Reynolds-Averaged Navier–Stokes (RANS) simulation campaign conducted to predict hydraulic performance, internal velocity distributions, and pressure recovery characteristics within the Model 7-XR single-stage centrifugal pump. The computational effort was commissioned to support impeller redesign decisions ahead of a scheduled prototype build in Q3 2024.

The pump operates at a design flow rate of 142 L/min against a 28 m head rise, with a specific speed (N_s) of approximately 1,850 rpm·(L/min)^0.5/m^0.75. Inlet conditions are cold water at 20 °C, with a suction-side absolute pressure of 1.4 bar. The simulation domain spans the full impeller passage (six blades, one passage modeled with periodic boundaries), the diffuser vane region, and a simplified volute representation.

The purpose of this assessment is to evaluate the degree of confidence that can be placed in the simulation outputs for engineering decision-making, and to identify areas where additional work would materially improve that confidence. The framework applied draws on established V&V principles for computational simulations used in safety-relevant engineering contexts.

---

## 2. Simulation Description

### 2.1 Solver and Physical Models

All computations were performed using ANSYS Fluent 2023 R2. Turbulence closure was achieved using the SST k-ω model with curvature correction enabled, selected based on prior internal benchmarking against impeller passage flows showing superior pressure gradient prediction relative to standard k-ε variants. Wall treatment used the automatic near-wall blending function; target y+ values were maintained below 1.5 on blade surfaces and below 5 on hub/shroud surfaces.

Steady-state Multiple Reference Frame (MRF) formulation was used for the rotating domain. Fluid properties were treated as incompressible with constant density (998.2 kg/m³) and dynamic viscosity (1.003 × 10⁻³ Pa·s). Cavitation modeling was not activated for this campaign.

### 2.2 Geometry and Meshing

Geometry was imported from the CAD model (SolidWorks 2023, file revision C4) and processed in ANSYS SpaceClaim. Minor fillets below 0.3 mm radius were suppressed following a sensitivity check confirming negligible influence on passage-averaged quantities. The mesh was generated in ANSYS Meshing with a predominantly hexahedral core and prismatic boundary layer inflation on all wetted surfaces.

### 2.3 Boundary Conditions

Inlet: mass flow rate specified (2.366 kg/s, corresponding to design point). Turbulence intensity set to 5% with a hydraulic diameter-based length scale.
Outlet: static pressure boundary (atmospheric reference, 0 Pa gauge at volute exit).
Walls: no-slip, hydraulically smooth.
Periodic interfaces: rotational periodicity with 60° sector.

---

## 3. Solution Quality and Numerical Integrity

### 3.1 Residual Convergence and Monitor Points

All six governing equation residuals (continuity, three momentum components, k, ω) were driven below 1 × 10⁻⁵ (scaled residuals) before solutions were accepted. In addition to residual monitoring, surface-averaged total pressure at the impeller exit plane and shaft torque were tracked as functional monitors; both stabilized to within 0.05% variation over the final 300 iterations. This dual-criterion approach was adopted because residual norms alone have been observed in prior work to give false convergence signals in rotating machinery problems.

### 3.2 Mesh Refinement Study

A structured mesh refinement study was conducted using three systematically refined grids:

| Grid Level | Cell Count | Head Rise (m) | Shaft Power (W) |
|------------|-----------|---------------|-----------------|
| Coarse (G3) | 1.21 × 10⁶ | 29.14 | 1,087 |
| Medium (G2) | 4.87 × 10⁶ | 28.61 | 1,063 |
| Fine (G1)   | 19.5 × 10⁶ | 28.43 | 1,057 |

Grid refinement ratios were approximately 1.6 in each spatial direction (volumetric ratio ~4:1 between successive levels). The Grid Convergence Index (GCI) was computed following the Celik et al. (2008) procedure. For head rise, GCI_fine = 0.72%, indicating the fine-grid solution is well within the asymptotic convergence regime (apparent order p = 2.11, theoretical order for second-order scheme = 2.0). For shaft power, GCI_fine = 0.43%. The medium grid (G2) was selected for the production runs as it provides GCI values below 1.5% at substantially reduced computational cost. No Richardson extrapolation correction was applied to the reported results; the raw G2 values are used, with the GCI bounds treated as numerical uncertainty.

---

## 4. Physical Modeling Fidelity

### 4.1 Applicability of the Turbulence Model

The SST k-ω model is well-established for attached boundary layer flows with mild adverse pressure gradients. However, the 7-XR passage exhibits a region of incipient separation on the suction surface near the trailing edge at off-design conditions (±15% of design flow). At these operating points, the RANS closure is expected to underpredict separation extent. A supplementary LES simulation was not conducted in this campaign due to computational budget constraints, but is recommended prior to any off-design structural loading assessment. For the design-point predictions that form the basis of this report, the SST model's applicability is judged adequate based on the benchmark data described in Section 5.

The curvature correction coefficient C_cc was left at its default value of 1.0. Sensitivity runs varying C_cc between 0.8 and 1.2 showed less than 0.4% variation in head rise prediction, confirming low sensitivity to this parameter at the design point.

### 4.2 Geometric Fidelity and Simplifications

The volute geometry was simplified from the full spiral casing to a constant-area annular exit section. This simplification was validated in a prior study (internal report VA-CFD-2022-031) showing less than 1.8% deviation in impeller exit total pressure when comparing simplified versus full-volute representations at design flow. The simplification is considered acceptable for the current scope, which focuses on impeller passage aerodynamics rather than volute pressure recovery.

---

## 5. Validation Against Experimental Data

### 5.1 Test Data Provenance and Traceability

Experimental data were obtained from a dedicated hydraulic performance test conducted at the company's ISO 9906:2012-compliant test rig (Facility TF-3, calibration certificate CC-2024-017, valid through December 2024). Instrumentation included:

- Differential pressure transducer (Rosemount 3051, ±0.065% of span, calibrated February 2024)
- Electromagnetic flowmeter (Krohne OPTIFLUX 4000, ±0.3% of reading)
- Torque meter (HBM T40B, ±0.1% of nominal)
- Inlet/outlet static pressure taps (4-tap averaging rings, machined to ±0.02 mm positional tolerance)

All instruments were calibrated traceable to national standards (PTB-traceable reference standards). Measurement uncertainty was formally propagated using the GUM framework; combined expanded uncertainty (k=2) on hydraulic efficiency was ±1.1 percentage points.

### 5.2 Comparison of Simulation to Experiment

At the design operating point (Q = 142 L/min, N = 2,900 rpm):

| Quantity | Experiment | CFD (G2) | Deviation |
|----------|-----------|----------|-----------|
| Head Rise (m) | 28.1 ± 0.4 | 28.61 | +1.8% |
| Shaft Power (W) | 1,041 ± 12 | 1,063 | +2.1% |
| Hydraulic Efficiency (%) | 74.8 ± 1.1 | 75.2 | +0.4 pp |

The CFD head rise prediction falls within 1.8% of the experimental value. Given the experimental uncertainty of ±1.4% (k=2) on head rise and the numerical uncertainty (GCI) of ±1.5%, the simulation and experiment are considered in agreement within combined uncertainty bounds. This validation was performed at a single operating point (design flow); validation at off-design conditions is deferred.

Internal velocity profiles were compared to 5-hole probe traverse data acquired at the impeller exit plane (r/r_tip = 1.02). Circumferentially averaged radial and tangential velocity components agreed within 4.5% RMS across the blade-to-blade pitch, with the largest discrepancies occurring near the shroud wall where secondary flow effects are most pronounced.

### 5.3 Validation Domain and Extrapolation Risk

The validation evidence is directly applicable to the design-point operating condition, same fluid, same rotational speed, and same geometry. The intended use of the simulation outputs includes off-design performance prediction at ±20% flow deviation. This extrapolation beyond the validated envelope carries additional uncertainty that has not been quantified in this campaign. Users of the simulation results for off-design decisions should apply a conservative uncertainty margin of at least ±5% on predicted head values, pending additional validation work.

---

## 6. Software and Process Integrity

### 6.1 Solver Verification Status

ANSYS Fluent 2023 R2 is a commercially distributed solver with an established verification and validation record. The vendor publishes verification test cases (ANSYS Fluent Verification Manual, Release 2023 R2) covering manufactured solution tests for the governing equations, including the incompressible Navier–Stokes system and the SST k-ω turbulence model. Internal re-execution of three vendor verification cases (lid-driven cavity Re=1000, backward-facing step, and rotating channel flow) confirmed expected second-order spatial accuracy and agreement with published benchmark solutions to within stated tolerances. No modifications to solver source code were made; the standard licensed executable was used throughout.

Simulation workflow scripts (Python-based journal files for geometry processing, meshing parameter application, and post-processing) were maintained under version control (Git, repository CFD-7XR-v2). A dedicated test suite of 12 regression checks was run against a reference solution archive before each production run batch to detect inadvertent workflow changes. All 12 checks passed for the production runs documented here.

### 6.2 Input Data Traceability

All boundary condition inputs were drawn from the pump design specification document DS-7XR-Rev4, with explicit cross-references logged in the simulation setup record (SSR-CFD-2024-047). Fluid property data were sourced from NIST WebBook (accessed 12 January 2024, documented in SSR). No manual transcription of values was performed; all numerical inputs were populated via parameterized input files to eliminate transcription error risk.

---

## 7. Analyst Qualifications and Independent Review

### 7.1 Team Competency

The lead analyst (Dr. A. Müller) holds a PhD in turbomachinery fluid mechanics and has eight years of post-doctoral experience in industrial CFD for rotating machinery. Two supporting analysts (M. Sc. level) with three and five years of relevant experience respectively contributed to mesh generation and post-processing. All three analysts have completed the company's internal CFD qualification program (QP-CFD-2022), which includes proficiency assessment in turbulence model selection, mesh quality evaluation, and uncertainty quantification.

### 7.2 Independent Technical Review

An independent review of the simulation setup, mesh quality, and results interpretation was conducted by a senior engineer from the Aerodynamics Methods group (Dr. F. Okafor), who was not involved in the original simulation work. The review covered: boundary condition appropriateness, turbulence model selection rationale, GCI calculation methodology, and comparison to experimental data. Dr. Okafor's review comments (Review Record RR-2024-047) were addressed in revision R2 of this report; three minor corrections to the GCI table and one clarification to the validation comparison methodology were incorporated. The reviewer confirmed no outstanding concerns.

---

## 8. Uncertainty Summary and Confidence Assessment

The table below summarizes the primary uncertainty contributions to the head rise prediction at design point:

| Source | Estimated Contribution |
|--------|----------------------|
| Numerical discretization (GCI, G2) | ±1.5% |
| Turbulence model form error (design point) | ±2–3% (judgment) |
| Geometric simplification (volute) | ±1.8% (prior study) |
| Boundary condition specification | <0.5% (sensitivity tested) |
| **Combined (RSS)** | **±3.0–3.9%** |

The experimental validation data shows the simulation lies within this combined uncertainty band. For the specific intended use — comparing impeller design variants at design-point conditions — the simulation is judged to provide sufficient fidelity for relative ranking of designs. Absolute performance predictions should be used with the uncertainty bounds stated above.

---

## 9. Limitations and Recommended Future Work

1. **Off-design validation:** The current validation evidence covers only the design operating point. Validation at minimum flow (Q_min = 85 L/min) and maximum continuous flow (Q_max = 170 L/min) is recommended before using CFD for off-design design decisions.

2. **Transient effects:** The MRF steady-state approach does not capture rotor-stator interaction unsteadiness. For noise and vibration assessments, a sliding mesh transient simulation would be required.

3. **LES at separation-prone conditions:** As noted in Section 4.1, RANS limitations at off-design conditions with significant separation are not fully characterized. A targeted LES study at the minimum flow condition is recommended.

4. **Volute representation:** The annular exit simplification should be revisited if volute pressure recovery becomes a design driver.

5. **Cavitation:** The current campaign does not address cavitation inception. A separate CFD campaign with the full cavitation model is required if NPSH margin is to be assessed computationally.

---

## 10. Conclusions

The CFD simulation of the Model 7-XR centrifugal pump impeller passage has been conducted with appropriate rigor for the intended design-point application. Mesh convergence has been formally demonstrated with GCI values below 1.5% on key outputs. Experimental validation shows agreement within combined uncertainty bounds at the design operating point, with calibrated, traceable instrumentation. The solver has been independently verified, workflow integrity is maintained under version control with regression testing, and the analyst team has documented competency. An independent technical review has been completed with all comments resolved.

The simulation outputs are assessed as suitable for supporting impeller design variant comparisons at the design operating point. Extension of this confidence to off-design conditions requires the additional validation work identified above.

---

*End of Report VA-CFD-2024-047-R2*
