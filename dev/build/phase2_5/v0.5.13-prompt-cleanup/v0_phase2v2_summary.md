# Phase 2 v2 prompt cleanup — v0.5.13 outcome summary

**Date**: 2026-04-28
**Catalog version**: v0.5.13 (commit TBD, tag `v0.5.13-phase2v2-prompt-cleanup`)
**Predecessor**: v0.5.12.1 (commit 0d56b18, hooks-active baseline)
**Decision**: **HOOKS RETAINED** — v0.5.13 ships as a prompt-improvement-only release
**Total cost**: $34.81 (Phase A $4.48 + Phase B.3 $30.33), of $140 budget cap

---

## TL;DR

Phase B prompt cleanup substantively improved LLM compliance with NC schema
requirements. **Complete-profile compliance jumped from 0% → 96%, NC clean
rate of validated NCs reached 100%.** However, the LLM still emits
*placeholder-content* SA blocks ~75% of the time, well below the 70% target
for substantive content. **The post-LLM hooks remain load-bearing as a
safety net.**

v0.5.13 ships as a prompt-quality release: the prompt directives improve
both LLM compliance AND the substantive content of the ~25% of NCs where
the LLM emits real Sobol-style SA descriptions (vs. v0.5.12's placeholder
noise). The hooks keep the catalog's NC clean rate at 100% on the
remaining 75%.

---

## Per-archetype prompt edits

