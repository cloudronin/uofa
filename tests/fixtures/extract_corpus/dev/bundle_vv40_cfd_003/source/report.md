# CFD Credibility Assessment – Axial Fan Stage Aerodynamics
## Internal Review Slide Deck | Rev B | Project: VENTCORE-7 | Prepared by: Aero-Thermal Methods Group

---

## Slide 1 – Overview & Purpose

- **Scope of this review**
  - Assess the readiness of the VENTCORE-7 axial fan stage CFD model for use in design decisions at 70–110% of nominal flow coefficient
  - Model developed in ANSYS Fluent 2023 R1; steady-state RANS with k-ω SST turbulence closure
  - Geometry: 9-blade rotor + 11-vane stator, 1.2 m tip diameter, design point 14,000 m³/hr at 850 Pa total-to-total pressure rise
- **Review basis**
  - Internal simulation reports SIM-VCF-001 through SIM-VCF-008
  - Experimental campaign at TU Braunschweig low-speed wind tunnel (Test Reports TB-2023-44 and TB-2023-45)
  - Analyst interview notes (Dec 2023)
- **Intended use of the model**
  - Rank candidate blade sweep geometries (not absolute performance certification)
  - Predict stall inception margin to ±5% accuracy relative to measured characteristic
- **Caution flags identified during review**
  - Several areas carry contradictory or insufficiently supported evidence — flagged with ⚠️ throughout

---

## Slide 2 – Problem Definition & Governing Equations

- **Physical phenomena targeted**
  - Incompressible, turbulent, swirling internal flow; tip leakage; rotor-stator interaction (modelled via mixing plane)
  - Mach number at tip ≈ 0.18 — compressibility effects deemed negligible; no justification document found ⚠️
- **Governing equations**
  - Reynolds-averaged Navier-Stokes with SST two-equation closure; rotating reference frame (MRF)
  - Energy equation deactivated — acceptable given isothermal assumption, but the assumption is stated in SIM-VCF-001 without supporting sensitivity analysis
- **Boundary condition specification**
  - Inlet: uniform total pressure (101,325 Pa), turbulence intensity 3%, hydraulic diameter 1.18 m
  - Outlet: mass-flow rate prescribed; value derived from orifice plate calibration (±1.5% uncertainty per TB-2023-44)
  - Walls: no-slip, smooth; hub and casing treated as stationary in absolute frame — consistent with physical setup
- **Rotation**
  - Rotor domain: 1,450 rpm; centrifugal and Coriolis source terms confirmed active in solver log files
- **Assessment**
  - Problem statement is reasonably complete for the intended ranking use; the missing compressibility justification is a minor gap at this Mach regime

---

## Slide 3 – Software & Solver Pedigree

- **Solver identity**
  - ANSYS Fluent 2023 R1, double-precision, pressure-based coupled solver
  - License held by the performing organisation; version control confirmed via solver header in output files
- **Prior validation history of the solver**
  - Fluent has an extensive published validation base for turbomachinery RANS (AGARD AR-355, NASA TM-2003-212600)
  - Project team did NOT conduct independent code-level verification tests (e.g., manufactured solution, Taylor-Green vortex benchmark) — reliance is entirely on vendor documentation ⚠️
  - Vendor release notes for 2023 R1 cite one known issue with MRF frame acceleration terms in highly skewed cells; team confirmed mesh quality metrics are within acceptable bounds but did not explicitly test this defect scenario
- **User qualification**
  - Lead analyst: 8 years CFD experience, 4 turbomachinery projects; peer reviewer: 5 years, external consultant
  - No formal competency record on file; verbal confirmation only ⚠️ (contradicts the project quality plan, which requires documented analyst qualification per QP-AERO-03)
- **Assessment**
  - Solver choice is appropriate; the gap in independent code-level checks is partially mitigated by the solver's broad literature record, but the analyst qualification documentation gap should be closed before design freeze

---

## Slide 4 – Geometry & Computational Domain Fidelity

- **CAD-to-mesh fidelity**
  - Blade profiles imported from CATIA V5 STEP files; leading-edge radii verified against CMM data (max deviation 0.12 mm, well within tolerance)
  - Tip clearance modelled at 0.8 mm (nominal); manufacturing tolerance is ±0.15 mm — sensitivity to clearance variation not yet studied ⚠️
- **Domain extent**
  - 1.5-chord inlet extension upstream of rotor leading edge; 2-chord downstream of stator trailing edge
  - Periodic sector: 1 rotor passage + 1 stator passage (non-integer blade count ratio handled via pitch-change scaling at mixing plane — standard practice, acknowledged limitation)
