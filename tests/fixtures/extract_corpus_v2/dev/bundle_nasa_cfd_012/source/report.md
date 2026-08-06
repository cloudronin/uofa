To:    A. Patel, Project Lead, Aero Loads
From:  M. Rivera, CFD V&V Lead
Subj:  Status update — CRM transonic CFD credibility package (FUN3D)
Date:  2026-08-06

Quick readout
We are on track to use the FUN3D predictions for the CRM wing-body at transonic conditions to support the loads envelope. Evidence below touches the key pieces reviewers will look for. Bottom line: mean forces and surface pressures are within the agreed error bars at the validated points; uncertainty bands and limits-of-use are documented; process control and traceability are in place.

- What we’re trying to predict and how it will be used
  - Intended use: estimate mean CL/CD and sectional Cp for aero loads and shock positioning in the range M=0.72–0.90, α=0–4 deg, Re=3–8 million.
  - Decision tolerance agreed with Loads/Structures: ≤±1.5% on CL, ≤±8 drag counts on CD, shock location within ±0.02c, Cp RMS within ±5% at tap rows.

- Physics and modeling choices
  - Governing equations: compressible RANS (steady) for mean loads; IDDES for limited unsteady buffet spot checks at M=0.85, α=3 deg.
  - Turbulence: k–ω SST; fully turbulent boundary layers; transition not modeled (consistent with NTF roughness and tripping).
  - Thermo: air, Sutherland’s law; walls adiabatic, no slip; rigid airframe (no aeroelastic coupling).

- Numerical approach and solver pedigree
  - Solver: FUN3D 13.8 (commit 3b7d9d1), double precision, second-order in space and time (dual-time stepping for unsteady).
  - Code checks: local manufactured-solution (source term) test reproduced FUN3D’s internal baseline with observed order 1.97 on a smooth field; re-ran the FUN3D regression suite with max diff <1e-13. 2D NACA0012 inviscid grid-convergence recovered ~2nd-order lift trend.

- Geometry and BCs rationale
  - Geometry: NASA CRM wing-body baseline, Rev 2, watertight surface from LaRC CAD; verified planform/section vs. reference within 0.2 mm.
  - Farfield: pressure/temperature set for target M and Re; α via velocity vector; farfield radius ≥20 chords; outlet nonreflecting.
  - Wall roughness set to NTF-equivalent smooth; checked sensitivity (see below).

- Mesh quality and solution convergence
  - Three unstructured grids: 12M / 34M / 96M cells; near-wall y+ ≤ 1 over 98% area, first-layer height 1e-5 m, growth ≤1.2.
  - Residuals dropped 4–5 orders; force histories level; 2000 physical timesteps for IDDES with CFLconv ~3–5 after initial transients.
  - Grid study: GCI estimates at M=0.85, α=2 deg: CL 0.9%, CD 3.5 counts, shock x/c within 0.015. Time-step halving changed CL by 0.2%.

- Input data credibility
  - α calibration from model attitude sensors: ±0.03 deg (1σ). Tunnel total conditions from facility DAS: p0 ±0.1%, T0 ±0.15%. Turbulence intensity set to 0.5% ±0.3%.
  - Material/thermo properties: NIST air; Sutherland constant validated to within ±2% over 200–300 K.

- Cross-check against test data
  - Dataset: NTF CRM campaign (AIAA DPW-III/IV lineage), cryogenic conditions; blockage/weight corrections per facility procedures.
  - Measurement uncertainty: CL ±0.002, CD ±3 counts, Cp taps ±50 Pa; AoA repeatability ±0.02 deg.
  - Results at M=0.85, α=2–4 deg: CL within 0.8% of mean; CD within 6 counts; spanwise shock position within 0.02c; Cp RMS within 3–4% on upper-surface rows.

- Uncertainty bands on predictions
  - Propagated input spreads via a 40-point Latin hypercube (α ±0.05 deg, Tu 0.2–1.0%, roughness k+ 0–3). 95% intervals: ±1.2% on CL, ±8 counts on CD, shock x/c ±0.02.

- Sensitivity and calibration notes
  - One-at-a-time and Sobol screening show α explains ~72% of output variance in CL; Tu contributes ~18%; roughness negligible at tested levels.
  - No tuning of turbulence constants performed; shock position sensitivity to βkω toggles checked (<0.01c change).

- Range where we trust the model
  - Validated envelope: 0.72 ≤ M ≤ 0.90; 0 ≤ α ≤ 4 deg; Re 3–8M. Above α≈5 deg with onset of stronger separation, RANS accuracy degrades; use IDDES only with caution and no formal error bars outside the above envelope.

- Software QA and reproducibility
  - Builds: Intel oneAPI 2023.2, OpenMPI 4.1.5 on Pleiades (Skylake). Deterministic MPI reduction enabled; fixed random seeds for IDDES.
  - Config management: git-tracked inputs/meshes; run manifests (hashes, compiler flags) stored with checksums; archive on DAAC with nightly backups.

- Analyst qualifications and process discipline
  - Team completed FUN3D user training in 2025; standard pre/post checklists used; peer desk check performed on setup before long runs.

- Documentation and provenance
  - Analysis plan AL-23-CRM Rev C; run matrix RM-CRM-09; naming convention CRM_M085_A2_G96_SST; all plots scripted (Py3.11, Matplotlib); DOIs reserved for final datasets.

- Independent eyes
  - Red-team review by AeroSci Branch (R. Jensen, L. Park) on 2026-07-22: requested coarser-grid y+ histogram and BC summary; both addressed. Final sign-off targeted for SRR-2.

- Track record and community standing
  - FUN3D and our workflow matched DPW benchmarks within typical community spreads (lift ±1–2%, drag ±5–10 counts) in prior X-59 and TCA efforts.

- Platform behavior and stability
  - Pleiades node health nominal; two reruns of the same case match to within 0.3% on CL for IDDES; no negative volumes or CFL blowups reported.

- Result robustness checks
  - Restart from three different initial fields converged to same steady RANS solution; refinement from 34M→96M monotonic in CL/CD; Cp contours inspected for spurious oscillations (none).

- Assumptions/limitations called out
  - No aeroelastic or aero-thermal coupling; fully turbulent assumption; no ice/contamination; facility corrections applied as provided.

- Management and risk posture
  - M&S plan approved; risk item “shock-induced separation fidelity” mitigated via targeted IDDES runs and expanded uncertainty bounds; 1-week schedule margin preserved.

Ask
- Approve use of the steady RANS results for loads within the validated envelope.
- Endorse IDDES use only as qualitative guidance for buffet onset; no formal margins derived from unsteady runs at this stage.

Attachments: mesh stats, convergence plots, validation overlays, uncertainty workbook, review minutes.
