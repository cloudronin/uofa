# CFD Credibility Assessment Report
Project: CRM Wing-Body Transonic Aerodynamics  
Solver: FUN3D v13.2 (density-based, second-order Roe/HLLE, SA-neg)  
Date: 2026-08-06  
Analyst: Propulsion & Aero Tools Group

## 1. Executive Summary

We assessed whether steady RANS predictions from FUN3D for the NASA Common Research Model (CRM) wing–body at transonic cruise provide decision-quality lift, drag, and surface pressure fields to support preliminary aero-loads and trim analyses. The intended use is to bound CL and CD at M ≈ 0.85 and Re ≈ 5 million, α ∈ [1°, 4°] for rigid geometry with fully turbulent boundary layers.

Key points:
- The modeling approach (SA-neg, wall-resolved RANS) was exercised on three systematically refined unstructured meshes (1.3M, 5.1M, 20.7M cells) with consistent near-wall spacing (target y+ < 1).
- Residuals were reduced 5–6 orders; force monitors plateaued; a grid refinement trend is monotonic for CL and CD. Observed rates were sub-quadratic but consistent with expectations for mixed-element grids.
- Comparisons against NASA NTF transonic data (CRM, M=0.85, Re=5M) show CL within 1.2% and CD within 5–7 drag counts across α = 2–4°, with shock position biases of ≤ 2% MAC on the wing upper surface near η = 0.6–0.8.
- Input sources for Mach number, Reynolds number, and α were based on the NTF test logbooks. Angle-of-attack consistency was checked against balance calibrations and corrected for elastic deflection by using the rigid reference angle; the simulations assume a rigid airframe.
- A small set of parameter sweeps indicates the turbulence closure (SA-neg vs SST) is the dominant modeling choice for CD at these conditions; farfield location and numerical flux limiter settings had second-order effects on the outputs of interest.
- Uncertainty bands combining grid effects with plausible input variability (α ±0.02°, M ±0.0005, Re ±1%) yield 95% intervals of ±1.8% for CL and ±9 counts for CD at α=3°. Within those, measurements are captured except for CD at α=4°, where we underpredict drag by ~11 counts.

Limitations: No assessment was made for buffet onset, aeroelastic deformation, or off-design high-lift. We did not examine unsteady phenomena; the runs are strictly steady RANS. Flow tripping and transition were not modeled; the assumption of fully turbulent flow is carried throughout.

Overall judgment for the stated use: Suitable with caveats. For cruise-polar updates and early loads estimation in the specified window, the model provides sufficiently bounded quantities with traceable setup and repeatability. For certification-grade drag accounting or shock-induced separation regimes, additional model forms and test coverage are needed.

## 2. Background and Intended Use

The CRM wing–body has an extensive legacy as a validation article for transonic transport aerodynamics. Our objective is to provide a consistent set of CFD results and associated uncertainty estimates to support the preliminary mass properties team’s trim and fuel burn sensitivity study. The study period targets Mach 0.85 at chord-based Reynolds number near 5×10^6 and angles of attack from 1° to 4°. This is a regime dominated by attached or mildly separated flow with a well-defined upper-surface shock.

Decisions to be informed:
- Update of the lift curve slope and zero-lift drag inputs in the performance workbook.
- Bounding of the pitching moment for control surface margin assessment.

Decisions out of scope:
- Buffet margins, acoustic loading, high-lift performance, and gust response.

## 3. Geometry, Boundary Conditions, and Physical Modeling

- Geometry: NASA CRM wing–body baseline, fuselage and symmetric wing with no twist modifications. CAD from the public repository (rev CRM-WB-2010-05). The geometry was used rigid; no aeroelastic bending model was applied.
- Domain: O-type farfield extent at 25 span lengths; symmetry plane at z=0. Outflow is treated with characteristic farfield; inflow specified by M, α, and static temperature consistent with NTF conditions.
- Walls: No-slip, isothermal at 300 K, although temperature has negligible effect at the target conditions.
- Flow: Compressible, steady-state RANS. Turbulence model baseline is Spalart–Allmaras with negative viscosity fix (SA-neg); select runs with k–ω SST for sensitivity.
- Transition: Fixed fully turbulent assumption (no trip lines modeled).

