To:      LEO Antenna Bracket IPT Lead
From:    R. Singh, Structures V&V
Date:    2026-08-06
Subject: Credibility check on FEA of LEO-ABRKT-02 support arm (rev v19)

Quick context
We analyzed the aluminum support arm that carries the S-band antenna during ascent and on-orbit slews. The finite element model (Abaqus/Standard 2023 HF1) includes the arm, clevis, and a two-bolt interface to the deck. Primary checks: worst-case ascent loads (1.8 g axial, 0.8 g lateral), random vibe PSD (20–2,000 Hz), and on-orbit thermal swing (-80 C to +60 C) with preload retention.

What looks solid
- Model setup and loads trace back to SYS-ANT-REQ-112 through 118. The gravity vectors and vibe PSD match Dynamics’ release DRN-0247.
- Geometry fidelity is good in most places. The imported STEP from CAD rev H keeps the 8 mm fillet on the inside knee; holes/slots are to nominal.
- We spot-checked the solver against two industry benchmarks (NASA cranfield lug and a bolted lap plate). Stress contours and joint slip-onset loads are within 4–7% of reference solutions.
- For the linear static ascent case using bonded contact, we ran three meshes (1.8M, 3.9M, 7.4M DOF). Peak von Mises at the knee settled from 286 MPa to 281 MPa (approx. 1.8% change) and tip deflection varied <1%. First bending mode sits at 182 Hz, above the 150 Hz keep-out.

Areas that need attention or have mixed signals
- Joint representation
  The v17 runs used tied constraints at the bolts and clevis pin; v19 swaps in surface interaction with friction (µ = 0.2) and bolt pretension elements (5.5 kN each). The text states “joint behavior has minimal effect on peak stress (<3%),” but the attached sensitivity sheet shows an 11–14% increase in knee stress when contact is enabled. We need to resolve which set is being reported in the margin tables.

- Mesh sufficiency near the knee
  The memo claims local refinement to 0.5 mm and quadratic tets. However, the final v19 deck lists 0.8 mm minimum with curvature control off for two small ribs. A separate note says the coarsest mesh was used for vibe due to time. This conflicts with the earlier convergence statement. If vibe stresses are riding the coarse mesh, the 1.8% stabilization figure is not applicable to that case.

- Material properties and temperature
  Inputs sheet cites 7075‑T7351 with room-temperature yield of 503 MPa and E = 71 GPa. A footnote says “-80 C modulus +6% per MMPDS” but the model keeps a constant E and ν. The pull test coupons used AlSi10Mg (printed) as a geometric surrogate; the memo states “correlation within 5%,” but that’s not a like-for-like alloy. Also, one paragraph claims an elastic‑plastic curve with tangent modulus 1.2 GPa was used to check local yielding; the .inp in the vault (v19) has only linear elasticity. Which model underlies the reported FOS?

- Boundary condition realism
  The fixed deck assumption is carried over from PDR, yet the deck panel is a 6 mm CFRP sandwich. A quick superelement swap (NX Nastran) indicated a 0.4–0.6 mm increase in tip displacement and a 7% reduction in first mode. The current result summary still references the fully-fixed case.

- Tool chain and reproducibility
  We state “results repeated on a second solver with <3% difference.” The comparison plot shows 3% at the arm midspan but 9–12% around the bolt head where contact pressure concentrates. Additionally, the vibe case on the backup run used single precision per the job file; primary used double. This undermines the blanket “<3%” claim.

- Load envelope coverage
  The text says ascent lateral load cases include +/-Y and +/-Z. The run list includes only +Y and +Z for the static cases; sign-reversed loads appear only in the vibe combination. It’s not obvious the worst sign has been captured for secondary bending in the knee.

- Documentation and independence
  The header calls out an “independent check by Structures Team B.” The sign-off page shows my initials for both setup and check due to Team B’s availability last week. We should either get a true red-team pass or relabel the current state.

- Manufacturing tolerances
  Metrology report MT-031 notes the as-built inner fillet on the development unit is 6.2–6.6 mm, not 8 mm nominal. A side calc in the deck says “smaller fillet increases stress ~14%,” yet the main margin table assumes the nominal fillet and claims a 1.42 factor above yield. If we apply the 14% hit, that factor slips to ~1.25 without considering temp effects.

What I recommend
- Lock the joint model: use contact with measured friction/bearing stiffness, and propagate that consistently through static, vibe, and thermal-preload runs.
- Re-run local mesh refinement at the knee and bolt holes with curvature-based sizing; document the change in peak stress and hotspot size. Apply the refined mesh to vibe as well.
- Update materials to temperature-dependent data for 7075‑T7351 per MMPDS, or bound the error with a defensible penalty.
- Replace the fixed-base with a deck submodel or flexible constraint representing the CFRP panel, at least for the modal and lateral ascent cases.
- Perform a like-for-like correlation: either test a 7075 arm or clearly segregate the AlSi10Mg surrogate data and do not claim tight agreement across alloys.
- Secure a true peer review from Team B and correct the tool-to-tool delta statement to reflect the high-gradient regions.

Bottom line
On the primary ascent case with bonded joints and nominal geometry, margins are comfortable. However, when using more realistic joint/contact, smaller as-built fillets, and a flexible deck, several figures shift by 10–15%. I’m not blocking CDR, but I recommend labeling current results as provisional pending the above corrections, especially the joint/contact and fillet radius effects. Without that, the stated factors of safety look optimistic.
