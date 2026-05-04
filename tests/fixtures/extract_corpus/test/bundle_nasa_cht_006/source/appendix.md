# Appendix A — Supporting Evidence Summary Table

**Document:** CHT-VV-2024-047-R2 Appendix
**Purpose:** Traceability matrix linking credibility evidence to supporting documentation

---

## A.1 Supporting Document Register

| Ref ID | Document Title | Document Number | Relevance |
|---|---|---|---|
| [1] | Model Use Agreement — CHT Cooling Channel | MUA-CHT-2024-03 | Defines intended use, decision risk, acceptable uncertainty |
| [2] | Rig Test Report — Serpentine Cooling Passage Campaign | RTR-CHT-2023-08 | Validation experimental data, inlet condition uncertainty |
| [3] | HPT Stage CFD Analysis Report | CFD-HPT-2023-112 | Source of hot-gas boundary condition |
| [4] | Material Test Report — Inconel 718 Thermal Properties | MTR-IN718-2022-04 | Material property uncertainty characterization |
| [5] | Prior V&V Report — PW1100G Cooling Analysis | PW-CHT-VV-2019-031 | Model pedigree, prior validation history |
| [6] | Software Quality Management System Procedure | SQMS-2024-001 | Software configuration control |
| [7] | Peer Check Record | PeerCheck-CHT-2024-047-02 | Input deck independent review |
| [8] | Independent Review Record | IRR-CHT-2024-047 | V&V independent review by Dr. Okonkwo |
| [9] | NASA Benchmark Report | NASA-TM-2019-220154 | Solver benchmarking reference |
| [10] | Transient Thermal Analysis Report | CHT-TRANS-2024-009 | Out-of-scope transient analysis |

---

## A.2 Uncertainty Budget Detail

The following table provides the itemized uncertainty contributions to peak metal temperature prediction at the nominal operating condition (Re = 42,000, mid-chord location).

| Uncertainty Source | Type | Magnitude (±K or %) | Contribution to T_peak (±K) |
|---|---|---|---|
| Numerical discretization (GCI) | Aleatory | 0.6% | ±0.7 |
| Coolant inlet temperature | Aleatory | ±3.5 K | ±3.5 |
| Coolant mass flow rate | Aleatory | ±0.8% | ±1.8 |
| Hot-gas heat flux (boundary) | Epistemic | ±8% local | ±12.4 |
| Thermal conductivity (IN718) | Aleatory | ±2.5% | ±2.9 |
| Turbulence model form | Epistemic | — | ±9.4 |
| Validation comparison error | Epistemic | 3.2% Nu | ±3.8 |
| **RSS Combined** | | | **±17.3** |

Note: RSS combination assumes independence of contributions. The correlation between hot-gas boundary condition uncertainty and turbulence model-form uncertainty is not fully characterized; if these are positively correlated, the combined uncertainty could be up to ±22 K. This represents a known conservatism gap that is flagged for the CDR phase analysis.

---

## A.3 Mesh Convergence Plots — Description

Three mesh convergence plots are archived in the PDM system under project tree PRJ-CHT-2024-047/VV/MeshStudy/:

- **Figure MC-1**: Nusselt number augmentation ratio vs. inverse cell count for Pass 1 trailing wall, showing monotonic convergence toward Richardson-extrapolated value.
- **Figure MC-2**: Total pressure drop vs. mesh refinement level, demonstrating <1% change between medium and fine meshes.
- **Figure MC-3**: Peak metal temperature vs. mesh refinement level, with GCI error bars shown.

All three plots confirm that the medium mesh (14.2M cells) is in the asymptotic convergence regime for the quantities of interest.

---

## A.4 Validation Comparison Plots — Description

Validation comparison figures are archived under PRJ-CHT-2024-047/VV/Validation/:

- **Figure V-1**: Nu/Nu₀ spanwise distribution, model vs. LCT experiment, Pass 1 trailing wall, Re = 42,000. Error bars represent k=2 experimental uncertainty.
- **Figure V-2**: Nu/Nu₀ spanwise distribution, model vs. LCT experiment, Pass 3 leading wall, Re = 42,000.
- **Figure V-3**: Coolant pressure drop vs. Reynolds number, model vs. experiment, all 30 test points.
- **Figure V-4**: Scatter plot of predicted vs. measured Nu/Nu₀ at all 14 spanwise stations and all 30 Reynolds number conditions, with ±10% and ±15% bands shown.

Figure V-4 shows that 89% of predictions fall within the ±10% band, with the outliers concentrated near the U-bend regions as described in Section 6.2 of the main report.

---

## A.5 Qualifications of Key Personnel

**J. Harrington, Senior Thermal Analyst**
- B.S./M.S. Mechanical Engineering, Georgia Institute of Technology
- 9 years experience in turbomachinery CHT simulation
- Prior programs: PW1100G, CFM LEAP-1B, GE90-115B cooling analyses
- ANSYS Fluent certified user (2022)

**Dr. M. Okonkwo, Principal Engineer — Thermal Sciences**
- Ph.D. Mechanical Engineering (Heat Transfer), University of Michigan
- 18 years experience in gas turbine thermal analysis and V&V
- No involvement in CHT-VV-2024-047 model development activities
- Reviewed validation comparison methodology and uncertainty budget independently

**T. Vasquez, Chief Engineer — Propulsion Systems**
- 24 years experience in propulsion system development and certification
- Approval authority for PDR-phase analysis release

---

## A.6 Notes on Scope Boundaries

The following topics were explicitly identified as out-of-scope for this credibility assessment and are addressed in separate program documents:

- **Transient thermal cycling** (engine start/shutdown): addressed in CHT-TRANS-2024-009
- **Film cooling effectiveness on the external blade surface**: addressed in separate external film cooling analysis (EXT-FC-2024-011)
- **Oxidation and creep life calculations**: these use the thermal outputs from this model as inputs but are assessed in a separate structural life analysis
- **Probabilistic risk assessment** of the thermal margin: the uncertainty quantification in this report provides inputs to the probabilistic assessment but the risk integration is performed at the program level

These scope boundaries were agreed with the chief engineer and documented in MUA-CHT-2024-03.
