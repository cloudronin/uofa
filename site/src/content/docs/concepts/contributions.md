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

- **Tamper evidence.** Any change to the document — content, provenance, decision — invalidates the signature.
- **Tool independence.** The package travels as a single JSON-LD file across organizations, simulation tools, and submission systems.
- **Portable provenance.** Source documents, models, datasets, and prior UofAs are referenced by IRI. The provenance chain crosses tool boundaries.
- **Reproducibility.** Anyone with the public key can verify integrity. No vendor lock-in. No infrastructure dependency.

The C1 contribution is what differentiates UofA from a Word document containing the same information. A signed Word document attests to the document. A signed UofA attests to the decision *and* its provenance chain *and* its evidence linkages — all checkable mechanically.

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
- **Risk-proportional rigor.** The two-profile system aligns with how NASA-STD-7009 and the in-development ASME VVUQ 90 define proportional assurance.

The "thin schema" objection is preempted by the standards themselves. UofA's graded profiles are not a limitation. They are aligned with how regulated standards define proportional rigor.

## C3 — Quality gates

<a id="c3"></a>

The Apache Jena forward-chaining rule engine detects substantive credibility gaps that SHACL cannot express. The current catalog has 23 patterns: 21 Level-1 patterns plus 2 active compound patterns.

The compound patterns are the differentiator. A compound rule fires on the *output* of Level-1 rules. This is chained inference that standalone SPARQL queries cannot produce.

| Category | Patterns | Detects |
|---|---|---|
| Epistemic (W-EP-*) | 4 | Orphan claims, broken provenance, evidence-source gaps |
| Aleatoric (W-AL-*) | 2 | Missing UQ, missing sensitivity analysis |
| Ontological (W-ON-*) | 2 | Applicability, operating-envelope gaps |
| Argumentation (W-AR-*) | 5 | Comparator absence, residual-risk gaps |
| Structural (W-SI-*) | 2 | Internal consistency gaps |
| Consistency (W-CON-*) | 5 | Decision-vs-factor mismatches |
| Provenance (W-PROV-*) | 1 | Provenance-chain orphans |
| Compound | 2 | Risk escalation, assurance-level override |

See [Weakeners](/concepts/weakeners/) for the full taxonomy and the worked Morrison example.

What this gives you:

- **Automated reviewer attention.** Reviewers focus on the gaps the rule engine surfaces, not on hunting for them in prose.
- **Risk-driven divergence.** Same model, same data, different model risk produce measurably different weakener profiles. The rule engine surfaces this automatically with `uofa diff`.
- **Compound inference.** Coexisting Critical and High weakeners on the same UofA trigger COMPOUND-01. A declared assurance level inconsistent with detected gaps triggers COMPOUND-03. These are the kinds of patterns no individual SPARQL query can express.

Zero weakeners does not mean the model passed. Zero weakeners means the *evidence package* is structurally complete and auditable, even when the evidence indicates the model fails. The core value proposition is evidence packaging quality, not evidence sufficiency.
