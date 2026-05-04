# Structural FEA Credibility Review — Titanium Spinal Cage Implant Assembly
## Internal V&V Slide Deck | Project VERTEC-3 | Rev B | 2024-03-14

---

## Slide 1: Overview & Scope

- **Model under review:** ABAQUS/Standard 2023.HF4 finite-element model of a PEEK-Ti composite lumbar interbody fusion cage (VERTEC-3 device)
- **Analysis type:** Quasi-static compressive loading + cyclic fatigue pre-screening; linear-elastic and elastic-plastic material regimes
- **Intended use of model outputs:**
  - Predict peak von Mises stress and subsidence force under 1800 N compressive load (worst-case patient scenario per ASTM F2077)
  - Support 510(k) submission as computational evidence per FDA guidance on computational modeling
- **Review team:** 3 internal analysts, 1 external biomechanics consultant (Dr. R. Halvorsen, TechMed Consulting)
- **This deck documents the current state of credibility evidence — several areas flagged as requiring resolution before regulatory submission**

---

## Slide 2: Geometry & Model Scope Decisions

- CAD source: SOLIDWORKS 2023 assembly exported to STEP; imported into ABAQUS via SimScale pre-processing bridge
  - **Note:** Two minor geometric simplifications applied
    - Internal lattice strut fillets (r = 0.15 mm) suppressed — analyst judgment that stress contribution negligible
    - Bone graft window chamfers idealized to sharp edges in mesh — *this decision is not formally documented in the model log and was flagged by external reviewer*
- Endplate contact surfaces retained at full resolution; cortical shell modeled as discrete 1.2 mm shell layer
- **Scope boundary:** Vertebral body modeled as rigid analytical surface in primary runs — deformable bone model deferred to Phase 2
  - This boundary condition choice is consequential and discussed further in Slide 7

---

## Slide 3: Software & Solver Pedigree

- **Solver:** ABAQUS/Standard 2023.HF4 (Dassault Systèmes)
  - Widely used in orthopaedic FEA; implicit solver with full Newton-Raphson iteration
  - Dassault publishes benchmark suite results annually; internal IT team confirmed installation qualification (IQ) completed Feb 2024
- **Element library:** C3D10 (10-node quadratic tetrahedral) for cage body; S4R shell elements for cortical endplate representation
  - *Slide 9 revisits element choice — there is a discrepancy between this selection and what is described in the mesh convergence documentation*
- **Contact algorithm:** Surface-to-surface, finite sliding, penalty stiffness = 1×10⁵ N/mm
- **Code correctness checks:**
  - Simple patch test performed on single-element cube: passed to within 0.01% of analytical solution
  - Hertzian contact benchmark (sphere-on-flat, R=5mm, E=110 GPa): FEA peak pressure within 2.3% of closed-form — acceptable
  - No formal regression test suite maintained; analyst relies on benchmark re-runs when solver version changes — *gap noted*

---

## Slide 4: Material Inputs & Uncertainty

- **Titanium alloy (Ti-6Al-4V ELI):**
  - E = 114 GPa, ν = 0.33, σ_y = 880 MPa (per ASTM F136 certificate lot data)
  - Plastic hardening curve from internal coupon testing (n=6 specimens, 3-point bend + tensile); data scatter ±4%
- **PEEK (Invibio PEEK-OPTIMA HA30):**
  - E = 18 GPa, ν = 0.39 — sourced from Invibio datasheet, not independently tested
  - *Datasheet value is for dry-as-molded; no moisture conditioning correction applied despite cage being implanted in wet environment — flagged as potential non-conservatism*
- **Bone substitute (rigid surface assumption):** No material uncertainty quantification performed for primary load case — sensitivity study planned but not completed
- **Summary:** Material inputs for metallic components are well-characterized; polymer and biological tissue inputs carry unquantified uncertainty that is not propagated through the model

---

## Slide 5: Loading & Boundary Conditions

- Applied load: 1800 N axial compression, distributed over superior endplate via rigid platen (per ASTM F2077 test configuration)
- Inferior endplate: fully encastred (all 6 DOF fixed)
- Lateral shear load case (450 N): also run but results not yet peer-reviewed internally
- **Physiological relevance:**
  - ASTM F2077 loading is a standardized mechanical test protocol — it does not fully represent in vivo loading (combined compression + bending + torsion during activities of daily living)
  - Model team acknowledges this limitation; no attempt to bound in vivo loads has been made in this revision
  - *External reviewer noted that the 1800 N load may be non-conservative for obese patient population (BMI > 40) — response from model team pending*

---

## Slide 6: Mesh Refinement Study

- **Three mesh densities evaluated:**

  | Mesh ID | Global seed (mm) | Elements | Peak σ_VM (MPa) | Change vs. prior |
  |---------|-----------------|----------|-----------------|-----------------|
  | M1 (coarse) | 1.5 | 48,320 | 623 | — |
  | M2 (medium) | 0.8 | 187,450 | 701 | +12.5% |
  | M3 (fine) | 0.4 | 694,200 | 718 | +2.4% |

