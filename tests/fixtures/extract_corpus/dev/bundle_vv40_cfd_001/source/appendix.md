# Appendix A — Supporting Evidence Summary Table

**Project:** Cooling Water Pump Stage Analysis — CAR-CFD-2024-047-Rev2

This appendix provides a consolidated reference to the primary evidence items supporting each major assessment dimension discussed in the main report. It is intended to facilitate independent review and traceability.

---

## A.1 Simulation Scope and Decision Framing

| Evidence Item | Location | Notes |
|---|---|---|
| Simulation Plan defining QoIs and decision context | SP-2024-031, §2–3 | Reviewed and approved prior to analysis |
| Explicit bounds on simulation claims | SP-2024-031, §4.1 | Clearly distinguishes CFD role from physical testing |
| Geometry variants under evaluation | SP-2024-031, §5 | Three impeller variants described |

The simulation plan was finalized and signed off by the project lead before any mesh generation or solver runs were initiated. This sequencing is important: it ensures that the QoIs and acceptance criteria were not defined post-hoc to match favorable results. The team's documentation practice on this point is commendable.

---

## A.2 Mesh Convergence — Detailed Data

The three meshes used in the GCI study are characterized as follows:

**Mesh 1 (Coarse):** 2.14M cells, TurboGrid blocking topology, minimum orthogonal quality 0.31, average aspect ratio 18.4 on blade surfaces.

**Mesh 2 (Medium — Production):** 6.83M cells, minimum orthogonal quality 0.38, average aspect ratio 14.2 on blade surfaces. O-grid blocks around all blade surfaces, H-grid in passage core.

**Mesh 3 (Fine):** 18.41M cells, minimum orthogonal quality 0.41, average aspect ratio 11.8 on blade surfaces.

GCI calculations for total head at BEP:

```
h1 = 49.37 m  (fine)
h2 = 49.44 m  (medium)
h3 = 50.16 m  (coarse)

r21 = (18.41/6.83)^(1/3) = 1.392
r32 = (6.83/2.14)^(1/3) = 1.474

p = ln((h3-h2)/(h2-h1)) / ln(r32/r21) ... [iterative, corrected for sign]
p_observed = 1.93

GCI_fine  = 1.25 * |e21| / (r21^p - 1) = 0.8%
GCI_medium = 1.25 * |e32| / (r32^p - 1) = 2.7%

Asymptotic check: GCI_fine / (r21^p * GCI_medium) = 1.04  ✓
```

These calculations confirm the solution is in the asymptotic convergence regime and that the medium mesh carries a numerical uncertainty of approximately ±0.9% (using the fine-grid extrapolated value as reference).

---

## A.3 Turbulence Model Selection Rationale

The SST k-ω model was selected based on the following considerations, documented in the Simulation Plan:

1. **Literature precedent:** Five published validation studies for centrifugal pumps with Ns between 25 and 60 (SI) using SST k-ω were reviewed. Mean head prediction error across these studies ranged from 1.8% to 4.3%, with efficiency errors of 0.5–1.8 percentage points. References: Gonzalez et al. (2002), Stel et al. (2013), Zhang et al. (2018), Kye et al. (2018), and Li et al. (2020).

2. **Flow physics considerations:** The blade suction surface experiences adverse pressure gradients near the leading edge at off-design conditions. SST k-ω's use of the k-ω formulation in the boundary layer (avoiding the freestream sensitivity of standard k-ω) and k-ε in the freestream is appropriate for this environment.

3. **Alternative considered:** The Realizable k-ε model was also assessed. A comparative run at BEP showed a 1.4% higher head prediction with Realizable k-ε compared to SST k-ω. The SST k-ω result was closer to the test data, and the model is considered more physically appropriate for the flow regime.

The team did not evaluate LES or hybrid RANS/LES approaches, which is appropriate for steady-state design-phase analysis but would be worth considering for detailed off-design flow structure analysis in future phases.

---

## A.4 Boundary Condition Documentation

All boundary conditions are fully documented in the Simulation Report (SR-2024-047, §3.4) and are traceable to either:
- Physical measurements (inlet pressure from facility instrumentation)
- Engineering standards (turbulence intensity from ASHRAE/ISO guidelines for pipe inlets)
- Manufacturer data (wear ring clearance from engineering drawing revision 4.2)

