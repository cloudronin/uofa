To:     PM, SmallSat Attitude Control Subsystem
From:   CFD Lead, Aerosciences Group
Subj:   Credibility snapshot — cold-gas plume loads on deployable panel (FUN3D)
Date:   06 Aug 2026

Summary
We built and checked a CFD model to predict force and torque on the solar wing from a 12 N nitrogen thruster for control authority sizing. The model is suitable for steady burns at sea-level to 5 km altitude, panel standoffs 0.4–0.8 m, and jet-panel misalignment up to 20°. Below are the key points that govern how much trust to place in the numbers.

- Intended use and success criteria: Output needed is panel-integrated normal force and hinge torque with ±10% total error over 0–30° yaw and H/D of 50–100. The analysis supports PDR load tables; it is not intended for high-frequency jitter or contamination risk.

- Modeling choices and simplifications: Compressible, fully turbulent single-phase N2; no chemistry or rarefaction (Kn < 1e-3); adiabatic, no-slip walls; steady-state RANS. k–ω SST with low-Re wall treatment (y+ ~ 0.8) was chosen over realizable k–ε based on jet impingement literature.

- Geometry and boundaries: Nozzle diameter 8.00 ± 0.02 mm (vendor cert QN-22-145); a 0.1 mm lip chamfer was omitted (<0.2% area effect). Domain extends 40D upstream and 60D downstream; non-reflecting farfield with sponge. Plenum total pressure 8.6 bar ±1%; T0 295 ± 2 K; ambient 101.3 ± 1 kPa.

- Numerical setup: FUN3D v13.5, double precision, Roe flux with Venkat limiter, 2nd-order spatial, implicit pseudo-time stepping. Switching to AUSM+up altered hinge torque by 1.5%, so scheme dependence is low for this case.

- Code checkout: We ran FUN3D’s manufactured-solution suite (compressible shear/MMS). Observed L2 order: u,v,w = 2.01±0.03; p = 1.96 on uniform refinements (h, h/2, h/4). Nightly regression (186 tests) all green on the same build hash (a38f4c2).

- Solution convergence and discretization study: Three unstructured meshes: 1.2M, 4.8M, 19M cells with boundary-layer clustering. Residuals dropped 4–5 decades; force/torque monitors flat to <0.2% over 4k iterations. GCI on hinge torque at the medium mesh is 3.2% (asymptotic range verified); pressure footprint GCI 2.4% RMS.

- Input pedigree and traceability: Thruster calibration and plenum P–T uncertainty are NIST-traceable (Cal Lab 03/2026). Nozzle D and panel standoff surveyed with CMM (±0.05 mm). All inputs, units, and tolerances are captured in inputs.yaml with schema checks.

- Comparison to tests: Benchmarked against published impinging jet pressure maps for H/D = 60 and 80 (NASA TM-2001-210823) and an AFRL angled-jet rig at 15°. Mean normal force error 6.7% (H/D=60) and 7.9% (H/D=80). Radial Cp RMS error 9.3% over 0<r/D<8. For 15° yaw, hinge moment differed by 8.5%. We bracket the intended envelope with four data points.

- Range of validity and caveats: Do not use for pulsed firings, altitudes where Kn > 0.01, or flexible-panel fluid–structure effects. DES trials indicate mild unsteadiness at H/D < 40 not captured by steady RANS; we excluded that regime.

- Uncertainty quantification: Latin hypercube (N=500) on P0, T0, D, H, inlet turbulence intensity, and panel yaw; included a discrete model choice (SST vs realizable k–ε) as a between-model variance. 95% interval on hinge torque at H/D=62.5 is ±11%. Variance contributions: H (52%), P0 (28%), D (10%), I’ (6%), model form (3%).

- Sensitivity and robustness: Local Sobol indices agree with one-at-a-time slopes within 10%. Outlier rejection not needed; three repeat runs on the same mesh vary <0.2% (random seeds fixed).

- Post-processing fidelity: Loads integrated on the CAD-faithful panel; pressure sampled on 256 probes matched to test radii using area-weighted Voronoi maps; interpolation error <0.5% by refinement of the sampling surface.

- People and experience: Two analysts with >6 yrs FUN3D experience; both completed the internal RANS-for-jets checklist. Same workflow supported Sensorsat-1 plume loads (post-flight telemetry within 8%).

- Process control and configuration: Git-managed repository (tag v1.3.2), Jenkins CI for meshing and run scripts, issue tracker for deviations. All meshes, decks, and notebooks archived with DOI (10.5281/zenodo.1234567).

- Independent eyes: Dr. A. Velasquez (not on project) reviewed decks and BCs; flagged an inconsistent inlet turbulence spec (fixed to 5% TI, L=0.5D). Sign-off memo dated 2026-07-22.

- Computing environment: Runs on Sagitta cluster (Intel Xeon Gold 6248R, OFED 5.1). Reproducible in a Singularity container with FUN3D build a38f4c2 and Intel 2021.4 compilers; hashes recorded in run logs.

- Planning and governance: The analysis plan and acceptance thresholds were approved at SRR; this memo closes PDR action A-17. Next step is targeted wind tunnel check at 10° yaw, H/D=70 to tighten the 95% band to ±8%.

- Error checking and user safeguards: YAML schema validation blocks unit mismatches; pre-run script verifies y+ targets, farfield extent, and CFL limits; failures halt job submission.

Bottom line: For the defined envelope, the predicted hinge torque and panel normal load meet the ±10% target with quantified margins. Use the medium mesh results with the stated ±11% 95% interval and the limitations above for PDR loads; higher fidelity (DES or a tunnel point) is recommended only if tighter margins are required post-PDR.
