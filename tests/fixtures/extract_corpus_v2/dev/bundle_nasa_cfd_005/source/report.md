# CFD Credibility Assessment Report
Project: Transonic Wing-Body Aerodynamics (NASA CRM)  
Solver: FUN3D 13.9 (double precision)  
Date: 2026-08-06

## 1. Background

This document records the basis for trusting the aerodynamic predictions produced for the NASA Common Research Model (CRM) wing-body configuration in the transonic regime. The simulations were executed to inform early trade studies on cruise drag and lift-to-drag ratio for a notional transport at conditions relevant to the NASA TDT test campaigns. The primary outputs of interest are lift, drag, and pitching moment trends with angle of attack near cruise. Because this is a pre-PDR check, the scope emphasizes core physics and numerical behavior, with a narrower focus on comparisons to a single well-characterized test point.

The questions we set out to answer:
- Is the physics model and numerical setup appropriate for attached/transonic-wing flow near buffet onset but below shock-induced separation?
- Are the numerical errors (grid, iterative, and boundary truncation) quantified to a level consistent with decision needs?
- How well do the predictions reproduce established wind-tunnel trends for the same geometry and conditions?

We do not address aeroelastic deflection, propulsion-airframe interactions, or high-lift devices. Transition is treated with a fully turbulent assumption unless otherwise stated.

## 2. Geometry and Operating Points

- Configuration: CRM wing-body, no tail, half-model with symmetry at fuselage centerplane.
- Reference geometry: NASA CRM v2.0 IGES (Wing Body I), trimmed for half-model. Leading-edge and trailing-edge tolerances checked against the public CAD; no fairings or mounting stings modeled.
- Reference chord c_ref = 7.008 ft; S_ref = 594.72 ft².
- Primary condition: M∞ = 0.85; Re = 5.0e6 per foot; T∞ = 298 K; p∞ = 101.3 kPa; α = 2.0 deg.
- Supplemental sweep: α in [-1.0, 3.0] deg at M∞ = 0.85.

No active flow control or roughness elements are included. Walls are adiabatic.

## 3. Numerical Approach

- Equations: Steady Reynolds-averaged Navier–Stokes, compressible.
- Turbulence closure: Spalart–Allmaras with rotation/curvature correction (SA-RC), negative formulation enabled.
- Discretization: Second-order finite volume; Roe-Turkel flux with Venkatakrishnan limiter; Harten entropy fix set to 0.05.
- Linear solver: GMRES with ILU(1) preconditioning; CFL ramp 5 → 200 over 2,000 iterations.
- Convergence criteria: Density residual drop ≥ 3 orders; lift/drag monitors stable to within 0.1% over 1,000 iterations; shock location steady within one cell over final 500 iterations.
- Computational resources: Pleiades (SKX), 256 MPI ranks per run; typical wall time 9–14 hours per case.

### Boundary Conditions and Domain Truncation

- Far-field: C-grid style outer boundary at 100 c_ref; characteristic-based inflow/outflow.
- Symmetry: Fuselage centerplane symmetry to exploit half-model.
- Wall: No-slip adiabatic on wing and fuselage.
- Verification of domain size: A companion run at 50 c_ref changed CD by 0.4 counts and CL by 0.06%, which we attribute to weak shock/far-field interactions. The 100 c_ref domain is used for production.

## 4. Mesh Generation and Refinement Study

Meshes are unstructured with prismatic layers near walls and tetrahedral/hexahedral hybrid core, generated using Pointwise 18.5R2.

- Near-wall: 35 prism layers, growth factor 1.18, first off-wall height set to target y+ < 1 over 95% of the wing; maximum y+ observed 1.7 near the kink at α = 3.0 deg.
- Shock-capturing: Streamwise and normal refinements aligned with expected shock locations on the upper wing; curvature-based refinement on the leading edge.
- Three-level family:
  - Coarse: 8.6M cells, 0.9M nodes.
  - Medium: 17.2M cells, 1.8M nodes.
  - Fine: 34.5M cells, 3.6M nodes.

Refinement ratio r ≈ 2^(1/3) ≈ 1.26 in characteristic cell size between levels. Interpolation errors minimized by regenerating, not agglomerating/refining from lower levels.

### Observed Mesh Behavior

At α = 2.0 deg, M∞ = 0.85:
- CL: 0.536 (coarse), 0.542 (medium), 0.545 (fine).
- CD: 0.02891 (coarse), 0.02867 (medium), 0.02857 (fine); differences of 2.4 counts (coarse→medium) and 1.0 count (medium→fine).
- CM_pitch about 0.25 MAC: -0.0893 (coarse), -0.0901 (medium), -0.0904 (fine).

Using Richardson extrapolation with observed order p ≈ 1.95 for drag and p ≈ 2.08 for lift, the estimated infinite-grid drag at this point is 0.02852 with a Grid Convergence Index (95% coverage) of 0.00008 (~0.8 counts). Lift GCI is 0.0033 (0.6%).

Separate tests with increased near-wall resolution (first cell height halved; y+ ~ 0.5) altered CD by 0.6 counts and CL by 0.1%, indicating that the baseline y+ target is adequate for attached/transonic conditions considered here.

