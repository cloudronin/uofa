# `out/phase2_5/` — Phase 2.5 refinement output workspace

> **Note**: This directory is gitignored except for this README. The
> contents here are the empirical output of the Phase 2.5 catalog
> refinement work. The deterministic regenerator is the codebase +
> spec yamls; this dir is the artifact trail.

## Layout (post-Tier-2 reorg, 2026-04-29)

The output is split into **per-version subdirs** for the human-facing
summary documents, plus a **legacy `2026-04-27/` dir** that retains
the cumulative tool-path artifacts (refinement_log, splits, milestones,
predicate_diffs, plots, per_iter_outcomes) at their original locations
so the tools in `tools/phase2_5/` continue to work without code
changes.

```
out/phase2_5/
├── README.md (this file, force-tracked despite gitignore)
│
├── v0.5.10-w-on-02/                        ← Phase 2.5 W-ON-02 fix
│   ├── v0510_summary.md
│   └── regen_nc_envelope_report.csv
│
├── v0.5.11-w-ar-02/                        ← Phase 2.5 W-AR-02 fix
│   ├── v0511_summary.md
│   └── regen_nc_offset_rationale_report.csv
│
├── v0.5.12-w-con-fixes/                    ← W-CON-01/04 + W-AR-01
│   ├── v0512_summary.md
│   ├── v0512_audit_residuals.md
│   └── v0512_phase2v2_prompt_proposal.md
│
├── v0.5.13-prompt-cleanup/                 ← Phase 2 v2 NC prompt cleanup
│   ├── v0_phase2v2_summary.md
│   └── holdout_v0513_summary.md
│
├── v0.5.15-tool-use/                       ← Phase 2 v3 tool-use migration
│   ├── phase_a_pipeline_test_summary.md
│   └── v0_phase2v3_pilot_summary.md
│
├── v0.5.15.1-shacl-and-sa-fix/             ← Tool-use SHACL lock + SA boolean fix
│   └── holdout_v0515_summary.md            ← *** NAFEMS-ready: 97.1% NC clean ***
│
└── 2026-04-27/                             ← cumulative tool-path artifacts
    ├── refinement_log.jsonl                ← cumulative iteration audit log
    ├── milestones/                         ← per-version after_<rule>.csv files
    ├── predicate_diffs/                    ← unified diffs per rule iteration
    ├── plots/                              ← PNG trajectories
    ├── splits/                             ← train/dev/holdout JSON per rule
    ├── holdout_used/                       ← holdout-spend lock files
    ├── per_iter_outcomes/                  ← analyze outputs per iteration
    ├── review_packet.md                    ← C1.5 semantic review summary
    └── report.md                           ← M5 baseline narrative
```

## Why the legacy `2026-04-27/` directory was preserved

Seven of the Phase 2.5 tools hardcode `out/phase2_5/2026-04-27/` as
the default location for refinement_log, predicate_diffs, milestones,
splits, holdout_used, and plots:

- `tools/phase2_5/refine_loop.py`
- `tools/phase2_5/lock_in.py`
- `tools/phase2_5/log_decision.py`
- `tools/phase2_5/metrics.py`
- `tools/phase2_5/plot_pr.py`
- `tools/phase2_5/split.py`
- `tools/phase2_5/verify_sentinels.py`

Migrating those to a new path (e.g., `out/phase2_5/shared/`) is a
separate code-change pass deferred to a future Tier 3+ reorg. Keeping
the dated dir preserves backwards-compatibility with all existing
tool invocations + paths embedded in summary docs.

## Summary docs by Phase 2.5 version

| Version | Subdir | Highlight |
|---|---|---|
| **v0.5.7 M5 baseline** | (in `2026-04-27/report.md`) | Pre-Phase-2.5 corpus state |
| **v0.5.8 W-EP-01** | (predicate-diff only in `2026-04-27/predicate_diffs/`) | URI-handle Claim guard |
| **v0.5.9 W-AL-02** | (predicate-diff only) | UQ boolean schema-aligned predicate |
| **v0.5.10 W-ON-02** | `v0.5.10-w-on-02/v0510_summary.md` | NC envelope corpus regen |
| **v0.5.11 W-AR-02** | `v0.5.11-w-ar-02/v0511_summary.md` | OffsetRationale schema + 2-rule pattern |
| **v0.5.12 W-CON + W-AR-01** | `v0.5.12-w-con-fixes/v0512_summary.md` (+2 more docs) | factorStatus guards + SA injection |
| **v0.5.13 Phase 2 v2** | `v0.5.13-prompt-cleanup/v0_phase2v2_summary.md` + `holdout_v0513_summary.md` | Directive prompt rewrite + first holdout (87.5% NC clean) |
| **v0.5.14 W-CON-01 not-assessed** | (predicate-diff only) | Found via v0.5.13 holdout |
| **v0.5.15 Phase 2 v3 tool-use** | `v0.5.15-tool-use/phase_a_pipeline_test_summary.md` + `v0_phase2v3_pilot_summary.md` | Anthropic tool-use migration |
| **v0.5.15.1 SHACL + SA fix** | `v0.5.15.1-shacl-and-sa-fix/holdout_v0515_summary.md` | **NAFEMS-ready: 97.1% NC clean rate** |

## Persistent files (cumulative across all versions)

| File | Role |
|---|---|
| `2026-04-27/refinement_log.jsonl` | The audit trail. Every iteration's metrics + decision. |
| `2026-04-27/milestones/00_m5_baseline.csv` | The M5 baseline. Reference for all subsequent comparisons. |
| `2026-04-27/milestones/after_<rule>.csv` | Post-lock-in catalog state for each rule. |
| `2026-04-27/holdout_used/<rule>.lock` | Holdout-spend marker (one per rule, prevents double-use). |
| `2026-04-27/splits/<rule>_split.json` | Train/dev/holdout assignment per rule (seed-pinned). |
| `2026-04-27/plots/<rule>_trajectory.png` | Per-rule PR trajectory across iterations. |
| `2026-04-27/plots/catalog_milestones.png` | Catalog-wide cumulative milestone scatter. |

## Per-iteration outcomes (`2026-04-27/per_iter_outcomes/`)

Each subdirectory holds a single `uofa adversarial analyze` output
(outcomes.csv, matrix.csv, summary.csv, index.html):

| Subdir | Source |
|---|---|
| `w_ep_01_iter01/`, `w_on_02_iter01/`, `w_on_02_v0510/`, `w_ar_02_iter01/`, `w_ar_02_v0511/`, etc. | Per-rule iteration outcomes |
| `v0512_consistency/` | v0.5.12 corpus regen analyze |
| `phase2v2_test/` | v0.5.13 fresh-corpus test (180 NCs) |
| `holdout_v0513/` | v0.5.13 full-battery holdout (483 packages) |
| `holdout_v0515/` | v0.5.15.1 NC holdout (180 NCs) — NAFEMS-ready |

## Cross-references

- Tool taxonomy: `tools/phase2_5/README.md`
- Top-level repo orientation: `docs/repo-layout.md`
- Most recent NAFEMS-ready summary: `v0.5.15.1-shacl-and-sa-fix/holdout_v0515_summary.md`