- **Simplifications**
  - Spinner nose fairing geometry simplified to axisymmetric cone; actual part has three mounting bosses — local flow distortion not captured
  - Bleed holes on casing omitted; confirmed negligible by separate 2D axisymmetric test (SIM-VCF-003)
- **Assessment**
  - Geometry representation is adequate for ranking purposes; tip clearance sensitivity and spinner boss effects are known open items

---

## Slide 5 – Mesh Quality & Refinement Study

- **Mesh generation**
  - Structured hexahedral mesh via ANSYS TurboGrid 2023 R1; O-grid topology around blade surfaces
  - Rotor passage: 2.1 M cells; stator passage: 1.4 M cells; total (full-annulus equivalent): ~30 M cells
  - y⁺ target: 1.0 on blade surfaces (SST low-Re mode); achieved mean y⁺ = 0.92, max y⁺ = 2.4 on rotor suction-side near tip
- **Mesh convergence evidence**
  - Three mesh levels run: coarse (0.7M/passage), medium (2.1M/passage), fine (5.8M/passage)
  - GCI (Grid Convergence Index, Celik et al. 2008) computed for total-to-total pressure rise at design point:
    - GCI_fine = 1.3% — within acceptable range for design-phase work
  - **However**: SIM-VCF-007 (stall-point prediction) uses only the medium mesh and states "mesh sensitivity confirmed" — this is inconsistent with the GCI study, which was only performed at the design point, not near stall ⚠️
  - Near-stall flow features (leading-edge separation, tip vortex breakdown) are known to be mesh-sensitive; no refinement study exists for off-design conditions
- **Skewness / orthogonality**
  - Max skewness 0.61 (TurboGrid report); mean 0.18 — acceptable per Fluent best-practice guidelines
- **Assessment**
  - Design-point mesh quality is well-documented; the claim of mesh-independence for stall prediction is unsupported and represents a significant credibility gap for one of the two stated use cases

---

## Slide 6 – Solver Convergence & Numerical Settings

- **Convergence criteria**
  - Residual targets: 1×10⁻⁵ for continuity, momentum, k, ω
  - Mass imbalance across mixing plane monitored; target <0.01% — achieved in all design-point cases
  - Integrated quantities (pressure rise, torque) monitored over last 500 iterations for flatness
- **Evidence of convergence**
  - Residual histories provided in SIM-VCF-002 appendix; all design-point cases show monotonic decay to target
  - **Contradiction**: SIM-VCF-007 (near-stall, 72% flow coefficient) shows continuity residual plateauing at ~8×10⁻⁴; report text states "converged solution obtained" ⚠️
    - Reviewer notes: this residual level is two orders of magnitude above target; the pressure-rise value reported may not represent a true steady-state solution
    - The near-stall characteristic point is used directly in the stall margin estimate without caveat
- **Discretisation schemes**
  - Second-order upwind for momentum and turbulence quantities; SIMPLEC pressure-velocity coupling
  - No justification provided for scheme selection beyond "default second-order" — adequate but undocumented
- **Assessment**
  - Convergence evidence is solid for on-design conditions; the near-stall case has a serious unresolved convergence issue that directly undermines the stall-margin use case

---

## Slide 7 – Turbulence Modelling Choices

- **Model selected: k-ω SST**
  - Appropriate for attached and mildly separated boundary layers; known to overpredict separation bubble extent in strongly adverse pressure gradient regions
  - No alternative turbulence model runs performed; no sensitivity study documented
- **Wall treatment**
  - Low-Reynolds formulation (y⁺ ≈ 1) — consistent with SST guidelines; commendable
- **Transition effects**
  - Fully turbulent assumption applied throughout; no γ-Reθ transition model used
  - At design-point chord Reynolds number ~4.5×10⁵, laminar-turbulent transition on blade suction side is plausible
  - SIM-VCF-001 acknowledges this but concludes "transition effects are secondary for this application" without quantitative support
- **LES / higher-fidelity comparison**
  - No LES or DES reference solution available; team noted budget constraints precluded this
- **Assessment**
  - SST is a defensible choice for the ranking application; the absence of any turbulence model sensitivity study is a moderate gap; transition modelling omission is acknowledged but unquantified

---

## Slide 8 – Boundary Condition Uncertainty & Sensitivity

- **Inlet turbulence intensity**
  - Specified as 3%; hot-wire measurements in TB-2023-44 report 2.8% ± 0.4% at the measurement plane 0.5 m upstream of rotor
  - No CFD sensitivity run varying Tu from 2.4% to 3.2% — gap noted
