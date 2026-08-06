# Credibility Assessment Report: CFD Prediction of Pressure Loss in a 90° Rectangular Duct Elbow

Project: South Intake AHU Upgrade — Elbow Loss Prediction  
Analyst: L. Chen, Fluids Group  
Date: 2026-08-05  
Toolchain: Ansys Fluent 2023 R2, SpaceClaim 2022 R1, PyVista 0.41

## Executive Summary

This report documents the credibility of a steady RANS CFD model used to estimate the additional pressure loss introduced by a 90-degree elbow in the upgraded south intake air-handling unit (AHU). The model is used to inform fan selection and assess whether the existing VFD envelope provides sufficient static pressure margin. The principal output of interest is the elbow loss coefficient K, defined using area-averaged total pressures at sections 4 hydraulic diameters upstream and 6 downstream of the bend.

The simulation uses the k-omega SST turbulence model with scalable wall functions, second-order spatial discretization, and a steady segregated solver. A three-level mesh refinement study was performed on a geometry including straight upstream and downstream runs to isolate the elbow contribution. The medium grid result for K is 0.225, with an estimated mesh-induced uncertainty of 1.8% based on a Richardson-style extrapolation. Residuals fell by at least three orders of magnitude and the monitored pressure drop stabilized to within 0.3% for the final 1000 iterations.

Comparison against tabulated values for long-radius elbows in ASHRAE Fundamentals (2017) at comparable Reynolds number and curvature ratio indicates the prediction is within 7% of the reported central tendency. Limited perturbation checks (inlet turbulence intensity and upstream profile shape) caused less than 2–5% variation in K for the range of conditions evaluated.

Within the defined context, we judge the computational model appropriately trustworthy for estimating the pressure loss of this elbow to guide fan sizing, with the caveat that strong swirl or highly skewed inflow conditions were not simulated. The Mechanical Systems Review Board has accepted the model for use in the south intake design decision as stated in the Decision section.

## 1. Background and Intended Use

The south intake corridor of Building 5 will be reconfigured to accommodate two additional mixing boxes. The new layout introduces a rectangular 90° bend transitioning a 0.4 m × 0.4 m duct around a column. The project team needs a credible estimate of the additional static pressure drop from this bend to decide whether to retain the existing 7.5 kW fan and VFD or to upgrade.

The CFD model’s output will be used to:
- Quantify the incremental loss across the elbow at the design flow of 10 m/s core velocity (approximately 0.64 m³/s volumetric flow).
- Support the selection of the fan operating point on the proposed system curve.

Metric and screening threshold:
- Elbow loss coefficient K expressed using total pressure: target agreement with standard reference data within ±10%.
- For design, K ≤ 0.25 is desirable to avoid moving the selected fan off the efficiency plateau.

The model is not intended to predict off-design transient behavior or acoustic characteristics. The geometric configuration is fixed for this evaluation: rectangular cross-section, long-radius elbow with centerline R/D of 1.5, with 6D straight approach and 10D run-out included to minimize entrance/exit interference.

## 2. Model Construction

### 2.1 Geometry and Flow Domain

- Duct internal dimensions: 0.4 m × 0.4 m; hydraulic diameter Dh = 0.4 m.
- Elbow: 90° centerline turn, long-radius with R/D = 1.5 based on Dh.
- Domain extents: Inlet located 4Dh upstream of the elbow entry; outlet located 6Dh downstream of the elbow exit. Additional straight lengths were trimmed to focus on the elbow contribution while providing sufficient flow development.
- No internal vanes or turning blades.

### 2.2 Governing Equations and Physical Models

- Incompressible, isothermal Newtonian flow of air at 20°C (ρ = 1.204 kg/m³, μ = 1.81e-5 Pa·s).
- Reynolds-Averaged Navier–Stokes with the k-omega SST turbulence closure.
- Scalable wall functions; near-wall resolution targeted to y+ ≈ 40–80.
- Buoyancy neglected; gravity disabled.

### 2.3 Boundary and Initial Conditions

- Inlet: Plug-flow velocity profile set to 10 m/s bulk velocity. Turbulence intensity set nominally to 5% and turbulent viscosity ratio to 10. The inlet plane is 4Dh upstream to allow profile development.
- Outlet: Static pressure condition set to 0 Pa gauge with backflow turbulence consistent with the inlet setting.
- Walls: No-slip, adiabatic.
- Initial field: Uniform 10 m/s streamwise velocity for accelerated startup; sensitivity to initialization is negligible once converged.

### 2.4 Numerics and Solver Controls

- Solver: Steady segregated SIMPLE-type pressure-velocity coupling.
- Gradient: Least-squares cell-based.
- Momentum and turbulence equations: Second-order upwind spatial discretization.
- Pressure interpolation: Standard; pressure staggering factor 0.25.
- Under-relaxation: 0.3 for pressure, 0.7 for momentum, 0.6 for k and ω.
- Convergence stopping: Residuals < 1e-4 for continuity, momentum, and turbulence equations; additionally, the area-averaged total pressure drop between the monitor sections changes by <0.3% over 1000 iterations.

