"""Tests for the outcome classifier — Phase 2 §10."""

from __future__ import annotations

from uofa_cli.adversarial.classifier import (
    _build_matrix,
    _classify,
    _detect_baseline_key,
    _OutcomeRow,
    _parse_rule_firings_from_check,
    _subtract_baseline,
    BASELINE_FIRINGS,
)


# ----- _classify outcome-class tests -----


def _row(intent, target=None, source=None):
    """Helper: minimal kwargs for _classify."""
    return dict(coverage_intent=intent, target_weakener=target, source_taxonomy=source)


def test_classify_confirm_existing_hit():
    cls, fired = _classify(
        coverage_intent="confirm_existing",
        target_weakener="W-AR-01",
        firings_minus_baseline={"W-AR-01": 1},
        package_exists=True,
    )
    assert cls == "COV-HIT"
    assert fired is True


def test_classify_confirm_existing_hit_plus():
    cls, fired = _classify(
        coverage_intent="confirm_existing",
        target_weakener="W-AR-01",
        firings_minus_baseline={"W-AR-01": 1, "W-AL-01": 1},
        package_exists=True,
    )
    assert cls == "COV-HIT-PLUS"
    assert fired is True


def test_classify_confirm_existing_miss():
    cls, fired = _classify(
        coverage_intent="confirm_existing",
        target_weakener="W-AR-01",
        firings_minus_baseline={},
        package_exists=True,
    )
    assert cls == "COV-MISS"
    assert fired is False


def test_classify_confirm_existing_wrong():
    cls, fired = _classify(
        coverage_intent="confirm_existing",
        target_weakener="W-AR-01",
        firings_minus_baseline={"W-EP-01": 1},
        package_exists=True,
    )
    assert cls == "COV-WRONG"
    assert fired is False


def test_classify_gap_probe_miss():
    cls, _ = _classify(
        coverage_intent="gap_probe",
        target_weakener=None,
        firings_minus_baseline={},
        package_exists=True,
    )
    assert cls == "COV-MISS"


def test_classify_gap_probe_wrong():
    cls, _ = _classify(
        coverage_intent="gap_probe",
        target_weakener=None,
        firings_minus_baseline={"W-CON-03": 1},
        package_exists=True,
    )
    assert cls == "COV-WRONG"


def test_classify_negative_control_correct():
    cls, _ = _classify(
        coverage_intent="negative_control",
        target_weakener=None,
        firings_minus_baseline={},
        package_exists=True,
    )
    assert cls == "COV-CLEAN-CORRECT"


def test_classify_negative_control_wrong():
    cls, _ = _classify(
        coverage_intent="negative_control",
        target_weakener=None,
        firings_minus_baseline={"W-AR-05": 1},
        package_exists=True,
    )
    assert cls == "COV-CLEAN-WRONG"


def test_classify_gen_invalid():
    cls, _ = _classify(
        coverage_intent="confirm_existing",
        target_weakener="W-AR-01",
        firings_minus_baseline={},
        package_exists=False,
    )
    assert cls == "GEN-INVALID"


# ----- _parse_rule_firings_from_check -----


def test_parse_rule_firings_from_check_extracts_pattern_and_count():
    sample = """
    ══════════════════════════════════════════════════════════════
      SUMMARY: 5 weakener(s) detected
      ⚡ COMPOUND-01 [Critical] — 2 hit(s)
          → affected: cou1
      ⚠ W-AR-05 [High] — 3 hit(s)
          → affected: cou1
    """
    firings = _parse_rule_firings_from_check(sample)
    assert firings == {"COMPOUND-01": 2, "W-AR-05": 3}


def test_parse_rule_firings_handles_empty_output():
    assert _parse_rule_firings_from_check("") == {}


# ----- _detect_baseline_key -----


def test_detect_baseline_morrison_cou1():
    assert _detect_baseline_key("packs/vv40/examples/morrison/cou1") == "morrison/cou1"


def test_detect_baseline_morrison_cou2():
    assert _detect_baseline_key("/abs/path/morrison/cou2/uofa.jsonld") == "morrison/cou2"


def test_detect_baseline_nagaraja():
    assert _detect_baseline_key("packs/vv40/examples/nagaraja/cou1") == "nagaraja/cou1"


def test_detect_baseline_unknown_returns_none():
    assert _detect_baseline_key("packs/vv40/examples/unknown/cou1") is None
    assert _detect_baseline_key(None) is None


def test_baseline_firings_constants():
    """Baseline values must match Phase 2 Spec v1.7 §3.1."""
    assert BASELINE_FIRINGS["morrison/cou1"] == 24
    assert BASELINE_FIRINGS["morrison/cou2"] == 18
    assert BASELINE_FIRINGS["nagaraja/cou1"] == 32


# ----- _subtract_baseline -----


def test_subtract_baseline_full_baseline_clears_firings():
    """If observed firings == baseline, subtraction yields empty dict."""
    firings = {"W-AR-05": 3, "W-AL-01": 3, "COMPOUND-01": 2}
    assert _subtract_baseline(firings, baseline_count=8) == {}


def test_subtract_baseline_excess_firings_preserved():
    """If observed > baseline, some firings remain as positive counts.

    Conservative proportional subtraction rounds each pattern's deduction;
    the post-subtraction total is approximately observed - baseline (give
    or take rounding) but every original pattern still has a positive
    count.
    """
    firings = {"W-AR-05": 3, "W-AL-01": 3, "W-EP-01": 4}  # total 10
    out = _subtract_baseline(firings, baseline_count=5)
    assert all(v >= 0 for v in out.values())
    # Every input pattern with non-trivial count survives subtraction.
    assert set(out.keys()) == set(firings.keys())
    # Approximate total: between zero and original total, strictly less.
    assert sum(out.values()) < sum(firings.values())


def test_subtract_baseline_no_baseline_returns_input():
    firings = {"W-AR-05": 1}
    assert _subtract_baseline(firings, baseline_count=None) == firings


# ----- _build_matrix -----


def _row_obj(**overrides):
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


def test_build_matrix_aggregates_hit_rate():
    rows = [
        _row_obj(target_weakener="W-AR-01", subtlety="high", outcome_class="COV-HIT"),
        _row_obj(target_weakener="W-AR-01", subtlety="high", outcome_class="COV-HIT-PLUS"),
        _row_obj(target_weakener="W-AR-01", subtlety="high", outcome_class="COV-MISS"),
        _row_obj(target_weakener="W-EP-01", subtlety="low", outcome_class="COV-MISS"),
    ]
    pivot = _build_matrix(rows)
    assert pivot[("W-AR-01", "high")] == {"hit": 2, "total": 3}
    assert pivot[("W-EP-01", "low")] == {"hit": 0, "total": 1}


def test_build_matrix_excludes_non_confirm_existing():
    """gap_probe / negative_control rows must not contribute to catalog matrix."""
    rows = [
        _row_obj(coverage_intent="gap_probe", target_weakener=None,
                 source_taxonomy="gohar/evidence_validity/data-drift"),
        _row_obj(coverage_intent="negative_control", target_weakener=None),
    ]
    pivot = _build_matrix(rows)
    assert pivot == {}
