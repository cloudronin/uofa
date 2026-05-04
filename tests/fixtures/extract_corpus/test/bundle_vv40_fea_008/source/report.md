# FEA Credibility Review — Slide Deck
## Structural Integrity Assessment: Titanium Spinal Fusion Cage (TFC-7 Implant)
### Internal Review Package | Milestone 3 | Rev B

---

## Slide 1 — Scope and Purpose

- **Assessment objective:** Evaluate the trustworthiness of the finite-element model used to predict fatigue life and subsidence risk of the TFC-7 porous titanium interbody fusion cage under physiological loading
- **Model owner:** Advanced Implant Mechanics Group (AIMG), using Abaqus/Standard 2022.HF4
- **Intended use of simulation outputs:**
  - Regulatory submission support (510(k) pathway)
  - Design optimization — pore geometry and strut thickness trade-off
  - Comparison against ASTM F2077 dynamic compression testing
- **Review approach:** Evidence gathered from AIMG internal memos, solver log archives, mesh study documentation, and physical test reports dating from Q1–Q3 of the current fiscal year
- **Caveats up front:** Several areas of evidence are internally inconsistent; reviewers should weigh conflicting sources carefully before assigning confidence levels

---

## Slide 2 — What the Model Is (and Isn't)

- **Geometry:** Full 3D solid model of TFC-7, reconstructed from CAD in CATIA V5; porous lattice represented via explicit strut geometry (not homogenized)
  - Lattice cell count: ~4,200 unit cells; strut diameter 0.38 mm nominal
- **Loading scenario:** Axial compressive fatigue per ASTM F2077, plus a 4° anterior tilt moment (worst-case spondylolisthesis posture per clinical literature)
- **Material model:** Elastic-plastic Ti-6Al-4V with isotropic hardening; yield strength 880 MPa, UTS 950 MPa from coupon data supplied by Arcam AB (EBM powder bed process)
- **Boundary conditions:** Inferior endplate fully fixed; superior endplate loaded via rigid reference point with prescribed displacement amplitude
- **What the model does NOT cover:**
  - Bone ingrowth / osseointegration effects — deferred to Phase 4 biological modeling effort
  - Corrosion or fretting fatigue — outside current scope
  - Patient-specific bone quality variation — addressed separately in probabilistic sensitivity study (not reviewed here)

---

## Slide 3 — Software and Numerical Platform

- **Solver:** Abaqus/Standard 2022.HF4, implicit quasi-static with automatic stabilization (STABILIZE, FACTOR=2×10⁻⁴)
  - Automatic stabilization was activated in early runs to handle contact convergence; the stabilization energy ratio was checked and remained below 1% in all production runs — **acceptable**
- **Element library:** C3D10 modified tetrahedral elements (10-node, hybrid pressure formulation for near-incompressible plasticity regions)
  - Strut elements: C3D8R reduced-integration hex where geometry permitted; hourglass control via enhanced assumed strain
- **Contact formulation:** General contact, finite sliding, penalty stiffness method; friction coefficient μ = 0.3 (Ti-on-UHMWPE test fixture)
- **Code verification status:**
  - Abaqus is a commercially qualified solver with documented benchmark history; AIMG has not performed independent benchmark problems for this specific lattice geometry class
  - *Concern flagged:* No internal benchmark against known analytical solutions for porous strut bending — this gap is noted but not resolved in the current package

---

## Slide 4 — Mesh Refinement Study (Discretization Sensitivity)

- **Study design:** Three mesh densities evaluated on a representative 5×5 unit-cell sub-model extracted from the full cage
  - Coarse: ~180k elements, average strut element edge length 0.12 mm
  - Medium: ~510k elements, 0.07 mm
  - Fine: ~1.4M elements, 0.04 mm
- **Metric tracked:** Peak von Mises stress at the strut-node junction (historically the fatigue initiation site)
- **Results:**

  | Mesh | Peak σ_VM (MPa) | Change vs. prior |
  |------|----------------|-----------------|
  | Coarse | 743 | — |
  | Medium | 812 | +9.3% |
  | Fine | 819 | +0.9% |

