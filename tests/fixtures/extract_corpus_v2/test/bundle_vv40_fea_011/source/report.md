To: A. Patel, Vehicle Structures Lead
From: D. Wong, CAE
Subject: Status update — battery pack front mount bracket FEA (rev B geometry)
Date: 2026-08-06

Quick summary
- Scope: Quasi-static structural response of the front battery pack mount bracket under the 10 g longitudinal event and combined service loads. Geometry per CAD 23-1187B; fastener pattern and stack-up per Dwg 23-1187B-ASM.
- Toolchain: Abaqus/CAE 2022, Abaqus/Standard implicit solver. Nonlinear contact and elastoplastic material enabled. All runs on Linux cluster (Intel Xeon 3.1 GHz).
- Decision tie-in: Go/no-go for EVT bracket release and bolt class selection.

Model details
- Geometry: Solid model imported from NX; small cosmetic radii (<0.5 mm) suppressed except at the inner lobe where stress is known to peak. Bolt holes modeled true to size (10.5 mm). Chassis interface plate modeled as rigid to isolate bracket behavior; compliance of the chassis rails is not included in this phase.
- Materials: Bracket is 6061‑T6. Elastic: E = 69.0 GPa, ν = 0.33. Plastic: true stress–strain from in-house tensile coupons (lot L3207), fitted to a bilinear curve: yield (0.2% offset) = 276 MPa, tangent modulus = 1.5 GPa to 4% true strain. Density 2700 kg/m^3 (for NL-geom stability, not mass effects).
- Fasteners/joints: Four M10 class 10.9 bolts represented with pretension sections (initial preload 18 kN each) and kinematic couplings to nut-bolt shank. Contact between bracket and chassis plate: surface-to-surface, augmented Lagrange, μ = 0.25 (phosphate/oil assumption). Small sliding disabled; finite sliding used.
- Loads/BCs: Bracket base constrained at the chassis plate via the bolt clamping footprint; remaining DOFs of the rigid plate fixed. Pack-side load applied as a distributed pressure on the saddle surface equivalent to 8.2 kN forward and 1.3 kN vertical (worst-case combined per RM-17). Load introduced via a reference point and distributing coupling to reflect fixture.
- Solver controls: Geometric nonlinearity ON. Automatic time incrementation, initial 0.05, min 1e-6, max 0.2. Convergence tolerances default (residual 1e-3). Contact stabilization off; penalty stiffness tuned by default scaling.

Mesh and numerical checks
- Elements: Quadratic tetra (C3D10) throughout. Local refinement around the inner fillet and bolt holes. Element edge size ~6 mm bulk; 2.0 mm at fillets; 1.2 mm along hole chamfers.
- Refinement study: Three meshes (M1/M2/M3). Peak von Mises at the inner fillet: 257 MPa (M1, 2.0 mm), 246 MPa (M2, 1.5 mm), 242 MPa (M3, 1.0 mm). Change M2→M3 = −1.6%. Displacement at the load reference: 0.66 mm, 0.63 mm, 0.62 mm respectively. Based on this, we take M2 as adequate for turnaround; spot-checked with M3 for the 10 g case.
- Element quality: Min Jacobian > 0.55; no inverted elements. Contact chattering suppressed after switching to augmented Lagrange; no artificial overclosure observed.

Results (10 g longitudinal + service vertical)
- Max von Mises in bracket: 242 MPa at inner fillet toe (M3). Local plastic strain 0.12% in a ~1.3 mm^3 volume; elsewhere elastic.
- Bolt utilization: Bolt axial under combined load: 23–31% of proof after preload. Slip not detected at μ = 0.25; interface shear below capacity by factor ~1.7.
- Stiffness: Deflection at the saddle 0.62 mm in the load direction; pitch rotation 0.18°.
- Margin to yield (component): 276/242 = 1.14 on nominal properties. Using the fitted curve, onset of yielding is localized and self-limiting; no gross plastic collapse or snap-through observed.

Sensitivity to key assumptions
- Friction: μ varied 0.20–0.35. At μ = 0.20, local peak stress rises to 259 MPa (+7%); still below yield with margin 1.07. At μ = 0.35, stress reduces to 236 MPa.
- Preload: 15–22 kN per bolt. At 15 kN, more shear transfers via bearing; stress at the inner fillet increases to 252 MPa; minor micro-slip but sticks after 60% of peak load step; no separation.
- Thickness tolerance: −0.5 mm on bracket wall increases peak stress to 268 MPa (near-equal to spec yield). This is the limiting case; recommends holding −0.25/+0.0 on the inner lobe wall during EVT.

Cross-checks
- Hand estimate: Treat the inner lobe as a curved beam with r/t ≈ 1.6; nominal bending stress from the resultant moment gives ~210–225 MPa before notch magnification, which aligns directionally with FEA when including a Kt ~1.15–1.2 due to geometry nuance.
- Alternate constraint: Replaced rigid chassis plate with a 3 mm shell patch tied to the bracket footprint to mimic some compliance; bracket peak stress drops 3–4 MPa, displacement increases 6%. Primary conclusions unchanged.

Recommendations
- Proceed with EVT using class 10.9 hardware and target bolt preload ≥18 kN. Specify μ ≥ 0.25 interface condition (phosphated/oiled) on the drawing to avoid unintended slip.
- Tighten the inner lobe wall thickness tolerance and maintain the as-modeled 2.5 mm radius; do not down-rev the fillet. If procurement requests alternate stock, recheck the 1.5 mm mesh case for confirmation.
- For DVT, consider expanding the analysis to bracket-chassis compliance and full tolerance stack-up once as-built data is available.

Attachments available on request: Abaqus .cae and .inp (M2 and M3), material coupon curves (lot L3207), and post-processing ODBs with field outputs at critical increments.

End of memo. Please advise if additional load cases should be prioritized for the next spin.
