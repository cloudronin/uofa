"""Whose judgment set each factor status, recorded honestly.

The Inspector's confirm step is the one place a human touches the assessment.
The emitted package therefore has to say, per factor, whether a status came from
the model or from a person. `result_to_import_dict` writes that as
`status_provenance`, and the rule it implements is deliberately narrow:

    corrected   the user moved this status
    extracted   a confirm step ran and the user left this one alone
    (absent)    no confirm step ran at all, so nothing may be claimed

**There is no "confirmed" state, on purpose.** The UI pre-fills every status and
the user submits one form, so an unchanged factor is one they may have read and
agreed with, or scrolled past. `extracted` says only what is true: the model
produced this and no human moved it. Anything stronger would sell a scroll as a
review.

Written 2026-09-08. The behaviour was already correct and had **zero tests** --
nothing in the suite referenced `status_provenance`, so the distinction the
human-boundary gate rests on could have been deleted without turning anything
red. That is the gap these tests close.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from uofa_cli.card_bundle import result_to_import_dict


def _factor(factor_type: str, status: str) -> dict:
    return {"factor_type": factor_type, "status": status}


def _result(*factors: dict) -> SimpleNamespace:
    return SimpleNamespace(
        assessment_summary={},
        model_and_data=[],
        validation_results=[],
        credibility_factors=list(factors),
        decision={},
    )


def _by_type(data: dict) -> dict[str, dict]:
    return {f["factor_type"]: f for f in data["factors"]}


@pytest.fixture
def two_assessed_factors():
    return _result(_factor("Model form", "assessed"),
                   _factor("Model inputs", "assessed"))


def test_a_moved_status_is_recorded_as_corrected(two_assessed_factors):
    """The user changed this one, so the package says a human set it."""
    edits = {"Model form": "assessed", "Model inputs": "not-assessed"}
    rows = _by_type(result_to_import_dict(two_assessed_factors, "vv40", edits))

    assert rows["Model inputs"]["status"] == "not-assessed"
    assert rows["Model inputs"]["status_provenance"] == "corrected"


def test_an_untouched_status_stays_extracted(two_assessed_factors):
    """A confirm step ran and the user left this one alone.

    `factor_edits` is seeded with EVERY extracted status and then merged as the
    user edits, so the presence of a key proves nothing. The value has to be
    compared. If this ever reads "corrected", the comparison has been dropped
    and every factor would look human-reviewed.
    """
    edits = {"Model form": "assessed", "Model inputs": "not-assessed"}
    rows = _by_type(result_to_import_dict(two_assessed_factors, "vv40", edits))

    assert rows["Model form"]["status"] == "assessed"
    assert rows["Model form"]["status_provenance"] == "extracted"


def test_no_confirm_step_claims_nothing_at_all(two_assessed_factors):
    """No confirm step ran, so the field is absent rather than "extracted".

    Absent and "extracted" are different claims. "extracted" says a human saw
    this factor in a confirm step and did not move it. Absent says the question
    was never put to anyone. Emitting "extracted" here would invent a review
    step that did not happen.
    """
    rows = _by_type(result_to_import_dict(two_assessed_factors, "vv40", None))

    for name in ("Model form", "Model inputs"):
        assert "status_provenance" not in rows[name], (
            f"{name} claims provenance, but no confirm step ran"
        )


def test_confirmed_is_never_emitted(two_assessed_factors):
    """Only two words are allowed. "confirmed" would overstate a form submit."""
    edits = {"Model form": "assessed", "Model inputs": "not-assessed"}
    rows = _by_type(result_to_import_dict(two_assessed_factors, "vv40", edits))

    seen = {r.get("status_provenance") for r in rows.values()}
    assert seen == {"corrected", "extracted"}, (
        f"unexpected provenance values {seen}; only corrected/extracted are "
        "supportable from a pre-filled form the user submits once"
    )
