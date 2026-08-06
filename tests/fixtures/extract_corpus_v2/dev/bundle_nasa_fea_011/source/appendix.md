# Appendix A — Supporting Details

A.1 Mesh Quality Metrics
- Element aspect ratios: 95th percentile 3.2, max 4.8 near bolt holes; Jacobians > 0.65 throughout.
- Hotspot region F3 uses curvature-based refinement with a minimum edge length 0.28 mm on M4; five elements through fillet thickness.
- Contact surface discretization: target edge 0.5 mm within 5 mm of bolt lines; 1.0 mm elsewhere.

A.2 Mesh Convergence Data at F3
- M1: Peak 301 MPa
- M2: Peak 307 MPa
- M3: Peak 312 MPa
- M4: Peak 314 MPa
- Extrapolated asymptote: 316 MPa
- Estimated numerical uncertainty on M4 result: ±2.1% (95%)

A.3 Joint Stiffness and CTE Justification
- A benchtop compression test of the deck–bracket joint stack (without fastener torque) yielded a joint stiffness of 1.8 GN/m; the model uses 1.9 GN/m based on the contact algorithm plus clamping. A perturbation of −50% to +100% in spring representation changed F3 stress by ±2.5%.
- For CTE mismatch, a separate coupon assembly with Al–Ti interface under uniform +55 °C did not exhibit slip at 9 kN preload; measured micro-slip displacements < 1 µm. Thermal gradient effects were not tested and are out of the accepted envelope.

A.4 Validation Test Setup Notes
- Static test: Load application via a custom fixture transferring load to the bracket flange to reproduce the same moment arm as in the vehicle. Alignment verified with laser tracker (±0.2 mm).
- DIC: Vic-3D, calibration residual 0.018 pixels; strain gauge backup on opposite surface showed consistency within 4%.
- Modal test: 16 accelerometers mounted with wax; mass loading estimated at 1.4 g total, entered into FEA as lumped masses for correlation iteration.

A.5 Sensitivity Study Results (Selected)
- Fillet radius F3: −0.1 mm change → +6.5% peak stress; +0.1 mm → −5.8%.
- Friction coefficient: 0.18 → +1.3% stress; 0.24 → −1.6%.
- Bolt preload: 8 kN → +1.1% stress; 10 kN → −0.9%.
- Interface stiffness: 0.5× → +2.5%; 2× → −1.9%.
- Tetra element order: switching to linear tets increased peak stress error to 7.9% vs test and produced pronounced mesh dependency; quadratic tets retained.

A.6 Reproducibility Checklist
- To reproduce LC1 M4:
  - Checkout repo tag v1.4.
  - Run script preprocess.py with flags: --mesh-level M4 --contact-tol 1e-6.
  - Launch ANSYS with run_lc1.mac.
  - Post-process with extract_peak.py; expected peak stress within 2 MPa of archived result on same solver build.

A.7 Personnel Credentials
- Certificates and training logs for analyst and checker are stored under docs/training in the repository. Resumes include relevant FEA and uncertainty quantification coursework.

A.8 Independent Rerun Log
- Independent rerun performed 2026-07-18 on Windows 11, ANSYS 2023R2 build 21.4.0.27. Peak stress 316 MPa due to minor differences in BLAS; frequency predictions within 0.3% of Linux runs. Log attached: rerun_log_Adebayo.txt.

A.9 Risk-informed Targets Justification
- The 12% stress accuracy threshold ties to the minimum factor-of-safety budget of 1.25: with a worst-case 95% bound added to stress, residual margin remains at least 0.20. This reflects the program’s tolerance for conservatism given the non-fracture-critical nature of the bracket.

A.10 Open Items and Planned Work
- Schedule for environmental chamber test to measure joint behavior at +55 °C: October 2026.
- Additional torque–tension characterization with five more samples: November 2026.
- Evaluate multi-linear plasticity for off-nominal analyses before CDR.
