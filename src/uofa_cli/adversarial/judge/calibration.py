"""Stage 1 production-judge calibration (spec v1.6 §8.1–8.4, §15.1 #5/6/7).

Reads `specs/calibration/calibration_set_v1.jsonl` (the Judge D anchor),
runs Judges A/B/C against it, computes:

  - per-judge accuracy = correct / 30 (gate: ≥ 80%, spec §15.1 #5)
  - pairwise Cohen's κ for A/B, A/C, B/C (gate: ≥ 0.70, spec §15.1 #6)
  - per-class accuracy table — 6 classes × 3 judges (gate: ≥ 50% per
    cell, spec §15.1 #7 "soft within hard")
  - optionally Judge E sanity check vs Judge D (informational only,
    not a gate; spec §8.4)

The runner pins prompt_template_version to v1.1.0 explicitly so gate
values don't drift if the module-level default changes (e.g. when
v1.2.0 ships during the §8.3 3-iteration prompt-tuning path). Each
emitted Judgment record carries the pinned version; post-run
validation refuses to write the markdown summary if any record
diverges (defensive guard against silent drift).

Outputs (in `out_dir`):
  - judge_{a,b,c,e}_calibration.jsonl  raw per-judge Judgment records
  - calibration_run_v1_results.json     aggregated metrics + provenance
  - calibration_run_v1_summary.md        markdown summary with hard-gate table

The calibration set's case_id ranges (verified 2026-05-05):
  - cal-001..005: CORRECT-DETECTION
  - cal-006..010: REAL-GAP
  - cal-011..015: GENERATOR-ARTIFACT
  - cal-016..020: EXISTING-RULE-MISBEHAVIOR
  - cal-021..025: OUT-OF-SCOPE  (note: handoff doc references cal-026..030
                                 but our committed set uses cal-021..025;
                                 OOS / UNCERTAIN swap is doc drift, not a
                                 real issue. Validated by validate_v2.)
  - cal-026..030: UNCERTAIN
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from uofa_cli.adversarial.judge.adjudication import (
    VERDICT_CLASSES,
    cohen_kappa,
    fleiss_kappa,
)
from uofa_cli.adversarial.judge.anchor import ingest_anchor
from uofa_cli.adversarial.judge.providers.base import AbstractJudgeProvider, Judgment

logger = logging.getLogger(__name__)


DEFAULT_PROMPT_VERSION = "v1.1.0"
DEFAULT_CALIBRATION_PATH = Path("specs/calibration/calibration_set_v1.jsonl")

# Hard-gate thresholds per spec §15.1.
GATE_PER_JUDGE_ACCURACY = 0.80
GATE_PAIRWISE_KAPPA = 0.70
GATE_PER_CLASS_ACCURACY = 0.50


@dataclass
class JudgeCalibrationResult:
    """One judge's calibration output.

    `verdicts_by_index` is the verdict at each calibration-case index,
    aligned with the calibration set's order. `None` entries mark
    cases where the judge errored — preserving the index lets pairwise
    κ alignment work even when a model echoes a non-canonical case_id
    in its response (which would break case_id-keyed alignment).
    """

    position: str  # "A", "B", "C", "E"
    provider_token: str
    judge_model: str
    case_count: int
    correct_count: int
    overall_accuracy: float
    per_class_correct: dict[str, int]
    per_class_total: dict[str, int]
    per_class_accuracy: dict[str, float]
    judgments: list[Judgment]  # filtered to non-None for serialization
    verdicts_by_index: list[str | None]  # aligned with calibration order


@dataclass
class CalibrationRunResults:
    """Aggregated Stage 1 metrics + hard-gate verdicts."""

    run_timestamp_utc: str
    prompt_template_version: str
    calibration_set_path: str
    case_count: int
    judge_results: dict[str, JudgeCalibrationResult]  # by position
    pairwise_kappa: dict[str, float]  # 'AB', 'AC', 'BC'
    fleiss_kappa: float
    judge_e_vs_d_match_rate: float | None
    gate_per_judge_accuracy: dict[str, bool]
    gate_pairwise_kappa: dict[str, bool]
    gate_per_class_accuracy: dict[str, dict[str, bool]]  # position → {class: pass}
    all_gates_pass: bool


# ── runner ─────────────────────────────────────────────────────────────


def _load_calibration_records(
    out_dir: Path,
    *,
    calibration_path: Path = DEFAULT_CALIBRATION_PATH,
    overrides_path: Path | None = None,
) -> list[dict]:
    """Validate + ingest the calibration set, then read it back.

    `ingest_anchor` writes a normalized copy to `<out_dir>/judge_d_anchor.jsonl`;
    we read from there so any author overrides take effect.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    ingest_anchor(
        calibration_path,
        overrides_path=overrides_path,
        out_dir=out_dir,
    )
    anchor_path = out_dir / "judge_d_anchor.jsonl"
    return [
        json.loads(line)
        for line in anchor_path.read_text().splitlines()
        if line.strip()
    ]