- **Conclusion stated in AIMG memo (dated 14-Mar):** "Medium mesh is sufficiently converged; fine mesh used for all production runs as conservative choice"
- **⚠ Contradiction flagged:** The full-cage production model submitted for regulatory review uses the *coarse* mesh density (~180k elements per the solver log file header), not the fine mesh. The AIMG memo and the actual model file are inconsistent. This discrepancy was not resolved before the Milestone 3 package was assembled.

---

## Slide 5 — Solution Verification and Numerical Checks

- **Residual force convergence:** All load increments converge to default Abaqus tolerance (0.5% of time-averaged force norm); no increment cutbacks in production runs
- **Energy balance check:** Strain energy vs. external work ratio monitored; within 0.2% across all steps — good
- **Reaction force check:** Sum of contact reaction forces at fixed boundary matches applied load to within 0.04% — good
- **Plasticity extent:** Plastic strain localized to <0.8% of total element volume at peak load; confirms predominantly elastic response, consistent with design intent
- **Time-step sensitivity:** Not formally documented; analyst notes suggest a single step size was used throughout without sensitivity sweep
  - This is a minor gap for a quasi-static problem but should be noted for completeness

---

## Slide 6 — Material Property Sourcing and Uncertainty

- **Ti-6Al-4V EBM material data:** Provided by Arcam AB certificate of conformance; batch-specific tensile data from 12 coupons (horizontal build orientation)
  - Mean yield: 880 MPa, CoV = 3.1%
  - Mean UTS: 950 MPa, CoV = 2.4%
  - Fatigue limit (R = 0.1, 10⁷ cycles): 500 MPa — sourced from published literature (Leuders et al., 2013) **not from project-specific coupon testing**
- **⚠ Ambiguity — fatigue limit:** Slide 9 of the AIMG design review deck (separate document, same project) cites a fatigue limit of 430 MPa for the same material/process, referencing an internal coupon test campaign from 18 months prior. The 70 MPa discrepancy (14%) is material to the fatigue life prediction and has not been adjudicated. Both values appear in circulation within the project team.
- **Anisotropy:** Build-direction anisotropy acknowledged in material cert; vertical-build yield strength ~820 MPa (5% lower). The model uses the horizontal-build value uniformly — potentially non-conservative for struts oriented vertically in the lattice
- **Bone analog material (test fixture):** UHMWPE endplate blocks; modulus 1.1 GPa per ASTM F1839 surrogate — not explicitly modeled; fixture treated as rigid. Acceptable simplification given UHMWPE stiffness >> applied displacement amplitude

---

## Slide 7 — Comparison Against Physical Test Data (Model Accuracy)

- **Test campaign:** ASTM F2077 Type I dynamic compression, n=6 specimens, 5 Hz sinusoidal loading, load range 50–1200 N
- **Measured quantity compared:** Axial stiffness (initial linear regime) and cycles-to-crack-initiation (dye penetrant inspection at 10⁵, 5×10⁵, 10⁶ intervals)
- **Stiffness comparison:**
  - Test mean: 2,340 N/mm (±85 N/mm, 1σ)
  - Model prediction: 2,190 N/mm
  - Discrepancy: −6.4% (model slightly softer) — within typical FEA-to-test scatter for porous structures; **acceptable**
- **Fatigue life comparison:**
  - Test: 3 of 6 specimens survived 5×10⁵ cycles without crack; 3 cracked between 2.1×10⁵ and 3.8×10⁵ cycles
  - Model (using 500 MPa fatigue limit): predicts infinite life at test load level — **non-conservative and inconsistent with test observations**
  - Model (using 430 MPa fatigue limit): predicts crack initiation around 2.8×10⁵ cycles — **consistent with test median**
- **This directly corroborates the material property ambiguity on Slide 6.** The 430 MPa value appears to be the better-supported number for this geometry and build process, but the production regulatory submission uses 500 MPa.

---

