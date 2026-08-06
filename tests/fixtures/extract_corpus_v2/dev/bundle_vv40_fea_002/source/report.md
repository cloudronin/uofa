To: Ava Morales, Structures Lead
From: R. Chen, CAE
Date: 06 Aug 2026
Subject: Status check on FEA of rear carrier bracket — preliminary credibility readout

Summary
We used Ansys Mechanical 2023 R2 to evaluate the aluminum rear carrier bracket (PN RBK-212) for the e-mobility platform. The immediate decision is whether this geometry can be locked for mounting-hole location and general envelope while the supplier kicks off tooling. The analysis covers static torque from worst-case braking and a first-mode target to avoid frame resonance. On the static side, predicted hot-spot stress sits just below our allowable; the first bending mode is under the target if the bracket is modeled as a stand-alone part. Because we did not include clamp-up and adjacent structure, I’m treating the dynamic result as conservative.

Problem definition and loads
- Part: CNC-machined 6061-T6 bracket with a 0.5 mm edge radius at the interior fillet, as per latest CAD (rev H).
- Constraints: Contact faces at the two M8 bosses tied to ground via fixed supports (representing rigid frame lugs).
- Loads: 1.2 kN lateral force applied at the pannier attach point, 95 mm from the boss line of action, representing brake spike + rider input (load vector resolved from the Vehicle team’s worst-case sheet).
- Target criteria: von Mises < 275/1.5 = 183 MPa at 25 C; first bending mode > 220 Hz.

Modeling choices
- Element type: 10-node tets (SOLID187 equivalent). Local refinement at the inner fillet and the bolt pads; rest of the volume on a growth rate of 1.2.
- Contacts: Boss faces treated as bonded to frame; no pretension or friction modeled.
- Material: 6061-T6, E=69 GPa, ν=0.33, σy=275 MPa, density 2700 kg/m^3 (datasheet values from Kaiser).
- Analysis steps: Linear static; separate undamped eigen-solve for the first six modes. Geometric nonlinearity left off (max strain << 0.2%).

Element-size sweep and solver notes
- Mesh A (coarser): 2.5 mm global, 0.8 mm at the fillet; 410k DOF.
- Mesh B (finer): 1.6 mm global, 0.5 mm at the fillet; 1.05M DOF.
- The max von Mises at the fillet moved from 176 MPa (A) to 182 MPa (B), a 3.4% increase. Tip deflection at the pannier point shifted 1.1% between meshes.
- Sparse direct solver with pivot check on; default contact stiffness since all interfaces are tied.
- Quick hand calc using a cantilever idealization (same section properties at the neck) gives 1.04 mm vs FEA 0.98–0.99 mm at the load point (≈5–6% difference), acceptable for a sanity check.

Results snapshot
- Peak stress: 182 MPa at the inner fillet toe on Mesh B. Local gradient indicates a geometric feature, not a sharp singularity.
- Displacement: 0.99 mm at the pannier eyelet.
- First bending mode (part only): 205 Hz with nodal line through the mid-span. With clamp-up and frame stiffness included, prior assemblies of similar topology picked up 20–30 Hz. We should expect 225–235 Hz once fastener clamp and interface stiffness are in the model.
- Reaction forces at bosses balanced within 0.5% of applied load moments.

What gives confidence vs. where it’s thin
- The element-size sweep shows the hot-spot stress settling; displacement barely moves with refinement. The hand calc tracks the overall compliance within a few percent, suggesting the global stiffness is captured.
- Assumptions that might sway outcomes:
  - No bolt preload modeled. Clamp-up generally raises local frequencies and reduces bending at the fillet.
  - Frame lugs treated as perfectly rigid. In reality, some compliance will shift load share and the mode shape.
  - Thermal effects, surface finish, and residual stresses not considered at this phase.

Open items we did not address in this round
- Assembly-level dynamics with realistic joint stiffness.
- Alternate load paths (e.g., curb strike vectoring differently into the bracket).
- Fillet radius tolerance study; only the nominal 0.5 mm was run.

Recommendation and decision
Given the above, the model is fit to answer the narrow question of “Can we hold the hole pattern and outer envelope while we firm up the joint model?” Static margin is razor-thin but positive (≈1 MPa below allowable at nominal). The frequency shortfall on the free part is expected to clear once clamp-up is included; however, that is not demonstrated here.

Decision: accepted for preliminary layout and bracket topology freeze, subject to adding a 1 mm web in the neck region and re-running the assembly-included modal case before release to manufacturing. Not approved for final sign-off or durability claims at this time.

Approved by: A. Morales (Structures Lead), with the above scope and conditions.
