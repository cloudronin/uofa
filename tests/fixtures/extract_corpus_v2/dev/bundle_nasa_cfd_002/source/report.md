To:    A. Whitaker, ECLSS Subsystem Lead
From:  L. Ng, Fluids Modeling
Date:  2026-08-06
Subj:  CFD status for Purge Duct Y-Junction pressure loss and flow split

Quick read-out
- Purpose: Use RANS CFD to estimate total pressure drop and branch flow distribution through the crew module purge Y at 20–60 CFM for fan sizing and control margin.
- Current confidence: Good for 20–45 CFM under lab-like, isothermal conditions; less certain when extrapolating to 60 CFM or with upstream swirl.

Model setup
- Software: FUN3D v13.5 (double precision, steady solver). Second-order schemes for convection and gradients. Runs executed on Ames “Nereid” nodes (16 cores/case).
- Physics: Incompressible assumption (M < 0.12 throughout); constant properties at 295 K, ρ = 1.18 kg/m³, μ = 1.86e-5 Pa·s. Turbulence: SST k–ω with near-wall integration; cross-check with SA (baseline).
- Geometry: Based on Purge Duct CAD Rev D. Sub-mm fillets and screw bosses suppressed; branch lip detail retained. Perforated screen modeled as a porous jump (quadratic loss), coefficients from vendor curve fit at Re = 3–6×10³.
- Boundaries: Inlet set by prescribed volumetric flow (20, 30, 45, 60 CFM cases). Common outlet to ambient static pressure (101.3 kPa). Walls no-slip, adiabatic. Screen implemented as internal surface with K1 = 1.7e7 1/m², K2 = 3.2e3 1/m.

Numerics and convergence
- Mesh: Unstructured tet-prism; 5 prism layers, growth 1.2, first cell height sized for y+ ≈ 1–2 on 30 CFM case. Three levels: 2.1M / 4.7M / 10.3M cells.
- Convergence indicators: L2 residuals <1e-5 for continuity and momentum; branch mass balance <0.2%; pressure-drop monitor flat over last 1,000 iterations.
- Mesh study: ΔP across the Y at 30 CFM changed +3.9% (2.1M→4.7M) and +1.8% (4.7M→10.3M). Extrapolated asymptote suggests fine-grid remaining discretization effect ≈2–3%.

Sensitivity to modeling choices
- Turbulence model: SA produced ΔP ~3% lower than SST on the fine grid; branch split within 1 percentage point. We have adopted SST for production due to better separation capture at the inner lip seen in smoke visualization.
- Wall treatment: Switching to scalable wall functions (target y+ ~35) increased ΔP ~6% and muted the secondary flow at the junction; not used further.
- Porous jump coefficients: ±15% perturbation in K-values leads to ±6% swing in predicted ΔP; minimal effect on split (<1.5 points).

Comparison against bench data
- Two points available on the lab mockup with pressure taps at stations P1 (upstream) and P2 (downstream of Y), and thermal mass flowmeter on the inlet leg:
  - 20 CFM: test ΔP = 70 Pa (±3 Pa). CFD (fine grid, SST) = 68 Pa (−2.9%).
  - 30 CFM: test ΔP = 128 Pa (±5 Pa). CFD = 124 Pa (−3.1%).
- Flow split at 30 CFM: test 60/40 (±2%). CFD = 62/38 on fine grid.
- No facility point at 45 or 60 CFM; we are extrapolating there. At 45 CFM, CFD predicts ΔP = 220 Pa and split 64/36.

Uncertainty on key outputs
- Combine contributions from remaining grid effects (~2.5%), inlet flowrate setting (±1% → ~±1% on ΔP), and porous media fit (dominant, ±6%). Quadrature suggests overall ±6.7% on ΔP at 30 CFM. Branch split uncertainty estimated at ±2–3 percentage points dominated by turbulence model choice.

Traceability and reproducibility
- Case directories, meshes, and input decks tracked in GitLab repo cfd-purge-duct (tag v0.7). Meshing journals and solver scripts are parameterized per flowrate. Run logs archived with FUN3D hashes and compiler flags. Results posted to the team SharePoint with a one-page “how to rerun” note.

Limitations and caveats
- Upstream swirl and pulsation not modeled; the current inlet is spatially uniform. If the fan or upstream ducting introduces rotation, the split may shift by several points based on literature for Y-junctions.
- The porous jump relies on vendor data at a lower Reynolds range than 60 CFM; we need either updated coefficients or a plate-resolved model for that regime.
- Only steady solutions were pursued; no URANS/LES to capture potential unsteady separation at higher flow.

Recommendations before CDR
1) Get an additional facility point at 45–50 CFM to anchor the trend and refine the porous-coefficient fit.
2) Run one resolved-screen case on the fine grid (or a local submodel) to bracket the porous-jump bias.
3) If operations anticipate swirl >0.2 turn-rate at the Y, add an inflow profile study to bound branch split.
4) Freeze the fine-grid setup and archive as “baseline v1.0”; defer further algorithm changes unless new data disagree.

Happy to walk through the meshes and residual histories in the next tag-up.
