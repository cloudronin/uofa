To:     M. Ortega, Vehicle Integration Lead
From:   L. Kim, Structures Analysis
Date:   2026-08-06
Subject: Status memo — Battery Tray Corner Lug FEA (Rev C) for lateral crash case

Summary
We ran an updated finite-element assessment of the A356-T6 cast corner lug on the 18 kg battery tray for the 15 g lateral/3 g vertical crash scenario. The model predicts peak von Mises stress of 198 MPa at the inner fillet of the lug with the current 2.0 mm fillet and M8 bolt pair preloaded to 12 kN each. Using 210 MPa as the allowable (conservative vs. lot-average 221 MPa), the static safety margin is ~1.06. Slip across the tray-to-rail joint remains below 0.05 mm. Overall, the analysis supports design use as-is but leaves little buffer; increasing the fillet to 2.5 mm raises the margin to ~1.18 by our sensitivity sweep.

Model setup and key assumptions
- Geometry: Full 3D of the lug, local section of the tray flange, and two M8 bolt shanks modeled as simplified cylinders with washer-bearing faces. Threads not modeled; preload applied via bolt pretension elements.
- Loads: Crash represented by an equivalent static load with a 1.3 dynamic amplification factor applied to the tray’s CG. Lateral: 14.7 g; Vertical: 3 g. With an 18 kg tray and a 120 mm lateral CG offset from the lug plane, this produces ~650 N lateral and ~130 N vertical per corner plus a torsional couple. Load path captured via MPCs to the tray flange.
- Restraints: Chassis rails represented by kinematic constraints at the mating bolt holes and a grounded rail surface. Symmetry not used due to the torsional component.
- Contact: Augmented Lagrange formulation between tray flange and rail; μ = 0.18 (hardcoat on aluminum, lightly greased assembly not permitted by work instructions). Normal stiffness tuned by a contact compliance study; penalty factor 1.0e7 N/mm avoided spurious overclosure while maintaining negligible penetration (<5 μm).
- Material data: A356-T6 cast aluminum, isotropic elastic-plastic with bilinear hardening. E = 71 GPa, ν = 0.33, σy = 210 MPa (0.2% offset), tangent modulus 1.1 GPa. Property basis from foundry lot 24-03 tensile bars (n = 7; mean yield 221 MPa, COV 6%). Surface finish effects not explicitly modeled; local Kt reflects geometry only.
- Meshing: Quadratic tets in the lug and flange (TET10), 0.9–1.2 mm elements in the fillet region, 3–4 mm elsewhere. Through-thickness minimum three elements at the fillet root. Bolt shanks meshed with 1.0 mm hexa where feasible; transitions handled via tet sweep.

Refinement and numerical checks
- Mesh study: Three grids (h = 1.6/1.2/0.9 mm nominal at fillet). Peak von Mises changed -8.9% (L1→L2) and -4.8% (L2→L3). We adopted the middle mesh (1.2 mm) for turnaround time; expect remaining grid-induced bias on peak stress of ~5%. Contact pressure distributions stabilized by L2.
- Solver settings: Static nonlinear with line search; displacement convergence at 1e-6 m, force residual <1%. Load ramped in 10 steps to help contact settle; no divergence observed.

Correlation with bench data
We compared strain near the inner fillet to a Rev B pull test (single-lug fixture, 2.0 mm fillet, same bolt pattern). At an equivalent lateral force of 2.6 kN and matched preload, the rosette on the tray face read 1750 με; the current model at the rosette centroid gives 1620 με (−7.4%). The Rev B castings were from a different vendor; hardness and microstructure varied slightly, but geometry and shot-peen spec were the same. On balance, this gives reasonable confidence in the load path and joint behavior.

Parameter sensitivity (local)
- Fillet radius: +0.5 mm reduces peak von Mises by ~11%.
- Bolt preload: Dropping to 8 kN per bolt increases peak stress ~9% and introduces ~0.12 mm slip; at 12 kN slip remains <0.05 mm.
- Friction: Reducing μ from 0.18 to 0.12 increases peak stress ~6% and raises shear in bolts by ~8%.

Results and interpretation
- Peak von Mises: 198 MPa at lug fillet, element-averaged. Plastic strain at hotspot <0.2%. Bearing under washers is below compressive yield by ~20%.
- Joint behavior: Micro-slip confined to bolt nearest the CG line of action; no gross sliding predicted.
- Margin: With 210 MPa allowable, FoS ≈ 1.06 on the adopted mesh; accounting heuristically for the 5% mesh bias puts the range at ~1.01–1.11. Moving to a 2.5 mm fillet shifts the range to ~1.12–1.20.

Limitations and actions
- Casting features such as local porosity, chill lines, and surface dents were not represented; these could erode the small margin at the fillet. NDT acceptance currently limits indications but may warrant a notch-factor allowance.
- Temperature effects were held at 23°C; for A356-T6, low-temperature yield tends to increase modestly, which is favorable, but we did not include that uplift.
- Recommend: Increase fillet to 2.5 mm if packaging allows, maintain 12 kN minimum bolt preload in work instructions, and keep μ ≥ 0.18 by prohibiting lubricants at the joint surface. If fillet change is not feasible, consider a 0.5 mm localized radius blend and washer OD increase.

Please advise on priority for implementing the fillet update before the DV2 crash sled build. If schedule does not permit geometry change, we can complete an additional high-resolution mesh pass around the hotspot and run a quick coupon test to firm up the margin.
