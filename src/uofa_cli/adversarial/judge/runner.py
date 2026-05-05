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
    AuthorAdjudicationStats,
    JudgeDAgreementStats,
    JudgeEStats,
    compute_agreement,
    compute_author_adjudication,
    compute_judge_e_agreement,
    compute_judge_e_vs_d_agreement,
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
    prompt_template_version: str | None = None,
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

    `prompt_template_version`, when set, is stamped into every Judgment
    record this provider emits — production runs pin this to "v1.1.0" so
    gate values don't silently shift if the module-level default in
    prompts.py changes during the §8.3 3-iteration path.
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
                prompt_template_version=prompt_template_version,
            ))
        except KeyError as e:
            raise ValueError(f"unknown judge token: {token}") from e
    return providers


# ── run_arbitrate (Phase 3 v1.6 §6.7, §10.2) ───────────────────────────


def run_arbitrate(args) -> int:
    """Entry point for `uofa adversarial arbitrate`.

    Reads triage Stage 3a output (DISAGREEMENT queue) + the three
    production-judge JSONL files, runs Judge E (Mistral via litellm or
    a mock provider) over each disagreement case, partitions by
    confidence into ARBITRATED / ESCALATED bins per spec §10.2.
    """
    from uofa_cli.adversarial.judge.arbitration import (
        arbitrate_disagreement_queue,
        write_arbitration_jsonl,
        write_escalation_queue_csv,
        partition_arbitration_results,
    )

    judgments_a_path: Path = args.judgments_a
    judgments_b_path: Path = args.judgments_b
    judgments_c_path: Path = args.judgments_c
    disagreement_csv: Path = args.disagreement_queue
    out_dir: Path = args.out
    judge_e_token: str = getattr(args, "judge_e", "mistral")
    confidence_floor: float = float(getattr(args, "confidence_floor", 0.6))

    out_dir.mkdir(parents=True, exist_ok=True)

    # Load production judgments + index by case_id, per position.
    production: dict[str, dict[str, Judgment]] = {
        "A": {j.case_id: j for j in _load_judgments(judgments_a_path)},
        "B": {j.case_id: j for j in _load_judgments(judgments_b_path)},
        "C": {j.case_id: j for j in _load_judgments(judgments_c_path)},
    }

    disagreement_case_ids = _read_disagreement_queue(disagreement_csv)
    info(f"  arbitration queue: {len(disagreement_case_ids)} cases")

    # Build the Judge E provider (real via litellm, or mock via _MockProvider).
    if judge_e_token.startswith("mock_"):
        provider = _MockProvider(judge_e_token)
    else:
        # Real Mistral via litellm.
        from uofa_cli.adversarial.judge.providers.litellm_provider import (
            LiteLLMProvider,
        )
        try:
            provider = LiteLLMProvider(
                provider_token=judge_e_token,
                judge_role="arbiter",
            )
        except KeyError as e:
            error(f"unknown judge_e token: {judge_e_token}")
            return 2

    partition = asyncio.run(arbitrate_disagreement_queue(
        disagreement_case_ids=disagreement_case_ids,
        production_judgments=production,
        judge_e=provider,
        confidence_floor=confidence_floor,
    ))

    # Persist outputs.
    all_entries = partition.arbitrated + partition.escalated
    write_arbitration_jsonl(all_entries, out_dir / "judgments_E.jsonl")
    write_arbitration_jsonl(partition.arbitrated, out_dir / "arbitrated.jsonl")
    write_escalation_queue_csv(partition.escalated, out_dir / "escalation_queue.csv")

    info(f"  ARBITRATED (≥{confidence_floor}): {len(partition.arbitrated)}")
    info(f"  ESCALATED  (<{confidence_floor}): {len(partition.escalated)}")
    result_line("judgments_E", True, str(out_dir / "judgments_E.jsonl"))
    result_line("escalation_queue", True, str(out_dir / "escalation_queue.csv"))
    return 0


def _read_disagreement_queue(path: Path) -> list[str]:
    """Read case_ids from the triage Stage 3a disagreement_queue.csv."""
    import csv as _csv
    if not path.exists():
        raise FileNotFoundError(f"disagreement queue CSV not found: {path}")
    out = []
    with path.open(newline="") as f:
        reader = _csv.DictReader(f)
        for row in reader:
            cid = row.get("case_id")
            if cid:
                out.append(cid)
    return out


# ── run_calibrate_anchor (Phase 3 v1.6 §8.0) ───────────────────────────


