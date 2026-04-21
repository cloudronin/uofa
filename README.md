# Unit of Assurance (UofA) — v0.5.2

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
pip install -e .    # one-time setup (installs uofa CLI + all Python dependencies)

# Run the full C1 + C2 + C3 pipeline in one command
uofa check packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld --build
```

That single command runs three checks:

| Step | Command | What it does |
|---|---|---|
| C2 | `uofa shacl FILE` | SHACL Complete profile validation — all required fields present |
| C1 | `uofa verify FILE` | SHA-256 hash + ed25519 signature verification — content untampered |
| C3 | `uofa rules FILE` | Jena rule engine — 23 forward-chaining rules (21 core + 2 compound) detect quality gaps |

The Jena JAR auto-builds on first run with `--build` (requires Java 17+ and Maven 3.8+).

**What the rule engine finds on Morrison COU1 at v0.5.2 (24 weakeners across 9 patterns):**

| Pattern | Severity | Hits | What it detects |
|---|---|---|---|
| W-EP-01 | Critical | 1 | Orphan claim — no evidence chain to supporting data |
| W-EP-02 | High | 3 | Broken provenance — validation results with no generation activity |
| W-AL-01 | High | 3 | Missing uncertainty quantification on validation results |
| W-AR-05 | High | 3 | Comparator absence — results not linked to reference entities |
| W-CON-01 | High | 6 | Accepted decision with factors lacking both requiredLevel and achievedLevel |
| W-CON-04 | Medium | 1 | Complete profile with no sensitivity analysis linked |
| W-ON-02 | High | 1 | COU lacks both applicability constraint and operating envelope |
| ⚡ COMPOUND-01 | Critical | 5 | Risk escalation — Critical + High weakeners coexist on same UofA |
| ⚡ COMPOUND-03 | High | 1 | Assurance level override — declared "Medium" but Critical gaps exist |

The v0.5.2 catalog includes 23 core weakener patterns spanning epistemic, aleatoric, ontological, structural, consistency, provenance, and argumentation categories. Run `uofa catalog` to list the full set. The Morrison COU1 example fires 9 of those 23 (7 Level-1 rules plus 2 compound rules).

The ⚡ compound rules fire on the output of the core rules — this is chained forward-chaining inference that standalone SPARQL queries cannot produce. Same model, same data, same rules: the rule engine reasons about the *interactions* between gaps, not just the gaps themselves.

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
           Weakeners  9                                 6

══ Weakener Patterns (10) ══
  ┌────────────────────────────────────────────────────────────────┐
  │   Pattern    │  Severity  │  COU A  │  COU B  │    Status    │
  ├──────────────┼────────────┼─────────┼─────────┼──────────────┤
  │ W-AL-01      │ [High]     │   ✓     │   ✗     │ ◆ divergent  │
  │ W-AL-02      │ [Medium]   │   ✗     │   ✓     │ ◆ divergent  │
  │ W-AR-05      │ [High]     │   ✓     │   ✗     │ ◆ divergent  │
  │ W-CON-01     │ [High]     │   ✓     │   ✗     │ ◆ divergent  │
  │ W-CON-04     │ [Medium]   │   ✓     │   ✓     │   same       │
  │ W-EP-01      │ [Critical] │   ✓     │   ✗     │ ◆ divergent  │
  │ W-EP-02      │ [High]     │   ✓     │   ✗     │ ◆ divergent  │
  │ W-EP-04      │ [High]     │   ✗     │   ✓     │ ◆ divergent  │
  │ W-ON-02      │ [High]     │   ✓     │   ✓     │   same       │
  │ W-PROV-01    │ [Critical] │   ✗     │   ✓     │ ◆ divergent  │
  └──────────────┴────────────┴─────────┴─────────┴──────────────┘

══ Compound Patterns (2) ══
  ┌────────────────────────────────────────────────────────────────┐
  │   Pattern    │  Severity  │  COU A  │  COU B  │    Status    │
  ├──────────────┼────────────┼─────────┼─────────┼──────────────┤
  │ COMPOUND-01  │ [Critical] │   ✓     │   ✓     │   same       │
  │ COMPOUND-03  │ [High]     │   ✓     │   ✗     │ ◆ divergent  │
  └──────────────┴────────────┴─────────┴─────────┴──────────────┘

══ Summary ══
  COU A (COU1: Cardiopulmonary bypass use (Class II)):
    [Critical] 2
    [High] 6
    [Medium] 1
  COU B (COU2: Ventricular assist device use (Class III)):
    [Critical] 2
    [High] 2
    [Medium] 2

  9 divergence(s) detected

══ Divergence Explanations ══

  [High] COMPOUND-03 — only in COU A
    COU1: Cardiopulmonary bypass use (Class II): Assurance level is not Low, yet Critical weakeners exist — stated assurance level may be overstated.
    COU2: Ventricular assist device use (Class III): pattern does not fire.

  [High] W-AL-01 — only in COU A
    COU1: Cardiopulmonary bypass use (Class II): Validation result has no uncertainty quantification — aleatory uncertainty is uncharacterized.
    COU2: Ventricular assist device use (Class III): pattern does not fire.

  [High] W-AR-05 — only in COU A
    COU1: Cardiopulmonary bypass use (Class II): Validation result has no comparedAgainst link — comparator data source is absent.
    COU2: Ventricular assist device use (Class III): pattern does not fire.

  [High] W-CON-01 — only in COU A
    COU1: Cardiopulmonary bypass use (Class II): Decision is Accepted but a credibility factor has neither requiredLevel nor achievedLevel — the acceptance rests on an unestablished factor.
    COU2: Ventricular assist device use (Class III): pattern does not fire.

  [Critical] W-EP-01 — only in COU A
    COU1: Cardiopulmonary bypass use (Class II): Claim has no prov:wasDerivedFrom link to evidence — provenance chain is broken.
    COU2: Ventricular assist device use (Class III): pattern does not fire.

  [High] W-EP-02 — only in COU A
    COU1: Cardiopulmonary bypass use (Class II): Validation result has no prov:wasGeneratedBy — generation activity is missing.
    COU2: Ventricular assist device use (Class III): pattern does not fire.

  [Medium] W-AL-02 — only in COU B
    COU2: Ventricular assist device use (Class III): Uncertainty quantification is reported but no sensitivity analysis is linked — the drivers of uncertainty are undocumented.
    COU1: Cardiopulmonary bypass use (Class II): pattern does not fire.

  [High] W-EP-04 — only in COU B
    COU2: Ventricular assist device use (Class III): Credibility factor is not assessed but model risk level exceeds 2 — unassessed factors at elevated risk weaken the credibility argument.
    COU1: Cardiopulmonary bypass use (Class II): pattern does not fire.

  [Critical] W-PROV-01 — only in COU B
    COU2: Ventricular assist device use (Class III): Provenance chain terminates at a node that has no upstream derivation/generation/use edge and is not marked uofa:isFoundationalEvidence=true — chain is incomplete.
    COU1: Cardiopulmonary bypass use (Class II): pattern does not fire.
```

