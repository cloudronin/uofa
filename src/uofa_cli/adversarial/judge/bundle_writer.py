"""judge_ready_bundle.tgz writer (spec v1.5 §2.1).

Packages a Phase 2 batch directory (output of `uofa adversarial run` +
`uofa adversarial analyze`) into the §2.1 bundle schema. Round-trip
compatible with `judge.bundle.open_bundle()`.

**Class normalization.** Phase 2 emits outcome classes (`COV-HIT-PLUS`,
`COV-WRONG`, `COV-CLEAN-WRONG`, `GEN-INVALID`) that diverge from the
Phase 3 spec's assumed taxonomy. The writer normalizes via NORMALIZE map;
the original Phase 2 class is preserved on every outcome under
`phase2_outcome_class_raw` for downstream provenance.

**Entry granularity.** One bundle entry per `.jsonld` variant file in
the batch. The same `outcomes.csv` row (key = spec_id + variant_num +
subtlety) can produce multiple entries when a spec was run against
multiple `--base-cou-override` values; case_id is extended with the
sub-directory name suffix (subtlety + base_cou) to keep entries unique.
"""

from __future__ import annotations

import csv
import json
import logging
import re
import tarfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)


# Phase 2 → spec class normalization. New classes must explicitly map here
# or the writer raises BundleWriteError; silent pass-through would hide
# Phase 2 schema drift.
NORMALIZE: dict[str, str] = {
    "COV-HIT": "COV-HIT",
    "COV-HIT-PLUS": "COV-HIT",
    "COV-MISS": "COV-MISS",
    "COV-WRONG": "COV-WRONG",
    "COV-CLEAN-WRONG": "COV-WRONG",
    "GEN-INVALID": "GEN-INVALID",
}

# Per-package dir name. The runner appends `_<subtlety>_<base_cou>` suffix
# to the base spec id when --subtlety-override / --base-cou-override are
# applied. Crucially, outcomes.csv records the FULL dir name as `spec_id`
# (not the base id), so the writer treats the dir name itself as the
# lookup key into outcomes.csv. Optional suffix capture is informational
# (drives experimental_factors.base_cou).
_SPEC_DIR_RE = re.compile(
    r"^(?P<full_id>"
    r"(?P<base_id>adv-\d+-[a-z0-9]+-\d+-[a-z0-9-]+?)"
    r"(?:_(?P<subtlety>low|medium|high))?"
    r"(?:_(?P<base_cou>[a-z]+-cou\d+))?"
    r")$"
)

# Per-variant jsonld filename: <base_spec_id>-v<NN>.jsonld
_VARIANT_FILE_RE = re.compile(
    r"^(?P<base_id>adv-\d+-[a-z0-9]+-\d+-[a-z0-9-]+)-v(?P<variant>\d+)\.jsonld$"
)


class BundleWriteError(Exception):
    """Raised when the writer can't produce a consistent bundle."""


@dataclass(frozen=True)
class _RowKey:
    """The (spec_id_full, variant_num) tuple keying outcomes.csv → jsonld.

    spec_id_full is the FULL spec_id from outcomes.csv, which includes the
    subtlety+base_cou suffix when those override flags were applied during
    the Phase 2 run.
    """

    spec_id_full: str
    variant_num: int


@dataclass
class WriteResult:
    """Summary returned to the caller of `write_bundle`."""

    bundle_path: Path
    package_count: int
    distribution: dict[str, int]  # normalized class → count
    raw_distribution: dict[str, int]  # original Phase 2 class → count
    warnings: list[str]