- **Outlet boundary condition**
  - Mass-flow prescription is clean; no recirculation detected at outlet plane in any converged case
- **Rotational speed uncertainty**
  - Test rig speed controlled to ±2 rpm (0.14%); modelled at exact nominal — acceptable
- **Tip clearance (repeated from Slide 4)**
  - 0.8 mm nominal; no sensitivity run — this gap affects both geometry fidelity and effective boundary condition representation
- **Atmospheric conditions**
  - Test conducted at 98.2 kPa ambient (Braunschweig altitude); CFD inlet set to 101,325 Pa ⚠️
    - SIM-VCF-005 notes this discrepancy and applies a density correction to experimental data — but the correction methodology is not described in sufficient detail to assess its validity
    - This affects the absolute pressure-rise comparison; for non-dimensional coefficient comparison the impact is second-order
- **Assessment**
  - Boundary conditions are generally well-defined; the atmospheric pressure correction is an under-documented source of systematic bias in the validation comparison

---

## Slide 9 – Validation Against Experimental Data

- **Experimental dataset**
  - TU Braunschweig five-hole probe traverses at rotor exit (radial profiles, 10 operating points)
  - Facility uncertainty: total pressure ±12 Pa, flow angle ±0.4°, velocity ±0.8% (TB-2023-44 §4.2)
- **Comparison metrics**
  - Total-to-total pressure rise coefficient ψ: CFD vs. experiment across 80–110% flow coefficient
  - Radial profiles of total pressure and yaw angle at rotor exit (design point only)
- **Quantitative agreement**
  - ψ at design point: CFD 0.412, experiment 0.408 — 1.0% difference, within experimental uncertainty
  - ψ at 80% flow coefficient: CFD 0.501, experiment 0.478 — **4.8% difference**, outside experimental uncertainty band
  - Radial profile of total pressure: CFD over-predicts hub-side loading by ~7% — attributed to secondary flow modelling limitation, not further investigated
- **Stall point**
  - CFD predicts stall at 68% flow coefficient; experiment shows stall onset at 74% ⚠️
    - SIM-VCF-007 presents this as "good agreement (within 10%)" — but the stated use-case accuracy requirement is ±5%
    - The convergence issue noted on Slide 6 further undermines confidence in this prediction
- **Validation domain**
  - Validation data exist only for one tip clearance (0.8 mm) and one rotational speed — limited coverage of the design space
- **Assessment**
  - On-design validation is satisfactory for a ranking tool; off-design and stall-point predictions are not adequately validated for the stated ±5% accuracy requirement

---

## Slide 10 – Uncertainty Quantification Approach

- **What was done**
  - GCI-based numerical uncertainty at design point (Slide 5)
  - Experimental measurement uncertainty quoted from facility calibration records
  - No formal propagation of input uncertainty (tip clearance, Tu, blade profile tolerance) through to output quantities
- **What was not done**
  - No Monte Carlo or polynomial chaos expansion for parametric uncertainty
  - No sensitivity indices (Sobol or otherwise) computed
  - The validation comparison in SIM-VCF-005 presents only point estimates with no combined uncertainty band — making it difficult to judge whether CFD-experiment differences are meaningful
- **Stated uncertainty in summary report**
  - SIM-VCF-008 executive summary claims "total model uncertainty ±3% on pressure rise" — this figure appears to be an engineering judgement, not a traceable calculation ⚠️
    - No supporting worksheet or methodology reference is provided
    - This contradicts the 4.8% discrepancy observed at 80% flow coefficient (which alone exceeds the claimed total uncertainty)
- **Assessment**
  - Uncertainty quantification is superficial; the headline ±3% claim is not credible given observable evidence to the contrary; this is the most significant credibility concern in the bundle

---

## Slide 11 – Documentation & Traceability

- **Simulation records**
  - Case files archived in project SharePoint (VENTCORE-7/CFD/Cases/); naming convention consistent with SIM-VCF-001 index
  - Input decks (journal files) version-controlled in Git repository; commit hashes referenced in SIM-VCF reports
  - Mesh files archived as .msh.gz; TurboGrid project files retained
- **Reproducibility**
  - Reviewer was able to rerun the design-point case (medium mesh) and reproduce reported ψ within 0.1% — positive indicator
  - Near-stall case (SIM-VCF-007) journal file references a geometry file "rotor_v4_final_FINAL.stp" that does not match the archived STEP file name; possible version mismatch ⚠️
    - Team verbal confirmation that the geometry is the same, but no formal reconciliation documented
- **Change log**
  - SIM-VCF reports carry revision history; changes between Rev A and Rev B are itemised — good practice
