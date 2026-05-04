# CFD Credibility Assessment – Slide Deck
## Centrifugal Pump Stage Aerothermal Analysis | Project AQUILA-3 | Rev B

---

## Slide 1 – Overview & Scope

- **Simulation objective:** Predict head-rise, shaft power, and internal recirculation patterns for a 6-stage centrifugal water pump operating at 3,550 RPM under partial-load conditions (40–110 % BEP)
- **Solver platform:** ANSYS Fluent 2023 R1; steady-state RANS formulation; MRF (multiple reference frame) for impeller–diffuser interaction
- **Primary outputs of interest:**
  - Stage total-to-total pressure rise (±2 % target accuracy)
  - Shaft torque and hydraulic efficiency
  - Recirculation onset flow coefficient
- **Review context:** This deck was prepared for the Milestone 3 design gate; not all V&V activities have been completed — items deferred to Phase 4 are flagged explicitly
- **Audience:** Systems engineering, pump design leads, independent V&V reviewer

---

## Slide 2 – How Well Does the Code Actually Solve the Equations?

- **Verification activity summary:**
  - Manufactured-solution test (Method of Manufactured Solutions, MMS) was run on the pressure-velocity coupling scheme (SIMPLE-C) using a 2D pipe-bend geometry
  - Observed order of accuracy: **1.94** for velocity, **1.87** for pressure — consistent with formal 2nd-order expectation for Fluent's node-based gradients
  - Residual convergence: all scaled residuals driven below **1 × 10⁻⁵** for continuity and momentum; energy residual below **1 × 10⁻⁷**
- **Known solver limitations noted:**
  - Wall-function formulation switches between scalable and standard depending on local y⁺ — this created inconsistency in early runs (see Slide 6 for contradiction flagged by reviewer)
  - Fluent's MRF implementation has a documented asymmetry artifact at the rotor–stator interface when pitch ratio ≠ 1; correction factor applied per Ansys TechNote FLU-2021-044
- **Assessment:** Code behaves as expected for this class of problem; MMS results are satisfactory

---

## Slide 3 – Mesh Refinement Study & Discretization Uncertainty

- **Three-level structured hex mesh generated in ANSYS Meshing:**
  - Coarse: 2.1 M cells | Medium: 6.8 M cells | Fine: 18.4 M cells
  - Mesh topology held constant; refinement ratio ≈ 1.41 (each direction)
- **Grid Convergence Index (GCI) computed per Roache (1998):**

  | Quantity | GCI (medium→fine) | Apparent Order |
  |---|---|---|
  | Stage ΔP | 0.83 % | 1.96 |
  | Shaft torque | 1.21 % | 1.88 |
  | Efficiency | 1.04 % | 1.91 |

- **All GCI values below the 2 % project threshold** — fine mesh selected for production runs
- **Note on y⁺:** Fine mesh targets y⁺ ≈ 30–60 for wall functions; actual near-wall y⁺ ranges from **12 to 95** across blade surfaces — lower bound falls into the viscous sublayer where standard wall functions are not valid
  - *This is flagged as an unresolved concern; see also Slide 6 where the turbulence model section claims y⁺ compliance is "fully satisfied"*
- **Temporal discretization:** Steady-state; no time-step study performed (not applicable for RANS MRF)

---

## Slide 4 – Turbulence Modeling & Physical Assumptions

- **Baseline model:** SST k-ω (Menter 1994); selected for favorable behavior in adverse pressure gradient regions near impeller shroud
- **Sensitivity runs completed:**
  - Realizable k-ε with enhanced wall treatment: efficiency prediction within 0.8 % of SST baseline
  - RSM (Reynolds Stress Model): 3.1 % higher predicted recirculation onset — noted as physically plausible given known SST over-prediction of turbulent viscosity in separated zones
- **Compressibility:** Incompressible (water at 25 °C, ρ = 997 kg/m³); Mach number < 0.003 throughout — assumption justified
- **Cavitation:** Not modeled in this phase; operating conditions are 2.4 m NPSH above cavitation inception from vendor test data — considered safe margin
- **Claim in executive summary (Slide 12):** *"The SST model has been validated for this pump family and y⁺ compliance is fully satisfied on all production meshes"*
  - **⚠ Reviewer note:** This statement contradicts the mesh study findings on Slide 3 where y⁺ values as low as 12 were observed; the validation reference cited (internal report AQ-VAL-019) covers a *different* impeller geometry with D = 320 mm vs. the current D = 415 mm — applicability is not demonstrated

---

## Slide 5 – Boundary Conditions & Problem Setup Fidelity

- **Inlet:** Uniform axial velocity profile derived from upstream pipe flow assumption (fully developed, Re = 4.2 × 10⁵); turbulence intensity set to 5 %, hydraulic diameter = 0.18 m
  - *No measured inlet profile available for this installation; the uniform-profile assumption introduces unknown bias at off-design conditions*
