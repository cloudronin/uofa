# `specs/quality_benchmark/` — model-quality fan-out specs

Phase 2 §7.7 — quality benchmark battery. Each spec runs the same
target weakener across multiple LLM models (claude-sonnet, gpt-4o,
qwen, etc.) to measure per-model generation quality.

## Use case

When a model swap is being considered (e.g., bumping the default
`generation_model` in NC specs), this battery measures the empirical
generation quality across models on a fixed set of weakener targets.

## Specs

| File | Target weakener | Defeater type |
|---|---|---|
| `qb_01_w_ar_01.yaml` | W-AR-01 | D1 undermining |
| `qb_02_w_ep_01.yaml` | W-EP-01 | epistemic |
| `qb_03_w_al_01.yaml` | W-AL-01 | aleatory |
| `qb_04_w_on_02.yaml` | W-ON-02 | operational |
| `qb_05_data_drift.yaml` | data drift | structural |
| `qb_06_req_missing.yaml` | requirement missing | requirements |
| `qb_07_hasty.yaml` | hasty conclusion | logical fallacy |
| `qb_08_elim_arg.yaml` | eliminative argumentation | argumentation workflow |

## How to run

```bash
uofa adversarial run \
    --batch specs/quality_benchmark \
    --out build/adversarial/qb-<date> \
    --models claude-sonnet-4-6,gpt-4o-2024-11,qwen2.5-7b \
    --max-cost 30
```

The `--models` flag fans each spec out across all listed models.
Each generated package's manifest tags it with the model that
produced it; downstream analyze can group by model.

## Status

Battery is defined but **rarely run** as of v0.5.15.1. Last
substantive use was during the M5 generation phase (Apr 26).
Active candidate for a Phase 3+ model-comparison study.

## Cross-references

- Top-level orientation: `docs/repo-layout.md`
- Adversarial generation pipeline: `src/uofa_cli/adversarial/`
- Other spec batteries: `specs/{confirm_existing,gap_probe,
  interaction,negative_controls,paraphrasing,cross_pack}/`
