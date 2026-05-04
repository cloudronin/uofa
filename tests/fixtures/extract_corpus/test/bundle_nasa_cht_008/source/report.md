# CHT Simulation Review: Turbine Blade Internal Cooling Passages
## Credibility Assessment Slide Deck — Mid-Phase Gate Review
### Program: AETHER-7 High-Pressure Turbine, Rev C

---

## Slide 1 — Purpose & Scope

- **Review objective:** Assess the trustworthiness of conjugate heat transfer (CHT) predictions for the AETHER-7 HPT rotor blade, specifically the serpentine internal cooling network and TBC interface temperatures
- **Tool under review:** Siemens STAR-CCM+ v18.04 coupled with in-house Python post-processing suite (`blade_thermal_v2.3.py`)
- **Operating conditions of interest:**
  - Inlet total temperature: 1,847 K
  - Coolant mass flow: 0.42 kg/s per passage
  - Pressure ratio across cooling circuit: 1.18
- **What this deck covers:**
  - Numerical setup and mesh quality
  - Comparison against experimental rig data (AFRL Turbine Aero Rig, Lot 7)
  - Known gaps and areas where confidence is lower
- **What this deck does NOT cover:**
  - Manufacturing tolerance sensitivity (deferred to Phase 3)
  - Oxidation/spallation life prediction — separate structural team deliverable

---

## Slide 2 — Model Pedigree & Prior Use

- The STAR-CCM+ CHT solver has been used on three previous turbine programs within this organization (HELIOS-4, PRISM-2, CONDOR-X)
  - HELIOS-4 predictions matched thermocouple rake data within ±4.1% on average metal temperature
  - PRISM-2 showed a systematic +6.8% overprediction on pressure-side film effectiveness — root cause traced to a turbulence model mismatch at the film hole exit; corrected in subsequent runs
- **Institutional knowledge transfer:**
  - Lead analyst (Dr. K. Morrow) has 11 years of CHT simulation experience; two supporting engineers have 3–5 years each
  - Formal internal training records on file for STAR-CCM+ v17 → v18 migration; no known breaking changes in the conjugate solver between versions
- **Software quality assurance:**
  - STAR-CCM+ v18.04 is a commercially released, widely validated code
  - In-house post-processing scripts (`blade_thermal_v2.3.py`) underwent a peer code review in January 2024; 14 minor issues resolved, 2 open non-critical items tracked in JIRA (BT-441, BT-447)
  - **CONCERN:** The open script issues (BT-441 relates to spanwise averaging indexing) have not been re-verified since the mesh topology changed in Rev C — this is flagged as a watch item

---

## Slide 3 — Physical Fidelity of the Model

- **Geometry representation:**
  - Full 3-D solid blade modeled including ribs, trip strips, and impingement insert; no mid-plane symmetry assumed
  - TBC layer (150 µm yttria-stabilized zirconia) explicitly meshed as a separate solid region
  - Film cooling holes: 17 of 23 holes modeled explicitly; 6 trailing-edge slots approximated as a distributed source (acknowledged simplification)
- **Material properties:**
  - René N5 alloy thermal conductivity from vendor datasheet (Cannon-Muskegon, 2022 revision); temperature-dependent, 7-point tabulation from 300 K to 1,400 K
  - TBC conductivity: 2.1 W/m·K at 1,000 K — **NOTE:** This value is taken from open literature (Padture et al., 2002); program-specific TBC lot data has NOT been incorporated. Vendor data was requested in Q3 2023 and remains outstanding.
- **Boundary conditions:**
  - Mainstream hot gas: total pressure/temperature profiles from companion RANS stage calculation (ANSYS CFX, run separately)
  - Coolant inlet: mass-flow inlet with measured plenum total temperature (±3 K uncertainty)
  - Outer casing: adiabatic — justified by insulating shroud design but not experimentally confirmed for this configuration
- **Turbulence modeling:**
  - SST k-ω with γ-Reθ transition model activated for external flow
  - Internal passages: realizable k-ε with enhanced wall treatment (y⁺ ≈ 1 on passage walls)
  - **Contradiction flagged in §3 vs. §6:** The setup documentation (§3 of the simulation plan) states SST k-ω is used throughout, including internal passages. The STAR-CCM+ physics continua XML archived in the project repository shows realizable k-ε for internal regions. The slide notes here reflect the XML (confirmed by Dr. Morrow verbally), but the written plan has not been corrected. This discrepancy must be resolved before final report issuance.

