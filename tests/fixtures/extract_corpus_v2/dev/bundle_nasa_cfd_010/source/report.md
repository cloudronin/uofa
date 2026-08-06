# Credibility Assessment Report
CFD Prediction of Flow Distortion and Pressure Recovery in a Serpentine Inlet (S‑Duct) for a Small Turbofan

Date: 2026‑08‑05
Prepared by: Aero-Thermal Analysis Group

## 1. Background and scope

This report evaluates whether the current computational fluid dynamics (CFD) setup can be relied upon to estimate two inlet aerodynamic metrics for a compact S‑duct feeding a 3–5 kN class turbofan:

- Exit total-pressure recovery (mass-averaged at the aerodynamic interface plane, AIP)
- Mean swirl angle and its cross-sectional variation at the AIP

The intended use is pre-PDR geometry trades and screening at low subsonic conditions representative of takeoff and climb (Mach 0.35–0.50; inlet diameter 0.30 m; Reynolds number O(10^6)). The S‑duct consists of two back-to-back bends with a centerline offset of 20 degrees and an area ratio of 1.20, loosely based on the generic configuration of Wellborn et al. (Langley studies of curved diffusers), but with project-specific cross-section shaping.

No rotating machinery is modeled; the AIP is a planar cut nominally one duct diameter upstream of the fan face. The simulation objective is steady-state performance of the clean inlet under nominal alignment, without splash lip rain ingestion, acoustic coupling, or unsteady buzz phenomena.

## 2. Model form and simplifying choices

- Equations: steady Reynolds-averaged Navier–Stokes with ideal gas, incompressible limit enforced through low-Mach preconditioning.
- Turbulence closure: Menter SST k–ω with production limiter; wall treatment integrates to the wall (no wall functions).
- Compressibility: density variation retained through isothermal ideal air at 300 K; viscous heating neglected.
- Geometry: exact CAD for inner mold line; fillets on features < 1.5 mm are suppressed to reduce mesh complexity. External nacelle not included; only the internal duct from lip to AIP is simulated.
- Inflow: circumferentially uniform total pressure and temperature, axial flow only; turbulence intensity 1% baseline with 0.5–5% explored in sensitivity runs.
- Outflow: fixed static pressure such that the bulk Mach number at the inlet plane remains within ±0.01 of target.
- Walls: hydraulically smooth, no-slip; equivalent sandgrain roughness assumed 10 µm for sensitivity bounds.

These choices prioritize numerical stability and reasonable fidelity for separated flows at low-subsonic speeds typical of S‑ducts, while keeping computation times suitable for a design loop. Known consequences include under-resolution of secondary-flow vortices if very thin near-wall cells are not maintained throughout the bends.

## 3. Operating points and reference data

The primary assessed point is M = 0.45 ± 0.01 at the lip, Reynolds number ReD ≈ 1.8×10^6 based on inlet diameter and bulk velocity.

Reference measurements used for comparison:

- LaRC generic S‑duct campaigns (Wellborn et al., mid‑1990s), steady data for total-pressure maps and swirl probes at the AIP, scaled to current diameter with matched nondimensional parameters. We use the published centerline pressure tap distributions and circumferential rakes.
- Supplemental low-order in-house pitot traverse in a small-scale acrylic model (1:3), performed last year at M ≈ 0.25; these data are used only qualitatively to confirm vortex pair location trends, not for quantitative validation at the target Mach.

Reported experimental uncertainties: pressure coefficients ±0.005; mass-averaged recovery ±0.003; swirl angle ±0.5 deg at the AIP. Flow uniformity upstream of the duct in Langley data is within ±0.3% for total pressure.

## 4. Numerical approach

- Solver: density-based coupled algorithm with second-order spatial discretization for convective and diffusive terms; pseudo-transient under‑relaxation ramped from CFL 5 to 50 during convergence.
- Gradient calculation: least-squares cell-based with limiter threshold 0.15; pressure–velocity coupling by a Rhie–Chow scheme tuned for low Mach.
- Linear solves: algebraic multigrid with V‑cycles, three smoothing sweeps, coarsest grid size ~1,000 control volumes.

Convergence criteria:

- L2 residuals for continuity and momentum drop at least 4 orders of magnitude from initialization, with the last 500 iterations showing slopes < 1e‑4 per iteration.
- Global mass and energy imbalances less than 0.05%.
- Monitored outputs (AIP recovery, average swirl angle) stabilize within ±0.1% over the last 1,000 iterations.

Typical run: 6,000–9,000 iterations from uniform initial field; wallclock 14–22 hours on 128 cores (AMD EPYC 7763).

## 5. Mesh generation and numerical behavior

Grid topology:

- Predominantly hexahedral with O‑grid near the wall extruded from the lip through both bends to the AIP; core region meshed with H‑block transitions to maintain alignment with the flow turns.
- First-cell height set to achieve y+ ≈ 0.7–1.2 over 90% of the wetted perimeter; target growth ratio 1.18 in the first 15 wall-normal layers, then < 1.25 to the core.

