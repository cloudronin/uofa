# Slide 1 — CFD study overview: battery enclosure manifold
- Objective: estimate pressure loss and flow distribution in the Gen-3 pack exhaust manifold to support blower sizing (target margin ≥ 10% at 1.2 kg/s)
- Toolchain: ANSYS Fluent 2023R2, pressure-based coupled solver, single-precision run on 32 cores (AMD EPYC 7452)
- Approach: steady RANS; air treated incompressible; isothermal walls; no rotating machinery included (fan replaced by mass-flow inlet)
- Deliverables: Δp across manifold, branch flow balance, velocity at four probe taps used on the bench

# Slide 2 — Geometry and modeling scope
- CAD: production enclosure with 7 outlet branches; minor fillets and fastener bosses below 2 mm omitted
- Internal roughness applied uniformly (10 μm) based on bead-blasted Al6061 finish
- Simplifications:
  - No buoyancy (ΔT < 3 K observed in pack), Boussinesq not activated
  - Joints sealed; leakage paths not modeled
  - Gaskets represented as smooth walls with equivalent blockage already in CAD

# Slide 3 — Operating point and boundary specs
- Inlet: mass flow rate 1.2 kg/s at 25 C; total turbulence intensity set to 5% (length scale 0.02 m)
- Outlets: gauge pressure 0 Pa; each branch terminates to ambient
- Fluid properties: ρ = 1.184 kg/m3, μ = 1.85e-5 Pa·s (constant)
- Wall condition: no-slip; scalable wall functions disabled; direct integration to the wall

# Slide 4 — Numerics and solver controls
- Turbulence closure: k-ω SST; curvature correction off
- Spatial schemes: second-order for pressure and momentum; high-order blending factor 0.7
- Pressure–velocity coupling: coupled; pseudo-transient ramp 0.2→1.0 over first 500 iterations
- Stopping rules:
  - Scaled residuals < 1e-5 for continuity, momentum, k, ω
  - Mass imbalance < 0.2% at convergence
  - Monitors: Δp and branch mass flows flat within 0.1% over last 300 iters

# Slide 5 — Grid build and near-wall treatment
- Three unstructured poly-hexcore meshes:
  - Coarse: 2.1M cells; 6 prism layers (growth 1.2); target y+ ≈ 1.8
  - Medium: 4.3M cells; 8 prism layers; target y+ ≈ 1.0
  - Fine: 8.9M cells; 10 prism layers; 1st layer 0.03 mm, growth 1.18; achieved y+ 0.6–1.2 on main duct
- Local refinement around T-junctions and vane supports (cell size 2.5 mm → 0.8 mm)
- Checked skewness P95 < 0.28; non-orthogonality P95 < 12°

# Slide 6 — Grid sensitivity: headline results
- Key output: manifold Δp from blower flange to ambient across all branches
  - Coarse: 373 Pa; Medium: 362 Pa; Fine: 358 Pa
- Richardson extrapolation (assuming p ≈ 1.95 from Δp trend) → asymptotic Δp ≈ 354 Pa
  - Estimated numerical uncertainty on fine grid ~2.8% for Δp
- Branch flow split (fine vs medium): max difference 1.7 percentage points (branch 6)

# Slide 7 — Stability and repeatability checks
- Restarted from three initial states: (a) zero field, (b) 50% of target MFR, (c) uniform 2 m/s velocity guess
  - Final Δp variation ≤ 0.4%; branch flows within 0.6% across restarts
- Tightened relaxation (pseudo time step reduced by 50%) → no change beyond 0.2% in monitors
- Residuals occasionally plateaued at 2e-5 in k; extended 300 iterations produced no meaningful change in integral outputs

# Slide 8 — Comparison with bench data at 1.2 kg/s
- Test setup: production enclosure, same seven branches plumbed to atmosphere; blower stand delivers commanded mass flow
- Measured totals:
  - Bench Δp across manifold: 347 Pa
  - Tap velocities at four locations: 11.9, 8.3, 6.4, 4.7 m/s
- CFD (fine mesh):
  - Δp: 358 Pa (+3.2% vs bench)
  - Taps: 12.5, 8.0, 6.1, 5.0 m/s (errors +5.0%, -3.6%, -4.7%, +6.4%)
- Qualitative pattern (smoke visualization vs streamlines): same dominant recirculation in header near branch 2; CFD recirc length ~10% shorter

# Slide 9 — Sensitivity sweeps (inputs most likely to sway the decision)
- Inlet turbulence intensity:
  - 3% → Δp 353 Pa; branch uniformity (std/mean) 9.1%
  - 5% baseline → Δp 358 Pa; uniformity 9.6%
  - 10% → Δp 364 Pa; uniformity 10.4%
- Wall roughness:
  - 0 μm → Δp 352 Pa
  - 25 μm → Δp 366 Pa
- Takeaway: Δp shifts by ~±2% over plausible inlet TI; roughness assumption matters more (~4%)

# Slide 10 — Turbulence model choice and quick cross-check
- Rationale for SST: adverse pressure gradients in the header and strong curvature at T-junctions; y+ ≤ 1 feasible with current mesh
- One-off check with realizable k-ε (same mesh, standard wall treatment):
  - Δp = 363 Pa (+1.5% vs SST fine); recirculation bubble extends further into branch 2
- No unsteady vortex shedding observed in steady solver monitors; transient run not pursued at this stage

# Slide 11 — What this means for blower sizing
- Using SST fine-grid Δp = 358 Pa, add ducting and filter allowances from systems team (not modeled here) → composite target Δp ≈ 420–440 Pa
- Bench Δp lower than CFD by ~3%; if we take the higher of the two for margin, the selected blower (model “XB-92”) retains ~12–15% headroom at 1.2 kg/s per vendor map
- Flow balance acceptable: all branches within ±8% of mean on CFD fine mesh

# Slide 12 — Assumptions that bound the interpretation
- Isothermal flow; any thermal stratification effects ignored
- No leakage; gasket permeation and micro-gaps neglected
- Fan represented via mass-flow boundary; swirl and non-uniformity at flange not modeled
- Air properties fixed; humidity effects neglected

# Slide 13 — Items recommended if higher confidence becomes necessary
- Extend roughness characterization beyond a single nominal value (map from profilometer across parts)
- Probe more operating points (0.8–1.4 kg/s) to confirm trend in Δp and branch balance
- Local mesh enrichment at vane tips if branch 2 uniformity becomes critical to acoustics

# Slide 14 — Key numbers to carry forward
- Δp (fine mesh, SST): 358 Pa; estimated grid-induced uncertainty ~2.8%
- Δp (bench): 347 Pa; CFD–bench gap +3.2%
- Sensitivity ranges at 1.2 kg/s:
  - Inlet TI 3–10% → Δp 353–364 Pa
  - Roughness 0–25 μm → Δp 352–366 Pa
- Convergence: residuals < 1e-5; mass imbalance < 0.2%; restart spread ≤ 0.4%

# Slide 15 — Closing
- The present model adequately captures the pressure loss and distribution trends for the sizing decision at 1.2 kg/s
- Differences to bench are small and directionally conservative for Δp
- No blockers identified for using these results in the blower selection review next week
