To:       PM, Avionics Structures
From:     L. Patel, Structural Analysis
Date:     2026-08-06
Subject:  V&V status for the Ti-6Al-4V SDR Bracket finite element model

Summary
We built and checked an Abaqus/2023 HF6 model of the SDR avionics bracket (Ti-6Al-4V, AM build, machined finish) to support sizing for quasi-static limit loads and qualification random vibration. The analysis meets the acceptance targets in the analysis plan (APL-STR-224, Rev C) and is ready to drive the PDR closeout decision, with quantified margins and error bars.

Intended use and outputs
- Decision: confirm ≥0.20 margin on yield at worst-case combined static + dynamic stresses and avoid local buckling at mounting ears.
- Metrics reported: peak von Mises at fillet F3, bearing stress at lug L2, first four natural frequencies, RMS stress during random vib, and margins with uncertainty bands.

Modeling approach and assumptions
- Geometry: Imported from PTC Windchill CAD (BRK-112-A, Rev B); all fillets >0.75 mm retained; AM surface waviness not explicitly meshed.
- Elements: 10-node quadratic tets (C3D10); 316k elements final. Contact at bolt interfaces via surface-to-surface hard contact; bolt preload via pretension sections.
- Material: Ti-6Al-4V Grade 5, E = 113 ± 3 GPa (MMPDS-17), ν = 0.34, σy = 880 ± 20 MPa. No plasticity modeled (elastic response only); check against yield only.
- Loads/BCs: Static accelerations per SYS-ENV-031 Rev D (±10.2 g axes); bolt preload 6.5 ± 0.7 kN per torque-to-tension calibration; random vibration PSD per GEVS 2.5.2, Q=10, 60 s/axis. Damping as 1.5% structural (from prior bracket family tests).
- Simplifications: No thermal load; no fretting wear; AM porosity not modeled explicitly—captured in material allowables knockdown.

Numerics and solution quality
- Mesh refinement: three meshes (160k/316k/620k). Peak stress at F3 changed by 6.1% (coarse→mid) and 2.7% (mid→fine). Richardson extrapolation suggests 2.4% discretization error at F3; 1.8% for first bending mode.
- Solver behavior: Static solves converged in <12 NR iterations; force balance within 0.6%. Modal extraction using Lanczos; frequency residuals <0.5%.
- Element formulation check: Reduced vs full integration gave <1.5% stress difference in hot spots; no hourglassing observed.

Tool and process control
- Code pedigree: Abaqus/2023 HF6, vendor benchmark suite (NAFEMS LE10, BEAM3, and Axisymmetric pressure vessel) reproduced in-house within 1–2% using our templates.
- Platform: RHEL 8.8, Intel oneAPI 2024, cluster node dual Xeon 6338; runs are repeatable on Windows 11 workstation within 0.8% for stresses.
- Configuration management: Model, scripts, and run decks tracked in Git (repo STR/BRK-112, tag v0.9.7); solver version and environment captured via conda env export; mesh seeds scripted in Python.
- Data traceability: Inputs trace to PLM items (CAD Rev B), materials database MD-017, and load spec SYS-ENV-031 Rev D; all runs logged in RunLog.xlsx with seeds and checksums.

Input quality and test pedigree
- Material data: Coupons from the same AM lot (n=8) confirmed E and yield scatter consistent with MMPDS; used A-basis yield for margins.
- Bolt preload: Torque–tension tests on our hardware stack (n=12) yielded COV 11%; used as uncertainty on pretension.
- Validation data: Subcomponent shaker test on an engineering unit with 3D scans to confirm geometry; accelerometers and rosettes at F3 and L2. First two modes matched within 4.3% and 3.1%; strain RMS during vib within 6.8% after damping tuning to 1.6%. Static pull test to 8.5 g: strain at F3 within 5.9% of model.

Sensitivity and uncertainty
- Local studies: ±10% thickness, ±0.5 mm fillet, ±15% preload, ±3% E. Peak stress is most responsive to preload (∂σ/∂P ≈ 7.4 MPa/kN) and fillet radius.
- Error bars: Combined contributions (mesh 2.4%, material 3%, preload 5%, damping 10% effect on vib RMS) propagated to margin via linearization around the as-run point yield ΔMS ≈ ±0.05 (95%).
- Applicability: Valid for load set SYS-ENV-031 Rev D, temperatures 20–40 C, intact fasteners, and geometry at or above fillet callouts. Do not use for plastic sizing or thermal distortions.

Independent checks and reviews
- Peer review: Independent analyst repeated the mid-mesh case and matched F3 stress within 2.2%; also completed a hand lug check per MIL-HDBK-5—bearing stress MS = 0.41 (vs FEA 0.38).
- QA: Pre/post scripts passed unit tests; checklist STR-CHK-05 signed; no open NCRs.

Results and recommendation
- Worst-case static + vib equivalent stress at F3 is 684 MPa. With A-basis yield 880 MPa, mean MS = 0.29 with ±0.05 uncertainty at 95% confidence.
- First four modes: 412, 487, 1,036, 1,211 Hz (all >1.25× instrument notch frequencies).
- No local buckling predicted; eigenvalue buckling factor 2.9 on ears.

Given the demonstrated correlation to test, bounded numerical error, controlled inputs, and complete provenance, the model is fit-for-purpose for PDR closeout and can be used to finalize bolt sizing and fillet callouts. Limit the reuse to the applicability envelope above; any geometry or load changes beyond that trigger re-verification per APL-STR-224. Training records for both analysts current (Abaqus and random vib courses, 2024), and all artifacts are archived on the project drive (\\nas\STR\BRK-112\release\v0.9.7). No further actions required before FRR other than updating for final CAD Rev C when released.
