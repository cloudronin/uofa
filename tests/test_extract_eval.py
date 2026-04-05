"""Extract eval scoring — measures extraction accuracy against ground truth.

The scoring framework evaluates how well the LLM extracts credibility factors
from evidence documents. Mock tests validate the scoring infrastructure.
Real LLM tests (gated by OLLAMA_AVAILABLE) measure actual accuracy.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uofa_cli.llm_extractor import (
    ExtractionResult, FieldExtraction, _mock_extract, _json_to_result,
)
from uofa_cli.excel_constants import VV40_FACTOR_NAMES, NASA_ALL_FACTOR_NAMES


# ── Scoring function ─────────────────────────────────────────


def score_extraction(result: ExtractionResult, ground_truth: dict) -> dict:
    """Score extraction results against ground truth.

    Args:
        result: ExtractionResult from the LLM
        ground_truth: Dict with 'expected_factors' list, each having:
            - factor_type: str
            - expected_status: "assessed" | "mentioned" | "not-found" | "ambiguous"
            - expected_level_range: [min, max] (optional)
            - evidence_present: bool

    Returns:
        Dict with precision, recall, F1, per-factor details.
    """
    extracted_factors = {}
    for factor in result.credibility_factors:
        ft = factor.get("factor_type")
        if ft and ft.value:
            extracted_factors[ft.value] = factor

    tp = fp = fn = tn = 0
    level_matches = 0
    level_total = 0
    per_factor = {}

    for gt_factor in ground_truth.get("expected_factors", []):
        ft_name = gt_factor["factor_type"]
        expected_status = gt_factor["expected_status"]
        extracted = extracted_factors.pop(ft_name, None)

        if expected_status in ("assessed", "mentioned"):
            if extracted is not None:
                tp += 1
                per_factor[ft_name] = {"status": "TP"}

                # Check level accuracy
                level_range = gt_factor.get("expected_level_range")
                if level_range and extracted.get("achieved_level"):
                    level_total += 1
                    achieved = extracted["achieved_level"].value
                    if achieved is not None:
                        lo, hi = level_range
                        if lo - 1 <= achieved <= hi + 1:  # ±1 tolerance
                            level_matches += 1
                            per_factor[ft_name]["level_match"] = True
                        else:
                            per_factor[ft_name]["level_match"] = False
            else:
                fn += 1
                per_factor[ft_name] = {"status": "FN"}

        elif expected_status == "not-found":
            if extracted is not None:
                fp += 1
                per_factor[ft_name] = {"status": "FP"}
            else:
                tn += 1
                per_factor[ft_name] = {"status": "TN"}

        elif expected_status == "ambiguous":
            # Ambiguous: correct whether found or not
            if extracted is not None:
                tp += 1
                per_factor[ft_name] = {"status": "TP (ambiguous)"}
            else:
                tn += 1
                per_factor[ft_name] = {"status": "TN (ambiguous)"}

    # Any remaining extracted factors not in ground truth are false positives
    for ft_name in extracted_factors:
        fp += 1
        per_factor[ft_name] = {"status": "FP (extra)"}

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    level_accuracy = level_matches / level_total if level_total > 0 else 0.0

    return {
        "total_factors": len(ground_truth.get("expected_factors", [])),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "level_accuracy": level_accuracy,
        "per_factor": per_factor,
    }


# ── Mock ground truth for VV40 ───────────────────────────────

# The mock provider returns all 13 factors as "assessed" with level 3.
# Ground truth: all 13 factors assessed.
MOCK_VV40_GROUND_TRUTH = {
    "expected_factors": [
        {"factor_type": name, "expected_status": "assessed",
         "expected_level_range": [2, 4], "evidence_present": True}
        for name in VV40_FACTOR_NAMES
    ]
}

# Partial ground truth: 9 assessed, 4 not-found
PARTIAL_VV40_GROUND_TRUTH = {
    "expected_factors": [
        {"factor_type": name, "expected_status": "assessed",
         "expected_level_range": [2, 4], "evidence_present": True}
        for name in VV40_FACTOR_NAMES[:9]
    ] + [
        {"factor_type": name, "expected_status": "not-found",
         "evidence_present": False}
        for name in VV40_FACTOR_NAMES[9:]
    ]
}


# ── Scoring tests ────────────────────────────────────────────


class TestScoring:
    def test_perfect_score(self):
        """Mock returns all 13 factors, ground truth expects all 13 → F1 = 1.0."""
        raw = json.loads(_mock_extract("vv40"))
        result = _json_to_result(raw, "vv40")
        scores = score_extraction(result, MOCK_VV40_GROUND_TRUTH)
        assert scores["f1"] == 1.0
        assert scores["true_positives"] == 13
        assert scores["false_positives"] == 0
        assert scores["false_negatives"] == 0

    def test_partial_ground_truth_has_fp(self):
        """Mock returns 13 factors but ground truth only expects 9 → 4 FPs."""
        raw = json.loads(_mock_extract("vv40"))
        result = _json_to_result(raw, "vv40")
        scores = score_extraction(result, PARTIAL_VV40_GROUND_TRUTH)
        assert scores["true_positives"] == 9
        assert scores["false_positives"] == 4  # Hallucinated 4 factors
        assert scores["false_negatives"] == 0
        assert scores["precision"] == 9 / 13
        assert scores["recall"] == 1.0

    def test_empty_extraction(self):
        """No factors extracted → all expected factors are FN."""
        result = ExtractionResult()
        scores = score_extraction(result, MOCK_VV40_GROUND_TRUTH)
        assert scores["true_positives"] == 0
        assert scores["false_negatives"] == 13
        assert scores["f1"] == 0.0

    def test_nasa_perfect_score(self):
        raw = json.loads(_mock_extract("nasa-7009b"))
        result = _json_to_result(raw, "nasa-7009b")
        gt = {
            "expected_factors": [
                {"factor_type": name, "expected_status": "assessed",
                 "expected_level_range": [1, 3], "evidence_present": True}
                for name in NASA_ALL_FACTOR_NAMES
            ]
        }
        scores = score_extraction(result, gt)
        assert scores["f1"] == 1.0
        assert scores["true_positives"] == 19

    def test_level_accuracy(self):
        """Mock returns level 3 for all, ground truth range [2,4] → all match."""
        raw = json.loads(_mock_extract("vv40"))
        result = _json_to_result(raw, "vv40")
        scores = score_extraction(result, MOCK_VV40_GROUND_TRUTH)
        assert scores["level_accuracy"] == 1.0

    def test_per_factor_details(self):
        raw = json.loads(_mock_extract("vv40"))
        result = _json_to_result(raw, "vv40")
        scores = score_extraction(result, MOCK_VV40_GROUND_TRUTH)
        assert "Software quality assurance" in scores["per_factor"]
        assert scores["per_factor"]["Software quality assurance"]["status"] == "TP"

    def test_not_found_true_negative(self):
        """Factor expected as not-found and not extracted → TN."""
        result = ExtractionResult()
        gt = {
            "expected_factors": [
                {"factor_type": "Use error", "expected_status": "not-found",
                 "evidence_present": False}
            ]
        }
        scores = score_extraction(result, gt)
        assert scores["true_negatives"] == 1
        assert scores["per_factor"]["Use error"]["status"] == "TN"


# ── Mock pipeline F1 gate ────────────────────────────────────


class TestMockF1Gate:
    """Verify that mock extraction meets the F1 gate threshold."""

    def test_vv40_mock_f1_above_gate(self):
        raw = json.loads(_mock_extract("vv40"))
        result = _json_to_result(raw, "vv40")
        scores = score_extraction(result, MOCK_VV40_GROUND_TRUTH)
        assert scores["f1"] >= 0.70, f"VV40 mock F1={scores['f1']:.2f} below 0.70"

    def test_nasa_mock_f1_above_gate(self):
        raw = json.loads(_mock_extract("nasa-7009b"))
        result = _json_to_result(raw, "nasa-7009b")
        gt = {
            "expected_factors": [
                {"factor_type": name, "expected_status": "assessed",
                 "expected_level_range": [1, 3], "evidence_present": True}
                for name in NASA_ALL_FACTOR_NAMES
            ]
        }
        scores = score_extraction(result, gt)
        assert scores["f1"] >= 0.70, f"NASA mock F1={scores['f1']:.2f} below 0.70"