def run_calibrate_anchor(args) -> int:
    """Entry point for `uofa adversarial calibrate-anchor`.

    Subactions: `ingest` (default) and `regenerate` (Wave B item 15).
    """
    from uofa_cli.adversarial.judge.anchor import ingest_anchor

    action = getattr(args, "anchor_action", "ingest")
    if action == "regenerate":
        error("regenerate mode not yet implemented; use ingest mode (calibration set already committed)")
        return 2

    cal_path: Path = args.in_path
    out_dir: Path | None = getattr(args, "out", None)
    overrides_path: Path | None = getattr(args, "overrides", None)

    if not cal_path.exists():
        error(f"calibration set not found: {cal_path}")
        return 2

    try:
        result = ingest_anchor(
            cal_path, overrides_path=overrides_path, out_dir=out_dir
        )
    except (ValueError, FileNotFoundError) as e:
        error(f"calibration ingest failed: {e}")
        return 3

    info(f"  records: {result.record_count}")
    info(f"  canonical few-shots: {result.canonical_few_shot_count}")
    info(f"  REAL-GAP §6.7 coverage: {result.section_6_7_coverage}")
    if result.override_count:
        info(f"  author overrides applied: {result.override_count}")
    if out_dir:
        result_line("judge_d_anchor", True, str(out_dir / "judge_d_anchor.jsonl"))
    return 0


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
    dry_run: bool = getattr(args, "dry_run", False)
    max_cost: float | None = getattr(args, "max_cost", None)
    resume: bool = getattr(args, "resume", False)
    concurrency: int = int(getattr(args, "concurrency", 1) or 1)
    concurrency_per_judge_raw: str | None = getattr(args, "concurrency_per_judge", None)
    concurrency_per_judge: dict[str, int] | None = None
    if concurrency_per_judge_raw:
        concurrency_per_judge = {}
        for pair in concurrency_per_judge_raw.split(","):
            if "=" not in pair:
                continue
            k, v = pair.split("=", 1)
            try:
                concurrency_per_judge[k.strip()] = int(v.strip())
            except ValueError:
                error(f"--concurrency-per-judge: bad value {pair!r}")
                return 2
    max_requests_raw: str | None = getattr(args, "max_requests_per_judge", None)
    max_requests_per_judge: dict[str, int] | None = None
    if max_requests_raw:
        from uofa_cli.adversarial.judge.request_tracker import (
            parse_per_judge_cap,
        )
        try:
            max_requests_per_judge = parse_per_judge_cap(max_requests_raw)
        except ValueError as e:
            error(str(e))
            return 2

    # TPM caps parsed up-front; auto-derivation deferred until after
    # parse_judges since it needs the resolved token list.
    max_tpm_raw: str | None = getattr(args, "max_tpm_per_judge", None)
    auto_tpm: bool = bool(getattr(args, "auto_tpm", True))
    max_tpm_per_judge: dict[str, int] | None = None
    if max_tpm_raw:
        from uofa_cli.adversarial.judge.token_rate_tracker import (
            parse_per_judge_tpm,
        )
        try:
            max_tpm_per_judge = parse_per_judge_tpm(max_tpm_raw)
        except ValueError as e:
            error(str(e))
            return 2

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

    # TPM auto-derivation: when --max-tpm-per-judge isn't set and
    # --no-auto-tpm isn't passed, pull defaults from each judge's
    # capability-table `default_tpm_cap`. None means uncapped.
    if max_tpm_per_judge is None and auto_tpm:
        from uofa_cli.adversarial.judge.token_rate_tracker import (
            caps_from_capability_table,
        )
        derived = caps_from_capability_table(list(judges.tokens))
        if derived:
            max_tpm_per_judge = derived

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
    # Pin prompt template version into every Judgment this run emits.
    # Calibration validity claims (Stage 1 hard gates) tie to v1.1.0;
    # production output must demonstrably be the same. Default comes
    # from the CLI flag (`--prompt-version`, default v1.1.0).
    prompt_version: str = getattr(args, "prompt_version", "v1.1.0") or "v1.1.0"
    providers = _build_providers(
        judges,
        model_overrides=model_overrides,
        prompt_template_version=prompt_version,
    )

    info(
        f"judging {in_bundle.name} with judges "
        f"{list(zip(judges.positions, judges.tokens))} (parallel={parallel}, "
        f"calibration_only={calibration_only}, dry_run={dry_run})"
    )

    # ── --dry-run: cost-only path, no LLM calls ──
    if dry_run:
        return _run_dry_run_cost_estimate(
            in_bundle=in_bundle,
            tokens=judges.tokens,
            model_overrides=model_overrides,
            calibration_only=calibration_only,
            out_dir=out_dir,
            max_cost=max_cost,
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
        max_cost=max_cost,
        resume=resume,
        concurrency=concurrency,
        concurrency_per_judge=concurrency_per_judge,
        max_requests_per_judge=max_requests_per_judge,
        max_tpm_per_judge=max_tpm_per_judge,
    ))

    # Post-run prompt-version drift check: every emitted Judgment must
    # carry the pinned `prompt_version`. Production output has to be
    # demonstrably tied to the calibration-validated prompt version.
    drift = _check_prompt_version_drift(out_dir, judges.positions, prompt_version)
    if drift:
        for line in drift[:5]:
            error(f"  {line}")
        if len(drift) > 5:
            error(f"  ... and {len(drift) - 5} more drifted records")
        error(
            f"prompt-version drift: {len(drift)} judgment(s) do not match "
            f"--prompt-version={prompt_version!r}. Production output must "
            f"match calibration prompt version."
        )
        return 4

    result_line("judgments", True, str(out_dir))
    return 0


def _check_prompt_version_drift(
    out_dir: Path,
    positions: tuple[str, ...],
    expected: str,
) -> list[str]:
    """Re-read per-judge JSONL after a run; flag any record whose
    prompt_template_version diverges from `expected`.

    Returns a list of "<pos>/<case_id>: got X expected Y" strings
    (empty when clean). Mock providers stamp "v0.0.0-stub" by design;
    those are exempt. Skipped silently when the JSONL doesn't exist
    (e.g. judge halted before any case for that position completed).
    """
    drift: list[str] = []
    for pos in positions:
        path = out_dir / f"judgments_{pos}.jsonl"
        if not path.exists():
            continue
        with path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                got = rec.get("prompt_template_version")
                # Mock stamp ("v0.0.0-stub") is exempt — mocks don't run prompts.
                if got == "v0.0.0-stub":
                    continue
                if got != expected:
                    drift.append(
                        f"{pos}/{rec.get('case_id', '<unknown>')}: "
                        f"got {got!r} expected {expected!r}"
                    )
    return drift


