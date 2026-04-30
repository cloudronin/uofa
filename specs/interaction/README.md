# `specs/interaction/` — multi-weakener interaction specs

Phase 2 — interaction battery. Each spec targets a *combination* of
weakeners that should fire together (compound rules, severity
escalation chains, etc.).

## Use case

The interaction battery exercises **rule chains** rather than
individual rules. E.g., a "Critical+High coexistence" spec produces
packages where two weakeners fire on the same node, triggering
COMPOUND-01.

## Specs

| File | Trigger pattern |
|---|---|
| `int-1-critical-plus-high.yaml` | Critical + High weakener coexistence (COMPOUND-01) |
| `int-2-two-criticals.yaml` | Two Critical weakeners on same node |
| `int-3-high-assurance-with-gaps.yaml` | Declared High assurance level + Critical weakener (COMPOUND-03) |
| `int-4-three-way.yaml` | Three-way compound trigger |
| `int-5-critical-plus-medium.yaml` | Critical + Medium escalation |

(Plus 2 additional yamls covering edge cases.)

## How to run

```bash
uofa adversarial run --batch specs/interaction --out build/adversarial/<date>
```

## Status

7 specs as of v0.5.15.1. Battery is **active** — used in the
v0.5.13 holdout (1 INT spec) and v0.5.15.1 small validation. A few
specs were pinned in tests (`tests/adversarial/test_runner.py`).

## Cross-references

- COMPOUND rule definitions: `packs/core/rules/uofa_weakener.rules`
- Top-level orientation: `docs/repo-layout.md`
- Other spec batteries: `specs/{confirm_existing,gap_probe,
  negative_controls,paraphrasing,quality_benchmark,cross_pack}/`
