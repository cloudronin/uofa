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
