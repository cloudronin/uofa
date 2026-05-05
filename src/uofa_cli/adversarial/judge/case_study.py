"""Wave K: case-study re-run + delta table (spec v1.6 §13.3).

Compares two catalog versions (typically v0.4.1 vs v0.5 with the new
proposed rules from Wave J) against the published case-study COUs:

  - Morrison COU1 / COU2  (CFD-based hemolysis assessment)
  - Nagaraja COU1         (centrifugal pump VAD)

For each (catalog × COU) pair we compute:
  - count of WeakenerAnnotations fired
  - per-pattern firings
  - delta table (catalog A vs catalog B)

The runner shells out to `uofa rules` for each catalog × COU pair.
Tier A: this module is structured around a `RuleEngineFn` callable so
tests inject a deterministic stub; the real path uses `subprocess.run`.

Output: a markdown table at `delta_table.md` per spec §13.3 plus a
machine-readable `delta_table.json` for downstream tooling.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, Sequence


@dataclass(frozen=True)
class CatalogRun:
    """One (catalog × COU) rule-engine result."""

    catalog: str
    cou: str
    annotation_count: int
    per_pattern_firings: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class DeltaRow:
    """One row of the delta table: a single COU compared across catalogs."""

    cou: str
    catalog_a: str
    catalog_b: str
    count_a: int
    count_b: int
    delta: int
    new_patterns_in_b: list[str] = field(default_factory=list)


# Type alias for the rule-engine seam (production: shells out to
# `uofa rules`; tests inject a stub).
RuleEngineFn = Callable[[str, str], CatalogRun]


def _default_rule_engine(catalog: str, cou: str) -> CatalogRun:
    """Default rule engine: shells out to `uofa rules` and parses the output."""
    # The `uofa rules` CLI prints a JSON summary when invoked with --json.
    # The exact CLI surface varies by version; this default targets v0.5.
    cmd = ["uofa", "rules", "--catalog", catalog, "--cou", cou, "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(proc.stdout)
    return CatalogRun(
        catalog=catalog,
        cou=cou,
        annotation_count=int(data.get("annotation_count", 0)),
        per_pattern_firings=dict(data.get("per_pattern_firings", {})),
    )


def run_case_study(
    *,
    catalogs: Sequence[str],
    cous: Sequence[str],
    rule_engine: RuleEngineFn | None = None,
) -> list[CatalogRun]:
    """Run the rule engine for every (catalog × COU) pair."""
    rule_engine = rule_engine or _default_rule_engine
    runs: list[CatalogRun] = []
    for catalog in catalogs:
        for cou in cous:
            runs.append(rule_engine(catalog, cou))
    return runs


def compute_delta_rows(
    runs: Sequence[CatalogRun],
    *,
    catalog_a: str,
    catalog_b: str,
) -> list[DeltaRow]:
    """Pair runs by COU and compute per-COU deltas A vs B."""
    runs_by_cou_catalog: dict[tuple[str, str], CatalogRun] = {
        (r.cou, r.catalog): r for r in runs
    }
    cous = sorted({r.cou for r in runs})
    rows: list[DeltaRow] = []
    for cou in cous:
        ra = runs_by_cou_catalog.get((cou, catalog_a))
        rb = runs_by_cou_catalog.get((cou, catalog_b))
        if ra is None or rb is None:
            continue
        new_patterns = sorted(
            set(rb.per_pattern_firings) - set(ra.per_pattern_firings)
        )
        rows.append(DeltaRow(
            cou=cou,
            catalog_a=catalog_a,
            catalog_b=catalog_b,
            count_a=ra.annotation_count,
            count_b=rb.annotation_count,
            delta=rb.annotation_count - ra.annotation_count,
            new_patterns_in_b=new_patterns,
        ))
    return rows


def render_delta_table_markdown(
    rows: Sequence[DeltaRow],
    *,
    title: str = "v0.5 vs v0.4.1 Case-Study Delta Table",
) -> str:
    """Render rows as a markdown table per spec §13.3."""
    out: list[str] = [
        f"# {title}",
        "",
        "| COU | catalog A | catalog B | count A | count B | Δ | new patterns in B |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for r in rows:
        new = ", ".join(r.new_patterns_in_b) if r.new_patterns_in_b else "—"
        sign = "+" if r.delta > 0 else ""
        out.append(
            f"| {r.cou} | {r.catalog_a} | {r.catalog_b} | "
            f"{r.count_a} | {r.count_b} | {sign}{r.delta} | {new} |"
        )
    out.append("")
    return "\n".join(out)


def render_delta_table_json(rows: Sequence[DeltaRow]) -> str:
    """Render rows as a machine-readable JSON document."""
    return json.dumps([
        {
            "cou": r.cou,
            "catalog_a": r.catalog_a,
            "catalog_b": r.catalog_b,
            "count_a": r.count_a,
            "count_b": r.count_b,
            "delta": r.delta,
            "new_patterns_in_b": list(r.new_patterns_in_b),
        }
        for r in rows
    ], indent=2)


def write_delta_artifacts(
    rows: Sequence[DeltaRow],
    out_dir: Path,
    *,
    catalog_a: str,
    catalog_b: str,
) -> dict[str, Path]:
    """Persist delta_table.md + delta_table.json."""
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "delta_table.md"
    json_path = out_dir / "delta_table.json"
    md_path.write_text(render_delta_table_markdown(
        rows,
        title=f"{catalog_b} vs {catalog_a} Case-Study Delta Table",
    ))
    json_path.write_text(render_delta_table_json(rows))
    return {"markdown": md_path, "json": json_path}
