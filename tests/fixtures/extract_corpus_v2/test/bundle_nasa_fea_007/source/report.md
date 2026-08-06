To:      DPM, Avionics Structures
From:    R. Chen, FEA Lead
Date:    2026-08-06
Subject: Credibility snapshot — antenna boom bracket FEA (P/N BRKT-ANT-021)

Quick summary
We’ve completed the stress analysis for the deployable antenna boom bracket under quasi-static launch loads. Current model points to a minimum yield margin of 0.18 at the lower inboard filet adjoining the web. No red flags on fastener loads. Some open items remain around fillet radius confirmation and bolt preload scatter, but the basic picture is stable.

Model setup
- Geometry: Native from CAD rev C (drawing ANT-021-003). Small chamfers (<0.3 mm) suppressed; the as-machined relief at the web root modeled explicitly at 1.6 mm. Bolt holes modeled with nominal diameters; no thread features.
- Elements: Tetrahedral quadratic (C3D10M), with local sizing to 0.35 mm in the web-root zone and 1.2–2.5 mm elsewhere. Final production run at ~520k elements, ~840k nodes.
- Material: 7075-T73 aluminum. E = 71.7 GPa, ν = 0.33, σy = 435 MPa (MMPDS-28 Table 3.7.6.0(b)). Density for inertial check 2810 kg/m³.
- Contacts: Surface-to-surface with penalty formulation at the bracket–base interface; μ = 0.20. Fastener shanks tied to hole surfaces; under-head contact active.
- Loads/BCs: Quasi-static “stubbed” launch case: 30 g axial (parallel to boom), 15 g lateral. Base ring fully constrained at mounting lugs consistent with the adapter plate. Twelve M6 bolts preloaded to 8.5 kN each (per fastener spec FST-M6-12.9, torque 10.5 N·m and k = 0.20 assumed).

Mesh adequacy
We ran a three-level refinement on the high-stress area:
- Coarse: 180k elements → peak von Mises = 374 MPa
- Medium: 340k elements → 356 MPa
- Fine: 520k elements → 349 MPa
Change medium→fine = −2.0% at the hotspot; bolt load distribution shifted <1%. Displacements at antenna hinge line changed <0.6%. Based on that, we used the fine mesh for reporting.

Sensitivity checks
- Bolt preload 7–10 kN: hotspot stress varied +4.8%/−3.1%; max bolt axial load shifted from 9.4 kN to 10.1 kN.
- Interface friction μ = 0.15–0.30: hotspot stress within ±2.2%; slip tendency reduced as expected with higher μ.
- Fillet radius at web root 1.2–2.0 mm: stress dropped roughly 9% per +0.4 mm increase; this is the dominant geometric lever.

Correlation with bench data
We instrumented the development article (rev B machining, same nominal geometry at the critical filet) and pulled with a calibrated test frame to mimic the 30 g axial resultant. Three strain gauges near the hotspot read 1980–2140 με. The model predicted 2060–2185 με at the same locations/gage lengths after applying the measured bolt torques (8.1–8.7 kN equivalent). Average difference across the three gauges: 5.9%, worst case 8.3%. No anomalous bending evident; bolt strain in the two most loaded fasteners matched within 6% of the predicted axial.

Results of record
- Peak von Mises at web root: 349 MPa (fine mesh), margin to yield = (435/349 − 1) = 0.25. Including 3% allowance for discretization per the refinement trend, reported margin = 0.18.
- Next hot area: under-head fillet of the forward inboard bolt, 312 MPa; bearing stress at hole edges max 218 MPa.
- Load path: 63% of axial reaction carried by the six inner-ring bolts; shear sharing is uniform within ±7%.
- Stiffness: hinge-line lateral deflection under combined quasi-static loads = 0.28 mm.

Model artifacts and files
- Primary model: Abaqus/Standard 2023.HF2, job “ANT021_QS_AxLat_revC_fine.inp”
- Stored in PDMVault under “BRKT-ANT-021-FEA” rev C, with a readme noting the gauge locations and test fixture offsets.

Gaps and next steps
- Confirm as-built fillet at web root. The supplier’s first-article report lists 1.55–1.65 mm; drawing shows 1.60 ± 0.10 mm. We modeled 1.60 mm nominal; updating to measured values is unlikely to shift margins more than a few percent, but we should lock this down.
- Bolt torque scatter: request production torque-tension data (k-factor) from ME; our assumption of k = 0.20 drives ~±5% on hotspot stress across the observed range.
- Run an orthogonal lateral load case (0 g axial, 15 g lateral) to close the envelope for adapter-plate sizing; expected to be non-controlling but not yet executed.
- For vibe, a separate modal and PSD assessment is in progress on the system model; not duplicated here.

Ask
- Approve carrying the 0.18 yield margin for SRR-level reporting with the stated caveats on fillet and preload. We’ll refresh the numbers within a week after metrology and torque-tension data arrive.

End. Reach out if you want the ODB and the test/analysis overlay plots.
