# UofA CLI — Architecture & Contributor Guide

This document covers the architecture, design patterns, and conventions used across the UofA CLI. It is intended for contributors who want to understand the codebase and add new features.

---

## High-Level Overview

The UofA CLI implements three validation pipelines for credibility evidence packages:

| Pipeline | Label | What it checks | Mechanism |
|---|---|---|---|
| **C1** | Integrity | Content hasn't been tampered with | SHA-256 hash + ed25519 digital signature |
| **C2** | Completeness | Required fields are present and well-formed | SHACL shapes (pyshacl) |
| **C3** | Quality gates | Substantive credibility gaps | Apache Jena forward-chaining rules (Java subprocess) |

The CLI is a Python package (`uofa_cli`) with 10 subcommands, a set of core modules for cryptography and formatting, and a Java backend for the rule engine.

```
                      uofa <command>
                            │
              ┌─────────────┼─────────────────┐
              │             │                 │
         Pure Python    Python + Java     Utility
         ┌────────┐    ┌───────────┐    ┌─────────┐
         │ sign   │    │ rules     │    │ init    │
         │ verify │    │ check     │    │ keygen  │
         │ shacl  │    │           │    │ schema  │
         │ diff   │    │           │    │ validate│
         └────────┘    └───────────┘    └─────────┘
```

---

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
  commands/               # one module per subcommand
    check.py              # full C1+C2+C3 pipeline
    diff.py               # COU divergence analysis
    init.py               # scaffold new projects
    keygen.py             # generate ed25519 keypair
    packs.py              # list and inspect installed domain packs
    rules.py              # Jena rule engine (C3)
    schema.py             # generate JSON Schema from SHACL
    shacl.py              # SHACL validation (C2)
    sign.py               # sign UofA files
    validate.py           # bulk validate all examples
    verify.py             # verify hash + signature (C1)

packs/
  core/                   # Base V&V 40 domain pack
    pack.json             # Pack manifest (name, version, shapes, rules, etc.)
    shapes/
      uofa_shacl.ttl      # SHACL shapes — single source of truth for validation
    rules/
      uofa_weakener.rules # Jena forward-chaining rules (13 patterns)
    templates/            # (populated when uofa import ships)
    prompts/              # (populated when uofa extract ships)
  README.md               # How to create a domain pack

spec/
  context/v0.3.jsonld     # JSON-LD vocabulary context (@vocab, property mappings)
  schemas/
    uofa_shacl.ttl        # SYMLINK → ../../packs/core/shapes/uofa_shacl.ttl
    uofa.schema.json      # JSON Schema — generated from SHACL via `uofa schema`

examples/
  morrison/               # Reference Morrison blood pump case study
    uofa_weakener.rules   # SYMLINK → ../../packs/core/rules/uofa_weakener.rules
    cou1/                 # COU1: CPB use (Class II, Accepted)
    cou2/                 # COU2: VAD use (Class III, Not accepted)
  templates/              # Skeleton files used by `uofa init`
  starters/               # Real-world starter examples

weakener-engine/          # Java Jena rule engine
  pom.xml                 # Maven config (Jena 5.3, picocli)
  src/main/java/.../
    WeakenerEngine.java   # CLI entry point — loads JSON-LD, runs rules, outputs report

tests/
  test_integration.py     # integration tests covering all subcommands
  test_explain.py         # unit tests for divergence explanation module
