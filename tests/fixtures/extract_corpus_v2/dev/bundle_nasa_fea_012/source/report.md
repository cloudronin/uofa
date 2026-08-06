To: Lander Structures IPT Lead
From: M. Ortega, Senior Analyst, Structures V&V
Subject: Status of FEA model for avionics deck corner bracket (LL-HF-STR-FEA-2001)
Date: 2026-08-06

Context and scope
We built and evaluated the finite-element model of the avionics deck corner bracket that carries the star tracker electronics during launch and ascent. The intended use is to establish load paths, stresses/strains, and mode shapes for PDR and to support the structural margin roll-up in the 20–2000 Hz random environment. Not in scope: pyro-shock response, impact/handling damage, or long-duration thermal creep.

Model description and numerical checks
- Software and setup: Ansys Mechanical 2024 R1 (build 24.1.106) with SOLID186/187 elements for the 7075-T7351 bracket, MPC beam elements for fasteners, and surface-to-surface contact (Augmented Lagrange, µ = 0.30 ± 0.05) to the 6061-T6 deck. Large deflection OFF; material behavior linear elastic; bolt preload included (8.5 ± 0.5 kN).
- Discretization: Three meshes studied at the fillet hotspot—coarse (2.0 mm), medium (1.0 mm), fine (0.5 mm). Peak von Mises at the notch root: 182, 191, 194 MPa. GCI on stress at the hotspot is 2.1% (observed order 1.9). Element quality: Jacobian ratio > 0.65 everywhere; max aspect ratio 3.8; no negative volumes.
- Solver behavior: Static substeps up to 50; contact stabilization OFF. Convergence criteria: force residual < 0.5% and displacement < 0.5% of reference. Re-running the fine mesh on a separate workstation reproduced results within 0.4%.

Physical comparison and coverage
- Subcomponent static test (bracket bolted to a surrogate deck plate, Instron 5985, 10 kN vertical load): tip deflection 1.23 mm measured vs 1.19 mm predicted (3.3% low). Strain at Gage S3 near the fillet: 612 µε measured vs 575 µε predicted (6.0% low). Load path and deformation shapes visually consistent.
- Bench modal survey (free-free, roving hammer, PCB 086E80): first three bending/torsion modes at 488/733/1059 Hz measured; model gave 472/709/1036 Hz. Frequency error −3.3%/−3.3%/−2.2%. MAC > 0.92 for all three modes.
- Envelope match: Tests exercised 0.6–1.2× the anticipated bolt preload and contact pressure ranges; vibration modes in the band of interest. No data yet for temperatures above 60 C; model not claimed valid there.

Inputs and their pedigree
- Alloy property data from MMPDS-17, Sheet 3-7 (7075-T7351), cross-checked with receiving inspection coupons (Lab Report MAT-LL-1121). Adhesive shim properties not used; joint modeled metal-to-metal with surface roughness implicit in friction.
- Fastener torque from MECH-ICD-LL-19 Rev D; torque-to-preload scatter ±6% based on in-house calibration.
- Random vibe PSD from Environments Rev G; loads converted to equivalent static per DO-160G procedure for sizing; time-domain verification to come at CDR.
- Geometry from CAD Rev K; tolerances applied in UQ per GD&T callouts.

Uncertainty and sensitivity work-up
- Parameter variations (Latin Hypercube, 300 samples): E(7075) ±3%, µ 0.25–0.35 uniform, bolt preload 8.0–9.0 kN triangular, deck thickness 6.2–6.4 mm uniform, hole diameter tolerance ±0.05 mm, residual numerics via GCI treated as normal with σ = 2% on hotspot stress.
- 95th percentile stress at the fillet: 201 MPa; with allowable 275 MPa (limit), margin of safety (allowable/demand − 1) is 0.37 at 95th percentile. Exceedance probability of demand > allowable estimated at <0.1% under the input distributions.
- Global drivers (Morris then Sobol on top 5): friction coefficient and bolt preload dominate (>60% total variance on hotspot stress); deck thickness next (~20%); material E minor. This ranking is consistent with our contact-dominated load path.

Robustness exercises
- Nudging key knobs (µ ±0.05, penalty parameter ×/÷2, large-deflection ON): hotspot stress moved <2.5%; mode frequencies within 1.8%.
- Artificial clearance of 25 µm introduced at one bolt: local stress rose 3.1% but margin remained >0.33.
- Reruns with different solver tolerances and order of operations showed no bifurcations or chatter in contact convergence.

Assumptions and applicability
- Linear elastic metals; no plasticity invoked since peak stress <75% of yield at all cases studied. No thermal preload; ambient 20–30 C. Contact modeled dry; no lubrication. Load introduction is through specified bolt pattern; no back-side supports beyond deck plate in the test configuration. Model not intended for shock, drop, or temperatures >80 C.

Software governance and traceability
- All decks, APDL snippets, and post scripts stored in GitLab repo M&S/LL/Bracket at tag v1.6. Commit a71cf5e matches the results herein; run logs archived under Jenkins job LL-FEA-020 with artifact checksums.
- Toolchain QA: solver version pinned; patch notes reviewed (no open bugs affecting SOLID186 small-strain). Element behavior verified with patch tests and comparison to Roark closed forms for simple cases earlier in the campaign (see notebook VNV-LL-08).

People and process
- Primary analyst (Ortega) 12 yrs spacecraft structures; Ansys Certified Professional. Peer analyst (K. Shah) 8 yrs fastener/contact modeling.
- Reviews held: analysis plan review (APR) on 2026-06-14, model walk-down on 2026-07-02, and red-team readout on 2026-07-30. Action items closed; two clarifications on friction prior warranted—addressed with updated coupon data.
- Configuration control via the Lander M&S Plan MP-LL-7009B-01; model change requests logged and dispositioned by the Structures V&V Board.

Use history
- The same bracket family and workflow were applied on Pathfinder-3 (2022); correlation to test within 5% strain at hotspots and 4% on first mode. Lessons learned (contact stabilization pitfalls) incorporated here.

Data quality from test
- Strain gages calibrated to NIST-traceable standards; one gage (S5) dropped during the static test due to lead failure—excluded per procedure and replaced in a repeat pull; results consistent within 1.2%. Load cell ±0.5% FS.

Interpretation and limitations
- The contact-dominated joint means friction and preload control field performance; margins are healthy but rely on maintaining torque procedurally. The model does not capture fretting or wear, nor bolt bending nonlinearity beyond small deflection. For pyro-shock or high-temperature duty cycles, a separate model is required.

Independent review
- AeroSys IV&V performed an independent model review; no critical findings. They recommended adding a torsional mode target in the next modal survey; we agree and have added it to the CDR plan.

Bottom line and decision
- The analysis set produces stable, reproducible results; comparison with bench data is within 2–6% across key metrics; inputs are traceable and their uncertainties have been propagated. Margins meet program criteria with low exceedance probability, and the modeling choices are appropriate for the current questions.

Recommendation
- By decision of the Structures V&V Board (Chair: L. Kim, 2026-08-06), the bracket FEA model LL-HF-STR-FEA-2001 is accepted for PDR stress and modal substantiation and for generating load participation factors, subject to:
  1) re-run of the random response with the CDR PSD update when available, and
  2) one additional modal target (torsion about the long axis) to be matched within 5% at CDR.
- The model is not approved for shock analysis or for thermal creep assessments; separate models/validation will be provided for those contexts.
