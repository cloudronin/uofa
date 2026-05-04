# Credibility Assessment Report
## CFD Analysis of Centrifugal Pump Internal Flow — HVAC Recirculation Loop
### Project: Meridian-7 Building Services Pump Platform
### Report Revision: B | Review Cycle: PDR-2

---

## 1. Background and Scope

This report documents the credibility evaluation of computational fluid dynamics simulations performed in support of the Meridian-7 centrifugal pump development program. The simulations were executed using ANSYS Fluent 2023 R1 to characterize internal hydraulic performance across a range of operating conditions, with particular focus on head-flow curve prediction, efficiency at the best-efficiency point (BEP), and recirculation onset at low-flow conditions.

The pump geometry features a six-blade backward-swept impeller (outer diameter 312 mm), a volute casing with a single cutwater, and an axial inlet with a 90° elbow upstream. Operating conditions span 60–140% of BEP flow rate, with the nominal duty point at Q = 48 m³/hr, H = 22.4 m, at 1450 RPM. Working fluid is water at 20°C.

The scope of this credibility assessment is limited to the hydraulic performance predictions used for pump curve certification. Structural integrity analysis (FEA of the impeller) and acoustic predictions are explicitly deferred to the next design phase and are not addressed here.

---

## 2. Intended Use and Decision Context

The simulation outputs will be used to:
1. Select the final impeller blade angle prior to tooling release
2. Predict off-design performance margins to satisfy EN 809 compliance requirements
3. Reduce the number of physical prototype test iterations from three to one

The decision risk is moderate. An over-predicted head curve could result in a pump that fails factory acceptance testing, requiring costly impeller re-machining. Under-prediction carries lower commercial risk but could result in over-designed motor selection. The simulation team and the program chief engineer have agreed that predictions within ±5% of measured head at BEP constitute an acceptable outcome for tooling release decisions.

---

## 3. Model Description and Governing Physics

The simulation employs a steady-state, incompressible RANS formulation. Turbulence closure is achieved using the SST k-ω model, selected on the basis of its established performance in rotating machinery flows with moderate adverse pressure gradients. Wall treatment uses the automatic near-wall function blending available in Fluent, with target y⁺ values in the range 30–100 on impeller blade surfaces.

The rotating reference frame (MRF) approach is used to couple the rotating impeller domain with the stationary volute. This is a known simplification relative to a sliding mesh (transient) approach; the implications are discussed in Section 6.

Fluid properties are specified as constant-density water (ρ = 998.2 kg/m³, μ = 1.003×10⁻³ Pa·s). Cavitation modeling is not activated; the analysis assumes sufficient NPSH margin throughout the operating range.

---

## 4. Geometry and Boundary Condition Fidelity

The CAD geometry imported into ANSYS SpaceClaim was sourced directly from the released Meridian-7 impeller drawing set (rev. D4, dated 2024-03-11). The volute geometry was reconstructed from a combination of the casting drawing and a structured point cloud obtained from a coordinate-measuring machine (CMM) scan of the pattern tool. Differences between the nominal CAD and the CMM-derived surface were less than 0.4 mm across 94% of the volute wetted area, which the team judged acceptable given the overall hydraulic passage dimensions.

Inlet boundary conditions are specified as a uniform velocity profile at a plane located 3.5 diameters upstream of the impeller eye, with turbulence intensity set to 5% and a hydraulic diameter length scale. The outlet is a pressure-outlet condition at the volute discharge flange. No attempt has been made to characterize the actual upstream piping velocity profile in the test rig; this is noted as a limitation (see Section 6).

Shaft seal leakage paths and wear-ring clearance flows are not modeled. Based on published correlations for this pump size class, the omitted leakage is estimated to represent less than 1.2% of total flow, which falls within the stated prediction tolerance.

---

## 5. Mesh Refinement Study and Numerical Error Estimation

A systematic grid refinement study was completed using three mesh levels:

| Mesh Level | Total Cell Count | Impeller Cells | Volute Cells |
|------------|-----------------|----------------|--------------|
| Coarse     | 2.1 M           | 1.4 M          | 0.7 M        |
| Medium     | 5.8 M           | 3.9 M          | 1.9 M        |
| Fine       | 14.6 M          | 9.7 M          | 4.9 M        |

All meshes were generated using ANSYS Meshing with polyhedral cells in the volute and structured hexahedral cells in the impeller passages. The refinement ratio between successive levels is approximately 1.36 on a per-dimension basis (volumetric ratio ≈ 2.5×).

The Grid Convergence Index (GCI) methodology (Roache, 1994; Celik et al., 2008) was applied to the predicted total head at BEP. The observed order of convergence, p, was computed as 1.87, which is consistent with the nominally second-order spatial discretization scheme used (second-order upwind for momentum and turbulence quantities). The fine-grid GCI for head prediction is 1.3%, indicating that the fine mesh solution is well within the asymptotic convergence regime.

Residuals for all transport equations were converged to below 10⁻⁵ (mass imbalance below 10⁻⁶) at each operating point. Torque and total head were monitored as solution progress indicators; both stabilized to within 0.05% variation over the final 500 iterations.

The fine mesh (14.6 M cells) was selected for all production runs.

---

## 6. Comparison Against Physical Test Data

### 6.1 Test Facility Description

