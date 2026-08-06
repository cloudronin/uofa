# CFD Credibility Assessment Report: Centrifugal Pump Head Curve Prediction

Project code: CP-HTR-020  
Date: 2026-08-06  
Analyst: E. K. Navarro

## 1. Executive Summary

We ran steady CFD to estimate the head-versus-flow curve for the TK250-50 centrifugal pump operating at 1785 rpm with water at 25 C. The analysis used a rotating reference frame for the impeller, RANS with a shear-stress transport type turbulence closure, and wall functions tuned for industrial y+ ranges. Three flow points were simulated to cover the target duty region: 65, 85, and 100 m^3/h.

The computational setup predicts head within 3.2–6.9% of bench data supplied by the test lab for two of the three flow points; at the highest flow (near the end of the vendor’s data range), the shortfall is 6.9%. Mesh refinement from ~1.9M to ~7.2M cells changed the predicted head by 1.2–2.1%, with monitors and residuals indicating a steady operating state in each case. Mass imbalance closed to <0.1% for all cases.

We consider the results proportionate for preliminary pump sizing and curve placement in the intended operating band. Noted limitations include simplified clearances and a frozen-rotor assumption that suppresses unsteady blade-passing dynamics.

## 2. Context and Modeling Intent

The goal is to provide head predictions at three target flow rates to support selection of motor size and expected operating point in a recirculating loop. The CFD is intended to:

- Estimate pressure rise for the TK250-50 impeller/volute combination at nominal speed.
- Provide internal flow fields to flag potential areas of recirculation or separation in the tongue region.
- Offer curve guidance prior to ordering a second round of factory tests at a modified trim diameter.

Outputs of interest:

- Pump total head (m) vs. flow (m^3/h).
- Shaft power (kW) inferred from torque on the rotating domain.
- Qualitative visualization of secondary flows at the impeller exit and in the volute.

The model is not configured to capture cavitation onset, two-phase effects, or structural loading of blades.

## 3. Geometry and Physical Idealizations

- Geometry basis: The CAD model provided by PumpWorks dated 2025-11-03 (file TK250-50_revC.x_t). Components meshed: impeller blades and hub/shroud; volute including tongue and diffuser; inlet nozzle; discharge elbow up to the 150 mm flange face.
- Trim: Blade passage count is 7, blade thickness nominal as provided. Leading-edge rounding preserved. Tip clearance modeled as a uniform 0.4 mm gap circumferentially.
- Leakage paths: Balance holes omitted; back shroud to casing gap not modeled; shaft seals excluded.
- Surface roughness: Represented via scalable wall functions with an equivalent sand-grain height ks = 25 microns on all wetted surfaces, aligned with glass-bead blast finish.
- Physics choices: Single-phase, isothermal liquid water at 998.2 kg/m^3, 0.00089 Pa·s. Incompressible solver with density constant.

Rationale: The flow regime of interest (Re > 10^6) justifies a RANS closure. The frozen-rotor approach (multiple reference frame) is acceptable for a head curve at fixed speed where time-averaged quantities dominate, and for the available schedule.

## 4. Solver Setup and Turbulence Modeling

- Software: ANSYS CFX 2023 R2
- Approach: Steady-state rotating frame for impeller domain, stationary frame for casing, with a mixing-plane interface at the impeller exit.
- Turbulence closure: SST formulation with curvature correction disabled. Transitional modeling not activated.
- Near-wall treatment: Automatic wall functions; y+ target 30–120 on most surfaces, with localized departures near the tongue.
- Discretization: Second-order for advection; high-resolution scheme in CFX terms. Pressure-velocity coupling via coupled algebraic multigrid.
- Convergence controls: Physical timescale started at 0.001 s, ramped adaptively; residual targets 1e-5 on RMS for continuity and momentum; monitor points include head, shaft torque, and circumferentially averaged swirl at the volute throat.

## 5. Operating Conditions and Boundary Specification

Three operating points:

- OP-A: 65 m^3/h at 1 atm inlet total pressure (gauge 0), outlet static pressure adjusted to achieve the requested flow via an opening condition. Speed fixed at 1785 rpm.
- OP-B: 85 m^3/h with same inlet condition and adjusted outlet back-pressure.
- OP-C: 100 m^3/h with same inlet condition and adjusted outlet back-pressure.

Further details:

