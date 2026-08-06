To: R. Patel, AHU Upgrade Program
From: L. Nguyen, CFD Lead
Subject: Status memo — CFD of elbow + diffuser downstream of 1.5 kW axial fan
Date: 06 Aug 2026

Quick read
We’ve run a steady CFD campaign to judge whether the new elbow/diffuser arrangement will meet the pressure recovery target without excessive swirl into the filter bank. The analysis is on track for decision support on layout, with mesh-independence checked and credible wall treatment. Key findings: predicted diffuser recovery 0.73 ± ~0.02 at 2.5 m3/s, swirl number at filter face <0.18, and no large-scale unsteadiness observed in the steady runs. Items to watch: separation bubble at the elbow outer wall is sensitive to near-wall resolution; results may be conservative in that region with steady RANS.

What we modeled
- Geometry: 400 mm round inlet, 90° mitered elbow (R/D = 1.2), 3.2× area ratio conical diffuser (7° half-angle), followed by a 900×600 mm plenum. A 12-blade axial fan (Ø 450 mm) is upstream of the elbow; blades are simplified to constant thickness, zero tip clearance.
- Operating point: Q = 2.5 m3/s at 20 °C; air treated as incompressible (ρ = 1.18 kg/m³, μ = 1.85e-5 Pa·s).
- Boundaries: Velocity inlet with top-hat profile; turbulence intensity 5%, turbulent viscosity ratio 10; outlet fixed static pressure at 0 Pa gauge. Rotating region around the fan at 1450 rpm using a steady rotating-frame (MRF) approach; frozen rotor interface.

Numerics and settings
- Solver: Ansys Fluent 2023 R2, double precision, pressure-based, steady.
- Turbulence closure: k–ω SST with curvature correction off; production limiter on.
- Discretization: second-order upwind for momentum and turbulence, least-squares cell-based gradients, second-order pressure.
- Coupling: SIMPLEC with under-relaxation tuned to reach sustained residual reduction.
- Wall treatment: automatic near-wall modeling; we targeted y+ ≈ 1–3 on walls in elbow/diffuser, y+ 15–40 acceptable on far plenum surfaces. Uniform roughness not applied (assumed smooth galvanized sheet).

Grid and convergence hygiene
- Mesh: hybrid poly-hexcore (ICEM + Fluent poly); boundary layer with 12 prism layers, first cell height 0.05 mm, growth 1.2. Medium grid: 9.7 M cells.
- Two additional grids: coarse 4.1 M, fine 21.3 M (same topology, refined by factor ~1.3 in each direction in the elbow/diffuser and rotor tip region).
- Quality: min orthogonal quality 0.14 on the coarse (worst at elbow lip), 0.19 on medium, 0.24 on fine; max non-orthogonality <68° on fine.
- Iterative behavior: on medium grid, scaled residuals dropped below 1e-5 for continuity/momentum and 5e-6 for k, ω; mass imbalance <0.2%; surface monitors (diffuser static pressure rise, swirl number at filter plane) plateaued within 0.2% over 2000 iterations.

Mesh-dependence check
- Predicted diffuser recovery factor (Cp_rec) at Q = 2.5 m3/s:
  - Coarse: 0.710
  - Medium: 0.729
  - Fine: 0.735
  Using observed order p ≈ 1.95 (from Richardson fit), the estimated asymptotic value is 0.741. The uncertainty band from the fine/medium pair indicates ~2.2% on Cp_rec. Similar trending on the elbow loss coefficient: ζ_elbow = 0.39, 0.37, 0.36 (coarse→fine).
- Swirl number at the filter plane: 0.20 (coarse), 0.18 (medium), 0.18 (fine). Velocity profile uniformity index at the same plane improved from 0.86 to 0.90 with refinement.

Results snapshot (medium grid)
- Total-to-static rise across fan MRF control surface: 416 Pa; downstream of elbow + diffuser, net static recovery of 303 Pa.
- Largest separated zone: ~0.7D long on the elbow outer wall, reattaching before the diffuser entrance; diffuser attached except for a thin corner recirculation near the upper lip (<0.1D).
- Peak y+ in the separated region remained <5; skin friction lines consistent with expected corner secondary flow in the elbow.
- No backflow regions detected at outlet.

Assumptions and bounds of use
- Steady RANS may under-resolve vortex shedding at the elbow; if present, it would likely increase mixing and reduce swirl at the expense of slightly higher pressure loss.
- Fan blade geometry is simplified and tip clearance neglected; near-tongue interaction effects are muted in MRF. This setup should be used for layout ranking, not acoustic predictions.
- Thermal effects, buoyancy, and particulate loading are excluded.
- Roughness not modeled; if the as-built condition is visibly matte or dirty, expect a small drop in recovery (order 1–3%).

Recommendations
- For the next design gate, keep the diffuser half-angle ≤7° and maintain at least 2D of straight length after the elbow before expansion; our runs show visible benefit in uniformity.
- Before freezing the layout, consider a targeted fine-grid patch refinement at the elbow lip to collapse the remaining 2% spread on Cp_rec.
- If schedule allows, a short transient run (URANS with SST) focused on the elbow could clarify the stability of the separation bubble and its impact on filter-face swirl.

I can walk through the case setup and field plots in the Thursday design sync if helpful.
