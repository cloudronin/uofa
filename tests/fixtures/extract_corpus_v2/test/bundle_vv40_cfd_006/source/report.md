# Credibility Assessment Report: CFD of an Axial Fan in an AMCA 210 Test Plenum

Project: Data Center Rack Cooling Fan Selection  
Model: RANS-based rotating machinery simulation of a 7-blade axial fan (254 mm diameter) in an AMCA 210 setup  
Analyst: Thermal-Fluid Group, Epsilon Engineering  
Date: 2026-08-06  
Software: Ansys Fluent 2024 R1 (double precision), Ansys Meshing 2024 R1, Pointwise 18.5 R4, Python 3.11 for post-processing

## 1. Background and Decision Context

The operations team must select an axial fan for a 42U data center rack. The governing decision is whether the candidate fan (Model AF-254-7C, vendor datasheet Rev. K) can deliver 1.20 m³/s at a static rise of 325 Pa when paired with the rack’s flow resistance. The impact of a wrong call is moderate: if the fan is under-specified, the rack inlet temperatures will drift above ASHRAE TC 9.9 Class A1 by 2–3°C under peak load, potentially throttling CPUs and risking SLA penalties. A conservative design margin of 10% on pressure rise is targeted.

We applied CFD to predict the pressure-flow (P–Q) curve between 800 and 1800 RPM, with special emphasis at 1600 RPM, where the system curve is expected to intersect the fan curve. The model results are compared against measurements in our in-house AMCA 210-16 lab, following a conforming test arrangement (Arrangement 1 per the standard, inlet fan with a standardized plenum and flow measurement section).

This report documents how the airflow model was built, checked, and compared to data; how numerical resolution and physical modeling choices influence the outcome; and why the results are usable for the selection decision. The analysis is steady unless otherwise noted, leveraging a rotating reference frame (MRF) for the blade region and stationary frames upstream/downstream.

## 2. Model Setup

- Geometry: Full blade passage model (7 blades), hub, shroud, inlet bellmouth, and a 2.5D-length straight outlet duct to the measurement section. Tip clearance measured at 0.70 ± 0.05 mm using feeler gauges and included as a circumferential gap.
- Flow regime: Incompressible air; maximum tip Mach number < 0.12 at 1800 RPM; density from lab barometric and psychrometric data (1.184 kg/m³ ± 0.4%).
- Governing equations: Steady RANS; MRF in the rotor cell zone; segregated pressure-based solver with second-order spatial discretization; coupled pressure-velocity via SIMPLEC; second-order gradient reconstruction.
- Turbulence model: Baseline: SST k–ω with curvature correction. Comparative runs: Spalart–Allmaras (SA) and Reynolds Stress Model (RSM) for sensitivity.
- Wall treatment: y+ targeted below 1.5 on blade surfaces using an inflation stack of 30 prismatic layers; automatic near-wall treatment in Fluent (low-Re).
- Boundaries: Total pressure inlet with measured turbulence intensity (baseline 1.0% ± 0.5%) and eddy viscosity ratio (10). Outlet imposed as static pressure controlled to hit operating points along the P–Q curve. No-slip, smooth walls for blade and hub; shroud roughness set to equivalent sand roughness ks = 15 µm based on profilometer scans; downstream measurement section walls ks = 5 µm.
- Rotational speed: Validated at 1200, 1400, 1600, and 1800 RPM. Primary decision point is 1600 RPM.
- Initialization and numerics: Double precision; conservative under-relaxation; algebraic multigrid with default coarsening; residual targets 10^-6 on continuity, momentum, turbulence scalars; monitors on torque, Δp across the fan, and mass flow.

## 3. How We Checked the Numerics

### 3.1 Solver Checking and Templates
Before production runs, the CFD template used here was exercised on:
- A laminar Poiseuille flow case (3D rectangular duct) with an analytical pressure gradient; error in average axial velocity ≤ 0.3% on the fine mesh.
- A rotating cavity (simplified lid-driven rotor) verifying frame transformations; angular momentum balance closure within 0.7%.
- A canonical turbulent channel at Re_τ ≈ 395 comparing skin friction against accepted correlations (error 2.5% with SST).

We also reviewed Ansys’ published method of manufactured solutions (MMS) for advection-diffusion and Navier–Stokes (2023 whitepaper). Internal notes show no outstanding defects related to MRF or rotating wall boundary conditions for 2024 R1 on Linux.

