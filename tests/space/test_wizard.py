"""S2 wizard tests — step transitions as plain functions, no Gradio launch."""

from __future__ import annotations

from pathlib import Path

import pytest

from space import wizard
from space._extract_hooks import failing_extract
from space.pipeline import DEBUG_RESPONSE_FILE, FailureKind


def _src(tmp_path: Path, text: str, name: str = "evidence.txt") -> Path:
    d = tmp_path / "src"
    d.mkdir(exist_ok=True)
    (d / name).write_text(text, encoding="utf-8")
    return d


def test_prepare_routes_vv40_confidently(tmp_path):
    src = _src(tmp_path, "ASME V&V 40 assessment: context of use and model risk for a medical device.")
    out = wizard.prepare([src])
    assert out.ok
    d = out.payload["decision"]
    assert d.primary == "vv40"
    assert not wizard.requires_confirmation(d)


def test_prepare_low_confidence_on_generic(tmp_path):
    src = _src(tmp_path, "Quarterly revenue summary and headcount planning notes.")
    out = wizard.prepare([src])
    assert out.ok
    assert wizard.requires_confirmation(out.payload["decision"]) is True


def test_prepare_read_error_on_empty_dir(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    out = wizard.prepare([empty])
    assert not out.ok
    assert out.kind == FailureKind.READ_ERROR


def test_extract_step_success_returns_rows(tmp_path):
    src = _src(tmp_path, "ASME V&V 40 context of use, model risk.")
    prep = wizard.prepare([src])
    out = wizard.extract(prep.payload["corpus"], "vv40", model="mock")
    assert out.ok
    assert len(out.payload["rows"]) == 13
    assert {r["status"] for r in out.payload["rows"]} == {"assessed"}  # mock default


def test_extract_step_failure(tmp_path):
    src = _src(tmp_path, "ASME V&V 40 context of use.")
    prep = wizard.prepare([src])
    out = wizard.extract(prep.payload["corpus"], "vv40", model="mock", extract_fn=failing_extract)
    assert not out.ok
    assert out.kind == FailureKind.EXTRACT_ERROR


def test_finalize_applies_edits_and_tears_down(tmp_path):
    src = _src(tmp_path, "ASME V&V 40 context of use, model risk.")
    prep = wizard.prepare([src])
    ext = wizard.extract(prep.payload["corpus"], "vv40", model="mock")
    edits = {"Use error": "not-assessed"}
    out = wizard.finalize(ext.payload["result"], "vv40", edits, warnings=prep.payload["warnings"])
    assert out.ok, out.user_message
    c = out.payload["completeness"]
    assert "Use error" in c["missing"]
    assert c["n_assessed"] == 12
    assert "Accepted" not in out.payload["headline"]
    # finalize owns + tears down its work dir and scrubs the /tmp debug file.
    assert not DEBUG_RESPONSE_FILE.exists()


def test_requires_confirmation_helper():
    class D:
        low_confidence = True

    assert wizard.requires_confirmation(D()) is True
    D.low_confidence = False
    assert wizard.requires_confirmation(D()) is False


def test_app_builds():
    """Constructing the Blocks validates imports, gr.render usage, and wiring."""
    gr = pytest.importorskip("gradio")
    from space import app

    demo = app.build()
    assert isinstance(demo, gr.Blocks)
