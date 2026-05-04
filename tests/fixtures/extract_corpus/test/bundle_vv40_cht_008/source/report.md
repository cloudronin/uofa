# CHT Simulation Review: Turbine Blade Internal Cooling Channel — V&V Status Slides
### Program: APEX-7 High-Pressure Turbine, Phase 2B Credibility Review
### Prepared by: Thermal Analysis Group, Rev. C

---

## Slide 1 — Scope and Motivation

- **Simulation objective:** Predict metal temperature distributions and coolant pressure drop in a three-pass serpentine cooling channel for the APEX-7 Stage-1 HPT blade
- **Code under review:** ANSYS Fluent 2023R2 with user-defined conjugate wall coupling; secondary solver cross-checks performed in OpenFOAM v2206 (k-ω SST)
- **Why this review matters:**
  - Blade life predictions feed directly into maintenance interval scheduling
  - Over-temperature exceedances in prior program (APEX-5) traced to unconservative CFD boundary conditions
  - Program office requires documented simulation credibility before hardware sign-off at CDR
- **Slide deck covers:** grid sensitivity, physical model choices, comparison against available experimental data, uncertainty sources, and outstanding open items
- **What this deck does NOT cover:** probabilistic life analysis (deferred to Phase 3), oxidation model validation (vendor data not yet received from Rolls-Royce HTM)

---

## Slide 2 — Physical Configuration and Boundary Conditions

- **Geometry:** Full 3-D solid + fluid domain; blade chord ~42 mm, three-pass channel with trip strips at 45°; tip cap included
- **Fluid:** Air at engine representative conditions — inlet total pressure 38.4 bar, inlet total temperature 820 K, coolant-to-mainstream temperature ratio 0.62
- **Solid:** IN-738LC nickel superalloy; temperature-dependent conductivity from MMPDS-12 tabulated data
- **Thermal boundary conditions:**
  - Mainstream hot gas: convective BC derived from RANS stage CFD (separate run, Turbo-RANS v4.1); heat transfer coefficient map applied as profile BC
  - Coolant inlet: mass flow rate 0.0083 kg/s per passage, uniform total temperature
  - External film cooling holes: modeled as sink terms — *NOTE: film effectiveness distribution assumed uniform at η = 0.35; actual spatially varying distribution from rig test is available but was not yet incorporated at time of this analysis (see Slide 11)*
- **Potential concern flagged by reviewer DR-022:** The mainstream HTC profile was generated at a different rotor speed (14,200 RPM) than the current design point (14,850 RPM); sensitivity study pending

---

## Slide 3 — Governing Equations and Physical Model Selection

- **Turbulence treatment:** k-ω SST throughout fluid domain; wall y+ maintained between 0.8 and 2.1 on channel walls (confirmed via post-processing script `yplus_check_v3.py`)
- **Conjugate coupling:** Implicit coupling at fluid-solid interface; energy equation solved simultaneously across domains; interface temperature continuity enforced to residual < 1×10⁻⁷
- **Radiation:** Participating medium radiation neglected in coolant channel (optical thickness argument: τ < 0.01 at channel dimensions); external blade surface radiation included via DO model with emissivity ε = 0.85
- **Buoyancy effects:** Boussinesq approximation active in all three passes; Richardson number Ri ≈ 0.18 in second pass — borderline for buoyancy significance, included per conservative practice
- **Trip strip heat transfer augmentation:** Resolved geometrically rather than modeled empirically — this is a deliberate choice to avoid reliance on correlations outside their validated Re range
- **Open question (not resolved this phase):** Whether the SST model adequately captures reattachment heat transfer downstream of trip strips at Re_Dh ~ 18,000; literature suggests 15–25% underprediction possible (Han & Park, 1988 benchmark)

---

## Slide 4 — Grid Sensitivity Study

- **Mesh strategy:** Polyhedral core with prismatic inflation layers; generated in ANSYS Meshing 2023R2
- **Three grid levels tested:**

  | Level | Total Cells (fluid+solid) | Avg. Wall y+ | Peak Metal Temp (K) |
  |-------|--------------------------|--------------|---------------------|
  | Coarse | 4.2 M | 1.9 | 1,187 |
  | Medium | 11.7 M | 1.4 | 1,204 |
  | Fine | 31.4 M | 0.9 | 1,208 |

- **Richardson extrapolation applied** to peak metal temperature and passage-averaged Nusselt number:
  - Grid Convergence Index (GCI) fine-to-medium: **1.3%** on peak T_metal
  - GCI fine-to-medium: **2.1%** on Nu_avg (second pass)
  - Apparent order of convergence p = 1.87 (expected ~2 for second-order scheme)
