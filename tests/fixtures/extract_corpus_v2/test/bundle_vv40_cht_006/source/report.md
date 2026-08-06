# Conjugate Thermal-Fluid Credibility Assessment
Project: SiC Inverter Module on Glycol-Cooled Cold Plate (CHT)
Document ID: VVR-CHT-IM-042
Date: 2026-08-06
Toolchain: Ansys Fluent 2024 R2, Ansys Meshing 2024 R2, Python 3.11 (post), Git LFS (model repository)

## 1. Background and Intended Use

This report evaluates the trustworthiness of a 3D conjugate heat transfer model used to predict peak junction temperature and coolant-side pressure drop for an automotive SiC inverter power module mounted on an aluminum cold plate. The results inform a design gate decision: whether the current stack-up and cold-plate channel geometry provide at least 10 K thermal headroom to the device limit (175 C) under worst-case power dissipation and coolant conditions.

The model is intended for:

- Comparing design variants of the cold-plate channel pattern and TIM thickness.
- Establishing peak junction temperatures for qualification test planning.
- Anticipating pressure drop at nominal and high flow rates to check pump sizing.

The model is not intended for:

- Predicting solder fatigue life or thermal cycling durability.
- Detailed coolant cavitation analysis or two-phase effects.
- Noise and vibration predictions.

Consequences of misuse: If the model underestimates junction temperature by more than 10 K under the prescribed range, the product could ship with insufficient thermal margin. If the pressure drop is underpredicted by >15%, the cooling loop could exceed pump capability.

## 2. Team, Tools, and Process Controls

- Analysts: Two thermal engineers (7 and 12 years experience in electronics cooling) and a fluids SME (turbulence modeling).
- Independent reviewer: Not part of the design team; provided red-team critique at two checkpoints.
- Software: Ansys Fluent 2024 R2 (double precision), operating on a 28-core Linux workstation; builds validated against vendor “Getting Started” and “T-Junction” benchmarks.
- Configuration control: All meshes, case files, scripts, and post templates in Git LFS under repo tag CHT-IM-v1.9. Model change log maintained; see Appendix A for tag mapping.
- Human-factors controls: Boundary condition checklist (BC-CHK-07) completed and countersigned; units and reference frame checks performed using pre-simulation script.

## 3. Physics, Geometry, and Data Sources

3.1 Governing physics and model form

- Flow: Single-phase, incompressible water-ethylene glycol mixture (50/50 by volume), temperature-dependent properties via Fluent’s built-in mixture library polynomial fits (validated vs vendor data to within 1.5% over 20–80 C).
- Turbulence: k-omega SST with low-Re near-wall treatment; y+ ≈ 0.8–1.5 on the coolant-side wall adjacent to heat sources and ≤5 elsewhere.
- Heat transfer: Conjugate across solid stack-up layers; radiation neglected (check showed <1% contribution at 160 C to 50 C).
- Solid conduction: Anisotropic thermal conductivity for IMS ceramic layer (alumina, in-plane 24 W/m·K, through-plane 27 W/m·K); layer thicknesses from supplier drawings. Copper cladding 0.3 mm; DBC variant not modeled in this release.
- Contact/TIM: TIM modeled as isotropic 3.4 W/m·K, 55 μm mean thickness; contact resistance between DBC copper and base plate assumed negligible due to soldered joint; aluminum base plate bulk conductivity 167 W/m·K, verified by vendor certificate.

3.2 Geometry

- CAD from PDM item CP-4172 Rev C; CMM on as-built part shows average channel height 5.05 mm (±0.04), width 7.94 mm (±0.03), confirming within manufacturing tolerance. Mesh built from Rev C geometry. Solder fillets not represented; fillet omission sensitivity checked.

3.3 Boundary and operating conditions

- Inlet: Mass flow rate 8 L/min nominal (range 3–12 L/min assessed). Temperature 50 C (range 30–60 C for applicability).
- Outlet: Gauge pressure 0 Pa.
- Die heat map: Spatially varying heat flux based on electrical loss model at 2.4 kW total for eight SiC dies; distribution ±20% across dies; die thermal footprints from layout MW-239.
- External convection: Module top cover surfaces exposed to air modeled with h = 5 W/m^2·K at 25 C; effect on max junction <0.5 K; retained for completeness.

