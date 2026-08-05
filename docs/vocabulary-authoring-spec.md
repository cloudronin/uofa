# UofA Vocabulary Authoring Spec v0.3

*v0.3 (2026-08-04): label casing corrected, classes Title Case and
properties lowercase, matching all 166 existing labels; group 3e cut from 22 to
19 after git archaeology; the pinned-count claim in §5 corrected.*

*v0.2 (2026-08-04): core standard-agnostic rule promoted to §3 with its evidence;
Tier 3 resolved as define-all and split into five sourced groups; criteria set
decision added; shape-file counts corrected. All counts re-verified against the
repo at this revision.*

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
    rdfs:label "has weakener" ;
    rdfs:domain uofa:UnitOfAssurance ;
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

The type line must end at `;` or `.`. Writing
`a rdf:Property, owl:DeprecatedProperty ;` drops the term from the published
vocabulary **without erroring**, so put any extra type or flag on its own line.

### `rdfs:domain` and `rdfs:range`

Order is label, then domain, then range, then comment.

**`rdfs:domain` is not "may only appear on".** It entails that anything carrying
the property *is* an instance of that class. So declare it only when a single
class is true of **every** carrier, and omit it otherwise — the definition says
in prose which classes carry the term instead.

Deciding, in order:

1. If the shipped examples carry the property, the domain is the class every
   carrying node has. Nodes hold several types at once (four packages are typed
   `["UnitOfAssurance", "CredibilityEvidencePackage"]`), so intersect the type
   sets rather than collecting them.
2. If nothing uses it yet, take the `sh:targetClass` of the node shape whose
   `sh:path` is the property, where exactly one shape claims it.
3. Otherwise declare nothing.

**Omit whenever the answer is not in the term's own namespace.** A `uofa:`
property with `rdfs:domain uofa-aims:DataResourceProvenance` makes core depend
on a pack and inverts the layering. `documentReference`, `sourceReference` and
`hasOperatingEnvelope` are the three that tempt it; a test enforces this.

Range follows `sh:datatype` where a property shape gives one, `sh:class` next,
and the type of the referenced node otherwise. Where usage points at several
classes that share a superclass in the right namespace, name the superclass:
`bindsClaim` reaches eight aims claim classes, all of which subclass
`uofa:AssuranceClaim`.

These triples are documentation. No validator reads them: pyshacl is called
with no `ont_graph` and no inference at all three call sites, and the Jena
engine never loads the shapes. Declaring a domain cannot change what validates.

### `owl:deprecated`

For a term that was published and should no longer be used:

```turtle
uofa:frameworkTransfers a rdf:Property ;
    rdfs:label "framework transfers" ;
    rdfs:comment "Declared in context v0.6 and not used by any package or shape." ;
    owl:deprecated true .
```

Mark, never delete. The IRI stays resolvable for anyone who already wrote it
down; removing it turns a published identifier into a 404.

Write only `true` — `false` is the RDF default and says nothing, so the
extractor ignores it rather than treating it as a second state.

State the checkable fact, not the intent. "not used by any package or shape" is
something a reader can verify; "abandoned" is a claim about what someone meant,
and the repository is usually not the place that knows.

---

## 3. What each definition must cover

### `rdfs:label`

Expands the identifier into words rather than restating it, with no trailing
period. **Casing depends on whether the term is a class or a property**, and the
166 labels already in the repo are unanimous on this:

| | Casing | Example |
|---|---|---|
| Classes | Title Case | `uofa:ContextOfUse` becomes `"Context of Use"` |
| Properties | lowercase | `uofa:hasValidationResult` becomes `"has validation result"` |

*(Corrected in v0.3. Earlier revisions said Title case for everything and used
`"Has weakener"` as a worked example, which no existing label in the repo
matches. 83 of 83 classes are Title Case and 83 of 83 properties are lowercase,
across both the aims and surrogate namespaces.)*

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

This is not a stylistic preference. `uofa:factorType` and
`uofa:factorStandard` are each constrained by four different shape files
(`core`, `vv40`, `nasa-7009b`, `mrm-nist`); `uofa:achievedLevel` and
`uofa:requiredLevel` by three (`core`, `vv40`, `nasa-7009b`). One term, several
standards. A definition that says "the V&V 40 Table 5-1 factor name" is wrong
the moment a NASA package uses it, and packages already do.

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
    rdfs:label "required level" ;
    rdfs:comment "The ASME V&V 40 Table 5-1 gradation this factor must reach." .

