To:    LEO Deck IPT Lead
From:  S. Ortega, Structures Analyst
Date:  06 Aug 2026
Subj:  Status memo — FEA credibility for Equipment Deck under quasi-static launch loads

Scope and intended use
We built a finite-element model of the avionics equipment deck (aluminum honeycomb panel with bonded facesheets and twelve M6 fasteners to the ring frame) to support preliminary margin calls for the LV-induced quasi-static load cases X+, Y+, and Z–. The current intent is to use the model for early sizing and fastener pattern vetting, not for the final loads certification package.

Model setup and inputs
Geometry was derived from CAD rev. P9; fillets <1.5 mm were suppressed. The panel is modeled as layered shells with equivalent orthotropic properties; the ring frame is a solid mesh in the joint regions and shells elsewhere. Bolts are represented as beam elements tied to kinematic spiders at the hole perimeters, with pretension of 2.8 kN each.

Material properties: facesheets were entered as E = 71.7 GPa, ν = 0.33, σy = 345 MPa with a bilinear hardening slope of 1.2 GPa, based on supplier “7075-T6” datasheet. The core was taken as 5052-H39, out-of-plane E3 = 0.85 GPa per Hexcel tables. We also referenced a set of in-house coupons pulled last quarter; those report 7050-T7451 facesheets with E = 72.4 GPa and σy = 455 MPa. We used the lower values to be conservative, but that mismatch should be resolved before downstream reuse.

Loads and constraints
Quasi-static accelerations were mapped from the LV ICD (8.0 g axial, 2.5 g lateral). The deck-to-frame attachment is represented by no-separation contact with μ = 0.2 and bolt pretension as above. Earlier model notes describe the same interface as tied, without friction; we removed that tie in r12 because it over-stiffened the joint and underpredicted local slip.

Solver and discretization checks
Analyses ran in Abaqus/Standard. The header in the archive lists Abaqus 2022 HF5; a screen cap in the appendix slide deck shows 2021. We used reduced-integration shells and quadratic tets around the fasteners. A three-level mesh refinement around the bolt circle was exercised: element edge ~2.0 mm, 1.2 mm, and 0.7 mm. Peak von Mises at the critical fastener bore reported 198 MPa, 212 MPa, and 225 MPa respectively; that is a 6.4% change between the last two meshes. Extrapolated Richardson error suggests ~1.8% discretization uncertainty in the stress hotspot, but given the 6.4% delta, I am not fully convinced the asymptotic regime was achieved.

Correlation to test
We compared Z– case displacements to the static load test on the EM panel conducted in Bay 12. Midspan out-of-plane deflection at 8 g matched within 5.2%. Strain at gage SG-07 near the SW fastener line was off by as much as 12% (test higher). The test setup used 3.0 kN bolt torque; the model currently assumes 2.8 kN pretension. That likely explains part of the bias.

Sensitivity and confidence bounds
One-at-a-time perturbations were run: ±10% on facesheet E and ±0.5 kN on bolt pretension. Midspan deflection shifted 3.8% per –10% E and 2.1% per –0.5 kN preload. For the hotspot stress, the model is more responsive to pretension (≈7% per –0.5 kN) than to E (≈1.5% per –10% E). Combining the mesh-change effect, test measurement repeatability (±2% from EM report), and input scatter, I estimate a 95% band of roughly ±9% on the displacement prediction and ±12–15% on local stress. Note: an earlier draft stated ±6% for stresses; that predated the friction/contact change.

Limitations and open items
- Material pedigree: the coupon program reports 7050-T7451 while the CAD and BOM point to 7075-T6; we used the lower property set, but the inconsistency introduces avoidable uncertainty.
- Joint modeling: results are sensitive to bolt pretension and contact friction. The model says μ = 0.2; the test log did not record μ, and earlier runs used a tied interface.
- Mesh near fastener bores may still be too coarse; the 6.4% change between last two meshes is larger than desirable for local stresses.

Decision
Based on the above, I judge the current deck model accepted for preliminary sizing and fastener layout trade studies, subject to: using 7075-T6 properties unless/until BOM changes, keeping to quasi-static load cases from the current ICD, and not using the model to release flight margins at fastener holes. It is not approved for certification of local stress allowables or for sign-off of detailed bolt sizing. Decision recorded by S. Ortega with concurrence from the Deck IPT lead on 06 Aug 2026.
