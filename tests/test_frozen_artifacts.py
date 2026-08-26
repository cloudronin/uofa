"""Byte-freeze: shipped artifacts the praxis record cites are not editable.

A session working on the decision model will find these artifacts missing the
current model's fields and will be tempted to "fix" them. That temptation is
exactly what this pins against. The praxis record's LEDGER counts, worked
examples, and cross-version-verify claim are claims about *these bytes*; editing
them silently invalidates published claims and breaks seals that no longer have
a signer available to renew them.

The correction path is a SIBLING (see `packs/vv40/examples/morrison-v09/`), never
an edit. Re-issuing a shipped example under a newer context is available and not
owed, and it is the author's deliberate act in a named session.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PINS = json.loads((REPO_ROOT / "tests" / "fixtures" / "frozen_artifact_pins.json")
                  .read_text(encoding="utf-8"))["pins"]


@pytest.mark.parametrize("rel", sorted(PINS))
def test_frozen_artifact_bytes_are_unchanged(rel):
    path = REPO_ROOT / rel
    assert path.is_file(), f"{rel} is frozen and must not be moved or deleted"
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual == PINS[rel], (
        f"{rel} has been edited.\n"
        f"  expected sha256 {PINS[rel]}\n"
        f"  actual   sha256 {actual}\n\n"
        f"These bytes are cited by the praxis record and their seal cannot be "
        f"renewed by this session. If the decision model has moved on, ship a "
        f"SIBLING under the new context -- as morrison-v09 does -- and leave "
        f"these bytes alone. Re-issuance is available, not owed."
    )


def test_the_sibling_carries_the_new_model_so_the_original_need_not():
    """The freeze only holds if the correction path actually exists."""
    for cou in ("cou1", "cou2"):
        sib = (REPO_ROOT / "packs/vv40/examples/morrison-v09" / cou
               / f"uofa-morrison-v09-{cou}.jsonld")
        assert sib.is_file(), "the freeze needs somewhere for corrections to go"
        rec = json.loads(sib.read_text(encoding="utf-8"))["hasDecisionRecord"]
        assert rec["decisionProvenance"] == "extracted"
        assert rec["decisionAnchor"]["anchorSha256"].startswith("sha256:")
        assert "hasDecisionSignature" not in rec, \
            "Morrison's team never signed a UofA package; the format must not imply they could"


@pytest.mark.parametrize("cou", ["cou1", "cou2"])
def test_the_siblings_anchor_pin_matches_the_shipped_source(cou):
    """The pin is computed from a real document, never invented.

    An anchor whose digest nobody can reproduce is decoration: it asserts
    "the source says this" while giving the reader no way to check. That would
    make Case 1's whole claim -- transcription, not invention -- unfalsifiable.
    """
    sib = (REPO_ROOT / "packs/vv40/examples/morrison-v09" / cou
           / f"uofa-morrison-v09-{cou}.jsonld")
    rec = json.loads(sib.read_text(encoding="utf-8"))["hasDecisionRecord"]
    src = REPO_ROOT / "packs/vv40/examples/morrison/source" / f"decision_rationale_{cou}.pdf"
    assert src.is_file(), "the anchored source must ship with the anchor"
    expected = "sha256:" + hashlib.sha256(src.read_bytes()).hexdigest()
    assert rec["decisionAnchor"]["anchorSha256"] == expected


def test_the_sibling_does_not_squat_on_the_frozen_artifacts_iris():
    """A sibling restates the content; it must not claim the same identity.

    The siblings were first created by copying the originals wholesale, which
    carried their `id` values along -- so two different documents claimed
    `uofa.net/morrison/cou1`, one with the decision fork and one without. No
    test failed: SHACL validates each file alone, and the byte-freeze watches
    the originals, which were untouched. The site's IRI generator caught it,
    and only because it refuses to publish a package count it was not told to
    expect.

    An IRI names one thing. Two documents under one IRI means the identifier has
    stopped identifying -- and here it would have pointed the praxis record's own
    citation at the wrong bytes.
    """
    import json

    for cou in ("cou1", "cou2"):
        original = json.loads(
            (REPO_ROOT / "packs/vv40/examples/morrison" / cou
             / f"uofa-morrison-{cou}.jsonld").read_text(encoding="utf-8"))
        sibling = json.loads(
            (REPO_ROOT / "packs/vv40/examples/morrison-v09" / cou
             / f"uofa-morrison-v09-{cou}.jsonld").read_text(encoding="utf-8"))

        assert original["id"] != sibling["id"], \
            f"{cou}: the sibling squats on the frozen artifact's IRI"
        assert sibling["id"].startswith("https://uofa.net/morrison-v09/")
        assert (original["hasDecisionRecord"]["id"]
                != sibling["hasDecisionRecord"]["id"])

        # The anchor is the one thing that must NOT move: it points at the real
        # shipped archive, and the sha256 pin is computed from that file.
        assert (sibling["hasDecisionRecord"]["decisionAnchor"]["anchorLocator"]
                .startswith("archive://morrison/source/"))
