# Conjugate Heat Transfer Model Credibility Assessment
## Turbine Blade Internal Cooling Channel Simulation
### Assessment Report — Rev B | Milestone: PDR+6 Weeks

---

## 1. Background and Scope

This report documents the credibility assessment activities performed on the conjugate heat transfer (CHT) simulation suite developed to predict internal cooling channel performance in a high-pressure turbine blade for the LX-7 demonstrator engine program. The simulation environment is based on ANSYS Fluent 2023 R1 with the coupled solid-fluid solver activated, targeting steady-state metal temperature distributions along the pressure-side and suction-side walls of a three-pass serpentine cooling passage.

The primary engineering questions driving this analysis are:

1. What is the predicted peak metal temperature at the leading-edge impingement zone under maximum continuous thrust conditions?
2. How does the coolant-side heat transfer coefficient distribution compare against available legacy rig data from the LX-5 predecessor program?
3. What uncertainty bounds should be applied to metal temperature predictions before these values feed the low-cycle fatigue life model?

This assessment covers the simulation model as configured for the **PDR analysis cycle** (Fluent project file `LX7_CHT_PDR_Rev4.cas`). Work on the film cooling augmentation model is explicitly deferred to CDR and is **not assessed here**. Similarly, the transient thermal model used for engine start/shutdown cycles is out of scope for this review phase — that work is being led by the Oxford subcontractor team and will be assessed separately.

The assessment team consisted of two internal analysts (P. Nakamura, R. Osei) and one independent reviewer (Dr. C. Lindqvist, contracted through AeroThermal Consulting).

---

## 2. Simulation Configuration and Physical Scope

The geometry represents a single blade passage extracted from the 3D CAD assembly (CATIA V5 file `LX7_BLD_GEOM_Rev9`). The solid domain is Rene 80 nickel superalloy; thermal conductivity was assigned as a temperature-dependent polynomial fit (third-order, 300–1200 K) derived from the materials database entry `MAT_R80_TC_v3`, which was validated against published ASM Handbook values to within ±2.1% across the operating range.

The fluid domain uses air as the working coolant, with ideal-gas compressibility enabled. Inlet total pressure and total temperature boundary conditions are drawn from the cycle deck output at the 100% N2 operating point: 42.3 bar and 873 K respectively. The outlet is specified as a pressure outlet at 38.1 bar.

Turbulence is represented using the SST k-ω model with low-Reynolds-number corrections active. This choice was made on the basis of internal benchmarking (memo `INT-TURB-2022-04`) that showed SST k-ω outperforming realizable k-ε and the standard k-ω model against the LX-5 rig data by approximately 8% in area-averaged Nusselt number on the first-pass straight section. The realizable k-ε model overpredicted heat transfer in the bend regions by 14–19%.

Wall treatment uses enhanced wall functions (y+ target of 1–5 on the cooled surfaces, y+ < 30 on the outer shroud). Actual y+ values on the critical pressure-side wall averaged 2.8 in the Rev4 mesh, confirmed via contour plots in Appendix A.

---

## 3. Mesh Refinement Study

A structured mesh was generated using ANSYS Meshing with hexahedral-dominant elements in the fluid passages and a conformally matched tetrahedral mesh in the solid. Three mesh densities were evaluated:

| Mesh Level | Fluid Cells | Solid Cells | Total |
|------------|-------------|-------------|-------|
| Coarse (M1) | 1.2 M | 0.4 M | 1.6 M |
| Medium (M2) | 3.8 M | 1.1 M | 4.9 M |
| Fine (M3) | 9.6 M | 2.7 M | 12.3 M |

The Grid Convergence Index (GCI) methodology per Celik et al. (2008) was applied to three scalar quantities of interest: (a) area-averaged heat flux on the pressure-side wall of pass 1, (b) peak metal temperature at the leading-edge impingement zone, and (c) coolant-side friction factor in pass 2.

Results for the primary QoI (peak metal temperature):

- M1 → M2 change: −18.4 K (−1.6%)
- M2 → M3 change: −4.1 K (−0.36%)
- GCI (fine): 0.71% — well within the 2% threshold adopted for this program

The apparent order of convergence was 2.14, consistent with the second-order upwind scheme used throughout. The medium mesh (M2) was selected as the production mesh on the basis of this study. All subsequent results in this report are from M2 unless otherwise noted.

