# Credibility Assessment Report: CFD of an S‑Duct Inlet With Boundary Layer Ingestion

Project: Inlet Distortion Study for Small UAV Propulsion Integration  
Analyst: A. S. Malik, Aerodynamics Group  
Date: 2026‑07‑16

## 1. Background

This report documents the credibility assessment of a steady RANS analysis of a compact S‑shaped inlet designed to ingest the fuselage boundary layer for a small electrically driven UAV. The objective was to estimate inlet pressure recovery and distortion at the aerodynamic interface plane (AIP) across a moderate envelope of flight conditions. The configuration is a 0.3‑m diameter, two-bend serpentine duct mounted flush on a generic cylindrical fuselage. 

The numerical predictions were cross-checked against data from a closed‑return, low-turbulence wind tunnel using a 1:2 scale test article with interchangeable lips and bleed settings. The wind tunnel model includes a 5‑hole probe rake at the AIP and surface static taps for wall pressure coefficient distribution (Cp). The analysis outcomes are intended to inform early design decisions for the inlet lip shape and to de‑risk selection of rake locations for engine face instrumentation.

We focus on whether the present modeling approach is fit for comparative evaluations among lip geometries and whether the predicted metrics (pressure recovery, swirl intensity, DC60) behave sensibly across changes in free‑stream speed and angle of attack. Where possible, we provide quantitative indicators of numerical quality and compare predictions with measured data at matched conditions.

## 2. Scope and Intended Use

- The analysis spans free‑stream speeds from 25 m/s to 55 m/s (ReD ≈ 0.5–1.1×10^6), angles of attack from −2° to +6°, and sideslip angle fixed at 0°. Static sea‑level conditions were assumed. We examined two lip radii (baseline and +20% radius) and one bleed setting (2% of inlet mass flow extracted near the highlight).
- Primary outputs are:
  - Mass‑averaged total pressure recovery at the AIP
  - DC60 distortion index derived from 5‑hole probe rake data
  - Maximum swirl magnitude in the AIP plane
  - Mean centerline Cp distribution along the inner bend
- The analysis supports down‑selection of the lip variant for prototype fabrication. It is not intended to set final certification margins. The modeled envelope aligns with the subset of wind tunnel cases acquired in Q2.

## 3. Modeling Approach

### 3.1 Geometry and Flow Physics Assumptions

- The computational geometry includes the external fuselage forebody, the inlet lip, a 1.1‑m centerline length S‑duct, and a short plenum terminating 0.05 m downstream of the AIP. No internal fan or spinner was modeled; the AIP plane is treated as a uniform mass‑flow extraction boundary.
- Assumptions:
  - Air treated as perfect gas with γ=1.4, R=287 J/kg‑K; density variations modest in the explored Mach range (M∞ ≤ 0.18), but compressible formulation retained.
  - Steady flow assumption adopted. Unsteady separation bubbles that may form at higher incidence are not captured; separated zones are represented in a time‑averaged sense by the turbulence closure.
  - Surface roughness neglected; tunnel model and CFD surfaces treated as hydraulically smooth.
  - Symmetry not enforced due to off‑center secondary flow structures; full 360° geometry solved even for β=0°.

### 3.2 Governing Equations and Numerical Schemes

- RANS equations solved with the SST k–ω turbulence model with production limiter; low‑Re corrections enabled.
- Pressure‑based coupled solver; second‑order accurate spatial differencing for momentum and turbulence quantities; pressure interpolation PRESTO.
- Pressure–velocity coupling by coupled scheme; under‑relaxation tuned only during initial 100 iterations.
- Steady-state; no temporal advancement except pseudo‑time for coupled solver.

### 3.3 Boundary Conditions

