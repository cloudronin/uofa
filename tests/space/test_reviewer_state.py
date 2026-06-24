"""ReviewerState derivation: status precedence, completeness=f(status), claims."""

from __future__ import annotations

from space.gloss import load_gloss
from space.reviewer_state import Status, build_reviewer_state
from space.summary import expected_factors

GLOSS = load_gloss()
ALL13 = expected_factors("vv40")


def W(pid, sev, factors=(), hits=1, desc="why"):
    return {"patternId": pid, "severity": sev, "factors": list(factors), "hits": hits, "description": desc}


def _analysis(assessed=(), missing=(), excluded=(), weakeners=(), mrl=5, conforms=True):
    return {
        "pack": "vv40",
        "completeness": {
            "assessed": list(assessed), "missing": list(missing), "excluded": list(excluded),
            "n_assessed": len(assessed), "n_expected": 13, "denom": 13 - len(excluded),
        },
        "weakeners": list(weakeners),
        "structural": {"conforms": conforms, "violations": [], "n": 0},
        "context": {"model_risk_level": mrl, "standard": "ASME V&V 40", "authenticity": {}},
    }


def _status_of(state, name):
    return next(f.status for f in state.factors if f.name == name)


# ── status precedence (the four branches) ──

def test_explicit_evidence_is_evidenced():
    s = build_reviewer_state(_analysis(assessed=["Model form"]), GLOSS)
    assert _status_of(s, "Model form") is Status.EVIDENCED


def test_scoped_out_is_not_applicable_and_not_required():
    s = build_reviewer_state(_analysis(excluded=["Use error"]), GLOSS)
    f = next(f for f in s.factors if f.name == "Use error")
    assert f.status is Status.NOT_APPLICABLE
    assert f.required is False


def test_absent_factor_is_not_stated_never_evidenced():
    s = build_reviewer_state(_analysis(), GLOSS)  # nothing assessed
    assert all(f.status is not Status.EVIDENCED for f in s.factors)
    assert _status_of(s, "Model form") is Status.NOT_STATED


def test_high_weakener_demotes_an_assessed_factor():
    # Build B regression: extraction marked it assessed, a High weakener targets it.
    s = build_reviewer_state(
        _analysis(assessed=["Model form"], weakeners=[W("W-X", "High", ["Model form"])]), GLOSS)
    f = next(f for f in s.factors if f.name == "Model form")
    assert f.status is Status.NOT_STATED            # cannot be Evidenced
    assert "W-X" in f.targeting_weakeners


def test_scope_out_beats_demotion():
    s = build_reviewer_state(
        _analysis(excluded=["Model form"], weakeners=[W("W-X", "High", ["Model form"])]), GLOSS)
    assert _status_of(s, "Model form") is Status.NOT_APPLICABLE


def test_low_weakener_does_not_demote():
    s = build_reviewer_state(
        _analysis(assessed=["Model form"], weakeners=[W("W-L", "Low", ["Model form"])]), GLOSS)
    assert _status_of(s, "Model form") is Status.EVIDENCED


# ── completeness = f(status) ──

def test_completeness_counts_only_evidenced_status():
    s = build_reviewer_state(_analysis(assessed=["Model form", "Model inputs", "Test samples"]), GLOSS)
    assert s.n_evidenced == 3
    assert s.completeness_pct == round(100 * 3 / 13)


def test_demotion_lowers_completeness():
    # Three "assessed" but a High weakener disputes one -> only two evidenced.
    s = build_reviewer_state(_analysis(
        assessed=["Model form", "Model inputs", "Test samples"],
        weakeners=[W("W-X", "High", ["Test samples"])]), GLOSS)
    assert s.n_evidenced == 2


# ── required_all_accounted (the reframing) ──

def test_all_accounted_true_only_when_complete_and_no_high_concern():
    s = build_reviewer_state(_analysis(assessed=ALL13), GLOSS)
    assert s.missing == ()
    assert s.required_all_accounted is True
    assert s.completeness_pct == 100


def test_high_concern_blocks_all_accounted_even_at_full_completeness():
    # The key reframing: 100% factor-completeness + an open High concern that
    # maps to no factor must NOT read as "all accounted for".
    s = build_reviewer_state(
        _analysis(assessed=ALL13, weakeners=[W("W-VAL", "High", factors=[])]), GLOSS)
    assert s.completeness_pct == 100
    assert s.open_high_count == 1
    assert s.required_all_accounted is False


def test_missing_lists_required_unevidenced_factors():
    assessed = [n for n in ALL13 if n != "Output comparison"]
    s = build_reviewer_state(_analysis(assessed=assessed), GLOSS)
    assert s.missing == ("Output comparison",)
    assert s.required_all_accounted is False
