Title: Credibility Assessment Report — CFD of a 90° Mixing Elbow Feeding a Grade B Cleanroom Supply Plenum

Document ID: AER-CFD-ELB-021  
Prepared by: AeroNova Simulation Group  
Date: 2026-08-06

1. Background

A 355-mm square duct with a short-radius 90° elbow transitions into a 1.8 m by 0.9 m supply plenum feeding a Grade B (ISO 5 at rest) pharmaceutical cleanroom. The objective of the analysis is twofold:
- Predict the static pressure loss across the elbow-plus-plenum assembly at nominal flow.
- Quantify velocity uniformity at the four outlet registers feeding the HEPA filter bank.

The airflow is nominally 2.2 m³/s (±5%). Design targets from the HVAC team:
- Total pressure drop across elbow and plenum ≤ 280 Pa at 2.2 m³/s and 20°C.
- Outflow uniformity index UI = (u_max − u_min) / (2·u_mean) ≤ 0.12 at the registers’ upstream plane (50 mm ahead of HEPA seats).

The CFD model supports a go/no-go decision on retaining an existing elbow geometry in a retrofit. The intention is to assess the current design under a narrow operating window (Reynolds number around 2.3×10⁵ in the elbow) and gauge whether any mixing-induced maldistribution could jeopardize HEPA loading balance.

2. Methodology

2.1 Geometry and operating conditions

- Geometry: Laser scan of the installed elbow and immediate downstream plenum was supplied by Facilities; parasitics (small penetrations, tag brackets) were removed if ≤ 5 mm. The plenum includes internal turning vanes at the first third of the volume and four rectangular discharge frames (0.35 m × 0.4 m each). Modeled length: centerline elbow radius R_c = 180 mm; duct hydraulic diameter D_h = 0.355 m.
- Working fluid: Dry air, isothermal at 20°C; density 1.204 kg/m³; viscosity 1.82×10⁻⁵ Pa·s (values from NIST REFPROP, round-tripped in unit tests by Facilities).
- Flow rates: Nominal 2.2 m³/s; off-design checks at 1.8 and 2.6 m³/s for trending only.
- Surface condition: Galvanized steel duct; equivalent sand-roughness height k_s = 15 μm used on all walls.

2.2 Modeling approach and numerics

- Physics: Steady-state, incompressible, single-phase turbulent airflow.
- Turbulence closure: k-ω SST selected after a brief screening versus realizable k-ε on the coarse mesh. SST was retained due to better capture of the separation bubble and secondary swirl in the elbow bend; details in Section 4.3.
- Discretization: Second-order upwind for convection of momentum and turbulence scalars; central differencing for viscous terms; pressure–velocity coupling via SIMPLEC.
- Near-wall resolution: Low-Reynolds formulation with explicit near-wall treatment; 20 prism layers, growth 1.2, first-layer height 0.03 mm; computed y+ between 0.8 and 1.5 over 95% of duct walls at nominal flow.
- Boundary conditions:
  - Inlet: Specified mass flow rate; assumed turbulence intensity 5% with a length scale 0.07·D_h. A top-hat profile was used as baseline, with sensitivity to a mild swirl discussed later.
  - Outlets (four register planes): Pressure outlets at 0 Pa gauge. Backflow turbulence intensity 5%.
  - Walls: No-slip; equivalent sand roughness height and C_s = 0.5.

2.3 Spatial resolution and convergence checks

A three-level mesh refinement study was performed to establish solution stability with grid density. Grids were generated with the same topology (trimmed hex in the core plus boundary layers). Cell counts:
- Coarse (G1): 0.9 million cells
- Medium (G2): 3.4 million cells
- Fine (G3): 13.7 million cells

Refinement ratio r ≈ 1.9 in characteristic cell edge length between consecutive levels, preserving prism BL parameters. Residuals for continuity, momentum, and turbulence scalars were driven below 1×10⁻⁵ on all grids, and key monitors (total pressure drop, UI per register plane) were flattened to within 0.2% over 1000 iterations before termination. Solver relaxation factors and multigrid were tuned once on G2 and kept fixed for G1 and G3.