**Note on solid mesh sensitivity:** The solid domain mesh was refined independently in a subsidiary study. Varying solid mesh density by ±50% around the M2 level changed peak metal temperature by less than 0.8 K, confirming that the overall GCI is dominated by the fluid mesh.

---

## 4. Solver and Code Verification

The Fluent solver itself is a commercial product with an established verification history. For this program, code verification activities focused on confirming that the coupled CHT interface was implemented correctly and that the solid energy equation was being solved with the expected material properties.

A manufactured-solution test was conducted on a simplified 2D fin geometry (rectangular cross-section, uniform heat generation, convective boundary on one face). The analytical solution is well-known; Fluent reproduced the temperature distribution to within 0.03 K RMS across 400 monitoring points, consistent with second-order spatial accuracy. This test is documented in verification report `VR-CHT-001`.

Additionally, the pressure-velocity coupling (SIMPLE algorithm) convergence was confirmed by monitoring residuals to below 1×10⁻⁵ for continuity and momentum, and 1×10⁻⁷ for energy. Mass imbalance across the fluid domain was less than 0.002% at convergence. These thresholds were set based on guidance in the Fluent Theory Guide and prior program experience.

---

## 5. Comparison Against Test Data

### 5.1 Legacy Rig Data (LX-5 Program)

The LX-5 cooling rig (test campaign completed 2019, data archive `LX5_RIG_DATA_v2.xlsx`) provides the primary experimental reference. The rig geometry is geometrically similar to the LX-7 passage at a 1.8× scale, with matched Reynolds number (Re ≈ 24,000 in pass 1) and matched Biot number at the walls. Forty-two thermocouple positions and twelve heat flux gauges are available.

Simulation predictions at matched conditions (LX-5 operating point, not LX-7 design point) were compared against the rig data:

- Area-averaged Nusselt number, pass 1 straight section: predicted 187, measured 194 ± 9 (−3.6%, within measurement uncertainty)
- Area-averaged Nusselt number, first 180° bend: predicted 231, measured 218 ± 14 (+5.9%, within measurement uncertainty)
- Peak thermocouple temperature, leading-edge impingement array: predicted 641 K, measured 648 ± 4 K (−1.1%, within measurement uncertainty)

Overall, 38 of 42 thermocouple predictions fall within the stated ±4 K measurement uncertainty. The four outliers are located near the trip-strip features in pass 3; the simulation does not explicitly resolve the trip-strip geometry (it is modeled using an augmentation factor), and this is a known source of local discrepancy.

### 5.2 Applicability of the LX-5 Data to LX-7 Conditions

The LX-7 design point operates at approximately 2.3× the coolant mass flow rate of the LX-5 rig test, and the wall heat flux is substantially higher due to the increased turbine inlet temperature. An uncertainty contribution from extrapolation outside the validated Reynolds number range (Re_LX5 ≈ 24,000 vs. Re_LX7 ≈ 57,000) has been estimated using the Dittus-Boelter correlation sensitivity and is quantified in §7.

No new rig data specific to LX-7 geometry or operating conditions has been collected to date. A dedicated LX-7 heat transfer rig is planned for the CDR phase; the absence of this data is the primary limitation of the current assessment.

---

## 6. Sensitivity and Uncertainty Quantification

A one-at-a-time (OAT) sensitivity study was performed on seven input parameters judged most influential based on engineering judgment and prior program experience:

| Parameter | Nominal | Perturbation | ΔT_peak (K) |
|-----------|---------|--------------|-------------|
| Coolant inlet total temperature | 873 K | ±10 K | ±6.2 K |
| Coolant inlet total pressure | 42.3 bar | ±0.5 bar | ±2.1 K |
| Rene 80 thermal conductivity | Polynomial fit | ±5% | ±3.8 K |
| Hot-gas-side HTC (boundary) | 4,200 W/m²K | ±15% | ±11.4 K |
| Turbulence intensity at inlet | 5% | 3–8% | ±1.9 K |
| SST model constant (β*) | 0.09 | ±10% | ±0.7 K |
| Trip-strip augmentation factor | 1.35 | ±0.10 | ±4.3 K |

The hot-gas-side heat transfer coefficient applied as the outer-wall boundary condition is the dominant uncertainty driver. This value is taken from a separate RANS simulation of the external hot-gas path; the ±15% uncertainty on that boundary condition propagates to an ±11.4 K uncertainty in peak metal temperature.

A root-sum-square combination of the dominant contributors gives a combined uncertainty estimate of approximately ±15 K (k=1) on the peak metal temperature prediction of 1,087 K at the leading-edge impingement zone.

