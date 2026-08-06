Conjugate Heat Transfer Credibility Assessment Report
Avionics Cold Plate for the Gateway PMU, Rev. B

Executive summary
This report evaluates whether a three‑dimensional thermal–fluid model of the Gateway Power Management Unit (PMU) cold plate is dependable for its stated job: guiding pre‑PDR design choices (channel geometry, pump sizing, and temperature margin assessment) under single‑phase operation of a PAO coolant. The model is implemented in Siemens Simcenter STAR‑CCM+ 2022.1 with RANS turbulence (SST k–ω), steady solver, and tight coupling between fluid and solid regions.

The evaluation draws on: (1) a mesh‑quality campaign and solver checks; (2) comparison to bench measurements from an engineering development unit (EDU) across nine operating points; (3) quantified uncertainty from inputs and measurements; (4) sensitivity exploration; (5) configuration control, tool pedigree, user qualifications, and independent review. Within its stated boundaries, the model reproduces EDU component case temperatures within ±1.5 K (95% confidence) and pressure drop within 6% across the measured envelope. The modeling approach has been used on prior spaceflight avionics cooling projects with similar error characteristics.

Decision: accepted for Gateway PMU pre‑PDR design trades, heat‑load allocation, and pump sizing across the single‑phase envelope defined in Section 2; not approved for flight certification temperatures, boiling onset prediction, or two‑phase behavior. Decision taken by the Thermal Discipline Lead, Gateway PPE/HLCS IPT, on 2026‑07‑14.

1. Background and context of use
The PMU cold plate is a machined 6061‑T6 aluminum block with a serpentine channel network under the PCB mounting surface. Coolant is polyalphaolefin (PAO) circulated in a closed loop. The analysis supports:
- Screening alternative channel topologies prior to CDR.
- Establishing pump head and flow targets for the shared loop.
- Estimating temperature margins to component limits during early trades.

The problem class is steady, single‑phase forced convection with conjugate conduction through the base plate, thermal interface materials (TIM), and copper planes in the PCB surrogates. No boiling, flashing, or gas ingestion is modeled in this iteration.

2. Model overview, scope limits, and key assumptions
Geometry and physics
- Fluid region: serpentine channels 3.0 mm (W) × 2.0 mm (H), fifteen passes, manifolded ends.
- Solid regions: 6061‑T6 base plate (k = 167 W/m·K), threaded inserts and bosses modeled as 303 SS (k = 15 W/m·K), PCB surrogates as FR‑4 (k = 0.3 W/m·K) with 30% copper fill, and heat‑source bricks representing ICs.
- Interfaces: TIM modeled as equivalent solid layers: Bergquist Gap Pad 5000S35, nominal thickness 0.5 mm, effective k = 3.2 W/m·K from vendor curve at 30°C; contact resistance not modeled separately in the main CHT runs but bracketed in sensitivity (Section 9).
- Fluid: PAO meeting MIL‑PRF‑87252; density, cp, k, μ fitted to polynomial functions of temperature using vendor and NASA TP‑2003‑212909 data from 15–50°C.

Boundary conditions and operating envelope
- Inlet mass flow: 0.5–1.5 L/min; baseline 0.9 L/min.
- Inlet temperature: 20–35°C; baseline 23°C.
- Outlet static pressure: 1.2 bar(a) as reference; pressure drop reported relative to outlet.
- Heat inputs: three heater blocks at 80 W, 60 W, and 45 W; total 185 W unless otherwise stated.
- External faces other than mounting bosses: adiabatic (enclosed bay); four M5 bosses tied to 0.2 W/K conduction path to surrounding structure, derived from thermal desktop network model of the avionics bay.

Assumptions and limitations
- Flow is treated as turbulent over the full range (SST k–ω with automatic wall functions). Justification: baseline Reynolds number at 0.9 L/min in 3×2 mm channels is ≈ 4,200 (T = 23°C).
- Coolant remains single phase; cavitation and boiling are out of scope.
- Surface roughness set to 1.5 µm Ra based on CMM surface finish measurements.
- Manifold minor losses are represented geometrically; no extra K‑factors are added beyond what the CAD captures.
- TIM thickness uniform per pad; assembly variation handled via uncertainty analysis.

