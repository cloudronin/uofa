"""Gemini (Google) judge provider (spec v1.5 §5.2, §7.7).

Uses the `google-generativeai` SDK with structured-output mode:
    response_mime_type='application/json' + response_schema=SCHEMA

This is Gemini's equivalent of OpenAI strict-mode and provides
API-enforced schema validation.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from uofa_cli.adversarial.judge.prompts import (
    PROMPT_TEMPLATE_VERSION,
    build_prompt_for_case,
    build_prompt_static_prefix,
)
from uofa_cli.adversarial.judge.providers.base import (
    AbstractJudgeProvider,
    CalibrationResult,
    Judgment,
)
from uofa_cli.adversarial.judge.retry import TransientError, with_retry

logger = logging.getLogger(__name__)

_DEFAULT_GEMINI_MODEL = "gemini-3.1-pro"


def _load_schema() -> dict:
    """Load specs/judge_output_schema.json from the repo root."""
    repo_root = Path(__file__).resolve().parents[5]
    schema_path = repo_root / "specs" / "judge_output_schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(
            f"judge output schema not found at {schema_path}"
        )
    return json.loads(schema_path.read_text())


class GeminiProvider(AbstractJudgeProvider):
    """Judge B — Google Gemini 3.1 Pro with thinking enabled.

    Construction:
        gemini = GeminiProvider()  # uses GEMINI_API_KEY from env
        gemini = GeminiProvider(client=mock_client)  # for tests
    """

    def __init__(
        self,
        *,
        model: str = _DEFAULT_GEMINI_MODEL,
        thinking_enabled: bool = True,
        client: Any = None,  # mock-able
    ) -> None:
        self._model = model
        self._thinking_enabled = thinking_enabled
        self._client = client if client is not None else self._build_default_client()

    def _build_default_client(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY not set")
        # Lazy import so tests with a mock client don't need the SDK.
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        return genai.GenerativeModel(self._model)

    @property
    def family(self) -> str:
        return "Gemini"

    @property
    def model(self) -> str:
        return self._model

    @property
    def supports_strict_schema(self) -> bool:
        # Gemini's response_schema is API-enforced; treated as strict.
        return True

    async def judge(self, case: dict) -> Judgment:
        return await self._judge_with_retry(case)

    @with_retry()
    async def _judge_with_retry(self, case: dict) -> Judgment:
        prompt_prefix = build_prompt_static_prefix()
        prompt_case = build_prompt_for_case(case)
        full_prompt = prompt_prefix + prompt_case
        schema = _load_schema()

        try:
            # The SDK exposes generate_content() returning a response with
            # `.text` for the JSON payload when response_mime_type is set.
            response = self._client.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.0,
                    "response_mime_type": "application/json",
                    "response_schema": schema,
                },
            )
        except Exception as e:
            if _is_transient(e):
                raise TransientError(str(e)) from e
            raise

        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("empty response from Gemini")
        parsed = json.loads(text)
        return self._build_judgment(case, parsed, raw=parsed)

    def _build_judgment(self, case: dict, parsed: dict, *, raw: dict) -> Judgment:
        return Judgment(
            case_id=parsed["case_id"],
            verdict=parsed["verdict"],
            confidence=parsed["confidence"],
            reasoning_steps=parsed["reasoning_steps"],
            reasoning=parsed["reasoning"],
            section_6_7_candidate=parsed.get("section_6_7_candidate"),
            alternative_rule_analysis=parsed.get("alternative_rule_analysis"),
            prompt_template_version=parsed.get(
                "prompt_template_version", PROMPT_TEMPLATE_VERSION
            ),
            judge_model=parsed.get("judge_model", self._model),
            judge_thinking_enabled=parsed.get(
                "judge_thinking_enabled", self._thinking_enabled
            ),
            judge_model_params=parsed.get(
                "judge_model_params", {"temperature": 0.0, "seed": None}
            ),
            generator_provenance=parsed.get(
                "generator_provenance",
                {"generator_model": "unknown", "temperature": None, "seed": None},
            ),
            raw_response=raw,
        )

    async def calibrate(self, calibration_set: list[dict]) -> CalibrationResult:
        """Same calibration shape as OpenAICompatProvider; spec §8 acceptance."""
        if not calibration_set:
            return CalibrationResult(
                judge_model=self._model,
                overall_accuracy=0.0,
                per_class_accuracy={},
                confusion_matrix={},
                case_count=0,
                correct_count=0,
            )

        per_class_total: dict[str, int] = {}
        per_class_correct: dict[str, int] = {}
        confusion: dict[str, dict[str, int]] = {}
        correct = 0

        for entry in calibration_set:
            ground_truth = entry["ground_truth_verdict"]
            judgment = await self.judge(entry)
            per_class_total[ground_truth] = per_class_total.get(ground_truth, 0) + 1
            if judgment.verdict == ground_truth:
                correct += 1
                per_class_correct[ground_truth] = per_class_correct.get(ground_truth, 0) + 1
            confusion.setdefault(ground_truth, {})
            confusion[ground_truth][judgment.verdict] = (
                confusion[ground_truth].get(judgment.verdict, 0) + 1
            )

        per_class_accuracy = {
            cls: per_class_correct.get(cls, 0) / per_class_total[cls]
            for cls in per_class_total
        }

        return CalibrationResult(
            judge_model=self._model,
            overall_accuracy=correct / len(calibration_set),
            per_class_accuracy=per_class_accuracy,
            confusion_matrix=confusion,
            case_count=len(calibration_set),
            correct_count=correct,
        )


def _is_transient(exc: BaseException) -> bool:
    """Heuristic: classify Gemini errors as retry-worthy."""
    name = type(exc).__name__.lower()
    if "rate" in name or "timeout" in name or "deadline" in name:
        return True
    code = getattr(exc, "status_code", None)
    if isinstance(code, int) and 500 <= code < 600:
        return True
    return False
