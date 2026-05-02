# Round 1 audit — Context bundle gap (SME Task 1)

**Date:** 2026-05-02
**Target firing:** W-EP-04 in [Morrison COU2](../../../packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld) — 6 hits, the SME-flagged canonical generic case
**Diagnostic script:** [round1_audit.py](round1_audit.py) (run to reproduce)

---

## Findings

**Hypothesis confirmed.** The current explain prompt for W-EP-04 contains:

- Pattern ID, severity, hit count
- A one-line pattern description from the `.rules` file
- COU metadata (name, device class, MRL)
- Standard reference

**It does not contain** any data that would let the LLM identify which six
factors were unassessed. The `affected_node` and `evidence_excerpt`
`FiringContext` fields are explicitly populated as empty strings (see
[context.py:197-199](../../../src/uofa_cli/interpretation/context.py)).

The data the SME wants the model to ground in is **already produced by the
rule engine in jsonld output mode**. We just don't pipe it through.

## Side-by-side: what's in the prompt vs what's available

### Currently in the prompt sent to Qwen

```
INPUT:
- Pattern ID: W-EP-04
- Severity: High
- Number of matches in this package: 6
- Pattern description (from rule definition): Unassessed Factor at Elevated Risk
- Context of Use: COU2: Ventricular assist device use (Class III) | Class III | MRL 5
- Standard: ASME-VV40-2018
```

The model sees "6 matches" with no way to know what was matched. The
explanation that comes back inevitably reads "six instances within the
simulation evidence package where a critical factor was not assessed" —
correct, but generic.

### Available via `rules.run_structured(format="jsonld")` — currently unused

The same engine, called with `--format jsonld`, emits one
`WeakenerAnnotation` per firing carrying the affected node IRI:

```json
{
  "@id": "_:b1",
  "@type": "https://uofa.net/vocab#WeakenerAnnotation",
  "https://uofa.net/vocab#patternId": "W-EP-04",
  "https://uofa.net/vocab#severity": "High",
  "https://uofa.net/vocab#affectedNode": {
    "@id": "https://uofa.net/morrison/cou2/factor/use-error"
  },
  "https://schema.org/description": "Credibility factor is not assessed but model risk level exceeds 2 — unassessed factors at elevated risk weaken the credibility argument."
}
```

Six W-EP-04 annotations carry these affected-node IRIs:
- `https://uofa.net/morrison/cou2/factor/use-error`
- `https://uofa.net/morrison/cou2/factor/test-samples`
- `https://uofa.net/morrison/cou2/factor/model-form`
- `https://uofa.net/morrison/cou2/factor/equivalency-of-input-parameters`
- `https://uofa.net/morrison/cou2/factor/numerical-solver-error`
- `https://uofa.net/morrison/cou2/factor/model-inputs`

### Available via JSON-LD walk of the package itself — currently unused

Each affected IRI resolves in the package to a credibility factor node
with a human-readable name + status:

| factorType | factorStatus | required | achieved |
|---|---|---|---|
| Use error | not-assessed | (omitted) | (omitted) |
| Test samples | not-assessed | (omitted) | (omitted) |
| Model form | not-assessed | (omitted) | (omitted) |
| Equivalency of input parameters | not-assessed | (omitted) | (omitted) |
| Numerical solver error | not-assessed | (omitted) | (omitted) |
| Model inputs | not-assessed | (omitted) | (omitted) |

The `factorType` field is exactly the regulatory-affairs-readable name
that the SME wants the explanation to cite. It's right there in the
package.

(Note: `requiredLevel` / `achievedLevel` are absent for not-assessed
factors in this fixture — the package doesn't pre-populate them. That's
fine; the explanation should say "not assessed" rather than enumerating
levels in this case.)

## Same gap for COMPOUND-01

The Round 0 SME score flagged COMPOUND-01 as the worst case: explanation
"a Critical weakener and a High weakener are present simultaneously"
without identifying *which two*. The jsonld engine output includes
`escalationSource` arrays linking the compound annotation to the
constituent firings; the same context-enrichment fix resolves both.

## Decision: scope of fix

| Approach | Cost | Decision |
|---|---|---|
| Switch all rules invocations to jsonld mode internally and reparse for both display and interpretation | Bigger change; risks breaking existing CLI behavior; touches `RulesResult` surface | **Rejected** |
| Re-invoke engine in jsonld mode only when `--explain` is set; pass rich firings to interpretation pipeline | One extra subprocess call when --explain is used; isolated to interpretation layer; `RulesResult.firings` and existing CLI output unchanged | **Selected** |
| Modify the rule engine itself to emit richer summary-mode output | Out of scope (Java work, ripple through diff.py and other consumers) | **Rejected** |

## Estimated time saved by Phase 1

Without this audit, Phase 3 (context enrichment) would have started by
guessing what the engine emits. The audit confirms:

1. The IRI structure (full URIs in jsonld output, mixed `id`/`@id` in
   package — the resolver needs to handle both)
2. The exact missing fields the model needs (`factorType`, `factorStatus`)
3. That the engine's `description` field on each WeakenerAnnotation
   makes our `parse_pattern_descriptions()` reading of the `.rules`
   file unnecessary in jsonld mode (it's a free downgrade)
4. The escalationSource shape for COMPOUND-01 (referenced in jsonld but
   not parsed yet — needs walking)

Phase 3 starts with a concrete spec for `_resolve_node_in_doc()`,
`_summarize_factor()`, and `_resolve_constituent_firings()` instead of a
guess.
