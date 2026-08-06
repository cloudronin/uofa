# Appendix A — Supplementary Material

A.1 Mesh details
- Coarse mesh: 11.2 million cells (fluid: 6.9M, solid: 4.3M). Minimum prism layer thickness: 8 μm; target y+ ~1.2 at nominal.
- Medium mesh: 18.7 million cells (fluid: 11.5M, solid: 7.2M). Minimum prism layer thickness: 6 μm; achieved y+ ~0.9.
- Fine mesh: 31.4 million cells (fluid: 19.8M, solid: 11.6M). Minimum prism layer thickness: 4 μm; achieved y+ ~0.8.

Notes:
- Prism layers maintained coverage >98% of wetted area without collapse. Local quality minima (skewness <0.85) only occurred at two sharp plenum turns; no solver divergence observed.
- CPU time per 1,000 iterations: coarse 1.4 hr, medium 2.7 hr, fine 4.9 hr on the reference node.

A.2 Convergence records
- Residual histories exhibit two slope changes: initial transients (0–500 iters), coupling stabilization (500–1,200 iters), asymptotic decay (1,200+ iters).
- Energy imbalance decreased from 1.2% at 500 iterations to 0.08% at 2,000 iterations for the nominal case on the medium mesh.

A.3 Bench test instrumentation
- Thermocouples adhered with high-temperature epoxy; bead encapsulation thickness ~0.2 mm. Emissivity set to 0.92 for IR comparison, based on a black-painted witness coupon.
- DAQ sampling at 2 Hz; steady-state defined as dT/dt < 0.05 C over 5 min window.
- Pressure transducers calibrated week-of-test against a DPI 620 calibrator; linearity within 0.25% FS.

A.4 Property sources
- EGW 50/50 mixture: density and specific heat from ASHRAE Fundamentals 2021, k from Sutherland-based fit; verification point at 20 C matched REFPROP within 1.2% for viscosity and 0.9% for k.
- 6061-T6 aluminum thermal conductivity: vendor cert states 167±5 W/m-K at 25 C; temperature slope −0.24 W/m-K per C applied across 10–80 C.
- TIM conductance measurement summary:
  - At 40 C, 0.3 MPa: Hc = 15,100 W/m²-K (σ ≈ 6.5%)
  - At 60 C, 0.3 MPa: Hc = 14,500 W/m²-K
  - At 80 C, 0.3 MPa: Hc = 13,900 W/m²-K
  Linear interpolation used for 65 C. Mounting procedure in analysis mirrors test stack (same torque pattern and washers).

A.5 Local sensitivity snapshots
- Increasing mass flow from 0.12 to 0.16 kg/s decreased T_max by 8.9 C and increased ΔP by 6.2 kPa.
- Raising inlet temperature from 20 C to 25 C shifted the entire temperature field up by ~4.9 C; relative hot spot location unchanged.
- Increasing Hc by 20% reduced T_max by 0.34 C; effect localized to die edges.

A.6 Alternative turbulence model check
- Realizable k-ε with enhanced wall treatment on the medium mesh at nominal conditions:
  - T_max = 79.3 C (Δ +0.6 C vs SST)
  - ΔP = 19.7 kPa (Δ +1.0 kPa vs SST)
  Given the small thermal difference and slightly higher ΔP, SST was retained.

A.7 Reproducibility evidence
- STAR-CCM+ solver prints file hash summary:
  - geometry.x_t SHA-256: 8f1a918e3…
  - material_props.csv SHA-256: 071c2c9df…
  - powers.yaml SHA-256: 0a0b6a8d2…
- Re-run on a second node (EPYC 7543) produced T_max within 0.07 C and ΔP within 0.3 kPa, attributed to minor parallel reduction ordering differences.

A.8 Known gaps and planned actions
- Extend bench matrix to include 600 W total power and 10 C / 35 C inlet temperatures. Timing: next thermal bench slot, mid Q4.
- Measure as-built channel roughness on the prototype using profilometry to tighten ΔP predictions.
- Acquire clamp force vs torque curve for the final fastener stack to refine TIM pressure representation.

A.9 File manifest (selected)
- cp_cht_v1_6.sim (STAR-CCM+ model)
- bc_envelope.xlsx (boundary settings per case)
- properties_egw50.json (fluid properties functions)
- tim_hc.csv (measured conductance data)
- run_macros/launch_batch.java (solver macro)
- post/summarize_fields.py (post-processing)
