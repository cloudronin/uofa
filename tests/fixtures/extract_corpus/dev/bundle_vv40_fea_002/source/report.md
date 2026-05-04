# INTERNAL TECHNICAL MEMO

**To:** Dr. Priya Nambiar, Project Lead – Structural Integrity Program
**From:** Marcus Ellenbogen, V&V Engineer
**Date:** 14 March 2025
**Re:** FEA Credibility Status – Titanium Acetabular Shell Model (Rev. C)
**Project:** HipSecure™ HA-7 Implant Platform

---

## Purpose

This memo summarizes the current verification and validation standing of the ABAQUS 2023.HF4 finite-element model used to predict contact pressure distribution and peak von Mises stress in the HA-7 acetabular shell under physiological loading. The intent is to support the upcoming design review gate. Several areas remain deferred to Phase 2 — those gaps are noted explicitly below.

---

## Scope and Intended Use

The model was built to answer a specific engineering question: does the Ti-6Al-4V shell exceed 80% of the endurance limit under worst-case single-leg-stance loading at a 70 kg patient body weight? The simulation outputs contact pressure maps on the UHMWPE liner interface and peak principal stresses at the shell rim. These outputs are the primary quantities of interest (QoIs).

The model is **not** intended for predicting fatigue crack propagation or cement-mantle behavior — those use cases fall outside the current scope and would require separate validation evidence. This distinction matters when reading the confidence statements below.

---

## Model Description

The geometry was imported from the CAD master (SolidWorks 2024 SP2, revision C3) and meshed in ABAQUS/CAE using second-order tetrahedral elements (C3D10) throughout the shell body, with a structured hex layer (C3D8R with enhanced hourglass control) at the bone-implant interface region. The liner was meshed with C3D10H hybrid elements appropriate for the near-incompressible UHMWPE material.

Contact between liner and shell is modeled with a hard-contact normal formulation and a penalty-method tangential stiffness (friction coefficient μ = 0.07, sourced from published tribology literature for dry Ti/UHMWPE pairs — wet-condition data from the vendor is still outstanding and has been flagged as a Phase 2 item).

---

## Mesh Refinement Study

A three-level refinement study was completed on the shell rim region, which is the highest-stress zone. Element edge lengths were stepped from 1.2 mm (coarse) → 0.6 mm (medium) → 0.3 mm (fine). Peak von Mises stress values at the critical node cluster were 312 MPa, 334 MPa, and 339 MPa respectively, yielding an apparent order of convergence of approximately 1.8 — consistent with the C3D10 element's theoretical order. The Richardson-extrapolated value is 341 MPa, and the Grid Convergence Index on the fine mesh is 0.9%, which we consider acceptable for this application. The medium mesh (0.6 mm at the rim) was selected for production runs as a balance between accuracy and runtime.

---

## Material Representation

Ti-6Al-4V elastic properties (E = 114 GPa, ν = 0.33) were taken from ASM Handbook Vol. 2 and are well-established. The UHMWPE nonlinear stress-strain response was fit to compression test data from our materials lab (5 specimens, GUR 1050 resin, gamma-sterilized). The curve fit uses a two-term Ogden model; residuals between fit and test data are below 3% across the strain range of interest (0–15%).

One gap worth flagging: temperature-dependent property variation has not been incorporated. Intraoperative temperature excursions during insertion are unlikely to affect the long-term stress state, but this has not been formally assessed. Deferred to Phase 2.

---

## Loading and Boundary Conditions

The applied load vector (2.5× BW, directed at 16° medial from vertical) follows ISO 7206-4:2010 test geometry. The femoral head is represented as a rigid analytical surface. Cortical bone backing is modeled as a fixed constraint on the outer shell face — this is a simplification; actual bone stiffness varies patient-to-patient. Sensitivity to backing stiffness was checked by running two bracketing cases (rigid vs. 15 GPa cortical modulus), and peak shell stress changed by less than 4%, so the fixed constraint is judged acceptable.

---

## Code Verification Activities

The ABAQUS solver version in use (2023.HF4) has been through our internal qualification protocol per our SOQ-FEA-003 procedure. This included running the NAFEMS LE1 and LE10 benchmark problems — computed stresses matched reference solutions within 0.4% and 1.1% respectively. We also ran a Hertzian contact patch benchmark; the computed peak pressure agreed with the analytical solution to within 2.3%. These checks give reasonable confidence that the solver is performing correctly for the element types and contact formulations in use.

---

## Comparison Against Physical Test Data

Bench testing of the HA-7 shell under ISO 7206-4 loading was completed in February 2025 by our test lab (report TL-2025-017). Strain gauges were bonded at three locations on the outer shell surface. Predicted strains from the FEA at those gauge locations were 1,840 με, 960 με, and 420 με; measured values were 1,790 με, 1,010 με, and 390 με. The differences are 2.8%, 5.2%, and 7.7% respectively. The largest discrepancy is at the gauge nearest the fixation screw hole, which is a stress-concentration region where gauge placement uncertainty is highest — this is a plausible explanation but has not been formally quantified.

Overall, the model-to-test agreement is considered adequate for the intended use, though it falls short of what we would want for a fatigue life prediction application.

---

## Uncertainty and Sensitivity

A one-at-a-time sensitivity study was run varying: applied load magnitude (±15%), friction coefficient (±50%), and UHMWPE modulus (±10%). Peak shell stress was most sensitive to load magnitude, as expected — a 15% load increase drove a 14% stress increase, approximately linear. Friction coefficient variation had minimal effect on shell stress (<2%) but had a meaningful effect on liner contact pressure distribution (up to 11% change in peak pressure). This is noted as a risk for liner wear predictions, which are a downstream use case.

A formal uncertainty propagation (e.g., Monte Carlo or polynomial chaos) has not been performed. Given the linear sensitivity behavior observed, engineering judgment is that the one-at-a-time approach is sufficient for the current design-review purpose, but this should be revisited if the model is used for probabilistic fatigue assessment.

---

## Items Explicitly Out of Scope / Deferred

- **Vendor friction data (wet conditions):** Not received. Dry-condition literature value used. Phase 2.
- **Temperature-dependent material properties:** Not assessed. Phase 2.
- **Fatigue life prediction validation:** Outside current model scope.
- **Probabilistic uncertainty quantification:** Deferred pending decision on whether probabilistic design margins are required.

---

## Summary Judgment

For the specific intended use — screening peak stress against the endurance limit threshold under the defined loading scenario — the model is considered adequately credible. The mesh convergence is well-characterized, the solver has been checked against benchmarks, and the strain gauge comparison shows agreement within ~8% at the worst location. The primary open items (wet friction data, temperature effects) do not materially affect the QoIs for this use case.

Recommend proceeding to design review with the understanding that the model scope is limited as described above.

— M. Ellenbogen
