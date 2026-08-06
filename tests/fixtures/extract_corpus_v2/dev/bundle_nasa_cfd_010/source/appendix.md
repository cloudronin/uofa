Appendix A: Additional details on boundary conditions and monitors

- Inflow specification
  - Total pressure: set to achieve M = 0.45 at the lip under isothermal 300 K air. Iteratively adjusted during initialization, then held constant.
  - Total temperature: 300 K, consistent with the reference dataset; effects of ±10 K variation were negligible on the non-dimensional metrics.
  - Turbulence: 1% intensity with turbulent viscosity ratio 10 at the inlet plane; length scale 10 mm informed by duct hydraulic diameter.

- Outflow specification
  - Static pressure: tuned to match the target mass flow within ±0.05% after convergence; small pressure ramps used to avoid shocklets when starting from rest.

- Wall boundary condition
  - No-slip; adiabatic. Roughness height set to zero in baseline runs.

- Convergence monitors
  - Mass-averaged total-pressure recovery at AIP; averaged over last 1,000 iterations for reporting.
  - Mean swirl angle at AIP, computed from planar velocity components in a local polar frame.
  - Four wall-tap Cp locations in each bend to detect late-stage drift.

Appendix B: Notes on postprocessing

- The AIP plane was located one diameter upstream of the nominal fan face; averaging excluded a 3 mm bleed ring near the wall to avoid numerical contamination from the wall damping region.
- Swirl angle was computed as atan(Vtheta/Vaxial) in degrees; outliers beyond ±30 deg were clipped before computing RMS, consistent with probe saturation limits in the reference dataset.
- Recovery was defined as the mass-weighted average of P0/P0,inlet over the plane, using density-weighted velocities for mass flux.

Appendix C: Sensitivity run deltas (qualitative)

- The turbulence intensity sweep moved the secondary vortices slightly closer to the outer wall in the second bend at 5% intensity, which accounts for the +0.4 deg mean swirl shift.
- Wall roughness primarily influenced the wall-shear distribution in the first bend; the core flow topology at the AIP remained qualitatively unchanged over 0–40 µm.
- The SA model produced a thicker separated region on the inner wall of the first bend, elongating the low-pressure plateau by ~5% of the bend length; this aligns with the lower recovery and mean swirl predictions relative to SST.
