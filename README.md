# Unit of Assurance (UofA) — v0.2

![validate examples](https://github.com/cloudronin/uofa/actions/workflows/validate.yml/badge.svg)

The **Unit of Assurance** is the smallest independently verifiable bundle of credibility evidence for computational modeling and simulation (CM&S). It packages the **credibility decision** — who judged what, against what criteria, using what evidence, with what result — as a signed, provenance-linked, machine-verifiable engineering artifact.

## Quick Start: Create Your Own UofA

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/cloudronin/uofa?quickstart=1)

**No install required** — click the button above to open a ready-to-use environment with Python, Java, and the `uofa` CLI pre-installed.

Or run locally:

```bash
# 1. Install the uofa CLI
pip install -e .

# 2. Scaffold a new project (creates template + keys)
uofa init my-project

# 3. Edit my-project/my-project-cou1.jsonld — fill in your project details

# 4. Sign your evidence package
uofa sign my-project/my-project-cou1.jsonld --key my-project/keys/my-project.key

# 5. Validate (C1 integrity + C2 SHACL + C3 rule engine)
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

The `examples/morrison-cou1/` directory contains a complete, working UofA evidence package built from [Morrison et al. (2019)](https://doi.org/10.1097/MAT.0000000000000996) — an FDA OSEL co-authored V&V 40 credibility assessment for a centrifugal blood pump. This is the most widely cited V&V 40 worked example.

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
uofa check examples/morrison-cou1/uofa-morrison-cou1.jsonld --build
```

That single command runs three checks:

| Step | Command | What it does |
|---|---|---|
| C2 | `uofa shacl FILE` | SHACL Complete profile validation — all required fields present |
| C1 | `uofa verify FILE` | SHA-256 hash + ed25519 signature verification — content untampered |
| C3 | `uofa rules FILE` | Jena rule engine — 12 forward-chaining rules detect quality gaps |

The Jena JAR auto-builds on first run with `--build` (requires Java 17+ and Maven 3.8+).

**What the rule engine finds (29 weakeners across 7 patterns):**

| Pattern | Severity | Hits | What it detects |
|---|---|---|---|
| W-EP-01 | Critical | 2 | Orphan claim — no evidence chain to supporting data |
| W-EP-02 | High | 3 | Broken provenance — validation results with no generation activity |
| W-AL-01 | High | 4 | Missing uncertainty quantification on validation results |
| W-AR-01 | Critical | 8 | No acceptance criteria — factor levels set but rationale not encoded |
| W-AR-05 | High | 4 | Comparator absence — results not linked to reference entities |
| ⚡ COMPOUND-01 | Critical | 6 | Risk escalation — Critical + High weakeners coexist on same UofA |
| ⚡ COMPOUND-03 | High | 2 | Assurance level override — declared "Medium" but Critical gaps exist |

The ⚡ compound rules fire on the output of the core rules — this is chained forward-chaining inference that standalone SPARQL queries cannot produce. Same model, same data, same rules: the rule engine reasons about the *interactions* between gaps, not just the gaps themselves.

---

## COU Divergence: The C1 Value Proposition

Morrison contains two Contexts of Use assessing the same CFD model:

- **COU1** (CPB, Class II, Model Risk Level 2) → Decision: **Accepted**
- **COU2** (VAD, Class III, Model Risk Level 5) → Decision: **Not accepted**

Same model. Same experimental data. Different credibility requirements driven by different model risk. The weakener pattern **W-AL-01 (Missing UQ) fires for COU1 but not COU2** — because COU2 includes Monte Carlo uncertainty quantification that COU1 does not.

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
uofa sign examples/morrison-cou1/uofa-morrison-cou1.jsonld --key keys/research.key

# Verify integrity
uofa verify examples/morrison-cou1/uofa-morrison-cou1.jsonld
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

Each factor maps to one row in V&V 40 Table 5-1:

| Property | Constraint | Purpose |
|---|---|---|
| `factorType` | One of 13 V&V 40 factor names | Which credibility factor is being assessed |
| `requiredLevel` | Integer 1–5 | Target credibility level for this COU |
| `achievedLevel` | Integer 1–5 | Actual credibility level achieved |

### WeakenerAnnotation

Quality gap annotations detected by the Jena rule engine (C3). Optional — a UofA with zero weakeners is valid (and desirable).

| Property | Constraint | Purpose |
|---|---|---|
| `patternId` | Format: `W-XX-NN` (e.g., `W-EP-01`) | Catalog ID from the weakener pattern taxonomy |
| `severity` | `Critical` / `High` / `Medium` / `Low` | Impact severity |
| `affectedNode` | IRI | The specific graph node flagged by this pattern |

---

## Working with Your Own UofA

The `uofa` CLI provides commands for every step of the workflow:

```bash
# Full pipeline (C1 + C2 + C3) on your file
uofa check path/to/your-uofa.jsonld

# Individual steps
uofa shacl  path/to/your-uofa.jsonld           # C2: SHACL validation
uofa verify path/to/your-uofa.jsonld           # C1: Hash + signature check
uofa rules  path/to/your-uofa.jsonld           # C3: Jena weakener detection

# Sign with your own key
uofa sign path/to/your-uofa.jsonld --key keys/your.key

# Scaffold a new project
uofa init my-new-project

# Validate all examples in the repo
uofa validate

# Compare weakener profiles across two COUs
uofa diff uofa-cou1.jsonld uofa-cou2.jsonld
```

