"""A9.1 source pins: two types, and the round-trip that must not break.

The pin distinction is the ruling of 2026-08-11: an artifact pin claims "this
exact content was read" and supports re-derivation; an occasion pin claims "this
subject was measured at this time" and supports re-performance only. Conflating
them lets a consumer treat a difference between two performances as evidence of
tampering.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from uofa_cli.furnishers import pins

REPO = Path(__file__).resolve().parents[1]
_GEMMA_PIN = REPO / "tests" / "fixtures" / "model_cards" / "google__gemma-3-27b-it.pin.json"


def test_the_two_pin_types_claim_different_things():
    art = pins.artifact_pin("https://example.org/card", "text", fetched_at="2026-08-11")
    occ = pins.occasion_pin("openai/gpt-5.6", measured_at="2026-08-11T00:00:00Z")
    assert art["supports"] == "re-derivation"
    assert occ["supports"] == "re-performance"
    assert occ["verifiedByAssessor"] is False, (
        "a hosted endpoint's identity is asserted by its provider; recording it "
        "as verified would claim an assurance nobody holds")


def test_one_occasion_pin_makes_the_bundle_not_re_derivable():
    """The weaker claim governs. A bundle mixing a pinned card with a live run is
    re-derivable in part, and the card must not promise more than that."""
    bundle = {"id": "x"}
    pins.attach(bundle, pins.artifact_pin("https://example.org/c", "t", fetched_at="d"))
    assert pins.re_derivable(bundle)
    pins.attach(bundle, pins.occasion_pin("m", measured_at="t"))
    assert not pins.re_derivable(bundle)


def test_no_pins_is_not_re_derivable():
    """Absence of evidence is not a re-derivability claim."""
    assert not pins.re_derivable({"id": "x"})


@pytest.mark.skipif(not _GEMMA_PIN.exists(), reason="gemma pin fixture absent")
def test_the_revision_recorded_is_the_blob_not_the_repo_sha():
    """The repo sha moves when ANY file changes, so pinning it marks a
    byte-identical card stale on a weights re-upload -- a badge going amber for a
    reason the reader cannot see and the card cannot support."""
    pinned = json.loads(_GEMMA_PIN.read_text())
    assert pinned["readmeBlobOid"] != pinned["repoSha"], (
        "fixture must demonstrate the two differ, or it proves nothing")

    pin = pins.artifact_pin("https://huggingface.co/google/gemma-3-27b-it",
                            "card text", fetched_at="2026-08-11",
                            revision=pinned["readmeBlobOid"],
                            revision_kind="readme-blob-oid")
    assert pin["revision"] == pinned["readmeBlobOid"]
    assert pin["revision"] != pinned["repoSha"]
    assert pin["revisionKind"] == "readme-blob-oid"


def test_pins_survive_an_rdflib_round_trip(tmp_path):
    """MANDATORY. This is the exact bug class that once made every package in the
    repo unparseable while C1, C2 and C3 all stayed green -- a provenance record
    put vocabulary term names in JSON-LD key position and `generatedAtTime:
    "run-context"` was read as an xsd:dateTime. One e2e test out of 2,681 caught
    it. Nested pin objects are the same shape of risk.
    """
    rdflib = pytest.importorskip("rdflib")

    bundle = {
        "@context": {"@vocab": "https://uofa.net/vocab#"},
        "id": "https://example.org/uofa/pinned",
        "type": "UnitOfAssurance",
    }
    pins.attach(bundle, pins.artifact_pin(
        "https://huggingface.co/google/gemma-3-27b-it", "card text",
        fetched_at="2026-08-11", revision="fdce721ee5de878029a086bcc7f6cd7f183fab32",
        revision_kind="readme-blob-oid"))
    pins.attach(bundle, pins.occasion_pin(
        "openai/gpt-5.6", measured_at="2026-08-11T00:00:00Z",
        version_claim="gpt-5.6", claimed_by="openai"))

    path = tmp_path / "bundle.jsonld"
    path.write_text(json.dumps(bundle))

    graph = rdflib.Graph()
    graph.parse(str(path), format="json-ld")        # must not raise
    triples = list(graph)
    assert triples, "pins produced no triples; the terms did not expand"

    predicates = {str(p) for _s, p, _o in triples}
    for term in ("pinType", "contentHash", "supports", "subjectId"):
        assert any(term in p for p in predicates), (
            f"{term} did not expand to a uofa: IRI -- @vocab is doing this work, "
            "and nothing may be added to spec/context/v0.5.jsonld to 'fix' it: "
            "that file is inlined before hashing (AGENTS.md §13)")


def test_no_pin_value_fails_datatype_conversion(tmp_path, caplog):
    """No pin value may hit a term whose datatype it cannot satisfy.

    The historical failure was `generatedAtTime: "run-context"` against an
    xsd:dateTime term. **This rdflib no longer raises on that** -- it logs
    "Failed to convert Literal lexical form to value" and keeps the lexical
    form, so a test that merely parses would pass vacuously and prove nothing.
    Verified by reproducing the original shape: it parses, warns, and returns
    the string.

    So the assertion is on the LOG, which is where the signal actually is now.
    """
    rdflib = pytest.importorskip("rdflib")
    bundle = {"@context": {"@vocab": "https://uofa.net/vocab#"}, "id": "https://example.org/u"}
    pins.attach(bundle, pins.artifact_pin("https://example.org/c", "t",
                                          fetched_at="2026-08-11"))
    pins.attach(bundle, pins.occasion_pin("m", measured_at="2026-08-11T00:00:00Z"))
    path = tmp_path / "b.jsonld"
    path.write_text(json.dumps(bundle))

    with caplog.at_level(logging.WARNING):
        rdflib.Graph().parse(str(path), format="json-ld")
    bad = [r.getMessage() for r in caplog.records
           if "Failed to convert" in r.getMessage()]
    assert not bad, f"a pin value failed datatype conversion: {bad}"
