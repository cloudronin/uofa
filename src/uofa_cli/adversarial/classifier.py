"""Outcome classifier for adversarial coverage experiments — Phase 2 §10.

`uofa adversarial analyze` reads a batch manifest produced by
:mod:`uofa_cli.adversarial.runner`, runs ``uofa rules`` per generated
package to extract the rule firings, and classifies each package into
one of seven outcome classes per spec §10.3:

    COV-HIT          target rule fires; no unexpected rules
    COV-HIT-PLUS     target fires; other rules also fire
    COV-MISS         target does not fire; no other rules fire
    COV-WRONG        target does not fire; different rules fire
    COV-CLEAN-CORRECT  no rules fire (negative_control as desired)
    COV-CLEAN-WRONG    rules fire on a negative_control (precision bug)
    GEN-INVALID      package SHACL-failed during generation

Output CSVs (per spec §10.3, §10.4, §11.2):

    outcomes.csv  per-package row
    matrix.csv    aggregated catalog × subtlety pivot
    summary.csv   per-pattern aggregate (one row per shipped UofA core
                  pattern; schema per UofA_Phase2_M4_Cleanup_Spec.md)

Baseline subtraction: when a spec's ``base_cou`` is a shipped example
(Morrison COU1=24, COU2=18, Nagaraja COU1=32) the classifier records
``baseline_firings_count`` and ``baseline_firings_minus_target`` so the
caller can distinguish target-rule firings from pre-existing ones.

Note on summary.csv: View-3 overall precision/recall metrics
(catalog_recall, catalog_precision_1_minus_fpr, gap_probe_miss_rate)
are emitted in the HTML report's View 3 only — they were previously
also written to summary.csv but were moved out so summary.csv can
carry the per-pattern aggregate that the D1 extension spec depends on.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import socket
import subprocess
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

from uofa_cli.output import error, info, result_line, warn


# v0.5.2 baselines per Phase 2 Spec v1.7 §3.1.
BASELINE_FIRINGS: dict[str, int] = {
    "morrison/cou1": 24,
    "morrison/cou2": 18,
    "nagaraja/cou1": 32,
}


# Active UofA core patterns at v0.5.4. Source of truth:
# packs/core/rules/uofa_weakener.rules (`uofa catalog` reports the
# same 23 IDs at v0.5.4 HEAD; COMPOUND-02 is commented out and
# excluded). Used as the row index for summary.csv per-pattern aggregate.
_CORE_PATTERN_IDS: tuple[str, ...] = (
    "W-AR-01", "W-AR-02", "W-AR-03", "W-AR-04", "W-AR-05",
    "W-EP-01", "W-EP-02", "W-EP-03", "W-EP-04",
    "W-AL-01", "W-AL-02",
    "W-ON-01", "W-ON-02",
    "W-SI-01", "W-SI-02",
    "W-CON-01", "W-CON-02", "W-CON-03", "W-CON-04", "W-CON-05",
    "W-PROV-01",
    "COMPOUND-01", "COMPOUND-03",
)


SUMMARY_FIELDS: tuple[str, ...] = (
    "pattern_id",
    "confirm_existing_count",
    "confirm_existing_hits",
    "recall",
    "negative_control_firings",
    "gap_probe_firings",
    "total_firings_across_battery",
    # D1 (v1.8) per-COU coverage delta columns
    "recall_morrison_cou1",
    "recall_morrison_cou2",
    "recall_nagaraja",
    "recall_min_per_cou",
    "recall_cou_disparity",
    "cou_dependent_flag",
)


# D1 (v1.8): _detect_baseline_key returns one of these for shipped base COUs.
# These are the column-name suffixes used in summary.csv per-COU columns.
_COU_KEY_TO_COLUMN: dict[str, str] = {
    "morrison/cou1": "recall_morrison_cou1",
    "morrison/cou2": "recall_morrison_cou2",
    "nagaraja/cou1": "recall_nagaraja",
}

# D1 (v1.8): rules with recall disparity >= this threshold across base COUs
# are flagged as COU-dependent. Threshold per Phase 2 Spec v1.8 §10.4.
COU_DEPENDENT_DISPARITY_THRESHOLD: float = 0.30


@dataclass
class _OutcomeRow:
    spec_id: str
    variant_num: int
    target_weakener: str | None
    source_taxonomy: str | None
    coverage_intent: str
    subtlety: str
    outcome_class: str
    rules_fired: str
    target_rule_fired: bool
    baseline_firings_count: int | None
    baseline_firings_minus_target: int | None
    section_6_7_candidate: str | None
    shacl_retries: int
    tokens: int
    cost_usd: float
    # D1 (v1.8): which base COU this row's spec was generated against. Values
    # are keys of BASELINE_FIRINGS ("morrison/cou1" etc.) or None for specs
    # whose base_cou doesn't match a shipped COU. Internal-only — not written
    # to outcomes.csv (v1.8 §10.3 only adds D2 timing columns).
    base_cou_key: str | None = None
    # D2 (v1.8) per-package timing capture; see Phase 2 Spec §5.4.
    total_eval_ms: int = 0
    jena_load_ms: int = 0
    jena_inference_ms: int = 0
    output_serialize_ms: int = 0
    eval_host_id: str = ""


def _detect_baseline_key(base_cou: str | None) -> str | None:
    """Match ``packs/vv40/examples/morrison/cou1`` → ``morrison/cou1``."""
    if not base_cou:
        return None
    s = str(base_cou)
    for key in BASELINE_FIRINGS:
        if key in s:
            return key
    return None


# Pattern matching for `uofa rules` output (one annotation per line).
_RULE_LINE = re.compile(r"^\s*[⚠⚡]\s+(W-[A-Z]+-\d+|COMPOUND-\d+)\s+\[")
_HIT_COUNT = re.compile(r"—\s+(\d+)\s+hit\(s\)")


def _parse_rule_firings_from_check(stdout: str) -> dict[str, int]:
    """Extract ``{pattern_id: hit_count}`` from `uofa check` / `uofa rules` stdout."""
    firings: dict[str, int] = {}
    for line in stdout.splitlines():
        m = _RULE_LINE.search(line)
        if not m:
            continue
        pattern = m.group(1)
        hit_match = _HIT_COUNT.search(line)
        firings[pattern] = int(hit_match.group(1)) if hit_match else 1
    return firings


def _resolve_eval_host_id() -> str:
    """D2 (v1.8) host id: env var override or hostname fallback."""
    return os.environ.get("UOFA_EVAL_HOST_ID") or socket.gethostname() or "unknown"


def _run_rules_on_package(
    package_path: Path, pack: str = "vv40"
) -> tuple[dict[str, int], dict[str, int]]:
    """Invoke `uofa rules` on a package and return (firings, timings).

    timings dict keys: ``total_eval_ms``, ``jena_load_ms``,
    ``jena_inference_ms``, ``output_serialize_ms``. The Jena split is
    best-effort — without Java-side instrumentation we cannot separate
    load from inference, so ``jena_load_ms`` is 0 and ``jena_inference_ms``
    carries the lumped subprocess cost. ``output_serialize_ms`` is the
    Python-side parse time. See Phase 2 Spec v1.8 §5.4 fallback.

    Returns ({}, {timings}) on subprocess error so the classifier records
    GEN-INVALID without crashing.
    """
    timings = {
        "total_eval_ms": 0,
        "jena_load_ms": 0,
        "jena_inference_ms": 0,
        "output_serialize_ms": 0,
    }

    t_start = time.perf_counter_ns()
    try:
        result = subprocess.run(
            ["python", "-m", "uofa_cli", "rules", "--pack", pack, str(package_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (subprocess.TimeoutExpired, OSError):
        timings["total_eval_ms"] = int((time.perf_counter_ns() - t_start) / 1_000_000)
        return {}, timings
    t_subprocess_end = time.perf_counter_ns()

    firings = _parse_rule_firings_from_check(result.stdout)
    t_parse_end = time.perf_counter_ns()

    subprocess_ms = int((t_subprocess_end - t_start) / 1_000_000)
    parse_ms = int((t_parse_end - t_subprocess_end) / 1_000_000)
    timings["total_eval_ms"] = subprocess_ms + parse_ms
    # Lump subprocess time into jena_inference_ms (see docstring fallback).
    timings["jena_inference_ms"] = subprocess_ms
    timings["output_serialize_ms"] = parse_ms
    return firings, timings


def _classify(
    coverage_intent: str,
    target_weakener: str | None,
    firings_minus_baseline: dict[str, int],
    package_exists: bool,
) -> tuple[str, bool]:
    """Return ``(outcome_class, target_rule_fired)``.

    *firings_minus_baseline* should already have the base-COU baseline
    subtracted; it represents the firings ATTRIBUTABLE to the synthetic
    perturbation in the generated package.
    """
    if not package_exists:
        return "GEN-INVALID", False

    fired = set(firings_minus_baseline.keys())
    target_fired = bool(target_weakener and target_weakener in fired)

    if coverage_intent == "negative_control":
        if not fired:
            return "COV-CLEAN-CORRECT", False
        return "COV-CLEAN-WRONG", False

    if coverage_intent == "gap_probe":
        if not fired:
            return "COV-MISS", False
        return "COV-WRONG", False

    if coverage_intent == "interaction":
        # Interaction expects multiple firings; we report HIT-PLUS if any
        # rule fires (the spec §13.4 acceptance for INT-1..4 checks
        # COMPOUND firings via the per-pattern matrix, not via this label).
        if not fired:
            return "COV-MISS", False
        return "COV-HIT-PLUS", target_fired

    # confirm_existing
    if target_fired:
        if len(fired) == 1:
            return "COV-HIT", True
        return "COV-HIT-PLUS", True
    if not fired:
        return "COV-MISS", False
    return "COV-WRONG", False


def _subtract_baseline(
    firings: dict[str, int], baseline_count: int | None
) -> dict[str, int]:
    """Reduce per-pattern hit counts by approximating the baseline as a
    proportional reduction. Conservative: preserves any fired pattern as
    a positive count if the baseline does not fully account for it.
    """
    if baseline_count is None:
        return firings
    total = sum(firings.values())
    if total <= baseline_count:
        return {}
    # Conservative trimming: assume baseline scales proportionally and
    # subtract that fraction from each pattern's hit count, floor at 0.
    factor = baseline_count / max(total, 1)
    out = {}
    for pat, count in firings.items():
        delta = max(0, count - int(round(count * factor)))
        if delta:
            out[pat] = delta
    return out


def _scan_outcomes(
    in_dir: Path, pack: str
) -> list[_OutcomeRow]:
    """Walk the batch_manifest.perSpecResults and produce per-package rows."""
    manifest_path = in_dir / "batch_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"batch_manifest.json not found in {in_dir}; "
            f"run `uofa adversarial run` first"
        )
    batch = json.loads(manifest_path.read_text())

    # D2 (v1.8): single host id per analyze invocation.
    eval_host_id = _resolve_eval_host_id()

    # Per-rule timing accumulator for rule_timing.csv (D2). Keyed by
    # (rule_id, package_path); value is rule_eval_ms. With Jena's native
    # per-rule timing unavailable, we record only that the rule fired
    # (rule_eval_ms = 0 placeholder) so the CSV is shape-correct for
    # downstream consumers. The fallback note in batch_manifest documents
    # the limitation.
    rule_timing_rows: list[dict] = []

    rows: list[_OutcomeRow] = []

    for per_spec in batch.get("perSpecResults", []):
        spec_id = per_spec["spec_id"]
        spec_out_dir = Path(per_spec["out_dir"])
        coverage_intent = per_spec["coverage_intent"]
        target_weakener = per_spec.get("target_weakener")
        source_taxonomy = per_spec.get("source_taxonomy")

        per_spec_manifest_path = spec_out_dir / "manifest.json"
        if not per_spec_manifest_path.exists():
            warn(f"  (no per-spec manifest for {spec_id}; skipping)")
            continue
        per_spec_manifest = json.loads(per_spec_manifest_path.read_text())

        # Detect baseline from spec_path -> base_cou (best effort: read spec).
        baseline_key = None
        try:
            spec_path = Path(per_spec["spec_path"])
            from uofa_cli.adversarial.spec_loader import load_spec
            spec_obj = load_spec(spec_path)
            baseline_key = _detect_baseline_key(str(spec_obj.base_cou))
        except Exception:
            pass
        baseline_count = (
            BASELINE_FIRINGS.get(baseline_key) if baseline_key else None
        )

        for variant in per_spec_manifest.get("variants", []):
            variant_num = variant.get("variantNum") or variant.get("variant_num")
            package_path_str = (
                variant.get("packagePath") or variant.get("package_path")
            )
            tokens = variant.get("tokens", 0)
            shacl_retries = variant.get("shaclRetries") or variant.get("shacl_retries", 0)
            shacl_passed = (
                variant.get("shaclPassed", False)
                or variant.get("shacl_passed", False)
            )

            # Generator writes packagePath as a bare filename relative to
            # the per-spec output directory. Resolve it.
            package_path = None
            if package_path_str:
                p = Path(package_path_str)
                if not p.is_absolute():
                    p = spec_out_dir / p
                package_path = p
            package_exists = (
                package_path is not None and package_path.exists() and shacl_passed
            )

            if package_exists:
                firings, timings = _run_rules_on_package(package_path, pack=pack)
            else:
                firings, timings = {}, {
                    "total_eval_ms": 0,
                    "jena_load_ms": 0,
                    "jena_inference_ms": 0,
                    "output_serialize_ms": 0,
                }

            # D2: collect per-rule timing rows. Jena native per-rule timing
            # is not exposed; record rule_fired only (rule_eval_ms 0).
            for pat in firings:
                rule_timing_rows.append({
                    "rule_id": pat,
                    "package_path": str(package_path) if package_path else "",
                    "rule_eval_ms": 0,
                    "rule_fired": "True",
                })

            firings_subtracted = _subtract_baseline(firings, baseline_count)

            outcome_class, target_fired = _classify(
                coverage_intent=coverage_intent,
                target_weakener=target_weakener,
                firings_minus_baseline=firings_subtracted,
                package_exists=package_exists,
            )

            rules_fired_str = ",".join(sorted(firings_subtracted.keys()))
            baseline_minus = (
                baseline_count - sum(firings.values()) if baseline_count else None
            )

            rows.append(_OutcomeRow(
                spec_id=spec_id,
                variant_num=variant_num or 0,
                target_weakener=target_weakener,
                source_taxonomy=source_taxonomy,
                coverage_intent=coverage_intent,
                subtlety=per_spec_manifest.get("subtlety", "high"),
                outcome_class=outcome_class,
                rules_fired=rules_fired_str,
                target_rule_fired=target_fired,
                baseline_firings_count=baseline_count,
                baseline_firings_minus_target=baseline_minus,
                section_6_7_candidate=None,
                shacl_retries=shacl_retries,
                tokens=tokens,
                cost_usd=variant.get("estimatedCostUsd", 0.0),
                base_cou_key=baseline_key,
                total_eval_ms=timings["total_eval_ms"],
                jena_load_ms=timings["jena_load_ms"],
                jena_inference_ms=timings["jena_inference_ms"],
                output_serialize_ms=timings["output_serialize_ms"],
                eval_host_id=eval_host_id,
            ))
    # Stash rule_timing_rows on the function for run_analyze to pick up.
    # (Cleaner than rewiring the return tuple; classifier callers within
    # the codebase only consume rows.)
    _scan_outcomes._last_rule_timing_rows = rule_timing_rows  # type: ignore[attr-defined]
    return rows


# Internal-only _OutcomeRow fields that are NOT exported to outcomes.csv.
# (D1 v1.8: base_cou_key is internal to the per-COU aggregator; v1.8 §10.3
# does not add a base_cou column to outcomes.csv.)
_OUTCOMES_CSV_EXCLUDED_FIELDS: frozenset[str] = frozenset({"base_cou_key"})


def _write_outcomes_csv(rows: list[_OutcomeRow], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        f for f in _OutcomeRow.__dataclass_fields__
        if f not in _OUTCOMES_CSV_EXCLUDED_FIELDS
    ]
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(asdict(row))


def _build_matrix(rows: list[_OutcomeRow]) -> dict:
    """Pivot 1: catalog self-coverage = HIT+HIT-PLUS / total per (pattern × subtlety)."""
    pivot: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: {"hit": 0, "total": 0})
    for r in rows:
        if r.coverage_intent != "confirm_existing" or not r.target_weakener:
            continue
        key = (r.target_weakener, r.subtlety)
        pivot[key]["total"] += 1
        if r.outcome_class in ("COV-HIT", "COV-HIT-PLUS"):
            pivot[key]["hit"] += 1
    return pivot


def _write_matrix_csv(rows: list[_OutcomeRow], out_path: Path) -> None:
    pivot = _build_matrix(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pattern", "subtlety", "hit_rate", "hits", "total"])
        for (pattern, subtlety), counts in sorted(pivot.items()):
            total = counts["total"]
            rate = counts["hit"] / total if total else 0.0
            w.writerow([pattern, subtlety, f"{rate:.3f}", counts["hit"], total])


def _split_rules_fired(rules_fired: str) -> set[str]:
    """Split a comma-separated ``rules_fired`` field into a set of pattern IDs."""
    if not rules_fired:
        return set()
    return {p.strip() for p in rules_fired.split(",") if p.strip()}


def _write_summary_csv(rows: list[_OutcomeRow], out_path: Path) -> None:
    """Per-pattern aggregate, one row per active UofA core pattern.

    Schema per `UofA_Phase2_M4_Cleanup_Spec.md` (closes v1.7 §13.1 gate #9
    and unblocks the D1 extension spec, which appends per-COU breakdown
    columns to this same file):

        pattern_id, confirm_existing_count, confirm_existing_hits, recall,
        negative_control_firings, gap_probe_firings,
        total_firings_across_battery

    All counts derived from *rows* — no re-evaluation of packages.
    """
    # Per-pattern accumulators, indexed by pattern_id from _CORE_PATTERN_IDS.
    confirm_count: Counter[str] = Counter()
    confirm_hits: Counter[str] = Counter()
    nc_firings: Counter[str] = Counter()
    gp_firings: Counter[str] = Counter()
    total_firings: Counter[str] = Counter()

    # D1 (v1.8): per-(pattern, base_cou_key) accumulators for per-COU recall.
    per_cou_count: dict[tuple[str, str], int] = defaultdict(int)
    per_cou_hits: dict[tuple[str, str], int] = defaultdict(int)

    def _is_truthy(value) -> bool:
        return (value is True) or (
            isinstance(value, str) and value.strip().lower() == "true"
        )

    for r in rows:
        fired = _split_rules_fired(r.rules_fired)

        # Total firings across the battery — per pattern.
        for pat in fired:
            total_firings[pat] += 1

        # confirm_existing: count attempts and hits per target pattern.
        if r.coverage_intent == "confirm_existing" and r.target_weakener:
            confirm_count[r.target_weakener] += 1
            # ``target_rule_fired`` arrives here as a Python bool from
            # _OutcomeRow but the same code path runs after CSV reads
            # produce strings; accept both.
            hit = _is_truthy(r.target_rule_fired)
            if hit:
                confirm_hits[r.target_weakener] += 1

            # D1: per-COU bucketing (only when row carries a base_cou_key).
            cou_key = getattr(r, "base_cou_key", None)
            if cou_key in _COU_KEY_TO_COLUMN:
                per_cou_count[(r.target_weakener, cou_key)] += 1
                if hit:
                    per_cou_hits[(r.target_weakener, cou_key)] += 1

        if r.coverage_intent == "negative_control":
            for pat in fired:
                nc_firings[pat] += 1

        if r.coverage_intent == "gap_probe":
            for pat in fired:
                gp_firings[pat] += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        w.writeheader()
        for pat in _CORE_PATTERN_IDS:
            n = confirm_count[pat]
            h = confirm_hits[pat]
            recall_str = f"{(h / n):.3f}" if n else ""

            # D1: per-COU recall computation.
            per_cou_recall: dict[str, str] = {
                col: "" for col in _COU_KEY_TO_COLUMN.values()
            }
            non_empty_recalls: list[float] = []
            for cou_key, col_name in _COU_KEY_TO_COLUMN.items():
                count = per_cou_count.get((pat, cou_key), 0)
                if count == 0:
                    continue
                hits = per_cou_hits.get((pat, cou_key), 0)
                value = hits / count
                per_cou_recall[col_name] = f"{value:.3f}"
                non_empty_recalls.append(value)

            if len(non_empty_recalls) >= 1:
                recall_min = f"{min(non_empty_recalls):.3f}"
            else:
                recall_min = ""

            if len(non_empty_recalls) >= 2:
                disparity = max(non_empty_recalls) - min(non_empty_recalls)
                disparity_str = f"{disparity:.3f}"
                cou_dependent = (
                    "True" if disparity >= COU_DEPENDENT_DISPARITY_THRESHOLD
                    else "False"
                )
            else:
                disparity_str = ""
                cou_dependent = ""

            w.writerow({
                "pattern_id": pat,
                "confirm_existing_count": n,
                "confirm_existing_hits": h,
                "recall": recall_str,
                "negative_control_firings": nc_firings[pat],
                "gap_probe_firings": gp_firings[pat],
                "total_firings_across_battery": total_firings[pat],
                "recall_morrison_cou1": per_cou_recall["recall_morrison_cou1"],
                "recall_morrison_cou2": per_cou_recall["recall_morrison_cou2"],
                "recall_nagaraja": per_cou_recall["recall_nagaraja"],
                "recall_min_per_cou": recall_min,
                "recall_cou_disparity": disparity_str,
                "cou_dependent_flag": cou_dependent,
            })


RULE_TIMING_FIELDS: tuple[str, ...] = (
    "rule_id",
    "package_path",
    "rule_eval_ms",
    "rule_fired",
)

#: Fallback note recorded in <batch_dir>/batch_manifest.json when per-rule
#: timing is unavailable from Jena natively. Per Phase 2 Spec v1.8 §10.5,
#: the rule_timing.csv file is written with the per-(rule, package) firing
#: rows but rule_eval_ms is set to 0 (Jena GenericRuleReasoner does not
#: expose per-rule wall-clock without Java-side instrumentation).
RULE_TIMING_FALLBACK_NOTE: str = (
    "Per-rule wall-clock timing is not exposed by Jena's GenericRuleReasoner "
    "(FORWARD_RETE) without Java-side instrumentation. rule_timing.csv "
    "records (rule, package) firing pairs with rule_eval_ms=0; the lumped "
    "subprocess time appears in outcomes.csv jena_inference_ms / "
    "total_eval_ms. Phase 2 Spec v1.8 §10.5 acknowledges this fallback."
)


def _write_rule_timing_csv(rule_timing_rows: list[dict], out_path: Path) -> None:
    """D2 (v1.8) §10.5: per-(rule, package) timing CSV.

    Always writes a schema-conformant header. The Jena native fallback path
    sets rule_eval_ms=0 on every row (see RULE_TIMING_FALLBACK_NOTE).
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=RULE_TIMING_FIELDS)
        w.writeheader()
        for row in rule_timing_rows:
            w.writerow({k: row.get(k, "") for k in RULE_TIMING_FIELDS})