def _run_dry_run_cost_estimate(
    *,
    in_bundle: Path,
    tokens: tuple[str, ...],
    model_overrides: dict[str, str | None],
    calibration_only: bool,
    out_dir: Path,
    max_cost: float | None,
) -> int:
    """Walk the bundle, estimate per-judge cost, print + write a table.

    Exits 0 always (dry-run is informational). Writes
    `cost_estimate.json` to `out_dir` so downstream tooling can consume it.
    """
    from uofa_cli.adversarial.judge.cost_gate import (
        estimate_bundle_cost,
        render_estimate_table,
    )
    from uofa_cli.adversarial.judge.prompts import (
        build_prompt_for_case,
        build_prompt_static_prefix,
    )

    out_dir.mkdir(parents=True, exist_ok=True)

    with open_bundle(in_bundle) as bundle:
        cases = list(bundle.iter_entries())
    if calibration_only:
        cases = cases[:5]

    static_prefix = build_prompt_static_prefix()
    per_case_blocks: list[str] = []
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
        }
        per_case_blocks.append(build_prompt_for_case(case))

    estimates = []
    for token in tokens:
        if token.startswith("mock_"):
            continue
        try:
            est = estimate_bundle_cost(
                provider_token=token,
                model=model_overrides.get(token),
                static_prefix=static_prefix,
                per_case_blocks=per_case_blocks,
            )
            estimates.append(est)
        except KeyError:
            warn(f"unknown provider token in --judges: {token}")

    table = render_estimate_table(estimates)
    info(f"dry-run cost estimate ({len(per_case_blocks)} cases per judge):")
    for line in table.split("\n"):
        info(line)

    total_usd = sum(e.estimated_usd for e in estimates)
    if max_cost is not None and total_usd > max_cost:
        warn(
            f"estimated total ${total_usd:.4f} exceeds --max-cost "
            f"${max_cost:.4f}"
        )

    out_path = out_dir / "cost_estimate.json"
    out_path.write_text(json.dumps({
        "case_count_per_judge": len(per_case_blocks),
        "max_cost_usd": max_cost,
        "estimated_total_usd": total_usd,
        "exceeds_max_cost": (
            max_cost is not None and total_usd > max_cost
        ),
        "per_judge": [
            {
                "provider_token": e.provider_token,
                "model": e.model,
                "case_count": e.case_count,
                "total_input_tokens": e.total_input_tokens,
                "total_output_tokens": e.total_output_tokens,
                "estimated_usd": e.estimated_usd,
            }
            for e in estimates
        ],
    }, indent=2))
    result_line("cost_estimate", True, str(out_path))
    return 0


