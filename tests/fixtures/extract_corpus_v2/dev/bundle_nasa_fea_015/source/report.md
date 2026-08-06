To: AIT Lead, Solar Array Mechanism Project
From: R. Delgado, Structures and Dynamics
Date: 2026-08-06
Subject: Credibility snapshot for hinge-bracket FEA supporting PDR closeout

Scope and context
We evaluated the finite element model of the 3U CubeSat solar array hinge bracket for two decisions: (1) size the bracket and fasteners for quasi-static qualification loads derived from random vibration, and (2) check that the first flexible mode of the deployed leaf clears 150 Hz. The model covers the Ti-6Al-4V bracket, the 17-4PH hinge pin, and two M3 fasteners; the solar panel itself is represented as a distributed mass and edge stiffness. Thermal preload and on-orbit thermal distortion are not included here.

Model setup and key assumptions
- Geometry is from CAD Rev H, with fillets retained down to 0.5 mm radius. The panel leaf is a mass/stiffness boundary rather than full laminate detail.
- Contact: surface-to-surface with a small initial opening (30 µm) between lug and pin to represent machining clearance; penalty method, k=1e8 N/mm, friction coefficient 0.12.
- Fasteners are pretensioned to 3.5 kN each and tied to the bracket via rigid beams; threads are not modeled.
- Loads: lateral tip force equivalent to 17 g on a 120 g deployed leaf (20.0 N), plus a 1.5 Nm out-of-plane moment; separate eigenvalue extraction to 500 Hz.

Numerics and solver checks
- Abaqus/Standard 2023, quadratic tetrahedra (C3D10) in the fillet and bearing regions, reduced integration hexa (C3D8R) elsewhere. Final mesh has ~1.3M DOF.
- Mesh refinement study targeted the pin–lug interface and bracket fillets: halving element edge length from 1.5 mm to 0.75 mm grew the peak von Mises stress from 312 to 324 MPa (+3.8%); a further local split to 0.5 mm changed the peak to 327 MPa (+0.9%). We treat 0.75 mm as sufficient for decision support.
- Nonlinear iterations converged with residual norms below 1e-6; contact chattering was suppressed via stabilization at 0.2% of critical damping. Energy balance error <0.5%.

Data sources
- Ti-6Al-4V (forged) properties from MMPDS-17: E=113±3 GPa, ν=0.34, yield (room temp) 880 MPa A-basis. 17-4PH H1025: E=200 GPa, yield 1000 MPa.
- Friction: vendor tribology sheet for hard-anodized Ti against stainless, μ=0.12±0.05 (dry). Fastener preload tolerance ±10%.
- CAD and mass properties per MECH-DRW-412 Rev H and ARR-MLI-101 for the deployed mass estimate.

Comparison to bench data
We compared bracket stiffness using a brassboard hinge tested in May: panel tip load vs. tip deflection under the same fixturing. Test slope was 42.0 N/mm; the model predicted 40.5 N/mm (−3.6%). First mode with the brassboard panel measured 178 Hz; the model with equivalent boundary conditions gave 185 Hz (+3.9%). The discrepancy is attributed mainly to uncertainty in μ and clamp torque.

Uncertainty and sensitivity
- A 200-run Latin hypercube varied E(Ti), μ, and preload within the ranges above. Peak bracket stress at the fillet had mean 336 MPa, σ=18 MPa; the 95th percentile was 366 MPa. The corresponding safety margin against room-temperature yield is ~1.4 on stress ratio. When μ is pushed to 0.17 and preload drops 10%, predicted tip stiffness falls by 8% and the first mode by ~5 Hz.
- The model is most responsive to μ in the bearing, then to fastener preload; modulus scatter has a small effect on both stress and frequency over the stated ranges.

Appropriateness for use
Within the envelope of loads used for qualification and for the Rev H geometry, the analysis behaves smoothly under small perturbations. Repeating the solution with the contact penalty doubled and halved moved the peak stress by less than 2% and the first frequency by less than 1 Hz. We did not include fretting, wear-in, or temperature effects; those are expected to bias μ downward in service, reducing stiffness modestly. The mass/stiffness abstraction for the panel is adequate for the hinge decision but will not support panel-level strain predictions.

Results summary
- Peak von Mises in the bracket under the quasi-static load set: 327 MPa at the inner fillet; pin bearing stress below 620 MPa with local plasticity not predicted.
- First flexible mode (deployed) predicted: 187–190 Hz across the μ/preload spread noted.
- Displacement at panel tip under the qualification-equivalent lateral load: 0.49–0.54 mm over the same spread.

Limitations and to-dos
- No thermal gradients or CTE mismatch included; to be handled in the CDR update.
- Panel modeled as a boundary abstraction; laminate detail and hinge leaf flexibility to be included once the panel stack-up freezes.
- The friction model is Coulomb with a single μ; no Stribeck or velocity dependence.

Decision
Based on the above, the hinge-bracket model is accepted for preliminary sizing and first-mode clearance assessments for PDR, subject to updating the friction and preload ranges with as-built test data before CDR. This decision is made by the Structures and Dynamics lead for the Solar Array Mechanism Project.
