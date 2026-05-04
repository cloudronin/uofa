# CFD Credibility Assessment — Axial Compressor Stage Aerodynamics
## Internal Review Slides | Milestone 3 | Revision B

---

### Slide 1 — Overview & Scope

- **Simulation campaign:** RANS-based CFD of a single-stage axial compressor (rotor + stator), targeting peak-efficiency operating point and two off-design conditions
- **Solver:** ANSYS CFX 2023 R1; turbulence closure via SST k-ω with curvature correction
- **Purpose of this review:** Assess whether the simulation evidence is sufficient to support design decisions on blade geometry modifications ahead of rig testing
- **Geometry:** 1.4 m tip diameter, 18-blade rotor, 22-blade stator; modeled as a single-passage with mixing-plane interface
- **Operating conditions:** Design mass flow 42 kg/s, inlet total pressure 101.3 kPa, inlet total temperature 288 K
- **Review panel:** Aero-thermal lead, V&V coordinator, external CFD consultant (Dr. R. Holmberg, Turbomachinery Dynamics Ltd.)
- **Caveats up front:** Several evidence threads are incomplete or show internal inconsistencies — flagged on relevant slides

---

### Slide 2 — Intended Use & Decision Context

- The simulation outputs are being used to:
  - Rank three blade camber variants by predicted total-to-total efficiency (Δη ~ 0.3–1.1%)
  - Estimate stall margin reduction from a leading-edge modification
  - Provide boundary conditions for a downstream combustor CFD model
- **Risk framing:** Efficiency ranking decisions carry moderate consequence; stall margin prediction is higher-stakes given proximity to surge in the test campaign
- The team has explicitly scoped out any use of these results for certification or safety-of-flight claims — this is pre-test design guidance only
- Quantity of interest (QoI) hierarchy established:
  - Primary: total-to-total pressure ratio, isentropic efficiency at design point
  - Secondary: spanwise total pressure profile at stator exit, rotor tip leakage loss
  - Tertiary: surface static pressure distributions for boundary condition export

---

### Slide 3 — Governing Equations & Physical Fidelity

- Steady-state RANS with mixing-plane; compressible ideal gas; no heat transfer through walls (adiabatic assumption)
- **Turbulence model choice rationale:**
  - SST k-ω selected for its documented performance in adverse pressure gradient regions
  - LES was considered but ruled out on cost grounds — acknowledged limitation
  - No transition modeling; fully turbulent assumed from leading edge — **this is a known source of discrepancy at part-load**
- **Rotation effects:** Frame change handled via frozen-rotor for off-design sweeps, mixing-plane for design point — inconsistency flagged below (see Slide 9)
- Physical phenomena considered in scope:
  - Tip clearance gap (0.5 mm modeled explicitly)
  - Inlet total pressure distortion (uniform assumed — simplified from rig hardware which has a 4% circumferential distortion)
- Physical phenomena explicitly out of scope:
  - Blade vibration / aeroelastic coupling
  - Film cooling (not applicable to this stage)
  - Real-gas effects (Mach < 0.7 throughout)

---

### Slide 4 — Geometry & Boundary Condition Fidelity

- CAD source: CATIA V5 master model, revision 14C; imported via IGES to ANSYS SpaceClaim
- **Geometry simplifications:**
  - Fillet radii at blade root < 0.8 mm were suppressed — sensitivity not quantified
  - Bleed ports (2× circumferential slots) omitted from model; estimated mass flow extraction is 1.2% of main flow — **not accounted for in mass balance**
  - Seal geometry at rotor hub simplified to a smooth wall
- **Boundary conditions:**
  - Inlet: total pressure and temperature profiles from upstream IGV CFD (separate model, Rev 3)
  - Outlet: averaged static pressure specified; radial equilibrium not enforced — may affect spanwise redistribution
  - Walls: no-slip, adiabatic; y+ maintained between 1 and 5 across rotor blade surfaces (spot-checked at 12 locations)
- **Concern:** The inlet total pressure profile used was from an earlier IGV model revision that did not include the revised IGV trailing-edge geometry. Updated profile was available by the time of this review but was not re-run. Impact on efficiency QoI estimated at ±0.15% by engineering judgment — not formally quantified.

---

### Slide 5 — Mesh Generation & Refinement Study