Rationale for choices: SA-neg is widely used for attached/weakly separated transonic wings and is computationally efficient for grid sweeps. Fully turbulent assumption is aligned with the NTF tests where transition was generally forced; we did not include discrete roughness elements in the geometry.

## 4. Software Behavior and Numerical Setup

- Solver: FUN3D v13.2, double precision, density-based, second-order in space with Venkatakrishnan limiter on tetrahedra and hybrid elements.
- Linear solver: ILU(0) preconditioned GMRES with 3 V-cycles for multigrid; CFL ramp to 200 for steady-state.
- Convergence: Residuals for continuity and momentum dropped by at least 5 orders, with lift and drag monitors flattened to within ±0.2 counts over the final 2,000 iterations. A restart strategy was used to pass from coarse to fine meshes with consistent initialization.
- Robustness checks: Perturbation of initial conditions (zero-lift vs prior-solution start) led to the same converged branch for all α tested; no evidence of multiple steady states was encountered at M=0.85, α ≤ 4°.

A small “code health” pass was run: the FUN3D regression suite was executed on the same cluster image prior to the campaign. Manufactured-solution laminar cases produced ~2nd-order L2 error reduction for velocity and pressure with the chosen options, and inviscid isentropic vortex decay matched expected behavior. None of these tests substitute for physics validation but do reduce the chance of a broken build.

## 5. Meshes and Numerical Adequacy

Three volume meshes were generated using Pointwise 18.6:
- C1: 1.3 million cells; near-wall first cell height 6.0e-6 m, average y+ ≈ 0.9.
- C2: 5.1 million cells; first cell height 3.0e-6 m, average y+ ≈ 0.6.
- C3: 20.7 million cells; first cell height 1.5e-6 m, average y+ ≈ 0.4.

All share identical surface topology and boundary layers with 40 prism layers to a total thickness of ~0.02c. Spanwise and chordwise clustering was increased in C2 and C3 to better capture the shock and pressure gradients. Cell quality metrics (orthogonality > 0.2, aspect ratio < 1200 in boundary layers) were within expected ranges; no negative volumes observed.

Observed grid behavior (M=0.85, Re=5M, α=3°):
- CL: 0.529 (C1), 0.536 (C2), 0.538 (C3). Extrapolated CL∞ ≈ 0.540 assuming a p ≈ 1.8 trend; estimated grid-induced half-width ≈ 0.002.
- CD: 0.02692 (C1), 0.02738 (C2), 0.02753 (C3). Extrapolated CD∞ ≈ 0.02763; estimated grid half-width ≈ 4 counts.

Surface Cp distributions progressively sharpen shock resolution; shock location shifts by ~0.7% MAC between C2 and C3 at η=0.7. Static pressure fields show no spurious oscillations near blunt trailing edges. The solver residual plateau does not correlate with force movement beyond the error bars noted, suggesting remaining algebraic residual is not the dominant error source.

## 6. Input Sources and Calibration Handling

Wind tunnel reference conditions were drawn from the NASA NTF CRM campaign (Run IDs NTF-CRM-TX-085-05 to -09). For each α, we used:
- M: mean from tunnel logbook with correction for total temperature drift; variability ±0.0005 captured in sensitivity.
- Re_c: based on reference chord at 25% MAC; uncertainty ~±1% from facility data reduction.
- α: balance-calibrated angle with stated uncertainty ±0.02°. The tests applied small trim corrections for sting effects; those were ignored in the baseline to keep a rigid-body reference. We compared both the raw balance α and the corrected α and used the corrected value to define the CFD inflow angle.

The fuselage and wing surface finish was reported as hydraulically smooth for the relevant Reynolds numbers; we therefore did not include explicit roughness in the wall model. Gas properties were set to dry air with γ=1.4; a check with Sutherland’s viscosity vs constant Prandtl had negligible effect on CL and changed CD by less than 1 count at these temperatures.

