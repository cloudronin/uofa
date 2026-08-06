"""Null-model controls for the extract scorer, and what they say about it.

Two constant functions saturate the metrics `score_extraction.py` reports. On
the shipped 50-bundle corpus, 740 of 800 factor rows are `assessed` and every
assessed level is 1, 2 or 3 -- never 4, never 5. So emitting the pack's fixed
checklist scores detection F1 0.960 having read no input, and predicting the
constant 2 lands inside the +/-1 tolerance every time.

These tests pin that, because it is the reason the controls exist: a candidate
extractor's absolute F1 is not interpretable on this corpus, and a report that
prints one without the controls beside it invites a conclusion the number does
not support.

They are also a corpus tripwire. If the corpus is ever regenerated with a wider
level distribution, `test_constant_level_saturates_the_tolerance` starts failing
-- which is the *good* outcome, and the failure message says so.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))

from score_extraction import (  # noqa: E402
    CONTROL_NAMES,
    control_predictions,
    score_controls,
    score_factors,
)

CORPUS = _ROOT / "tests" / "fixtures" / "extract_corpus"


def _bundles() -> list[dict]:
    out = []
    for f in sorted(CORPUS.glob("*/*/ground_truth.json")):
        out.append(json.loads(f.read_text(encoding="utf-8")))
    return out


@pytest.fixture(scope="module")
def scored() -> dict[str, list[dict]]:
    per_control: dict[str, list[dict]] = {n: [] for n in CONTROL_NAMES}
    for gt in _bundles():
        for name, s in score_controls(gt["pack"], gt["expected_factors"]).items():
            per_control[name].append(s)
    return per_control


def _mean(rows, key) -> float:
    return statistics.mean(r[key] for r in rows)


def test_corpus_is_present():
    b = _bundles()
    assert len(b) == 50, f"expected the 50-bundle corpus, found {len(b)}"


def test_constant_checklist_nearly_saturates_detection(scored):
    """The headline: 0 parameters, 0 input read, detection F1 0.960.

    Any candidate scoring at or below this on detection has demonstrated
    nothing, whatever its absolute number looks like.
    """
    f1 = _mean(scored["control_constant_list"], "overall_f1")
    assert f1 == pytest.approx(0.960, abs=0.005), (
        f"control_constant_list F1 is {f1:.3f}; the corpus label distribution "
        "moved, so every published comparison against it needs re-checking"
    )
    assert _mean(scored["control_constant_list"], "detection_rate") == pytest.approx(1.0)


def test_constant_level_saturates_the_tolerance(scored):
    """Predicting 2 is inside +/-1 of every assessed level in the corpus.

    This failing is the *good* outcome: it means the level distribution was
    widened past 1-3 and the level metric can finally discriminate.
    """
    acc = _mean(scored["control_constant_level"], "level_accuracy")
    assert acc == pytest.approx(1.0, abs=0.001), (
        f"constant level 2 now scores {acc:.3f} at +/-1 rather than 1.000. "
        "If the corpus was regenerated with levels spanning 1-5, this is "
        "expected -- update the anchor and re-baseline."
    )


def test_the_absolute_gate_is_cleared_by_a_null_model(scored):
    """print_report's F1 >= 0.70 gate is not evidence on this corpus.

    Pinned so nobody reintroduces the gate as a standalone pass/fail without
    the controls printed beside it.
    """
    clears = [n for n in CONTROL_NAMES
              if _mean(scored[n], "overall_f1") >= 0.70]
    assert clears, "expected at least one null model to clear the 0.70 gate"
    assert "control_constant_list" in clears


def test_empty_control_is_the_floor(scored):
    for key in ("overall_f1", "detection_rate", "status_accuracy"):
        assert _mean(scored["control_empty"], key) == 0.0


def test_controls_read_no_input():
    """A control's output depends on the pack and nothing else.

    If a control ever consults the bundle, it stops being a null model and the
    deltas measured against it become meaningless.
    """
    for name in CONTROL_NAMES:
        a = control_predictions(name, "vv40")
        b = control_predictions(name, "vv40")
        assert a == b, f"{name} is not deterministic"
    # Different packs differ only because the checklist differs.
    assert (control_predictions("control_constant_list", "vv40")
            != control_predictions("control_constant_list", "nasa-7009b"))


def test_controls_are_scored_by_the_same_function_as_candidates():
    """Scoring a control by hand must equal scoring it through score_factors.

    Guards the property that makes the deltas legitimate: control and candidate
    are measured identically, so a difference between them is a difference in
    the method rather than in the measurement.
    """
    gt = _bundles()[0]
    preds = control_predictions("control_constant_list", gt["pack"])
    direct = score_factors(preds, gt["expected_factors"])
    viascore = score_controls(gt["pack"], gt["expected_factors"])["control_constant_list"]
    assert direct["overall_f1"] == viascore["overall_f1"]
    assert direct["detection_rate"] == viascore["detection_rate"]


def test_constant_list_does_not_claim_levels_or_status(scored):
    """The detection control must not accidentally win the other sub-tasks.

    It emits factor_type alone, so level and status stay at zero and each
    sub-task is attributable to the control built for it.
    """
    assert _mean(scored["control_constant_list"], "level_accuracy") == 0.0
    assert _mean(scored["control_constant_list"], "status_accuracy") == 0.0
