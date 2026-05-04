# CFD Credibility Assessment — Axial Compressor Stage Aerodynamics
## Internal Review Slide Deck | Rev C | Program: APEX-7 Turbomachinery Platform

---

### Slide 1 — Scope and Purpose

- **What this deck covers**
  - Steady-state RANS simulation of a single-stage axial compressor (rotor + stator) at 85%, 100%, and 110% design speed
  - Solver: ANSYS Fluent 2023 R1 with SST k-ω turbulence closure
  - Goal: assess whether simulation outputs (total pressure ratio, isentropic efficiency, stall margin) are trustworthy enough to inform blading redesign decisions
- **What this deck does NOT cover**
  - Unsteady rotor-stator interaction (deferred to Phase 3 LES campaign)
  - Thermal effects on blade metal temperature (separate CHT model, not reviewed here)
- **Reviewers should note**
  - This is a *credibility assessment*, not a validation report — the distinction matters for how findings propagate to design authority
  - Contradictions between sections have been flagged with ⚠️ markers; see Slide 11 for reconciliation status

---

### Slide 2 — Simulation Pedigree and Prior Use

- **Code lineage**
  - Fluent's pressure-based coupled solver has an extensive published history in turbomachinery aerodynamics (Cumpsty 1989 comparisons, NASA TM-2012-217656 benchmarks)
  - In-house use on APEX-3 and APEX-5 programs established baseline confidence for similar operating envelopes
  - No bespoke user-defined functions (UDFs) were introduced in this campaign — standard solver physics only
- **Intended use context**
  - Outputs feed a multi-disciplinary optimization loop; errors in efficiency prediction directly bias optimizer reward function
  - Consequence of a 1% efficiency over-prediction: optimizer selects geometries that underperform in rig testing → schedule and cost impact estimated at ~6 weeks slip
- **Relevance to prior campaigns**
  - Rotor tip clearance (0.4% chord) is tighter than APEX-5 geometry; extrapolation of prior confidence is only partially justified
  - ⚠️ Program office memo (dated 14 Feb 2024) states "APEX-7 is a direct derivative of APEX-5 with minimal aerodynamic change" — this characterization is disputed by the CFD team (see Slide 11)

---

### Slide 3 — Geometry and Boundary Condition Fidelity

- **CAD-to-mesh fidelity**
  - Production geometry imported from CATIA V5 via IGES; leading/trailing edge radii preserved to ±0.01 mm
  - Blade count: 22 rotor blades, 37 stator vanes — single-passage periodic model used (pitch ratio 37/22 = 1.682; mixing plane at rotor-stator interface)
  - Tip clearance gap meshed explicitly with 12 prismatic layers; y⁺ target ≤ 1.0 on all viscous walls
- **Inlet boundary specification**
  - Total pressure and total temperature profiles from upstream IGV exit measurements (Test Cell TC-4, March 2023 rig data)
  - Turbulence intensity set to 3.5% with length scale 2 mm — consistent with hot-wire measurements from the same rig
  - ⚠️ **Contradiction noted**: Slide deck from the mesh generation team (internal ref. CFD-MG-2024-003) specifies inlet turbulence intensity of 1.2% "per program standard." The 3.5% value used in the solver input file was confirmed by the lead analyst but the discrepancy has not been formally resolved. Impact on predicted boundary layer transition and separation bubble extent is non-trivial.
- **Exit boundary**
  - Radial equilibrium static pressure at rotor exit; stator exit uses averaged static pressure condition
  - Back-pressure sweep performed from choke to near-stall (11 operating points per speed line)

---

### Slide 4 — Mesh Refinement and Numerical Sensitivity

- **Mesh topology**
  - Structured multi-block O-H topology generated in Pointwise 18.4
  - Three mesh levels prepared: Coarse (~1.8 M cells/passage), Medium (~5.6 M), Fine (~16.2 M)
- **Grid convergence study**
  - Richardson extrapolation applied to total-to-total pressure ratio and isentropic efficiency at design point
  - Grid Convergence Index (GCI) computed per Roache (1998) methodology
    - Pressure ratio GCI (fine-to-medium): **0.31%** — acceptable
    - Efficiency GCI (fine-to-medium): **0.87%** — marginal; within program threshold of 1.0% but close to the tolerance that matters for optimizer fidelity
  - Observed order of convergence p = 1.94 (expected ~2 for second-order scheme) — confirms asymptotic range behavior
