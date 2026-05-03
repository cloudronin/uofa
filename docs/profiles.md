# Profiles

UofA uses a two-tier profile system. **Minimal** captures the bare evidence package. **Complete** adds the full credibility assessment.

## Minimal Profile

The minimum viable UofA. Suitable for evidence capture during live pipeline execution or as a lightweight audit artifact.

| Property | Type | Purpose |
|---|---|---|
| `bindsRequirement` | IRI | The requirement this UofA substantiates |
| `hasContextOfUse` | IRI | The V&V 40 Context of Use for this assessment |
| `hasValidationResult` | IRI | At least one validation result |
| `hasDecisionRecord` | IRI | The credibility decision (accepted/rejected + rationale) |
| `generatedAtTime` | xsd:dateTime | When this UofA was created |
| `hash` | string | Content hash (format-validated: `sha256:<64 hex chars>`) |
| `signature` | string | Digital signature (format-validated: `ed25519:<hex>`) |

## Complete Profile

Extends Minimal with full V&V 40 credibility assessment, provenance chain, and quality metrics. Required for regulatory submissions and formal credibility arguments.

Everything in Minimal, plus:

| Property | Type | Purpose |
|---|---|---|
| `bindsModel` | IRI | The computational model assessed |
| `bindsDataset` | IRI | The dataset(s) used in validation |
| `wasDerivedFrom` | IRI | Provenance link to parent artifact |
| `wasAttributedTo` | IRI | Responsible actor or organization |
| `hasCredibilityFactor` | CredibilityFactor[] | Per-factor assessment (V&V 40 Table 5-1) |
| `hasWeakener` | WeakenerAnnotation[] | *(optional)* Detected quality gaps |
| `credibilityIndex` | xsd:decimal [0–1] | Overall credibility score |
| `traceCompleteness` | xsd:decimal [0–1] | Provenance chain completeness |
| `verificationCoverage` | xsd:decimal [0–1] | Verification evidence coverage |
| `validationCoverage` | xsd:decimal [0–1] | Validation evidence coverage |
| `uncertaintyCIWidth` | xsd:decimal [≥0] | Uncertainty confidence interval width |
| `assuranceLevel` | string | `Low` / `Medium` / `High` |
| `criteriaSet` | IRI | Reference criteria set (e.g., `ASME-VV40-2018`) |

## CredibilityFactor

Each factor maps to one row in V&V 40 Table 5-1 or NASA-STD-7009B:

| Property | Constraint | Purpose |
|---|---|---|
| `factorType` | Factor name from the active pack's taxonomy | Which credibility factor is being assessed |
| `factorStandard` | String (e.g., `"ASME-VV40-2018"`, `"NASA-STD-7009B"`) | Which standard defines this factor |
| `assessmentPhase` | `"capability"` or `"results"` *(NASA-STD-7009B only)* | NASA CAS assessment phase |
| `requiredLevel` | Integer (1–5 for V&V 40, 0–4 for NASA-7009B) | Target credibility level for this COU |
| `achievedLevel` | Integer (1–5 for V&V 40, 0–4 for NASA-7009B) | Actual credibility level achieved |
| `hasEvidence` | IRI or IRI[] *(optional)* | Links to backing evidence entities |

## WeakenerAnnotation

Quality gap annotations detected by the Jena rule engine (C3). Optional — a UofA with zero weakeners is valid (and desirable).

| Property | Constraint | Purpose |
|---|---|---|
| `patternId` | Format: `W-XX-NN` or `COMPOUND-NN` | Catalog ID from the weakener pattern taxonomy |
| `severity` | `Critical` / `High` / `Medium` / `Low` | Impact severity |
| `affectedNode` | IRI | The specific graph node flagged by this pattern |
| `description` | string *(optional)* | Human-readable explanation of why this weakener fires |
