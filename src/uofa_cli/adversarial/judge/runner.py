"""CLI dispatch for `uofa adversarial judge|triage|adjudicate`.

This is the glue layer between the argparse surface (in
`commands/adversarial.py`) and the typed module APIs (`bundle.py`,
`providers/*`, `triage.py`, `adjudication.py`).

Mock providers (`mock_a`, `mock_b`, `mock_c`) are wired here for the
spec §14.3 smoke path — they return canned Judgment fixtures with
non-degenerate inter-judge agreement (pairwise κ in 0.4–0.7 per the
plan) so the smoke test exercises Stage 4 stats math without spending
API budget.
"""

from __future__ import annotations

import asyncio
import csv
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

from uofa_cli.adversarial.judge.adjudication import (
    AgreementStats,
    compute_agreement,
    confusion_matrix,
    VERDICT_CLASSES,
)
from uofa_cli.adversarial.judge.bundle import open_bundle
from uofa_cli.adversarial.judge.bundle_writer import (
    BundleWriteError,
    write_bundle,
)
from uofa_cli.adversarial.judge.cli_args import (
    JudgesConfig,
    parse_judges,
    validate_parallel_flag,
)
from uofa_cli.adversarial.judge.family_check import check_judge_ensemble
from uofa_cli.adversarial.judge.providers.base import (
    AbstractJudgeProvider,
    CalibrationResult,
    Judgment,
)
from uofa_cli.adversarial.judge.triage import (
    TriageBucket,
    align_trios,
    triage_corpus,
)
from uofa_cli.output import error, info, result_line, warn

logger = logging.getLogger(__name__)


# ── mock provider for smoke testing ────────────────────────────────────


# Hand-designed verdicts so pairwise κ across the three mock judges lands
# in 0.4–0.7. Same shape as the test_adjudication fixture: 5 cases with
# 2-of-5 disagreements per pair. Indexed by case_id; falls back to a
# deterministic per-case hash if the case_id isn't pre-canned.
_MOCK_VERDICTS_A = ["REAL-GAP", "GENERATOR-ARTIFACT", "REAL-GAP", "OUT-OF-SCOPE", "CORRECT-DETECTION"]
_MOCK_VERDICTS_B = ["REAL-GAP", "REAL-GAP",           "REAL-GAP", "OUT-OF-SCOPE", "EXISTING-RULE-MISBEHAVIOR"]
_MOCK_VERDICTS_C = ["REAL-GAP", "GENERATOR-ARTIFACT", "GENERATOR-ARTIFACT", "OUT-OF-SCOPE", "EXISTING-RULE-MISBEHAVIOR"]
# Judge D (calibration anchor): produces a clean verdict per case for
# calibrate-anchor smoke. Mostly aligned with A so accuracy reads are sane.
_MOCK_VERDICTS_D = ["REAL-GAP", "GENERATOR-ARTIFACT", "REAL-GAP", "OUT-OF-SCOPE", "CORRECT-DETECTION"]
# Judge E (arbiter): produces verdicts for arbitration smoke. Confidence
# levels are emitted per-case so Stage 3b ARBITRATED/ESCALATED partition
# is exercised; see _build_mock_judgment confidence parameter for control.
_MOCK_VERDICTS_E = ["REAL-GAP", "GENERATOR-ARTIFACT", "REAL-GAP", "UNCERTAIN", "EXISTING-RULE-MISBEHAVIOR"]
_MOCK_VERDICT_MAP = {
    "mock_a": _MOCK_VERDICTS_A,
    "mock_b": _MOCK_VERDICTS_B,
    "mock_c": _MOCK_VERDICTS_C,
    "mock_d": _MOCK_VERDICTS_D,
    "mock_e": _MOCK_VERDICTS_E,
}

# Encounter-order ledger keyed by case_id. All mock providers use this to
# pick the same verdict array index per case, which is what preserves the
# pairwise-κ structure designed into _MOCK_VERDICTS_*.
_MOCK_CASE_LEDGER: dict[str, int] = {}


def _mock_case_index(case_id: str) -> int:
    """Assign each case_id a stable index on first encounter."""
    if case_id not in _MOCK_CASE_LEDGER:
        _MOCK_CASE_LEDGER[case_id] = len(_MOCK_CASE_LEDGER)
    return _MOCK_CASE_LEDGER[case_id]


def _reset_mock_ledger() -> None:
    """Clear the ledger between runs (used by tests)."""
    _MOCK_CASE_LEDGER.clear()


