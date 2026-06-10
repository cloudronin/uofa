# Phase 2.5 v0.5.12 — Residual NC firing audit (W-EP-04)

After v0.5.12, the catalog has 5 residual NC firings, all on W-EP-04. This
document audits each firing to determine whether it represents a rule
over-firing (that should be addressed in a future fix) or a legitimate
weakener detection on a corpus-quality issue (that should be deferred to
Phase 2 v2 NC-regen).

## Summary

**Conclusion: all 5 firings are LEGITIMATE detections.** No rule changes
required. Defer to Phase 2 v2 NC-regen brief.

The W-EP-04 rule fires when:
- `modelRiskLevel > 2` AND
- ≥1 credibility factor has `factorStatus='not-assessed'`

The semantic intent — "an unassessed factor at elevated model-risk weakens
the credibility argument" — is sound. The 5 firings are on NC packages
where the LLM **honestly** emitted unassessed factors at elevated MRL,
which is exactly the corpus-quality pattern the rule is designed to catch.

## Per-NC audit

All 5 firings come from the **NC-207 ("rejected decision")** archetype on
**Morrison COU2 (MRL=5)**:

| spec_id | variant | outcome | MRL | not-assessed factors | Verdict |
|---|---|---|---|---|---|
| `adv-2026-p2-207-nc-clean-rejected-decision_low_morrison-cou2` | v=1 | Not accepted | 5 | 5 (Numerical solver, Use, Model form, +2) | Legitimate |
| `adv-2026-p2-207-nc-clean-rejected-decision_low_morrison-cou2` | v=2 | Not accepted | 5 | 6 | Legitimate |
| `adv-2026-p2-207-nc-clean-rejected-decision_medium_morrison-cou2` | v=1 | Not accepted | 5 | 6 | Legitimate |
| `adv-2026-p2-207-nc-clean-rejected-decision_high_morrison-cou2` | v=1 | Not accepted | 5 | 6 | Legitimate |
| `adv-2026-p2-207-nc-clean-rejected-decision_high_morrison-cou2` | v=2 | Not accepted | 5 | 6 | Legitimate |

## Pattern analysis

The NC-207 archetype's task says (per `src/uofa_cli/adversarial/prompts/negative_controls.py`):

> generate a UofA whose decision is 'Not accepted' with documented rationale.
> This is a CLEAN negative example — the rejection is justified by the
> structured evidence (factors below required level, weaknesses
> acknowledged), so no rule should fire spuriously.

The LLM correctly produces a "rejection-justified-by-evidence" package. But
on Morrison COU2 (modelRiskLevel=5), the rejection mechanic the LLM chose is
to flag specific factors as `factorStatus='not-assessed'` — which is a
legitimate way to construct a rejected-decision-with-rationale package, but
also exactly what triggers W-EP-04 at MRL>2.

### Two possible interpretations

**Interpretation A: "Not-assessed at MRL=5 in a rejection scenario should be
fine because the package was rejected anyway."**

This would call for tightening W-EP-04 to skip when `outcome != 'Accepted'`
(adding `(?dr uofa:outcome 'Accepted')` guard). However, this changes the
rule's intent — currently W-EP-04 flags an unassessed factor at elevated
risk regardless of whether the package was accepted, on the principle that
"unassessed at elevated risk is a credibility gap, full stop."

**Interpretation B: "The rule is correctly flagging a real corpus issue —
NC-207 should construct rejection rationale via `factorStatus='scoped-out'`
with rationale, not `not-assessed`."**

This is the position v0.5.12 adopts. The factor status `'not-assessed'`
literally means "we did not assess this factor" — emitting it at MRL=5 is
a credibility gap (you should have assessed it). The cleaner NC-207
construction would use `'scoped-out'` (we explicitly chose not to apply
this factor) or `'not-applicable'` (this factor doesn't apply to the
domain), both of which the v0.5.12 W-CON-01 / W-AR-01 guards already
respect.

## Phase 2 v2 NC-regen prescription

NC-207 task (line 167-176 of `src/uofa_cli/adversarial/prompts/negative_controls.py`)
should be updated to instruct the LLM:

```
generate a UofA whose decision is 'Not accepted' with documented
rationale. The rejection is justified by:
  - factors below required level (achievedLevel < requiredLevel) — fires
    W-AR-02, but the OffsetRationale stub suppresses it on assessed
    factors; OR
  - factors marked 'scoped-out' with rationale (NOT 'not-assessed' at
    MRL>2 — that fires W-EP-04 by design)
```

This nudges future NC-207 generations toward the cleaner construction.
Existing 5 NC-207 packages from M5 corpus would still fire W-EP-04 unless
re-generated, which is out of scope for v0.5.12.

## Decision

**No code changes for v0.5.12.** Document the legitimate detections in this
audit; defer NC-207 template improvement to Phase 2 v2.

## Comparison with prior audits

| Phase 2.5 release | Audited residuals | Verdict |
|---|---|---|
| v0.5.10 | 105 NCs across 5 rules | Mostly corpus quality (W-AR-02, W-CON-01/04, COMPOUND chain) |
| v0.5.11 | 69 NCs across 5 rules | Mostly corpus quality (W-CON-01/04, W-EP-04 minor) |
| **v0.5.12** | **5 NCs on W-EP-04 only** | **All legitimate detections — corpus quality issue, not rule overreach** |