```

---

## Subcommand Module Contract

Every subcommand in `src/uofa_cli/commands/` exports exactly three things:

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

---

## Subcommand Reference

### `uofa keygen <path>`

Generates an ed25519 keypair. Creates `<path>` (private key, PEM PKCS8) and `<path>.pub` (public key, PEM SubjectPublicKeyInfo). Parent directories are created automatically.

### `uofa sign <file> --key <key>`

Signs a UofA JSON-LD file. Process: load JSON-LD, resolve `@context`, strip integrity fields (`hash`, `signature`, `signatureAlg`, `canonicalizationAlg`), canonicalize (sorted-key JSON, UTF-8), compute SHA-256, sign with ed25519, inject integrity fields back, write file.

Optional: `--context` for external context file, `--output` for separate output path.

### `uofa verify <file>`

Verifies C1 integrity. Recomputes SHA-256 from canonical form and compares to declared `hash` field. Verifies `signature` against the public key. Returns 0 only if both match.

Optional: `--pubkey` (default: `keys/research.pub`).

### `uofa shacl <file>`

Runs C2 SHACL validation using pyshacl. Default mode translates violations into friendly messages with severity badges and fix suggestions. `--raw` shows raw pyshacl output.

The SHACL schema at `spec/schemas/uofa_shacl.ttl` defines a dispatcher shape that branches based on `conformsToProfile` to either `MinimalBody` or `CompleteBody` constraints.

### `uofa rules <file>`

Runs C3 quality gap detection via the Java Jena rule engine. Invokes `java -jar weakener-engine/target/uofa-weakener-engine-0.1.0.jar` as a subprocess. The engine loads JSON-LD into an RDF graph, applies forward-chaining rules in RETE mode, and reports detected `WeakenerAnnotation` triples.

`--build` auto-builds the JAR if missing. `--rules` overrides the default rules file. `--raw` shows uncolorized output. Requires Java 17+ and Maven 3.8+ (for building).

### `uofa check <file>`

Runs the full pipeline in order: C2 (SHACL) then C1 (integrity) then C3 (rules). Prints a summary with pass/fail for each step. `--skip-rules` omits C3 (no Java required). `--build` auto-builds the Jena JAR.

### `uofa validate`

Bulk validates all `*.jsonld` files under `examples/` against SHACL. Excludes `templates/` subdirectory. `--verify` additionally checks hash + signature integrity on each file (skips unsigned files with placeholder hashes). `--dir` overrides the scan directory.

### `uofa init <name>`

Scaffolds a new UofA project. Creates a directory with a template JSON-LD file (from `examples/templates/`), generates a keypair, and creates a `.gitignore`. `--profile minimal|complete` selects the template. `--dir` sets the parent directory.

### `uofa diff <file_a> <file_b>`

Compares weakener profiles between two UofA files. Outputs four sections:

1. **COU Identity Block** — side-by-side metadata (name, device class, MRL, decision, assurance level)
2. **Weakener Profile Table** — pattern presence grid with divergence markers. COMPOUND patterns get a separate sub-table.
3. **Summary Counts** — per-COU severity tier breakdown + total divergence count
4. **Divergence Explanations** — reads the `description` field from each divergent WeakenerAnnotation. Falls back to a generic message if no description is present.

The diff command is entirely pattern-agnostic — it works with any pattern IDs and does not hardcode rule-specific logic.

### `uofa packs [name]`

Lists installed domain packs or inspects a specific pack. Without arguments, shows all packs with version and description. With a pack name, shows full manifest details including shapes path, rules path, standards, and factor counts.

### `uofa schema`

Generates `spec/schemas/uofa.schema.json` from the SHACL shapes in the active pack. This ensures the JSON Schema stays in sync with the SHACL source of truth. Uses rdflib to parse Turtle and maps SHACL constraints to JSON Schema properties.

---

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

Canonicalization: `json.dumps(doc, sort_keys=True, ensure_ascii=False, separators=(',', ':'))`. This is a deterministic JSON canonical form, not RDFC-1.0 (despite the `canonicalizationAlg` field in the document).

### `paths.py` — Asset discovery and pack resolution

Finds the repo root by searching upward for the marker file `packs/core/pack.json` or `spec/schemas/uofa_shacl.ttl` (backward compat). All other paths are relative to this root. The root is cached globally after first discovery.

**Pack-aware resolution:** The `--pack` flag (default: `core`) sets the active pack via `set_active_pack()`. Asset functions like `shacl_schema()` and `rules_file()` read from the active pack's manifest (`pack.json`) to locate files. If the pack or manifest is missing, they fall back to the legacy hardcoded paths.

Key pattern: commands never hardcode paths. They call `paths.shacl_schema()`, `paths.jar_path()`, `paths.rules_file(input_path)`, etc.

The `rules_file()` function searches in order: same directory as the input file, then the parent directory, then the active pack's rules directory. This allows per-project rules files while falling back to the pack rules.

Additional pack functions:
- `pack_dir(name)` — returns the directory for a named pack
- `pack_manifest(name)` — loads and returns `pack.json` as a dict
- `list_packs()` — discovers all installed packs (directories under `packs/` with `pack.json`)
- `template_path()` / `extract_prompt()` — resolve template and prompt paths from the manifest

### `output.py` — Terminal formatting

ANSI color helpers, severity badges, and table rendering. Color is auto-detected from TTY status and can be disabled via `--no-color` or the `NO_COLOR` environment variable.

Table functions (`table_header`, `table_row`, `table_footer`, `table_separator`) use box-drawing characters and handle ANSI-aware column width padding.

### `shacl_friendly.py` — SHACL violation translator

Translates raw pyshacl violations into structured dicts with fields: `path` (friendly field name), `message`, `fix` (actionable suggestion), `severity` (Critical/High/Medium/Low). The fix suggestions and severity assignments are keyed on SHACL property URIs.

### `explain.py` — Divergence explanation

A single function, `explain_divergence()`, that reads the `description` field from a `WeakenerAnnotation` dict and formats it into explanation lines. Falls back to showing the `affectedNode` IRI if no description is present. No pattern-specific logic — the rule engine is the authority on *why* a weakener fires.

---

## The Java Rule Engine

The weakener engine at `weakener-engine/` is a Java CLI built with Apache Jena 5.3 and picocli. It is invoked as a subprocess from `rules.py`.

**Invocation:**
```
java -jar weakener-engine/target/uofa-weakener-engine-0.1.0.jar \
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