def write_bundle(
    batch_dir: Path,
    outcomes_csv: Path,
    out_path: Path,
    *,
    phase2_spec_version: str = "1.3",
    phase2_tag: str = "v0.4.1-phase2-complete",
    generator_model: str = "anthropic/claude-sonnet-4-6",
    generated_at: str | None = None,
) -> WriteResult:
    """Package `batch_dir` into a judge_ready_bundle.tgz at `out_path`.

    Reads outcomes.csv to attach per-variant outcome metadata, then
    iterates jsonld files in the batch dir to build per-package entries.

    Returns a WriteResult summarizing the package count, normalized class
    distribution, and any warnings encountered (e.g., jsonld files with
    no matching outcomes row).
    """
    batch_dir = Path(batch_dir)
    outcomes_csv = Path(outcomes_csv)
    out_path = Path(out_path)

    if not batch_dir.is_dir():
        raise BundleWriteError(f"batch_dir not found or not a directory: {batch_dir}")
    if not outcomes_csv.is_file():
        raise BundleWriteError(f"outcomes.csv not found: {outcomes_csv}")

    rows_by_key = _index_outcomes(outcomes_csv)
    entries = list(_iter_entries(batch_dir, rows_by_key))
    if not entries:
        raise BundleWriteError(
            f"no jsonld variants found under {batch_dir}; "
            f"is this a Phase 2 batch directory?"
        )

    distribution: dict[str, int] = {}
    raw_distribution: dict[str, int] = {}
    warnings: list[str] = []
    source_taxonomies: set[str] = set()

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tarfile.open(out_path, "w:gz") as tf:
        for entry in entries:
            outcome = entry.outcome_dict
            normalized = outcome["coverage_class"]
            raw = outcome["phase2_outcome_class_raw"]
            distribution[normalized] = distribution.get(normalized, 0) + 1
            raw_distribution[raw] = raw_distribution.get(raw, 0) + 1
            if outcome.get("source_taxonomy"):
                source_taxonomies.add(str(outcome["source_taxonomy"]).split("/")[0])

            _add_member(
                tf,
                f"judge_ready_bundle/packages/{entry.case_id}.jsonld",
                entry.package_text,
            )
            _add_member(
                tf,
                f"judge_ready_bundle/packages/{entry.case_id}.outcome.json",
                json.dumps(outcome, indent=2),
            )

        # Manifest. Built last so package_count + distribution are accurate.
        manifest = {
            "phase2_spec_version": phase2_spec_version,
            "generated_at": generated_at or _now_iso(),
            "generator_provenance": {
                "generator_model": generator_model,
                "phase2_tag": phase2_tag,
            },
            "package_count": len(entries),
            "coverage_class_distribution": distribution,
            "phase2_outcome_class_raw_distribution": raw_distribution,
            "source_taxonomies": sorted(source_taxonomies),
            "experimental_factors": {
                "subtlety_levels": ["low", "medium", "high"],
                "base_cous": ["morrison_cou1", "morrison_cou2", "nagaraja_cou1"],
                "model_families": ["claude"],
            },
        }
        _add_member(
            tf, "judge_ready_bundle/manifest.json", json.dumps(manifest, indent=2)
        )

        # Coverage CSVs: copy from <batch>/coverage/{matrix,summary}.csv if
        # present. Optional — older Phase 2 batches may not have them.
        for csv_name in ("matrix.csv", "summary.csv"):
            src = batch_dir / "coverage" / csv_name
            if src.exists():
                _add_member(
                    tf, f"judge_ready_bundle/coverage/{csv_name}", src.read_text()
                )
            else:
                warnings.append(f"coverage/{csv_name} not present in batch dir")

    return WriteResult(
        bundle_path=out_path,
        package_count=len(entries),
        distribution=distribution,
        raw_distribution=raw_distribution,
        warnings=warnings,
    )


# ── outcomes.csv indexing ───────────────────────────────────────────────


def _index_outcomes(path: Path) -> dict[_RowKey, dict[str, str]]:
    """Read outcomes.csv into a dict keyed by (spec_id_full, variant_num)."""
    out: dict[_RowKey, dict[str, str]] = {}
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = _RowKey(
                spec_id_full=row["spec_id"],
                variant_num=int(row["variant_num"]),
            )
            out[key] = row
    return out


# ── per-entry assembly ──────────────────────────────────────────────────


@dataclass
class _Entry:
    case_id: str
    package_text: str  # raw jsonld bytes (passed through verbatim)
    outcome_dict: dict