Applicability window
- Valid for PAO in the 15–40°C bulk temperature range, 0.5–1.5 L/min, total heat loads 100–250 W, single‑phase. Outside this domain, error growth is unquantified.

3. Software, hardware platform, and configuration control
- Solver: STAR‑CCM+ 2022.1 (build 16.02.008‑R8), double precision, steady segregated flow/energy solver, coupled CHT.
- Turbulence: SST k–ω; turbulent Prandtl number 0.85; low‑Re corrections enabled.
- Hardware: JSC HPC “Hera,” 2× Intel Xeon Gold 6248R (48 cores total), 192 GB RAM. All production runs on RHEL 8.6, Intel MKL 2022.3, and consistent MPI stack as captured in run logs.
- Versioning: Geometry (NX 2206), meshes (.sim files), journals, and post‑processing scripts maintained in GitLab repo PMU-CHT-CP at MSFC, protected main branch, model releases tagged v0.9.0 through v1.2.3. SHA‑256 hashes recorded in the run manifest (Appendix A).
- Reproducibility: Solver settings stored in parametric template; automated Jenkins job re‑runs baseline weekly to detect drift versus pinned version; last three reruns within 0.03 K on max case temperature.

4. Team qualifications and process discipline
- Lead analyst: P.E., 14 years spacecraft thermal/fluid simulation, STAR‑CCM+ Certified Professional.
- Two supporting analysts: one Ph.D. in heat transfer, one M.S. with electronics cooling background.
- Test engineer: 20 years thermal test, owns calibration and DAQ setup.
- Peer reviewer: independent of IPT, prior lead for Orion cold‐plate thermal certification.
- Procedures: Work followed JSC‑SWP‑TH‑017 for CHT analysis, including readiness reviews, modeling checklists, and archival requirements. Analysts completed annual STAR‑CCM+ update training (2025).

5. Numerical quality checks: mesh, residuals, and conservation
Gridding strategy
- Polyhedral volume elements in fluid; ten prism layers on walls with growth 1.2; y+ < 1 for main channel surfaces.
- Solid regions meshed with trimmed cells around heat sources and bosses; local refinements under components.

Mesh independence
- Three systematically refined meshes built with geometric factor r = 1.3 (coarse C: 1.1 M cells; medium M: 2.7 M; fine F: 5.8 M). Same setup run on each; under‑relaxation unchanged.
- Target metrics:
  - Peak component case temperature T_case,max at nominal operating point.
  - Channel outlet bulk temperature.
  - Pressure drop Δp between inlet and outlet monitors.
- Observed Richardson extrapolation and GCI:
  - T_case,max: extrapolated 58.9°C; M deviation −0.6°C; GCI_M = 1.1%.
  - Outlet T: extrapolated 30.7°C; M deviation −0.05°C; GCI_M = 0.2%.
  - Δp: extrapolated 18.6 kPa; M deviation +0.9 kPa; GCI_M = 4.8%.
- Iterative convergence
  - Residuals reduced below 1×10^−6 for continuity and energy, 1×10^−5 for momentum; last 500 iterations: max change in monitored temperatures < 0.01 K.
- Conservation
  - Mass imbalance < 0.05%.
  - Energy balance between electrical heat input and coolant enthalpy rise plus conduction to bosses closed to within 0.3% on the baseline mesh.

6. Tool behavior spot‑checks and benchmarks
While STAR‑CCM+ is a vetted commercial tool, we performed two focused checks:
- Internal flow pressure drop: Single straight channel geometry, 3×2 mm, L = 100 mm, PAO at 23°C; predicted friction factor f within 2.5% of Blasius correlation at Re = 4300.
- Heated duct Nusselt number: Same channel with 10 W uniform heat flux; predicted Nu within 4.1% of Gnielinski correlation over Re = 2500–8000.