### 3.2 Resolution Independence
A three-level mesh refinement study was performed at 1600 RPM and at 1400 RPM:

- Meshes: 5.2M cells (coarse), 8.7M (medium), 14.6M (fine), refinement ratio ≈ 1.4 globally with localized enrichment near the tip gap and trailing edges; stretching ratio ≤ 1.15 in boundary layer.
- Monitors: Pressure rise across the fan Δp, shaft torque T, and overall efficiency η = Δp·Q/(T·ω).
- Outcome: For 1600 RPM, the observed changes between medium and fine were 0.8% (Δp) and 1.1% (T). Using the Roache procedure with apparent order p ≈ 2.1 for Δp and safety factor 1.25, the estimated remaining grid uncertainty on Δp at the fine mesh is 1.2%.
- Time dependence: One transient sliding-mesh run at 1600 RPM was conducted with 2° time step per blade passage (3.6e-4 s) for 10 revolutions; the phase-averaged Δp differed from the steady MRF by 0.9%. Based on this, steady MRF was retained for the P–Q sweep.

### 3.3 Convergence Behavior
On the fine mesh:
- Residuals reach 10^-6 in all equations; torque and Δp plateaus achieved over the final 500 iterations.
- Mass imbalance < 0.05%.
- For challenging points near the knee of the fan curve, we used a ramped outlet pressure and swirl correction to avoid false convergence. No divergence encountered. Several restarts verified repeatability.

## 4. Physical Assumptions and Their Justification

- Turbulence closure: SST is known to capture adverse pressure gradients and separation zones on rotors more reliably than k–ε. The curvature correction aids near the hub region with strong streamline curvature. RSM was used as a check; it increased cost by ~4x but showed only a small change in Δp (see Sensitivity).
- Compressibility: Ignored (Ma < 0.3 rule of thumb); maximum dynamic pressure correction ≤ 1.2% of static rise; validated via a compressible run at 1800 RPM showing negligible differences in Δp and T.
- Heat transfer: Isothermal; blade temperature measured 23–27°C; density variation due to temperature is included via measured ρ. No buoyancy effects.
- Roughness: Set from profilometer data; not tuned to match Δp.
- Blade deformation: Structural flexibility neglected; expected deflection < 0.2 mm at tip under operating loads (vendor FEA), small relative to tip gap.

## 5. Inputs and Data Pedigree

- Geometry from vendor CAD (STEP, Rev. K); cross-checked against physical part using CMM at three blade sections; maximum deviation 0.18 mm at leading edge.
- Tip clearance measured with feeler gauges at six circumferential locations; mean 0.70 mm, SD 0.06 mm; implemented as a uniform gap of 0.70 mm; variability explored in a sensitivity run.
- Inlet turbulence intensity measured in the test duct with a hot-wire at 0.5D upstream, 5-point traverse; mean 0.9% ± 0.4%.
- Air properties derived from lab logs: temperature 21.8–22.4°C, pressure 100.6–101.2 kPa, RH 44–48%. Density set per test condition for paired comparisons.
- RPM verified with optical tachometer (±0.2%); controller feedback cross-checked.

All input files are tracked under Git (repo EE-CFD-Fans, tag amca-254-v3). Pre- and post-processing scripts include hash-based checks to prevent accidental changes in boundary assignments.

## 6. Experimental Reference and Quality

AMCA 210-16 test conducted in Epsilon’s Lab 2:
- Arrangement 1 (free inlet), standard nozzles for flow rate determination, static pressure taps per standard.
- Instruments: Druck PDCR 1830 differential transducer (±0.25% FS of 500 Pa), Setra 239 (±0.1% of reading) for verification, K-type thermocouples (±0.5°C) averaged at inlet and outlet stations, barometer (Vaisala PTB330, ±0.1 hPa).
- Calibration: All sensors calibrated within six months; certificates archived.
- Repeatability: Each operating point measured in triplicate; standard deviation in Δp < 0.7% of mean; flow rate repeatability < 0.6%.
- Corrections: Air density corrections per AMCA; end-effects minimized via flow straighteners upstream of the measurement section; swirl angle at the nozzle plane < 5° based on five-hole probe traverses.

We modeled the plenum, bellmouth, and measurement section sufficiently to reproduce the boundary conditions, not just an isolated fan. The spatial correspondence ensures the comparison is like-for-like within a few percent.

## 7. Results