---

## Slide 4 — Mesh Refinement Study

- **Baseline mesh:** ~28 million polyhedral cells; prism layer count = 18 on all wetted surfaces
- **Three-level refinement study conducted:**

  | Level | Cell Count | Max Metal Temp (K) | Coolant Exit T (K) |
  |-------|-----------|-------------------|-------------------|
  | Coarse | 11.2 M | 1,204 | 847 |
  | Medium | 28.4 M | 1,189 | 841 |
  | Fine | 61.7 M | 1,186 | 840 |

- Grid Convergence Index (GCI) computed per Roache methodology:
  - Metal temperature GCI (medium→fine): **1.3%** — acceptable
  - Coolant exit temperature GCI: **0.4%** — well converged
- **Observed issue:** The coarse mesh shows a 15 K offset vs. fine — larger than expected. Investigation showed inadequate prism layer resolution near the rib-to-endwall junction in the coarse case. Medium and fine meshes are consistent.
- **Recommendation:** Medium mesh (28.4 M) adopted as production mesh; fine mesh used only for spot-check comparisons at three critical span locations
- **Iterative convergence:** All residuals dropped below 1×10⁻⁵ (continuity, momentum) and 1×10⁻⁶ (energy); monitored over last 500 iterations of 3,000-iteration run; blade average temperature variation < 0.2 K over final 200 iterations

---

## Slide 5 — Comparison to Experimental Data (Primary Validation)

- **Test article:** AFRL Turbine Aero Rig, Lot 7 — scaled cascade with matched Biot number and Reynolds number; not full-temperature (mainstream T_in = 450 K in rig vs. 1,847 K engine)
- **Scaling approach:** Non-dimensional heat transfer coefficient (Nusselt number) and film effectiveness (η) compared; temperature ratio corrections applied per standard methodology
- **Thermocouple comparison (internal passage):**
  - 12 embedded Type-K thermocouples at mid-chord serpentine passage
  - Simulation mean absolute error: **3.8 K** (0.9% of local ΔT)
  - Maximum single-point error: **9.2 K** at TC-07 (pressure side, turn 2) — analyst notes possible conduction error in TC installation; flagged but not resolved
- **External surface IR thermography comparison:**
  - Infrared camera data available for suction side only (pressure side obstructed in rig)
  - Nusselt number distribution: simulation within ±12% across 80% of suction surface
  - **Discrepancy at leading edge (x/C < 0.05):** Simulation predicts Nu ~340; rig data shows Nu ~410 — approximately 21% underprediction. Analyst attributes this to transition model limitations near stagnation; no correction applied to production runs.
- **Overall validation assessment:** Adequate for mid-chord and suction side predictions; leading-edge confidence is reduced

---

## Slide 6 — Uncertainty Quantification Approach

- A **parametric sensitivity sweep** was conducted (not a formal UQ propagation):
  - TBC conductivity varied ±20% around nominal: peak metal temperature shifts ±18 K
  - Coolant inlet temperature varied ±5 K: exit temperature shifts ±4.1 K (near-linear)
  - Mainstream turbulence intensity varied 5% → 15%: leading-edge Nu changes by ~9% (consistent with known sensitivity)
- **What was NOT done:** No formal polynomial chaos or Monte Carlo propagation; no joint probability distribution assigned to inputs
- **Analyst's stated confidence interval:** ±25 K on peak metal temperature (95% coverage)
  - **Concern:** This ±25 K figure appears in the executive summary but is described as "engineering judgment" in the body of the analysis. It is not traceable to the sensitivity sweep results above, which would suggest a larger interval if TBC uncertainty and transition model uncertainty are considered jointly. The basis for the ±25 K claim should be formally documented.

---

## Slide 7 — Code Verification Activities

- **Solver verification (STAR-CCM+ internal):**
  - Siemens publishes annual verification test suite results; v18 suite covers 214 canonical cases including backward-facing step, pin-fin array, and impingement jet
  - Program team did not run independent verification cases specific to this geometry class — relying on vendor-published results
- **In-house script verification:**
  - `blade_thermal_v2.3.py` post-processing: peer review completed (Jan 2024); unit tests cover 11 of 17 functions
  - Spanwise averaging function (implicated in BT-441) lacks a unit test — identified gap
- **Manufactured solution testing:** Not performed for this program; considered out of scope given commercial solver pedigree
- **Version control:** STAR-CCM+ input files (.sim) stored in GitLab repo `aether7-cht`; tagged at Rev B and Rev C; diff reviewed by lead analyst

