# CHT Solver Assessment — Turbine Blade Internal Cooling Channel Model
## V&V Status Briefing | Program: AERO-COOL Phase IIb | Revision 0.4

---

## Slide 1 — Purpose & Scope

- **Objective:** Evaluate the predictive reliability of the AERO-COOL conjugate heat transfer model for a multi-pass serpentine cooling channel in a high-pressure turbine blade
- **Solver platform:** ANSYS Fluent 2023 R1 with user-defined property tables; CHT coupling via native solid-fluid interface
- **Scope of this review:**
  - Internal channel flow (Re 8,000–45,000)
  - Steady-state metal temperature distribution
  - Pressure drop across ribs and bends
- **Out of scope (deferred to Phase III):**
  - Film cooling holes
  - Transient thermal cycling
  - Oxidation / creep coupling
- **Audience:** Program V&V lead, turbine aero team, independent reviewer

---

## Slide 2 — Model Pedigree & Intended Use Context

- Model was originally developed for a research program (DARPA-HTEC, 2019–2021) targeting academic validation; current application is **design-support for a flight-critical component**
  - This represents a significant **expansion of intended use** — the original model was never stress-tested at the operating pressures now being requested (up to 28 bar)
  - No formal re-scoping document exists; the team verbally agreed the extension was "engineering judgment"
- Hardware context: Inconel 718 blade, chord ~62 mm, 5-pass channel with 45° angled ribs, rib pitch-to-height ratio P/e = 10
- Coolant: compressed air at inlet total temperature 650 K, inlet total pressure 22–28 bar
- **Intended use classification:** The model outputs feed directly into life prediction and are used to set inspection intervals — this is a **high-consequence use case**
  - The review team notes that documentation of this consequence level was only added to the model record in the current revision; earlier revisions described the model as "preliminary design guidance only"

---

## Slide 3 — Governing Equations & Physical Assumptions

- Reynolds-Averaged Navier-Stokes (RANS) with realizable k-ε turbulence closure
  - Wall treatment: enhanced wall functions, y⁺ target 1–5 on rib surfaces
  - Buoyancy terms neglected (Ri < 0.02 for all operating points — justified)
- Solid conduction: isotropic thermal conductivity for Inconel 718 using Touloukian curve-fit (validated separately by materials group)
- Radiation: neglected inside cooling channel — **this assumption is stated as justified in §3.2 of the solver theory guide**, but a separate internal memo (Ref. TN-2024-017) flags that at wall temperatures above 1100 K, radiation contributes ~4–7% of total heat flux at the rib tips
  - The main slide deck does not reconcile this discrepancy; the memo is listed only in the reference log
- Fluid properties: ideal gas with polynomial fits to NIST data; Pr = 0.71 assumed constant
  - Constant Prandtl number is a recognized simplification at high pressure; sensitivity not quantified in current documentation

---

## Slide 4 — Software Baseline & Configuration Control

- Fluent 2023 R1 build 23.1.0.282 — release notes reviewed; no known solver bugs affecting CHT in this regime
- Case files version-controlled in GitLab repo `aero-cool/cht-blade-v2`; mesh files stored in LFS
- **UDF (user-defined function) for rib heat transfer augmentation factor:** version 2.3 compiled and linked
  - UDF source code is in the repo; however, **the compiled binary (.so file) on the cluster does not match the hash of the source-compiled version** — discrepancy noted by IT on 14 March 2024, not yet resolved
  - This is a potential configuration integrity issue; results generated after 14 March may reflect an unknown UDF state
- Pre-processing: ANSYS Meshing 2023 R1; post-processing: CFD-Post + in-house Python scripts (version-tagged)
- Operating system: RHEL 8.6; MPI: OpenMPI 4.1.2

---

## Slide 5 — Mesh Refinement Study

- Three structured hexahedral meshes generated: Coarse (2.1M cells), Medium (6.8M cells), Fine (17.4M cells)
- Richardson extrapolation applied to Nusselt number (area-averaged over rib-roughened surface) and total pressure drop
- **Grid Convergence Index (GCI) results:**
  - Nu_avg: GCI_fine = 1.8%, GCI_medium = 4.3% → apparent order p = 1.94 (close to nominal 2nd-order)
  - ΔP_total: GCI_fine = 0.9%, GCI_medium = 2.1% → p = 2.07
- Medium mesh selected for production runs (balance of accuracy and runtime ~6 hr on 128 cores)
- **Solid mesh:** 380,000 hexahedral elements; no formal refinement study performed on solid domain
  - Team argues solid conduction is "not the limiting physics" — this is plausible but undocumented