# Right. True whichever standard governs the assessment.
uofa:requiredLevel a rdf:Property ;
    rdfs:label "required level" ;
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

**Decision (2026-08-04): all 53 get definitions.** Nothing is deprecated and
nothing is removed. The earlier framing of this as define-or-retire is closed.

A caveat that survives the decision, and belongs in review rather than in the
prose: a definition on an unadopted term makes it look load-bearing. Where a
term is deliberately not in use, say so in the definition itself. The staged
group below is the clearest case.

These terms have no label, comment, SHACL constraint or schema description, so
the writer needs a source. The repo has more than it looks like, unevenly
distributed. Groups are ordered by how much material exists.

#### 3a. Staged vocabulary, 3 terms

`consideredAlternative`, `knownLimitation`, `residualRiskJustification`

**These are unused on purpose and must not be described as abandoned.**
`CHANGELOG.md` records them as "Staged CLARISSA vocabulary for v0.6
W-AR-06/W-AR-07", and
`src/uofa_cli/adversarial/prompts/clarissa_machinery.py` actively enforces
non-emission, because the calibration probes target their *absence* as the
defeater condition. A generator that emitted them would break the probes.

Each definition should say what the property will record and note that it is
reserved for the W-AR-06/W-AR-07 patterns and not yet expected in packages.

#### 3b. Excel importer vocabulary, 9 terms

`attestedBy`, `deployedIn`, `deploymentOutcome`, `processType`, `reviewType`,
and the classes `DeploymentRecord`, `InputPedigreeLink`, `ProcessAttestation`,
`ReviewActivity`

Source: `src/uofa_cli/excel_mapper.py` and `src/uofa_cli/excel_constants.py`.
The importer maps spreadsheet columns onto these, so the column headings and the
mapping code carry the intended meaning. `packs/core/shapes/uofa_shacl.ttl`
constrains several of them as well.

#### 3c. Weakener-rule vocabulary, 11 terms

`activityType`, `assessmentPhase`, `hasApplicabilityConstraint`,
`hasFactorOffset`, `hasVerificationActivity`, `offsettingEvidence`,
`requiredVerificationMethod`, and the classes `ApplicabilityConstraint`,
`ModelConfiguration`, `OperatingEnvelope`, `SensitivityAnalysis`

Source: the pattern descriptions in `CHANGELOG.md` (W-ON-02 is defined as a COU
lacking both `hasApplicabilityConstraint` and `hasOperatingEnvelope`, W-AR-03
compares `requiredVerificationMethod` against `activityType`, W-AR-04 compares
`ModelConfiguration.modelVersion` against `currentModelVersion`), plus
`packs/core/rules/uofa_weakener.rules` and the positive and negative fixture
pairs under `tests/fixtures/weakeners/`. A fixture pair shows exactly what the
presence and absence of a term mean, which is the strongest evidence available
for any of these terms.

#### 3d. Structural terms with wide usage elsewhere, 8 terms

`commit`, `referencesIdentifier`, `supports`, `tool`, `version`, and the classes
`Dataset`, `Model`, `Requirement`

These are used across `src/`, `specs/` and the calibration corpus, but under
names common enough that a plain search is noisy. Read the JSON Schema and the
SHACL shape that constrains each before writing, and beware of matching
unrelated English.

#### 3e. No source anywhere in the repository, 22 terms

`addresses`, `agreementMakesNonDispositive`, `analyzesConfiguration`,
`attestedAt`, `deploymentContext`, `deploymentDate`, `environment`, `exercised`,
`factorConstraintWarrants`, `frameworkTransfers`, `hasDiscrepancy`,
`hasJustification`, `hasParameter`, `reviewDate`, `reviewFindings`,
`reviewScope`, `sustainedDefeaterJustified`, `thresholdDistanceModulates`,
`transformationDescription`, `validForModelVersion`, plus `ProfileDisposition`
and `pedigreeLevel`