- Richardson extrapolation applied between M2 and M3: extrapolated value = 724 MPa; GCI = 1.1% — convergence deemed acceptable
- **However:** M1→M2 change of 12.5% suggests the coarse mesh is inadequate; all reported results use M3
- Local mesh refinement applied at cage-endplate interface (element size 0.15 mm) — this zone drives peak stress
- *Inconsistency flagged: the mesh convergence report (Doc VERTEC3-MC-001) states C3D8R (linear hexahedral reduced integration) elements were used for the convergence study, while the production model uses C3D10 — these are different element formulations and the convergence study may not be directly applicable to the submitted model*

---

## Slide 7: Boundary Condition Sensitivity & Model Form Uncertainty

- Rigid endplate assumption (Slide 2) tested against a simplified deformable cortical bone shell (E_cortical = 15 GPa, t = 1.0 mm):
  - Peak cage stress reduced by 18% when bone deformation is permitted
  - **This is a large sensitivity** — rigid assumption is conservative for cage stress but may be non-conservative for subsidence prediction
- Friction coefficient at cage-bone interface: μ = 0.4 (literature mid-range)
  - Sensitivity run at μ = 0.2 and μ = 0.6: peak interface shear stress varies ±22%
  - No experimental measurement of friction coefficient for this specific surface finish (Ra = 3.2 μm, grit-blasted Ti)
- Graft window idealization (sharp vs. filleted): not formally studied — *noted as open item*
- **Overall assessment of model form:** Multiple consequential assumptions remain incompletely characterized; the model team describes this as "conservative" in the executive summary but the deformable-bone sensitivity suggests conservatism is not uniformly maintained

---

## Slide 8: Solution Verification & Numerical Checks

- Equilibrium check: sum of reaction forces at fixed boundary = 1800.3 N vs. applied 1800.0 N — residual 0.017%, acceptable
- Energy balance: strain energy = 1.42 J; external work = 1.44 J — 1.4% discrepancy, within tolerance for contact problems
- Contact pressure distribution visualized and physically plausible — no spurious stress concentrations at non-contact zones
- Convergence: Newton-Raphson converged in 4 increments, no cutbacks — clean solution
- **Negative aspect:** No automated check for element distortion metrics (Jacobian ratio); analyst visually inspected mesh but no quantitative distortion report generated
  - Spot-checked 12 elements near lattice strut roots: max Jacobian ratio 0.31 — borderline acceptable per ABAQUS documentation (threshold 0.1)
  - *Wait — the threshold cited here is incorrect: ABAQUS flags elements below Jacobian ratio 0.1 as distorted, and 0.31 is well above that threshold. However, the analyst's own note in the model log states "several elements exceed distortion limits" — this contradiction between the slide narrative and the model log has not been resolved*

---

## Slide 9: Element Formulation Discrepancy (Flagged Issue)

- As noted in Slide 3 and Slide 6, there is a **documented inconsistency** in element type:
  - Mesh convergence study (Doc VERTEC3-MC-001, dated Jan 2024): uses C3D8R linear hex reduced integration
  - Production submission model (Doc VERTEC3-FEA-007, dated Feb 2024): uses C3D10 quadratic tet
- Rationale for change: complex lattice geometry not amenable to structured hex meshing — tet meshing was necessary
- **Problem:** The convergence behavior of C3D8R and C3D10 elements differs; the GCI computed from the hex-mesh study cannot be directly transferred to justify the tet-mesh model's spatial accuracy
- Recommended resolution: re-run mesh convergence study using C3D10 elements on the production geometry
- *Model team response (email, 2024-02-28): "We believe the convergence trend is similar and the GCI is still valid." This assertion is not supported by any numerical evidence in the record.*
- **This is a significant open item for regulatory submission**

---

## Slide 10: Comparison Against Physical Test Data

- **Test data available:** ASTM F2077 mechanical test results from 5 cage specimens (lot VTEC-0023)
  - Subsidence load at 1 mm displacement: test mean = 2,340 N ± 180 N (1σ)
  - FEA prediction of 1 mm subsidence load: 2,510 N
  - Discrepancy: +7.3% (FEA overpredicts stiffness)
- **Interpretation:**
  - 7.3% overprediction is within ±10% informal acceptance criterion cited by model team
  - However, the acceptance criterion of ±10% appears in a comment in the analysis plan (Doc VERTEC3-AP-002) with no technical justification — it is not derived from fitness-for-purpose requirements
- **Peak stress validation:** No direct experimental measurement of internal stress available (expected — not feasible for this geometry); DIC surface strain data from 2 specimens compared to FEA surface strain:
  - Max principal surface strain: FEA 4,820 με vs. DIC mean 5,110 με — 5.7% underprediction by FEA
  - *Note: FEA overpredicts stiffness (subsidence test) but underpredicts surface strain — these are not necessarily contradictory but the combination warrants scrutiny; no reconciliation analysis has been performed*