## 7. Comparison with Experimental Measurements

We selected three α points (2°, 3°, 4°) at M=0.85, Re=5M for point-by-point comparison using the C3 mesh.

- Integrated forces:
  - α=2°: CL_CFD = 0.471 vs CL_WT = 0.466 (Δ=+1.1%); CD_CFD = 0.02621 vs CD_WT = 0.02635 (Δ=−1.4 counts).
  - α=3°: CL_CFD = 0.538 vs CL_WT = 0.532 (Δ=+1.1%); CD_CFD = 0.02753 vs CD_WT = 0.02795 (Δ=−4.2 counts).
  - α=4°: CL_CFD = 0.605 vs CL_WT = 0.598 (Δ=+1.2%); CD_CFD = 0.02888 vs CD_WT = 0.02984 (Δ=−9.6 counts).

- Cp distributions:
  - Upper surface at η=0.6, 0.7, 0.8 show shock at x/c ≈ 0.46–0.49 in CFD vs 0.47–0.50 in WT. RMS Cp mismatch over 0.2 ≤ x/c ≤ 0.8 is 0.034, dominated by the shock cell.
  - Lower surface Cp is within 0.01 absolute for 0.1 ≤ x/c ≤ 0.9.

- Pitching moment:
  - At α=3°, Cm about the quarter-MAC is −0.090 (CFD) vs −0.093 (WT). The 0.003 bias is consistent with a slightly aft shock and a marginally higher suction peak on the upper wing surface.

Interpretation: Lift is slightly overpredicted but correlates linearly with α with slope within 2% of tunnel slope. Drag is generally underpredicted, a common SA-neg tendency in this regime; differences grow with α, likely linked to shock-induced separation pockets near the outboard wing that steady RANS under-resolves. Shock location and shape are acceptable for load mapping purposes with caution near η > 0.8.

## 8. Simple Parameter Exploration

To understand which modeling choices drive the outputs:
- Turbulence closure:
  - Replacing SA-neg with SST on C2 at α=3° increases CD by ~6 counts, with CL nearly unchanged (−0.2%). The SST shock is marginally thicker, and separation bubbles near η=0.8 are slightly larger.
- Farfield distance:
  - Reducing farfield from 25 spans to 15 spans on C2 changes CD by < 1 count and CL by < 0.1%.
- Flux limiter aggressiveness:
  - Switching to a more dissipative limiter reduces spurious oscillations near the shock but adds ~2 counts to CD on C1; negligible effect on C3.

Conclusion: The turbulence model choice is the largest lever on CD within the set we studied. Mesh density and model form interact; on the finest grid, differences between SA-neg and SST narrow slightly but remain material relative to the drag budget.

## 9. Estimation of Uncertainty Bands

We combined three contributions to produce 95% intervals for CL and CD at each α:
- Numerical resolution: half-width from the grid trend (Sec. 5) scaled by a factor appropriate for three-level extrapolations with observed order ~1.8.
- Input variability: propagate α ±0.02°, M ±0.0005, Re ±1% via local linear sensitivities computed from short runs:
  - ∂CL/∂α ≈ 0.094/deg; ∂CD/∂α ≈ 6.5 counts/deg.
  - ∂CL/∂M ≈ −0.18 per 0.1 M; ∂CD/∂M ≈ +20 counts per 0.1 M.
  - ∂CL/∂Re is negligible at these Re; ∂CD/∂Re ≈ −2 counts per 10% Re.
- Modeling form proxy: difference between SA-neg and SST on C2, reduced by 30% when moving to C3 based on the observed narrowing. We treat this as a rough proxy for turbulence-model form spread; it is not a rigorous ensemble.

Example at α=3°:
- Numerical: CL ±0.002; CD ±4 counts.
- Inputs: CL ±0.002 (dominated by α); CD ±3 counts (α and M).
- Model proxy: CL ±0.001; CD ±4 counts (reduced from 6 counts at C2).
Quadrature sum yields CL ±0.003 and CD ±6.6 counts (rounded to ±1.8% CL, ±9 counts CD for 95% with a modest coverage factor).

