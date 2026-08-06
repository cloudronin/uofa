To: PL-HabLander Structures
From: D. Kline, Loads & Dynamics
Subject: FEA credibility status — avionics tray side bracket LLAB-12 (launch environment)

Quick take
- The finite-element model is mostly in line with what we need for CDR, but there are a few places where the story isn’t internally consistent. We should plan one cleanup sprint before freezing the model for downstream loads handoffs.

Model overview
- Geometry: Native CAD from Rev F; fillets retained ≥1.0 mm radius; vent holes included. Local bolt bosses are as-built.
- Connections: Bracket attaches to the tray with four M5 fasteners. Most runs used pretension elements targeting 7.5 kN per bolt and friction 0.2 at the faying surface. One early static run (Static_03) kept the interface fully fixed as a simplification; later runs (Static_05 onward) used contact with preload. This matters for local strains near Hole 2.
- Materials: 7075-T73 aluminum. The writeup in section 2.3 says temperature-dependent modulus (E(T)) was used, but the solver inputs for Static_05 and Random_02 show a constant E = 71.7 GPa at 23 C. Density 2810 kg/m^3, Poisson’s 0.33.
- Loads: Quasi-static 6g axial + 3g lateral combinations, shaker-qualified random vibration (20–2000 Hz PSD), and thermal soak. The test matrix references -40 to +70 C, but the credibility limits summary at the end of the slide deck lists -20 to +50 C as the range of use.

Discretization and solution controls
- Elements: Tetra second order (ANSYS SOLID187), with local refinement to 0.8 mm near fillets and around bolt holes. Global min edge 2.5 mm. 1.2–1.4 M DOF depending on contact state.
- Mesh study: Three densities (h, h/1.5, h/2). The body text claims “stress at the critical fillet changed by <3%” between the two finest meshes; the attached CSV shows 312 MPa (h/1.5) vs 337 MPa (h/2), i.e., +8.0%. For modal frequencies, the first mode varied by 1.7% across the same refinement.
- Nonlinearity: Large-deformation was enabled for contact runs and modal disabled as expected. However, Static_05 has NLGEOM off in the log even though the summary table marks it as on.
- Convergence: Force residuals ≤1e-5 and contact penetration <1% of min element size for the final static runs. Two contact steps required stabilization (0.1% energy damping) to quell chattering.

Comparison to hardware
- We instrumented a single bracket on the shaker (S/N 03) with three strain gauges and a tri-ax at the free edge. Fixtures replicated the bolt pattern with torque-to-tension correlation (7.6±0.4 kN).
- First bending frequency: test 780±4 Hz; model 735 Hz for the contact-preload case (−5.8%). The executive summary slide reads “within 3%,” which doesn’t align with the numbers.
- Strain at Gage 2 (near Hole 2, lateral 3g+6g combined): test 1750 με peak; model 1580 με (−9.7%). Gage 1 and 3 are within 4–6%. The fully fixed early run matched Gage 2 better (1710 με) but at the expense of unrealistic bolt load transfer.

Uncertainty, knobs, and margins
- We explored bolt preload (±15%), friction 0.15–0.25, and E ±3%. The text claims a 1000-run Monte Carlo. The scripts directory shows a 200-sample Latin hypercube (UQ_07) and a 60-run one-at-a-time sweep (Sens_04). No evidence of 1000 samples on disk.
- Peak von Mises at the fillet under the worst combined axis load: deterministic 337 MPa on the finest mesh. Using UQ_07, the 95th percentile lands at 366 MPa. With Ftu/√3 = 455 MPa allowable, tabulated margins alternate between +0.21 and +0.08 depending on which run set is referenced. The -0.02 “tail risk” in draft notes appears to come from extrapolating beyond the 200 LHS samples; that extrapolation is not traceable.

Tooling and pedigree
- Solver: ANSYS Mechanical 2023 R2 on the LunaHPC cluster (double precision), except Static_03, which ran locally on a workstation. Our analysis plan cites 2024 R1 due to an anticipated IT upgrade that didn’t occur before these runs.
- QA: Model files and post scripts are in Git (repo LLAB-12-FEA, tag cdr_pre2). Some solver setting toggles (NLGEOM on/off) were made via GUI and are not captured in the param files.
- People: Lead analyst (me) 7 yrs FEA, 4 on flight hardware. Peer review held with S. Rizzo (8/2). The training matrix lists ANSYS Nonlinear Masterclass as “in progress” for J. Chen, who authored Static_05.

Use bounds and caveats
- Valid when: four fasteners installed, torque achieving 7.5±0.5 kN tension, faying surfaces clean and dry, no shims. Temperature effects currently treated as isothermal at 23 C in the actual runs used for margins.
- Not covered: fretting wear, bolt bending, thread compliance, radiation-induced property shifts, or damage tolerance after mishandling. Acoustic-only excitation not separately evaluated.

Recommendations before freeze
- Re-run the static corner cases with contact+preload and NLGEOM on, and repeat the three-level mesh check; update the table with the actual percent changes.
- Align the temperature treatment with the declared environment. Either turn on E(T) for the launch cases or narrow the applicability box.
- Replace “within 3%” language with the measured 5.8% difference for the first mode, or add evidence that the fixture compliance accounts for the gap.
- Consolidate the UQ story: keep the 200-sample LHS, drop “1000-run” language, and avoid extrapolated tail margins. Report 95th percentile margins from actual samples.
- Capture GUI toggles in the param scripts and retag the model state. If IT approves 2024 R1, document deltas or stay on 2023 R2 through CDR.

Bottom line: The bracket looks healthy on margin, and the trends vs test are reasonable, but the internal mismatches (contact state, mesh deltas, environment limits, and sample counts) need to be reconciled to meet our credibility bar for CDR. I can deliver the cleanup set by Friday if we lock scope today.
