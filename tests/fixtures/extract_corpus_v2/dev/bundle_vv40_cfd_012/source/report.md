CFD Credibility Report: Elbow Duct with Turning Vanes (VV40 Assessment Excerpt)

Background and Purpose
This document summarizes the engineering basis for using a steady RANS simulation to estimate pressure loss and internal flow quality for a 90-degree square HVAC elbow fitted with three turning vanes. The intent is to support early sizing choices for a retrofit project (building AHU-7). Decisions to be informed include fan static pressure allowance at 1.8–2.2 m3/s and expected maldistribution into downstream branches. The analysis focuses on pressure loss coefficient (K) between upstream and downstream taps and mid-plane velocity profiles. We present the setup, checks performed for numerical robustness, comparison to bench-scale measurements, and limitations. The aim is to provide just enough confidence for schematic and equipment selection; finer-grained design, acoustics, and fouling are out of scope.

Physical Configuration
- Duct nominal: 0.300 m × 0.300 m square, elbow centerline radius 0.300 m (R/Dh ≈ 1.2).
- Three aluminum turning vanes, chord length 70 mm, 2 mm thickness, canted at 45° relative to bisector. Gap between vanes ≈ 60 mm.
- Upstream straight run: 8 hydraulic diameters. Downstream straight run: 6 hydraulic diameters.
- Wall material: galvanized steel; measured average roughness Ra = 20 µm; vane edges are sharp.
- Operating air: 20 °C, 1 atm; density 1.204 kg/m3; dynamic viscosity 1.82e-5 Pa·s.
- Flow rates analyzed: 1.2, 1.8, 2.4 m3/s (Re_Dh ≈ 0.8e5, 1.2e5, 1.6e5).

Computational Approach

Geometry preparation
- Native geometry created from survey data (Leica Disto X4 and calipers). Vane placement accuracy ±1.5 mm; corner radii matched to as-built S-bend corners.
- CAD cleaned in SpaceClaim 2023 R2. Small bolt holes and flange beads suppressed to reduce nonessential curvature. The modeled wall roughness is represented via equivalent sandgrain height, not explicit texture.

Mesh generation
- Unstructured poly-hexcore mesh in Fluent Meshing. Near-wall prism layers: 18 layers, first cell height set for y+ ≈ 1.0 at 2.4 m3/s, growth 1.2, total BL thickness 7 mm.
- Cell counts:
  - Coarse: 2.6 million total, 7.5e5 prism cells on walls and vanes.
  - Medium: 5.3 million total, 1.5e6 prism cells.
  - Fine: 10.7 million total, 3.0e6 prism cells.
- Minimum orthogonal quality > 0.12; max skewness < 0.85; smoothness acceptable across vane leading edges after local remeshing.

Governing models and numerics
- Solver: Ansys Fluent 2023 R2, pressure-based steady solver.
- Turbulence closure: k-omega SST with low-Re wall treatment (integrated to the wall, no wall functions).
- Turbulent Schmidt number 0.85 for k and omega default; production limiter on.
- Convective schemes: second-order upwind for momentum and turbulence scalars; pressure interpolation second order.
- Pressure-velocity coupling via coupled scheme; pseudo-transient acceleration enabled initially to aid stabilization (pseudo time step ~1e-4 s decreasing).
- Under-relaxation factors left at Fluent defaults after initial 500 iterations; no relaxation tightening observed necessary.
- Grid interfaces: conformal throughout (no non-matching interfaces).
- Convergence targets: scaled residuals below 1e-5 for continuity and momentum, 1e-4 for turbulence; and steady monitors of section-averaged static pressure at taps varying less than 0.2% over 500 iterations.

Boundary and initial conditions
- Inlet: velocity inlet specified by flow rate; inlet turbulence intensity 5% (baseline), turbulent length scale 0.07 Dh; sensitivity explored 2% and 10%.
- Outlet: static pressure outlet set to 0 gauge; average static at outlet surface matched to measurement plane position.
- Walls and vanes: no-slip, isothermal at 20 °C; surface roughness modeled via ks = 0.1 mm (from Ra via k_s ≈ 4 Ra) with C_s = 0.5.
- Initialization: hybrid initialization followed by patching of a swirling profile informed by a precursor straight-duct run to shorten spin-up.

