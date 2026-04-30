# `dev/specs/cross_pack/` — multi-pack integration specs

Phase 2 — cross-pack battery. Each spec exercises a weakener rule
that should fire identically (or with documented differences)
across multiple packs (vv40 / nasa-7009b / core).

## Use case

When a rule's predicate is defined in `packs/core/rules/` but the
SHACL shapes differ per pack, packages generated against
pack-specific shapes should still trigger the cross-pack rule
correctly. This battery validates that.

## Specs

| File | Rule | Pack scope |
|---|---|---|
| `cp_nasa_compound_01.yaml` | COMPOUND-01 | vv40 + nasa-7009b |
| `cp_nasa_w_al_01.yaml` | W-AL-01 | vv40 + nasa-7009b |
| `cp_nasa_w_ar_01.yaml` | W-AR-01 | vv40 + nasa-7009b |
| `cp_nasa_w_ar_05.yaml` | W-AR-05 | vv40 + nasa-7009b |
| `cp_nasa_w_con_01.yaml` | W-CON-01 | vv40 + nasa-7009b |
| `cp_nasa_w_ep_01.yaml` | W-EP-01 | vv40 + nasa-7009b |
| `cp_nasa_w_ep_04.yaml` | W-EP-04 | vv40 + nasa-7009b |
| `cp_nasa_w_on_01.yaml` | W-ON-01 | vv40 + nasa-7009b |
| `cp_nasa_w_prov_01.yaml` | W-PROV-01 | vv40 + nasa-7009b |
| `cp_nasa_w_si_01.yaml` | W-SI-01 | vv40 + nasa-7009b |

## How to run

```bash
uofa adversarial run --batch dev/specs/cross_pack \
    --out build/adversarial/cross-pack-<date>
```

## Status

10 specs as of v0.5.15.1. Battery is **active but exploratory** —
NASA-7009B examples are seeded but the comprehensive cross-pack
analysis hasn't been published. Active candidate for a Phase 3+
multi-pack study.

## Cross-references

- NASA pack: `packs/nasa-7009b/`
- VV40 pack: `packs/vv40/`
- Top-level orientation: `docs/repo-layout.md`
- Other spec batteries: `dev/specs/{confirm_existing,gap_probe,
  interaction,negative_controls,paraphrasing,quality_benchmark}/`