class _MockProvider(AbstractJudgeProvider):
    """Canned-response provider for smoke tests; no network calls.

    Uses a per-case-id ledger (assigned in encounter order) to pick a
    verdict from the 5-cell array. All three providers share the global
    `_MOCK_CASE_INDEX` so case_id 'foo' lands at the same index across
    A/B/C — that's what preserves the designed pairwise κ structure.
    """

    def __init__(self, token: str) -> None:
        if token not in _MOCK_VERDICT_MAP:
            raise ValueError(f"unknown mock token: {token}")
        self._token = token
        self._family = {
            "mock_a": "Mock-A", "mock_b": "Mock-B", "mock_c": "Mock-C",
            "mock_d": "Mock-D", "mock_e": "Mock-E",
        }[token]
        self._judge_role = {
            "mock_a": "production", "mock_b": "production", "mock_c": "production",
            "mock_d": "calibration_anchor",
            "mock_e": "arbiter",
        }[token]
        self._verdicts = _MOCK_VERDICT_MAP[token]

    @property
    def family(self) -> str:
        return self._family

    @property
    def model(self) -> str:
        return self._token

    @property
    def judge_role(self) -> str:
        return self._judge_role

    @property
    def supports_strict_schema(self) -> bool:
        return False

    async def judge(self, case: dict) -> Judgment:
        case_id = case.get("case_id", "<unknown>")
        idx = _mock_case_index(case_id) % len(self._verdicts)
        verdict = self._verdicts[idx]
        return _build_mock_judgment(case_id, verdict, self._token)

    async def calibrate(self, calibration_set: list[dict]) -> CalibrationResult:
        # Used only to verify the smoke test produces a calibration_results
        # JSON file with the expected shape. Real calibration is post-Tier-A.
        if not calibration_set:
            return CalibrationResult(
                judge_model=self._token,
                overall_accuracy=0.0,
                per_class_accuracy={},
                confusion_matrix={},
                case_count=0,
                correct_count=0,
            )
        correct = 0
        per_class_total: dict[str, int] = {}
        per_class_correct: dict[str, int] = {}
        for entry in calibration_set:
            gt = entry.get("ground_truth_verdict", "REAL-GAP")
            judgment = await self.judge(entry)
            per_class_total[gt] = per_class_total.get(gt, 0) + 1
            if judgment.verdict == gt:
                correct += 1
                per_class_correct[gt] = per_class_correct.get(gt, 0) + 1
        return CalibrationResult(
            judge_model=self._token,
            overall_accuracy=correct / len(calibration_set),
            per_class_accuracy={
                cls: per_class_correct.get(cls, 0) / per_class_total[cls]
                for cls in per_class_total
            },
            confusion_matrix={},
            case_count=len(calibration_set),
            correct_count=correct,
        )


def _build_mock_judgment(case_id: str, verdict: str, model: str) -> Judgment:
    return Judgment(
        case_id=case_id,
        verdict=verdict,
        confidence=0.85,
        reasoning_steps={
            "source_taxonomy_identified": "[mock]",
            "target_rule_identified": "[mock]",
            "rule_firings_inspected": "[mock]",
            "instantiation_check": "[mock] hand-canned for smoke determinism",
            "verdict_commitment": verdict,
        },
        reasoning="[mock] canned verdict for smoke test",
        section_6_7_candidate=None,
        alternative_rule_analysis=None,
        prompt_template_version="v0.0.0-stub",
        judge_model=model,
        judge_thinking_enabled=False,
        judge_model_params={"temperature": 0.0, "seed": 42},
        generator_provenance={
            "generator_model": "anthropic/claude-sonnet-4-6",
            "temperature": None,
            "seed": None,
        },
    )


# ── provider construction ──────────────────────────────────────────────