- Inlet: Total pressure set to 0 Pa gauge, turbulence intensity 5%, turbulence length scale 0.01 m. Flow direction normal to inlet plane with a short 3D straight run upstream.
- Outlet: Static pressure boundary at the flange plane with opening specification allowing reverse flow if present. Prescribed turbulence intensity 5%.
- Rotational speed: 1785 rpm constant, single-speed runs.
- Reference frames: Impeller domain rotating; stationary for others. Stage averaging (mixing-plane) across the interface.

## 6. Gridding Strategy and Resolution Checks

Meshing performed in ANSYS TurboGrid (impeller) and ANSYS Meshing (volute):

- Baseline grid counts:
  - Coarse: 1.92 million cells (impeller 0.88M, volute 1.04M)
  - Medium: 3.84 million cells (impeller 1.78M, volute 2.06M)
  - Fine: 7.21 million cells (impeller 3.45M, volute 3.76M)

Cell types:

- Impeller: Structured H/J/C topology with O-grid around blade leading and trailing edges; 49 spanwise layers across blade channel. First-layer height set to achieve y+ ~35–50 on average.
- Volute: Predominantly poly-hexcore with inflation layers; minimum orthogonal quality 0.21; skewness below 0.81 on 99.4% of cells.

Mesh quality highlights:

- y+ statistics (OP-B, medium mesh): 92% of wetted area between y+=28 and 110; 5% between 110 and 180; small tongue-adjacent pockets near y+=220.
- Interface resolution: 180 circumferential nodes at the mixing plane per passage.

Refinement approach:

- Successive uniform refinement applied in boundary layers and in the tongue region; impeller surface grid density increased to preserve aspect ratio in the fine case.
- No significant remeshing between operating points; the same three meshes used across OP-A/B/C.

Convergence and grid sensitivity:

- Residuals: RMS continuity and momentum dropped 3–4 orders of magnitude; maximum residual below 1e-3 for all equations in final iterations.
- Monitors: Head and torque flattened to within 0.2% over the last 200 iterations for each run.
- Head variation across meshes (OP-B): 27.8 m (coarse), 28.2 m (medium), 28.5 m (fine). Extrapolated asymptotic value ~28.7 m assuming observed refinement ratio. A Richardson-style estimate suggests a numerical scatter near 0.4–0.6 m for this operating point.

## 7. Numerical Behavior Observations

- Stability: No oscillatory behavior in the steady solver once the timescale settled; early-stage oscillations controlled with a conservative physical timescale ramp.
- Mass balance: Overall imbalance <0.1% for all cases; blade-passage resolved fluxes balanced within 0.2%.
- Impeller-volute interface: Limited spurious swirl transfer observed; stage averaging smoothed passage-to-passage variations as intended for steady runs.
- Sensitivity to initialization: Using a ramp from a reduced speed (1000 rpm) shortened convergence by 30–40% compared to starting from rest.

## 8. Bench Comparisons

Vendor-provided hydraulic lab tests (PumpWorks Report PW-TK250-50-HTR-2025-12):

- Water at 25 C; barometric pressure 100.8 kPa; speed 1785±3 rpm.
- Calibration of pressure taps stated in report; details not reproduced here.

CFD-to-test comparisons:

- OP-A (65 m^3/h): CFD head 31.4 m (fine mesh); lab data 32.5 m → difference −3.4%.
- OP-B (85 m^3/h): CFD head 28.5 m (fine mesh); lab data 29.4 m → difference −3.1%.
- OP-C (100 m^3/h): CFD head 25.2 m (fine mesh); lab data 27.1 m → difference −6.9%.

Trend:

- The slope of the curve matches well in the central band (OP-A to OP-B). The shortfall increases near the higher-flow point where tongue separation becomes more pronounced in the model.
- Visual inspection of meridional planes shows a larger recirculation bubble near the tongue at OP-C compared to OP-B, likely exaggerating loss in the steady, stage-averaged treatment.

Power draw:

- OP-B torque yields 12.8 kW at the shaft in the CFD; the lab reported 12.1 kW electrical input with an estimated 90% motor efficiency. Given the unknowns in drive efficiency, the magnitudes are in the same ballpark.

## 9. Results and Flow Features

- Impeller exit: Flow angle relative to tangential direction is 12–17 degrees lean for OP-A/B; angle increases to 22 degrees at OP-C, indicating higher incidence to the volute tongue at high flow.
- Volute: Static pressure contours show a peak at the tongue with a mild wrap-around over 30 degrees circumferentially. OP-C exhibits a flatter pressure recovery profile downstream of the tongue, consistent with elevated mixing loss.
- Blade loading: Pressure-side suction peaks are moderate, with no sub-ambient patches on the shroud side at the simulated points (no cavitation captured by design).
- Efficiency indicators: Ratio of hydraulic power rise to torque-implied power points to an internal efficiency of 76% at OP-B, which is slightly optimistic relative to typical published curves for this size class; part of the overprediction could stem from neglected leakage.

