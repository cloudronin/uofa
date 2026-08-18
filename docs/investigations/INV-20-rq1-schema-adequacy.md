# INV-20 — the Stage 4 adjudication is answering RQ1, and the answer is bounded but negative

Status: **OPEN** — the finding is measured; the adjudication it emerged from is not finished
Date: 2026-08-18
Found during: Stage 4 author adjudication, rows 2, 11, 12, 13, 16
Feeds: RQ1, Ch5 limitations, [UofA_Requirement_Layer_Spec_v0_1](../UofA_Requirement_Layer_Spec_v0_1.md)
Subsumes as symptoms: [INV-18](INV-18-w-con-02-scope.md), [INV-19](INV-19-requirement-layer-absent.md)

## The reframe

Stage 4 was built to measure the **ensemble**: author-versus-judge agreement over
21 disagreement cases, and a spot-check override rate over 50 convergent ones.
Phase 3's stated purpose is finding gaps in the **catalog**.

Twenty-one rows in, the dominant output is neither. It is a schema-adequacy
audit, and it bears on **RQ1 — is UofA capturing sufficient information to model
real-world examples?**

This was discovered, not hypothesized. The note records it as such, because a
reviewer will otherwise ask why an instrument built to measure ensemble agreement
is being cited for schema adequacy.

## The answer, bounded

A flat "no" would be both weaker and less accurate. The boundary is precise:

**Sufficient** for the credibility assessment itself — factors, gradations,
decisions, provenance, integrity. This demonstrably works across 4,556 packages
and the canonical examples.

**Insufficient** for the requirement being assessed against, the constraints that
requirement imposes, the argument connecting evidence to conclusion, and the
quantity identity that would link all three.

> **UofA captures the assessment, not the assurance case.**

## What was measured

| | |
|---|---|
| `uofa:Requirement` | class, **0** declared properties |
| `uofa:AssuranceClaim` | class, **0** declared properties |
| `uofa:OperatingEnvelope`, `uofa:ApplicabilityConstraint` | classes, **0** declared properties |
| Strategy / inference / warrant element | **none**; `factorConstraintWarrants` is `owl:deprecated`, comment reads *"not used by any package or shape"* |
| `specification`, `acceptanceThreshold`, `comparisonValue`, `comparisonMetric`, `quantityOfInterest`, `passed` | used in the corpus, **declared in neither vocabulary nor context**; reach `uofa:` only via `@vocab` |
| `requiredVerificationMethod` | declared, read by W-AR-03, populated in **1 of 78** packages |
| IRI references in canonical examples | **7/7, 7/7, 6/6, 3/3, 1/1** dangling |
| W-ON-02 | fires on **65 of 71** queue packages |

Four empty rooms, one absent element, six undeclared terms, one rule with no
data, and an absence-check that fires on nearly everything.

## Two classes with self-indicting comments

The vocabulary states the gap in its own words.

```
uofa:AssuranceClaim
  "The proposition the evidence is offered in support of. Naming it separately
   is what lets a reviewer ask whether the evidence actually supports it."
```

The stated purpose is to make support inspectable. The class has no properties,
so nothing can say what supports it or how.

```
uofa:WeakenerAnnotation
  "A condition under which the stated evidence does not support the claim
   it is offered for."
```

That describes a defeater on an **inference step** — GSN's SupportedBy, SACM's
`AssertedInference`, Toulmin's rebuttal. There is no inference step in the model.
Weakeners attach via `affectedNode` to a node, so the catalog has defeaters and
nothing for them to defeat.

## The common cause

INV-18 and INV-19 read as two unrelated gaps. They are the same one at different
depths, and a third sits beneath both:

1. **Rules look in the wrong places** (INV-18) — W-CON-02 polices an optional
   citation while every load-bearing reference dangles unchecked.
2. **There is nowhere right to look** (INV-19) — requirement content, constraints
   and applicability have no declared home, so prose fills them.
3. **There is no reasoning chain** — evidence and claims exist; the inference
   between them does not.

