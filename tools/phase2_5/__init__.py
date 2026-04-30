"""Phase 2.5 — rule refinement loop tooling.

Implements UofA_Phase2_5_Rule_Refinement_Spec_v0_1.md with four
documented adaptations (auto-mode metric-gated accept, PR-curve
plotting, W-AL-02 skipped, stretch goals enabled).

Operates against the M5 dataset under `dev/build/adversarial/phase2/2026-04-26/`
in read-only mode; all Phase 2.5 outputs land under
`dev/build/phase2_5/shared/`. The M5 outcomes.csv is never overwritten.

Subpackages (post-Phase-2.5 reorg, v0.5.15.1+):

    refinement_loop/    metric-gated rule-tightening loop (refine_loop,
                        lock_in, propose_revision, log, log_decision,
                        metrics, split)
    corpus_regen/       per-rule NC corpus patch tools (regen_nc_envelope,
                        regen_nc_offset_rationale, regen_nc_consistency)
    audit/              tool-use migration validation (audit_phase_a,
                        audit_phase_b, pilot_tool_use, run_phase_a.sh)
    analysis/           per-iteration diagnostics (inspect_misfires,
                        plot_pr, verify_sentinels)

The pre-reorg flat layout (e.g. ``tools.phase2_5.lock_in``) is kept as
a deprecation shim for one release cycle; new code should import from
the subpackage path (``tools.phase2_5.refinement_loop.lock_in``).
"""
