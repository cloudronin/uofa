To: Propulsion CFD Working Group
From: J. Kim, Turbomachinery Modeling Lead
Date: 2026-08-06
Subject: Credibility status for Rotor 37 stage CFD — V&V summary and recommendation

Context and intended use
- Objective: Use steady compressible CFD to predict the performance map (pressure ratio, isentropic efficiency, exit flow angles) of the NASA Rotor 37 single-stage compressor at 98–102% corrected speed for preliminary system sizing and bleed scheduling. Not for rotating stall onset or surge margin certification.
- Acceptance targets from the M&S Plan Rev C: ±2% on pressure ratio at design mass flow, ±2.5 pts on efficiency at design, trend fidelity across ±10% mass flow from design, and bounded estimates of prediction uncertainty.

Physics and modeling choices
- Governing equations: steady RANS, rotating frame with mixing-plane interface; ideal gas with Sutherland viscosity; adiabatic no-slip walls; fully turbulent assumption (no transition).
- Turbulence: k-ω SST (primary); cross-check with Spalart–Allmaras with rotation/curvature correction.
- Tip clearance, fillets, and hub/shroud contours matched to the NASA drawings; casing treatment omitted (none present in this rig).

Input pedigree and boundary conditions
- Inlet total temperature/pressure and turbulence intensity taken from Reid & Moore Rotor 37 test reports; corrected speed and backpressure schedules match runs R37-98, R37-100, R37-102. Tip clearance set to 0.356 mm per rig as-built. Instrumentation uncertainty per report: Pt ±0.15%, Tt ±0.2 K, speed ±0.05%.

Numerics and software trustworthiness
- Code: ANSYS CFX 2024 R1, double precision; second-order spatial schemes; multigrid AMG; convergence to residual drops >5 orders and mass/energy imbalance <0.2%.
- Code verification: Internal MMS case set for compressible rotating Euler shows L2 error ~O(Δx^2) with observed order 1.98; vendor regression suite for rotating frames passed (report archived in Confluence MS-211).
- Platform comparability: Results reproduced within 0.2% PR on two clusters (Intel Ice Lake and AMD Milan) using identical input decks; runs tracked via GitLab CI job IDs.

Solution verification (discretization/time)
- Mesh family: 3.2M, 7.8M, 18.5M cells (structured, O4H topology), y+ ≈ 0.8 at design; 35 blade-to-blade points minimum.
- GCI (Roache, Fs=1.25) at design: PR GCI = 1.5%, efficiency GCI = 1.9%, exit swirl angle GCI = 0.9°. Richardson extrapolation consistent with monotonic approach on all three grids.
- Pseudo-time step and physical URANS spot checks: at near-stall, unsteady content raises PR by 0.3%; steady assumption acceptable for accepted envelope.

Validation against test data
- Design point (100% speed): PR predicted 2.106 vs 2.082 test (+1.2%); efficiency 0.847 vs 0.863 (−1.6 pts). Spanwise Cp distributions at 20/50/80% span within ±4% except near 90% span suction peak (k-ω SST overpredicts by ~6%).
- Off-design trends: Across ±10% mass flow at 100% speed, slope of PR–ṁ curve matches within 0.05 PR per 0.01ṁ. At 98% speed, exit swirl at mid-span within 1.2° RMS; at 102% speed, efficiency low by up to 2.3 pts near choke.
- Data-method consistency: Mixing-plane model departs from rig near stall; mismatch up to 5% PR in last two points before stability limit.

Uncertainty and sensitivity
- Input variability considered: inlet turbulence (2–6%), tip clearance (±0.05 mm), speed sensor (±0.05%), backpressure regulation (±0.2%).
- Medium-mesh Monte Carlo (200 samples) with sparse Sobol screening: tip clearance dominates PR sensitivity (≈0.9% PR per +0.1 mm), inlet turbulence second-order on efficiency (≈0.3 pts per +2%).
- Combined uncertainty at design (RSS of input, discretization, and validation noise): PR ±1.8% (95%), efficiency ±2.2 pts (95%). Uncertainty bands envelop test values across accepted range.

Robustness and range of applicability
- Convergence achieved across 0.9–1.05 relative mass flow at each speed; two near-stall points required URANS restarts. Turbulence model swap changes PR by <0.7% at design.
- No solver divergence observed with ±10% perturbations in inlet Tt or Pt; solution stable to mesh perturbations in LE refinement region.

Quality assurance, traceability, and governance
- Configuration control: Input decks, meshing scripts (Autogrid5 templates), and post-processing notebooks versioned in GitLab (tag rotor37_cfx_v1.3). DOORS links requirements to runs; unique run IDs embedded in .res files.
- Documentation: Modeling Guide MG-TRB-07 Rev B, Verification Note VN-2026-12, and Validation Report VAL-2026-05 complete and archived.
- Personnel: Lead analyst 12 yrs turbomachinery CFD (CFX/AIAA associate fellow); peer checker 5 yrs experience; both completed annual M&S training.
- Independent review: External SME (Dr. S. Patel, GRC) replicated design point on medium mesh; PR within 0.5%, provided comments on hub boundary layer treatment; dispositions closed in CR-1189.
- Prior use: Same workflow applied to Rotor 67 and Stage 35; published accuracy consistent (AIAA-2025-2198).
- Compliance: All items in M&S Plan Rev C closed; acceptance metrics met or explained; risk register shows residual risk confined to stall-near conditions.

Assumptions and limitations
- Steady RANS with mixing-plane cannot capture rotating stall cells or stage clocking; no heat transfer modeled; roughness neglected (rig surfaces polished). Not approved for predicting stability margin or detailed blade buffeting loads.

Decision
- By consensus of the Propulsion CFD Working Group and approved by the Chief CFD Engineer (M. Alvarez): The Rotor 37 stage CFD model and workflow are accepted for predicting pressure ratio, efficiency, and exit flow angles over 98–102% corrected speed and 0.9–1.05 relative mass flow, subject to documenting the uncertainty bands reported herein. The model is not accepted for rotating stall onset, surge margin quantification, or unsteady load predictions.

Next steps
- Retain URANS capability for near-stall diagnostics (informational only).
- Explore curvature-corrected SST and near-tip mesh enrichment to reduce 90% span Cp bias.
- Update the Confluence page with reproducibility package and rebaseline to tag rotor37_cfx_v1.4 after changes.