---

## Slide 11: Uncertainty Quantification & Sensitivity Summary

- Formal UQ: **not performed** — model team describes this as out of scope for Phase 1
- Informal sensitivity studies completed:
  - Friction coefficient (Slide 7): ±22% on interface shear
  - Rigid vs. deformable bone: 18% on peak cage stress
  - Material E for PEEK ±10%: peak stress changes ±6%
- No Monte Carlo or polynomial chaos expansion; no probabilistic output distribution
- **Gap:** The regulatory submission currently claims "the model predictions are robust" — this claim is not supported by a quantitative uncertainty analysis
- Sensitivity study results are documented in a spreadsheet (VERTEC3-SENS-001.xlsx) but this document is not formally controlled under the project QMS

---

## Slide 12: Intended Use & Applicability Domain

- Model is intended to support a specific 510(k) claim: peak stress under standardized compressive load does not exceed Ti-6Al-4V fatigue limit (550 MPa at 10⁷ cycles, R = 0.1)
- FEA peak stress result: 718 MPa — **this exceeds the stated fatigue limit**
  - Model team explanation: peak stress is highly localized (single integration point at lattice strut root); nominal stress in surrounding region is 480 MPa, which is below the fatigue limit
  - This interpretation may be defensible but is not formally argued in the submission document; the executive summary states "peak stresses are within acceptable limits" without qualification — *potentially misleading to a reviewer who does not read the detailed results*
- Applicability to patient population: model represents a single geometry (size L, 10° lordosis); no analysis of size variants or lordosis sensitivity
- **Operator/user factors:** The model outputs are intended to be interpreted by regulatory affairs staff who may not have FEA expertise — no guidance document or interpretation aid has been prepared

---

## Slide 13: Documentation & Traceability

- Model files stored in ProjectWise (version-controlled); input decks, output databases, and post-processing scripts all present
- Model log (VERTEC3-ML-001): reasonably complete but missing entries for the geometry simplification decisions (Slide 2) and the element type change rationale
- V&V plan (VERTEC3-VVP-001 Rev A): exists and was approved; however, the plan was written after the analysis was partially complete — *some V&V activities listed in the plan were retroactively documented rather than prospectively planned*
- Independent technical review: performed by Dr. Halvorsen (external); review report VTEC-EXT-004 dated 2024-03-01
  - Reviewer identified 7 issues; 3 resolved, 4 open (including element type discrepancy and PEEK moisture correction)
- QMS traceability: analysis is linked to design history file DHF-VERTEC-0031; linkage to risk management file (ISO 14971) not yet established

---

## Slide 14: Summary of Open Items & Credibility Assessment

- **Strengths:**
  - Solver is well-established and installation-qualified
  - Mesh refinement study performed with Richardson extrapolation; fine mesh GCI < 2%
  - Physical test comparison available with <10% discrepancy on subsidence load
  - Independent external review conducted

- **Significant open items (must resolve before submission):**
  1. Element type mismatch between convergence study and production model — convergence evidence is not currently valid for submitted model
  2. PEEK material properties not corrected for wet/implanted environment
  3. Peak stress result (718 MPa) exceeds fatigue limit; executive summary language is misleading
  4. FEA stiffness overprediction and surface strain underprediction not reconciled
  5. Acceptance criterion (±10%) lacks technical justification
  6. Rigid endplate assumption — conservatism claim not uniformly supported

- **Minor open items (should address, not blocking):**
  - Graft window geometry sensitivity not studied
  - Element distortion contradiction between slide narrative and model log
  - UQ not performed; robustness claim unsupported
  - ISO 14971 linkage missing
  - Retroactive V&V planning noted

- **Overall credibility posture:** Model provides useful directional insight but current documentation and consistency gaps mean it does not yet meet the standard required for primary regulatory evidence. Recommend targeted remediation (estimated 3–4 weeks of analyst effort) before re-review.

---

## Slide 15: Recommended Next Steps

- [ ] Re-run mesh convergence study using C3D10 elements on production geometry; update GCI documentation
- [ ] Obtain or derive moisture-conditioned PEEK modulus; assess impact on peak stress
- [ ] Revise executive summary to accurately represent peak stress result and localization argument; add supporting stress distribution figures
- [ ] Perform reconciliation analysis for subsidence stiffness vs. surface strain discrepancy
- [ ] Formally justify ±10% acceptance criterion or replace with fitness-for-purpose derivation
- [ ] Document geometry simplification decisions in model log
- [ ] Establish linkage between FEA model and ISO 14971 risk file
- [ ] Prepare model interpretation guidance for regulatory affairs staff
- [ ] Schedule re-review after items 1–4 resolved (target: 2024-04-30)

---
*End of slide deck — VERTEC-3 FEA Credibility Review Rev B*
*Prepared by: J. Okonkwo, Sr. Analyst | Reviewed by: M. Thériault, Lead Engineer | External input: R. Halvorsen, TechMed Consulting*
