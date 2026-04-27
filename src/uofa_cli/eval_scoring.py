"""Extraction-vs-ground-truth scoring (precision / recall / F1 / level accuracy).

Promoted from tests/test_extract_eval.py so that `uofa setup verify`
(REQ-DIST-006) and the existing test suite share one implementation.
The verify command needs the same F1 metric as the eval tests use; if
they drift the install verification stops being a faithful reproduction
of test behavior.
"""

from __future__ import annotations

from typing import Any

from uofa_cli.llm_extractor import ExtractionResult


def score_extraction(result: ExtractionResult, ground_truth: dict) -> dict[str, Any]:
    """Score extraction results against ground truth.

    Args:
        result: ExtractionResult from the LLM.
        ground_truth: Dict with 'expected_factors' list, each having:
            - factor_type: str
            - expected_status: "assessed" | "mentioned" | "not-found" | "ambiguous"
            - expected_level_range: [min, max] (optional)
            - evidence_present: bool

    Returns:
        Dict with precision, recall, F1, level_accuracy, per-factor details.
    """
    extracted_factors: dict[str, dict] = {}
    for factor in result.credibility_factors:
        ft = factor.get("factor_type")
        if ft and ft.value:
            extracted_factors[ft.value] = factor

    tp = fp = fn = tn = 0
    level_matches = 0
    level_total = 0
    per_factor: dict[str, dict] = {}

    for gt_factor in ground_truth.get("expected_factors", []):
        ft_name = gt_factor["factor_type"]
        expected_status = gt_factor["expected_status"]
        extracted = extracted_factors.pop(ft_name, None)

        if expected_status in ("assessed", "mentioned"):
            if extracted is not None:
                tp += 1
                per_factor[ft_name] = {"status": "TP"}

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
            if extracted is not None:
                tp += 1
                per_factor[ft_name] = {"status": "TP (ambiguous)"}
            else:
                tn += 1
                per_factor[ft_name] = {"status": "TN (ambiguous)"}

    # Any remaining extracted factors not in ground truth are false positives.
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