def _build_case_for_judge(record: dict) -> dict:
    """Build the case dict that LiteLLMProvider.judge() expects.

    The calibration record is a §22-shape ground-truth row; we project
    it into the case-dict shape the production prompt builder consumes.
    Missing the actual package content is OK for calibration since the
    prompt only needs the case_id + section_6_7 + outcome class to
    operate; the package text is loaded by `build_prompt_for_case`
    from `case["package"]` if present, else falls back to a placeholder
    summary built from the other fields.
    """
    package = record.get("package")
    if not isinstance(package, dict):
        # Lazy-load the package content if a path is given.
        pkg_path = record.get("package_path")
        if pkg_path:
            p = Path(pkg_path)
            if p.exists():
                package = json.loads(p.read_text())
            else:
                package = {"id": record["case_id"], "name": "(package missing)"}
        else:
            package = {"id": record["case_id"], "name": "(package missing)"}

    return {
        "case_id": record["case_id"],
        "phase2_case_id": record.get("phase2_case_id"),
        "source_taxonomy": record.get("source_taxonomy"),
        "rules_fired": record.get("rules_fired", []),
        "expected_rule": record.get("expected_target_rule"),
        "section_6_7_mapping": record.get("section_6_7_mapping"),
        "phase2_outcome_class_raw": record.get("phase2_outcome_class")
        or record.get("phase2_outcome_class_normalized"),
        "package": package,
    }


async def _run_one_judge(
    *,
    position: str,
    provider: AbstractJudgeProvider,
    cases: list[dict],
    ground_truth: list[str],
    concurrency: int = 5,
) -> JudgeCalibrationResult:
    """Run one judge over all cases at the given concurrency, score against ground truth."""
    sem = asyncio.Semaphore(max(1, concurrency))

    async def _one(idx: int) -> tuple[int, Judgment | None]:
        async with sem:
            try:
                j = await provider.judge(cases[idx])
                return idx, j
            except Exception as exc:
                logger.warning(
                    "calibration: judge %s failed on case %s: %s",
                    position, cases[idx]["case_id"], exc,
                )
                return idx, None

    results = await asyncio.gather(*(_one(i) for i in range(len(cases))))
    # Maintain index order so judgment[i] aligns with ground_truth[i].
    judgments: list[Judgment | None] = [None] * len(cases)
    for idx, j in results:
        judgments[idx] = j

    # Score.
    per_class_correct: dict[str, int] = {cls: 0 for cls in VERDICT_CLASSES}
    per_class_total: dict[str, int] = {cls: 0 for cls in VERDICT_CLASSES}
    correct = 0
    for j, gt in zip(judgments, ground_truth):
        if gt in per_class_total:
            per_class_total[gt] += 1
        if j is None:
            continue
        if j.verdict == gt:
            correct += 1
            per_class_correct[gt] = per_class_correct.get(gt, 0) + 1

    per_class_accuracy = {
        cls: (per_class_correct[cls] / per_class_total[cls])
        if per_class_total[cls] > 0 else 0.0
        for cls in VERDICT_CLASSES
    }

    # Drop the Nones from the judgment list — they're errors and
    # downstream κ calculation needs aligned non-null verdicts. The
    # caller compares lengths.
    return JudgeCalibrationResult(
        position=position,
        provider_token=getattr(provider, "_provider_token", "unknown"),
        judge_model=provider.model,
        case_count=len(cases),
        correct_count=correct,
        overall_accuracy=correct / len(cases) if cases else 0.0,
        per_class_correct=per_class_correct,
        per_class_total=per_class_total,
        per_class_accuracy=per_class_accuracy,
        judgments=[j for j in judgments if j is not None],
        verdicts_by_index=[j.verdict if j is not None else None for j in judgments],
    )