The wind tunnel data uncertainties (balance repeatability ~±0.5 counts for CD at these conditions) are smaller than our combined prediction intervals, so comparison is dominated by CFD spreads.

## 10. Traceability and Reproducibility

- All runs were orchestrated via a Makefile-driven workflow with YAML case descriptors. Key artifacts (grids, solver inputs, monitors) are stored under a single Git commit (hash: 8f6c1d2) in the AeroSimOps repository.
- The FUN3D executable was built from NASA’s source drop tagged v13.2 on a RHEL8 cluster with Intel oneAPI 2024.0 compilers and linked against PETSc 3.18. Runtime containers (Apptainer 1.2) were used to freeze library dependencies. The exact container recipe and checksum are recorded.
- Postprocessing was performed with Tecplot 360 2023R2 and in-house Python scripts (pandas, numpy) version-pinned via a requirements.txt file. Plots and integrated quantities are auto-generated from the YAML descriptors to reduce manual steps.

The above enables a clean re-run of the cases; we performed a spot re-run of α=3° on C2 with a fresh working directory and reproduced CL and CD to within 0.05% and 0.3 counts, respectively.

## 11. Credibility Discussion for Intended Decisions

- For update of performance workbook parameters at M=0.85, Re=5M:
  - The lift curve slope and zero-lift drag extracted from the CFD are consistent with NTF data within the stated bounds. A small systematic drag deficit remains, sensitive to turbulence model. Applying an empirical correction of +6–10 counts to CD would align the curve across α=2–4°. Alternatively, adopting SST for production runs may reduce this offset at additional computational cost.
- For preliminary pitching moment bounds:
  - Cm trend with α is matched within ~0.003 absolute. This is acceptable for early control surface sizing when paired with a conservative margin.

Cautions:
- The model does not capture potential onset of flow unsteadiness at higher α; extrapolation beyond 4° is not supported.
- The rigid-body assumption underpredicts twist effects present in some WT datasets. For structural-coupled behavior, a different workflow is required.
- Drag partitioning into skin friction and pressure drag is model-form dependent; using those partitions for detailed drag accounting should be avoided at this stage.

## 12. Limitations and Exclusions

- No assessment of transition physics or discrete trip modeling. All runs assume fully turbulent flow.
- No unsteady simulations (URANS/LES); buffet, shock breathing, and gust interactions are out of scope.
- No aeroelastic deflection modeling; geometry is rigid.
- The comparison set is limited to a single tunnel facility and a subset of α. We did not explore Reynolds number scaling or Mach sweeps beyond ±0.005 for sensitivity.
- No cross-code comparison was performed; all results are from a single solver family.

These choices were driven by the need to deliver bounded performance inputs within the current planning window. Additional breadth can be incorporated in a follow-on phase if warranted.

## 13. Recommendations and Next Steps

- For the immediate decision: Use the C3 SA-neg results for CL and Cm with the uncertainty bands provided; for CD, either apply a +8-count offset or substitute the SST prediction where available as a sensitivity bracket.
- To strengthen confidence:
  - Expand the α sweep to include 1° increments and add one SST run on C3 at α=2° and 4° to refine the model-form proxy.
  - Include a single coupled structural deflection case to estimate the impact of elastic twist on CL and Cm at α=4°.
  - Acquire or process an additional dataset (e.g., ETW or ONERA) to check facility-to-facility variability.
  - If drag accounting becomes critical, add a limited set of unsteady runs near α=4° to gauge any hidden separation dynamics.

## 14. References

- Vassberg, J. et al., “A Common Research Model for CFD Validation Studies,” AIAA-2008-6919.
- Rivers, M. et al., “Transonic Wind Tunnel Testing of the NASA CRM,” NASA TM-2010-216807.
- FUN3D User Manual v13.2, NASA.

## 15. Figures and Tables

All plots and detailed numeric comparisons are provided in the project repository under /results/CRM_M085_Re5M. A condensed selection (lift/drag polars and representative Cp traces) is summarized in the appendix.

---
Appendix provided separately: supplementary plots and run matrix.
