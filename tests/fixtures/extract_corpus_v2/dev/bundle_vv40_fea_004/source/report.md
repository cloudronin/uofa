To: Priya Shah, Mechanical Design Lead
From: Ethan Miller, V&V Engineer
Subject: Status of hip-stem FEA credibility against ISO 7206 bending

Summary
We evaluated the Abaqus-based finite element model of the cementless femoral stem (sizes 1–5) used to predict bending stiffness, peak stress at the neck fillet, and relative hotspot ranking under ISO 7206-4/8 style loading. Against our pre-declared acceptance targets (±10% on peak von Mises at the gauge region, ±5% on stem stiffness, correct ordering of the top three stress hotspots), the model met or exceeded requirements. Key numbers: stiffness error 3.5% (mean across n=8 specimens), stress error 6.9% at the primary gauge, and hotspot ordering matched test strain maps in all eight cases.

Geometry, loading, and materials
- CAD simplifications are limited to removal of laser-mark engravings and threaded extraction holes; fillets ≥0.25 mm are retained. A tie-rod boss blend radius was measured on production parts (2.1±0.05 mm) and set to 2.1 mm in the model.
- Test fixture replicated ISO 7206-4: 80 mm embedding length in PMMA potting; load vector 10° anterior, 10° lateral; target bending moment 230 N·m. The model includes the PMMA block with E=3.0 GPa from vendor certs; stem–PMMA contact modeled as bonded, per irreversible cure.
- Base material is wrought Ti-6Al-4V ELI; elastic modulus 110±3 GPa and 0.34 Poisson from heat-lot tensile tests (n=12). Elastoplastic response is represented with a bilinear hardening rule (yield 880 MPa, tangent 1.2 GPa) matching our coupon data to within 2% in the 0.2–0.6% strain band used for the stiffness check. No parameter fitting to bench data was performed.

Numerics and element technology
- Second-order tets (C3D10) in the stem; linear bricks in the PMMA. Contact stabilization off; automatic surface-to-surface contact between stem and potting disabled (bonded interface).
- Nonlinear solution with NLGEOM=ON due to fixture compliance; force residual tolerance 0.5%, displacement norm 0.1 mm, achieved within 18–32 increments across cases. Energy balance error <1.5% at convergence.

Mesh refinement and solution checks
- Local size at the neck blend: 0.3 mm; growth rate ≤1.3. Global element count 1.4–1.7M.
- Three-level refinement around the fillet produced a 1.8% Grid Convergence Index (95% confidence) on peak von Mises at the notch root; stem compliance changed <0.8% between last two meshes.
- Contact overclosure at the potting interface averaged 2.4 μm (<0.5% of the smallest element edge), indicating a well-behaved constraint system.

Software quality and benchmarks
- Abaqus/Standard 2023 FD03 with SMP; verified against NAFEMS LE10 bending benchmark (error 0.4% in displacement) and a custom cantilever with an analytical tip-load solution (error 0.3% in stress).
- Model and scripts tracked in Git (repo MS-hipstem-fea, tag v1.7.2). Results are replicable on Windows 11 and RHEL 8; hash-matched output within 0.2% across platforms.

Physical test comparators and data quality
- Eight stems (sizes 1–5, two repeats for size 3) tested on an MTS 858, ISO 7206-4 setup. Load cell uncertainty 1.0%; DIC strain measurement uncertainty 2.2% (calibrated with a 25 mm grid plate). Potting length and load angle measured per specimen; used as inputs to the model.
- Strain gauges at the medial and lateral neck recorded peak strains corresponding to 615–670 MPa computed stress via E; DIC full-field maps used for hotspot ordering.

Uncertainty and sensitivity
- Input variations sampled with Latin Hypercube: E (±3 GPa), potting angle (±0.5°), embedding length (±1 mm), and load magnitude (±1%). The combined output uncertainty on peak stress is 7.6% (RSS of contributions), with alignment contributing ~4.1%, modulus ~3.0%, mesh ~1.8%, and geometry measurement ~1.5%.
- Local one-at-a-time scans confirm friction at the stem–PMMA interface does not affect results under bonded assumption; switching to μ=0.3 contact reduces peak stress by 1.2%, bounded by our acceptance margin.

Validation outcomes and metrics
- Mean absolute percent error: 6.9% at the primary gauge; 8.1% at the secondary. Normalized RMSE across all gauges: 6.2%. Stiffness (slope of load–deflection) within 3.5% of test on average, worst case 4.7%.
- Hotspot ranking by stress amplitude matched DIC-identified maxima for all eight tests. No outliers exceeded the 10% stress tolerance.

Scope and limits of use
- Applies to sizes 1–5 with the current neck geometry, ISO 7206-4/8 style bending between 150–260 N·m. Not to be used for patient gait cycles, fretting, or corrosion-fatigue without additional evidence. Temperature assumed 23±2°C; no creep modeled.

Review independence and traceability
- Independent check by S. Liang (not on the design team) reproduced the size-3 model from the repository and obtained stress within 1.1% and stiffness within 0.6% of our numbers. All assumptions, CAD trims, and test metadata are cataloged in Confluence page FEA-HIP-ISO-BEND v1.7.

Decision
Based on the above, the hip-stem FEA is accepted for design down-select, stiffness substantiation, and hotspot ranking under ISO 7206-4/8 bending for sizes 1–5, subject to operating within the stated bounds. This decision is recorded by the V&V lead (E. Miller) and concurred by the project MDR reviewer (S. Liang). The model is not approved for predicting in vivo fatigue life or for labeling claims outside ISO-style bending without further validation.
