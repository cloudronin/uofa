# Vocabulary cleanup audit, v0.7

What was removed, what was kept, and how each decision was checked.

The question that started it: the repository has no external users yet, so a
term nothing references is as good as abandoned and could be dropped. That
turned out to be true for core and false for the packs, for a reason worth
recording.

## Method

A term is removable only if nothing outside its own declaration refers to it.
"Nothing" was checked by reading every `.ttl`, `.jsonld`, `.json`, `.py`,
`.mjs`, `.md`, `.rules` and `.sparql` file in the repository and matching four
reference forms: the prefixed name (`uofa:x`), the rdflib namespace form
(`UOFA.x`), the JSON key (`"x":`), and the full IRI (`vocab#x`).

Two things had to be excluded from counting as a use:

- a term's own `rdfs:label`/`rdfs:comment` block in the shapes file, and
- `spec/schemas/uofa_shacl.ttl`, which is a symlink to
  `packs/core/shapes/uofa_shacl.ttl` and so is the same declaration twice.

**Two earlier passes of this audit were wrong, both by under-scanning.** A
bare-word regex matched `environment` and `addresses` in unrelated Python. A
`packs/*/rules/*` glob missed `packs/*/rules/oos/`, and nothing globbed
`specs/calibration/`. Both errors pointed the same way -- toward deleting
things that were in use -- so the scan is deliberately recursive over the whole
tree now rather than over a list of directories.

## Removed: 19 core terms, in `spec/context/v0.7.jsonld`

v0.7 is v0.6 minus 19 terms. It is a new file; **v0.5 and v0.6 are untouched**,
so the 11 shipped packages stay valid and none needed re-signing.

Fourteen legacy terms, present since v0.1 to v0.4 and never used:

```
addresses            analyzesConfiguration   attestedAt        deploymentContext
deploymentDate       environment             exercised         hasJustification
hasParameter         reviewDate              reviewFindings    reviewScope
transformationDescription                    validForModelVersion
```

Plus the five v0.6 reasoning relations already marked `owl:deprecated`:
`agreementMakesNonDispositive`, `factorConstraintWarrants`, `frameworkTransfers`,
`sustainedDefeaterJustified`, `thresholdDistanceModulates`.

Each of the 19 has: no SHACL shape, no JSON Schema entry, no rule, no example,
no calibration package, no authored definition. They existed only as context
entries.

Checked: all 11 shipped packages re-expanded under v0.7 produce a **graph
isomorphic to the one they produce under v0.5** -- zero triples differ.

`hasDiscrepancy` was a candidate and was kept: `uofa:Discrepancy` has a node
shape in the disposition pack, and this is the only property that attaches one.

## Kept: all 55 pack terms

The first pass reported 49 iso42001 and 6 surrogate terms as inert. **That was
wrong. Every one of the 55 is referenced**, and removing any would have broken
something:

| Referenced by | Terms |
|---|---|
| `packs/*/rules/oos/oos_v0.1.rules` — out-of-scope detection | `AuditorIndependenceAttestation`, `AuditScopeNonOverlapAttestation`, `ConsultationOutcomeIntegrationRecord`, `IndependentVerificationRecord`, `MethodologyValidationRecord`, `PolicyToPurposeReviewRecord`, `RiskFrameworkComparisonRecord`, `RootCauseExpertReviewRecord`, `StakeholderValidationRecord`, `SupplierEvidenceAdequacyReviewRecord`, and the five surrogate classes |
| `specs/calibration/packages/cal-*.jsonld` — OOS calibration fixtures | `ConsultationLog`, `ImpactAssessmentScopeJustification`, `MeasurementMethodologyDocument`, `OrganizationalPurposeStatement`, `RiskIdentificationMethodology`, `RootCauseAnalysisRecord`, `StakeholderConsultationAdequacyClaim`, `SupplierAssuranceEvidenceAdequacyClaim`, `controlObjective`, `CalibrationClaim`, `CalibrationEvidence`, `ComparativePerformanceClaim` |
| The adversarial corpora (`aims.json`, `surrogate.json`) | all 55 |
| `sip_evidence_bundle_schema.json` | `parentSignatureTimestamp` |
| Weakener test fixtures | `RiskAcceptanceRationale`, `riskCategory` |

So "not used by the two shipped example packages" measured the wrong thing. The
iso42001 pack's vocabulary is exercised by the **out-of-scope detection
machinery**, not by the demo packages -- the calibration corpus is what proves
a weakener fires when evidence is absent, and it needs the vocabulary for the
evidence that is absent.

Independently, 18 of the aims classes cite a specific ISO 42001 clause in their
own definition (`CorrectiveActionRecord` 10.2, `RiskTreatmentPlan` 6.1.3,
`InternalAuditPlan` 9.2, `OpportunityRegister` 6.1.2, `AIMSObjective` 6.2, and
Annex A entries A.6.2, A.7.6, A.8.4, A.9.2, A.9.3, A.10.2, A.10.3). Removing
those narrows what the pack claims to implement, separately from breaking the
rules.

Seven subclass a core or pack class, including `CalibrationEvidence` and
`ModelComparisonRecord` (`uofa:ValidationResult`) and `CalibrationClaim`,
`ComparativePerformanceClaim`, `StakeholderConsultationAdequacyClaim`,
`SupplierAssuranceEvidenceAdequacyClaim` (`uofa:AssuranceClaim` /
`uofa-aims:AIMSClaim`).

## What the site does with a dropped term

Nothing is hidden. A term the newest context no longer carries is still listed,
marked *not in the current context*, with its range shown as `v0.4` to `v0.6`.
Its IRI still resolves, because packages pinned to an older context still use
it and this project spent real effort making those IRIs not 404.

The marking is derived by comparing context files, so no hand-maintained list
can go stale. `site/scripts/lib/vocab-extract.mjs` compares each term's last
appearance against the newest version.

## Not done

**The toolchain still emits v0.5.** `CONTEXT_URL` in `excel_constants.py`,
the scaffolding in `commands/init.py`, and four tests pin it. Pointing new
packages at v0.7 is the step that makes the cleanup take effect for anything
newly authored; it is a behaviour change to what the importer produces and was
left as a separate decision.
