# Structural FEA Credibility Review — Slide Deck
### Titanium Acetabular Cup Implant Analysis | Project ORTHO-7 | Rev C

---

## Slide 1 — Session Overview

- **Purpose of this review:** Evaluate the trustworthiness of finite-element predictions used to support regulatory submission for the ORTHO-7 titanium acetabular cup
- **Analyst team:** BioMech Simulation Group, Hartwell Engineering Associates
- **Solver platform:** Abaqus/Standard 2022.HF4 (Dassault Systèmes)
- **Geometry source:** CT-derived surface scan + CAD cleanup in CATIA V5
- **Review scope covers:**
  - How well the model is built and exercised
  - Whether the math underlying the code has been checked
  - How confidently predictions translate to real-world implant behavior
  - Whether the right people are using outputs in the right context
- **Key concern flagged by project lead:** Contradictory statements about element order exist across deliverables — addressed on Slide 6

---

## Slide 2 — Clinical & Regulatory Context

- ORTHO-7 cup is a press-fit cementless device, Ti-6Al-4V ELI substrate with HA plasma-spray coating
- Primary FEA deliverable: peak Von Mises stress under ISO 7206-4 loading conditions (2300 N axial, 30° tilt)
- Secondary deliverable: micromotion map at bone-implant interface (target < 50 µm for osseointegration)
- Regulatory pathway: 510(k) substantial equivalence; FDA guidance references ASTM F2996 and ISO 7206 series
- **Model is being used to:**
  - Screen design variants (3 cup geometries evaluated)
  - Justify reduced physical testing protocol (2 of 6 planned fatigue tests waived based on simulation results)
    - *This is a high-stakes use — credibility bar is correspondingly elevated*
- Predicate device FEA (CompuOrtho HipShield v2) used as informal benchmark; data shared under NDA

---

## Slide 3 — What the Model Is Actually Predicting (Intended Use Clarity)

- The simulation team has documented the **specific quantities of interest (QoIs):**
  - Peak stress in the superior dome region (single scalar, reported in MPa)
  - Maximum interface relative displacement (µm, extracted at 12 nodal pairs)
  - First three natural frequencies (modal analysis, free-free boundary condition)
- **Boundary condition assumptions are explicitly stated:**
  - Bone modeled as rigid analytical surface (conservative for stress, acknowledged limitation)
  - Press-fit preload simulated via interference fit of 0.05 mm radial — *see contradiction note, Slide 6*
- Intended users: regulatory affairs engineers and design leads
  - These users are **not** FEA practitioners; slide deck is the primary communication vehicle
  - No guidance document exists yet on how to interpret confidence intervals on micromotion predictions
    - *Gap: downstream user interpretation risk not formally characterized*
- The scope statement in the simulation plan (Doc SP-ORTHO7-002 Rev B) is clear and internally consistent

---

## Slide 4 — Geometry & Material Fidelity

- **Geometry:**
  - CAD model validated against CMM measurements of 3 production cups; max deviation 0.08 mm (within tolerance)
  - Fillet radii at peg-cup junction: nominal 0.4 mm; meshed at 0.35 mm effective radius (slight under-representation — noted in model assumptions log)
  - Coating layer (HA, ~120 µm) **not explicitly meshed** — modeled as surface traction modifier; literature basis cited (Completo et al. 2008)

- **Material properties:**
  - Ti-6Al-4V: E = 114 GPa, ν = 0.33, yield 880 MPa — sourced from ASM Handbook Vol. 2, lot-specific cert not used
  - Cortical bone (rigid surface): not assigned mechanical properties — consistent with rigid assumption
  - Trabecular bone region: **not included** in current model revision
    - *Noted as acceptable simplification for ISO 7206-4 compliance posture*
  - Temperature and strain-rate dependence: **not modeled** — justified for quasi-static loading regime

- **Overall geometry/material fidelity assessment: moderate-to-high for titanium component; bone representation is a known simplification**

---

## Slide 5 — Numerical Solution Quality: Mesh Refinement Study

