# Unit of Assurance (UoA) Specification – v0.1

**Canonical URL:** [https://uofa.net](https://uofa.net)

---

## 🧭 Overview
The **Unit of Assurance (UoA)** is a minimal, semantic data structure that unites a  
**requirement, model, dataset, validation result, and decision** into a single verifiable record.

It is the foundational artifact of the [Assurance Alliance](https://assurancealliance.org)  
and is designed to make credibility **measurable, portable, and machine-verifiable**.

---

## Design Principles
- **Minimal:** Small enough to read by eye; easy to parse.
- **Semantic:** Built on JSON-LD for ontology alignment and reasoning.
- **Verifiable:** Supports digital signatures and content hashes.
- **Composable:** Many UoAs form an “Assurance Graph”.
- **Tool-agnostic:** Works with SysML, Simulink, Modelica, CFD/FEA pipelines.
  
---

## 🧱 Specification
- **Format:** JSON-LD  
- **Current version:** [v0.1](https://uofa.net/context/v0.1)  
- **Namespace:** `https://uofa.net/vocab#`
- **License:** [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)


### Core Fields

| Field | Description |
|--------|-------------|
| `uofa:id` | Unique identifier (UUID or hash) |
| `uofa:requirement` | Requirement text or URI |
| `uofa:model` | Model URI, tool, and version |
| `uofa:data` | Dataset source and hash |
| `uofa:validation` | Verification/validation result |
| `uofa:decision` | Decision and rationale |
| `uofa:signature` | Digital signature of the UoFA |
| `uofa:timestamp` | ISO-8601 timestamp |

---

## 💡 Example

### Notes
- Metrics are typed as xsd:decimal by context.
- Provide values as strings (recommended) or adjust SHACL to accept xsd:double if using bare numbers.

```json
{
  "@context": "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.1.jsonld",
  "id": "https://uofa.net/example/uoa/OpenFAST-Turbine-042",
  "type": "UnitOfAssurance",
  "conformsToProfile": "https://uofa.net/vocab#ProfileComplete",
  "name": "OpenFAST Turbine Simulation Validation – Complete Profile",
  "description": "Full-profile UoA including model, dataset, dual-twin validation, provenance chain, and graded-assurance metadata.",
  "bindsRequirement": "https://uofa.net/req/REQ-TURB-LoadPredict",
  "bindsClaim": "https://uofa.net/claim/CLM-TURB-LoadPredict",
  "bindsModel": "https://uofa.net/model/OpenFAST-v3.4",
  "bindsDataset": "https://uofa.net/data/NREL-Turbine-Benchmark",
  "hasValidationResult": "https://uofa.net/validation/VAL-2025-04",
  "wasDerivedFrom": "https://uofa.net/uoa/OpenFAST-Turbine-041",
  "wasAttributedTo": "https://uofa.net/org/NREL-Lab",
  "generatedAtTime": "2025-11-02T13:30:00Z",
  "hash": "sha256:a2b4432e3f4a9d8b6f2c5d90b8a0c75e",
  "signature": "ed25519:3efde42c91f...",
  "signatureAlg": "ed25519",
  "canonicalizationAlg": "URDNA2015",

  "credibilityIndex":   "0.93",
  "traceCompleteness":  "0.98",
  "verificationCoverage": "0.95",
  "validationCoverage":   "0.92",
  "uncertaintyCIWidth":   "0.04",


  "assuranceLevel": "High",
  "criteriaSet": "https://uofa.net/criteria/ASME-VVUQ-90",
  "hasDecisionRecord": "https://uofa.net/decision/DEC-2025-07"
}


