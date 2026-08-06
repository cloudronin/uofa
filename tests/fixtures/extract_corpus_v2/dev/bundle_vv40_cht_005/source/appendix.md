Appendix A — Selected Numeric Details

A1. Mesh Variants and Key Results (identical physics and BCs)
- Coarse mesh: 6.1 million cells; 8 prism layers; minimum first-cell height 2.5e-5 m.
  - VRM2 base temperature: 82.4°C.
  - Total mass flow: 0.083 kg/s.
  - Module pressure drop: 63 Pa.
- Medium mesh: 10.2 million cells; 12 prism layers; minimum first-cell height 1.5e-5 m.
  - VRM2 base temperature: 81.1°C.
  - Total mass flow: 0.084 kg/s.
  - Module pressure drop: 62 Pa.
- Fine mesh: 15.7 million cells; 16 prism layers; minimum first-cell height 1.0e-5 m.
  - VRM2 base temperature: 80.7°C.
  - Total mass flow: 0.085 kg/s.
  - Module pressure drop: 61 Pa.

Estimated asymptotic VRM2 base temperature via three-level Richardson: 80.5°C (assumed observed order p ≈ 1.9). The medium mesh differs from the asymptote by about 0.6%. Pressure drop difference medium-to-fine is within 1.5 Pa.

A2. Radiation Sensitivity (medium grid)
- With radiation off:
  - VRM2 base temperature: 82.2°C.
  - Net convective heat through outlet: 418 W.
- With radiation on (εpaint = 0.85, εsink = 0.2):
  - VRM2 base temperature: 81.1°C.
  - Net convective heat through outlet: 403 W.
  - Net radiative exchange to panels: 24 W.
- With radiation on and εpaint reduced to 0.75:
  - VRM2 base temperature: 81.5°C.
  - Net radiative exchange: 20 W.

A3. Fan Curve Implementation
- Vendor P–Q data were fit to Δp = a0 + a1·Q + a2·Q^2 over the valid range. Coefficients for each fan differ by less than 2%. The implemented curve is clamped at zero flow and at free delivery.
- The orifice bench suggests a 3–4% reduction in pressure rise at our Reynolds number versus the catalog curve; we applied this as a uniform scale to a0 and a1 terms.

A4. Monitors and Convergence Behavior
- Monitored temperatures at VRM1 and VRM2 showed monotonic decrease during iterations, ending with slopes below 2e-5 K/iter. Integrated outlet enthalpy converged within 0.1 W over the final 500 iterations.
- The L2 norm of the energy residual fell below 1e-5 by 2400 iterations on the medium grid; momentum residuals settled at ~6e-5 and continued to decrease slowly.

A5. Thermocouple and IR Locations
- TC1–TC8: device-base attachment points (VRM1, VRM2, CPU1, CPU2, FPGA, PHY, and two DC-DC packages).
- TC9–TC12: heat sink roots near leading and trailing edges of the VRM sinks.
- IR patches: 15 spots on fin tips, center panel, and bezel interior. Matte tape dots were used to fix emissivity at 0.95 for IR readings.

A6. Energy Balance Components (medium grid, representative run)
- Electrical heat input: 450 W.
- Convective outlet enthalpy rise: 403 W.
- Radiative exchange to internal walls: 24 W.
- Conductive transfer to side rails held at 27°C: 20 W.
- Residual (numerical): 3 W.

Appendix B — CAD and Mesh Notes

B1. Geometric Simplifications
- Stiffening beads on side panels were retained as they influence panel conduction.
- Screw bosses in the top cover were simplified but kept to maintain conduction area.

B2. Surface Preparation and Meshing
- Surface gaps below 0.05 mm were closed by remesher, except at panel seams adjacent to the bezel where local curvature demanded smaller patches.
- Local volumetric controls: 0.6 mm base size in the fin passages, 0.3 mm near device bases, 1.5–2.5 mm in the free stream away from fins.

Appendix C — Test Bench Snapshot

C1. Ambient Control
- A mixing chamber and honeycomb straightener upstream of the bezel reduced inlet swirl; measured swirl angle < 5° by five-hole probe.

C2. Stabilization Time
- Time to reach steady readings after power-on was 32–37 minutes across runs; the last 10 minutes were used for averaging.

C3. Flow Metering
- The orifice plate had beta ratio 0.5; calibration certificate indicates ±1.2% of reading uncertainty. Differential pressure at operating point: 88 Pa.

These details support the statements in the main report and provide traceable numbers for repeat runs.