- **Outlet:** Pressure outlet at atmospheric reference; backflow turbulence intensity 10 % (Fluent default retained — not physically justified for this geometry)
- **Walls:** No-slip; adiabatic; surface roughness Ra = 3.2 µm applied to impeller passages per manufacturing spec
- **Rotation:** MRF at 3,550 RPM; interface plane located at 15 % chord downstream of trailing edge — verified against Ansys best-practice guidelines
- **Leakage flows:** Wear-ring leakage not modeled; estimated to contribute < 0.5 % efficiency penalty based on empirical correlation (Gülich, 2008) — acceptable for design-phase accuracy target
- **Assessment:** Setup is representative for design intent; inlet profile uncertainty is a recognized limitation that should be revisited when site measurements become available

---

## Slide 6 – Validation Against Experimental Data

- **Test data source:** Factory acceptance test (FAT) on a geometrically similar pump (D_imp = 395 mm, scaled to current geometry per affinity laws); data from vendor report AQ-FAT-2022-07
- **Comparison metrics:**

  | Operating Point | Measured η (%) | Predicted η (%) | Δη |
  |---|---|---|---|
  | 40 % BEP | 61.3 | 58.9 | −2.4 % |
  | 70 % BEP | 78.1 | 77.6 | −0.5 % |
  | 100 % BEP | 82.4 | 83.1 | +0.7 % |
  | 110 % BEP | 79.8 | 81.9 | +2.1 % |

- **Head-rise comparison:** Within 1.5 % across all operating points — satisfactory
- **Discrepancy at 40 % BEP:** 2.4 % efficiency under-prediction; attributed to unmodeled recirculation losses and the inlet profile assumption — not fully resolved
- **Validation hierarchy concern:** The reference geometry differs by ~5 % in impeller diameter; affinity law scaling assumes geometric and dynamic similarity, which may not hold for recirculation-dominated regimes at low flow
- **⚠ Contradiction flagged:** The executive summary (Slide 12) states *"validation agreement within 1 % across all operating points"* — this is inconsistent with the 2.4 % deviation at 40 % BEP documented in this table; the executive summary appears to have been written before the low-flow data were processed

---

## Slide 7 – Uncertainty Quantification & Error Budget

- **Sources of uncertainty quantified:**
  - Numerical/discretization: GCI-based, 0.83–1.21 % (see Slide 3)
  - Turbulence model form: ±1.6 % efficiency (SST vs. RSM spread)
  - Inlet boundary condition: estimated ±0.8 % (engineering judgment, not formal UQ)
  - Experimental measurement uncertainty (FAT data): ±1.0 % on efficiency per ISO 9906 Grade 1
- **Combined uncertainty (RSS):** ≈ ±2.2 % on efficiency prediction — marginally exceeds the ±2 % project target
- **Sensitivity to roughness:** Parametric sweep from Ra = 1.6 to 6.3 µm showed 0.9 % efficiency variation — within expected range; nominal value retained
- **Formal propagation method:** Not applied; individual contributions estimated separately and combined by root-sum-square — recognized as an approximation
- **Recommendation:** A structured uncertainty propagation study (e.g., Monte Carlo or polynomial chaos) is recommended before Phase 4 design freeze, particularly to address correlated boundary condition and turbulence model uncertainties

---

## Slide 8 – Model Pedigree & Prior Use History

- **ANSYS Fluent version history for this project:**
  - Phase 1 & 2 used Fluent 2021 R2; Phase 3 upgraded to 2023 R1 mid-cycle
  - Regression check performed: BEP efficiency prediction changed by 0.3 % between versions — attributed to updated wall function numerics; considered acceptable
- **Prior applications of this modeling approach:**
  - AQ-SIM-001 through AQ-SIM-008: eight previous pump analyses in the AQUILA family, all using SST k-ω with MRF; all passed FAT within ±2.5 %
  - External benchmark: ERCOFTAC pump test case SHF (Ubaldi et al.) reproduced to within 1.8 % on head coefficient — provides additional confidence in solver/model combination
- **Maturity of approach:** The SST/MRF combination for centrifugal pumps is well-established in open literature; the team has 6+ years of institutional experience with this workflow
- **Deviations from standard practice:** None documented beyond the y⁺ concern noted on Slide 3

---

## Slide 9 – Applicability of Validation Data to Prediction Case

- **Similarity assessment:**
  - Reynolds number: FAT pump Re ≈ 3.8 × 10⁶; current design Re ≈ 4.2 × 10⁶ — within 11 %; turbulent regime fully established in both cases
  - Specific speed Ns: FAT = 1,820 rpm·gpm^0.5/ft^0.75; current = 1,790 — within 2 %; acceptable
  - Geometric similarity: 5 % diameter scale-up; blade angle and passage aspect ratio preserved; wear-ring clearance not scaled (held at 0.3 mm absolute) — introduces a known dissimilarity
- **Operating condition coverage:** Validation data span 40–110 % BEP; prediction cases include 35 % BEP (below validation range) — extrapolation risk acknowledged
- **Fluid properties:** Both cases use water at ~25 °C; no property mismatch
- **Overall applicability:** Moderate-to-good; the wear-ring clearance dissimilarity and the below-range extrapolation at 35 % BEP reduce confidence; these are documented as residual risks

---

## Slide 10 – Software Quality & Configuration Management

