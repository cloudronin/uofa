To: Axiom C&DH Flight Avionics Lead
From: P. Mercado, Thermal/Fluids
Date: 06 Aug 2026
Subject: CHT model status for the avionics cold plate (rack bay 2)

Quick take
- The current conjugate heat transfer model of the bay-2 cold plate is producing stable, mesh-insensitive results and matches the bench article within a few °C for the metrics we care about (peak device temperature and coolant pressure drop).
- The analysis is adequate to support the upcoming geometry freeze and pump sizing check, with caveats around interface resistance and extrapolation to warmer coolant.

What we modeled
- Tooling: Ansys Fluent 2023 R2, double precision, pressure-based coupled solver; SST k-ω with low-Re treatment; second-order spatial schemes.
- Geometry: Full plate, manifold, and attached board stack with copper heat spreader and TIM. Conjugate solid-fluid solved with shared interfaces; no radiation. Coolant is 30% PG/water, single-phase; no cavitation or boiling modeled.
- Operating point assessed: 0.20 kg/s loop flow, 25 °C inlet, 1.5 bar inlet pressure, 120 W distributed over four devices on the board.

Numerics and mesh sanity
- Mesh: 8.7M cells, poly-hexcore in fluid; 12 prism layers, first-cell y+ < 1 on all wetted walls; conformal nonmatching interfaces through fluent-to-solid.
- Refinement study: two coarsenings (5.4M, 3.2M) with uniform 1.6× change in characteristic cell size. Peak device temperature changed by -0.6 °C (mid to fine) and -1.5 °C (coarse to mid); Richardson-based estimate gives 1.8% numerical uncertainty on the peak. Pressure drop variation < 4%.
- Residuals fell below 1e-5 for energy and 1e-4 for momentum; area-averaged heat fluxes steady within 0.1% over last 1,000 iterations.

Quick checks on the math
- We exercised the workflow on two closed-form cases before running the full plate:
  - 1D composite wall with constant heat flux: predicted mid-plane temperatures agreed within 0.2%.
  - Laminar pipe cooling of a uniform heat-flux tube: Nusselt number within 0.6% of the analytical solution at Re ~ 1,200 (same schemes and property tables). This gives confidence that conduction–convection coupling and property handling are wired correctly.

Inputs we trust (and why)
- Metals: Al 6061-T6 and C110 copper, temperature-dependent k(T) from ASM data; verified against MatWeb within 3%.
- TIM: vendor sheet (Laird Tflex 600, 3 W/m-K) adjusted to 2.4 W/m-K based on our coupon test; thickness set to measured 0.38 mm.
- Contact resistance between spreader and cold plate: measured on the bench stack via step-heating, 1.2e-4 m^2·K/W ± 0.4e-4 (1σ).
- Coolant properties: NASA Glenn tables for 30% PG; Fluent polynomial fit applied over 20–60 °C.

Bench comparison
- Hardware: CNC’d aluminum plate and manifold; same bolt pattern and gasket groove; four Kapton heaters (120 W total). Instrumentation: 12 T-type thermocouples (±0.5 °C), FLIR A655sc (emissivity tuned at 0.92 via tape reference), differential pressure transducer (±0.25 kPa).
- Conditions matched within tolerance: flow 0.202 kg/s, inlet 25.7 °C.
- Results:
  - Peak device temp: model 58.4 °C vs test 62.0 °C (Δ = -3.6 °C). Hot spot in both cases sits at the outboard device; location offset ~8 mm.
  - Area-averaged board temp: 47.8 °C vs 49.1 °C (Δ = -1.3 °C).
  - Coolant Δp across the plate: 18.2 kPa vs 19.5 kPa (Δ = -1.3 kPa).
- The residual bias on peak temperature tracks the lower assumed interface resistance in the model. When we set R”t to the high end of the measured band, the peak rises by +2.9 °C and the IR pattern aligns better.

What matters most (levers and spread)
- Sensitivity (standardized regression on 120 Latin hypercube samples varying R”t ±30%, flow ±5%, inlet ±2 °C, TIM k ±20%, copper k ±5%):
  - Contact resistance (R”t): +0.62 on peak temp
  - Flow rate: -0.31 on peak temp
  - TIM conductivity: -0.21 on peak temp
  - Others < |0.1|
- Propagated uncertainty on the predicted peak at the nominal condition: 58.4 °C ± 4.2 °C (95%). Pressure drop band: 18.2 kPa ± 1.1 kPa (95%).

Assumptions to remember
- No boiling or two-phase in the manifold; verified wall superheat margin > 25 K at all modeled locations.
- Radiation ignored; enclosure view factors are poor and ΔT to ambient is small (< 35 K). Including ε = 0.9 raised heat loss by < 1 W in a spot check.
- Manifold surface roughness taken as 1.6 μm Ra; doubling roughness moved Δp by < 0.8 kPa.

People, files, and reruns
- Primary analyst: Mercado (12 yrs CHT); secondary check: H. Dwyer (8 yrs), who reran the mid-mesh case and reproduced key numbers within reported bands.
- Repro: Git tag cht_rack_v12; Fluent case and journal scripts under Vault/thermal/avx_bay2; solver build 23R2-20230915. Cluster: JPL-Pallas, 64 cores, 3.5 h wall.

Next steps before PDR
- Expand the sweep to inlet temperatures up to 35 °C and flows down to 0.16 kg/s to bracket ops.
- Tighten the interface characterization on the flight gasket stack; this is the dominant driver on the peak.
- Add a localized mesh enrichment under the outboard device to see if the remaining 3–4 °C gap can be narrowed without overmeshing the whole plate.

Bottom line
The model is in good shape for design decisions on geometry and pump load. The remaining discrepancies are explainable by measured interface behavior, and the uncertainty bands put the peak well below the 75 °C device limit at nominal flow. I recommend using these results for the PDR package with the stated bounds and assumptions.
