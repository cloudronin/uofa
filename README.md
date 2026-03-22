# Unit of Assurance (UofA) — v0.2-draft

The **Unit of Assurance** is the smallest independently verifiable bundle of credibility evidence for computational modeling and simulation (CM&S). It packages the **credibility decision** — who judged what, against what criteria, using what evidence, with what result — as a signed, provenance-linked, machine-verifiable engineering artifact.

UofA exists because the credibility frameworks are not the problem. ASME V&V 40, NASA-STD-7009B, and the FDA's 2023 guidance on CM&S credibility provide clear instructions for *how to assess* simulation credibility. The problem is the **last mile**: there is no standardized construct for packaging, transmitting, and verifying the *evidence and decisions* those assessments produce.

The result is predictable. Credibility decisions live in prose PDFs. Evidence is scattered across tools. Provenance is partial. Audit packaging is manual. And reviewers catch quality gaps by intuition rather than automation.

UofA addresses this through three contributions:

| Contribution | What it does | Mechanism |
|---|---|---|
| **C1 — Decision as artifact** | Captures the credibility decision as a portable, tool-independent object with provenance lineage and integrity guarantees | JSON-LD + PROV-DM + digital signatures |
| **C2 — Completeness enforcement** | Defines what a UofA must contain at each rigor level and enforces it as a computable constraint | SHACL profiles (Minimal / Complete) |
| **C3 — Quality gates** | Detects substantive credibility gaps — missing UQ, stale inputs, orphan claims — that structural completeness alone cannot catch | Named SPARQL weakener patterns mapped to V&V 40 credibility factors |

---

## Standards Alignment

UofA is grounded in existing standards rather than inventing new ones:

- **ASME V&V 40-2018** — Credibility factors, model risk framework, and the Context of Use (COU) concept that drives per-factor assessment
- **FDA 2023 Final Guidance on CM&S Credibility** — Regulatory expectations for credibility evidence in medical device submissions
- **NASA-STD-7009B** — CMS credibility assessment standard for models and simulations
- **W3C PROV-DM / PROV-O** — Provenance data model for artifact lineage (`wasDerivedFrom`, `wasAttributedTo`, `generatedAtTime`)
- **W3C SHACL** — Shapes Constraint Language for RDF graph validation
- **JSON-LD 1.1** — Linked data serialization that stays human-readable

---

## Profiles

UofA uses a two-tier profile system. **Minimal** captures the bare evidence package. **Complete** adds the full credibility assessment.

### Minimal Profile

The minimum viable UofA. Suitable for evidence capture during live pipeline execution or as a lightweight audit artifact.

| Property | Type | Purpose |
|---|---|---|
| `bindsRequirement` | IRI | The requirement this UofA substantiates |
| `hasContextOfUse` | IRI | The V&V 40 Context of Use for this assessment |
| `hasValidationResult` | IRI | At least one validation result |
| `hasDecisionRecord` | IRI | The credibility decision (accepted/rejected + rationale) |
| `generatedAtTime` | xsd:dateTime | When this UofA was created |
| `hash` | string | Content hash for integrity verification |
| `signature` | string | Digital signature (placeholder OK in synthetic runs) |

### Complete Profile

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

### CredibilityFactor

Each factor maps to one row in V&V 40 Table 5-1:

| Property | Constraint | Purpose |
|---|---|---|
| `factorType` | One of 13 V&V 40 factor names | Which credibility factor is being assessed |
| `requiredLevel` | Integer 1–5 | Target credibility level for this COU |
| `achievedLevel` | Integer 1–5 | Actual credibility level achieved |

The 13 allowed factor names correspond to V&V 40 Table 5-1: Software quality assurance, Numerical code verification, Discretization error, Numerical solver error, Use error, Model form, Model inputs, Test samples, Test conditions, Equivalency of input parameters, Output comparison, Relevance of the quantities of interest, and Relevance of the validation activities to the COU.

### WeakenerAnnotation

Quality gap annotations detected by SPARQL patterns (C3). Optional — a UofA with zero weakeners is valid.

| Property | Constraint | Purpose |
|---|---|---|
| `patternId` | Format: `W-XX-NN` (e.g., `W-EP-01`) | Catalog ID from the weakener pattern taxonomy |
| `severity` | `Critical` / `High` / `Medium` / `Low` | Impact severity |
| `affectedNode` | IRI | The specific graph node flagged by this pattern |

The weakener pattern catalog contains 14 named patterns across 5 categories (Epistemic, Aleatory, Ontological, Argument, Structural Integrity), derived from Khakzad Shahandashti et al. (2024) and mapped to V&V 40 credibility factors.