## 5. Solver Self-Checks (Manufactured and Benchmark Cases)

Before production runs, we exercised the setup on two verification problems:
- 2D compressible manufactured field (smooth, with body force) at M = 0.3, Reynolds number scaled to ensure viscous and convective terms of comparable magnitude. On uniform triangular meshes, the L2 norm of the velocity error exhibited slopes of 1.98–2.01 with mesh spacing halved, consistent with nominal second-order accuracy.
- Laminar subsonic flat plate with an iso-thermal wall to confirm wall-normal spacing logic. Skin-friction coefficient c_f matched the Blasius trend within 1.7% at Rex=1e6 on the medium-resolution mesh. This check validates the near-wall layer generation and SA model in laminar limit (trip disabled).

These are not substitutes for application-level evidence; they provide confidence that discretization and boundary conditions behave as expected on problems with known solutions.

## 6. Convergence and Stability Indicators

For all production cases:
- Density, momentum, and energy residuals decreased by 3–4 orders of magnitude.
- Force histories plateaued to within ±0.1% over the final 800–1,200 iterations.
- Restarting from different initial conditions (inviscid start vs. medium-mesh restart) resulted in final CD differences ≤ 0.2 counts and CL differences ≤ 0.05% at α = 2.0 deg, indicating that the solutions are not path dependent within the tested regime.
- Shock sensors (based on pressure gradients) showed a stationary pattern on the fine mesh; any residual oscillations were confined to one or two cells along the mid-chord shock on the upper surface.

We take the final 500-iteration averages as the reported steady values; the standard deviation over that window is used as a measure of iterative noise (≪ discretization effects).

## 7. Comparison with Measurements

We compared against the publicly available CRM wing-body dataset at M∞ = 0.85, Re = 5e6 per foot, α ∈ [-1, 3] deg. No attempt was made to match mounting hardware or tunnel support corrections.

- Lift: The simulated CL-α slope is 0.096 per degree; the dataset indicates ~0.095 per degree. At α = 2.0 deg, CL (fine mesh) is 0.545 vs. the reported 0.539. The offset is 1.1%.
- Drag: The computed CD at α = 2.0 deg is 0.02857; the reported is 0.02942 after tunnel corrections. The difference is 8.5 counts, with the simulation lower. Across the sweep, the drag rise with lift^2 is captured, but the zero-lift intercept is underpredicted by 3–5 counts, consistent with known tendencies of fully turbulent RANS without roughness or support-interference modeling.
- Pitching moment: CM about 0.25 MAC trends correctly with α; at α = 2.0 deg, -0.0904 vs. -0.0890 reported; 1.6% more nose-down.

Surface pressure signatures at α = 2.0 deg show a shock on the upper wing near η ≈ 0.6 moving aft from x/c ≈ 0.44 to 0.48 as α increases 1 to 3 deg, consistent qualitatively with pressure tap data. Integrated differences in suction peak magnitude are within the range expected for SA-RC without transition modeling.

These results indicate acceptable agreement for early-stage design decisions, with a conservative recognition that drag levels are typically optimistic in RANS at these conditions.

## 8. Sensitivity to Key Modeling Choices

We probed how much the predictions move when we perturb plausible inputs:

- Incoming turbulence level: Varying free-stream turbulence intensity from 0.1% to 1.0% (via far-field eddy viscosity ratio 0.01 to 0.1) changed CD by less than 0.5 counts and CL by less than 0.2% at α = 2.0 deg.
- Transition assumption: Applying a fixed transition location at 5% chord on the wing (e^N-like proxy) increased CD by 4.2 counts and reduced CL by 0.3% relative to fully turbulent. Because the wind-tunnel model is typically tripped, using fully turbulent is reasonable for the comparison point.
- Far-field radius: Reducing outer boundary from 100 c_ref to 50 c_ref altered CD by 0.4 counts and CL by 0.06%, as noted earlier.
- Angle-of-attack perturbation: Changing α by ±0.02 deg produced linear responses with ∂CL/∂α ≈ 0.096/deg and ∂CD/∂α ≈ 1.1 counts/0.1 deg, confirming expected local sensitivity.

The most influential of these is the transition location; for this dataset we adopted fully turbulent to align with the tripped-tunnel assumption.

## 9. Input Data Lineage and Case Setup Trace

- Geometry was taken from the NASA CRM v2.0 CAD posted on the public repository on 2020-06-15. A streamlined script (Pointwise Glyph) applied a standard cleanup: heal gaps < 1e-5 c_ref, enforce wing–fuselage watertightness, and stitch trailing edge.
- Operating conditions derive from the published test matrix (M∞ = 0.85, Re = 5e6/ft). No attempt was made to adjust for facility-specific calibrations or support interference.
- All input decks (FUN3D .namelist, boundary condition maps, and mesh files), along with run cards, are archived under a single directory with date/time stamps. The solver executable was built from FUN3D 13.9 source obtained on 2025-12-04; local patch identifier fb9c3e7; compiler Intel 2021.6 with -O3 -fp-model precise.

This chain allows replaying the analyses if the same hardware and compiler are used.

