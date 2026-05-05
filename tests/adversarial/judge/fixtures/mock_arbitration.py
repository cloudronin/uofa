"""10-case Judge E arbitration fixture with mixed confidence (Phase 3 v1.6 Wave C).

Designed so partition_arbitration_results yields 7 ARBITRATED + 3
ESCALATED at the default 0.6 confidence floor. At least one case is
OOS with a populated evidence_gap to exercise the productive-OOS
schema validation in the post-parse path.
"""

from __future__ import annotations

from uofa_cli.adversarial.judge.arbitration import ArbitrationEntry


def build_mock_arbitration_results() -> list[ArbitrationEntry]:
    return [
        # 7 ARBITRATED (confidence ≥ 0.6)
        ArbitrationEntry(
            case_id="adv-2026-p2-001-test-v01",
            verdict="REAL-GAP",
            confidence=0.82,
            reasoning="Production judges A and B agreed REAL-GAP; C said GENERATOR-ARTIFACT. "
                      "Inspecting the package shows the W-EV-01 candidate is legitimately instantiated.",
            arbitration_basis="package_content",
            production_judge_evaluation={
                "judge_a_reasoning_assessment": "sound",
                "judge_b_reasoning_assessment": "sound",
                "judge_c_reasoning_assessment": "weak",
            },
            evidence_gap=None,
            raw_response={"verdict": "REAL-GAP"},
        ),
        ArbitrationEntry(
            case_id="adv-2026-p2-002-test-v01",
            verdict="CORRECT-DETECTION",
            confidence=0.91,
            reasoning="Three-way disagreement; Judge A's W-AR-01 confirm_existing reading is sound.",
            arbitration_basis="production_judge_evaluation",
            production_judge_evaluation={
                "judge_a_reasoning_assessment": "sound",
                "judge_b_reasoning_assessment": "weak",
                "judge_c_reasoning_assessment": "irrelevant",
            },
            evidence_gap=None,
            raw_response={},
        ),
        ArbitrationEntry(
            case_id="adv-2026-p2-003-test-v01",
            verdict="EXISTING-RULE-MISBEHAVIOR",
            confidence=0.68,
            reasoning="W-AL-02 false-positive on a clean negative-control COU. Two of three "
                      "production judges flagged this; consensus is that the rule misbehaved.",
            arbitration_basis="production_judge_evaluation",
            production_judge_evaluation={
                "judge_a_reasoning_assessment": "sound",
                "judge_b_reasoning_assessment": "weak",
                "judge_c_reasoning_assessment": "sound",
            },
            evidence_gap=None,
            raw_response={},
        ),
        ArbitrationEntry(
            case_id="adv-2026-p2-004-test-v01",
            verdict="OUT-OF-SCOPE",
            confidence=0.74,
            reasoning="Bundle is structurally complete but credibility argument depends on "
                      "physician clinical-judgment evidence not present in the bundle. "
                      "Productive OOS with concrete evidence_gap.",
            arbitration_basis="package_content",
            production_judge_evaluation={
                "judge_a_reasoning_assessment": "weak",
                "judge_b_reasoning_assessment": "weak",
                "judge_c_reasoning_assessment": "irrelevant",
            },
            evidence_gap={
                "missing_evidence_type": "clinical interpretation framework + physician acceptance criteria",
                "would_support_defeater_evaluation": "clinical-judgment arbitration in V&V 40 acceptance",
            },
            raw_response={},
        ),
        ArbitrationEntry(
            case_id="adv-2026-p2-005-test-v01",
            verdict="GENERATOR-ARTIFACT",
            confidence=0.85,
            reasoning="GEN-INVALID class; SHACL profile failure consistent with prompt-template drift.",
            arbitration_basis="package_content",
            production_judge_evaluation={
                "judge_a_reasoning_assessment": "sound",
                "judge_b_reasoning_assessment": "sound",
                "judge_c_reasoning_assessment": "sound",
            },
            evidence_gap=None,
            raw_response={},
        ),
        ArbitrationEntry(
            case_id="adv-2026-p2-006-test-v01",
            verdict="REAL-GAP",
            confidence=0.62,
            reasoning="W-CX-01 candidate; configuration divergence mapping clean.",
            arbitration_basis="package_content",
            production_judge_evaluation={
                "judge_a_reasoning_assessment": "weak",
                "judge_b_reasoning_assessment": "sound",
                "judge_c_reasoning_assessment": "weak",
            },
            evidence_gap=None,
            raw_response={},
        ),
        ArbitrationEntry(
            case_id="adv-2026-p2-007-test-v01",
            verdict="CORRECT-DETECTION",
            confidence=0.79,
            reasoning="Standard COV-HIT-PLUS; production judges' disagreement resolved on package content.",
            arbitration_basis="package_content",
            production_judge_evaluation={
                "judge_a_reasoning_assessment": "sound",
                "judge_b_reasoning_assessment": "weak",
                "judge_c_reasoning_assessment": "weak",
            },
            evidence_gap=None,
            raw_response={},
        ),
        # 3 ESCALATED (confidence < 0.6)
        ArbitrationEntry(
            case_id="adv-2026-p2-008-test-v01",
            verdict="UNCERTAIN",
            confidence=0.42,
            reasoning="Genuine three-way disagreement; package content does not clearly support any verdict. "
                      "Escalating to author final-arbitration.",
            arbitration_basis="independent_disagreement",
            production_judge_evaluation={
                "judge_a_reasoning_assessment": "weak",
                "judge_b_reasoning_assessment": "weak",
                "judge_c_reasoning_assessment": "weak",
            },
            evidence_gap=None,
            raw_response={},
        ),
        ArbitrationEntry(
            case_id="adv-2026-p2-009-test-v01",
            verdict="REAL-GAP",
            confidence=0.55,
            reasoning="Plausibly REAL-GAP for W-AR-06 but the source taxonomy mapping is unclear. "
                      "Confidence below threshold; escalating.",
            arbitration_basis="package_content",
            production_judge_evaluation={
                "judge_a_reasoning_assessment": "weak",
                "judge_b_reasoning_assessment": "weak",
                "judge_c_reasoning_assessment": "irrelevant",
            },
            evidence_gap=None,
            raw_response={},
        ),
        ArbitrationEntry(
            case_id="adv-2026-p2-010-test-v01",
            verdict="GENERATOR-ARTIFACT",
            confidence=0.50,
            reasoning="Possible GEN-INVALID but SHACL output ambiguous; escalating for author review.",
            arbitration_basis="package_content",
            production_judge_evaluation={
                "judge_a_reasoning_assessment": "weak",
                "judge_b_reasoning_assessment": "irrelevant",
                "judge_c_reasoning_assessment": "weak",
            },
            evidence_gap=None,
            raw_response={},
        ),
    ]
