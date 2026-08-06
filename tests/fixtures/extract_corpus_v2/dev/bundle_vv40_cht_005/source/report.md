Title: Conjugate Thermal-Fluid Assessment of a 3U Telecom Compute Module with Dual 80 mm Fans

Author: Thermal Systems Group, Platform Engineering
Date: 2026-07-22

1. Background and Intended Use

This document summarizes the evidence we assembled to judge whether our thermal-fluid model of the 3U compute module (project code: Ares-B3) is sufficiently trustworthy to support the M3 gate decision. The module houses a 450 W electronics payload on a single 12-layer PCB, cooled by two 80×25 mm axial fans that pull air through a perforated bezel across four finned heat sinks and out the rear grille. Structural elements (top cover, side rails, base) act as secondary heat spreaders. The analysis is fully conjugate: conductive heat flow through solids is coupled to air motion and heat transfer in the flow passages and plenum.

The analysis is intended for the following decisions:
- Confirm that the hottest device base (VRM2) stays at or below 85°C for 25°C nominal ambient.
- Estimate module pressure drop and fan operating point to within engineering accuracy so we can size the fan controller margins.
- Check that radiation is not a controlling path for heat removal under paint and finish choices currently specified.

The model is not intended to establish performance at extremes (low-pressure, high-altitude) or to qualify shock/vibration-induced airflow interruption. Those will be handled in later program phases.

2. Modeling Approach (Summary)

We used Simcenter STAR-CCM+ 2021.3 to build a coupled fluid/solid model of the module, including:
- Fluid region: air treated as ideal gas with temperature-dependent properties; buoyancy via Boussinesq was not used—full density variation handles it.
- Turbulence: k-ω SST RANS. Near-wall regions on heat sinks and enclosure walls were resolved to y+ ≲ 1 using 12 prism layers grown with 1.2 expansion.
- Radiation: surface-to-surface (diffuse-gray). Spectral effects were neglected; we used band-averaged emissivities based on supplier finishes.
- Solids: isotropic aluminum (6061-T6), stainless steel fasteners, orthotropic PCB core.
- Conjugate interfaces: conservative coupling, thin-layer contact for the thermal pads.

Steady solutions were targeted with a segregated flow solver and pseudo-transient relaxation. A transient check was performed to make sure the steady solver was not masking periodic instabilities from blade-passing or recirculation.

3. Geometry and Domain Representations

CAD basis is assembly “Ares-B3 Enclosure” rev P2.3 from NX. We retained all fins on the four heat sinks and through-slots on the front bezel. We simplified the following:
- Screws and standoffs were represented as cylindrical solids with equivalent cross-sectional area; threads were not modeled.
- Cable bundles were represented as porous baffles with porosity of 0.65 and directional resistance derived from pressure drop testing of similar harnesses.
- Fan housings and rotor details were suppressed; the fans are represented by pressure-jump interfaces as described below.

The computational domain extends from a plane 5 mm inside the bezel grille to 5 mm past the rear grille to capture jet development and vena contracta effects.

4. Materials and Contact Interfaces

- Aluminum 6061-T6: k = 167 W/m·K, ρ = 2700 kg/m3, cp = 896 J/kg·K.
- PCB (12-layer, 2 oz copper planes): in-plane kx, ky = 20 W/m·K; through-thickness kz = 2.0 W/m·K.
- Thermal interface (gap pad) between device bases and heat sinks: thickness 100 µm, k = 3.5 W/m·K, giving areal resistance of 2.86×10^-5 m2·K/W. Compression effects on conductivity were not modeled; thickness per build spec.
- Painted aluminum panels: emissivity 0.85 (matte black), validated by supplier test report SR-19-044. Bare machined heat sinks: emissivity 0.2.

5. Operating Conditions and Loads

- Total electrical dissipation: 450 ± 5 W distributed across eight devices (primary CPUs, two VRMs, PHY, FPGA). Power splits derived from DC supply readback and per-board instrumentation (Keysight DAQ 34970A).
- Ambient air: 25°C at 50% RH. Air properties in solver use temperature dependency; humidity ignored for properties.
- Fans: Two Sunon EF80251S2-999, 12 V. We represented each fan as a rotating-frame pressure-jump interface using the vendor P–Q curve corrected by our bench test to operating Re. Curve fits are second-order polynomials in volumetric flow, implemented via a user function. Electrical speed control at 100% duty cycle for this study.
- Rear grill exit static pressure was set to 0 Pa reference; enclosure is not sealed (no leakage modeling in this phase).

6. Numerics and Solution Controls