- **Residual convergence**
  - All equations converged to 10⁻⁵ (mass, momentum) and 10⁻⁶ (energy) — monitored over last 500 iterations
  - Mass flow imbalance across mixing plane: < 0.02% — satisfactory
- **Discretization scheme**
  - Second-order upwind for all transport equations; PRESTO! scheme for pressure
  - No artificial diffusion or flux limiters active in final production runs

---

### Slide 5 — Turbulence Model Appropriateness

- **Model selection rationale**
  - SST k-ω chosen for its documented performance in adverse pressure gradient flows and mild separation (Menter 1994, Bardina et al. 1997)
  - Alternative considered: Spalart-Allmaras — rejected due to known deficiencies in predicting secondary flow losses in annular passages
- **Sensitivity study**
  - Realizable k-ε run at design point for comparison: efficiency prediction differed by +1.3% relative to SST — outside acceptable band
  - No LES or scale-resolving simulation performed at this stage (cost-prohibitive for full speed line sweeps)
- **Known limitations acknowledged**
  - SST is known to over-predict stall margin in transonic compressors when shock-induced separation is present (Spalart 2000)
  - At 110% speed, rotor passage shock is present; stall margin prediction at this condition should be treated with elevated uncertainty
  - ⚠️ Executive summary (Slide 13) states "turbulence model selection is appropriate across all operating conditions" — this is inconsistent with the limitation acknowledged here and in the analyst's own notes

---

### Slide 6 — Solution Verification Activities

- **Code-level checks**
  - Fluent 2023 R1 regression tests against NASA Rotor 37 benchmark (Reid & Moore 1978): mass-averaged total pressure ratio within 0.4% of published experimental data at design point
  - Internal software QA log (ref. QA-CFD-2023-114) confirms solver version locked and checksummed prior to production runs
  - No in-house developed solver modifications; vendor release notes reviewed for known bugs affecting turbomachinery applications — none flagged for this version
- **Calculation verification**
  - Periodic boundary condition symmetry check: passage-to-passage mass flow variation < 0.05% across 5 independent single-passage runs with perturbed initial conditions
  - Mixing plane conservation: total enthalpy imbalance < 0.1% — within solver documentation tolerance
- **What was NOT done**
  - Method of manufactured solutions (MMS) not applied — deemed out of scope for production campaign; reliance placed on vendor's published MMS results for Navier-Stokes kernel
  - No independent re-implementation of solver to cross-check results

---

### Slide 7 — Experimental Validation Data

- **Available test data**
  - APEX-7 rig test data from Test Cell TC-4 (March 2023): 5-hole probe traverses at rotor exit and stator exit planes
  - Measurements at 85% and 100% speed only — **no rig data available at 110% speed**
  - Inlet total pressure uniformity confirmed: ±0.15% variation across annulus
- **Validation metrics and outcomes**

  | Metric | Speed | Sim | Exp | Δ |
  |---|---|---|---|---|
  | T-T Pressure Ratio | 85% | 1.312 | 1.308 | +0.31% |
  | T-T Pressure Ratio | 100% | 1.487 | 1.479 | +0.54% |
  | Isentropic Efficiency | 85% | 0.881 | 0.876 | +0.57% |
  | Isentropic Efficiency | 100% | 0.868 | 0.855 | +1.52% |

- **Interpretation**
  - Pressure ratio agreement is within measurement uncertainty (probe calibration uncertainty ±0.4%)
  - Efficiency at 100% speed: +1.52% over-prediction exceeds measurement uncertainty — suggests model is optimistic at high loading
  - ⚠️ The validation summary circulated to the program office (email thread, 22 Apr 2024) reported efficiency agreement as "within 1%" — this appears to have selectively cited the 85% speed result only. The 100% speed discrepancy was not highlighted.

---

### Slide 8 — Uncertainty Quantification