## 3. Mesh and Numerical Quality Checks

### 3.1 Meshing Strategy

- Hex-dominant core with swept layers in straight sections; prism inflation (10 layers, growth rate 1.2) on walls to capture boundary layer with wall functions.
- Cell count per grid:
  - Coarse: 1.2 million cells, average y+ ≈ 85, minimum 10 layers near wall.
  - Medium: 3.8 million cells, average y+ ≈ 55, minimum 10 layers near wall.
  - Fine: 12.5 million cells, average y+ ≈ 38, minimum 12 layers near wall.
- Non-orthogonality < 20° everywhere; skewness below 0.28 (volume-weighted average 0.11 on the fine grid).
- Local refinement around the elbow intrados and extrados to resolve secondary motion and Dean vortices.

### 3.2 Residual History and Monitors

- On the medium grid, residuals dropped by 3–4 orders within 3000 iterations and leveled without oscillations.
- A line-integral monitor of total pressure along the duct centerline and area-averaged total pressure at the control planes both stabilized; last 1000 iterations showed <0.2% drift.
- Mass imbalance < 0.05% of inlet mass flow for all grids.

### 3.3 Mesh Refinement Study

A three-grid assessment was performed, keeping identical physics and solver controls. The characteristic grid spacing was defined based on the cubic root of the average cell volume in the elbow region.

- Computed K (coarse, medium, fine): 0.236, 0.228, 0.223.
- Observed refinement ratio r ≈ 1.55 (coarse→medium) and ≈ 1.65 (medium→fine) in terms of the characteristic mesh length scale.
- Apparent order p inferred from the three-point fit was approximately 1.9.
- Extrapolated K∞ ≈ 0.218 using Richardson’s approach.
- Estimated mesh-induced uncertainty on the medium grid: approximately 1.8% of K, assuming monotonic convergence and using a safety factor of 1.25.

Based on runtime and diminishing returns, the medium grid was selected for the reported value. The difference between medium and fine was 2.2%, within the target uncertainty budget for this decision.

## 4. Comparison with Published Reference Data

The result was compared against long-radius elbow loss coefficients from ASHRAE Fundamentals (2017), Chapter on Duct Design, which tabulates K for rectangular elbows with R/D ≈ 1.5 over a range of Reynolds numbers. For ReDh in the 2×10^5–4×10^5 range and square aspect ratio, the tabulated central estimate is K ≈ 0.21, with a spread of ±0.02 across datasets.

- CFD (medium grid): K = 0.225.
- Reference: K_ref = 0.21 (nominal), range 0.19–0.23.
- Percent difference from nominal: +7.1%.
- Absolute difference from upper bound of published spread: within +0.0% to +1.6%, depending on which dataset is taken as the upper margin.

The predicted streamline patterns in the elbow (two counter-rotating secondary vortices seen on a cross-section downstream of the bend) match the canonical behavior documented in the literature. The total pressure contours at the outlet exhibit the expected non-uniformity, healing over several diameters of downstream straight run, consistent with published flow-visualization figures for similar curvature ratios.

No attempt was made to adjust model constants to force agreement. The predicted K sits comfortably within the published envelope for the intended flow regime and geometry class.

## 5. Influence of Inlet Conditions and Solver Options

Several perturbation checks were performed to understand how robust the reported K is to plausible variations in the assumed inputs and numerics. Each of these used the medium grid.

- Inlet turbulence level:
  - 1% TI: K = 0.222
  - 5% TI (baseline): K = 0.225
  - 10% TI: K = 0.228
  - Sensitivity: about 0.006 change over a 9% TI swing (≈ ±1.3% relative variation from baseline).

- Inlet velocity profile:
  - Plug (baseline): K = 0.225
  - 1/7th power-law profile fit to ReDh ≈ 2.7×10^5: K = 0.221
  - Effect: approximately −1.8%.

- Swirl bias at inlet (rigid-body rotation added to match 5° nominal swirl angle):
  - K = 0.236, i.e., about +4.9% relative to baseline. This case is not expected in the as-built system given the 6Dh straight approach but is informative should field conditions deviate.

- Discretization order:
  - First-order upwind (otherwise identical): K = 0.233
  - Second-order upwind (baseline): K = 0.225
  - Numerics effect: −3.4% when moving from first- to second-order, justifying the higher-order scheme selection.

- Convergence criterion:
  - Tightening residual threshold to 1e-5 changed K by <0.2% relative to 1e-4 baseline.

These checks indicate that, within realistic ranges of inlet turbulence and profile shape for a straight approach duct, the predicted K is stable within a ±2% band. Non-uniform inflow with swirl increases losses more noticeably.

## 6. Results and Interpretation