- Inlet (farfield): velocity magnitude and direction set to target U∞ and angle of attack using a velocity inlet with turbulence quantities specified by intensity and length scale. Free‑stream turbulence intensity set to 0.5% ± 0.25%; turbulent length scale 0.03 m (based on 7% of duct diameter).
- Wall: no‑slip, adiabatic.
- AIP: mass‑flow outlet matched to tunnel blockage‑corrected mass flow determined from AIP rake total pressure and static pressure in the wind tunnel; swirl at AIP unconstrained by boundary condition.

### 3.4 Meshing

- Poly‑hexcore volume mesh generated using Pointwise; prism layers on all walls targeting y+ ≈ 1.0; first cell height 8 µm; 28 inflation layers with growth rate 1.2.
- Baseline grid: 4.9 million cells (1.3M prisms, 3.6M poly‑hex core).
- Two additional grids for refinement study:
  - Coarse: 2.4M cells; first cell 12 µm; 22 layers; target y+ ≈ 2.0.
  - Fine: 10.2M cells; first cell 6 µm; 34 layers; target y+ ≈ 0.7.

### 3.5 Solution Process and Convergence Indicators

- Each case initialized with potential flow and ramped to target mass flow over 500 iterations. Residuals reduced typically 3–4 orders of magnitude; area‑averaged total pressure at AIP and wall shear stress on inner bend monitored; both stabilized to within 0.1% over 600 iterations.
- For the fine grid at the most demanding condition (U∞=55 m/s, α=+6°), 1400 iterations were required to reach a flat signal history; no periodic cycling observed.

## 4. Numerical Quality Checks

### 4.1 Mesh Refinement Study

- The three‑level grid sequence produced monotonic behavior in mass‑averaged pressure recovery. Using generalized Richardson extrapolation assuming apparent second‑order convergence, the estimated grid uncertainty (95% confidence) at the reference condition (U∞=40 m/s, α=2°, baseline lip) is:
  - Recovery: GCI ≈ 0.42%
  - DC60: GCI ≈ 1.8%
  - Maximum swirl: GCI ≈ 2.1°
- Sensitivity of GCI values to the convergence order assumption was probed by repeating the estimate with p=1.8 and p=2.2; the recovery GCI varied between 0.49% and 0.38%, respectively.
- Local flow features such as the inner bend separation bubble shrink with refinement; however, the separation onset location varies by less than 3 mm between the fine and baseline grids.

### 4.2 Iterative Convergence and Residual Behavior

- Normalized residuals for continuity, momentum, k, and ω reduced below 2×10^-5 for baseline and fine grids at all conditions. The coarse grid stalled at 4×10^-5 for the α=+6° case. Monitors at the AIP and along the inner bend showed no remaining trends after the residuals plateaued.
- Finalization criterion: less than 0.05% change in AIP recovery over 200 iterations.

## 5. Comparison With Wind Tunnel Measurements

### 5.1 Data Sources and Matching

- Wind tunnel tests conducted in the 1.8 m × 1.8 m closed‑return facility at NTF‑West. Flow quality specified by the facility as turbulence intensity below 0.25% in the empty test section. Total temperature maintained at 295±1 K.
- Measurements:
  - 48‑port 5‑hole probe rake at the AIP; combined uncertainty in port total pressure reported by metrology as ±0.6% of reading; yaw/pitch angle uncertainty ±0.7°.
  - Cp taps along inner and outer walls (36 taps). Pressure transducers MKS Baratron 690A series; calibration drift <0.15% over a week.
- Test cases selected to match three free‑stream speeds and two angles of attack. The tunnel model used the baseline lip and the +20% lip radius insert; bleed fixed at 2% of measured inlet mass flow. Fairing pieces at the lip/plenum joint minimized steps; remaining seam height <0.2 mm by feeler gauge.

### 5.2 Plane‑Averaged Metrics

- Pressure recovery at AIP:
  - Baseline lip, U∞=40 m/s, α=2°: experiment 0.948; CFD 0.954 (Δ=+0.006).
  - +20% lip, same condition: experiment 0.961; CFD 0.964 (Δ=+0.003).
