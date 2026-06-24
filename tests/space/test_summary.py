"""S1 summary tests — completeness math, weakener->factor mapping, honest headline."""

from __future__ import annotations

from space.summary import compute, expected_factors


def _statuses(pack="vv40", **overrides):
    """All expected factors 'assessed' unless overridden."""
    s = {n: "assessed" for n in expected_factors(pack)}
    s.update(overrides)
    return s


def test_completeness_counts_and_excluded_denominator():
    statuses = _statuses(
        **{"Use error": "not-assessed", "Test samples": "scoped-out", "Model form": "not-applicable"}
    )
    out = compute("vv40", statuses, {"conforms": True, "violations": []}, [])
    c = out["completeness"]
    assert c["n_expected"] == 13
    assert c["missing"] == ["Use error"]
    assert set(c["excluded"]) == {"Test samples", "Model form"}
    assert c["denom"] == 11  # scoped-out / N/A drop out of the denominator
    assert c["n_assessed"] == 10


def test_weakener_factor_attribution():
    base = "https://uofa.net/instances/proj/cou"
    firings = [
        {
            "patternId": "W-EP-04",
            "severity": "High",
            "hits": 2,
            "affected_nodes": [f"{base}/factor/use-error", f"{base}/factor/test-samples"],
        },
        {"patternId": "W-AL-02", "severity": "Medium", "hits": 1, "affected_nodes": [base]},
    ]
    out = compute("vv40", _statuses(), {"conforms": False, "violations": []}, firings)
    ep04 = next(w for w in out["weakeners"] if w["patternId"] == "W-EP-04")
    assert set(ep04["factors"]) == {"Use error", "Test samples"}
    # A non-factor node resolves to no factor names (not an error).
    al02 = next(w for w in out["weakeners"] if w["patternId"] == "W-AL-02")
    assert al02["factors"] == []
    assert out["weakener_severity"] == {"High": 1, "Medium": 1}


def test_structural_violations_surfaced_globally():
    violations = [{"path": "uofa:requiredLevel", "message": "missing", "severity": "Violation", "fix": "x"}]
    out = compute("vv40", _statuses(), {"conforms": False, "violations": violations}, [])
    assert out["structural"]["n"] == 1
    v = out["structural"]["violations"][0]
    assert set(v) == {"path", "message", "severity"}  # fix dropped; no fake factor focus


def test_headline_has_no_verdict():
    out = compute("vv40", _statuses(**{"Use error": "not-assessed"}),
                  {"conforms": False, "violations": []},
                  [{"patternId": "W-EP-04", "severity": "High", "hits": 1, "affected_nodes": []}])
    h = out["headline"]
    assert "12 of 13 credibility factors assessed" in h
    assert "1 weakener fired" in h and "High" in h
    assert "Accepted" not in h and "Not accepted" not in h
    # Gaps lead: weakeners appear before completeness in the headline.
    assert h.index("weakener") < h.index("12 of 13")


def test_headline_no_weakeners():
    out = compute("vv40", _statuses(), {"conforms": True, "violations": []}, [])
    assert "no weakeners fired" in out["headline"]


def test_nasa_expected_factor_count():
    assert len(expected_factors("nasa-7009b")) == 19
