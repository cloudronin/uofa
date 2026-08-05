# The UofA vocabulary: what it says, and what it does not

Status of `uofa.net/vocab#` and the two pack namespaces after the definition and
cleanup work of 4-5 August 2026, and an honest account of what is still missing.

Companion documents:
[vocabulary-authoring-spec.md](vocabulary-authoring-spec.md) is the rulebook for
writing definitions; [vocabulary-cleanup-audit.md](vocabulary-cleanup-audit.md)
records what v0.7 removed and why nothing was removed from the packs.

## Where it started

The vocabulary existed as identifiers and nothing else. `uofa.net/vocab#` had
**2 authored definitions across 136 terms**. A reader who followed a term IRI
out of a package got a page that could tell them the JSON key and the SHACL
constraints, and could not tell them what the term meant.

The packs were better documented but incomplete, and no namespace said which
class a property belonged to.

## Where it is now

| | core | iso42001 (aims) | surrogate |
|---|---|---|---|
| Terms | 136 | 127 | 39 |
| With a label | **122** | 127 | 39 |
| With a description | **122** | 76 | 25 |
| Declaring `rdfs:domain` | **65** | 8 | 2 |
| Deprecated | 5 | 0 | 0 |
| Dropped in the current context | 19 | 0 | 0 |
| Used by a shipped package | 64 | 63 | 25 |

Core went from 2 definitions to 122. The 14 that remain undefined are covered
below, and are the reason this document exists rather than a "done" note.

## What was done

**Definitions, in four batches.** 120 core terms defined against evidence in the
repository - the SHACL shapes, the JSON Schema, and how the shipped packages
actually use each term - rather than from the term's name. Two rules emerged and
are now in the authoring spec:

- *Core is standard-agnostic.* No core definition cites ASME V&V 40,
  NASA-STD-7009B or ISO 42001. `uofa:factorType` and `uofa:factorStandard` are
  each constrained by four different packs, so naming one standard makes the
  definition false for the others.
- *Labels follow the corpus:* classes Title Case, properties lowercase. This was
  checked against all 166 existing labels, which are unanimous. An earlier draft
  of the spec asserted Title Case for everything; that was wrong.

**Domains and ranges.** 65 `rdfs:domain` and 29 `rdfs:range` declarations on
core, where before there were none. Every declared domain was verified against
the shipped packages: **no declared domain is contradicted by any node that
carries the property.**

25 properties deliberately have no domain, because `rdfs:domain` entails
"anything carrying this *is* an X" rather than "may only appear on an X".
Declaring one on `rationale` would make every `CredibilityFactor` carrying a
rationale into a `DecisionRecord`. Those terms name their carrying classes in
prose instead.

Computing this correctly turned out to be subtler than expected: nodes hold
several `@type` values at once - four packages are typed
`["UnitOfAssurance", "CredibilityEvidencePackage"]` - so the candidate domain is
the **intersection** of the carriers' type sets. Taking the union reported 21
conflicts where there are 7.

**Deprecation.** The five v0.6 reasoning relations
(`agreementMakesNonDispositive`, `factorConstraintWarrants`,
`frameworkTransfers`, `sustainedDefeaterJustified`,
`thresholdDistanceModulates`) carry `owl:deprecated true`. Their comments state
the checkable fact - declared in v0.6, used by no package or shape - and not
whether they were abandoned, which is a claim about intent the repository cannot
evidence.

**A validation-result taxonomy question, half answered.**
`uofa:hasValidationResult` attached two iso42001 classes that had never said
what they were. `ModelEvaluationReport` requires an evaluated model version and
a documented test set, so it does record model output against held-out truth: it
now declares `rdfs:subClassOf uofa:ValidationResult`, matching what the
surrogate pack does for its three equivalents. `AuditResultsRecord` requires an
audited function, a date and findings - it examines the management system, not
the model - and is deliberately not a ValidationResult.

## The v0.7 cleanup release

`spec/context/v0.7.jsonld` is v0.6 minus 19 terms nothing referenced: the 14
undefined legacy terms plus the 5 deprecated relations.

| Context | Terms |
|---|---|
| v0.1 | 56 |
| v0.2 | 69 |
| v0.3 | 97 |
| v0.4 | 120 |
| v0.5 | 138 |
| v0.6 | 156 |
| **v0.7** | **137** |

The first release to shrink. It is a **new file**: v0.5 and v0.6 are untouched,
so the 11 shipped packages stay valid and none needed re-signing. Verified by
re-expanding every shipped package under v0.7 and confirming the resulting RDF
graph is **isomorphic** to its v0.5 expansion - zero triples differ.