2.4 Experimental comparison

A full-scale acrylic mock-up of the elbow and plenum (including turning vanes) was built at the Wrightfield test loop. The upstream duct length > 8·D_h to ensure a settled profile at the instrument station. Measurements:
- Flow rate via Venturi meter (ASME MFC-3M), ±0.5% of reading, recalibrated April 2026.
- Static pressure taps located 2·D_h upstream of elbow entry and 1·D_h downstream of final register plane; differential via Setra Model 239, ±0.25% FS (0–625 Pa range).
- Velocity at the register measurement plane using a Dantec 55P11 hot-wire probe, traversed on a 10×12 grid per register; data acquisition 10 kHz, 10 s per point, temperature-compensated; repeatability ±1.5% RMS.

The rig employed the same inlet and outlet boundary conditions as the model (to the extent possible): the four registers were open to the same downstream pressure plenum. No flow-conditioning honeycomb was used; however, the straight upstream length provided a developed inlet profile within ±3% of the log-law prediction when checked with the probe.

3. Results

3.1 Pressure loss

At 2.2 m³/s and 20°C:
- CFD (G3, SST): Δp_total = 262 Pa
- Test: Δp_total = 245 Pa; measurement uncertainty (expanded, k=2) ≈ ±8 Pa

Difference (CFD − Test) = +6.9%, within the design margin to 280 Pa. Across the three grids, the computed Δp_total was:
- G1: 270 Pa
- G2: 265 Pa
- G3: 262 Pa
Extrapolation suggests residual grid dependence at the few-Pascal level.

3.2 Velocity uniformity at the registers

Definition used: UI = (u_max − u_min) / (2·u_mean), per register. The metric for decision-making is the worst register (highest UI). At 2.2 m³/s:
- CFD (G3, SST): worst-register UI = 0.089
- Test: worst-register UI = 0.072; expanded uncertainty ≈ ±0.01

The distribution shows a mild skew toward the outer radius side of the elbow, consistent with expected Dean vortices. The predicted mapping of high-speed streaks matches the hot-wire traverse qualitatively; the near-wall slow zone extent is slightly larger in the simulation.

3.3 Flow structures

The elbow produces a pair of counter-rotating secondary flows that persist about half-way into the plenum volume. The first vane row partially breaks the swirl; however, a non-negligible cross-flow remains, which biases the lower-left register toward higher velocities. Q-criterion iso-surfaces (normalized) confirm a narrow separation on the inner elbow wall starting at θ ≈ 42° into the bend and reattachment around θ ≈ 80°.

4. Credibility considerations

4.1 Intended use and decision thresholds

The analysis is scoped to answer whether the retrofit geometry meets the pressure drop and register uniformity constraints at nominal flow. The comparison at 2.2 m³/s shows:
- Pressure: Prediction is under the 280 Pa ceiling with a model-to-data difference of 6.9%.
- Uniformity: Predicted worst UI (0.089) is below the 0.12 limit and within 0.017 of the measured value.

For off-nominal checks (1.8 and 2.6 m³/s), results were used trend-wise and are not relied upon for pass/fail; no further credibility argument is made for those points beyond solver consistency.

4.2 Geometric and boundary condition fidelity

- The elbow radius and plenum dimensions were imported directly from the point cloud with simplifications only on sub-5 mm features deemed hydraulically insignificant for Re ≈ 2.3×10⁵. A comparison of the as-modeled cross-sectional area versus the CAD ideal showed <1.1% discrepancy.
- The inlet flow in the rig approximates a fully developed duct profile. In the simulation, a flat (top-hat) profile was applied at the upstream boundary to eliminate dependence on the unknown entrance condition upstream of the model domain. Sensitivity to inlet profile was performed (see 4.4).
- Surface roughness was set to 15 μm based on vendor finish data for galvanized sheet; alternate runs with 5 μm and 30 μm showed minimal effect on UI and <2 Pa effect on Δp.

