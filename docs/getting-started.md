# Getting Started: Create Your First UofA

This guide walks you through creating a Unit of Assurance (UofA) evidence package for your own project. By the end, you'll have a signed, validated, machine-verifiable record of your credibility decision.

## Prerequisites

**Fastest option — GitHub Codespace (zero install):**

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/cloudronin/uofa?quickstart=1)

Click the button above. The Codespace comes with Python, Java, Maven, and the `uofa` CLI pre-installed. Skip to [Step 1](#step-1-choose-a-profile).

**Local install:**

```bash
# Install the uofa CLI (includes all Python dependencies + Excel import)
pip install -e '.[excel]'

# Java 17+ and Maven 3.8+ (required only for the rule engine, Step 5)
java -version   # should show 17+
mvn -version    # should show 3.8+
```

Java is only needed for the Jena rule engine (C3). You can use `--skip-rules` if Java is not available. The `[excel]` extra installs openpyxl for Excel import; omit it if you only work with JSON-LD directly.

## Choosing a Domain Pack

Domain packs define the standard-specific validation rules and allowed factor types. Pick the pack that matches your target standard:

| Pack | Standard | Use when |
|------|----------|----------|
| `vv40` | ASME V&V 40 | FDA submissions, medical device credibility evidence |
| `nasa-7009b` | NASA-STD-7009B | NASA M&S credibility assessments |

Pass the `--pack` flag to any command:

```bash
uofa check my-file.jsonld --pack vv40
uofa shacl my-file.jsonld --pack nasa-7009b
```

If you omit `--pack`, the CLI uses the `core` pack, which provides base shapes without standard-specific constraints.

### Migrating from v0.3

If you have existing v0.3 evidence packages, use the `migrate` command to upgrade them to v0.4:

```bash
uofa migrate my-project/my-cou1.jsonld
```

This updates the `@context` reference and adjusts fields as needed for the v0.4 vocabulary.

## Option A: Import from Excel (Fastest)

If you prefer working in a spreadsheet, use the Excel import pipeline. Fill in an Excel workbook and convert it to a signed JSON-LD evidence package in one command:

```bash
# Start from the filled example or a pack template
cp examples/starters/uofa-starter-filled.xlsx my-assessment.xlsx

# Edit my-assessment.xlsx in Excel — fill in your project details,
# credibility factors, validation results, and decision

# Import, sign, and validate in one step
uofa import my-assessment.xlsx --sign --key keys/research.key --check --pack vv40
```

The Excel template has 5 sheets: **Assessment Summary**, **Model & Data**, **Validation Results**, **Credibility Factors**, and **Decision**. Factor names and categories are pre-populated; you fill in levels, rationale, and status. The import command generates URIs, assigns `factorStandard`, tracks provenance, and writes a complete JSON-LD file.

For NASA-STD-7009B assessments, use `--pack nasa-7009b` — the template expands to 19 factors with `assessmentPhase` auto-assigned from factor categories.

**Prefer editing JSON-LD directly?** Continue with Option B below.

---

## Option B: Scaffold from JSON-LD Template

## Step 1: Choose a Profile

UofA has two profiles. Pick the one that fits your situation:

| Profile | When to use | Fields |
|---------|------------|--------|
| **Minimal** | Lightweight audit trail, live pipeline capture, early-stage projects | 7 required fields |
| **Complete** | Regulatory submissions, formal V&V 40 assessments, full credibility arguments | All of Minimal + model bindings, credibility factors, provenance, quality metrics |

**Starting out?** Begin with Minimal. You can upgrade to Complete later.

## Step 2: Scaffold Your Project

```bash
# Creates a directory with template, signing keys, and .gitignore
uofa init my-project

# Or for a Complete profile:
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

You can also start manually by copying a template:
```bash
cp examples/templates/uofa-minimal-skeleton.jsonld my-project-cou1.jsonld
```

## Step 3: Fill In Your Project Details

Open `my-project/my-project-cou1.jsonld` in your editor and replace the placeholder values.

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
| `hasCredibilityFactor` | Array of factor assessments (factorType + requiredLevel + achievedLevel). Factor types depend on the active pack. |
| `factorStandard` | URI of the standard that defines the factor types (e.g., `https://uofa.net/standards/ASME-VV40-2018`) |
| `assessmentPhase` | Phase of the assessment lifecycle (e.g., `"Planning"`, `"Execution"`, `"Review"`) |
| `hasEvidence` | URI(s) linking to supporting evidence artifacts |
| `assuranceLevel` | `"Low"`, `"Medium"`, or `"High"` |
| `criteriaSet` | URI of the standard used (e.g., `https://uofa.net/criteria/ASME-VV40-2018`) |

### Tips for IRIs

URIs don't need to resolve to real web pages. They serve as stable identifiers. Common patterns:
- `https://yourorg.com/projects/<project>/<type>/<name>`
- `https://doi.org/10.xxxx/...` for published references
- Use the same base URI across all artifacts in a project for consistency

### V&V 40 Factor Types

When using the `vv40` pack (`--pack vv40`), the `factorType` field accepts exactly these 13 values (from ASME V&V 40 Table 5-1):

**Verification -- Code:** `Software quality assurance`, `Numerical code verification`
**Verification -- Calculation:** `Discretization error`, `Numerical solver error`, `Use error`
**Validation -- Model:** `Model form`, `Model inputs`
**Validation -- Comparator:** `Test samples`, `Test conditions`
**Validation -- Assessment:** `Equivalency of input parameters`, `Output comparison`
**Applicability:** `Relevance of the quantities of interest`, `Relevance of the validation activities to the COU`

You don't need to assess all 13. Include only the factors relevant to your COU.

The `nasa-7009b` pack (`--pack nasa-7009b`) defines its own set of factor types aligned with NASA-STD-7009B. Use `uofa packs nasa-7009b` to see the available factors for that standard.

## Step 4: Sign Your Evidence Package

```bash
# Sign your UofA — this fills in the hash and signature fields
uofa sign my-project/my-project-cou1.jsonld --key my-project/keys/my-project.key
```

After signing, the `hash` and `signature` fields in your file will contain real values.

**Important:** Keep your private key (`.key`) secure and never commit it. Only the public key (`.pub`) should be shared or committed.

## Step 5: Validate

```bash
# Full pipeline — SHACL + integrity + rule engine
uofa check my-project/my-project-cou1.jsonld

# Or run components individually:
uofa shacl  my-project/my-project-cou1.jsonld    # C2: Completeness
uofa verify my-project/my-project-cou1.jsonld    # C1: Integrity (hash + signature)
uofa rules  my-project/my-project-cou1.jsonld    # C3: Quality gap detection (Jena)

# Skip the rule engine if Java is not available:
uofa check my-project/my-project-cou1.jsonld --skip-rules
```

### Reading Validation Output

**SHACL passes:** You'll see `✓ SHACL validation  Conforms`

**SHACL fails:** Each violation shows the field name, a plain-English message, and a fix suggestion. Common issues:
- Missing a required field → add it
- Hash/signature still has placeholder zeros → run `uofa sign` (Step 4)
- `factorType` not in the allowed list → check spelling against the factor types defined by your active pack (e.g., `--pack vv40`)

Use `uofa shacl FILE --raw` to see the full pyshacl report if you need more detail.

**Rule engine output:** Shows detected weakeners grouped by severity. These are not errors — they're quality gaps in your evidence. For example:
- `W-AL-01 (High)`: A validation result has no uncertainty quantification linked
- `W-AR-01 (Critical)`: A credibility factor has no acceptance criteria encoded
- `W-EP-01 (Critical)`: A claim has no provenance chain to supporting evidence

Zero weakeners is valid and desirable. The weakeners tell you where your evidence package could be strengthened.

## Step 6: Iterate

A typical workflow:

1. **Edit** your `.jsonld` to add evidence, fix gaps, or update the decision
2. **Re-sign** (`uofa sign FILE --key KEY`) — editing invalidates the previous hash
3. **Re-validate** (`uofa check FILE`) — confirm everything still passes
4. **Review weakeners** — address Critical/High gaps before submission

## What's Next

- **Study the Morrison example** (`examples/morrison/`) to see Complete profiles for an FDA V&V 40 case study (COU1 and COU2)
- **Add a second COU** — same model, different context of use, potentially different credibility requirements
- **Run COU divergence analysis** — compare weakener profiles across COUs to see how risk level affects evidence requirements
- **Integrate with CI** — add `uofa check` to your pipeline so credibility evidence is validated on every commit

## Reference

| Command | What it does |
|---------|-------------|
| `uofa import FILE.xlsx` | Import Excel workbook to JSON-LD (with optional `--sign`, `--check`) |
| `uofa check FILE` | Full C1+C2+C3 pipeline on any UofA file |
| `uofa shacl FILE` | SHACL profile validation only |
| `uofa verify FILE` | Hash + signature verification only |
| `uofa rules FILE` | Jena rule engine only |
| `uofa sign FILE --key KEY` | Sign/re-sign a UofA |
| `uofa keygen PATH` | Generate ed25519 signing keypair |
| `uofa validate` | SHACL validation on all examples |
| `uofa init NAME` | Scaffold a new UofA project |
| `uofa diff FILE_A FILE_B` | Compare weakener profiles across two COUs |
| `uofa packs [NAME]` | List installed packs or inspect a specific pack |
| `uofa schema` | Generate JSON Schema from SHACL (`--emit python` for import constants) |
| `uofa migrate FILE` | Migrate a v0.3 file to v0.4 |