**Building:** `cd weakener-engine && mvn package -q` (requires Java 17+ and Maven 3.8+). The CLI's `--build` flag automates this.

---

## Spec Files and Schema Strategy

The SHACL shapes in `packs/core/shapes/uofa_shacl.ttl` are the **single source of truth** for validation constraints. A symlink at `spec/schemas/uofa_shacl.ttl` preserves backward compatibility. The JSON Schema at `spec/schemas/uofa.schema.json` is **generated** from SHACL via `uofa schema` and should never be edited by hand.

If you change a validation constraint:
1. Edit `packs/core/shapes/uofa_shacl.ttl`
2. Run `uofa schema` to regenerate the JSON Schema
3. Run `uofa validate` to verify all examples still conform

The JSON-LD context at `spec/context/v0.3.jsonld` defines the vocabulary mappings. It maps short property names (e.g., `patternId`) to full URIs (e.g., `uofa:patternId`). If you add a new property to the schema, you must also add its mapping here. The context is framework-level (not pack-specific) — all packs share the same vocabulary.

---

## Integration Tests

Tests live in `tests/test_integration.py` and `tests/test_explain.py`. Run them with:

```bash
pip install -e '.[test]'
pytest tests/ -v
```

### How tests work

All integration tests use the `run_uofa(*args)` helper, which invokes `python -m uofa_cli` as a subprocess and returns a `CompletedProcess` with `stdout`, `stderr`, and `returncode`. This tests the full CLI path including argument parsing and exit codes.

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
| `MORRISON` | `examples/morrison/cou1/uofa-morrison-cou1.jsonld` | Reference valid Complete profile (signed) |
| `MORRISON_COU2` | `examples/morrison/cou2/uofa-morrison-cou2.jsonld` | COU2 variant (different weakener profile) |
| `MINIMAL_TEMPLATE` | `examples/templates/uofa-minimal-skeleton.jsonld` | Minimal profile skeleton |
| `COMPLETE_TEMPLATE` | `examples/templates/uofa-complete-skeleton.jsonld` | Complete profile skeleton |
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
| `TestEndToEnd` | Complete workflow: init → sign → shacl → verify |

### Key test patterns

- **Return code assertions:** `assert result.returncode == 0` for pass, `!= 0` for fail
- **Output substring checks:** `assert "Conforms" in result.stdout`
- **Temp file fixtures:** Tests that create custom JSON-LD use `tmp_path` (pytest built-in)
- **Java gating:** `@pytest.mark.skipif(not JAVA_AVAILABLE, reason="Java not available")`
- **Roundtrip tests:** Create → sign → verify → shacl to test the full flow

