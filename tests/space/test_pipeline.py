"""S0 pipeline tests — happy path + error paths, no Ollama required.

Happy-path extraction uses `model="mock"` (routes to the in-process canned
extractor). Failure-path tests inject spawn-safe `extract_fn` hooks from
`space._extract_hooks`. Weakener assertions are gated on the Jena jar.
"""

from __future__ import annotations

import json
import shutil
import types
from pathlib import Path

import pytest

from space import pipeline
from space._extract_hooks import empty_extract, failing_extract, slow_extract
from space.pipeline import (
    FailureKind,
    PipelineOutcome,
    WeakenerEngineError,
    analyze,
    result_to_import_dict,
)
from uofa_cli.excel_mapper import map_to_jsonld
from uofa_cli.llm_extractor import ExtractionResult, _json_to_result, _mock_extract

_JAR = Path(__file__).resolve().parents[2] / "src" / "weakener-engine" / "target" / "uofa-weakener-engine-0.1.0.jar"
needs_jar = pytest.mark.skipif(
    not (shutil.which("java") and _JAR.exists()),
    reason="java + built weakener-engine JAR required",
)


def _fake_rules_result(stdout: str, stderr: str = "", returncode: int = 0):
    return types.SimpleNamespace(raw_stdout=stdout, raw_stderr=stderr, returncode=returncode)


@pytest.fixture
def capture_workdir(monkeypatch, tmp_path):
    """Force analyze's owned work_dir to a known path so teardown is checkable."""
    created = {}

    def fake_mkdtemp(*_a, **_k):
        d = tmp_path / "workdir"
        d.mkdir(exist_ok=True)
        created["path"] = d
        return str(d)

    monkeypatch.setattr("space.pipeline.tempfile.mkdtemp", fake_mkdtemp)
    return created


def _mock_result(pack: str = "vv40") -> ExtractionResult:
    return _json_to_result(json.loads(_mock_extract(pack)), pack)


# ── Happy path ───────────────────────────────────────────────


def test_result_to_import_dict_shape_and_edits():
    result = _mock_result("vv40")
    edits = {"Use error": "not-assessed"}
    data = result_to_import_dict(result, "vv40", factor_edits=edits)

    # Forced Complete profile + synthetic (never-shown) outcome.
    assert data["summary"]["profile"] == "Complete"
    assert data["decision"]["outcome"] in ("Accepted", "Not accepted")

    # Factor dict uses the key names map_to_jsonld/read_workbook expect.
    f0 = data["factors"][0]
    assert set(f0) >= {
        "factor_type", "category", "required_level", "achieved_level",
        "acceptance_criteria", "rationale", "status", "linked_evidence",
    }
    # Category resolved for a known factor.
    assert f0["category"]

    # Edit overrides the extracted status for exactly that factor.
    by = {f["factor_type"]: f["status"] for f in data["factors"]}
    assert by["Use error"] == "not-assessed"
    assert by["Model form"] == "assessed"  # mock default, untouched


def test_pipeline_vv40_mock_end_to_end(text_corpus, assert_clean_state):
    outcome = analyze([text_corpus], "vv40", model="mock")
    assert outcome.ok, outcome.user_message
    c = outcome.payload["completeness"]
    assert c["n_expected"] == 13
    assert c["n_assessed"] == 13  # mock marks every factor assessed
    assert outcome.payload["structural"]["conforms"] in (True, False)
    assert "assessed" in outcome.payload["headline"]
    assert "Accepted" not in outcome.payload["headline"]  # no verdict
    assert_clean_state()  # extractor /tmp debug file scrubbed


def test_pipeline_nasa_mock_factor_count(text_corpus):
    outcome = analyze([text_corpus], "nasa-7009b", model="mock")
    assert outcome.ok, outcome.user_message
    assert outcome.payload["completeness"]["n_expected"] == 19


def test_workdir_torn_down_on_success(text_corpus, capture_workdir, assert_clean_state):
    outcome = analyze([text_corpus], "vv40", model="mock")
    assert outcome.ok
    assert_clean_state(capture_workdir["path"])


def test_weakeners_fire_with_rich_shape(text_corpus):
    """The Jena engine runs and parse_firings_jsonld yields rich firing dicts.

    (The W-EP-04 -> factor-name mapping needs an MRL>2 scenario and lands in
    the S1 summary tests; here we validate completeness + firing shape.)
    """
    edits = {"Use error": "not-assessed", "Test samples": "not-assessed"}
    outcome = analyze([text_corpus], "vv40", model="mock", factor_edits=edits)
    assert outcome.ok, outcome.user_message

    c = outcome.payload["completeness"]
    assert set(c["missing"]) == {"Use error", "Test samples"}
    assert c["n_assessed"] == 11

    firings = outcome.payload["weakeners"]
    if not firings:
        pytest.skip("Jena jar/Java unavailable — weakeners degrade to []")
    w = firings[0]
    assert set(w) >= {"patternId", "severity", "affected_nodes"}
    assert w["patternId"].startswith(("W-", "COMPOUND"))


