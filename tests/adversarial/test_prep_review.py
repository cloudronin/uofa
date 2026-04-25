"""Tests for D3 — Phase 3 reviewer prep packet generation (Phase 2 §10.6 v1.8)."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import pytest

from uofa_cli.adversarial.prep_review import (
    _ReviewableCase,
    _dedup_by_spec_id,
    _format_packet,
    _format_index,
    _invert_default_attributions,
    _normalize_include,
    _read_outcomes,
    _resolve_neighborhood,
    _resolve_taxonomy_citation,
    _sort_for_index,
    run_prep_review,
)


# ----- normalization helpers -----


def test_normalize_include_default():
    assert _normalize_include(None) == {"COV-MISS", "COV-WRONG"}
    assert _normalize_include("") == {"COV-MISS", "COV-WRONG"}


def test_normalize_include_short_forms():
    assert _normalize_include("miss,wrong") == {"COV-MISS", "COV-WRONG"}
    assert _normalize_include("cov-miss,cov-clean-wrong") == {
        "COV-MISS", "COV-CLEAN-WRONG"
    }


def test_normalize_include_strips_whitespace():
    assert _normalize_include("cov-miss , cov-wrong") == {"COV-MISS", "COV-WRONG"}


# ----- outcomes.csv reading + filtering + dedup -----


def _write_outcomes_fixture(path: Path, rows: list[dict]) -> None:
    fieldnames = list(rows[0].keys()) if rows else []
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def test_read_outcomes_filters_to_include_classes(tmp_path):
    outcomes = tmp_path / "outcomes.csv"
    _write_outcomes_fixture(outcomes, [
        {"spec_id": "s1", "outcome_class": "COV-MISS",
         "target_weakener": "", "source_taxonomy": "gohar/req/missing",
         "coverage_intent": "gap_probe", "subtlety": "high",
         "rules_fired": "", "section_6_7_candidate": ""},
        {"spec_id": "s2", "outcome_class": "COV-HIT",
         "target_weakener": "W-AR-01", "source_taxonomy": "",
         "coverage_intent": "confirm_existing", "subtlety": "medium",
         "rules_fired": "W-AR-01", "section_6_7_candidate": ""},
        {"spec_id": "s3", "outcome_class": "COV-WRONG",
         "target_weakener": "", "source_taxonomy": "gohar/ev/data-drift",
         "coverage_intent": "gap_probe", "subtlety": "high",
         "rules_fired": "W-CON-03", "section_6_7_candidate": "True"},
    ])

    cases = _read_outcomes(outcomes, {"COV-MISS", "COV-WRONG"})
    assert {c.spec_id for c in cases} == {"s1", "s3"}
    # COV-HIT filtered out


def test_dedup_by_spec_id_keeps_first(tmp_path):
    cases = [
        _ReviewableCase("s1", None, "tx/a/1", "gap_probe", "COV-MISS",
                        "high", "", False),
        _ReviewableCase("s1", None, "tx/a/1", "gap_probe", "COV-MISS",
                        "low", "", False),
        _ReviewableCase("s2", None, "tx/b/2", "gap_probe", "COV-WRONG",
                        "high", "W-X", True),
    ]
    out = _dedup_by_spec_id(cases)
    assert [c.spec_id for c in out] == ["s1", "s2"]
    # First occurrence preserved (subtlety=high)
    assert out[0].subtlety == "high"


# ----- sorting -----


def test_sort_for_index_candidates_first():
    cases = [
        _ReviewableCase("s-non", None, "z/late", "gap_probe", "COV-MISS",
                        "high", "", False),
        _ReviewableCase("s-cand-b", None, "b/cand", "gap_probe", "COV-MISS",
                        "high", "", True),
        _ReviewableCase("s-cand-a", None, "a/cand", "gap_probe", "COV-MISS",
                        "high", "", True),
    ]
    out = _sort_for_index(cases)
    # Candidates first, sorted by source_taxonomy alpha
    assert [c.spec_id for c in out] == ["s-cand-a", "s-cand-b", "s-non"]


# ----- registry helpers -----


def test_invert_default_attributions_groups_by_prefix():
    registry = {
        "default_attribution_for_uofa_pattern": {
            "_comment": "ignored",
            "W-AR-01": "jarzebowicz-wardzinski/argument_defeaters/D1-undermining",
            "W-AR-02": "jarzebowicz-wardzinski/argument_defeaters/D2-rebutting",
            "W-EP-01": "khakzad/epistemic/incomplete-knowledge",
        }
    }
    by_prefix = _invert_default_attributions(registry)
    assert "jarzebowicz-wardzinski/argument_defeaters" in by_prefix
    assert by_prefix["jarzebowicz-wardzinski/argument_defeaters"] == ["W-AR-01", "W-AR-02"]
    assert by_prefix["khakzad/epistemic"] == ["W-EP-01"]


def test_resolve_neighborhood_returns_shared_prefix_patterns():
    by_prefix = {
        "gohar/evidence_validity": ["W-X-01", "W-Y-02"],
        "gohar/requirements": ["W-Z-03"],
    }
    assert _resolve_neighborhood(
        "gohar/evidence_validity/data-drift", by_prefix
    ) == ["W-X-01", "W-Y-02"]
    assert _resolve_neighborhood(
        "gohar/contextual/faults-physical", by_prefix
    ) == []
    assert _resolve_neighborhood(None, by_prefix) == []


def test_resolve_taxonomy_citation_returns_registry_text():
    registry = {
        "taxonomies": {
            "gohar": {"citation": "Gohar et al. 2025"},
        }
    }
    assert _resolve_taxonomy_citation(
        "gohar/evidence_validity/data-drift", registry
    ) == "Gohar et al. 2025"
    assert "no citation registered" in _resolve_taxonomy_citation(
        "unknown/foo/bar", registry
    )
    assert _resolve_taxonomy_citation(None, registry) == "(no source_taxonomy declared)"


# ----- formatting -----


def test_format_packet_includes_required_sections():
    case = _ReviewableCase(
        "adv-test-1", "W-AR-01", "gohar/evidence_validity/data-drift",
        "gap_probe", "COV-MISS", "high",
        "W-CON-03", False,
    )
    packet = _format_packet(
        case=case,
        spec_path=None,
        package_path=None,
        package_text="",
        taxonomy_citation="Gohar et al. 2025",
        neighborhood=["W-X-01", "W-Y-02"],
    )
    # Required sections per §10.6
    assert "Source taxonomy attribution" in packet
    assert "Spec description" in packet
    assert "Generated package" in packet
    assert "What the existing catalog covers in this neighborhood" in packet
    assert "Reviewer questions" in packet
    assert "Representative package (JSON-LD)" in packet
    # Four reviewer questions
    assert "1. **Is the gap genuine?**" in packet
    assert "2. **If genuine, would a new Jena rule be warranted?**" in packet
    assert "3. **Severity classification" in packet
    assert "4. **Free-form notes:**" in packet
    # Neighborhood patterns present
    assert "W-X-01" in packet
    assert "W-Y-02" in packet
    # Outcome class + spec_id in header
    assert "adv-test-1" in packet
    assert "COV-MISS" in packet


def test_format_index_renders_table():
    cases = [
        _ReviewableCase("s-cand", None, "tx/a/1", "gap_probe", "COV-MISS",
                        "high", "", True),
        _ReviewableCase("s-non", None, "tx/b/2", "gap_probe", "COV-WRONG",
                        "high", "W-X", False),
    ]
    idx = _format_index(cases)
    assert "Phase 3 review packet index" in idx
    assert "Total packets: **2**" in idx
    assert "`s-cand`" in idx
    assert "`s-non`" in idx
    # Star marks §6.7 candidate
    assert "★" in idx
    # Link to per-packet file
    assert "[`s-cand_review.md`](./s-cand_review.md)" in idx


# ----- end-to-end CLI -----


def _build_args(outcomes: Path, output: Path, **kw) -> argparse.Namespace:
    base = dict(outcomes=outcomes, output=output, include=None, max_cases=50)
    base.update(kw)
    return argparse.Namespace(**base)


def test_run_prep_review_writes_packets_and_index(tmp_path):
    outcomes = tmp_path / "outcomes.csv"
    _write_outcomes_fixture(outcomes, [
        {"spec_id": "adv-r1", "outcome_class": "COV-MISS",
         "target_weakener": "", "source_taxonomy": "gohar/evidence_validity/data-drift",
         "coverage_intent": "gap_probe", "subtlety": "high",
         "rules_fired": "", "section_6_7_candidate": ""},
        {"spec_id": "adv-r2", "outcome_class": "COV-WRONG",
         "target_weakener": "", "source_taxonomy": "gohar/requirements/stale",
         "coverage_intent": "gap_probe", "subtlety": "medium",
         "rules_fired": "W-CON-03", "section_6_7_candidate": "True"},
        {"spec_id": "adv-hit", "outcome_class": "COV-HIT",
         "target_weakener": "W-AR-01", "source_taxonomy": "",
         "coverage_intent": "confirm_existing", "subtlety": "high",
         "rules_fired": "W-AR-01", "section_6_7_candidate": ""},
    ])
    output = tmp_path / "review_packets"

    rc = run_prep_review(_build_args(outcomes, output))
    assert rc == 0
    assert (output / "INDEX.md").exists()
    assert (output / "adv-r1_review.md").exists()
    assert (output / "adv-r2_review.md").exists()
    # COV-HIT row not packeted
    assert not (output / "adv-hit_review.md").exists()


def test_run_prep_review_max_cases_caps_output(tmp_path):
    outcomes = tmp_path / "outcomes.csv"
    rows = [
        {"spec_id": f"adv-{i:02d}", "outcome_class": "COV-MISS",
         "target_weakener": "", "source_taxonomy": "gohar/evidence_validity/data-drift",
         "coverage_intent": "gap_probe", "subtlety": "high",
         "rules_fired": "", "section_6_7_candidate": ""}
        for i in range(10)
    ]
    _write_outcomes_fixture(outcomes, rows)
    output = tmp_path / "review_packets"

    rc = run_prep_review(_build_args(outcomes, output, max_cases=3))
    assert rc == 0
    md_files = list(output.glob("adv-*_review.md"))
    assert len(md_files) == 3


def test_run_prep_review_returns_1_when_no_matches(tmp_path):
    outcomes = tmp_path / "outcomes.csv"
    _write_outcomes_fixture(outcomes, [
        {"spec_id": "adv-hit", "outcome_class": "COV-HIT",
         "target_weakener": "W-AR-01", "source_taxonomy": "",
         "coverage_intent": "confirm_existing", "subtlety": "high",
         "rules_fired": "W-AR-01", "section_6_7_candidate": ""},
    ])
    output = tmp_path / "review_packets"
    rc = run_prep_review(_build_args(outcomes, output))
    assert rc == 1


def test_run_prep_review_returns_2_when_outcomes_missing(tmp_path):
    output = tmp_path / "review_packets"
    rc = run_prep_review(_build_args(tmp_path / "no-such-file.csv", output))
    assert rc == 2


def test_run_prep_review_index_sort_candidates_first(tmp_path):
    outcomes = tmp_path / "outcomes.csv"
    _write_outcomes_fixture(outcomes, [
        {"spec_id": "adv-non", "outcome_class": "COV-MISS",
         "target_weakener": "", "source_taxonomy": "z/late/x",
         "coverage_intent": "gap_probe", "subtlety": "high",
         "rules_fired": "", "section_6_7_candidate": ""},
        {"spec_id": "adv-cand", "outcome_class": "COV-MISS",
         "target_weakener": "", "source_taxonomy": "a/early/y",
         "coverage_intent": "gap_probe", "subtlety": "high",
         "rules_fired": "", "section_6_7_candidate": "True"},
    ])
    output = tmp_path / "review_packets"
    run_prep_review(_build_args(outcomes, output))

    index_text = (output / "INDEX.md").read_text()
    cand_pos = index_text.find("`adv-cand`")
    non_pos = index_text.find("`adv-non`")
    assert cand_pos != -1 and non_pos != -1
    # §6.7 candidate listed before non-candidate
    assert cand_pos < non_pos
