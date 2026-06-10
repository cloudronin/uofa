# Stage 1 calibration — 2026-06-10T03:08:45Z

**Prompt template version:** `v1.2.0`
**Calibration set:** `specs/calibration/calibration_set_v1.jsonl` (30 cases)

**Methodology disclosure**: Gemini Judge B ships with `gemini-2.5-pro` instead of spec §6.1's `gemini-3.1-pro` because the preview tier's 100 RPD is insufficient for the production-corpus run. See TIER_A_HANDOFF.md for details.

## Hard gates (spec §15.1)

| Gate | Target | Verdict |
|---|---|---|
| Judge A accuracy ≥ 80% | 96.7% | ✅ |
| Judge B accuracy ≥ 80% | 90.0% | ✅ |
| Judge C accuracy ≥ 80% | 63.3% | ❌ |
| Pairwise κ A/B ≥ 0.70 | 0.903 | ✅ |
| Pairwise κ A/C ≥ 0.70 | 0.756 | ✅ |
| Pairwise κ B/C ≥ 0.70 | 0.755 | ✅ |
| Judge A per-class ≥ 50% | all classes pass | ✅ |
| Judge B per-class ≥ 50% | all classes pass | ✅ |
| Judge C per-class ≥ 50% | see table below | ❌ |

**Overall**: ❌ ONE OR MORE GATES FAIL

## Per-judge accuracy

| Position | Token | Model | Accuracy | Correct/Total |
|---|---|---|---:|---:|
| A | openai | gpt-5.4 | 96.7% | 29/30 |
| B | gemini | gemini-2.5-pro | 90.0% | 27/30 |
| C | hf-llama | Llama-4-Maverick-17B-128E-Instruct | 63.3% | 19/30 |
| E | mistral | mistral-large-2411 | 83.3% | 25/30 |

## Pairwise Cohen's κ + Fleiss κ

| A/B | A/C | B/C | Fleiss (A,B,C) |
|---:|---:|---:|---:|
| 0.903 | 0.756 | 0.755 | 0.804 |

## Per-class accuracy (judge × verdict class)

| Verdict class | n | A | B | C |
|---|---:|---:|---:|---:|
| CORRECT-DETECTION | 5 | 100% | 100% | 80% |
| REAL-GAP | 5 | 100% | 100% | 40% |
| GENERATOR-ARTIFACT | 5 | 100% | 100% | 80% |
| EXISTING-RULE-MISBEHAVIOR | 5 | 100% | 80% | 80% |
| OUT-OF-SCOPE | 5 | 100% | 100% | 100% |
| UNCERTAIN | 5 | 80% | 60% | 0% |

## Judge E sanity check (informational only)

Judge E verdict matches Judge D ground truth on 83.3% of 30 successful attempts (Mistral failed 0 of 30 cases — typically rate-limit or schema validation, not a gate).
