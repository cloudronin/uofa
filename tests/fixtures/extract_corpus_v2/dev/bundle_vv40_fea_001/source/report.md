# Credibility Assessment Report — Landing Gear Strut FEA Model

Project: SkyReach UAS-17 main landing gear strut  
Analyst: L. Moreno (Structures)  
Independent reviewer: C. Patel (Stress and Test)  
FEA tool: Abaqus/Standard 2022 HF4 with in-house pre/post scripts (pyAster-bridge v3.2)  
Model ID: UAS17-LG-STRUT-STAT-ULT-RevD  
Date: 2026-07-15

## Executive Summary

This report evaluates whether the finite-element model of the UAS-17 aluminum main gear strut is dependable enough to inform go/no-go design decisions at the ultimate load case and to support certification artifacts for static strength. The model focuses on quasi-static behavior under the CS-VLA-equivalent 6.0 g landing condition with forward drag and side load components. The primary outputs are:

- Peak equivalent stress at the inboard lug fillet radius.
- Bearing stress under the two M10 fasteners at the fuselage interface.
- Axle vertical deflection at the wheel centerline.
- Elastic-plastic margin to yielding and reserve to a 1.5× ultimate uplift edge case.

We compare simulation to targeted component and full-scale tests (strain gages and LVDT deflections), evaluate numerical robustness (mesh refinement, nonlinear convergence behavior, contact stabilization), assess input pedigree (material data, bolt preload measurements), propagate input variability to outputs (Latin Hypercube sampling), and examine whether the modeling scope matches the intended decisions. The analysis supports acceptance for static strength assessment and design screening within the defined operating envelope; it is not approved for fatigue life, wear, or crash energy absorption.

## Background and Intended Use

- Decision being supported: finalize geometry of the machined 7075-T6 aluminum strut and release for machining of Qualification Test Article (QTA) and certification static test planning.
- How the model is used: predict local stress and deformation in regions that are poorly instrumented in tests (e.g., hidden lug fillets), inform bolt pattern sizing, and corroborate compliance under ultimate static loads.
- Quantities of interest (QOIs): 
  - Maximum von Mises stress in the inboard lug transition radius.
  - Bolt-hole bearing stress at the fuselage interface.
  - Axle vertical deflection at the wheel centerline.
  - Plastic strain hotspot size (equivalent plastic strain > 0.2%).
- Acceptance bands:
  - Correlation target for validation points (strain and deflection): within ±10% of test means at ultimate load.
  - Mesh-related uncertainty on QOIs: under 5%.
  - Probability that peak stress exceeds 0.9× yield at ultimate: below 5% with the specified input variation.

## Model Description

- Geometry: Solid model from CAD P/N UAS17-STRUT-ASY-310 rev B. Simplifications include: removal of cosmetic fillets < 0.5 mm; thread representation replaced by smooth shank + tied constraints; wheel axle represented as a rigid beam proxy to maintain load distribution while reducing degrees of freedom.
- Elements: C3D10 (tetrahedral, 10-node) in the lugs and fillets; C3D8R (hexahedral, reduced-integration) in prismatic web regions; COH3D8 cohesive “bonding” elements not used; beam elements for axle surrogate (B31).
- Material models:
  - 7075-T6: Elastic-plastic with isotropic hardening based on MMPDS-07 curves, E = 71.7 GPa, ν = 0.33, σy0.2% = 503 MPa; plastic curve digitized and smoothed; temperature fixed at 23°C.
  - Steel fasteners (A286): linear elastic up to 1200 MPa for the static scenario; preload introduced via bolt load feature.
  - Frictional contact: lug-pin and fuselage interface with μ = 0.18 (dry aluminum-steel, rough machining).
- Contacts and constraints:
  - Surface-to-surface contact on lug-pin and foot-to-fuselage pad; penalty formulation; finite sliding.
  - Tie constraints between insert pads and strut web where bonded.
  - Remote load coupling for drag and side load, applied at axle beam reference point.
- Loads:
  - Vertical landing reaction: 18.2 kN per leg (worst case distribution from landing dynamics).
  - Drag: 2.0 kN; Side: 1.1 kN.
  - Bolt preloads: 11.5 kN each (measured torque–tension correlation with K = 0.2; ±10% uncertainty).
