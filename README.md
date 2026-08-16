# Unit of Assurance (UofA)

[![PyPI version](https://img.shields.io/pypi/v/uofa.svg)](https://pypi.org/project/uofa/)
![validate examples](https://github.com/cloudronin/uofa/actions/workflows/validate.yml/badge.svg)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

The **Unit of Assurance** is the smallest independently verifiable bundle of credibility evidence for computational modeling and simulation (CM&S). It packages the **credibility decision** — who judged what, against what criteria, using what evidence, with what result — as a signed, provenance-linked, machine-verifiable engineering artifact.

```bash
pip install uofa
```

One command. The wheel bundles the Python dependencies, the rule-engine JAR, and an OpenJDK 17 JRE — no Java or Maven install required.

---

## See it work — 30 seconds

```bash
uofa demo
```

Runs the full **C1** (signature + integrity) + **C2** (SHACL) + **C3** (Jena rule engine) pipeline against a bundled fixture. No Java install, no LLM runtime, no internet.

---

## The on-ramp: an evidence folder to a validated package

Four steps. Each is checkable, and the tool tells you what it could not do rather than filling the gap.

### 1. Extract — evidence documents to a spreadsheet

```bash
uofa extract path/to/evidence/ --pack vv40 -o extracted.xlsx
```

Reads PDF, DOCX, XLSX, CSV and TXT and produces a pre-filled workbook. By default this uses a local model (`qwen3.5:4b` via Ollama, 3–10 min per folder, no API spend). To use a remote backend:

```bash
uofa extract path/to/evidence/ --pack vv40 \
    --extract-backend anthropic --extract-model claude-sonnet-4-6 -o extracted.xlsx
# requires ANTHROPIC_API_KEY
```

**Or with no model at all:**

```bash
uofa extract path/to/evidence/ --pack vv40 --keyless -o extracted.xlsx
```

No API key, no network, no spend. It fills only the fields with a route measured to beat a null model that reads nothing, and **leaves the rest blank rather than guessing** — every blank is named in the run output. See [what extraction is worth](#what-extraction-is-actually-worth) below.

### 2. Review the spreadsheet — this step is not optional

The workbook is a draft, not an answer. Cells are colour-coded by confidence: **green** ≥ 0.85, **yellow** 0.50–0.84, uncoloured below that. Hover a cell for its source document.

Check the per-factor levels and rationales first — they are where an extractor is most often wrong, and where a wrong value does the most damage, because a plausible level validates just as well as a correct one.

### 3. Import and sign

```bash
uofa import extracted.xlsx -o my-cou.jsonld --sign --key keys/my.key
```

Every import prints where each field came from:

```
field provenance: 1 defaulted, 1 derived, 2 extracted, 6 run-context
```

* **extracted** — read from your documents
* **run-context** — supplied by the run: who ran it, when, the input filenames, the hash and signature
* **defaulted** / **derived** — filled in for you, or computed

This is how you ask **how much of a package was actually read**. A conforming package can be mostly about the run that produced it, and that is worth knowing before you rely on it.

The declared profile is *derived* from what the package contains, not asserted — it claims what it earned. If it satisfies no profile, import says which fields are missing rather than declaring a lower one it also does not meet.

### 4. Check

```bash
uofa check my-cou.jsonld
```

| | |
|---|---|
| **C1 Integrity** | hash + signature over the canonicalized graph |
| **C2 SHACL** | required fields for the declared profile |
| **C3 Rules** | 23 weakener patterns via the Jena rule engine |

`uofa check` runs all three. Add `--explain` for plain-language findings.

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

The catalog includes 23 weakener patterns spanning epistemic, aleatory, ontological, structural, consistency, provenance, and argumentation categories. Run `uofa catalog` to list the full set. Morrison COU1 fires 5 of those 23 — the more risky COU2 fires a different 6 patterns including 2 Critical compound rules. See the divergence below.

The compound rules fire on the output of the core rules — this is chained forward-chaining inference that standalone SPARQL queries cannot produce. Same model, same data, same rules: the rule engine reasons about the *interactions* between gaps, not just the gaps themselves.

**Want to see the same divergence mechanism in aerospace?** A parallel NASA-STD-7009B case study on an HPT turbine-blade CHT model lives at [docs/examples/hpt-blade-cht.md](https://github.com/cloudronin/uofa/blob/main/docs/examples/hpt-blade-cht.md).

---

---

## The Jena Rule Engine (C3)

Quality gap detection uses [Apache Jena](https://jena.apache.org/) forward-chaining rules, not just SPARQL queries. The rule engine operates in two levels:

**Level 1 — Core detection rules** (21 patterns) match structural patterns against the evidence graph. Categories include epistemic (W-EP-*), aleatory (W-AL-*), ontological (W-ON-*), structural (W-SI-*), consistency (W-CON-*), provenance (W-PROV-*), and argumentation (W-AR-*). Run `uofa catalog` for the full list with descriptions.

**Level 2 — Compound inference rules** (2 active) fire on the output of Level 1 rules:

| Rule | What it detects |
|---|---|
| COMPOUND-01 | Critical + High weakeners coexist → escalated compound risk |
| COMPOUND-03 | Declared assurance level contradicts detected Critical gaps |

(COMPOUND-02 ships in the rules file but is currently commented out pending design review; `uofa catalog` filters it from listing output.)

The compound rules are the key differentiator versus SPARQL. They reason about the *interactions* between gaps — something that requires chained forward-chaining inference. All weakener rules evaluate in a single Jena forward-chaining pass, so compound rules can reason over the full weakener set.

For the data shape (Minimal vs. Complete profiles, CredibilityFactor, WeakenerAnnotation), see [docs/profiles.md](https://github.com/cloudronin/uofa/blob/main/docs/profiles.md).

---

---

## Integrity Verification

Every UofA carries a real cryptographic hash and digital signature — not placeholders.

| Level | What it checks | Mechanism |
|---|---|---|
| **Format gate** | Hash and signature are well-formed | SHACL `sh:pattern` regex on both Minimal and Complete profiles |
| **Content verification** | Hash matches the canonical document content | `uofa verify` recomputes SHA-256 from JSON canonical form |
| **Cryptographic signature** | Document was signed by the declared authority | ed25519 signature verification against the repo public key |

```bash
# Sign with your own key — the project's private key is not distributed
uofa keygen keys/my-project.key
uofa sign my-assessment.jsonld --key keys/my-project.key

# Verify integrity (against your key; omit --pubkey to use the repo's)
uofa verify my-assessment.jsonld --pubkey keys/my-project.pub
```

Placeholder strings (e.g., `sha256:placeholder...`) **fail** SHACL validation by design — a UofA claiming ProfileComplete must carry a real hash.

---

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
    --explain-model claude-sonnet-5
# requires ANTHROPIC_API_KEY in environment
```

Results are cached at `~/.uofa/cache/explain.db` — a second invocation
on the same input completes in <100 ms. Standalone re-interpretation of
cached output: `uofa explain --from-file cache.json`.

Full documentation:

- **[docs/explain.md](https://github.com/cloudronin/uofa/blob/main/docs/explain.md)** — usage, output formats, caching, limitations
- **[docs/llm-config.md](https://github.com/cloudronin/uofa/blob/main/docs/llm-config.md)** — `[llm]` section, supported backends, precedence
- **[docs/security.md](https://github.com/cloudronin/uofa/blob/main/docs/security.md)** — API key handling, threat model

---

---

## Domain Packs

SHACL shapes, Jena rules, templates, and extraction prompts are organized into **domain packs** under `packs/`. The `core` pack ships with standards-agnostic credibility assessment rules (23 weakener patterns). The `vv40` pack provides the ASME V&V 40-2018 factor taxonomy (13 factors), and the `nasa-7009b` pack provides the NASA-STD-7009B factor taxonomy (19 factors, including 6 NASA-only lifecycle factors).

```bash
uofa packs            # list installed packs + counts
uofa check FILE --pack vv40                  # use V&V 40
uofa check FILE --pack vv40 --pack nasa-7009b  # combine packs
```

The `--pack` flag on any command switches the active pack(s). Multiple packs can be specified to combine factor taxonomies and rules. Per-project rules files next to the input file still take precedence over the pack default. See [`packs/README.md`](https://github.com/cloudronin/uofa/blob/main/packs/README.md) for the full pack contract.

---

## Assess a published model card

Every other pack assesses an assurance package *you authored*. The
`model-credibility` pack assesses **someone else's published model card** — and
it answers two questions that are deliberately kept apart.

```bash
# Documentation completeness + evaluation sufficiency, from a HuggingFace id
uofa report allenai/OLMo-2-1124-13B-Instruct --pack model-credibility

# Scope the assessment to a decision you are actually making
uofa report owner/model --pack model-credibility \
    --cou "clinical triage screening" --mrl 3

# Attach independently furnished benchmark results
uofa report owner/model --pack model-credibility --raidex-hub
```

### The two sections, and the firewall between them

| Section | Asks | Standard |
|---|---|---|
| **[1] Documentation completeness** | does this model document itself? | NIST AI RMF 1.0 |
| **[3] Evaluation sufficiency** | are the reported numbers interpretable as evidence? | NIST AI 800-3 |

A benchmark score with no uncertainty, no null baseline, and no stated context of
use is **a number, not evidence**. Section [3] assesses reported results the way
V&V 40 assesses a simulation validation study.

**A card with no reported evaluation cannot produce a section [3] finding.** That
is structural, not a convention: every evaluation-sufficiency rule body binds
`uofa:hasValidationResult`, so there is no configuration in which a
documentation-only card is accused of insufficient evaluation. The readout says
*"no reported evaluation to assess"* — a different claim from finding nothing
wrong, and it is rendered differently.

### Reported, furnished, and the divergence between them

`evidenceSource` separates a score the card's authors published (`reported`) from
one an independent run produced (`furnished`). That distinction is what makes
`W-EV-DIV-07` expressible: when a card's own number and an independent
measurement of the same benchmark disagree beyond tolerance, that is a finding
about the record. **It does not establish which number is correct**, and the
rule's wording does not imply it does.

### What gets pinned

Assessing an artifact you do not control means recording exactly which bytes you
read. `sourcePin` carries two kinds, and they support different claims:

- **artifact pin** — re-derivation. For a HuggingFace card that is the `README.md`
  **blob oid**, never the repo sha: a repo sha moves when *any* file changes, so
  pinning it would mark a byte-identical card stale on a weights re-upload.
- **occasion pin** — re-performance only. A hosted endpoint's identity is what the
  provider asserts and can change under a stable name, so a furnished score pins
  *when it was measured*, and says so.

Full pack contract, the ten weakeners and their grounding:
[`packs/model-credibility/README.md`](https://github.com/cloudronin/uofa/blob/main/packs/model-credibility/README.md).

---

---

## Interrogate a Surrogate (SIP)

UofA's shift-left front door for **physics-AI surrogates** (ROMs, PINNs, operator-learning, data-driven emulators, ML closures). Point it at your surrogate and get a principled, auditable read on **when to trust it** — run it yourself in minutes.

`uofa interrogate` is a **measurement instrument, not a verdict.** It runs your surrogate against a benchmark, compares to a supplied reference, and emits a **signed, provenance-bearing evidence bundle** plus an at-a-glance comparison — per-QoI residuals, envelope coverage, physics-constraint residuals, UQ calibration. It **never** prints pass/fail: measure-don't-judge is the firewall. The output is trust-calibration evidence *for you to judge*.

**What you supply** (your surrogate stays behind one thin adapter — UofA never imports your ML framework):

| Input | Flag | What it is |
|---|---|---|
| Adapter | `--adapter` | a tiny `ModelAdapter` wrapping your model's `predict` (ONNX / torch / sklearn / remote) |
| Benchmark | `--benchmark` | the evaluation inputs (`.npz` / `.json`) |
| Reference | `--reference` | the truth to compare against — **supplied, never generated** |
| Scope | `--scope` | the declared training envelope + evaluation point |

```bash
# guided setup — or non-interactively for CI/containers:
#   uofa interrogate init --yes --scope sip_scope.json --output-names lift_coefficient
uofa interrogate init --model my_surrogate.onnx

# measure → signed evidence bundle + verdict-free comparison
uofa interrogate \
  --adapter sip_adapter.py:GeneratedAdapter \
  --benchmark bench.npz --reference truth.npz --scope sip_scope.json \
  -o evidence.json --key keys/my-project.key
```

**Try it now** on a committed surrogate evidence package (no model or data needed) — the surrogate pack's weakener catalog flags where the credibility evidence is incomplete:

```bash
uofa rules packs/surrogate/examples/airfrans/cou1/uofa-surrogate-airfrans-cou1.jsonld --pack surrogate
```

**Reading the output.** Residuals, coverage, and UQ are *measurements*; the pack's weakeners flag *evidence gaps* (e.g. an evaluation point outside the declared envelope, an unlinked residual). **Zero weakeners is not a guarantee of accuracy** — it means the evidence package is complete and auditable, and the trust decision is yours (`uofa decision sign`). In the appliance, a stock-Qwen explanation rides on top as **reference annotation** (decode, clearly labeled) — it explains the flags, it never adjudicates them.

**The appliance (one command).** The concept appliance bundles the core + the surrogate pack + a stock explainer in one container; the two-container demo feeds it live signals from a PhysicsNeMo-CFD container through the SIP interface:

```bash
docker compose up        # signals-in → explained, signed, verdict-free evidence-out
```

See [Domain Packs](#domain-packs) for the `--pack surrogate` catalog, and `docs/UofA_PostRefactor_Phase_A_Implementation_Plan.md` for the appliance build.

---

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

Full command reference (extract, import, init, validate, packs, migrate, schema, …) lives in [docs/onboarding.md](https://github.com/cloudronin/uofa/blob/main/docs/onboarding.md#cli-command-reference).

---

---

## What extraction is actually worth

### With no model: `--keyless`

| field | route | measured |
|---|---|---|
| validation results | trained classifier | recall@5 **0.438** vs a 0.125 control |
| decision outcome | trained classifier | **0.917** balanced; 5 of 6 rejections vs 0 |
| model & dataset names | named-entity patterns | 0.418 / 0.088 |
| context of use | definitional match | V&V 40 only — correctly silent on 7009A |
| **per-factor levels** | — | **left blank**: the best keyless route scores 0.100 end to end, and a wrong level validates |

On five real journal papers it produces a conforming package for the three V&V 40
documents. The two NASA-STD-7009A documents fail, and **correctly**: 7009A defines
no context of use, so there is nothing to derive a bound requirement from, and the
package says so rather than inventing one.

The two trained routes need `scikit-learn`. Without it they report themselves
unavailable and the run names the fields that went unattempted.

### With a model

This section used to report **F1 = 1.000** on the Morrison case, **0.973** on an
aero HPT blade, and **0.964 dev / 0.954 test** across a 50-bundle synthetic
corpus, with "all 19 factors detected at 100% rate".

**Those numbers measure detection, and detection cannot discriminate here.**
`control_constant_list` — a function that prints the standard's checklist and
reads nothing at all — scores **1.000 on the real corpus** and 0.960 on the
synthetic one. A published credibility assessment enumerates every factor and
scores absent evidence rather than omitting the row; that is what the artefact
*is*. So any evaluation built on detection ranks a null model at the top, and
this is not a corpus defect that a better corpus fixes.

The same eval reported `mean overall F1 0.964 — PASS` while **37 of 45 packages
failed the SHACL shape**.

Measured on **five real journal papers** with gpt-5 (2026-08-08), against
annotated gold:

| | measured | its control |
|---|---|---|
| validation results found, recall@5 | **11 of 24** (0.458) | 1 of 24 |
| rationale claims traceable to the source | **83 of 84** (0.988) | — |
| per-factor levels filled | 65 of 65 | — |
| **packages that validate** | **5 of 5** | a null extractor: **0** |

Two cautions that belong with those figures. **Groundedness is not
correctness** — 0.988 says the numbers in a rationale appear in the document, not
that the level assigned is right. And **per-factor levels are reported as filled,
not as correct**: the papers grade a letter within a range (`b` of `a-c`) while
the template takes an integer, and scoring one against the other would measure
the mapping rather than the extractor.

The full method and the seeded-corpus work behind it are in
[docs/keyless-hybrid-ceiling.md](https://github.com/cloudronin/uofa/blob/main/docs/keyless-hybrid-ceiling.md) and
[docs/extract_eval_v1.md](https://github.com/cloudronin/uofa/blob/main/docs/extract_eval_v1.md).

To use a remote backend instead (faster, costs money):

```bash
uofa extract path/to/evidence/ --pack vv40 \
    --extract-backend anthropic --extract-model claude-sonnet-4-6 -o extracted.xlsx
# requires ANTHROPIC_API_KEY in environment
```
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

For a zero-install try-it-out path, see [docs/onboarding.md](https://github.com/cloudronin/uofa/blob/main/docs/onboarding.md#zero-install-option-github-codespaces).

---

---

## Further reading

- **[docs/onboarding.md](https://github.com/cloudronin/uofa/blob/main/docs/onboarding.md)** — combined quick-start + architecture + contributor guide; full CLI reference
- **[docs/profiles.md](https://github.com/cloudronin/uofa/blob/main/docs/profiles.md)** — Minimal/Complete profiles, CredibilityFactor schema, WeakenerAnnotation schema
- **[docs/architecture.md](https://github.com/cloudronin/uofa/blob/main/docs/architecture.md)** — One UofA per Context of Use (the data model in tree form)
- **[docs/examples/hpt-blade-cht.md](https://github.com/cloudronin/uofa/blob/main/docs/examples/hpt-blade-cht.md)** — Aerospace companion case study (NASA-STD-7009B)
- **[docs/explain.md](https://github.com/cloudronin/uofa/blob/main/docs/explain.md)** — `--explain` flag deep dive
- **[docs/design.md](https://github.com/cloudronin/uofa/blob/main/docs/design.md)** — Research context + design principles
- **[docs/adversarial.md](https://github.com/cloudronin/uofa/blob/main/docs/adversarial.md)** — Adversarial generation tooling (research instrument)
- **[docs/repo-layout.md](https://github.com/cloudronin/uofa/blob/main/docs/repo-layout.md)** — Top-level repo orientation for contributors

---

---

## License

Apache License, Version 2.0 — see [LICENSE](https://github.com/cloudronin/uofa/blob/main/LICENSE) for the full text and
[NOTICE](https://github.com/cloudronin/uofa/blob/main/NOTICE) for bundled-software attributions.

The full project (UofA ontology, JSON-LD context, SHACL shapes, reference
examples, Jena rule implementations, and the CLI) is licensed under
Apache 2.0. Bundled third-party components retain their own licenses
as enumerated in `NOTICE` (e.g., OpenJDK GPLv2-CE, Ollama MIT).

---

---

## Contributing

Contributions are welcome, especially real-world UofA examples from practitioners working with CM&S credibility assessment. If you are preparing a CM&S-supported regulatory submission and want to explore UofA packaging for your evidence, please reach out.

For contributors, see [CONTRIBUTING.md](https://github.com/cloudronin/uofa/blob/main/CONTRIBUTING.md), [docs/repo-layout.md](https://github.com/cloudronin/uofa/blob/main/docs/repo-layout.md), and [docs/onboarding.md](https://github.com/cloudronin/uofa/blob/main/docs/onboarding.md).

**Website:** [uofa.net](https://uofa.net)