- **Decision:** Medium mesh (11.7 M cells) adopted for production runs as engineering compromise between accuracy and turnaround time (~18 hrs on 256-core cluster vs. ~54 hrs for fine)
- **Contradiction flag (internal):** The executive summary on Slide 13 states "fine mesh used for all reported results" — this is INCORRECT; medium mesh was used. This discrepancy was introduced during slide revision and has not been corrected as of Rev. C. Readers should treat Slide 13 summary statistics with caution until reconciled.

---

## Slide 5 — Solver and Numerical Settings

- **Pressure-velocity coupling:** Coupled solver (ANSYS Fluent pseudo-transient formulation); pseudo time step 1×10⁻⁴ s
- **Spatial discretization:** Second-order upwind for momentum and energy; QUICK scheme tested on medium mesh — negligible difference (<0.3 K) in peak temperature
- **Convergence criteria:**
  - Continuity: 1×10⁻⁵
  - Momentum: 1×10⁻⁶
  - Energy: 1×10⁻⁸
  - Monitored via area-averaged outlet temperature and blade tip temperature — both flat to < 0.1 K over final 500 iterations
- **Code-level verification (unit tests):** Fluent's built-in manufactured solution test for conjugate heat transfer was run on a 2-D slab geometry; temperature error norm < 0.02% relative to analytical solution — confirms solver implementation is functioning correctly for diffusion-dominated regimes
- **Cross-code comparison:** OpenFOAM v2206 (chtMultiRegionFoam) run on equivalent medium mesh; peak metal temperature 1,211 K vs. Fluent 1,204 K — 0.6% difference, within expected inter-code variability
  - *Note: OpenFOAM run used a slightly different inlet turbulence intensity (5% vs. 3% in Fluent); this was not matched intentionally and may account for part of the discrepancy — acknowledged as a limitation*

---

## Slide 6 — Experimental Comparison: Nusselt Number Benchmarking

- **Reference dataset:** University of Stuttgart rig data (Schüler et al., 2011) — smooth two-pass channel, Re_Dh = 15,000–25,000, rotation number Ro = 0–0.3
- **Comparison metric:** Passage-averaged Nusselt number ratio Nu/Nu₀ on leading and trailing walls
- **Results:**

  | Wall | Re | Ro | Exp. Nu/Nu₀ | Sim. Nu/Nu₀ | % Error |
  |------|----|----|-------------|-------------|---------|
  | Trailing | 18,000 | 0.15 | 2.41 ± 0.12 | 2.29 | −5.0% |
  | Leading | 18,000 | 0.15 | 1.63 ± 0.09 | 1.71 | +4.9% |
  | Trailing | 22,000 | 0.25 | 2.68 ± 0.14 | 2.44 | −9.0% |
  | Leading | 22,000 | 0.25 | 1.55 ± 0.11 | 1.78 | +14.8% |

- **Assessment:** Agreement is acceptable at lower rotation numbers; at Ro = 0.25 the leading wall overprediction of +14.8% exceeds the ±10% program acceptance criterion
- **Mitigating context:** Schüler geometry has smooth walls; APEX-7 channel has trip strips — direct applicability is imperfect. A dedicated trip-strip rotation rig dataset (NASA/CR-2019-220215) shows better agreement (within 8%) but only covers Ro ≤ 0.18
- **Conclusion from thermal analysis group:** Model is conditionally adequate for design intent but overpredicts leading-wall cooling at high rotation — conservative for blade life (underpredicts metal temperature on leading edge) but potentially non-conservative for trailing edge

---

## Slide 7 — Uncertainty Quantification: Input Parameter Sensitivity

- **Method:** One-at-a-time (OAT) sensitivity study; ±1σ perturbations on key inputs
- **Parameters varied and peak T_metal response:**

  | Parameter | Nominal | Perturbation | ΔT_peak (K) |
  |-----------|---------|--------------|-------------|
  | Coolant mass flow | 0.0083 kg/s | ±5% | ∓14 K |
  | Mainstream HTC | Profile BC | ±10% | ±22 K |
  | Solid conductivity (k) | MMPDS-12 | ±3% | ∓4 K |
  | Film effectiveness η | 0.35 uniform | ±0.05 | ∓18 K |
  | Inlet total temperature | 820 K | ±15 K | ±11 K |