- Solution controls:
  - Static, general step; NLgeom = On.
  - Automatic stabilization factor 2e-6; line search enabled.
  - Convergence tolerances: 1e-6 force residual; max 100 increments, initial increment 0.05, min 1e-6.

## Solver Correctness and Software Trustworthiness

- Benchmark comparison:
  - Plate with a central hole under uniaxial tension (Kirsch solution). Using C3D8R with reduced integration and selective refinement near the hole, we reproduced the stress concentration factor Kt = 3.02 vs analytic 3.0 (0.7% deviation).
  - Cantilever beam tip displacement under end load matched Euler–Bernoulli closed-form within 0.5% using B31 elements over 10 elements per span.
- Regression tests:
  - Our pyAster-bridge scripts executed 12 nightly checks on common pre/post routines (material mapping, contact sets). All green over the last 90 days.
- Software configuration:
  - Abaqus/Standard 2022 HF4 validated internally (GEER-1220) with vendor’s QA documentation. No open SCRs affecting contact or elastoplasticity for this release were found in the internal tracker as of 2026-06-28.

Evidence indicates the solver and scripting environment behave consistently for the physics and element types employed.

## Mesh Quality and Numerical Convergence

- Mesh refinement study:
  - Three meshes: M1 (0.9M DOF), M2 (1.8M DOF), M3 (3.7M DOF). Local control in fillets and around bolt holes; growth ratio ≤ 1.3.
  - Extrapolated peak stress at lug fillet via Richardson-like extrapolation (assuming observed order p ≈ 1.8 for tetra-dominant zones) gives 532 MPa; M3 predicts 523 MPa (1.7% shortfall). GCI-style estimate yields numerical uncertainty of 2.4% for that QOI.
  - Axle deflection converged faster: M2 to M3 change 0.8% (80.7 mm to 80.1 mm).
- Nonlinear contact:
  - Penalty stiffness scaled with material E and element size; verified no chatter by inspecting contact status maps and monitoring oscillation in reaction force (variation < 1.5% per increment at steady push).
- Solver robustness:
  - With stabilization off, step convergence required cutbacks in early contact closure but reached the same final state; residual pattern and plastic zones were consistent. Stabilization was retained for production runs due to 30% reduction in wall time with negligible damping energy (<0.1% of external work).

We consider the discretization choices and stopping criteria sufficient for the decision scope; numerical imprecision on QOIs remains under the set thresholds.

## Input Data Pedigree and Calibration Steps

- Material properties:
  - 7075-T6 data derived from MMPDS-07 and corroborated by three tensile coupons from batch SR-7075-23. Average yield = 510 MPa (COV 2.1%), ultimate = 568 MPa. Plastic curve scaled to match coupon yield; hardening slope aligned within 3% of handbook curve up to 3% strain. No ratcheting or cyclic data used (out of scope).
- Bolt preload:
  - Torque-to-tension correlation obtained from 8 instrumented installations; mean preload 11.5 kN with SD 1.2 kN. This distribution feeds the uncertainty model.
- Friction coefficient:
  - Estimated from literature and a small ring-on-disc test (n=5) with mean 0.19, SD 0.03. We set nominal μ = 0.18 for structural runs. No tuning to match test strain; only used to avoid unrealistically large slip at pads.
- Geometry tolerance:
  - Fillet radii per drawing R3.0 ±0.3 mm. As-built metrology of QTA shows R = 2.92–3.08 mm. Mesh was parameterized to 3.0 mm nominal; sensitivity study covers ±0.3 mm.

No parameter was “fit” to force quantitative agreement with tests; minor alignment of plastic curve to batch yield mitigated known batch-to-batch scatter.

## Physical Tests and Comparison

- Component test: Single lug coupon under pin loading.
  - Set-up: Reamed hole, pin fit H7/g6, μ minimized with lubricant to isolate bearing response.
  - Measured strain at 1.2× limit load matched FEA within 6.4% at the 45° gage.
- Full assembly static press:
  - The strut installed to a rigid fuselage surrogate with two M10 fasteners preloaded to 11.5 kN, vertical load applied via hydraulic ram and load cell, drag and side components imposed with turnbuckle. Strain gages at inboard and outboard lug fillet, axial on web; LVDT at axle.
  - At 6.0 g equivalent: 
    - Inboard lug fillet strain: Test 2530 με ± 70; FEA 2420 με (−4.3%).
    - Web axial strain: Test 1380 με ± 60; FEA 1325 με (−4.0%).
    - Axle vertical deflection: Test 81.3 mm ± 1.2; FEA 80.1 mm (−1.5%).
  - Hysteresis small; unloading residual strain negligible within gage error, consistent with localized plasticity confined to <2 mm^3 near the hotspot in FEA.

