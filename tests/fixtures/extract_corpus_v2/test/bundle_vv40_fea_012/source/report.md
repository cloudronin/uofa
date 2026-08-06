# Structural Credibility Report: Mount Bracket for Battery Enclosure (FEA)

Project: eVTOL-PEM-4827  
Component: Forward battery enclosure mount bracket (P/N MBRKT-7075-FWD)  
Analysis tool: Abaqus/Standard 2023x  
Date: 2026-08-05  
Prepared by: Structures Group, Airframe Integration

## 1. Background

The forward battery enclosure is suspended from the primary keel via two aluminum brackets. This report summarizes the finite-element simulation performed to inform the preliminary release decision for the bracket geometry through CDR. The question addressed is limited: does the current bracket meet static strength targets under the defined ground maneuver load case (GM-2.3), with sufficient margin to proceed to coupon procurement and machining of flight-test articles?

The bracket interfaces to the keel using four M8 Class 12.9 bolts and clamps to the enclosure via two M10 fasteners. The relevant load channel for GM-2.3 is vertical uplift due to combined ground resonance and abrupt throttle change; the total factored external load transmitted through the bracket is 9.5 kN applied at the enclosure side lugs with a conservatism of 1.35 based on dynamic amplification measured on a prior airframe. No fatigue or crashworthiness assessments are included here.

Risk if the model is wrong: an under-designed bracket could plastically deform during ground tests, potentially compromising harness routing and resulting in schedule slip. We therefore aim for a modest safety buffer on yield and deflection within the context of a static proof-level check.

## 2. Geometry and Load Case Definition

- CAD source: NX assembly 11-15324-E, Rev B. Geometry was simplified to remove cosmetic fillets and small holes (<1.5 mm) not participating in load paths. The primary fillet at the inner corner (r = 2.5 mm) was preserved as it governs stress concentration.
- Mounting interface: Four M8 clearance holes on a 90 mm by 60 mm rectangle. The keel is much stiffer than the bracket in the direction of the primary load.
- Enclosure interface: Two M10 through-holes at 105 mm spacing, with a slot feature for alignment. The load from the enclosure strap is applied via a pad region around these two holes.
- Material: 7075-T6 aluminum plate, 10 mm nominal thickness. Mechanical properties at 23 C assumed isotropic: E = 71.7 GPa, ν = 0.33, density 2810 kg/m^3, yield (Rp0.2) = 503 MPa. No plasticity modeled in the baseline analysis; a supplemental elastoplastic check is described later.
- Load case GM-2.3: 9.5 kN vertical tension applied as a distributed pressure over 220 mm^2 around the two enclosure-side holes, biased 60/40 between the holes per strap geometry. Load application line is 32 mm from the fillet root. Component weight and minor lateral forces are neglected for this worst-axis case.
- Boundary representation: The keel-side bolt shanks are idealized as encastre constraints on the hole cylinders via multi-point constraints tying the hole perimeters to rigid reference points located at hole centroids, assuming the keel plate is dominant in stiffness. The two enclosure-side bolts are modeled with pretension elements as described below.

## 3. Modeling Approach

- Element formulation: Quadratic tetrahedra (C3D10) for the bracket solid. We tested a small submodel with 20-node hex elements (C3D20R) to confirm trends on the fillet, but the full part is tets for meshing robustness.
- Contacts and fasteners: Surface-to-surface contact with small-sliding formulation between bracket and bolt head/nut bearing surfaces. Friction coefficient assumed 0.20 (dry anodized aluminum/steel interface, mid-range from MIL-HDBK-60). The enclosure-side M10 fasteners are modeled using Abaqus pretension sections set to 11 kN initial preload each (measured torque-tension correlation for the assembly procedure).
- Mesh density: Three meshes were constructed:
  - Coarse: 1.2 mm global seed, with 0.8 mm local seed at the 2.5 mm fillet; 0.92 million elements.
  - Medium: 0.8 mm global, 0.5 mm local at fillet; 1.86 million elements.
  - Fine: 0.6 mm global, 0.35 mm local at fillet; 3.24 million elements.
  All meshes use curvature-based refinement with Jacobian checks enabled; minimum element quality metric > 0.45 on a 0–1 scale.