Three systematically refined meshes:

- Coarse: 3.1 million cells; 40 wall-normal layers; minimum wall spacing 0.030 mm.
- Medium: 6.3 million cells; 56 layers; minimum wall spacing 0.022 mm.
- Fine: 12.6 million cells; 74 layers; minimum wall spacing 0.016 mm.

Quality checks included:

- Orthogonality > 0.22 in 99% of cells; minimum skewness 0.08; maximum aspect ratio 420 in attached boundary layer stripes, not in separated cores.
- No negative volumes; Jacobian determinants > 0.5 across bends.

Residual histories show a clean monotonic decay after CFL ramp; occasional early-stage oscillations in vorticity magnitude within the second bend settle by ~3,000 iterations.

## 6. Mesh adequacy and discretization error

A grid refinement exercise was carried out at M = 0.45 baseline conditions using the three meshes. Key outputs:

- Mass-averaged total-pressure recovery at AIP: 0.956 (coarse), 0.962 (medium), 0.965 (fine).
- Apparent order of accuracy estimated from these three levels is 1.9–2.1 depending on metric; extrapolated asymptotic value for recovery is 0.967.
- Grid convergence index (GCI) on the fine grid: 0.4% for mass-averaged recovery (95% confidence), 0.6% for mean swirl angle, and 1.1% for swirl RMS.

Wall static pressure coefficient distributions along the inner and outer walls of both bends show RMS differences between medium and fine grids of 0.018 and 0.023, respectively, with the largest deltas concentrated at the separation reattachment region. The fine grid captures the pressure plateau on the inner wall of the first bend more distinctly; the medium grid underpredicts the plateau magnitude by ~0.02 Cp.

Based on these observations, the fine grid is used for the validation comparisons and sensitivity work. The medium grid remains acceptable for rapid geometry screening if a 0.5–1.0% margin is applied to AIP recovery targets.

## 7. Comparison to experiments

All validation shown below refers to the fine grid at the nominal operating point unless otherwise noted.

- AIP total-pressure recovery
  - CFD: 0.965 ± 0.004 (numerical estimate)
  - LaRC reference: 0.967 ± 0.003
  - Difference: −0.002 (absolute), within combined uncertainty bounds.

- AIP swirl angle distribution
  - CFD mean swirl: 9.2 deg; RMS across the face: 3.4 deg
  - Reference mean: 9.8 deg ± 0.5; RMS: 3.1 deg
  - Differences: mean −0.6 deg, RMS +0.3 deg. The underprediction of mean swirl is consistent with a slightly weaker secondary-flow pair in CFD.

- Wall pressure taps (selected stations)
  - First bend, inner wall: plateau level Cp differs by +0.024 relative to reference at the middle of the separation bubble; reattachment length is within 3% of measured axial position.
  - Second bend, outer wall: the peak suction region is captured within +0.012 Cp; the gradient through the corner fillet is marginally too steep in CFD.

Spatial patterns of low-momentum streaks at the AIP show the characteristic counter-rotating vortex pair; the location and size match the Langley maps within 1/20 of the diameter in both spanwise and vertical coordinates.

No tuning to match a specific dataset was performed; the same turbulence model constants and inlet turbulence prescription were used across the refinement and sensitivity studies.

## 8. Sensitivity exploration

To understand how fragile the outputs are to modeling inputs, we ran a set of variations relative to the baseline:

- Inlet turbulence intensity: 0.5%, 1%, 3%, 5% at fixed turbulent length scale of 10 mm
  - AIP recovery varied by ±0.15% around baseline across this range.
  - Mean swirl shifted by up to +0.4 deg at 5%; RMS changed negligibly.

- Wall roughness, equivalent sandgrain: 0 µm, 10 µm, 40 µm
  - AIP recovery changed by −0.18% going from 0 to 40 µm.
  - Wall pressure plateau height increased by ~0.01 Cp at 40 µm.

- Outflow static pressure perturbation: ±0.5% of baseline
  - Mass flow adjusted automatically; AIP recovery and swirl metrics shifted by less than 0.2% and 0.2 deg, respectively.

- Turbulence closure swap: Spalart–Allmaras (baseline options otherwise unchanged)
  - AIP recovery predicted 0.957 vs 0.965 for SST.
  - Mean swirl 8.7 deg vs 9.2 deg for SST.
  - Secondary-flow structures appear slightly more diffuse with SA.

These indicate that, within reasonable bounds for the intended operating condition, the metrics of interest are most sensitive to the choice of turbulence closure and least sensitive to inlet turbulence intensity or modest wall roughness.

## 9. Estimated uncertainty on reported outputs

We combined the following components to attach an uncertainty estimate to the two metrics of interest:

- Numerical discretization: taken from the GCI estimate on the fine grid.
- Model form: taken as half the absolute difference between SST and SA predictions at the validation point.
- Experimental noise in the reference: applied when differences are computed; not carried into standalone predictions.
- Input variability: captured by the observed shifts due to turbulence intensity and wall roughness bounds, added conservatively as ±0.2% in recovery and ±0.3 deg in mean swirl.

