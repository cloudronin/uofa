# CFD Credibility Briefing — S‑Duct APU Inlet with Bleed
- Project: APU intake S‑duct with perimeter bleed, semi-scale rig correlation
- Toolchain: ANSYS Fluent (see version notes), Pointwise meshing, Python post
- Audience: IPT leads, test liaison, chief engineer
- Date: 2026‑08‑06
- Presenter: M&S team (3 analysts)

## Scope and context of use
- Purpose: predict pressure recovery, swirl distortion, and bleed effectiveness for pre‑design trades and rig test planning
- Operating window targeted for decision support:
  - Mach 0.20–0.40, ReD ≈ 2.5e6–5.0e6
  - Inlet incidence −2 to +8 deg
  - Bleed mass extraction 0–5% of core flow
- Success thresholds discussed with IPT:
  - PR prediction within 2% of rig mean
  - Distortion level (DC60) within 10% relative
  - Qualitative capture of separation onset location within ±5% of arc length

## Geometry and physics setup
- CAD basis: CATIA V5 Rev D (“APU_Sduct_RevD.step”)
  - Small chamfers (<0.5 mm), fasteners, and wiring bosses suppressed
  - Lip leading edge kept as‑is; internal surface waviness ignored
- Bleed representation:
  - Statement A: production runs modeled slots as porous jump (K=8.5e7 1/m2, C2=0)
  - Note: slot‑to‑plenum coupling via mass sink; plenum not modeled
- Fluid: dry air, Sutherland law, constant Cp; compressibility enabled
- Thermal: isothermal walls at 300 K; no heat transfer modeled

## Computational setup
- Solver: steady RANS, coupled pressure‑velocity; second‑order spatial schemes
- Turbulence:
  - Statement B: all production cases used SST k‑ω with curvature correction off
  - Wall treatment: low‑Re formulation; target y+ < 1
- Time: pseudo‑transient with local time step; target CFL 50–200 for robustness
- Slots:
  - Statement C: final production meshes resolve each bleed slot with at least 18 cells across width and 30 cells through thickness
- Hardware: Ares cluster, 256 cores/job, 128 GB/job; reported double precision

## Mesh quality and convergence
- Unstructured hybrid grids; prism layers with growth 1.2; 35 layers, first cell height 3.5e‑6 m (aiming for y+ ≈ 0.8 at M=0.3)
- Global counts:
  - Coarse: 3.2M cells; Medium: 7.8M; Fine: 22.1M
- Refinement study:
  - GCI (Richardson, p=~1.9 observed): PR GCI12 = 1.1%, PR GCI23 = 0.6%
  - Mass/energy imbalances: <0.15% (area‑weighted)
  - Residuals: normalized <1e‑5; monitor plateaus reached in <2000 iterations
- Near‑wall metrics:
  - Statement D: y+ < 1 at 98% of wall faces (fine grid), 92% (medium)
  - Analyst log excerpt: average y+ across internal walls 45–80 on medium grid using scalable wall functions

## Boundary and operating conditions
- Inlet: total pressure 101.3 kPa, total temperature 288 K
  - Turbulence intensity 5%, integral length scale 0.02 m
- Outlet: static pressure specified to match target mass flow (rig throttle mapping)
- Bleed: target extraction 3% of core; imposed via porous‑jump dP correlation
- Consistency with rig:
  - Statement E: validation cases matched rig turbulence at 5% and bleed at 3%
  - Run record PDR‑02: TI=1%, length scale 0.10 m; bleed set to 5% to aid convergence

## Verification activities
- Code behavior checks:
  - Regression on internal suite: subsonic diffuser, 2D periodic channel, NACA 0012 at Re=6e6 (lift/drag within literature bounds)
- Solution verification:
  - Mesh refinement as above; iterative convergence tested with tighter criteria (1e‑6) showing <0.1% change in PR
  - Solver settings A/B comparison: coupled vs segregated pressure showed <0.3% PR difference on medium grid
- Numerical fragility:
  - Backflow sensitivity tested at outlet; applied 5% backflow fraction damping; PR change 0.2%
- Precision:
  - Statement F: all runs executed in double precision
  - Scheduler logs indicate several early runs (cases VLD‑03/04) in single precision due to memory limits

## Validation against rig tests
- Data source: NASA‑Ames 9x7 S‑duct rig, campaign 2025‑Q4, 89‑probe rake at AIP, 32 wall static taps
- Conditions compared:
  - M=0.27, α=0°, bleed=3%; M=0.35, α=6°, bleed=0 and 3%