Dropped terms are not hidden. The vocabulary page still lists them, marked *not
in the current context* with their range shown (`v0.4` to `v0.6`), and their
IRIs still resolve, because packages pinned to an older context still carry
them. The marking is derived by comparing context files, so no hand-maintained
list can go stale.

**Nothing was removed from the packs.** An audit of 55 candidate pack terms
found all 55 in use - by the out-of-scope detection rules and the calibration
corpus, not by the two demo packages. See the cleanup audit for the per-term
evidence and for the two scanning mistakes that first suggested otherwise.

## Bugs found on the way

Each of these was pre-existing and found because the vocabulary work forced a
look at something:

- **`rdfs:range uofa:Person`** in the iso42001 shapes, but `"Person"` has mapped
  to `schema:Person` in every context since v0.1. A wrong-prefix typo minting a
  term that never existed.
- **Seven dead links** on the aims and surrogate vocabulary pages: the renderer
  linked `rdfs:subClassOf` to a same-page anchor, but the packs subclass core's
  `ValidationResult`, `AssuranceClaim`, `ProcessAttestation` and `Model`.
- **`PROFILE_URIS` could silently mislabel a package.** It was hardcoded in the
  generator while the sibling `VALID_PROFILES` was derived from `sh:in`. Once
  v0.6 added a third profile, regenerating would have widened one and not the
  other, and `excel_mapper`'s `.get(profile, ...Minimal)` fallback would have
  emitted a Disposition package as Minimal with no error.
- **`excel_constants.py` is a hybrid** whose own docstring told you to
  regenerate it wholesale - which deletes six hand-maintained constants.
- **Context versions sorted lexicographically**, so v0.10 would have sorted
  before v0.2 and silently backdated every term's `since`.
- **A SHACL property block was truncated at `[a-f0-9]`** inside a regex
  character class, which had been silently swallowing constraints. Terms with
  visible constraints went from 66 to 103 once fixed.

## What is still missing

**14 core terms have no definition, and the repository cannot supply one.**
They have no shape, no JSON Schema entry, no rule, no example and no calibration
package - they existed only as context entries, which is why v0.7 drops them:

| Added in | Terms |
|---|---|
| v0.1 | `environment` |
| v0.3 | `addresses`, `analyzesConfiguration`, `exercised`, `hasJustification`, `hasParameter`, `validForModelVersion` |
| v0.4 | `attestedAt`, `deploymentContext`, `deploymentDate`, `reviewDate`, `reviewFindings`, `reviewScope`, `transformationDescription` |

Plausible definitions could be written from the names. They would be guesses,
and the authoring spec forbids that. The seven v0.4 terms look like one coherent
feature - a review / deployment / attestation cluster added together - so
describing that one feature would likely resolve half of them.

**`rdfs:range uofa:ValidationResult` is still undeclared.** Every other
resolvable range was declared. This one is blocked because iso42001
`hybrid/cou1` is a governance-only context of use with no model evaluation, and
`ProfileMinimal` requires `hasValidationResult` `minCount 1` - so it points the
property at the audit record it already carries under `hasEvidence`. That is a
shape-fit question (may a pure AIMS package have nothing to validate?), not a
typo. `tests/test_validation_result_taxonomy.py` holds it as the single listed
exception and fails once resolved, so the range gets declared rather than
forgotten.

**The toolchain still emits v0.5.** `CONTEXT_URL` in `excel_constants.py`, the
scaffolding in `commands/init.py`, and four tests pin it. Until that changes,
v0.7 is published but changes nothing about what newly authored packages carry.

**The v0.6 disposition line is adopted by nothing.** Zero packages declare
`ProfileDisposition`, zero load v0.6, and `packs/disposition/` has no tests. Its
machinery works - the dispatcher branch and node shapes are real, and the JSON
Schema was deliberately left at v0.5 - but it has never been exercised. It
deserves an explicit decision: finish it, or mark it as the five relations were.

**iso42001 and surrogate descriptions lag their labels.** Every term in both
packs is labelled, but only 76 of 127 aims terms and 25 of 39 surrogate terms
carry a description. Neither pack has been through the batch treatment core got.

## Verification

The state above is what ships at `7a9fe815`:

```bash
pytest tests/ -q                      # 2349 passed, 14 skipped
cd site && npm run sync:vocab && npm test   # 30 passed
```

Four tests were added specifically to keep these findings from regressing:
`test_validation_result_taxonomy.py`, `test_excel_constants_derived.py`, the
profile-subset guard in `test_c2_c3_patternid_consistency.py`, and the
render-level dead-anchor check in `site/scripts/lib/vocab-extract.test.mjs`.

Every RDFS triple added here is **inert to validation**: all three
`pyshacl.validate` call sites pass no `ont_graph` and no inference, and the Jena
weakener engine never loads the shapes. Declaring a domain cannot change what
validates or what fires.
