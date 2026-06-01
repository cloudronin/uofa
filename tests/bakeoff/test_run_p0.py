"""The P0 runner + scorer over the committed corpus (no LLM).

Proves the harness loads the answer-keyed corpus (every key with real
provenance), the runner normalizes a structured answer, and the scorer reads the
gate correctly on the REAL corpus: a gold-following model clears it; a false-OK
model (accepts the dangerous-OK / out-of-envelope cases) fails on the hard-core
strata.
"""

from __future__ import annotations

from pathlib import Path

from harness.bakeoff import run_p0, score

CORPUS = Path(__file__).resolve().parents[2] / "harness" / "bakeoff" / "corpus"


class _FixedBackend:
    """Minimal LLMBackend duck-type returning a fixed action_class."""

    def __init__(self, action_class):
        self._a = action_class

    def supports_structured_output(self):
        return True

    def generate_structured(self, prompt, schema, options):
        return {"finding": "x", "why_fired": "x", "recommended_action": "x",
                "action_class": self._a, "confidence": "high", "escalate": False}

    def generate(self, prompt, options):  # pragma: no cover - structured path used
        return "{}"


def _answers(rows, *, action_class=None, gold=False):
    out = []
    for row in rows:
        cls = row["answer_key"]["gold_action"]["selected_class"] if gold else action_class
        out.append({"row_id": row["row_id"], "action_class": cls,
                    "confidence": "high", "escalate": False})
    return out


def test_corpus_loads_with_grounded_keys():
    rows = run_p0.load_corpus(CORPUS)
    assert len(rows) >= 6
    for row in rows:
        key = row["answer_key"]
        assert key["gold_action"]["selected_class"]
        assert key["forbidden_claims"] and key["acceptable_confidence"]
        # Every key carries real, external provenance — never pipeline/frontier sourced.
        prov = row["label_provenance"]
        assert prov["external_grounding"]
        assert "pipeline output" in prov["not_sourced_from"]


def test_run_corpus_normalizes_answers():
    rows = run_p0.load_corpus(CORPUS)
    answers = run_p0.run_corpus(rows, _FixedBackend("acquire-validation"))
    assert len(answers) == len(rows)
    assert all(a.get("row_id") and a.get("action_class") for a in answers)


def test_gold_following_model_clears_the_gate():
    rows = run_p0.load_corpus(CORPUS)
    card = score.scorecard(rows, _answers(rows, gold=True), alpha=0.02)
    assert card["hard_core"]["dangerous_error_rate"] == 0.0
    assert score.gate_read(card, max_dangerous_error=0.0, min_selective_coverage=0.5)["clears"]


def test_false_ok_model_fails_the_gate():
    rows = run_p0.load_corpus(CORPUS)
    # Always "accept" — the confident-wrong false-OK on every fire/dangerous-OK row.
    card = score.scorecard(rows, _answers(rows, action_class="accept-residual-risk"), alpha=0.02)
    assert card["hard_core"]["dangerous_error_rate"] > 0.0
    assert not score.gate_read(card, max_dangerous_error=0.0, min_selective_coverage=0.5)["clears"]