See the [Getting Started Guide](docs/getting-started.md) for a full walkthrough.

---

## Repository Structure

```
pyproject.toml                   # pip install -e . (installs the uofa CLI)

src/uofa_cli/                    # uofa CLI package
  cli.py                         # argparse entry point + subcommand dispatch
  integrity.py                   # SHA-256 hashing + ed25519 signing/verification
  shacl_friendly.py              # SHACL violation → plain English translator
  paths.py                       # auto-discovery of spec files, JAR, keys
  output.py                      # ANSI color helpers
  commands/                      # one module per subcommand
    check.py, shacl.py, verify.py, rules.py,
    sign.py, keygen.py, validate.py, init.py, diff.py

spec/
  context/
    v0.2.jsonld                  # JSON-LD @context (term definitions)
  schemas/
    uofa_shacl.ttl               # SHACL shapes (Minimal + Complete + dispatcher)

examples/
  morrison-cou1/
    uofa-morrison-cou1.jsonld    # ✓ Complete profile — Morrison COU1 (CPB, Accepted)
    uofa_weakener.rules          # 12 forward-chaining rules (9 core + 3 compound)
  templates/
    uofa-minimal-skeleton.jsonld # Starter template — Minimal profile
    uofa-complete-skeleton.jsonld # Starter template — Complete profile
  starters/
    uofa-aero-fatigue-minimal.jsonld   # Wind turbine fatigue (NASA-STD-7009B)
    uofa-structural-bridge-minimal.jsonld # Highway bridge FEA load rating

tests/
  test_integration.py            # 45 integration tests (pytest)

.devcontainer/
  devcontainer.json              # GitHub Codespace / VS Code Dev Container config

weakener-engine/                 # Jena rule engine (Maven project)
  src/main/java/.../
    WeakenerEngine.java          # CLI entry point
  pom.xml                        # Maven build (Jena 5.3 + picocli)

keys/
  research.pub                   # ed25519 public key for signature verification

docs/
  getting-started.md             # Step-by-step tutorial for new users
```

---

## Prerequisites

**Zero-install option:** [Open in GitHub Codespaces](https://codespaces.new/cloudronin/uofa?quickstart=1) — everything is pre-installed.

**Local install:**

```bash
pip install -e .    # installs the uofa CLI and all Python dependencies
```

| Tool | Version | Purpose |
|---|---|---|
| Python 3.10+ | Installed via `pip install -e .` | SHACL validation + integrity verification |
| Java 17+ | OpenJDK or equivalent | Jena rule engine (C3 only) |
| Maven 3.8+ | `mvn package` | Build the Jena fat JAR (C3 only) |

Java and Maven are only required for the Jena rule engine (C3). Use `uofa check FILE --skip-rules` if Java is not available.

---

## Architecture: One UofA per Context of Use

The v0.2 architecture models credibility assessment at the **COU level**, not the individual factor level. Each UofA packages the complete credibility decision for one Context of Use — including all per-factor assessments as embedded CredibilityFactor nodes and any detected quality gaps as WeakenerAnnotation nodes.

```
Morrison Blood Pump Assessment
├── uofa-morrison-cou1.jsonld (ProfileComplete)
│   COU1: CPB Use (Class II) — Model Risk Level 2
│   ├── hasContextOfUse    → COU1 node
│   ├── bindsRequirement   → hemolysis safety requirement
│   ├── bindsModel         → ANSYS CFX v.15.0 + Eulerian HI model
│   ├── bindsDataset       → [PIV data, hemolysis in vitro data]
│   ├── hasValidationResult → [mesh convergence, PIV velocity, hemolysis comparison]
│   ├── hasCredibilityFactor → [7 assessed V&V 40 factors]
│   ├── hasWeakener        → [W-EP-01, W-AL-01, W-AR-01, W-AR-05] + compounds
│   ├── hasDecisionRecord  → "Accepted for COU1"
│   ├── hash               → sha256:<real hash>
│   ├── signature          → ed25519:<real signature>
│   └── wasDerivedFrom     → Morrison DOI
│
└── uofa-morrison-cou2.jsonld (ProfileComplete) [planned]
    COU2: VAD Use (Class III) — Model Risk Level 5
    └── W-AL-01 does NOT fire — COU2 has UQ
```

Shared entities (model, datasets, pump geometry) are referenced by IRI, not duplicated. The divergence between COU1 and COU2 weakener profiles is the central analytical demonstration.

---

## Research Context

UofA is the subject of a Doctor of Engineering praxis at George Washington University. The evaluation uses two FDA case studies:

- **Tier 1 (Retrospective):** Morrison et al. (2019) — FDA generic centrifugal blood pump V&V 40 credibility assessment. Re-expressed as UofA evidence packages with real cryptographic integrity. Rule engine detects 29 quality gaps including 8 compound inferences.
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

**Website:** [crediblesimulation.com](https://crediblesimulation.com)