4.3 Turbulence closure rationale

Both k-ω SST and realizable k-ε were tried on G2. The k-ε version underpredicted the size of the inner-wall separation bubble and yielded a slightly flatter velocity profile at the registers, leading to a worst-register UI = 0.079 on G2 (SST gave 0.092 on G2). Against data, SST was closer on Δp and captured the secondary-flow topology more convincingly in line-integral convolution plots of in-plane velocity in the plenum.

Given the elbow’s curvature and adverse pressure gradient, SST was selected for final reporting. No effort was made to run transient LES or hybrid RANS–LES; the schedule and computational budget did not justify that for this decision point.

4.4 Sensitivity checks

Because inlet conditions and certain material properties have some variability, we probed the following on G2 with SST:

- Turbulence intensity at the inlet: varied from 1% to 10%; impact on worst-register UI: −0.004 to +0.006 relative to 5% baseline; impact on Δp: within ±1.2%.
- Weak solid-body swirl at inlet: ±3° equivalent (constructed via a tangential component proportional to radius); UI increased by up to +0.014 at +3° swirl co-rotating with the elbow bend; Δp essentially unchanged (<1 Pa).
- Surface roughness: 5 μm and 30 μm cases; Δp shifted by −1.7 Pa and +1.9 Pa respectively; UI unchanged within 0.002.

These indicate that gross conclusions are robust to plausible variations. The most influential unmeasured factor is inlet swirl.

4.5 Mesh refinement and iterative convergence

The three grids indicate monotonic behavior in both Δp and UI. Using the three-level data and a standard Richardson approach for monotone solutions:
- Apparent order p ≈ 2.1 for Δp, consistent with the second-order numerical scheme.
- Estimated fractional change from G3 to the asymptote for Δp is ~1.1% (≈ 3 Pa); for worst-register UI it is ~2.6% (≈ 0.0023 absolute).

Iterative residuals fell below 1×10⁻⁵ in all fields; monitor histories for Δp and per-register UI flattened within 0.2% over at least 1000 final iterations. Doubling the iteration count created negligible shifts (<0.1 Pa, <0.0005 UI).

4.6 Comparison to experimental data

The test loop readings provide an external reference for the two quantities of interest. The match is summarized:
- Pressure drop: CFD higher than test by 17 Pa (6.9%). The offset is consistent with modeling choices (e.g., top-hat inlet) and remaining grid dependence. Considering the measurement’s ±8 Pa expanded uncertainty and the grid effect (~3 Pa), the disagreement is not unexpected for steady RANS of a separated internal flow.
- Velocity uniformity: CFD worst-register UI = 0.089 vs test 0.072 ± 0.01. The model overpredicts non-uniformity by ~0.017. The measured maps show slightly stronger vane performance in diffusing the secondary flow than the model returns, which can arise from sub-grid vane-edge effects and manufacturing fillets that were smoothed in the CAD cleanup.

No direct calibration to the data was applied; the comparison is a forward prediction using as-modeled geometry and baseline turbulence settings.

4.7 Data handling and reproducibility

- Software: OpenFOAM v10 (community release); mesh generated with snappyHexMesh and prism layers with layer addition controls tuned to achieve target y+.
- Hardware: Two-node run on an internal Slurm cluster; each node 2× Intel Xeon Gold 6330, 28 cores/socket; total 112 cores for G3 run; wall clock ≈ 18 hours to convergence.
- Case management: All dictionaries, meshes, and post-processing scripts tracked under GitLab project CFD-ELB-021, tag v1.3. Solver build hash and OS environment recorded in case/metadata.txt. Random seeds not used.
- Post-processing: Sampling defined by surfaces matching the test register planes; scripts (Python) compute u_mean, u_min, u_max, and report UI values. Versioned in the same repo.

5. Limitations and scope