---

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

---

## Adding a New Weakener Rule

Weakener rules are defined in Jena rule syntax in `.rules` files. The core rules live at `packs/core/rules/uofa_weakener.rules` (symlinked from `examples/morrison/uofa_weakener.rules` for backward compatibility).

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

Always include a `schema:description` triple — the `uofa diff` command reads it to generate divergence explanations.

2. **Update the SHACL patternId regex** if your pattern ID uses a new category prefix. Edit `spec/schemas/uofa_shacl.ttl`:

```turtle
sh:pattern "^(W-(EP|AL|ON|AR|SI|XX)-\\d{2}|COMPOUND-\\d{2})$" ;
```

3. **Regenerate the JSON Schema** so it stays in sync:

```bash
uofa schema
```

4. **Re-sign any example files** whose weakener arrays you modified:

```bash
uofa sign examples/morrison/cou1/uofa-morrison-cou1.jsonld --key keys/research.key
```

5. **Run the full test suite:**

```bash
pytest tests/ -v
```

---

## Modifying the SHACL Schema

The SHACL shapes at `packs/core/shapes/uofa_shacl.ttl` define what fields are required, their types, and allowed values. If you need to add a new field to the UofA vocabulary:

1. **Add the property mapping** to `spec/context/v0.3.jsonld`:

```json
"myNewField": {"@id": "uofa:myNewField", "@type": "xsd:string"}
```

2. **Add the SHACL constraint** to the appropriate body shape in `uofa_shacl.ttl`:

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

---

## CI and Dev Environment

### GitHub Actions

`.github/workflows/validate.yml` runs on every push and PR. It builds the devcontainer and executes:
- `pytest tests/test_integration.py -v`
- `uofa validate --verify`
- `uofa check examples/morrison/cou1/uofa-morrison-cou1.jsonld`

### Dev Container / Codespaces

`.devcontainer/devcontainer.json` configures a Python 3.11 + Java 17 + Maven environment. On creation it runs:
```bash
pip install -e '.[test]' && cd weakener-engine && mvn package -q
```

This means GitHub Codespaces users get a fully working environment with zero setup.

### Local Development

```bash
# Python only (no Java needed for most work)
pip install -e '.[test]'
pytest tests/ -v

# Full stack (includes Jena rule engine)
pip install -e '.[test]'
cd weakener-engine && mvn package -q && cd ..
pytest tests/ -v
```

Tests that require Java are gated with `@pytest.mark.skipif(not JAVA_AVAILABLE, ...)` so the test suite passes without Java installed.

---

## Key Design Decisions

**JSON-LD as plain JSON.** The CLI treats JSON-LD files as plain JSON (parsed with `json.load()`), not as RDF graphs. Only the Jena rule engine and pyshacl interpret the RDF semantics. This keeps the Python code simple and fast.

**SHACL as single source of truth.** All validation constraints are defined in SHACL. The JSON Schema is generated from SHACL and should never be edited directly. This avoids drift between the two.

**Pattern-agnostic diff.** The `diff` command and `explain.py` module contain zero pattern-specific logic. Divergence explanations come from the `description` field on `WeakenerAnnotation` objects, which are emitted by the rule engine. New rules automatically get meaningful diff output by including a `schema:description` triple.

**Subprocess for Java.** The Jena rule engine runs as a Java subprocess, not via py4j or similar bridges. This keeps the dependency boundary clean — Java is only needed for C3 and can be skipped entirely via `--skip-rules`.

**Convention-based rules discovery.** The `rules_file()` function searches for `uofa_weakener.rules` next to the input file, then one directory up, then falls back to the active pack's rules. This lets projects carry their own rules without CLI changes.

**Domain pack architecture.** SHACL shapes, Jena rules, templates, and prompts are organized into domain packs under `packs/`. The `core` pack ships with the base V&V 40 rules. Future domain packs (e.g., `cardio-cfd`, `ortho-fatigue`) drop into `packs/` following the same convention. Each pack has a `pack.json` manifest that the CLI reads to discover assets. The `--pack` global flag switches between packs. See `packs/README.md` for the full pack contract.
