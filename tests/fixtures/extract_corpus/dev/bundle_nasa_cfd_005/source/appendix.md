# Appendix A — Supporting Details and Traceability

## A.1 Software Configuration Record

| Item | Details |
|---|---|
| Solver | ANSYS Fluent 2023 R1 (build 2023.01.0045) |
| Mesh generator | ANSYS TurboGrid 2023 R1 |
| Post-processor | ANSYS CFD-Post 2023 R1 + in-house Python scripts (v2.4.1) |
| Operating system | RHEL 8.7, 64-bit |
| HPC cluster | Internal cluster "Hydra-3", 256 cores (Intel Xeon Gold 6338), InfiniBand HDR |

All software was used under current license agreements. Fluent version 2023 R1 is on the company's approved solver list (see Software Qualification Register SQR-2024-01). The in-house Python post-processing scripts are version-controlled in the corporate GitLab repository (project: cfd-postproc, tag v2.4.1) and were last validated against analytical test cases in January 2024 (validation record VR-PYPOST-2024-01).

Note: Formal regression test documentation from ANSYS for this specific Fluent build has been requested and is pending (reference OA-4400-11). Until receipt, reliance is placed on the company's internal solver benchmarking history (reports INT-TURB-2019-01 through INT-TURB-2023-04), which covers 23 turbomachinery test cases and demonstrates consistent solution accuracy within stated tolerances across Fluent versions 19.2 through 2023 R1.

---

## A.2 Operating Condition Coverage

The table below documents which operating points were simulated and which have corresponding experimental data. Points marked "CFD only" have no experimental counterpart and are used for interpolation of the H-Q curve between validated points.

| Flow Rate (m³/h) | CFD Run | Test Data | Notes |
|---|---|---|---|
| 18 | ✓ | — | CFD only; near shut-off, elevated uncertainty |
| 20 | ✓ | ✓ | Validated |
| 27 | ✓ | ✓ | Validated |
| 36 | ✓ | ✓ | BEP — primary validation point |
| 45 | ✓ | ✓ | Validated |
| 54 | ✓ | ✓ | Validated |
| 63 | ✓ | — | CFD only |
| 68 | ✓ | ✓ | Validated |
| 72 | ✓ | — | CFD only; near runout, elevated uncertainty |

The two CFD-only end points (18 and 72 m³/h) carry elevated uncertainty and should not be used as primary design inputs without additional test data or conservative margin application.

---

## A.3 Mesh Quality Metrics — Fine Mesh

| Metric | Value | Threshold |
|---|---|---|
| Maximum skewness | 0.71 | < 0.85 |
| Minimum orthogonal quality | 0.22 | > 0.15 |
| Maximum aspect ratio | 312 | < 500 (near-wall layers) |
| Average y⁺ (impeller blade) | 3.8 | < 5 |
| Average y⁺ (diffuser vane) | 4.1 | < 5 |
| % cells y⁺ > 5 | 6.2% | < 10% |

Mesh quality is considered acceptable per internal standard IS-MESH-003. The maximum skewness of 0.71 occurs in a small cluster of cells at the impeller blade trailing edge where the geometry transitions sharply; local solution monitoring confirmed no anomalous velocity or pressure values in this region.

---

## A.4 Convergence Monitoring Plots (Summary)

Convergence was assessed using three criteria applied simultaneously:

1. **Residual criterion:** All scaled residuals (continuity, x/y/z momentum, k, ω) below 1×10⁻⁵
2. **Integrated quantity criterion:** Head and shaft torque variation less than 0.1% over the final 500 iterations
3. **Mass balance criterion:** Inlet-outlet mass imbalance less than 0.01%

All operating points met all three criteria before results were accepted. The most challenging convergence behavior was observed at 18 m³/h (near shut-off), where residuals oscillated between 8×10⁻⁶ and 3×10⁻⁵ for continuity; however, integrated head variation remained below 0.15% and the result was accepted with a notation of elevated numerical uncertainty at this condition.

---

## A.5 Validation Data Provenance

The experimental data used for validation were collected under Test Report TR-WP4400-HYD-001 (issued 2023-11-08). Key aspects of the test setup:

- Test fluid: Potable water at 19.8°C (viscosity correction applied per ISO 9906 Annex E)
- Flow measurement: Electromagnetic flowmeter, DN80, calibrated 2023-09-15, calibration traceable to national standards (PTB certificate 2023-FM-4471)
- Head measurement: Differential pressure transmitter, calibrated 2023-10-02 (Rosemount 3051, range 0–400 kPa)
- Speed measurement: Optical tachometer, ±0.5 RPM accuracy
- Data acquisition: 60-second averages at each flow point, 10 Hz sampling rate

The test was witnessed by the project quality engineer and the results were reviewed and signed off by the hydraulic design lead. Raw data files are archived in the project data management system (DMS reference: WP4400-TEST-RAW-001).

---

## A.6 Applicability of Validation to Production Configuration

The validation test was conducted on a pre-production prototype with the following known differences from the production design:

| Feature | Test Article | Production Design | Impact Assessment |
|---|---|---|---|
| Impeller material | Aluminum (machined) | Cast stainless steel | Surface finish difference; roughness correction applied |
| Shaft seal | Mechanical seal (test rig) | Lip seal (production) | Leakage path difference; volumetric efficiency correction ±0.3% |
| Diffuser | Identical to production | — | No correction needed |
| Wear rings | New (0.3 mm clearance) | New (0.3 mm clearance) | No correction needed |

The aluminum-to-stainless transition affects surface roughness. The test article was measured at Ra = 0.6 µm (blasted and polished); production castings are expected at Ra = 1.2–3.2 µm. This is the primary source of the roughness uncertainty flagged in Section 5.2 and Section 7 of the main report. A sensitivity run with equivalent sand roughness ks = 4 µm was conducted and showed a head reduction of 1.4 m at BEP, which has been incorporated into the uncertainty budget.

---

## A.7 Open Actions and Traceability

| Action ID | Description | Owner | Target Date | Status |
|---|---|---|---|---|
| OA-4400-11 | Obtain ANSYS Fluent QMS documentation | Procurement / V&V Coord | 2024-05-01 | Open |
| OA-4400-14 | Obtain as-built roughness measurements from manufacturing | Manufacturing Eng | 2024-04-15 | Open |
| OA-4400-17 | Extend validation to multi-stage configuration (Stages 2+3) | Fluid Systems | 2024-Q3 | Planned |
| OA-4400-19 | System-level uncertainty rollup integration | Thermal-Hydraulic Team | 2024-Q3 | Planned |

---

*Appendix prepared by: Lead CFD Analyst, Fluid Systems Analysis Group*
*Document reference: WP-4400-VVR-003-AppA, Rev B*
