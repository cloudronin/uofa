# Credibility Assessment Report: CFD Simulation of a Radial Centrifugal Pump Performance Curve

Prepared by: Thermal-Fluid Modeling Group  
Date: 2026-08-06  
Toolchain: Ansys CFX 2024 R1, ICEM/Fluent Meshing 2024 R1, Python 3.11 post-processing scripts  
Hardware: Dual-socket AMD EPYC 7713 (64 cores/socket), 256 GB RAM, Infiniband HDR100 interconnect

## Executive Summary

We performed a computational study to predict the head–flow characteristic and hydraulic efficiency of a single-stage radial centrifugal pump operating at 2,900 rpm in clean water at 25°C. The analysis is intended to inform the design gate for a 20% impeller trim decision and to assess whether the as-built volute geometry supports the target duty point: 58 m^3/h at 24 m head, ISO 9906 Grade 2 acceptance.

Our computational setup uses a rotating frame approach (frozen rotor/MRF) for the impeller with a non-conformal interface to the volute. Turbulence closure is Shear Stress Transport (SST) with wall integration (y+ ~ 1). We conducted grid intensification, solver tolerance tightening, and a check against a transient sliding-mesh case at the duty point. The predicted curve matches test-stand data within 3.2% MAE in head and 1.8 percentage points in efficiency over nine flow points, with wide-open-throttle off-design deviation peaking at 5.1% in head due to volute tongue unsteadiness that is better captured in the transient check. Numerical uncertainty from the mesh/time/iteration choices is estimated at ±1.4% (k=2) on head near the duty point. Input sensitivity is dominated by surface roughness (±0.6% head impact) and inlet turbulence level (±0.4%).

The workflow is fully scripted with case and result hashes recorded. Repeated runs on different core counts produce essentially the same results (<0.05% drift in head rise). We did not adjust the turbulence model or wall functions post hoc; only measured roughness and the as-measured tip gap were used. The study applies to single-phase, non-cavitating operation for NPSHa ≥ 7 m; cavitation, gas entrainment, and solids were excluded.

We judge the analysis fit for use in design selection and margin assessment within the stated envelope. Identified restrictions include limited fidelity for tongue-passing unsteadiness at low flow and omission of cavitation physics.

## 1. Context and Intended Use

- Scenario: 100 mm nominal radial centrifugal pump with 6-blade closed impeller, volute collector, electric motor drive with VFD. Fluid: water (ρ = 997 kg/m^3, μ = 0.00089 Pa·s), temperature 25 ± 0.5°C.
- Primary decision: confirm that the untrimmed wheel meets the target head and efficiency at 58 m^3/h; extrapolate using affinity relations for slight speed adjustments (±5%).
- Accept/reject criteria: predicted head within ±5% of test data across 30–90% of BEP flow; numerical and input uncertainty budget reported; no calibration to test data allowed beyond using as-built geometry and measured surface finish.

The model will not be used to certify cavitation performance, acoustic behavior, or structural integrity of the shaft/impeller.

## 2. Geometry, Physics, and Boundary Conditions

- Geometry: CAD derived from CMM of the casting and machined impeller. Tip gap measured 0.35 ± 0.05 mm; fillets at blade leading edge 0.8 mm radius. We retained all major features except boltholes and minor casting lettering. Volute tongue chamfer retained (0.5 mm).
- Simplifications: Omitted motor housing and discharge piping beyond 2D (hydraulic diameter) downstream of the flange; added a 3D/2D inlet extension of 6D length to reduce inlet profile sensitivity.
- Flow regime: Re ~ 3.5×10^6 at BEP based on impeller outlet chord and relative velocity. Mach number < 0.02; incompressible, isothermal assumed.
- Turbulence closure: Menter SST with automatic near-wall treatment; y+ maintained between 0.5 and 1.7 over 95% of wetted area; curvature correction disabled. Sensitivity to RNG k-ε and RSM performed (Section 7).
- Rotational modeling: Primary results use Multiple Reference Frame (frozen rotor). A transient sliding-mesh check (32 rotor positions per revolution) is used at the duty point to assess steady approximation limits.
- Inlet: Mass flow specified per point in the curve sweep (30–100 m^3/h in 10 m^3/h increments), uniform total temperature, turbulence intensity 5% with length scale 7 mm (half hydraulic diameter of the inlet).
- Outlet: Static pressure set to 0 Pa gauge at the discharge plane located 2D downstream; backflow prevented during initialization only; swapped to “opening” when needed at low flows to maintain stability.
- Wall roughness: Equivalent sand roughness ks = 1.2 μm (impeller) and 3.0 μm (volute), based on profilometer measurements; roughness used in near-wall model.
- Cavitation: Disabled. Test data taken at NPSHa ≥ 7 m with no observable cavitation inception.