- **Sources of uncertainty addressed**
  - Inlet boundary condition uncertainty: ±0.5% total pressure, ±0.3 K total temperature propagated through 8 Monte Carlo runs (Latin hypercube sampling)
  - Turbulence intensity uncertainty (3.5% ± 1.5%): sensitivity coefficient on efficiency = 0.18%/% TI change — modest but non-negligible given the unresolved discrepancy from Slide 3
  - Tip clearance manufacturing tolerance (±0.05 mm): efficiency sensitivity = −0.12%/0.01 mm clearance increase — well-characterized
- **What is NOT quantified**
  - Turbulence model-form uncertainty not formally propagated (acknowledged as the dominant unknown)
  - Geometric uncertainty from surface finish and blade twist under centrifugal loading not included
- **Overall uncertainty estimate**
  - Combined (RSS) numerical + boundary condition uncertainty on efficiency: ±0.6%
  - When model-form uncertainty is informally included (based on k-ε vs. SST spread): effective uncertainty band widens to ±1.5–2.0%
  - This wider band is not reflected in the optimizer interface documentation

---

### Slide 9 — Operator and Workflow Controls

- **Analyst qualification**
  - Lead analyst: 8 years turbomachinery CFD experience, certified per company procedure CP-SIM-004 (Fluent competency assessment)
  - Second analyst performed independent mesh generation and setup replication for design-point case — results agreed to within 0.2% on all key metrics
- **Workflow documentation**
  - Simulation setup documented in controlled procedure SIM-APEX7-CFD-001 Rev B
  - All run scripts version-controlled in GitLab (repo: apex7-cfd, branch: release/v2.3)
  - Post-processing scripts peer-reviewed; known issue with circumferential averaging script corrected in Rev B (prior Rev A had a ±0.3° indexing error in probe plane extraction)
- **Review process**
  - Internal technical review completed 18 March 2024 (reviewers: Dr. K. Osei, Dr. M. Tanaka)
  - No external peer review conducted to date — flagged as gap for Phase 2 design freeze

---

### Slide 10 — Physical Modeling Choices

