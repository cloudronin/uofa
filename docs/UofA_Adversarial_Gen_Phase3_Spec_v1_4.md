# UofA Adversarial Generator — Phase 3 Specification v1.4

**Target repo:** github.com/cloudronin/uofa
**Author:** Vishnu Vettrivel
**Date:** April 26, 2026
**Supersedes:** UofA_Adversarial_Gen_Phase3_Spec_v1.3.md (April 26, 2026, same-day revision)
**Phase 2 status:** Targeted for completion May 24, 2026 (per Phase 2 Spec v1.3)
**Phase 3 target window:** June 1 – June 28, 2026 (4 weeks, overlaps reframe execution window)

**Dependencies:**

* Phase 2 completion: ~3,231 synthetic packages and rule-engine outcomes
* `v0.4.1-phase2-complete` tag
* External API access: OpenAI (`OPENAI_API_KEY`) and Google (`GEMINI_API_KEY`)
* HuggingFace Inference Endpoints account with billing enabled (~$60 budget for the Llama judge)
* LLM judge budget: ~$580 across calibration plus full-corpus judgment for three judge families, with $150 contingency
* Reframe Plan v5 §3 Gate 2 trigger condition references Phase 3 Stage 4 inter-judge agreement statistics

---

## Changelog: v1.3 → v1.4

Major scope expansion plus methodology upgrades. Five substantive changes:

| Change | Detail |
|---|---|
| Full-corpus judgment scope | v1.3 judged ~400 COV-MISS plus COV-WRONG cases. v1.4 judges all ~3,231-4,000+ Phase 2 packages including COV-HIT. Verdict schema extends from 5 classes to 6 with CORRECT-DETECTION added. |
| Three-judge ensemble | v1.3 required two cross-family judges. v1.4 requires three. Default: GPT-5.4 (OpenAI), Gemini 3.1 Pro (Google), Llama 3.3 70B (Meta, hosted via HuggingFace Inference Endpoints). Triage logic shifts from unanimity-of-2 to majority-of-3. |
| State-of-the-art model selection | v1.3 default judges were GPT-4.1 and Gemini 2.5 Pro. v1.4 uses current SOTA flagships GPT-5.4 (released March 2026) and Gemini 3.1 Pro (released February 2026), both with extended reasoning ("thinking") mode enabled for the judgment task. |
| Kappa-improvement methodology | New §7.5 specifies prompt design choices that lift inter-judge agreement: few-shot examples per verdict class drawn from calibration set, structured chain-of-thought scaffold, calibration-driven prompt refinement on weakest verdict classes, temperature 0.0 with fixed seed. Realistic kappa target moves from ≥0.6 (v1.3) to ≥0.70 (v1.4). |
| Cost optimization | Prompt caching enabled by default (~90% discount on the static framework context, ~12K of the 15K per-call input). Batch API used for the full-corpus runs (50% discount on both vendors, no latency requirement). HF Endpoints for Llama uses dedicated 1x H200 instance with single-spinup-per-session lifecycle. |

Three secondary changes:

| Change | Detail |
|---|---|
| Stratified-sample adjudication backstop | New §11.4 defines a queue-management protocol. If the DIVERGENT plus UNCERTAIN queue exceeds 30 hours of author time, the author may sample stratified across §6.7 Tier 1 mappings, source taxonomies, and confidence levels rather than adjudicating the full queue. |
| Architecture simplification | The v1.3 Llama provider via local Ollama is removed. HF Inference Endpoints exposes an OpenAI-compatible API, so the existing OpenAI provider class is reused with a different `base_url` and API token. The provider module count drops from 4 to 2. |
| Schedule densification | Author hours rise from 40 (v1.3) to ~50-55 (v1.4) due to 10x larger corpus, 3-judge calibration overhead, and prompt iteration for kappa improvement. The 4-week window still holds. |

All other v1.3 content (§13 pattern formalization, §13.4 ANOVA analysis, §17 reframe coordination, §20 paper addendum stub) preserved with light edits.

---

## 1. Purpose

Phase 3 resolves the Phase 2 output, approximately 3,231-4,000+ synthetic packages across all coverage classes (COV-HIT, COV-MISS, COV-WRONG), into a concrete set of catalog actions. For each package, the protocol determines whether the rule-engine outcome represents one of six verdict classes:

* **CORRECT-DETECTION** (new in v1.4) — the package legitimately instantiates the target defeater AND the expected rule fired correctly. The COV-HIT case behaved as intended.
* **REAL-GAP** — the package correctly instantiates the target defeater, the expected rule should have fired, but it did not. Routes to formalization as a new Jena rule.
* **GENERATOR-ARTIFACT** — the synthetic package did not actually instantiate the target defeater despite the prompt template's intent. Routes to prompt template debugging.
* **EXISTING-RULE-MISBEHAVIOR** — an existing rule fired when it should not have (false positive on COV-WRONG), or did not fire when it should have (false negative on COV-MISS). Routes to existing-rule refinement.
* **OUT-OF-SCOPE** — the defeater falls outside the deliberate scope of the UofA catalog. Routes to §2.9 documentation in the praxis.
* **UNCERTAIN** — judge cannot determine confidently. Escalates to author adjudication.

The praxis-scope protocol uses three cross-family LLM judges for first-pass triage and the author for adjudication of judge disagreements and any case flagged UNCERTAIN by a majority of judges. Calibration against an author-annotated 30-case ground-truth set (5 cases per verdict class) establishes per-judge accuracy. Pairwise Cohen's kappa across the three judge pairs plus Fleiss' kappa across all three judges establish how stable the catalog conclusions are across model families.

This protocol is sufficient to defend a methodology contribution in the praxis. It is not a substitute for external expert validation. Three cross-family judges trained on overlapping public corpora provide stronger triangulation than two, but they do not eliminate the shared-training-data validity caveat. The author-annotated calibration set anchors per-judge accuracy against a human-curated ground truth, but the calibration author and the praxis author are the same person. This remains the central limitation of the praxis-scope protocol and is documented as such in Ch3. The paper addendum (§20) will add an Upwork expert reviewer panel and report Cohen's κ(judge, median human) plus Fleiss' κ(humans).

Phase 3 outputs feed two praxis artifacts:

* **Catalog extension (v0.5)** — up to 6 new Jena rules corresponding to empirically confirmed §6.7 Tier 1 candidates, each accompanied by unit tests and pre-assigned severity from Reframe Plan v5 §6.7
* **Case study re-run delta table** — Morrison COU1, Morrison COU2, and Nagaraja analyzed with both v0.4.1 and v0.5 catalogs, showing the empirical impact of the extensions

---

## 2. What Phase 2 delivered (Phase 3 inputs)

By May 24, 2026, the following artifacts are expected on `v0.4.1-phase2-complete`:

* Phase 2 full corpus, ~3,231 synthetic packages in `out/adversarial/phase2/` with outcomes classified per §10 of Phase 2 Spec
* Coverage matrix CSV at `coverage/matrix.csv` with per-spec outcome class and source_taxonomy attribution
* Precision/recall summary at `coverage/summary.csv` with headline metrics
* Figure 3.x two-axis HTML View 2 PDF export
* Phase 2 judge-ready bundle at `out/adversarial/phase2/judge_ready_bundle.tgz`, compressed bundle of all JSON-LD packages (not just COV-MISS/COV-WRONG as in v1.3) plus rule-engine outputs and metadata ready for judge ingestion

If Phase 2 underdelivers package count materially, the v1.4 stratified-sample adjudication backstop (§11.4) handles the scope gracefully without requiring a spec revision.

---

## 3. Phase 3 scope summary