Monitors and stability
- Monitored area-weighted average pressure at the two tap planes (8 Dh upstream and 6 Dh downstream), plus mass imbalance across inlet/outlet.
- Mass residuals balanced to within 0.05% at convergence for all meshes and flow rates.
- No divergence or non-physical negative k/omega observed after initial 200 iterations; production limiter prevented overshoot near vane edges.

Evidence of Numerical Adequacy

Mesh refinement study
- Three systematically refined meshes (nominal refinement ratio r ≈ 1.25 in characteristic cell size across the elbow and vane wakes; near-wall first layer unchanged to preserve y+ ≈ 1).
- Quantity examined: loss coefficient K = ΔP / (0.5 ρ U_bulk^2) between center of upstream tap section and downstream tap section.
- Observed trends at 1.8 m3/s:
  - K_coarse = 0.37
  - K_medium = 0.355
  - K_fine = 0.349
- Using an apparent order based on the three-point estimator (neglecting BL-layer constraint), p_obs ≈ 1.92 for K. Extrapolated K_ext ≈ 0.345; estimated discretization band on fine grid ≈ 1.2% relative.
- For velocity profile metrics, L2 norm of difference between consecutive meshes dropped by ~35% per refinement, consistent with near-second-order behavior in the bulk; peak gradients at vane tips converge slower.

Steady-state behavior
- Residuals: continuity and momentum below 1e-5; turbulence quantities to 5e-5 on fine grid by 3500 iterations.
- Solution monitors: K variation <0.15% over the final 700 iterations on the fine mesh.
- Patch independence: starting from uniform vs precursor-patched initial fields resulted in the same K within 0.3% on medium mesh, indicating minimal dependence on initial condition.

Near-wall resolution check
- Achieved y+ range on walls and vane surfaces: 0.6–1.8 at 2.4 m3/s; most of the elbow outer radius kept below 1.2. Thus, the low-Re formulation operated within the intended viscous sublayer regime.
- Wall shear stress patterns smooth with expected separation bubble on inner corner at the highest flow case diminishing with vanes; no unphysical skin-friction spikes.

Parameter Sensitivity (Targeted)
- Inlet turbulence level: at 1.8 m3/s on the medium mesh, K changed by +0.9% (2% TI) and −1.5% (10% TI) relative to baseline 5% TI. Downstream profile fullness responded modestly; secondary flow strength altered by ~3% in peak lateral velocity.
- Surface roughness: doubling ks to 0.2 mm increased K by 2.1%; halving to 0.05 mm decreased K by 1.3%. Given measurement of Ra and conversion uncertainty, we include ±1.5% as roughness-induced spread.
- Outlet static pressure location: moving the outlet pressure boundary 2 Dh further downstream changed K by −0.4%, within run-to-run noise. Current placement is deemed sufficient to decouple reflections.

Laboratory Benchmark

Test facility
- Duct module built to match geometry above at 1:1 scale in the HVAC lab; flow delivered by a variable-speed centrifugal blower through a 12 Dh conditioning section with honeycomb and two screens.
- Two static pressure rings installed at the tap planes; each ring has eight equispaced ports; the averages used to mitigate swirl bias.
- Velocity measurements at three cross sections (upstream plane, elbow mid-plane, downstream plane) using 2D PIV (double-pulsed Nd:YAG, 200 mJ/pulse) with 0.5 mm resolution light sheet; seeding via DEHS aerosol.
- Environment stabilized at 20 ± 1 °C.

Instrumentation and uncertainty
- Pressure: Setra Model 264 differential transducers (±0.25% FS); calibration traceable; combined standard uncertainty on ΔP over test range ≈ 0.6% of reading after ring averaging.
- PIV: in-plane velocity uncertainty 2.5% (due to timing, particle image density, and cross-correlation windowing). Out-of-plane motion considered small in the straight sections but non-negligible in the elbow; 3D effects noted qualitatively.
- Flow rate determined from nozzle array (ASME MFC-3M) upstream of the conditioning section; combined uncertainty 1.1%.