- **Dominant uncertainty source:** Mainstream HTC profile (±22 K) and film effectiveness assumption (±18 K)
- **Combined RSS uncertainty estimate:** ±34 K on peak metal temperature (assuming independent inputs)
- **Important caveat:** This is NOT a full uncertainty propagation — correlations between HTC and film effectiveness (both derived from the same stage CFD run) are ignored. A formal UQ study using Dakota v6.17 is planned for Phase 3 but was not completed for this review cycle.
- **Contradiction note (subtle):** Slide 2 states film effectiveness was held at η = 0.35 uniform because rig data "was not yet incorporated." However, the sensitivity table above varies η ± 0.05 around 0.35, implying the team had sufficient knowledge to bound this parameter. The basis for the ±0.05 bound is not documented in the analysis record — this was flagged by reviewer DR-019 as requiring clarification.

---

## Slide 8 — Comparison Against In-House Rig Data (APEX Cooling Rig, Facility 4B)

- **Test article:** Scaled (2.5×) aluminum model of APEX-7 cooling channel, operating at matched Re_Dh and Ro; heat flux applied via thin-film heaters on channel walls
- **Measurements:** Infrared thermography on external wall (±2 K uncertainty per calibration report CAL-2023-047); pressure taps at inlet/outlet and inter-pass turn
- **Temperature comparison (second pass, trailing wall):**
  - Rig: 342 K (non-dimensional Θ = 0.71)
  - Simulation (scaled): Θ = 0.68
  - Difference: ~4% in non-dimensional temperature — within measurement uncertainty
- **Pressure drop comparison:**
  - Rig total ΔP: 1,847 Pa
  - Simulation: 1,791 Pa (−3.0%)
  - Within ±5% program acceptance criterion ✓
- **Limitation acknowledged:** Rig uses aluminum (k ≈ 160 W/m·K) vs. IN-738LC (k ≈ 11 W/m·K at 900 K) — Biot number similarity not maintained; solid conduction path is not representative. Rig data therefore validates fluid-side heat transfer only, not the coupled solid response.
- **Second contradiction (significant):** The rig test report (Facility 4B Test Report APEX-4B-2023-09) states the test was conducted at Re_Dh = 16,400, but the simulation comparison on this slide uses a boundary condition of Re_Dh = 18,000. The thermal analysis group's internal memo (TAG-M-2023-112) acknowledges this mismatch but concludes "the difference is within the acceptable operating envelope." No re-run at matched Re has been performed.

---

## Slide 9 — Applicability of Reference Data and Model Pedigree

- **Is this the right model for this application?**
  - The simulation represents a three-pass serpentine geometry with 45° trip strips and a tip cap — geometry is directly representative of the APEX-7 design
  - Operating conditions (Re_Dh, Ro, buoyancy parameter Bo) are within the range of the validation datasets cited in Slides 6 and 8
  - Extrapolation concern: The highest rotation number in the validation database is Ro = 0.30; the APEX-7 design point corresponds to Ro = 0.27 — within range, but near the upper bound
- **Model pedigree:**
  - k-ω SST for internal cooling channels: extensively used in literature; known limitations at high Ro documented (Iacovides & Launder, 1995; Saha & Acharya, 2005)
  - Conjugate coupling approach: standard practice; no known implementation defects in Fluent 2023R2 for this use case
  - Trip strip geometry: resolved (not modeled) — increases confidence relative to correlation-based approaches
- **Overall judgment from team:** The physical model choices are appropriate for the design phase; limitations are bounded and documented

---

## Slide 10 — Sensitivity of Conclusions to Modeling Assumptions

- **What if buoyancy is turned off?**
  - Peak metal temperature increases by 9 K (buoyancy aids cooling in second pass)
  - Trailing wall Nu/Nu₀ drops from 2.29 to 2.11 — further from experimental data
  - Confirms buoyancy inclusion is physically correct and improves agreement
- **What if the mainstream HTC profile is replaced with a uniform value (area-average)?**
  - Peak metal temperature changes by < 3 K — blade peak is located in a region of near-uniform HTC
  - Pressure drop unaffected
  - Suggests HTC profile uncertainty (±22 K from Slide 7) may be conservative for the peak temperature location specifically
- **What if DO radiation on external surface is turned off?**
  - Peak metal temperature increases by 6 K — non-negligible but second-order effect
  - Radiation should be retained
- **Sensitivity summary:** Conclusions are robust to most modeling choices except (a) film effectiveness distribution and (b) mainstream HTC magnitude — both of which require resolution before final sign-off

---

## Slide 11 — Open Items and Deferred Work