- **Assessment**
  - Documentation is above average for a design-phase project; the geometry file discrepancy in the near-stall case should be formally resolved

---

## Slide 12 – Intended Use Alignment & Extrapolation Risk

- **Use Case 1: Blade sweep ranking**
  - Model runs planned for 6 candidate geometries at design point and 90% flow coefficient
  - On-design validation (Slide 9) supports this use; ranking is a relative comparison, reducing sensitivity to absolute bias
  - **Risk**: if sweep changes shift the stall margin significantly, the off-design limitation becomes relevant
- **Use Case 2: Stall margin prediction to ±5%**
  - Current evidence does NOT support this claim (6-point stall underprediction, unconverged near-stall solution, unvalidated mesh at off-design)
  - Recommend this use case be downgraded to qualitative / trend-only until convergence and mesh issues are resolved
- **Extrapolation beyond validated range**
  - Model has not been run or validated at rotational speeds other than 1,450 rpm; any off-speed predictions would be extrapolations
  - Tip clearance sensitivity unstudied — if manufacturing produces 0.65 mm or 0.95 mm clearance, model applicability is unknown
- **Assessment**
  - Use Case 1 is credible at current state; Use Case 2 is not — this distinction must be communicated clearly to the design team

---

## Slide 13 – Summary Scorecard (Reviewer Assessment)

| Area | Evidence Quality | Key Gap |
|---|---|---|
| Problem formulation | Adequate | Compressibility justification missing |
| Solver pedigree | Moderate | No independent code checks; analyst quals undocumented |
| Geometry fidelity | Adequate | Tip clearance sensitivity open |
| Mesh / discretisation | Adequate (design pt) / Poor (off-design) | No GCI near stall |
| Solver convergence | Good (design pt) / Unacceptable (near-stall) | Unconverged stall case presented as valid |
| Turbulence modelling | Adequate | No sensitivity study |
| Boundary conditions | Adequate | Atmospheric correction under-documented |
| Experimental validation | Good (design pt) / Poor (stall) | Stall error exceeds stated requirement |
| Uncertainty quantification | Poor | ±3% claim unsupported; contradicted by data |
| Documentation | Good | Geometry file discrepancy in near-stall case |

- **Overall credibility for Use Case 1 (ranking):** MODERATE — acceptable for design decisions with stated caveats
- **Overall credibility for Use Case 2 (stall margin ±5%):** LOW — not currently supported; remediation required

---

## Slide 14 – Recommended Remediation Actions

- **Priority 1 (before next design gate)**
  - Resolve convergence of near-stall case — consider transient (URANS) approach; steady RANS may be fundamentally inadequate at 72% flow coefficient
  - Perform mesh refinement study at 80% and 72% flow coefficients; compute GCI for off-design ψ
  - Reconcile geometry file discrepancy in SIM-VCF-007; issue formal errata

- **Priority 2 (within 4 weeks)**
  - Document analyst qualification records per QP-AERO-03
  - Provide traceable calculation supporting the ±3% uncertainty claim or withdraw it from SIM-VCF-008
  - Run tip clearance sensitivity (±0.15 mm) at design point

- **Priority 3 (before any off-speed use)**
  - Validate at second operating speed (e.g., 1,200 rpm) if speed variation is within the design space
  - Document compressibility justification for tip Mach number

- **No action required**
  - Design-point mesh quality, y⁺ compliance, and archival practices are satisfactory

---

## Slide 15 – References & Document Index

- SIM-VCF-001 through SIM-VCF-008 — VENTCORE-7 CFD Simulation Reports (Rev B, Dec 2023)
- TB-2023-44 — TU Braunschweig Five-Hole Probe Traverse Test Report, VENTCORE-7 Fan Stage
- TB-2023-45 — TU Braunschweig Facility Calibration & Uncertainty Report
- QP-AERO-03 — Aero-Thermal Methods Group Quality Plan, Analyst Competency Requirements
- Celik, I.B. et al. (2008) "Procedure for Estimation and Reporting of Uncertainty Due to Discretization in CFD Applications," *ASME J. Fluids Eng.* 130(7)
- AGARD AR-355 — "CFD Validation for Propulsion System Components"
- ANSYS Fluent 2023 R1 User's Guide & Release Notes
- Menter, F.R. (1994) "Two-Equation Eddy-Viscosity Turbulence Models for Engineering Applications," *AIAA J.* 32(8)

---
*Prepared by: Aero-Thermal Methods Group | Review date: 15 January 2024 | Next review trigger: design gate DG-3 or any geometry change exceeding 2% chord modification*
