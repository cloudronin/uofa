# Appendix A — Supporting Data and Supplementary Analysis

## A.1 Mesh Quality Metrics

The following table summarizes mesh quality statistics for the medium production mesh (5.4 M impeller + 2.7 M volute cells). Metrics were computed using ANSYS Meshing quality diagnostics.

| Region | Min Orthogonality | Max Skewness | Max Aspect Ratio | % Cells > 0.85 Orthogonality |
|---|---|---|---|---|
| Impeller passages (×6) | 0.31 | 0.61 | 18.4 | 94.2% |
| Impeller hub/shroud | 0.44 | 0.48 | 12.1 | 97.8% |
| Volute body | 0.29 | 0.67 | 22.7 | 89.6% |
| Volute tongue region | 0.24 | 0.71 | 31.2 | 83.1% |

The volute tongue region shows the lowest orthogonality and highest skewness, which is geometrically unavoidable given the sharp curvature. A local mesh refinement was applied in this region (3 additional refinement passes), and sensitivity testing confirmed that further refinement changed predicted head by less than 0.2%. The maximum skewness of 0.71 is within the Fluent recommended threshold of 0.85 for turbulent flow simulations.

---

## A.2 Boundary Condition Traceability

All boundary conditions are traceable to facility design documents. The table below maps each CFD boundary to its source.

| Boundary | Type | Value (Design Point) | Source Document |
|---|---|---|---|
| Pump inlet | Total pressure inlet | 101,325 Pa (abs) | P&ID-HYDRA7-003 Rev. B |
| Pump outlet | Mass flow outlet | 23.61 kg/s (85 m³/hr) | Process Datasheet PD-007 |
| Impeller walls | No-slip, rotating | 1,450 RPM | Motor nameplate / PD-007 |
| Volute walls | No-slip, stationary | — | Geometry |
| Fluid properties | Water, 25°C | ρ=998 kg/m³, μ=1.003e-3 Pa·s | NIST WebBook 2024-02-10 |

Turbulence inlet conditions were set to 5% intensity and hydraulic diameter length scale, consistent with the upstream pipe geometry (DN150 straight run, L/D > 20). Sensitivity to this choice was assessed in Section 4.3 of the main report.

---

## A.3 Operating Point Sweep Results

Predicted and measured performance across the 11 simulated operating points:

| Flow (% design) | CFD Head (m) | Exp. Head (m) | Error (%) | CFD Efficiency (%) | Exp. Efficiency (%) | Error (pp) |
|---|---|---|---|---|---|---|
| 60% | 53.1 | 52.2 | +1.7% | 68.4 | 66.9 | +1.5 |
| 70% | 51.8 | 50.9 | +1.8% | 74.1 | 72.8 | +1.3 |
| 80% | 50.2 | 49.4 | +1.6% | 79.3 | 77.6 | +1.7 |
| 90% | 48.9 | 48.1 | +1.7% | 82.7 | 81.4 | +1.3 |
| 100% | 47.3 | 46.8 | +1.1% | 83.6 | 82.1 | +1.5 |
| 110% | 44.8 | 44.1 | +1.6% | 81.9 | 80.3 | +1.6 |
| 120% | 41.6 | 40.7 | +2.2% | 77.2 | 75.4 | +1.8 |

Note: Only seven of the eleven simulated points are shown; the remaining four (55%, 65%, 95%, 115% flow) showed errors consistent with the values above. The systematic positive bias in head prediction (+1.1% to +2.2%) is consistent with the known tendency of steady RANS to slightly overpredict pressure rise due to underestimation of turbulent mixing losses in the volute. This bias is within the documented uncertainty budget.

---

## A.4 Five-Hole Probe Traverse Comparison — Section C-C

The five-hole probe traverse was conducted at 100% design flow. The traverse covered 85% of the volute exit cross-sectional area (the remaining 15% near the wall was inaccessible to the probe). CFD data were extracted at the same spatial locations as the probe measurement points.

**Velocity magnitude comparison (normalized by bulk velocity U_bulk = 3.14 m/s):**

- Core flow region (r/R < 0.7): RMS error = 3.1%, max error = 6.8%
- Outer annular region (0.7 < r/R < 0.9): RMS error = 5.9%, max error = 9.4%
- Tongue wake region: RMS error = 10.8%, max error = 14.2% (3 probe points)

The elevated errors in the tongue wake are attributed to unsteady shedding that the steady simulation cannot represent. These points were excluded from the RMS calculation reported in the main report (Section 5.2), where the 4.8% figure applies to the non-wake measurement points. The main report's statement of "RMS velocity error of 4.8% of local bulk velocity" should be understood as applying to the core and outer annular regions only; the tongue wake region shows substantially higher local discrepancy. This distinction is important for any future use cases involving volute tongue flow field fidelity.

---

## A.5 Peer Review Disposition Log (Summary)

The independent peer review by Dr. L. Okonkwo identified seven comments. All were formally dispositioned prior to report finalization:

| Comment # | Topic | Disposition |
|---|---|---|
| PR-01 | Volute tongue mesh skewness exceeds 0.70 in 12 cells | Accepted; sensitivity test added (Appendix A.1) |
| PR-02 | Turbulence model sensitivity should include RSM | Partially accepted; RSM run at design point only showed +1.9% head vs SST k-ω; full sweep deferred |
| PR-03 | Inlet turbulence length scale not documented | Accepted; Appendix A.2 updated |
| PR-04 | Experimental data source independence concern | Accepted; flagged as residual risk in Section 9 |
| PR-05 | GCI safety factor should be 3.0 for coarse grids | Rejected with rationale; Celik 2008 Fs=1.25 appropriate for observed order p > 1.9 |
| PR-06 | Off-design (50%, 130%) experimental points not simulated | Noted; outside agreed project scope |
| PR-07 | Version control tag not cited in main report | Accepted; Section 7.3 updated |

---

## A.6 Turbulence Model Benchmark Summary

To support the selection of SST k-ω as the production turbulence model, the following benchmark comparisons were performed prior to the project simulation campaign:

**Backward-facing step (Driver & Seegmiller, Re = 37,500):**
- SST k-ω: Reattachment length error = +4.2% vs. experiment
- Realizable k-ε: Reattachment length error = +11.8% vs. experiment
- Standard k-ω: Reattachment length error = −6.1% vs. experiment

**2D diffuser (Buice-Eaton geometry, adverse pressure gradient):**
- SST k-ω: Pressure recovery coefficient error = 3.7% RMS
- Realizable k-ε: Pressure recovery coefficient error = 8.1% RMS

These benchmarks, while not identical to the pump geometry, demonstrate that SST k-ω provides superior performance in flows with adverse pressure gradients and boundary layer separation — conditions present on the impeller suction surface at off-design flow rates. The benchmark results justify the turbulence model selection and are consistent with published guidance for turbomachinery applications (Smirnov & Menter, 2009; Casey & Wintergerste, 2000).

---

*Appendix prepared by: Fluid Systems Analysis Group*
*Document control: DC-HYDRA7-CFD-0042-APP-A*
