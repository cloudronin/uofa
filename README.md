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
- **License:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

### Core Fields
| Field | Description |
|-------|--------------|
| `uoa:id` | Unique identifier (UUID or hash) |
| `uoa:requirement` | Requirement text or URI |
| `uoa:model` | Model URI, tool, and version |
| `uoa:data` | Dataset source and hash |
| `uoa:validation` | Verification/validation result |
| `uoa:decision` | Decision and rationale |
| `uoa:signature` | Digital signature of the UoA |
| `uoa:timestamp` | ISO-8601 timestamp |

---
### 💡 Example
```json
{
 "@context": "https://uofa.net/context/v0.1",
 "uoa:id": "urn:uoa:3c4a2d58",
 "uoa:requirement": {
   "id": "REQ-1234",
   "text": "The system shall maintain heart rate accuracy within ±5 bpm."
 },
 "uoa:model": {
   "uri": "https://example.org/models/hearty/sim.slx",
   "tool": "Simulink"
 },
 "uoa:data": {
   "source": "HeartyPatch Dataset v3.2",
   "hash": "sha256:ab3f..."
 },
 "uoa:validation": {
   "metric": "RMSE",
   "value": 2.4,
   "unit": "bpm"
 },
 "uoa:decision": {
   "author": "QA-Lead",
   "verdict": "Accepted"
 },
 "uoa:signature": "ed25519:abc123...",
 "uoa:timestamp": "2025-11-01T12:45:00Z"
}

