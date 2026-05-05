"""Judge E arbitration pipeline (Phase 3 v1.6 §6.7, §7.8, §10.2).

Stage 3b workflow:
  1. Load production-judge JSONL files (judgments_A/B/C.jsonl).
  2. Load DISAGREEMENT queue from triage Stage 3a output.
  3. For each disagreement case, build the arbitration prompt with the
     three production-judge verdicts side-by-side (without Judge D's
     calibration verdict per spec §7.8 anti-patterns).
  4. Call Judge E (Mistral via litellm) with the
     judge_e_output_schema.json strict-mode response_format.
  5. Validate response against the full schema (including evidence_gap
     conditional-required for OOS).
  6. Partition results by Judge E confidence:
        ≥ 0.6 → ARBITRATED (close at Judge E layer; final verdict)
        < 0.6 → ESCALATED (route to author final-arbitration)
"""

from __future__ import annotations

import asyncio
import csv
import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

from uofa_cli.adversarial.judge.providers.base import (
    AbstractJudgeProvider,
    Judgment,
)

logger = logging.getLogger(__name__)


# Default confidence floor matches spec §10.1 / §10.2 for protocol consistency.
DEFAULT_CONFIDENCE_FLOOR = 0.6


@dataclass(frozen=True)
class ArbitrationEntry:
    """One Judge E arbitration result."""

    case_id: str
    verdict: str
    confidence: float
    reasoning: str
    arbitration_basis: str
    production_judge_evaluation: dict
    evidence_gap: dict | None
    raw_response: dict


@dataclass
class Stage3bPartition:
    """ARBITRATED / ESCALATED partition per spec §10.2."""

    arbitrated: list[ArbitrationEntry]
    escalated: list[ArbitrationEntry]
    confidence_floor: float


async def arbitrate_disagreement_queue(
    disagreement_case_ids: Iterable[str],
    production_judgments: dict[str, dict[str, Judgment]],
    judge_e: AbstractJudgeProvider,
    *,
    package_lookup: dict[str, dict] | None = None,
    confidence_floor: float = DEFAULT_CONFIDENCE_FLOOR,
) -> Stage3bPartition:
    """Run Judge E over the disagreement queue and partition by confidence.

    `production_judgments` is a dict keyed by position ('A', 'B', 'C')
    where each value is a dict {case_id: Judgment} from that production
    judge.

    `package_lookup` is optional: dict {case_id: package_dict} so the
    arbitration prompt can include the JSON-LD payload. If absent,
    Judge E sees the production-judge reasoning + case metadata only
    (the case dict from the bundle entry).
    """
    arbitrated: list[ArbitrationEntry] = []
    escalated: list[ArbitrationEntry] = []
    package_lookup = package_lookup or {}

    for case_id in disagreement_case_ids:
        production_verdicts = []
        for position in ("A", "B", "C"):
            j = production_judgments.get(position, {}).get(case_id)
            if j is None:
                logger.warning(
                    "case %s missing judgment for position %s; skipping arbitration",
                    case_id, position,
                )
                break
            production_verdicts.append({
                "judge_position": position,
                "judge_model": j.judge_model,
                "verdict": j.verdict,
                "confidence": j.confidence,
                "reasoning_steps": j.reasoning_steps,
                "reasoning": j.reasoning,
            })
        else:
            # All three production judgments found; arbitrate.
            case = {
                "case_id": case_id,
                "package": package_lookup.get(case_id, {}),
                "production_verdicts": production_verdicts,
            }
            try:
                judgment = await _arbitrate_case(
                    judge_e, case, production_verdicts
                )
            except Exception as e:
                logger.error("arbitration failed for case %s: %s", case_id, e)
                continue

            entry = _judgment_to_entry(judgment)
            if entry.confidence >= confidence_floor:
                arbitrated.append(entry)
            else:
                escalated.append(entry)

    return Stage3bPartition(
        arbitrated=arbitrated,
        escalated=escalated,
        confidence_floor=confidence_floor,
    )


async def _arbitrate_case(
    judge_e: AbstractJudgeProvider,
    case: dict,
    production_verdicts: list[dict],
) -> Judgment:
    """Single-case Judge E call.

    For the LiteLLM-backed Judge E we extend the per-case prompt with
    the three production-judge verdicts. The provider's `judge` method
    builds the prompt using the case dict; we attach the production
    verdicts in a way the prompt builder picks up.
    """
    # Annotate the case so the prompt builder can pick up production verdicts.
    annotated = {**case, "_production_verdicts": production_verdicts}
    # Switch the provider's prompt mode for this call. Real LiteLLMProvider
    # uses `judge_role=='arbiter'` to select the arbitration prompt.
    return await judge_e.judge(annotated)


def _judgment_to_entry(j: Judgment) -> ArbitrationEntry:
    raw = j.raw_response or {}
    return ArbitrationEntry(
        case_id=j.case_id,
        verdict=j.verdict,
        confidence=j.confidence,
        reasoning=j.reasoning,
        arbitration_basis=raw.get("arbitration_basis", "package_content"),
        production_judge_evaluation=raw.get("production_judge_evaluation", {}),
        evidence_gap=raw.get("evidence_gap"),
        raw_response=raw,
    )


# ── Stage 3b partition (works on already-collected Judge E results) ────


def partition_arbitration_results(
    arbitration_results: list[ArbitrationEntry],
    *,
    confidence_floor: float = DEFAULT_CONFIDENCE_FLOOR,
) -> Stage3bPartition:
    """Pure-function partition — used by tests and by replays."""
    arbitrated = [r for r in arbitration_results if r.confidence >= confidence_floor]
    escalated = [r for r in arbitration_results if r.confidence < confidence_floor]
    return Stage3bPartition(
        arbitrated=arbitrated,
        escalated=escalated,
        confidence_floor=confidence_floor,
    )


# ── output writers ─────────────────────────────────────────────────────


def write_arbitration_jsonl(entries: Iterable[ArbitrationEntry], out_path: Path) -> None:
    """Persist arbitration entries as JSONL (one record per line)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        for entry in entries:
            f.write(json.dumps(asdict(entry)) + "\n")


def write_escalation_queue_csv(entries: Iterable[ArbitrationEntry], out_path: Path) -> None:
    """Write the ESCALATED bin as a CSV for author final-arbitration (spec §10.3)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "case_id", "judge_e_verdict", "judge_e_confidence",
            "arbitration_basis", "judge_e_reasoning",
        ])
        for entry in entries:
            w.writerow([
                entry.case_id, entry.verdict, f"{entry.confidence:.3f}",
                entry.arbitration_basis, entry.reasoning,
            ])


def load_arbitration_jsonl(path: Path) -> list[ArbitrationEntry]:
    """Read a judgments_E.jsonl file back into ArbitrationEntry objects."""
    if not path.exists():
        raise FileNotFoundError(path)
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        out.append(ArbitrationEntry(
            case_id=d["case_id"],
            verdict=d["verdict"],
            confidence=float(d["confidence"]),
            reasoning=d.get("reasoning", ""),
            arbitration_basis=d.get("arbitration_basis", "package_content"),
            production_judge_evaluation=d.get("production_judge_evaluation", {}),
            evidence_gap=d.get("evidence_gap"),
            raw_response=d.get("raw_response", {}),
        ))
    return out
