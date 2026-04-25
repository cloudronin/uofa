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
import re
import subprocess
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
)


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


def _run_rules_on_package(package_path: Path, pack: str = "vv40") -> dict[str, int]:
    """Invoke `uofa rules` on a package and return parsed firings.

    Returns an empty dict on subprocess error so the classifier records
    GEN-INVALID rather than crashing.
    """
    try:
        result = subprocess.run(
            ["python", "-m", "uofa_cli", "rules", "--pack", pack, str(package_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (subprocess.TimeoutExpired, OSError):
        return {}
    return _parse_rule_firings_from_check(result.stdout)


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

            firings = (
                _run_rules_on_package(package_path, pack=pack)
                if package_exists else {}
            )
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
            ))
    return rows


def _write_outcomes_csv(rows: list[_OutcomeRow], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(_OutcomeRow.__dataclass_fields__)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
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
            tr = r.target_rule_fired
            if (tr is True) or (isinstance(tr, str) and tr.strip().lower() == "true"):
                confirm_hits[r.target_weakener] += 1

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
            w.writerow({
                "pattern_id": pat,
                "confirm_existing_count": n,
                "confirm_existing_hits": h,
                "recall": recall_str,
                "negative_control_firings": nc_firings[pat],
                "gap_probe_firings": gp_firings[pat],
                "total_firings_across_battery": total_firings[pat],
            })


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

    _write_outcomes_csv(rows, outcomes_path)
    _write_matrix_csv(rows, matrix_path)
    _write_summary_csv(rows, summary_path)

    # HTML report (delegated to reporter.py)
    from uofa_cli.adversarial.reporter import write_html_report
    html_path = out_dir / "index.html"
    write_html_report(rows, html_path)

    by_class = Counter(r.outcome_class for r in rows)
    info(f"  outcomes by class: {dict(by_class)}")
    result_line("outcomes", True, str(outcomes_path))
    result_line("matrix", True, str(matrix_path))
    result_line("summary", True, str(summary_path))
    result_line("report", True, str(html_path))
    return 0
