To: Priya Shah, Spine Program Lead
From: L. Nguyen, CAE
Subject: Status memo — cage compression FEA vs bench data (VV40 touchpoints)

Context and what we’re trying to answer
We used a solid-mechanics model to estimate the highest combined stress in the C5–C6 interbody PEEK cage during axial compression representative of ASTM F2077 fixture loading. This is intended to screen Rev B geometry before we commit to full matrix testing. The decision hinge is whether the stress stays under the material’s allowable with a reasonable buffer. Early on we stated the limit as 95 MPa (per Invibio data sheet, room temp). During review last week we adopted 110 MPa as the working cap assuming a 1.5× margin on static proof (note this discrepancy; see Closeout).

Model setup and simplifications
- CAD: porous lattice left as homogenized solid volume (no strut-level detail). Footprint 14×12 mm, height 7 mm, 7° lordosis.
- Elements: second‑order tets in the cage body; rigid platens modeled as analytical surfaces.
- Material: PEEK, E = 3.6 GPa, ν = 0.38, rate‑independent. No creep or plasticity included.
- Interfaces: frictional contact cage–platen with μ = 0.2 baseline; small sliding, penalty enforcement.
- Loads: quasi‑static compression to 3.0 kN; inferior platen constrained in all DOF, superior platen driven in Z.
- Outputs of interest: von Mises at the posterior inner fillet, and average compressive strain in the anterior wall.

Discretization check (local hot-spot focus)
Three meshes were run: ~180k, 420k, and 1.1M DOF. Peak stress at the target fillet shifted less than 3% between the two finer models (112 vs. 114 MPa). Separately, my scratch notes from the morning run say the coarse-to-medium change was 7.4% at 3.0 kN; I will re‑run to reconcile because the original plot shows a 4.9% swing at that location. Strain energy and reaction force matched within 1% across meshes, so global response is stable. We did not chase contact patch resolution beyond ensuring ~4 elements across the nominal footprint.

Sensitivity “spot checks”
- Modulus: ±15% about 3.6 GPa changed the hot‑spot stress by ~2%. In the follow‑up with the 420k mesh the same sweep showed a 5–6% effect, likely tied to contact stiffness linearization.
- Friction: going from μ = 0.1 to 0.3 moved the peak stress by 10–12% (earlier email said “negligible”; that was based on a single 0.2→0.25 step and appears optimistic).
- Fillet radius: +0.25 mm at the posterior inner corner drops the computed stress ~9%.

Bench comparison (ASTM‑style compression, static)
We ran five static compressions on the Rev B 14×12×7 mm PEEK cages using an Instron 5969 (10 kN load cell), polished platens, no saline. Digital image correlation (subset 19 px, 75% correlation) gave surface strains on the anterior wall; we back‑calculated an equivalent von Mises using Hooke’s law (acknowledging limitations). Nominally, the FEA reaction force vs. platen displacement overlays the median test within 5% up to 3.0 kN. Peak field value from DIC corresponds to 118 ± 6 MPa, while the model predicts 112 MPa at the posterior fillet. However, when we align by local strain instead of machine stroke, the difference widens to ~12–18%, likely due to bedding‑in and fixture tilt not represented in the model. Test repeatability was decent (COV ≈ 4% on force at 1.5 kN). No plastic offset observed in test up to 3.0 kN.

What this means for the gate
- The analysis suggests we’re at or just beyond the original 95 MPa cap but under the later 110 MPa threshold at 3.0 kN. Given the friction sensitivity and the unresolved 7% vs. 5% mesh delta, I’d keep this as a screening‑level green with a caution flag on contact modeling.
- The static compression behavior is captured reasonably in a global sense; local fields are directionally consistent but not tight if we use strain‑based alignment.

Open items before design freeze
- Reconcile the mesh‑study numbers and publish the final figure of merit at 3.0 kN.
- Repeat the friction sweep with refined contact discretization.
- Add one variant with a 0.25 mm larger posterior fillet to confirm the ~9% stress drop is robust.

Closeout
The allowable discrepancy (95 vs. 110 MPa) needs program‑level confirmation. If we must hold 95 MPa, the larger fillet or a 16×12 footprint should be considered immediately; if 110 MPa stands, Rev B can proceed to the torsion and shear cases (not covered here) while we tighten the mesh/contact items above.