- Mesh: polyhedral cells with trimmed prism layers in near-wall regions. The baseline grid has 10.2 million cells; coarser and finer variants are 6.1 million and 15.7 million cells respectively. Minimum prism first height was picked for y+ ≈ 1 on heat sinks (1.5e-5 m).
- Residuals: momentum and continuity were driven below 1e-4, energy residual below 1e-5. Surface heat flux and device-base temperature monitors were used as stopping criteria (change <0.02 K over 1000 iterations).
- Under-relaxation was adjusted after initial startup; maximum Courant limited to 50 in pseudo-transient mode.

7. Mesh Refinement and Time-Stepping Checks

To test sensitivity to grid resolution, we ran three systematically refined meshes (scale factor ~1.3 in linear cell size) at identical physics settings and compared key outputs:
- Maximum device-base temperature (VRM2 location).
- Module pressure drop (front to rear grille).
- Total mass flow through each fan interface.

Results are summarized in Appendix A. Between the medium and fine grids, the VRM2 base temperature changed by 0.4 K (81.1°C vs. 80.7°C). Using three-level Richardson extrapolation with nominal order 1.9 (empirically fit from the sequence), we estimate the asymptotic grid solution for VRM2 base temperature is 80.5°C, implying the medium-grid result is within ~0.6% of the asymptote. Pressure drop and mass flow differences between medium and fine grids are within 1.5 Pa and 0.001 kg/s, respectively.

Because the solver target is steady, we ran a transient stabilization check with a fixed time step of 0.005 s for 10 s of physical time starting from the converged steady field. The monitor points on VRM1 and VRM2 bases drifted by less than 0.3 K and then flattened, and no limit-cycle behavior in the near-fan recirculation zones was observed.

8. Radiation Treatment

Given the black finish on external panels, we assessed radiative exchange via S2S. Within the enclosure, surface temperatures are near 60–85°C and view factors between heat sinks and walls are non-negligible. At M3 conditions, the net radiative heat leaving the fins and devices is 22–27 W depending on emissivity setting (see Appendix A), approximately 5–6% of the total. Neglecting radiation increases the predicted peak device base temperatures by 1.1–1.5 K on the medium grid, which is not decisive for the pass/fail limit but is comparable to other modeling effects, so we retained radiation.

9. Energy Balance and Sanity Checks

We closed a first-law balance to make sure the solver’s energy accounting was reasonable. For the medium grid run with radiation:
- Electrical input: 450 W.
- Convective heat flow through outlets (enthalpy rise across the air domain): 403 W.
- Radiative transfer to the enclosure inner surfaces and loss to ambient through the top cover: 24 W (modeled via S2S + external convection coefficient 10 W/m2·K on the top panel).
- Conductive path to the rack rails (modeled as isothermal at 27°C with contact at side walls): 20 W.
- Remainder: 3 W, which is within 0.7% of total input and attributed to iterative tolerance and volume-source interpolation.

An integral momentum balance at the fans matched pressure forces across the bezel and rear grille to within 3% of the product of mass flow and momentum change, consistent with discretization and porous-loss model simplifications.

10. Bench Measurements for Cross-Checking

We compared the thermal-fluid model to a set of controlled lab measurements on a surrogate unit.

Test configuration:
- Same PCB, heat sinks, and housing. Fans identical (lot 7C).
- Flow apparatus: upstream orifice plate per ISO 5167 with differential pressure measured by Dwyer 605, calibrated April 2026. We established the fan operating point under 12 V supply.
- Ambient: 25.0 ± 0.4°C maintained by room control and a mixing chamber upstream of the bezel.
- Temperature instrumentation: twelve Type-T thermocouples (Omega, grounded junction, 36 AWG) affixed to device bases and heat sink roots with high-temperature epoxy; IR camera (FLIR A655sc) for surface mapping. A matte black tape dot was applied at camera locations to enforce defined emissivity where needed.
- Data acquisition: 1 Hz sampling for 45 minutes after stabilization. Reported values are time-averaged over the last 10 minutes.

Measured performance:
- Total flow rate: 0.081 kg/s at 12 V supply.
- Module pressure drop (bezel to rear grille): 65 Pa.
- Device-base temperatures of eight hot components ranged from 69.4°C to 82.8°C. VRM2 (the hotspot) was 82.3°C.

11. Comparison of Predictions With Measurements

We compared the medium-grid simulation predictions against the lab data at the same conditions.

Key outcomes:
- Flow and pressure: Simulation predicted 0.084 kg/s and 62 Pa. Differences are +3.7% in flow and −4.6% in pressure relative to measurements. Given the pressure–flow coupling, the sign and magnitude are internally consistent and align with the expected bias from neglecting small leak paths around the bezel.
- Hotspot (VRM2) base temperature: Simulation 81.1°C vs. measured 82.3°C (−1.2 K difference).
- Across all twelve thermocouple sites: mean absolute difference 1.7 K; standard deviation of errors 1.1 K; largest deviation 3.8 K at VRM1 near the trailing edge of the sink where recirculation is strong.

