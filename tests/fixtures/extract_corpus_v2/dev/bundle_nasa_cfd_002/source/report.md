To: A. Patel, Propulsion IPT Lead
From: L. Romero, CFD Task Lead
Date: 2026-08-06
Subject: Credibility memo — S-duct inlet CFD for Block 2 UAV

Purpose and use
We ran steady-state CFD to estimate total-pressure recovery and exit swirl for the Block 2 S-duct at low subsonic conditions to support the bleed-port layout trade. The working acceptance band discussed at PDR was ±3% on area-averaged recovery and ±0.02 on swirl index at Station 2. This memo summarizes what we did and whether the numbers are solid enough for that decision.

Modeling approach
Simulations used ANSYS Fluent with a pressure-based solver and ideal-gas properties. Wall modeling targeted y+ under 1 with near-wall spacing of 0.03 mm; on average we achieved y+ ≈ 1.5, with local hot spots near the inner bend up to 3. The turbulence closure is k–ω SST for separated flow capture. Note: the last two production runs used Spalart–Allmaras to reduce turnaround time; results changed less than 1.2% on recovery at the nominal condition.

Operating points and boundaries
Free-stream Mach was 0.23 at a stagnation temperature of 288 K. We prescribed total pressure at the inlet as 101.3 kPa and set turbulence intensity to 1%. Exit was mass-flow at 4.5 kg/s. In the wind-tunnel match cases used for comparison, we used 3% inlet turbulence and 4.3 kg/s to mirror test conditions.

Discretization and run behavior
We built three unstructured meshes with prism layers: 3.1M, 6.5M, and 11.2M cells. Residuals of continuity and momentum fell three orders of magnitude; the run log lists five orders for the coarse and medium grids. Mass imbalance closed within 0.2%. A grid refinement check indicates less than 0.8% change in area-averaged recovery from medium to fine; when recomputed with a uniform refinement ratio, the estimated GCI at Station 2 is 1.6%. Exit swirl index varied by 0.013 across the grid set.

Comparison to test
We compared to the rigid S-duct rig data (alpha 0–12 deg; tunnel data sheet also lists −2 to 14 deg) using five-hole probe maps at Station 2. At nominal (M0.23, alpha 0), CFD recovery was 2.6% low relative to test; swirl index differed by 0.015. At alpha = 8 deg, the shortfall grew to 4.1% and swirl bias to 0.028. Flow patterns matched gross features: inner-bend separation onset at x/L ≈ 0.38 and reattachment by ≈0.62, with the footprint location within 5 mm of the oil flow.

Uncertainty and robustness
We combined the fine-grid GCI (1.6%) with observed run-to-run jitter from restart tests (0.9%) as a root-sum-square to get about 1.9% numerical spread on recovery at nominal. No correction for measurement scatter has been applied. The SA-versus-SST difference at the nominal point (1.2%) is within that band, but at alpha = 8 deg the model choice affected swirl by 0.021.

Applicability
These results are intended for M ≈ 0.2–0.3 and angles of attack 0–10 deg; earlier planning notes limited use to −2 to 8 deg. Reynolds number is O(4.4e6) based on inlet lip. We did not include surface roughness or bleed mass extraction.

Credibility takeaways
- Mesh dependence is small at the nominal point, but the GCI varies from 0.8% to 1.6% depending on how the refinement ratio is interpreted.
- Residual reductions are acceptable for steady RANS; the discrepancy between 1e−3 and 1e−5 noted in the logs needs a cleaner story.
- Boundary inputs were consistent with spec for design-point runs; the validation cases used higher inlet turbulence and a slightly lower mass flow to mirror the tunnel, which complicates one-to-one comparison.
- Against test, recovery bias is within the ±4% band at nominal but outside the ±3% band at alpha = 8 deg; swirl error is below 0.02 at nominal and above it off-design.

Decision
Given the above, I judge the current CFD set accepted for preliminary placement and sizing of bleed ports at M0.23 and alpha 0–8 deg, subject to rerunning the off-design cases on the fine grid with SST and documented y+ ≤ 1 near the inner-bend separation. It is not accepted for certification-level distortion predictions or for AoA beyond 8 deg. Decision by: L. Romero, CFD Task Lead, concurred by Propulsion IPT at the 2026-08-06 check-in.
