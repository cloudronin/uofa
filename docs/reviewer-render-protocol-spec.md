# Spec: Reviewer Render Protocol — derive once, enforce invariants

**Repo:** github.com/cloudronin/uofa
**Space:** huggingface.co/spaces/cloudronin/uofa-demo
**Status:** Refactor of the existing reviewer render. No engine, schema, or extraction (`uofa_cli.*`) changes.
**Build mode:** Spec-driven, paired with Claude Code.

---

## 1. Problem

The reviewer view has shipped two contradictory renders of the same Morrison COU2 case:

- Build A: 38% complete, 5 of 13 evidenced, but a missing-line claiming "nothing required is missing."
- Build B: 100% complete, 13 of 13 evidenced, while listing High-severity concerns (absent comparator data, undocumented COU boundary) that defeat that claim.

Both are the same bug class: the at-a-glance panel, the factor table, the concerns list, and the missing-line each interpret the raw analysis payload independently, so they drift out of agreement. Each fix has been a patch on one panel. This spec replaces patching with a protocol that makes a contradictory render structurally impossible.

---

## 2. Protocol (the five rules)

1. **One derivation, one source.** The render computes a single `ReviewerState` object from the analysis payload before any HTML exists. Every panel reads from `ReviewerState`. No panel computes counts, statuses, or completeness on its own.
2. **Status is derived, never defaulted.** Each factor status is computed from explicit evidence presence plus weakener targeting. Absence of a field maps to `NOT_STATED`. Deliberate scope-out maps to `NOT_APPLICABLE`. A field is `EVIDENCED` only on explicit positive evidence. No code path defaults a missing/unknown factor to `EVIDENCED`.
3. **Completeness is a function of status.** `completeness = f(statuses)`. The at-a-glance count and percentage are derived from the same status list the factor table renders. They cannot be computed separately.
4. **Invariants validated before render.** `ReviewerState` is asserted against the frozen invariant set (section 4) before HTML generation. On violation the render raises, it does not emit a misleading page.
5. **Fixtures validated against source JSON-LD.** Golden snapshots are checked against the actual COU evidence packages, not regenerated from current render output. Regenerating a golden from a buggy render enshrines the bug; forbidden.

---

## 3. Data model

### `ReviewerState` (new intermediate object)

Pure data, framework-free, produced by a single function `build_reviewer_state(analysis) -> ReviewerState`.

| Field | Type | Source / rule |
|---|---|---|
| `cou_name`, `cou_description` | str | `context` block |
| `standard`, `risk_level`, `device_class` | str | `context` block |
| `factors` | list[`FactorState`] | one per expected factor for the pack |
| `completeness_pct` | int | derived: evidenced / expected, see rule |
| `n_evidenced`, `n_expected`, `n_required` | int | derived from `factors` |
| `required_all_accounted` | bool | derived: every required factor is EVIDENCED or NOT_APPLICABLE |
| `concerns` | list[`Concern`] | from `weakeners[]` |
| `severity_counts` | dict | derived from `concerns`, single source for at-a-glance |
| `gates` | dict | structural gate = `structural.conforms`; completeness gate = `missing == []` |
| `authenticity` | block | unchanged from current `context.authenticity` |

### `FactorState`

| Field | Rule |
|---|---|
| `name` | canonical factor name |
| `plain_name`, `what_it_means` | from gloss (single lookup) |
| `status` | enum: `EVIDENCED` / `NOT_STATED` / `NOT_APPLICABLE` |
| `required` | bool, from pack requirement at this risk level |
| `targeting_weakeners` | list of concern ids whose `factors[]` include this factor |

### Status derivation (precedence, evaluated in order)

1. If the factor is the target of an open High or Moderate weakener → it CANNOT be `EVIDENCED`. Resolve to `NOT_STATED` (the evidence is present but disputed/incomplete) unless explicitly scoped out.
2. Else if explicitly scoped out for this COU/risk level → `NOT_APPLICABLE`.
3. Else if explicit positive evidence present → `EVIDENCED`.
4. Else → `NOT_STATED`.

Absence never produces `EVIDENCED`. This is the rule that kills the Build B regression.

---

## 4. Invariants (frozen)

Enforced by `assert_reviewer_invariants(state)` at render time, and asserted in tests.

