"""Abstract judge provider interface + result dataclasses (spec v1.5 §5.1).

`AbstractJudgeProvider` is intentionally a separate hierarchy from the
existing `uofa_cli.llm.backend.LLMBackend` Protocol. Judges need:

  - Batch submit/poll for OpenAI + Gemini (spec §9.1 `--enable-batch-api`)
  - Vendor-specific cache-key construction (spec §9.1 `--enable-prompt-caching`)
  - Schema-enforcement modes (strict JSON for OpenAI/Gemini, JSON-mode + tolerant
    parser for HF Llama, per spec §7.7)
  - Async concurrency on the HF Endpoints path (spec §9.1 `--parallel`)

None of these belong on `LLMBackend`, which targets single-shot calls in
the extract / interpretation pipelines. Spec §5.1 puts judge providers in
their own package; this base class follows that guidance.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Judgment:
    """One judge's verdict on one case.

    Mirrors `specs/judge_output_schema.json`. Construction goes through
    `Judgment.from_response()` which validates against that schema, so
    callers can trust the fields are well-formed.

    `evidence_gap` is required by the schema when `verdict == 'OUT-OF-SCOPE'`
    (productive-OOS framing per spec v1.6 §7.1, Delta 1). Shape:
        {"missing_evidence_type": str, "would_support_defeater_evaluation": str}
    None for non-OOS verdicts.
    """

    case_id: str
    verdict: str  # one of the 6 spec classes
    confidence: float
    reasoning_steps: dict[str, str]
    reasoning: str
    section_6_7_candidate: str | None
    alternative_rule_analysis: str | None
    prompt_template_version: str
    judge_model: str
    judge_thinking_enabled: bool
    judge_model_params: dict[str, Any]
    generator_provenance: dict[str, Any]
    evidence_gap: dict[str, str] | None = None
    # Provider-side metadata not part of the output schema. Kept here for
    # run-manifest accounting (latency, cache hits, retries).
    raw_response: dict | None = field(default=None, compare=False)


@dataclass(frozen=True)
class CalibrationResult:
    """Per-judge accuracy on a calibration set (spec §8.3).

    - `overall_accuracy` = correct_count / total
    - `per_class_accuracy` = {verdict_class: correct/total}
    - `confusion_matrix` = {true_class: {predicted_class: count}}
    """

    judge_model: str
    overall_accuracy: float
    per_class_accuracy: dict[str, float]
    confusion_matrix: dict[str, dict[str, int]]
    case_count: int
    correct_count: int


class AbstractJudgeProvider(ABC):
    """Pluggable interface for the three Phase 3 judges.

    Concrete implementations:
        - `OpenAICompatProvider(target='openai')` — Judge A
        - `GeminiProvider()` — Judge B
        - `OpenAICompatProvider(target='hf-llama')` — Judge C
        - `MockProvider(family=..., judgments=...)` — for tests + smoke

    All methods are async to keep the HF parallel path uniform; sync
    callers wrap with `asyncio.run()`.
    """

    @property
    @abstractmethod
    def family(self) -> str:
        """Resolved family label (e.g. 'GPT', 'Gemini', 'Llama', 'Claude', 'Mistral')."""

    @property
    @abstractmethod
    def model(self) -> str:
        """Provider-visible model id (e.g. 'gpt-5.4', 'gemini-3.1-pro')."""

    @property
    def judge_role(self) -> str:
        """Role this judge plays in the v1.6 ensemble.

        Values: 'production' (Judges A/B/C), 'calibration_anchor' (Judge D),
        'arbiter' (Judge E). Default 'production' for back-compat with the
        v1.5 abstract base; v1.6 LiteLLMProvider overrides this per-instance.
        """
        return "production"

    @property
    @abstractmethod
    def supports_strict_schema(self) -> bool:
        """True if the API enforces our JSON schema server-side.

        OpenAI: True (response_format json_schema strict=True).
        Gemini: True (response_schema with response_mime_type).
        HF Llama via TGI: False (JSON-mode only; tolerant parser fallback).
        """

    @abstractmethod
    async def judge(self, case: dict) -> Judgment:
        """Verdict a single case. Used in calibration + sync HF path.

        `case` is the dict described in `prompts.build_prompt_for_case()`.
        """

    @abstractmethod
    async def calibrate(self, calibration_set: list[dict]) -> CalibrationResult:
        """Run the full calibration set and compute per-judge stats.

        Each `calibration_set` entry has the case dict plus a
        `ground_truth_verdict` field used to score.
        """