| Scope item | Count / deliverable |
|---|---|
| New CLI subcommand | `uofa adversarial judge` with `--judges` flag accepting comma-separated provider names |
| Judge provider modules | 2 (OpenAI-compat for both GPT-5.4 and Llama-via-HF-Endpoints, Gemini for Gemini 3.1 Pro) |
| Required judges | 3 cross-family: GPT-5.4 (OpenAI), Gemini 3.1 Pro (Google), Llama 3.3 70B (Meta via HF Endpoints) |
| Judge prompt template | 1 primary (v1.0.0) with few-shot examples per verdict class; identical prompt for all three judges |
| Calibration set | 30 cases with author ground-truth annotations (5 per verdict class across 6 classes) |
| Full-corpus judgment | All Phase 2 packages, expected 3,231-4,000+ × 3 judges |
| Author adjudication queue | DIVERGENT plus UNCERTAIN cases under majority-of-3 logic, expected 400-700 cases at pairwise κ ≈ 0.70-0.78 |
| Stratified-sample adjudication | Optional cap at 200-300 cases drawn proportionally across §6.7 Tier 1 mappings, source taxonomies, and confidence levels if queue exceeds 30 author hours |
| Agreement statistics | Pairwise Cohen's κ for all 3 pairs, Fleiss' κ across all 3 judges, per-judge calibration accuracy, confusion matrices |
| Pattern formalization | Up to 6 new Jena rules (§6.7 Tier 1 validated) |
| Case study re-run | Morrison COU1, Morrison COU2, Nagaraja (if encoded) with v0.5 catalog |
| Total budget | ~$580 LLM judge spend with $150 contingency |

### Budget breakdown

| Component | Cost |
|---|---|
| GPT-5.4 with thinking, full corpus 4,000 cases (cached + batch) | ~$220 |
| Gemini 3.1 Pro with thinking, full corpus 4,000 cases (cached + batch) | ~$150 |
| Llama 3.3 70B via HF Endpoints (1x H200 at $5/hr × ~10 hrs realistic) | ~$50 |
| Calibration plus tuning iterations across 3 judges | ~$30 |
| Retry overhead and re-runs (~10%) | ~$45 |
| Contingency (25%) | ~$120 |
| **Total** | **~$615** |

### Phase 3 stages

```
Phase 2 output (~3,231-4,000+ packages, all coverage classes)
      │
      ▼
Stage 1: Calibration set construction + per-judge calibration runs (3 judges)
      │   target: each judge ≥ 80% accuracy on 30-case set; pairwise κ ≥ 0.70 on calibration
      ▼
Stage 2: Full-corpus judgment with all three judges
      │   ~4,000 × 3 → verdict + confidence + reasoning per case per judge
      ▼
Stage 3: Majority-of-3 inter-judge agreement triage
      │   CONVERGENT (≥2 agree) / DIVERGENT (all disagree or 2+UNCERTAIN) / UNCERTAIN (majority UNCERTAIN)
      ▼
Stage 4: Author adjudication of DIVERGENT and UNCERTAIN cases
      │   Pairwise Cohen's κ, Fleiss' κ, confusion matrices, adjudication record
      ▼
Stage 5: Pattern formalization + case study re-run + ANOVA robustness analysis
        → v0.5 catalog, delta table, methodology section drafted
```

---

## 4. Design principles

Eight principles govern Phase 3 execution. They extend but do not supersede Phase 1 and Phase 2 principles.

1. **Generator-judge family independence.** All three judges MUST come from a different model family than the generator. Generation used Claude (Anthropic). Judgment uses GPT-5.4 (OpenAI), Gemini 3.1 Pro (Google), and Llama 3.3 70B (Meta via HF Endpoints). Same principle as the extract-vs-generator circularity check in Phase 1 §7.2, applied to the next layer of the methodology.

2. **Cross-family judge independence within the ensemble.** The three required judges must all come from different model families. Two GPT variants would not satisfy this. The OpenAI-Google-Meta combination satisfies the requirement.

3. **Majority triage with author adjudication.** First-pass classification uses majority-of-3 across the judge ensemble. Cases where ≥2 judges agree on a verdict are CONVERGENT. Cases where all three disagree, or where two disagree and one is UNCERTAIN, route to the author adjudication queue. Cases where ≥2 judges return UNCERTAIN route to the author. The author adjudicates with documented rationale.

4. **Author as sole adjudicator with explicit validity caveat.** Phase 3 has no external human reviewer panel. The author adjudicates the queue and annotates the 30-case calibration ground truth. Three-judge ensemble agreement is reported as model concordance, not as ground-truth validity. Per-judge calibration accuracy on the author-annotated set is the validity anchor for the praxis. The praxis Ch3 documents this honestly. The paper addendum (§20) will introduce external reviewers for upgraded validity claims.

5. **Pre-calibration before trust.** No judge verdicts are treated as authoritative until calibration accuracy is at least 80% on the 30-case ground-truth set, computed independently for each judge. If a judge's default prompt fails this threshold, prompt tuning is required before Stage 2 for all judges (single prompt across the ensemble per Principle 6). Calibration accuracy and inter-judge calibration κ are published metrics.

6. **Single shared prompt across the ensemble.** All three judges receive identical prompts. This isolates inter-judge disagreement to model differences rather than prompt differences. Per-judge prompt tuning is not permitted; the prompt is tuned once against the calibration set and applied uniformly.

7. **Disagreement as data, not noise.** Three-way disagreements are preserved in the outputs and analyzed statistically. They do not get discarded or averaged away. Pairwise Cohen's κ for all three pairs reveals which judge pairs systematically disagree. Author adjudication resolves them for catalog decisions but the raw disagreement data remains in the praxis supplementary materials.

8. **Traceability end-to-end.** Every Phase 3 judgment from each judge traces to a specific Phase 2 package, which traces to a Phase 1 prompt template, which traces to a source taxonomy sub-type. Every catalog extension traces to specific majority-of-3 or author-adjudicated REAL-GAP verdicts. The trace chain is machine-queryable via the existing provenance infrastructure.

---

## 5. Architecture additions

### 5.1 Module layout

```
uofa/
├── adversarial/
│   ├── judge/                            # NEW (Phase 3)
│   │   ├── __init__.py
│   │   ├── cli.py                        # `uofa adversarial judge` subcommand
│   │   ├── judge.py                      # LLMJudge class, prompt assembly, parsing
│   │   ├── prompts.py                    # Judge prompt templates (v1.0.0) with few-shot examples
│   │   ├── calibration.py                # Calibration set loader + per-judge scorer + cross-judge κ
│   │   ├── caching.py                    # Prompt caching helpers (vendor-specific cache key handling)
│   │   ├── batch.py                      # Batch API submission and result polling for OpenAI/Gemini
│   │   └── providers/
│   │       ├── __init__.py
│   │       ├── base.py                   # AbstractJudgeProvider
│   │       ├── openai_compat.py          # OpenAI-compatible API; serves OpenAI proper AND HF Endpoints
│   │       └── gemini.py                 # Google Gemini API
│   ├── triage.py                         # NEW - majority-of-3 inter-judge agreement bucketing
│   ├── adjudication.py                   # NEW - author adjudication + pairwise + Fleiss κ
│   └── formalization.py                  # NEW - REAL-GAP → Jena rule scaffold
specs/
└── calibration/                          # NEW
    └── calibration_set_v1.jsonl          # 30 cases with author ground-truth (5 per verdict class)
packs/
└── core/
    └── judge_prompts/                    # NEW
        ├── v1.0.0.md                     # base prompt template
        └── v1.0.0_few_shot/              # few-shot examples per verdict class
            ├── correct_detection.json
            ├── real_gap.json
            ├── generator_artifact.json
            ├── existing_rule_misbehavior.json
            ├── out_of_scope.json
            └── uncertain.json
tests/
└── adversarial/
    └── judge/
        ├── test_judge.py
        ├── test_calibration.py
        ├── test_triage.py
        ├── test_adjudication.py
        ├── test_formalization.py
        ├── test_caching.py
        ├── test_batch.py
        └── fixtures/
            └── mock_judgments_5_case.jsonl
```

### 5.2 New dependencies