- Agreement summary:
  - Statement G: pressure recovery error within 1% across the matrix; DC60 within 8% relative; swirl direction and magnitude captured within 2°
  - Detailed cuts:
    - At M=0.27, α=0°, PR error 0.8%; DC60 error 6%
    - At M=0.35, α=6°, PR error 4.7%; local separation length underpredicted by ~12% of arc
- Rig uncertainty:
  - PR expanded uncertainty U=±0.6% (k=2); swirl angle U=±0.8°; DC60 U=±4% relative
- Applicability claim:
  - Slide charter stated valid up to α=8°, M=0.4; engineer note in validation deck references use “up to M=0.7, α=15° for concept screening” without new data

## Sensitivity and uncertainty exploration
- Input perturbations (one‑at‑a‑time, medium grid):
  - Inlet TI 1–7%: PR span ±0.3%; DC60 span ±5%
  - Bleed ±1 percentage point: PR change 0.9–1.6%; separation onset shifts ±3% arc
  - Outlet static ±250 Pa: PR change ±0.4%
- Model form checks:
  - Statement H: Spalart–Allmaras selected for production due to stability; PR within 0.5% of SST; DC60 within 6%
  - Curvature correction on vs off (SST): PR difference 0.2%; vortex core location shift ~1 probe pitch
- Combined UQ (simple Monte Carlo, 200 samples; TI, bleed, outlet pressure as inputs):
  - PR standard deviation 0.35%; 95% CI width ~0.9%
- Robustness:
  - Grid adaptation on vorticity magnitude changed PR by 0.2% on fine grid; DC60 by 3%

## Software, configuration, and traceability
- Configuration management:
  - Case decks, meshes, and post scripts in Git (Repo: sduct_apu_cfd); tags PDR‑freeze‑v1 to v3
  - As‑run inputs archived under /proj/sduct/runs with checksum manifests
- Software versions:
  - Statement I: Fluent 2023 R1, build 2023.1.0.133 used for all production
  - HPC job metadata shows VLD‑01 .. VLD‑05 executed with Fluent 2022 R2 (2022.2.0.104)
- Hardware/OS:
  - RHEL 8.7 on Ares; Intel Xeon Gold 6248; Infiniband EDR
- Repeatability:
  - Restart tests on two nodes yielded identical PR within 0.05% (double precision runs)

## Team, process, and reviews
- Analysts: 3 engineers (avg 7 yrs CFD); two have prior S‑duct experience
- Process:
  - Analysis plan B‑342 issued at project start; checklists for setup and QA applied
  - Exception log shows 2 waived checks (mesh skewness criterion exceeded near slot edges; y+ target not met on medium grid)
- Peer review:
  - Design review held 2026‑07‑15; internal peer review completed; test liaison participated
  - Action items 7/12 closed; two open items on slot modeling fidelity and TI matching
- Training and licensing:
  - All users current on tool training; license features verified

## Limitations and outstanding items
- Separation dynamics at α ≥ 10° likely require URANS/LES; current steady RANS may misplace bubble onset
- Bleed slot modeling inconsistency between porous‑jump and resolved geometry across runs requires reconciliation
- Inlet turbulence level in several validation cases not matched to rig records; impact on distortion non‑negligible
- Near‑wall resolution claims conflict with medium‑grid y+ logs; potential overconfidence in SST low‑Re performance
- Version/precision discrepancies (2022 R2 vs 2023 R1; single vs double) not fully bounded
- Applicability beyond M=0.4 and α>8° not substantiated by data

## Recommendation and decision
- Recommendation by CFD Lead (J. Patel) and Chief Engineer (L. Brooks):
  - The current CFD setup is accepted for:
    - pre‑design screening of bleed door sizing and inlet PR trends for M=0.20–0.40 and α within −2..+8°, and
    - planning of rig test points within that envelope,
    - with the understanding that predicted DC60 may deviate up to ~10% relative at off‑design.
  - The current CFD setup is not approved for:
    - final inlet distortion compliance reporting,
    - certification‑level predictions, or
    - flight envelope expansion beyond α=8° or M>0.40.
- Required follow‑ups before any broader approval:
  - Align turbulence inflow with rig measurements; re‑baseline distortion metrics
  - Resolve slot modeling approach and re‑run a subset of validation cases
  - Demonstrate consistent near‑wall resolution or adopt appropriate wall functions with quantified impact
  - Lock software version/precision and document re‑runs where deviations occurred
