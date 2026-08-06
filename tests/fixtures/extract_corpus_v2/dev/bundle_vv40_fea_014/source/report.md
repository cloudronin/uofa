To:     M. Ortega, Implant Program Lead
From:   A. Singh, FEA V&V Lead
Date:   2026-08-06
Subject: Credibility memo — hip stem neck stress model for ISO 7206-4 decisions

Context and decision use
- Purpose: use the Abaqus model to predict peak von Mises stress at the neck fillet of the Ti-6Al-4V stem under the ISO 7206-4 bending setup to support design down-select and demonstrate margin relative to 0.2% yield. Physical bench tests remain the compliance evidence; the model informs geometry choices ahead of test.
- Decision impact: moderate. Design changes will be based on model trends and margins; final accept/reject of the product stays with lab results. Target credibility: ≤10% discrepancy to strain data at the critical location; numerical error <5%; documented pedigree and independent review.

Model setup and solver behavior
- Software/hardware: Abaqus/Standard 2022.HF7 on RHEL 8.6, Intel Xeon 6348, double precision. Re-ran on Windows 11/2022.HF7 for a spot-check; key stress within 0.5%.
- Elements and formulation: C3D10 with hourglass control off; large-deformation on; isotropic elastoplastic Ti-6Al-4V (E=110±3 GPa, ν=0.34, σ0.2=825 MPa, Voce hardening from ASTM E8 coupons).
- Contacts/BCs: Stem potted in PMMA (E=2.8 GPa measured); potting modeled explicitly to 40 mm embed per ISO; far face of potting encastre. No frictional interfaces at the neck (monolithic part). Load applied via 12 mm spherical indenter per ISO; surface-to-surface contact (penalty) with k=1e7 N/mm; sensitivity run at 5e6 and 2e7 N/mm shifted local strain by <1%.
- Loads: 2.3 kN to 3.0 kN range assessed; primary check at 2.5 kN as in lab.

Numerical checks
- Mesh refinement study: three levels focused at the 2.5 mm neck radius; min edge 0.2/0.3/0.45 mm; global count 0.9M/1.6M/2.2M tets. Extrapolated peak stress at critical element corner changed 1.9% between last two meshes; energy-norm change 1.5%. We carry ±2% as discretization uncertainty for the QoI.
- Nonlinear solution: load ramped in 20 steps; force residual <0.1% at convergence; contact stabilization off except initial settle step. Step subdivision on did not change the QoI by more than 0.3%.

Bench correlation
- Three stems (Rev C) instrumented with stacked 3 mm gauges near the fillet were tested per ISO 7206-4 by Test Lab B (TR-2026-041). At 2.5 kN, mean measured strain = 1350 με (SD 40). Model-predicted surface strain at gauge centroid = 1405 με; average difference 4.1% (all within 7%). Overlay of full-field DIC (subset 17 px) vs model surface strain shows RMS error 5.3% over a 12×12 mm window.
- We did not tune the neck behavior to these tests. Potting modulus was set from separate PMMA coupon bending (LAB-MAT-2026-08), not from the stem runs.

Inputs and their pedigree
- Geometry: Rev C CAD (NX-2026-06, signed); fillet radius measured by metrology on the tested parts (2.48–2.52 mm) was used in the model for validation runs; for design predictions we parameterized 2.3–2.7 mm.
- Materials: Ti-6Al-4V coupons (lot 6K) per ASTM E8; mean E=110.7 GPa, σ0.2=828 MPa; curves digitized and fit to Voce; PMMA potting modulus from three-point bend coupons (E=2.8±0.2 GPa). All source reports are linked in EDRMS with revision locks.
- Loads/fixture: ISO geometry and indenter verified by calipers; machine alignment within 0.3°. Indenter hardness and radius confirmed.

Assumptions and model form
- The neck is treated as continuum elastic–plastic with isotropic hardening; no microstructural anisotropy modeled. Residual stresses from machining neglected; metrology did not show evidence of tensile bias near the fillet. Temperature effects ignored (lab at 22±1°C). Contact formulation choice shown to be non-influential at QoI.

Sensitivity and variability
- Screening with Morris then Sobol (200 model runs on the mid mesh) across E, potting length (±5 mm), fillet radius (±0.1 mm), and indenter position (±0.2 mm): first-order Sobol indices at 2.5 kN—fillet radius 0.44, E 0.23, potting length 0.19, indenter position 0.08. Interactions small.
- Uncertainty propagation: Latin hypercube (n=300) on E, potting modulus, fillet radius, and indenter offset with measured distributions. 97.5th percentile peak von Mises at the fillet = 612 MPa; combined with ±2% numerical component gives 624 MPa upper bound. Margin to 0.2% yield = 1.32.

Software quality, traceability, and oversight
- Model files, Python pre/post scripts, and material tables are in Git (repo mdx-hipstem, tag v1.4.2); all runs recorded with hash of .inp and Abaqus version. Automated sanity test (cantilever patch with linear field) shows <0.02% error; manufactured bending field on a tapered bar checked at <0.5%.
- Peer review performed by R. Chen (not an author) on 2026-07-18; five findings addressed (contact penalty range, time incrementation, metrology use, mesh transition, DIC alignment). Execution record and sign-off captured in QA-REC-2026-19.
- Analysts: two senior FEA engineers (8 and 12 yrs) executed; lab liaison confirmed test fixture details.

Limitations and applicability
- Intended only for predicting neck fillet stresses under the ISO 7206-4 fixture and load range 2.3–3.0 kN. Not to be used for patient gait spectra, fretting/wear, or fatigue life estimation; separate models are needed. Effects of residual stress, corrosion, or temperature excursions are out of scope. Extrapolation beyond fillet radii 2.3–2.7 mm not supported.

Decision
Based on the evidence above, the hip stem neck FEA is accepted for predicting peak stress at the neck fillet under ISO 7206-4 conditions to support design down-select and demonstrate margin to yield for Revs C–E with measured fillet radii in 2.3–2.7 mm, subject to using a mesh no coarser than the 0.3 mm local size and Abaqus/Standard 2022.HF7 or later with identical material curves. Decision made by A. Singh (FEA V&V Lead) and concurred by J. Patel (Chief Engineer). Not approved for fatigue life, patient activities, or non-ISO fixtures.