## 4. Model Construction, Numerics, and QA

- Meshing: Poly-hexcore with prismatic layers on coolant walls; first-layer thickness 25 μm to maintain y+ ≈1 near hotspots; max skewness 0.28, average orthogonality 0.84. Solid mesh conformed to die edges and layer transitions.
- Coupling: Fully coupled CHT solution; segregated pressure-based solver with pseudo-transient ramp; pressure-velocity coupling using coupled algorithm; second-order upwind for momentum and energy; second-order for turbulence equations.
- Convergence: Residuals reduced below 1e-5 for flow and turbulence, 1e-8 for energy; monitored integral quantities (max junction temperature, total heat flux across inlet/outlet) flattened with last 100 iterations drift <0.1 K and energy imbalance <0.3%.
- Stability/robustness: No clipped variables or relaxation overrides; two restarts required for the finest grid to achieve tight energy balance; noted in log.

## 5. Code-Level Checks and Reference Solutions

We performed targeted code-level checks to ensure the numerical setup reproduces known solutions:

- Laminar–turbulent channel heat transfer: For Re = 20,000, Pr = 6.1 (50% glycol at 50 C), the Dittus–Boelter correlation predicts Nu ≈ 148. Fluent reproduction in a straight channel case (same wall y+, SST) delivered area-averaged Nu = 151.5 (2.4% high). This validates wall treatment and turbulence model constants within expected scatter.
- 1D composite slab conduction: Analytical sandwich conduction (Cu–Al2O3–Cu) with uniform heat flux compared to a 3D conduction-only Fluent case. Predicted through-thickness temperature drop matched within 0.3 K at 160 C hot-side for the reference load.
- Energy accounting: For the full CHT model, scaled difference between total imposed heat and enthalpy rise in the coolant plus losses to ambient remained within 0.5% across all meshes.

## 6. Numerical Solution Quality: Mesh and Time Sensitivities

6.1 Steady-state mesh study

- Three systematically refined meshes: 7.2M, 13.5M, and 26.1M cells with near-wall spacing proportionally reduced to maintain y+ ≈ 1.
- Peak junction temperature predictions: 163.8 C (coarse), 162.1 C (medium), 161.5 C (fine) at 2.4 kW, 8 L/min, 50 C inlet.
- Extrapolated Richardson estimate suggests an asymptotic temperature 161.0 C; estimated grid-induced uncertainty for peak temperature on the medium mesh is 1.7 K (≈1.0%). The Grid Convergence Index (95%) for the medium mesh is 1.1%.
- Pressure drop across the cold plate: 42.6 kPa (coarse), 41.0 kPa (medium), 40.7 kPa (fine). Medium-to-fine difference 0.7%. We proceeded with the medium mesh for parametric and UQ studies; fine mesh used to spot-check nominal point.

6.2 Transient check

- A transient ramp of die power (0 to 2.4 kW over 60 s, 0.1 s timestep) showed the steady-state peak within 0.4 K of the long-time limit and no oscillatory behavior. Maximum Courant number <10 in the bulk channel; energy convergence per time step to 1e-7 maintained. No significant time-step sensitivity detected at 0.1–0.2 s.

## 7. Experimental Program and Data Treatment

7.1 Hardware and setup

- Test article: Same module stack and cold plate geometry as simulated, built from production-intent parts from Lot LP-11. TIM applied with automated stencil; post-assembly X-ray measured thickness 53–60 μm.
- Instrumentation:
  - Flow: Coriolis mass flow meter (±0.5% of reading), calibrated July 2026.
  - Temperature: Type T thermocouples embedded near die corners (±0.5 C after ice-point calibration); IR camera for surface die tops with emissivity calibrated using taped patches; die-to-IR correction validated on a sacrificial die with an embedded micro-RTD (agreement within 1.1 C).
  - Pressure: Differential transducer across plate (±1% FS, 0–100 kPa).
- Test matrix: Three loads (1.2, 1.8, 2.4 kW) and three flow rates (4, 8, 12 L/min) at 50 C inlet. Each point repeated twice on separate days; no statistically significant drift observed.

7.2 Data reduction and uncertainty