**Note:** A formal polynomial chaos or Monte Carlo propagation has not been performed for this milestone. The OAT approach is acknowledged to miss interaction effects. This is flagged as a limitation and is planned for the CDR cycle.

---

## 7. Applicability and Extrapolation Assessment

As noted in §5.2, the simulation is being applied at conditions that exceed the validated Reynolds number range. The following factors were considered in assessing the applicability of the model to the LX-7 design point:

- **Reynolds number extrapolation:** The SST k-ω model has published validation data for internal cooling channel flows up to Re ≈ 80,000 in the open literature (Han et al., 2012; Bunker, 2009). The LX-7 Re of 57,000 falls within this broader literature range, though not within the specific LX-5 rig data range. An additional ±8 K uncertainty contribution is assigned for this extrapolation.
- **Geometry differences:** The LX-7 passage includes a novel compound-angle impingement array not present in the LX-5 rig. The simulation models this feature explicitly, but no experimental validation data exists for this specific configuration. This is the most significant applicability gap and is flagged as a high-priority item for the CDR rig test.
- **Rotation effects:** The LX-7 operating environment involves blade rotation at approximately 12,400 RPM. The current model is a stationary passage simulation; rotational buoyancy and Coriolis effects on the coolant flow are not represented. Literature correlations (Johnson et al., 2014) suggest these effects can modify local heat transfer by 10–25% in radially outward passes. This limitation is explicitly noted; quantification is deferred to CDR.

---

## 8. Credibility Summary

Based on the activities described above, the following assessment is offered for the primary quantity of interest (peak metal temperature at the leading-edge impingement zone):

The mesh refinement study demonstrates good numerical convergence (GCI < 1%) and the solver verification activities confirm correct implementation of the CHT coupling. Comparison against the LX-5 legacy rig data shows agreement within measurement uncertainty for the majority of monitored locations, providing moderate confidence in the model's representation of internal convective heat transfer physics.

The primary limitations reducing confidence in the LX-7 design-point prediction are:

1. Absence of validation data at LX-7-specific conditions (Re, geometry, heat flux levels)
2. The compound-angle impingement array is unvalidated
3. Rotation effects are not modeled
4. The hot-gas-side boundary condition carries ±15% uncertainty, which is the dominant driver of prediction uncertainty

The combined uncertainty on peak metal temperature (±15 K at k=1, expanding to approximately ±23 K at k=1.5 when the extrapolation contribution is included) should be applied as a margin in the life model inputs.

**Recommended use:** The current model is judged adequate to support PDR-level design decisions (material selection, passage geometry trade studies) but is **not** adequate to support final life certification without the CDR rig data and incorporation of rotation effects.

---

## 9. Limitations and Deferred Items

The following items were explicitly out of scope for this assessment and are not addressed:

- Film cooling augmentation model (CDR milestone, Oxford subcontractor)
- Transient thermal model for start/shutdown cycles (CDR milestone)
- Probabilistic uncertainty propagation beyond OAT sensitivity (CDR milestone)
- Assessment of the external hot-gas-path simulation that provides the outer-wall boundary condition (separate assessment, `REPORT-EXT-CHT-002`, in progress)
- Documentation of the simulation team's training records and qualification status — this was flagged by Dr. Lindqvist during the independent review as an item that should be addressed before CDR; it was not available for review at the time this report was finalized

---

## References

1. Celik, I.B. et al. (2008). "Procedure for Estimation and Reporting of Uncertainty Due to Discretization in CFD Applications." *ASME J. Fluids Eng.*, 130(7).
2. Han, J.C., Dutta, S., Ekkad, S. (2012). *Gas Turbine Heat Transfer and Cooling Technology*, 2nd ed. CRC Press.
3. Bunker, R.S. (2009). "The Effects of Manufacturing Tolerances on Gas Turbine Cooling." *ASME J. Turbomachinery*, 131(4).
4. Johnson, B.V. et al. (2014). "Heat Transfer in Rotating Serpentine Passages with Selected Model Orientations." NASA CR-2014-218096.
5. ANSYS Fluent Theory Guide, Release 2023 R1.
6. ASM Handbook, Volume 2: Properties and Selection — Nonferrous Alloys and Special-Purpose Materials.

---

*Report prepared by: P. Nakamura, R. Osei*
*Independent review: Dr. C. Lindqvist, AeroThermal Consulting*
*Date: 14 March 2024 | Document number: LX7-CHT-CA-007-RevB*
