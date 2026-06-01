"""The P0 runner over the committed seed corpus, with stub backends (no LLM).

Proves the harness loads the answer-keyed corpus, builds the retrieval prompt,
normalizes a structured answer, and scores it — and that a *false-OK* model
(accepts the dangerous-OK case) fails the gate on the hard-core strata while a
competent model clears it.
"""

from __future__ import annotations

from pathlib import Path

from harness.bakeoff import run_p0, score

CORPUS = Path(__file__).resolve().parents[2] / "harness" / "bakeoff" / "corpus"


class _Backend:
    """Minimal LLMBackend duck-type that returns a fixed action_class policy."""

    def __init__(self, *, gap_action, clean_action):
        self._gap, self._clean = gap_action, clean_action

    def supports_structured_output(self):
        return True

    def generate_structured(self, prompt, schema, options):
        # The fire row carries `"per_region_competence_characterized": false`.
        gap = '"per_region_competence_characterized": false' in prompt
        return {
            "finding": "rendered", "why_fired": "rendered", "recommended_action": "rendered",
            "action_class": self._gap if gap else self._clean,
            "confidence": "high", "escalate": False,
        }

    def generate(self, prompt, options):  # pragma: no cover - structured path used
        return "{}"


def test_seed_corpus_loads_with_answer_keys():
    rows = run_p0.load_corpus(CORPUS)
    assert len(rows) >= 2
    for row in rows:
        key = row["answer_key"]
        assert key["gold_action"]["selected_class"]
        assert "forbidden_claims" in key and "acceptable_confidence" in key


def test_competent_model_clears_hard_core():
    rows = run_p0.load_corpus(CORPUS)
    # Acts on the gap (acquire-validation), accepts the characterized control.
    answers = run_p0.run_corpus(rows, _Backend(gap_action="acquire-validation",
                                               clean_action="accept-residual-risk"))
    card = score.scorecard(rows, answers, alpha=0.02)
    assert card["hard_core"]["dangerous_error_rate"] == 0.0
    assert score.gate_read(card, max_dangerous_error=0.0, min_selective_coverage=0.5)["clears"]


def test_false_ok_model_fails_the_gate():
    rows = run_p0.load_corpus(CORPUS)
    # Always "accept" — the confident-wrong false-OK on the dangerous-OK case.
    answers = run_p0.run_corpus(rows, _Backend(gap_action="accept-residual-risk",
                                               clean_action="accept-residual-risk"))
    card = score.scorecard(rows, answers, alpha=0.02)
    assert card["hard_core"]["dangerous_error_rate"] > 0.0          # the false-OK is harmful
    assert not score.gate_read(card, max_dangerous_error=0.0, min_selective_coverage=0.5)["clears"]
