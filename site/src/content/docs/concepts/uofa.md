---
title: What a UofA is
description: The Unit of Assurance construct. One signed JSON-LD package per Context of Use.
---

The **Unit of Assurance** is the smallest independently verifiable bundle of credibility evidence for computational modeling and simulation. It packages the credibility decision — who judged what, against what criteria, using what evidence, with what result — as a signed, provenance-linked, machine-verifiable engineering artifact.

## One UofA per Context of Use

UofA models credibility assessment at the **COU level**, not the individual factor level. Each UofA packages the complete credibility decision for one Context of Use, including all per-factor assessments as embedded `CredibilityFactor` nodes and any detected quality gaps as `WeakenerAnnotation` nodes.

```
Morrison Blood Pump Assessment
├── morrison/cou1/uofa-morrison-cou1.jsonld (ProfileComplete)
│   COU1: CPB Use (Class II) — Model Risk Level 2
│   ├── hasContextOfUse    → COU1 node
│   ├── bindsRequirement   → hemolysis safety requirement
│   ├── bindsModel         → ANSYS CFX v.15.0 + Eulerian HI model
│   ├── bindsDataset       → [PIV data, hemolysis in vitro data]
│   ├── hasValidationResult → [mesh convergence, PIV velocity, hemolysis comparison]
│   ├── hasCredibilityFactor → [13 V&V 40 factors: 7 assessed + 6 not-assessed]
│   ├── hasWeakener        → [W-AL-01 ×3, W-AR-05 ×3, W-EP-02 ×3, W-ON-02, W-CON-04]
│   ├── hasDecisionRecord  → "Accepted for COU1"
│   ├── hash               → sha256:<real hash>
│   ├── signature          → ed25519:<real signature>
│   └── wasDerivedFrom     → Morrison DOI
│
└── morrison/cou2/uofa-morrison-cou2.jsonld (ProfileComplete)
    COU2: VAD Use (Class III) — Model Risk Level 5
    └── ... (same structure, different decision and weakener profile)
```

Shared entities (model, datasets, geometry) are referenced by IRI rather than duplicated. The divergence between COU1 and COU2 weakener profiles is the central analytical demonstration: same model, same data, different model risk produce measurably different credibility evidence.

## Two profiles

| Profile | Use case | Required fields |
|---|---|---|
| **Minimal** | Lightweight audit trail, live pipeline capture, early-stage projects | 7 |
| **Complete** | Regulatory submissions, formal V&V 40 assessments, full credibility arguments | All Minimal + model bindings, credibility factors, provenance, quality metrics |

The profiles are computable. SHACL shapes enforce the field set for each profile. See [C1, C2, C3](/concepts/contributions/) for how this enforcement works.

## Standards alignment

<a id="standards"></a>

UofA is standards-anchored, not standards-replacing. It packages evidence for assessments performed against existing credibility frameworks.

| Standard | Pack | Factor count | Level range |
|---|---|---|---|
| ASME V&V 40-2018 | `vv40` | 13 | 1–5 |
| NASA-STD-7009B | `nasa-7009b` | 19 (13 shared + 6 NASA-only) | 0–4 |
| FDA 2023 CM&S Guidance | (uses `vv40`) | 13 | 1–5 |
| DO-178C aerospace software | (planned, post-defense) | — | — |

Multiple packs can be loaded simultaneously. The CLI loads core SHACL plus pack-specific shapes additively. See [Reference → CLI](/reference/cli/) for the `--pack` flag.

## Design principles

| Principle | Meaning |
|---|---|
| Minimal | Small JSON-LD document, human-readable, one file per COU |
| Semantic | Aligns with PROV-O, V&V 40, and domain ontologies |
| Verifiable | Real SHA-256 hashes, ed25519 signatures, SHACL validation |
| Composable | UofAs form nodes in system-level assurance graphs via `wasDerivedFrom` |
| Tool-agnostic | Works with any simulation tool, MBSE platform, or ML pipeline |
| Hide the plumbing | Practitioners see completeness reports and gap alerts, not triples and SPARQL |