- DC60 distortion:
  - Baseline lip: experiment 0.038; CFD 0.042.
  - +20% lip: experiment 0.030; CFD 0.034.
- Maximum swirl angle:
  - Baseline lip: experiment 7.4°; CFD 6.1°.
  - +20% lip: experiment 5.9°; CFD 5.3°.
- Trends with α:
  - Increasing α from 0° to +6° reduces recovery by ~1.7% in both CFD and experiment for the baseline lip; the +20% lip variant shows smaller degradation (~1.1% in CFD, ~1.3% in data).

### 5.3 Spatial Distributions

- Swirl pattern at AIP shows a pair of counter‑rotating vortices skewed toward the inner bend. The vortex core separation and swirl magnitude contour shapes are captured in CFD, though the computational vortices are more diffuse.
- Wall pressure coefficient along the inner bend correlates well up to s/L ≈ 0.55. Downstream of that, the CFD underpredicts suction by ~0.04 in Cp, coincident with onset of measured separation indicated by oil-flow visualization. The RANS solution predicts separation onset about 0.03L later than indicated by the Cp plateau, consistent with known SST behavior on mildly adverse pressure gradient ducts.

## 6. Sensitivity Exploration

We examined the response of the primary outputs to variations in three influential inputs:

- Free‑stream turbulence intensity (Tu∞): 0.25%, 0.5%, 1.0%
- AIP mass flow rate: ±1.5% from nominal
- Inlet boundary layer thickness on the fuselage δ99 at the lip station: ±10% via wall suction adjustment in the external approach section

Key observations at U∞=40 m/s, α=2°:

- Recovery decreased by 0.003 when Tu∞ increased from 0.5% to 1.0%; DC60 improved slightly (~0.002) as increased ambient eddies softened the inner bend separation.
- A +1.5% change in AIP mass flow increased recovery by ~0.005 and reduced DC60 by ~0.003 for both lip variants.
- Thickening the incoming boundary layer by 10% worsened DC60 by ~0.006 in CFD. This effect was more pronounced for the baseline lip than for the larger‑radius lip.

The ranking between the two lips was insensitive to these perturbations: the +20% lip variant consistently outperformed the baseline in both recovery and distortion by margins exceeding the estimated numerical error bounds.

## 7. Uncertainty Considerations

- Input variability for the CFD runs was represented by triangular distributions on Tu∞ (0.25%–1.0%, mode 0.5%) and AIP mass flow (−1% to +1.5%, mode 0%). A simple Latin hypercube sampling with 40 samples on the baseline grid was used at U∞=40 m/s, α=2°.
- Resulting spread at the AIP:
  - Recovery: mean 0.955, standard deviation 0.0031; 95% interval ±0.006.
  - DC60: mean 0.040, standard deviation 0.0022; 95% interval ±0.004.
  - Maximum swirl: mean 6.0°, standard deviation 0.7°.
- Combining the numerical discretization estimate (Section 4.1) with the input variability for recovery in quadrature suggests an overall assessment band of roughly ±0.007 at the selected condition for the baseline lip. The wind tunnel measurement uncertainty (±0.6% for total pressure) contributes comparably on the experimental side.

## 8. Applicability and Limits of the Current Model

- The present steady RANS approach is appropriate for screening inlet lip shapes for modest angle‑of‑attack changes at low subsonic speed. It reproduces plane‑averaged recovery within about 0.5–0.7% of measured values and captures the direction of change for DC60 with fidelity sufficient to rank alternatives.
- For aggressive incidence or if bleed control variations become a dominant factor, the steady RANS assumption may be strained. High‑frequency unsteadiness of the separation bubble and vortex wandering would require unsteady modeling to resolve phase coherence at the AIP.
- The absence of a rotating fan or boundary condition swirl constraint means the model cannot predict engine‑face ingestion effects or any compressor‑face flow redistribution that would occur in the integrated propulsion system configuration.

