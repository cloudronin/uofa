# INV-19 — requirement content has nowhere structured to live, so prose fills it

Status: **OPEN** — measured; proposal drafted, four questions unruled
Date: 2026-08-18
Found during: Stage 4 author adjudication, row 12 (`adv-2026-p2-111-inconsistent_medium-v02`)
Feeds: [UofA_Requirement_Layer_Spec_v0_1](../UofA_Requirement_Layer_Spec_v0_1.md), Ch5 limitations
Related: [INV-18](INV-18-w-con-02-scope.md) — the rules look in the wrong places; this one says there is nowhere right to look

## The question

Row 12 is a gap probe for contradictory requirements. Adjudicating it meant
reading **1,087 characters of prose** across two `specification` fields and doing
interval arithmetic by hand to find that the two criteria disagree. That is the
exact activity the project exists to eliminate, so: **can a requirement be
expressed in UofA at all, such that a rule could have found this?**

## Headline

**No. `uofa:Requirement` is a declared class with zero declared properties, and
`specification` — the field the whole corpus uses — is declared nowhere.**

| | |
|---|---|
| Properties declared on `uofa:Requirement` | **0** |
| `uofa:specification` in the vocabulary | **absent** |
| `uofa:specification` in the v0.5 context | **absent** |
| Other constraint-shaped classes, also empty | `OperatingEnvelope`, `ApplicabilityConstraint` |
| `requiredVerificationMethod` — declared, rule-read | populated in **1 of 75** packages |

## What is actually in the package

```
{'id': …, 'type': 'Requirement', 'name': '…',
 'specification': '<473 chars of prose>', 'rationale': '<146 chars>'}
{'id': …, 'type': 'Requirement', 'name': '…',
 'specification': '<614 chars of prose>', 'rationale': '<242 chars>'}
```

Structure supplies two nodes and their names. The thresholds, the operators and
the contradiction are inside the prose. The disagreement is also larger than a
boundary quibble — the primary accepts any `RH < 1.0` with no floor, the
secondary accepts only `0.95 ≤ RH ≤ 1.0`, so they conflict at `RH = 1.0` **and**
across the whole band `[0, 0.95)`.

Nothing in the declared model could see either.

## Undeclared terms that look structural

`specification` is not an isolated case. Fields that appear structural in the
corpus and are declared in neither the vocabulary nor the context:

```
acceptanceThreshold  5x     comparisonValue    5x     passed             5x
comparisonMetric     7x     quantityOfInterest 7x     specification      2x
```

Because the context sets `@vocab: https://uofa.net/vocab#`, each silently expands
into a `uofa:` IRI the vocabulary never defines — real-looking terms in the
project's own namespace that resolve to nothing. `rationale` is the exception; it
is genuinely declared.

So packages that *look* like they carry structured thresholds carry improvised
ones.

## The pattern is native, pointed one level up

`W-AR-02` already compares `achievedLevel < requiredLevel` numerically and fires
on the gap. "Required value versus achieved value, checked mechanically" is not
foreign to this model — it is applied to **assessment gradation levels** rather
than to **engineering quantities**. One level down, where the physics is, the
rooms are empty.

## What V&V 40 actually asks for

Sampled from `packs/vv40/examples/morrison/cou1`. Real acceptance criteria take
four shapes and only one is a value bound:

| Shape | Representable today |
|---|---|
| Gradation goal — "Goal (b)" | **yes** |
| Required activity with cardinality — "repeated five times", "≥3 refined meshes" | no |
| Region containment — "validation point lies within the COU operating range" | no |
| Value bound — "RH < 1", "GCI below 5%" | no |

A single constraint primitive would cover roughly a quarter of the standard.

## The two layers

**Credibility goals** (V&V 40 Table 3/4) are modelled and checked.
**Device requirements** ("hemolysis shall not exceed predicate levels") have no
representation; `bindsRequirement` names one by IRI and its content lives nowhere.

The canonical example shows them colliding: the *Output comparison* credibility
goal quotes the device threshold as prose — *"small relative to safety threshold
(RH < 1)"* — because there is no requirement layer to put it in. The one
genuinely checkable engineering constraint in the factor set is embedded inside a
credibility goal.

## Why this is the load-bearing gap

Weakener analysis today answers *was the assessment adequately conducted*. It
cannot answer *does the model meet its requirement*, and every attempt to reach
the second through the first must infer from narrative — the failure INV-17
measured at ~200 judgments.

Extending catalog coverage without closing this adds rules to the layer that
already works while the layer beneath stays unmodelled. `requiredVerificationMethod`
is the warning: declared, read by `W-AR-03`, populated in 1 of 75 packages, and
firing once across the entire adjudication queue. A rule whose field nobody can
populate ships correct and never fires.

## Proposal

[UofA_Requirement_Layer_Spec_v0_1](../UofA_Requirement_Layer_Spec_v0_1.md) —
reference the external requirement (IRI + fetch hint + version + content hash),
project only the machine-relevant constraints, retain the source expression
verbatim so a mis-projection is detectable. Borrows SysML v2's
`subject` / `assume` / `require` frame.

Five pieces in dependency order; **quantity identity is the one that matters** —
a declared way for a requirement, a model output and a measurement to refer to
the same quantity. The rest is vocabulary and one rule.

Additive: a new context version leaves the 4,556-package Phase 2 corpus pinned to
v0.5 untouched, hashes and signatures intact, validating against the frozen
`/schemas/v0.5.json`.

## Left open

Four questions are posed in the proposal and none is ruled here: expressiveness
ceiling, quantity-identity mechanism, unit handling, and whether satisfaction
checking is *part of* the credibility claim or a layer deliberately beside it.
That last is a positioning decision and determines whether Ch5 reads "we do not
check this" or "we check this as of v0.8".

## Reproducing

```bash
# Requirement is a class with no properties; specification is undeclared
grep -n "uofa:Requirement a rdfs:Class" packs/core/shapes/uofa_shacl.ttl
grep -c "^uofa:specification" packs/core/shapes/uofa_shacl.ttl        # 0
python -c "import json; print(json.load(open('spec/context/v0.5.jsonld'))['@context'].get('specification'))"  # None

# the declared, rule-read field nobody populates
grep -rl requiredVerificationMethod packs/*/examples dev/build/adversarial/phase2/2026-04-26/adjudication_packages/packages | wc -l   # 1
```