- **OI-001 (High priority):** Incorporate spatially varying film effectiveness distribution from rig test (data available from Aero group, contact J. Hartmann). Expected impact: ±18 K on peak temperature. Target: before CDR.
- **OI-002 (Medium priority):** Re-run rig comparison at matched Re_Dh = 16,400 to resolve mismatch identified in Slide 8. Estimated effort: 4 hours compute + 2 hours post-processing.
- **OI-003 (Medium priority):** Reconcile executive summary (Slide 13) statement about fine mesh vs. actual medium mesh used. Update all reported values accordingly or re-run on fine mesh.
- **OI-004 (Low priority for Phase 2B):** Full probabilistic UQ using Dakota — deferred to Phase 3 per program plan.
- **OI-005 (Low priority):** Oxidation model validation data from Rolls-Royce HTM not yet available — not blocking Phase 2B but required for Phase 3 life analysis.
- **OI-006 (Informational):** Rotor speed mismatch in mainstream HTC boundary condition (14,200 vs. 14,850 RPM) — sensitivity study to be completed by J. Park within 2 weeks.

---

## Slide 12 — Summary of Confidence Assessment

- **Numerical solution quality:** Medium-high confidence
  - GCI < 2.1% on key QoIs; cross-code agreement within 0.6%; convergence criteria met
  - Reduced slightly by medium (not fine) mesh being used for production runs
- **Physical model fidelity:** Medium confidence
  - SST performs adequately at low-to-moderate rotation numbers; known overprediction on leading wall at Ro > 0.20
  - Film effectiveness assumption is the largest unresolved physical uncertainty
- **Experimental grounding:** Medium confidence
  - In-house rig data provides useful validation but Biot number mismatch limits direct applicability to coupled response
  - Re_Dh mismatch in rig comparison (Slide 8) reduces confidence until resolved
- **Overall assessment:** The simulation is suitable for design guidance at Phase 2B with the following caveats:
  1. Peak metal temperature uncertainty is ±34 K (RSS); design margins must accommodate this
  2. Leading-edge temperatures should be treated as potentially underpredicted by up to ~15% in Nu
  3. Three open items (OI-001, OI-002, OI-003) must be closed before results are used for formal life prediction

---

## Slide 13 — Executive Summary (NOTE: UNDER REVISION — SEE OI-003)

- APEX-7 HPT blade cooling channel CHT simulation completed using ANSYS Fluent 2023R2
- **Fine mesh used for all reported results** ← *[THIS STATEMENT IS UNDER REVIEW — medium mesh (11.7 M cells) was used; see Slide 4 and OI-003]*
- Peak metal temperature: 1,204 K (medium mesh); GCI-corrected estimate 1,209 K
- Pressure drop within 3% of rig measurement ✓
- Nusselt number comparison: within ±10% at Ro ≤ 0.18; exceeds criterion at Ro = 0.25 (leading wall +14.8%)
- Combined temperature uncertainty: ±34 K (OAT RSS; formal UQ deferred to Phase 3)
- **Recommendation:** Proceed to CDR with documented limitations; close OI-001 through OI-003 prior to using results for life prediction sign-off
- **Distribution:** Program Chief Engineer, Thermal Analysis Group, Aero/Thermal IPT, CDR Review Board

---

## Slide 14 — References and Supporting Documents

- Schüler, M. et al. (2011). "Experimental investigation of heat transfer in a two-pass rotating channel." *ASME J. Turbomach.* 133(2).
- Han, J.C. & Park, J.S. (1988). "Developing heat transfer in rectangular channels with rib turbulators." *Int. J. Heat Mass Transfer* 31(1).
- Iacovides, H. & Launder, B.E. (1995). "Computational fluid dynamics applied to internal gas-turbine blade cooling." *Int. J. Heat Fluid Flow* 16(6).
- NASA/CR-2019-220215: *Rotating Channel Heat Transfer with Trip Strips*, NASA Glenn Research Center.
- MMPDS-12: *Metallic Materials Properties Development and Standardization Handbook*.
- APEX-4B-2023-09: Facility 4B Test Report, APEX Cooling Rig, Phase 2B.
- CAL-2023-047: IR Thermography Calibration Report, Facility 4B.
- TAG-M-2023-112: Thermal Analysis Group Internal Memo — Re mismatch acknowledgment.
- ANSYS Fluent 2023R2 Theory Guide, Chapter 4 (Conjugate Heat Transfer).
- OpenFOAM v2206 chtMultiRegionFoam: User Guide and Validation Cases.