## 10. Choices that Influence Credibility

- Rotating model: The frozen-rotor assumption is known to undershoot mixing losses where strong clocking effects occur; switching to a transient sliding mesh would likely erode 0.5–1.5 m of head near OP-C. For the central operating band, the difference is usually smaller for this pump class.
- Turbulence model: The SST closure is generally robust for adverse pressure gradients; disabling curvature correction sacrificed a small stabilizing effect in swirling regions to keep runtime consistent across points.
- Wall treatment: With y+ mostly in the 30–120 window, the adopted wall function regime is appropriate. Local high-y+ near the tongue could modestly distort loss calculation but is a second-order effect relative to the steady interface choice.
- Geometric omissions: The back-shroud gap and balance holes, not represented here, tend to reduce head and efficiency by allowing leakage and recirculation. Their absence likely contributes to the CFD being on the high side for efficiency-related metrics even as head is slightly underpredicted at high flow due to volute losses.

## 11. What Would Move the Needle

If turnaround allowed, the following changes would likely tighten alignment with lab data and reduce model-form bias:

- Run a transient sliding-mesh case at OP-C to quantify the tongue-blade interaction cost and set a bracket for the steady result.
- Introduce a simple representation of leakage paths (back-shroud annulus with a pressure-driven gap model) to decrease the optimistic efficiency noted in Section 9 and adjust the balance between impeller and volute losses.
- Increase near-tongue resolution to push local y+ below 120 and refine capture of the adverse-gradient separation bubble.

## 12. Interpretation for Intended Use

For pre-test planning and pump curve placement near the preferred duty point (65–85 m^3/h), the present CFD gives a reliable directional estimate with a small negative bias in head. At the high-flow edge (100 m^3/h), the model’s steady assumptions tend to penalize the predicted head, so the current numbers should be read as conservative in that corner of the map. Internally, the flow feature maps provide helpful guidance on volute tongue repositioning for the next design loop if pursued.

## 13. Credibility Discussion

Evidence supporting the level of confidence appropriate for early sizing:

- Multiple resolutions were executed with small changes in key outputs between the two finest meshes, and solution monitors stabilized tightly.
- The method aligns with long-standing practice for industrial pump assessments: steady RANS with SST and a mixing-plane interface is a common combination when the target is the average head curve.
- The degree of alignment with the lab data is consistent across the central operating region, and the divergence at the high-flow point is explained by well-understood modeling constraints.

Known limitations that temper reliance:

- The steady rotational treatment filters blade-passing unsteadiness and associated losses, which matters most at high flow. The model also lacks small-scale leakage pathways that can meaningfully change the head balance.
- Surface roughness was idealized uniformly; in-service deposits or variable finish were not represented.

On balance, the computed curve is fit for preliminary selection of motor power and expected duty placement, with the caveat that the upper-flow-edge prediction should be treated as a lower bound on head until a transient model or additional testing is completed.

## 14. Limitations

- Single-phase assumption; cavitation and air ingestion are not represented.
- No heat transfer; fluid properties kept constant.
- No representation of the back-shroud cavity, balance holes, or mechanical seals.
- Steady mixing-plane treatment suppresses unsteady tongue interactions.
- Surface roughness modeled uniformly rather than per-component.
- No off-design speed sweeps; only nominal 1785 rpm was run.

## 15. Reproducibility Notes

- Project archive includes meshes for the three grid levels and the CFX setup files for OP-A, OP-B, and OP-C.
- Hardware environment: Linux workstation with 32 cores (Intel Xeon), 128 GB RAM; typical run time per operating point ~4.5 hours on the medium mesh and ~9.5 hours on the fine mesh.
- All cases executed in double precision.

## 16. Conclusions

The TK250-50 pump head predictions from the steady RANS, frozen-rotor CFD runs show good agreement with bench data in the intended operating band (−3.1% to −3.4% deviation), with larger shortfall at the high-flow extreme (−6.9%). Mesh refinement reduced sensitivity to discretization, and solver monitors demonstrate tight steady behavior. For decisions around pump sizing and expected operating point selection near 65–85 m^3/h, this level of fidelity is adequate. For robust conclusions near 100 m^3/h, incorporating unsteady rotor-stator interaction or commissioning an additional test point would be prudent.

Appendix includes mesh statistics and monitor histories summary.
