# UofA — Onboarding Guide

This single guide covers two audiences:

1. **End-users** who want to create their first signed, validated
   credibility evidence package — start with [Part 1: Quick Start](#part-1--quick-start).
2. **Contributors** who want to understand the codebase and add new
   features — read [Part 2: Architecture](#part-2--architecture) and
   [Part 3: Contributing](#part-3--contributing).

> **Companion docs:** [`repo-layout.md`](repo-layout.md) for top-level
> directory orientation, [`phase2_runbook.md`](phase2_runbook.md) for
> the adversarial corpus generation pipeline, and
> [`m5_findings.md`](m5_findings.md) for the Phase 2.5 catalog
> refinement context.

> **Older versions** of these notes live in [`docs/archive/`](archive/)
> as `architecture.md` and `getting-started.md`.

---

# Part 1 — Quick Start

This walks you through creating a Unit of Assurance (UofA) evidence
package for your own project. By the end, you'll have a signed,
validated, machine-verifiable record of your credibility decision.

## Prerequisites

**Fastest option — GitHub Codespace (zero install):**

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/cloudronin/uofa?quickstart=1)

Click the button above. The Codespace comes with Python, Java, Maven,
and the `uofa` CLI pre-installed. Skip ahead to [choosing a domain pack](#choosing-a-domain-pack).

**Local install:**

```bash
# Install the uofa CLI (includes all Python dependencies + Excel import)
pip install -e '.[excel]'

# Java 17+ and Maven 3.8+ (required only for the rule engine, Step 5)
java -version   # should show 17+
mvn -version    # should show 3.8+
```

Java is only needed for the Jena rule engine (C3). Use `--skip-rules`
if Java is not available. The `[excel]` extra installs openpyxl for
Excel import; omit it if you only work with JSON-LD directly.

## Choosing a Domain Pack

Domain packs define the standard-specific validation rules and allowed
factor types. Pick the pack that matches your target standard:

| Pack | Standard | Use when |
|------|----------|----------|
| `vv40` | ASME V&V 40 | FDA submissions, medical device credibility evidence |
| `nasa-7009b` | NASA-STD-7009B | NASA M&S credibility assessments |

Pass the `--pack` flag to any command:

```bash
uofa check my-file.jsonld --pack vv40
uofa shacl my-file.jsonld --pack nasa-7009b
```

If you omit `--pack`, the CLI uses the `core` pack, which provides base
shapes without standard-specific constraints.

### Migrating from v0.3

If you have existing v0.3 evidence packages, use the `migrate` command
to upgrade them to v0.4:

```bash
uofa migrate my-project/my-cou1.jsonld
```

This updates the `@context` reference and adjusts fields as needed for
the v0.4 vocabulary.

## Option A: Import from Excel (Fastest)

If you prefer working in a spreadsheet, use the Excel import pipeline.
Fill in an Excel workbook and convert it to a signed JSON-LD evidence
package in one command:

```bash
# Start from the filled example or a pack template
cp packs/vv40/templates/uofa-starter-filled.xlsx my-assessment.xlsx

# Edit my-assessment.xlsx in Excel — fill in your project details,
# credibility factors, validation results, and decision

# Import, sign, and validate in one step
uofa import my-assessment.xlsx --sign --key keys/research.key --check --pack vv40
```

The Excel template has 5 sheets: **Assessment Summary**, **Model & Data**,
**Validation Results**, **Credibility Factors**, and **Decision**.
Factor names and categories are pre-populated; you fill in levels,
rationale, and status. The import command generates URIs, assigns
`factorStandard`, tracks provenance, and writes a complete JSON-LD file.

For NASA-STD-7009B assessments, use `--pack nasa-7009b` — the template
expands to 19 factors with `assessmentPhase` auto-assigned from factor
categories.

**Prefer editing JSON-LD directly?** Continue with Option B below.

---

## Option B: Scaffold from JSON-LD Template

### Step 1: Choose a Profile

UofA has two profiles. Pick the one that fits your situation:

| Profile | When to use | Fields |
|---------|------------|--------|
| **Minimal** | Lightweight audit trail, live pipeline capture, early-stage projects | 7 required fields |
| **Complete** | Regulatory submissions, formal V&V 40 assessments, full credibility arguments | All of Minimal + model bindings, credibility factors, provenance, quality metrics |

**Starting out?** Begin with Minimal. You can upgrade to Complete later.

### Step 2: Scaffold Your Project

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
cp packs/core/templates/uofa-minimal-skeleton.jsonld my-project-cou1.jsonld
```

### Step 3: Fill In Your Project Details

Open `my-project/my-project-cou1.jsonld` in your editor and replace the
placeholder values.

#### Minimal Profile Fields

| Field | What to put here | Example |
|-------|-----------------|---------|
| `id` | Unique URI for this UofA | `https://yourorg.com/projects/turbine-fatigue/uofa-cou1` |
| `name` | Short descriptive title | `Wind turbine blade fatigue — normal operation COU` |
| `bindsRequirement` | URI of the requirement this assessment supports | `https://yourorg.com/projects/turbine-fatigue/req/blade-life` |
| `hasContextOfUse` | Inline object describing the intended use | See template for structure |
| `hasValidationResult` | URI(s) of validation results | Array of URIs |
| `hasDecisionRecord` | Inline object with who decided, what, and why | See template for structure |
| `generatedAtTime` | ISO 8601 timestamp | `2026-03-15T00:00:00Z` |

Leave `hash` and `signature` as placeholder zeros for now — you'll
sign the file in Step 4.

#### Complete Profile — Additional Fields

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

#### Tips for IRIs

URIs don't need to resolve to real web pages. They serve as stable
identifiers. Common patterns:
- `https://yourorg.com/projects/<project>/<type>/<name>`
- `https://doi.org/10.xxxx/...` for published references
- Use the same base URI across all artifacts in a project for consistency

#### V&V 40 Factor Types

When using the `vv40` pack (`--pack vv40`), the `factorType` field
accepts exactly these 13 values (from ASME V&V 40 Table 5-1):

**Verification -- Code:** `Software quality assurance`, `Numerical code verification`
**Verification -- Calculation:** `Discretization error`, `Numerical solver error`, `Use error`
**Validation -- Model:** `Model form`, `Model inputs`
**Validation -- Comparator:** `Test samples`, `Test conditions`
**Validation -- Assessment:** `Equivalency of input parameters`, `Output comparison`
**Applicability:** `Relevance of the quantities of interest`, `Relevance of the validation activities to the COU`

You don't need to assess all 13. Include only the factors relevant to
your COU.

The `nasa-7009b` pack (`--pack nasa-7009b`) defines its own set of
factor types aligned with NASA-STD-7009B. Use `uofa packs nasa-7009b`
to see the available factors for that standard.

### Step 4: Sign Your Evidence Package

```bash
# Sign your UofA — this fills in the hash and signature fields
uofa sign my-project/my-project-cou1.jsonld --key my-project/keys/my-project.key
```

After signing, the `hash` and `signature` fields in your file will
contain real values.

**Important:** Keep your private key (`.key`) secure and never commit
it. Only the public key (`.pub`) should be shared or committed.

### Step 5: Validate

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

#### Reading Validation Output

**SHACL passes:** You'll see `✓ SHACL validation  Conforms`

**SHACL fails:** Each violation shows the field name, a plain-English
message, and a fix suggestion. Common issues:
- Missing a required field → add it
- Hash/signature still has placeholder zeros → run `uofa sign` (Step 4)
- `factorType` not in the allowed list → check spelling against the factor types defined by your active pack (e.g., `--pack vv40`)

Use `uofa shacl FILE --raw` to see the full pyshacl report if you need
more detail.

**Rule engine output:** Shows detected weakeners grouped by severity.
These are not errors — they're quality gaps in your evidence. For
example:
- `W-AL-01 (High)`: A validation result has no uncertainty quantification linked
- `W-AR-01 (Critical)`: A credibility factor has no acceptance criteria encoded
- `W-EP-01 (Critical)`: A claim has no provenance chain to supporting evidence

Zero weakeners is valid and desirable. The weakeners tell you where
your evidence package could be strengthened.

### Step 6: Iterate

A typical workflow:

1. **Edit** your `.jsonld` to add evidence, fix gaps, or update the decision
2. **Re-sign** (`uofa sign FILE --key KEY`) — editing invalidates the previous hash
3. **Re-validate** (`uofa check FILE`) — confirm everything still passes
4. **Review weakeners** — address Critical/High gaps before submission

## Evidence format limitations

Guidance from the Pre-Tester QA Corpus runs:

- **`uofa extract` works best on structured reports of 10+ pages with
  tables.** Performance degrades on slide decks, scanned (image-only)
  documents, and brief memos. Scanned PDFs will parse but yield the
  sentinel chunk `(image-only PDF — no extractable text)`; use OCR
  upstream if you need the text.
- **UofA prefers UTF-8 files.** Non-UTF-8 input (e.g., Shift-JIS, CP1252)
  is handled via a `chardet` fallback but may produce warnings or
  mojibake — save sources as UTF-8 where possible.
- **Password-protected Excel workbooks are refused with a named error**;
  remove the password before running `uofa import` or `uofa extract`.
- **Corrupted or truncated PDFs** produce a named warning rather than
  crashing the pipeline; the file is skipped.

## What's Next

- **Study the Morrison example** (`packs/vv40/examples/morrison/`) to
  see Complete profiles for an FDA V&V 40 case study (COU1 and COU2)
- **Run the NASA aerospace roundtrip** — `packs/nasa-7009b/examples/aerospace/`
  ships two zipped evidence bundles (take-off + cruise) plus their
  reasoned outputs. Exercise the full `uofa extract → import → rules`
  pipeline on real documents:
  `uofa extract tests/fixtures/extract/aero-evidence-cou1 --pack nasa-7009b --model ollama/qwen3.5:4b`.
  See the [aerospace demo section of the README](../README.md#live-demo-hpt-blade-cht-nasa-std-7009b-aerospace).
- **Add a second COU** — same model, different context of use, potentially different credibility requirements
- **Run COU divergence analysis** — compare weakener profiles across COUs to see how risk level affects evidence requirements
- **Integrate with CI** — add `uofa check` to your pipeline so credibility evidence is validated on every commit

## Command Reference

| Command | What it does |
|---------|-------------|
| `uofa extract DIR` | LLM-extract credibility data from evidence documents into a pack xlsx (`--model`, `--pack`, `-o`) |
| `uofa import FILE.xlsx` | Import Excel workbook to JSON-LD (with optional `--sign`, `--check`) |
| `uofa check FILE` | Full C1+C2+C3 pipeline on any UofA file |
| `uofa shacl FILE` | SHACL profile validation only |
| `uofa verify FILE` | Hash + signature verification only |
| `uofa rules FILE` | Jena rule engine only (human-readable summary) |
| `uofa rules FILE --format jsonld -o REASONED.jsonld` | Jena rule engine writing reasoned JSON-LD with weakener annotations |
| `uofa sign FILE --key KEY` | Sign/re-sign a UofA |
| `uofa keygen PATH` | Generate ed25519 signing keypair |
| `uofa validate` | SHACL validation on all examples |
| `uofa init NAME` | Scaffold a new UofA project |
| `uofa diff FILE_A FILE_B` | Compare weakener profiles across two COUs |
| `uofa packs [NAME]` | List installed packs or inspect a specific pack |
| `uofa schema` | Generate JSON Schema from SHACL (`--emit python` for import constants) |
| `uofa migrate FILE` | Migrate a v0.3 file to v0.4 |

---

# Part 2 — Architecture

This part covers the architecture, design patterns, and conventions
used across the UofA CLI. It is intended for contributors who want to
understand the codebase before adding new features.

## High-Level Overview

The UofA CLI implements three validation pipelines for credibility
evidence packages:

| Pipeline | Label | What it checks | Mechanism |
|---|---|---|---|
| **C1** | Integrity | Content hasn't been tampered with | SHA-256 hash + ed25519 digital signature |
| **C2** | Completeness | Required fields are present and well-formed | SHACL shapes (pyshacl) |
| **C3** | Quality gates | Substantive credibility gaps | Apache Jena forward-chaining rules (Java subprocess) |

The CLI is a Python package (`uofa_cli`) with 12 subcommands, a set of
core modules for cryptography and formatting, an Excel import pipeline,
and a Java backend for the rule engine.

```
                      uofa <command>
                            │
              ┌─────────────┼─────────────────┐
              │             │                 │
         Pure Python    Python + Java     Utility        Import
         ┌────────┐    ┌───────────┐    ┌─────────┐    ┌────────┐
         │ sign   │    │ rules     │    │ init    │    │ import │
         │ verify │    │ check     │    │ keygen  │    └────────┘
         │ shacl  │    │           │    │ schema  │
         │ diff   │    │           │    │ validate│
         └────────┘    └───────────┘    └─────────┘
```

## Directory Structure

```
src/uofa_cli/
  __main__.py             # python -m uofa_cli entry point
  cli.py                  # argparse dispatcher — registers all subcommands
  integrity.py            # SHA-256 hashing + ed25519 signing/verification
  paths.py                # auto-discovery of repo root, packs, and asset paths
  output.py               # ANSI color helpers + table rendering
  explain.py              # generic divergence explanation (reads description field)
  shacl_friendly.py       # SHACL violation → plain English translator
  excel_constants.py      # GENERATED from SHACL — factor names, enums, level ranges
  excel_reader.py         # Excel workbook parser + validator (openpyxl)
  excel_mapper.py         # intermediate dict → JSON-LD with URIs + provenance
  commands/               # one module per subcommand
    check.py              # full C1+C2+C3 pipeline
    diff.py               # COU divergence analysis
    import_excel.py       # import Excel workbook → JSON-LD (with --sign, --check)
    init.py               # scaffold new projects
    keygen.py             # generate ed25519 keypair
    packs.py              # list and inspect installed domain packs
    rules.py              # Jena rule engine (C3)
    schema.py             # generate JSON Schema or Python constants from SHACL
    shacl.py              # SHACL validation (C2)
    sign.py               # sign UofA files
    validate.py           # bulk validate all examples
    verify.py             # verify hash + signature (C1)
    migrate.py            # migrate v0.3 files to v0.4

packs/
  core/                   # Base domain pack (pack-agnostic core shapes)
    pack.json             # Pack manifest (name, version, shapes, rules, etc.)
    shapes/
      uofa_shacl.ttl      # SHACL shapes — single source of truth for validation
    rules/
      uofa_weakener.rules # Jena forward-chaining rules
    templates/
      uofa-template.xlsx  # Excel template for uofa import
    prompts/              # (populated when uofa extract ships)
  vv40/                   # ASME V&V 40 domain pack (13 credibility factors)
    pack.json
    shapes/               # V&V 40–specific SHACL constraints (factorType enum, etc.)
    rules/                # V&V 40–specific weakener rules
  nasa-7009b/             # NASA-STD-7009B domain pack
    pack.json
    shapes/               # 7009B-specific SHACL constraints
    rules/                # 7009B-specific weakener rules
  README.md               # How to create a domain pack

spec/
  context/v0.5.jsonld     # JSON-LD vocabulary context (@vocab, property mappings)
  schemas/
    uofa_shacl.ttl        # SYMLINK → ../../packs/core/shapes/uofa_shacl.ttl
    uofa.schema.json      # JSON Schema — generated from SHACL via `uofa schema`

  # Examples and templates live alongside their pack's shapes and rules.
  # Each pack is self-contained — no top-level examples/ directory.

src/weakener-engine/      # Java Jena rule engine
  pom.xml                 # Maven config (Jena 5.3, picocli)
  src/main/java/.../
    WeakenerEngine.java   # CLI entry point — loads JSON-LD, runs rules, outputs report

tests/
  test_integration.py     # integration tests covering all subcommands
  test_import_corpus.py   # parametrized import tests driven by corpus manifest
  test_explain.py         # unit tests for divergence explanation module
  generate_test_corpus.py # generates Excel test fixtures + tc_manifest.json
  fixtures/import/        # generated .xlsx test files (TC-01 through TC-62)
```

For a top-level orientation across `specs/`, `build/`, `tools/`, `docs/`,
see [`repo-layout.md`](repo-layout.md).

## Subcommand Module Contract

Every subcommand in `src/uofa_cli/commands/` exports exactly three
things:

```python
HELP: str                          # one-line description for argparse
add_arguments(parser) -> None      # configure subcommand arguments
run(args) -> int                   # execute and return 0 (pass) or non-zero (fail)
```

Registration happens in `cli.py`:

```python
from uofa_cli.commands import keygen, sign, verify, ...

modules = {"keygen": keygen, "sign": sign, "verify": verify, ...}

for name, mod in modules.items():
    sp = sub.add_parser(name, help=mod.HELP, parents=[parent])
    mod.add_arguments(sp)
```

At runtime, the dispatcher calls `modules[args.command].run(args)`.

**Global flags** available to all subcommands (defined on the parent parser):
- `--no-color` — disables ANSI color output
- `--verbose` — shows full tracebacks on error
- `--repo-root PATH` — overrides repo root auto-detection
- `--pack NAME` — selects the domain pack for shapes, rules, and templates (default: `core`)

## Subcommand Details

(Brief table is in [Part 1's Command Reference](#command-reference).
Below are implementation details that contributors care about.)

### `uofa keygen <path>`

Generates an ed25519 keypair. Creates `<path>` (private key, PEM PKCS8)
and `<path>.pub` (public key, PEM SubjectPublicKeyInfo). Parent
directories are created automatically.

### `uofa sign <file> --key <key>`

Signs a UofA JSON-LD file. Process: load JSON-LD, resolve `@context`,
strip integrity fields (`hash`, `signature`, `signatureAlg`,
`canonicalizationAlg`), canonicalize (sorted-key JSON, UTF-8), compute
SHA-256, sign with ed25519, inject integrity fields back, write file.

Optional: `--context` for external context file, `--output` for
separate output path.

### `uofa verify <file>`

Verifies C1 integrity. Recomputes SHA-256 from canonical form and
compares to declared `hash` field. Verifies `signature` against the
public key. Returns 0 only if both match.

Optional: `--pubkey` (default: `keys/research.pub`).

### `uofa shacl <file>`

Runs C2 SHACL validation using pyshacl. Default mode translates
violations into friendly messages with severity badges and fix
suggestions. `--raw` shows raw pyshacl output.

The SHACL schema at `spec/schemas/uofa_shacl.ttl` defines a dispatcher
shape that branches based on `conformsToProfile` to either
`MinimalBody` or `CompleteBody` constraints.

### `uofa rules <file>`

Runs C3 quality gap detection via the Java Jena rule engine. Invokes
`java -jar src/weakener-engine/target/uofa-weakener-engine-0.1.0.jar` as a
subprocess. The engine loads JSON-LD into an RDF graph, applies
forward-chaining rules in RETE mode, and reports detected
`WeakenerAnnotation` triples.

`--build` auto-builds the JAR if missing. `--rules` overrides the
default rules file. `--raw` shows uncolorized output. Requires Java
17+ and Maven 3.8+ (for building).

### `uofa check <file>`

Runs the full pipeline in order: C2 (SHACL) then C1 (integrity) then
C3 (rules). Prints a summary with pass/fail for each step.
`--skip-rules` omits C3 (no Java required). `--build` auto-builds the
Jena JAR.

### `uofa validate`

Bulk validates all `*.jsonld` files under `packs/*/examples/` against
SHACL. Excludes `templates/` subdirectory. `--verify` additionally
checks hash + signature integrity on each file (skips unsigned files
with placeholder hashes). `--dir` overrides the scan directory.

### `uofa init <name>`

Scaffolds a new UofA project. Creates a directory with a template
JSON-LD file (from `packs/core/templates/`), generates a keypair, and
creates a `.gitignore`. `--profile minimal|complete` selects the
template. `--dir` sets the parent directory.

### `uofa diff <file_a> <file_b>`

Compares weakener profiles between two UofA files. Outputs four
sections:

1. **COU Identity Block** — side-by-side metadata (name, device class, MRL, decision, assurance level)
2. **Weakener Profile Table** — pattern presence grid with divergence markers. COMPOUND patterns get a separate sub-table.
3. **Summary Counts** — per-COU severity tier breakdown + total divergence count
4. **Divergence Explanations** — reads the `description` field from each divergent WeakenerAnnotation. Falls back to a generic message if no description is present.

The diff command is entirely pattern-agnostic — it works with any
pattern IDs and does not hardcode rule-specific logic.

### `uofa packs [name]`

Lists installed domain packs or inspects a specific pack. Without
arguments, shows all packs with version and description. With a pack
name, shows full manifest details including shapes path, rules path,
standards, and factor counts.

### `uofa import <file.xlsx>`

Imports an Excel workbook into a UofA JSON-LD file. The pipeline:
`excel_reader.py` (parse + validate) → `excel_mapper.py` (JSON-LD
generation) → write → optional sign → optional check.

Arguments: `--output` (default: same path with `.jsonld`), `--sign` +
`--key` (signs after writing), `--check` (runs full C1+C2+C3 pipeline),
`--profile` (override auto-detection).

The import pipeline uses `excel_constants.py` for factor names, level
ranges, and enum validation. This file is **generated** from SHACL
shapes via `uofa schema --emit python` — see "Schema Strategy" below.

The reader detects old-format templates (without the Type column in
Validation Results) and v2 templates (with evidence type column)
automatically. Error messages include sheet name + cell reference for
easy debugging.

### `uofa schema`

Generates `spec/schemas/uofa.schema.json` from the SHACL shapes in the
active pack. This ensures the JSON Schema stays in sync with the SHACL
source of truth. Uses rdflib to parse Turtle and maps SHACL constraints
to JSON Schema properties.

With `--emit python`, generates `src/uofa_cli/excel_constants.py`
instead — a Python module containing factor names, level ranges,
dropdown enums, and evidence types extracted from all SHACL shapes
(core + all packs). This keeps the Excel import pipeline in sync with
SHACL without manual constant maintenance.

### `uofa migrate <file>`

Migrates a v0.3 UofA JSON-LD file to v0.4. Updates the `@context`
reference, adds any new required properties with sensible defaults,
and adjusts pack-specific fields as needed. Use this when upgrading
existing evidence packages to the v0.4 vocabulary.

## Core Modules

### `integrity.py` — Cryptographic operations

All signing and verification logic lives here. Key functions:

| Function | Purpose |
|---|---|
| `resolve_context(doc, jsonld_path, context_path)` | Inlines `@context` references from file |
| `strip_integrity_fields(doc)` | Returns copy without hash/signature/signatureAlg/canonicalizationAlg |
| `canonicalize_and_hash(doc)` | Sorted-key JSON → SHA-256 hex |
| `generate_keypair(key_path)` | Creates ed25519 `.key` + `.pub` files |
| `sign_hash(sha256_hex, key_path)` | Signs hash with private key |
| `verify_signature(sha256_hex, sig_hex, pubkey_path)` | Verifies signature against public key |
| `sign_file(input, key, context, output)` | High-level: load → hash → sign → write |
| `verify_file(input, pubkey, context)` | High-level: load → hash → compare → verify sig |

Canonicalization:
`json.dumps(doc, sort_keys=True, ensure_ascii=False, separators=(',', ':'))`.
This is a deterministic JSON canonical form, not RDFC-1.0 (despite the
`canonicalizationAlg` field in the document).

### `paths.py` — Asset discovery and pack resolution

Finds the repo root by searching upward for the marker file
`packs/core/pack.json` or `spec/schemas/uofa_shacl.ttl` (backward
compat). All other paths are relative to this root. The root is cached
globally after first discovery.

**Pack-aware resolution:** The `--pack` flag (default: `core`) sets the
active pack via `set_active_pack()`. Asset functions like
`shacl_schema()` and `rules_file()` read from the active pack's
manifest (`pack.json`) to locate files. If the pack or manifest is
missing, they fall back to the legacy hardcoded paths.

Key pattern: commands never hardcode paths. They call
`paths.shacl_schema()`, `paths.jar_path()`,
`paths.rules_file(input_path)`, etc.

The `rules_file()` function searches in order: same directory as the
input file, then the parent directory, then the active pack's rules
directory. This allows per-project rules files while falling back to
the pack rules.

Additional pack functions:
- `pack_dir(name)` — returns the directory for a named pack
- `pack_manifest(name)` — loads and returns `pack.json` as a dict
- `list_packs()` — discovers all installed packs (directories under `packs/` with `pack.json`)
- `template_path()` / `extract_prompt()` — resolve template and prompt paths from the manifest

### `output.py` — Terminal formatting

ANSI color helpers, severity badges, and table rendering. Color is
auto-detected from TTY status and can be disabled via `--no-color` or
the `NO_COLOR` environment variable.

Table functions (`table_header`, `table_row`, `table_footer`,
`table_separator`) use box-drawing characters and handle ANSI-aware
column width padding.

### `shacl_friendly.py` — SHACL violation translator

Translates raw pyshacl violations into structured dicts with fields:
`path` (friendly field name), `message`, `fix` (actionable suggestion),
`severity` (Critical/High/Medium/Low). The fix suggestions and
severity assignments are keyed on SHACL property URIs.

A module-level `threading.RLock` serializes pyshacl calls because
`rdflib` graph state is not thread-safe under `ThreadPoolExecutor`
parallelism. This was added in v0.5.15.1 after parallel adversarial
generation surfaced spurious 0/N pass rates.

### `explain.py` — Divergence explanation

A single function, `explain_divergence()`, that reads the `description`
field from a `WeakenerAnnotation` dict and formats it into explanation
lines. Falls back to showing the `affectedNode` IRI if no description
is present. No pattern-specific logic — the rule engine is the
authority on *why* a weakener fires.

### Excel Import Pipeline

Three modules handle Excel → JSON-LD conversion:

| Module | Responsibility |
|---|---|
| `excel_constants.py` | **Generated** from SHACL. Factor names, level ranges, enum values, evidence types. Also contains hand-maintained Excel layout constants (sheet names, row offsets, category mappings). Regenerate with `uofa schema --emit python`. |
| `excel_reader.py` | Parses Excel workbooks via openpyxl. Validates required sheets, dropdown values, level ranges. Returns clean intermediate dict. Knows Excel structure, not JSON-LD. |
| `excel_mapper.py` | Transforms intermediate dict → JSON-LD document. Handles URI slugification, `factorStandard` assignment based on pack, NASA-specific `assessmentPhase`, evidence `@type`, provenance chain injection. Knows JSON-LD, not openpyxl. |

The separation means `excel_reader.py` can be tested without JSON-LD
knowledge, and `excel_mapper.py` can be tested without Excel files.

## The Java Rule Engine

The weakener engine at `src/weakener-engine/` is a Java CLI built with
Apache Jena 5.3 and picocli. It is invoked as a subprocess from
`rules.py`.

**Invocation:**
```
java -jar src/weakener-engine/target/uofa-weakener-engine-0.1.0.jar \
    <input.jsonld> --rules <rules_file> --context <context.jsonld>
```

**How it works:**
1. Parses JSON-LD into an RDF graph (resolves `@context`)
2. Loads Jena forward-chaining rules (`.rules` file)
3. Creates a `GenericRuleReasoner` in `FORWARD_RETE` mode
4. Runs inference — new `WeakenerAnnotation` triples are materialized
5. Extracts and reports weakener annotations (pattern ID, severity, affected node)

**Rule levels:**
- **Level 1 (core rules):** Match structural patterns in the evidence graph (e.g., missing provenance, missing UQ, credibility factor gaps)
- **Level 2 (compound rules):** Fire on the output of Level 1 (e.g., Critical + High coexist → COMPOUND-01 risk escalation). This chained inference is what SPARQL cannot produce.

**Building:** `cd src/weakener-engine && mvn package -q` (requires Java 17+
and Maven 3.8+). The CLI's `--build` flag automates this.

## Spec Files and Schema Strategy

The SHACL shapes in `packs/core/shapes/uofa_shacl.ttl` are the
**single source of truth** for validation constraints. A symlink at
`spec/schemas/uofa_shacl.ttl` preserves backward compatibility. The
JSON Schema at `spec/schemas/uofa.schema.json` is **generated** from
SHACL via `uofa schema` and should never be edited by hand.

If you change a validation constraint:
1. Edit `packs/core/shapes/uofa_shacl.ttl` (or the relevant pack shapes)
2. Run `uofa schema` to regenerate the JSON Schema
3. Run `uofa schema --emit python` to regenerate import constants
4. Run `uofa validate` to verify all examples still conform

The JSON-LD context at `spec/context/v0.5.jsonld` defines the
vocabulary mappings. It maps short property names (e.g., `patternId`)
to full URIs (e.g., `uofa:patternId`). If you add a new property to
the schema, you must also add its mapping here. The context is
framework-level (not pack-specific) — all packs share the same
vocabulary. New properties added in v0.5 back the expanded weakener
catalog: `dataVintage`, `modelRevisionDate`, `hasSensitivityAnalysis`,
`modelVersion`, `evidenceTimestamp`, `signatureTimestamp`,
`isFoundationalEvidence`, `hasVerificationActivity`,
`referencesIdentifier`, `residualRiskJustification`,
`consideredAlternative`, and `knownLimitation`.

> **Naming note:** `spec/` (singular) holds the v0.5 vocabulary +
> JSON Schema + SHACL symlink, while `specs/` (plural) holds adversarial
> spec YAML batteries. See [`repo-layout.md`](repo-layout.md) for the
> rationale.

## Integration Tests

Tests live in `tests/test_integration.py`,
`tests/test_import_corpus.py`, and `tests/test_explain.py`. Run them
with:

```bash
pip install -e '.[test,excel]'
python tests/generate_test_corpus.py   # one-time: generates Excel test fixtures
pytest tests/ -v
```

### How tests work

All integration tests use the `run_uofa(*args)` helper, which invokes
`python -m uofa_cli` as a subprocess and returns a `CompletedProcess`
with `stdout`, `stderr`, and `returncode`. This tests the full CLI
path including argument parsing and exit codes.

```python
def run_uofa(*args):
    return subprocess.run(
        [sys.executable, "-m", "uofa_cli", *args],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
```

### Test fixtures

| Constant | Path | Purpose |
|---|---|---|
| `MORRISON` | `packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld` | Reference valid Complete profile (signed) |
| `MORRISON_COU2` | `packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld` | COU2 variant (different weakener profile) |
| `MINIMAL_TEMPLATE` | `packs/core/templates/uofa-minimal-skeleton.jsonld` | Minimal profile skeleton |
| `COMPLETE_TEMPLATE` | `packs/core/templates/uofa-complete-skeleton.jsonld` | Complete profile skeleton |
| `JAVA_AVAILABLE` | `shutil.which("java")` | Gates tests that require the Jena engine |

### Test classes

| Class | What it covers |
|---|---|
| `TestCLIBasics` | `--help`, `--version`, no-command behavior |
| `TestKeygen` | Keypair generation, parent directory creation |
| `TestSign` | Signing, missing key/file errors |
| `TestVerify` | Verification, unsigned files, sign-then-verify roundtrip, tamper detection |
| `TestShacl` | SHACL conformance, invalid files, raw mode, friendly fix suggestions |
| `TestRules` | Jena weakener detection (skipped if no Java) |
| `TestCheck` | Full C1+C2+C3 pipeline, `--skip-rules` |
| `TestValidate` | Bulk SHACL validation, `--verify` integrity checks |
| `TestSchema` | JSON Schema generation, content assertions |
| `TestInit` | Project scaffolding, template substitution, init-sign-shacl roundtrip |
| `TestDiff` | Identical files, different profiles, compound separation, identity block, severity breakdown, description passthrough, minimal profile fallback |
| `TestPacks` | Pack listing, pack detail, missing pack error |
| `TestGlobalFlags` | `--repo-root`, `--no-color`, `--pack` |
| `TestStarterExamples` | Starter files conform to SHACL |
| `TestImport` | Excel import: starter file, sign, factor standards, default output path, schema emit |
| `TestEndToEnd` | Complete workflow: init → sign → shacl → verify |

### Key test patterns

- **Return code assertions:** `assert result.returncode == 0` for pass, `!= 0` for fail
- **Output substring checks:** `assert "Conforms" in result.stdout`
- **Temp file fixtures:** Tests that create custom JSON-LD use `tmp_path` (pytest built-in)
- **Java gating:** `@pytest.mark.skipif(not JAVA_AVAILABLE, reason="Java not available")`
- **Roundtrip tests:** Create → sign → verify → shacl to test the full flow

---

# Part 3 — Contributing

## Adding a New Subcommand

1. **Create the module** at `src/uofa_cli/commands/mycommand.py`:

```python
"""uofa mycommand — brief description."""

from pathlib import Path
from uofa_cli.output import header, info, result_line

HELP = "brief description for argparse"

def add_arguments(parser):
    parser.add_argument("file", type=Path, help="input file")
    # add more arguments as needed

def run(args) -> int:
    # implement the command
    return 0  # 0 = success, non-zero = failure
```

2. **Register it** in `cli.py`:

```python
from uofa_cli.commands import ..., mycommand

modules = {
    ...,
    "mycommand": mycommand,
}
```

3. **Add integration tests** in `tests/test_integration.py`:

```python
class TestMyCommand:
    def test_basic_usage(self):
        result = run_uofa("mycommand", str(MORRISON))
        assert result.returncode == 0
        assert "expected output" in result.stdout

    def test_missing_file_fails(self):
        result = run_uofa("mycommand", "/nonexistent/file.jsonld")
        assert result.returncode != 0
```

4. **Reinstall** the package so the new module is importable:

```bash
pip install -e .
```

5. **Run the full test suite** to verify nothing broke:

```bash
pytest tests/ -v
```

## Adding a New Weakener Rule

Weakener rules are defined in Jena rule syntax in `.rules` files. The
core rules live at `packs/core/rules/uofa_weakener.rules`.

1. **Add the rule** to the `.rules` file:

```
[my_rule:
    (?uofa rdf:type uofa:UnitOfAssurance)
    (?uofa uofa:someProperty ?value)
    # condition that triggers the weakener
    makeSkolem(?ann, ?uofa, 'W-XX-01', ?value)
    ->
    (?ann rdf:type uofa:WeakenerAnnotation)
    (?ann uofa:patternId 'W-XX-01')
    (?ann uofa:severity 'High')
    (?ann uofa:affectedNode ?value)
    (?ann schema:description 'Human-readable explanation of why this fires.')
    (?uofa uofa:hasWeakener ?ann)
]
```

Always include a `schema:description` triple — the `uofa diff` command
reads it to generate divergence explanations.

2. **Update the SHACL patternId regex** if your pattern ID uses a new
   category prefix. Edit `spec/schemas/uofa_shacl.ttl`:

```turtle
sh:pattern "^(W-(EP|AL|ON|AR|SI|XX)-\\d{2}|COMPOUND-\\d{2})$" ;
```

3. **Regenerate the JSON Schema** so it stays in sync:

```bash
uofa schema
```

4. **Re-sign any example files** whose weakener arrays you modified:

```bash
uofa sign packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld --key keys/research.key
```

5. **Run the full test suite:**

```bash
pytest tests/ -v
```

> **For Phase 2.5 catalog rule changes** (rule-tightening on the
> existing weakener catalog), see [`phase2_runbook.md`](phase2_runbook.md)
> for the metric-gated refinement loop and target zone semantics.

## Modifying the SHACL Schema

The SHACL shapes at `packs/core/shapes/uofa_shacl.ttl` define what
fields are required, their types, and allowed values. If you need to
add a new field to the UofA vocabulary:

1. **Add the property mapping** to `spec/context/v0.5.jsonld`:

```json
"myNewField": {"@id": "uofa:myNewField", "@type": "xsd:string"}
```

2. **Add the SHACL constraint** to the appropriate body shape in
   `uofa_shacl.ttl`:

```turtle
sh:property [
    sh:path uofa:myNewField ;
    sh:datatype xsd:string ;
    sh:minCount 1 ;         # if required
    sh:message "Helpful message if validation fails." ;
] ;
```

3. **Regenerate JSON Schema:**

```bash
uofa schema
```

4. **Update example files** if they need the new field, then re-sign.

5. **Run validation to verify:**

```bash
uofa validate
pytest tests/ -v
```

## CI and Dev Environment

### GitHub Actions

`.github/workflows/validate.yml` runs on every push and PR. It builds
the devcontainer and executes:
- `pytest tests/test_integration.py -v`
- `uofa validate --verify`
- `uofa check packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld`

### Dev Container / Codespaces

`.devcontainer/devcontainer.json` configures a Python 3.11 + Java 17 +
Maven environment. On creation it runs:
```bash
pip install -e '.[test]' && cd src/weakener-engine && mvn package -q
```

This means GitHub Codespaces users get a fully working environment
with zero setup.

### Local Development

```bash
# Python only (no Java needed for most work)
pip install -e '.[test]'
pytest tests/ -v

# Full stack (includes Jena rule engine)
pip install -e '.[test]'
cd src/weakener-engine && mvn package -q && cd ..
pytest tests/ -v
```

Tests that require Java are gated with
`@pytest.mark.skipif(not JAVA_AVAILABLE, ...)` so the test suite passes
without Java installed.

## Key Design Decisions

**JSON-LD as plain JSON.** The CLI treats JSON-LD files as plain JSON
(parsed with `json.load()`), not as RDF graphs. Only the Jena rule
engine and pyshacl interpret the RDF semantics. This keeps the Python
code simple and fast.

**SHACL as single source of truth.** All validation constraints are
defined in SHACL. The JSON Schema is generated from SHACL and should
never be edited directly. This avoids drift between the two.

**Pattern-agnostic diff.** The `diff` command and `explain.py` module
contain zero pattern-specific logic. Divergence explanations come from
the `description` field on `WeakenerAnnotation` objects, which are
emitted by the rule engine. New rules automatically get meaningful
diff output by including a `schema:description` triple.

**Subprocess for Java.** The Jena rule engine runs as a Java
subprocess, not via py4j or similar bridges. This keeps the dependency
boundary clean — Java is only needed for C3 and can be skipped
entirely via `--skip-rules`.

**Convention-based rules discovery.** The `rules_file()` function
searches for `uofa_weakener.rules` next to the input file, then one
directory up, then falls back to the active pack's rules. This lets
projects carry their own rules without CLI changes.

**Domain pack architecture.** SHACL shapes, Jena rules, templates, and
prompts are organized into domain packs under `packs/`. The `core`
pack provides base, pack-agnostic shapes. Two standards-specific packs
ship with v0.4: `vv40` (ASME V&V 40, with its 13 credibility factor
types) and `nasa-7009b` (NASA-STD-7009B). Standard-specific
constraints such as the `factorType` enum are defined in the pack's
own SHACL shapes rather than in core. Additional domain packs can be
added by dropping into `packs/` following the same convention. Each
pack has a `pack.json` manifest that the CLI reads to discover assets.
The `--pack` global flag switches between packs, and multi-pack
support allows combining constraints from several packs in a single
validation run. See `packs/README.md` for the full pack contract.
