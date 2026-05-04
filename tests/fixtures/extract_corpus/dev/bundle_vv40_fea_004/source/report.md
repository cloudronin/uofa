# INTERNAL TECHNICAL MEMO

**To:** Dr. Priya Nambiar, Project Lead — OrthoFrame Tibial Tray Program
**From:** Marcus Elfeld, Computational Methods Group
**Date:** 14 March 2025
**Re:** V&V Status — Finite Element Simulation of Tibial Tray Under Gait Loading (Model Rev. 4.2)

---

Priya,

Following last week's design review I wanted to consolidate where we stand on the simulation credibility picture before the regulatory submission package goes to drafting. The short version: the model is in good shape across most dimensions, but there are a few areas I'd flag for attention. Details below.

---

### Code and Solver Provenance

We are running ANSYS Mechanical 2024 R1 with the Mechanical APDL solver back-end. The element library used (SOLID186 for the CoCr tray, SOLID187 for the UHMWPE insert, and CONTA174/TARGE170 for the tray-insert interface) is well-established and has been exercised extensively in the published orthopedic FEA literature. Internal regression testing against the NAFEMS LE1 and LE10 benchmark problems was completed in January 2025 — both problems passed to within 0.4% of the analytical reference, which satisfies our group's acceptance threshold of ±1%. The solver itself is a commercial product with a documented QMS under ISO 9001; we are not the primary developers, so we rely on the vendor's own verification suite, but we have confirmed the specific build (2024 R1, patch 3) against our benchmark library. This gives me reasonable confidence that numerical errors introduced by the solver itself are negligible relative to other uncertainty sources.

---

### Geometry and Mesh Fidelity

The CAD geometry was imported directly from the STEP file provided by the implant design team (Rev. 4.2, released 28 Feb 2025). One simplification was made: the three fixation peg fillets were reduced from their nominal 0.3 mm radius to 0.5 mm to avoid excessively small elements at those features — this was documented in the model assumptions log. The tibial cortical and cancellous bone geometry was derived from a de-identified CT dataset of a 72 kg male subject, segmented using Mimics 25.0.

A mesh refinement study was conducted using three successive global refinements (coarse: ~180k elements; medium: ~610k elements; fine: ~1.95M elements) plus a targeted local refinement around the anterior keel stress riser. Peak von Mises stress in the CoCr tray converged to within 2.1% between the medium and fine meshes, and maximum interface micromotion converged to within 3.4%. We adopted the medium mesh for production runs as the fine mesh offered no practically significant improvement at roughly 3× the computational cost. The Richardson extrapolation-based grid convergence index (GCI) for peak stress was computed at 4.7%, which we consider acceptable for this application given the dominance of material property uncertainty (discussed below).

---

### Material Characterization and Input Uncertainty

Material properties for the CoCr alloy (ASTM F1537) and UHMWPE (ASTM F648 GUR 1050) were taken from published standards and our in-house coupon test data. CoCr elastic modulus was measured at 218 GPa (n=6, CV=1.2%), consistent with literature. UHMWPE modulus showed more scatter: 0.93 GPa mean with a coefficient of variation of 8.4% across five lots, which is not unusual for this material.

Bone material properties are a more significant source of uncertainty. We used density-modulus relationships from Morgan et al. (2003) applied to the CT Hounsfield data. No subject-specific mechanical testing was performed. A sensitivity study varying cortical bone modulus ±20% (spanning the range reported in the literature) showed a ±14% effect on peak tibial cortex strain and a ±6% effect on tray stress — these ranges are captured in the uncertainty budget.

---

### Boundary Conditions and Loading

Loading was applied per ISO 14243-1 (force-controlled gait cycle), using peak axial force of 2450 N (representing approximately 3.5× body weight for the reference subject) and the corresponding AP shear and flexion moment profiles. The tibial stem was fully constrained at the distal cut surface, which is a simplification of the actual bone-cement interface behavior. We ran a sensitivity check using a distributed spring foundation (Winkler model, k = 500 MPa/mm) in place of the fixed constraint; peak tray stress changed by less than 5%, so the fixed-base assumption is defensible for stress predictions, though it would not be appropriate for bone strain analysis.

