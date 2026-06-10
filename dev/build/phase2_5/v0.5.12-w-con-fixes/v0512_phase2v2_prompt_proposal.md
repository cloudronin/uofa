# Phase 2 v2 — NC prompt template improvement proposal

**Status**: planning doc only, not for execution this week. Captured during
v0.5.12.1 generator-hook audit so Phase 2 v2 has a clean starting point.

## Why prompt-template updates matter

Phase 2.5 closed the catalog NC clean rate from 0% to 97.2% via three
mechanisms layered on top of each other:

1. **Predicate tightening** at the rule layer (W-EP-01 v0.5.8, W-AL-02
   v0.5.9, W-CON-01 v0.5.12, W-AR-01 v0.5.12) — surgical, no LLM
   involvement.
2. **Post-LLM mutation hooks** in the generator pipeline (W-AR-02 v0.5.11,
   W-ON-02 + W-CON-04 v0.5.12.1) — runs reliably regardless of LLM
   behavior, but is "papering over" what should be the LLM's job.
3. **Patch tools** (`regen_nc_envelope.py`, `regen_nc_offset_rationale.py`,
   `regen_nc_consistency.py`) — same logic as the post-LLM hooks, applied
   post-hoc to existing corpus.

Mechanisms (2) and (3) are duplicates: the post-LLM hook fixes new
generations, and the patch tool fixes the existing M5 corpus. Both inject
*placeholder* content marked "(v0.5.10 NC regen)" / "(v0.5.11 NC regen)"
/ etc. **The placeholder content is structurally well-formed but
substantively empty.** A reviewer scanning a fresh-generated NC sees
generic strings like:

> "Placeholder operating envelope (v0.5.10 NC regen). Placeholder
> envelope inserted to satisfy the noValue check on
> uofa:hasOperatingEnvelope in the W-ON-02 rule predicate. Not
> substantively meaningful."

That's noise. It tells the reader nothing about the COU's actual envelope.
Phase 2 v2 should aim to have the LLM emit substantively-meaningful
content for these fields — making the post-LLM hook + patch tool
unnecessary.

## Per-NC archetype prompt updates

The current NC templates are in
`src/uofa_cli/adversarial/prompts/negative_controls.py`. The key
construct is the `NC_CONFIGS` dict mapping spec_id → `description` /
`task` / `subtlety` content. For each archetype, here's the proposed
delta.

### NC-1: `nc-clean-full-morrison-cou1` (Complete profile, MRL=2)

**Current task** (line 102-108):
```
generate a Complete-profile UofA covering all 13 V&V 40 factors as
'assessed' with consistent levels (requiredLevel <= achievedLevel for
each), full provenance, UQ present, acceptance criteria documented per
factor, decision Accepted.
```

**Proposed task** (additions in **bold**):
```
generate a Complete-profile UofA covering all 13 V&V 40 factors as
'assessed' with consistent levels (requiredLevel <= achievedLevel for
each), full provenance, UQ present, acceptance criteria documented per
factor, decision Accepted. **Include `hasSensitivityAnalysis` as an
inline SensitivityAnalysis object describing which model parameters
were varied and the response (1-2 sentences sufficient). Include
`hasApplicabilityConstraint` and `hasOperatingEnvelope` on the COU
with concrete bounds (e.g., flow rates 1-7 L/min for CPB, geometry
range, etc.) — derive from the base COU's narrative if available.**
```

Affects: W-CON-04 (SA), W-ON-02 (envelope) — replaces the post-LLM hook
output with substantively-meaningful content.

### NC-2: `nc-clean-minimal-morrison-cou1` (Minimal profile)