- **Fluent 2023 R1:** Commercial release; Ansys holds ISO 9001 certification for software development; release notes document QA testing suite
- **In-house UDF (user-defined function) for impeller angular velocity ramp:** Reviewed by two engineers; version-controlled in GitLab (tag: aquila3-udf-v2.3); unit test confirmed correct RPM profile
- **Simulation input files:** Stored in project repository under `/AQUILA3/CFD/Phase3/`; mesh files, case files, and journal files all version-tagged at Rev B
- **Run log:** Automated convergence monitor exports residual history and integrated quantities at each 50-iteration interval; logs archived
- **Post-processing scripts:** Python 3.11 with NumPy/Matplotlib; scripts version-controlled; peer-reviewed by CFD lead
- **Assessment:** Configuration management practices are adequate for an industrial design study; no gaps identified

---

## Slide 11 – Intended Use & Decision Context

- **Primary decision supported:** Go/no-go on impeller geometry before committing to casting tooling (~$340K investment)
- **Consequence of error:** An over-predicted efficiency at design point could lead to under-sizing the motor drive; an under-predicted recirculation onset could miss a reliability risk
- **Confidence requirement:** Project risk register classifies this as a Medium-High consequence decision; V&V rigor level targeted at ASME V&V 20 "Level 3" (quantified uncertainty with validation)
- **Current assessment vs. requirement:** Discretization and model uncertainty are quantified; combined uncertainty marginally exceeds target; validation geometry is similar but not identical
- **Fitness-for-purpose judgment:** The simulation is considered adequate to support the go/no-go decision at BEP ± 20 %; predictions at 35 % BEP (below validation range) should be treated as indicative only and not used for binding design decisions without additional validation data
- **Deferred items that affect this judgment:** Formal UQ propagation (deferred to Phase 4); site-specific inlet profile measurement (pending installation contractor schedule)

---

## Slide 12 – Executive Summary (as submitted to Program Office)

> *"The AQUILA-3 CFD model has been verified and validated to the required accuracy standard. The SST turbulence model has been validated for this pump family and y⁺ compliance is fully satisfied on all production meshes. Validation agreement is within 1 % across all operating points. The model is recommended for use in all design decisions through Phase 4."*

- **⚠ Review team annotation:**
  - Statement 1 (*"y⁺ compliance fully satisfied"*): **Contradicted** by Slide 3 — y⁺ as low as 12 observed on blade suction side; standard wall functions not valid below y⁺ ≈ 30
  - Statement 2 (*"within 1 % across all operating points"*): **Contradicted** by Slide 6 — 2.4 % deviation at 40 % BEP
  - Statement 3 (*"recommended for all design decisions through Phase 4"*): **Overstated** relative to Slide 11 fitness-for-purpose judgment, which restricts binding use to BEP ± 20 % range
  - **Action required:** Executive summary must be revised before submission to program office; current version should not be transmitted

---

## Slide 13 – Open Items & Recommended Actions

| # | Item | Priority | Owner | Target |
|---|---|---|---|---|
| 1 | Revise executive summary to correct y⁺ and validation accuracy statements | HIGH | CFD Lead | Before gate review |
| 2 | Resolve y⁺ non-compliance on blade suction side: either refine mesh locally or switch to low-Re wall treatment | HIGH | Mesh Engineer | Phase 4 kickoff |
| 3 | Obtain or generate site-specific inlet velocity profile; rerun sensitivity | MEDIUM | Hydraulics Eng. | Phase 4 |
| 4 | Conduct formal uncertainty propagation (Monte Carlo or PCE) for correlated inputs | MEDIUM | V&V Lead | Phase 4 |
| 5 | Acquire validation data at 35 % BEP or document extrapolation risk formally | MEDIUM | Test Coordinator | Phase 4 |
| 6 | Confirm applicability of AQ-VAL-019 to D = 415 mm geometry or commission new validation dataset | HIGH | V&V Lead | Before Phase 4 freeze |

- **Items 1 and 6 are blocking for gate approval in current form**
- Items 2–5 are non-blocking but must be resolved before Phase 4 design freeze

---

## Slide 14 – Appendix: Convergence Monitoring Examples

- Residual plots for representative BEP run (100 % flow):
  - Continuity: drops from 1.0 to 4.3 × 10⁻⁶ over 1,200 iterations
  - x-momentum: 2.1 × 10⁻⁶; y-momentum: 1.8 × 10⁻⁶; z-momentum: 3.0 × 10⁻⁶
  - k and ω: 6.2 × 10⁻⁶ and 5.1 × 10⁻⁶ respectively
- Integrated monitor: stage ΔP stabilizes to < 0.05 % variation over final 200 iterations — convergence confirmed
- **At 40 % BEP:** Residuals plateau at ~2 × 10⁻⁴ for continuity; integrated ΔP oscillates ± 0.3 % — indicative of unsteady physics not captured by steady RANS; this is a known limitation and contributes to the larger discrepancy at this operating point
- **Recommendation:** A transient (sliding mesh, SAS-SST or LES) study at 40 % BEP is warranted if reliability at low-flow conditions becomes a design driver
