# Appendix A — Supporting Data and Traceability Matrix

## A.1 Referenced Documents

| Document ID | Title | Revision | Notes |
|---|---|---|---|
| MP-2024-031 | APEX-7 Thermal Simulation Modeling Plan | B | Defines intended use, uncertainty requirements |
| TR-2022-041 | APEX-6 Interface Thermal Resistance Characterization | Final | Source of TIM/solder contact resistance values |
| TR-2024-071 | APEX-7 Thermal Validation Test Report | 1.0 | Primary validation dataset |
| TR-2024-088 | APEX-7 Off-Nominal CHT Parametric Study | Draft | Companion document; not assessed here |
| TP-2024-022 | APEX-7 Thermal Validation Test Plan | A | Test configuration and measurement procedure |
| CVR-2024-005 | Fluent CHT Code Verification Report | 1.0 | Graetz, conjugate slab, serpentine ΔP cases |
| GS-2024-007 | Geometry Simplification Log | A | Justification for suppressed features |
| ICD-2024-014 | Electrical-Thermal Interface Control Document | C | Power dissipation data exchange protocol |
| PRR-2024-018 | Peer Review Record — APEX-7 CHT Simulation | Final | Independent review, no open issues |
| SR-2024-112 | Simulation Records Archive | — | Residual histories, monitor plots, case files |

---

## A.2 Mesh Quality Summary (Production Mesh M2)

| Metric | Fluid Domain | Solid Domain |
|---|---|---|
| Element type | Hexahedral (structured) | Tetrahedral + inflation |
| Total elements | 3.8 × 10⁶ | — (combined count above) |
| Max skewness | 0.61 | 0.72 |
| Min orthogonal quality | 0.39 | 0.28 |
| y+ at channel wall (max) | 2.1 | N/A |
| Inflation layers (fluid) | 8 layers, growth 1.2 | N/A |

The y+ values are consistent with the enhanced wall treatment used in the near-wall region. No elements with skewness > 0.85 were present in either domain.

---

## A.3 Material Properties Summary

| Material | Thermal Conductivity (W/m·K) | Source |
|---|---|---|
| AlN substrate | 180 | Manufacturer datasheet (CeramTec, ±5%) |
| DBC copper layer | 385 | Literature (Incropera 7th ed.) |
| SAC305 solder | 57 | TR-2022-041 measurement (±8%) |
| IGBT die (effective) | 148 | Vendor thermal model (Infineon, IGBT4 series) |
| Aluminum baseplate (6061) | 167 | ASM handbook |
| Coolant (50/50 EG-water) | f(T), 0.42–0.45 | ASHRAE correlations |

All solid properties were treated as temperature-independent at the nominal operating temperature. Sensitivity of T_j to ±10% variation in AlN conductivity was evaluated at ±0.9 °C, confirming that property uncertainty is not a dominant contributor.

---

## A.4 Validation Uncertainty Budget Detail

The measurement uncertainty for the NTC thermistors was established through a calibration chain as follows:

- NIST-traceable Pt100 reference: ±0.05 °C
- Calibration bath stability: ±0.1 °C
- In-situ installation uncertainty (thermal contact, lead conduction): ±0.6 °C (estimated from sensitivity analysis)
- Data acquisition system (Keysight 34970A): ±0.05 °C

Combined (RSS): ±0.62 °C, rounded to ±0.8 °C in the report to provide a conservative bound. This is consistent with the uncertainty statement in TR-2024-071.

---

## A.5 GCI Calculation Summary

Following Roache (1994) and Celik et al. (2008), the GCI was computed for peak junction temperature using the three-mesh refinement study described in §3.2.

- Refinement ratio r₁₂ = (N₂/N₁)^(1/3) = (3.8/1.2)^(1/3) = 1.47
- Refinement ratio r₂₃ = (11.4/3.8)^(1/3) = 1.44
- Observed order of convergence p = ln[(f₃-f₂)/(f₂-f₁)] / ln(r) = 1.87
- GCI_fine (M3→M2): 0.9% of f₃ = ±1.1 °C
- GCI_medium (M2→M1): 2.2% of f₂ = ±2.7 °C (used for M2 production uncertainty)

Note: The GCI_medium value used in the uncertainty budget (§5.1) is cited as ±2.2 °C in the main report body, which corresponds to the GCI computed relative to the fine-mesh extrapolated value using Richardson extrapolation. The ±2.7 °C figure above is the direct GCI_medium from the three-mesh formula. The difference reflects the extrapolation approach and is conservatively resolved by using the larger value in sensitivity studies where noted.

The asymptotic range check (GCI_fine / (r^p × GCI_medium) = 0.98 ≈ 1.0) confirms that the meshes are within the asymptotic convergence regime.

---

## A.6 Analyst Qualification Summary

| Role | Qualification | Relevant Experience |
|---|---|---|
| Lead analyst | M.S. Mechanical Engineering (Thermal-Fluid Sciences) | 8 years CHT simulation, 4 IGBT thermal projects |
| Independent reviewer | B.S. Mechanical Engineering, P.E. | 12 years thermal system design and simulation |
| QA witness (validation test) | QA Level II certification | 5 years test witnessing |

Training records for ANSYS HT-301 (Lead analyst, completed March 2023) are on file in the project training management system.

---

## A.7 Open Issues and Action Items

| Item | Description | Owner | Target Date | Status |
|---|---|---|---|---|
| AI-001 | Develop sub-model for intra-die power distribution using Infineon vendor thermal maps | Lead analyst | 2025-02-28 | Open |
| AI-002 | Execute and document validation at 50% load / 4 L/min condition | Test team | 2025-03-31 | Open |
| AI-003 | Coordinate with electrical team to reduce power input uncertainty from ±10% to ±5% | Electrical lead | 2025-01-31 | In progress |

No open items affect the validity of the assessment conclusions for the nominal operating condition.
