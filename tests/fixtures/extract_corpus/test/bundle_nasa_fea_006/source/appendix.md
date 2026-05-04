# Appendix A — Quantitative Model-to-Test Comparison Data

## OCV-2031 Skirt Assembly — SQTC-2029 Strain Gauge Correlation

### A.1 Gauge Location Map Reference

Gauge locations are defined relative to the skirt coordinate system (SCS) with origin at the vessel-to-skirt weld centerline. Positive Z is axially upward (toward vessel dome). Gauge orientation (axial, hoop, or 45° rosette) is noted for each location.

---

### A.2 LC-1: Internal Pressure Only (34.5 MPa)

| Gauge ID | Location (SCS) | Orientation | Measured με | Predicted με | Ratio (P/M) |
|---|---|---|---|---|---|
| G-01 | Z=+45 mm, θ=0° | Hoop | 1842 | 1901 | 1.032 |
| G-02 | Z=+45 mm, θ=90° | Hoop | 1835 | 1887 | 1.028 |
| G-03 | Z=+45 mm, θ=180° | Hoop | 1849 | 1893 | 1.024 |
| G-04 | Z=+45 mm, θ=270° | Hoop | 1831 | 1879 | 1.026 |
| G-05 | Z=−20 mm, θ=0° | Axial | 612 | 589 | 0.962 |
| G-06 | Z=−20 mm, θ=90° | Axial | 608 | 594 | 0.977 |
| G-07 | Z=−20 mm, θ=180° | Axial | 619 | 601 | 0.971 |
| G-08 | Z=−20 mm, θ=270° | Axial | 605 | 587 | 0.970 |
| G-09 | Lug A, face | 45° rosette | 2104 | 2187 | 1.039 |
| G-10 | Lug B, face | 45° rosette | 2098 | 2171 | 1.035 |
| G-11 | Lug C, face | 45° rosette | 2091 | 2163 | 1.034 |
| G-12 | Lug D, face | 45° rosette | 2112 | 2194 | 1.039 |
| G-13 | WAZ, θ=0° | Axial | 987 | 1003 | 1.016 |
| G-14 | W-07 vicinity, 12 mm | Axial | 1456 | 1413 | 0.970 |

**LC-1 Summary:** Mean P/M ratio = 1.009; Std Dev = 0.028

---

### A.3 LC-2: Axial Compression (2.2 MN, no pressure)

| Gauge ID | Location (SCS) | Orientation | Measured με | Predicted με | Ratio (P/M) |
|---|---|---|---|---|---|
| G-01 | Z=+45 mm, θ=0° | Hoop | −124 | −118 | 0.952 |
| G-02 | Z=+45 mm, θ=90° | Hoop | −121 | −116 | 0.959 |
| G-03 | Z=+45 mm, θ=180° | Hoop | −126 | −119 | 0.944 |
| G-04 | Z=+45 mm, θ=270° | Hoop | −122 | −117 | 0.959 |
| G-05 | Z=−20 mm, θ=0° | Axial | −3241 | −3318 | 1.024 |
| G-06 | Z=−20 mm, θ=90° | Axial | −3229 | −3301 | 1.022 |
| G-07 | Z=−20 mm, θ=180° | Axial | −3255 | −3327 | 1.022 |
| G-08 | Z=−20 mm, θ=270° | Axial | −3244 | −3309 | 1.020 |
| G-09 | Lug A, face | 45° rosette | −1872 | −1943 | 1.038 |
| G-10 | Lug B, face | 45° rosette | −1865 | −1931 | 1.035 |
| G-11 | Lug C, face | 45° rosette | −1879 | −1948 | 1.037 |
| G-12 | Lug D, face | 45° rosette | −1869 | −1937 | 1.036 |
| G-13 | WAZ, θ=0° | Axial | −2104 | −2167 | 1.030 |
| G-14 | W-07 vicinity, 12 mm | Axial | −2891 | −2978 | 1.030 |

**LC-2 Summary:** Mean P/M ratio = 1.008; Std Dev = 0.031

---

### A.4 LC-3: Combined Pressure (34.5 MPa) + Bending (850 kN·m)

Selected gauge results shown; full dataset in project database record SQTC-2029-DATA-003.

| Gauge ID | Measured με | Predicted με | Ratio (P/M) |
|---|---|---|---|
| G-01 | 2341 | 2419 | 1.033 |
| G-05 | −2841 | −2923 | 1.029 |
| G-07 | 4102 | 4198 | 1.023 |
| G-09 | 3187 | 3301 | 1.036 |
| G-14 | 3944 | 3826 | 0.970 |

**LC-3 Summary (all 22 gauges):** Mean P/M ratio = 1.030; Std Dev = 0.041

---

### A.5 Modal Frequency Comparison

A free-free modal test was conducted on the skirt assembly (without vessel, boundary condition: foam-supported to simulate free-free) using a Brüel & Kjær LDS V780 electrodynamic shaker and 24-channel PCB 352C33 accelerometer array. Mode shapes were identified using PolyMAX curve fitting in LMS Test.Lab 2021.

| Mode | Description | Measured Freq (Hz) | Predicted Freq (Hz) | Error (%) |
|---|---|---|---|---|
| 1 | Ovaling (2-lobe) | 312.4 | 318.7 | +2.0 |
| 2 | Ovaling (2-lobe, 90° rotated) | 313.1 | 318.7 | +1.8 |
| 3 | Axial breathing | 487.2 | 491.3 | +0.8 |
| 4 | Lug rocking | 621.8 | 634.2 | +2.0 |
| 5 | Higher ovaling (3-lobe) | 744.3 | 758.9 | +2.0 |

All predicted frequencies are within 2.1% of measured values. Modal assurance criterion (MAC) values for the first five modes ranged from 0.961 to 0.988, indicating excellent mode shape correlation.

---

### A.6 Uncertainty Budget Summary (LC-3 Peak Stress at W-07)

| Uncertainty Source | Distribution | ±1σ Contribution to Peak Stress |
|---|---|---|
| Elastic modulus (Ti-6Al-4V) | Normal, ±5% | ±3.1% |
| Applied load magnitude | Normal, ±2% | ±1.4% |
| Weld-toe fillet radius | Uniform, ±15% | ±2.8% |
| WAZ property reduction | Normal, ±10% | ±1.9% |
| Mesh discretization (GCI-based) | Conservative bound | ±0.8% |
| **Combined (RSS)** | | **±5.1%** |
| **Monte Carlo 95th percentile exceedance** | | **+5.9%** |

Nominal predicted peak stress at W-07 (LC-3): **389 MPa**
95th-percentile predicted peak stress: **412 MPa**
Material yield strength (AMS 4928, annealed): **896 MPa**
Margin of safety (95th-percentile basis): **+1.17**

---

*End of Appendix A*

*Document No.: SCA-FEA-0047-Rev C | Appendix A | Meridian Aerospace Engineering | 14 March 2025*
