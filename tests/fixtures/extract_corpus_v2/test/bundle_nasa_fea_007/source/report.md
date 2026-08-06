To: Dana Liu, Avionics Bay IPT Lead
From: M. Ortega, Structures
Date: 06 Aug 2026
Subject: FEA credibility snapshot — avionics bracket (P/N ACB-4213) for PDR

Context and intended use
We built a finite-element model to judge whether the ACB-4213 bracket can fly as designed or needs a geometry change before long-lead release. The analysis supports two decisions: (1) go/no-go on current fillet radii and wall thickness, and (2) whether to carry a friction-reduction coating at the interface. The model is being used for static strength, local strain predictions for gauge placement, and approximate stiffness; detailed vibro response is out of scope until the shaker test data arrives.

Model setup and idealizations
- Geometry: CAD as-designed except threads replaced by smooth holes; fasteners represented by beam elements with pretension. Fillets below 0.5 mm suppressed. The avionics box is represented as a rigid body tied to the bracket interface.
- Material: 7075-T73 aluminum, E = 71.2 GPa (±2 GPa from our coupon set), ν = 0.33, σy = 435 MPa. Bolts: A286 with 1100 MPa proof.
- Interfaces: Contact at the bus interface with roughness-based μ = 0.2 baseline; sensitivity 0.1–0.3 explored. Bolt pretension 6 kN each (±10% sweep).
- Loads/BCs: Quasi-static envelopes from loads team: 12 g vertical, 6 g lateral, 4 g longitudinal applied to the avionics box CG; combined via worst-direction vectoring. Random vibe translated into an equivalent static for local clip evaluation only (3σ integrated); full dynamic is deferred.

Numerics and mesh checks
Abaqus/Standard 2023 FD05. The bracket body meshed with C3D10 tets; near the fillet we enforced 2 elements through thickness. Three meshes were run (global edge 4.0/2.5/1.5 mm). Peak von Mises at the lower lug fillet: 329/318/314 MPa. From Richardson extrapolation the asymptote is ~311 MPa with an estimated mesh-induced bias of ~1.0%. Strain energy change between the two finest meshes is 1.8%. Nonlinear iterations per step <8; max contact overclosure 0.009 mm. No hourglassing or negative pivot warnings.

Comparison to bench data
We ran a simple single-axis pull on an engineering article (Rev B bracket alone) to 5.5 kN. Mid-span deflection: test 0.92 mm vs model 0.98 mm (+6.5%). Rosette at the fillet: principal strain test 1850 με vs model 1740 με (−6.0%). These are within the ±10% band we agreed for PDR-level correlation. Note: the test used dry aluminum-on-aluminum; no coating present.

Input data pedigree
- Elastic properties: 5 ASTM E8 coupons cut from the same lot as the bracket; mean and spread as above.
- Friction coefficient: in-house lap-shear of 7075-T73 to Al 6061 yielded 0.15–0.25; we set 0.2 baseline.
- Bolt preload: torque-tension curve from NASM1312-31 gave 6 kN at 0.95 N·m for our lubrication scheme.

Sensitivity and uncertainty
Local peak stress moves by roughly:
- ±5% E → negligible on stress; ±5% on deflection.
- μ = 0.1 to 0.3 → −3% to +4% on peak stress.
- Pretension ±10% → ±2% on peak stress.
Combining these independent contributors in quadrature gives ~5–7% for stress and ~7–9% for deflection at PDR fidelity. Using the mesh bias above, a conservative 95% band on the fillet stress is 311 MPa ± 25 MPa.

Traceability and reproducibility
All input decks, material cards, and post-processing scripts are in repo aero-structures/avx-bracket at commit 9f3d1a2. Abaqus job file: ACB4213_pdr_v27.inp. Runs executed on Redwood cluster (RHEL 8.6, Intel oneAPI 2023). Bolt pretension implemented via *PRETENSION SECTION; contact via small-sliding penalty. Plot templates saved in the repository for re-runs.

People and review
Primary analyst: 12 years structural FEA on flight hardware (Orion avionics trays, LEO payload mounts); Abaqus and hand-check certification current. Independent check by P. Alvarez, PE, 27 Jun 2026; comments resolved (switched to quadratic tets at fillet; added third mesh level; corrected pretension application order).

Bottom line for PDR
- Strength: With current geometry, predicted peak stress 314 MPa on the medium-fine mesh, 311 MPa extrapolated; margin to yield ≈ 0.40 at limit loads. Acceptable for PDR with noted caveats.
- Stiffness: Model is slightly soft vs test; within tolerance for avionics alignment. No action now.
- Coating decision: Given low friction sensitivity on stress and the test being dry, coating is not required for strength; other disciplines may still want it for wear/corrosion.

Open items to carry
- Formal shaker correlation and mode shape check after TVAC/shaker testing.
- Fretting and micro-slip at the interface not modeled; if wear becomes a driver, we’ll need a refined contact law.
- Threads idealized; if bolt bending or joint slip emerges in test, revisit the fastener model.