- Wall y⁺ distribution: median 2.1, 95th percentile 6.8 — a small number of cells near the bend exits exceed y⁺ = 11; impact not assessed

---

## Slide 6 — Code Verification Activities

- Fluent solver itself: ANSYS internal verification suite results cited (v&v summary document ANS-VV-2023-CHT); not independently reproduced
- **In-house verification tests performed:**
  - Fully-developed duct flow with uniform heat flux: analytical Nusselt number (Dittus-Boelter) recovered within 1.2% on medium mesh ✓
  - Conjugate slab problem (1D conduction + convection): temperature profile matches analytical solution within 0.3% ✓
  - Rib-roughened channel benchmark (NASA TM-2003-212790 geometry): Nu augmentation within 6% of published DNS data at Re = 10,000 ✓
- **Observed inconsistency:** The rib benchmark test uses the k-ω SST model in the verification slides, but production runs use realizable k-ε
  - The justification for switching turbulence models between verification and production is not documented; a comment in the GitLab issue tracker (#114) says "SST was too slow, switched to k-e, results look fine" — this is insufficient justification for a flight-critical application
- No method of manufactured solutions (MMS) study has been performed

---

## Slide 7 — Comparison Against Experimental Data

- **Primary validation dataset:** In-house rig test (Rig COOL-3B), Inconel 718 blade section, 5-pass geometry, instrumented with 48 Type-K thermocouples and 6 pressure taps
  - Test matrix: 4 coolant flow rates × 3 heat flux levels = 12 operating points
  - Uncertainty analysis: thermocouple ±2.5 K (k=2), pressure tap ±0.15% FS
- **Temperature predictions:**
  - Mean absolute error across all 48 TC locations, all 12 points: **14.3 K**
  - Maximum single-point error: **38 K** at TC-31 (located near 3rd-pass bend exit)
  - The 38 K outlier is attributed in the text to "possible thermocouple installation error" — **no corrective action or re-test is documented**
- **Pressure drop predictions:**
  - Within 5% of measured values for 10 of 12 points; two high-flow points overpredict by 11–13%
- **Secondary validation:** Comparison to open-literature data (Han et al., ASME J. Turbomachinery, 1988) for rib geometry only
  - Good agreement (within 8%) for Re < 20,000; diverges at higher Re — acknowledged in notes but not flagged as a limitation for the 28-bar operating point which reaches Re ~ 42,000

---

## Slide 8 — Uncertainty Quantification

- **Input uncertainty propagation:** Monte Carlo study (500 samples) varying:
  - Inlet total temperature: ±15 K (1σ)
  - Inlet mass flow rate: ±2% (1σ)
  - Solid thermal conductivity: ±3% (1σ based on Touloukian scatter)
- Output: 95th-percentile spread in peak metal temperature = ±22 K
- **Turbulence model uncertainty:** NOT formally quantified
  - A note in the appendix states "turbulence model sensitivity is expected to be secondary" — **this contradicts the 38 K outlier near the bend exit**, where secondary flow structures are dominant and RANS models are known to struggle
- **Numerical uncertainty (from GCI):** ±1.8% on Nu → translates to approximately ±8 K on metal temperature (estimated by team)
- Total combined uncertainty budget: **not formally assembled**; individual components exist in separate documents but have not been root-sum-squared or otherwise combined into a single statement
  - This is a notable gap for a high-consequence application

---

## Slide 9 — Sensitivity & Parametric Coverage

- Parametric sweeps performed:
  - Coolant inlet temperature: 600–750 K (5 points)
  - Mass flow rate: 0.08–0.18 kg/s (5 points)
  - Rib angle: 30°, 45°, 60° (3 configurations)
- Results tabulated in internal report AERO-COOL-TR-2024-04
- **Operating pressure sensitivity:** Only one pressure level (22 bar) tested in the parametric sweep
  - Production intent includes 28 bar; no validation data or sensitivity runs exist at this condition
  - The team notes "pressure effect on heat transfer is captured through density in the Re number" — this is partially correct but ignores real-gas effects and potential changes in turbulent Prandtl number at high pressure
- Geometric sensitivity: rib height variation ±10% studied; results show ±7% change in Nu_avg — documented

---

## Slide 10 — Independent Review & Peer Scrutiny

- Internal peer review conducted by Dr. A. Petrov (turbine aero, not involved in model development) — review memo dated 22 Feb 2024
  - Dr. Petrov flagged the turbulence model switch (also noted in Slide 6) and the missing radiation contribution
  - **Response to review:** Both items marked "acknowledged, to be addressed in Phase III" — no resolution in current revision
- External review: none performed to date
  - Program schedule does not currently include an external independent technical review; this is flagged as a risk by the V&V lead
- Standards compliance: model development nominally follows ASME V&V 20-2009 for fluid dynamics; no formal compliance matrix has been completed

---

## Slide 11 — Operational Context & User Interaction

- Model is run by two engineers (E. Nakamura and T. Osei) who were involved in its development
  - No formal training record or qualification procedure exists for new users
  - A "quick-start guide" (3 pages) is available on the SharePoint; it does not cover edge cases or known failure modes
- Post-processing scripts produce a standardized PDF report; however, the **script does not flag when y⁺ exceeds acceptable limits** — users must manually check
- No formal review of potential operator error modes has been conducted (e.g., incorrect boundary condition entry, wrong UDF version loaded)
  - The UDF version mismatch identified in Slide 4 is an example of exactly this class of problem occurring in practice

---

## Slide 12 — Documentation & Traceability

- Model documentation package (MDP-AERO-COOL-002, Rev 0.4) covers:
  - Geometry and mesh description ✓
  - Boundary condition specification ✓
  - Solver settings and convergence criteria ✓
  - Validation summary ✓ (partial — see gaps above)
- **Gaps identified:**
  - No formal assumptions log (assumptions are scattered across slides, theory guide, and TN-2024-017)
  - Uncertainty budget not consolidated
  - UDF version control issue unresolved
  - No record of the decision to expand scope from research to flight-critical use
- Version history in MDP is incomplete: Rev 0.1 and 0.2 are missing from the document control system; only Rev 0.3 and 0.4 are available

---

## Slide 13 — Summary Assessment & Recommended Actions

- **Strengths:**
  - Solid mesh refinement study with GCI < 2% on key QoIs (fluid domain)
  - Reasonable agreement with in-house rig data for most operating points
  - Monte Carlo UQ on primary inputs completed
  - Code verification against analytical and benchmark cases (with caveats)

- **Key concerns (action required before production use):**
  1. Resolve UDF binary/source hash mismatch — re-run affected cases after confirmation
  2. Document and justify turbulence model selection (k-ε vs. SST); perform sensitivity comparison
  3. Quantify radiation contribution at high-temperature conditions; update or justify neglect
  4. Obtain validation data (or defensible justification) at 28 bar operating condition
  5. Assemble consolidated uncertainty budget
  6. Address TC-31 outlier: re-test or provide physical explanation
  7. Establish user qualification procedure and update post-processing scripts to include automated QC checks

- **Overall readiness:** Model is **NOT recommended for flight-critical design decisions** in current state. Suitable for continued design-space exploration with engineering judgment applied to results. Re-assessment recommended after items 1, 2, 3, and 6 are resolved.

---

## Slide 14 — Open Issues Log (Summary)

| # | Issue | Severity | Owner | Status |
|---|-------|----------|-------|--------|
| 01 | UDF binary mismatch | High | T. Osei | Open |
| 02 | Turbulence model justification | High | E. Nakamura | Open |
| 03 | Radiation at high T | Medium | E. Nakamura | Deferred Ph.III |
| 04 | 28-bar validation gap | High | Program lead | Open |
| 05 | TC-31 outlier explanation | Medium | Test team | Open |
| 06 | Consolidated UQ budget | Medium | V&V lead | Open |
| 07 | User qualification procedure | Low | Program lead | Open |
| 08 | Solid domain mesh study | Low | E. Nakamura | Deferred Ph.III |
| 09 | External independent review | Medium | Program lead | Not scheduled |

---

## Slide 15 — References & Supporting Documents

- ANSYS Fluent Theory Guide, Release 2023 R1 (ANS-TG-2023-FLU)
- ANSYS V&V Summary, CHT Module (ANS-VV-2023-CHT)
- AERO-COOL Model Documentation Package MDP-AERO-COOL-002 Rev 0.4
- Internal Technical Note TN-2024-017: Radiation Effects in Cooling Channels at T > 1100 K
- Internal Test Report: Rig COOL-3B Campaign Results, Feb 2024
- AERO-COOL Parametric Study Report AERO-COOL-TR-2024-04
- Han, J.C., Park, J.S., Lei, C.K. (1988), ASME J. Turbomachinery, 110(3)
- NASA TM-2003-212790, Rib-Roughened Channel DNS Benchmark
- Dr. A. Petrov Peer Review Memo, 22 Feb 2024
- GitLab Issue Tracker, `aero-cool/cht-blade-v2`, Issue #114
- ASME V&V 20-2009, Standard for Verification and Validation in Computational Fluid Dynamics and Heat Transfer
