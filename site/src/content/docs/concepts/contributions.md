---
title: C1 / C2 / C3
description: The three contributions of UofA — integrity, completeness, and quality gates.
---

UofA addresses the credibility-evidence packaging problem through three contributions. Each maps to a CLI subcommand and a layer of validation.

| Contribution | What it does | Mechanism | Subcommand |
|---|---|---|---|
| **C1 — Integrity** | Captures the credibility decision as a portable, tool-independent object with provenance lineage and integrity guarantees | JSON-LD + PROV-DM + SHA-256 + ed25519 | `uofa verify` |
| **C2 — Completeness** | Defines what a UofA must contain at each rigor level and enforces it as a computable constraint | SHACL profiles (Minimal / Complete) | `uofa shacl` |
| **C3 — Quality gates** | Detects substantive credibility gaps including compound risks no individual query can find | Apache Jena forward-chaining rule engine | `uofa rules` |

`uofa check` runs all three in sequence.

## C1 — Decisions as artifacts

<a id="c1"></a>

The credibility decision is encoded as a JSON-LD document with PROV-DM provenance. The document is hashed with SHA-256 and signed with ed25519. The hash and signature are stored as fields on the document itself, making the package self-contained and verifiable without external infrastructure.

What this gives you:

- **Tamper evidence.** Any change to the document — content, provenance, decision — invalidates the signature. This holds today, against any v0.7.1 UofA.
- **A package format designed for tool independence.** The single-JSON-LD form is intended to travel across organizations, simulation tools, and submission systems. Tool-side ingestion is the active integration target; see [Feedback](/feedback/) for current outreach to PLM, SPDM, and submission-system stakeholders.
- **Portable provenance.** Source documents, models, datasets, and prior UofAs are referenced by IRI. The provenance graph is portable; whether downstream tools consume it depends on those tools.
- **Reproducibility of integrity.** Anyone with the public key can verify the signature with `uofa verify`. Trust-anchoring (how a verifier obtains and trusts the public key) is addressed under "What C1 does not yet give you" below.

**What C1 does not yet give you.** ed25519 verifies that a UofA was signed by a specific key. It does not address how the verifier comes to trust that key. Trust-anchoring (PKI, did:web, organizational issuer registries) is external to C1 by design. UofA establishes the data-structural prerequisite for verifiable integrity. The trust-anchoring layer is the responsibility of the deploying organization, in the same way that a signed PDF is verifiable only against a trusted certificate authority. Post-defense work includes a reference integration with at least one trust-anchor mechanism.

C1 establishes the per-decision signed evidence object as the unit of credibility exchange. The decision, its provenance, and its evidence linkages are bound together in a single artifact and verifiable mechanically. Existing structured frameworks (CLARISSA, RACK, GSN/SACM, MoSSEC, SSP-LS-Traceability) provide structured argumentation, trace data, or lifecycle linkage; UofA's contribution is the per-decision signed package as the granular, portable, machine-verifiable evidence unit that flows through and across them.

## C2 — Computable completeness

<a id="c2"></a>

A UofA is structurally constrained by SHACL shapes that define two profiles:

| Profile | Required fields | Use case |
|---|---|---|
| `ProfileMinimal` | 7 | Lightweight audit trail, live pipeline capture |
| `ProfileComplete` | 17 | Regulatory submissions, formal V&V 40 assessments |

Domain packs add their own shapes additively. The `vv40` pack constrains `factorType` to the 13 V&V 40 categories. The `nasa-7009b` pack constrains levels to 0–4 and adds `assessmentPhase`.

What this gives you:

- **Machine-checkable submissions.** Reviewers can run `uofa shacl FILE` and get a deterministic answer.
- **Plain-English error messages.** SHACL violations are translated to actionable messages with sheet name and cell reference (for Excel imports) or field name (for direct JSON-LD).
- **Two-profile structural completeness.** Minimal (7 fields) supports lightweight live-pipeline capture; Complete (17 fields) supports formal regulatory submissions. These two levels measure structural completeness of the evidence package. They are orthogonal to credibility-level scales such as NASA-STD-7009B's Credibility Assessment Scale (CAS levels 0–4) and ASME V&V 40's risk-informed credibility framework, which measure how much credibility evidence is needed. The COU's `modelRiskLevel` carries the credibility-level signal independently.

The "thin schema" framing applies only to the structural-completeness layer. UofA does not attempt to redefine credibility-level scales; it provides a portable evidence-package shape into which any standards-defined credibility level fits.

## C3 — Quality gates

<a id="c3"></a>

The Apache Jena forward-chaining rule engine detects substantive credibility gaps that SHACL cannot express. The current core pack has 23 patterns: 21 Level-1 patterns plus 2 active compound patterns (`COMPOUND-01` and `COMPOUND-03`). Domain packs extend this catalog additively — the `nasa-7009b` pack contributes 6 NASA-STD-7009B-specific patterns (`W-NASA-01` … `W-NASA-06`), bringing the total to 29 when both packs are loaded. See the [Weakener catalog](/reference/catalog/) for the full enumeration.

The compound patterns are the differentiator. A compound rule fires on the *output* of Level-1 rules. This is chained inference that standalone SPARQL queries cannot produce.

| Category | Patterns | Detects |
|---|---|---|
| Epistemic (W-EP-*) | 4 | Orphan claims, broken provenance, evidence-source gaps |
| Aleatory (W-AL-*) | 2 | Missing UQ, missing sensitivity analysis |
| Ontological (W-ON-*) | 2 | Applicability, operating-envelope gaps |
| Argumentation (W-AR-*) | 5 | Comparator absence, residual-risk gaps |
| Structural (W-SI-*) | 2 | Internal consistency gaps |
| Consistency (W-CON-*) | 5 | Decision-vs-factor mismatches |
| Provenance (W-PROV-*) | 1 | Provenance-chain orphans |
| Compound | 2 | Risk escalation, assurance-level override |

See [Weakeners](/concepts/weakeners/) for the full taxonomy and the worked Morrison example.

What this gives you:

- **A pattern catalog designed to direct reviewer attention.** The 29-pattern catalog (core + nasa-7009b) encodes credibility gaps that are otherwise hunted for in prose. Reviewer-side adoption is the next validation milestone — Phase 3 of the praxis runs the catalog against expert-adjudicated cases to calibrate severity assignments.
- **Risk-driven divergence (validated today).** Same model, same data, different model risk produces measurably different weakener profiles. The Morrison COU 1 vs COU 2 diff is the worked demonstration; reproduce with `uofa diff`. See [/demo/](/demo/).
- **Compound inference.** Coexisting Critical and High weakeners on the same UofA trigger `COMPOUND-01`. A declared assurance level inconsistent with detected gaps triggers `COMPOUND-03`. These are the kinds of patterns no individual SPARQL query can express.

Zero weakeners does not mean the model passed. Zero weakeners means the *evidence package* is structurally complete and auditable, even when the evidence indicates the model fails. The core value proposition is evidence packaging quality, not evidence sufficiency.
