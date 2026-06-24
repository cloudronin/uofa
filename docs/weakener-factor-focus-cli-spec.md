# Weakener→factor focus, shared in the CLI (as built)

**Status:** Implemented. The semantic weakener→credibility-factor focus and the
credibility-report logic now live in `uofa_cli`, shared by the CLI `uofa report`
command and the demo Space. The focus map is **pack data**, declared in each
pack manifest and loaded dynamically — never hardcoded in code.
**Boundary:** Read-side interpretation of engine output. The Jena rule engine,
SHACL shapes, and `.rules` files are untouched.

---

## 0. Why

The factor-focus map used to live in `space/summary.py` (demo-only), and an
earlier draft kept it as a hardcoded Python dict of pattern IDs. Both are wrong:
the map only benefited the Space, and a hardcoded dict silently goes stale the
moment a pack adds/renames/removes a weakener pattern. The fix relocates the
logic to `uofa_cli` **and** makes the map pack-declared, loaded the same way
patternIds/shapes/rules already are (`paths.detection_config`).

---

## 1. The focus map is pack data

Declared in the detection-capability `payload.factorFocus` of each pack manifest
(the pack-manifest schema allows extra payload keys — `additionalProperties:
true`). Core patterns live in `packs/core`; a pack augments them.

`packs/core/pack.json` (detection payload):

```json
"factorFocus": {
  "W-AR-05":   ["Output comparison"],
  "W-PROV-01": ["Output comparison"],
  "W-ON-02":   ["Relevance of the validation activities to the COU"]
}
```

`packs/nasa-7009b/pack.json` augments W-PROV-01 with NASA's provenance factor:

```json
"factorFocus": { "W-PROV-01": ["Data pedigree"] }
```

Only patterns that fire on a **non-factor node** need an entry. Patterns whose
`affectedNode` is the credibility factor itself (`W-EP-04`, all `W-NASA-*`)
resolve to their factor by IRI and need no focus entry.

### Loader

- `paths.detection_config(manifest)` now surfaces `factorFocus`.
- `paths.factor_focus_index(packs)` merges `core` + the active packs into
  `{patternId: [factor, ...]}` (union, order-preserving, cached). NASA's
  `W-PROV-01` becomes `["Output comparison", "Data pedigree"]`; vv40 keeps
  `["Output comparison"]`.

### `uofa_cli/weakener_focus.py`

- `expected_factors(pack)` — the pack's factor universe.
- `resolve_factor_names(affected_nodes, slug_to_name)` — `.../factor/<slug>` → name.
- `factor_focus(firing, pack, focus_map, slug_to_name, expected)` — IRI-resolved
  ∪ the pattern's declared focus, **filtered to factors expected for the pack**
  (so a foreign-pack name like `Data pedigree` is dropped for a vv40 bundle).
- `enrich_firings(firings, pack)` — attaches `factors` to each firing, loading
  the map via `paths.factor_focus_index([pack])`. Non-mutating.

---

## 2. Shared report logic — `uofa_cli/report_state.py`

- `compute_findings(pack, factor_statuses, shacl, firings)` — the analysis
  payload (completeness from confirmed statuses + enriched weakeners +
  structural). This is the old `summary.compute`, moved down.
- `build_report_state(analysis, gloss=None)` — the single derived state. Status
  precedence: scoped-out → demoted-by-open-High/Moderate-concern → assessed →
  not-stated. Absence never yields Evidenced. Gloss is optional (CLI renders
  canonical names; the Space injects its plain-language gloss).
- `assert_report_invariants(state)` — the six frozen invariants. A
  contradictory report raises `ReportInvariantError`, never renders.

The Space is now a thin adapter:
- `space/summary.py` → re-exports `compute_findings as compute`.
- `space/reviewer_state.py` → re-exports the shared names under their historical
  `Reviewer*` spellings and defaults the gloss. `space/reviewer.py` and the Space
  goldens are unchanged.

---

## 3. `uofa report` command — `uofa_cli/commands/report.py`

```
uofa report <bundle>.jsonld [--format text|markdown|json] [--output FILE] [--pack NAME]
```

Reads a bundle (inlined tree or compact `@graph`), runs SHACL + the rule engine,
reads `factorStatus` from the bundle, assembles the analysis via
`compute_findings`, builds + invariant-checks the state, and renders. Registered
in `cli.py`; `--help-all` picks it up automatically. Guards: a file with no
credibility factors is rejected with a clear message rather than a hollow 0%.

Pack-aware: pass `--pack nasa-7009b` for a NASA bundle. Fully deterministic — no
LLM, no extraction.

---

## 4. Verification

- `tests/test_weakener_focus.py` — IRI resolution; the focus index matches the
  manifests; every declared focus name is a real factor for its pack (typo
  guard); vv40 vs NASA enrichment (Data pedigree added for NASA, dropped for
  vv40).
- `tests/test_report_command.py` — runs the real engine on both Morrison
  bundles: 38% / 5-of-13 (bundle ground truth — 7 assessed, Output comparison +
  Relevance-to-COU demoted by their concerns), invariants hold, all three
  formats render, non-evidence file rejected.
- `tests/space` green and goldens byte-identical (Space behavior unchanged after
  delegation); `N_FINALIZE == 8`; em-dash guard green.
- NASA focus is unit-verified only: the repo has no clean NASA *input* bundle
  (the NASA example files are reasoned weakener-annotation dumps), so there is no
  end-to-end NASA report to assert. Flagged, not a gap in the mechanism.

---

## 5. Follow-ups (not built)

- NASA equivalents for uncertainty/sensitivity patterns (`W-AL-*` → `Results
  uncertainty`/`Results robustness`) if those should demote a NASA factor.
- `report --format html` (the Space keeps its HTML renderer on top of the shared
  state; the CLI emits text/markdown/json).
- A clean NASA input example bundle, to enable an end-to-end NASA report test.