The contact at the tray-insert interface was modeled as frictional (μ = 0.04, taken from published UHMWPE-on-CoCr tribology data). A frictionless sensitivity run showed a 9% increase in insert edge stress, which we note but do not consider the bounding case for the primary design metric.

---

### Comparison Against Physical Test Data

This is the most important credibility checkpoint and the one I want to flag most directly. We have strain gauge data from a cadaveric bench test conducted by the Biomechanics Lab in November 2024 (six specimens, same implant geometry, ISO 14243-1 loading). Predicted cortical strains at four gauge locations were compared against the experimental mean values:

| Gauge Location | Predicted (με) | Experimental Mean (με) | % Difference |
|---|---|---|---|
| Anterior cortex, proximal | 412 | 438 ± 52 | −5.9% |
| Medial cortex, proximal | 187 | 201 ± 38 | −7.0% |
| Lateral cortex, proximal | 223 | 209 ± 44 | +6.7% |
| Posterior cortex, proximal | 156 | 148 ± 31 | +5.4% |

All four predictions fall within one experimental standard deviation of the measured mean. The systematic underprediction at the anterior and medial locations is consistent with the fixed-base boundary condition being slightly stiffer than the physical cement mantle — this is expected and acceptable. I would characterize the agreement as good for a single-subject model compared against a six-specimen population, though a reviewer could reasonably ask for broader population coverage.

No direct experimental data exists for peak tray stress or insert contact pressure — these are internal quantities not accessible in the cadaveric setup. We are relying on the strain correlation to build confidence that the load transfer is captured correctly, and then trusting the model for the inaccessible outputs. This is standard practice but worth stating plainly.

---

### Sensitivity and Uncertainty Propagation

Beyond the individual sensitivity checks noted above, we ran a formal one-at-a-time sensitivity study across eight input parameters (bone modulus, UHMWPE modulus, friction coefficient, axial load magnitude, AP shear magnitude, fillet radius, cement stiffness, and element size). Peak tray von Mises stress ranged from 187 MPa to 264 MPa across the full parameter space, compared to the nominal prediction of 221 MPa. The dominant driver is axial load magnitude (±15% load → ±12% stress), followed by bone modulus. These findings are consistent with physical intuition and give me confidence the model is not exhibiting unexpected sensitivities.

A formal probabilistic propagation (Monte Carlo or similar) has not been completed — this is on the roadmap for Phase 2 but was out of scope for the current submission milestone.

---

### Documentation and Traceability

The simulation plan, assumptions log, mesh study report, and comparison data are all stored in the project SharePoint under `/OrthoFrame/FEA/Rev4.2/` with version control via Confluence. The model file lineage (STEP → Spaceclaim geometry → Mechanical project archive) is documented in the model log. One gap I'll flag: the CT segmentation parameters used in Mimics are recorded in a lab notebook but have not yet been formally transcribed into the controlled documentation system — Jess is working on that this week.

---

### Operator and Workflow Considerations

The simulation was set up and run by two analysts (myself and Tariq Osman). Tariq independently re-meshed the geometry from the same STEP file and ran the medium-mesh case; his peak stress result agreed with mine to within 0.8%, which I take as confirmation that the setup is not sensitive to individual analyst choices in meshing strategy. Input files and run scripts are stored in version control (Git, internal GitLab) so the analysis is reproducible. No external users will interact with the model directly, so end-user interface concerns are not applicable here.

---

### Overall Assessment

The model is credibly validated for its intended use: predicting relative stress distributions and strain magnitudes in the tibial tray and proximal tibia under ISO 14243-1 gait loading for a representative subject geometry. The primary limitations are: (1) single-subject geometry limits population generalizability; (2) no direct experimental access to tray stress or insert contact pressure; (3) probabilistic uncertainty quantification is incomplete. None of these are disqualifying for the current submission, but all three should be addressed in the Phase 2 program.

Happy to discuss any of this before the drafting kickoff on the 18th.

Marcus

---
*Computational Methods Group | Revision 1.0 | Distribution: P. Nambiar, T. Osman, J. Whitfield (Regulatory)*
