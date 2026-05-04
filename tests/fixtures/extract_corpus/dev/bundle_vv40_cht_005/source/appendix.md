# Appendix A — Benchmark Case Summary Sheets

## A.1 Graetz Solution Comparison

**Solver:** ANSYS Fluent 2023 R2, laminar steady-state, 2D axisymmetric
**Geometry:** Circular tube, L/D = 80, uniform wall heat flux q″ = 5,000 W/m²
**Working fluid:** Air at 300 K, Re = 400 (laminar)
**Reference:** Incropera & DeWitt, 7th ed., Table 8.1 (thermally developing, hydrodynamically developed)

| x/D | Nu (Fluent) | Nu (Graetz) | Error (%) |
|-----|-------------|-------------|-----------|
| 2   | 9.14        | 9.21        | −0.76%    |
| 5   | 6.83        | 6.88        | −0.73%    |
| 10  | 5.12        | 5.14        | −0.39%    |
| 20  | 4.02        | 4.04        | −0.50%    |
| 40  | 3.67        | 3.66        | +0.27%    |
| 80  | 3.66        | 3.66        | 0.00%     |

Maximum error across all stations: 0.76%. Passes benchmark acceptance criterion of <1%.

---

## A.2 Fin Array Benchmark (NACA TN-3208)

**Configuration:** Rectangular fin array, aluminum fins on steel base plate
**Boundary condition:** Uniform base temperature T_base = 400 K, convective tip h = 85 W/m²·K, T∞ = 300 K
**Biot number range:** 0.1 to 5.0 (varied by adjusting fin conductivity)

| Bi   | T_tip Fluent (K) | T_tip Reference (K) | ΔT (K) |
|------|------------------|---------------------|--------|
| 0.1  | 398.2            | 398.1               | +0.1   |
| 0.5  | 391.4            | 391.0               | +0.4   |
| 1.0  | 381.7            | 381.2               | +0.5   |
| 2.0  | 364.3            | 363.9               | +0.4   |
| 5.0  | 336.8            | 336.1               | +0.7   |

Maximum deviation: 0.8 K across all Biot number conditions. Passes acceptance criterion.

---

## A.3 Iterative Convergence Monitoring Protocol

For all production runs, convergence was assessed using the following criteria applied simultaneously:

1. Scaled residuals for continuity, x/y/z momentum, k, ω, and energy all reduced by ≥ 5 orders of magnitude from iteration 1 values
2. QoI monitors (peak wall temperature, area-averaged Nu per pass) showing variation < 0.1% over the final 500 iterations
3. Global energy balance check: net heat flux imbalance across all boundaries < 0.05% of total heat input

All three criteria were satisfied for the production mesh runs. Convergence history plots are archived in TBC-REPO/VV/convergence/.

---

## A.4 Material Property Data Sources

Thermal conductivity of MAR-M247 used in the simulation:

| Temperature (K) | k (W/m·K) — TBC-MAT-DB Rev.4 | k (W/m·K) — Touloukian (1970) | Difference (%) |
|----------------|-------------------------------|-------------------------------|----------------|
| 1,100          | 13.1                          | 13.4                          | −2.2%          |
| 1,200          | 14.2                          | 14.5                          | −2.1%          |
| 1,300          | 15.6                          | 15.9                          | −1.9%          |

Differences are within the ±5% variation band used in the sensitivity study (§6.1 of main report). The program material database values are considered acceptable for use.

---

## A.5 Mesh Quality Metrics — Production Mesh (5.6 M cells)

| Metric | Value | Threshold |
|--------|-------|-----------|
| Maximum skewness (fluid) | 0.71 | < 0.85 |
| Mean skewness (fluid) | 0.18 | < 0.30 |
| Minimum orthogonal quality | 0.31 | > 0.10 |
| Maximum aspect ratio (near-wall prism layers) | 48:1 | < 100:1 |
| y⁺ max (all fluid-solid interfaces) | 0.94 | < 1.0 |
| y⁺ mean (all fluid-solid interfaces) | 0.41 | < 0.5 |

All mesh quality metrics satisfy the project mesh quality standard (TBC-STD-MESH-001 Rev. 2).
