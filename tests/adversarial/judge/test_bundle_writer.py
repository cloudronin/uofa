"""Tests for the bundle writer (writer↔reader round-trip + class normalization)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from uofa_cli.adversarial.judge.bundle import open_bundle
from uofa_cli.adversarial.judge.bundle_writer import (
    NORMALIZE,
    BundleWriteError,
    write_bundle,
)


# ── fixture: a tiny Phase 2-shaped batch directory ─────────────────────


def _build_fixture_batch(root: Path) -> Path:
    """Construct a minimal Phase 2 batch dir under `root`.

    Layout:
        batch/
            coverage/outcomes.csv           # 4 rows
            coverage/matrix.csv             # placeholder
            coverage/summary.csv            # placeholder
            confirm_existing/
                adv-2026-p2-001-w-ar-01_high_morrison-cou1/
                    adv-2026-p2-001-w-ar-01-v01.jsonld   (COV-HIT-PLUS)
                    adv-2026-p2-001-w-ar-01-v02.jsonld   (COV-WRONG)
            gap_probe/
                adv-2026-p2-101-data-drift_medium_morrison-cou1/
                    adv-2026-p2-101-data-drift-v01.jsonld (COV-MISS)
            negative_controls/
                adv-2026-p2-200-clean_low_morrison-cou1/
                    adv-2026-p2-200-clean-v01.jsonld     (COV-CLEAN-WRONG)
    """
    batch = root / "batch"
    coverage = batch / "coverage"
    coverage.mkdir(parents=True)

    # outcomes.csv — minimal header that bundle_writer expects.
    outcomes_path = coverage / "outcomes.csv"
    fieldnames = [
        "spec_id", "variant_num", "target_weakener", "source_taxonomy",
        "coverage_intent", "subtlety", "outcome_class", "rules_fired",
        "target_rule_fired", "section_6_7_candidate",
        "shacl_retries", "tokens", "cost_usd",
    ]
    # spec_id in outcomes.csv = the FULL dir name (with _<subtlety>_<basecou>
    # suffix), per the actual Phase 2 batch convention. The writer keys
    # rows on this FULL id; the variant filename has the bare base id.
    rows = [
        {
            "spec_id": "adv-2026-p2-001-w-ar-01_high_morrison-cou1", "variant_num": "1",
            "target_weakener": "W-AR-01",
            "source_taxonomy": "jarzebowicz-wardzinski/argument_defeaters/D1-undermining",
            "coverage_intent": "confirm_existing", "subtlety": "high",
            "outcome_class": "COV-HIT-PLUS",
            "rules_fired": "W-AR-01,W-AR-05,W-EP-01",
            "target_rule_fired": "True", "section_6_7_candidate": "",
            "shacl_retries": "0", "tokens": "6877", "cost_usd": "0.0",
        },
        {
            "spec_id": "adv-2026-p2-001-w-ar-01_high_morrison-cou1", "variant_num": "2",
            "target_weakener": "W-AR-01",
            "source_taxonomy": "jarzebowicz-wardzinski/argument_defeaters/D1-undermining",
            "coverage_intent": "confirm_existing", "subtlety": "high",
            "outcome_class": "COV-WRONG",
            "rules_fired": "W-EP-03",
            "target_rule_fired": "False", "section_6_7_candidate": "",
            "shacl_retries": "0", "tokens": "7000", "cost_usd": "0.0",
        },
        {
            "spec_id": "adv-2026-p2-101-data-drift_medium_morrison-cou1", "variant_num": "1",
            "target_weakener": "W-EV-01",
            "source_taxonomy": "gohar/evidence_validity/data-drift",
            "coverage_intent": "gap_probe", "subtlety": "medium",
            "outcome_class": "COV-MISS",
            "rules_fired": "",
            "target_rule_fired": "False", "section_6_7_candidate": "W-EV-01",
            "shacl_retries": "0", "tokens": "5000", "cost_usd": "0.0",
        },
        {
            "spec_id": "adv-2026-p2-200-clean_low_morrison-cou1", "variant_num": "1",
            "target_weakener": "",
            "source_taxonomy": "negative_control/clean",
            "coverage_intent": "negative_control", "subtlety": "low",
            "outcome_class": "COV-CLEAN-WRONG",
            "rules_fired": "W-AL-02",
            "target_rule_fired": "False", "section_6_7_candidate": "",
            "shacl_retries": "0", "tokens": "4000", "cost_usd": "0.0",
        },
    ]
    with outcomes_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    # Optional coverage CSVs.
    (coverage / "matrix.csv").write_text("pattern,subtlety,hit_rate,hits,total\nW-AR-01,high,1.000,1,1\n")
    (coverage / "summary.csv").write_text("pattern_id,confirm_existing_count\nW-AR-01,1\n")

    # Spec dirs + jsonld files.
    def _make(category: str, dir_name: str, files: list[tuple[str, dict]]) -> None:
        d = batch / category / dir_name
        d.mkdir(parents=True)
        for name, payload in files:
            (d / name).write_text(json.dumps(payload))

    _make(
        "confirm_existing",
        "adv-2026-p2-001-w-ar-01_high_morrison-cou1",
        [
            ("adv-2026-p2-001-w-ar-01-v01.jsonld", {"@type": "EvidencePackage", "spec_id": "adv-2026-p2-001-w-ar-01"}),
            ("adv-2026-p2-001-w-ar-01-v02.jsonld", {"@type": "EvidencePackage", "spec_id": "adv-2026-p2-001-w-ar-01"}),
        ],
    )
    _make(
        "gap_probe",
        "adv-2026-p2-101-data-drift_medium_morrison-cou1",
        [("adv-2026-p2-101-data-drift-v01.jsonld", {"@type": "EvidencePackage"})],
    )
    _make(
        "negative_controls",
        "adv-2026-p2-200-clean_low_morrison-cou1",
        [("adv-2026-p2-200-clean-v01.jsonld", {"@type": "EvidencePackage"})],
    )

    return batch


# ── happy path ──────────────────────────────────────────────────────────


class TestWriteBundleHappyPath:
    def test_produces_bundle_with_4_packages(self, tmp_path: Path) -> None:
        batch = _build_fixture_batch(tmp_path)
        out = tmp_path / "bundle.tgz"
        result = write_bundle(batch, batch / "coverage" / "outcomes.csv", out)

        assert result.bundle_path == out
        assert result.package_count == 4
        assert out.exists()

    def test_normalizes_class_names(self, tmp_path: Path) -> None:
        batch = _build_fixture_batch(tmp_path)
        out = tmp_path / "bundle.tgz"
        result = write_bundle(batch, batch / "coverage" / "outcomes.csv", out)

        # 4 fixture rows: HIT-PLUS, WRONG, MISS, CLEAN-WRONG
        # Normalized: HIT, WRONG, MISS, WRONG → counts {HIT:1, WRONG:2, MISS:1}
        assert result.distribution == {"COV-HIT": 1, "COV-WRONG": 2, "COV-MISS": 1}
        assert result.raw_distribution == {
            "COV-HIT-PLUS": 1, "COV-WRONG": 1, "COV-MISS": 1, "COV-CLEAN-WRONG": 1,
        }

    def test_round_trip_through_reader(self, tmp_path: Path) -> None:
        batch = _build_fixture_batch(tmp_path)
        out = tmp_path / "bundle.tgz"
        write_bundle(batch, batch / "coverage" / "outcomes.csv", out)

        with open_bundle(out) as bundle:
            entries = list(bundle.iter_entries())

        assert len(entries) == 4
        # Every entry has both normalized class and raw provenance preserved.
        for e in entries:
            assert e.outcome["coverage_class"] in NORMALIZE.values()
            assert "phase2_outcome_class_raw" in e.outcome

    def test_case_id_includes_base_cou_when_present(self, tmp_path: Path) -> None:
        batch = _build_fixture_batch(tmp_path)
        out = tmp_path / "bundle.tgz"
        write_bundle(batch, batch / "coverage" / "outcomes.csv", out)

        with open_bundle(out) as bundle:
            entries = list(bundle.iter_entries())

        # Spec dirs all encoded base_cou=morrison-cou1.
        for e in entries:
            assert "morrison-cou1" in e.case_id

    def test_experimental_factors_recorded(self, tmp_path: Path) -> None:
        batch = _build_fixture_batch(tmp_path)
        out = tmp_path / "bundle.tgz"
        write_bundle(batch, batch / "coverage" / "outcomes.csv", out)

        with open_bundle(out) as bundle:
            entries = list(bundle.iter_entries())

        ce_entry = next(e for e in entries if "w-ar-01" in e.case_id)
        ef = ce_entry.outcome["experimental_factors"]
        assert ef["subtlety_level"] == "high"
        assert ef["base_cou"] == "morrison-cou1"
        assert ef["coverage_intent"] == "confirm_existing"

    def test_manifest_matches_distribution(self, tmp_path: Path) -> None:
        batch = _build_fixture_batch(tmp_path)
        out = tmp_path / "bundle.tgz"
        write_bundle(batch, batch / "coverage" / "outcomes.csv", out)

        with open_bundle(out) as bundle:
            assert bundle.manifest["package_count"] == 4
            assert bundle.manifest["coverage_class_distribution"] == {
                "COV-HIT": 1, "COV-WRONG": 2, "COV-MISS": 1,
            }


# ── failure modes ───────────────────────────────────────────────────────


class TestFailureModes:
    def test_unknown_class_raises(self, tmp_path: Path) -> None:
        batch = _build_fixture_batch(tmp_path)
        # Corrupt outcomes.csv with an unknown class.
        outcomes = batch / "coverage" / "outcomes.csv"
        text = outcomes.read_text().replace("COV-HIT-PLUS", "COV-NEW-WEIRD")
        outcomes.write_text(text)

        with pytest.raises(BundleWriteError, match="unknown outcome_class"):
            write_bundle(batch, outcomes, tmp_path / "out.tgz")

    def test_missing_batch_dir_raises(self, tmp_path: Path) -> None:
        with pytest.raises(BundleWriteError, match="batch_dir not found"):
            write_bundle(
                tmp_path / "nonexistent",
                tmp_path / "outcomes.csv",
                tmp_path / "out.tgz",
            )

    def test_missing_outcomes_csv_raises(self, tmp_path: Path) -> None:
        batch = _build_fixture_batch(tmp_path)
        with pytest.raises(BundleWriteError, match="outcomes.csv not found"):
            write_bundle(batch, tmp_path / "nope.csv", tmp_path / "out.tgz")

    def test_empty_batch_dir_raises(self, tmp_path: Path) -> None:
        batch = tmp_path / "batch"
        coverage = batch / "coverage"
        coverage.mkdir(parents=True)
        (coverage / "outcomes.csv").write_text(
            "spec_id,variant_num,target_weakener,source_taxonomy,coverage_intent,"
            "subtlety,outcome_class,rules_fired,target_rule_fired,"
            "section_6_7_candidate,shacl_retries,tokens,cost_usd\n"
        )
        with pytest.raises(BundleWriteError, match="no jsonld variants"):
            write_bundle(batch, coverage / "outcomes.csv", tmp_path / "out.tgz")