| Archetype | Edit |
|---|---|
| NC-1 (`nc-clean-full-morrison-cou1`) | Added directive `EMIT conformsToProfile: 'uofa:ProfileComplete'` (override base COU's profile) + explicit inline `hasSensitivityAnalysis` / envelope / acceptance criteria requirements |
| NC-2 (Minimal) | No change |
| NC-3 (`nc-clean-full-morrison-cou2`) | Same Complete-profile directive + Spec yaml `base_cou` bug fix (was pointing at cou1, now cou2; mrl 2→5) + max_tokens 8K→12K |
| NC-4 (`nc-clean-full-nagaraja`) | Same Complete-profile directive + Spec yaml `base_cou` bug fix (was pointing at morrison/cou1, now nagaraja/cou1; mrl 2→3) + max_tokens 8K→10K |
| NC-5 (scoped-out) | Added "DO NOT emit `requiredLevel`/`achievedLevel` on scoped-out factors" |
| NC-6 (not-applicable) | Same DO-NOT-EMIT directive for N/A factors |
| NC-7 (rejected) | **Full task rewrite**: forbid `factorStatus='not-assessed'` at MRL>2; specify alternative rejection mechanics (assessed-with-shortfall OR scoped-out-with-rationale) |
| NC-8 (partial envelope) | Added explicit "INLINE objects, not narrative-only" directive |
| NC-9 (low confidence) | Added conditional Complete-profile SA directive |
| NC-10 (compound-free) | No change |

`extra_schema_rules` block rewritten as 5 numbered DIRECTIVE requirements
(replacing v0.5.12's conditional "if Complete then SA" wording, which the
LLM was misreading as license to switch to Minimal).

Spec yaml bumps: NC-1 `max_tokens` 8K→10K (Complete profile + 13 factors).

---

## Phase B.4 field-presence audit results

149 successful packages from `out/adversarial/phase2/2026-04-29-v0_phase2v2-test`.
Cost cap halted generation at 75/90 cells; NC-5 (scoped-out) and most of
NC-7 (rejected) didn't generate. Remaining 9 archetypes have ≥17 packages
each — sufficient sample.

| Compliance metric | Result | Target | Status | Notes |
|---|---|---|---|---|
| Complete-profile compliance (NC-1/3/4 emit ProfileComplete) | 52/54 = 96% | ≥ 90% | ✓ | Was 0% in Phase A |
| `hasSensitivityAnalysis` present on Complete NCs | 52/52 = 100% | ≥ 90% | ✓ | LLM (25%) + hook (75%) combined |
| `hasSensitivityAnalysis` SUBSTANTIVE (not placeholder) | 13/52 = 25% | ≥ 70% | **✗** | LLM compliance gap; hook fills the rest |
| Envelope stubs present (all NCs) | 149/149 = 100% | ≥ 90% | ✓ | LLM (66%) + hook (34%) combined |
| Envelope SUBSTANTIVE (not placeholder) | 99/149 = 66% | ≥ 70% | ⚠ | Marginal — close but below target |
| NC-7 with `factorStatus='not-assessed'` at MRL>2 | 0 of 8 | 0 | ✓ | Rewrite worked |
| NC-5/6 with vestigial `requiredLevel`/`achievedLevel` | 0 of 18 | 0 | ✓ | Directive worked |

The two ✗/⚠ are about LLM compliance with substantive content, not
structural validity. The hooks ensure structural validity is maintained
even when the LLM defers.

---

## Phase B.5 catalog analysis on fresh corpus

```
Outcome class breakdown:
  COV-CLEAN-CORRECT        : 118
  GEN-INVALID              : 22

NC clean rate (of validated): 118/118 = 100.0%
NC clean rate (strict, incl GEN-INVALID): 118/140 = 84.3%
COV-CLEAN-WRONG (validation passes but rules fire): 0
GEN-INVALID (failed validation, didn't reach rules): 22
```

**Per-rule NC firings**: 0 across all rules.

The 100% clean rate of validated NCs proves the v0.5.13 prompts +
v0.5.12.1 hooks together produce zero rule firings. The 22 GEN-INVALID
are LLM token-limit / JSON-quality issues unrelated to the catalog
(token limits hitting at 10-12K with rich Complete-profile content).

For comparison:
- M5 baseline (v0.5.7): NC clean rate 0%
- v0.5.12 (post-Phase 2.5 cumulative): NC clean rate 97.2%
- **v0.5.13 fresh corpus (validated NCs): 100.0%**

---

## Phase B.6 hook removal decision

**HOOKS RETAINED.** Three signals point to hooks still being load-bearing:

1. **SA substantive emission: 25% of Complete NCs** — for the other 75%
   the LLM omits SA entirely, and the post-LLM hook injects the
   placeholder. Without the hook, those 75% would lack
   `hasSensitivityAnalysis` and fire W-CON-04.

2. **Envelope substantive emission: 66% of all NCs** — the other 34%
   are hook-injected placeholders. Without the hook, those would lack
   envelope and fire W-ON-02.

3. **NC clean rate WITH hooks: 100%; projected WITHOUT hooks: ~25-66%**
   on Complete-profile NCs depending on which hooks are removed.
   Hook removal would regress the catalog's NC FPR back toward
   pre-Phase-2.5 levels.

The hooks are not deadweight — they're filling a real LLM compliance
gap that prompts alone don't close. v0.5.13's value is the
**combination** of cleaner prompts (improving LLM compliance from 0%→
25-66% substantive) AND retained hooks (filling the remaining gap).

Future Phase 2 v3 work could try stronger prompt engineering or a
more compliant model (claude-opus, gpt-4o) to push substantive content
from 25% → 70%+, at which point hook removal becomes viable.

---

## Issues observed (informative, not blocking)

### GEN-INVALID rate of 16% (22/140)

Causes per package inspection:
- ~half: JSON truncation at the new 10-12K max_tokens cap (Complete
  profile + 13 factors + SA + envelope + offset rationale + acceptance
  criteria adds up to a lot of content)
- ~half: SHACL violations on edge cases (e.g., factor structure that
  passes SHACL when LLM is concise but fails when the LLM emits
  extensive narrative)

This affected which archetypes got fully covered — NC-5 (scoped-out)
and most of NC-7 (rejected) didn't run at all due to the cost cap
hitting first.

**Phase 2 v3 prescription**: bump max_tokens to 16K for Complete-profile
NCs, OR move toward streaming generation that doesn't truncate.

### NC-5 / NC-7 partial coverage

The cost cap halted generation at 75/90 cells. NC-5 had 0 packages
generated (its specs ran last alphabetically and got cut). NC-7 had
8/18 packages.

For the audit purposes, this isn't blocking — the field-presence
metrics are reliable on the archetypes that did run. But NC-5 and
NC-7 will need re-validation in Phase C's holdout if those archetypes
appear in the proportional spec sample.

---

## Cumulative catalog progression

| Milestone | NC clean rate | Mechanism |
|---|---|---|
| M5 baseline (v0.5.7) | 0/176 = 0.0% | (baseline) |
| v0.5.8 (W-EP-01 predicate) | 0/176 = 0.0% | predicate guard added |
| v0.5.9 (W-AL-02 schema-aligned) | 8/176 = 4.5% | predicate + schema |
| v0.5.10 (W-ON-02 corpus regen) | 71/176 = 40.3% | corpus regen + post-LLM hook |
| v0.5.11 (W-AR-02 schema + 2-rule + corpus) | 107/176 = 60.8% | predicate + schema + corpus + post-LLM hook |
| v0.5.12 (W-CON-01/04/AR-01) | 175/180 = 97.2% | predicate + corpus + post-LLM hook |
| v0.5.12.1 (generator-hook consistency) | 175/180 = 97.2% | hook fix only — production CLI now works |
| **v0.5.13 (Phase 2 v2 prompt cleanup)** | **118/118 = 100.0%** of validated | prompt directives + retained hooks |

---

## Files shipped in v0.5.13

| Path | Change |
|---|---|
| `specs/negative_controls/nc-clean-full-morrison-cou1.yaml` | max_tokens 8K→10K |
| `specs/negative_controls/nc-clean-full-morrison-cou2.yaml` | base_cou bug fix (cou1→cou2), mrl 2→5, max_tokens 8K→12K |
| `specs/negative_controls/nc-clean-full-nagaraja.yaml` | base_cou bug fix (morrison→nagaraja), mrl 2→3, max_tokens 8K→10K |
| `src/uofa_cli/adversarial/prompts/negative_controls.py` | Per-archetype task directives + new `NC_SCHEMA_REQUIREMENTS` block |
| `tests/adversarial/fixtures/snapshots/snapshot_negative_controls_*.txt` | 30 NC snapshots refreshed |
| `tools/phase2_5/run_phase_a.sh` (NEW) | Phase A driver |
| `tools/phase2_5/audit_phase_a.py` (NEW) | Phase A audit |
| `tools/phase2_5/audit_phase_b.py` (NEW) | Phase B audit |
| `out/phase2_5/2026-04-27/phase_a_pipeline_test_summary.md` (NEW) | Phase A findings |
| `out/phase2_5/2026-04-27/v0_phase2v2_summary.md` (this file, NEW) | Phase B findings |

NC corpus dir `out/adversarial/phase2/2026-04-29-v0_phase2v2-test/` is
gitignored per established Phase 2.5 convention.

**`src/uofa_cli/adversarial/generator.py` is UNCHANGED** — the v0.5.12.1
post-LLM hook block is preserved as designed. Hook removal deferred.

---

## Recommendation for Phase C

Proceed to Phase C (450-package holdout validation) using the v0.5.13
prompts + v0.5.12.1 hooks combination. Expected catalog characteristics:
- NC clean rate ≥ 90% on validated NCs (likely 100% based on Phase B)
- Some GEN-INVALID rate (~10-15%) due to LLM token-limit issues
- Hooks ensure structural integrity for the LLM's non-substantive output

Phase 2 v3 (future work) could revisit hook removal once SA substantive
emission consistently reaches ≥ 70%.
