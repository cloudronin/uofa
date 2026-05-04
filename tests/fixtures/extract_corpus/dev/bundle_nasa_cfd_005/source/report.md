# Credibility Assessment Report
## CFD Analysis of Centrifugal Pump Stage — Hydraulic Performance Prediction
### Project: WP-4400 Multistage Pump V&V Activity
### Revision: B | Date: 2024-03-14 | Prepared by: Fluid Systems Analysis Group

---

## 1. Background and Purpose

This report documents the credibility assessment activities performed on the Reynolds-Averaged Navier–Stokes (RANS) computational fluid dynamics model used to predict hydraulic performance of the WP-4400 three-stage centrifugal pump. The simulation campaign was conducted in support of the pump's hydraulic redesign, specifically targeting head-rise curve prediction across a flow range of 40–160% of best efficiency point (BEP). The solver employed was ANSYS Fluent 2023 R1, with the SST k-ω turbulence closure selected based on prior internal benchmarking for similar impeller geometries.

The assessment framework applied here follows internal procedure IP-CFD-007, which is aligned with recognized simulation credibility practices for engineering decision-making. The intent is to establish confidence in the model outputs sufficient to support pump selection decisions without requiring a full-scale prototype test at this stage of the program.

Factors not addressed in this report — specifically those relating to software quality assurance records from the solver vendor and the formal uncertainty apportionment across the full system model — are deferred to Phase 2, pending receipt of documentation from ANSYS and completion of the system-level uncertainty rollup by the thermal-hydraulic team.

---

## 2. Scope Definition and Model Intended Use

### 2.1 What the Model Is Asked to Do

The CFD model is used to predict:

- Total head rise (H) vs. volumetric flow rate (Q) across the operating envelope
- Shaft power consumption at BEP ± 30%
- Internal recirculation onset flow rate (estimated to ±5% of BEP)

The primary decision the model supports is selection of impeller trim diameter (range: 285–310 mm) to achieve a target head of 142 m at BEP. Secondary outputs — including internal velocity distributions and pressure recovery in the diffuser — are considered supporting information only and are not used directly in the trim selection decision.

### 2.2 Bounding the Problem

The model scope is explicitly limited to single-phase, steady-state, isothermal operation at 20°C water. Cavitation inception prediction, transient rotor-stator interaction, and off-design surge behavior are outside scope for this phase. These exclusions are documented in Model Scope Record MSR-4400-02.

The operating conditions of interest span shaft speeds of 2,950–3,050 RPM (nominal 2,985 RPM) and flow rates from 18 m³/h to 72 m³/h per stage. These bounds are well within the range of validated RANS applicability for this class of turbomachinery geometry.

---

## 3. Geometry and Computational Domain

The impeller and diffuser geometry was imported from the CAD release (CATIA V5, file revision 14C). A comparison between the as-modeled geometry and the engineering drawing dimensions was performed for 12 critical features (blade inlet angle, outlet angle, passage width at hub and shroud, and diffuser vane spacing). Maximum deviation observed was 0.3 mm on the shroud trailing edge fillet, which was judged inconsequential for bulk performance prediction. Seal clearances were modeled using a simplified annular gap rather than the full labyrinth geometry — this is a known simplification that may introduce a small systematic bias in predicted volumetric efficiency, estimated at <0.5% based on correlations from Gülich (2008).

The computational domain encompasses one impeller passage (1/7 periodicity), the full vaneless space, and one diffuser passage (1/8 periodicity), connected via mixing plane interfaces. A full 360° model was not used at this stage due to computational resource constraints; the implications of this choice on circumferential non-uniformity are acknowledged but considered secondary for the intended use.

---

## 4. Mesh Refinement Study

A systematic grid sensitivity study was conducted using three structured hexahedral meshes generated in ANSYS TurboGrid 2023 R1:

| Mesh Level | Node Count | y⁺ (avg) | Predicted H at BEP (m) |
|---|---|---|---|
| Coarse | 1.2 M | 38 | 147.3 |
| Medium | 3.8 M | 12 | 143.6 |
| Fine | 9.1 M | 4.2 | 142.8 |

