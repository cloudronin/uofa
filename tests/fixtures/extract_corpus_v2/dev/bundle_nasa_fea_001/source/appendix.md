Appendix A: Load Cases and Boundary Conditions
- LC-1: Vertical compression at 1.0× design, 110 K. Axial load applied via footpad RBE3; clevis mounting plate constrained with six DOF at bolt hole pattern.
- LC-2: Side load at 1.0×, 110 K. Lateral force vector applied at footpad center; reaction balanced at clevis.
- LC-3: Combined resultant at 1.0× (15° off-axis), 110 K. Vector magnitude matches ENV-LND-001 table 3-2.
- LC-4: Vertical compression at 1.2×, 110 K.
- LC-5: Side load at 1.2×, 110 K.
- LC-6: Combined resultant at 1.2×.
- LC-7: Worst-case combined with torsional bias, 110 K. Used for mesh study and UQ.
- LC-8: Warm case (293 K) combined 1.0× to check temperature sensitivity.

Pretension application
- PRETS179 elements on 12 M10 bolts; initial pretension set to 22 kN each (scatter ±2 kN) before external loading. Pretension defined at first substep; locked thereafter.

Appendix B: Mesh Refinement Details
Global mesh levels (DOFs, peak von Mises at clevis root for LC-7):
- L1: 1.1M DOFs, 594 MPa
- L2: 1.6M DOFs, 582 MPa
- L3: 2.1M DOFs, 571 MPa
- L4: 2.9M DOFs, 568 MPa
Richardson extrapolation using L2–L4 indicates an asymptotic value near 559–563 MPa, consistent with observed trend. Estimated discretization error at L3 ≈ 1.8%.

Local submodel
- Extracted boundary at 10 mm offset from hotspot; mapped hex mesh 1.0–1.5 mm elements. Submodel peak: 589 MPa at 110 K, indicating local stress amplification captured by refined mesh relative to tet-only model. Volume above 0.95× yield <0.3% at 1.2× loads.

Contact sensitivity
- Normal stiffness scaled ±50% from default; change in peak stress ≤1.9%. Friction coefficient varied 0.07–0.15; peak stress varied within ±5.4%. No non-physical slip observed at μ ≥ 0.10; at μ = 0.07, minor slip bands appear at 1.2× loads, matching conservative expectations.

Appendix C: Test Correlation Data (Summaries)
- Strain gauges: 22 channels; average model-to-test strain ratio 0.96 at 1.0× loads (compression), 1.05 (tension). Outlier G14 improved after test μ adjustment.
- DIC: In-plane displacement maps show near-identical bending curvature; pixel-tracking error estimated 30–50 με equivalent.
- Modal: MAC matrix diagonal entries: [0.96, 0.94, 0.93, 0.95] for first four correlated modes.

Appendix D: Uncertainty Inputs for UQ
- E (Ti-6Al-4V at 110 K): Normal, mean 122 GPa, σ = 2 GPa.
- Yield: Normal, mean 1,020 MPa, σ = 30 MPa (used for allowable derivation, not propagated as failure criterion uses fixed allowable).
- Clevis thickness at hotspot: Uniform, ±0.15 mm about nominal (based on CMM).
- μ (friction): Triangular, min 0.07, mode 0.12, max 0.15.
- Pretension per bolt: Normal, mean 22 kN, σ = 2 kN (truncated at ±3σ).
- Liner stiffness: Uniform, ±10%.
- Temperature: Uniform, 110 ± 10 K.
Sampling: 200-run Latin Hypercube with fixed random seed (435672). Convergence of mean and 95th percentile checked via running estimates; stabilization occurred by ~160 runs.

Appendix E: Cross-Solver Check
- MSC Nastran SOL 600 setup mirrored the Ansys contact strategy (penalty with μ = 0.12). Material cards consistent within rounding. Results aligned within 2% for displacements and 1.6% for peak stress in LC-1.

Appendix F: Governance
- Review checklist (closed): run reproducibility, mesh sensitivity adequacy, contact robustness, test data calibration review, uncertainty propagation adequacy, and risk linkage verification (R-STRUT-007 friction).
- All items signed off by peer reviewer on 2026-07-30; TA concurrence on 2026-08-01.

End of Appendix