- Three mesh densities evaluated on the baseline cup geometry:

  | Mesh ID | Global Seed (mm) | Peg-region seed (mm) | Elements | Peak Stress (MPa) |
  |---------|-----------------|----------------------|----------|-------------------|
  | M1 (coarse) | 2.0 | 0.8 | 41,200 | 387 |
  | M2 (medium) | 1.2 | 0.5 | 118,600 | 412 |
  | M3 (fine) | 0.7 | 0.25 | 389,000 | 419 |

- Richardson extrapolation applied between M2 and M3: extrapolated value 421 MPa
- **Grid Convergence Index (GCI) for M3:** 0.9% — considered acceptable per ASME V&V 10.1 guidance
- M2 selected for production runs as engineering compromise (runtime ~4 hrs vs. ~18 hrs for M3)
  - *Difference between M2 and extrapolated value: ~2.1% — within stated 5% tolerance*
- **Element formulation:** C3D10 (10-node quadratic tetrahedra) used throughout
  - *However — see Slide 6 for conflicting statement in the mesh report appendix*
- Contact at bone interface: surface-to-surface, finite sliding, friction µ = 0.3 (Shirazi-Adl 1992)
- Convergence criterion: residual force norm < 1×10⁻⁴ N; confirmed met for all production runs

---

## Slide 6 — ⚠ Identified Contradictions & Ambiguities (Reviewer Flags)

> *This slide summarizes four areas where the evidence bundle contains internally inconsistent information. These must be resolved before credibility ratings can be finalized.*

**Contradiction A — Element Formulation**
- Slide 5 (and simulation plan SP-ORTHO7-002 Rev B) states C3D10 quadratic tet elements used throughout
- Mesh report appendix (Doc MR-ORTHO7-009 Rev A, Table 3) lists element type as **C3D4 (linear tet)** for Variant B and Variant C cup geometries
- Linear tets are known to be overly stiff in bending-dominated regions; stress predictions could be non-conservative
- *Impact: if Variant B/C runs used C3D4, the 2300 N peak stress values for those variants are suspect*

**Contradiction B — Interference Fit Preload**
- Slide 3 states press-fit preload is 0.05 mm radial interference
- Analysis input deck (archived as ORTHO7_BaseCase_v4.inp) shows `*INTERFERENCE, SHRINK` parameter set to **0.025 mm**
- A factor-of-two discrepancy in preload directly affects predicted micromotion; 0.025 mm would underestimate seating stiffness and may over-predict micromotion (non-conservative for osseointegration claim)

**Contradiction C — Validation Test Correlation**
- Executive summary (Slide 10, same deck) states "model predictions agree with bench test data within 8%"
- Validation data table (Doc VR-ORTHO7-014 Rev A, Table 5) shows one strain gauge location (SG-04, superior dome) with **23% discrepancy** between FEA and physical measurement
- The 8% figure appears to be an average across all gauges, masking the worst-case outlier at the most safety-critical location

**Contradiction D — Scope of Modal Analysis**
- Simulation plan states modal analysis performed under **in-situ boundary conditions** (cup seated in synthetic bone block)
- Modal results section reports free-free natural frequencies only; no in-situ modal data appears in any deliverable
- Unclear whether in-situ analysis was conducted, deferred, or silently dropped from scope

---

## Slide 7 — Code Verification & Solver Trustworthiness

- **Abaqus/Standard 2022.HF4** is a commercially mature solver; Dassault publishes benchmark verification manuals (Abaqus Benchmarks Guide, Section 1.1–2.3)
- Project team ran three internal verification problems:
  1. Thick-walled pressure vessel (Lamé solution): FEA vs. analytical — max error 0.3%
  2. Cantilevered beam with tip load (Euler-Bernoulli): FEA vs. analytical — max error 0.8% (C3D10 mesh)
  3. Hertzian contact patch (sphere-on-flat): FEA vs. analytical — max error 4.1% (acceptable for contact)