def _build_providers(
    judges: JudgesConfig,
    *,
    model_overrides: dict[str, str | None] | None = None,
    judge_role: str = "production",
) -> list[AbstractJudgeProvider]:
    """Construct provider instances for each token in the config.

    All real providers go through `LiteLLMProvider` (Phase 3 v1.6 litellm-first
    refactor); per-vendor variations live in `capabilities.py`. Mock tokens
    use the canned-verdict `_MockProvider`.

    `model_overrides` keys are provider tokens (`openai`, `gemini`, `hf-llama`,
    `anthropic`, `mistral`); values are model id strings or None (use
    capability-table default).

    `judge_role` is propagated to LiteLLMProvider for run-manifest accounting.
    Default 'production' for the `judge` subcommand; calibrate-anchor uses
    'calibration_anchor', arbitrate uses 'arbiter'.
    """
    from uofa_cli.adversarial.judge.providers.litellm_provider import LiteLLMProvider

    overrides = model_overrides or {}
    providers: list[AbstractJudgeProvider] = []
    for token in judges.tokens:
        if token.startswith("mock_"):
            providers.append(_MockProvider(token))
            continue
        # Real provider via litellm. Capability table maps token → defaults.
        try:
            providers.append(LiteLLMProvider(
                provider_token=token,
                model=overrides.get(token),
                judge_role=judge_role,
            ))
        except KeyError as e:
            raise ValueError(f"unknown judge token: {token}") from e
    return providers


# ── run_bundle ─────────────────────────────────────────────────────────


def run_bundle(args) -> int:
    """Entry point for `uofa adversarial bundle`.

    Packages an already-analyzed Phase 2 batch into a judge_ready_bundle.tgz
    without re-running the rule engine. Use when outcomes.csv already exists
    (e.g., 2026-04-26 corpus). For fresh runs, use `analyze --emit-judge-bundle`.
    """
    batch_dir: Path = args.batch_dir
    out_path: Path = args.out
    outcomes_csv: Path = args.outcomes_csv or (batch_dir / "coverage" / "outcomes.csv")

    if not batch_dir.is_dir():
        error(f"batch_dir not found: {batch_dir}")
        return 2
    if not outcomes_csv.exists():
        error(f"outcomes.csv not found: {outcomes_csv}")
        return 2

    info(f"packaging {batch_dir} → {out_path}")
    try:
        result = write_bundle(batch_dir, outcomes_csv, out_path)
    except BundleWriteError as e:
        error(f"bundle write failed: {e}")
        return 3

    info(
        f"  wrote {result.package_count} packages; "
        f"normalized class distribution {result.distribution}"
    )
    if result.warnings:
        for w in result.warnings:
            warn(w)
    result_line("judge_bundle", True, str(out_path))
    return 0


# ── run_judge ──────────────────────────────────────────────────────────


def run_judge(args) -> int:
    """Entry point for `uofa adversarial judge`."""
    in_bundle: Path = args.in_bundle
    out_dir: Path = args.out
    raw_judges: str = args.judges
    parallel: int = getattr(args, "parallel", 8)
    calibration_only: bool = getattr(args, "calibration_only", False)
    allow_same_family: bool = getattr(args, "allow_same_family_judge", False)

    try:
        judges = parse_judges(raw_judges)
    except ValueError as e:
        error(f"--judges: {e}")
        return 2

    try:
        validate_parallel_flag(judges, parallel)
    except ValueError as e:
        error(str(e))
        return 2

    # Family check on real providers only; mock_* tokens are synthetic
    # and skipped (they have no FAMILY_MAP entry by design).
    real_roles = [
        (f"judge_{p}", t)
        for p, t in zip(judges.positions, judges.tokens)
        if not t.startswith("mock_")
    ]
    if real_roles:
        result = check_judge_ensemble(real_roles, allow_same_family=allow_same_family)
        if result.warning:
            warn(result.warning)
        if result.exit_code != 0:
            return result.exit_code

    if not in_bundle.exists():
        error(f"bundle not found: {in_bundle}")
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)
    model_overrides = {
        "openai": getattr(args, "model_openai", None),
        "gemini": getattr(args, "model_gemini", None),
        "hf-llama": getattr(args, "model_hf_llama", None),
        "anthropic": getattr(args, "model_anthropic", None),
    }
    providers = _build_providers(judges, model_overrides=model_overrides)

    info(
        f"judging {in_bundle.name} with judges "
        f"{list(zip(judges.positions, judges.tokens))} (parallel={parallel}, "
        f"calibration_only={calibration_only})"
    )

    # Run async per-judge judgments. Tier A: serial calls per case (the
    # parallelism story is for HF Endpoints batches, deferred to Stage 2).
    asyncio.run(_judge_bundle(
        in_bundle=in_bundle,
        providers=providers,
        positions=judges.positions,
        tokens=judges.tokens,
        out_dir=out_dir,
        calibration_only=calibration_only,
    ))

    result_line("judgments", True, str(out_dir))
    return 0