Each is a consequence of the layer below it. Extending catalog coverage while (2)
and (3) hold adds rules to the one layer that already works.

## The worked example

Row 16 (`adv-2026-p2-119-confusion-necessary-sufficient_high-v03`) is the cleanest
case in the queue, because **every structural fact in it is correct**.

The decision record argues that satisfying `RH < 1` — a necessary condition —
*"constitutes sufficient evidence that the computational model meets the safety
goal of this COU"*, then dismisses six unassessed factors as *"not required for
acceptance at this risk level and do not affect the sufficiency of the RH-based
safety demonstration."*

Model risk level is 2. At MRL 2 those six factors legitimately need not be
assessed, `factorStatus: not-assessed` records that faithfully, and W-EP-04
correctly stays silent. **The package is V&V 40 compliant.** What is abused is the
framework's own gradation logic: meeting the required rigour is claimed to
establish fitness for purpose.

Adjudicating it required a human to read a rationale paragraph and identify a
logical fallacy. That inference is in neither the package nor the catalog, and a
different reasoner could read the same rationale, accept it, and be no less
faithful to the artifact.

The corpus already measures this: **21 cases where three judges could not reach
2-of-3**. Those are cases where the artifact underdetermines the conclusion, and
the author adjudication is a human supplying the missing inference from outside
the record.

## Consequence for the design

Nothing in a UofA should be hand-authored. `uofa extract` already has the right
shape — documents in, structured out, HITL review of a spreadsheet, then `uofa
import` to a signed package — but its scope stops at credibility factors.
Requirements, constraints and argument reasoning would be further extraction
targets through the same path, grounded by the attribution work already underway
(`attribution-sentence-index`, `evidence-span`, `published-rationale-ceiling`).

For argument reasoning this matters more than anywhere else: an
extracted-with-spans argument is one located in what the assessor wrote, not one
the tool invented. That traceability is what makes a reasoning chain defensible
between reasoners, which is the property the corpus currently lacks.

**The failure mode to design against is measured.** `requiredVerificationMethod`
is declared, rule-read, and populated in 1 of 78 packages. Optional structure in
this project goes unpopulated. An argument layer that must be authored will be
empty in exactly the same way; one that is derived from the V&V 40 template — the
framework is itself an argument skeleton — leaves the author only the steps the
template does not determine. In Morrison COU1 that is precisely the step row 16
gets wrong.

## What this does not license

It does not retire the readouts Stage 4 was built for. Author-versus-judge
agreement and the per-stratum override rate still require the adjudication to be
finished, and they matter *more* under this finding, not less: "the ensemble was
judging against an inadequate schema" is a claim that wants the agreement numbers
attached to it.

It is also not a reason to stop adjudicating. The remaining rows are what convert
this from a well-founded reading of 21 rows into a measured claim over 71 — the
standard INV-17 set for itself: *count it before the chapter uses it*.

## Reproducing

```bash
# empty rooms
grep -c "rdfs:domain uofa:Requirement"    packs/core/shapes/uofa_shacl.ttl   # 0
grep -c "rdfs:domain uofa:AssuranceClaim" packs/core/shapes/uofa_shacl.ttl   # 0

# no inference element
grep -icE "strategy|assertedinference|decompos|warrant" packs/core/shapes/uofa_shacl.ttl

# terms used but undeclared
python -c "import json; c=json.load(open('spec/context/v0.5.jsonld'))['@context']; \
print({t: c.get(t) for t in ['specification','acceptanceThreshold','comparisonValue','quantityOfInterest']})"

# the declared rule-read field nobody populates
grep -rl requiredVerificationMethod packs/*/examples \
  dev/build/adversarial/phase2/2026-04-26/adjudication_packages/packages | wc -l   # 1
ls packs/*/examples/*/*/*.jsonld \
  dev/build/adversarial/phase2/2026-04-26/adjudication_packages/packages/*.jsonld | wc -l  # 78
```