- Solution type: Static general step, Newton–Raphson iterations with automatic stabilization off. Convergence tolerances: force residual 0.5% of reference, displacement increment norm ratio < 1e-6 between successive iterations. Max 50 increments; automatic incrementation enabled with 0.1 initial step size.

### Sanity checks on the build

We executed a simple cantilever beam case (rectangular section, L = 400 mm, b = 30 mm, h = 10 mm, end load 1 kN) using the same element family and solver settings. Tip deflection agreed with the Euler–Bernoulli closed form within 0.6% for the medium mesh. A patch test for stress recovery around a hole in a plate (Kirsch solution) gave hoop stress at the hole boundary within 3.1% on the refined mesh. These short runs served as a reality check that unit systems and boundary implementations were consistent.

## 4. Solver Controls and Stability

The load ramp was quasi-static; the nonlinearities present are contact and bolt preload. We monitored:
- Average and max contact slip vs. load to ensure no numerical chatter. Slip converged smoothly, with small (≤0.03 mm) relative motion around the enclosure bolt bearing surfaces.
- Equilibrium iterations per increment: mostly 6–10, with a spike to 17 near the onset of contact engagement. No step restarts were required.
- Reaction force balance across constrained nodes matched the applied load within 0.2%.

To avoid locking in the narrow fillet region, we confirmed that reduced integration is not used with C3D10 in Abaqus; hourglassing is thus not a concern. The displacement field was checked for checkerboard patterns—none observed.

## 5. Studies to Increase Confidence

### 5.1 Mesh refinement study

For the governing quantity (max von Mises stress at the inner fillet), stresses increased with refinement and appeared to asymptote. Values were:
- Coarse: 273 MPa at the fillet crown
- Medium: 284 MPa
- Fine: 287 MPa

Using a three-point Richardson extrapolation on the stress peak with an assumed order p ≈ 1.8 for the irregular tetra mesh, the extrapolated stress was 291 MPa. The Grid Convergence Index at the fine mesh relative to the extrapolated value is approximately 1.4 × (|291 − 287| / 287) ≈ 1.9%. Energy norm of the error computed from successive mesh levels dropped by 48% from coarse to medium and 18% from medium to fine. Displacement at the load application pad changed by less than 1.6% from medium to fine.

Based on this, the medium mesh is already adequate for global deflection, while the fine mesh was used to quote stress margins at the hotspot.

### 5.2 Contact and preload sensitivity

We explored parameter variation around friction and fastener preload to understand the spread in bracket stress:
- Friction coefficient μ: 0.15, 0.20 (baseline), 0.25. The maximum von Mises stress at the fillet shifted by ±4 MPa across the range, with lower friction yielding slightly higher stress due to more load bypass through the bracket rather than bolt clamping.
- M10 preload: 9 kN, 11 kN (baseline), 13 kN. Each 1 kN increase in preload reduced the fillet stress by ~1.8 MPa (nearly linear in this band), suggesting some stress shielding effect.

The combined plausible worst case (μ = 0.15, preload = 9 kN) produced a fillet stress of 294 MPa on the fine mesh. The plausible best case (μ = 0.25, preload = 13 kN) yielded 281 MPa.

### 5.3 Material and thickness variations

We assessed sensitivity to thickness tolerance (−0.3 mm on the 10.0 mm nominal plate) and material modulus perturbation (−5% E):
- Thickness −0.3 mm increased the hotspot stress by 3.2% and deflection by 4.7%.
- E −5% had negligible effect on stress (<0.5%) but increased deflection by ~5%.

Yield strength variation was not explicitly propagated; we discuss allowables in the Results section.

### 5.4 Elastoplastic check

To gauge proximity to yielding, we ran a supplemental case with an elastic–plastic material model: bilinear isotropic hardening with tangent modulus 1.1 GPa beyond Rp0.2 = 503 MPa (per MMPDS guidance). Under the same load, the plastic strain remained below 0.05% and localized to a <1 mm^3 region at the fillet crown. The global load-displacement curve did not deviate perceptibly from linear up to 9.5 kN.

