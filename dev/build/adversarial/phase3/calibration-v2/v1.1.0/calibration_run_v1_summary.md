# Stage 1 calibration — 2026-05-05T17:08:23Z

**Prompt template version:** `v1.1.0`
**Calibration set:** `specs/calibration/calibration_set_v1.jsonl` (30 cases)

**Methodology disclosure**: Gemini Judge B ships with `gemini-2.5-pro` instead of spec §6.1's `gemini-3.1-pro` because the preview tier's 100 RPD is insufficient for the production-corpus run. See TIER_A_HANDOFF.md for details.

## Hard gates (spec §15.1)

| Gate | Target | Verdict |
|---|---|---|
| Judge A accuracy ≥ 80% | 90.0% | ✅ |
| Judge B accuracy ≥ 80% | 86.7% | ✅ |
| Judge C accuracy ≥ 80% | 83.3% | ✅ |
| Pairwise κ A/B ≥ 0.70 | 0.959 | ✅ |
| Pairwise κ A/C ≥ 0.70 | 0.917 | ✅ |
| Pairwise κ B/C ≥ 0.70 | 0.958 | ✅ |
| Judge A per-class ≥ 50% | see table below | ❌ |
| Judge B per-class ≥ 50% | see table below | ❌ |
| Judge C per-class ≥ 50% | see table below | ❌ |

**Overall**: ❌ ONE OR MORE GATES FAIL

## Per-judge accuracy

| Position | Token | Model | Accuracy | Correct/Total |
|---|---|---|---:|---:|
| A | openai | gpt-5.4 | 90.0% | 27/30 |
| B | gemini | gemini-2.5-pro | 86.7% | 26/30 |
| C | hf-llama | meta-llama/Llama-4-Maverick-17B-128E-Instruct:sambanova | 83.3% | 25/30 |
| E | mistral | mistral-large-2512 | 16.7% | 5/30 |

## Pairwise Cohen's κ + Fleiss κ

| A/B | A/C | B/C | Fleiss (A,B,C) |
|---:|---:|---:|---:|
| 0.959 | 0.917 | 0.958 | 0.944 |

## Per-class accuracy (judge × verdict class)

| Verdict class | n | A | B | C |
|---|---:|---:|---:|---:|
| CORRECT-DETECTION | 5 | 100% | 100% | 100% |
| REAL-GAP | 5 | 100% | 100% | 100% |
| GENERATOR-ARTIFACT | 5 | 100% | 100% | 100% |
| EXISTING-RULE-MISBEHAVIOR | 5 | 100% | 100% | 100% |
| OUT-OF-SCOPE | 5 | 100% | 100% | 100% |
| UNCERTAIN | 5 | 40% | 20% | 0% |

## Judge E sanity check (informational only)

Judge E verdict matches Judge D ground truth on 71.4% of 30 cases.
