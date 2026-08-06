To: A. Patel, Structures Lead
From: M. Rios, FEA
Subject: Status memo — avionics tray bracket static analysis (P/N 71-56234, Rev C)

Purpose
This note summarizes where the finite element model for the avionics tray bracket stands relative to the load case driving the PDR decision: a 20 g vertical crash pulse with the current 3.2 kg avionics mass. The intent is to inform the go/no-go on releasing the machining drawings for the bracket and backing plate.

Model setup highlights
- Geometry: Imported from CAD Rev C. Fastener holes and fillets retained; cosmetic chamfers and non-load-bearing cable tie features suppressed. Four M6 interface bolts modeled as pretensioned bolt connectors with washers. Backing plate included.
- Materials: 7075‑T6 aluminum for bracket and plate, isotropic elastoplastic. E = 71 GPa, ν = 0.33, yield (0.2% offset) = 503 MPa. Plasticity captured via a Ramberg–Osgood fit to MMPDS 2023 sheet data (n = 12.5, α chosen to match 0.2–1% strain region).
- Loads and restraints: Vertical inertial load equivalent to 20 g applied to the tray via a distributed mass element tied to the tray mounting surface (3.2 kg → 628 N). Bolt pretension set to 8 kN per bolt to reflect assembly torque spec. Tray feet constrained in all directions through the bolt stacks into the chassis reference plane. Friction coefficient in clamped interfaces = 0.2.
- Contact: Augmented Lagrange with friction at tray-to-bracket and bracket-to-plate interfaces; no separation under preload unless local uplift exceeds clamp.

Discretization and solver choices
- Elements: Quadratic tetrahedra (Tet10) with curvature-based refinement. Minimum edge length ~0.6 mm at the 1.5 mm fillets and around bolt holes; ~3.0 mm in far field. At least 5 elements through thickness in the highest curvature zones.
- Nonlinearity: Small-strain plasticity active; kinematics left in small-displacement regime after a trial showed <1% change when geometric nonlinearity was toggled on. Five substeps with automatic stabilization disabled.
- Convergence checks: Force balance within 0.5% of applied. Peak contact penetration under 3 µm. Plastic strain localization restricted to the inner bracket fillet at the inboard fastener.

Mesh refinement study
We ran three systematically refined meshes. The hotspot von Mises at the inboard fillet progressed 378 → 392 → 396 MPa; tray tip deflection progressed 0.84 → 0.87 → 0.88 mm. Extrapolating with a simple Richardson fit suggests an asymptote near 400 MPa. Based on this, remaining discretization error at the hotspot is estimated at ~1% on stress and <0.5% on deflection for the “medium” mesh (used for the rest of the sweeps).

Cross-checks and reasonableness
- Hand estimate: Treating the tray and bracket as an equivalent cantilever of 120 mm with rectangular section matching bracket net thickness gives a nominal bending stress ~360 MPa before local notch effects; the FE result of ~396 MPa at the fillet after including geometry detail is consistent with this.
- Fastener load split: Analytical plate-on-elastic-foundation prying approximation (per Timoshenko method) for the 4-bolt pattern predicts axial loads of [6.5, 5.9, 5.1, 4.8] kN (descending from inboard to outboard). The FE model reports [6.4, 6.0, 5.2, 4.7] kN under the same pretension and external load, within ~5%.

Sensitivity to key knobs
- Friction coefficient: Varying μ from 0.1 to 0.3 shifts the peak stress by −1% to +2% relative to μ = 0.2; deflection changes <1%.
- Material yield scatter: ±5% shift in yield strength modifies the computed margin proportionally; at nominal, the limit-state margin relative to 0.2% offset yield is (503/396) − 1 ≈ 0.27.
- Pretension: Reducing bolt preload to 6 kN increases max stress by ~4% due to slight increase in joint slip; increasing to 10 kN changes stress by <1%.

What looks solid
- The hotspot and global stiffness are stable with mesh refinement, and equilibrium checks are tight.
- Contact behavior is well-controlled with negligible overclosure.
- Independent sanity checks (beam bending and fastener load distribution) land close to the FE predictions.

Caveats tied to scope
- The current model addresses the quasi-static 20 g vertical pulse only. Lateral components, thermal effects, and fastener loosening over time are not included by design for this PDR gate.
- Manufacturing tolerances were not embedded parametrically; the fillet radius is as-modeled from Rev C.

Recommendation
For the 20 g vertical case with the current mass and torque spec, the bracket as modeled shows a 27% margin to first yield at the critical fillet with low numerical scatter and consistent cross-checks. On that basis, I recommend proceeding to release the machined bracket and backing plate drawings for PDR, with the note that any mass increase beyond 10% or a change to a lower bolt torque should trigger a quick re-run using this setup.

If you want me to extend this to the lateral pulse or incorporate temperature effects, I can turn those in the next sprint using the same model backbone.