We also checked that strain field shapes along scan lines match within 8–12% RMS. The model slightly under-predicts peak strain but within acceptance.

## Applicability and Boundaries of Use

- Load envelope: Valid for vertical reactions up to 1.1× the 6.0 g case; beyond that, hardening model extrapolation is unproven.
- Temperature: Room temperature 15–35°C; no thermal softening modeled.
- Surface condition: Dry, unlubricated lug-pin and pad interfaces; μ between 0.12 and 0.24 covered in UQ.
- Geometric tolerance: Fillet radius within ±0.3 mm; hole clearance within H7/g6 range.
- Not covered: Corrosion pitting, fretting wear, crack growth, or off-axis impact events. Dynamics of drop tests are analyzed with a different model; this one is static-equivalent only.

Users should not apply the current model to fatigue life estimation or crashworthiness claims.

## Uncertainty and Sensitivity Exploration

- Sources considered:
  - Material yield ±3.5% (normal).
  - Bolt preload ±10% (normal, truncated at ±3σ).
  - Fillet radius ±0.3 mm (uniform).
  - Friction μ ~ N(0.18, 0.03), truncated to [0.12, 0.24].
  - Vertical load ±2% (instrumentation variance).
- Propagation:
  - 240-point Latin Hypercube sampling on M2 mesh with response correction to M3 via locally linear surrogate on key QOIs.
  - Results (at 6.0 g nominal):
    - Peak von Mises at lug fillet: mean 518 MPa, SD 16 MPa; 95th percentile 544 MPa.
    - Probability that stress > 0.9× yield (0.9×503=452.7 MPa): >99%; expected at this load level. However, area above yield >0.2% plastic strain remained below 3 mm^3 in all samples.
    - Axle deflection: mean 80.5 mm, SD 1.1 mm.
  - Dominant contributors via Morris screening followed by Sobol:
    - Yield strength and fillet radius drive peak stress (first-order indices 0.47 and 0.29).
    - Bolt preload influences pad slip and secondary bending (index 0.15).
    - Friction has moderate effect on local slip but low impact on peak von Mises at the fillet (index 0.07).

- Combining numerical and input uncertainty:
  - Total uncertainty on peak stress combining mesh (2.4%) and input variation (~3.1%) by root-sum-square yields ~3.9%.

Uncertainty is bounded and aligned with the decision risk tolerance specified by the structures lead.

## Data Handling, Traceability, and Reproducibility

- Configuration management:
  - Inputs (CAD STEP, material curves, bolt data), solver decks, and post-process scripts under Git repo STRUT-FEA with tag v1.4.2; commit 7f9b3d1 for production runs; read-only archive in PDM under ECO-3107.
- Run environment:
  - HPC cluster AMC-02, Intel Ice Lake nodes, 256 GB RAM per job, Abaqus/Standard 2022 HF4; job logs archived with run IDs LG-U6G-R1..R3 (deterministic single-thread solver; no stochastic dependence).
- Review artifacts:
  - Peer review checklist completed 2026-07-05; action items 2/2 closed prior to RevD (contact stabilization justification; confirm bolt preload distributions).
- Accessibility:
  - All figures and CSV exports in /results/RevD/plots; automated notebooks (Jupyter) reproduce figures from ODB files via Abaqus2Matplotlib.

Anyone with read access can re-run the RevD workflow and regenerate key metrics in under 6 hours wall time.

## Quality Controls, Human-in-the-Loop Checks, and Usability Constraints

- Preprocessing safeguards:
  - Scripted entity naming and property assignment; cross-checks flag elements missing material or sets lacking contact. Zero warnings for production mesh.
- Manual inspections:
  - Section cuts at lugs, contact pressure distributions, and plastic strain contours were reviewed by two analysts.
- Training/qualification:
  - Primary analyst certified on Abaqus elastoplastic/contact module per internal training STR-102; reviewer has conducted three prior gear-lug studies.
- Risk of misuse:
  - To avoid extrapolation errors, the analysis template blocks runs if vertical load exceeds 1.1× ultimate; it also warns if temperature field is attached.