---

## Slide 8 — Relevance of Validation Data to Production Conditions

- The AFRL Lot 7 rig operates at:
  - Re_c = 5.2×10⁵ (matches engine within 8%)
  - Biot number: matched by design
  - Mainstream temperature: 450 K (engine: 1,847 K) — radiation effects not present in rig; not modeled in simulation either (radiation omitted by assumption)
- **Extrapolation concerns:**
  - At engine temperatures, radiation from hot gas to blade surface could contribute 5–15% of total heat load (per AFRL internal estimate, referenced in rig test report)
  - Current CHT model has NO radiation model active — this is acknowledged in the simulation plan as a known limitation
  - **Contradictory statements:** The executive summary (Slide 1 of the original analyst deck, archived as `AETHER7_CHT_Exec_Rev2.pptx`) states "radiation effects are captured via an effective emissivity boundary condition." The STAR-CCM+ physics XML and Dr. Morrow's verbal confirmation both indicate radiation is OFF. The executive summary statement appears to be carried over from an earlier model configuration and is incorrect for Rev C. This must be corrected.
- **Coolant chemistry:** Rig uses dry air; engine uses air with trace fuel-rich combustion products — no correction applied; considered second-order

---

## Slide 9 — Intended Use & Decision Context

- **Primary use of simulation outputs:**
  1. Identify peak metal temperature location for life prediction input (feeds DARWIN probabilistic fracture code)
  2. Guide cooling circuit redesign — specifically, rib spacing optimization in Pass 3
  3. Support PDR documentation for AETHER-7 program
- **Fitness for purpose assessment:**
  - For use #1 (peak temperature location): Moderate confidence — leading-edge underprediction and missing radiation are concerns, but peak temperature occurs at mid-chord (confirmed by rig data), where simulation accuracy is better
  - For use #2 (rib spacing sensitivity): High confidence — relative trends in passage Nusselt number are well-captured; absolute accuracy less critical for optimization
  - For use #3 (PDR documentation): Adequate if stated limitations are clearly communicated in the PDR package
- **Decisions this simulation should NOT drive alone:**
  - Final material temperature limits sign-off — requires updated TBC vendor data
  - Leading-edge film cooling design — accuracy insufficient at x/C < 0.05

---

## Slide 10 — Sensitivity of Outputs to Key Assumptions

- **Adiabatic outer casing assumption:**
  - Bounding calculation performed: if casing heat flux = 5 kW/m² (conservative estimate), peak blade temperature changes by < 2 K — negligible
- **Film hole simplification (6 TE slots as distributed source):**
  - Compared simplified vs. explicit representation for a 2-D slice model: local temperature difference < 8 K in the trailing-edge region
  - Accepted as adequate for current phase; explicit modeling planned for Phase 3
- **Turbulence model sensitivity (internal passages):**
  - Ran SST k-ω in internal passages as a cross-check (matching the incorrectly documented plan):
    - Passage-averaged Nu: 4% lower than realizable k-ε result
    - This 4% difference translates to approximately 12 K on local metal temperature
    - **This sensitivity is not reflected in the ±25 K uncertainty estimate** — further evidence that the stated confidence interval is underestimated

---

## Slide 11 — Peer Review & Independent Checks

- **Internal peer review:**
  - Simulation plan reviewed by Dr. A. Vasquez (Senior Thermal Engineer, not on analysis team) in November 2023
  - Dr. Vasquez raised the turbulence model documentation inconsistency (now Slide 3 concern) — response logged as "will correct before final report" — NOT YET CORRECTED as of this review date
  - No issues raised regarding the radiation boundary condition at that time (executive summary error predates the peer review)
- **Customer review:**
  - AETHER-7 customer (GE Aerospace) reviewed Rev B results in February 2024; no major technical objections; requested clarification on TBC property source — response provided, vendor data status explained
- **Independent simulation:** No independent replication by a separate team or tool; considered out of scope and budget for this phase
- **Checklist compliance:** Internal CHT simulation checklist (Form CHT-22, Rev 4) completed and signed; 3 of 47 items marked "N/A — deferred"; no items marked non-compliant

---

## Slide 12 — Documentation Quality & Traceability

- **Simulation plan:** `AETHER7_CHT_SimPlan_RevC.docx` — covers geometry, BCs, solver settings, and acceptance criteria; last updated March 2024
  - **Gap:** Turbulence model section not updated to match actual XML (see Slide 3)