def _annotate_batch_manifest_with_timing_fallback(in_dir: Path) -> None:
    """Append D2 timing_fallback_note to the batch manifest if not already
    present. Idempotent — safe to call from analyze even when the runner
    didn't write it during generation."""
    manifest_path = in_dir / "batch_manifest.json"
    if not manifest_path.exists():
        return
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError):
        return
    if manifest.get("timing_fallback_note"):
        return
    manifest["timing_fallback_note"] = RULE_TIMING_FALLBACK_NOTE
    manifest_path.write_text(json.dumps(manifest, indent=2))


def run_analyze(args) -> int:
    """Entry point for ``uofa adversarial analyze``."""
    in_dir: Path = args.in_dir
    out_dir: Path = args.out
    pack = args.check_pack

    info(f"analyzing batch at {in_dir}")
    try:
        rows = _scan_outcomes(in_dir, pack=pack)
    except FileNotFoundError as e:
        error(str(e))
        return 2

    if not rows:
        warn("no per-package rows produced; nothing to write")
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    outcomes_path = out_dir / "outcomes.csv"
    matrix_path = out_dir / "matrix.csv"
    summary_path = out_dir / "summary.csv"
    rule_timing_path = out_dir / "rule_timing.csv"

    _write_outcomes_csv(rows, outcomes_path)
    _write_matrix_csv(rows, matrix_path)
    _write_summary_csv(rows, summary_path)

    # D2: rule_timing.csv (fallback path — see RULE_TIMING_FALLBACK_NOTE).
    rule_timing_rows = getattr(_scan_outcomes, "_last_rule_timing_rows", [])
    _write_rule_timing_csv(rule_timing_rows, rule_timing_path)
    _annotate_batch_manifest_with_timing_fallback(in_dir)

    # HTML report (delegated to reporter.py)
    from uofa_cli.adversarial.reporter import write_html_report
    html_path = out_dir / "index.html"
    write_html_report(rows, html_path)

    by_class = Counter(r.outcome_class for r in rows)
    info(f"  outcomes by class: {dict(by_class)}")
    result_line("outcomes", True, str(outcomes_path))
    result_line("matrix", True, str(matrix_path))
    result_line("summary", True, str(summary_path))
    result_line("rule_timing", True, str(rule_timing_path))
    result_line("report", True, str(html_path))
    return 0
