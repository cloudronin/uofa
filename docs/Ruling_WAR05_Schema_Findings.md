# Ruling and filing: W-AR-05 scope, two schema findings

Date: 2026-08-20
From: author
Execute after the protocol restructure lands. Small session; nothing here blocks the review packets.

## Ruling: W-AR-05 is mis-scoped, D-03/04/05 are Not Applicable

The rule's precondition (a validation comparison should name its comparator) is not meaningful for evidence nodes that are not comparisons. A ReviewActivity and a ProcessAttestation have no comparator by nature; the firings arose because the Excel mapper routes all five evidence types through `hasValidationResult`, so the rule tests node classes it was never about. The three Johnson candidates D-03, D-04, D-05 are Not Applicable on that basis. Update DISPOSITIONS_DRAFT.md: verdict NA on those three rows, rationale one line each ("pattern precondition not meaningful for this node class; see SF-1"), still marked DRAFT pending my review pass, where I will confirm rather than re-derive.

The rule itself is not wrong and is not changed now. The catalog is frozen post-R1a; the fix rides the schema increment below.

## File two schema findings in the post-defense increment list

Add both to the schema-findings channel alongside Input pedigree (A-07) and Level 0 (A-08), same format, each citing the pilot artifacts.

**SF-1, evidence typing: non-comparison evidence needs its own predicate.** The ontology already types the node classes; the graph loses the distinction because the mapper funnels every evidence type through `hasValidationResult`. Proposed shape, recorded as a proposal not a design: a predicate for non-comparison evidence (hasReviewEvidence, or a general hasSupportingEvidence), mapper routes by evidence type, W-AR-05 then scopes itself by walking only the validation predicate, no type guard required. Note the INV-21 lesson explicitly: if any type guard is ever considered instead, the class it guards on must be declared in the ontology first. Evidence: five Johnson firings, three surviving as D-03/04/05; controlled experiment in the W3 session log.

**SF-2, comparator identity: real comparators are not always URI-shaped.** `comparedAgainst` is @type:@id, so "SME judgment" and "test data as referent, no RWS data available" are silently dropped at import as malformed subjects, and W-AR-05 then fires on an absence import itself created. The source stated a comparator; the package cannot carry it. Proposed shape, again a proposal: a comparator-description node or a small controlled vocabulary of referent classes (expert judgment, test data as referent, published benchmark, predicate reference to a cited artifact). Note that Morrison and Nagaraja never surfaced this because their comparators were bench data with citable identities; Johnson surfaces it because judgment-borne referents are normal in this document class. Evidence: the relative-IRI expansion experiment and the dropped-comparator finding in the W3 session log.

Both findings carry the boundary-section tag: judgment-borne and prose-borne evidence is where the schema stops. SF-1 and SF-2 are the third and fourth instances of the existing finding class, not a new class.

## One sentence for the session report

Record that this is the first catalog defect found by the encoding-protocol pipeline rather than by the adversarial machinery; the method-finds-defects claim now has a second independent route. The chapter picks this up later; the session just needs the sentence in the record with the artifact refs.

## Out of scope

No rule edits, no mapper edits, no ontology edits, no catalog version change. My review pass on Johnson proceeds independently; the NA verdicts above become final there, in my commits.
