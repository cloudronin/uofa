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


def test_view4_per_rule_precision_renders_with_fpr_drivers_first(tmp_path):
    """M5-B: View 4 ranks rules by NC FPR descending so the worst FPR
    contributors surface at the top of the table."""
    rows = [
        # W-FPR-HIGH: fires on every NC, never targeted → high NC FPR
        _row(coverage_intent="negative_control", target_weakener=None,
             rules_fired="W-FPR-HIGH", outcome_class="COV-CLEAN-WRONG"),
        _row(coverage_intent="negative_control", target_weakener=None,
             rules_fired="W-FPR-HIGH", outcome_class="COV-CLEAN-WRONG"),
        # W-CLEAN: never fires on NC, targeted+fires on confirm
        _row(coverage_intent="negative_control", target_weakener=None,
             rules_fired="", outcome_class="COV-CLEAN-CORRECT"),
        _row(coverage_intent="confirm_existing", target_weakener="W-CLEAN",
             rules_fired="W-CLEAN", target_rule_fired=True,
             outcome_class="COV-HIT"),
    ]
    out = tmp_path / "index.html"
    write_html_report(rows, out)
    html = out.read_text()
    # View 4 section + rules present
    assert "View 4 — Per-rule precision" in html
    assert "W-FPR-HIGH" in html
    assert "W-CLEAN" in html
    # Scope the ordering check to inside View 4's section, since
    # W-CLEAN also appears in View 1 as a confirm_existing target.
    # Use the H2 anchor (not the nav link) so we skip past View 1.
    view4_start = html.find("<h2 id='view4'>")
    view4_section = html[view4_start:]
    fpr_high_pos = view4_section.find("W-FPR-HIGH")
    clean_pos = view4_section.find("W-CLEAN")
    assert fpr_high_pos != -1 and clean_pos != -1
    # W-FPR-HIGH should appear BEFORE W-CLEAN in View 4 (sorted by FPR desc)
    assert fpr_high_pos < clean_pos
    # FPR cell coloring: W-FPR-HIGH should get cell-miss (FPR >= 50%)
    fpr_high_row = view4_section[fpr_high_pos:view4_section.find("</tr>", fpr_high_pos)]
    assert "cell-miss" in fpr_high_row  # high-FPR red coloring


def test_view1_renders_not_measurable_for_all_gen_invalid_cell(tmp_path):
    """View 1 catalog × subtlety pivot: a (pattern, subtlety) cell where
    every confirm_existing row is GEN-INVALID renders as 'not measurable'
    rather than '0%'. The rules never had a chance to fire."""
    rows = [
        # 3 GEN-INVALID rows for W-ON-01 at low subtlety
        _row(coverage_intent="confirm_existing", target_weakener="W-ON-01",
             subtlety="low", outcome_class="GEN-INVALID"),
        _row(coverage_intent="confirm_existing", target_weakener="W-ON-01",
             subtlety="low", outcome_class="GEN-INVALID"),
        _row(coverage_intent="confirm_existing", target_weakener="W-ON-01",
             subtlety="low", outcome_class="GEN-INVALID"),
        # Plus a healthy W-AR-01 high cell to keep the pivot non-empty
        _row(coverage_intent="confirm_existing", target_weakener="W-AR-01",
             subtlety="high", outcome_class="COV-HIT"),
    ]
    out = tmp_path / "index.html"
    write_html_report(rows, out)
    html = out.read_text()
    # Sentinel + CSS class present
    assert "not measurable" in html
    assert "cell-not-measurable" in html
    # Should NOT show "0%" or "0/3" for the W-ON-01 low cell
    # (other cells may legitimately show 0% — we only care about the W-ON-01 cell)
    # The W-ON-01 row should contain the not-measurable sentinel
    war01_row_start = html.find("W-AR-01")
    won01_row_start = html.find("W-ON-01")
    # W-ON-01 row should mention "not measurable" somewhere within its row scope
    # (between W-ON-01 mention and the next </tr>)
    won01_row = html[won01_row_start:html.find("</tr>", won01_row_start)]
    assert "not measurable" in won01_row


def test_view3_metrics_exclude_gen_invalid_from_denominators(tmp_path):
    """GEN-INVALID rows must NOT inflate any of the three View 3 denominators.

    Smoke evidence: SMOKE-suite-p3 had 18 confirm_existing rows where 3 were
    GEN-INVALID (p2 refusal). Pre-fix recall = 15/18 = 83.3%. Post-fix recall
    must be 15/15 = 100%.
    """
    rows = [
        # 2 evaluable confirm_existing rows, both hit
        _row(coverage_intent="confirm_existing", outcome_class="COV-HIT"),
        _row(coverage_intent="confirm_existing", outcome_class="COV-HIT-PLUS"),
        # 1 GEN-INVALID — must be excluded from confirm_total
        _row(coverage_intent="confirm_existing", outcome_class="GEN-INVALID"),
        # 1 evaluable NC, no firings → CLEAN-CORRECT
        _row(coverage_intent="negative_control", target_weakener=None,
             outcome_class="COV-CLEAN-CORRECT"),
        # 1 GEN-INVALID NC — must be excluded from nc_total
        _row(coverage_intent="negative_control", target_weakener=None,
             outcome_class="GEN-INVALID"),
        # 1 evaluable gap_probe, miss
        _row(coverage_intent="gap_probe", target_weakener=None,
             source_taxonomy="gohar/evidence_validity/data-drift",
             outcome_class="COV-MISS"),
        # 1 GEN-INVALID gap_probe — must be excluded from gp_total
        _row(coverage_intent="gap_probe", target_weakener=None,
             source_taxonomy="gohar/evidence_validity/data-drift",
             outcome_class="GEN-INVALID"),
    ]
    out = tmp_path / "index.html"
    write_html_report(rows, out)
    html = out.read_text()
    # Catalog recall: 2 hits / 2 evaluable = 100% (NOT 66.7%)
    assert "100.0%" in html
    # confirm_existing (n=2) — denominator excludes GEN-INVALID (was n=3)
    assert "n=2" in html
    # negative_controls (n=1) — denominator excludes GEN-INVALID (was n=2)
    # gap_probe (n=1) — denominator excludes GEN-INVALID (was n=2)
    assert html.count("n=1") >= 2


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