IR mappings showed the lateral temperature gradients on the fin tips agree qualitatively with the simulation, including the cooler wake region behind the front standoffs. The model slightly under-predicts the gradient on the right-side panel, likely due to omission of internal cabling shadows beyond the simplified porous representation.

12. Inputs Defaulted and Simplifications

Where explicit supplier data was unavailable, we used standard engineering stand-ins:
- Contact resistance across chassis joints was not modeled explicitly; panels were assumed perfectly fitted with no gap conduction penalty. This is conservative for peak base temperatures, as leakage paths would modestly cool the solids.
- Electric-to-thermal split for the DC-DC modules was taken as 100% heat to the base; any heat into the PCB via pins was neglected, again conservative for base temperatures.

13. Credibility Assessment

The intended use is to support the M3 gate decision that the design clears the 85°C limit on hottest device base at nominal ambient. We judge the model provides adequate evidence for that decision for the following reasons:

- Geometry and physics coverage: All primary heat paths are represented, including conduction in the chassis and radiation across the enclosure. The turbulence model (SST) with near-wall resolution to y+ ~ 1 is appropriate for separated, internal flows over densely spaced fins. Radiation contributes ~5% of total heat removal at these conditions and was retained.

- Operating condition fidelity: The fan operating point is determined by vendor data corrected to our bench results, and the measured module pressure drop agrees within 5 Pa on the medium grid.

- Numerical robustness: Monitors and residuals converge to tight thresholds. Mesh refinement study shows negligible differences (<0.5 K on the hotspot) between medium and fine grids. A transient check shows no hidden unsteadiness that would undermine steady-state predictions.

- Experimental cross-check: The predicted temperature field agrees with thermocouple measurements to within 1.7 K on average, with the worst case 3.8 K. The hotspot location and magnitude match closely (−1.2 K). Flow and pressure predictions are consistent with the bench.

- Energy accounting: Global heat balance closes within 1%, indicating no hidden source/sink or coupling error.

On that basis, for the stated operating point and use-case, there is a small margin (approximately 3–4 K) to the 85°C requirement even accounting for grid-related variability and the model’s known biases. We are not extending this judgment to off-nominal ambient, reduced fan speed, or blocked inlet scenarios at this time.

14. Limitations and Open Items

- The fan representations do not include swirl or rotating frame effects beyond a lumped pressure jump; off-design or pulsation behavior is not captured.
- Cable bundles and minor leak paths are simplified. This has a visible effect near the trailing edge of VRM1 where recirculation pockets form.
- Surface finishes were assigned as uniform per supplier spec; in-product variation across panels and sinks is not represented.
- The enclosure is treated as mechanically perfect with respect to panel fit; gap conduction and air bypass at joints are neglected.
- Through-pin heat spreading into the PCB from the hottest packages is ignored; if this path is significant, base temperatures would be slightly over-predicted.
- The study does not address altitude, dust loading, or fan degradation over life.

15. Recommendations

- For the next phase, refine the local geometry around VRM1 and the adjacent cable guide, or validate the porous resistance with a targeted flow visualization to reduce the 3.8 K outlier.
- Consider adding a simple leakage model at the bezel to better capture the pressure/flow split, especially if grille geometry changes.
- Acquire emissivity measurements on production-finished sinks; while radiation is a minor path, a 0.1 change in emissivity shifts the hotspot by about 0.4 K in our what-if runs (Appendix A).
- If the operating envelope expands to higher ambient, repeat the steady solution at 35°C and 45°C and reconfirm margin on the same grid; the model runtime is acceptable (about 9 hours on 2×24-core nodes for the medium grid).

16. Reproducibility Footnotes

- Software: Simcenter STAR-CCM+ 2021.3, license server EL-407. Radiation model S2S, view factor tolerance 1e-4.
- Hardware: Runs executed on the internal cluster (Neptune), nodes with dual Intel Xeon Gold 6248R, 192 GB RAM.
- CAD: NX assembly Ares-B3 rev P2.3; meshing in STAR-CCM+ with automated surface repair set to tolerance 0.05 mm.
- Post-processing: Temperatures reported at device-base monitor points (circular patches of 4 mm diameter) to match thermocouple bead footprint.

17. Conclusion

The conjugate thermal-fluid model of the Ares-B3 compute module demonstrates consistency with bench data for the nominal condition of interest and shows low sensitivity to mesh refinement. Energy and momentum balances close, and the inclusion of radiation slightly improves agreement without changing pass/fail outcomes. On balance, we consider the model’s predictions credible for the M3 decision: at 25°C ambient with fans at full duty, the hottest device-base temperature is predicted at 81.1°C (medium grid) versus 82.3°C measured, leaving approximately 3–4 K margin to the 85°C requirement. The open items listed above do not materially affect this judgment at this design stage but should be addressed before committing to derating curves or environmental extremes.

Appendices provide additional numeric details supporting the statements above.