## 3. Discretization and Solver Settings

- Mesh: Poly-hexcore approach, local refinement at blade leading/trailing edges and tongue. Three global levels: 
  - Coarse: 1.2 M cells, avg y+ ~ 1.6
  - Medium: 3.2 M cells, avg y+ ~ 1.1
  - Fine: 7.5 M cells, avg y+ ~ 0.8
  Non-orthogonality 95th percentile < 18°, max skewness < 0.87.
- Interfaces: General grid interface between rotor and volute; conservative flux-based transfer.
- Spatial discretization: Advection “High Resolution” scheme in CFX (nominal second order); pressure-velocity coupling via coupled solver. Turbulence numerics second order.
- Iterative control: RMS residual target 1×10^-6; additionally, head and shaft torque monitored to within 0.05% change over 200 iterations before declaring convergence.
- Temporal treatment: Steady-state for MRF. For sliding-mesh validation at the duty point: physical time step equals 2° rotor motion per step (Δt = 1.148×10^-4 s), second-order backward Euler, 4 inner loops per step. Two full revolutions to wash out transients; statistics gathered over the third revolution.

## 4. Benchmarks and Solver Reliability Checks

We ran a sequence of known problems using the same toolchain:

- Laminar Poiseuille flow in a pipe: recovers analytic pressure drop within 0.11% on the medium grid; second-order convergence observed when refining radially.
- 2D lid-driven cavity at Re=10,000: centerline velocity profiles match Ghia et al. within 1.8%.
- Taylor–Couette in the narrow-gap limit: torque vs speed curve matches analytic solution within 0.6% for the laminar case; confirms rotating frame implementation.
- Parallel consistency: running the BEP MRF case on 48, 96, and 192 cores yields head changes less than 0.05%; checksum of flow field within 1.2×10^-6 L2 norm relative difference after convergence.

These give reasonable confidence that the solver and our setup are not producing gross numerical artifacts. We also unit-tested the custom Python post-processing function for head calculation against manual pressure integrations on simple synthetic fields.

## 5. Spatial and Temporal Adequacy

We quantify the effect of grid and time choices on key outcomes.

- Grid intensification: For the duty point, head rise H on Coarse/Medium/Fine was 23.52 m, 24.08 m, and 24.27 m respectively. Using the Roache approach with an observed order p ≈ 1.93 (from head), the extrapolated infinite-resolution head is 24.45 m and the estimated band from the High vs Fine grid is ±0.62% (95% CL assumed).
- Wall resolution: y+ histograms confirm adequate wall integration. Repeating the Medium grid with a coarsened prism stack (y+ ≈ 3) shifted head by 0.38%, consistent with expectations.
- Temporal resolution: At the duty point, the sliding-mesh head averaged over a revolution is 24.31 m with a standard deviation of 0.09 m (unsteadiness due to tongue interaction). Tightening the time step to 1° per step changed the mean by 0.07% and reduced the standard deviation to 0.06 m. This supports the chosen time step for the transient check and indicates the steady MRF head is within 0.6% of the time-averaged unsteady value.

## 6. Solver Behavior and Convergence Quality

- Residual decay met target 1×10^-6 across all points. 
- Imbalance: Net mass and momentum residual flux across domain boundaries < 0.08% of inlet mass flow and < 0.04% of inlet dynamic pressure area integral, respectively.
- Path dependence: Starting from different initializations (zero flow, previous flow point, and potential flow) converged to the same head within 0.1%. 
- Local hotspots: Recirculation regions appear at very low flows near the tongue. We ran an “opening” outlet BC and reduced under-relaxation to ensure a stationary solution; repeating with the transient method confirms existence of these zones, lending credibility that they are physical, not numerical.

## 7. Model Form Choices and Sensitivity

We evaluated alternatives to the chosen turbulence closure to understand model-form variability:

- RNG k-ε with scalable wall functions: BEP head 23.76 m (−1.3% vs SST Medium), efficiency −0.9 percentage points. At high flow, RNG slightly over-predicts head, consistent with literature bias in adverse pressure gradient handling.
- Reynolds Stress Model (SSG): BEP head 24.18 m (+0.4% vs SST Medium), better separation capture near the tongue, but significantly higher computational cost and slightly more delicate convergence at low flow.
- Decision: SST strikes a good balance of cost and fidelity. We incorporate ±0.7% model-form spread into the uncertainty budget near BEP, increasing to ±1.5% at the lowest flow where anisotropy effects are stronger.

## 8. Input Data Pedigree

- Fluid properties: Adopted from IAPWS formulation at 25°C; density and viscosity fixed values, justified by negligible temperature rise (<0.05°C) across the pump.
- Surface finish: Profilometer measured arithmetic roughness Ra = 0.3–0.5 μm on the impeller and 0.7–1.2 μm in the volute; converted to equivalent sand roughness using ks ≈ 2.5 Ra.
- Inlet turbulence level: Estimated from upstream piping length and Reynolds number using standard correlations; spot-checked with a hot-wire in a mock-up line indicating 4–6% TI.
- Geometry verification: Tip gap measured at four circumferential positions; we used the mean value. A sensitivity run with ±0.05 mm variation showed ±0.35% head change.

Assumption list is documented in the case’s README, with rationale and references. No post hoc tuning to match test data was performed.

## 9. Quantification of Uncertainty and Sensitivity

We aggregated numerical and modeling sources:

- Numerical (grid/iteration): ±0.62% (near BEP), growing to ±0.9% at the strongest gradients (lowest flow).
- Temporal (from transient vs steady comparison): ±0.3% near BEP; ±0.7% at lowest flow.
- Model-form (turbulence closure spread): ±0.7% at BEP; ±1.5% at lowest flow.
- Input variability:
  - Inlet TI 4–6%: ±0.4%
  - Roughness ks ±0.6 μm volute: ±0.6%
  - Tip gap ±0.05 mm: ±0.35%
  - Fluid property ±0.5°C: negligible (<0.05%)

Assuming weak correlation among these contributors, the combined band (root-sum-square) near BEP is ±1.4% on head and ±0.9 percentage points on efficiency, with coverage factor k = 2 based on the distributional assumptions for inputs and an empirical check with bootstrap resampling of the transient data for the unsteady mean.

We also performed a one-at-a-time local sensitivity sweep around BEP. Head is most sensitive to rotational speed (∂H/∂N ≈ 2H/N as expected by affinity), moderately sensitive to roughness in the volute, and relatively insensitive to inlet TI within 3–7%.

## 10. Comparison to Test Data

- Test facility: ISO 9906 compliant bench, calibrated pressure taps (±0.25% FS), Coriolis mass flowmeter (±0.1%), temperature held to 25 ± 0.5°C, NPSHa maintained > 7 m. Nine points taken from 30 to 100 m^3/h.
- Data conditioning: Head computed from area-averaged total pressure at inlet and static pressure at discharge plane; for the transient case, averages taken over one full revolution after two revolutions of settling.
- Results:
  - Overall mean absolute error in head: 3.2% across all points (MRF, Medium grid).
  - Near BEP (58 m^3/h): CFD head 24.08 m vs test 24.20 m (−0.5%); efficiency 75.3% vs 76.8% (−1.5 points).
  - Low flow (30 m^3/h): CFD head under-predicts by 5.1% in steady MRF; the transient sliding-mesh reduces the gap to 3.8%, suggesting unsteady tongue–blade interactions matter more away from BEP.
  - High flow (100 m^3/h): Agreement within 2.3% in head.

Error bars combining numerical and input uncertainty bracket the measured points at 7 of 9 stations. The two outliers are at the extreme low flow where separation is largest; model-form uncertainty there is likely under-estimated by the RANS family.

## 11. Applicability and Operating Envelope

- Validity window:
  - Speed: 2,800–3,050 rpm (linearly scalable per affinity laws, within ±5% change).
  - Flow: 35–95 m^3/h with highest confidence; 30–35 and 95–100 m^3/h with elevated uncertainty due to amplified unsteadiness and separation.
  - Fluid: Clean water, 20–30°C, kinematic viscosity within ±15% of baseline.
  - Suction: NPSHa ≥ 7 m, no cavitation. Cavitation and gas entrainment excluded.
  - Hardware state: As-built geometry with measured tip gap 0.35 ± 0.05 mm and roughness per Section 8.
- Out-of-scope:
  - Two-phase flow, erosion, or particle-laden slurries.
  - Acoustics and vibration predictions.
  - Structural response of the shaft/impeller.