Factory acceptance testing was conducted on the Meridian-7 prototype at the hydraulic test rig operated by the pump manufacturer (facility designation: HTR-02). The rig is instrumented with a calibrated electromagnetic flowmeter (±0.3% of reading), differential pressure transducers across suction and discharge flanges (±0.15% full scale), and a torque flange on the motor shaft (±0.2% of reading). Speed is controlled and measured via a variable-frequency drive with encoder feedback. The test was witnessed by a third-party inspector and conducted in accordance with ISO 9906 Grade 2 tolerances.

### 6.2 Head-Flow Curve Comparison

Simulation predictions and test measurements are compared at seven operating points spanning 60% to 130% of BEP flow.

At the BEP (Q = 48 m³/hr), the CFD-predicted head is 22.1 m versus the measured 22.6 m — a deviation of −2.2%, which is within the stated ±5% acceptance criterion. Across all operating points, the mean absolute error in head prediction is 2.8%, with the largest deviation occurring at 65% BEP flow (−4.9%), where recirculation onset introduces unsteady flow features that the steady-state MRF approach does not fully resolve.

Efficiency predictions show a systematic under-prediction of approximately 1.5–2.0 percentage points across the operating range. The team attributes this primarily to the omission of disk friction losses and mechanical seal drag in the CFD model, consistent with published correction factors for pumps in this specific speed range (Ns ≈ 35 in SI units).

### 6.3 Uncertainty and Sensitivity

A brief sensitivity study was performed by varying inlet turbulence intensity between 2% and 10%. Head predictions varied by less than 0.4% across this range, confirming low sensitivity to this uncertain boundary condition parameter. No formal uncertainty propagation through the full simulation chain has been completed for this review cycle; this is deferred to the next milestone.

---

## 7. Software Verification Status

ANSYS Fluent 2023 R1 is a commercially available solver with an established history of use in rotating machinery applications. The software vendor publishes verification test cases in the Fluent Theory Guide and Verification Manual (ANSYS, 2023), covering canonical flows including rotating channel flow, backward-facing step, and turbulent pipe flow. Internal QA records confirm that the version of Fluent used here passed all vendor-supplied regression tests at the time of installation on the project HPC cluster.

The project team did not perform independent verification of the solver against analytical solutions for this specific problem class; reliance is placed on the vendor's published verification suite. This represents a pragmatic decision given schedule constraints and is consistent with practice for commercial CFD codes in industrial pump applications.

---

## 8. Reviewer Qualifications and Process

The simulation was executed by a CFD engineer with seven years of experience in turbomachinery flow analysis, holding a master's degree in mechanical engineering with a thesis on impeller-volute interaction. An independent technical review of the simulation setup, mesh quality metrics, and results interpretation was conducted by a senior engineer from a separate business unit who was not involved in the original analysis. The review covered boundary condition selection, turbulence model justification, and GCI calculation methodology.

No formal review of the post-processing scripts or data reduction procedures was performed within this cycle; this is identified as a gap to be addressed before final report release.

---

## 9. Limitations and Items Deferred

The following limitations are acknowledged:

1. **MRF vs. sliding mesh:** The steady-state MRF approach introduces modeling error at off-design conditions, particularly at low-flow where impeller-volute interaction is significant. A transient sliding-mesh study is planned for Phase 2 if prototype testing reveals unacceptable discrepancy at part-load.

2. **Upstream piping profile:** The actual test rig inlet condition includes a 90° elbow located approximately 2.8 diameters upstream of the impeller eye. The CFD model uses a uniform inlet profile. This is expected to influence predicted swirl and incidence at the impeller leading edge, particularly at off-BEP conditions.

3. **Thermal effects:** All simulations assume isothermal operation. For HVAC applications where supply water temperature may vary between 6°C and 45°C, fluid property variation could affect predictions by up to 3% in viscous losses. This is not assessed here.

4. **Uncertainty quantification framework:** A comprehensive UQ analysis propagating geometric tolerances, boundary condition uncertainty, and turbulence model-form uncertainty through to output quantities of interest has not been completed. The sensitivity study in §6.3 provides partial coverage only.

5. **Configuration management of simulation inputs:** Input files (mesh, case files, boundary condition tables) are stored on the project SharePoint in a folder structure maintained by the lead CFD engineer. No formal version-control system (e.g., Git) is in use. File provenance can be traced through naming conventions and a manually maintained log, but this is acknowledged as a process gap relative to best practices.

---

## 10. Summary Assessment

The CFD analysis of the Meridian-7 pump internal flow has been conducted with a level of rigor appropriate to the program phase and decision context. The mesh refinement study demonstrates numerical convergence to within GCI of 1.3%, and comparison against factory acceptance test data shows head prediction within ±5% across the primary operating range.

Key strengths of the simulation activity include: systematic GCI-based error estimation, use of production-quality geometry from released drawings, independent technical review of the simulation setup, and direct comparison against witnessed ISO 9906 test data.

Key gaps that limit confidence include: absence of a formal uncertainty propagation framework, reliance on vendor verification rather than independent code verification for this problem class, omission of disk friction and leakage paths, and informal configuration management of simulation files.

The simulation outputs are judged **sufficient to support the impeller blade angle selection decision** at this program stage, with the understanding that a transient sliding-mesh analysis and formal uncertainty quantification will be required before the simulation is used for any regulatory submission or extended off-design performance guarantee.

---

*Report prepared by: CFD Analysis Group, Meridian Platform Engineering*
*Review completed: 2024-05-14*
*Distribution: Program Chief Engineer, Hydraulic Design Lead, Quality Assurance*