Matching simulation to test
- For each flow rate case, air properties and bulk velocity were matched to within 0.5% of the test conditions. The downstream tap plane in the model was positioned to coincide with the ring centerline.
- Probing strategy: CFD velocity data sampled on planes corresponding to PIV sheets, downsampled to PIV interrogation grid spacing, and time-averaged CFD field compared to PIV mean. No attempt to replicate PIV filtering was made beyond spatial averaging.

Results

Pressure loss coefficient
- Measured K at 1.8 m3/s: 0.358 ± 0.007 (95% CI combining instrument and repeatability).
- CFD fine grid K at 1.8 m3/s: 0.349 ± 0.004 (mesh-derived band).
- Difference: −2.6% relative to measurement mean, within the combined envelope when considering roughness sensitivity. Over the three flow rates:
  - 1.2 m3/s: CFD 0.365 vs test 0.372 (−1.9%).
  - 1.8 m3/s: CFD 0.349 vs test 0.358 (−2.6%).
  - 2.4 m3/s: CFD 0.341 vs test 0.351 (−2.8%).
- Trend with flow rate captured; mild underprediction likely tied to roughness modeling and unresolved vane-edge losses.

Velocity fields
- Upstream section: CFD reproduces near-uniform profile with ~3% boundary layer growth; PIV confirms minor corner deficits.
- Elbow mid-plane: Secondary motion predicted with two counter-rotating vortices; peak lateral velocities in CFD are 0.19 U_bulk vs 0.21 U_bulk in PIV; vortex cores slightly closer to the inner wall in CFD by ~8 mm.
- Downstream section: Profile flattening relative to a bare elbow evident with vanes. Centerline velocity ratio CFD 1.07 vs PIV 1.05. Corner recirculation zones weaker in CFD, consistent with underprediction trend in K.
- Spatial correlation coefficient between CFD and PIV velocity magnitude on the downstream plane: 0.94 (CFD fields bilinearly sampled onto the PIV grid).

Qualitative flow features
- Separation largely suppressed by vanes except a small bubble at the inner lip for 2.4 m3/s. The SST model predicts reattachment ~0.4 Dh downstream; smoke visualization suggests slightly earlier reattachment, consistent with higher loss in test.

Credibility Discussion

Appropriateness of physics
- The flows considered are subsonic, incompressible, with moderate curvature and vane-induced turning. The chosen two-equation closure with low-Re treatment is consistent with the engineering purpose: estimate mean losses and first-order distribution effects.
- Near-wall resolution (y+ ≈ 1) matches the modeling assumption; use of an equivalent sandgrain roughness links measured Ra to wall function parameters. This is a simplification but captures first-order roughness drag.

Numerical solution quality
- Residual norms and stability behavior are consistent with a well-converged steady solution across all meshes and operating points. Section-averaged static pressures stabilized within 0.2%, and mass continuity closed to 0.05%, which supports steady-state viability.
- The three-mesh study with an observed near-second-order rate provides a defensible bound on numerical error in K (~1–1.5% on the fine grid). Velocity field convergence is slower in shear layers at the vane tips, yet differences between medium and fine were small relative to measurement uncertainty.

Input data and boundaries
- Inlet turbulence intensity is not measured in the lab upstream of the elbow module; the 5% baseline is reasonable for post-screen flows but introduces uncertainty. The small sensitivity of K to TI (≤1.5%) makes this manageable for the present use-case. A more significant impact is seen on secondary flows, but still within 3% of U_bulk in peak lateral velocity.
- Roughness conversion (Ra to k_s) and the lack of explicit vane edge radiusing contribute to the persistent CFD underprediction of K. The targeted roughness sensitivity band brackets most of the observed offset with data.
- Outlet placement study indicates low sensitivity, minimizing concern over numerical reflections.

