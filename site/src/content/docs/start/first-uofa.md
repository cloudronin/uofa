---
title: Your first UofA
description: Scaffold a project, fill in your project details, sign, and validate.
---

This walkthrough produces a signed, validated UofA evidence package for one Context of Use.

## 1. Choose a profile

| Profile | When to use | Fields |
|---|---|---|
| **Minimal** | Lightweight audit trail, live pipeline capture, early-stage projects | 7 required fields |
| **Complete** | Regulatory submissions, formal V&V 40 assessments, full credibility arguments | All Minimal fields plus model bindings, credibility factors, provenance, and quality metrics |

Start with Minimal. You can upgrade to Complete later.

## 2. Scaffold your project

```bash
uofa init my-project
# or for a Complete profile:
uofa init my-project --profile complete
```

This creates:

```
my-project/
  my-project-cou1.jsonld       # template with placeholder values
  keys/
    my-project.key             # ed25519 private key (keep secret)
    my-project.pub             # ed25519 public key (commit this)
  .gitignore                   # excludes *.key
```

## 3. Fill in your project details

Open `my-project/my-project-cou1.jsonld` and replace the placeholder values.

### Minimal profile fields

| Field | What to put here |
|---|---|
| `id` | Unique URI for this UofA |
| `name` | Short descriptive title |
| `bindsRequirement` | URI of the requirement this assessment supports |
| `hasContextOfUse` | Inline object describing the intended use |
| `hasValidationResult` | URI(s) of validation results |
| `hasDecisionRecord` | Inline object with who decided, what, and why |
| `generatedAtTime` | ISO 8601 timestamp |

Leave `hash` and `signature` as placeholder zeros for now. You will sign the file in step 4.

### Complete profile adds

| Field | What to put here |
|---|---|
| `bindsModel` | URI identifying the computational model |
| `bindsDataset` | URI(s) of experimental or reference datasets |
| `wasDerivedFrom` | URI of the source document (report, DOI, prior UofA) |
| `wasAttributedTo` | URI of the responsible person or organization |
| `hasCredibilityFactor` | Array of factor assessments (factorType + requiredLevel + achievedLevel) |
| `factorStandard` | URI of the standard that defines the factor types |
| `assessmentPhase` | Phase of the assessment lifecycle |
| `hasEvidence` | URI(s) linking to supporting evidence artifacts |
| `assuranceLevel` | `"Low"`, `"Medium"`, or `"High"` |
| `criteriaSet` | URI of the standard used |

## 4. Sign

```bash
uofa sign my-project/my-project-cou1.jsonld --key my-project/keys/my-project.key
```

The `hash` and `signature` fields now contain real values. Keep your private key secure and never commit it. Only the public key (`.pub`) should be shared.

## 5. Validate

```bash
# Full pipeline: SHACL + integrity + rule engine
uofa check my-project/my-project-cou1.jsonld

# Or run components individually:
uofa shacl  my-project/my-project-cou1.jsonld    # C2: completeness
uofa verify my-project/my-project-cou1.jsonld    # C1: integrity
uofa rules  my-project/my-project-cou1.jsonld    # C3: quality gaps
```

Skip the rule engine if Java is not available:

```bash
uofa check my-project/my-project-cou1.jsonld --skip-rules
```

### Reading rule-engine output

The rule engine surfaces detected weakeners grouped by severity. Weakeners are not errors. They are quality gaps. For example:

- **W-AL-01 (High)** — a validation result has no uncertainty quantification linked
- **W-AR-01 (Critical)** — a credibility factor has no acceptance criteria encoded
- **W-EP-01 (Critical)** — a claim has no provenance chain to supporting evidence

Zero weakeners is valid and desirable. The weakeners tell you where your evidence package could be strengthened. See [Concepts → Weakeners](/concepts/weakeners/) for the full taxonomy.

## 6. Iterate

A typical workflow:

1. Edit your `.jsonld` to add evidence, fix gaps, or update the decision
2. Re-sign (`uofa sign FILE --key KEY`) — editing invalidates the previous hash
3. Re-validate (`uofa check FILE`) — confirm everything still passes
4. Review weakeners and address Critical and High gaps before submission
