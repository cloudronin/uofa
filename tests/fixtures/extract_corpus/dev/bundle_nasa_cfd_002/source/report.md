# INTERNAL TECHNICAL MEMO

**TO:** Dr. Priya Nambiar, Project Lead — Centrifugal Pump CFD Program
**FROM:** Marcus Hollenbeck, V&V Engineer
**DATE:** 14 March 2025
**RE:** V&V Status Summary — Impeller Stage Flow Solver, Pre-PDR Checkpoint

---

Priya,

Here's a quick rundown of where we stand on the simulation credibility work ahead of the PDR. I'll flag what's solid, what's partial, and what we haven't touched yet. Bottom line up front: the solver is in reasonable shape for design-trend use, but I'd be cautious about using the current results for absolute performance guarantees until a few gaps are closed.

---

## Solver Pedigree and Code Checks

The flow solver in use is ANSYS Fluent 2023 R2, running steady RANS with the SST k-ω turbulence closure. We ran a basic set of manufactured-solution tests earlier in the program on canonical geometries (backward-facing step, fully developed pipe flow) and the observed convergence rates matched the expected second-order behavior for the pressure-velocity coupling scheme. That gives us reasonable confidence that the numerical machinery is doing what it's supposed to do on smooth problems. No issues to flag there — the code behaves as advertised by the vendor for these problem classes.

---

## Mesh Refinement Study

We conducted a three-level mesh refinement study on the impeller passage using structured hexahedral grids at approximately 1.2M, 3.8M, and 9.6M cells. The Grid Convergence Index (GCI) for total-to-total pressure rise at the design point came out at roughly 2.3% between the medium and fine meshes, which is acceptable for this phase. The coarse-to-medium jump was larger (~8.1%), confirming the coarse mesh is not suitable for production runs. All production cases are being run on the medium mesh (3.8M cells) as a compromise between fidelity and turnaround time.

One caveat: the GCI analysis was only performed at the design operating point (Q = 0.042 m³/s). We haven't repeated the refinement study at off-design conditions (partial load or overload), and the mesh topology near the volute cutwater is known to be coarser than ideal. I'd flag this as an open item.

---

## Boundary Conditions and Input Fidelity

Inlet total pressure and temperature profiles were derived from upstream pipe measurements taken during the vendor's factory acceptance test (FAT) in January. The radial non-uniformity in the inlet velocity profile is modest (~4% variation across the annulus) and has been represented as a spatially-averaged uniform inlet in the CFD model. This simplification was a deliberate choice to reduce setup complexity for this phase — whether it matters will depend on how sensitive the impeller loading is to inlet swirl, which we haven't quantified yet.

Outlet boundary conditions use a pressure-outlet with a target static pressure set to match the test loop back-pressure. Rotational speed is fixed at 2,950 rpm per the test specification.

---

## Comparison Against Physical Test Data

We have three sets of pump performance curves from the vendor (delivered February) covering total head, shaft power, and hydraulic efficiency across a flow range of 0.020–0.065 m³/s. The CFD predictions at design point agree to within 1.8% on total head and 3.4% on shaft power, which is within the range we'd expect for this class of pump and this level of modeling. At off-design conditions, particularly below 60% of design flow, the head prediction diverges by up to 9%, which is likely tied to the recirculation onset that RANS handles poorly. This is a known limitation and has been communicated to the design team.

No internal flow field measurements (e.g., PIV or LDV) are available for this geometry. The validation dataset is therefore limited to integral performance metrics, which means we can't confirm the local flow structure is correct even when the global numbers look reasonable.

---

## Uncertainty in Physical Measurements

The test data uncertainty breakdown provided by the vendor lists ±0.8% on flow rate (Coriolis meter, calibrated), ±1.1% on differential pressure (Rosemount 3051), and ±1.5% on shaft torque (in-line torque flange). These are 95% confidence intervals per the vendor's calibration certificates. We've used these to construct error bars on the validation plots, and the CFD results fall within the combined uncertainty band at design point. This is a meaningful result, though the relatively wide torque uncertainty does limit how tightly we can validate efficiency.

---

## Applicability of the Model to the Intended Use

The simulation is intended to support impeller blade angle optimization for a single-stage, water-handling centrifugal pump operating in the specific speed range Ns = 800–1200 (US customary). The CFD model geometry, fluid properties, and operating conditions are directly representative of this application. We are not extrapolating to multiphase flow, non-Newtonian fluids, or significantly different specific speeds. The scope is well-matched to the model's demonstrated range.

That said, the turbulence model choice (SST k-ω) has known weaknesses in strongly adverse pressure gradient regions and in predicting onset of rotating stall — both of which are relevant at off-design. This is documented in the limitations section of the simulation plan.

---

## What We Haven't Addressed Yet

A few areas are explicitly out of scope for this phase and will need to be picked up before final design sign-off:

- **Transient behavior:** We have not run any time-accurate simulations. Rotor-stator interaction, pressure pulsations, and unsteady loading on the impeller blades are all deferred to Phase 2. The current steady-state approach cannot address these phenomena.
- **Sensitivity to turbulence model selection:** We ran the production cases exclusively with SST k-ω. A comparison against, say, the realizable k-ε or an RSM closure hasn't been done. Given schedule pressure, this was deprioritized, but it does mean we can't quantify how much of the off-design discrepancy is attributable to turbulence model choice versus mesh or BCs.
- **Software configuration control:** I need to confirm with IT whether the Fluent license version used for the GCI study matches the version used for all production runs. There was a minor patch update (2023 R2 → 2023 R2.1) mid-program that may or may not affect results. This is a documentation gap more than a technical one, but it should be closed before PDR.
- **Independent review of simulation setup:** No one outside our immediate team has reviewed the case setup files, boundary condition choices, or post-processing scripts. Given that this work is informing blade geometry decisions, a peer check by someone not involved in the original setup would be prudent. We haven't scheduled this yet.

---

## Summary Assessment

For the purpose of design-trend guidance and relative comparison between impeller variants, the current CFD setup is credible and fit for purpose. The mesh refinement study is adequate at design point, the validation against integral performance data is reasonable, and the solver code behavior is consistent with expectations.

For absolute performance guarantees or off-design certification, additional work is needed — specifically the transient analysis, turbulence model sensitivity study, and expanded validation at off-design points.

I'm available to discuss any of this before the review. Happy to put together a more formal write-up if the PDR package requires it.

— Marcus