The output has four sections: **identity block** (side-by-side COU metadata), **weakener profile table** (✓/✗ presence with divergence markers), **summary counts** (per-severity breakdown), and **divergence explanations** (from the `description` field on each WeakenerAnnotation — generated by the rule engine, not hardcoded in the diff command).

Compound patterns (COMPOUND-*) are separated into their own sub-table when present, since they fire on the output of Level 1 rules.

This divergence is invisible in the prose paper. It becomes machine-visible in the UofA. That's C1: the credibility *decision* — not just the evidence — captured as a first-class artifact.

---

## Live Demo: HPT Blade CHT (NASA-STD-7009B, Aerospace)

The `packs/nasa-7009b/examples/aerospace/` directory contains a parallel NASA-STD-7009B case study — an HPT turbine-blade conjugate heat transfer CFD model assessed for two operating points:

- **COU1** (take-off transient, MRL 3) → Decision: **Accepted with conditions**
- **COU2** (cruise steady-state, MRL 4) → Decision: **Not accepted**

Same CFD model, same cascade-rig validation data, re-purposed for a different operating regime — reproducing the Morrison divergence mechanism in aerospace. The bundles ship as zipped evidence folders (10 docs each — narrative DOCX, CFX solver settings, cascade CSVs, board minutes, decision rationale PDFs), so you can exercise the full `extract → import → rules` pipeline end-to-end on real input.