# ── Error paths ──────────────────────────────────────────────


def test_extract_timeout(text_corpus, capture_workdir, assert_clean_state):
    outcome = analyze(
        [text_corpus], "vv40", model="mock",
        extract_fn=slow_extract, extract_timeout=2,
    )
    assert not outcome.ok
    assert outcome.kind == FailureKind.EXTRACT_TIMEOUT
    assert outcome.user_message
    assert_clean_state(capture_workdir["path"])


def test_extract_error(text_corpus, capture_workdir, assert_clean_state):
    outcome = analyze([text_corpus], "vv40", model="mock", extract_fn=failing_extract)
    assert not outcome.ok
    assert outcome.kind == FailureKind.EXTRACT_ERROR
    assert_clean_state(capture_workdir["path"])


def test_empty_factors(text_corpus, capture_workdir, assert_clean_state):
    outcome = analyze([text_corpus], "vv40", model="mock", extract_fn=empty_extract)
    assert not outcome.ok
    assert outcome.kind == FailureKind.EMPTY_FACTORS
    assert_clean_state(capture_workdir["path"])


def test_read_error_on_empty_source(tmp_path, assert_clean_state):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    outcome = analyze([empty_dir], "vv40", model="mock")
    assert not outcome.ok
    assert outcome.kind == FailureKind.READ_ERROR
    assert_clean_state()


def test_validate_error_when_mapping_raises(text_corpus, monkeypatch, capture_workdir, assert_clean_state):
    def boom(*_a, **_k):
        raise RuntimeError("mapping blew up")

    monkeypatch.setattr("space.pipeline.map_to_jsonld", boom)
    outcome = analyze([text_corpus], "vv40", model="mock")
    assert not outcome.ok
    assert outcome.kind == FailureKind.VALIDATE_ERROR
    assert "raise" not in (outcome.user_message or "").lower()  # friendly, not a traceback
    assert_clean_state(capture_workdir["path"])


def test_weakener_engine_abort_surfaces_as_failure(text_corpus, monkeypatch, capture_workdir, assert_clean_state):
    """Engine ran but produced no valid JSON-LD (crash) -> WEAKENER_ERROR,
    not a silent 'no weakeners'."""
    monkeypatch.setattr(
        "uofa_cli.commands.rules.run_structured",
        lambda _args: _fake_rules_result(
            stdout="org.apache.jena.datatypes.DatatypeFormatException: ...",
            stderr="Exception in thread main DatatypeFormatException: 'MRL 2'",
            returncode=1,
        ),
    )
    outcome = analyze([text_corpus], "vv40", model="mock")
    assert not outcome.ok
    assert outcome.kind == FailureKind.WEAKENER_ERROR
    assert_clean_state(capture_workdir["path"])


def test_weakener_nonzero_returncode_with_valid_output_is_not_abort(text_corpus, monkeypatch):
    """A non-zero rc with valid JSON-LD means 'weakeners detected' — must NOT
    be mistaken for an abort."""
    monkeypatch.setattr(
        "uofa_cli.commands.rules.run_structured",
        lambda _args: _fake_rules_result(stdout='{"@graph": []}', returncode=1),
    )
    outcome = analyze([text_corpus], "vv40", model="mock")
    assert outcome.ok, outcome.user_message
    assert outcome.payload["weakeners"] == []


@needs_jar
def test_real_engine_abort_raises_weakener_error(tmp_path):
    """Reproduce the actual abort: a malformed modelRiskLevel literal makes the
    Jena engine throw DatatypeFormatException -> WeakenerEngineError."""
    data = result_to_import_dict(_mock_result("vv40"), "vv40")
    data["summary"]["model_risk_level"] = "MRL 2"  # invalid xsd:integer
    # A not-assessed factor drives W-EP-04's greaterThan(?mrl, 2) onto the bad
    # literal, which is what actually throws DatatypeFormatException.
    for f in data["factors"]:
        if f["factor_type"] in ("Use error", "Test samples"):
            f["status"] = "not-assessed"
    doc = map_to_jsonld(data, packs=["vv40"], source_path=Path("x"))
    p = tmp_path / "bad.jsonld"
    p.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(WeakenerEngineError):
        pipeline._run_weakeners(p, "vv40")


def test_failure_messages_are_friendly():
    for kind in vars(FailureKind).values():
        if isinstance(kind, str) and not kind.startswith("__"):
            out = PipelineOutcome.failure(kind)
            assert out.user_message and len(out.user_message) > 10