Resulting combined standard uncertainty (root-sum-square) for predictions at the nominal point:

- AIP total-pressure recovery: ~0.9% of the reported value.
- Mean swirl angle at AIP: ~0.8 deg.

When comparing to Langley measurements, the combined (CFD plus experiment) bounds envelop the observed differences for both metrics.

## 10. Analyst qualifications

The primary analyst for this work has 12 years of applied CFD experience, including previous RANS and LES studies of curved diffusers and intakes for UAVs and small transport aircraft. The analyst completed turbulence modeling short courses led by Menter’s group (2022) and has run multiple mesh-convergence campaigns using GCI and residual behavior criteria. A second engineer executed the mesh generation and runtime monitoring after a two-week handoff, using the same practices.

## 11. Strengths and weaknesses of the current setup

Strengths:

- The grid-independence exercise shows asymptotic behavior in both recovery and swirl metrics; fine-grid estimates are within 0.5–1.1% numerical uncertainty.
- Against a widely cited dataset, the predictions fall within the reported experimental band, both in integral metrics and in spatial patterns of distortion at the AIP.
- Sensitivity sweeps indicate limited dependence on uncertain inflow turbulence and modest roughness; the primary lever is the turbulence model family, which has been explicitly bracketed.

Weaknesses and caveats:

- The approach is steady-state RANS. Unsteady shedding from the separation bubble, if present, is time-averaged out. As such, any conclusions about temporal variability or rotating-stall precursors are out of scope.
- The geometry excludes external lip shaping and any upstream installation effects; ingestion of boundary layer or crossflow from the fuselage is not represented.
- Fillet suppression below 1.5 mm could bias local wall pressure gradients near sharp corners, though the AIP metrics seem insensitive to this at the tested conditions.
- Only two turbulence closures were exercised; a broader bracket (e.g., Reynolds stress models or wall-modeled LES at higher cost) could be informative for off-design points where separation is more severe.

## 12. Results summary for intended use

At Mach 0.45 and ReD ≈ 1.8×10^6:

- Predicted AIP total-pressure recovery: 0.965 with an uncertainty of ~0.9%.
- Predicted mean swirl angle at the AIP: 9.2 deg ± 0.8 deg; spatial RMS 3.4 deg.

Behavior with small parametric nudges (±0.5% backpressure, 0.5–5% inlet turbulence, 0–40 µm roughness) remains within the quoted uncertainty. Replacement of SST with SA closure reduces recovery by ~0.8 percentage points and mean swirl by ~0.5 deg, serving as a practical indicator of model-form spread for this configuration.

These outputs are suitable to rank design variants by recovery and to flag geometries that induce excessive swirl, provided the comparison is made within the same modeling framework and mesh adequacy.

## 13. Limitations

- The model has not been exercised at higher Mach numbers, with engine face boundary conditions, or under gust/distortion inflow. It should not be used to predict stall margins or fan–inlet interactions.
- The method does not address acoustic resonance, icing, ingestion of particulates, or rain.
- The validation basis is a close cousin to the present duct, not a perfect geometric match, and it covers one operating condition in detail. Extrapolation to off-design, higher incidence, or mass-flow throttling is not supported by this assessment.
- Secondary metrics such as high-order distortion descriptors (e.g., DC60) were inspected qualitatively during postprocessing but are not reported here; the mesh and model were not optimized for those.

## 14. Credibility discussion

For the two metrics central to the intended decision (AIP recovery and mean swirl at low-subsonic, nominal alignment), the evidence chain is coherent:

- The numerics behave predictably on a refinement ladder, with small extrapolation gaps.
- The physics simplified in the model (steady RANS) is proportionate to the question asked (time-averaged, integral metrics).
- Input prescriptions (uniform inflow, fixed backpressure) match the way the reference experiments were conducted and the way early design trades are framed.

Residual uncertainties are dominated by model-form choices typical of corner-separated flows in curved diffusers. The bracketing between SST and SA offers a practical, if limited, indication of that component. While wall pressure details show small localized discrepancies, they do not propagate meaningfully into the AIP integrals at the nominal point. The current setup thus provides decision-quality information for pre-PDR screening of S‑duct candidates on the two stated metrics, within the tested envelope.

## 15. Decision

On 2026‑08‑05, the Propulsion Inlet IPT Lead reviewed this assessment and decided:

- The CFD setup described in this report is accepted for pre-PDR use in ranking S‑duct geometry variants by AIP total-pressure recovery and mean swirl at Mach 0.35–0.50 with clean, steady inflow and no fan model, subject to maintaining mesh resolution comparable to the fine grid and using the same turbulence model family (SST k–ω or SA) for internal consistency.
- The setup is not approved for predictions requiring time-resolved distortion, fan–inlet interaction, operability margins, or off-design cases outside the stated Mach range.

This decision enables its use in the ongoing trade study, with the understanding that additional validation will be required if the context of use expands.