**End-to-end roundtrip on COU1:**

```bash
# 1. Extract: LLM reads 10 evidence documents, produces a pre-filled 19-factor xlsx
uofa extract tests/fixtures/extract/aero-evidence-cou1 \
  --pack nasa-7009b --model ollama/qwen3.5:4b -o /tmp/aero-cou1.xlsx

# 2. Import: convert the xlsx to signed JSON-LD
uofa import /tmp/aero-cou1.xlsx --pack nasa-7009b -o /tmp/aero-cou1.jsonld

# 3. Rules: run the Jena weakener engine, write the reasoned jsonld
uofa rules /tmp/aero-cou1.jsonld --pack nasa-7009b \
  --format jsonld -o /tmp/aero-cou1-reasoned.jsonld --build
```

The pack ships pre-computed reasoned outputs so you can skip to the interesting part:

```bash
# COU1 (Accepted) — W-AR-02 fires on narrative-stated level gaps
uofa rules packs/nasa-7009b/examples/aerospace/uofa-aero-cou1-nasa7009b.jsonld --pack nasa-7009b

# COU2 (Not Accepted) — W-AR-02 stays at zero despite 4+ not-assessed factors
uofa rules packs/nasa-7009b/examples/aerospace/uofa-aero-cou2-nasa7009b.jsonld --pack nasa-7009b
```

**The divergence:**

| Pattern | COU1 (Accepted) | COU2 (Not Accepted) |
|---|---|---|
| **W-AR-02** (accept-despite-gap) | **4 fires** on level gaps | **0 fires** (hard gate) |
| W-EP-04 (not-assessed at MRL>2) | 1 | 4 |
| COMPOUND-01 (Critical + High) | 6 | 5 |
| W-NASA-02/03/06 (missing evidence linkage) | 1 each | 1 each |
| Total weakeners | 17 | 20 |
| Distinct patterns | 9 | 8 |

**Why this matters:** W-AR-02 (the rebutting-defeater rule) fires *only* when a decision says `Accepted` AND any factor has `achievedLevel < requiredLevel`. Flipping the decision to `Not accepted` disarms every instance of this rule — even though COU2 actually has *more* credibility gaps than COU1. That's the C3 rule engine correctly modeling the argument: a not-accepted decision has no "contradictory result ignored" to defeat. The same mechanism is visible in Morrison; here it repeats in aerospace.

**Reproduce the accuracy numbers:**

```bash
# Factor F1 + weakener gate scoring, logs to scripts/extract_accuracy_log.jsonl
python scripts/score_extraction.py --pack nasa-7009b --case cou1 \
  --model ollama/qwen3.5:4b --prompt-version v3-nasa-aero
python scripts/score_extraction.py --pack nasa-7009b --case cou2 \
  --model ollama/qwen3.5:4b --prompt-version v3-nasa-aero
```

The scorer runs `extract → import → rules` end-to-end and asserts gates from `tests/fixtures/extract/ground_truth/aero-cou{1,2}-nasa7009b.json`. The hard gate for COU2 is `W-AR-02 count == 0`; if it ever fires, either the extracted decision outcome isn't `"Not accepted"` or the rule engine is mis-matching. Most recent live run: COU1 F1 = 0.97, COU2 F1 = 0.85, both weakener gates pass.

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

Placeholder strings (e.g., `sha256:placeholder...`) now **fail** SHACL validation. This is deliberate — a UofA claiming ProfileComplete must carry a real hash.

---

## The Jena Rule Engine (C3)

