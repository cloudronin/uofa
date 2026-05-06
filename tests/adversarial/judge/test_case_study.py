"""Tests for Wave K: case-study delta table."""

from __future__ import annotations

import json
from pathlib import Path

from uofa_cli.adversarial.judge.case_study import (
    CatalogRun,
    DeltaRow,
    compute_delta_rows,
    render_delta_table_json,
    render_delta_table_markdown,
    run_case_study,
    write_delta_artifacts,
)


# ── run_case_study with stub rule engine ───────────────────────────────


def _stub_engine(catalog: str, cou: str) -> CatalogRun:
    """Deterministic stub mapping (catalog, cou) → counts.

    Pattern designed so v0.5 introduces W-EV-01 firings on Morrison COU2.
    """
    table = {
        ("v0.4.1", "morrison-cou1"): CatalogRun(
            catalog="v0.4.1", cou="morrison-cou1", annotation_count=2,
            per_pattern_firings={"W-EP-01": 2},
        ),
        ("v0.4.1", "morrison-cou2"): CatalogRun(
            catalog="v0.4.1", cou="morrison-cou2", annotation_count=1,
            per_pattern_firings={"W-EP-01": 1},
        ),
        ("v0.4.1", "nagaraja-cou1"): CatalogRun(
            catalog="v0.4.1", cou="nagaraja-cou1", annotation_count=0,
            per_pattern_firings={},
        ),
        ("v0.5", "morrison-cou1"): CatalogRun(
            catalog="v0.5", cou="morrison-cou1", annotation_count=3,
            per_pattern_firings={"W-EP-01": 2, "W-CX-01": 1},
        ),
        ("v0.5", "morrison-cou2"): CatalogRun(
            catalog="v0.5", cou="morrison-cou2", annotation_count=3,
            per_pattern_firings={"W-EP-01": 1, "W-EV-01": 2},
        ),
        ("v0.5", "nagaraja-cou1"): CatalogRun(
            catalog="v0.5", cou="nagaraja-cou1", annotation_count=1,
            per_pattern_firings={"W-AR-06": 1},
        ),
    }
    return table[(catalog, cou)]


class TestRunCaseStudy:
    def test_matrix_runs(self) -> None:
        runs = run_case_study(
            catalogs=["v0.4.1", "v0.5"],
            cous=["morrison-cou1", "morrison-cou2", "nagaraja-cou1"],
            rule_engine=_stub_engine,
        )
        assert len(runs) == 6


class TestComputeDeltaRows:
    def test_per_cou_delta(self) -> None:
        runs = run_case_study(
            catalogs=["v0.4.1", "v0.5"],
            cous=["morrison-cou1", "morrison-cou2", "nagaraja-cou1"],
            rule_engine=_stub_engine,
        )
        rows = compute_delta_rows(runs, catalog_a="v0.4.1", catalog_b="v0.5")
        assert len(rows) == 3
        by_cou = {r.cou: r for r in rows}
        # morrison-cou1: 2 → 3 (W-CX-01 added)
        assert by_cou["morrison-cou1"].delta == 1
        assert by_cou["morrison-cou1"].new_patterns_in_b == ["W-CX-01"]
        # morrison-cou2: 1 → 3 (W-EV-01 added; previously zero)
        assert by_cou["morrison-cou2"].delta == 2
        assert "W-EV-01" in by_cou["morrison-cou2"].new_patterns_in_b
        # nagaraja-cou1: 0 → 1 (W-AR-06 added)
        assert by_cou["nagaraja-cou1"].delta == 1
        assert by_cou["nagaraja-cou1"].new_patterns_in_b == ["W-AR-06"]


class TestRendering:
    def test_markdown_table_has_expected_columns(self) -> None:
        rows = [
            DeltaRow(
                cou="morrison-cou1", catalog_a="v0.4.1", catalog_b="v0.5",
                count_a=2, count_b=3, delta=1,
                new_patterns_in_b=["W-CX-01"],
            ),
        ]
        md = render_delta_table_markdown(rows)
        assert "morrison-cou1" in md
        assert "v0.4.1" in md
        assert "v0.5" in md
        assert "+1" in md
        assert "W-CX-01" in md
        # Header row.
        assert "| COU |" in md

    def test_markdown_dash_for_no_new_patterns(self) -> None:
        rows = [
            DeltaRow(
                cou="x", catalog_a="a", catalog_b="b",
                count_a=0, count_b=0, delta=0,
            ),
        ]
        md = render_delta_table_markdown(rows)
        assert "| — |" in md

    def test_json_is_valid(self) -> None:
        rows = [
            DeltaRow(
                cou="x", catalog_a="a", catalog_b="b",
                count_a=1, count_b=2, delta=1, new_patterns_in_b=["W"],
            ),
        ]
        data = json.loads(render_delta_table_json(rows))
        assert data[0]["cou"] == "x"
        assert data[0]["delta"] == 1


class TestWriteDeltaArtifacts:
    def test_writes_md_and_json(self, tmp_path: Path) -> None:
        runs = run_case_study(
            catalogs=["v0.4.1", "v0.5"],
            cous=["morrison-cou1"],
            rule_engine=_stub_engine,
        )
        rows = compute_delta_rows(runs, catalog_a="v0.4.1", catalog_b="v0.5")
        paths = write_delta_artifacts(
            rows, tmp_path, catalog_a="v0.4.1", catalog_b="v0.5"
        )
        assert paths["markdown"].exists()
        assert paths["json"].exists()
        # Markdown title reflects the comparison direction.
        assert "v0.5 vs v0.4.1" in paths["markdown"].read_text()
