"""Coverage experiment (B) scaffolding: the K1 prompt must hide the structured inputs,
and the artifacts must not leak the conclusion (or K1 is handed the answer and B is void).
"""
from harness.bakeoff import run_p0
from harness.bakeoff.coverage_artifacts import RAW_ARTIFACTS


def test_raw_artifact_prompt_excludes_structured_inputs_and_catalog():
    row = {"row_id": "x", "input": {
        "raw_artifact": "Reported validation error is 0.012; normalization used the full dataset.",
        "case_context": {"cou": "a sign-off decision"}}}
    p = run_p0.build_prompt(row, condition="raw_artifact")
    assert "validation error is 0.012" in p          # the prose IS supplied
    assert "a sign-off decision" in p                 # the COU is supplied
    assert "acquire-validation" in p                  # the §5B menu is supplied
    # but NONE of the structured/catalog scaffolding K1 must not see:
    assert "MEASURES:" not in p
    assert "DEFINITION:" not in p
    assert "FIRED PATTERN" not in p


def test_raw_artifact_without_artifact_raises():
    import pytest
    with pytest.raises(ValueError):
        run_p0.build_prompt({"row_id": "y", "input": {}}, condition="raw_artifact")


def test_artifacts_do_not_leak_the_conclusion():
    # Factual records (e.g. "Not Accepted") are fair; words that pre-judge credibility are not.
    leak = ["leakage", "circular", "out-of-distribution", "inadequate", "biased", "overfit",
            "unreliable", "not credible", "spurious", "data leak"]
    for rid, art in RAW_ARTIFACTS.items():
        low = art.lower()
        bad = [w for w in leak if w in low]
        assert not bad, f"{rid} artifact leaks conclusion word(s): {bad}"


def test_all_31_coverage_artifacts_present():
    assert len(RAW_ARTIFACTS) == 31
    assert all(isinstance(v, str) and len(v) > 60 for v in RAW_ARTIFACTS.values())