### 7.1 P–Q Curve and Decision Point
- The predicted Δp at 1600 RPM and Q = 1.20 m³/s is 332 Pa on the fine mesh (ρ = 1.184 kg/m³). The test mean is 327 Pa with combined measurement uncertainty 1.6% (k=2).
- Over 800–1800 RPM, the curve shape is captured; mean absolute deviation between CFD and test across eight points is 2.3%. Largest discrepancy occurs near the onset of stall at the high-pressure, low-flow end (CFD overpredicts by 4.1% at 1800 RPM and Q = 0.75 m³/s).

### 7.2 Efficiency and Torque
- Predicted efficiency at 1600 RPM: 64.8%; measured 63.9% (from electrical input corrected for motor and VFD losses). Torque prediction within 2.6% of back-calculated test torque.

### 7.3 Flow Features
- Tip leakage vortex forms at ~20% chord and rolls up toward the shroud; separation bubble at the hub near mid-chord under the 1800 RPM, low-flow point; no gross separation under the decision condition.
- Surface y+ between 0.7 and 1.9 on blades; hub/shroud y+ < 2.5.

## 8. Sensitivity to Modeling Choices and Uncertain Inputs

We tested the impact of several plausible deviations:
- Turbulence model: SA reduced Δp by 1.6% vs. SST; RSM increased Δp by 0.8% and smoothed the knee in the P–Q curve. Spread across models at the decision point is ±1.2%.
- Roughness: Raising shroud ks from 15 µm to 45 µm reduced Δp by 0.9%.
- Inlet turbulence: Increasing inlet TI from 1% to 5% changed Δp by +0.5% (slightly fuller boundary layer at inlet bellmouth).
- Tip gap: ±0.1 mm around the measured mean shifts Δp by ∓0.7%.
- MRF vs. transient sliding mesh: difference of −0.9% for Δp as noted earlier.

These runs, along with the grid uncertainty, provide a basis to bound the model’s prediction interval at the decision point.

## 9. Quantifying Uncertainty in the Prediction

- Numerical resolution: GCI at fine mesh for Δp = 1.2%.
- Model form: From the turbulence model spread and the MRF vs. transient difference, we assign a modeling component of ±1.5% (covering both).
- Inputs: Combined from roughness, inlet turbulence, and tip gap uncertainty using root-sum-square gives ~1.3%.
- Experimental comparison: Test uncertainty for Δp is ~1.6% (k=2). We do not blend test uncertainty into the model prediction interval, but it frames validation residuals.

Assuming independence, the model-only uncertainty (numerical + physics + inputs) at the decision point is approximately 2.3% (k≈1). Taking the mean bias between CFD and test over the validated range as negligible (−0.2%), the 95% prediction interval on Δp at 1.20 m³/s and 1600 RPM is about ±4.6% relative if we inflate to k=2.

## 10. How Well Does the Model Match Reality?

For the four RPMs tested and points spanning the stable portion of the fan curve:
- Mean absolute percentage error in Δp: 2.3%; max 4.1% near stall.
- Slope of the P–Q curve between 1.0 and 1.4 m³/s aligns within 5% of test trends.
- No systematic bias with RPM: residuals centered around zero with light heteroscedasticity at the extremes.

We intentionally avoided tuning (e.g., inflating roughness or altering inlet TI) to force agreement. The only calibrated inputs were measured directly or from vendor metrology (tip gap, geometry). The proximity of the results to data without tuning increases confidence for use in selection.

## 11. Process Controls and Analyst Qualifications

- Personnel: Lead analyst has 12 years of turbomachinery CFD experience, with prior AMCA validation campaigns; supporting engineer handled meshing and post-processing. Both completed internal rotating machinery training in 2025.
- Checklists: A 37-point rotating CFD checklist was followed, covering BCs, units, mesh metrics (Skewness < 0.35; Orthogonality > 0.21), y+, and residual criteria. Sign-off by independent reviewer (J. Yuan).
- Versioning: All meshes, case/data files, and scripts are in Git with semantic version tags; CI job runs a small regression case nightly to flag solver environment drift.
- Hardware/OS: Runs performed on a 64-core AMD EPYC 7713 node with 256 GB RAM; RHEL 9.2; OFED 5.6; Fluent build hash logged. Randomness is not used; runs are deterministic.

## 12. Independence and Review

- Internal peer review conducted by an engineer not on the project team; comments addressed include adding the transient cross-check and extending mesh refinement to the outlet duct.
- Cross-code spot check: A single point at 1600 RPM, Q ≈ 1.20 m³/s was replicated in CFX 2023 R2 (SST, similar mesh), producing Δp within 1.3% of Fluent’s result.