## Slide 8 — Sensitivity Analysis and Uncertainty Propagation

- **Parameters varied:** Strut diameter (±0.05 mm manufacturing tolerance), friction coefficient (0.2–0.4), and applied moment arm (±2°)
- **Method:** One-at-a-time (OAT) perturbation; 3 levels per parameter; 9 additional model runs
- **Key finding:** Peak stress most sensitive to strut diameter (±12% stress change per ±0.05 mm) — manufacturing tolerance is the dominant uncertainty driver
- **What was NOT done:**
  - No Monte Carlo or polynomial chaos expansion — AIMG cited schedule constraints; deferred to Phase 4
  - No sensitivity to fatigue limit value — notably absent given the known dispute between 430 and 500 MPa values
- **Overall:** Sensitivity study is narrower than ideal; the most consequential uncertainty (fatigue limit) was not propagated

---

## Slide 9 — Boundary Condition Fidelity and Modeling Assumptions

- **Clinical loading representation:**
  - The 4° anterior tilt was selected based on a 2019 biomechanics literature review (Wilke et al.); represents approximately the 75th percentile worst-case posture
  - Muscle force contributions are not included — standard simplification per FDA guidance for in vitro device testing correlation
- **Fixture representation:** Rigid endplate assumption discussed on Slide 6; reviewer concurs this is defensible
- **⚠ Inconsistency — load magnitude:** The executive summary slide (Slide 2 of AIMG internal deck) states the peak compressive load is 1,200 N. The Abaqus input file reviewed by this team specifies a peak displacement corresponding to approximately 1,450 N reaction force (back-calculated from stiffness). AIMG was asked to clarify; response as of report date: "under investigation." A 21% load discrepancy would significantly affect fatigue predictions.
- **Symmetry:** No symmetry assumed; full model used — appropriate given asymmetric loading scenario

---

## Slide 10 — Independent Replication and Peer Checks

- **Internal peer review:** One independent analyst within AIMG performed a model audit in February; findings documented in IR-2024-009
  - Audit confirmed element quality metrics (Jacobian ratio > 0.4 throughout, no negative-Jacobian elements)
  - Audit did NOT check mesh density against the convergence study — the coarse/fine discrepancy (Slide 4) was therefore not caught
- **External review:** No external independent model replication has been performed to date
  - AIMG position: external replication is "not required for 510(k) pathway" — this is a debatable interpretation of FDA's least burdensome principle; the complexity of the lattice geometry arguably warrants it
- **Test-analysis correlation sign-off:** Not formally signed off; the fatigue life discrepancy (Slide 7) remains open as a corrective action item (CAI-2024-031)

---

## Slide 11 — Documentation and Traceability

- **Model configuration management:** Abaqus input files stored in Windchill PLM under part number TFC7-SIM-001 Rev C; change history logged
- **Run records:** All production runs archived with solver logs, including CPU time, increment counts, and convergence history — good practice
- **Analysis plan:** A formal simulation plan document (SP-TFC7-001) exists and was reviewed; it predates the mesh convergence study and has not been updated to reflect the fine-mesh decision — creates a traceability gap
- **Material data traceability:** Arcam cert linked in PLM; Leuders et al. literature reference cited but not formally controlled as a project document — minor gap
- **Test data traceability:** ASTM F2077 test reports formally released under TR-TFC7-2024-003; chain of custody for specimens documented

---

## Slide 12 — Intended Use Alignment and Model Applicability

- **Primary intended use match:** The model geometry, loading, and boundary conditions are directly representative of the ASTM F2077 test configuration — strong alignment for the test-correlation use case
- **Regulatory submission use case:** Model is intended to supplement (not replace) physical testing; FDA precedent supports this approach for complex lattice structures
- **Design optimization use case:** Using the model for strut thickness trade-offs is reasonable given demonstrated stiffness accuracy, but the unresolved fatigue limit ambiguity limits confidence in absolute fatigue life predictions for design variants
- **Out-of-scope extrapolations to watch:**
  - Multi-level construct loading (two cages in series) — not validated
  - Revision surgery scenarios (partial bone ingrowth) — explicitly out of scope