def _gate_pairwise_kappa(
    results_by_pos: dict[str, JudgeCalibrationResult],
) -> tuple[dict[str, float], float]:
    """Compute pairwise κ for A/B, A/C, B/C and Fleiss across all three.

    Aligns judgments by INDEX (calibration-case order), not by case_id.
    Each Judgment record's case_id may be the model's echo of either
    the calibration `cal-NNN-...` id or the underlying `phase2_case_id`,
    depending on schema-strict-mode semantics — these don't align
    across vendors. The index alignment is the source of truth: each
    judge's verdicts_by_index[i] is its verdict on the i-th calibration
    case. Indices where ANY judge errored (None) are dropped from κ.
    """
    a_v = results_by_pos["A"].verdicts_by_index
    b_v = results_by_pos["B"].verdicts_by_index
    c_v = results_by_pos["C"].verdicts_by_index

    # Drop indices where any judge errored.
    aligned = [
        (a, b, c) for a, b, c in zip(a_v, b_v, c_v)
        if a is not None and b is not None and c is not None
    ]
    if not aligned:
        return {"AB": float("nan"), "AC": float("nan"), "BC": float("nan")}, float("nan")
    va, vb, vc = (
        [t[0] for t in aligned],
        [t[1] for t in aligned],
        [t[2] for t in aligned],
    )
    return (
        {
            "AB": cohen_kappa(va, vb),
            "AC": cohen_kappa(va, vc),
            "BC": cohen_kappa(vb, vc),
        },
        fleiss_kappa([list(t) for t in zip(va, vb, vc)]),
    )


def _judge_e_vs_d_agreement(
    judge_e: JudgeCalibrationResult, ground_truth: list[str],
) -> float:
    """Match rate of Judge E vs Judge D ground-truth on the calibration set.

    Aligns by INDEX (calibration order); see `_gate_pairwise_kappa` for
    why we don't use case_id keying.
    """
    valid = [
        v for v in judge_e.verdicts_by_index if v is not None
    ]
    if not valid:
        return float("nan")
    # Iterate paired by index, skipping E errors.
    matched = 0
    counted = 0
    for v, gt in zip(judge_e.verdicts_by_index, ground_truth):
        if v is None:
            continue
        counted += 1
        if v == gt:
            matched += 1
    return matched / counted if counted else float("nan")


def _evaluate_hard_gates(
    judge_results: dict[str, JudgeCalibrationResult],
    pairwise_kappa: dict[str, float],
) -> tuple[dict[str, bool], dict[str, bool], dict[str, dict[str, bool]], bool]:
    """Apply spec §15.1 #5/6/7 thresholds; return per-gate verdicts."""
    per_judge: dict[str, bool] = {
        pos: judge_results[pos].overall_accuracy >= GATE_PER_JUDGE_ACCURACY
        for pos in ("A", "B", "C")
    }
    pair_pass: dict[str, bool] = {
        pair: (kappa >= GATE_PAIRWISE_KAPPA)
        for pair, kappa in pairwise_kappa.items()
    }
    per_class: dict[str, dict[str, bool]] = {}
    for pos in ("A", "B", "C"):
        cells = {}
        for cls, acc in judge_results[pos].per_class_accuracy.items():
            # Only judge classes that had at least one ground-truth instance.
            if judge_results[pos].per_class_total.get(cls, 0) > 0:
                cells[cls] = acc >= GATE_PER_CLASS_ACCURACY
        per_class[pos] = cells
    all_pass = (
        all(per_judge.values())
        and all(pair_pass.values())
        and all(all(cells.values()) for cells in per_class.values())
    )
    return per_judge, pair_pass, per_class, all_pass


def _validate_prompt_version(
    judge_results: dict[str, JudgeCalibrationResult],
    expected: str,
) -> list[str]:
    """Defensive: every Judgment must carry the pinned prompt version.

    Returns a list of (position, case_id) for any record whose version
    diverges. Empty list = all clean.
    """
    bad = []
    for pos, res in judge_results.items():
        for j in res.judgments:
            if j.prompt_template_version != expected:
                bad.append(
                    f"{pos}/{j.case_id}: got {j.prompt_template_version!r} "
                    f"expected {expected!r}"
                )
    return bad