7. Experimental comparison
Test article and instrumentation
- EDU cold plate, as‑machined, inspected dimensions ±0.03 mm.
- Heat inputs applied by three cartridge heaters embedded in copper blocks sized to component footprints. Power measured by a Yokogawa WT3000E power analyzer, ±0.1% FS, corrected for lead losses.
- Coolant: PAO from flight batch; density and viscosity sampled via Anton Paar SVM 3001 (certificate #SVM-3001‑0423).
- Flow rate by Emerson Micro Motion CMF010M Coriolis meter (±0.5% of rate); inlet/outlet pressure by WIKA S‑11 transducers (±0.25% FS); temperatures by Type‑T thermocouples, Special Limits of Error, individually calibrated against a Fluke 5608 PRT in an isothermal bath; combined uncertainty ±0.12 K (k = 2).
- DAQ: NI cDAQ‑9178 with 9213 modules; sample rate 10 Hz; 10 min averaging after steady state.

Test matrix
- Three flow rates: 0.6, 0.9, 1.2 L/min.
- Three heat load distributions: [80,60,45], [70,70,45], and [60,60,60] W for [U1,U2,U3] blocks; total ~185 W.
- Inlet temperature 23±0.2°C.

Model–test comparison summary (95% CI)
- Component case temperatures (10 thermocouples across three blocks): mean absolute difference 0.9 K; worst‑case bias +1.4 K at U2, low‑flow case; no spatial outliers > 1.6 K.
- Outlet temperature: predicted 30.7–33.9°C vs measured 30.9–34.0°C; differences −0.2 to −0.1 K.
- Pressure drop: predicted 13.2–22.1 kPa vs measured 12.5–21.0 kPa; relative error +2.3% to +6.1%.
- Trends with flow and power matched monotonicity and curvature within measurement uncertainty; no need for a posteriori tuning. Note: we did not adjust TIM properties using EDU data; separate coupon tests informed TIM values (Section 8).

8. Inputs and supporting data: sources and traceability
- TIM conductivity: Vendor datasheet curve (Bergquist 5000S35), de‑rated by 20% based on a separate guarded hot‑plate test at JSC (sample GP5000‑A12, 0.5 mm, 30°C contact pressure 100 kPa). Test report JSC‑TH‑LAB‑2026‑031 archived in repo /testdata/tim.
- PAO properties: NASA TP‑2003‑212909 primary; cross‑checked against ExxonMobil SHC ATO logs; polynomial fits documented in tools/properties.py with unit tests ensuring RMS fit error < 1% over 15–50°C.
- Geometry: NX model PMU_CP_v17.prt, GD&T inspection file PMU_CP_DIM_2026‑06‑11.xlsx; discrepancies from design used to update analysis geometry.
- Boss conduction path: Derived from Thermal Desktop v6.4 resistor network of avionics bay, with contact conductance at mounting interfaces from torque‑to‑conductance correlation (Appendix B).
- Heater power: Calibrated per WT3000E certificate Y‑3000E‑22‑113; line losses computed from 4‑wire resistance at 23°C.

Input data management
- Each parameter set has a provenance tag (source doc ID, date, owner) in params.yaml.
- Changes to defaults require pull request and two approvals (analysis lead + test lead).
- Attempted edits to vendor‑controlled files in repo are blocked; SHA verification on ingest.

9. Uncertainty and sensitivity
Measurement uncertainty in validation
- Combined standard uncertainty for a typical case temperature difference is 0.35 K after accounting for sensor calibration, spatial gradients within the thermocouple bead footprint, and DAQ quantization; expanded to 0.7 K at k = 2. The model‑experiment comparison accounts for this.

Input and model uncertainty for predictions
- Epistemic sources: TIM effective conductivity (±25%), TIM thickness (0.5±0.1 mm), PAO viscosity fit (±2%), inlet flow (±1%), surface roughness (1.5±0.5 µm), boss‑to‑structure conductance (0.2±0.05 W/K), turbulence model constant (turbulent Prandtl 0.85±0.05).
- Aleatory sources: assembly pressure variation on TIM, represented as a normal perturbation of ±15 kPa around nominal clamp load; realized via conductivity adjustment per vendor curve.
- Propagation: Latin Hypercube sampling, N = 500; outputs tracked: T_case,max and Δp.
- Results at baseline operating condition:
  - T_case,max mean 59.1°C; standard deviation 0.6 K; P95 = 60.1°C.
  - Δp mean 19.1 kPa; standard deviation 0.8 kPa; P95 = 20.4 kPa.
- Contribution to variance (Morris screening followed by Sobol on top three factors):
  - TIM conductivity and thickness jointly explain 63% of variance on T_case,max.
  - Flow rate explains 22% of T_case,max variance and 81% of Δp variance.
  - Roughness affects Δp at the 6–8% level; negligible on temperatures within tested range.
- Model‑form uncertainty:
  - Alternative turbulence model (realizable k–ε with enhanced wall treatment) shifts T_case,max by +0.4 K and Δp by −1.1 kPa relative to SST k–ω at baseline; we incorporate ±0.5 K, ±1.2 kPa as model‑form contributions in the above totals.

10. Alternative models and cross‑checks
- A 1‑D network model (Thermal Desktop + SINDA/FLUINT 6.0) predicts outlet temperature within 0.3 K of the 3‑D CHT across the validation matrix but lacks spatial resolution on hot‑spot temperatures. Pressure drops are underpredicted by ≈ 8% due to simplified loss coefficients.
- A finite‑volume in‑house code (legacy FORTRAN) for heated channel flow provided a single‑pass comparison differing by 3.0% in Δp and 0.6 K in wall temperature at Re = 4,500.

11. Results robustness and operating envelope coverage
- The solver converged across 36 parametric operating points (flow 0.5–1.5 L/min, inlet 20–35°C, heat 100–250 W) without divergence or oscillation.
- Hot‑spot locations remain co‑located with the highest heat flux components across the envelope; no anomalous reversal of temperature ranking with flow rate or inlet temperature.
- No prediction indicates approach to saturation temperature at any point within the envelope; minimum wall‑to‑bulk superheat observed is > 25 K.

12. Planning, reviews, and stakeholder involvement
- A modeling and test plan was baselined at IPT MRR‑CHT‑001 (2026‑04‑05) defining acceptance targets for comparison: mean case temperature difference < 2 K, no point > 3 K; pressure drop within 10%.
- Readiness and closeout reviews were held with the Thermal Working Group (TWG) on 2026‑05‑02 and 2026‑07‑07. Action items addressed: refine prism layers to achieve y+ < 1 near bends; include boss conduction per updated bay model; and treat turbulence model uncertainty explicitly.
- The test plan and results were witnessed by the Systems V&V representative; raw data and reduction scripts are archived.

13. Documentation and traceability
- This report, the plan, raw test data, reduced data, meshes, solver settings, post‑processing macros, and the run manifest are stored under PMU-CHT-CP/releases/v1.2.3 in the PLM system and mirrored in the GitLab project.
- Each figure and table in this report is traceable to a script with a commit ID; rerunning the figure build regenerates the artifacts from raw sources.

14. Prior use and operating experience
- The same modeling workflow (STAR‑CCM+, SST k–ω, polyhedral mesh with near‑wall resolution) was used for:
  - Orion ECLSS avionics cold plates (2018): archived comparison showed ±1.8 K on component temperatures, +5% on Δp.
  - Europa Clipper RF module cold plate (2020): ±1.4 K on component temperatures, +7% on Δp.
- The toolchain and post‑processing macros are derivations of those projects; differences are documented in CHANGELOG.md.

15. Independent review and cross‑discipline checks
- An external reviewer from the Orion program completed a line‑by‑line model review on 2026‑06‑21 (Review Report ORN‑XT‑REV‑221). Findings closed include: (a) initially missing roughness assignment in manifold regions (corrected), and (b) outdated PAO viscosity correlation (updated to TP‑2003‑212909 fit).
- The Systems Engineer confirmed that the modeled heat load distribution aligns with the latest PMU board power map (ECN‑PMU‑PWR‑17).

16. Limitations and open items
- Two‑phase behavior is not represented. If loop pressure falls or heat flux rises to trigger local boiling, errors could be large and unbounded.
- Contact resistances between pad and component were consolidated into an effective conductivity; we did not explicitly simulate micro‑gaps or bowing. This is partially covered by uncertainty bounds.
- Temperature‑dependent mechanical preload on TIM due to differential expansion is not in the model; for the current range (20–35°C) the effect is judged small, but for wider sweeps it should be revisited.
- Manufacturing variability in channel geometry was characterized for a single EDU; production variance could affect Δp more than temperatures. A process capability study is planned with QA.

17. Credibility synthesis against acceptance goals
- Numerical soundness: Residuals, conservation, and mesh studies indicate small discretization error for temperatures (< 1.2% on T_case,max). Pressure drop GCI is higher (≈ 5%) but still within targets and dominated by roughness/manifold details.
- Representation of physics: Selected turbulence model and single‑phase CHT are appropriate for Reynolds numbers and heat fluxes in scope; alternative model tests show small shifts consistent with expectations.
- Data pedigree: Material and fluid properties are from primary sources; TIM properties are anchored with a local test. Geometry reflects measured parts.
- Agreement with reality: Across nine operating points, the model captures both absolute values and trends with tight residuals; no hidden tuning was introduced using the validation data set.
- Uncertainty awareness: A structured propagation quantified the spread due to key inputs; decision‑relevant outputs are reported with 95% bounds.
- Process and people: Qualified team, configuration control, and reproducibility mechanisms are in place. An independent reviewer and the TWG weighed in.
- Prior track record: Similar avionics applications with this workflow have performed comparably, increasing confidence in transferability.

18. Results summary relevant to decisions
- For the baseline case (0.9 L/min, 23°C, 185 W), predicted T_case,max = 59.1°C (P95 = 60.1°C) with a 100°C component limit, leaving > 39 K margin. Outlet temperature 30.7°C; Δp = 19.1 kPa (P95 = 20.4 kPa).
- Across 0.5–1.5 L/min and 100–250 W, margins to the 100°C limit remain > 20 K, assuming single‑phase operation and the TIM properties within the tested bounds.
- Pump head sizing for the shared loop should include 21 kPa per cold plate at 1.2 L/min plus manifolds and instrument losses; with three plates in parallel, the loop design point remains within the pump performance curve provided by the vendor (ref. PMP‑VND‑2861).

19. Decision
Based on the body of evidence, the Gateway Thermal Discipline Lead has accepted the PMU cold‑plate CHT model for:
- pre‑PDR design trade studies,
- sizing and selection of the loop pump and valve positions,
- estimating temperature margins for board‑level component placement in the single‑phase regime defined herein.

The model is not approved for:
- flight certification temperatures,
- assessment of boiling onset, cavitation, or gas ingestion effects,
- analysis outside the 15–40°C PAO temperature and 0.5–1.5 L/min flow range.

Conditions for use
- Use the provided model version v1.2.3 or later with the same solver version; if tool versions change, re‑run the baseline check.
- For predictions used in design decisions, include the uncertainty bands from Section 9.
- If the loop design indicates approach to saturation or reduced pressure margins, a two‑phase‑capable model and additional testing shall be planned.

Approval
Decision owner: Thermal Discipline Lead, Gateway PPE/HLCS IPT
Date: 2026‑07‑14
Rationale reference: Sections 5–9, 12, 14–18.

Appendix A. Run manifest (excerpt)
- Baseline case: tag v1.2.3, commit 0x8f4c2e, STAR‑CCM+ 2022.1, mesh “M” 2.7 M cells, journal run_baseline.jou, log hash 7c6d…d4b2.
- Mesh study: cases mesh_C (1.1 M), mesh_M (2.7 M), mesh_F (5.8 M). Report scripts: gci_temp.m, gci_dp.m.
- UQ set: LHS‑500, seed 112358, properties.py v0.3.1.

Appendix B. Mount boss conduction derivation (summary)
- Thermal Desktop network reduction of avionics bay ties four M5 bosses to the structure through plated inserts and bracket legs. Contact conductance functions developed from torque vs conductance correlation (JSC‑MECH‑2025‑019) at 2.5 N·m, yielding 0.2 W/K aggregate to the bay structure at 23°C. Sensitivity ±0.05 W/K encompassed in UQ.

Acknowledgments
We acknowledge the TWG for review, the test lab for timely EDU testing, and the HPC support team for maintaining consistent solver environments.
