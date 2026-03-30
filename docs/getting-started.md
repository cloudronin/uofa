# Getting Started: Create Your First UofA

This guide walks you through creating a Unit of Assurance (UofA) evidence package for your own project. By the end, you'll have a signed, validated, machine-verifiable record of your credibility decision.

## Prerequisites

```bash
# Python dependencies
pip install pyshacl rdflib cryptography

# Java 17+ and Maven 3.8+ (required only for the rule engine, Step 5)
java -version   # should show 17+
mvn -version    # should show 3.8+
```

## Step 1: Choose a Profile

UofA has two profiles. Pick the one that fits your situation:

| Profile | When to use | Fields |
|---------|------------|--------|
| **Minimal** | Lightweight audit trail, live pipeline capture, early-stage projects | 7 required fields |
| **Complete** | Regulatory submissions, formal V&V 40 assessments, full credibility arguments | All of Minimal + model bindings, credibility factors, provenance, quality metrics |

**Starting out?** Begin with Minimal. You can upgrade to Complete later.

## Step 2: Copy a Template

```bash
# For Minimal profile
cp examples/templates/uofa-minimal-skeleton.jsonld my-project-cou1.jsonld

# For Complete profile
cp examples/templates/uofa-complete-skeleton.jsonld my-project-cou1.jsonld
```

## Step 3: Fill In Your Project Details

Open `my-project-cou1.jsonld` in your editor and replace the placeholder values.

### Minimal Profile Fields

| Field | What to put here | Example |
|-------|-----------------|---------|
| `id` | Unique URI for this UofA | `https://yourorg.com/projects/turbine-fatigue/uofa-cou1` |
| `name` | Short descriptive title | `Wind turbine blade fatigue — normal operation COU` |
| `bindsRequirement` | URI of the requirement this assessment supports | `https://yourorg.com/projects/turbine-fatigue/req/blade-life` |
| `hasContextOfUse` | Inline object describing the intended use | See template for structure |
| `hasValidationResult` | URI(s) of validation results | Array of URIs |
| `hasDecisionRecord` | Inline object with who decided, what, and why | See template for structure |
| `generatedAtTime` | ISO 8601 timestamp | `2026-03-15T00:00:00Z` |

Leave `hash` and `signature` as placeholder zeros for now — you'll sign the file in Step 4.

### Complete Profile — Additional Fields

On top of Minimal, Complete requires:

| Field | What to put here |
|-------|-----------------|
| `bindsModel` | URI identifying the computational model |
| `bindsDataset` | URI(s) of experimental or reference datasets |
| `wasDerivedFrom` | URI of the source document (report, DOI, prior UofA) |
| `wasAttributedTo` | URI of the responsible person or organization |
| `hasCredibilityFactor` | Array of V&V 40 factor assessments (factorType + requiredLevel + achievedLevel) |
| `assuranceLevel` | `"Low"`, `"Medium"`, or `"High"` |
| `criteriaSet` | URI of the standard used (e.g., `https://uofa.net/criteria/ASME-VV40-2018`) |

### Tips for IRIs

URIs don't need to resolve to real web pages. They serve as stable identifiers. Common patterns:
- `https://yourorg.com/projects/<project>/<type>/<name>`
- `https://doi.org/10.xxxx/...` for published references
- Use the same base URI across all artifacts in a project for consistency

### V&V 40 Factor Types

The `factorType` field accepts exactly these 13 values (from ASME V&V 40 Table 5-1):

**Verification — Code:** `Software quality assurance`, `Numerical code verification`
**Verification — Calculation:** `Discretization error`, `Numerical solver error`, `Use error`
**Validation — Model:** `Model form`, `Model inputs`
**Validation — Comparator:** `Test samples`, `Test conditions`
**Validation — Assessment:** `Equivalency of input parameters`, `Output comparison`
**Applicability:** `Relevance of the quantities of interest`, `Relevance of the validation activities to the COU`

You don't need to assess all 13. Include only the factors relevant to your COU.

## Step 4: Generate Keys and Sign

```bash
# Generate a signing keypair (one-time setup)
python scripts/sign_uofa.py --generate-key keys/my-project.key
# This creates keys/my-project.key (private) and keys/my-project.pub (public)

# Sign your UofA — this fills in the hash and signature fields
python scripts/sign_uofa.py my-project-cou1.jsonld \
  --key keys/my-project.key \
  --context spec/context/v0.2.jsonld
```

After signing, the `hash` and `signature` fields in your file will contain real values.

**Important:** Keep your private key (`.key`) secure and never commit it. Only the public key (`.pub`) should be shared or committed.

## Step 5: Validate

```bash
# SHACL validation — checks all required fields and format constraints
make check FILE=my-project-cou1.jsonld

# Or run components individually:
make shacl FILE=my-project-cou1.jsonld     # C2: Completeness
make verify FILE=my-project-cou1.jsonld    # C1: Integrity (hash + signature)
make rules FILE=my-project-cou1.jsonld     # C3: Quality gap detection (Jena)
```

### Reading Validation Output

**SHACL passes:** You'll see `Validation Report: Conforms: True`

**SHACL fails:** The report lists each violation with the property path and a human-readable message. Common issues:
- Missing a required field → add it
- Hash/signature still has placeholder zeros → run signing (Step 4)
- `factorType` not in the allowed list → check spelling against the 13 V&V 40 factors above

**Rule engine output:** Shows detected weakeners grouped by severity. These are not errors — they're quality gaps in your evidence. For example:
- `W-AL-01 (High)`: A validation result has no uncertainty quantification linked
- `W-AR-01 (Critical)`: A credibility factor has no acceptance criteria encoded
- `W-EP-01 (Critical)`: A claim has no provenance chain to supporting evidence

Zero weakeners is valid and desirable. The weakeners tell you where your evidence package could be strengthened.

## Step 6: Iterate

A typical workflow:

1. **Edit** your `.jsonld` to add evidence, fix gaps, or update the decision
2. **Re-sign** (`make sign FILE=...`) — editing invalidates the previous hash
3. **Re-validate** (`make check FILE=...`) — confirm everything still passes
4. **Review weakeners** — address Critical/High gaps before submission

## What's Next

- **Study the Morrison example** (`examples/morrison-cou1/`) to see a Complete profile for an FDA V&V 40 case study
- **Add a second COU** — same model, different context of use, potentially different credibility requirements
- **Run COU divergence analysis** — compare weakener profiles across COUs to see how risk level affects evidence requirements
- **Integrate with CI** — add `make check` to your pipeline so credibility evidence is validated on every commit

## Reference

| Command | What it does |
|---------|-------------|
| `make check FILE=<path>` | Full C1+C2+C3 pipeline on any UofA file |
| `make shacl FILE=<path>` | SHACL profile validation only |
| `make verify FILE=<path>` | Hash + signature verification only |
| `make rules FILE=<path>` | Jena rule engine only |
| `make sign FILE=<path> KEY=<keypath>` | Sign/re-sign a UofA |
| `make morrison` | Run the Morrison demo (C1+C2+C3) |