- **Overall applicability judgment:** Model is fit for stiffness-dominated comparisons; fatigue life predictions require resolution of the material property and load magnitude discrepancies before regulatory use

---

## Slide 13 — Summary of Open Issues and Risk Register

| Issue ID | Description | Severity | Status |
|----------|-------------|----------|--------|
| OI-01 | Production model uses coarse mesh despite fine-mesh convergence study conclusion | High | Open |
| OI-02 | Fatigue limit discrepancy: 500 MPa (lit) vs. 430 MPa (internal coupon) | Critical | Open — CAI-2024-031 |
| OI-03 | Applied load magnitude inconsistency: 1,200 N (summary) vs. ~1,450 N (input file) | High | Under investigation |
| OI-04 | No benchmark of solver for lattice strut bending | Medium | Deferred |
| OI-05 | Sensitivity analysis does not cover fatigue limit uncertainty | Medium | Deferred to Phase 4 |
| OI-06 | Analysis plan SP-TFC7-001 not updated post mesh study | Low | Pending revision |

- **Recommendation:** OI-01, OI-02, and OI-03 must be resolved before this model package is used in any regulatory submission
- OI-04 and OI-05 are acceptable risks for design optimization use at current phase

---

## Slide 14 — Preliminary Credibility Ratings (Draft — Pending Issue Resolution)

*Note: Ratings below reflect current evidence state. Several factors carry reduced confidence due to open issues identified in this review. These are NOT final ratings.*

- **Geometric fidelity of model to physical device:** Evidence strong — explicit CAD-derived lattice geometry, well-documented ✦✦✦✦
- **Numerical solution quality (convergence, energy balance):** Evidence good for solution-level checks; mesh density question (OI-01) unresolved ✦✦ (provisional)
- **Material representation:** Contradictory evidence in circulation; fatigue limit value disputed ✦✦ (cannot rate higher until OI-02 resolved)
- **Loading and boundary condition fidelity:** Load magnitude discrepancy (OI-03) prevents confident rating ✦✦ (provisional)
- **Comparison to experimental data — stiffness:** Good agreement, well-documented ✦✦✦
- **Comparison to experimental data — fatigue life:** Model non-conservative with currently used material value; agreement only with disputed lower value ✦ (poor, as-is)
- **Sensitivity/uncertainty coverage:** Partial; dominant uncertainty not covered ✦✦
- **Documentation and traceability:** Generally good with minor gaps ✦✦✦

---

## Slide 15 — Recommended Path Forward

- **Immediate actions (before next milestone):**
  1. Confirm which mesh density is actually used in the regulatory submission model — reconcile AIMG memo with input file header (OI-01)
  2. Conduct definitive fatigue coupon testing on TFC-7 build-process material to resolve 430 vs. 500 MPa dispute (OI-02); do not rely solely on literature values for a safety-critical fatigue prediction
  3. Reconcile load magnitude specification between executive summary and Abaqus input file; re-run if necessary (OI-03)

- **Near-term actions (Phase 4):**
  4. Add fatigue limit as a parameter in the sensitivity / uncertainty propagation study
  5. Develop at least one analytical benchmark case for porous strut bending to support solver confidence for this geometry class
  6. Update SP-TFC7-001 to reflect current mesh strategy and material data sources

- **Longer-term:**
  - Consider independent external model replication given regulatory stakes and lattice geometry complexity
  - Revisit build-direction anisotropy treatment once Phase 4 biological modeling defines preferred strut orientation criteria

- **Overall assessment:** The modeling approach is technically sound in its framework, and several aspects (stiffness correlation, documentation infrastructure, element formulation choices) reflect competent FEA practice. However, the three high/critical open issues identified here represent substantive credibility risks that would be difficult to defend under FDA scrutiny in their current state.

---

*Prepared by: Simulation Credibility Review Team | Distribution: AIMG Lead, Regulatory Affairs, Quality Engineering | Classification: Internal Use Only*
