"""Phase 2.5 — rule refinement loop tooling.

Implements UofA_Phase2_5_Rule_Refinement_Spec_v0_1.md with four
documented adaptations (auto-mode metric-gated accept, PR-curve
plotting, W-AL-02 skipped, stretch goals enabled).

Operates against the M5 dataset under `out/adversarial/phase2/2026-04-26/`
in read-only mode; all Phase 2.5 outputs land under
`out/phase2_5/2026-04-27/`. The M5 outcomes.csv is never overwritten.

Modules:

    split.py            — train/dev/holdout per rule (stratified, seed=20260427)
    metrics.py          — compute_metrics + AFFECTED_RULES splice + holdout enforcement
    inspect_misfires.py — sample misfires for the propose step
    propose_revision.py — LLM-drafted predicate diff + rationale
    refine_loop.py      — auto-mode metric-gated orchestrator
    plot_pr.py          — per-rule trajectory + catalog milestone scatter
    log.py              — refinement_log.jsonl reader/writer + predicate SHAs

Constants live in `metrics.py` so importing splice tables is cheap.
"""