- **Results archive:** All .sim files, mesh files, and post-processing outputs stored in GitLab under tag `RevC_Final_Candidate`; reproducible from stored inputs
- **Assumptions log:** 14 documented assumptions in Appendix B of simulation plan; each has an owner and a review status
  - 11 of 14 closed/accepted
  - 3 open: TBC vendor data (O-01), radiation model (O-02), TE slot simplification (O-03)
- **Test data traceability:** AFRL Lot 7 data received under data sharing agreement; raw data files stored in program SharePoint with access-controlled folder; calibration records for thermocouples and IR camera on file
- **Change log:** Rev A → Rev B → Rev C changes documented; major change at Rev C was mesh topology update (structured → polyhedral in internal passages)

---

## Slide 13 — Summary of Confidence Assessment

- **Areas of higher confidence:**
  - Mid-chord internal passage temperatures (well-validated, low GCI, good TC agreement)
  - Relative trends for cooling circuit optimization (rib spacing)
  - Mesh convergence and iterative solution quality

- **Areas of moderate confidence:**
  - Overall peak metal temperature magnitude (radiation gap, TBC property uncertainty)
  - Suction-side external heat transfer (rig data available but ±12% scatter)

- **Areas of lower confidence / active concerns:**
  - Leading-edge heat transfer (21% underprediction vs. rig; no correction)
  - Stated ±25 K uncertainty bound (not formally derived; likely optimistic)
  - Radiation omission at engine conditions (unquantified; estimated 5–15% heat load impact)

- **Open contradictions requiring resolution before PDR:**
  1. Turbulence model specification in simulation plan vs. actual XML (Slide 3)
  2. Executive summary radiation claim vs. actual model configuration (Slide 8)
  3. Uncertainty interval traceability (Slide 6 vs. Slide 10 findings)

---

## Slide 14 — Recommended Actions & Path Forward

| # | Action | Owner | Due |
|---|--------|-------|-----|
| A1 | Correct turbulence model description in SimPlan RevC | Dr. Morrow | 2024-05-15 |
| A2 | Correct executive summary radiation statement | Dr. Morrow | 2024-05-15 |
| A3 | Formally derive and document uncertainty interval with sensitivity data | K. Morrow + UQ lead | 2024-06-01 |
| A4 | Obtain TBC vendor thermal conductivity data (Cannon-Muskegon) | Program manager | 2024-06-15 |
| A5 | Add unit test for spanwise averaging function; re-verify BT-441 with Rev C mesh | Software team | 2024-05-30 |
| A6 | Assess radiation heat load contribution via simplified view-factor model | Thermal team | 2024-07-01 |
| A7 | Explicit TE slot modeling — schedule for Phase 3 | Phase 3 planning | TBD |

- **Gate recommendation:** CONDITIONAL PROCEED — simulation is adequate for rib-spacing optimization and PDR support provided A1 and A2 are resolved; life prediction inputs should be held pending A3 and A4

---

## Slide 15 — Appendix: Validation Data Summary

- **AFRL Lot 7 Rig — Key Parameters:**
  - Test article scale: 2.3× engine scale
  - Mainstream Re: 5.2×10⁵ (engine match ±8%)
  - Coolant-to-mainstream temperature ratio: 0.72 (engine: 0.41 — not matched; Biot number matched instead)
  - Measurement uncertainty: TC ±1.5 K (k=2); IR camera ±3% of reading

- **Simulation vs. Data Summary Table:**

  | Region | Metric | Sim | Rig | Δ% |
  |--------|--------|-----|-----|----|
  | Pass 1 inlet | Nu | 187 | 194 | −3.6% |
  | Pass 2 mid | Nu | 231 | 228 | +1.3% |
  | Pass 3 exit | Nu | 198 | 203 | −2.5% |
  | Suction side (avg) | Nu | 312 | 318 | −1.9% |
  | Leading edge | Nu | 340 | 410 | −17.1% |
  | TC-07 (P-side turn 2) | T (K) | 837 | 846 | −1.1% |

  *Note: Leading-edge Nu discrepancy is 17.1% here vs. "approximately 21%" cited in Slide 5 — the 21% figure was from an earlier Rev B dataset; Rev C shows improvement but discrepancy remains significant.*

- **This inconsistency in the reported leading-edge error (17% vs. 21% across slides) is itself a documentation quality issue and should be clarified in the final report.**
