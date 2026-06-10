# Calibration v5 — Diagnosis of the gate-7 UNCERTAIN failures (Judges B and C)

**Date:** 2026-06-09
**Author:** Vishnu Vettrivel (paired with Claude Code)
**Inputs:** v4 raw judge records `dev/build/adversarial/phase3/calibration-v4/v1.1.0/judge_{b,c}_calibration.jsonl`; v4 metrics `…/calibration_run_v1_results.json`.
**Scope rule:** the v4 calibration anchor set (`specs/calibration/calibration_set_v1.jsonl`, cases cal-026..030) is **frozen**. This diagnosis drives a prompt-only lever (v1.2.0). It does not alter calibration ground truth.

## Gate-7 failure recap (v4)

Per-class UNCERTAIN accuracy against a 50% floor: A 80% (4/5) pass, **B 20% (1/5) fail, C 0% (0/5) fail**. All headline gates (per-judge accuracy ≥80%, pairwise κ ≥0.70) passed.

## What B and C actually returned on the five UNCERTAIN cases (v4)

| Case (ground truth = UNCERTAIN) | Judge B (gemini-2.5-pro) | Judge C (Llama-4-Maverick) |
|---|---|---|
| cal-026 incomplete-knowledge (w-prov-01) | EXISTING-RULE-MISBEHAVIOR @ 0.95 | EXISTING-RULE-MISBEHAVIOR @ 0.80 |
| cal-027 undermining-d1 (w-ar-01 morrison) | GENERATOR-ARTIFACT @ 0.95 | EXISTING-RULE-MISBEHAVIOR @ 0.80 |
| cal-028 d1-undermining (w-ar-01 nagaraja) | GENERATOR-ARTIFACT @ 0.95 | EXISTING-RULE-MISBEHAVIOR @ 0.80 |
| cal-029 data-imprecision (w-ep-03) | EXISTING-RULE-MISBEHAVIOR @ 0.95 | EXISTING-RULE-MISBEHAVIOR @ 0.80 |
| cal-030 variability (w-ar-01 nagaraja) | **UNCERTAIN @ 0.50** (correct) | EXISTING-RULE-MISBEHAVIOR @ 0.80 |

## Failure mode per judge

- **Judge B (gemini-2.5-pro): over-confident single-verdict commitment.** On four of five it commits to one defensible class (GENERATOR-ARTIFACT or EXISTING-RULE-MISBEHAVIOR) at confidence **0.95**. It is capable of UNCERTAIN (cal-030 at 0.50), but its default is a confident pick. Its own v4 reasoning on cal-030 names "genuine ambiguity between two verdict classes," yet on cal-027/028 it resolves the same kind of ambiguity by choosing GENERATOR-ARTIFACT.
- **Judge C (Llama-4-Maverick): uniform absorption into EXISTING-RULE-MISBEHAVIOR.** All five return ERM at confidence **0.80**. C never emits UNCERTAIN on this set.

Both judges return well-formed verdicts drawn from the schema enum, at high confidence. The misses are reasoning and commitment, not output mechanics.

## Mechanical causes ruled out

The data alone is decisive: a mechanical suppression would show malformed output, a missing verdict, or a coerced low-confidence default, not clean high-confidence enum members. The code path confirms it:

1. **Strict schema does not drop UNCERTAIN.** `strip_schema_for_provider` (`src/uofa_cli/adversarial/judge/providers/capabilities.py`) removes only the keyword blocklist (`if`/`then`/`else`) and applies Gemini's nullable→OpenAPI transform. The `verdict` enum in `specs/judge_output_schema.json` (which includes UNCERTAIN) is preserved, and both B and C emit other enum members freely.
2. **Coercion does not rewrite verdicts.** `_coerce_partial_response` (`…/providers/litellm_provider.py`) fills only missing or malformed fields and never synthesizes `confidence`. The 0.80 and 0.95 values are model-emitted.
3. **Thinking mode is off and consistent.** `calibration.py` constructs providers with `thinking_enabled=False`, and `runner._build_providers` defaults to the same; `LiteLLMProvider._call` injects `thinking_kwargs` only when `thinking_enabled` is true, so Gemini's `thinking_config` was never sent. The `judge_thinking_enabled: true` field in the records is the model's self-report inside its JSON body, not the runtime setting. Calibration and production are therefore thinking-consistent, and the gate decision transfers to production unchanged.

## Conclusion

The failure is **vendor commitment-style bias**. On cases the anchor labels UNCERTAIN because two or more verdicts are each defensible after inspection, B and C resolve the ambiguity by committing to one defensible verdict at high confidence rather than reporting UNCERTAIN. This matches the diagnosis of record in `TIER_A_HANDOFF.md`.

## Two consequences for the rest of the task

1. **v1.2.0 lever is prompt-only and identical for all judges.** Strengthen the §6 UNCERTAIN trigger so that "two or more verdicts each defensible after thorough inspection, with none dominating" maps to UNCERTAIN, and name the over-commitment default as the anti-pattern. Because the bias is vendor-level and the misses sit at confidence 0.80–0.95, a single prompt pass may not lift B and C to the 50% floor. Per the one-iteration rule, **RELAX is the probable branch**; the v5 run decides.
2. **The Part 3.1 low-confidence routing will not catch this pattern.** B and C miss at confidence 0.80–0.95, far above the 0.5 routing threshold, so those forced verdicts route as CONVERGENT. The routing is still worth building as a general safety net for genuinely low-confidence forced verdicts elsewhere in the corpus, but the control that addresses the UNCERTAIN→ERM absorption is Judge E arbitration plus Stage 4 author adjudication. This is the named residual risk to carry into the Ch3 disclosure.
