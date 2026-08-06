# Appendix A — Additional Technical Details

A.1 Mesh Quality Metrics
- Minimum cell volume ratio > 0.12; maximum skewness < 0.81.
- First off-wall spacing targets matched via y+ maps; 92% of the wing area with y+ ∈ [0.5, 1.5] on the fine mesh.
- Overset connectivity: hole-cutting margins > 5 cells; fringe layers = 3; no orphan donor cells detected in final connect.

A.2 Convergence and Monitoring
- Force histories flattened after ~3,500 iterations (fine grid). The last 2,000 iterations show CL variation ±0.0006; CD ±0.3 counts.
- Residual stagnation seen at 1×10^-6 at tip vortex cells; this was mitigated by local CFL reduction (from 5.0 to 3.0) in the tip block; forces unaffected beyond 0.1 counts.

A.3 Experimental Data Handling
- Tap data interpolated onto CFD chordwise stations using cubic splines constrained to monotonicity to avoid spurious oscillations near shock.
- Shock location algorithm: maximum gradient in Cp along each surface line; compared with experiment via tap gradients thresholding as in AR-138 Appendix C.

A.4 Sensitivity/Uncertainty Method Details
- Latin Hypercube generated via pyDOE2 with maximin criterion; seed 481516.
- Surrogate screening with a quadratic response surface confirmed near-linearity in CL with α and modest Mach cross terms for CD; direct CFD used for the reported statistics, not the surrogate.
- For completeness, a small Morris screening (p=8 levels, 10 trajectories) gave the same rank ordering: α >> M > Re > TI for CL; M > α > Re > TI for CD.

A.5 Cross-Code Setups
- FUN3D used SA model with QCR option off to match OVERFLOW; inviscid flux: Van Leer; limiter minmod. Second-order reconstruction. Convergence threshold matched to OVERFLOW as closely as possible.
- FUN3D grids imported from Pointwise via CGNS; metrics recomputed to eliminate conversion artifacts. Solutions differed negligibly except at the trailing-edge suction peak where limiter choice softened Cp by ~0.01.

A.6 Software and Build Details
- OVERFLOW build flags: -O3 -xCORE-AVX2 -fp-model precise; MPI pinned by NUMA domain; reproducibility mode on for reductions.
- FUN3D build flags: -O3 -fimf-precision=high; OpenMP disabled to ensure comparable parallelism characteristics.

A.7 Personnel and Review Notes
- Independent reviewers required a direct comparison of medium-vs-fine grids for induced drag breakdown. Added wake refinement increased CD by 0.7 counts on medium grid; recommendation to use fine grid for any drag targets ≤ 10 counts.
- Peer reviewers confirmed that no turbulence model constant was altered; only facility-consistent boundary conditions were tuned.

A.8 Out-of-Envelope Test
- One exploratory case at α = 5.0° (still M = 0.84, Re = 11.72×10^6) showed stronger shock-induced separation near η = 0.95, with CL error growing to 5.2% and hysteresis on restart. As this angle lies outside the approved α band, the result serves only to emphasize the stated applicability boundary.

A.9 Records, Archival, and Reproducibility
- Each run produces a run.json capturing:
  - Git commit, solver hash, mesh ID, node type, wall clock, force histories and convergence status.
- The re-execution recipe is provided in scripts/reproduce.sh; executing on Pleiades Skylake nodes reproduced fine-grid CL within 0.0012 and CD within 0.4 counts on 2026-08-03.

A.10 Known Gaps and Next Steps
- To reduce CD uncertainty below 8% for trade studies requiring tighter margins, consider:
  - switch to k–ω SST with tip-vortex adaptation,
  - extend wake refinement to 40c with farfield at 50c,
  - optional hybrid RANS–LES at η > 0.8 for cases where tip separation is dominant.
- For future design wings with substantially different sweep or taper, acquire a small validation set (2–3 points) at η-matched stations before extending the acceptance to those configurations.

End of Appendix.
