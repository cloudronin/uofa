"""Tests for the outcome classifier — Phase 2 §10."""

from __future__ import annotations

import csv

from uofa_cli.adversarial.classifier import (
    _build_matrix,
    _CORE_PATTERN_IDS,
    _classify,
    _detect_baseline_key,
    _OutcomeRow,
    _parse_rule_firings_from_check,
    _split_rules_fired,
    _subtract_baseline,
    _write_summary_csv,
    BASELINE_FIRINGS,
    SUMMARY_FIELDS,
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


# ----- summary.csv per-pattern schema (M4 cleanup) -----


def test_core_pattern_ids_count_is_23():
    """Spec §13.1 gate #9 / cleanup spec: summary.csv must have exactly
    23 rows — one per shipped active core pattern at v0.5.4."""
    assert len(_CORE_PATTERN_IDS) == 23
    # Spot-check a few canonical IDs for typo resistance.
    assert "W-AR-05" in _CORE_PATTERN_IDS
    assert "W-PROV-01" in _CORE_PATTERN_IDS
    assert "COMPOUND-01" in _CORE_PATTERN_IDS
    assert "COMPOUND-03" in _CORE_PATTERN_IDS
    # COMPOUND-02 is commented out in the rules file, so excluded.
    assert "COMPOUND-02" not in _CORE_PATTERN_IDS


def test_summary_fields_match_cleanup_spec_plus_d1():
    """First 7 fields per M4 cleanup spec; last 6 per Phase 2 §10.4 D1 (v1.8)."""
    assert SUMMARY_FIELDS == (
        "pattern_id",
        "confirm_existing_count",
        "confirm_existing_hits",
        "recall",
        "negative_control_firings",
        "gap_probe_firings",
        "total_firings_across_battery",
        "recall_morrison_cou1",
        "recall_morrison_cou2",
        "recall_nagaraja",
        "recall_min_per_cou",
        "recall_cou_disparity",
        "cou_dependent_flag",
    )


def test_split_rules_fired_handles_empty_and_comma_separated():
    assert _split_rules_fired("") == set()
    assert _split_rules_fired("W-AR-05") == {"W-AR-05"}
    assert _split_rules_fired("W-AR-05,W-AL-01,COMPOUND-01") == {
        "W-AR-05", "W-AL-01", "COMPOUND-01"
    }
    # Tolerates whitespace
    assert _split_rules_fired("W-AR-05, W-AL-01") == {"W-AR-05", "W-AL-01"}


def test_write_summary_csv_emits_23_rows_and_correct_schema(tmp_path):
    rows = [
        _row_obj(coverage_intent="confirm_existing", target_weakener="W-AR-01",
                 outcome_class="COV-HIT", rules_fired="W-AR-01",
                 target_rule_fired=True),
        _row_obj(coverage_intent="confirm_existing", target_weakener="W-AR-01",
                 outcome_class="COV-MISS", rules_fired="",
                 target_rule_fired=False),
        _row_obj(coverage_intent="confirm_existing", target_weakener="W-EP-01",
                 outcome_class="COV-HIT-PLUS", rules_fired="W-EP-01,W-AL-01",
                 target_rule_fired=True),
    ]
    out = tmp_path / "summary.csv"
    _write_summary_csv(rows, out)

    with open(out) as f:
        reader = csv.DictReader(f)
        loaded = list(reader)

    # Schema
    assert tuple(reader.fieldnames or ()) == SUMMARY_FIELDS
    # Exactly 23 rows
    assert len(loaded) == 23
    # All 23 patterns appear, in registry order
    assert [r["pattern_id"] for r in loaded] == list(_CORE_PATTERN_IDS)


def test_write_summary_csv_aggregates_confirm_existing(tmp_path):
    """confirm_existing_count / hits / recall aggregate per target pattern."""
    rows = [
        _row_obj(coverage_intent="confirm_existing", target_weakener="W-AR-01",
                 rules_fired="W-AR-01", target_rule_fired=True),
        _row_obj(coverage_intent="confirm_existing", target_weakener="W-AR-01",
                 rules_fired="", target_rule_fired=False),
        _row_obj(coverage_intent="confirm_existing", target_weakener="W-AR-01",
                 rules_fired="W-AR-01", target_rule_fired=True),
    ]
    out = tmp_path / "summary.csv"
    _write_summary_csv(rows, out)
    by_pat = {r["pattern_id"]: r for r in csv.DictReader(open(out))}

    war01 = by_pat["W-AR-01"]
    assert war01["confirm_existing_count"] == "3"
    assert war01["confirm_existing_hits"] == "2"
    assert war01["recall"] == "0.667"


def test_write_summary_csv_recall_empty_when_no_attempts(tmp_path):
    rows = []
    out = tmp_path / "summary.csv"
    _write_summary_csv(rows, out)
    by_pat = {r["pattern_id"]: r for r in csv.DictReader(open(out))}

    # Every pattern has zero attempts; recall is the empty string per spec.
    for pat in _CORE_PATTERN_IDS:
        assert by_pat[pat]["confirm_existing_count"] == "0"
        assert by_pat[pat]["recall"] == ""


def test_write_summary_csv_aggregates_negative_control_and_gap_probe(tmp_path):
    rows = [
        # NC fires W-AR-05 (precision bug)
        _row_obj(coverage_intent="negative_control", target_weakener=None,
                 rules_fired="W-AR-05", target_rule_fired=False,
                 outcome_class="COV-CLEAN-WRONG"),
        # NC clean
        _row_obj(coverage_intent="negative_control", target_weakener=None,
                 rules_fired="", target_rule_fired=False,
                 outcome_class="COV-CLEAN-CORRECT"),
        # gap_probe fires W-CON-03 (informative)
        _row_obj(coverage_intent="gap_probe", target_weakener=None,
                 rules_fired="W-CON-03", target_rule_fired=False,
                 outcome_class="COV-WRONG"),
        # gap_probe also fires W-CON-03
        _row_obj(coverage_intent="gap_probe", target_weakener=None,
                 rules_fired="W-CON-03", target_rule_fired=False,
                 outcome_class="COV-WRONG"),
    ]
    out = tmp_path / "summary.csv"
    _write_summary_csv(rows, out)
    by_pat = {r["pattern_id"]: r for r in csv.DictReader(open(out))}

    assert by_pat["W-AR-05"]["negative_control_firings"] == "1"
    assert by_pat["W-AR-05"]["gap_probe_firings"] == "0"
    assert by_pat["W-AR-05"]["total_firings_across_battery"] == "1"

    assert by_pat["W-CON-03"]["gap_probe_firings"] == "2"
    assert by_pat["W-CON-03"]["negative_control_firings"] == "0"
    assert by_pat["W-CON-03"]["total_firings_across_battery"] == "2"

    # Patterns that never fired show all-zero counts.
    assert by_pat["W-PROV-01"]["total_firings_across_battery"] == "0"


def test_write_summary_csv_target_rule_fired_string_form(tmp_path):
    """When rows are reconstructed from CSV reads, target_rule_fired is
    'True' / 'False' strings. The aggregator must handle both forms."""
    rows = [
        _row_obj(coverage_intent="confirm_existing", target_weakener="W-AR-01",
                 rules_fired="W-AR-01", target_rule_fired="True"),
        _row_obj(coverage_intent="confirm_existing", target_weakener="W-AR-01",
                 rules_fired="", target_rule_fired="False"),
    ]
    out = tmp_path / "summary.csv"
    _write_summary_csv(rows, out)
    by_pat = {r["pattern_id"]: r for r in csv.DictReader(open(out))}
    assert by_pat["W-AR-01"]["confirm_existing_count"] == "2"
    assert by_pat["W-AR-01"]["confirm_existing_hits"] == "1"


def test_summary_csv_total_firings_reconciles_with_rules_fired(tmp_path):
    """Acceptance criterion: aggregate values reconcile against outcomes.csv.

    Sum of total_firings_across_battery across all patterns should equal
    the total number of (row, fired_pattern) pairs.
    """
    rows = [
        _row_obj(rules_fired="W-AR-01"),
        _row_obj(rules_fired="W-AR-01,W-AL-01,COMPOUND-01"),
        _row_obj(rules_fired=""),
        _row_obj(rules_fired="W-EP-01,W-AL-01"),
    ]
    out = tmp_path / "summary.csv"
    _write_summary_csv(rows, out)

    expected_total_firings = sum(
        len(_split_rules_fired(r.rules_fired)) for r in rows
    )  # = 1 + 3 + 0 + 2 = 6
    actual = sum(int(row["total_firings_across_battery"])
                 for row in csv.DictReader(open(out)))
    assert actual == expected_total_firings == 6


# ----- D1: per-COU coverage delta reporting (Phase 2 §10.4 v1.8) -----


def _row_obj_with_cou(base_cou_key, **overrides):
    """Helper: build an _OutcomeRow with a base_cou_key set."""
    overrides["base_cou_key"] = base_cou_key
    return _row_obj(**overrides)


def test_d1_per_cou_recall_three_cous_distinct(tmp_path):
    """Three confirm_existing variants targeting W-AR-01 across 3 base COUs;
    summary.csv records one recall value per COU."""
    rows = [
        # Morrison COU1: 2/2 = 100%
        _row_obj_with_cou("morrison/cou1",
                          coverage_intent="confirm_existing",
                          target_weakener="W-AR-01",
                          target_rule_fired=True),
        _row_obj_with_cou("morrison/cou1",
                          coverage_intent="confirm_existing",
                          target_weakener="W-AR-01",
                          target_rule_fired=True),
        # Morrison COU2: 1/2 = 50%
        _row_obj_with_cou("morrison/cou2",
                          coverage_intent="confirm_existing",
                          target_weakener="W-AR-01",
                          target_rule_fired=True),
        _row_obj_with_cou("morrison/cou2",
                          coverage_intent="confirm_existing",
                          target_weakener="W-AR-01",
                          target_rule_fired=False),
        # Nagaraja: 0/2 = 0%
        _row_obj_with_cou("nagaraja/cou1",
                          coverage_intent="confirm_existing",
                          target_weakener="W-AR-01",
                          target_rule_fired=False),
        _row_obj_with_cou("nagaraja/cou1",
                          coverage_intent="confirm_existing",
                          target_weakener="W-AR-01",
                          target_rule_fired=False),
    ]
    out = tmp_path / "summary.csv"
    _write_summary_csv(rows, out)
    by_pat = {r["pattern_id"]: r for r in csv.DictReader(open(out))}

    war01 = by_pat["W-AR-01"]
    assert war01["recall_morrison_cou1"] == "1.000"
    assert war01["recall_morrison_cou2"] == "0.500"
    assert war01["recall_nagaraja"] == "0.000"
    assert war01["recall_min_per_cou"] == "0.000"
    # disparity = 1.000 - 0.000 = 1.000 ≥ 0.30 → cou_dependent_flag True
    assert war01["recall_cou_disparity"] == "1.000"
    assert war01["cou_dependent_flag"] == "True"


def test_d1_disparity_below_threshold_flag_false(tmp_path):
    """Recall variation < 30% across COUs → cou_dependent_flag = False."""
    rows = [
        _row_obj_with_cou("morrison/cou1",
                          coverage_intent="confirm_existing",
                          target_weakener="W-EP-01",
                          target_rule_fired=True),
        _row_obj_with_cou("morrison/cou2",
                          coverage_intent="confirm_existing",
                          target_weakener="W-EP-01",
                          target_rule_fired=True),
        # Nagaraja: 8/10 = 80% (disparity vs COU1's 100% = 20%)
        *[
            _row_obj_with_cou("nagaraja/cou1",
                              coverage_intent="confirm_existing",
                              target_weakener="W-EP-01",
                              target_rule_fired=True)
            for _ in range(8)
        ],
        *[
            _row_obj_with_cou("nagaraja/cou1",
                              coverage_intent="confirm_existing",
                              target_weakener="W-EP-01",
                              target_rule_fired=False)
            for _ in range(2)
        ],
    ]
    out = tmp_path / "summary.csv"
    _write_summary_csv(rows, out)
    by_pat = {r["pattern_id"]: r for r in csv.DictReader(open(out))}

    wep01 = by_pat["W-EP-01"]
    assert wep01["recall_morrison_cou1"] == "1.000"
    assert wep01["recall_morrison_cou2"] == "1.000"
    assert wep01["recall_nagaraja"] == "0.800"
    # disparity = 1.000 - 0.800 = 0.200 < 0.30 → False
    assert wep01["recall_cou_disparity"] == "0.200"
    assert wep01["cou_dependent_flag"] == "False"


def test_d1_empty_columns_when_no_per_cou_data(tmp_path):
    """A pattern with no per-COU bucketed rows yields empty per-COU columns."""
    rows: list = []  # no rows at all
    out = tmp_path / "summary.csv"
    _write_summary_csv(rows, out)
    by_pat = {r["pattern_id"]: r for r in csv.DictReader(open(out))}

    war05 = by_pat["W-AR-05"]
    assert war05["recall_morrison_cou1"] == ""
    assert war05["recall_morrison_cou2"] == ""
    assert war05["recall_nagaraja"] == ""
    assert war05["recall_min_per_cou"] == ""
    assert war05["recall_cou_disparity"] == ""
    assert war05["cou_dependent_flag"] == ""


def test_d1_disparity_threshold_at_exactly_30_percent(tmp_path):
    """At exactly 0.30 disparity, the flag is True (≥ comparison)."""
    rows = [
        # Morrison COU1: 1/1 = 100%
        _row_obj_with_cou("morrison/cou1",
                          coverage_intent="confirm_existing",
                          target_weakener="W-CON-01",
                          target_rule_fired=True),
        # Morrison COU2: 7/10 = 70%
        *[
            _row_obj_with_cou("morrison/cou2",
                              coverage_intent="confirm_existing",
                              target_weakener="W-CON-01",
                              target_rule_fired=True)
            for _ in range(7)
        ],
        *[
            _row_obj_with_cou("morrison/cou2",
                              coverage_intent="confirm_existing",
                              target_weakener="W-CON-01",
                              target_rule_fired=False)
            for _ in range(3)
        ],
    ]
    out = tmp_path / "summary.csv"
    _write_summary_csv(rows, out)
    by_pat = {r["pattern_id"]: r for r in csv.DictReader(open(out))}
    wcon = by_pat["W-CON-01"]
    # 1.000 - 0.700 = 0.300 → True (≥ threshold)
    assert wcon["recall_cou_disparity"] == "0.300"
    assert wcon["cou_dependent_flag"] == "True"


def test_d1_outcomes_csv_does_not_export_base_cou_key(tmp_path):
    """v1.8 §10.3 only adds D2 timing columns to outcomes.csv; base_cou_key
    stays internal to the classifier."""
    from uofa_cli.adversarial.classifier import _write_outcomes_csv
    rows = [_row_obj_with_cou("morrison/cou1", spec_id="t1")]
    out = tmp_path / "outcomes.csv"
    _write_outcomes_csv(rows, out)
    with open(out) as f:
        reader = csv.DictReader(f)
        loaded = list(reader)
    assert "base_cou_key" not in (reader.fieldnames or [])
    # Sanity: row data is still correctly written.
    assert loaded[0]["spec_id"] == "t1"


# ----- D2: time-to-fire instrumentation (Phase 2 §5.4 / §10.3 v1.8) -----


def test_d2_resolve_eval_host_id_default_uses_hostname():
    """Default host id is socket.gethostname()."""
    import socket
    import os
    from uofa_cli.adversarial.classifier import _resolve_eval_host_id

    # Save & clear the env var
    saved = os.environ.pop("UOFA_EVAL_HOST_ID", None)
    try:
        host = _resolve_eval_host_id()
        assert host == socket.gethostname() or host == "unknown"
    finally:
        if saved is not None:
            os.environ["UOFA_EVAL_HOST_ID"] = saved


def test_d2_resolve_eval_host_id_env_override(monkeypatch):
    """UOFA_EVAL_HOST_ID overrides the hostname."""
    from uofa_cli.adversarial.classifier import _resolve_eval_host_id
    monkeypatch.setenv("UOFA_EVAL_HOST_ID", "test-host-42")
    assert _resolve_eval_host_id() == "test-host-42"


def test_d2_outcomes_csv_includes_d2_timing_columns(tmp_path):
    """outcomes.csv schema gains 5 D2 timing columns per v1.8 §10.3."""
    from uofa_cli.adversarial.classifier import _write_outcomes_csv

    rows = [_row_obj(
        spec_id="t1",
        rules_fired="W-AR-01",
    )]
    # Set timing fields on the row directly
    rows[0].total_eval_ms = 1234
    rows[0].jena_load_ms = 0
    rows[0].jena_inference_ms = 1200
    rows[0].output_serialize_ms = 34
    rows[0].eval_host_id = "test-host"

    out = tmp_path / "outcomes.csv"
    _write_outcomes_csv(rows, out)
    with open(out) as f:
        reader = csv.DictReader(f)
        loaded = list(reader)
    expected = {
        "total_eval_ms", "jena_load_ms", "jena_inference_ms",
        "output_serialize_ms", "eval_host_id",
    }
    assert expected.issubset(set(reader.fieldnames or []))
    assert loaded[0]["total_eval_ms"] == "1234"
    assert loaded[0]["eval_host_id"] == "test-host"


def test_d2_rule_timing_csv_schema(tmp_path):
    """rule_timing.csv conforms to §10.5 schema."""
    from uofa_cli.adversarial.classifier import (
        _write_rule_timing_csv,
        RULE_TIMING_FIELDS,
    )
    rows = [
        {"rule_id": "W-AR-05", "package_path": "/p/v1.jsonld",
         "rule_eval_ms": 0, "rule_fired": "True"},
        {"rule_id": "W-AL-01", "package_path": "/p/v1.jsonld",
         "rule_eval_ms": 0, "rule_fired": "True"},
    ]
    out = tmp_path / "rule_timing.csv"
    _write_rule_timing_csv(rows, out)
    with open(out) as f:
        reader = csv.DictReader(f)
        loaded = list(reader)
    assert tuple(reader.fieldnames or ()) == RULE_TIMING_FIELDS
    assert len(loaded) == 2
    assert loaded[0]["rule_id"] == "W-AR-05"


def test_d2_rule_timing_csv_empty_input_writes_header_only(tmp_path):
    """Even with no rule_timing rows, the file is created with the schema
    header (per v1.8 §10.5 fallback path)."""
    from uofa_cli.adversarial.classifier import (
        _write_rule_timing_csv,
        RULE_TIMING_FIELDS,
    )
    out = tmp_path / "rule_timing.csv"
    _write_rule_timing_csv([], out)
    assert out.exists()
    with open(out) as f:
        reader = csv.DictReader(f)
        loaded = list(reader)
    assert tuple(reader.fieldnames or ()) == RULE_TIMING_FIELDS
    assert loaded == []


def test_d2_batch_manifest_timing_fallback_note(tmp_path):
    """run_analyze annotates batch_manifest with the timing fallback note."""
    import json
    from uofa_cli.adversarial.classifier import (
        _annotate_batch_manifest_with_timing_fallback,
        RULE_TIMING_FALLBACK_NOTE,
    )
    bm = tmp_path / "batch_manifest.json"
    bm.write_text(json.dumps({"specsLoaded": 1}))
    _annotate_batch_manifest_with_timing_fallback(tmp_path)
    annotated = json.loads(bm.read_text())
    assert annotated["timing_fallback_note"] == RULE_TIMING_FALLBACK_NOTE


def test_d2_annotate_idempotent(tmp_path):
    """Calling the annotate helper twice does not corrupt the manifest."""
    import json
    from uofa_cli.adversarial.classifier import (
        _annotate_batch_manifest_with_timing_fallback,
    )
    bm = tmp_path / "batch_manifest.json"
    bm.write_text(json.dumps({"specsLoaded": 1}))
    _annotate_batch_manifest_with_timing_fallback(tmp_path)
    first = json.loads(bm.read_text())
    _annotate_batch_manifest_with_timing_fallback(tmp_path)
    second = json.loads(bm.read_text())
    assert first == second
