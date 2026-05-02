# SME scoring — `--explain` plain-language explanation function (P-B kill criterion)

Spec v0.4 §8.3: explanations must be SME-rated **≥ 80% useful-and-correct** on a 30-firing sample after one round of prompt iteration. If missed, the entire interpretation work stops.

## How to use this directory

1. Run the sample generator (slow — one LLM call per firing):
   ```
   python dev/tools/explain_sme_review/generate_sample.py
   ```
   Writes `sample_<backend>_<model>_<timestamp>.json`. Defaults to bundled
   Ollama / qwen3.5:4b. Override with env vars:
   ```
   UOFA_EXPLAIN_BACKEND=anthropic UOFA_EXPLAIN_MODEL=claude-sonnet-5-2026 \
       python dev/tools/explain_sme_review/generate_sample.py
   ```

2. Review each explanation against the SME quality criteria in spec §8.3:
   - Correctly identifies what the firing is about (no hallucination)
   - Grounded in specific evidence content (not generic)
   - Readable by regulatory affairs people without UofA expertise

3. Record results in a new section below: model, sample size, count of
   useful-and-correct vs total, percentage, kill-criterion verdict, notes
   on common failure modes.

4. If the percentage is < 80%, iterate the prompt at
   [src/uofa_cli/interpretation/templates/rules/explain.jinja2](../../../src/uofa_cli/interpretation/templates/rules/explain.jinja2)
   and re-generate. Per spec §8.3 you get **one** round of prompt iteration
   before the kill criterion fires.

## Scoring rubric

For each explanation in the sample:

- **Useful-and-correct (1)**: explanation is accurate AND would help a
  regulatory affairs person decide whether the firing matters in this
  package's context.
- **Not useful (0)**: explanation hallucinates details, contradicts the
  pattern's actual behavior, repeats the input verbatim without adding
  context, or is too vague to act on.

## Scoring runs

(Populate this section as runs are scored.)

### Run 2026-05-02 — bundled Qwen 3.5 4B (Round 0)

- Sample file: `sample_ollama_qwen3.5_4b_20260502-124203.json`
- Sample size: 11
- SME score: **3 Pass / 5 Marginal / 3 Fail** = 27% strict / 50% generous
- Kill criterion (≥80%): **MISSED**
- Wall clock: 114s total

**SME findings** ([PB_SME_Review_Handoff.md](../../../../../../Writing/Methodology/PB_SME_Review_Handoff.md)):
The model gets "what pattern fired" right but cannot say "where in the
package" or "what's missing specifically" because the context bundle
sent to the LLM contains only patternId/severity/hits — no actual
evidence content from the affected nodes. Generic restatements rather
than per-firing analysis.

---

### Run 2026-05-02 — bundled Qwen 3.5 4B (Round 1, with context enrichment + new prompt)