## 12. Software Quality, Traceability, and Reproducibility

- Versioning: Case setup, meshes, and post-processing scripts tracked in Git (repo: pumps/v24r1_cfx_bench), tags locked at v1.3. Meshes stored in LFS with SHA-256 hashes recorded in the run manifest. Solver version pinned to Ansys CFX 2024 R1, double precision build.
- Automation: A Snakemake workflow orchestrates meshing, run, and post-processing; environment captured via Conda lockfile and module snapshots. A single command reproduces the entire curve sweep on the cluster.
- Determinism: Consistent results across MPI layouts as shown in Section 4. No randomized components in the solver configuration.
- Data checks: Unit conversions verified (SI units only). A sanity check script inspects BCs, fluid properties, and ensures no unexpected default overrides. A regression test run nightly on a cut-down case checks key KPIs (head, torque) within 0.2%.

## 13. Independent Oversight and Review

- Peer review: Two senior analysts (not involved in model building) reviewed the case file, BC rationale, and the mesh metrics. Their comments led to an added refinement box at the volute tongue and a more conservative convergence criterion on torque.
- Cross-check: Another engineer reproduced the BEP MRF case starting from the coarse grid mesh and achieved a head within 0.2% of our reported value after following the documented steps.
- Human-factors read-through: A non-CFD mechanical engineer validated the interpretation of the head definition and checked consistency with ISO 9906 data reduction to avoid definitional mismatches.

## 14. Decision Risk and Fitness for Purpose

The decisions relying on this study are moderate consequence: selection of impeller trim and confirmation of volute adequacy. The uncertainties reported (±1.4% near BEP) are well within the acceptance criteria and the observed spread against test data. We thus assess the analysis as sufficient for design gate passage, with the caveat that extreme off-design operation has elevated uncertainty. We recommend that low-flow operation margins be derived from the transient sliding-mesh results where practical.

## 15. Limitations and Known Shortcomings

- RANS turbulence models have limited fidelity for large-scale, periodic unsteadiness near the tongue at very low flow; URANS partially addresses this but may still smear coherent structures.
- No cavitation model included; predictions must not be used near NPSHr or for suction-side design decisions.
- Manufacturing variability beyond measured roughness and nominal tip gap (e.g., blade thickness tolerances, slight misalignment) not fully propagated; however, sensitivity suggests small effect on head at BEP.
- The MRF assumption suppresses blade-passing frequency content. We mitigated this by a spot transient check, but a full curve resolved with sliding mesh would be ideal for future releases if compute permits.

## 16. Conclusions

- The CFD workflow produces head–flow predictions for the centrifugal pump that align with ISO 9906 test data within 3.2% MAE overall and 0.5% at BEP, with transparent and repeatable numerics.
- Numerical and input uncertainties are characterized and small relative to acceptance bands; turbulence model-form variation is the dominant contributor at off-design low flows.
- The analysis is appropriate for the intended design decisions within the defined operating window. Documented limitations and uncertainty ranges should accompany any reuse or extrapolation.

## 17. Supporting Details

- KPI extraction: Head defined as Δ(p_total,inlet) − Δ(p_static, outlet), area-averaged on planes one diameter away from the hardware to minimize local swirl effects; efficiency computed from hydraulic power divided by shaft power (torque × angular velocity), with torque from the solver-reported impeller moment.
- Mesh QA: Aspect ratio in boundary layers < 120; growth rate ≤ 1.25; cell volume ratio across the rotor–stator interface < 3.
- Convergence monitors: Head and torque traces flatten exponentially; oscillations at low flow disappear after switching to opening BC and damping the first 200 iterations.

## 18. References

- ISO 9906:2012 Rotodynamic pumps — Hydraulic performance acceptance tests — Grades 1 and 2.
- Menter, F. (1994). Two-equation eddy-viscosity turbulence models for engineering applications. AIAA Journal.
- Roache, P.J. (1998). Verification and validation in computational science and engineering.
- Gülich, J.F. (2010). Centrifugal Pumps.

---
### Credibility Summary (plain-language)

- Physics representation appropriate for the regime; no cavitation or compressibility.
- Numerics tight enough to keep mesh/time effects small; residuals and balances demonstrate solid convergence.
- Model choices (SST) justified and alternatives explored; uncertainty budget accounts for spread.
- Strong alignment with high-quality experimental data; no a posteriori tuning.
- Reproducible runs with documented environment; independent checks in place.
- Clear statement of where the model works and where it doesn’t.