## 10. Quantifying Numerical and Input Contributions to Result Spread

We combined several contributors to the overall spread at α = 2.0 deg:

- Grid resolution: GCI for drag = 0.8 counts; lift = 0.6%.
- Iterative repeatability: Force monitors over last 500 iterations yield σ_CD ≈ 0.08 counts; σ_CL ≈ 0.03%.
- Far-field truncation: 0.4 counts (drag), 0.06% (lift) from the 50 c_ref sensitivity test.
- Transition modeling choice: Difference between forced transition at 5% c and fully turbulent is 4.2 counts in drag; for the comparison to a tripped model, we adopt fully turbulent and treat the remaining effect as not applicable for the wind-tunnel point. For operational predictions without tripping, this would dominate the uncertainty budget.

For the wind-tunnel-like case (fully turbulent), combining grid, iterative, and truncation in quadrature yields an estimated 95% bound of approximately 0.9–1.1 counts in drag and ~0.7% in lift. This does not include model-form limitations of SA-RC in shock/boundary-layer interaction, which are better reflected by the comparison against measurements (8–9 count drag shortfall).

## 11. Credibility Discussion

- Physics representation: For a clean wing-body at transonic cruise, steady RANS with SA-RC is a standard, economical choice. The simulation captures the location and strength of the mid-chord shock and its movement with incidence. It does not resolve potential unsteadiness near buffet onset; we intentionally remain below that threshold.
- Numerical behavior: The mesh family exhibits monotonic convergence for lift and drag toward asymptotic values, with observed orders near two, as expected for second-order schemes. The domain bounds are sufficiently distant to suppress far-field coupling with shocks. Iterative histories and restart robustness support that the steady-state fixed point is reached consistently.
- Agreement with data: The lift slope and pitching moment angle-dependence align closely with the tunnel trends. Drag is under by ~8–9 counts, consistent with the absence of facility corrections and the optimistic bias of RANS. For early trades, recognizing and bracketing this gap is more important than eliminating it.
- Sensitivities: The analysis is not particularly sensitive to free-stream turbulence intensity within a plausible range. The choice of transition is impactful for drag; using fully turbulent aligns with the tripped test article and gives the most apples-to-apples comparison point.
- Reproducibility: The archived input decks, identified solver build, and recorded meshes provide a clear path to reproduce the numbers. The refinement study and manufactured-case checks demonstrate expected solver behavior and lend weight to the reported trends.

Overall, within the constraints of a steady RANS approach and the defined operating window, the evidence supports using these results for ranking design options and assessing margins at the level of a few drag counts. The reliability is bolstered by mesh convergence and single-point comparison to measurements; the main caveat is the inherent model-form bias on drag at transonic conditions.

## 12. Limitations and Deferred Work

- No aeroelastic deformation: The wing is assumed rigid. At high dynamic pressure, elastic washout can affect shock position and drag. A fluid–structure coupling could reduce the model–data differences further; this is out of scope for this phase.
- No tunnel support or surface roughness modeling: The simulation omits mounting devices and roughness, which can add several counts of drag.
- Unsteadiness not addressed: Near buffet onset, unsteady shock motion can influence average loads; here we restrict to steady conditions where RANS is appropriate.
- Single dataset used for cross-checks: Only the M∞ = 0.85, Re = 5e6 per foot series was used for direct comparison. Additional datasets (e.g., different Reynolds numbers or Mach numbers) were not exercised in this cycle.
- Propulsion effects excluded: All cases are airframe-only. Jet exhaust or inlets are not present.

These items were consciously deferred to keep the scope aligned with pre-PDR needs and available compute budget.

## 13. Conclusions

The transonic wing-body simulations on the CRM geometry, using steady RANS with SA-RC and a documented mesh family, demonstrate:
- Convergent behavior of lift and drag with mesh refinement, with a residual grid effect on drag under ~1.1 counts at 95% confidence.
- Stable numerical performance with small iterative noise and minimal sensitivity to initial conditions.
- Trends with angle of attack that are consistent with measurements; absolute drag levels are optimistic by roughly 8–9 counts compared to the wind tunnel after corrections.
- Limited sensitivity to far-field parameters and free-stream turbulence within a plausible range; stronger sensitivity to transition modeling, addressed here by adopting fully turbulent flow to mirror a tripped test article.

Taken together, these points justify using the present results for concept evaluation and margin-setting in the specified operating window. For downstream phases that require tighter absolute accuracy on drag (≤ 5 counts), we recommend expanding the comparison set, considering transition modeling matched to the tested configuration, and evaluating a higher-fidelity turbulence closure or unsteady approach where appropriate.

## 14. References

- NASA Common Research Model public geometry and wind tunnel database (accessed 2025-11-10).
- Spalart, P.R., Allmaras, S.R., “A One-Equation Turbulence Model for Aerodynamic Flows,” AIAA 1992-0439.
- Roache, P.J., “Verification and Validation in Computational Science and Engineering,” Hermosa Publishers, 1998.
- FUN3D User’s Guide 13.x Series.

---
Prepared by: CFD Methods Group  
Contact: cfd-methods@org.example