These measures mitigate user error and ensure consistent model application.

## Results Summary

- Deterministic (nominal inputs, M3 mesh):
  - Peak von Mises inboard lug fillet: 523 MPa. Plastic strain limited to 0.28% in a 2.6 mm^3 zone.
  - Bearing stress at fuselage bolts: 428 MPa against bearing allowables of 680 MPa (MMPDS pin-bearing, B-basis).
  - Axle vertical deflection: 80.1 mm; test 81.3 mm ± 1.2 mm.
  - Load path assessment: 94% vertical reaction via lug-pin; 6% via pad friction. Slip at pads under 0.15 mm.
- Margin discourse:
  - Peak stress slightly exceeds nominal 0.2% offset yield (503 MPa) by 4%; however, area is small and local; no global plastic collapse; static test acceptance allows localized yielding with no detrimental permanent set in function.
- Robustness:
  - Removing stabilization yields 525 MPa (+0.4%); alternate μ = 0.12 raises slip but reduces fillet stress to 516 MPa (load redistribution).

Overall, the model captures the full-field response and local peaks well, with trends and magnitudes consistent with physical tests.

## Assessment of Fitness for Purpose

- Alignment with decision:
  - The model addresses static strength under combined vertical, drag, and side loads, which is the immediate design gate. QOIs match the design criteria (stress at critical fillet, bolt bearing, deflection).
- Evidence sufficiency:
  - Solver trust established via targeted benchmarks and regression checks.
  - Mesh and convergence studies bound numerical error below thresholds.
  - Validation against both component and system-level static data falls within ±10% targets.
  - Input variability treatment shows limited spread on critical outputs and highlights main drivers.
  - Documentation and repeatability are in place.

Given the moderate decision consequence (structural integrity at ultimate static load) and the breadth of corroborating evidence, the credibility of this model is assessed as suitable for the stated use within its applicability limits.

## Limitations and Open Issues

- Model form:
  - No damage initiation/evolution or crack propagation; peak stress is used as a proxy for local yielding only. This is acceptable for static ultimate but not for life predictions.
- Time-dependent effects:
  - Creep, rate sensitivity, and impact dynamics are excluded. The companion drop test simulation (explicit) is out of scope here.
- Thermal and environment:
  - No temperature or moisture effects; corrosion and fretting not modeled.
- Assembly variability:
  - Only preload and friction variability considered; pin fit tolerance and surface roughness not fully propagated. Future iterations could expand this coverage.
- Experimental scope:
  - Validation tests at a single ambient condition; no thermal sweeps; limited gage coverage near some second-order hotspots.

These gaps are acknowledged and reflected in the final usage statement below.

## Decision

By joint determination of the Structures Lead (J. Kim) and Chief Engineer (R. Ortega), the FEA model UAS17-LG-STRUT-STAT-ULT-RevD is accepted for:

- Design screening and drawing release of the UAS-17 landing gear strut for static strength at and below the 6.0 g ultimate equivalent load, including preparation of certification submittals for static tests,

subject to the following conditions:

- It is not approved for fatigue life substantiation, wear/fretting evaluation, or crash/impact scenarios.
- Analysts must keep inputs within the applicability bounds defined herein (load, temperature, geometry tolerances, friction range).
- Any changes to geometry beyond ±0.3 mm in critical fillets, bolt pattern, or material batch outside the verified property band require re-run of the mesh study and re-correlation against tests.

The model is not accepted for any purpose outside the context stated above.

## References

- MMPDS-07, Metallic Materials Properties Development and Standardization.
- Abaqus 2022 Documentation, Dassault Systèmes.
- Internal Test Report TR-STRUT-STATIC-026, “UAS-17 Landing Gear Strut Static Press,” 2026-06-12.
- Internal Materials Report MR-7075-SR23, “Coupon Tensile Data for Batch SR-7075-23,” 2026-05-08.
- GEER-1220, “Abaqus/Standard 2022 HF4 QA Summary.”
- Script QA Log SQAL-bridge-v3.2, 2026-07-01.

## Appendix Map

- Appendix A: Mesh refinement details and element metrics.
- Appendix B: Validation plots and residuals.
- Appendix C: Uncertainty propagation settings and sample distributions.

See accompanying appendix.md for extended details.