# ── persistence + report ───────────────────────────────────────────────


def _judgment_to_dict(j: Judgment) -> dict:
    d = asdict(j)
    d.pop("raw_response", None)
    return d


def write_per_judge_jsonl(
    out_dir: Path, results: dict[str, JudgeCalibrationResult]
) -> None:
    for pos, res in results.items():
        path = out_dir / f"judge_{pos.lower()}_calibration.jsonl"
        with path.open("w") as f:
            for j in res.judgments:
                f.write(json.dumps(_judgment_to_dict(j)) + "\n")


def render_results_json(run: CalibrationRunResults) -> dict:
    """Aggregated results in JSON form for `calibration_run_v1_results.json`."""
    return {
        "run_timestamp_utc": run.run_timestamp_utc,
        "prompt_template_version": run.prompt_template_version,
        "calibration_set_path": run.calibration_set_path,
        "case_count": run.case_count,
        "per_judge": {
            pos: {
                "judge_model": res.judge_model,
                "provider_token": res.provider_token,
                "case_count": res.case_count,
                "correct_count": res.correct_count,
                "overall_accuracy": res.overall_accuracy,
                "per_class_accuracy": res.per_class_accuracy,
                "per_class_total": res.per_class_total,
            }
            for pos, res in run.judge_results.items()
        },
        "pairwise_kappa": run.pairwise_kappa,
        "fleiss_kappa": run.fleiss_kappa,
        "judge_e_vs_d_match_rate": run.judge_e_vs_d_match_rate,
        "hard_gates": {
            "per_judge_accuracy": run.gate_per_judge_accuracy,
            "pairwise_kappa": run.gate_pairwise_kappa,
            "per_class_accuracy": run.gate_per_class_accuracy,
            "all_pass": run.all_gates_pass,
        },
    }


