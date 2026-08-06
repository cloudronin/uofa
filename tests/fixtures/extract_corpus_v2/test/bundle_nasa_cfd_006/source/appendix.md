# Appendix A: Mesh and Convergence Details

A1. Mesh statistics
- Coarse: 4.3 million cells; 28 prism layers; first-layer height 6.2e-6 m; growth 1.25; outer boundary at 20c.
- Medium: 8.7 million cells; 30 prism layers; first-layer height 4.9e-6 m; growth 1.22.
- Fine: 17.5 million cells; 30 prism layers; first-layer height 4.2e-6 m; growth 1.20.

A2. Residual drops (fine grid)
- Continuity L2: 1.7e-1 → 6.3e-8
- Momentum-x L2: 2.2e-1 → 7.4e-8
- Momentum-y L2: 1.9e-1 → 8.2e-8
- Momentum-z L2: 1.8e-1 → 9.1e-8
- Turbulence variable: 2.1e-1 → 3.3e-7
- Final 1,000-iteration force standard deviation: σ(CL) = 1.9e-4; σ(CD) = 2.8e-4

A3. Time-to-solution (192 MPI ranks)
- Coarse: 2.1 hours
- Medium: 5.4 hours
- Fine: 12.8 hours

# Appendix B: Validation Metrics Computation

B1. Cp RMS error
- E_RMS = sqrt( Σ_i (Cp_pred,i − Cp_test,i)^2 / N )
- Computed over matching tap x/c points; excluded outliers per AR-138 errata.

B2. Validation ratio (Whitney–Coleman type)
- VR = |δ| / U_combined, where δ is prediction-test difference and U_combined is root-sum-square of test and prediction uncertainty (numerical + input + model-form).
- For CL: δ = −0.0006; U_combined = 0.0063 → VR = 0.095 (conservative VR quoted in main text was 0.42 using a narrower, numerical+test-only bound; both pass standard acceptance).

# Appendix C: Scripts and Reproduction Notes

C1. Run script excerpt
- make-run.sh sets environment modules, copies tagged meshes (SHA-256: 33d0c…a1e2), and launches FUN3D with control file fun3d.nml.
- Post-processing with scripts/calc_coeffs.py and scripts/plot_cp.py; outputs CSV and PNG with stamped commit ID.

C2. Randomness and determinism
- FUN3D uses deterministic updates for SA on fixed grids; floating-point reductions across MPI ranks can alter round-off at 1e-15 scale. Observed impact negligible on integrated metrics.

# Appendix D: Peer Review Notes (abridged)

- Reviewer requested independent SST run: completed; results fell within sensitivity envelope.
- Recommendation to verify y+ at root corner: addressed; added local mesh refinement patch (ΔCL < 0.0001, ΔCD < 0.0001).
- Suggestion to test HLLC flux: done; drag sensitivity documented.

# Appendix E: Range-of-Validity Checklist

- Physics match: compressible, transonic, attached or mildly separated — yes.
- Geometry similarity: swept wing without high-lift devices — yes.
- Flow quality: low Tu assumed; if higher Tu or surface roughness present, reassess transition.
- Operating window: M∞ [0.82, 0.86], α [2.5°, 3.5°], Re ±15% — supported by evidence.
- Extrapolation warning: beyond α ≈ 3.8°, separation may invalidate RANS closure assumptions used here.

# Appendix F: Data Sources

- AGARD AR-138: ONERA M6 wing pressure distributions and forces.
- AIAA DPW-III archives: community results for comparison bands.
- FUN3D User Guide and Verification Suite: MMS case descriptions.

End of appendix.
