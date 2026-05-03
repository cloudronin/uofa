# Unit of Assurance (UofA)

[![PyPI version](https://img.shields.io/pypi/v/uofa.svg)](https://pypi.org/project/uofa/)
![validate examples](https://github.com/cloudronin/uofa/actions/workflows/validate.yml/badge.svg)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

The **Unit of Assurance** is the smallest independently verifiable bundle of credibility evidence for computational modeling and simulation (CM&S). It packages the **credibility decision** — who judged what, against what criteria, using what evidence, with what result — as a signed, provenance-linked, machine-verifiable engineering artifact.

## Conference Attendees: Run the 30-Second Demo

```bash
pip install uofa
uofa demo
```

The bundled fixture exercises the full C1 (signature + integrity) +
C2 (SHACL) + C3 (Jena rule engine) pipeline against a small pre-computed
UofA artifact — no Java install, no LLM runtime, no internet required.
Use it to verify "yes, this tool actually does what the speaker claimed"
in under a minute.

When you're ready to encode your own evidence, see the Quick Start below.

## Quick Start: Create Your Own UofA

```bash
# 1. Install the uofa CLI (one command — bundles Python deps, the rule
#    engine JAR, and an OpenJDK 17 JRE inside the wheel; no Java or Maven
#    install required).
pip install uofa

# 2. Import from Excel (fastest on-ramp for practitioners)
uofa import my-assessment.xlsx --sign --key keys/research.key --check

# — OR — scaffold from a JSON-LD template
uofa init my-project
# Edit my-project/my-project-cou1.jsonld — fill in your project details
uofa sign my-project/my-project-cou1.jsonld --key my-project/keys/my-project.key
uofa check my-project/my-project-cou1.jsonld
```

Platform wheels are published for macOS (arm64), Linux (x86_64 + aarch64),
and Windows (x86_64). Intel-Mac users install the `py3-none-any` wheel and
provide a system Java 17 (`brew install openjdk@17`). The `uofa[extract]`
extra adds the LLM-backed prose-to-UofA pipeline; see `uofa setup --help`
for one-time runtime installation.

**New to UofA?** See the [Onboarding Guide](docs/onboarding.md) for a step-by-step walkthrough (and a zero-install Codespaces option), or study the [Morrison demo](#live-demo-morrison-blood-pump-fda-vv-40-case-study) below.

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

The `packs/vv40/examples/morrison/` directory contains complete, working UofA evidence packages built from [Morrison et al. (2019)](https://doi.org/10.1097/MAT.0000000000000996) — an FDA OSEL co-authored V&V 40 credibility assessment for a centrifugal blood pump. This is the most widely cited V&V 40 worked example.

**What the demo shows:**

```
Morrison prose assessment          →  UofA structured evidence package
  "model deemed credible"               JSON-LD with 13 V&V 40 factors,
  scattered across 10 pages              provenance chain, integrity hash,
  of journal article                     machine-verifiable in 30 seconds
```

**Run it yourself:**

```bash
pip install uofa     # bundles the rule engine JAR + an OpenJDK 17 JRE

# Run the full C1 + C2 + C3 pipeline in one command
uofa check packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld
```

That single command runs three checks:

| Step | Command | What it does |
|---|---|---|
| C2 | `uofa shacl FILE` | SHACL Complete profile validation — all required fields present |
| C1 | `uofa verify FILE` | SHA-256 hash + ed25519 signature verification — content untampered |
| C3 | `uofa rules FILE` | Jena rule engine — 23 forward-chaining rules (21 core + 2 compound) detect quality gaps |

The bundled JAR + JRE inside the wheel mean no Maven, no separate Java
install, and no `--build` flag is needed. Source-tree contributors can
still build the JAR via `cd src/weakener-engine && mvn package` and run from
their own checkout — the bundled JRE only activates inside an installed
wheel.

<!-- Generated from `uofa rules packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld`.
     Re-run if the catalog or example changes. -->

**What the rule engine finds on Morrison COU1 (11 weakeners across 5 patterns):**

| Pattern | Severity | Hits | What it detects |
|---|---|---|---|
| W-EP-02 | High | 3 | Validation result has no `prov:wasGeneratedBy` — generation activity is missing |
| W-AL-01 | High | 3 | Validation result has no uncertainty quantification — aleatory uncertainty is uncharacterized |
| W-AR-05 | High | 3 | Validation result has no `comparedAgainst` link — comparator data source is absent |
| W-CON-04 | Medium | 1 | Complete profile with no sensitivity analysis linked |
| W-ON-02 | High | 1 | Context of Use lacks both applicability constraint and operating envelope |

The catalog includes 23 weakener patterns spanning epistemic, aleatoric, ontological, structural, consistency, provenance, and argumentation categories. Run `uofa catalog` to list the full set. Morrison COU1 fires 5 of those 23 — the more risky COU2 fires a different 6 patterns including 2 Critical compound rules. See the divergence below.

The compound rules fire on the output of the core rules — this is chained forward-chaining inference that standalone SPARQL queries cannot produce. Same model, same data, same rules: the rule engine reasons about the *interactions* between gaps, not just the gaps themselves.

**Want to see the same divergence mechanism in aerospace?** A parallel NASA-STD-7009B case study on an HPT turbine-blade CHT model lives at [docs/examples/hpt-blade-cht.md](docs/examples/hpt-blade-cht.md).

---

## COU Divergence: `uofa diff`

Morrison contains two Contexts of Use assessing the same CFD model:

- **COU1** (CPB, Class II, Model Risk Level 2) → Decision: **Accepted**
- **COU2** (VAD, Class III, Model Risk Level 5) → Decision: **Not accepted**

Same model. Same experimental data. Different credibility requirements driven by different model risk. The `uofa diff` command surfaces this divergence automatically:

```bash
uofa diff packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld \
         packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld
```

<!-- Generated from `uofa diff packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld
     packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld`. Re-run if the catalog changes. -->

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
           Weakeners  5                                 6

══ Weakener Patterns (8) ══
  ┌────────────────────────────────────────────────────────────────┐
  │   Pattern    │  Severity  │  COU A  │  COU B  │    Status    │
  ├──────────────┼────────────┼─────────┼─────────┼──────────────┤
  │ W-AL-01      │ [High]     │   ✓     │   ✗     │ ◆ divergent  │
  │ W-AL-02      │ [Medium]   │   ✗     │   ✓     │ ◆ divergent  │
  │ W-AR-05      │ [High]     │   ✓     │   ✗     │ ◆ divergent  │
  │ W-CON-04     │ [Medium]   │   ✓     │   ✓     │   same       │
  │ W-EP-02      │ [High]     │   ✓     │   ✗     │ ◆ divergent  │
  │ W-EP-04      │ [High]     │   ✗     │   ✓     │ ◆ divergent  │
  │ W-ON-02      │ [High]     │   ✓     │   ✓     │   same       │
  │ W-PROV-01    │ [Critical] │   ✗     │   ✓     │ ◆ divergent  │
  └──────────────┴────────────┴─────────┴─────────┴──────────────┘

══ Compound Patterns (1) ══
  ┌────────────────────────────────────────────────────────────────┐
  │   Pattern    │  Severity  │  COU A  │  COU B  │    Status    │
  ├──────────────┼────────────┼─────────┼─────────┼──────────────┤
  │ COMPOUND-01  │ [Critical] │   ✗     │   ✓     │ ◆ divergent  │
  └──────────────┴────────────┴─────────┴─────────┴──────────────┘

══ Summary ══
  COU A (COU1: Cardiopulmonary bypass use (Class II)):
    [High] 4
    [Medium] 1
  COU B (COU2: Ventricular assist device use (Class III)):
    [Critical] 2
    [High] 2
    [Medium] 2

  7 divergence(s) detected
```

The full report includes a per-divergence "Divergence Explanations" block with the human-readable reason each pattern does or doesn't fire on each side. The headline: COU2 (the higher-risk Ventricular Assist Device application) trips a Critical W-PROV-01 (broken provenance chain) and a Critical COMPOUND-01 (Critical+High coexistence) that don't fire under COU1's lower MRL — even though COU1 has more raw weakeners by count. The C3 engine is correctly weighting risk-driven severity, not raw frequency.

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
uofa sign packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld --key keys/research.key

# Verify integrity
uofa verify packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld
```

Placeholder strings (e.g., `sha256:placeholder...`) **fail** SHACL validation by design — a UofA claiming ProfileComplete must carry a real hash.

---

## The Jena Rule Engine (C3)

Quality gap detection uses [Apache Jena](https://jena.apache.org/) forward-chaining rules, not just SPARQL queries. The rule engine operates in two levels:

**Level 1 — Core detection rules** (21 patterns) match structural patterns against the evidence graph. Categories include epistemic (W-EP-*), aleatoric (W-AL-*), ontological (W-ON-*), structural (W-SI-*), consistency (W-CON-*), provenance (W-PROV-*), and argumentation (W-AR-*). Run `uofa catalog` for the full list with descriptions.

**Level 2 — Compound inference rules** (2 active) fire on the output of Level 1 rules:

| Rule | What it detects |
|---|---|
| COMPOUND-01 | Critical + High weakeners coexist → escalated compound risk |
| COMPOUND-03 | Declared assurance level contradicts detected Critical gaps |

(COMPOUND-02 ships in the rules file but is currently commented out pending design review; `uofa catalog` filters it from listing output.)

The compound rules are the key differentiator versus SPARQL. They reason about the *interactions* between gaps — something that requires chained forward-chaining inference. All weakener rules evaluate in a single Jena forward-chaining pass, so compound rules can reason over the full weakener set.

For the data shape (Minimal vs. Complete profiles, CredibilityFactor, WeakenerAnnotation), see [docs/profiles.md](docs/profiles.md).

---

## Plain-language explanations: `--explain`

`uofa rules`, `check`, `diff`, and `shacl` accept an `--explain` flag that
adds a plain-language interpretation block to the structured output. The
deterministic analysis remains the source of truth; the explanation is a
human-readable layer for regulatory affairs and validation engineers.

```bash
uofa rules my-package.jsonld --explain
uofa rules my-package.jsonld --explain --explain-max-items 3
uofa rules my-package.jsonld --explain --explain-format json
```

Default backend is bundled Ollama (qwen3.5:4b, local-only, free). For
higher quality or larger context, configure a remote backend in
`uofa.toml` or override per invocation:

```bash
uofa rules my-package.jsonld --explain \
    --explain-backend anthropic \
    --explain-model claude-sonnet-5-2026
# requires ANTHROPIC_API_KEY in environment
```

Results are cached at `~/.uofa/cache/explain.db` — a second invocation
on the same input completes in <100 ms. Standalone re-interpretation of
cached output: `uofa explain --from-file cache.json`.

Full documentation:

- **[docs/explain.md](docs/explain.md)** — usage, output formats, caching, limitations
- **[docs/llm-config.md](docs/llm-config.md)** — `[llm]` section, supported backends, precedence
- **[docs/security.md](docs/security.md)** — API key handling, threat model

---

## Excel Import: The Practitioner On-Ramp

Simulation engineers fill an Excel workbook, run one command, and get a signed, validated JSON-LD evidence package. The import pipeline handles URI generation, factor standard assignment, provenance tracking, and optional signing + validation in a single invocation.

```bash
pip install -e '.[excel]'    # one-time: adds openpyxl dependency

# Import from Excel → JSON-LD, sign, and validate in one step
uofa import my-assessment.xlsx --sign --key keys/research.key --check --pack vv40
```

The Excel template has 5 sheets: **Assessment Summary**, **Model & Data**, **Validation Results**, **Credibility Factors**, and **Decision**. Each pack provides a pre-populated template with locked factor names and dropdown validation. See `packs/vv40/templates/uofa-starter-filled.xlsx` for a complete filled example.

---

## Domain Packs

SHACL shapes, Jena rules, templates, and extraction prompts are organized into **domain packs** under `packs/`. The `core` pack ships with standards-agnostic credibility assessment rules (23 weakener patterns). The `vv40` pack provides the ASME V&V 40-2018 factor taxonomy (13 factors), and the `nasa-7009b` pack provides the NASA-STD-7009B factor taxonomy (19 factors, including 6 NASA-only lifecycle factors).

```bash
uofa packs            # list installed packs + counts
uofa check FILE --pack vv40                  # use V&V 40
uofa check FILE --pack vv40 --pack nasa-7009b  # combine packs
```

The `--pack` flag on any command switches the active pack(s). Multiple packs can be specified to combine factor taxonomies and rules. Per-project rules files next to the input file still take precedence over the pack default. See [`packs/README.md`](packs/README.md) for the full pack contract.

---

## Prerequisites

```bash
pip install uofa             # CLI + bundled JAR + bundled JRE; nothing else needed
pip install 'uofa[excel]'    # adds openpyxl for `uofa import`
pip install 'uofa[extract]'  # adds litellm + pdfplumber + python-docx for `uofa extract`
```

| Tool | Purpose | When you need it |
|---|---|---|
| Python 3.10+ | Runtime | Always |
| Java 17+ | Jena rule engine (C3) | Only on Intel macOS (where the bundled JRE doesn't ship) or in source-tree dev when running outside the wheel |
| Maven 3.8+ | Build the Jena JAR | Only when developing on the rule engine itself |

For a zero-install try-it-out path, see [docs/onboarding.md](docs/onboarding.md#zero-install-option-github-codespaces).

---

## Working with Your Own UofA

```bash
# Full pipeline (C1 + C2 + C3) on your file
uofa check path/to/your-uofa.jsonld

# Individual steps
uofa shacl  path/to/your-uofa.jsonld          # C2: SHACL validation
uofa verify path/to/your-uofa.jsonld          # C1: Hash + signature check
uofa rules  path/to/your-uofa.jsonld          # C3: Jena weakener detection

# Sign with your own key
uofa sign path/to/your-uofa.jsonld --key keys/your.key

# Compare weakener profiles across two COUs
uofa diff uofa-cou1.jsonld uofa-cou2.jsonld
```

Full command reference (extract, import, init, validate, packs, migrate, schema, …) lives in [docs/onboarding.md](docs/onboarding.md#cli-command-reference).

---

## Further reading

- **[docs/onboarding.md](docs/onboarding.md)** — combined quick-start + architecture + contributor guide; full CLI reference
- **[docs/profiles.md](docs/profiles.md)** — Minimal/Complete profiles, CredibilityFactor schema, WeakenerAnnotation schema
- **[docs/architecture.md](docs/architecture.md)** — One UofA per Context of Use (the data model in tree form)
- **[docs/examples/hpt-blade-cht.md](docs/examples/hpt-blade-cht.md)** — Aerospace companion case study (NASA-STD-7009B)
- **[docs/explain.md](docs/explain.md)** — `--explain` flag deep dive
- **[docs/design.md](docs/design.md)** — Research context + design principles
- **[docs/adversarial.md](docs/adversarial.md)** — Adversarial generation tooling (research instrument)
- **[docs/repo-layout.md](docs/repo-layout.md)** — Top-level repo orientation for contributors

---

## License

Apache License, Version 2.0 — see [LICENSE](LICENSE) for the full text and
[NOTICE](NOTICE) for bundled-software attributions.

The full project (UofA ontology, JSON-LD context, SHACL shapes, reference
examples, Jena rule implementations, and the CLI) is licensed under
Apache 2.0. Bundled third-party components retain their own licenses
as enumerated in `NOTICE` (e.g., OpenJDK GPLv2-CE, Ollama MIT).

---

## Contributing

Contributions are welcome, especially real-world UofA examples from practitioners working with CM&S credibility assessment. If you are preparing a CM&S-supported regulatory submission and want to explore UofA packaging for your evidence, please reach out.

For contributors, see [CONTRIBUTING.md](CONTRIBUTING.md), [docs/repo-layout.md](docs/repo-layout.md), and [docs/onboarding.md](docs/onboarding.md).

**Website:** [uofa.net](https://uofa.net)
