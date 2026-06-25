"""`uofa report <model id/URL>`: source detection, the LLM/deterministic extraction
paths and their honest provenance labels, the no-card readout, default bundle
saving, and the tracked LLM-vs-deterministic divergence.

Network is never required: id-mode tests monkeypatch the fetch, and the
deterministic path runs on the committed example card text. Engine-dependent
assertions are skipped when the Jena JAR is not built.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from uofa_cli import card_bundle, hf_card, paths
from uofa_cli.commands import report

_ROOT = paths.find_repo_root()
_EX = _ROOT / "packs" / "mrm-nist" / "examples"
sys.path.insert(0, str(_EX))
from curated_cards import CARDIFF  # noqa: E402

_HAS_JAR = paths.jar_path().exists()
_needs_engine = pytest.mark.skipif(not _HAS_JAR, reason="weakener engine JAR not built")


# ── source detection ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("source,kind,value", [
    ("model.jsonld", "file", "model.jsonld"),                       # bundle extension
    ("acme/widget", "id", "acme/widget"),                           # bare id
    ("https://huggingface.co/acme/widget", "id", "acme/widget"),    # model URL
    ("https://huggingface.co/acme/widget/tree/main", "id", "acme/widget"),  # URL w/ subpath
    ("http://www.huggingface.co/acme/widget?x=1", "id", "acme/widget"),     # scheme/host/query
])
def test_resolve_source_classifies(source, kind, value):
    assert hf_card.resolve_source(source) == (kind, value)


def test_resolve_source_existing_file_is_file_mode():
    f = _EX / "twitter-roberta-sentiment" / "card.md"
    assert hf_card.resolve_source(str(f)) == ("file", str(f))


@pytest.mark.parametrize("source", [
    "https://huggingface.co/spaces/owner/demo",
    "https://huggingface.co/datasets/owner/data",
])
def test_resolve_source_rejects_non_model_urls(source):
    kind, msg = hf_card.resolve_source(source)
    assert kind == "error" and ("space" in msg or "dataset" in msg)


def test_resolve_source_rejects_garbage():
    kind, _ = hf_card.resolve_source("this is not a source")
    assert kind == "error"


# ── extraction paths + provenance labels ─────────────────────────────────────

def _card_text() -> str:
    return (_EX / "twitter-roberta-sentiment" / "card.md").read_text(encoding="utf-8")


def test_deterministic_path_labels_itself_approximate():
    bundle, prov = card_bundle.card_to_bundle(
        _card_text(), "mrm-nist", model_id="cardiffnlp/twitter-roberta-base-sentiment",
        allow_llm=False)
    assert prov == card_bundle.PROV_HEURISTIC
    assert "approximate" in prov
    factors = bundle["hasCredibilityFactor"]
    assert len(factors) == 17
    assert all(f["factorStandard"] == "NIST-AI-RMF-1.0" for f in factors)  # the gotcha fix


def _fake_extract_result():
    return SimpleNamespace(
        assessment_summary={"project_name": "acme/widget", "cou_name": "Demo use",
                            "model_risk_level": "MRL 3", "has_uq": "No"},
        model_and_data=[], validation_results=[],
        credibility_factors=[{"factor_type": "Intended use", "status": "assessed"},
                             {"factor_type": "Known limitations", "status": "not-assessed"}],
        decision={"rationale": "x"},
    )


def test_llm_path_labels_the_model(monkeypatch):
    monkeypatch.setattr("uofa_cli.llm_extractor.extract", lambda *a, **k: _fake_extract_result())
    bundle, prov = card_bundle.card_to_bundle(
        _card_text(), "mrm-nist", model_id="acme/widget", model="testbackend/m1", allow_llm=True)
    assert prov == "LLM extraction - testbackend/m1"
    # the disclosed posture is forced regardless of what the model returned
    assert bundle["modelRiskLevel"] == card_bundle.MRM_NIST_ASSUMED_MRL


def test_llm_failure_falls_back_to_heuristic_with_an_honest_label(monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("backend unreachable")
    monkeypatch.setattr("uofa_cli.llm_extractor.extract", _boom)
    _bundle, prov = card_bundle.card_to_bundle(
        _card_text(), "mrm-nist", model_id="acme/widget", model="testbackend/m1", allow_llm=True)
    assert prov == card_bundle.PROV_HEURISTIC_FALLBACK
    assert "fell back" in prov and "approximate" in prov


# ── no-card: one consistent framing, live and committed ──────────────────────

def test_empty_card_yields_zero_assessed():
    bundle, _ = card_bundle.card_to_bundle("", "mrm-nist", model_id="x/y", allow_llm=False)
    statuses = {f["factorType"]: f["factorStatus"] for f in bundle["hasCredibilityFactor"]}
    assert not any(s == "assessed" for s in statuses.values())


def test_committed_chemberta_carries_the_no_card_framing():
    # the committed gallery example must tell the same story a live no-card run does
    state = json.loads((_EX / "chemberta-77m-mtr" / "state.json").read_text(encoding="utf-8"))
    assert state["context"]["documentation_status"] == "none"
    html = (_EX / "chemberta-77m-mtr" / "reviewer.html").read_text(encoding="utf-8")
    assert "No model card published" in html


# ── the LLM-vs-deterministic divergence is tracked, not discovered live ───────

def test_deterministic_vs_curated_divergence_is_the_known_gap():
    # Curated statuses are the faithful reading; the deterministic scan is approximate.
    # This pins the exact gap on the committed cardiff card so any parser drift fails
    # here (visible) instead of surfacing in front of someone. The two known
    # divergences show both failure modes: an over-credit and an under-credit.
    curated = {n: "assessed" for n in CARDIFF.assessed}
    curated.update({n: "not-assessed" for n in CARDIFF.not_assessed})
    curated.update({n: "scoped-out" for n in CARDIFF.scoped_out})
    det = card_bundle.deterministic_factor_statuses(_card_text(), "mrm-nist")
    diverged = {n for n in curated if det[n] != curated[n]}
    assert diverged == {"Evaluation metrics", "Intended use"}, (
        f"deterministic parser drifted from the curated baseline: {sorted(diverged)} "
        "(update the recorded gap intentionally, or fix the parser)")


# ── id mode end to end (needs the engine) ────────────────────────────────────

def _args(source, **over):
    base = dict(source=source, format="text", output=None, active_packs=["mrm-nist"],
                pack=["mrm-nist"], repo_root=None, deterministic=True, revision=None,
                save_bundle=None, no_save_bundle=True, extract_backend=None,
                extract_model=None, extract_base_url=None)
    base.update(over)
    return argparse.Namespace(**base)


@_needs_engine
def test_run_id_mode_renders_with_provenance(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr("uofa_cli.hf_card.fetch_card",
                        lambda mid, rev=None: hf_card.CardFetch(_card_text(), "ok"))
    rc = report.run(_args("cardiffnlp/twitter-roberta-base-sentiment",
                          save_bundle=tmp_path / "b.jsonld", no_save_bundle=False))
    assert rc == 0
    out = capsys.readouterr().out
    assert "Heuristic" in out and "approximate" in out      # provenance disclosed
    assert "Risk posture" in out and "MRL 3" in out          # MRL assumption disclosed
    assert (tmp_path / "b.jsonld").exists()                   # bundle saved (auditable source)


@_needs_engine
def test_run_id_mode_no_card_leads_with_notice(monkeypatch, capsys):
    monkeypatch.setattr("uofa_cli.hf_card.fetch_card",
                        lambda mid, rev=None: hf_card.CardFetch("", "notfound", "no card (404)."))
    rc = report.run(_args("DeepChem/ChemBERTa-77M-MTR"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "NO MODEL CARD PUBLISHED" in out
    assert "0%" in out


def test_run_id_mode_gated_is_a_hard_failure(monkeypatch):
    monkeypatch.setattr("uofa_cli.hf_card.fetch_card",
                        lambda mid, rev=None: hf_card.CardFetch("", "gated", "private or gated (403)."))
    assert report.run(_args("acme/private")) == 1
