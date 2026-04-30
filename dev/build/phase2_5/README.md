# `dev/build/phase2_5/` — Phase 2.5 refinement output workspace

> **Note**: This directory is gitignored except for this README. The
> contents here are the empirical output of the Phase 2.5 catalog
> refinement work. The deterministic regenerator is the codebase +
> spec yamls; this dir is the artifact trail.

## Layout (post-Phase-E reorg, 2026-04-29)

The output is split into **per-version subdirs** for the human-facing
summary documents, plus a **`shared/` directory** holding the cumulative
tool-path artifacts (refinement_log, splits, milestones, predicate_diffs,
plots, per_iter_outcomes). A back-compat symlink `2026-04-27 → shared`
keeps the original path resolvable for one release cycle.

```
dev/build/phase2_5/
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
├── shared/                                 ← cumulative tool-path artifacts (Phase C+ default)
│   ├── refinement_log.jsonl                ← cumulative iteration audit log
│   ├── milestones/                         ← per-version after_<rule>.csv files
│   ├── predicate_diffs/                    ← unified diffs per rule iteration
│   ├── plots/                              ← PNG trajectories
│   ├── splits/                             ← train/dev/holdout JSON per rule
│   ├── holdout_used/                       ← holdout-spend lock files
│   ├── per_iter_outcomes/                  ← analyze outputs per iteration
│   ├── review_packet.md                    ← C1.5 semantic review summary
│   └── report.md                           ← M5 baseline narrative
│
└── 2026-04-27 → shared                     ← back-compat symlink (one release cycle)
```

## Why the `2026-04-27 → shared` back-compat symlink

Phase C of the post-Phase-2.5 cleanup migrated the seven Phase 2.5
tool defaults from the misleadingly-named `2026-04-27/` dir (the
workspace was created on Apr 27 but spans Apr 26 → Apr 29) to a
neutrally-named `shared/`. The relative symlink `2026-04-27 → shared`
keeps any external tool or summary doc that hardcodes the old path
working for one release cycle. It will be removed after v0.6.

The seven tools whose defaults migrated:

- `tools/phase2_5/refinement_loop/refine_loop.py`
- `tools/phase2_5/refinement_loop/lock_in.py`
- `tools/phase2_5/refinement_loop/log_decision.py`
- `tools/phase2_5/refinement_loop/metrics.py`
- `tools/phase2_5/analysis/plot_pr.py`
- `tools/phase2_5/refinement_loop/split.py`
- `tools/phase2_5/analysis/verify_sentinels.py`

Phase D additionally renamed the parent `out/` → `build/`, and Phase E
nested it under `dev/build/`. Combined with the Phase C reorg of
`tools/phase2_5/` into purpose-keyed subpackages (refinement_loop/,
corpus_regen/, audit/, analysis/), the repo no longer carries
pre-cleanup naming oddities.

## Summary docs by Phase 2.5 version

| Version | Subdir | Highlight |
|---|---|---|
| **v0.5.7 M5 baseline** | (in `shared/report.md`) | Pre-Phase-2.5 corpus state |
| **v0.5.8 W-EP-01** | (predicate-diff only in `shared/predicate_diffs/`) | URI-handle Claim guard |
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
| `shared/refinement_log.jsonl` | The audit trail. Every iteration's metrics + decision. |
| `shared/milestones/00_m5_baseline.csv` | The M5 baseline. Reference for all subsequent comparisons. |
| `shared/milestones/after_<rule>.csv` | Post-lock-in catalog state for each rule. |
| `shared/holdout_used/<rule>.lock` | Holdout-spend marker (one per rule, prevents double-use). |
| `shared/splits/<rule>_split.json` | Train/dev/holdout assignment per rule (seed-pinned). |
| `shared/plots/<rule>_trajectory.png` | Per-rule PR trajectory across iterations. |
| `shared/plots/catalog_milestones.png` | Catalog-wide cumulative milestone scatter. |

## Per-iteration outcomes (`shared/per_iter_outcomes/`)

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
