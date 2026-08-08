"""`uofa extract --keyless` must leave blank what it cannot read.

The contract these tests defend is not accuracy, it is honesty about accuracy.
`minCount >= 1` is satisfied by a field being PRESENT, so an extractor that fills
everything produces a package that validates while being wrong -- which is how 14
turbomachinery models labelled "Class II" came to validate here while packages
naming their device honestly failed.
"""
from __future__ import annotations

import pytest

from uofa_cli import keyless_extractor as KX


class _Chunk:
    def __init__(self, text: str) -> None:
        self.text = text


class _Corpus:
    def __init__(self, text: str) -> None:
        self.chunks = [_Chunk(text)]
        self.total_tokens = len(text.split())
        self.file_manifest = [{"name": "paper.pdf"}]
        self.warnings: list[str] = []


_VV40 = _Corpus(
    "The context of use is prediction of peak contact stress in the acetabular "
    "liner under level gait. Model influence was graded Medium. Decision "
    "consequence was graded High. Peak stress was 134 MPa compared to 141 MPa "
    "measured, a 5% difference. The EXD-Knee v1.2 model was compared against "
    "the AMTI six-station knee simulator dataset. We conclude the model is "
    "adequate for the stated context of use and accept it."
)


def test_unreadable_fields_are_blank_not_plausible():
    """A placeholder satisfies minCount; that is the failure mode, not a fallback."""
    res = KX.extract(_VV40, "vv40")
    for field in ("project_name", "device_class", "assessor_name",
                  "assurance_level"):
        fe = res.assessment_summary[field]
        assert fe.value is None, (
            f"{field} was filled with {fe.value!r}. Nothing here reads it, so a "
            f"value can only be invented -- and minCount would accept it.")
        assert fe.confidence == 0.0


def test_credibility_factors_are_named_but_never_scored():
    """The best keyless route for levels is 0.100 end to end."""
    res = KX.extract(_VV40, "vv40")
    assert res.credibility_factors, "the factor rows should be scaffolded"
    for row in res.credibility_factors:
        assert row["achieved_level"].value is None
        assert row["required_level"].value is None
        assert row["rationale"].value is None
        assert row["status"].value == "not_assessed"


def test_the_checklist_is_not_reported_as_high_confidence():
    """Enumerating the standard's factors is free and proves nothing.

    `control_constant_list` -- a function that prints the checklist and reads
    nothing -- scores 1.000 on factor detection. Emitting those names at high
    confidence paints the spreadsheet green for work never done, which is the
    same finding rendered as a colour.
    """
    res = KX.extract(_VV40, "vv40")
    for row in res.credibility_factors:
        assert row["factor_type"].confidence < 0.85, (
            "the writer paints >= 0.85 green; the checklist is not evidence")


def test_no_requirement_entities_are_invented():
    """bindsRequirement is author-supplied: only 30% of papers cite a standard."""
    res = KX.extract(_VV40, "vv40")
    kinds = {r["entity_type"].value for r in res.model_and_data}
    assert "Requirement" not in kinds, (
        "the engineering requirement a model is trusted to help satisfy lives "
        "in a design history file, not in a paper")


def test_context_of_use_is_blank_under_7009a():
    """NASA-STD-7009A defines no context of use; a value there is invented."""
    res = KX.extract(_VV40, "nasa-7009b")
    assert res.assessment_summary["cou_name"].value is None
    assert res.assessment_summary["cou_description"].value is None


def test_confidences_are_the_measured_figures():
    """Confidence here is a measurement, so it must equal the recorded one."""
    res = KX.extract(_VV40, "vv40")
    for row in res.model_and_data:
        assert row["name"].confidence in (KX._CONF["model"], KX._CONF["dataset"])
    cou = res.assessment_summary["cou_name"]
    if cou.value is not None:
        assert cou.confidence == KX._CONF["cou"]


def test_the_decision_span_carries_the_locator_number_not_the_classifier_s():
    """Two claims, two measurements, and they must not be swapped.

    "The outcome is Accepted" is the classifier's, 0.917 balanced given the
    decision sentence. "THIS sentence is the decision" is the locator's, 0.400
    top-1. Carrying 0.917 on the span reports one measurement as the other and
    paints a 40%-likely sentence green.
    """
    ok, _ = __import__("uofa_cli.keyless.trained", fromlist=["x"]).available()
    if not ok:
        pytest.skip("trained routes unavailable")
    res = KX.extract(_VV40, "vv40")
    if res.decision.get("rationale") and res.decision["rationale"].value:
        assert res.decision["rationale"].confidence == KX._CONF["decision_span"]
        assert KX._CONF["decision_span"] < KX._CONF["decision"]


def test_summarise_states_the_blanks():
    """A run reporting only what it filled reads as a success."""
    res = KX.extract(_VV40, "vv40")
    text = " ".join(KX.summarise(res)).lower()
    assert "blank" in text
    assert "0 scored" in text


def test_an_unrunnable_route_says_so_rather_than_reporting_zero(monkeypatch):
    """"0 results" from a missing dependency and from an empty paper look alike.

    They mean opposite things. Without scikit-learn the run must announce that
    validation results and the decision were not ATTEMPTED -- otherwise a user
    reads a silent degradation as a finding about their document. The same
    defect made the corpus dry run crash in CI rather than say it could not
    check the render path.
    """
    from uofa_cli.keyless import trained as T
    monkeypatch.setattr(T, "available", lambda: (False, "simulated: no sklearn"))
    res = KX.extract(_VV40, "vv40")
    assert res.validation_results == []
    assert res.decision["outcome"].value is None
    text = " ".join(KX.summarise(res))
    assert "NOT attempted" in text and "simulated: no sklearn" in text
