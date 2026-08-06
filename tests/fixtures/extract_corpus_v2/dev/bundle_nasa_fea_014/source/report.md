# FEA Credibility Notes — Avionics Bracket for SmallSat Bus

- Scope
  - Structural analysis of the aluminum avionics bracket that supports the X-band transceiver and harness clamps on the SmallSat bus panel P3.
  - Primary decision supported: fly/no-fly for CDR based on margins under quasi-static and random-launch environments.
  - Tooling: ANSYS Mechanical with quadratic tets for the bracket and pretension elements for bolts; postprocessing in nCode for stress ranges.

- What “good enough” looks like for this use
  - Minimum margins: ≥1.4 on yield in static combined-load case; ≥1.2 on ultimate for fasteners.
  - First natural frequency target: >150 Hz with free-free cable representation (soft springs).
  - Limit strain at gage locations to <0.18% during vibe to preclude plasticity in local features.

- Geometry, representation, and simplifications
  - CAD from PDM rev. C; fillets smaller than 0.8 mm suppressed to avoid poorly shaped tets in tight creases.
  - Boss/thread features replaced with through-holes and head-bearing surfaces; washers modeled as rigid rings to capture load spread.
  - Bolts: A286 M4s represented by beam shafts with pretension sections and rigid spiders tying head and nut to hole perimeters.
  - Cable bundle added as distributed 30 g point mass on the upper flange through soft links (5 N/mm each).
  - Contacts: bracket-to-panel bonded; beneath bolt heads and nuts treated as no-separation to allow lift-off but no slip.
  - Rationale: local thread-level stress not needed for system decision; focus is bracket stress and joint forces.

- Loads and supports
  - Quasi-static: directional accelerations per launch provider ICD: +Z 15 g, ±X/±Y 9 g, combined with 1.25 load scale on the worst axis.
  - Random vibe: NASA GEVS small payload curve, 20–2000 Hz, 0.033 g^2/Hz plateau, 9.7 g RMS, applied at panel mounting plane.
  - Cable preload: 15 N via harness clamps (two locations), represented as concentrated forces with 20° skew out of plane.
  - Bolt preloads: 4.0 kN per M4, introduced via pretension sections; torque-to-clamp conversion per fastener vendor note.
  - Constraints: panel interface defined by 8 countersunk screws to the CFRP panel; panel represented as orthotropic shell submodel with fixed outer perimeter, bracket tied to panel via bonded contact.

- Discretization and local refinement strategy
  - Elements: SOLID187 10-node tets for bracket and rigid rings; BEAM188 for bolts; PRETS179 for pretension.
  - Mesh levels near the critical fillet (upper flange to web):
    - Coarse: 3.0 mm average; ~120k solid elements; hotspot von Mises 212 MPa.
    - Medium: 1.8 mm average; ~410k solid elements; hotspot 226 MPa.
    - Fine: 1.2 mm average; ~930k solid elements; hotspot 231 MPa.
  - Richardson trend consistent with p≈2.0; extrapolated hotspot ~236 MPa; using fine mesh for reporting implies ~2–4% remaining local stress error.
  - Displacement at antenna lug converged within 1.2% between medium and fine.

- Materials and fastener data pedigree
  - Bracket: 7075-T7351 plate, thickness 6.0 mm. Room-temp mechanicals from MMPDS-17 A-basis: E = 71.7 GPa, ν = 0.33, σ_y = 505 MPa, σ_u = 572 MPa.
  - Panel insert rings: 7075-T73, matched to bracket for interface stiffness.
  - Bolts: A286 per NAS 1580, σ_u = 1310 MPa; proof load 1090 MPa; seating hardness modeled as rigid for conservatism.
  - Damping: 1% modal damping for bracket-only; 0.5% for bracket+panel assembly when random is applied (per heritage on similar brackets).

- Key results (fine mesh)
  - Static combined-load case (15 g Z worst-case): peak von Mises at upper flange fillet = 231 MPa; FoS_yield = 505/231 = 2.19.
  - Fastener checks: highest axial at bolt B5 = 3.2 kN tension; shear at B5 = 1.0 kN; interaction within proof envelope (margin_u ≈ 1.35).
  - Modal: first bracket-dominated mode (torsion about web) = 184 Hz with cable mass; second (bending of top flange) = 236 Hz.
  - Random response: RMS von Mises at gage G2 (upper flange midspan) = 58 MPa; 3σ peak estimate 174 MPa using narrowband assumption; cumulative damage not assessed here.

- Correlation with bench data
  - Setup: single-axis sine sweep to 15 g at 40–220 Hz on bracket+panel subassembly; three 350Ω strain gages at G1/G2/G3 along the upper flange; bolts preloaded to 4.0 kN using torque wrench at 1% accuracy.
  - Compare at 120 Hz: measured ε_G2 = 1480 με; model predicted surface strain at gage footprint = 1370 με (−7.4% difference).
  - Across 60–200 Hz band: average magnitude error 8.1%; phase lead ~6–12° observed in model vs test near 180 Hz (mode shape alignment acceptable).
  - Note: no shaker data above 220 Hz; random environment correlation pending hardware availability.

- Uncertainty propagation (focused, small set)
  - Treated as independent normals unless noted: E_7075 ±2%; bolt preload ±10% (uniform); panel boundary stiffness ±15%; load scale ±5%.
  - 500 Latin Hypercube samples; response tracked: hotspot von Mises and first natural frequency.
  - 95th percentile hotspot stress = 248 MPa; corresponding FoS_yield,95 ≈ 2.04.
  - 5th percentile first mode = 172 Hz, still comfortably above the 150 Hz target.
  - Most of the spread came from bolt preload and panel stiffness interaction; modulus had minor effect on frequency only.

- Parameter influence ranking
  - Spearman ranking across samples on hotspot stress:
    1) Bolt preload (ρ ≈ −0.52; higher preload reduces slip/lift-off at the fillet)
    2) Panel boundary stiffness (ρ ≈ −0.31)
    3) Load scale factor (ρ ≈ +0.27)
    4) Modulus (ρ ≈ +0.06)
  - Local geometry check: increasing fillet radius from 1.2 mm to 2.4 mm in a side run dropped peak stress by ~14% with negligible mass impact (+6 g); design team already captured as CR-117.

- Takeaways, caveats, and immediate next steps
  - Under current assumptions and loading, the bracket meets margins with room to spare; modes clear the acoustic band crossover.
  - Limitations to keep in mind:
    - Joint friction neglected; contact is no-separation with zero tangential stiffness, which may overpredict slip and local stress.
    - Bolt/hole clearance not represented; bearing stress probably conservative at the current modeling fidelity.
    - No temperature gradients or CTE mismatch considered; mission thermal profile shows −10 to +35 C at the panel during ascent but is not included here.
    - Random environment correlation not yet executed; sine sweep data shows acceptable trends, but wideband response needs a check.
  - Near-term actions proposed:
    - One random run on the vibe table to 6 dB below protoqual to confirm RMS strain at G2 stays under 0.18%.
    - Optional geometry tweak: adopt 2.0–2.5 mm fillet at the upper flange if machining space allows; clears the hotspot with minimal rework.
    - Maintain 4.0 kN bolt preload in work instructions; lower preloads increase variability in hotspot stress per ranking above.
