# Appendix: Supporting Details

This appendix provides supporting numeric details referenced in the main report. Values are rounded for readability.

## A1. Mesh Characteristics and Convergence

- Coarse: 5.2 million cells, 30 prism layers, first-layer height set for y+ ≈ 1.2 on blades.
- Medium: 8.7 million cells, same layering, refined tip clearance and trailing edges; y+ ≈ 1.0.
- Fine: 14.6 million cells, additional hub fillet refinement; y+ ≈ 0.9.

Quality metrics:
- Max skewness < 0.35 across all meshes.
- Min orthogonality > 0.21.
- Max aspect ratio in prism layers < 180.

Convergence (1600 RPM, fine mesh):
- Iterations: 2800 to reach torque/Δp plateau.
- Residuals: continuity and momentum ≤ 1e-6; k and ω ≤ 1e-7.
- Mass imbalance: 0.0005 kg/s vs. 1.20 kg/s nominal flow (0.04%).

GCI summary (1600 RPM):
- Apparent order p ≈ 2.1 for Δp; 1.9 for torque.
- Extrapolated zero-grid Δp only 0.6% above fine-mesh Δp.

## A2. Transient Cross-Check

Sliding mesh setup:
- Time step: 2° per blade passage (3.6e-4 s).
- Total simulated time: 10 revolutions after 3-revolution spin-up.
- Spatial discretization: same as fine mesh.

Result:
- Phase-averaged Δp = 329 Pa vs. 332 Pa (steady MRF).
- Torque within 1.4% of steady prediction.
- Phase variation amplitude ±3.2 Pa.

## A3. Sensitivity Runs

- Turbulence model:
  - SA: Δp = −1.6% vs. SST; smoother separation at hub, slightly earlier loss onset.
  - RSM: Δp = +0.8% vs. SST; better secondary flow resolution but higher cost.
- Roughness: ks increased to 45 µm on shroud reduces Δp by 0.9%.
- Inlet TI: 1% → 5% increases Δp by 0.5%.
- Tip gap: 0.60 mm raises Δp by 0.7%; 0.80 mm lowers by 0.7%.

## A4. Experimental Uncertainty Summary

- Differential pressure transducer: ±0.25% FS (500 Pa) → ±1.25 Pa; combined with Setra check yields ±1.6% (k=2) on Δp considering tap placement and repeatability.
- Flow rate: nozzle method ±1.2% (k=2).
- RPM: ±0.2%.
- Temperature: ±0.5°C; density propagated into Δp normalization.
- Swirl angle at measurement plane: < 5°, impact on nozzle coefficient within published corrections.

## A5. File Traceability (SHA256)

- Geometry (STEP): 0e3a…d1c2
- Mesh (fine): 8b91…44ef
- Fluent case (fine, 1600 RPM): 3c77…aa02
- Journal script: 92b6…11d9
- Post-process notebook: cfe0…6b7b

Hashes are provided in full in the repository tag amca-254-v3.

## A6. Peer Review Notes (Extract)

- Reviewer requested:
  - Addition of transient check at 1600 RPM to justify MRF use.
  - Extension of lead-out duct by 0.5D to minimize reflection at outlet.
  - Documentation of inlet turbulence measurement method and value.

All requests addressed in this revision.

## A7. Analyst Training and Tool Chain

- Lead analyst completed “Rotating Machinery CFD Masterclass” (2025) covering SST and RSM best practices, tip clearance modeling, and AMCA 210 alignment.
- Tool chain fixed to Ansys 2024 R1; environment module file stored; nightly regression confirms laminar duct case stability within 0.1% over the past quarter.

## A8. Additional Plots and Tables

- P–Q curve overlay with error bars (not shown in text): CFD points with ±2.3% model band; test points with ±1.6% measurement band.
- Residual and monitor histories: torque and Δp flat over last 500 iterations.
- y+ histogram: blade surfaces median 1.05; 95th percentile 1.8.

End of Appendix.