The Grid Convergence Index (GCI) was computed following the Roache methodology using the fine and medium meshes. The GCI for head prediction at BEP was 0.9%, indicating that the medium mesh solution is within approximately 1.3 m of the asymptotic value. The observed order of convergence was 1.87, consistent with the second-order upwind discretization scheme employed.

The fine mesh was selected for all production runs. Wall y⁺ values on the fine mesh remain below 5 across 94% of wetted surfaces, satisfying the SST k-ω low-Reynolds treatment requirements. Localized y⁺ exceedances (up to 11) were noted near the impeller leading edge suction side at low-flow conditions; these regions are flagged as having elevated numerical uncertainty.

Residual convergence was monitored for all equations; mass and momentum residuals reached 10⁻⁵ or lower for all operating points. Integrated torque and head were additionally monitored for iteration stability, with variation less than 0.1% over the final 500 iterations.

---

## 5. Physics and Boundary Condition Fidelity

### 5.1 Turbulence Modeling Choice

The SST k-ω model was selected based on its established performance for adverse pressure gradient flows in diffusing passages. Internal benchmarking data (report INT-TURB-2021-04) showed SST k-ω predicting head within 2.1% of measured data for three geometrically similar impellers tested on the company's hydraulic test rig. An alternative LES approach was evaluated conceptually but rejected for this phase due to the approximately 40× increase in compute cost and the steady-state nature of the intended use.

Turbulence intensity at the inlet boundary was set to 5% with a turbulent length scale of 10% of the hydraulic diameter, consistent with upstream piping conditions in the installed configuration. Sensitivity of the head prediction to inlet turbulence intensity (range 2–8%) was assessed; the effect on BEP head was less than 0.4 m, which is within the stated model uncertainty.

### 5.2 Boundary Conditions

- **Inlet:** Mass flow rate specified (varied per operating point), total temperature 293 K
- **Outlet:** Static pressure (atmospheric reference), area-averaged
- **Walls:** No-slip, hydraulically smooth (Ra < 0.8 µm per manufacturing spec)
- **Periodic interfaces:** Rotational periodicity, 51.4° (impeller), 45° (diffuser)
- **Mixing plane:** Conservative flux interpolation, pitch-change ratio 7:8

Wall roughness was modeled as hydraulically smooth based on the manufacturing specification. However, it should be noted that actual surface roughness measurements from production parts were not available at the time of this analysis. If as-built roughness exceeds approximately 6 µm equivalent sand roughness, a correction to predicted efficiency of up to 1.2 percentage points may be required. This is flagged as a residual uncertainty item.

---

## 6. Comparison Against Test Data

### 6.1 Available Validation Data

Experimental data were obtained from a single-stage hydraulic performance test conducted on the WP-4400 prototype (Stage 1 only) at the company's ISO 9906 Grade 1 certified test facility. Test data cover 11 flow points from 20 m³/h to 68 m³/h. Measurement uncertainties were formally quantified per ISO 9906: flow rate ±0.7%, head ±1.1%, shaft power ±1.5% (all at 95% confidence).

### 6.2 Simulation-to-Test Agreement

Head-rise curve comparison:

| Flow (m³/h) | Test H (m) | CFD H (m) | Difference |
|---|---|---|---|
| 20 | 162.4 ± 1.8 | 165.1 | +1.7% |
| 36 (BEP) | 142.1 ± 1.6 | 143.6 | +1.1% |
| 54 | 118.3 ± 1.3 | 120.4 | +1.8% |
| 68 | 97.6 ± 1.1 | 96.2 | −1.4% |

Shaft power agreement was within 2.3% across all flow points. The CFD model systematically over-predicts head at low-flow conditions by approximately 1.5–2%, which is consistent with the known limitation of steady-state RANS in capturing the increased recirculation losses at part-load. This systematic offset is within the stated model uncertainty band and does not affect the intended use (trim selection at or near BEP).

### 6.3 Assessment of Validation Coverage

