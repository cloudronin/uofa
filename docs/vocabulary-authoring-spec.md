# UofA Vocabulary Authoring Spec v0.1

**Deliverable:** `rdfs:label` and `rdfs:comment` for the UofA vocabulary terms
that currently have none, written into the pack shape files.

**Why now:** the three vocabulary namespaces went live at
[uofa.net/vocab/](https://uofa.net/vocab/) on 2026-08-04. Every term is
addressable, so `https://uofa.net/vocab#hasWeakener` resolves to its entry. The
pages currently show derived metadata for most core terms and state plainly
where nothing exists. This spec covers closing that gap.

**Audience for the writing:** someone who has hit a UofA property name in a
JSON-LD package, or followed a `@vocab` expansion, and wants to know what the
term means. Not a standards author, and not someone reading the whole
vocabulary top to bottom.

---

## 1. What is missing

Counts are from `site/scripts/lib/vocab-extract.mjs` against the current repo.
Regenerate with `npm run sync:vocab` in `site/`.

| Namespace | Terms | Have label | Need label | Need comment |
|---|---|---|---|---|
| `vocab#` (core) | 136 | 2 | **134** | **134** |
| `vocab/aims#` | 127 | 127 | 0 | **51** |
| `vocab/surrogate#` | 39 | 39 | 0 | **14** |

**199 items total.** The two core terms that already have definitions
(`Disposition`, `Discrepancy`) come from `packs/disposition/shapes/`, and their
form is the model to follow.

The core namespace is the priority. It is the `@vocab` of every package the
project has ever produced, including packages on users' machines that will never
be published, so it is the one namespace a stranger is most likely to look up.

---

## 2. Where the writing goes

**Into the repo, not into the site generator.**

| Namespace | File |
|---|---|
| `vocab#` (core) | `packs/core/shapes/uofa_shacl.ttl`, in a new vocabulary block at the top |
| `vocab/aims#` | `packs/iso42001/shapes/iso42001_shapes.ttl`, existing §A block |
| `vocab/surrogate#` | `packs/surrogate/shapes/surrogate_shapes.ttl`, existing §A block |

`packs/iso42001/shapes/iso42001_shapes.ttl` already documents this pattern in
its own header: embedded RDFS is picked up by the existing pyshacl loader. So
definitions written here improve SHACL tooling as well as the website, and the
site regenerates from them with no code change.

Do not put prose in `site/scripts/`. The generator reads definitions; it must
never become the place they live.

### Required form

```turtle
uofa:ContextOfUse a rdfs:Class ;
    rdfs:label "Context of Use" ;
    rdfs:comment "The specific question the model is being used to answer, and the decision that rides on the answer." .

uofa:hasWeakener a rdf:Property ;
    rdfs:label "Has weakener" ;
    rdfs:comment "Links a package to a condition under which its stated evidence does not support the claim it is offered for." .
```

Constraints the extractor enforces, and will fail the build over:

- One `rdfs:label` and one `rdfs:comment` per term, each a **single-line
  double-quoted literal**. Triple-quoted and multi-line literals are rejected on
  purpose, so that a definition can never be silently half-read.
- Every term declared `a rdfs:Class` or `a rdf:Property`. 134 core terms
  currently declare neither, so the site cannot even say which a term is.
- `rdfs:subClassOf` where a genuine hierarchy exists. Optional.
- Terms use the `uofa:`, `uofa-aims:`, `uofa-surr:` prefixes already declared in
  each file.

---

## 3. What each definition must cover

### `rdfs:label`

Title case, no trailing period, expands the identifier rather than restating it.
`hasValidationResult` becomes "Has validation result", not "hasValidationResult".

### `rdfs:comment`

One or two sentences. It must answer **what the term means in a credibility
record**, not what its datatype is. The datatype, cardinality and pattern are
already derived from SHACL and shown next to the definition, so repeating them
wastes the only space anyone will read.

Every comment must cover:

| Requirement | Detail |
|---|---|
| What it is | The thing itself, in the reader's vocabulary, not the schema's |
| Why a record carries it | What a reviewer learns from it being present |
| For properties, what it connects | The subject and object in plain terms |

Explicitly out of scope for a comment:

- Restating the datatype or cardinality
- Naming the JSON key, which the page already shows
- Explaining JSON-LD or RDF mechanics
- Worked examples, which belong in `docs/` or the concept pages

### Core is standard-agnostic. This is a hard rule.

**No core definition may cite a standard, clause, or table.** Not ASME V&V 40,
not NASA-STD-7009B, not ISO 42001. Write core terms in terms of the UofA model
alone.

This is not a stylistic preference. `uofa:factorType`, `uofa:achievedLevel`,
`uofa:requiredLevel` and `uofa:factorStandard` are each constrained by four
different shape files: `core`, `vv40`, `nasa-7009b` and `mrm-nist`. One term,
four standards. A definition that says "the V&V 40 Table 5-1 factor name" is
wrong the moment a NASA package uses it, and packages already do.

The clinching evidence is `uofa:factorStandard` itself. Its existence means the
governing standard is **data carried on the factor**, not something baked into
the vocabulary. Writing the standard into the definition would contradict the
one term whose whole job is to record which standard applies.

Several core terms sound like they belong to V&V 40 because that is where the
vocabulary was first exercised. Gradation language in particular
(`achievedLevel`, `requiredLevel`) reads as V&V 40 house style. Resist it.

```turtle
# Wrong. Narrows a four-standard term to one, and duplicates factorStandard.
uofa:requiredLevel a rdf:Property ;
    rdfs:label "Required level" ;
    rdfs:comment "The ASME V&V 40 Table 5-1 gradation this factor must reach." .

# Right. True whichever standard governs the assessment.
uofa:requiredLevel a rdf:Property ;
    rdfs:label "Required level" ;
    rdfs:comment "The rigour this factor has to reach for the assessment to stand, set before the evidence is gathered. The standard that fixes the scale is recorded separately on the factor." .
```

The test to apply to any core definition: swap the package's `factorStandard`
from `ASME-VV40-2018` to `NASA-STD-7009B`. If the definition becomes false, it
is too narrow.

Where a term genuinely has no meaning outside one standard, that is a signal it
belongs in that standard's pack namespace rather than in core. Say so in review
instead of writing a narrow definition into a wide namespace.

**The pack namespaces are the opposite case.** `vocab/aims#` terms map one to
one onto ISO 42001 clauses and their existing comments cite them, correctly.
Keep doing that for `aims` and `surrogate`.

### Voice

Follow the existing `iso42001_shapes.ttl` comments for length and register. They
are short and declarative. Take the form, not the clause citations, which belong
only to the pack namespaces.

- No em dashes.
- No tripartite lists.
- Do not use "simply", "just", "of course", or "note that".
- Prefer the concrete noun to the abstraction. "The bench test the model is
  compared against" beats "the comparative evidentiary basis".
- A term whose meaning is genuinely contested or unsettled should say so rather
  than paper over it. `agreementMakesNonDispositive` is allowed to admit that it
  encodes a specific argumentation stance.

---

## 4. Order of work

The tiers are how the terms are actually encountered, not how they sort
alphabetically. Tier 1 alone would move the core namespace from 1% documented to
roughly 49%.

### Tier 1, the 64 terms used by the shipped example packages

These appear in published records, so a reader following a link from a case
handout or an identifier page lands on them first. 13 are classes.

Highest usage first, since these carry the most weight per definition written:

| Usage | Terms |
|---|---|
| 39 | `factorStandard`, `factorStatus`, `factorType`, `CredibilityFactor` |
| 37 | `affectedNode`, `patternId`, `severity`, `WeakenerAnnotation` |
| 32-28 | `rationale`, `acceptanceCriteria` |
| 27 | `achievedLevel`, `requiredLevel` |
| 11-10 | `intendedUse`, `outcome` |
| 7 | `actor`, `assuranceLevel`, `bindsRequirement`, `conformsToProfile`, `couName`, `decision`, `hash`, `hasContextOfUse`, `hasDecisionRecord`, `hasValidationResult`, `hasWeakener`, `modelRiskLevel`, `signature`, `ContextOfUse`, `DecisionRecord`, `UnitOfAssurance` |
| 6 | `deviceClass`, `hasUncertaintyQuantification` |
| 5 | `bindsClaim`, `decidedAt`, `role` |
| 1-4 | `bindsDataset`, `bindsModel`, `canonicalizationAlg`, `comparedAgainst`, `credibilityIndex`, `criteriaSet`, `currentModelVersion`, `hasCredibilityFactor`, `hasEvidence`, `hasOffsetRationale`, `hasOperatingEnvelope`, `hasSensitivityAnalysis`, `justification`, `refersToFactor`, `signatureAlg`, `sourceReference`, `toolVersion`, `traceCompleteness`, `uncertaintyCIWidth`, `validationCoverage`, `verificationCoverage`, `AcceptanceCriteria`, `AssuranceClaim`, `Comparator`, `OffsetRationale`, `ProfileComplete`, `ProfileMinimal`, `ValidationResult`, `VerificationActivity` |

**The structural spine inside Tier 1 is the real starting point:**
`UnitOfAssurance`, `ContextOfUse`, `CredibilityFactor`, `ValidationResult`,
`DecisionRecord`, `AssuranceClaim`, `AcceptanceCriteria`, `OffsetRationale`,
`WeakenerAnnotation`. Nine classes. They name the model everything else hangs
off, and all nine are currently blank. Write these first even though some have
low raw usage counts, because every other definition will refer to them.

### Tier 2, the 17 unused terms that carry a `sh:message`

`actionClass`, `actionParameters`, `confidenceLevel`, `dataVintage`,
`discrepancyMagnitude`, `discrepancyRegion`, `documentReference`,
`evidenceTimestamp`, `hasDisposition`, `isFoundationalEvidence`, `measureType`,
`modelRevisionDate`, `modelVersion`, `reviewer`, `signatureTimestamp`,
`solverTruth`, `surrogatePrediction`

Each already has a validation message that states the constraint. That message
is a starting point, not a definition, and must not be pasted in as one.

### Tier 3, the 53 terms with no derived text at all

`activityType`, `addresses`, `agreementMakesNonDispositive`,
`analyzesConfiguration`, `assessmentPhase`, `attestedAt`, `attestedBy`,
`commit`, `consideredAlternative`, `deployedIn`, `deploymentContext`,
`deploymentDate`, `deploymentOutcome`, `environment`, `exercised`,
`factorConstraintWarrants`, `frameworkTransfers`, `hasApplicabilityConstraint`,
`hasDiscrepancy`, `hasFactorOffset`, `hasJustification`, `hasParameter`,
`hasVerificationActivity`, `knownLimitation`, `offsettingEvidence`,
`pedigreeLevel`, `processType`, `referencesIdentifier`,
`requiredVerificationMethod`, `residualRiskJustification`, `reviewDate`,
`reviewFindings`, `reviewScope`, `reviewType`, `supports`,
`sustainedDefeaterJustified`, `thresholdDistanceModulates`, `tool`,
`transformationDescription`, `validForModelVersion`, `version`,
plus the classes `ApplicabilityConstraint`, `Dataset`, `DeploymentRecord`,
`InputPedigreeLink`, `Model`, `ModelConfiguration`, `OperatingEnvelope`,
`ProcessAttestation`, `ProfileDisposition`, `Requirement`, `ReviewActivity`,
`SensitivityAnalysis`

**Tier 3 needs a decision before it needs prose.** A term defined in the context
but used by nothing, constrained by nothing, and described by nothing may be
vocabulary that was designed and never adopted. For each, decide: define it,
mark it deprecated, or remove it from the context. Writing a definition for a
term that should be retired is worse than leaving it blank, because it makes
dead vocabulary look load-bearing.

### Tiers 4 and 5, the other two namespaces

51 `aims` and 14 `surrogate` terms have labels but no comment. Lower priority
because the label already carries most of the meaning and the ISO clause is
usually in a sibling term's comment. The surrogate set is small and cohesive
(`CalibrationEvidence`, `constraintId`, `coordinateName`, `coordinateValue`,
`declaredPhysicsConstraint`, `dimensionName`, `evaluationPoint`,
`evaluationRegion`, `hasBenchmarkProvenance`, `hasCoordinate`, `maxBound`,
`minBound`, `parentModelSnapshot`, `parentSignatureTimestamp`) and is a
reasonable single sitting.

---

## 5. Definition of done

Per tier, not for all 199 at once. A tier is done when:

1. `cd site && npm run sync:vocab` succeeds. It fails loudly on any
   `rdfs:label` or `rdfs:comment` line it cannot parse, so a malformed literal
   cannot ship.
2. `cd site && npm test` passes. The coverage assertions in
   `site/scripts/lib/vocab-extract.test.mjs` pin the current counts, so they
   **must be updated deliberately** as part of the same change. That is the
   intended friction: it makes coverage a reviewed number rather than a silent
   drift.
3. `uofa shacl packs/vv40/examples/nagaraja/cou1/uofa-nagaraja-cou1.jsonld`
   still conforms. Adding RDFS to a shapes file must not change validation.
4. The rendered page at `/vocab/` shows the new definitions and the honesty
   banner count has gone down.
5. No term has a comment that only restates its datatype or its name.

When core reaches full label coverage, remove the "largely undocumented" banner
logic from `site/scripts/lib/vocab-render.mjs`. It is driven by the counts, so it
will soften on its own, but the wording is written for a namespace at 1% and
should be revisited rather than left to degrade gracefully.

---

## 6. Non-goals

- Do not change any term IRI or any context file. Those are inside the
  canonicalised content that package hashes and signatures cover.
- Do not add new vocabulary terms. This is documentation of what exists.
- Do not write definitions into `site/`.
- Do not retarget shipped packages' `@context` at uofa.net.
- Do not expand `spec/schemas/uofa.schema.json` by hand. It is generated.

---

## 7. Open questions for whoever writes this

1. **Tier 3 disposition.** 53 terms are defined in the context but used,
   constrained and described by nothing. How many are live design and how many
   are abandoned? This is the only question that blocks work, and it only blocks
   Tier 3.
2. **`instances/` namespace.** `src/uofa_cli/excel_constants.py` sets
   `BASE_URI = "https://uofa.net/instances"`, so every package a user creates via
   the Excel importer mints identifiers in a domain they do not control, for
   private data that can never resolve there. Not a writing task, but it belongs
   in the same conversation about what the uofa.net namespace is for.
## 8. Decisions already taken

**Core is standard-agnostic** (2026-08-04). No core definition cites a standard,
clause or table. See the rule in §3, which carries the reasoning and the
evidence. The pack namespaces keep their clause citations.

A consequence worth watching during review: if a proposed core definition cannot
be written without naming a standard, that is evidence the term belongs in a
pack namespace instead. Raise it rather than narrowing the definition to fit.