**No change.** Minimal profile doesn't trigger W-CON-04, and the W-ON-02
post-LLM hook still applies (NCs derived from Morrison COU1 inherit the
base COU's envelope structure).

### NC-3: `nc-clean-full-morrison-cou2` (Complete + MRL=5)

**Current task** (line 116-120):
```
generate a Complete-profile UofA at modelRiskLevel 5 with all 13
factors assessed at high rigor, full UQ + sensitivity analysis linked,
decision Accepted with thorough rationale.
```

The task already says "sensitivity analysis linked" but the LLM doesn't
always emit `hasSensitivityAnalysis` as an inline object — sometimes as a
narrative reference. **Make it explicit**:
```
generate a Complete-profile UofA at modelRiskLevel 5 with all 13
factors assessed at high rigor, full UQ, **`hasSensitivityAnalysis` as
an inline SensitivityAnalysis object (id, type, name, description) —
NOT just a narrative mention**, decision Accepted with thorough
rationale. **Include `hasApplicabilityConstraint` and
`hasOperatingEnvelope` on the COU.**
```

Affects: W-CON-04, W-ON-02.

### NC-4: `nc-clean-full-nagaraja` (Complete + orthopedic)

Same prescription as NC-1 — add SA + envelope explicit instructions.

### NC-5: `nc-clean-scoped-out-factors`

**Current task** is already fine (factors marked scoped-out with rationale
won't fire W-CON-01 post-v0.5.12). **Add explicit guidance**:
```
generate a UofA where a subset of factors are 'scoped-out' with
documented rationale. ... **For scoped-out factors, DO NOT emit
`requiredLevel` or `achievedLevel` — those imply the factor is
intended to be assessed.**
```

This prevents the v0.5.11 corpus issue (NC-5 LLM emitted scoped-out
factors with vestigial requiredLevel that triggered W-AR-01 before the
v0.5.12 predicate guard).

### NC-6: `nc-clean-not-applicable-factors`

Same as NC-5: **add "DO NOT emit `requiredLevel` / `achievedLevel` for
not-applicable factors"**.

### NC-7: `nc-clean-rejected-decision`

**This is the big one** — currently produces 5 W-EP-04 firings (the only
remaining NC firings post-v0.5.12). **Rewrite the task entirely**:

**Current task** (line 184-189):
```
generate a UofA whose decision is 'Not accepted' with documented
rationale. This is a CLEAN negative example — the rejection is
justified by the structured evidence (factors below required level,
weaknesses acknowledged), so no rule should fire spuriously.
```

**Proposed task**:
```
generate a UofA whose decision is 'Not accepted' with documented
rationale. The rejection is justified by EITHER:
  (a) factors below required level (achievedLevel < requiredLevel)
      with `factorStatus: 'assessed'`. The OffsetRationale is omitted
      intentionally — the rejection is the response to the shortfall,
      no offset is being claimed; OR
  (b) factors marked `factorStatus: 'scoped-out'` with rationale
      explaining what was excluded and why; the rejection cites the
      scoping decision.

DO NOT use `factorStatus: 'not-assessed'` at modelRiskLevel > 2 — that
fires W-EP-04 (correctly: an unassessed factor at elevated risk is a
credibility gap, not a rejection rationale).
```

This eliminates the residual 5 W-EP-04 firings.

### NC-8: `nc-clean-partial-envelope`

Already explicit. **Add**: "ensure both `hasApplicabilityConstraint` and
`hasOperatingEnvelope` are emitted as inline objects on the COU (not
just narrative references)."

### NC-9: `nc-clean-low-confidence-but-documented`

**Add Complete-profile instruction**: "If `conformsToProfile` is
`uofa:ProfileComplete`, include `hasSensitivityAnalysis`."

### NC-10: `nc-clean-compound-free`

**No change.** Already explicit about avoiding Critical+High coexistence.

## Cross-cutting NC changes

### `extra_schema_rules` (line 90-94 of `_nc_render`)

**Current**:
```
NC-v0.5.12: if `conformsToProfile` is `uofa:ProfileComplete`, include
`hasSensitivityAnalysis` as an inline SensitivityAnalysis object
(placeholder content acceptable).
```

**Proposed Phase 2 v2**:
```
NC schema requirements:

1. If `conformsToProfile` is `uofa:ProfileComplete`:
   - `hasSensitivityAnalysis` MUST be an inline SensitivityAnalysis
     object with id, type, name, description (1-2 sentences).
   - `hasContextOfUse.hasOperatingEnvelope` MUST be an inline
     OperatingEnvelope with concrete bounds.
   - `hasContextOfUse.hasApplicabilityConstraint` MUST be an inline
     ApplicabilityConstraint object.

2. For every CredibilityFactor with `factorStatus: 'assessed'`:
   - BOTH `requiredLevel` AND `achievedLevel` MUST be present (1-5).
   - `acceptanceCriteria` MUST be an inline AcceptanceCriteria object.

3. For factors with `factorStatus: 'scoped-out'` or 'not-applicable':
   - `requiredLevel` and `achievedLevel` MUST be omitted (those imply
     intended-assessment).
   - `rationale` MUST explain the scoping/N/A decision.

4. If `hasDecisionRecord.outcome == 'Accepted'` AND any factor has
   `achievedLevel < requiredLevel`:
   - `hasDecisionRecord.hasOffsetRationale` MUST be an inline
     OffsetRationale referencing the shortfall factor and explaining
     why the acceptance is justified despite the gap.

These are SHACL-optional in the schema but rule-required for
clean-package status. NCs that violate these will fire spurious
weakeners.
```

### Generator pipeline simplification

Once Phase 2 v2 prompt updates ship and fresh NC generation reliably
produces these fields, the post-LLM hooks can be **removed** from
`generator.py::_attempt_variant`. The patch tools (`regen_nc_*.py`)
remain for backwards-compatibility on the existing M5 corpus, but
become unnecessary going forward.

Rough scope for prompt-cleanup commit:
- Edit `src/uofa_cli/adversarial/prompts/negative_controls.py` per the
  above per-archetype changes (~150 lines of task-string edits).
- Update `tests/adversarial/fixtures/snapshots/snapshot_negative_controls_*.txt`
  via `UOFA_UPDATE_SNAPSHOTS=1 pytest`.
- Generate a fresh NC corpus from these prompts; run analyze.
- If NC clean rate ≥ 97.2% (matching v0.5.12), accept the prompt update
  and **remove the post-LLM hooks** from `generator.py`.
- If NC clean rate drops, iterate the prompt + hook combination.

## Acceptance criteria for Phase 2 v2

- All NC-1/3/4 (Complete profile) fresh generations include inline
  `hasSensitivityAnalysis` (>= 90% — measured via field-presence audit
  on a 30-NC sample).
- All Complete-profile NC generations include
  `hasApplicabilityConstraint` + `hasOperatingEnvelope` on the COU.
- NC-7 fresh generations no longer emit `factorStatus='not-assessed'`
  at MRL>2 (zero W-EP-04 firings on a 30-NC sample).
- Post-LLM hooks REMOVED from `generator.py::_attempt_variant`.
- Patch tools KEPT in `tools/phase2_5/` for M5-corpus backwards-compat.
- Catalog NC clean rate stays ≥ 97% on the freshly-generated corpus.

## Risks

| Risk | Mitigation |
|---|---|
| LLM output bloat from extra instructions | Snapshot diff review — instruction text is ~40-60 lines, response budget remains 8K tokens |
| Some LLMs may still produce unfilled fields despite explicit instruction | Keep post-LLM hooks until empirical NC clean rate ≥ 95% on fresh corpus; transition gradually |
| Snapshot test churn | Refresh via `UOFA_UPDATE_SNAPSHOTS=1`; reviewable diff |
| Substantive content adds review burden (each NC has more meaningful text) | Acceptable — substantive content IS the goal vs placeholder noise |
| Different LLM models comply differently | Run the field-presence audit per-model (claude-sonnet-4-6, gpt-4o, qwen) and tune until all hit ≥ 90% |

## Out of scope

- **Schema changes**: SensitivityAnalysis, ApplicabilityConstraint,
  OperatingEnvelope, AcceptanceCriteria, OffsetRationale all already
  exist in `spec/context/v0.5.jsonld`. No schema work needed.
- **Rule predicate changes**: v0.5.12 already addresses all overfiring
  rules. The remaining 5 W-EP-04 firings are addressed via the NC-7
  template fix above, not predicate.
- **CE / gap_probe / interaction templates**: untouched. Their job is to
  trigger weakeners; the NC template's job is to be clean. Different
  semantic intents, no overlap.
- **Patch tools**: `regen_nc_envelope.py`, `regen_nc_offset_rationale.py`,
  `regen_nc_consistency.py` remain for M5-corpus compat. They're
  deterministic regenerators tagged with v0.5.10/11/12 milestones.

## Estimated effort

- Per-archetype prompt edits: 1.5 hours (10 archetypes × 5-10 min each
  + extra_schema_rules rewrite).
- Snapshot refresh + review: 30 min.
- Fresh NC corpus generation (1 archetype × 3 subtleties × 7 base COUs
  × 2 variants ≈ 30 NCs per archetype × 10 archetypes = 300 NCs at ~30s
  each via Claude API ≈ $5-10 cost): 2-3 hours.
- Analyze + audit: 1 hour.
- Hook removal + verification: 1 hour.

**Total: ~6 hours for Phase 2 v2 NC prompt cleanup.** Saves ongoing
post-LLM hook complexity + makes NC content substantively reviewable
instead of placeholder noise.