- Junction temperature estimate: Combined thermocouple and IR data using a bias-corrected fusion; uncertainty evaluated via root-sum-square of calibration, spatial nonuniformity, and emissivity-induced bias, yielding ±1.8 K (95%) for peak Tj at 2.4 kW.
- Pressure drop: Accounting for tubing and manifold losses using an in situ blank run; residual uncertainty ±4% after correction.
- Inlet and outlet temperature difference used to cross-check electrical input; energy balance closed within 2.2% across test points, supporting data reliability.

## 8. Model–Data Comparison and Fitness-for-Use Metrics

At the nominal worst case (2.4 kW, 8 L/min, 50 C inlet):

- Measured peak junction temperature: 165.0 C ± 1.8 K (95%).
- Simulated peak junction temperature (medium mesh): 162.1 C; difference −2.9 K, within combined uncertainty (simulation mesh + measurement) of approximately 3.4 K.
- Pressure drop: Measured 42.1 kPa ± 1.7 kPa; simulated 41.0 kPa; difference −1.1 kPa (−2.6%).

Across the 3×3 matrix:

- Temperature: Mean absolute deviation 3.2 K; maximum deviation 5.1 K at low flow (4 L/min), where the model underpredicts peak by 3.0%—still acceptable for screening decisions.
- Pressure drop: Mean absolute percentage error 4.3%; slight overprediction at the highest flow (12 L/min) by 6.1%, consistent with unmodeled surface roughness beyond nominal Ra.

Acceptance criteria established with the product owner:

- Peak Tj discrepancy less than 10 K across the matrix, with bias under 5 K at nominal condition.
- Pressure drop within 10% across the matrix.

All criteria were met.

## 9. Sensitivity and Uncertainty

9.1 Key factors examined

- TIM conductivity: Sampled 2.8–3.6 W/m·K (datasheet 3.4 ± 0.5); peak Tj sensitivity 2.3 K per 0.5 W/m·K.
- TIM thickness: 45–65 μm; 0.22 K/μm sensitivity.
- Inlet temperature: 30–60 C; linear shift of peak Tj ~1.02 K/K (due to minor property variations).
- Flow rate: 3–12 L/min; Tj change ~3.6 K per 1 L/min near 8 L/min, with diminishing returns above 10 L/min.
- Turbulence model: Realizable k-epsilon (enhanced wall treatment) vs SST; SST yields 1.8 K higher peak Tj on average and 3.5% lower pressure drop, aligning better with experiments.

9.2 Propagated uncertainty

A Latin Hypercube sample (N=100) over TIM conductivity, TIM thickness, inlet temperature, and inlet flow rate (reflecting their measured uncertainties) was executed on the medium mesh. Outputs:

- Peak Tj at nominal setting: Mean 162.4 C; 95% credible interval [160.1, 165.0] C.
- Dominant contributors to variance: Flow (43%), TIM thickness (31%), TIM conductivity (19%), inlet temperature (7%). First-order Sobol indices estimated via regression on LHS results support these rankings.

9.3 Model-form considerations

Comparing SST vs realizable k-epsilon across three points showed a systematic temperature difference of 1–2 K; we take 1.5 K as an estimate of model-form spread for turbulence closure at these Reynolds numbers (≈18,000 at 8 L/min). Radiation and surface roughness are secondary; including a roughness k_s = 10 μm in a sensitivity run raised pressure drop by 3.2% with <0.2 K thermal impact.

## 10. Applicability Envelope and Non-Use Cases

The analysis is applicable under:

- Coolant mixture: 40–55% ethylene glycol by volume.
- Inlet temperature: 20–65 C.
- Flow: 3–12 L/min.
- TIM thickness: 45–65 μm; conductivity 2.8–3.6 W/m·K.
- Single-phase operation; no boiling or cavitation.

Outside these ranges, predictive capability is unverified. Specifically, for coolant below 20 C at 12 L/min, Reynolds number exceeds 25,000 and wall roughness effects may become non-negligible. For inlet temperatures above 70 C, viscosity and thermal property correlations were not cross-checked with vendor data; increased uncertainty should be assumed.

## 11. Alignment with Decision Needs