async def _judge_bundle(
    *,
    in_bundle: Path,
    providers: list[AbstractJudgeProvider],
    positions: tuple[str, ...],
    tokens: tuple[str, ...],
    out_dir: Path,
    calibration_only: bool,
) -> None:
    """For each case in the bundle, run all providers and write per-judge JSONL."""
    _reset_mock_ledger()
    with open_bundle(in_bundle) as bundle:
        cases = list(bundle.iter_entries())

    if calibration_only:
        # Tier A: in absence of a real calibration set, judge first 5 cases
        # as a stand-in. Real Stage 1 reads specs/calibration/calibration_set_v1.jsonl.
        cases = cases[:5]

    # Collect verdicts in memory so the calibration summary doesn't have
    # to re-read partially-written JSONL files (the handles below are
    # buffered; reading them mid-loop returns nothing).
    verdicts_by_pos: dict[str, list[str]] = {pos: [] for pos in positions}

    handles = {pos: (out_dir / f"judgments_{pos}.jsonl").open("w") for pos in positions}
    try:
        for entry in cases:
            case = {
                "case_id": entry.case_id,
                "coverage_class": entry.outcome.get("coverage_class"),
                "phase2_outcome_class_raw": entry.outcome.get("phase2_outcome_class_raw"),
                "source_taxonomy": entry.outcome.get("source_taxonomy"),
                "rules_fired": entry.outcome.get("rules_fired", []),
                "expected_rule": entry.outcome.get("expected_rule"),
                "section_6_7_mapping": entry.outcome.get("section_6_7_mapping"),
                "package": entry.package,
                "ground_truth_verdict": entry.outcome.get("coverage_class"),  # mock
            }
            for pos, provider in zip(positions, providers):
                judgment = await provider.judge(case)
                handles[pos].write(json.dumps(_judgment_to_dict(judgment)) + "\n")
                verdicts_by_pos[pos].append(judgment.verdict)
    finally:
        for h in handles.values():
            h.close()

    # Calibration-only: write per-judge calibration_results plus a summary
    # with pairwise kappas computed from the in-memory verdict lists.
    if calibration_only:
        for pos, token, provider in zip(positions, tokens, providers):
            cal_cases = [
                {
                    "case_id": e.case_id,
                    "coverage_class": e.outcome.get("coverage_class"),
                    "ground_truth_verdict": e.outcome.get("coverage_class") or "REAL-GAP",
                }
                for e in cases
            ]
            cal_result = await provider.calibrate(cal_cases)
            cal_path = out_dir / f"calibration_results_{token}.json"
            cal_path.write_text(json.dumps({
                "judge_model": cal_result.judge_model,
                "overall_accuracy": cal_result.overall_accuracy,
                "per_class_accuracy": cal_result.per_class_accuracy,
                "case_count": cal_result.case_count,
                "correct_count": cal_result.correct_count,
            }, indent=2))

        stats = compute_agreement(
            verdicts_by_pos["A"], verdicts_by_pos["B"], verdicts_by_pos["C"]
        )
        # JSON doesn't have a NaN literal; substitute null (matches §12.2 convention).
        def _nan_to_none(x: float) -> float | None:
            return None if isinstance(x, float) and x != x else x
        (out_dir / "calibration_results_summary.json").write_text(json.dumps({
            "case_count": stats.case_count,
            "pairwise_kappa_AB": _nan_to_none(stats.cohen_kappa_AB),
            "pairwise_kappa_AC": _nan_to_none(stats.cohen_kappa_AC),
            "pairwise_kappa_BC": _nan_to_none(stats.cohen_kappa_BC),
            "fleiss_kappa": _nan_to_none(stats.fleiss_kappa),
        }, indent=2))


def _judgment_to_dict(j: Judgment) -> dict[str, Any]:
    """Serialize a Judgment to JSON-compatible dict (drops raw_response)."""
    d = asdict(j)
    d.pop("raw_response", None)
    return d


# ── run_triage ─────────────────────────────────────────────────────────