- Meshing tool: ANSYS TurboGrid 2023 R1; structured H-O-H topology for blade passage
- Three mesh levels generated:
  - Coarse: 1.8 M nodes/passage
  - Medium: 4.6 M nodes/passage
  - Fine: 11.2 M nodes/passage
- **Grid Convergence Index (GCI) analysis performed per Roache (1998) methodology:**
  - Pressure ratio (primary QoI): GCI_fine = 0.31% — acceptable
  - Isentropic efficiency: GCI_fine = 0.48% — marginal but within tolerance for design ranking
  - Tip leakage loss coefficient: GCI_fine = 1.9% — **elevated; fine mesh still not fully resolved in clearance gap**
- Apparent order of convergence p = 1.87 (theoretical ~2 for second-order scheme) — consistent
- **All production runs executed on the medium mesh** (4.6 M nodes) as a balance of accuracy and turnaround time; fine mesh used only for the design-point baseline
- Asymptotic range confirmed for pressure ratio and efficiency; **tip leakage metric NOT in asymptotic range** — Richardson extrapolation not applied there
- Wall y+ statistics: median 2.1, 95th percentile 4.8; isolated regions near leading-edge stagnation reach y+ ~ 8 (flagged, not corrected)

---

### Slide 6 — Solver Settings & Numerical Convergence

- Advection scheme: High Resolution (CFX blended scheme, nominally second-order)
- Convergence criteria: RMS residuals < 1×10⁻⁵ for all transport equations
- **Observed convergence behavior:**
  - Design point: residuals reached 8×10⁻⁶ after 1,200 iterations — satisfactory
  - Off-design case 2 (90% design mass flow): residuals plateaued at 3×10⁻⁵ after 2,500 iterations — **criterion not met**; solution accepted by analyst after monitoring mass flow imbalance (< 0.05%) and pressure ratio oscillation amplitude (< 0.2%)
  - Off-design case 3 (stall-approach, 82% mass flow): residuals never dropped below 1.2×10⁻⁴; significant oscillation in rotor passage — **result flagged as unreliable for quantitative use**
- Imbalances: global mass imbalance < 0.01% for converged cases; momentum imbalance < 0.08%
- Double-precision arithmetic used throughout
- **No time-accurate (unsteady) runs performed** — acknowledged limitation for stall-approach condition

---

### Slide 7 — Code Verification Status

- ANSYS CFX has an established verification history; vendor-published verification cases include:
  - NASA Rotor 37 benchmark (published in ANSYS validation library, Rev 2022)
  - NACA 0012 airfoil drag polar
  - Backward-facing step (turbulence model verification)
- **Internal code verification activities for this project:**
  - Taylor-Green vortex manufactured solution test NOT performed — team relied on vendor documentation
  - No method-of-manufactured-solutions (MMS) exercise conducted in-house
  - Unit testing of custom inlet profile interpolation routine: **performed and passed** (5 test cases, documented in V&V logbook entry CFX-VV-003)
- Assessment: Reliance on vendor verification is standard practice for commercial solvers; however, the absence of any in-house verification of the turbulence model implementation for rotating frame problems is a gap at this credibility level
- **Slide note from reviewer (Dr. Holmberg):** "The vendor NASA Rotor 37 case uses a different mesh topology and older solver version (2021 R2). Direct applicability to current setup is not established."

---

### Slide 8 — Comparison Against Reference Data (Validation Evidence)

- **Primary validation dataset:** NASA Rotor 37 experimental data (Reid & Moore, 1978); widely used community benchmark
  - Pressure ratio vs. mass flow: CFX predictions within 1.2% of experiment across operating line — **good agreement**
  - Spanwise total pressure profile: RMS deviation 1.8% — acceptable
  - Peak efficiency: CFX overpredicts by 1.4 percentage points — **known SST limitation in tip region; partially corrected by curvature correction**
- **Project-specific validation:** No rig data available yet (test campaign scheduled Q3); this is pre-test prediction
- **Surrogate validation:** Comparison to a previously tested similar-geometry stage (Company Archive Case AC-217, 2019):
  - Geometry similarity ratio ~0.87 (scaled); operating conditions differ in Reynolds number by ~15%
  - Efficiency prediction error: 0.9% — within acceptable range claimed by team
  - **Concern:** The 2019 archive case used a different turbulence model (k-ε realizable). The team claims this comparison validates the SST model, but the underlying data was generated with a different closure. This is a methodological inconsistency that weakens the validation claim.
