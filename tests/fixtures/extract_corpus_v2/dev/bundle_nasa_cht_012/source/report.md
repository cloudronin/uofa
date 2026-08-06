To:    Priya Nair, Avionics Thermal IPT Lead
From:  Daniel Cortez, CHT Analyst
Date:  2026-08-06
Subj:  CHT model status — electronics module with dual 40 mm blowers (Rev C)

Quick summary
We’ve reached a stable point on the conjugate thermal-fluid model for the 120 W processor module. Results are consistent with the bench rig within ~1–2% on key observables, and the analysis setup is repeatable from a clean checkout. Remaining risk is dominated by contact conductance and power mapping on the die footprint.

What we modeled
- Geometry: full heat sink (32 mm pins, 2.0 mm dia, 8 rows), housing lid and base, PCB stackup (homogenized 10-layer), die + lid + TIM2, and both 40 mm radial blowers. No cable harnesses; screw bosses included where they intrude into the flow.
- Physics: steady RANS with k-omega SST in the air; conjugate conduction in all solids with temperature-dependent k(T); surface-to-surface radiation (view factors precomputed on the housing cavity). Fan performance from the manufacturer curve applied as a pressure jump vs. flow rate.
- Coupling: segregated CHT with 10 outer loops per solve; energy URF 0.9, momentum 0.7. Interface heat-balance mismatch is under 0.3% at stop.

Numerics and grid
- Mesh: poly-hybrid; near-wall y+ mostly 30–60 on heat sink pins, wall functions used; prism layers 8 deep.
- Mesh refinement: 2.1M (coarse), 4.5M (medium), 9.8M (fine) cells. Max die temperature changed - by medium vs. fine: 1.8 C (2.2%); coarse vs. medium: 3.9 C (4.7%). We are using the fine grid for production numbers.
- Convergence: residuals below 1e-5 (energy) and 5e-4 (flow), with flat line heat rate and pressure drop over the last 500 iterations.

Comparison to lab data (Rev B hardware, heater block stand-in)
- Setup: 100.0 W ±0.5% DC into a copper heater the size of the die lid; 8 K-type thermocouples on baseplate and lid; pitot rake at outlet; ambient 24.3 ±0.2 C.
- Temperatures: measured lid centerline 78.2 C; model predicts 79.1 C (+0.9 C, 1.1%). Baseplate near screw boss: measured 63.5 C; model 62.6 C (-0.9 C).
- Flow/pressure: measured module Δp 142 ±7 Pa; model 135 Pa (-4.9%). Outlet bulk temperature rise matches within 0.3 C.
- Note: radiation turned on in both model and in the chamber (low-speed airflow, painted interior, estimated ε ~0.8 on housing).

Input data pedigree
- Materials: 6061-T6, copper lid, FR-4 effective k through-thickness fitted from IPC-2152; all k(T) from ASM Digital Library. TIM2 nominal 1.5 W/m-K (Parker Chomerics).
- Contact: heat sink-to-lid contact conductance set to 8,000 W/m^2-K derived from 1.2 N·m bolt torque using Mikic correlation; sensitivity explored below.
- Fans: Delta BFB0412 series, curve digitized from datasheet and curve-fit (R^2=0.998). Ambient density correction applied for 24–50 C.
- Power map: 70% central 10x10 mm, 30% in surrounding 18x18 mm. Based on FPGA team’s estimate.

Sensitivity highlights (single-parameter sweeps on the fine mesh)
- Contact conductance 4,000–12,000 W/m^2-K: T_die shifts +4.3/-1.7 C relative to nominal.
- Emissivity 0.1–0.9 on housing interior: T_die shifts up to 0.8 C.
- Fan curve ±10% flow: T_die changes ~1.1 C; module Δp tracks proportionally.
- Total power ±5%: T_die changes ~3.0 C; linear within this range.

Range we consider covered
- Airside Reynolds number (pin-fin hydraulic diameter) 2.2e4–3.8e4 over the expected operating flow; model closures remain in their intended regime.
- Component temperatures 30–90 C; material properties and radiation model applied over that span.
- Ambient 20–50 C and sea level to 5 km; density correction implemented for the blowers.

Reproducibility and QA notes
- Tools: Ansys Fluent 2023 R1, ICEM 2022 R2 for meshing; post via PyFluent + Paraview 5.11.
- Case and scripts under GitLab tag avx-cht-revC-2026-07-29 (commit 0f3c9c2). README includes run steps and machine file.
- Runs repeated on JSC “Merope” (32 AMD EPYC cores, Intel MPI) and local 16-core workstation; T_die agreement within 0.2 C.
- Independent check: J. Park recreated the medium mesh from the checklist and matched our 100 W case within 0.3 C on T_die and 6 Pa on Δp.

Recommendations before freezing Rev C
- Lock in a conservative band for contact conductance in the spec; current design margin absorbs +5 C headroom at 100 W if we hold 8,000 W/m^2-K or better.
- Get the FPGA team’s updated hotspot distribution; reshaping the power map had a 1.6 C effect in a quick trial.
- If time permits, confirm the fan curve at elevated inlet temperature (45–50 C) on the bench; the datasheet correction looks benign, but it’s a cheap check.

I can brief through the case tree and sensitivity scripts at tomorrow’s stand-up; total runtime per fine-grid case is ~3.9 h on 32 cores, so we can turn two what-ifs by EOD.