| # | Invariant | Catches |
|---|---|---|
| 1 | No factor with status `EVIDENCED` appears in any open High/Moderate weakener's `factors[]` | Build B |
| 2 | `completeness_pct == 100` is invalid if any High weakener is present | Build B |
| 3 | At-a-glance `n_evidenced` equals the count of `EVIDENCED` rows in `factors` | A/B drift |
| 4 | Severity words in `severity_counts` exactly match the severity words used in rendered concern lines | severity-word bug |
| 5 | `required_all_accounted` is True only if every `required` factor is `EVIDENCED` or `NOT_APPLICABLE` | Build A |
| 6 | At-a-glance concern count equals the number of rendered concern lines | count drift |

A violation raises `ReviewerInvariantError` with the failing invariant number and the offending values. The render never silently emits a contradictory page.

**Engine-data escape hatch:** if invariant 1 cannot be satisfied because the payload does not distinguish evidenced / absent / scoped-out for a factor, STOP and flag it. That is an engine/schema data gap surfacing as a render failure, not a presentation bug, and it is out of scope for this spec. Do not paper over it in the render.

---

## 5. Files to change / create

**`space/reviewer_state.py`** (NEW) — `build_reviewer_state(analysis, gloss) -> ReviewerState`, the `FactorState`/`Concern` dataclasses, the status-derivation precedence, and `assert_reviewer_invariants(state)`. Pure, no framework, no HTML.

**`space/reviewer.py`** (REFACTOR) — `render_reviewer_html(analysis, gloss)` now: (1) calls `build_reviewer_state`, (2) calls `assert_reviewer_invariants`, (3) renders purely from `ReviewerState`. Remove all per-panel computation of counts/status/completeness from this file. The six sections render exactly as today but read only from `state`.

**`space/gloss.*`** — unchanged. Single lookup still feeds `FactorState`.

**`space/pipeline.py`**, **`space/app.py`** — unchanged except: confirm `_finalize` still calls `render_reviewer_html` and arity stays 8. No new wiring.

---

## 6. Fixtures (validated against source, not render)

Two COUs, hand-validated from the actual JSON-LD in `packs/vv40/examples/morrison/cou{1,2}/`:

| Fixture | Expected shape (validate against cou JSON-LD, NOT current render) |
|---|---|
| `morrison_cou1_state.json` | COU1: accepted, MRL2, 11 weakeners / 5 patterns, 0 compound. Lower completeness, statuses consistent with its weakeners. |
| `morrison_cou2_state.json` | COU2: not accepted, MRL5, 18 weakeners / 6 patterns incl. COMPOUND-01. NOT 100% complete; factors targeted by High weakeners are NOT_STATED. |

Per the NAFEMS reproduction page, COU2 is the not-accepted, compound-risk case. A 100%/all-evidenced COU2 is by definition the bug. Hand-derive the expected `ReviewerState` for each from the evidence packages, check those in, and assert the render against them.

---

## 7. Verification

- `pytest tests/space` green, including:
  - `test_reviewer_state.py` — status derivation precedence (each of the 4 branches), completeness = f(status), `required_all_accounted` logic.
  - `test_reviewer_invariants.py` — each of the 6 invariants fails loudly on a constructed violating state; passes on both Morrison fixtures.
  - `test_reviewer.py` — render reads only from state; six headings present; golden HTML snapshot for COU1 and COU2 matches the hand-validated fixtures.
  - Negative test: feed a state with an `EVIDENCED` factor that is a weakener target → assert `ReviewerInvariantError` raised (invariant 1), render does NOT emit HTML.
- Engine/author regression: author markdowns at indices 3/4/5 byte-identical, `N_FINALIZE` 8, em-dash guard green.
- Determinism: fixtures are checked-in JSON, not live LLM.
- Manual after deploy: reload `/demo` Reviewer view on the default sample; factor table, completeness number, missing-line, and concerns tell one consistent story; Save as PDF renders only the reviewer panel.

---

## 8. Out of scope (flag, do not build)

- Glossing raw schema terms in concern lines (`comparedAgainst`, `bindsRequirement`, `ProfileComplete`, `SensitivityAnalysis`). Reader-facing copy improvement, separate pass.
- Any change to the analysis payload contents. If the invariants cannot be satisfied from the current payload, that is the engine-data flag in section 4, handled separately.

---

## 9. Why this ends the patching

Every shipped bug (Build A's missing-line, Build B's all-evidenced, the severity-word mismatch) is one of the six invariants firing. Encoding them once, enforced at render time and in tests, converts "catch the contradiction by eye on a PDF" into "a contradictory render cannot be produced." The protocol constrains how the payload is read, not what it contains, so the engine boundary holds.