def render_summary_md(run: CalibrationRunResults) -> str:
    """Markdown summary suitable for paste into a chat update.

    Includes:
      - run metadata + Gemini-substitution disclosure
      - hard-gate verdicts table
      - per-judge accuracy table
      - pairwise κ table
      - per-class accuracy table (6 × 3)
    """
    lines: list[str] = []
    lines.append(f"# Stage 1 calibration — {run.run_timestamp_utc}")
    lines.append("")
    lines.append(f"**Prompt template version:** `{run.prompt_template_version}`")
    lines.append(f"**Calibration set:** `{run.calibration_set_path}` ({run.case_count} cases)")
    lines.append("")
    lines.append(
        "**Methodology disclosure**: Gemini Judge B ships with "
        "`gemini-2.5-pro` instead of spec §6.1's `gemini-3.1-pro` "
        "because the preview tier's 100 RPD is insufficient for the "
        "production-corpus run. See TIER_A_HANDOFF.md for details."
    )
    lines.append("")

    # Hard-gate summary
    lines.append("## Hard gates (spec §15.1)")
    lines.append("")
    lines.append("| Gate | Target | Verdict |")
    lines.append("|---|---|---|")
    for pos in ("A", "B", "C"):
        v = "✅" if run.gate_per_judge_accuracy[pos] else "❌"
        lines.append(
            f"| Judge {pos} accuracy ≥ {GATE_PER_JUDGE_ACCURACY:.0%} | "
            f"{run.judge_results[pos].overall_accuracy:.1%} | {v} |"
        )
    for pair, ok in run.gate_pairwise_kappa.items():
        v = "✅" if ok else "❌"
        lines.append(
            f"| Pairwise κ {pair[0]}/{pair[1]} ≥ {GATE_PAIRWISE_KAPPA:.2f} | "
            f"{run.pairwise_kappa[pair]:.3f} | {v} |"
        )
    for pos, cells in run.gate_per_class_accuracy.items():
        per_class_pass = all(cells.values())
        v = "✅" if per_class_pass else "❌"
        lines.append(
            f"| Judge {pos} per-class ≥ {GATE_PER_CLASS_ACCURACY:.0%} | "
            f"{'all classes pass' if per_class_pass else 'see table below'} | {v} |"
        )
    lines.append("")
    overall = "✅ ALL HARD GATES PASS" if run.all_gates_pass else "❌ ONE OR MORE GATES FAIL"
    lines.append(f"**Overall**: {overall}")
    lines.append("")

    # Per-judge accuracy
    lines.append("## Per-judge accuracy")
    lines.append("")
    lines.append("| Position | Token | Model | Accuracy | Correct/Total |")
    lines.append("|---|---|---|---:|---:|")
    for pos in ("A", "B", "C", "E"):
        if pos not in run.judge_results:
            continue
        r = run.judge_results[pos]
        lines.append(
            f"| {pos} | {r.provider_token} | {r.judge_model} | "
            f"{r.overall_accuracy:.1%} | {r.correct_count}/{r.case_count} |"
        )
    lines.append("")

    # Pairwise κ
    lines.append("## Pairwise Cohen's κ + Fleiss κ")
    lines.append("")
    lines.append(
        f"| A/B | A/C | B/C | Fleiss (A,B,C) |"
    )
    lines.append("|---:|---:|---:|---:|")
    lines.append(
        f"| {run.pairwise_kappa['AB']:.3f} | "
        f"{run.pairwise_kappa['AC']:.3f} | "
        f"{run.pairwise_kappa['BC']:.3f} | "
        f"{run.fleiss_kappa:.3f} |"
    )
    lines.append("")

    # Per-class accuracy table (6 × 3)
    lines.append("## Per-class accuracy (judge × verdict class)")
    lines.append("")
    lines.append("| Verdict class | n | A | B | C |")
    lines.append("|---|---:|---:|---:|---:|")
    for cls in VERDICT_CLASSES:
        n = run.judge_results["A"].per_class_total.get(cls, 0)
        a = run.judge_results["A"].per_class_accuracy.get(cls, 0.0)
        b = run.judge_results["B"].per_class_accuracy.get(cls, 0.0)
        c = run.judge_results["C"].per_class_accuracy.get(cls, 0.0)
        flag = lambda v: f"{v:.0%}" if n > 0 else "—"
        lines.append(f"| {cls} | {n} | {flag(a)} | {flag(b)} | {flag(c)} |")
    lines.append("")

    # Judge E sanity check
    if run.judge_e_vs_d_match_rate is not None:
        lines.append("## Judge E sanity check (informational only)")
        lines.append("")
        e_res = run.judge_results.get("E")
        if e_res is not None:
            successful = sum(1 for v in e_res.verdicts_by_index if v is not None)
            lines.append(
                f"Judge E verdict matches Judge D ground truth on "
                f"{run.judge_e_vs_d_match_rate:.1%} of {successful} successful "
                f"attempts (Mistral failed {e_res.case_count - successful} of "
                f"{e_res.case_count} cases — typically rate-limit or schema "
                f"validation, not a gate)."
            )
        else:
            lines.append(
                f"Judge E verdict matches Judge D ground truth on "
                f"{run.judge_e_vs_d_match_rate:.1%} of {run.case_count} cases."
            )
        lines.append("")

    return "\n".join(lines)


# ── orchestration ──────────────────────────────────────────────────────


