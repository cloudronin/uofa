To: L. Chen, Thermal Systems Lead
From: A. Ruiz, CFD
Subject: Status check — CFD credibility for rack manifold pressure-loss predictions (Rev B)

Quick take
The current CFD setup is giving consistent pressure-drop trends for the Rev B manifold over 200–400 CFM per branch. Against the Rev A bench data at 300 CFM, the model undershoots total Δp by 4.8%. Grid tightening changes Δp by less than 3% from medium to fine. I’m comfortable using this to rank design tweaks and to size the fan with a small guard band. Not ready yet for committing to a spec number without additional test cross-checks.

What we modeled
- Software and model form: Steady RANS with SST (k-ω) in Fluent 2023R2. Second-order spatial schemes, coupled pressure-velocity. Flow is incompressible (Ma < 0.1) and isothermal. No fan wheel modeled; we imposed flow rates to map system resistance.
- Geometry: CAD of Rev B manifold with fillets and chamfers preserved above 0.5 mm. Fastener clearances and gasket lips omitted. No leakage paths included.
- Surfaces: Smooth aluminum with an equivalent sand roughness ks = 12 μm (baseline). 
- Operating points: Three flow partitions (200/300/400 CFM per branch). Inlet turbulence intensity 5%, length scale 0.02 m.

Numerical checks
- Mesh refinement: Poly-hexcore with prism layers to y+ ≈ 1–2 on walls.
  • Coarse: 3.1M cells; Medium: 6.4M; Fine: 13.2M.
  • Δp between medium and fine changed by 2.6% at 300 CFM; extrapolated asymptotic ratio ~1.3, suggesting we’re near the grid-converged regime for pressure loss.
  • Recirculation-zone volume fraction shifted 6.9% from medium to fine; that feature is more mesh-sensitive than Δp.
- Convergence: Residuals < 1e-5 for all equations; mass imbalance < 0.2%; monitor points flat for last 1,500 iterations.

Inputs and boundary conditions
- Outlets set to specified mass flow to hit target CFM; inlet as pressure outlet (backflow guarded with 10% TI).
- Wall roughness sensitivity run from ks = 6–24 μm; see below.
- No parameter tuning to match test data; settings selected a priori.

Cross-check with lab data
- Reference: Rev A manifold tested on the ASHRAE 51 rig, 25 °C air, neoprene gaskets installed. Instrumentation uncertainty reported by the lab: ±3% on Δp.
- At 300 CFM/branch: Test Δp = 230 Pa; model (Rev A geometry replicated following the same setup) = 219 Pa (−4.8%). Velocity at a downstream pitot rake: area-averaged magnitude off by 3.5%, with two near-wall taps off by as much as 12% (likely due to gasket lip not in the model).
- Bookends: At 200 and 400 CFM, Δp errors were −7.0% and −2.1%, respectively, same solver choices. Slope of the resistance curve matches the lab within ~2%.

Sensitivity probes
- Inlet turbulence intensity from 1% to 10% moves Δp by < 1.2%.
- Doubling ks from 12 to 24 μm increases Δp by 3.1%.
- Switching to realizable k-ε reduces Δp by ~2.4% and slightly enlarges the recirculation pocket at the elbow.
- Imposing a fuller inlet profile (1/7th power vs uniform) shifts the branch maldistribution metric up to 5% while leaving total Δp within 2%.

Where it works and known gaps
- Regime: Re ~ 6e4–2e5 in the tight turns; subsonic, mildly separated flow. RANS is expected to capture the dominant losses; corner vortices are present and mesh-sensitive but do not dominate Δp.
- Omissions that could bias low: no leakage around fasteners; gasket intrusion not represented. Expect up to a couple percent extra loss in the physical build.
- The validation point is for Rev A; Rev B differs at the splitter nose and diffuser angle. We used the Rev A cross-check mainly to flag gross bias of the solver choices.

Recommendation
- Use the current model to compare Rev B variants and to set the fan operating point with a modest margin over the predicted Δp at the design CFM.
- Before freezing the spec, run a quick rig test on one Rev B print with gaskets installed to confirm that the ≈5% low bias persists.
- If we need tighter confidence on branch-to-branch flow split, we should local-refine the elbow recirculation zones and repeat the medium/fine comparison for that metric specifically.

Attachments on request: mesh snapshots, monitor histories, and the three sensitivity runs.
