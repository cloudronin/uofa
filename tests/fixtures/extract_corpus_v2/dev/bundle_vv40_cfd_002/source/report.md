To: J. Patel, Respiratory Systems Program Lead
From: D. Nguyen, CFD Lead
Date: 06 Aug 2026
Subject: Credibility snapshot — CFD of blower volute/diffuser for Model V3 ventilator

Scope and intended use
- We ran steady-state CFD to support geometry down-select for the V3 blower volute and outlet diffuser. The specific question is: can the model rank three diffuser options by pressure rise and outlet swirl at 30–50 L/min when the rotor is at 18,000 rpm? The result will be used to choose a single design for the EVT set; it will not be used to set final performance guarantees.

Modeling notes
- Software: Ansys Fluent 2023 R2, pressure-based coupled solver.
- Physics: Incompressible RANS; k–ω SST with low-Re wall treatment. Target wall y+ was 0.8–1.5.
- Geometry: Derived from the released CAD of the blower housing and diffuser, with fillets under 0.3 mm removed. We did not model motor vents or wiring pass-throughs. Rotor modeled as a frozen-rotor MRF zone at 18,000 rpm with the as-designed blade solids. The tip gap was set to 0.20 mm per drawing (no inspection data yet).
- Boundaries: Mass flow specified at the outlet to match bench points (30/40/50 L/min); total pressure at the inlet (ambient); turbulence intensity 5% at inlet, 3% at outlet. Air at 25 C, 1.185 kg/m3, μ = 1.85e-5 Pa·s.
- Numerics: Second-order schemes for convection and pressure, least-squares cell-based gradients. Residual targets 1e-5; mass imbalance <0.05% of throughflow.

Grid and solver checks
- Three unstructured poly-hexcore meshes: 1.2M, 3.8M, and 11.5M cells with five prism layers on walls (growth 1.2, first cell 0.015 mm).
- At 40 L/min, predicted pressure rise was 960 Pa (coarse), 1005 Pa (medium), and 1018 Pa (fine). Extrapolated mesh-converged value ~1031 Pa; estimated GCI on the medium grid 2.4% with observed order ~1.9. Similar trends at 30 and 50 L/min.
- We used the 3.8M-cell mesh for design ranking runs. Total runtime per case ~2.1 hours on 24 cores; 350–450 iterations to convergence.

Bench comparison
- Bench setup: Modified AMCA 210 nozzle rig with a 5-hole probe 30 mm downstream of the diffuser exit. Three test points: 30/40/50 L/min. Delta-P across blower measured with Dwyer 2000 series (±0.5% FS); flow rate via calibrated nozzles (±2%). Repeatability over three runs gave SD of 11–18 Pa on delta-P.
- Results summary:
  - 30 L/min: Test 1110 ± 30 Pa; CFD 1126 Pa (+1.4%).
  - 40 L/min: Test 990 ± 25 Pa; CFD 1005 Pa (+1.5%).
  - 50 L/min: Test 880 ± 30 Pa; CFD 905 Pa (+2.8%).
- Outlet yaw angle vs. probe rake average differed by <3 degrees for all three designs at 40 L/min; diffuser B reduced swirl the most in both CFD and test.
- No tuning was performed after the initial setup; same turbulence model and wall treatment across all runs.

Assumptions and limitations
- No acoustic modeling; unsteady tones and broadband noise are not represented.
- Thermal effects ignored; air properties fixed at 25 C. Compressibility also ignored (local Mach max ~0.12 in CFD).
- Tip clearance set from drawings; we have not measured production rotor/housing gaps. Small leakage through motor wiring ports and gasket seams omitted.
- The frozen-rotor approach neglects blade-passing unsteadiness; suitable for mean performance only.

What this means for the decision
- The model reproduces the bench delta-P within 3% over 30–50 L/min for the baseline diffuser and captures the relative ranking of outlet swirl across the three designs. The medium grid shows small discretization error relative to the experimental scatter, and mass conservation/rate residuals are tight.
- The largest unknowns are unmodeled leakage and unmeasured as-built tip gaps; both would bias CFD high on pressure rise. Current agreement suggests those effects are within the experimental uncertainty for the prototypes we tested.

Recommendation
- Accepted for ranking diffuser options by mean pressure rise and outlet swirl at 18,000 rpm over 30–50 L/min, for EVT selection only. Not approved for acoustic predictions, transient loading, or extrapolation beyond 60 L/min.
- Decision by: J. Patel (Program Lead) on 06 Aug 2026.

Open items to improve confidence (not gating this decision)
- Add a fourth test point at 60 L/min to bound the intended range.
- Re-run one case with measured tip gaps once the CMM data lands, to confirm bias direction.
- Consider a short unsteady RANS run on the selected design to see if mean predictions shift relative to frozen-rotor.