async def run_calibration_async(
    *,
    judge_specs: list[tuple[str, str]],  # [(position, provider_token), ...]
    out_dir: Path,
    calibration_path: Path = DEFAULT_CALIBRATION_PATH,
    overrides_path: Path | None = None,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    concurrency: int = 5,
    judge_e_sanity_check: bool = True,
) -> CalibrationRunResults:
    """End-to-end Stage 1 calibration. Returns aggregated results."""
    from uofa_cli.adversarial.judge.providers.litellm_provider import LiteLLMProvider

    out_dir.mkdir(parents=True, exist_ok=True)

    records = _load_calibration_records(
        out_dir, calibration_path=calibration_path, overrides_path=overrides_path,
    )
    cases = [_build_case_for_judge(r) for r in records]
    ground_truth = [r["ground_truth_verdict"] for r in records]
    ground_truth_by_case = {r["case_id"]: r["ground_truth_verdict"] for r in records}

    # Build providers with the pinned prompt version. ALL judges
    # (including E) use judge_role="production" for Stage 1 because:
    # 1. The arbitration prompt expects production_verdicts in the case
    #    dict; we don't have those during a calibration sanity check.
    # 2. Spec §8.4's E-vs-D sanity check compares E running the same
    #    production prompt as A/B/C against Judge D's ground truth.
    #    Routing E through the arbitration prompt produces uninterpretable
    #    output (verified empirically on the first run: 5/30 accuracy
    #    + many parse failures).
    # E retains its arbiter role only at Stage 3b — separate from this.
    providers: dict[str, AbstractJudgeProvider] = {}
    for position, token in judge_specs:
        providers[position] = LiteLLMProvider(
            provider_token=token,
            judge_role="production",
            thinking_enabled=False,  # litellm 1.63 has gaps for current-gen reasoning params
            prompt_template_version=prompt_version,
        )

    # Dispatch each judge in parallel (independent vendors). Per-judge
    # concurrency overrides: Mistral's free-tier API has a tight RPS
    # cap (1/sec on free, varies on paid) that gets blown by
    # concurrency=5 on a 30-case sweep. Cap E at 1 by default — Stage 1's
    # E sanity check is small (30 cases × ~20s p50 = 10 min serial), so
    # the slowdown is acceptable. Production trio runs at the configured
    # concurrency.
    per_judge_concurrency = {
        pos: 1 if pos == "E" else concurrency for pos in providers
    }
    tasks = [
        _run_one_judge(
            position=pos, provider=p, cases=cases, ground_truth=ground_truth,
            concurrency=per_judge_concurrency[pos],
        )
        for pos, p in providers.items()
    ]
    results_list = await asyncio.gather(*tasks)
    results_by_pos: dict[str, JudgeCalibrationResult] = {
        r.position: r for r in results_list
    }

    # Defensive prompt-version check.
    drift = _validate_prompt_version(results_by_pos, expected=prompt_version)
    if drift:
        raise RuntimeError(
            "prompt-version drift detected — refusing to write summary. "
            f"Diverging records: {drift[:5]}{' ...' if len(drift) > 5 else ''}"
        )

    # Pairwise κ + Fleiss across A/B/C.
    pairwise, fleiss = _gate_pairwise_kappa(
        {pos: results_by_pos[pos] for pos in ("A", "B", "C") if pos in results_by_pos}
    )

    # Judge E sanity check (informational).
    judge_e_match: float | None = None
    if "E" in results_by_pos and judge_e_sanity_check:
        judge_e_match = _judge_e_vs_d_agreement(
            results_by_pos["E"], ground_truth
        )

    # Hard-gate evaluation (production trio only).
    per_judge_pass, pair_pass, per_class_pass, all_pass = _evaluate_hard_gates(
        {pos: results_by_pos[pos] for pos in ("A", "B", "C")},
        pairwise,
    )

    run = CalibrationRunResults(
        run_timestamp_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        prompt_template_version=prompt_version,
        calibration_set_path=str(calibration_path),
        case_count=len(records),
        judge_results=results_by_pos,
        pairwise_kappa=pairwise,
        fleiss_kappa=fleiss,
        judge_e_vs_d_match_rate=judge_e_match,
        gate_per_judge_accuracy=per_judge_pass,
        gate_pairwise_kappa=pair_pass,
        gate_per_class_accuracy=per_class_pass,
        all_gates_pass=all_pass,
    )

    # Persist.
    write_per_judge_jsonl(out_dir, results_by_pos)
    (out_dir / "calibration_run_v1_results.json").write_text(
        json.dumps(render_results_json(run), indent=2)
    )
    (out_dir / "calibration_run_v1_summary.md").write_text(render_summary_md(run))

    return run


def run_calibration(
    *,
    judge_specs: list[tuple[str, str]],
    out_dir: Path,
    calibration_path: Path = DEFAULT_CALIBRATION_PATH,
    overrides_path: Path | None = None,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    concurrency: int = 5,
    judge_e_sanity_check: bool = True,
) -> CalibrationRunResults:
    """Synchronous wrapper around run_calibration_async."""
    return asyncio.run(
        run_calibration_async(
            judge_specs=judge_specs,
            out_dir=out_dir,
            calibration_path=calibration_path,
            overrides_path=overrides_path,
            prompt_version=prompt_version,
            concurrency=concurrency,
            judge_e_sanity_check=judge_e_sanity_check,
        )
    )
