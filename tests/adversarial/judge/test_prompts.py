"""Tests for the prompt loader: v1.0.0 template + few-shot substitution + fallback."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from uofa_cli.adversarial.judge import prompts as prompts_mod
from uofa_cli.adversarial.judge.prompts import (
    FALLBACK_VERSION,
    PROMPT_TEMPLATE_VERSION,
    build_prompt_for_case,
    build_prompt_static_prefix,
    clear_prompt_caches,
)


@pytest.fixture(autouse=True)
def _reset_caches():
    """Each test starts with empty lru_caches so isolated patches stick."""
    clear_prompt_caches()
    yield
    clear_prompt_caches()


# ── happy path: v1.0.0 file present, no calibration set ────────────────


class TestV100PrefixLoading:
    def test_loads_v1_template_from_disk(self) -> None:
        prefix = build_prompt_static_prefix()
        # File at packs/core/judge_prompts/v1.0.0.md exists in this repo.
        assert "UofA Phase 3 Judge Prompt v1.0.0" in prefix
        assert prefix.endswith("Template version: v1.0.0\n")

    def test_full_catalog_referenced(self) -> None:
        prefix = build_prompt_static_prefix()
        # Spot-check several existing patterns + §6.7 candidates are
        # documented so the judge has the catalog context it needs.
        for pattern in ("W-AR-01", "W-EP-03", "W-CON-04", "W-EV-01", "W-AR-07"):
            assert pattern in prefix, f"pattern {pattern} missing from prompt"

    def test_six_verdict_classes_defined(self) -> None:
        prefix = build_prompt_static_prefix()
        for cls in (
            "CORRECT-DETECTION", "REAL-GAP", "GENERATOR-ARTIFACT",
            "EXISTING-RULE-MISBEHAVIOR", "OUT-OF-SCOPE", "UNCERTAIN",
        ):
            assert cls in prefix, f"verdict class {cls} not described in prompt"

    def test_reasoning_scaffold_documented(self) -> None:
        prefix = build_prompt_static_prefix()
        for field in (
            "source_taxonomy_identified", "target_rule_identified",
            "rule_firings_inspected", "instantiation_check",
            "verdict_commitment",
        ):
            assert field in prefix


# ── few-shot substitution from a calibration set ────────────────────────


class TestFewShotSubstitution:
    def test_no_calibration_set_emits_noshot_notice(self, tmp_path: Path) -> None:
        # Point the loader at an empty path; the v1.0.0 file still loads,
        # but the few-shot blocks render as "no canonical few-shot yet".
        with patch.object(prompts_mod, "_calibration_set_path", return_value=tmp_path / "missing.jsonl"):
            prefix = build_prompt_static_prefix()
        assert "No canonical few-shot for CORRECT-DETECTION" in prefix
        assert "No canonical few-shot for REAL-GAP" in prefix
        # Placeholders must be substituted, not left raw.
        assert "{{few_shot_correct_detection}}" not in prefix

    def test_canonical_entries_substituted(self, tmp_path: Path) -> None:
        cal_path = tmp_path / "cal.jsonl"
        records = [
            {
                "case_id": "cal-001-correct_detection-data-drift",
                "ground_truth_verdict": "CORRECT-DETECTION",
                "is_canonical_few_shot": True,
                "source_taxonomy": "gohar/evidence_validity/data-drift",
                "expected_target_rule": "W-EP-03",
                "ground_truth_section_6_7_candidate": None,
                "ground_truth_reasoning": "The validation dataset vintage is documented and the model revision postdates it; W-EP-03 fired correctly on this temporal mismatch and the package legitimately instantiates a stale-input-data defeater.",
            },
            {
                "case_id": "cal-006-real_gap-data-drift",
                "ground_truth_verdict": "REAL-GAP",
                "is_canonical_few_shot": True,
                "source_taxonomy": "gohar/evidence_validity/data-drift",
                "expected_target_rule": "W-EV-01",
                "ground_truth_section_6_7_candidate": "W-EV-01",
                "ground_truth_reasoning": "Validation vintage 2018 predates model rev 2024 with no recalibration; this is the canonical Stale Validation Data pattern and no existing UofA rule covers it. Maps to §6.7 Tier 1 candidate W-EV-01.",
            },
        ]
        cal_path.write_text("\n".join(json.dumps(r) for r in records))

        with patch.object(prompts_mod, "_calibration_set_path", return_value=cal_path):
            prefix = build_prompt_static_prefix()

        assert "cal-001-correct_detection-data-drift" in prefix
        assert "cal-006-real_gap-data-drift" in prefix
        assert "verdict CORRECT-DETECTION" in prefix
        assert "§6.7 candidate W-EV-01" in prefix
        # Other classes still get the no-shot notice.
        assert "No canonical few-shot for GENERATOR-ARTIFACT" in prefix

    def test_todo_marker_entries_skipped(self, tmp_path: Path) -> None:
        # Records with TODO_AUTHOR markers must NOT be picked as canonical
        # even if is_canonical_few_shot is true (defense in depth).
        cal_path = tmp_path / "cal.jsonl"
        cal_path.write_text(json.dumps({
            "case_id": "cal-001",
            "ground_truth_verdict": "TODO_AUTHOR_VERDICT",
            "is_canonical_few_shot": True,
            "ground_truth_reasoning": "anything",
        }) + "\n")

        with patch.object(prompts_mod, "_calibration_set_path", return_value=cal_path):
            prefix = build_prompt_static_prefix()
        # Should fall through to no-shot notice for that class.
        # No specific verdict class is set, so all classes show no-shot.
        for cls in ("CORRECT-DETECTION", "REAL-GAP"):
            assert f"No canonical few-shot for {cls}" in prefix

    def test_non_canonical_records_ignored(self, tmp_path: Path) -> None:
        cal_path = tmp_path / "cal.jsonl"
        cal_path.write_text(json.dumps({
            "case_id": "cal-001",
            "ground_truth_verdict": "CORRECT-DETECTION",
            "is_canonical_few_shot": False,  # not canonical
            "ground_truth_reasoning": "anything",
        }) + "\n")
        with patch.object(prompts_mod, "_calibration_set_path", return_value=cal_path):
            prefix = build_prompt_static_prefix()
        assert "No canonical few-shot for CORRECT-DETECTION" in prefix


# ── fallback when v1.0.0.md is missing ─────────────────────────────────


class TestFallbackPrompt:
    def test_fallback_when_template_missing(self, tmp_path: Path) -> None:
        with patch.object(prompts_mod, "_template_path", return_value=tmp_path / "doesnt-exist.md"):
            prefix = build_prompt_static_prefix()
        assert "Tier A fallback prompt" in prefix
        assert prefix.endswith(f"Template version: {FALLBACK_VERSION}\n")

    def test_fallback_still_documents_verdicts(self, tmp_path: Path) -> None:
        with patch.object(prompts_mod, "_template_path", return_value=tmp_path / "missing.md"):
            prefix = build_prompt_static_prefix()
        # Even the fallback names all 6 classes so the model has the
        # output enum to choose from.
        for cls in (
            "CORRECT-DETECTION", "REAL-GAP", "GENERATOR-ARTIFACT",
            "EXISTING-RULE-MISBEHAVIOR", "OUT-OF-SCOPE", "UNCERTAIN",
        ):
            assert cls in prefix


# ── per-case prompt ────────────────────────────────────────────────────


class TestPerCasePrompt:
    def _case(self, **overrides) -> dict:
        case = {
            "case_id": "adv-2026-p2-001-test-v01",
            "coverage_class": "COV-HIT",
            "phase2_outcome_class_raw": "COV-HIT-PLUS",
            "source_taxonomy": "test/example/sub-type",
            "expected_rule": "W-AR-01",
            "rules_fired": ["W-AR-01", "W-EP-01"],
            "section_6_7_mapping": "W-AR-06",
            "package": {"@type": "EvidencePackage", "test": True},
        }
        case.update(overrides)
        return case

    def test_includes_case_id_taxonomy_rules(self) -> None:
        out = build_prompt_for_case(self._case())
        assert "adv-2026-p2-001-test-v01" in out
        assert "test/example/sub-type" in out
        assert "W-AR-01" in out
        # The package payload is included.
        assert "EvidencePackage" in out

    def test_section_6_7_mapping_NOT_in_prompt(self) -> None:
        # Spec §7.6 anti-pattern: §6.7 mapping must not be shown to the
        # judge as a hint. Self-blinding reveal happens at §11.3 author
        # adjudication only.
        out = build_prompt_for_case(self._case(section_6_7_mapping="W-AR-06"))
        # The section_6_7_mapping field must not appear in the prompt,
        # even though we have it on the case dict.
        assert "section_6_7_mapping" not in out

    def test_package_truncation_at_budget(self) -> None:
        big_package = {"data": "x" * 50000}
        out = build_prompt_for_case(self._case(package=big_package))
        assert "package truncated at 12000 chars" in out

    def test_handles_missing_optional_fields(self) -> None:
        case = {"case_id": "c1", "package": {"x": 1}}
        # Should not raise.
        out = build_prompt_for_case(case)
        assert "c1" in out


# ── cache invalidation ─────────────────────────────────────────────────


class TestCacheInvalidation:
    def test_clear_caches_reloads_template(self, tmp_path: Path) -> None:
        # Load once, then patch the template path and verify it picks up
        # the new content after clear_prompt_caches().
        prefix1 = build_prompt_static_prefix()
        assert "UofA Phase 3 Judge Prompt v1.0.0" in prefix1

        custom_template = tmp_path / "v1.0.0.md"
        custom_template.write_text("# CUSTOM TEMPLATE\nshort prefix only.")

        with patch.object(prompts_mod, "_template_path", return_value=custom_template):
            # Without cache clear, lru_cache returns the old result.
            prefix_cached = build_prompt_static_prefix()
            assert "UofA Phase 3 Judge Prompt v1.0.0" in prefix_cached

            clear_prompt_caches()
            prefix_fresh = build_prompt_static_prefix()
            assert "CUSTOM TEMPLATE" in prefix_fresh


# ── default version constant ───────────────────────────────────────────


class TestVersionConstant:
    def test_default_is_v1_0_0(self) -> None:
        assert PROMPT_TEMPLATE_VERSION == "v1.0.0"

    def test_fallback_is_named(self) -> None:
        assert FALLBACK_VERSION == "v0.1.0-tier-a"
