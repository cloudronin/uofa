#!/usr/bin/env python3
"""End-to-end Phase 3 v1.6 smoke against the full 5-judge panel.

Runs ONE calibration case through:
  - Judge A (production, OpenAI gpt-5.4)
  - Judge B (production, Gemini 3.1 Pro Preview)
  - Judge C (production, Llama 4 Maverick via HF Router → Sambanova)
  - Judge D (calibration anchor, Claude Sonnet 4.6)
  - Triage (Stage 3a) → if DISAGREEMENT, Judge E arbitration
  - Judge E (arbiter, Mistral Large 3) when triage routes to Stage 3b

Reports per-judge: verdict, confidence, latency (s), USD cost (via
litellm.cost_per_token off the response usage), and evidence_gap when
the verdict is OUT-OF-SCOPE. Final summary line shows total wall-clock
+ total cost.

Usage (with all five keys present):
  ANTHROPIC_API_KEY=$(cat /tmp/anthropic.txt) \
  OPENAI_API_KEY=$(cat /tmp/openai.txt) \
  GEMINI_API_KEY=$(cat /tmp/gemini.txt) \
  HF_TOKEN=$(cat /tmp/huggingface.txt) \
  MISTRAL_API_KEY=$(cat /tmp/mistral.txt) \
      python dev/tools/scripts/smoke_full_panel.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Add src to path before importing.
HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3] / "src"))

from uofa_cli.adversarial.judge.providers.litellm_provider import LiteLLMProvider  # noqa: E402
from uofa_cli.adversarial.judge.triage import triage_case, TriageBucket  # noqa: E402


# Calibration case to use — non-canonical REAL-GAP so judges don't see
# it in the prompt's few-shot section.
CASE_ID = "cal-007-real_gap-ambiguous"


@dataclass
class JudgeRun:
    role: str
    token: str
    verdict: str
    confidence: float
    latency_s: float
    cost_usd: float
    evidence_gap: dict | None
    error: str | None = None


def _required_env(*names: str) -> dict[str, str]:
    """Verify all required env vars are set; print a hint if not."""
    missing = [n for n in names if n not in os.environ]
    if missing:
        print(f"ERROR: missing env vars: {missing}", file=sys.stderr)
        print(
            "  hint: ANTHROPIC_API_KEY=$(cat /tmp/anthropic.txt) "
            "OPENAI_API_KEY=$(cat /tmp/openai.txt) "
            "GEMINI_API_KEY=$(cat /tmp/gemini.txt) "
            "HF_TOKEN=$(cat /tmp/huggingface.txt) "
            "MISTRAL_API_KEY=$(cat /tmp/mistral.txt) "
            "python dev/tools/scripts/smoke_full_panel.py",
            file=sys.stderr,
        )
        sys.exit(2)
    return {n: os.environ[n] for n in names}


def _load_calibration_case(case_id: str) -> dict:
    """Load the calibration record + the package JSON-LD into the dict
    shape the prompt builder expects."""
    cal_path = Path("specs/calibration/calibration_set_v1.jsonl")
    record = None
    for line in cal_path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r["case_id"] == case_id:
            record = r
            break
    if record is None:
        raise SystemExit(f"calibration case {case_id} not found")

    pkg_path = Path(record["package_path"])
    package = json.loads(pkg_path.read_text()) if pkg_path.exists() else {
        "id": case_id, "name": "(package missing)"
    }
    return {
        "case_id": record["case_id"],
        "phase2_case_id": record.get("phase2_case_id"),
        "source_taxonomy": record.get("source_taxonomy"),
        "rules_fired": record.get("rules_fired", []),
        "expected_rule": record.get("expected_target_rule"),
        "section_6_7_mapping": record.get("section_6_7_mapping"),
        "phase2_outcome_class_raw": record.get("phase2_outcome_class"),
        "package": package,
        "ground_truth_verdict": record.get("ground_truth_verdict"),
    }


async def _run_one_judge(role: str, token: str, case: dict, *, judge_role: str = "production") -> JudgeRun:
    """Time + cost a single judge.judge() call."""
    provider = LiteLLMProvider(
        provider_token=token,
        judge_role=judge_role,
        thinking_enabled=False,  # litellm 1.63 has gaps for current-gen reasoning params
    )
    t0 = time.perf_counter()
    try:
        judgment = await provider.judge(case)
        latency = time.perf_counter() - t0
        cost = _extract_cost(judgment, token)
        return JudgeRun(
            role=role,
            token=token,
            verdict=judgment.verdict,
            confidence=judgment.confidence,
            latency_s=latency,
            cost_usd=cost,
            evidence_gap=judgment.evidence_gap,
        )
    except Exception as e:
        latency = time.perf_counter() - t0
        return JudgeRun(
            role=role, token=token, verdict="ERROR", confidence=0.0,
            latency_s=latency, cost_usd=0.0, evidence_gap=None, error=repr(e)[:300],
        )


def _extract_cost(judgment, provider_token: str) -> float:
    """Pull USD cost off the response. Mirrors runner._extract_response_cost."""
    raw = getattr(judgment, "raw_response", None) or {}
    if isinstance(raw, dict):
        hidden = raw.get("_hidden_params") or {}
        if "response_cost" in hidden:
            try:
                return float(hidden["response_cost"])
            except (ValueError, TypeError):
                pass
        usage = raw.get("usage")
        if usage:
            try:
                from uofa_cli.adversarial.judge.cost_gate import estimate_call_cost
                return estimate_call_cost(
                    provider_token, getattr(judgment, "judge_model", None),
                    input_tokens=int(usage.get("prompt_tokens", 0) or 0),
                    output_tokens=int(usage.get("completion_tokens", 0) or 0),
                )
            except Exception:
                return 0.0
    return 0.0


def _print_run(r: JudgeRun) -> None:
    if r.error:
        print(f"  {r.role:8} ({r.token:9}) FAIL  latency={r.latency_s:6.2f}s  err={r.error}")
        return
    gap = ""
    if r.evidence_gap:
        gap = f" gap={r.evidence_gap.get('missing_evidence_type','')[:60]!r}"
    print(
        f"  {r.role:8} ({r.token:9}) {r.verdict:25} "
        f"conf={r.confidence:.2f}  latency={r.latency_s:6.2f}s  "
        f"cost=${r.cost_usd:.5f}{gap}"
    )


async def main() -> int:
    _required_env(
        "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY",
        "HF_TOKEN", "MISTRAL_API_KEY",
    )

    case = _load_calibration_case(CASE_ID)
    print(f"Case: {CASE_ID}")
    print(f"  ground truth: {case['ground_truth_verdict']}")
    print(f"  source taxonomy: {case['source_taxonomy']}")
    print(f"  §6.7 candidate: {case['section_6_7_mapping']}")
    print(f"  package size: {len(json.dumps(case['package']))} bytes")
    print()

    # Stage 1+2: production trio + calibration anchor in parallel.
    print("Stage 1+2 — production trio + calibration anchor (parallel):")
    t0 = time.perf_counter()
    a, b, c, d = await asyncio.gather(
        _run_one_judge("Judge A", "openai", case, judge_role="production"),
        _run_one_judge("Judge B", "gemini", case, judge_role="production"),
        _run_one_judge("Judge C", "hf-llama", case, judge_role="production"),
        _run_one_judge("Judge D", "anthropic", case, judge_role="calibration_anchor"),
    )
    parallel_wall = time.perf_counter() - t0
    for r in (a, b, c, d):
        _print_run(r)
    print(f"  ── wall-clock for parallel block: {parallel_wall:.2f}s")
    print()

    # Stage 3a: triage A/B/C only (D is anchor, not part of production triage).
    if any(r.error for r in (a, b, c)):
        print("Stage 3 — SKIPPED: one or more production judges errored.")
    else:
        from types import SimpleNamespace
        # Build lightweight Judgment-like objects for triage_case.
        def _stub(r: JudgeRun, case_id: str):
            return SimpleNamespace(
                case_id=case_id, verdict=r.verdict, confidence=r.confidence,
            )
        ja, jb, jc = (_stub(r, case["case_id"]) for r in (a, b, c))
        triage = triage_case(ja, jb, jc, confidence_floor=0.6)
        print(f"Stage 3a — triage: bucket={triage.bucket.value}, "
              f"majority={triage.majority_verdict!r}, "
              f"subtype={triage.disagreement_type}")

        # Stage 3b: arbiter only on disagreement.
        e_run = None
        if triage.bucket != TriageBucket.CONVERGENT:
            print()
            print("Stage 3b — Judge E arbitration:")
            arbitration_case = dict(case)
            arbitration_case["production_verdicts"] = [
                {"position": "A", "verdict": a.verdict, "confidence": a.confidence,
                 "reasoning": "(see judgments_A.jsonl)"},
                {"position": "B", "verdict": b.verdict, "confidence": b.confidence,
                 "reasoning": "(see judgments_B.jsonl)"},
                {"position": "C", "verdict": c.verdict, "confidence": c.confidence,
                 "reasoning": "(see judgments_C.jsonl)"},
            ]
            e_run = await _run_one_judge(
                "Judge E", "mistral", arbitration_case, judge_role="arbiter"
            )
            _print_run(e_run)

    # Summary.
    print()
    print("=" * 60)
    runs = [a, b, c, d]
    if "e_run" in dir() and e_run is not None:
        runs.append(e_run)
    total_cost = sum(r.cost_usd for r in runs)
    total_latency_serial = sum(r.latency_s for r in runs)
    print(f"Total cost (USD):           ${total_cost:.5f}")
    print(f"Total latency (serial):     {total_latency_serial:.2f}s")
    print(f"Wall-clock (parallel A-D):  {parallel_wall:.2f}s")
    print()
    print("Verdict ledger:")
    print(f"  ground truth (cal-007):  {case['ground_truth_verdict']}")
    for r in runs:
        marker = " ✓" if r.verdict == case["ground_truth_verdict"] else ""
        print(f"  {r.role:8} ({r.token:9}): {r.verdict}{marker}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