- **Fluid properties**
  - Air modeled as ideal gas with temperature-dependent viscosity (Sutherland's law); cp = 1006 J/kg·K (constant) — acceptable for the temperature range (290–420 K)
  - Real gas effects: negligible at these conditions (max Mach ~0.85 in rotor passage)
- **Rotation modeling**
  - Multiple Reference Frame (MRF) approach for steady-state; rotor domain rotates at specified RPM, stator domain stationary
  - Mixing plane averages circumferential non-uniformities — known to smear wake interactions; accepted limitation for steady design assessment
- **Wall treatment**
  - Enhanced wall treatment active; y⁺ < 1.0 achieved on 97.3% of wall faces (spot checks on blade suction surface near trailing edge showed y⁺ up to 2.8 in separated region — within acceptable range per Fluent documentation)
- **Heat transfer**
  - Adiabatic walls assumed — consistent with short-duration rig test conditions
  - ⚠️ A separate internal memo (ref. APEX7-THERM-2024-007) recommends that blade metal temperature gradients be included "to correctly capture viscosity variation in the boundary layer near the hub." This recommendation has not been incorporated and its impact has not been assessed.

---

### Slide 11 — Contradictions and Open Issues Log

- **Issue 1 — Turbulence intensity at inlet** (raised Slide 3)
  - CFD solver uses 3.5%; mesh team standard specifies 1.2%
  - Resolution status: **OPEN** — lead analyst believes 3.5% is correct; no formal disposition document exists
  - Risk: if 1.2% is correct, efficiency predictions at 85% speed may be non-conservative by ~0.2–0.3%

- **Issue 2 — Program office characterization of APEX-7 as APEX-5 derivative** (raised Slide 2)
  - Tip clearance and blade loading differ substantially; prior validation confidence should not be directly inherited
  - Resolution status: **OPEN** — CFD team has requested a formal similarity assessment; no response as of deck date
  - Risk: credibility arguments based on APEX-5 heritage are overstated

- **Issue 3 — Efficiency agreement reported as "within 1%" to program office** (raised Slide 7)
  - Actual 100% speed discrepancy is +1.52% — outside the stated threshold
  - Resolution status: **OPEN** — program office has not been updated; design decisions at 100% speed may be based on incorrect confidence level
  - Risk: **HIGH** — optimizer may be selecting geometries based on a model that is known to over-predict efficiency at the primary design point

- **Issue 4 — Turbulence model suitability at 110% speed** (raised Slide 5)
  - Executive summary claims universal suitability; analyst notes acknowledge limitations at transonic conditions
  - Resolution status: **OPEN** — recommend either adding caveat language to executive summary or conducting a scale-resolving sensitivity run at 110% speed

- **Issue 5 — Adiabatic wall assumption** (raised Slide 10)
  - Thermal memo recommends inclusion of metal temperature effects; not yet assessed
  - Resolution status: **OPEN** — low priority for current phase but should be documented as a known assumption

---

### Slide 12 — Summary Assessment by Topic Area

- **Numerical solution quality**: Moderate-High
  - GCI values acceptable; residual convergence solid; second-order scheme appropriate
  - Minor concern: efficiency GCI at 0.87% is close to optimizer sensitivity threshold

- **Physical model representativeness**: Moderate
  - SST k-ω well-justified for most conditions; acknowledged weakness at 110% speed not reflected in summary documents
  - Unresolved inlet turbulence intensity discrepancy introduces unquantified uncertainty

- **Validation evidence**: Moderate-Low
  - Good agreement at 85% speed; concerning over-prediction at 100% speed
  - No validation data at 110% speed — extrapolation required
  - Selective reporting to program office is a process concern independent of technical merit

- **Workflow and process controls**: Moderate-High
  - Strong analyst qualification and version control practices
  - Gap: no external peer review; open issues not formally tracked in a risk register

- **Uncertainty communication**: Low-Moderate
  - Formal UQ performed but model-form uncertainty not propagated to optimizer interface
  - Effective uncertainty band (±1.5–2.0%) not communicated to downstream users

---

### Slide 13 — Recommendations

1. **Immediate**: Issue a formal correction to the program office clarifying the 100% speed efficiency discrepancy; do not allow optimizer to proceed at this speed until the +1.52% bias is understood and either corrected or bounded
2. **Short-term (within 4 weeks)**: Resolve the inlet turbulence intensity discrepancy via a documented technical disposition; run sensitivity cases to bracket the impact
3. **Short-term**: Revise the executive summary to include turbulence model caveats at 110% speed; consider a targeted scale-resolving run (e.g., DDES on a single rotor passage) to bound the stall margin uncertainty
4. **Medium-term**: Commission an external peer review of the CFD methodology prior to Phase 2 design freeze
5. **Medium-term**: Formally propagate model-form uncertainty to the optimizer interface; update the optimizer reward function weighting to reflect the wider effective uncertainty band
6. **Ongoing**: Establish a formal open-issues register linked to the simulation control plan; current informal tracking (slide deck annotations) is insufficient for a design-critical model

---

### Slide 14 — References and Supporting Documents

- ANSYS Fluent 2023 R1 Theory Guide, ANSYS Inc.
- Menter, F.R. (1994). "Two-equation eddy-viscosity turbulence models for engineering applications." *AIAA Journal*, 32(8), 1598–1605.
- Roache, P.J. (1998). *Verification and Validation in Computational Science and Engineering*. Hermosa Publishers.
- Reid, L. & Moore, R.D. (1978). NASA TM-78929 (Rotor 37 experimental data)
- NASA TM-2012-217656 — Benchmark validation of Fluent for turbomachinery applications
- Internal: SIM-APEX7-CFD-001 Rev B — Simulation Control Plan
- Internal: QA-CFD-2023-114 — Software QA Log
- Internal: CFD-MG-2024-003 — Mesh Generation Standards (APEX-7)
- Internal: APEX7-THERM-2024-007 — Thermal Modeling Recommendation Memo
- Internal: CP-SIM-004 — Analyst Competency Procedure

---

*Deck prepared by: CFD Methods Group | APEX-7 Program | Rev C — 02 May 2024*
*Distribution: Program Chief Engineer, Aero Design Lead, V&V Coordinator*
*Classification: Company Confidential — Not for External Distribution*