---

## Repository Structure

```
spec/
  context/
    v0.2-draft.jsonld          # JSON-LD @context (term definitions)
  schemas/
    uofa_shacl.ttl             # SHACL shapes (Minimal + Complete + dispatcher)

examples/
  mock-medical-minimal.jsonld  # Minimal profile — medical device
  mock-aero-complete.jsonld    # Complete profile — wind turbine simulation
  mock-self-contained-complete.jsonld  # Complete profile with weakener annotation
  medical.json                 # Minimal profile — heart rate monitor
  auto.json                    # Minimal profile — ABS yaw stability
  aero.json                    # Minimal profile — flight control lateral axis
  deprecated/
    medical.json               # Pre-v0.2 flat schema (kept for reference)
```

---

## Validation

UofA uses [pySHACL](https://github.com/RDFLib/pySHACL) for validation. The SHACL shapes file enforces both Minimal and Complete profiles through a dispatcher pattern — declare `conformsToProfile` and the correct constraint set activates automatically.

### Quick start

```bash
pip install pyshacl

# Validate a Minimal-profile example
pyshacl -s spec/schemas/uofa_shacl.ttl examples/mock-medical-minimal.jsonld

# Validate a Complete-profile example
pyshacl -s spec/schemas/uofa_shacl.ttl examples/mock-aero-complete.jsonld
```

A passing result means the UofA satisfies all structural constraints for its declared profile. SHACL handles C2 (completeness enforcement). C3 (quality gates) operates separately via SPARQL queries against the RDF graph.

---

## Context of Use and COU Divergence

The `hasContextOfUse` property is required at both Minimal and Complete profiles. This is a deliberate design choice: V&V 40 defines the Context of Use as the foundation of credibility assessment. Without a COU, there is no basis for judging what "adequate" means.

A key property of the UofA architecture is that the **same model and data can produce different credibility decisions** across different COUs. The Morrison et al. (2019) blood pump case study demonstrates this: COU1 (CPB predicate comparison) and COU2 (VAD acceptance) assess the same CFD model but require different credibility levels. The weakener pattern W-AL-01 (Missing UQ) fires for COU1 but not COU2, because COU2's lower model risk does not require the same UQ rigor.

This is C1's core value proposition: the credibility *decision* — not just the evidence — is captured as a first-class artifact, making COU-specific divergence visible and auditable.

---

## Design Principles

| Principle | Meaning |
|---|---|
| **Minimal** | Small JSON-LD document, human-readable, one file per claim |
| **Semantic** | Aligns with PROV-O, V&V 40, and domain ontologies |
| **Verifiable** | Digital signatures + content hashing + SHACL validation |
| **Composable** | UofAs form nodes in system-level assurance graphs |
| **Tool-agnostic** | Works with any simulation tool, MBSE platform, or ML pipeline |

---

## How UofAs Are Used

**One UofA per credibility claim.** A V&V 40 assessment with 8 credibility factors across 2 COUs produces ~16 UofAs. A system with 120 safety requirements produces ~120 Minimal UofAs during evidence capture, upgraded to Complete when the full credibility assessment is performed.

**Continuous assurance in CI/CD.** When a model changes, affected UofAs are flagged as suspect via weakener patterns (W-AR-04: Model Version Drift, W-EP-03: Stale Input). Only the affected UofAs need re-issuance — unaffected ones carry forward with their existing credibility levels.

**Evidence portability.** A UofA is a self-contained, signed evidence parcel. Send it to a regulator, an OEM, or an auditor — the provenance, integrity, and completeness are built in.

---

## Research Context

UofA is the subject of a Doctor of Engineering praxis at George Washington University. The primary evaluation uses two FDA case studies:

- **Tier 1 (Retrospective):** Morrison et al. (2019) — FDA generic centrifugal blood pump V&V 40 credibility assessment. Re-expressed as UofA evidence packages to measure the delta in completeness, provenance richness, and SHACL conformance.
- **Tier 2 (Prospective):** FDA VICTRE pipeline — live computational workflow instrumented to generate UofAs during execution rather than from retrospective documents.
- **Tier 3 (Exploratory):** Multi-component stress test on VICTRE — simulates change events to test continuous re-issuance and criticality-tiered economics as feasibility demonstrations.

Early Findings are planned to be presented at **NAFEMS Americas 2026** (May 27–29).

---

## License

CC0 1.0 — public domain, no restrictions.

---

## Contributing

Contributions are welcome, especially real-world UofA examples from practitioners working with CM&S credibility assessment. If you are preparing a CM&S-supported regulatory submission and want to explore UofA packaging for your evidence, please reach out.
