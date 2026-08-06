# CFD Credibility Assessment Report — Axial Blower for Battery Pack Cooling

Project: EB-214 Axial Blower Performance Predictions  
Analyst: L. Andrade (Fluid Systems Group)  
Date: 2026-07-30  
Software: Ansys Fluent 2023 R2

## 1. Background and Intended Use

This document summarizes the technical basis supporting the use of CFD to estimate the pressure–flow characteristic and efficiency trend of a 74 mm axial blower used to move air through a scooter battery pack duct network. The analysis is meant to inform geometry freeze for the B02 release and to rank design changes at the concept-stage (A/B/C variants). We are not using these simulations to set warranty thresholds or noise targets; acoustic prediction and stall margin at extreme throttling are out of scope.

Two operating ranges are of interest:

- Nominal speed window: 2200–3400 rpm
- Mass flow range per fan: 0.02–0.08 kg/s

The primary outputs are:
- Fan total pressure rise versus mass flow (fan curve)
- Shaft power and isentropic efficiency trend over the same range

A preliminary check against bench measurements was performed to gauge how well the setup captures reality within the intended envelope. The model is not intended to extrapolate beyond 3600 rpm or to very low flow rates where deep separation and rotating stall may occur.

## 2. Geometry, Physics Choices, and Simplifications

The CAD model includes the seven-blade rotor and shroud, a 15 mm inlet bellmouth, and 5D-long straight inlet and outlet ducts (both 70 mm ID) to match our test loop adapters. The following simplifications were applied:

- Tip clearance: set to a uniform 0.25 mm (measured average at assembly); local waviness was omitted.
- Fillets and parting-line chamfers below 0.8 mm were removed.
- Motor spokes were retained as solid; internal motor cavities were not modeled.
- Blade surface roughness was set to 10 μm equivalent sand-grain roughness based on profilometer readings on molded parts.

Working fluid is dry air at 25°C and 1 atm (ρ = 1.184 kg/m³, μ = 1.85×10⁻⁵ Pa·s). Compressibility effects are negligible; the maximum blade tip Mach number is below 0.15 at 3400 rpm. We therefore adopted an incompressible formulation with density held constant.

For turbulence closure, we selected k–ω SST with low-Re wall treatment. This choice was made based on the mix of attached flow on the blades and mild-to-moderate separation near the trailing edge and in the diffuser section. As a check, a single point was repeated with Spalart–Allmaras; the fan static rise changed by +1.6% and torque by +1.1% relative to k–ω SST at the same grid and residual tolerances. No transitional model was used; Reynolds number based on chord is above 2×10⁵ across the span for the operating range.

The rotor was represented using a Multiple Reference Frame (MRF) approach. We did not employ a sliding mesh for this phase due to the number of design iterations and the target turnaround time. The choice was revisited by running one transient case at 3000 rpm with 2° time-steps, which showed a 1.2% lower pressure rise compared to the steady MRF solution at matched flow—within the uncertainty band quoted later.

## 3. Boundary Conditions and Solver Setup

Boundary conditions were chosen to mirror the flow bench configuration:

- Inlet: mass-flow inlet with a flat velocity profile and 5% turbulence intensity. The inlet duct length (5 diameters) was included to damp profile development errors.
- Outlet: static pressure outlet, set to 0 Pa relative to ambient.
- Rotating region: MRF with angular velocity corresponding to the specified rpm.
- Wall functions: resolved to the viscous sublayer (target y+ ~1); no-slip, with the specified roughness height.

Numerics:
- Pressure–velocity coupling: coupled solver with second-order pressure discretization.
- Gradients and convective terms: second-order accurate schemes.
- Convergence: continuity and momentum scaled residuals below 1×10⁻⁵; additional stopping criteria required that mass imbalance <0.1% and that shaft torque and area-averaged outlet total pressure stabilize within 0.2% over 400 iterations.

Each operating point was initialized from a nearby converged solution to minimize startup transients. Under-relaxation coefficients were adjusted only for two low-flow points to avoid oscillations, not to exceed 0.6 for pressure and 0.8 for momentum.

## 4. Mesh Construction and Convergence Behavior

The domain was meshed with a hex-dominant unstructured grid (poly-hexcore) and 12 prism layers on all walls. We built three nested grids:

- Coarse: 5.2 million cells
- Medium: 9.8 million cells
- Fine: 18.4 million cells

Blade boundary layers were resolved with y+ between 0.8 and 1.5 across 85% of the wetted area at the medium grid; the hub trailing edge and sharp features reached y+ ≈ 2.2.

A mesh refinement study was executed at two flow rates (0.035 and 0.06 kg/s) at 3000 rpm. Quantities examined included pressure rise (Δpt) and shaft power (P). The observed changes were:

- 5.2M → 9.8M: Δpt increased by 2.6% (low flow) and 1.9% (high flow); P increased by 2.1% and 1.5%, respectively.
- 9.8M → 18.4M: Δpt increased by 0.9% (low) and 0.7% (high); P increased by 0.7% and 0.5%.

Using a three-grid Richardson approach assuming monotonic behavior, the apparent order was 1.9–2.1 for these quantities. Extrapolated estimates suggested a residual grid effect on Δpt of about 1.8% at 0.035 kg/s and 1.2% at 0.06 kg/s when using the 9.8M grid. We adopted the 9.8M mesh as the production grid, trading less than 1% expected bias for a threefold runtime reduction.

Convergence behavior was robust across most points. Two throttled conditions exhibited mild oscillations in torque and pressure after residuals fell below 1e-5; extending the run an additional 1500 iterations reduced oscillations to below 0.3% of mean values, which we accepted. The fine-grid cases were run to the same residual thresholds to confirm trends.

## 5. Experimental Check and Data Consistency

A simple validation exercise was conducted using a flow bench with an AMCA-style setup. A calibrated orifice meter provided flow rate, and static taps in the straight duct measured pressure difference; temperature and barometric pressure were recorded to correct density. The blower was driven by a PWM controller with closed-loop speed control. The instrumentation yields the following expanded uncertainties (95% level):

- Mass flow: ±1.2%
- Static pressure rise across the fan: ±1.5% of reading above 50 Pa, otherwise ±0.8 Pa absolute
- Rotational speed: ±10 rpm
- Air temperature: ±0.5°C

The test unit matched the CFD geometry within measurement resolution, including the uniform tip clearance. However, the as-molded surface roughness measured on the tested rotor was slightly higher than the nominal (Ra ≈ 13 μm vs. the 10 μm used in CFD), which is expected to decrease Δpt by roughly 0.5–1% based on empirical roughness sensitivity for similar profiles.

We compared three points at 2000 rpm and three at 3000 rpm, spanning the mass flow range of interest:

- 3000 rpm, 0.05 kg/s: CFD predicted Δpt = 175 Pa; test gave 168 Pa ± 2.5 Pa. Difference: +4.2% relative to test.
- 3000 rpm, 0.035 kg/s: CFD predicted 206 Pa; test gave 193 Pa ± 3 Pa. Difference: +6.7%.
- 3000 rpm, 0.065 kg/s: CFD predicted 142 Pa; test gave 145 Pa ± 2.2 Pa. Difference: −2.1%.

At 2000 rpm the trends were similar but with smaller absolute magnitudes:

- 2000 rpm, 0.035 kg/s: CFD 112 Pa; test 108 Pa ± 1.8 Pa. Difference: +3.7%.
- 2000 rpm, 0.02 kg/s: CFD 128 Pa; test 120 Pa ± 2 Pa. Difference: +6.7%.
- 2000 rpm, 0.055 kg/s: CFD 92 Pa; test 95 Pa ± 1.5 Pa. Difference: −3.2%.

The over-prediction at lower flow appears linked to how the MRF RANS model handles tip leakage and hub corner separation. Flow visualization from CFD indicates a strong recirculation cell on the suction side near 60–80% span at the trailing edge when throttled. Particle image velocimetry would help localize this, but we have not performed optical measurements.

Shaft power from CFD at 3000 rpm and 0.05 kg/s was 6.7 W; we lack an inline torque measurement for the bench, so efficiency comparisons rely solely on the CFD power number. This means the efficiency curve should be treated as model output without direct experimental confirmation.

## 6. Sensitivity to Modeling Assumptions

We probed several inputs to understand how much they affect the outputs within the range of interest:

- Turbulence model choice: Switching to Spalart–Allmaras at 3000 rpm and 0.05 kg/s reduced Δpt by 1.6% and P by 1.1%. Based on this, we assign ±2% as a rough model-form contribution for this class of flows in the present configuration.

- Inlet turbulence level: Varying the inlet turbulence intensity from 1% to 10% at fixed mass flow had marginal impact (<0.8% on Δpt, <0.5% on P). The 5% baseline was retained.

- Wall roughness: Increasing equivalent roughness from 10 μm to 15 μm reduced Δpt by ~0.9% at 0.05 kg/s and by ~1.4% at 0.035 kg/s. The nominal 10 μm is consistent with profilometer data on most blades, but production variability could expand this effect.

- MRF vs. transient sliding mesh: The single transient check at 3000 rpm and 0.05 kg/s (24 rotor positions per revolution, 2° step) yielded a Δpt 1.2% lower than the steady solution; the time-averaged torque differed by 0.9%. The unsteady case required significantly more CPU hours; for the design-screening purpose, MRF is acceptable.

- Outlet duct length: Reducing the outlet straight from 5D to 3D raised Δpt by 0.6% due to altered recovery losses. We kept 5D to match the test adapter length.

Collectively, these explorations suggest that within the intended use, the largest unquantified component is how RANS models tip leakage-driven separation at low flow. This is consistent with the direction and magnitude of the discrepancies against data.

## 7. Numerical Uncertainty and Error Budget

We combined the following contributions for a working uncertainty estimate on the predicted pressure rise at the 9.8M grid:

- Grid-related bias inferred from the three-grid study: 1.8% at low flow, 1.2% at high flow.
- Solver nonlinearity and stopping tolerance: estimated at 0.3% based on variation over extended iterations and different initializations.
- Turbulence model choice within RANS class: ±2% (based on k–ω SST vs. SA check).
- Geometric/roughness tolerance: ±1% (roughness variability and small fillet omissions).

Assuming these are largely independent, a root-sum-square combination yields a composite modeling uncertainty of approximately ±3.0% near BEP and ±3.4% at the throttled point. When compared to the experimental uncertainty (≈±1.5%), the observed differences at low flow (≈+6–7%) exceed this budget, indicating model-form limitations rather than numerical noise.

For shaft power, a similar roll-up gives ±2.5–3.0%. Because we lack torque data on the bench, this remains an internal estimate; efficiency values should be used comparatively rather than as absolutes.

## 8. Results Summary

- The CFD-predicted fan curve aligns with bench measurements within +4%/−3% over most of the intended operating window (2200–3400 rpm, 0.035–0.065 kg/s), with larger positive deviations (up to ~7%) at the most throttled conditions.
- The ranking of A/B/C rotor variants by peak efficiency is consistent across grids and modeling choices tested.
- The chosen mesh density (9.8M cells) provides a reasonable balance between turnaround time (~6 hours per operating point on a 32-core node) and accuracy; further refinement reduces Δpt by <1%.

We include below single-point values to illustrate the match; full curves are in the design archive:

- 3000 rpm, 0.05 kg/s: Δpt_CFD = 175 Pa; Δpt_test = 168 Pa ± 2.5 Pa; P_CFD = 6.7 W.
- 3000 rpm, 0.065 kg/s: Δpt_CFD = 142 Pa; Δpt_test = 145 Pa ± 2.2 Pa; P_CFD = 7.9 W.

## 9. Credibility Assessment Commentary

Given the purpose—screening design changes and estimating trends within a narrow operating envelope—the current setup provides a defensible basis for decision-making:

- Physical representation: The governing equations and closure model are appropriate for low-Mach internal flows with moderate separation. The MRF simplification introduces a small bias relative to fully unsteady treatment, but we quantified it at one point and found it within the aggregate uncertainty.

- Numerical behavior: Residuals and integral monitors demonstrate tight iterative convergence. A structured mesh-density study anchored the choice of production grid, and we derived a practical estimate of the remaining grid effect.

- Input conditions: Boundary conditions mirror the test loop; the sensitivity to inlet turbulence and outlet length was small. Surface condition assumptions are in family with measurements.

- External check: Agreement with bench data is generally within 3–5%, except at low flow where discrepancies approach 7%. The direction of error is consistent with known RANS challenges in tip leakage-dominated separated zones.