The validation dataset covers the primary operating range of interest (BEP ± 30%) with good spatial coverage of the H-Q curve. However, validation data are available for Stage 1 geometry only; Stages 2 and 3 share identical hydraulic geometry, so the validation is considered transferable, though this assumption introduces a small additional uncertainty not formally quantified here.

No validation data are available for shaft vibration, bearing loads, or internal flow visualization. These are outside the model's intended use and are not assessed here.

---

## 7. Sensitivity and Uncertainty Characterization

A one-at-a-time sensitivity study was conducted for the following input parameters, evaluating effect on predicted BEP head:

| Parameter | Nominal | Perturbation | ΔHBEP |
|---|---|---|---|
| Inlet turbulence intensity | 5% | ±3% | ±0.4 m |
| Wall roughness (smooth→6 µm) | 0 µm | +6 µm | −1.8 m |
| Impeller tip clearance | 0.3 mm | +0.15 mm | −0.9 m |
| Mixing plane axial position | nominal | ±2 mm | ±0.3 m |

The dominant uncertainty contributor is wall roughness, for which as-built data are unavailable. A combined expanded uncertainty (k=2) for the model prediction of BEP head is estimated at ±3.8 m (approximately ±2.7%), accounting for numerical discretization uncertainty (GCI-derived), input parameter uncertainty, and model-form uncertainty (estimated from the turbulence model benchmarking study).

This uncertainty is judged adequate for the trim selection decision, where the acceptable head tolerance is ±5 m from the 142 m target.

---

## 8. Personnel Qualifications and Review Process

The simulation work was performed by two engineers: a lead analyst (8 years CFD experience in turbomachinery, internal certification level CFD-3) and a supporting analyst (3 years experience, CFD-2 certified). Model setup, mesh generation, and post-processing were independently reviewed by a senior engineer not involved in the original analysis (15 years experience, CFD-4). The review covered boundary condition assignments, mesh quality metrics, and comparison methodology.

An independent check of the GCI calculation was performed by the V&V coordinator. No significant errors were identified in the review process. The review records are archived in the project document management system under WP-4400-VVR-003.

---

## 9. Limitations and Items Deferred to Phase 2

The following items are explicitly out of scope for this assessment and will be addressed in the Phase 2 credibility package:

1. **Solver vendor quality records:** ANSYS quality management documentation (ISO 9001 compliance, regression test suite coverage) has been requested but not yet received. This item is tracked as open action OA-4400-11.

2. **System-level uncertainty rollup:** Integration of this CFD model's uncertainty into the full pump system model (including motor, coupling, and piping losses) is deferred to the system V&V activity planned for Q3 2024.

3. **Transient and multi-phase behavior:** Cavitation, rotor-stator interaction harmonics, and surge onset are not addressed by this model and will require separate analysis activities if design requirements expand to include these phenomena.

4. **Formal assessment of prior simulation campaigns:** Historical CFD analyses of earlier WP-series pump designs were not formally reviewed for applicability to this assessment. Incorporation of that legacy data into a structured pedigree review is planned but not complete.

---

## 10. Overall Credibility Summary

Based on the activities documented in this report, the CFD model of the WP-4400 pump stage is assessed as providing **adequate credibility for the intended use** of impeller trim diameter selection. The key basis for this conclusion is:

- Grid convergence demonstrated with GCI < 1% at BEP
- Validation agreement within ±2% across the primary operating range
- Uncertainty band (±2.7%) comfortably within the decision tolerance (±3.5%)
- Qualified personnel with independent review completed

Areas of residual concern — primarily the unknown as-built surface roughness and the single-stage validation basis — are acknowledged and bounded. They do not alter the overall adequacy finding for the current decision context.

This assessment does **not** constitute approval for use of this model to support decisions beyond impeller trim selection (e.g., structural loading, rotordynamic analysis, or cavitation performance prediction) without additional V&V activities.

---

*Report prepared by: Fluid Systems Analysis Group*
*Reviewed by: Senior V&V Engineer, WP-4400 Program*
*Distribution: WP-4400 Chief Engineer, Hydraulic Design Lead, V&V Coordinator*