Comparison to data
- The agreement in K across the operating envelope is within approximately 3% with consistent negative bias. Downstream velocity shape and secondary motion topology align well with PIV, giving confidence that momentum redistribution is captured.
- The CFD-to-PIV comparison accounts for spatial resolution by sampling CFD on the PIV grid; temporal filtering differences remain (CFD is steady), which may partly explain the slightly stronger vortices in PIV.

Reproducibility notes
- All simulations executed with Ansys Fluent 2023 R2 on a 24-core Xeon Gold workstation; RAM usage peaked near 42 GB for the fine mesh. Wall-clock per run: coarse 2.1 h, medium 5.0 h, fine 11.6 h to convergence criteria above.
- Key setup parameters, mesh statistics, and boundary condition values are listed herein to enable reproduction. Case and data files are archived on the project share under AHU7_ElbowCFD/2024Q4.

Use for decision-making
- For early sizing at the system level, the provided K values with a conservative +4% margin cover modeling and numerical gaps observed. The spatial distribution insights are sufficiently faithful to anticipate branch maldistribution to first order.
- The analysis is not intended for acoustic prediction, fine-scale loss allocation per vane, or evaluation under highly turbulent inflow (e.g., immediately downstream of fans).

Limitations and Deferred Work
- The study is steady and Reynolds-averaged. Vortex shedding and unsteady separation dynamics, if present at the highest flow rate, are not resolved. A follow-on WMLES could refine loss allocation and vortex structure predictions if needed.
- Thermal coupling is neglected; density variation with temperature is insignificant here but was not modeled.
- Inlet turbulence characteristics were not measured in the lab; installing a hot-wire grid upstream would allow tighter matching and potentially reduce the residual bias.
- Vane leading and trailing edge micro-geometry (burrs, small radii) was not explicitly included. A detailed CAD capture or an empirically tuned edge loss model could address the remaining ~2–3% underprediction.
- The roughness specification is uniform; localized roughness patches or dust accumulation are not represented.
- Only one turbulence closure was evaluated in depth. While SST typically performs well in adverse pressure gradient flows, no alternate closures were explored in this phase to constrain model-form uncertainty beyond qualitative reasoning.
- Extrapolation to elbows with significantly different curvature or vane spacing was not investigated.

Conclusions
- The CFD approach, as configured, reproduces measured pressure loss within approximately 3% across the intended flow range, with a consistent low bias. Mesh checks and residual behavior support that numerical errors are small compared to the bias.
- Velocity field comparisons confirm correct topology and near-quantitative magnitudes for secondary flows. The SSE of differences in downstream velocity magnitude is consistent with expected steady-versus-time-averaged discrepancies.
- For preliminary design choices (fan sizing, allowance margin), the results are sufficiently mature. A 4% conservative uplift on the predicted K is recommended to cover bias and input uncertainties.
- If higher fidelity for internal loss budgeting is required, recommended next steps are: measure inflow turbulence; add vane-edge detail; test a roughness sweep; and consider an unsteady RANS or WMLES at the top flow rate.

Document Control and Contacts
- Lead analyst: J. Li (CFD), MEP Systems Group.
- Test lead: S. Ortiz (HVAC Lab).
- Software: Ansys Fluent 2023 R2; SpaceClaim 2023 R2.
- Run dates: 2024-11-12 to 2024-12-03.
- Project folder: AHU7_ElbowCFD/2024Q4 (internal).

Appendix: Key Numbers (abridged)
- Mesh y+: 0.6–1.8 (fine).
- Residual targets: 1e-5 (cont/mom), 1e-4 (k, ω).
- Mass imbalance: <0.05%.
- K (fine) at 1.8 m3/s: 0.349; estimated numerical band: ±0.004.
- Test K at 1.8 m3/s: 0.358; 95% CI: ±0.007.
- Sensitivity: TI 2–10% → ΔK within ±1.5%; ks ×2 → +2.1% K.
- Compute resources: 24 cores; fine mesh 11.6 h to converge.

Notes on Scope
- The present report emphasizes flow setup, numerical checks (residual behavior, mesh study), and data comparison. Broader process topics (software quality process, independent audits, or formal requirements mapping) are outside the scope of this phase and not covered here.
