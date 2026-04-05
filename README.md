# Unit of Assurance (UofA) — v0.4

![validate examples](https://github.com/cloudronin/uofa/actions/workflows/validate.yml/badge.svg)

The **Unit of Assurance** is the smallest independently verifiable bundle of credibility evidence for computational modeling and simulation (CM&S). It packages the **credibility decision** — who judged what, against what criteria, using what evidence, with what result — as a signed, provenance-linked, machine-verifiable engineering artifact.

## Quick Start: Create Your Own UofA

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/cloudronin/uofa?quickstart=1)

**No install required** — click the button above to open a ready-to-use environment with Python, Java, and the `uofa` CLI pre-installed.

Or run locally:

```bash
# 1. Install the uofa CLI
pip install -e '.[excel]'

# 2. Import from Excel (fastest on-ramp for practitioners)
uofa import my-assessment.xlsx --sign --key keys/research.key --check

# — OR — scaffold from a JSON-LD template
uofa init my-project
# Edit my-project/my-project-cou1.jsonld — fill in your project details
uofa sign my-project/my-project-cou1.jsonld --key my-project/keys/my-project.key
uofa check my-project/my-project-cou1.jsonld
```

**New to UofA?** See the [Getting Started Guide](docs/getting-started.md) for a step-by-step walkthrough, or study the [Morrison demo](#live-demo-morrison-blood-pump-fda-vv-40-case-study) below.

---

## Why UofA?

UofA exists because the credibility frameworks are not the problem. ASME V&V 40, NASA-STD-7009B, and the FDA's 2023 guidance on CM&S credibility provide clear instructions for *how to assess* simulation credibility. The problem is the **last mile**: there is no standardized construct for packaging, transmitting, and verifying the *evidence and decisions* those assessments produce.

The result is predictable. Credibility decisions live in prose PDFs. Evidence is scattered across tools. Provenance is partial. Audit packaging is manual. And reviewers catch quality gaps by intuition rather than automation.

UofA addresses this through three contributions:

| Contribution | What it does | Mechanism |
|---|---|---|
| **C1 — Decision as artifact** | Captures the credibility decision as a portable, tool-independent object with provenance lineage and integrity guarantees | JSON-LD + PROV-DM + SHA-256 hash + ed25519 digital signatures |
| **C2 — Completeness enforcement** | Defines what a UofA must contain at each rigor level and enforces it as a computable constraint | SHACL profiles (Minimal / Complete) with format-validated integrity fields |
| **C3 — Quality gates** | Detects substantive credibility gaps — missing UQ, orphan claims, acceptance criteria gaps — including compound risks that no individual query can find | Jena forward-chaining rule engine with compound inference |

---

## Live Demo: Morrison Blood Pump (FDA V&V 40 Case Study)

The `examples/morrison/` directory contains complete, working UofA evidence packages built from [Morrison et al. (2019)](https://doi.org/10.1097/MAT.0000000000000996) — an FDA OSEL co-authored V&V 40 credibility assessment for a centrifugal blood pump. This is the most widely cited V&V 40 worked example.

**What the demo shows:**

```
Morrison prose assessment          →  UofA structured evidence package
  "model deemed credible"               JSON-LD with 13 V&V 40 factors,
  scattered across 10 pages              provenance chain, integrity hash,
  of journal article                     machine-verifiable in 30 seconds
```

**Run it yourself:**

```bash
pip install -e .    # one-time setup (installs uofa CLI + all Python dependencies)

# Run the full C1 + C2 + C3 pipeline in one command
uofa check examples/morrison/cou1/uofa-morrison-cou1.jsonld --build
```

That single command runs three checks:

| Step | Command | What it does |
|---|---|---|
| C2 | `uofa shacl FILE` | SHACL Complete profile validation — all required fields present |
| C1 | `uofa verify FILE` | SHA-256 hash + ed25519 signature verification — content untampered |
| C3 | `uofa rules FILE` | Jena rule engine — 13 forward-chaining rules detect quality gaps |

The Jena JAR auto-builds on first run with `--build` (requires Java 17+ and Maven 3.8+).

**What the rule engine finds (14 weakeners across 6 patterns on COU1):**

| Pattern | Severity | Hits | What it detects |
|---|---|---|---|
| W-EP-01 | Critical | 1 | Orphan claim — no evidence chain to supporting data |
| W-EP-02 | High | 3 | Broken provenance — validation results with no generation activity |
| W-AL-01 | High | 3 | Missing uncertainty quantification on validation results |
| W-AR-05 | High | 3 | Comparator absence — results not linked to reference entities |
| ⚡ COMPOUND-01 | Critical | 3 | Risk escalation — Critical + High weakeners coexist on same UofA |
| ⚡ COMPOUND-03 | High | 1 | Assurance level override — declared "Medium" but Critical gaps exist |

The ⚡ compound rules fire on the output of the core rules — this is chained forward-chaining inference that standalone SPARQL queries cannot produce. Same model, same data, same rules: the rule engine reasons about the *interactions* between gaps, not just the gaps themselves.

---

## COU Divergence: `uofa diff`

Morrison contains two Contexts of Use assessing the same CFD model:

- **COU1** (CPB, Class II, Model Risk Level 2) → Decision: **Accepted**
- **COU2** (VAD, Class III, Model Risk Level 5) → Decision: **Not accepted**

Same model. Same experimental data. Different credibility requirements driven by different model risk. The `uofa diff` command surfaces this divergence automatically:

```bash
uofa diff examples/morrison/cou1/uofa-morrison-cou1.jsonld \
         examples/morrison/cou2/uofa-morrison-cou2.jsonld
```

```
════════════════════════════════════════════════════════
  COU Divergence Analysis
════════════════════════════════════════════════════════

                      COU A                             COU B
                Name  COU1: Cardiopulmonary bypass use (Class II)  COU2: Ventricular assist device use (Class III)
        Device class  Class II                          Class III
    Model risk level  MRL 2                             MRL 5
            Decision  Accepted                          Not accepted
     Assurance level  Medium                            Low
           Weakeners  6                                 1

══ Weakener Patterns (5) ══
  ┌────────────────────────────────────────────────────────────────┐
  │   Pattern    │  Severity  │  COU A  │  COU B  │    Status    │
  ├──────────────┼────────────┼─────────┼─────────┼──────────────┤
  │ W-AL-01      │ [High]     │   ✓     │   ✗     │ ◆ divergent  │
  │ W-AR-05      │ [High]     │   ✓     │   ✗     │ ◆ divergent  │
  │ W-EP-01      │ [Critical] │   ✓     │   ✗     │ ◆ divergent  │
  │ W-EP-02      │ [High]     │   ✓     │   ✗     │ ◆ divergent  │
  │ W-EP-04      │ [High]     │   ✗     │   ✓     │ ◆ divergent  │
  └──────────────┴────────────┴─────────┴─────────┴──────────────┘

══ Compound Patterns (2) ══
  ┌────────────────────────────────────────────────────────────────┐
  │   Pattern    │  Severity  │  COU A  │  COU B  │    Status    │
  ├──────────────┼────────────┼─────────┼─────────┼──────────────┤
  │ COMPOUND-01  │ [Critical] │   ✓     │   ✗     │ ◆ divergent  │
  │ COMPOUND-03  │ [High]     │   ✓     │   ✗     │ ◆ divergent  │
  └──────────────┴────────────┴─────────┴─────────┴──────────────┘

══ Summary ══
  COU A (COU1: Cardiopulmonary bypass use (Class II)):
    [Critical] 2
    [High] 4
  COU B (COU2: Ventricular assist device use (Class III)):
    [High] 1

  7 divergence(s) detected

══ Divergence Explanations ══

  [High] W-AL-01 — only in COU A
    COU1: Validation result has no uncertainty quantification —
    aleatory uncertainty is uncharacterized.
    COU2: pattern does not fire.

  [High] W-EP-04 — only in COU B
    COU2: Credibility factor is not assessed but model risk level
    exceeds 2 — unassessed factors at elevated risk weaken the
    credibility argument.
    COU1: pattern does not fire.
```

The output has four sections: **identity block** (side-by-side COU metadata), **weakener profile table** (✓/✗ presence with divergence markers), **summary counts** (per-severity breakdown), and **divergence explanations** (from the `description` field on each WeakenerAnnotation — generated by the rule engine, not hardcoded in the diff command).

Compound patterns (COMPOUND-*) are separated into their own sub-table when present, since they fire on the output of Level 1 rules.

This divergence is invisible in the prose paper. It becomes machine-visible in the UofA. That's C1: the credibility *decision* — not just the evidence — captured as a first-class artifact.

---

## Standards Alignment

UofA is grounded in existing standards rather than inventing new ones:

- **ASME V&V 40-2018** — Credibility factors, model risk framework, and the Context of Use (COU) concept that drives per-factor assessment
- **FDA 2023 Final Guidance on CM&S Credibility** — Regulatory expectations for credibility evidence in medical device submissions
- **NASA-STD-7009B** — CMS credibility assessment standard for models and simulations
- **W3C PROV-DM / PROV-O** — Provenance data model for artifact lineage
- **W3C SHACL** — Shapes Constraint Language for RDF graph validation
- **JSON-LD 1.1** — Linked data serialization that stays human-readable

---

## Integrity Verification

Every UofA carries a real cryptographic hash and digital signature — not placeholders.

| Level | What it checks | Mechanism |
|---|---|---|
| **Format gate** | Hash and signature are well-formed | SHACL `sh:pattern` regex on both Minimal and Complete profiles |
| **Content verification** | Hash matches the canonical document content | `uofa verify` recomputes SHA-256 from JSON canonical form |
| **Cryptographic signature** | Document was signed by the declared authority | ed25519 signature verification against the repo public key |

```bash
# Mint a sealed UofA (sign after edits)
uofa sign examples/morrison/cou1/uofa-morrison-cou1.jsonld --key keys/research.key

# Verify integrity
uofa verify examples/morrison/cou1/uofa-morrison-cou1.jsonld
```

Placeholder strings (e.g., `sha256:placeholder...`) now **fail** SHACL validation. This is deliberate — a UofA claiming ProfileComplete must carry a real hash.

---

## The Jena Rule Engine (C3)

Quality gap detection uses [Apache Jena](https://jena.apache.org/) forward-chaining rules, not just SPARQL queries. The rule engine operates in two levels:

**Level 1 — Core detection rules** match structural patterns against the evidence graph:

| Rule | Category | What it detects |
|---|---|---|
| W-EP-01 | Epistemic | Claim with no provenance chain to evidence |
| W-EP-02 | Epistemic | Validation result with no generation activity |
| W-EP-04 | Epistemic | Unassessed credibility factor at elevated model risk (MRL > 2) |
| W-AL-01 | Aleatory | Validation result with no uncertainty quantification |
| W-AR-01 | Argument (D1) | Credibility factor with no acceptance criteria |
| W-AR-02 | Argument (D2) | Decision "Accepted" but achievedLevel < requiredLevel |
| W-AR-05 | Argument (D5) | Validation result with no comparator linkage |
| W-SI-01 | Structural | Missing digital signature |
| W-SI-02 | Structural | Missing required profile bindings |

**Level 2 — Compound inference rules** fire on Level 1 output:

| Rule | What it detects |
|---|---|
| COMPOUND-01 | Critical + High weakeners coexist → escalated compound risk |
| COMPOUND-03 | Declared assurance level contradicts detected Critical gaps |

The compound rules are the key differentiator versus SPARQL. They reason about the *interactions* between gaps — something that requires chained forward-chaining inference. The RETE algorithm ensures only affected rules re-fire when new triples are added.

---

## Profiles

UofA uses a two-tier profile system. **Minimal** captures the bare evidence package. **Complete** adds the full credibility assessment.

### Minimal Profile

The minimum viable UofA. Suitable for evidence capture during live pipeline execution or as a lightweight audit artifact.

| Property | Type | Purpose |
|---|---|---|
| `bindsRequirement` | IRI | The requirement this UofA substantiates |
| `hasContextOfUse` | IRI | The V&V 40 Context of Use for this assessment |
| `hasValidationResult` | IRI | At least one validation result |
| `hasDecisionRecord` | IRI | The credibility decision (accepted/rejected + rationale) |
| `generatedAtTime` | xsd:dateTime | When this UofA was created |
| `hash` | string | Content hash (format-validated: `sha256:<64 hex chars>`) |
| `signature` | string | Digital signature (format-validated: `ed25519:<hex>`) |

### Complete Profile

Extends Minimal with full V&V 40 credibility assessment, provenance chain, and quality metrics. Required for regulatory submissions and formal credibility arguments.

Everything in Minimal, plus:

| Property | Type | Purpose |
|---|---|---|
| `bindsModel` | IRI | The computational model assessed |
| `bindsDataset` | IRI | The dataset(s) used in validation |
| `wasDerivedFrom` | IRI | Provenance link to parent artifact |
| `wasAttributedTo` | IRI | Responsible actor or organization |
| `hasCredibilityFactor` | CredibilityFactor[] | Per-factor assessment (V&V 40 Table 5-1) |
| `hasWeakener` | WeakenerAnnotation[] | *(optional)* Detected quality gaps |
| `credibilityIndex` | xsd:decimal [0–1] | Overall credibility score |
| `traceCompleteness` | xsd:decimal [0–1] | Provenance chain completeness |
| `verificationCoverage` | xsd:decimal [0–1] | Verification evidence coverage |
| `validationCoverage` | xsd:decimal [0–1] | Validation evidence coverage |
| `uncertaintyCIWidth` | xsd:decimal [≥0] | Uncertainty confidence interval width |
| `assuranceLevel` | string | `Low` / `Medium` / `High` |
| `criteriaSet` | IRI | Reference criteria set (e.g., `ASME-VV40-2018`) |

### CredibilityFactor

Each factor maps to one row in V&V 40 Table 5-1 or NASA-STD-7009B:

| Property | Constraint | Purpose |
|---|---|---|
| `factorType` | Factor name from the active pack's taxonomy | Which credibility factor is being assessed |
| `factorStandard` | String (e.g., `"ASME-VV40-2018"`, `"NASA-STD-7009B"`) | Which standard defines this factor |
| `assessmentPhase` | `"capability"` or `"results"` *(NASA-STD-7009B only)* | NASA CAS assessment phase |
| `requiredLevel` | Integer (1–5 for V&V 40, 0–4 for NASA-7009B) | Target credibility level for this COU |
| `achievedLevel` | Integer (1–5 for V&V 40, 0–4 for NASA-7009B) | Actual credibility level achieved |
| `hasEvidence` | IRI or IRI[] *(optional)* | Links to backing evidence entities |

### WeakenerAnnotation

Quality gap annotations detected by the Jena rule engine (C3). Optional — a UofA with zero weakeners is valid (and desirable).

| Property | Constraint | Purpose |
|---|---|---|
| `patternId` | Format: `W-XX-NN` or `COMPOUND-NN` | Catalog ID from the weakener pattern taxonomy |
| `severity` | `Critical` / `High` / `Medium` / `Low` | Impact severity |
| `affectedNode` | IRI | The specific graph node flagged by this pattern |
| `description` | string *(optional)* | Human-readable explanation of why this weakener fires |

---

## Working with Your Own UofA

The `uofa` CLI provides commands for every step of the workflow:

```bash
# Import from a practitioner-filled Excel workbook (fastest on-ramp)
uofa import assessment.xlsx --sign --key keys/your.key --check

# Full pipeline (C1 + C2 + C3) on your file
uofa check path/to/your-uofa.jsonld

# Individual steps
uofa shacl  path/to/your-uofa.jsonld           # C2: SHACL validation
uofa verify path/to/your-uofa.jsonld           # C1: Hash + signature check
uofa rules  path/to/your-uofa.jsonld           # C3: Jena weakener detection

# Sign with your own key
uofa sign path/to/your-uofa.jsonld --key keys/your.key

# Scaffold a new project from a JSON-LD template
uofa init my-new-project

# Validate all examples in the repo
uofa validate

# Compare weakener profiles across two COUs
uofa diff uofa-cou1.jsonld uofa-cou2.jsonld

# List installed domain packs
uofa packs

# Use a specific domain pack
uofa check path/to/your-uofa.jsonld --pack vv40

# Use multiple packs (e.g., V&V 40 + NASA-STD-7009B)
uofa check path/to/your-uofa.jsonld --pack vv40 --pack nasa-7009b

# Migrate a v0.3 file to v0.4
uofa migrate path/to/old-file.jsonld

# Generate import constants from SHACL (after schema changes)
uofa schema --emit python
```

See the [Getting Started Guide](docs/getting-started.md) for a full walkthrough.

---

## Domain Packs

SHACL shapes, Jena rules, templates, and extraction prompts are organized into **domain packs** under `packs/`. The `core` pack ships with standards-agnostic credibility assessment rules (12 weakener patterns). The `vv40` pack provides the ASME V&V 40-2018 factor taxonomy (13 factors), and the `nasa-7009b` pack provides the NASA-STD-7009B factor taxonomy (19 factors, including 6 NASA-only lifecycle factors).

```bash
$ uofa packs
Installed packs:
  core         v0.4.0   Core credibility assessment rules.               (any factors, 12 patterns) [always loaded]
  nasa-7009b   v0.4.0   NASA-STD-7009B credibility assessment factors... (19 factors, 6 patterns)
  vv40         v0.4.0   ASME V&V 40-2018 credibility factor taxonomy...  (13 factors, 0 patterns)   [active]
```

The `--pack` flag on any command switches the active pack(s). Multiple packs can be specified to combine factor taxonomies and rules. The default is `--pack vv40` for backward compatibility. Per-project rules files next to the input file still take precedence over the pack default. See [`packs/README.md`](packs/README.md) for the full pack contract and instructions for creating domain packs.

---

## Excel Import: The Practitioner On-Ramp

Simulation engineers fill an Excel workbook, run one command, and get a signed, validated JSON-LD evidence package. The import pipeline handles URI generation, factor standard assignment, provenance tracking, and optional signing + validation in a single invocation.

```bash
pip install -e '.[excel]'    # one-time: adds openpyxl dependency

# Import from Excel → JSON-LD, sign, and validate in one step
uofa import my-assessment.xlsx --sign --key keys/research.key --check --pack vv40
```

The Excel template has 5 sheets: **Assessment Summary**, **Model & Data**, **Validation Results**, **Credibility Factors**, and **Decision**. Each pack provides a pre-populated template with locked factor names and dropdown validation. See `examples/starters/uofa-starter-filled.xlsx` for a complete filled example.

| Feature | Detail |
|---|---|
| **VV40 support** | 13 V&V 40 factors, levels 1-5, `factorStandard: "ASME-VV40-2018"` |
| **NASA-STD-7009B** | 19 factors (13 shared + 6 NASA-only), levels 0-4, `assessmentPhase` auto-assigned |
| **Evidence types** | `ValidationResult`, `ReviewActivity`, `ProcessAttestation`, `DeploymentRecord`, `InputPedigreeLink` |
| **Provenance** | `ImportActivity` entry with timestamp, source file, and tool version |
| **Error messages** | Sheet name + cell reference (e.g., `[Credibility Factors!C7] Required Level must be 1-5`) |
| **SHACL-synced** | Factor names, level ranges, and enums are generated from SHACL shapes via `uofa schema --emit python` |

---

## Prerequisites

**Zero-install option:** [Open in GitHub Codespaces](https://codespaces.new/cloudronin/uofa?quickstart=1) — everything is pre-installed.

**Local install:**

```bash
pip install -e '.[excel]'   # installs uofa CLI + all Python deps + openpyxl for Excel import
```

| Tool | Version | Purpose |
|---|---|---|
| Python 3.10+ | Installed via `pip install -e .` | SHACL validation + integrity verification |
| openpyxl | Installed via `pip install -e '.[excel]'` | Excel import (`uofa import`) |
| Java 17+ | OpenJDK or equivalent | Jena rule engine (C3 only) |
| Maven 3.8+ | `mvn package` | Build the Jena fat JAR (C3 only) |

Java and Maven are only required for the Jena rule engine (C3). Use `uofa check FILE --skip-rules` if Java is not available. openpyxl is only required for `uofa import`; all other commands work without it.

---

## Architecture: One UofA per Context of Use

The v0.3 architecture models credibility assessment at the **COU level**, not the individual factor level. Each UofA packages the complete credibility decision for one Context of Use — including all per-factor assessments as embedded CredibilityFactor nodes and any detected quality gaps as WeakenerAnnotation nodes.

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
│   ├── hasWeakener        → [W-EP-01, W-EP-02, W-AL-01, W-AR-05] + compounds
│   ├── hasDecisionRecord  → "Accepted for COU1"
│   ├── hash               → sha256:<real hash>
│   ├── signature          → ed25519:<real signature>
│   └── wasDerivedFrom     → Morrison DOI
│
└── morrison/cou2/uofa-morrison-cou2.jsonld (ProfileComplete)
    COU2: VAD Use (Class III) — Model Risk Level 5
    ├── hasCredibilityFactor → [13 V&V 40 factors: 7 assessed + 6 not-assessed]
    ├── hasWeakener        → [W-EP-04 (6×)]
    └── W-AL-01 does NOT fire — COU2 has UQ; W-EP-04 fires 6× on not-assessed factors
```

Shared entities (model, datasets, pump geometry) are referenced by IRI, not duplicated. The divergence between COU1 and COU2 weakener profiles is the central analytical demonstration.

---

## Research Context

UofA is the subject of a Doctor of Engineering praxis at George Washington University. The evaluation uses two FDA case studies:

- **Tier 1 (Retrospective):** Morrison et al. (2019) — FDA generic centrifugal blood pump V&V 40 credibility assessment. Re-expressed as UofA evidence packages with real cryptographic integrity. Full 13-factor assessment (7 assessed, 6 not-assessed) with risk-driven divergence: COU1 (MRL 2) passes cleanly while COU2 (MRL 5) triggers 6 epistemic gap weakeners (W-EP-04) on unassessed factors.
- **Tier 2 (Prospective):** FDA VICTRE pipeline — live computational workflow instrumented to generate UofAs during execution rather than from retrospective documents.
- **Tier 3 (Exploratory):** Multi-component stress test on VICTRE — simulates change events to test continuous re-issuance and hierarchical credibility composition.

Early findings will be presented at [NAFEMS Americas 2026](https://www.nafems.org/events/nafems/2026/nafems-americas-conference/) (May 27–29, St. Charles, MO).

---

## Design Principles

| Principle | Meaning |
|---|---|
| **Minimal** | Small JSON-LD document, human-readable, one file per COU |
| **Semantic** | Aligns with PROV-O, V&V 40, and domain ontologies |
| **Verifiable** | Real SHA-256 hashes + ed25519 signatures + SHACL validation |
| **Composable** | UofAs form nodes in system-level assurance graphs via `wasDerivedFrom` |
| **Tool-agnostic** | Works with any simulation tool, MBSE platform, or ML pipeline |
| **Hide the plumbing** | Practitioners see completeness reports and gap alerts, not triples and SPARQL |

---

## License

CC0 1.0 — public domain, no restrictions.

The UofA ontology, JSON-LD context, SHACL shapes, and reference examples are open. The Jena rule implementations (compound inference rules, domain-specific composition rules) are proprietary.

---

## Contributing

Contributions are welcome, especially real-world UofA examples from practitioners working with CM&S credibility assessment. If you are preparing a CM&S-supported regulatory submission and want to explore UofA packaging for your evidence, please reach out.

For contributors looking to add features or fix bugs, see the [Architecture & Contributor Guide](docs/architecture.md) — it covers the CLI design, subcommand patterns, test structure, and step-by-step instructions for adding new commands, weakener rules, and schema changes.

**Website:** [crediblesimulation.com](https://crediblesimulation.com)