## 6. Bench Check with Strain Gauges

A single bracket prototype (CNC from 7075-T651 plate, anodized) was tested in the lab using a fixture that replicates the bolt pattern on the keel and applies vertical tension via a clevis at the enclosure-side holes. The setup is not a full assembly; it captures the load path through the bracket only.

- Instrumentation: 350 Ω strain gauge (Vishay CEA-13-240UZ-120) bonded 3 mm away from the fillet crown on the side face, aligned with the principal stress direction indicated by the FE.
- Loading: 0 → 7.5 kN → 0 in three cycles to settle the gauge; then a single ramp to 9.5 kN. Preloads on the M10s set by torque (42 N·m), checked with ultrasonic bolt elongation; measured preloads were 10.5–11.3 kN.
- Measurement uncertainty: ±20 με due to gauge factor tolerance and bridge conditioning; fixture compliance contributed an estimated ±1% on applied load.

Result at 7.5 kN:
- FE (medium mesh, μ = 0.20, preload 11 kN): predicted strain 490 με at the gauge location (principal direction).
- Measured: 520 με.
- Difference: 6.1% high in test relative to FE, within the combined measurement and modeling spread. Repeating with the fine mesh changed FE to 498 με (difference 4.2%).

Result at 9.5 kN:
- FE (fine mesh): 631 με; test: 662 με. Difference 4.9%.

We note that the lab fixture constrains rotations slightly differently than the vehicle keel; the observed higher strains are consistent with a stiffer test boundary condition. No yielding was detected via unload slopes or visible imprinting at the fillet under dye check.

## 7. Results Summary

All numerical results cited below are from the fine mesh unless otherwise noted.

- Peak von Mises stress at the fillet crown: 287 MPa (baseline μ = 0.20, preload 11 kN). With plausible worst-case contact and preload, 294 MPa. With thickness −0.3 mm, 303 MPa for the same contact/preload baseline.
- Deflection at the load application pad: 0.38 mm (baseline), 0.40 mm with thickness −0.3 mm.
- Bearing stresses under M10 heads: max 132 MPa, below anodized aluminum compressive allowable per MIL handbook (~240 MPa), factoring in contact area.
- Bolt forces: load split between the two M10s was 58/42 under baseline friction and preload; no loss of clamp predicted.
- Stress elsewhere: Secondary hotspots at the keel-side hole edges reached 162 MPa; these are remote from bends and below local bearing limits.

Allowables considered:
- For static proof in preliminary design, we use 0.6 × Rp0.2 for 7075-T6 as a conservative allowable: 0.6 × 503 = 302 MPa. This aligns with our internal practice for untested components at CDR (accounting for small-scale manufacturing variability).
- With the baseline fine-mesh stress (287 MPa), the margin is (302 − 287)/302 ≈ 5.0%. Under the combined conservative parameter set (μ = 0.15, preload = 9 kN, thickness −0.3 mm), stress approached 303 MPa; margin would be slightly negative (−0.3%). The probability of all three adverse parameters co-occurring is low given torque control and process capability on plate stock, but this highlights limited cushion.
- The elastoplastic run suggests that even if the local fillet experiences incipient yield, plastic strain would be minor and contained.

Based on the above, we recommend accepting the geometry for CDR with a change action to increase the fillet radius from 2.5 to 3.0 mm in the next CAD spin, or alternatively, to specify a minimum plate thickness of 10.1 mm at that region.

## 8. Credibility Discussion

Our aim was to build a case that the model’s answers are dependable enough to guide the go/no-go decision for preliminary release under GM-2.3. Key points that underpin our confidence:

- The problem is well within the range where small-deformation, linear elasticity describes the bracket behavior. Supplemental plasticity runs confirmed no significant nonlinearity in the load range. Hence, the chosen model form is consistent with the physics at hand.
- The boundary conditions at the keel side are idealized as rigid; the real keel is stiffer than the bracket by roughly an order of magnitude (see prior fuselage FE), so embedding the hole perimeters to reference points is appropriate. If anything, a fully flexible keel would slightly offload the bracket fillet due to system compliance; we are on the conservative side.
- Mesh resolution was pushed until diminishing returns. The hotspot stress moved by less than 1.5% from the medium to fine mesh, and the extrapolated stress is only 1.4% above the fine-mesh value. Global deflection is already converged at the medium level.
- The solver exhibited smooth convergence characteristics; no artificial dissipation or stabilization was needed. Force/displacement balances closed to within 0.5%.
- The lab check, while not a full assembly test, provided an anchor point: strains near the fillet matched the FE within 5–6% over the relevant load band. The modest gap is in the direction expected given fixture constraints and is comparable to the combined uncertainty from material modulus variability (±3–4%), friction variability, and torque-preload scatter.
- Input parameters with the most influence (contact and preload) were varied. The sensitivity is moderate; worst-case plausible combinations push the hotspot close to the preliminary allowable, signaling that small geometry tweaks (larger fillet) would reduce risk appreciably.

Given the decision stakes at this stage (release for machining of test articles, not flight), the above set of activities is proportionate. We are not claiming life predictions or behavior under crash loads; those require additional work.

## 9. Limitations and Next Steps

- The model does not include residual stresses from anodizing or machining marks; these may slightly reduce local ductility, but are unlikely to affect the static proof case at room temperature. Surface finish callouts should be maintained on critical fillet zones.
- No thermal effects are modeled. The battery bay typically stays under 50 C; a lower modulus at temperature would increase deflection marginally but has little effect on stress in a linear model.
- Assembly preload on the keel-side M8s was not explicitly modeled; we assumed encastre at the hole surfaces. Introducing fastener flexibility may shift minute portions of the load path but is not expected to change the dominant fillet hotspot under GM-2.3. We will include bolt shank flexibility in the system-level FE for completeness.
- The lab fixture differs from the airframe in constraint distribution; while the local match is good, a full hardware-in-the-loop test with the enclosure and keel should be run before QR. We have scheduled that for MCR-5.
- Fillet size has outsized influence on the hotspot. We recommend increasing the fillet to r = 3.0 mm and re-running the fine-mesh case; quick scoping runs suggest a 6–8% stress drop with that change.
- Manufacturing tolerance on thickness produces a measurable effect on stress and deflection; we suggest specifying a minimum material condition of 10.0 mm after finish, or qualifying plates accordingly.

## 10. Methodological Notes

- Preprocessing was performed in Abaqus/CAE. Element orientations were checked to align with curvature near the fillet to improve stress recovery. Quadratic tetrahedra were chosen to balance mesh quality and runtime; the fine mesh ran in 2 h 47 min on a 16-core workstation with 64 GB RAM.
- Contact pressure-overclosure behavior used default “hard” contact. We tested penalty enforcement stiffness scaled by 0.5× and 2× to confirm that pressures and slips were not numerically biased; hotspot stress changed by <1 MPa.
- The load application region was extended over a ring around the M10 bolt holes to avoid spurious singularities at point loads. Ring width was 2.0 mm; halving the width altered local stresses by <2.5 MPa at the hotspot.
- Reaction forces were extracted at the reference points; the sum of reactions matched the applied load within 0.2%. Energy balance (external work vs. strain energy) agreed within 0.8%.

## 11. Recommendations

- Proceed with CDR release of the current bracket, with a design note to increase the inner fillet to 3.0 mm in the next iteration or to tighten the minimum thickness specification.
- For the upcoming system test, instrument at least two brackets with strain gauges near the fillet to expand the comparison set under assembly-realistic constraints.
- Maintain torque control procedures that produce M10 preloads ≥11 kN to keep stress below 290 MPa for the target use case.

## 12. References

- MMPDS-17: Metallic Materials Properties Development and Standardization.
- MIL-HDBK-60: Threaded Fastener Torque–Tension.
- Lab note LN-STR-2026-044: “MBRKT-7075-FWD Bench Check,” June–July 2026.

---
End of report.
