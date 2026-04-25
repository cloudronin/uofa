"""Tests for the HTML reporter — Phase 2 §11."""

from __future__ import annotations

from pathlib import Path

from uofa_cli.adversarial.classifier import _OutcomeRow
from uofa_cli.adversarial.reporter import write_html_report


def _row(**overrides):
    base = dict(
        spec_id="test",
        variant_num=1,
        target_weakener="W-AR-01",
        source_taxonomy=None,
        coverage_intent="confirm_existing",
        subtlety="high",
        outcome_class="COV-HIT",
        rules_fired="W-AR-01",
        target_rule_fired=True,
        baseline_firings_count=None,
        baseline_firings_minus_target=None,
        section_6_7_candidate=None,
        shacl_retries=0,
        tokens=100,
        cost_usd=0.01,
    )
    base.update(overrides)
    return _OutcomeRow(**base)


def test_write_html_report_creates_file_with_three_views(tmp_path):
    rows = [
        _row(target_weakener="W-AR-01", outcome_class="COV-HIT"),
        _row(target_weakener="W-EP-01", outcome_class="COV-MISS"),
        _row(coverage_intent="gap_probe", target_weakener=None,
             source_taxonomy="gohar/evidence_validity/data-drift",
             outcome_class="COV-MISS"),
        _row(coverage_intent="negative_control", target_weakener=None,
             outcome_class="COV-CLEAN-CORRECT"),
    ]
    out_path = tmp_path / "index.html"
    write_html_report(rows, out_path)
    assert out_path.exists()
    html = out_path.read_text()
    # All three view headers present
    assert "View 1" in html
    assert "View 2" in html
    assert "View 3" in html
    # Cell coloring legend
    assert "cell-hit" in html
    assert "cell-miss" in html


def test_view2_red_cell_for_gap_probe_miss(tmp_path):
    rows = [
        _row(coverage_intent="gap_probe", target_weakener=None,
             source_taxonomy="gohar/evidence_validity/data-drift",
             outcome_class="COV-MISS"),
    ]
    out = tmp_path / "index.html"
    write_html_report(rows, out)
    html = out.read_text()
    # gap_probe MISS verdict should render in cell-miss styling
    assert "cell-miss" in html
    assert "open gap" in html


def test_view2_green_cell_for_gap_probe_hit(tmp_path):
    rows = [
        _row(coverage_intent="gap_probe", target_weakener=None,
             source_taxonomy="gohar/evidence_validity/data-drift",
             outcome_class="COV-HIT"),
    ]
    out = tmp_path / "index.html"
    write_html_report(rows, out)
    html = out.read_text()
    assert "covered" in html


def test_view3_metrics_match_input(tmp_path):
    rows = [
        _row(coverage_intent="confirm_existing", outcome_class="COV-HIT"),
        _row(coverage_intent="confirm_existing", outcome_class="COV-HIT"),
        _row(coverage_intent="confirm_existing", outcome_class="COV-MISS"),
        _row(coverage_intent="negative_control", target_weakener=None,
             outcome_class="COV-CLEAN-CORRECT"),
        _row(coverage_intent="negative_control", target_weakener=None,
             outcome_class="COV-CLEAN-WRONG"),
    ]
    out = tmp_path / "index.html"
    write_html_report(rows, out)
    html = out.read_text()
    # 2/3 confirm_existing hit rate ~= 66.7%
    assert "66.7%" in html or "67%" in html
    # FPR = 1/2 → precision = 50%
    assert "50.0%" in html or "50%" in html


def test_write_html_report_with_no_rows(tmp_path):
    """Empty input should not crash; report should render placeholder text."""
    out = tmp_path / "index.html"
    write_html_report([], out)
    assert out.exists()
    html = out.read_text()
    assert "No confirm_existing rows" in html
    assert "No gap_probe rows" in html


# ----- D1: View 1 per-COU additions (v1.8) -----


def _row_with_cou(base_cou_key, **overrides):
    overrides["base_cou_key"] = base_cou_key
    return _row(**overrides)


def test_view1_cou_dependent_header_when_no_disparity(tmp_path):
    """When no rule is COU-dependent, header row reads the spec sentinel."""
    rows = [
        _row_with_cou("morrison/cou1", target_weakener="W-AR-01", outcome_class="COV-HIT"),
        _row_with_cou("morrison/cou2", target_weakener="W-AR-01", outcome_class="COV-HIT"),
        _row_with_cou("nagaraja/cou1", target_weakener="W-AR-01", outcome_class="COV-HIT"),
    ]
    out = tmp_path / "index.html"
    write_html_report(rows, out)
    html = out.read_text()
    assert "COU-dependent rules" in html
    assert "No rules show COU-dependent firing behavior at the 30% disparity threshold." in html


def test_view1_cou_dependent_header_lists_disparity_pattern(tmp_path):
    """When a pattern has ≥30% disparity, it appears in the header row."""
    rows = [
        # W-EP-01: 100% on COU1, 0% on Nagaraja → 100% disparity
        _row_with_cou("morrison/cou1", target_weakener="W-EP-01", outcome_class="COV-HIT"),
        _row_with_cou("nagaraja/cou1", target_weakener="W-EP-01", outcome_class="COV-MISS"),
    ]
    out = tmp_path / "index.html"
    write_html_report(rows, out)
    html = out.read_text()
    # Header row mentions W-EP-01
    assert "<strong>COU-dependent rules:</strong>" in html
    assert "W-EP-01" in html


def test_view1_per_cou_collapsible_rendered_per_pattern(tmp_path):
    """Each pattern row gets a <details> per-COU breakdown."""
    rows = [
        _row_with_cou("morrison/cou1", target_weakener="W-AR-01", outcome_class="COV-HIT"),
    ]
    out = tmp_path / "index.html"
    write_html_report(rows, out)
    html = out.read_text()
    assert "<details>" in html
    assert "<summary>" in html
    assert "Morrison COU1" in html  # COU label appears in the details list


# ----- D2: performance characterization appendix (v1.8 §11.2) -----


def test_perf_appendix_renders_when_timing_present(tmp_path):
    """Perf appendix shows mean/median/p95 when total_eval_ms is populated."""
    rows = [_row(target_weakener="W-AR-01", outcome_class="COV-HIT")]
    rows[0].total_eval_ms = 1500
    rows[0].eval_host_id = "test-host"
    out = tmp_path / "index.html"
    write_html_report(rows, out)
    html = out.read_text()
    assert "Performance characterization" in html
    assert "Mean total_eval_ms" in html
    assert "Median total_eval_ms" in html
    assert "p95 total_eval_ms" in html


def test_perf_appendix_handles_no_timing_data(tmp_path):
    """When all total_eval_ms = 0, perf appendix renders the placeholder."""
    rows = [_row(target_weakener="W-AR-01", outcome_class="COV-HIT")]
    rows[0].total_eval_ms = 0
    out = tmp_path / "index.html"
    write_html_report(rows, out)
    html = out.read_text()
    assert "No per-package timing data captured" in html


def test_perf_appendix_uses_uofa_hw_spec_env_var(tmp_path, monkeypatch):
    """UOFA_HW_SPEC env var threads into the perf appendix header."""
    monkeypatch.setenv("UOFA_HW_SPEC", "Apple M4 Pro 24-core 36GB")
    rows = [_row(target_weakener="W-AR-01", outcome_class="COV-HIT")]
    rows[0].total_eval_ms = 100
    out = tmp_path / "index.html"
    write_html_report(rows, out)
    html = out.read_text()
    assert "Apple M4 Pro 24-core 36GB" in html