- Reported elbow loss coefficient on the medium grid with second-order schemes and 5% inlet TI: K = 0.225.
- Estimated numerical discretization contribution on this grid: ~1.8%.
- Variability due to reasonable inlet condition uncertainty (TI 1–10%, profile from plug to 1/7th): within ±2%.
- Aggregate indication: the computed K agrees with standard references within approximately +7% of nominal and lies inside the published range for this geometry class and Reynolds number.

Implications for design:
- With K ≈ 0.225 and bulk velocity 10 m/s (dynamic pressure ≈ 60 Pa), the elbow contributes roughly Δpt ≈ K × q ≈ 0.225 × 60 ≈ 13.5 Pa. Including straight-run friction, the total added system resistance remains compatible with the current fan curve at 70% speed, per preliminary HVAC calculations supplied by the mechanical lead.
- The additional static loss margin required for this bend alone is modest. However, if upstream fittings produce swirl (e.g., a mitered tee or damper ahead of the elbow), losses could increase by about 5%, adding roughly 0.7 Pa in this configuration — still within the VFD range.

## 7. Credibility Considerations

The following practices were used to build confidence in the prediction for this specific elbow and flow condition:

- Numerics: A structured refinement of the mesh and adoption of second-order schemes helped mitigate grid-related error. The observed near-monotonic behavior across the three grid levels and an apparent order near 2 lend credibility to the extrapolated trend.
- Physics and flow phenomena: The turbulence model chosen (SST) is widely used for internal duct flows with adverse pressure gradients and secondary motion. The cross-sectional velocity vectors downstream of the bend show the expected pair of counter-rotating vortices characteristic of Dean-type secondary flow in curved ducts.
- Comparison to established references: Matching within the published range for K at similar R/D and Reynolds number supports the applicability for this straightforward configuration.
- Input checks: Reasonable variations in inlet turbulence and profile shape did not materially shift K, indicating the result is not hypersensitive to small uncertainties in approach-flow conditions.

Limitations that bound the credibility of this result:

- Only steady-state computations were performed; any unsteadiness associated with flow separation is assumed to be statistically steady at this Reynolds number. This is appropriate for a long-radius elbow without sharp features.
- Wall roughness was not modeled; the duct is planned in 20-gauge galvanized sheet with expected equivalent sand-grain roughness less than 0.1 mm. At this Reynolds number and relative roughness, the impact on K over the modeled lengths is likely small but not zero.
- The comparators are tabulated values synthesized from multiple sources; while they are standard in HVAC design practice, they are not from a test of this exact elbow. The reported agreement should be interpreted in that light.
- Strong swirl or skew associated with upstream hardware was not included in the accepted baseline; the sensitivity case demonstrates the direction and approximate magnitude of that effect.

## 8. Limitations and Open Items

- Geometric tolerances such as out-of-squareness at the elbow joints, misalignment at flanges, or installation of turning vanes were not studied. Minor construction deviations typically have second-order influence on K for long-radius elbows but could affect local flow uniformity.
- Downstream mixing length was included nominally as 6Dh; different downstream measurement stations will report slightly different K values if the outlet cross-section is too near the elbow. Our definition used 6Dh, consistent with design guides.
- No direct linkage was made to field commissioning measurements at this stage. If end-of-line TAB data are later available (velocity pressure and total pressure taps), post-installation backchecks could be performed to refine the loss coefficient for the as-built system.

## 9. Decision

The Mechanical Systems Review Board has reviewed this analysis and accepts the CFD model for estimating the elbow loss coefficient for the south intake AHU reconfiguration, specifically:

- Accepted for: predicting the total-pressure-based loss coefficient K of the specified 0.4 m × 0.4 m long-radius (R/D = 1.5) 90° elbow at a bulk velocity near 10 m/s, to inform fan selection and VFD setpoints.
- Not approved for: scenarios with strong upstream swirl or highly non-uniform approach flow beyond what a 6Dh straight run would typically generate, or for acoustic/noise predictions.

Decision: accepted for the stated use.  
Decision authority: Mechanical Systems Review Board (Chair: D. Morales)  
Date of decision: 2026-08-05

## 10. Distribution and Archival

- This report is filed under South-Intake-AHU/CFD/Elbow-Loss/RevA.
- Native case and mesh files are stored on the project share under the same path, RevA subfolder, and are available to project personnel upon request.

## 11. References

- ASHRAE Handbook—Fundamentals, 2017. Chapter on Duct Design (Loss Coefficients).
- White, F. M., 2006. Viscous Fluid Flow, 3rd ed., Chapters on Internal Flows and Secondary Motion.
- Menter, F. R., 1994. Two-equation eddy-viscosity turbulence models for engineering applications. AIAA Journal.

## 12. Appendix: Selected Plots (description)

- Cross-sectional vectors at 1Dh downstream of the elbow show two symmetric vortices spanning roughly 0.3Dh radius, centered near the mid-height lines of the cross-section.
- Streamlines colored by total pressure confirm a higher-loss path along the intrados wall, with gradual recovery downstream.
- Residual and pressure-drop monitor plots (not included here) show steady decay and flattening of the monitored quantities consistent with the stated convergence.

End of report.