- Uncertainty in experimental reference data: not formally characterized; assumed ±0.3% on efficiency based on rig instrumentation class

---

### Slide 9 — Identified Contradictions & Internal Inconsistencies

*This slide consolidates flags raised elsewhere — reviewers should treat these as open items.*

- **Inconsistency A — Frame change method:**
  - Slide 3 states mixing-plane used for design point and frozen-rotor for off-design sweeps
  - The CFX run log files (attached as Appendix B, not included in this deck) reportedly show frozen-rotor was used for ALL cases including the design point baseline
  - If true, the mixing-plane result cited in the efficiency table (η = 87.3%) may not correspond to the production runs
  - **Status: unresolved; analyst team to clarify before final report**

- **Inconsistency B — Mesh used for production runs:**
  - Slide 5 states medium mesh (4.6 M) used for production; fine mesh for design-point baseline
  - Section 4.2 of the companion technical note (TN-CFD-2024-11) states "all results reported herein were obtained on the fine mesh"
  - Pressure ratio values in both documents agree to 4 significant figures — suggesting one document is wrong about which mesh was used, or the medium and fine meshes give nearly identical results (which would be consistent with GCI but was not explicitly stated)

- **Inconsistency C — Validation claim scope:**
  - Abstract of TN-CFD-2024-11 claims "the model has been validated for prediction of efficiency to within 1% across the operating range"
  - Body of the same document (§5.3) acknowledges validation data covers only the design point and one near-design condition; off-design and stall-approach conditions have no validation basis
  - This is a materially overstated claim relative to the evidence presented

- **Inconsistency D — Inlet distortion treatment:**
  - Slide 3 states uniform inlet total pressure assumed
  - The boundary condition setup table in TN-CFD-2024-11 lists "circumferential distortion profile applied, 4% amplitude, 1-per-rev"
  - These are contradictory; which BC was actually used affects the stall margin prediction significantly

---

### Slide 10 — Sensitivity & Uncertainty Quantification

- **Parametric sensitivities explored:**
  - Tip clearance gap: ±0.1 mm variation → ±0.22% efficiency, ±0.8% pressure ratio
  - Inlet turbulence intensity: 1% vs. 5% → < 0.05% efficiency change (negligible)
  - Outlet static pressure: ±500 Pa → ±0.1% efficiency (well-behaved)
- **Turbulence model sensitivity:** SST vs. k-ε realizable run at design point only
  - Efficiency difference: 0.6 percentage points (SST lower)
  - Pressure ratio difference: 0.4%
  - **No Spalart-Allmaras or RSM comparison performed** — reviewer recommends at least one additional model for the stall-approach condition
- **Formal UQ:** No polynomial chaos, Monte Carlo, or adjoint-based sensitivity analysis performed
  - Team justification: "Schedule did not permit formal UQ; engineering judgment used to bound key uncertainties"
  - Reviewer assessment: Acceptable for design-guidance use; not acceptable if results are later used to set test article acceptance criteria
- Combined uncertainty estimate on primary QoI (efficiency): ±0.7% (team estimate, informal RSS of mesh, BC, and model uncertainties) — **not traceable to a documented methodology**

---

### Slide 11 — Documentation & Traceability

- V&V plan document: CFD-VVP-2024-03, Rev A — exists, covers mesh convergence and comparison to reference data; does not address sensitivity analysis or formal UQ requirements
- Run log completeness: 14 of 17 production cases have complete input decks archived in the project repository (JIRA project CFD-AXL); 3 cases missing solver settings files — **reproducibility concern**
- Results traceability: Efficiency and pressure ratio tables in TN-CFD-2024-11 reference run IDs that map to archived cases — **spot-checked 4 of 14, all consistent**
- Configuration management: CFX project files version-controlled in GitLab (tag v3.2.1); CAD revision tracked separately in Windchill — **no formal link between CAD revision and CFX project file confirmed**
- Post-processing scripts: Python scripts for GCI calculation and spanwise averaging stored in repository; not independently verified but logic reviewed by V&V coordinator
- **Gap:** No formal review of whether the simulation scope and fidelity choices were documented and approved prior to execution — V&V plan appears to have been written after the runs were already underway

