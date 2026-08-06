To: Priya Rao, PM—Flow Analytics
From: CFD Team (A. Nguyen, L. Serrano)
Subject: Status check—CFD credibility package for stent‑graft screening (ASME V&V 40-aligned)

Quick take: The current model is suitable for down‑selecting stent‑graft designs using peak shear rate and arch pressure loss as decision metrics. We targeted a mid-to-high assurance bar based on the consequence of an incorrect screen (moderate, since we still gate by bench data). Evidence summarized below.

Context and decision linkage
- Intended use: rank candidate thoracic stent‑graft geometries under pulsatile flow for benchtop prioritization. Not for patient-specific prediction.
- Operating envelope: Re = 2,000–5,000; heart rate 50–90 bpm; hematocrit equivalent μ = 3.0–4.0 cP.
- Risk posture: Medium—screening errors can waste test time but won’t reach patients. This drove stronger checks on numerics and data relevance; model‑form bracketing set to “reasonable but not exhaustive.”

Model and numerics
- Physics: Incompressible Navier–Stokes, Newtonian blood surrogate justified by Re>2,000 and low shear‑thinning in our glycerol–water mix; density 1060±5 kg/m³.
- Turbulence treatment: URANS, k–ω SST with low‑Re wall functions; cross‑checked with SAS on one design to gauge model‑form spread.
- Discretization: Polyhedral cells with 10 prism layers; baseline 12M cells (Δy+≈1–2). Two refinements (6M→12M→24M) changed peak τw by 3.2% then 1.3%; arch ΔP by 2.8% then 0.9%. Reported GCI: 3.5% (τw), 1.8% (ΔP).
- Time marching: Δt = 1e‑4 s (CFL<1). Halving Δt moved cycle‑averaged ΔP by 0.6% and peak τw by 1.1%.
- Convergence: Residuals to 1e‑5; mass imbalance <0.1% per time step; periodicity error over last two cycles <0.5%.
- Implementation checks: OpenFOAM v10, double precision. Verified second‑order spatial/temporal rates on Poiseuille and Womersley tubes; lid‑driven cavity matches published benchmarks within 0.7%. Cross‑solver spot check (Fluent 2023R2) on coarse mesh: ΔP within 2.1%.
- Hardware effects: Intel and AMD clusters yield <0.3% spread on ΔP for identical decks.

Inputs, calibration, and traceability
- Boundary data: Measured inflow waveform from bench pump; outlet RCR targets matched to rig impedance (±15%). No tuning to match validation outputs; only inflow amplitude scaled to pump meter (±3%).
- Material properties: μ = 3.5 cP ±10% uniform; ρ = 1060±5 kg/m³.
- Reproducibility: Case files, meshing scripts, and post‑processing notebooks under Git LFS (tag v0.6.3); containerized environment (Ubuntu 22.04, OpenFOAM v10 image hash 9f2d…). Random seeds recorded.

Comparison with lab data
- Data source: Refractive‑index‑matched PIV in PDMS arch with the same graft geometry; Re ≈ 3,500, Womersley ≈ 14. Velocity uncertainty ≈5%, ΔP transducer ±1 mmHg (k=2).
- Match to COU: Geometric fidelity within 0.2 mm; identical waveform and fluid properties.
- Agreement: Cycle‑averaged arch ΔP: model 18.9 mmHg vs PIV‑based estimate 19.6 mmHg (‑3.6%). RMS velocity error on three centerlines: 6.1%. Jet width at zone 2: within 0.5 mm. Vortex core location within 3 mm.
- Data quality controls: PIV calibration performed pre/post; seeding density 0.04 ppp; outlier rejection <2%.

Uncertainty and sensitivity
- Propagation: Latin hypercube (N=120) over μ, inflow amplitude, outlet impedances; 95% CI on peak τw for the lead design: 2,750±220 s⁻¹; on ΔP: 18.9±1.1 mmHg.
- Drivers: First‑order effects—outlet resistance (Sobol 0.42), μ (0.31), inflow amplitude (0.18). Model‑form bracket (SST vs SAS) shifts peak τw by +7.4%, ΔP by +3.1%; we carry these as additive bounds.

Applicability and limitations
- We validated at Re ≈ 3,500; use spans 2,000–5,000. Extrapolation at the high end flagged; SAS check at Re ≈ 4,800 did not show new separation modes. Not capturing RBC‑scale hemolysis physics; leaflets assumed rigid; wall compliance neglected. Results are for design screening only.

Process quality and oversight
- Software QA: CI pipeline runs 32 regression CFD cases on each merge; mesh generator unit‑tests element quality metrics.
- Independent look: External SME (J. Patel, ex‑Medtronic) reviewed decks and post‑processing; suggested weaker gradient limiting—implemented; no impact on ΔP beyond 0.2%.
- Configuration control: Any geometry change >1 mm, waveform shape >5%, or property shift beyond stated bounds triggers rerun. Next check: new PIV at Re ≈ 4,500 (scheduled Q4) to extend evidence.

Bottom line: For the stated use, numerical errors are small compared to measurement noise, lab agreement is within 5–7% on key metrics, and uncertainty drivers are understood. Proceed with design ranking using ΔP and peak τw, carrying the model‑form bracket noted above. We’ll update the package after the Re ≈ 4,500 campaign.