async def _judge_bundle(
    *,
    in_bundle: Path,
    providers: list[AbstractJudgeProvider],
    positions: tuple[str, ...],
    tokens: tuple[str, ...],
    out_dir: Path,
    calibration_only: bool,
    max_cost: float | None = None,
    resume: bool = False,
    concurrency: int = 1,
    concurrency_per_judge: dict[str, int] | None = None,
    max_requests_per_judge: dict[str, int] | None = None,
    max_tpm_per_judge: dict[str, int] | None = None,
) -> None:
    """For each case in the bundle, run all providers and write per-judge JSONL.

    When `max_cost` is set, a `BudgetTracker` accumulates real spend and
    halts the run gracefully if the next call would push over budget.
    Partial outputs are flushed; `cost_manifest.json` records the halt
    state for downstream tooling.

    When `resume=True`, existing judgments_<pos>.jsonl files are scanned
    for already-judged case_ids; cases done across ALL active judges
    are skipped. JSONL handles open in append mode so the previous
    progress survives.

    `concurrency` is the per-judge max concurrent in-flight calls.
    Defaults to 1 (serial-per-vendor; retains v1.5 behavior). Bump
    higher to parallelize cases across vendors. Pilot v2 (2026-05-05)
    showed Gemini's per-call latency is the bottleneck — recommend
    setting `concurrency=15` (or `concurrency_per_judge={'gemini':20,'openai':10,'hf-llama':10,'anthropic':5}`)
    for production runs to drop wall-clock from ~9h → ~2-3h.

    `concurrency_per_judge` overrides `concurrency` per token when
    set; useful when one vendor has tighter rate limits than the
    others.
    """
    from uofa_cli.adversarial.judge.cost_gate import BudgetTracker
    from uofa_cli.adversarial.judge.request_tracker import RequestTracker
    from uofa_cli.adversarial.judge.resume import (
        compute_remaining_cases,
        load_done_case_ids,
        write_resume_manifest,
    )
    from uofa_cli.adversarial.judge.token_rate_tracker import (
        TokenRateTracker,
    )

    tracker = BudgetTracker(max_cost_usd=max_cost) if max_cost is not None else None
    # Per-judge daily-cap tracker. Loads any prior manifest from out_dir
    # so multi-day runs accumulate across resumes within a UTC day and
    # auto-reset when the day rolls over.
    request_tracker: RequestTracker | None = None
    if max_requests_per_judge:
        request_manifest_path = out_dir / "request_manifest.json"
        out_dir.mkdir(parents=True, exist_ok=True)
        request_tracker = RequestTracker.from_manifest(
            request_manifest_path, per_judge_cap=max_requests_per_judge
        )
    # TPM-aware soft throttle. Always-on when caps are configured; the
    # tracker is a no-op for tokens not in the dict. Unlike RequestTracker
    # this is an in-memory window — no manifest persistence (TPM windows
    # roll forward within seconds, not days).
    tpm_tracker: TokenRateTracker | None = None
    if max_tpm_per_judge:
        tpm_tracker = TokenRateTracker(per_judge_tpm=max_tpm_per_judge)

    _reset_mock_ledger()
    with open_bundle(in_bundle) as bundle:
        cases = list(bundle.iter_entries())

    if calibration_only:
        # Tier A: in absence of a real calibration set, judge first 5 cases
        # as a stand-in. Real Stage 1 reads specs/calibration/calibration_set_v1.jsonl.
        cases = cases[:5]

    total_count = len(cases)
    # Resume gate: drop already-done cases.
    if resume:
        done_per_judge: dict[str, set[str]] = {
            pos: load_done_case_ids(out_dir / f"judgments_{pos}.jsonl")
            for pos in positions
        }
        case_ids = [c.case_id for c in cases]
        remaining_ids = set(compute_remaining_cases(case_ids, done_per_judge))
        cases = [c for c in cases if c.case_id in remaining_ids]
        info(
            f"resume: {len(cases)}/{total_count} cases remaining "
            f"(skipped {total_count - len(cases)})"
        )

    # Collect verdicts in memory so the calibration summary doesn't have
    # to re-read partially-written JSONL files (the handles below are
    # buffered; reading them mid-loop returns nothing).
    verdicts_by_pos: dict[str, list[str]] = {pos: [] for pos in positions}

    # Resume mode opens in append; fresh runs truncate.
    open_mode = "a" if resume else "w"
    handles = {pos: (out_dir / f"judgments_{pos}.jsonl").open(open_mode) for pos in positions}
    halted_early = False

    # Build per-token semaphores. concurrency_per_judge overrides the
    # global concurrency value when present.
    per_token_caps = {token: concurrency for token in set(tokens)}
    if concurrency_per_judge:
        per_token_caps.update(concurrency_per_judge)
    semaphores = {
        token: asyncio.Semaphore(max(1, n))
        for token, n in per_token_caps.items()
    }

    def _build_case(entry) -> dict:
        return {
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

    async def _judge_one(entry, pos: str, token: str, provider) -> tuple[str, str, "Judgment | None"]:
        """Bound by the per-token semaphore. Returns (pos, case_id, judgment)
        or (pos, case_id, None) on error / cap-hit. Errors are NOT raised
        so one bad case doesn't kill the gather."""
        async with semaphores[token]:
            if tracker is not None and tracker.over_budget:
                return pos, entry.case_id, None
            # Per-judge daily-cap gate: skip the call if quota is hit.
            if request_tracker is not None and not request_tracker.authorize(token):
                return pos, entry.case_id, None
            # TPM throttle: estimate this call's tokens and sleep until
            # the 1-minute window has room. No-op when no cap configured.
            if tpm_tracker is not None:
                projected = _estimate_call_tokens(provider, entry, token)
                await tpm_tracker.sleep_until_authorized(token, projected)
            try:
                j = await provider.judge(_build_case(entry))
                if request_tracker is not None:
                    request_tracker.record(token)
                if tpm_tracker is not None:
                    tpm_tracker.record(token, _judgment_tokens(j))
                if tracker is not None:
                    tracker.record(token, _extract_response_cost(j, token))
                    if not tracker.authorize(token, 0.0):
                        # Budget tripped; let the rest of the gather
                        # complete with their own checks.
                        pass
                return pos, entry.case_id, j
            except Exception as exc:
                # Record the call even on failure — the vendor counted it.
                if request_tracker is not None:
                    request_tracker.record(token)
                logger.warning("judge %s failed on %s: %s", token, entry.case_id, exc)
                return pos, entry.case_id, None

    try:
        if concurrency <= 1 and not concurrency_per_judge:
            # Legacy serial-per-case loop. Identical to v1.5 behavior so
            # the calibration-only smoke + budget-tripping tests retain
            # their existing assertions.
            for entry in cases:
                case = _build_case(entry)
                for pos, token, provider in zip(positions, tokens, providers):
                    if tracker is not None and tracker.over_budget:
                        halted_early = True
                        break
                    if request_tracker is not None and not request_tracker.authorize(token):
                        halted_early = True
                        break
                    if tpm_tracker is not None:
                        projected = _estimate_call_tokens(provider, entry, token)
                        await tpm_tracker.sleep_until_authorized(token, projected)
                    judgment = await provider.judge(case)
                    handles[pos].write(json.dumps(_judgment_to_dict(judgment)) + "\n")
                    verdicts_by_pos[pos].append(judgment.verdict)
                    if request_tracker is not None:
                        request_tracker.record(token)
                    if tpm_tracker is not None:
                        tpm_tracker.record(token, _judgment_tokens(judgment))
                    if tracker is not None:
                        tracker.record(token, _extract_response_cost(judgment, token))
                        if not tracker.authorize(token, 0.0):
                            halted_early = True
                            break
                if halted_early:
                    break
        else:
            # Concurrent path: gather all (case × judge) tasks, bound
            # per-vendor by semaphores. Output ordering matches input
            # bundle ordering (asyncio.gather preserves the task list
            # order in its results).
            tasks = []
            for entry in cases:
                for pos, token, provider in zip(positions, tokens, providers):
                    tasks.append(_judge_one(entry, pos, token, provider))
            results = await asyncio.gather(*tasks)
            for pos, _case_id, judgment in results:
                if judgment is None:
                    continue
                handles[pos].write(json.dumps(_judgment_to_dict(judgment)) + "\n")
                verdicts_by_pos[pos].append(judgment.verdict)
            if tracker is not None and tracker.over_budget:
                halted_early = True
    finally:
        for h in handles.values():
            h.close()
        if tracker is not None:
            tracker.write_manifest(out_dir / "cost_manifest.json")
            if halted_early and tracker.over_budget:
                warn(
                    f"halted: total spend ${tracker.running_total_usd:.4f} "
                    f"≥ --max-cost ${tracker.max_cost_usd:.4f}"
                )
        if request_tracker is not None:
            request_tracker.write_manifest(out_dir / "request_manifest.json")
            if request_tracker.over_cap:
                warn(
                    f"halted: {request_tracker.halt_reason}. "
                    f"Re-run tomorrow with --resume to continue against "
                    f"the next UTC day's quota."
                )
        if resume:
            write_resume_manifest(
                out_dir=out_dir,
                bundle_path=in_bundle,
                total_case_count=total_count,
                skipped_case_count=total_count - len(cases),
                judged_case_count=len(cases),
            )

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


def _estimate_call_tokens(provider: AbstractJudgeProvider, entry, token: str) -> int:
    """Estimate input + output tokens for a single judge call.

    Used by TokenRateTracker before-call gate. Conservative: counts
    the case_id + package + outcome metadata as input proxy and
    assumes 800 output tokens (slightly above pilot v2's mean to
    absorb retries). Real token counting via litellm.token_counter
    needs the assembled prompt which is built later in the call
    chain; this estimate is good enough for TPM windowing.
    """
    try:
        from uofa_cli.adversarial.judge.cost_gate import count_tokens

        # Use the assembled case content as input proxy. Static prefix
        # tokens are double-counted across calls (each call sends
        # the prefix + case content), so include it.
        from uofa_cli.adversarial.judge.prompts import build_prompt_static_prefix
        prefix = build_prompt_static_prefix()
        case_text = json.dumps({
            "case_id": entry.case_id,
            "package": entry.package,
            "outcome": dict(entry.outcome),
        })
        in_tokens = count_tokens(token, getattr(provider, "_model_id", None), prefix + case_text)
        # Pilot v2 saw output token mean ~700 across vendors; pad to 1000
        # so brief throttle sleeps don't undershoot.
        return in_tokens + 1000
    except Exception:
        # Conservative fallback: assume an average pilot-v2 case.
        return 12_000


def _judgment_tokens(judgment: Judgment) -> int:
    """Extract actual input+output tokens from a Judgment's raw response."""
    raw = judgment.raw_response or {}
    if not isinstance(raw, dict):
        return 0
    usage = raw.get("usage") or {}
    in_tok = int(usage.get("prompt_tokens", 0) or 0)
    out_tok = int(usage.get("completion_tokens", 0) or 0)
    return in_tok + out_tok


def _extract_response_cost(judgment: Judgment, provider_token: str) -> float:
    """Pull actual USD cost off the provider response when available.

    Litellm normalizes usage onto `response.usage.{prompt,completion}_tokens`
    and emits `response._hidden_params.response_cost` for some providers.
    Fall back to estimation by token count + model price.
    """
    raw = judgment.raw_response or {}
    # Litellm hidden params path.
    hidden = raw.get("_hidden_params") if isinstance(raw, dict) else None
    if hidden and "response_cost" in hidden:
        try:
            return float(hidden["response_cost"])
        except (ValueError, TypeError):
            pass

    # Fallback: estimate from usage tokens + capability table model.
    usage = raw.get("usage") if isinstance(raw, dict) else None
    if not usage:
        return 0.0
    from uofa_cli.adversarial.judge.cost_gate import estimate_call_cost
    in_tok = int(usage.get("prompt_tokens", 0) or 0)
    out_tok = int(usage.get("completion_tokens", 0) or 0)
    try:
        return estimate_call_cost(
            provider_token, judgment.judge_model,
            input_tokens=in_tok, output_tokens=out_tok,
        )
    except Exception:
        return 0.0


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
    """Entry point for `uofa adversarial adjudicate` (v1.6).

    Reads judgments_A/B/C as before, plus optionally:
      - judgments_E.jsonl (Judge E arbitration output) → EA/EB/EC
        confusion matrices and Judge E vs production-judge κ on the
        disagreement queue.
      - author_adjudications.jsonl (author final verdicts on the
        escalation queue) → author_E confusion matrix.
      - spot_check_overrides.jsonl (author overrides on CONVERGENT
        cases) → spot-check override rate (target ≤ 0.10 per §11.4).
      - judgments_D.jsonl (Judge D calibration anchor) → Judge E vs
        Judge D agreement on the calibration set (informational).
    """
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

    summary: dict[str, Any] = {
        "case_count": stats.case_count,
        "cohen_kappa_AB": stats.cohen_kappa_AB,
        "cohen_kappa_AC": stats.cohen_kappa_AC,
        "cohen_kappa_BC": stats.cohen_kappa_BC,
        "fleiss_kappa": stats.fleiss_kappa,
        "raw_agreement_at_least_2of3": stats.raw_agreement_at_least_2of3,
    }

    # Confusion matrices per pair (spec §12.2 layout).
    _write_confusion(out_dir / "confusion_matrix_AB.csv", verdicts_a, verdicts_b)
    _write_confusion(out_dir / "confusion_matrix_AC.csv", verdicts_a, verdicts_c)
    _write_confusion(out_dir / "confusion_matrix_BC.csv", verdicts_b, verdicts_c)

    info(
        f"  agreement: AB κ={stats.cohen_kappa_AB:.3f}, "
        f"AC κ={stats.cohen_kappa_AC:.3f}, BC κ={stats.cohen_kappa_BC:.3f}, "
        f"Fleiss κ={stats.fleiss_kappa:.3f}"
    )

    # ── v1.6 Judge E branch ─────────────────────────────────────────────
    judgments_e_path: Path | None = getattr(args, "judgments_e", None)
    if judgments_e_path is not None and judgments_e_path.exists():
        # Build per-case index across all four judges so we can join the
        # disagreement queue subset.
        idx_a = {j.case_id: j for j in judgments_a}
        idx_b = {j.case_id: j for j in judgments_b}
        idx_c = {j.case_id: j for j in judgments_c}
        idx_e = {j.case_id: j for j in _load_judgments(judgments_e_path)}

        # The disagreement queue is exactly the set of cases Judge E judged.
        # Inner-joined with A/B/C (a missing production judgment is a bug
        # in the upstream pipeline; surface it loudly).
        common = sorted(set(idx_e) & set(idx_a) & set(idx_b) & set(idx_c))
        if not common:
            warn("judgments_E.jsonl present but no overlap with A/B/C; skipping")
        else:
            verdicts_e_q = [idx_e[k].verdict for k in common]
            verdicts_a_q = [idx_a[k].verdict for k in common]
            verdicts_b_q = [idx_b[k].verdict for k in common]
            verdicts_c_q = [idx_c[k].verdict for k in common]

            confidence_floor = float(getattr(args, "confidence_floor", 0.6))
            arbitrated = sum(
                1 for k in common if idx_e[k].confidence >= confidence_floor
            )
            escalated = len(common) - arbitrated

            e_stats = compute_judge_e_agreement(
                judgments_a=verdicts_a_q,
                judgments_b=verdicts_b_q,
                judgments_c=verdicts_c_q,
                judgments_e=verdicts_e_q,
                arbitrated_count=arbitrated,
                escalated_count=escalated,
            )

            _write_confusion(
                out_dir / "confusion_matrix_EA.csv", verdicts_e_q, verdicts_a_q
            )
            _write_confusion(
                out_dir / "confusion_matrix_EB.csv", verdicts_e_q, verdicts_b_q
            )
            _write_confusion(
                out_dir / "confusion_matrix_EC.csv", verdicts_e_q, verdicts_c_q
            )

            summary["judge_e"] = {
                "case_count": e_stats.case_count,
                "cohen_kappa_EA": e_stats.cohen_kappa_EA,
                "cohen_kappa_EB": e_stats.cohen_kappa_EB,
                "cohen_kappa_EC": e_stats.cohen_kappa_EC,
                "arbitrated_count": e_stats.arbitrated_count,
                "escalated_count": e_stats.escalated_count,
                "confidence_floor": confidence_floor,
            }
            info(
                f"  judge E: EA κ={e_stats.cohen_kappa_EA:.3f}, "
                f"EB κ={e_stats.cohen_kappa_EB:.3f}, EC κ={e_stats.cohen_kappa_EC:.3f}, "
                f"ARBITRATED={arbitrated} ESCALATED={escalated}"
            )

            # ── author_E confusion + spot-check override rate ──
            author_path: Path | None = getattr(args, "author_adjudications", None)
            spot_check_path: Path | None = getattr(args, "spot_check_overrides", None)
            if author_path is not None and author_path.exists():
                author_records = _load_simple_jsonl(author_path)
                # Match by case_id; only escalated cases (where author actually
                # rendered a verdict against Judge E) count for author_E.
                author_idx = {r["case_id"]: r for r in author_records}
                escalated_ids = [
                    k for k in common if idx_e[k].confidence < confidence_floor
                ]
                joined = [k for k in escalated_ids if k in author_idx]
                author_verdicts = [author_idx[k]["final_verdict"] for k in joined]
                judge_e_on_escalated = [idx_e[k].verdict for k in joined]

                spot_check_total = 0
                spot_check_override = 0
                if spot_check_path is not None and spot_check_path.exists():
                    spot_check_records = _load_simple_jsonl(spot_check_path)
                    spot_check_total = len(spot_check_records)
                    spot_check_override = sum(
                        1
                        for r in spot_check_records
                        if r.get("override_verdict")
                        and r["override_verdict"] != r.get("original_verdict")
                    )

                author_stats = compute_author_adjudication(
                    author_verdicts=author_verdicts,
                    judge_e_verdicts=judge_e_on_escalated,
                    spot_check_total=spot_check_total,
                    spot_check_override_count=spot_check_override,
                )

                if author_verdicts:
                    _write_confusion(
                        out_dir / "confusion_matrix_author_E.csv",
                        author_verdicts,
                        judge_e_on_escalated,
                    )

                summary["author_adjudication"] = {
                    "escalated_case_count": author_stats.escalated_case_count,
                    "spot_check_total": author_stats.spot_check_total,
                    "spot_check_override_count": author_stats.spot_check_override_count,
                    "spot_check_override_rate": author_stats.spot_check_override_rate,
                }
                info(
                    f"  author: escalated={author_stats.escalated_case_count}, "
                    f"spot-check override rate="
                    f"{author_stats.spot_check_override_rate:.3f}"
                )

        # ── Judge E vs Judge D agreement on calibration set ──
        judgments_d_path: Path | None = getattr(args, "judgments_d", None)
        if judgments_d_path is not None and judgments_d_path.exists():
            idx_d = {j.case_id: j for j in _load_judgments(judgments_d_path)}
            common_de = sorted(set(idx_d) & set(idx_e))
            if common_de:
                de_stats = compute_judge_e_vs_d_agreement(
                    judge_e_verdicts=[idx_e[k].verdict for k in common_de],
                    judge_d_verdicts=[idx_d[k].verdict for k in common_de],
                )
                summary["judge_e_vs_d_calibration"] = {
                    "case_count": de_stats.case_count,
                    "overall_match_rate": de_stats.overall_match_rate,
                    "per_class_match_rate": de_stats.per_class_match_rate,
                }
                info(
                    f"  E↔D calibration: overall match rate="
                    f"{de_stats.overall_match_rate:.3f}"
                )

    stats_path = out_dir / "agreement_stats.json"
    stats_path.write_text(json.dumps(summary, indent=2, default=_jsonable))
    result_line("agreement_stats", True, str(stats_path))
    return 0


# ── run_finalize (Phase 3 v1.6 §10.3, Delta 5) ─────────────────────────


def run_finalize(args) -> int:
    """Entry point for `uofa adversarial finalize`.

    Assembles `final_verdicts.jsonl` across the four-layer source
    priority: AUTHOR_OVERRIDE > AUTHOR_FINAL > ARBITRATED > CONVERGENT
    (per spec v1.6 §10.3). For OOS verdicts the evidence_gap carries
    through with explicit source attribution per Delta 5.
    """
    from uofa_cli.adversarial.judge.final_verdict import (
        assemble_final_verdicts,
        load_arbitration_records,
        load_author_records,
        load_spot_check_overrides,
        write_final_verdicts,
    )
    from uofa_cli.adversarial.judge.triage import triage_corpus

    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    judgments_a = _load_judgments(args.judgments_a)
    judgments_b = _load_judgments(args.judgments_b)
    judgments_c = _load_judgments(args.judgments_c)
    trios = align_trios(judgments_a, judgments_b, judgments_c)
    if not trios:
        error("no aligned trios; cannot assemble final verdicts")
        return 1

    confidence_floor = float(getattr(args, "confidence_floor", 0.6))
    triage_result = triage_corpus(trios, confidence_floor=confidence_floor)

    arbitration_path: Path | None = getattr(args, "judgments_e", None)
    author_path: Path | None = getattr(args, "author_adjudications", None)
    spot_check_path: Path | None = getattr(args, "spot_check_overrides", None)

    arbitration_records = (
        load_arbitration_records(arbitration_path)
        if arbitration_path else {}
    )
    author_records = (
        load_author_records(author_path) if author_path else {}
    )
    spot_check_overrides = (
        load_spot_check_overrides(spot_check_path) if spot_check_path else {}
    )

    final = assemble_final_verdicts(
        triage_entries=triage_result.entries,
        arbitration_records=arbitration_records,
        author_records=author_records,
        spot_check_overrides=spot_check_overrides,
        confidence_floor=confidence_floor,
    )

    out_path = out_dir / "final_verdicts.jsonl"
    write_final_verdicts(final, out_path)

    # Summary metrics by provenance + OOS evidence-gap counts.
    by_prov: dict[str, int] = {}
    oos_with_gap = 0
    oos_without_gap = 0
    for fv in final:
        by_prov[fv.provenance] = by_prov.get(fv.provenance, 0) + 1
        if fv.final_verdict == "OUT-OF-SCOPE":
            if fv.evidence_gap is not None:
                oos_with_gap += 1
            else:
                oos_without_gap += 1

    summary = {
        "case_count": len(final),
        "by_provenance": by_prov,
        "out_of_scope_with_evidence_gap": oos_with_gap,
        "out_of_scope_without_evidence_gap": oos_without_gap,
    }
    (out_dir / "final_verdicts_summary.json").write_text(
        json.dumps(summary, indent=2)
    )

    info(f"  finalize: {by_prov}, OOS with evidence_gap={oos_with_gap}")
    if oos_without_gap > 0:
        warn(
            f"{oos_without_gap} OUT-OF-SCOPE verdicts missing evidence_gap "
            f"(productive-OOS Delta 5 violation)"
        )
    result_line("final_verdicts", True, str(out_path))
    return 0


# ── run_calibrate (Phase 3 v1.6 §8.0–8.4, Stage 1 Block 3) ──


def run_calibrate(args) -> int:
    """Entry point for `uofa adversarial calibrate`.

    Stage 1 production-judge calibration: runs Judges A/B/C (and
    optionally E for sanity check) over the 30-case calibration set,
    computes per-judge accuracy + pairwise κ + per-class accuracy,
    and emits a markdown summary with hard-gate verdicts (spec §15.1
    #5/6/7). Pins prompt_template_version to v1.1.0 by default;
    override via --prompt-version for the §8.3 3-iteration path.
    """
    from uofa_cli.adversarial.judge.calibration import (
        DEFAULT_CALIBRATION_PATH,
        run_calibration,
    )

    raw_judges: str = args.judges
    out_dir: Path = args.out
    prompt_version: str = getattr(args, "prompt_version", "v1.1.0") or "v1.1.0"
    concurrency: int = int(getattr(args, "concurrency", 5) or 5)
    cal_path: Path = getattr(args, "calibration_set", DEFAULT_CALIBRATION_PATH) \
        or DEFAULT_CALIBRATION_PATH
    overrides_path: Path | None = getattr(args, "overrides", None)
    judge_e_sanity = not bool(getattr(args, "no_judge_e_sanity_check", False))

    from uofa_cli.adversarial.judge.cli_args import parse_calibrate_judges
    try:
        judges = parse_calibrate_judges(raw_judges)
    except ValueError as e:
        error(f"--judges: {e}")
        return 2

    judge_specs = list(zip(judges.positions, judges.tokens))

    # Versioned out-dir per the addendum: results land in
    # `<out_dir>/<prompt_version>/` so multiple iterations preserve their
    # gate values for audit.
    versioned_out = out_dir / prompt_version
    versioned_out.mkdir(parents=True, exist_ok=True)

    info(
        f"Stage 1 calibration: {len(judge_specs)} judges, "
        f"prompt {prompt_version}, concurrency {concurrency}"
    )

    try:
        run = run_calibration(
            judge_specs=judge_specs,
            out_dir=versioned_out,
            calibration_path=cal_path,
            overrides_path=overrides_path,
            prompt_version=prompt_version,
            concurrency=concurrency,
            judge_e_sanity_check=judge_e_sanity,
        )
    except (RuntimeError, FileNotFoundError, ValueError) as e:
        error(f"calibration failed: {e}")
        return 3

    info(
        f"hard gates: per-judge {run.gate_per_judge_accuracy}, "
        f"pairwise κ {run.gate_pairwise_kappa}, all_pass={run.all_gates_pass}"
    )
    result_line(
        "calibration_results", True,
        str(versioned_out / "calibration_run_v1_results.json"),
    )
    result_line(
        "calibration_summary", True,
        str(versioned_out / "calibration_run_v1_summary.md"),
    )
    return 0 if run.all_gates_pass else 1


# ── run_case_study_rerun (Phase 3 v1.6 §13.3, Wave K) ──


def run_case_study_rerun(args) -> int:
    """Entry point for `uofa adversarial case-study-rerun`.

    Runs the rule engine against `--catalog` × `--cou` matrix and emits
    `delta_table.md` + `delta_table.json` per spec §13.3.
    """
    from uofa_cli.adversarial.judge.case_study import (
        compute_delta_rows,
        run_case_study,
        write_delta_artifacts,
    )

    catalogs: list[str] = args.catalog
    cous: list[str] = args.cou
    out_dir: Path = args.out
    if len(catalogs) != 2:
        error("--catalog must take exactly two version strings (A B)")
        return 2

    info(f"running case-study: catalogs {catalogs} × COUs {cous}")
    runs = run_case_study(catalogs=catalogs, cous=cous)
    rows = compute_delta_rows(runs, catalog_a=catalogs[0], catalog_b=catalogs[1])
    paths = write_delta_artifacts(
        rows, out_dir, catalog_a=catalogs[0], catalog_b=catalogs[1]
    )
    info(f"  delta_table: {paths['markdown']}")
    result_line("delta_table", True, str(paths["markdown"]))
    return 0


# ── run_formalize (Phase 3 v1.6 §13.1, Wave J — forward-chaining only) ──


def run_formalize(args) -> int:
    """Entry point for `uofa adversarial formalize`.

    Reads `final_verdicts.jsonl` + (optionally) per-judge `judgments_*.jsonl`
    to attach §6.7 candidates, then emits Jena rule + test scaffolds for
    each REAL-GAP case. Forward-chaining only — backward-chaining OOS
    rules are out of Tier A scope (substrate validation test, May 11–24).
    """
    from uofa_cli.adversarial.judge.formalize import run_formalize_from_files

    final_verdicts_path: Path = args.final_verdicts
    out_dir: Path = args.out
    judgments_paths = {
        "A": getattr(args, "judgments_a", None),
        "B": getattr(args, "judgments_b", None),
        "C": getattr(args, "judgments_c", None),
    }
    judgments_paths = {k: v for k, v in judgments_paths.items() if v is not None}

    if not final_verdicts_path.exists():
        error(f"final_verdicts.jsonl not found: {final_verdicts_path}")
        return 2

    severity_overrides_path: Path | None = getattr(args, "severity_overrides", None)
    severity_overrides: dict[str, str] = {}
    if severity_overrides_path is not None and severity_overrides_path.exists():
        # JSON file: {"W-EV-01": "Critical", ...}
        severity_overrides = json.loads(severity_overrides_path.read_text())

    out_dir.mkdir(parents=True, exist_ok=True)
    result = run_formalize_from_files(
        final_verdicts_path=final_verdicts_path,
        judgments_paths=judgments_paths,
        out_dir=out_dir,
        severity_overrides=severity_overrides,
    )
    info(f"formalize: {len(result.candidates)} rule scaffolds generated")
    if result.skipped_case_count:
        info(f"  skipped: {result.skipped_case_count} ({result.skipped_reasons})")
    result_line(
        "formalization_summary",
        True,
        str(out_dir / "formalization_summary.json"),
    )
    return 0


def _load_simple_jsonl(path: Path) -> list[dict]:
    """Load a JSONL file as a list of dicts (no Judgment-class coercion)."""
    out: list[dict] = []
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        out.append(json.loads(line))
    return out


def _jsonable(o: Any) -> Any:
    """JSON encoder hook for NaN floats (spec §12.2 substitutes null)."""
    if isinstance(o, float) and o != o:  # NaN
        return None
    raise TypeError(f"non-serializable: {type(o).__name__}")


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
            evidence_gap=data.get("evidence_gap"),
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