---

### Slide 12 — Reviewer Qualifications & Process Independence

- Lead CFD analyst: 8 years turbomachinery CFD experience; ANSYS CFX certified; previously led compressor CFD for two production programs
- V&V coordinator: Independent of analysis team; background in aerospace V&V; reviewed GCI methodology and documentation completeness
- External reviewer (Dr. Holmberg): 20+ years turbomachinery aerodynamics; no financial interest in program outcome; provided written comments (attached)
- **Process independence assessment:**
  - GCI calculation independently reproduced by V&V coordinator using raw mesh size and QoI data — results confirmed
  - Validation comparison plots independently re-generated from archived data — consistent with report
  - **The off-design convergence assessment was NOT independently reviewed** — analyst's judgment that the case 2 solution is acceptable has not been verified by a second party
- Peer review of turbulence model selection: informal discussion documented in meeting minutes (2024-03-15); no formal sign-off

---

### Slide 13 — Applicability & Extrapolation Concerns

- The validation evidence base (NASA Rotor 37 + archive case AC-217) covers:
  - Rotor-only configurations (no stator interaction validated)
  - Reynolds number range: 8×10⁵ to 1.4×10⁶ chord-based
  - Mach number range: 0.4–0.9 relative tip Mach
- **Current application extends to:**
  - Stage configuration (rotor-stator interaction via mixing plane) — extrapolation from rotor-only validation
  - Near-stall condition (82% mass flow) — outside validated operating range
  - Inlet distortion effects — no validation basis (see Inconsistency D)
- Interpolation vs. extrapolation judgment:
  - Design-point efficiency ranking: **interpolation** — moderate confidence
  - Stall margin prediction: **extrapolation** — low confidence; results should be treated as qualitative indicators only
- Team has acknowledged these limits in the technical note executive summary — **however, the summary conclusions section does not repeat these caveats**, creating a risk that downstream users will not appreciate the limitations

---

### Slide 14 — Open Items & Recommended Actions Before Final Acceptance

| # | Item | Owner | Priority |
|---|------|-------|----------|
| 1 | Resolve Inconsistency A (frame change method in production runs) | CFD Lead | **Critical** |
| 2 | Resolve Inconsistency D (inlet distortion BC actually applied) | CFD Lead | **Critical** |
| 3 | Update TN-CFD-2024-11 abstract to accurately bound validation scope | V&V Coord | High |
| 4 | Archive missing solver settings for 3 production cases | CFD Lead | High |
| 5 | Quantify sensitivity to root fillet suppression | CFD Lead | Medium |
| 6 | Obtain independent review of off-design convergence acceptance | External Reviewer | Medium |
| 7 | Formally link CAD revision to CFX project file in CM system | CM Engineer | Medium |
| 8 | Consider additional turbulence model run at stall-approach condition | CFD Lead | Low/Deferred |

---

### Slide 15 — Preliminary Credibility Summary

*Ratings below are PRELIMINARY pending resolution of open items. Scale: Adequate / Marginal / Inadequate for intended use.*

- **Mesh refinement & numerical error:** Marginal — GCI acceptable for primary QoIs; tip leakage not resolved; off-design convergence not met
- **Physical model fidelity:** Marginal — SST appropriate for design point; no transition model; inlet distortion treatment unclear
- **Comparison to reference data:** Marginal — NASA Rotor 37 comparison adequate; project-specific validation absent pre-test; validation scope overstated
- **Documentation & traceability:** Marginal — V&V plan exists but written post-hoc; 3 missing run archives; CM linkage gap
- **Uncertainty characterization:** Inadequate — informal RSS estimate not traceable; no formal UQ; sensitivity study incomplete
- **Code correctness:** Adequate (with caveat) — reliance on vendor verification accepted; custom routine verified; reviewer concern about version applicability noted
- **Overall preliminary rating: MARGINAL** — results are suitable for design-guidance and blade ranking at design point only; stall margin and off-design quantitative predictions should not be used until open items 1, 2, and 3 are resolved

---

*End of slide deck. Prepared by V&V Coordination Office. Distribution: Program Aero Lead, Chief Engineer, External Reviewer. Not approved for external release.*
