Appendix E. Detailed Numerical Logs (Extracts)

Steady MRF case at 3000 rpm, 4 L/min (fine mesh)
- Initialization: hybrid init; residuals start O(1).
- Solver settings: coupled momentum-pressure; pseudo-transient with CFL ramp to 20; under-relaxation 0.7 for k, ω.
- Iterations: 1450 to reach residuals < 1e-6; last 200 iterations H changed from 111.06 to 111.00 mmHg.
- Mass imbalance: 0.04%; monitor on volute outlet surface stabilized within 0.05%.

Transient sliding-mesh hemolysis at 2400 rpm, 4 L/min (medium mesh)
- Time step 1e-4 s; sub-iterations per step 10–15 to reduce residuals below 1e-5.
- Monitors: τ99 on blade TE cell peaked at 450 Pa; volume-averaged D increased linearly after 0.2 s; last 4 blade-pass periods consistent within 1.8%.
- Pathline integration: 200k seeds at inlet; RK-4 with adaptive sub-stepping; failed integrations < 0.2%; seeds re-emitted every 50 steps to maintain statistics.

Manufactured solution test
- Grid spacing h = {1.0, 0.5, 0.25} mm on a cube; L2 error norms E(h) = {2.5e-2, 6.3e-3, 1.6e-3}; observed order 1.98.

Appendix F. Additional Sensitivity Sweeps

- Turbulence model constants: varying β* by ±10% changed H by < 0.4%, NIH by +6%/−4%.
- Wall roughness: imposing equivalent sand grain roughness k_s = 1 μm increased NIH by 2%, negligible H impact.
- Inflow turbulence intensity: 3% vs 7% changed NIH by < 3%, H by < 0.2%.
- Tip clearance: 60 μm vs 100 μm changed H by −3.2% and NIH by +14%.

Appendix G. Independence and Roles

- Case setup: Analyst A (5 years CFD, 2 pumps).
- Mesh build: Analyst B (Meshing specialist).
- Independent rerun: Analyst C (separate team).
- Experimental lead: Engineer D (not involved in CFD).
- External reviewer: SME E (turbomachinery, not on program).

Appendix H. Data Availability

All input decks and data are located at:
- Internal Git: git://eng/lvad-cfd/hem_v3.4
- Storage bucket: s3://lvad-data-archive/v3p4/
- Container image: registry.eng/containers/lvad-cfd:3.4.7

Access requires VPN and read permission to the MedDev/CFD group.