- The analysis is steady and uses a RANS model. Unsteady coherent structures and low-frequency breathing modes in the plenum are not captured. That said, the decision metrics (Δp and time-averaged UI) are static quantities; the omission primarily affects higher-order details not central to the go/no-go call.
- The inlet boundary condition uses a flat velocity and prescribed turbulence intensity, not a fully developed profile nor a measured swirl level. Sensitivity showed limited effect on Δp but noticeable on UI when swirl is imposed. If the installed upstream components inject swirl in operation, the reported UI should be considered optimistic.
- The turning vane edges and small fillets were simplified. In the acrylic rig, laser-cut vanes had measurable leading-edge sharpness and minor waviness that may trip boundary layers differently. These discrepancies likely contribute to the modest overprediction of UI.
- We did not pursue transient simulations or higher-fidelity turbulence closures due to time. Future work could include an IDDES case on the G2 grid as a check on model-form influence.
- The experiment used hot-wire anemometry with standard corrections and repeated traverses, but it did not include flow visualization in the plenum core. While pressure taps are well understood, the detailed distribution could be probed with PIV as a follow-up.

6. Conclusions

- At the nominal operating point, the computed pressure drop (262 Pa) falls below the 280 Pa limit with reasonable proximity to test data (6.9% high). Further mesh refinement suggests a remaining grid influence of ~3 Pa.
- The velocity uniformity at the register plane is predicted to be acceptable (UI = 0.089 worst). The model is more pessimistic than the experiment by ~0.017 absolute, which is within typical expectations for steady RANS on separated internal flows.
- Sensitivity to turbulence intensity, surface roughness, and mild swirl indicates that inlet swirl is the most influential unmeasured factor for UI. Field measurements of upstream swirl would reduce residual uncertainty in the deployment environment.
- Overall, for the stated decision context—retain or replace the elbow—the analysis supports retention, with the caveat that hardware introducing significant swirl upstream could degrade uniformity beyond predictions.

7. Recommendations

- Proceed with the retrofit using the existing elbow geometry, contingent on verifying that upstream components (e.g., fan outlet diffusers, dampers) do not impart appreciable swirl into the elbow.
- As a low-cost risk reducer, add a short perforated plate or honeycomb upstream of the elbow if space allows, to desensitize to unknown swirl.
- If program schedule allows, run a single hybrid RANS–LES check on G2 to bound the model’s tendency to overpredict non-uniformity and to provide a second point of comparison for the vane interaction.
- During commissioning, log differential pressure across the assembly and capture anemometer traverses at the register planes at 2.2 m³/s to confirm performance.

8. Detailed evidence summary

- Problem framing: Pressure budget and register uniformity at a single operating point govern accept/reject. CFD results address both metrics directly and are compared to like-for-like rig data.
- Physical representation: As-built geometry within ~1% area accuracy; realistic surface finish; simple but justified inlet/outlet definitions.
- Numerical setup: Second-order schemes; tight convergence; y+ ≈ 1; consistent prism layering; monotone mesh refinement behavior.
- Model selection: SST chosen following behavior in separated curve flow; comparative run with realizable k-ε documented.
- Mesh and iteration: Three-grid assessment, consistent apparent order, minimal iteration-induced jitter in monitors.
- Experiment anchor: Full-scale acrylic build; instrument accuracies reported; Δp and UI measured under consistent boundary conditions.
- Sensitivity: Reasonable perturbations to inlet turbulence, swirl, and roughness explored; swirl is the key driver for UI variation.
- Reproducibility: Case inputs and processing scripts versioned; solver version and runtime documented.

Appendix A provides concise mesh and monitor details, along with excerpts from convergence histories and per-register UI values on each grid.

9. Acknowledgments

Thanks to the Facilities Test Group for the rapid acrylic build and to the Controls team for sharing the flow budget and acceptance thresholds. Internal reviewers from the Ventilation Working Group provided helpful comments on the initial turbulence-model screening.

End of report.