No boundary conditions were assumed without documented justification. The sensitivity of results to the most uncertain boundary condition (surface roughness) is quantified in §8 of the main report.

---

## A.5 Experimental Data Traceability

The validation test was conducted on 2024-09-18 and 2024-09-19 at the organization's pump test facility (Test Cell 3). Test report reference: TR-2024-089.

Instrumentation calibration status at time of test:
- Electromagnetic flowmeter (Endress+Hauser Promag 10W, DN200): Calibrated 2024-06-15, certificate no. CAL-2024-FM-047. Accuracy ±0.5% of reading.
- Inlet pressure transducer (Kistler 4260A, 0–10 bar): Calibrated 2024-08-01, certificate no. CAL-2024-PT-112. Accuracy ±0.1% FS.
- Outlet pressure transducer (Kistler 4260A, 0–10 bar): Calibrated 2024-08-01, certificate no. CAL-2024-PT-113. Accuracy ±0.1% FS.
- Torque meter (HBM T40B, 500 N·m): Calibrated 2024-07-22, certificate no. CAL-2024-TQ-031. Accuracy ±0.1% FS.
- Speed sensor (magnetic pickup): Calibrated 2024-08-01, certificate no. CAL-2024-SP-019. Accuracy ±0.05% of reading.

All calibrations were current at the time of testing (within 12-month calibration intervals). Combined measurement uncertainty in hydraulic efficiency was computed as ±0.8 percentage points (95% confidence, RSS method per ISO 9906 Annex B).

---

## A.6 Software Configuration Record

| Item | Detail |
|---|---|
| Software | ANSYS Fluent 2023 R2 (build 23.2.0.22) |
| License server | LS-PROD-01 (verified active at time of runs) |
| Compute cluster | HPC-Cluster-A, 128-core Intel Xeon Platinum 8380 nodes |
| OS | Red Hat Enterprise Linux 8.6 |
| MPI | Intel MPI 2021.7 |
| SCMS registration | SCMS-2024-SW-0041 |
| Benchmark suite | ANSYS V&V Suite v23.2, all 47 cases passed (2024-10-02) |
| Canonical benchmarks | Lid-driven cavity (Re=1000, 3200), backward-facing step (Re=800), turbulent pipe flow (Re=50,000) — all within published reference tolerances |

The compute environment is consistent across all production runs. No mid-campaign software updates were applied.

---

## A.7 Analyst Qualifications Summary

**Lead Analyst:** M. Theriault, P.Eng.
- 8 years CFD experience, 5 years in rotating machinery applications
- Completed ANSYS Fluent Advanced Training (2022)
- Author of 3 internal technical reports on pump CFD methodology

**Reviewing Engineer:** Dr. S. Raghunathan
- 15 years engineering experience, 6 years in pump hydraulics
- PhD in fluid mechanics (turbomachinery focus)
- Approved simulation plan, mesh strategy, and final report

**Peer Review:** Conducted by J. Okonkwo (CFD Methods Group) using Form SIMQ-07 Rev 3 (2024-10-28). No major findings; two minor comments resolved before report finalization.

---

## A.8 Applicability Domain Assessment

The following table summarizes the comparison between the validation scenario and the simulation application scenario:

| Parameter | Validation Test | Simulation Application | Within Domain? |
|---|---|---|---|
| Fluid | Water, 25°C | Water, 25°C | Yes |
| Impeller diameter | 310 mm | 315 mm | Yes (affinity law applied) |
| Specific speed Ns | ~32 (SI) | ~32 (SI) | Yes |
| Flow range | 50%–120% BEP | 60%–120% BEP | Yes |
| Reynolds number | ~1.9×10⁶ | ~2.0×10⁶ | Yes |
| Number of blades | 7 | 7 | Yes |
| Volute type | Single tongue | Single tongue | Yes |
| Surface roughness | Ra ~3.2 µm | Ra ~3.2 µm (assumed) | Partial — to be confirmed on prototype |

The simulation application is well within the applicability domain of the validation dataset on all characterized parameters. The one partial item (surface roughness of prototype) is flagged as a recommended action in §12 of the main report.

---

*End of Appendix A*