- Uncertainty: An error budget combines grid resolution, solver tolerances, model-form within the tested RANS family, and geometric roughness. For Δpt near BEP we estimate ±3%; at throttled points ±3.4%.

For design selection and early performance forecasting, these elements collectively support use of the CFD results with caution noted at the extreme throttling end. We do not recommend using the present model to certify minimum performance at very low flow or to predict stall onset.

## 10. Limitations and Deferred Work

The following items limit the scope of conclusions or are left for a future phase:

- We have not characterized behavior below 0.02 kg/s where rotating stall is likely; steady RANS/MRF is not suitable there. If this regime becomes important, we will adopt a sliding mesh with a transient RANS or hybrid RANS–LES approach and compare to time-resolved pressure data.

- Efficiency has not been backed by torque measurements. If efficiency thresholds become contractual, install a torque transducer in the test loop and revisit the comparison.

- Only two turbulence closures were sampled. If the low-flow discrepancy needs to be closed, additional testing with curvature-corrected SST or a scale-resolving model is advised.

- The experimental geometry matched tip gap and major features, but small fillets and parting lines were idealized. We estimate the effect to be on the order of 1% on Δpt, but a detailed tolerance sweep is outstanding.

- Acoustic predictions and tonal/noise assessments are out of scope and were not attempted here.

## 11. Recommendations

- Use the CFD fan curves to guide selection among rotor concepts and to populate the system model for thermal analysis in the 2200–3400 rpm window. Apply a conservative correction factor of −4% at flows below 0.035 kg/s when combining with duct losses.

- For B02 freeze, retain the 0.25 mm nominal tip gap; small decreases in gap are predicted to increase Δpt modestly (≈+1% per 0.05 mm reduction, from a limited parametric sweep not documented here), but may increase scrap risk. A dedicated tolerance study is recommended if manufacturing changes are contemplated.

- If the cooling system design begins to rely heavily on performance at the most throttled conditions, schedule an LES-lite assessment of one point and expand the bench matrix to include fast-response pressure probes near the rotor exit.

- Keep the 5D straight sections in both the CFD and test setups for future comparisons to limit sensitivity to outlet recovery.

## 12. Supporting Figures (described)

- Figure A: Static pressure contours on a mid-span blade-to-blade cut at 3000 rpm, 0.05 kg/s. High-pressure region near the leading edge at the pressure side; smooth diffusion with slight trailing edge wake.

- Figure B: Streamlines colored by velocity magnitude near the tip region at 0.035 kg/s showing a coherent leakage vortex interacting with the suction surface; separation bubble extending ~12% chord from the trailing edge at 70% span.

- Figure C: Plot of Δpt vs. mass flow for 2000 rpm and 3000 rpm; CFD curves overlaid with test points and error bars. Max deviation near the lowest flow tested.

(Images available in the project share under EB-214/figures; not embedded here.)

## 13. Data and Case Organization

- All CFD cases described above use the same base mesh topology scaled to the three densities. Operating conditions are cataloged by mass flow and rpm in the EB-214 run log.

- Boundary and material properties were consistent across the set; no temperature corrections were needed because air temperature varied by less than 1.5°C during tests and was fixed in CFD.

- The medium grid was used to generate the complete fan curves at 2000 and 3000 rpm. The coarse and fine grids were restricted to the two validation points for mesh-sensitivity evaluation.

## 14. Conclusion

Within the intended use—predicting the axial blower’s pressure–flow behavior and comparative efficiency trends in the 2200–3400 rpm range—the CFD setup provides results that are generally within 3–5% of bench measurements, with flagged limitations at the most throttled points. The modeling choices (incompressible RANS with k–ω SST, MRF, wall-resolved meshes) are appropriate for this family of flows, and the numerical solution quality has been established via a systematic grid study and stringent convergence checks. The credibility of the predictions is strongest around the best-efficiency region and weakens as the operating point approaches stall, where we recommend more advanced modeling and targeted testing if decisions hinge on that regime.

This report should be treated as a technical basis for design screening rather than as a certification package. If the project’s needs shift toward formal acceptance of guaranteed minimum performance, additional work identified above should be planned.

---
Contact: luis.andrade@fluid-systems.local for case files and figures.
