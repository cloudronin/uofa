# `tools/phase2_5/` — Phase 2.5 catalog refinement tooling

This directory contains the metric-gated rule-tightening pipeline that
produced the v0.5.7 → v0.5.15.1 catalog refinements. It accumulated
during 4 weeks of rapid iteration; this README documents the script
taxonomy.

## How to navigate

| Goal | Entry point |
|---|---|
| Run the refinement loop on a rule | `python -m tools.phase2_5.refine_loop --rule W-EP-01` |
| Lock in metrics after a corpus regen / predicate edit | `python -m tools.phase2_5.lock_in --rule <ID> --new-outcomes <csv>` |
| Patch the NC corpus (W-ON-02 / W-AR-02 / W-CON-04) | `python -m tools.phase2_5.regen_nc_envelope` etc. |
| Audit a fresh-generated corpus for compliance | `python tools/phase2_5/audit_phase_b.py <corpus-dir>` |
| Inspect cases the rule misfired on | `python -m tools.phase2_5.inspect_misfires` |
| Plot PR trajectory across iterations | `python -m tools.phase2_5.plot_pr --rule <ID>` |

## Script taxonomy

### Refinement loop (the core orchestration chain)

| Script | Role |
|---|---|
| `refine_loop.py` | Main metric-gated loop — proposes / applies / measures predicate edits |
| `lock_in.py` | Locks a rule's predicate when metrics enter the target zone (recall ≥ 0.90, nc_fpr ≤ 0.10); writes the milestone CSV + holdout-spend lock |
| `propose_revision.py` | Generates candidate predicate edits (LLM-driven, one revision at a time) |
| `log.py` | JSONL audit log (`refinement_log.jsonl`); the canonical record of every iteration |
| `log_decision.py` | Decision log (`decision_log.csv`); per-iteration accept/revert/lock summary |
| `metrics.py` | Train/dev/holdout metric computation; recall, nc_fpr, bystander_rate, precision, specificity |
| `split.py` | Stratified train/dev/holdout splitter per rule (per Phase 2.5 spec §3) |

### Corpus regeneration (per-rule NC patch tools)

| Script | Version | Purpose |
|---|---|---|
| `regen_nc_envelope.py` | v0.5.10 (W-ON-02) | Inject placeholder `hasApplicabilityConstraint` + `hasOperatingEnvelope` into NC COUs |
| `regen_nc_offset_rationale.py` | v0.5.11 (W-AR-02) | Inject placeholder `hasOffsetRationale` on Accepted-with-shortfall DRs |
| `regen_nc_consistency.py` | v0.5.12 (W-CON-04) | Inject `hasSensitivityAnalysis` (boolean per v0.5.15.1 fix) on Complete-profile NCs |

Each builds a **hybrid batch dir** at `dev/build/adversarial/phase2/<date>-v0.5.X/`
that symlinks the pristine source dirs (CE / GP / interaction) and
materializes a real `negative_controls/` with patched + re-signed NCs.
This pattern is reusable for future per-rule NC patches.

### Phase 2 v3 audits (tool-use migration validation)

| Script | Phase | Purpose |
|---|---|---|
| `audit_phase_a.py` | Phase A | Field-presence + integrity + per-NC rule-firing audit on production CLI output |
| `audit_phase_b.py` | Phase B | Field-presence audit with substantive-content metrics on fresh corpus |
| `pilot_tool_use.py` | Phase A pilot | 5-package tool-use sanity test against NC-2 |
| `run_phase_a.sh` | Phase A | Driver script: source key, run cost preview, run live generation |

### Analysis & diagnostics

| Script | Purpose |
|---|---|
| `inspect_misfires.py` | Sample / visualize misfire cases per rule |
| `plot_pr.py` | Per-rule PR trajectory + catalog-milestone scatter PNGs |
| `verify_sentinels.py` | Sentinel-pool validation (loosening detection) |

### Tests (`tests/`)

| Test | Coverage |
|---|---|
| `test_log.py` | predicate_sha, IterationRecord roundtrip, JSONL append/read, per-rule filtering |
| `test_metrics.py` | Metrics construction, epoch selection, rule-set filtering |
| `test_refine_loop.py` | `_replace_rule_body`, full loop orchestration |
| `test_split.py` | Split logic, rule indexing |

Run with: `pytest tools/phase2_5/tests/`

## Outputs

All Phase 2.5 outputs land in `dev/build/phase2_5/shared/` (cumulative
artifacts) and `dev/build/phase2_5/v0.5.X-*/` (per-version summary docs).
A back-compat symlink `dev/build/phase2_5/2026-04-27 → shared` keeps the
pre-Phase-C path working for one release cycle. See
[`dev/build/phase2_5/README.md`](../../dev/build/phase2_5/README.md) for the
output-directory index.

## Cross-references

- Phase 2.5 spec: `docs/m5_findings.md`, `docs/phase2_runbook.md`
- Top-level repo orientation: `docs/repo-layout.md`
- Schema definitions (vs adversarial specs): see `spec/README.md` + `specs/README.md`

## Reorg history (post-Phase-2.5 cleanup, complete as of 2026-04-29)

- **Phase C** (commit 7df4ba0) — subdivided this directory into
  `refinement_loop/`, `corpus_regen/`, `audit/`, `analysis/` subpackages
  with deprecation shims at the old top-level paths.
- **Phase C** also migrated the seven cumulative-path tool defaults
  from `dev/build/phase2_5/2026-04-27/` → `dev/build/phase2_5/shared/`.
- **Phase D** renamed the parent `out/` → `build/`.