- These spot-checks are **not a substitute for full software QA** but provide reasonable confidence for the element types and loading modes used
- **No custom user subroutines (UMATs, UELs) employed** — reduces risk of in-house coding errors
- Abaqus version control: fixed version locked in project configuration management plan; no mid-project solver upgrades documented
- *Gap: no formal record of Abaqus license validation against a certified reference problem set as required by the project's own QA plan (Doc QA-ORTHO7-001 §4.2)*

---

## Slide 8 — Experimental Correlation & Physical Test Program

- **Bench test setup:** Composite femur block (Sawbones 4th gen, #3403) with cup press-fit per ISO 7206-4 fixture
- Instrumentation: 8 triaxial strain gauge rosettes (CEA-06-062WT-350, Vishay), 2 LVDT displacement sensors
- Load applied via servo-hydraulic test frame (MTS 858 Mini Bionix II), load cell calibrated to NIST traceable standard
- **Correlation summary (from VR-ORTHO7-014):**
  - SG-01 through SG-07: FEA within 6–14% of measured principal strain
  - SG-04 (superior dome): **23% over-prediction by FEA** — *flagged in Contradiction C, Slide 6*
  - LVDT micromotion: FEA predicts 31 µm; measured 28 µm (10.7% — within acceptable range)
- The 23% discrepancy at SG-04 has not been formally dispositioned; engineering note EN-ORTHO7-022 attributes it to "possible gauge bonding anomaly" without re-test evidence
- **Validation coverage: moderate** — one critical location unresolved; micromotion correlation is acceptable

---

## Slide 9 — Sensitivity & Uncertainty Characterization

- One-at-a-time (OAT) sensitivity study performed on 4 parameters:
  - Elastic modulus ±10%: peak stress varies ±3.2%
  - Friction coefficient µ: range 0.2–0.5 → micromotion varies 18–44 µm (significant sensitivity)
  - Interference fit: 0.025–0.075 mm → micromotion varies 22–38 µm
  - Load angle ±5°: peak stress varies ±7.1% (highest sensitivity parameter identified)
- **No formal probabilistic analysis (Monte Carlo or PCE) was conducted** — OAT only
  - For a regulatory submission waiving physical fatigue tests, this is a notable gap
- Material scatter: Ti-6Al-4V mechanical properties treated as deterministic; no allowance for lot-to-lot variation
- **Geometric tolerance effects:** not studied; fillet radius sensitivity not included despite known stress concentration influence
- Summary: sensitivity coverage is partial; the most influential parameters are identified but uncertainty bounds on QoIs are not formally propagated

---

## Slide 10 — Summary Claims vs. Supporting Evidence

- Executive summary states: *"Model predictions agree with bench test data within 8% across all measurement locations"*
  - **This is misleading** — see Slide 6 Contradiction C and Slide 8 detail
  - Recommend revising to report worst-case and mean discrepancy separately
- Claim: *"Mesh convergence demonstrates solution independence"*
  - **Supported** for Variant A (baseline); **not demonstrated** for Variants B and C if C3D4 elements were used (Contradiction A)
- Claim: *"Interference fit preload consistent with surgical protocol"*
  - **Undermined** by the 2× discrepancy between documented and implemented preload (Contradiction B)
- Claim: *"In-situ modal frequencies confirm no resonance risk during gait loading"*
  - **Unsubstantiated** — only free-free results exist; in-situ analysis status unknown (Contradiction D)
- Positive finding: micromotion predictions are well-correlated and sensitivity to friction is documented; this portion of the analysis is credibly supported

---

## Slide 11 — Human Factors & Appropriate Use Considerations

- Primary consumers of simulation outputs are **regulatory affairs and design engineers**, not simulation specialists
- Current output format: scalar peak stress values and contour plots in PDF — no uncertainty bands shown
- **Risk:** Non-specialist users may interpret FEA contour plots as exact rather than approximate; no guidance document accompanies outputs
- The decision to waive 2 of 6 fatigue tests was made partly on FEA basis — it is unclear whether decision-makers were informed of:
  - The unresolved 23% discrepancy at SG-04
  - The element formulation ambiguity for Variants B/C
  - The partial nature of the sensitivity study
- *Recommendation: A one-page "model use card" should be prepared stating valid use cases, known limitations, and the outstanding contradictions from Slide 6*
- No evidence of formal training records for personnel interpreting simulation outputs in a regulatory context

---

## Slide 12 — Overall Credibility Assessment Summary

| Area | Status | Notes |
|------|--------|-------|
| Clarity of intended use | ✅ Adequate | QoIs well-defined; user guidance gap exists |
| Geometry & material representation | ⚠️ Partial | Bone simplification acceptable; coating approximation documented |
| Mesh quality & convergence | ⚠️ Conditional | Demonstrated for Variant A only; element type ambiguity for B/C |
| Solver verification | ✅ Adequate | Benchmark problems passed; minor QA documentation gap |
| Physical test correlation | ⚠️ Partial | SG-04 discrepancy unresolved; micromotion correlation acceptable |
| Uncertainty quantification | ❌ Insufficient | OAT only; no probabilistic bounds; fatigue test waiver not justified |
| Appropriate use / user guidance | ❌ Insufficient | No model use card; non-specialist users not adequately supported |

- **Overall: CONDITIONAL — four contradictions must be resolved; uncertainty characterization must be strengthened before regulatory submission**
- Recommend a targeted re-analysis sprint (est. 3 weeks) addressing Contradictions A and B, followed by re-correlation at SG-04

---

## Slide 13 — Recommended Actions & Owners

1. **Resolve element type for Variants B & C** (Owner: FEA Lead, J. Tamboli) — re-run with confirmed C3D10; update mesh report
2. **Reconcile interference fit value** (Owner: FEA Lead + Design Eng, R. Osei) — confirm surgical protocol value, update input deck, re-run micromotion analysis
3. **Re-test or formally disposition SG-04 discrepancy** (Owner: Test Lab, M. Ferreira) — repeat strain gauge measurement or provide engineering justification with supporting literature
4. **Clarify in-situ modal analysis status** (Owner: Project Manager, L. Nguyen) — confirm scope, run analysis if required, update simulation plan
5. **Develop model use card** (Owner: Regulatory Affairs + FEA Lead) — one-page document; include limitations, uncertainty ranges, valid use cases
6. **Extend sensitivity study** (Owner: FEA Lead) — add geometric tolerance sensitivity; consider simplified probabilistic sweep (100-sample Latin hypercube minimum)

- Target completion: prior to regulatory submission package lock (currently scheduled T+6 weeks)
- All actions to be tracked in JIRA project ORTHO7-SIM; closure requires sign-off from Chief Engineer

---

## Slide 14 — References & Document Traceability

- SP-ORTHO7-002 Rev B — Simulation Plan, Acetabular Cup FEA
- MR-ORTHO7-009 Rev A — Mesh Generation Report (contains Contradiction A)
- VR-ORTHO7-014 Rev A — Validation Report, Bench Test Correlation
- QA-ORTHO7-001 — Project Quality Assurance Plan
- EN-ORTHO7-022 — Engineering Note, SG-04 Discrepancy Disposition (draft)
- ASTM F2996-13 — Standard Practice for FEA of Non-Modular Metallic Orthopaedic Hip Femoral Stems
- ISO 7206-4:2010 — Implants for Surgery — Partial and Total Hip Joint Prostheses
- ASME V&V 10-2006 / V&V 10.1-2012 — Verification and Validation in Solid Mechanics
- Abaqus Benchmarks Guide, v2022 — Dassault Systèmes
- Completo A. et al. (2008) — "The influence of different femoral stem designs on cement fatigue damage in cemented hip replacements" — *J Biomechanics*
- Shirazi-Adl A. (1992) — "Finite element stress analysis of a push-out test" — *J Biomechanics*
- ASM Handbook Vol. 2 — Properties and Selection: Nonferrous Alloys