## 13. Applicability and Limits of Extrapolation

- Validated regime: 1200–1800 RPM, flow rates 0.9–1.4 m³/s, within which we have direct comparisons.
- Out of scope:
  - Deep-stall behavior (low Q at high RPM) not modeled with URANS or DES; steady RANS is not trustworthy there.
  - Acoustic predictions are not part of this model.
  - Particle-laden or humid air effects: no droplets or condensate in the tests; not simulated.
- For the rack application, the system curve intersects near 1.20 m³/s at 1600 RPM, i.e., within the validated envelope; no extrapolation is required for the selection decision. If later operated above 2000 RPM or in ducts with significantly different inlet distortion, additional confirmation would be necessary.

## 14. Traceability and Reproducibility

- The run directory “amca-254-v3” includes a README with steps to regenerate results, mesh scripts with parameter files, solver journals for each operating point, and Python notebooks that compute P–Q curves and error bands. SHA256 hashes for critical files are listed in the appendix.
- Boundary naming and frame definitions are tested by a script that integrates fluxes over control surfaces and compares to expected signs and regions.
- Units are enforced via a linter script (converts any mm entries to m and flags rogue unit entries).

## 15. Risk-Informed Judgment for the Decision

- Decision need: Determine if the fan satisfies Δp ≥ 325 Pa at Q = 1.20 m³/s with 10% margin.
- Model outcome: CFD predicts 332 Pa; test gives 327 Pa. The model’s 95% interval is ±4.6% relative (~±15 Pa). Even the lower bound of the model’s interval is approximately 317 Pa; accounting for test mean and its uncertainty still leaves limited headroom relative to the target.
- Combined view: Since both the model and test are within a few pascals of the target, we recommend selecting the next higher RPM setting (1650 RPM nominal) or choosing the higher-stiffness impeller option to secure the 10% design margin. If the final system resistance proves lower in the integrated rack test, the 1600 RPM setting may be adequate.

The model is sufficiently trustworthy for comparing options and guiding RPM selection within the validated range, especially as it aligns with lab data without tuning. For claims outside the tested range (e.g., deep stall, off-axis inflow), the current setup is not adequate.

## 16. Limitations and Remaining Concerns

- The steady RANS approach cannot capture rotating stall inception with fidelity; thus, the high-pressure, low-flow edge has extra uncertainty not fully quantified.
- Wall roughness was implemented uniformly; actual spatial variability could introduce localized deviations in boundary layer growth.
- Motor losses and heat soaking in the test can bias efficiency estimation. Our torque agreement relies on electrical back-calculations; a direct torque transducer would be preferable for future campaigns.
- Small geometric discrepancies (e.g., fillet radii) below 0.2 mm are present between CAD and physical part; sensitivity to these was not explicitly quantified.
- Only one fan model was evaluated. Generalizing error statistics to other fans should not be assumed without additional evidence.

## 17. Summary and Recommendations

- The mesh refinement study indicates grid-related error on Δp is about 1.2% on the fine mesh.
- Differences among plausible turbulence closures and between MRF and transient methods amount to about ±1.5% on Δp at the decision point.
- Input variability (roughness, inlet TI, tip gap) contributes ~1.3% combined.
- The model matches AMCA 210 test points with an average deviation of 2.3% across the validated regime, with no evident systematic bias.
- Process controls (checklists, peer review, versioning) and solver checks reduce the likelihood of user mistakes and software defects influencing results.

Given the narrow margin to the target, it is prudent to:
- Select the 1650 RPM control point for deployment, or
- Proceed with the current fan at 1600 RPM contingent on an integrated rack test confirming the system curve is at least 5% lower than initially estimated.

The CFD model is credible for informing this choice within the specified operating envelope.

## 18. References

- AMCA 210-16, Laboratory Methods of Testing Fans for Certified Aerodynamic Performance Rating.
- Menter, F. R. “Two-Equation Eddy-Viscosity Turbulence Models for Engineering Applications,” AIAA Journal, 1994.
- Ansys Fluent 2024 R1, Validation and Verification Manual; Rotating Machinery, MRF and Sliding Mesh.
- Roache, P. J., “Code Verification by the Method of Manufactured Solutions,” ASME J. Fluids Eng., 2002.

---
For detailed mesh statistics, per-point comparisons, and file hashes, see the appendix.