- Decision: Proceed with Rev C cold-plate geometry and TIM specification to design freeze if thermal headroom ≥10 K at the worst-case electrical loss profile and nominal coolant.
- Findings: Predicted worst-case peak Tj = 162.1 C (medium mesh) vs device limit 175 C → 12.9 K margin. Fine-mesh check at the same condition yields 161.5 C; conservatively, margin remains ≥12.5 K.
- Sensitivity: Under simultaneous pessimistic settings (TIM at 65 μm, conductivity 2.8 W/m·K, flow −10% from nominal), peak Tj rises to 169.6 C, still 5.4 K below the limit. We recommend this as the “assured” margin under typical manufacturing variances.

## 12. Traceability and Evidence

- Requirements trace: Thermal margin requirement TR-IM-017 mapped to simulation cases SIM-IM-CHT-021 to -030 and test points TEST-IM-042 to -050; links captured in the case manifest.
- Provenance: Input properties cited to vendor datasheets VD-AL-11, VD-TIM-08, and mixture property library references. Geometry to CP-4172 Rev C. Heat map to ELM-014 rev G.
- Reproducibility: Running the provided case file on a different host (Windows 11, 24 cores) produced 162.5 C (Δ +0.4 K) with identical solver settings; random seeds not used.

## 13. Independent Review and Cross-Checks

- Peer review notes: Reviewer flagged initial y+ ~3–8 near leading edges; mesh was updated to ensure y+ ≤2 in those regions, reducing sensitivity in wall heat flux predictions.
- Blind comparison: Prior to any TIM property tuning, the model underpredicted Tj by 4.6 K. TIM conductivity was then set to the mid-range datasheet value (3.4 W/m·K) from the initial 3.6 W/m·K assumption. No fitting to match data beyond selecting within published ranges; selection justified by TIM vendor lot data.

## 14. Limitations and Outstanding Risks

- Micro-scale interface irregularities and voids are not explicitly modeled; represented through effective TIM property bounds. High local peaks due to void clusters cannot be captured.
- Thermal cycling and power transients faster than 0.1 s are not covered; the solver time-step control and material heat capacity smoothing may underresolve extremely rapid pulses.
- Subcooled boiling or flashing at sharp corners is not included; model invalid if local wall superheat crosses nucleation threshold, which is not approached in observed data.
- Surface roughness and aging: Long-term roughness change and TIM dry-out are not captured; a degradation study is recommended for end-of-life predictions.

## 15. Overall Credibility and Recommendation

Based on:

- Agreement with measured hardware across a range of powers and flow rates within pre-set acceptance bands,
- Demonstrated mesh convergence and validated solver behavior on canonical problems,
- Quantified uncertainty from both inputs and numerics,
- Process controls for repeatability, peer review, and configuration management,

we evaluate the model as suitable for the stated design decision and screening within the defined applicability envelope. The remaining uncertainties are small compared to the decision margin, with clear paths to reduce them further if necessary (e.g., expanded roughness characterization or extended temperature property validation).

Recommendation: Use the medium-mesh setup for design iterations, with periodic spot-checks on the fine mesh at any design freeze or major geometry change. Maintain the acceptance test correlation dataset for regression checks after any solver upgrade.

## 16. References

- Ansys Fluent 2024 R2 Theory Guide, Chapters on Turbulence and Multiphysics Coupling.
- VD-TIM-08: Thermal Interface Material Datasheet (Lot L9A), Thermexa 3.4.
- VD-AL-11: Aluminum 6061-T6 Material Certificate, Heat 4B76.
- Incropera et al., Fundamentals of Heat and Mass Transfer, 7th Ed., Dittus–Boelter correlation discussion.
- Mixing rules for ethylene glycol-water properties, ASHRAE Handbook 2025, Fundamentals.

## 17. Appendices

- Appendix A: Configuration identifiers, run manifests, and change log summary.
- Appendix B: Mesh quality snapshots and y+ distributions at nominal conditions.
- Appendix C: Uncertainty propagation setup and sample range definitions.

See appendix.md for details.

---
Prepared by: P. Ortega (Thermal Engineer)
Reviewed by: M. Shah (Fluids SME), D. Kim (Independent Reviewer)
Approved by: S. Brennan (Product Owner)