Quality gap detection uses [Apache Jena](https://jena.apache.org/) forward-chaining rules, not just SPARQL queries. The rule engine operates in two levels:

**Level 1 — Core detection rules** (21 patterns in v0.5.2) match structural patterns against the evidence graph. Categories include epistemic (W-EP-*), aleatoric (W-AL-*), ontological (W-ON-*), structural (W-SI-*), consistency (W-CON-*), provenance (W-PROV-*), and argumentation (W-AR-*). Run `uofa catalog` for the full list with descriptions.

**Level 2 — Compound inference rules** (2 active in v0.5.2) fire on the output of Level 1 rules:

| Rule | What it detects |
|---|---|
| COMPOUND-01 | Critical + High weakeners coexist → escalated compound risk |
| COMPOUND-03 | Declared assurance level contradicts detected Critical gaps |

COMPOUND-02 ships in the rules file but is currently commented out pending v0.6 design review; `uofa catalog` filters it from listing output.

The compound rules are the key differentiator versus SPARQL. They reason about the *interactions* between gaps — something that requires chained forward-chaining inference. As of v0.5.2, all weakener rules (including previously Python-implemented W-CON-02, W-CON-05, W-PROV-01) evaluate in a single Jena forward-chaining pass, enabling compound rules to reason over the full weakener set.

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
# Extract credibility data from evidence documents with an LLM (pre-fills a pack xlsx)
uofa extract path/to/evidence/ --pack nasa-7009b --model ollama/qwen3.5:4b -o out.xlsx

# Import from a practitioner-filled Excel workbook (fastest on-ramp)
uofa import assessment.xlsx --sign --key keys/your.key --check

# Full pipeline (C1 + C2 + C3) on your file
uofa check path/to/your-uofa.jsonld

# Individual steps
uofa shacl  path/to/your-uofa.jsonld                      # C2: SHACL validation
uofa verify path/to/your-uofa.jsonld                      # C1: Hash + signature check
uofa rules  path/to/your-uofa.jsonld                      # C3: Jena weakener detection (text summary)
uofa rules  FILE --format jsonld -o reasoned.jsonld       # C3: write reasoned JSON-LD with weakener annotations

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

## Adversarial Generation (research instrument)

`uofa adversarial generate` synthesizes JSON-LD evidence packages that target specific weakener patterns, then validates them against SHACL. The tool is an **instrument** for empirically characterizing rule coverage — it feeds the methodology section of Chapter 3 and the September 2026 JVVUQ paper. Synthetic packages are flagged and refused by `uofa sign` and `uofa verify` so they can never be mistaken for real evidence.

```bash
pip install -e '.[llm]'                          # one-time: adds litellm + pyyaml
export ANTHROPIC_API_KEY=sk-ant-...              # generation defaults to claude-opus-4-7

# Generate 5 synthetic packages targeting W-AR-05 (comparator absence / mismatch)
uofa adversarial generate \
  --spec specs/w_ar_05_baseline.yaml \
  --out out/adversarial/w_ar_05/

# Dry-run: render the prompt without calling the LLM
uofa adversarial generate --spec specs/w_ar_05_baseline.yaml --out /tmp/dry --dry-run

# Run the full Phase 1 acceptance script
bash tests/adversarial/test_acceptance.sh
```

Every generated package carries an `adversarialProvenance` block (spec id, prompt template version, generation model, timestamp, target weakener) and a `provenanceBlockHash` that `uofa verify` recomputes to detect tampering with the synthetic flag. `--strict-circularity` refuses to run when the generation model matches the configured extract model; `--allow-circular-model` is an explicit opt-in for debugging runs.

Spec file format and the full design are documented in [UofA_Adversarial_Gen_Spec_v1.1.md](../Requirements/UofA_Adversarial_Gen_Spec_v1.1.md). Phase 1 ships the W-AR-05 (D3 undercutting) template; the registry in `src/uofa_cli/adversarial/prompts/__init__.py` scales to additional weakener patterns by adding keys.

---

## Domain Packs

SHACL shapes, Jena rules, templates, and extraction prompts are organized into **domain packs** under `packs/`. The `core` pack ships with standards-agnostic credibility assessment rules (23 weakener patterns as of v0.5.2, up from 12 in v0.4). The `vv40` pack provides the ASME V&V 40-2018 factor taxonomy (13 factors), and the `nasa-7009b` pack provides the NASA-STD-7009B factor taxonomy (19 factors, including 6 NASA-only lifecycle factors).

```bash
$ uofa packs
════════════════════════════════════════════════════════
  Installed packs
════════════════════════════════════════════════════════
    core         v0.5.0    Core credibility assessment rules. Standards-agnostic. (any factors, 23 patterns)  [always loaded]
    nasa-7009b   v0.5.0    NASA-STD-7009B credibility assessment factors (19 factors: 1... (19 factors, 6 patterns)
    vv40         v0.5.0    ASME V&V 40-2018 credibility factor taxonomy (13 factors). (13 factors, 0 patterns)  [active]
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

The Excel template has 5 sheets: **Assessment Summary**, **Model & Data**, **Validation Results**, **Credibility Factors**, and **Decision**. Each pack provides a pre-populated template with locked factor names and dropdown validation. See `packs/vv40/templates/uofa-starter-filled.xlsx` for a complete filled example.

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

UofA models credibility assessment at the **COU level**, not the individual factor level. Each UofA packages the complete credibility decision for one Context of Use — including all per-factor assessments as embedded CredibilityFactor nodes and any detected quality gaps as WeakenerAnnotation nodes.

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
│   ├── hasWeakener        → [W-EP-01, W-EP-02 (3×), W-AL-01 (3×), W-AR-05 (3×), W-CON-01 (6×), W-CON-04, W-ON-02] + [COMPOUND-01 (5×), COMPOUND-03]
│   ├── hasDecisionRecord  → "Accepted for COU1"
│   ├── hash               → sha256:<real hash>
│   ├── signature          → ed25519:<real signature>
│   └── wasDerivedFrom     → Morrison DOI
│
└── morrison/cou2/uofa-morrison-cou2.jsonld (ProfileComplete)
    COU2: VAD Use (Class III) — Model Risk Level 5
    ├── hasCredibilityFactor → [13 V&V 40 factors: 7 assessed + 6 not-assessed]
    ├── hasWeakener        → [W-PROV-01 (7×), W-EP-04 (6×), W-ON-02, W-AL-02, W-CON-04] + [COMPOUND-01 (2×)]
    └── At MRL 5 the risk-driven catalog shifts: W-PROV-01 dominates COU2 (7 provenance-chain orphans),
        W-EP-04 fires 6× on not-assessed factors, and two of W-PROV-01's Criticals coexist with High
        weakeners on `cou2` — triggering 2 COMPOUND-01 cascades that were unreachable pre-v0.5.2.
```

Shared entities (model, datasets, pump geometry) are referenced by IRI, not duplicated. The divergence between COU1 and COU2 weakener profiles is the central analytical demonstration.

---

## Research Context

UofA is the subject of a Doctor of Engineering praxis at George Washington University. The evaluation uses two FDA case studies:

- **Tier 1 (Retrospective):** Morrison et al. (2019) — FDA generic centrifugal blood pump V&V 40 credibility assessment. Re-expressed as UofA evidence packages with real cryptographic integrity. Full 13-factor assessment (7 assessed, 6 not-assessed) with risk-driven divergence across the v0.5.2 catalog:

  - **Morrison COU1** (MRL 2, Accepted): 24 weakeners including 6 Critical (1 W-EP-01 orphan claim plus 5 COMPOUND-01 cascades from coexisting Critical and High weakeners), 17 High (W-CON-01 on 6 factors with missing level assertions under the Accepted decision, plus W-AL-01, W-AR-05, W-EP-02, W-ON-02), and 1 Medium (W-CON-04 structural gap).

  - **Morrison COU2** (MRL 5, Not Accepted): 18 weakeners including 9 Critical (7 W-PROV-01 provenance-chain orphans plus 2 COMPOUND-01 cascades), 7 High (6 W-EP-04 on unassessed factors at elevated model risk, 1 W-ON-02), and 2 Medium.

  The cross-COU divergence (7 pattern-level divergences between COU1 and COU2) is the central analytical demonstration: same model, same data, different credibility requirements driven by different model risk produce measurably different credibility evidence profiles.
- **Tier 2 (Prospective):** FDA VICTRE pipeline — live computational workflow instrumented to generate UofAs during execution rather than from retrospective documents.
- **Tier 3 (Exploratory):** Multi-component stress test on VICTRE — simulates change events to test continuous re-issuance and hierarchical credibility composition.

Early findings — including the aerospace companion case study ([HPT Blade CHT, NASA-STD-7009B](#live-demo-hpt-blade-cht-nasa-std-7009b-aerospace)) that reproduces the Morrison COU1/COU2 divergence mechanism in a turbomachinery domain — will be presented at [NAFEMS Americas 2026](https://www.nafems.org/events/nafems/2026/nafems-americas-conference/) (May 27–29, St. Charles, MO).

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