- Sample file: `sample_ollama_qwen3.5_4b_20260502-145911.json`
- Sample size: 11 (same firings as Round 0 for direct comparison)
- Wall clock: 171s total (15.6s per explanation, larger context)
- Iteration count: 1 (the spec's full budget)
- Confidence distribution: **11/11 high** (vs 1 high / 3 medium / 7 low in Round 0)
- Cache: invalidated automatically by INTERPRETATION_VERSION 0.2.0 → 0.3.0
- SME score: **PENDING FORMAL REVIEW**

**Engineering changes that drove this round:**

1. **Context bundle enrichment** — re-invoke rule engine in jsonld mode
   when `--explain` is set; parse `WeakenerAnnotation` nodes for
   `affectedNode` IRIs and `escalationSource` (for compounds); resolve
   IRIs in the package JSON-LD to surface the human-readable factor
   names, validation result names, etc. into the prompt. Audit:
   [round1_audit.md](round1_audit.md).

2. **Output schema migration** — replaced single `explanation` field
   with four structured fields (`affected_evidence_summary`,
   `gap_description`, `relevance_to_cou`, `confidence`) so the model
   does each piece of analytical work explicitly rather than producing
   prose that elides any of them.

3. **Prompt rewrite** — added grounding instructions, negative example
   of generic output, positive example of grounded output, COU stakes
   differentiation guidance, COMPOUND handling guidance, and a
   regulatory-affairs jargon-translation directive.

**Informal Claude Code spot-check** (NOT a substitute for SME review):

| # | Pattern | Round 0 | Round 1 (informal) | Notes |
|---|---|---|---|---|
| 1 | W-AL-01 | Marginal | Likely Pass | Names "hemolysis comparison, PIV velocity, mesh convergence" |
| 2 | W-AR-05 | Fail | Likely Pass | Says "lack the required comparedAgainst link to their comparator data sources" — concrete |
| 3 | W-CON-04 (COU1) | Marginal | Likely Pass | Names missing SensitivityAnalysis, ties to component dimensions |
| 4 | W-EP-02 | Marginal | Likely Pass | Names the three validation results; uses "provenance chain" but explains it ("how they were produced") |
| 5 | W-ON-02 (COU1) | Pass | Likely Pass | Preserved Round 0 quality |
| 6 | COMPOUND-01 | Fail | Likely Pass | **Names constituents**: "two instances of unassessed credibility factors coexisting with eleven instances of incomplete provenance chains and four instances of unassessed high-risk factors" |
| 7 | W-AL-02 | Pass | Likely Pass | Preserved + better COU framing |
| 8 | W-CON-04 (COU2) | Marginal | Likely Pass | **Distinguishes from #3 by COU2 stakes** (Class III VAD MRL 5) |
| 9 | W-EP-04 | Fail | Likely Pass | The canonical SME case — **lists all six factors by name** |
| 10 | W-ON-02 (COU2) | Pass | Likely Pass | Differentiates from #5 by Class III + MRL 5 |
| 11 | W-PROV-01 | Marginal | Likely Pass | **Names seven affected evidence items** |

If SME confirms, that's 11/11 = 100%. Even with one or two SME
re-classifications to Marginal/Fail, this is well above the 80% threshold.

**SME action items:**

1. Open [sample_ollama_qwen3.5_4b_20260502-145911.json](sample_ollama_qwen3.5_4b_20260502-145911.json)
2. Score each of the 11 explanations 1 (useful-and-correct) or 0 per
   the rubric above
3. If ≥ 80% (i.e. ≥ 9 / 11): P-B passes the kill criterion → unblock
   P-F (group), P-G (contextualize), P-H (cross-item patterns), P-J
   (diff explain), P-K (shacl explain)
4. If < 80%: kill criterion fires per spec §8.3 (we used the one
   allowed iteration round); pause remaining phases and reassess
5. Optionally: if Round 1 passes on Qwen, skip Phase 8 (Anthropic
   comparison) — the unified abstraction means Claude/GPT can be
   configured per-invocation without further engineering work; quality
   scaling is automatic

**Engineering notes from this round** (informational, not part of the SME score):

The first attempt produced 11 fallback strings ("explanation unavailable") because
litellm's `ollama_chat/` provider intermittently returns empty content for
thinking-capable models even with `think:False`. Resolved by:

1. Adding a direct `/api/chat` HTTP path in `LiteLLMBackend` for Ollama only;
   other backends keep using litellm. (See note in `litellm_backend.py:_DEFAULT_CAPS`.)
2. Disabling `supports_structured_output()` for Ollama (callers fall back to
   plain `generate()` + JSON parse, which is the path that works reliably).
3. Setting `extra={"think": False}` and bumping `max_tokens` to 4096 in the
   explain function so the model spends its budget on user-facing JSON
   rather than hidden reasoning.
4. Enriching `FiringContext.description` from the `.rules` files
   (`# W-XX-NN: <description>` headers) via the new
   `rules.load_pattern_descriptions()` helper. Without this, every
   explanation fell back to "the specific nature of W-EP-04 cannot be
   determined from the provided input" because the firings carried only
   patternId / severity / hits.

After (1)-(4), confidence flipped from 0/11 high → 11/11 high in 114s
total. The explanations now cite specific failure modes
(e.g. "ValidationResult objects lack associated generation activity",
"missing SensitivityAnalysis component", "Critical and High weakeners
coexist") grounded in the COU and standard.

**To-do for the SME (you):**

1. Open `sample_ollama_qwen3.5_4b_20260502-124203.json`
2. For each of the 11 explanations, score 1 (useful-and-correct) or 0
   per the rubric above
3. Fill in the X / 11 count and percentage above
4. If ≥ 80%, P-B passes the kill criterion → P-F (grouping function) can begin
5. If < 80%, list the failure modes in the notes; then iterate the prompt
   template at `src/uofa_cli/interpretation/templates/rules/explain.jinja2`
   and re-generate ONCE — that's the spec's full iteration budget
