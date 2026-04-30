# `out/phase2_5/` — Phase 2.5 refinement output workspace

> **Note**: This directory is gitignored. The contents here are the
> empirical output of the Phase 2.5 catalog refinement work. The
> deterministic regenerator is the codebase + spec yamls; this dir
> is the artifact trail.

## Current layout (pre-reorg, as of 2026-04-29)

All Phase 2.5 outputs live under a single dated workspace:

```
out/phase2_5/
└── 2026-04-27/
    ├── refinement_log.jsonl           ← cumulative iteration log
    ├── decision_log.csv               ← cumulative decision log
    ├── milestones/                    ← per-version CSVs
    ├── predicate_diffs/               ← unified diffs per rule iteration
    ├── plots/                         ← PNG trajectories
    ├── splits/                        ← train/dev/holdout per rule
    ├── per_iter_outcomes/             ← analyze outputs per iteration
    ├── holdout_used/                  ← holdout-spend locks
    ├── review_packet.md               ← C1.5 semantic review summary (consolidated)
    └── <11 per-version summary docs>  ← see index below
```

The dated folder name `2026-04-27` reflects when the workspace was
created; actual content spans 2026-04-26 (M5 baseline) through
2026-04-29 (v0.5.15.1).

## Summary docs by Phase 2.5 version

| Version | Summary doc(s) | Highlight |
|---|---|---|
| **v0.5.7 M5 baseline** | `report.md` | Pre-Phase-2.5 corpus state |
| **v0.5.8 W-EP-01** | (predicate-diff only, no summary) | URI-handle Claim guard |
| **v0.5.9 W-AL-02** | (predicate-diff only) | UQ boolean schema-aligned predicate |
| **v0.5.10 W-ON-02** | `v0510_summary.md` | NC envelope corpus regen |
| **v0.5.11 W-AR-02** | `v0511_summary.md` | OffsetRationale schema + 2-rule pattern |
| **v0.5.12 W-CON-01/04 + W-AR-01** | `v0512_summary.md`, `v0512_audit_residuals.md`, `v0512_phase2v2_prompt_proposal.md` | factorStatus guards + SA injection |
| **v0.5.13 Phase 2 v2 prompt cleanup** | `v0_phase2v2_summary.md`, `holdout_v0513_summary.md` | Directive prompt rewrite + first holdout (87.5% NC clean) |
| **v0.5.14 W-CON-01 not-assessed** | (predicate-diff only) | Found via v0.5.13 holdout |
| **v0.5.15 Phase 2 v3 tool-use** | `v0_phase2v3_pilot_summary.md`, `phase_a_pipeline_test_summary.md` | Anthropic tool-use migration |
| **v0.5.15.1 SHACL + SA fix** | `holdout_v0515_summary.md` | **NAFEMS-ready: 97.1% NC clean rate** |

## Important persistent files (cumulative across all versions)

| File | Role |
|---|---|
| `refinement_log.jsonl` | The audit trail. Every iteration's metrics + decision. |
| `decision_log.csv` | Tabular accept/revert log. |
| `milestones/00_m5_baseline.csv` | The M5 baseline. Reference for all subsequent comparisons. |
| `milestones/after_<rule>.csv` | Post-lock-in catalog state for each rule. |
| `holdout_used/<rule>.lock` | Holdout-spend marker (one per rule, prevents double-use). |
| `splits/<rule>_split.json` | Train/dev/holdout assignment per rule (seed-pinned). |

## Per-iteration outcomes (`per_iter_outcomes/`)

Each subdirectory holds a single `uofa adversarial analyze` output:

| Subdir | Source |
|---|---|
| `w_ep_01_iter01/`, `w_on_02_iter01/`, `w_on_02_v0510/`, etc. | Per-rule iteration outcomes |
| `phase2v2_test/` | v0.5.13 fresh-corpus test (180 NCs) |
| `holdout_v0513/` | v0.5.13 full-battery holdout (483 packages) |
| `holdout_v0515/` | v0.5.15.1 NC holdout (180 NCs) |

## Reorganization plan

This flat layout is being reorganized into per-version subdirs in a
follow-up cleanup pass:

```
out/phase2_5/
├── shared/             ← refinement_log.jsonl, splits/, holdout_used/, plots/
├── v0.5.10-w-on-02/    ← v0510_summary.md + milestone + per-iter outcomes
├── v0.5.11-w-ar-02/    ← v0511_summary.md + ...
├── v0.5.12-w-con-fixes/
├── v0.5.13-prompt-cleanup/
├── v0.5.15-tool-use/
├── v0.5.15.1-shacl-and-sa-fix/  ← holdout_v0515_summary.md
└── archive/2026-04-27/ ← symlink for back-compat
```

See `docs/repo-layout.md` for the broader cleanup plan.

## Cross-references

- Tool taxonomy: `tools/phase2_5/README.md`
- Top-level repo orientation: `docs/repo-layout.md`
- Most recent NAFEMS-ready summary: `2026-04-27/holdout_v0515_summary.md`