def run_triage(args) -> int:
    """Entry point for `uofa adversarial triage`."""
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    judgments_a = _load_judgments(args.judgments_a)
    judgments_b = _load_judgments(args.judgments_b)
    judgments_c = _load_judgments(args.judgments_c)

    trios = align_trios(judgments_a, judgments_b, judgments_c)
    confidence_floor = float(getattr(args, "confidence_floor", 0.6))
    result = triage_corpus(trios, confidence_floor=confidence_floor)

    # adjudication_queue.csv: DIVERGENT + UNCERTAIN cases for author review.
    queue_path = out_dir / "adjudication_queue.csv"
    with queue_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "case_id", "bucket", "majority_verdict", "disagreement_type",
            "verdict_a", "verdict_b", "verdict_c",
            "confidence_a", "confidence_b", "confidence_c",
        ])
        for entry in result.entries:
            if entry.bucket == TriageBucket.CONVERGENT:
                continue
            ja, jb, jc = entry.judgments
            w.writerow([
                entry.case_id, entry.bucket.value, entry.majority_verdict or "",
                entry.disagreement_type,
                ja.verdict, jb.verdict, jc.verdict,
                f"{ja.confidence:.3f}", f"{jb.confidence:.3f}", f"{jc.confidence:.3f}",
            ])

    # triage_summary.json with bucket counts.
    summary_path = out_dir / "triage_summary.json"
    summary_path.write_text(json.dumps({
        "case_count": len(result.entries),
        "bucket_counts": {b.value: c for b, c in result.bucket_counts.items()},
    }, indent=2))

    info(f"  triage: {dict((b.value, c) for b, c in result.bucket_counts.items())}")
    result_line("adjudication_queue", True, str(queue_path))
    result_line("triage_summary", True, str(summary_path))
    return 0


# ── run_adjudicate ─────────────────────────────────────────────────────


def run_adjudicate(args) -> int:
    """Entry point for `uofa adversarial adjudicate`."""
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    judgments_a = _load_judgments(args.judgments_a)
    judgments_b = _load_judgments(args.judgments_b)
    judgments_c = _load_judgments(args.judgments_c)

    trios = align_trios(judgments_a, judgments_b, judgments_c)
    if not trios:
        error("no aligned trios; cannot compute agreement statistics")
        return 1

    verdicts_a = [t[0].verdict for t in trios]
    verdicts_b = [t[1].verdict for t in trios]
    verdicts_c = [t[2].verdict for t in trios]

    stats = compute_agreement(verdicts_a, verdicts_b, verdicts_c)

    # agreement_stats.json (spec §12.2)
    stats_path = out_dir / "agreement_stats.json"
    stats_path.write_text(json.dumps({
        "case_count": stats.case_count,
        "cohen_kappa_AB": stats.cohen_kappa_AB,
        "cohen_kappa_AC": stats.cohen_kappa_AC,
        "cohen_kappa_BC": stats.cohen_kappa_BC,
        "fleiss_kappa": stats.fleiss_kappa,
        "raw_agreement_at_least_2of3": stats.raw_agreement_at_least_2of3,
    }, indent=2))

    # Confusion matrices per pair (spec §12.2 layout).
    _write_confusion(out_dir / "confusion_matrix_AB.csv", verdicts_a, verdicts_b)
    _write_confusion(out_dir / "confusion_matrix_AC.csv", verdicts_a, verdicts_c)
    _write_confusion(out_dir / "confusion_matrix_BC.csv", verdicts_b, verdicts_c)

    info(
        f"  agreement: AB κ={stats.cohen_kappa_AB:.3f}, "
        f"AC κ={stats.cohen_kappa_AC:.3f}, BC κ={stats.cohen_kappa_BC:.3f}, "
        f"Fleiss κ={stats.fleiss_kappa:.3f}"
    )
    result_line("agreement_stats", True, str(stats_path))
    return 0


def _load_judgments(path: Path) -> list[Judgment]:
    """Read a judgments_<position>.jsonl file into Judgment dataclasses."""
    judgments: list[Judgment] = []
    if not path.exists():
        raise FileNotFoundError(f"judgments file not found: {path}")
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        judgments.append(Judgment(
            case_id=data["case_id"],
            verdict=data["verdict"],
            confidence=data["confidence"],
            reasoning_steps=data["reasoning_steps"],
            reasoning=data["reasoning"],
            section_6_7_candidate=data.get("section_6_7_candidate"),
            alternative_rule_analysis=data.get("alternative_rule_analysis"),
            prompt_template_version=data["prompt_template_version"],
            judge_model=data["judge_model"],
            judge_thinking_enabled=data["judge_thinking_enabled"],
            judge_model_params=data["judge_model_params"],
            generator_provenance=data["generator_provenance"],
        ))
    return judgments


def _write_confusion(path: Path, x: list[str], y: list[str]) -> None:
    """Write a 6×6 confusion matrix CSV with VERDICT_CLASSES row/col headers."""
    matrix = confusion_matrix(x, y)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["", *VERDICT_CLASSES])
        for label, row in zip(VERDICT_CLASSES, matrix):
            w.writerow([label, *row])