* `openai` (OpenAI SDK), used for both OpenAI proper and HF Endpoints OpenAI-compat
* `google-generativeai` (Gemini SDK)
* `scikit-learn` (for Cohen's κ)
* `statsmodels` (for Fleiss' κ and confusion matrix utilities)
* `huggingface_hub` (for HF Endpoints lifecycle management; spinup, monitoring, scale-down)

The HF Endpoints integration uses the OpenAI-compatible API exposed by HuggingFace Text Generation Inference (TGI), so no new client SDK is needed. The endpoint URL and auth token go in `OPENAI_API_KEY_HF` and `OPENAI_BASE_URL_HF` environment variables; the existing OpenAI provider class is instantiated with these instead of the OpenAI defaults.

---

## 6. Judge model selection and circularity

### 6.1 Required judges

Three judges are required.

| Position | Model | Provider | Family | Hosting |
|---|---|---|---|---|
| Judge A | gpt-5.4 with thinking | OpenAI | GPT | OpenAI API direct |
| Judge B | gemini-3.1-pro with thinking | Google | Gemini | Google Generative AI API direct |
| Judge C | meta-llama/Llama-3.3-70B-Instruct | Meta | Llama | HuggingFace Inference Endpoints (1x H200, OpenAI-compat) |

All three judges use the same prompt template (§7), the same low-temperature decoding (`temperature=0.0`, `seed=42`), and run independently on the full corpus.

### 6.2 Family circularity check

On startup, the judge command inspects the generator model configuration from the Phase 2 output and verifies each configured judge is from a different family than the generator and from any other configured judge. Family mapping:

| Provider | Family |
|---|---|
| anthropic | Claude |
| google | Gemini |
| openai | GPT |
| meta / huggingface:meta-llama/* | Llama |
| ollama:qwen* | Qwen |

If any judge family matches the generator family or another judge family, the command exits with code 5 and a diagnostic message.

The `--allow-same-family-judge` flag overrides (exits 0 with prominent warning), intended only for Stage 0 smoke testing, never for Stage 2 full-corpus runs.

### 6.3 Training data overlap caveat

GPT-5.4, Gemini 3.1 Pro, and Llama 3.3 70B may share training data on V&V 40, safety assurance, and credibility framework literature. This is a known limitation of all LLM-as-judge methodology. Three cross-family judges reduce single-family training-data dependence but do not eliminate it. Documented in Ch3 methodology section as a limitation with references to the LLM-as-judge literature (Zheng et al. 2023 MT-Bench, Dubois et al. 2024 AlpacaEval). The paper addendum (§20) addresses this via expert human reviewers.

### 6.4 Cost expectations

Per-judge cost estimate (April 2026 pricing, with prompt caching plus batch API where supported):

| Judge | Per-call cost (cached input + batch) | 4,000-case full-corpus cost |
|---|---|---|
| GPT-5.4 with thinking | ~$0.055 | ~$220 |
| Gemini 3.1 Pro with thinking | ~$0.038 | ~$150 |
| Llama 3.3 70B (HF Endpoints, 1x H200, ~10 hrs at $5/hr) | n/a (per-hour billed) | ~$50 |
| **Combined per-call equivalent** | **~$0.105** | **~$420** |

With calibration, prompt tuning iterations, retry overhead, and 25% contingency: total Phase 3 LLM budget ~$580-615.

### 6.5 HF Endpoints lifecycle for the Llama judge

HuggingFace Inference Endpoints uses per-hour GPU billing, so endpoint lifecycle matters for cost control:

* **Spinup:** ~10-15 minutes for 70B model load. Bills from spinup completion.
* **Warm operation:** ~$5/hr on 1x H200 141GB (AWS).
* **Scale-down:** Manual or via API after run completes. Do not use scale-to-zero between sessions during the active phase; cold restart costs ~10 minutes per session.

Recommended workflow:

| Session | Activity | Endpoint state | Duration |
|---|---|---|---|
| Calibration spinup | Load endpoint, warm up | Cold → warm | ~15 min |
| Calibration runs | Run 30-case set, up to 3 prompt iterations | Warm | ~2 hrs |
| Pause | Scale down endpoint | Off | days/weeks |
| Full-corpus spinup | Load endpoint, warm up | Cold → warm | ~15 min |
| Full-corpus run | Judge all 4,000 cases | Warm | ~10 hrs |
| Re-validation (if prompt changed) | Re-run calibration | Warm | ~30 min |
| Scale-down | After all judgments complete | Off | permanent |

Total HF Endpoints uptime budget: ~13 hours including spinup overhead. At $5/hr H200: ~$65 with buffer.

---

## 7. Judge prompt design

### 7.1 Prompt template v1.0.0 structure

The prompt has six sections assembled per-case. All three judges receive identical prompts.

1. **System framing** — role: "You are an expert in computational modeling and simulation credibility assurance, evaluating synthetic evidence packages generated for the Unit of Assurance (UofA) weakener catalog."
2. **Framework context** — V&V 40 overview, credibility factor definitions, UofA weakener catalog overview with all 14 patterns described
3. **Verdict class definitions with worked examples** — each of the 6 verdict classes defined with one canonical example drawn from the calibration set (few-shot anchor)
4. **Reasoning scaffold** — structured chain-of-thought template the judge must follow: (a) identify the source taxonomy, (b) identify the target rule, (c) inspect rule firings, (d) check whether package legitimately instantiates the defeater, (e) commit to verdict class
5. **Case content** — the full JSON-LD package, the Phase 2 outcome classification (COV-HIT / COV-MISS / COV-WRONG), which rules fired, which rule was expected
6. **Output instruction** — structured JSON output schema with strict field requirements

The framework context plus verdict class definitions plus reasoning scaffold (~12K tokens) is the static portion eligible for prompt caching. The case content (~3K tokens) varies per call.

### 7.2 Output schema

```json
{
  "case_id": "adv-2026-p2-002-gohar-data-drift-v03",
  "verdict": "CORRECT-DETECTION | REAL-GAP | GENERATOR-ARTIFACT | EXISTING-RULE-MISBEHAVIOR | OUT-OF-SCOPE | UNCERTAIN",
  "confidence": 0.87,
  "reasoning_steps": {
    "source_taxonomy_identified": "Gohar Evidence Validity / Data Drift",
    "target_rule_identified": "W-EV-01 (not yet in catalog)",
    "rule_firings_inspected": "No rules fired (COV-MISS)",
    "instantiation_check": "Package correctly instantiates Data Drift: validation dataset vintage 2018 predates model revision 2024 with no re-calibration",
    "verdict_commitment": "REAL-GAP"
  },
  "reasoning": "The package correctly instantiates Gohar Data Drift...",
  "section_6_7_candidate": "W-EV-01",
  "alternative_rule_analysis": "W-CON-03 shares some temporal semantics but operates on future-dated evidence only; not applicable here.",
  "prompt_template_version": "v1.0.0",
  "judge_model": "gpt-5.4",
  "judge_thinking_enabled": true,
  "judge_model_params": {
    "temperature": 0.0,
    "seed": 42
  },
  "generator_provenance": {
    "generator_model": "anthropic/claude-sonnet-4-6",
    "temperature": "N/A",
    "seed": "N/A"
  }
}
```

The `reasoning_steps` field is the structured chain-of-thought output. It's the single most effective lever for kappa improvement (§7.5).

### 7.3 Verdict class definitions in prompt

Each of the 6 verdict classes has a one-paragraph definition the judge sees, followed by one worked example from the calibration set. The 6-class structure handles COV-HIT (CORRECT-DETECTION), COV-MISS (REAL-GAP if package legitimate, else GENERATOR-ARTIFACT or OUT-OF-SCOPE), and COV-WRONG (EXISTING-RULE-MISBEHAVIOR if rule misfired, else GENERATOR-ARTIFACT). UNCERTAIN is the explicit escape hatch.

### 7.4 Prompt tuning methodology

Calibration is the tuning loop. Initial prompt → calibration run for each judge → per-judge accuracy check → prompt refinement if any judge is below 80% OR if pairwise calibration κ is below 0.70 → re-run for all three judges. Each prompt version is committed to `packs/core/judge_prompts/vX.Y.Z.md` with a changelog. Per Principle 6, all judges use the same final prompt version.

Up to 3 tuning iterations. If thresholds not met after 3 iterations, escalate per §8.3.

### 7.5 Kappa-improvement methodology (new in v1.4)

Five prompt design choices lift inter-judge agreement, ranked by expected impact:

| Lever | Implementation | Expected κ lift |
|---|---|---|
| Few-shot examples per verdict class | One canonical example per class drawn from calibration set, embedded in prompt §3 | +0.10-0.15 |
| Structured chain-of-thought scaffold | Required `reasoning_steps` field with 5 named sub-fields, judge must populate before committing verdict | +0.05-0.10 |
| Calibration-driven prompt refinement | After calibration, identify the lowest-accuracy verdict class per judge; revise that class's definition and worked example; re-run calibration | +0.05-0.10 |
| Temperature 0.0 + fixed seed | Both vendors support; reduces stochastic disagreement | +0.02-0.05 |
| SOTA models with thinking enabled | GPT-5.4 + Gemini 3.1 Pro both with extended reasoning | +0.05-0.08 (already baked into model selection) |

Combined expected lift over the v1.3 baseline (~0.6): ~0.70-0.78 pairwise κ achievable. Realistic v1.4 target: ≥0.70 pairwise κ. Target of 0.85 is unrealistic for defeater triage and should not be pursued through prompt engineering tricks that risk biasing the judges.

### 7.6 Anti-patterns prohibited in prompt design

To preserve methodology validity, the prompt must NOT:

* Bias toward a default verdict (e.g., "when uncertain, default to GENERATOR-ARTIFACT")
* Include the §6.7 expected mapping for the case being judged
* Show one judge the verdict from another judge
* Remove UNCERTAIN as a verdict class
* Reduce the verdict class count for ease of judging

Any of these would inflate kappa while destroying its meaning. Honest agreement at κ = 0.72 is more defensible than gamed agreement at κ = 0.92.

---

## 8. Calibration methodology (Stage 1)

### 8.1 Calibration set construction

30 cases with author-annotated ground truth, balanced across the 6 verdict classes:

| Verdict class | Count | Source |
|---|---|---|
| CORRECT-DETECTION | 5 | Author-selected from Phase 2 COV-HIT cases where rule firing matches expected target cleanly |
| REAL-GAP | 5 | Author-annotated from Phase 2 gap_probe COV-MISS where §6.7 mapping is clear-cut |
| GENERATOR-ARTIFACT | 5 | Author-constructed deliberately-broken packages (wrong defeater instantiated) |
| EXISTING-RULE-MISBEHAVIOR | 5 | Author-seeded packages: existing weakener instantiated but rule's SPARQL pattern fails to match (false negative), or rule fires on a package without the defeater (false positive) |
| OUT-OF-SCOPE | 5 | Author-constructed packages instantiating out-of-scope defeaters (subjective model-form adequacy, human factors) |
| UNCERTAIN | 5 | Author-annotated genuinely ambiguous cases from Phase 2 COV-WRONG outcomes |

### 8.2 Calibration set storage

```
specs/calibration/calibration_set_v1.jsonl
```

Each line follows the JSON schema in Appendix B.

### 8.3 Calibration accuracy targets

Per-judge accuracy = (count of judge verdicts matching ground truth) / 30, computed independently for each judge.

Pairwise calibration κ = Cohen's κ between each pair of judges on the 30-case set, before exposure to the full corpus.

* Per-judge target: ≥ 80% accuracy (24/30 correct) for each of the three judges
* Pairwise calibration κ target: ≥ 0.70 for all three pairs (GPT-Gemini, GPT-Llama, Gemini-Llama)
* Per-class accuracy target: ≥ 50% per verdict class per judge (soft within hard)

If thresholds not met on default prompt: tune prompt, version bump, re-run for all three judges. Up to 3 tuning iterations.

If after 3 iterations one judge remains below 80% but the other two meet it: proceed to Stage 2 with that judge flagged in agreement statistics. Document the failure mode in Ch3.

If after 3 iterations two or more judges remain below 80%: escalate. Options: (a) substitute a different SOTA flagship for the failing judge (e.g., GPT-5.4-pro variant), (b) accept lower per-judge accuracy with documented rationale, (c) expand calibration set to diagnose failure modes.

### 8.4 Per-class accuracy disclosure

In addition to overall per-judge accuracy, calibration output reports per-class accuracy for each judge. The per-class table appears in Ch3 methodology and is a soft gate (target ≥ 50% per class per judge). It also feeds the calibration-driven prompt refinement loop in §7.5.

---

## 9. Full-corpus judgment (Stage 2)

### 9.1 CLI surface

```bash
uofa adversarial judge \
  --in out/adversarial/phase2/judge_ready_bundle.tgz \
  --out out/adversarial/phase3/judgments/ \
  --judges openai,gemini,hf-llama \
  --model-openai gpt-5.4 \
  --model-openai-thinking enabled \
  --model-gemini gemini-3.1-pro \
  --model-gemini-thinking enabled \
  --model-hf-llama meta-llama/Llama-3.3-70B-Instruct \
  --hf-endpoint-url https://your-endpoint.endpoints.huggingface.cloud \
  --prompt-version v1.0.0 \
  --enable-prompt-caching \
  --enable-batch-api \
  --calibration-check \
  --parallel 8
```

`--judges` accepts a comma-separated list. Three required for v1.4 default. Cross-family circularity check (§6.2) applies before any judgment runs.

`--enable-prompt-caching` activates vendor-specific cache keys for the static prompt prefix (~12K tokens of framework context plus verdict class definitions plus reasoning scaffold). Both OpenAI and Gemini support cache hits at ~90% discount on cached input tokens.

`--enable-batch-api` submits the full-corpus judgments as batch jobs (24-hour SLA) for 50% discount on both OpenAI and Gemini. The HF Endpoints judge uses normal request flow (no batch concept on dedicated infrastructure).

### 9.2 Semantics

* Reads the Phase 2 judge-ready bundle (all packages, all coverage classes)
* For each package, loads the JSON-LD plus rule-engine output
* Assembles prompt per §7.1 (identical prompt for all judges, with cache-friendly static prefix)
* For OpenAI and Gemini: submits batched requests; polls for completion within 24 hours
* For HF Endpoints (Llama): runs synchronously with `--parallel 8` concurrent requests against the dedicated endpoint
* Writes per-case-per-judge judgment to `judgments/{case_id}__{judge}.json` and appends to `judgments_{judge}.jsonl`
* Aggregates per-judge statistics: verdict class distribution, confidence distribution, median processing time
* `--calibration-check` re-runs the calibration set across all three judges as a sanity check and warns if accuracy has drifted

### 9.3 Output

```
out/adversarial/phase3/judgments/
├── run_manifest.json            # meta: judge models, prompt version, timestamps, cache+batch flags
├── judgments_gpt54.jsonl
├── judgments_gemini31pro.jsonl
├── judgments_llama33_70b.jsonl
├── judgments_combined.jsonl     # joined per-case three-judge view
├── calibration_recheck.json     # per judge, if --calibration-check used
├── verdict_distribution_gpt54.csv
├── verdict_distribution_gemini31pro.csv
├── verdict_distribution_llama33_70b.csv
└── failures/                    # cases that failed all retries (per judge)
    ├── openai/
    ├── gemini/
    └── hf-llama/
```

### 9.4 Expected runtime and cost

| Judge | Approach | Wall clock | Cost |
|---|---|---|---|
| GPT-5.4 (batch) | Batch submission, 24-hour SLA | ~6-12 hrs (vendor-managed) | ~$220 |
| Gemini 3.1 Pro (batch) | Batch submission, 24-hour SLA | ~6-12 hrs (vendor-managed) | ~$150 |
| Llama 3.3 70B (HF Endpoints, parallel 8) | Synchronous against dedicated H200 | ~7-10 hrs | ~$50 |
| **Total combined** | Run all 3 in parallel windows | ~24-48 hr clock-time elapsed | **~$420** |

Author wall time during Stage 2 is minimal: submit batches, spin up HF endpoint, monitor periodically, scale down HF endpoint after Llama run completes.

---

## 10. Majority-of-3 inter-judge agreement triage (Stage 3)

### 10.1 Triage buckets

The triage module partitions the ~4,000 cases into three bins based on majority-of-3 inter-judge agreement:

| Bucket | Criteria | Expected size at pairwise κ ≈ 0.72 |
|---|---|---|
| CONVERGENT | ≥ 2 of 3 judges agree on verdict, all agreeing judges with confidence ≥ 0.6 | ~3,200-3,400 cases (~80-85%) |
| DIVERGENT | All 3 disagree, OR 2 disagree + 1 UNCERTAIN, OR ≥ 2 agree but with confidence < 0.6 | ~400-600 cases (~10-15%) |
| UNCERTAIN | ≥ 2 of 3 judges return UNCERTAIN | ~100-200 cases (~3-5%) |

DIVERGENT plus UNCERTAIN bins together (~500-800 cases at pairwise κ ≈ 0.72) form the candidate author adjudication queue.

### 10.2 Adjudication queue assembly

Each entry in the candidate adjudication queue includes:

* Case ID
* Source taxonomy attribution
* Excerpt of the synthetic package (~300 lines, critical fields highlighted)
* Phase 2 outcome summary (COV-HIT, COV-MISS, or COV-WRONG, rules that did and did not fire)
* All three judge verdicts, confidences, and `reasoning_steps` side-by-side
* Computed disagreement type (verdict mismatch breakdown, low-confidence concurrence, or UNCERTAIN majority)

Format: a single CSV `out/adversarial/phase3/adjudication_queue.csv` plus a directory `adjudication_packets/` with one Markdown packet per case for author reading.

### 10.3 Author adjudication time budget at scale

At ~2.5 minutes per case, the realistic queue of 500-800 cases is 21-33 hours of author time. This exceeds the v1.3 budget of ~6 hours and requires the §11.4 stratified-sample backstop if the queue lands at the upper end.

---

## 11. Author adjudication protocol (Stage 4)

### 11.1 Adjudication input

The author works through `adjudication_queue.csv` row by row, reading each Markdown packet. For each case, the author records:

* `final_verdict` — one of the six verdict classes
* `adjudication_rationale` — minimum 50 words for DIVERGENT cases, minimum 30 words for UNCERTAIN cases
* `agrees_with_judge_a` / `_b` / `_c` — booleans, derived for stats
* `would_add_to_catalog` — yes/no/depends, informs Stage 5 formalization
* `notes` — free-form, optional

Output: `out/adversarial/phase3/adjudications.jsonl`.

### 11.2 Adjudication conventions

For DIVERGENT cases, the author documents which judge's reasoning was most sound and why, then states the final verdict. The adjudication record is the audit trail for catalog decisions, so rationales must reference the package content, the source taxonomy, and the existing catalog.

For UNCERTAIN-majority cases, the author resolves to one of the five definite verdict classes if possible, or accepts UNCERTAIN as the final verdict if the case is genuinely ambiguous. Final UNCERTAIN verdicts are excluded from catalog-extension decisions but preserved in the agreement statistics.

### 11.3 Self-blinding sanity check

To partially mitigate adjudicator bias, the author records each adjudication before reading the §6.7 Tier 1 expectation tag for that case. The expectation tag is then revealed and a `post_hoc_alignment` field is recorded indicating whether the adjudication matched, contradicted, or was independent of the §6.7 expectation. This produces an honest signal of how much §6.7 expectation drives author adjudication versus how much the package content drives it.

### 11.4 Stratified-sample adjudication backstop (new in v1.4)

If the candidate adjudication queue exceeds 30 hours of estimated author time (i.e., > ~700 cases), the author may invoke stratified sampling instead of full-queue adjudication. The sampling design:

| Stratum | Sample size | Notes |
|---|---|---|
| §6.7 Tier 1 candidate cases (W-EV-01, W-EV-02, W-REQ-01, W-CX-01, W-AR-06, W-AR-07) | 100% of DIVERGENT or UNCERTAIN cases mapping to these | All §6.7 cases get author eyes regardless of queue size |
| Top 5 source taxonomies by COV-MISS frequency | 30 cases each across DIVERGENT bin (proportional sub-sampling within taxonomy) | Ensures coverage of the most frequent gap categories |
| All-three-disagree (worst-case DIVERGENT) | 100% of cases where all 3 judges produced different verdicts | These are the strongest signal of methodology fragility |
| Random sample of remaining DIVERGENT | Up to 50 cases | Maintains representativeness |
| Random sample of UNCERTAIN-majority | Up to 30 cases | Validates judge uncertainty calibration |

Total stratified sample: ~150-200 cases. Author time: ~6-8 hours.

The praxis claim under stratified-sample adjudication: "Three cross-family LLM judges judged all N packages at pairwise Cohen's κ = X, Y, Z. A stratified sample of N=200 author-adjudicated cases validated the protocol across §6.7 Tier 1 candidates, top source taxonomies, and worst-case three-judge disagreements. The sampling design and sample composition are documented in §11.4 of the Phase 3 specification."

This claim is committee-defensible because the stratification ensures every catalog-relevant case category gets author attention, and the sampling design is published rather than ad-hoc. It is the structural backstop that makes the 4,000-package scope tractable inside the June schedule.

The author chooses between full-queue adjudication and stratified-sample adjudication after Stage 3 based on the actual queue size. Decision logged in `out/adversarial/phase3/adjudication_method.txt` with rationale.

---

## 12. Agreement statistics (Stage 4 output)

### 12.1 Agreement metrics

Compute:

| Metric | Formula | Target |
|---|---|---|
| Per-judge calibration accuracy | (correct verdicts on cal set) / 30, per judge | ≥ 80% per judge |
| Per-class calibration accuracy | per judge × per verdict class | ≥ 50% per class per judge (soft) |
| Pairwise calibration κ | Cohen's κ on calibration set, per judge pair | ≥ 0.70 per pair |
| Pairwise full-corpus Cohen's κ | sklearn.metrics.cohen_kappa_score, per pair (3 pairs) | ≥ 0.70 per pair |
| Fleiss' κ across all 3 judges | statsmodels.stats.inter_rater.fleiss_kappa | ≥ 0.65 |
| Inter-judge raw agreement (≥ 2 of 3) | (cases where at least 2 judges agree on verdict) / total | ≥ 80% (informational) |
| Author-vs-judge agreement (per judge, per pair) | (cases where author final verdict = judge verdict) / total adjudicated | informational |
| Confusion matrix (each judge pair) | 6×6 | informational, 3 matrices |
| Confusion matrix (author vs each judge, on adjudicated subset) | 6×6 | informational, 3 matrices |

### 12.2 Output

```
out/adversarial/phase3/stage4/
├── agreement_stats.json         # all metrics computed above
├── confusion_matrix_AB.csv      # GPT-5.4 vs Gemini 3.1 Pro
├── confusion_matrix_AC.csv      # GPT-5.4 vs Llama 3.3 70B
├── confusion_matrix_BC.csv      # Gemini 3.1 Pro vs Llama 3.3 70B
├── confusion_matrix_author_A.csv
├── confusion_matrix_author_B.csv
├── confusion_matrix_author_C.csv
├── adjudications.jsonl          # author adjudications for queue (full or stratified)
├── adjudication_method.txt      # full-queue vs stratified-sample with rationale
├── final_verdicts.jsonl         # one line per adjudicated case with final verdict
├── disagreement_record.jsonl    # raw three-judge disagreements preserved for praxis appendix
└── stratification_audit.csv     # if stratified, full sampling design + selected case list
```

### 12.3 Disclosure in praxis

Every agreement metric and its value appears in the praxis Ch3 methodology section. Cases where any pairwise κ falls below 0.70 are disclosed with an honest explanation of which judge pair disagrees and why, rather than hidden. Fleiss' κ is reported alongside pairwise κ to give a single ensemble-level agreement number.

The validity caveat from §4 Principle 4 is restated in the Ch3 limitations alongside the metrics. Three-judge ensemble at Fleiss' κ ≥ 0.65 is meaningfully stronger than two-judge agreement, but it is still model concordance not ground-truth validity.

---

## 13. Pattern formalization (Stage 5)

### 13.1 Workflow per confirmed REAL-GAP

For each case where the final verdict (CONVERGENT majority-of-3 or author-adjudicated) is REAL-GAP:

1. Extract the defeater pattern from the source_taxonomy attribution and the judge or author reasoning.
2. Check §6.7 Tier 1 mapping. If the sub-type maps to a §6.7 candidate (W-EV-01 through W-AR-07), use the candidate's pre-documented pattern definition as the starting point. If no mapping, draft a new pattern definition.
3. Draft Jena rule using the existing rule authoring conventions in `packs/vv40/rules/`.
4. Define SHACL requirements if the new pattern requires vocabulary additions. Should be rare.
5. Assign severity. For §6.7 Tier 1 candidates, use the Reframe Plan v5 §6.7 pre-assigned severity (High for W-EV-01, W-EV-02, W-CX-01, W-AR-07; Medium for W-REQ-01, W-AR-06). Author may revise with documented rationale. For non-§6.7 new patterns, author judgment alone.
6. Unit-test the new rule against (a) the Phase 2 synthetic package that validated it, (b) Morrison COU1 + COU2, (c) Nagaraja. Verify rule fires where expected and does not fire where not expected.
7. Catalog entry added to `packs/vv40/weakener_catalog.json` with description, severity, V&V 40 factor mapping, remediation guidance.
8. Tag as `v0.5` once all confirmed rules are integrated.

### 13.2 Expected outcome per §6.7 Tier 1 candidate

| Candidate | Pre-assigned Severity (Reframe v5 §6.7) | Expected Phase 3 verdict | Outcome if confirmed |
|---|---|---|---|
| W-EV-01 (Stale validation data) | High | REAL-GAP | New Jena rule shipped in v0.5 |
| W-EV-02 (Inadequate metric) | High | REAL-GAP | New Jena rule shipped in v0.5 |
| W-REQ-01 (Ambiguous acceptance criterion) | Medium | REAL-GAP | New Jena rule shipped in v0.5 |
| W-CX-01 (Configuration divergence) | High | REAL-GAP | New Jena rule shipped in v0.5 |
| W-AR-06 (Eliminative argumentation absent) | Medium | REAL-GAP | New Jena rule shipped in v0.5 |
| W-AR-07 (Sustained defeater without residual-risk justification) | High | REAL-GAP | New Jena rule shipped in v0.5 |

Success criterion: ≥ 3 of 6 candidates validated as REAL-GAP through majority-of-3 agreement or author adjudication. Candidates not validated are documented in Ch5 limitations.

### 13.3 Case study re-run delta table

Run v0.5 catalog against:

* Morrison COU1 (Class II, MRL 2, Accepted)
* Morrison COU2 (Class III, MRL 5, Not accepted)
* Nagaraja COU1 (Class II orthopedic, MRL 3, Accepted)

| Case | v0.4.1 weakener count | v0.5 weakener count | Delta | New rules firing |
|---|---|---|---|---|
| Morrison COU1 | 14 | TBD | TBD | TBD |
| Morrison COU2 | 6 | TBD | TBD | TBD |
| Nagaraja | TBD | TBD | TBD | TBD |

This table becomes Figure N in the praxis Ch5.

### 13.4 ANOVA-based robustness analysis (preserved from v1.1)

Phase 2 v1.2 varied four experimental factors: subtlety (3 levels), base COU (3 levels on primary battery), model family (3 levels on quality benchmark), and prompt wording (3 paraphrases on sensitivity battery). v1.4 preserves the v1.1/v1.2/v1.3 ANOVA pass unchanged. 4-6 hours of Week 4 analysis on Phase 2 v1.2 output. Zero additional API cost.

Output: `out/adversarial/phase3/robustness_analysis.md` with factor main-effects table, interaction tests, and predictive bounds (if interactions negligible).

Acceptance: non-blocking soft gate. Target for the praxis Ch3 robustness section.

---

## 14. Test plan additions

### 14.1 Unit tests

* `test_judge.py` — prompt assembly with few-shot examples, provider abstraction (OpenAI, Gemini, OpenAI-compat for HF), JSON parse robustness, retry logic, cross-family circularity check, prompt caching key generation
* `test_calibration.py` — calibration set loading, per-judge scoring across 6 verdict classes, per-class accuracy, cross-judge calibration κ computation
* `test_triage.py` — majority-of-3 bucket assignment logic (CONVERGENT, DIVERGENT, UNCERTAIN), confidence threshold handling, edge cases (all 3 disagree, 2+UNCERTAIN combos)
* `test_adjudication.py` — pairwise Cohen's κ + Fleiss' κ computation, confusion matrix generation, rationale length validation, stratified sampling design
* `test_formalization.py` — Jena rule scaffold generation from REAL-GAP final verdict
* `test_caching.py` — vendor-specific cache key construction, cache hit detection, fallback to non-cached path
* `test_batch.py` — batch job submission, polling, result reassembly into per-case judgments

### 14.2 Integration tests

* End-to-end with three mocked judges: 5-case fixture → all judges run → majority triage → author adjudication (simulated) → verdict output
* Calibration run with synthetic 5-case calibration set, known ground truth, all three mock judges
* Stratified-sample adjudication path with simulated 800-case queue

### 14.3 Smoke test (Phase 3 acceptance)

```bash
# 1. Verify judge module structure
test -d uofa/adversarial/judge/
test -f specs/calibration/calibration_set_v1.jsonl
wc -l specs/calibration/calibration_set_v1.jsonl | grep -q "^30"

# 2. Run calibration with three mocked providers (small subset)
uofa adversarial judge \
  --in specs/calibration/ \
  --out /tmp/cal_smoke/ \
  --judges mock_a,mock_b,mock_c \
  --calibration-only

# 3. Verify per-judge calibration output structure
test -f /tmp/cal_smoke/calibration_results_mock_a.json
test -f /tmp/cal_smoke/calibration_results_mock_b.json
test -f /tmp/cal_smoke/calibration_results_mock_c.json
grep -q "overall_accuracy" /tmp/cal_smoke/calibration_results_mock_a.json
grep -q "pairwise_kappa_AB" /tmp/cal_smoke/calibration_results_summary.json

# 4. Run triage on fixture judgments from three judges
uofa adversarial triage \
  --judgments-a tests/adversarial/judge/fixtures/mock_judgments_5_case_a.jsonl \
  --judgments-b tests/adversarial/judge/fixtures/mock_judgments_5_case_b.jsonl \
  --judgments-c tests/adversarial/judge/fixtures/mock_judgments_5_case_c.jsonl \
  --out /tmp/triage_smoke/
test -f /tmp/triage_smoke/adjudication_queue.csv

# 5. Run adjudication on fixture author adjudications
uofa adversarial adjudicate \
  --adjudications tests/adversarial/judge/fixtures/mock_adjudications.jsonl \
  --judgments-a ... --judgments-b ... --judgments-c ... \
  --out /tmp/adj_smoke/
test -f /tmp/adj_smoke/agreement_stats.json
grep -q "fleiss_kappa" /tmp/adj_smoke/agreement_stats.json
grep -q "cohen_kappa_AB" /tmp/adj_smoke/agreement_stats.json
grep -q "cohen_kappa_AC" /tmp/adj_smoke/agreement_stats.json
grep -q "cohen_kappa_BC" /tmp/adj_smoke/agreement_stats.json
```

---

## 15. Acceptance criteria

### 15.1 Hard gates

| # | Criterion |
|---|---|
| 1 | Judge module shipped with OpenAI-compat provider (serves both OpenAI proper and HF Endpoints) and Gemini provider |
| 2 | Judge prompt template v1.0.0 committed to `packs/core/judge_prompts/v1.0.0.md` with few-shot examples and chain-of-thought scaffold |
| 3 | Calibration set of 30 cases constructed with author ground-truth annotations (5 per verdict class across 6 classes) |
| 4 | Cross-family circularity check operational and verified to reject same-family configurations |
| 5 | Per-judge calibration accuracy ≥ 80% achieved on the final prompt version for all three required judges |
| 6 | Pairwise calibration κ ≥ 0.70 for all three judge pairs on the calibration set |
| 7 | Per-class calibration accuracy ≥ 50% for all six verdict classes for all three judges (soft within hard) |
| 8 | Full-corpus judgment completed by all three judges on all Phase 2 packages |
| 9 | Triage output assembled with CONVERGENT, DIVERGENT, UNCERTAIN bins under majority-of-3 logic |
| 10 | Author adjudication completed for the queue (full or stratified per §11.4) with adjudication rationale per §11.1 |
| 11 | Pairwise full-corpus Cohen's κ computed and reported for all three pairs, with explanation in Ch3 if any pair below 0.70 |
| 12 | Fleiss' κ across all three judges computed and reported, with explanation in Ch3 if below 0.65 |
| 13 | ≥ 3 of 6 §6.7 Tier 1 candidates validated as REAL-GAP through final-verdict adjudication |
| 14 | New Jena rules formalized and unit-tested against Phase 2 synthetic packages, Morrison, and Nagaraja |
| 15 | v0.5 catalog tagged with all new rules integrated |
| 16 | Case study re-run completed: Morrison COU1, Morrison COU2, Nagaraja with v0.5 catalog, delta table generated |
| 17 | All Phase 3 outputs committed to repository with provenance chain to Phase 2 artifacts |
| 18 | Validity caveat (§4 Principle 4) documented in praxis Ch3 limitations section, with three-judge ensemble framing and shared-training-data acknowledgment |
| 19 | Adjudication method (full-queue or stratified-sample) documented with rationale in `adjudication_method.txt` |

### 15.2 Soft gates

| # | Criterion |
|---|---|
| 20 | Inter-judge raw agreement (≥ 2 of 3) ≥ 80% (informational, motivates κ interpretation) |
| 21 | All 6 §6.7 Tier 1 candidates validated (full empirical confirmation of the extension plan) |
| 22 | Phase 3 completes by June 28, within the 4-week budget |
| 23 | §13.4 ANOVA analysis produces factor ranking with all main effects reported at F-statistic + p-value; interaction test result disclosed regardless of significance; predictive bounds reported if interactions validated as negligible |
| 24 | Stratified-sample adjudication is NOT invoked (i.e., full-queue adjudication completes within budget); soft signal that the protocol scales without compromise |
| 25 | HF Endpoints uptime cost stays under $80 (well within budget) |

### 15.3 Explicit non-goals

* Phase 3 does NOT extend the catalog with patterns outside the §6.7 Tier 1 candidate set. Novel patterns surfaced by adjudication are logged for post-defense investigation.
* Phase 3 does NOT re-run the full Phase 2 battery with v0.5 catalog. Case study re-run is limited to Morrison COU1, Morrison COU2, Nagaraja.
* Phase 3 does NOT address non-V&V 40 pack extensions. Those are post-defense work.
* Phase 3 does NOT include external human reviewer validation. That work is specified in the post-defense paper addendum (§20).
* Phase 3 does NOT pursue inter-judge κ above 0.78 through prompt engineering tricks that bias the judges toward agreement. Honest κ in the 0.70-0.78 range with the methodology in §7.5 is the target.

---

## 16. Execution schedule

Phase 3 fits in 4 weeks, June 1 to June 28, 2026. Author hours rise from v1.3's 40 to ~50-55 due to 10x corpus, 3-judge calibration overhead, and prompt iteration for kappa improvement.

| Week / date | Target hours | Work | Parallel reframe activity |
|---|---|---|---|
| Week 1: Jun 1-7 | 18 | Judge module scaffold + OpenAI-compat provider + Gemini provider + cross-family circularity check + prompt template v1.0.0 with few-shot examples and CoT scaffold + prompt caching + batch API integration. HF Endpoint provisioned (initial spinup test). Weekend (Jun 6-7): Calibration set construction (30 cases × 6 classes) + Stage 1 calibration runs across all three judges + prompt tuning until per-judge accuracy ≥ 80% and pairwise calibration κ ≥ 0.70. | Reframe Session R1 (planning, ~1.5 hr) Jun 7 evening |
| Week 2: Jun 8-14 | 8 | Mon (Jun 8): Stage 2 full-corpus judgment runs. OpenAI batch submission and Gemini batch submission early Mon morning (vendor-managed 6-12 hr completion). HF Endpoint spinup Mon morning, Llama judgments run synchronously through Mon-Tue (~7-10 hrs wall clock). HF Endpoint scale-down Tue evening. Wed: triage + adjudication queue assembly + queue-size assessment. Thu-Fri evenings: begin author adjudication on DIVERGENT + UNCERTAIN queue. | Reframe Session R2 (Ch1 edits, ~3 hr) mid-week; R3 (Ch2 + Ch5, ~3.5 hr) start |
| Week 3: Jun 15-21 | 12 | Continue author adjudication. If queue exceeds 30-hr budget, invoke stratified-sample protocol per §11.4. Begin pattern formalization for confirmed REAL-GAPs. Stage 4 agreement stats compilation (pairwise κ + Fleiss' κ). | Reframe Session R3 complete; R4 (bibliography, ~1 hr) |
| Week 4: Jun 22-28 | 14 | Mon-Tue: Complete adjudication and Stage 4 stats. Wed-Fri evenings: Stage 5 pattern formalization, unit tests, v0.5 catalog tag. Weekend (Jun 27-28): Case study re-run, delta table, §13.4 ANOVA analysis (4-6 hrs), Ch3 methodology section drafting for praxis. | Reframe Session R5 (delta document to Turman, ~1.5 hr), gated by Phase 3 Stage 4 completion; drafted Wed-Thu after Stage 4 complete, sent Jun 23-24 |

Total Phase 3 author effort: approximately 52 hours across 4 weeks. Roughly 13 hrs/week, achievable within evening + weekend capacity.

Critical path:

1. Per-judge calibration accuracy ≥ 80% AND pairwise calibration κ ≥ 0.70 by Jun 7 — gates Stage 2
2. Full-corpus judgments complete (all 3 judges) by Jun 10 — gates triage
3. Author adjudication complete (full or stratified) by Jun 22 — gates Stage 4 stats
4. Stage 4 agreement stats by Jun 23 — gates Reframe Plan v5 Session R5 (delta document to Turman)
5. Pattern formalization + delta table by Jun 28 — gates praxis Ch3 + Ch5 methodology sections

---

## 17. Coordination with reframe execution

The reframe plan has an execution window of June 8 to June 22 for Sessions R1-R4, with Session R5 (delta document) gated behind Phase 3 Stage 4 agreement statistics per Reframe Plan v5 §3 Gate 2. Coordination principles unchanged from v1.3:

1. **Calibration weekend frees Week 2.** Once all three judges hit thresholds by Jun 7, Week 2 is dominated by vendor-managed batch runs and the HF Endpoint Llama session, with author hours mostly going to triage + early adjudication.
2. **Phase 3 Stage 4 precedes reframe R5.** Stage 4 completes Jun 22-23; R5 runs Jun 23-24; delta document sent to Turman Jun 24.
3. **Reframe plan v5 trigger conditions.** Reframe Plan v5 §3 Gate 2 triggers on Phase 3 Stage 4 agreement statistics. Phase 3 Spec §15 hard gate #13 (≥ 3 of 6 §6.7 candidates adjudicated as REAL-GAP) is referenced by Reframe Plan v5 §3 condition 5.
4. **NAFEMS travel has zero Phase 3 work.** Phase 3 execution starts June 1, after NAFEMS return.

Combined Phase 3 + reframe weekly load: ~14-15 hrs/week across 4 weeks. Within available capacity.

---

## 18. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Any of three judges stuck below 80% calibration accuracy | Medium | Up to 3 prompt tuning iterations using §7.5 levers. If one judge fails persistently, substitute alternative SOTA model in same family (e.g., gpt-5.4-pro). If two or more fail, escalate per §8.3. |
| Pairwise calibration κ below 0.70 even with §7.5 prompt engineering | Medium | Document honestly. Proceed to Stage 2 with the lower-agreement judge pair flagged. The DIVERGENT bin grows, author adjudication time grows accordingly. Stratified-sample backstop activates if queue exceeds budget. |
| All three judges share LLM blind spot (high agreement, all wrong) | Medium | Three-judge ensemble cannot detect this. Per-judge calibration accuracy on author-annotated set is the partial mitigation. Honest disclosure in Ch3 limitations + paper addendum motivation. Three families reduces single-vendor blind-spot risk vs two-judge but does not eliminate shared-pretraining blind spots. |
| Adjudication queue exceeds 30 author hours | Medium-High | §11.4 stratified-sample backstop. Decision documented in adjudication_method.txt. Praxis claim still defensible. |
| HF Endpoints cold start consumes excessive billed time | Low-Medium | Single spinup per session (calibration + full corpus = 2 spinups total). Avoid scale-to-zero between sessions during active Phase 3. Documented in §6.5. |
| HF Endpoints H200 capacity unavailable on AWS | Low | Fallback options at same price point: 2x A100 80GB at $5/hr. Or substitute with 1x H100 80GB at $4.50/hr (FP8 quantization required, marginal quality risk). |
| OpenAI batch API submission errors or partial failures | Low-Medium | Retry logic with exponential backoff; failures isolated to per-case fallback to synchronous API at standard pricing. Cost impact minimal since batch failure rate typically < 5%. |
| Gemini batch API similar failure pattern | Low-Medium | Same mitigation as OpenAI. |
| Phase 2 delivers fewer than expected packages | Low | Degrade gracefully; smaller corpus means smaller queue. Cohen's κ computed on whatever the corpus is. |
| Nagaraja encoding not complete by Phase 3 case study re-run | Low | Delta table with only Morrison COU1/COU2 is still defensible. Nagaraja row added when encoding completes. |
| < 3 of 6 §6.7 candidates validated | Low-Medium | Adjust Ch5 to present non-validated candidates as investigated-but-not-confirmed. Core contribution (coverage methodology + 3-judge cross-family validation protocol) remains defensible independent of extension count. |
| Author adjudication bias toward §6.7 expectations | Medium | §11.3 self-blinding sanity check produces an honest signal of expectation-driven bias. Reported in Ch3. |
| Reframe execution and Phase 3 compete for author attention | Medium | §17 coordination plan addresses this. Combined ~14-15 hrs/week is achievable within evening + weekend capacity. |
| Praxis committee challenges absence of external human validation | High (anticipated, not catastrophic) | Anticipated and addressed proactively. Ch3 methodology section discloses the limitation and points to the paper addendum as the planned external-validation work. The praxis contribution is the framework + methodology + 3-judge cross-family validation protocol, not external anchoring against expert judgment. |
| LLM judge cost exceeds $700 budget envelope | Low | Contingency built in. If thinking mode token volume exceeds estimates, disable thinking on one judge as cost-control move; document. Caching + batch are highest-impact cost levers. |

---

## 19. Open questions

1. **Calibration set visibility.** Should `specs/calibration/calibration_set_v1.jsonl` be committed to the public repo or kept private? Default: committed publicly with `specs/calibration/annotation_rationale.md` explaining each ground-truth annotation. Invite community critique as future work.

2. **Multi-defeater packages.** Some Phase 2 packages may instantiate multiple defeaters beyond the target. Default: judge output includes `primary_verdict` and `secondary_observations` fields; agreement statistics use only primary; secondary observations go into supplementary data.

3. **Judge family substitution policy.** If GPT-5.4, Gemini 3.1 Pro, or Llama 3.3 70B becomes unavailable mid-execution, substitute within the same family if possible (e.g., gemini-3.1-pro → gemini-3.0-pro). Document any substitution in run manifest. Cross-family substitution requires re-running Stage 1 calibration to revalidate κ thresholds.

4. **Severity assignment for new rules.** §13.1.5: §6.7 Tier 1 pre-assigned severity wins; author may revise with rationale. For non-§6.7 patterns, author judgment alone.

5. **Catalog version numbering.** v0.4.0-nafems frozen. v0.4.1 includes Phase 2 schema additions. v0.5 includes Phase 3 rule additions. Standard semver continues.

6. **Stratified vs full-queue adjudication decision criteria.** Default: full-queue if estimated author time ≤ 30 hrs; stratified otherwise. The threshold is documented but the author has discretion to invoke stratified earlier if other factors (illness, travel) compress capacity.

7. **HF Endpoint region selection.** Default: AWS us-east-1 for lowest latency from US. Author may choose EU region if data residency becomes a concern (synthetic packages are not sensitive, so this is not anticipated).

8. **Post-Phase 3 roadmap.** Reframe completion and delivery to Turman (early July); praxis Ch3 + Ch5 drafting (July-August); paper addendum scoping for post-defense human reviewer extension. Phase 3 artifacts feed directly into both the praxis and the future paper.

---

## 20. Paper-track addendum (forward reference, post-defense)

The praxis-scope Phase 3 protocol specified above is sufficient for the praxis defense. Extending to a publishable paper requires external human validation that the praxis intentionally defers.

A separate document, `UofA_Adversarial_Gen_Phase3_Paper_Addendum_v1.md`, will be drafted post-defense (estimated Q1 2027) specifying:

* External reviewer panel (3 simulation engineers via Upwork, ~$400 budget)
* Reviewer protocol identical to the 6-class verdict task
* Updated agreement statistics: Cohen's κ(judge_A, median_human), Cohen's κ(judge_B, median_human), Cohen's κ(judge_C, median_human), Fleiss' κ(3 humans), confusion matrices
* Validity claim upgrade from model-concordance to expert-anchored validity
* Methodology paper section (~2,500 words) documenting the three-judge cross-family ensemble plus human-anchoring protocol as a novel contribution to LLM-as-judge methodology in assurance-case defeater analysis
* JVVUQ submission target TBD (likely 2027 issue)

The praxis Ch3 limitations section will reference §20 explicitly so the validity tradeoff and the planned remediation are visible to the defense committee.

---

## 21. Appendix A — Judge prompt template v1.0.0 (excerpt)

```markdown
# Judge Prompt Template v1.0.0

## System Framing

You are an expert in computational modeling and simulation credibility
assurance, evaluating synthetic evidence packages generated for the Unit of
Assurance (UofA) weakener catalog.

## Verdict Class Definitions with Worked Examples

[6 classes, each with definition + canonical example from calibration set]

## Reasoning Scaffold (REQUIRED)

For each case, populate the following reasoning_steps fields BEFORE
committing to a verdict:

1. source_taxonomy_identified: which taxonomy and sub-type does this case
   target?
2. target_rule_identified: which UofA rule (existing or §6.7 candidate) was
   expected to fire?
3. rule_firings_inspected: what did the rule engine actually do?
4. instantiation_check: does the package legitimately instantiate the target
   defeater?
5. verdict_commitment: based on the above, which of the 6 verdict classes
   applies?

## Output Schema

[See Phase 3 Spec §7.2 for full schema]

[Full prompt template in `packs/core/judge_prompts/v1.0.0.md`]
```

---

## 22. Appendix B — Example calibration case

```json
{
  "case_id": "cal-001-real-gap-data-drift",
  "package_path": "specs/calibration/packages/cal-001.jsonld",
  "source_taxonomy": "gohar/evidence_validity/data-drift",
  "phase2_outcome_class": "COV-MISS",
  "ground_truth_verdict": "REAL-GAP",
  "ground_truth_reasoning": "The package instantiates Gohar Data Drift: the validation dataset has vintage 2018, the model revision is dated 2024, and no re-calibration activity is recorded. No existing UofA rule detects this temporal misalignment.",
  "ground_truth_section_6_7_candidate": "W-EV-01",
  "annotator": "Vettrivel",
  "annotation_date": "2026-05-28",
  "review_confidence": "high",
  "notes": "Deliberately clear-cut to anchor the few-shot example for REAL-GAP class."
}
```

---

## 23. Appendix C — Author adjudication packet template (Markdown)

```markdown
# Adjudication Packet: adv-2026-p2-002-gohar-data-drift-v03

**Source Taxonomy:** Gohar (2025) / Evidence Validity / Data Drift
**Phase 2 outcome:** COV-MISS
**§6.7 Tier 1 mapping:** W-EV-01 (revealed AFTER initial adjudication per §11.3)

## What this defeater is

[Source taxonomy description]

## The synthetic package (excerpt)

[JSON-LD critical fields]

## UofA rule engine output

- COV-MISS: no rules fired
- Rules that could have been relevant:
  * W-EP-03 (stale input) — did not fire
  * W-CON-03 (future-dated evidence) — did not fire

## Judge A (GPT-5.4) verdict

- Verdict: REAL-GAP (confidence 0.87)
- reasoning_steps: [structured CoT]
- Reasoning: [free-text explanation]

## Judge B (Gemini 3.1 Pro) verdict

- Verdict: REAL-GAP (confidence 0.81)
- reasoning_steps: [structured CoT]
- Reasoning: [free-text explanation]

## Judge C (Llama 3.3 70B) verdict

- Verdict: GENERATOR-ARTIFACT (confidence 0.62)
- reasoning_steps: [structured CoT]
- Reasoning: "The validation dataset vintage is documented but the package
  does not show evidence that the model in question was deployed against
  data substantially different from the validation distribution..."

## Disagreement type

MAJORITY-AGREE-MINORITY-DISSENT (REAL-GAP × 2, GENERATOR-ARTIFACT × 1)

## Author adjudication (record before revealing §6.7 mapping)

- Final verdict: ___________
- Rationale (≥ 50 words): ___________________________________________
- Would add to catalog: [ ] Yes  [ ] No  [ ] Depends
- Notes: ____________________________________________________________

## Post-hoc §6.7 alignment (record after adjudication)

- §6.7 expectation: W-EV-01 expected as REAL-GAP
- Adjudication match: [ ] Match  [ ] Contradict  [ ] Independent
```

---

End of Phase 3 specification v1.4.