## 9. Credibility Assessment Summary

The following evidence contributes to confidence in the model for the stated use:

- Physics representation:
  - Use of SST k–ω with appropriate near‑wall resolution (target y+≈1) is standard for adverse pressure gradient duct flows. The inclusion of low‑Re corrections and layered boundary mesh supports resolution of the viscous sublayer where needed.
- Numerical consistency:
  - Three‑level grid sequence shows low GCI values for recovery and moderate GCI for distortion and swirl metrics; trends are monotonic with refinement and residual behavior is well‑controlled.
- Agreement with data:
  - Recovery values agree within about 0.6% on average; DC60 slightly overpredicted but consistent in ranking; swirl magnitudes underpredicted by ~1° absolute. Spatial distributions of Cp and vector fields show the expected vortex pair structure and the approximate separation region sizing.
- Robustness across inputs:
  - Variations in key inputs (Tu∞, mass flow, δ99) do not overturn the ranking between lip variants. Output sensitivity is smooth and consistent with physical intuition.
- Applicability envelope:
  - Conditions analyzed align with test points; flow regime and Reynolds numbers are similar between the computational and experimental setups for matched speeds.

Areas that warrant caution in interpreting the results:

- Distortion metrics are more sensitive to grid resolution and turbulence model details than plane‑averaged recovery. The reported GCI for DC60 is larger and the model tends to produce a more diffuse swirl structure than indicated by the rake data. 
- The RANS closure delays separation onset on the inner bend compared to cues from the Cp plateau; this discrepancy is a known behavior but implies that detailed local surface pressure features are less trustworthy than the integral metrics.
- While input variability was explored for Tu∞ and mass flow, other uncertainties such as precise wall temperature, minor geometric mismatches at the lip/plenum seam, and subtle tunnel flow angularity were not varied.

## 10. Results for Decision Support

For the design screen at U∞=40 m/s, α=2°:

- Baseline lip: recovery 0.954±0.007 (band reflects numerical and input variability); DC60 ≈ 0.040±0.004.
- +20% lip: recovery 0.964±0.007; DC60 ≈ 0.034±0.004.

These differences exceed the combined uncertainty bands for recovery and are commensurate with the bands for DC60. Across the speed sweep and α values examined, the +20% lip shows consistently better performance. Based on these findings, the larger lip radius is recommended for the prototype inlet for subsequent integrated tests.

## 11. Limitations

- The computational setup uses a simplified AIP outlet boundary and does not include downstream rotating machinery. Redistribution of total pressure and swirl by an actual fan stage is out of scope for this phase.
- Only one bleed setting was explored; bleed schedules can significantly affect separation onset and vortex strength. Further work should probe bleed sensitivity if distortion margins become tight in later phases.
- Sideslip effects and crosswind operation were not examined; the present results are limited to β=0°. If installation drives significant asymmetric loading, additional analysis would be required to characterize off‑design performance.

## 12. Conclusions

The steady RANS assessment for the S‑duct inlet demonstrates:

- Numerical behavior that is consistent across mesh levels with small extrapolated uncertainty for plane‑averaged recovery and modest uncertainty for distortion and swirl.
- Agreement with wind tunnel data at matched speeds and angles of attack that is within a percent for recovery and within a few thousandths for DC60, with recognizable spatial flow structures.
- Sensible sensitivity of outputs to turbulence intensity, mass flow, and incoming boundary layer thickness, without reversal in the ranking of lip variants.

For the purpose of screening inlet lip candidates and guiding instrumentation layout at the AIP under the tested conditions, the CFD approach provides adequate decision support. The +20% lip radius variant is favored on the basis of both predicted and measured improvements in recovery and reduced distortion. Extensions to higher incidence, active bleed strategies, or integrated fan interaction should be addressed with targeted follow‑on studies.

---
Contact: a.s.malik@aero‑group.example  
Supporting files: see appendix for mesh details and monitoring histories.