def _iter_entries(
    batch_dir: Path,
    rows_by_key: dict[_RowKey, dict[str, str]],
) -> Iterable[_Entry]:
    """Walk the batch dir, find jsonld variants, attach outcome rows.

    Skipped (with a warning to stderr via `logger`):
      - jsonld files outside a recognized spec dir name pattern
      - jsonld variants with no matching outcomes row
    """
    # Each top-level subdirectory is a battery: confirm_existing, gap_probe,
    # interaction, negative_controls. Inside is one dir per spec_id × subtlety
    # × base_cou combination; the dir NAME is the outcomes.csv spec_id.
    for category_dir in sorted(batch_dir.iterdir()):
        if not category_dir.is_dir() or category_dir.name == "coverage":
            continue
        if category_dir.name in ("review_packets", "raw_responses"):
            continue
        for spec_dir in sorted(category_dir.iterdir()):
            if not spec_dir.is_dir():
                continue
            dir_match = _SPEC_DIR_RE.match(spec_dir.name)
            if not dir_match:
                logger.warning("skipping unrecognized spec dir: %s", spec_dir.name)
                continue
            full_id = dir_match.group("full_id")
            dir_subtlety = dir_match.group("subtlety") or ""
            dir_base_cou = dir_match.group("base_cou") or ""

            for jsonld_path in sorted(spec_dir.glob("*.jsonld")):
                file_match = _VARIANT_FILE_RE.match(jsonld_path.name)
                if not file_match:
                    logger.warning("skipping unrecognized jsonld: %s", jsonld_path)
                    continue
                variant_num = int(file_match.group("variant"))
                # outcomes.csv keys on the FULL spec_id (= dir name), not the
                # base id; the (full_id, variant_num) pair uniquely identifies
                # a row.
                key = _RowKey(spec_id_full=full_id, variant_num=variant_num)
                row = rows_by_key.get(key)
                if row is None:
                    logger.warning(
                        "no outcomes row for spec_id=%s variant=%d; skipping",
                        full_id, variant_num,
                    )
                    continue

                yield _build_entry(
                    spec_id=full_id,
                    variant_num=variant_num,
                    subtlety=dir_subtlety,
                    base_cou=dir_base_cou,
                    jsonld_path=jsonld_path,
                    row=row,
                )


def _build_entry(
    *,
    spec_id: str,
    variant_num: int,
    subtlety: str,
    base_cou: str,
    jsonld_path: Path,
    row: dict[str, str],
) -> _Entry:
    """Construct a bundle entry from a jsonld file + outcomes.csv row."""
    raw_class = row["outcome_class"]
    if raw_class not in NORMALIZE:
        raise BundleWriteError(
            f"unknown outcome_class {raw_class!r} on {spec_id} v{variant_num}; "
            f"add to NORMALIZE map in bundle_writer.py"
        )
    normalized_class = NORMALIZE[raw_class]

    # case_id encodes the FULL spec_id (which already includes the
    # subtlety+base_cou suffix when overrides are applied) + variant.
    # The pair (full spec_id, variant_num) is the row key in outcomes.csv,
    # so this is naturally unique.
    case_id = f"{spec_id}-v{variant_num:02d}"

    rules_fired = [
        r.strip() for r in (row.get("rules_fired") or "").split(",") if r.strip()
    ]

    outcome = {
        "case_id": case_id,
        "coverage_class": normalized_class,
        "phase2_outcome_class_raw": raw_class,
        "expected_rule": row.get("target_weakener") or None,
        "rules_fired": rules_fired,
        "target_rule_fired": row.get("target_rule_fired") in ("True", "true", "1"),
        "source_taxonomy": row.get("source_taxonomy") or None,
        "section_6_7_mapping": row.get("section_6_7_candidate") or None,
        "experimental_factors": {
            "subtlety_level": subtlety or None,
            "base_cou": base_cou or None,
            "coverage_intent": row.get("coverage_intent"),
        },
        "phase2_metadata": {
            "shacl_retries": int(row.get("shacl_retries") or 0),
            "tokens": int(row.get("tokens") or 0),
            "cost_usd": float(row.get("cost_usd") or 0.0),
        },
    }

    return _Entry(
        case_id=case_id,
        package_text=jsonld_path.read_text(),
        outcome_dict=outcome,
    )


# ── tar utilities ───────────────────────────────────────────────────────


def _add_member(tf: tarfile.TarFile, name: str, payload: str) -> None:
    data = payload.encode("utf-8")
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    tf.addfile(info, BytesIO(data))


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