Searched: `docs/`, `specs/`, `src/`, `tests/`, `packs/`, `spec/`, `CHANGELOG.md`
and the archived architecture notes. These appear in the JSON-LD context files
and nowhere else. There is no code that reads them, no shape that constrains
them, no fixture that exercises them, and no prose that mentions them.

**Only the author can write these.** They cannot be reconstructed by reading the
repository, and a definition invented from the identifier would be a guess
published at an authoritative URL. Seven of them
(`agreementMakesNonDispositive`, `factorConstraintWarrants`,
`frameworkTransfers`, `hasDiscrepancy`, `ProfileDisposition`,
`sustainedDefeaterJustified`, `thresholdDistanceModulates`) arrived together in
context v0.6 alongside the disposition work, so
`packs/disposition/shapes/disposition_shapes.ttl` shows the register their
neighbours use even though it does not define them.

If a term in this group turns out to have no recoverable intent, that is worth
knowing and worth recording as such, rather than dressing it up.

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
   **must be updated deliberately** as part of the same change, which makes
   coverage a reviewed number rather than silent drift.

   **Run this by hand. No workflow does.** The only test command in
   `.github/workflows/` is `pytest tests/space -q` in `deploy-space.yml`, so the
   pinned counts gate nothing in CI today. Either add `npm test` to
   `deploy-site.yml` or accept that a reviewer checks it each batch. Note also
   that only `labelled` is pinned, not `commented`, so the aims and surrogate
   comment batches do not touch this file at all.
3. `uofa shacl packs/vv40/examples/nagaraja/cou1/uofa-nagaraja-cou1.jsonld`
   still conforms. Adding RDFS to a shapes file must not change validation.
4. The rendered page at `/vocab/` shows the new definitions and the honesty
   banner count has gone down.
5. No term has a comment that only restates its datatype or its name.

The "largely undocumented" banner in `site/scripts/lib/vocab-render.mjs` is
**not** count-driven, contrary to what an earlier revision of this spec said. It
renders whenever the namespace is core, so it will keep claiming the namespace is
undocumented at full coverage. Rewrite that logic once core labels land rather
than leaving it to soften on its own, because it will not.

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

**The 22 terms in group 3e**, and nothing else. They exist in the context files
and nowhere else in the repository. Only the author can supply their intent; no
amount of reading recovers it. This does not block the other 177 items, so the
writing can start without an answer.

Every other question this spec opened has since been decided. See §8.

---

## 8. Decisions already taken

**`uofa.net/instances/` is this project's own example namespace only**
(2026-08-04). `uofa import` previously minted every user's identifiers there,
under a domain they do not control. It now defaults to the `example.org`
placeholder, matching what `uofa init` already scaffolded, and takes a namespace
the author controls via `--base-uri` or `[project] base_uri` in `uofa.toml`.
uofa.net is refused outright. This mattered because the id is inside the
canonicalised content the hash and signature cover, so the mistake became
permanent on signing, and because two organisations sharing a project name minted
colliding identifiers.

**Criteria set identifiers split by what they name** (2026-08-04). A recognised
published standard keeps a project-controlled identifier under
`https://uofa.net/criteria/`, because it means the same document for everyone.
An unrecognised rubric is minted in the author's namespace, because the project
cannot vouch for a criteria set it has never seen. Aliases fold, so
`ASME-VV40-2018`, `asme-vv40-2018` and `ASME V&V 40` are one identifier rather
than three.

This bears directly on two Tier 1 terms. `criteriaSet` should be defined as the
rubric an assessment was graded against, not as "the standard", since an author's
own rubric is equally valid there. `AcceptanceCriteria` is the class, and its
definition should not imply the criteria are always published or external.

**All 53 Tier 3 terms get definitions** (2026-08-04). Nothing is deprecated and
nothing is removed. Where a term is deliberately not in use, the definition says
so rather than implying the term is expected in packages. Group 3a is the worked
case: those three are staged for W-AR-06/W-AR-07 and the calibration probes
depend on their absence.

**Core is standard-agnostic** (2026-08-04). No core definition cites a standard,
clause or table. See the rule in §3, which carries the reasoning and the
evidence. The pack namespaces keep their clause citations.

A consequence worth watching during review: if a proposed core definition cannot
be written without naming a standard, that is evidence the term belongs in a
pack namespace instead. Raise it rather than narrowing the definition to fit.
