"""The decision model's shapes, against the two canonical cases.

If an implementation choice contradicts either case, the case wins.

**Case 1 — Morrison.** The source already decided. The record is `extracted`:
actor is Morrison's team, timestamp is the source's, and its warrant is the
ANCHOR — the sha-pinned passage stating the acceptance. No signature from
Morrison exists or is expected; the paper is their attestation.

**Case 2 — Johnson.** No acceptance exists in the source, so the reviewer renders
one: `asserted`, actor is the reviewer, and its warrant is a DECISION SIGNATURE
with role `deciding-engineer`.

The invariant both demonstrate: **signatures attach to acts, not actors.** An
absent author is cited via an anchor, never impersonated.

The layer/record separation is deliberate and is asserted below: an
`encoder-of-record` signature covers the decision LAYER as an act of
transcription-attestation. Whether a package needs one is a COMPLETENESS
question owned by the protocol check — never a per-record shape requirement on
extracted entries. So Morrison's record satisfies the shape by its anchor alone.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from rdflib import Graph

from uofa_cli import paths
from uofa_cli.shacl_friendly import _load_data_graph

REPO = Path(__file__).resolve().parents[1]
V09 = "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.9.jsonld"


@pytest.fixture(scope="module")
def shapes() -> Graph:
    g = Graph()
    for p in paths.all_shacl_schemas():
        g.parse(str(p), format="turtle")
    return g


#: The messages this module owns. A minimal fixture document legitimately fails
#: unrelated shapes (`conformsToProfile`, COU, and the rest of the profile
#: dispatcher), so asserting on the global `conforms` verdict would make every
#: test here pass or fail for reasons that have nothing to do with decisions.
#: Filtering to our own messages is what keeps these assertions about the thing
#: they name.
_OURS = (
    "must name the actor",
    "must carry decidedAt",
    "decisionProvenance must be",
    "decisionScope must come from the closed set",
    "must cite the source passage",
    "must carry a decision signature",
    "must name where in the source",
    "must pin the passage by sha256",
    "must declare its role",
    "must name who signed",
    "binds the RECOMPUTED measurement hash",
)


def _validate(node, shapes, tmp_path, extra=None):
    """Returns (our_violations, full_text). `conforms` is deliberately not
    returned: this suite asks whether the DECISION shapes fired, never whether a
    stub document satisfies the whole vocabulary."""
    doc = {"@context": V09, "id": "urn:uofa:t", "type": "UnitOfAssurance"}
    if node is not None:
        doc["hasDecisionRecord"] = node
    doc.update(extra or {})
    p = tmp_path / "p.jsonld"
    p.write_text(json.dumps(doc), encoding="utf-8")
    from pyshacl import validate
    _conforms, _g, text = validate(data_graph=_load_data_graph(p), shacl_graph=shapes)
    return [m for m in _OURS if m in text], text


def _anchor(sha="a" * 64, locator="p.12 §3.2"):
    return {"type": "SourceAnchor", "anchorLocator": locator, "anchorSha256": sha}


def _signature(role="reviewer", who="Demo Reviewing Engineer"):
    return {"type": "DecisionSignature", "signatureRole": role,
            "signerIdentity": who, "measurementHash": "b" * 64}


def MORRISON():
    """Case 1: the source decided; the anchor is their attestation."""
    return {"type": "DecisionRecord", "outcome": "Accepted",
            "actor": "https://example.org/org/morrison-team",
            "role": "Morrison et al. 2019",
            "decidedAt": "2019-06-01T00:00:00Z",
            "decisionProvenance": "extracted",
            "decisionScope": "acceptance-of-model",
            "decisionAnchor": _anchor()}


def JOHNSON():
    """Case 2: no acceptance in the source; the reviewer renders one."""
    return {"type": "DecisionRecord", "outcome": "Accepted",
            "actor": "https://example.org/org/demo-reviewing-engineer",
            "role": "Demo Reviewing Engineer",
            "decidedAt": "2026-09-09T10:00:00Z",
            "decisionProvenance": "asserted",
            "decisionScope": "acceptance-of-model",
            "hasDecisionSignature": _signature("reviewer")}


# ── the two canonical cases ─────────────────────────────────────────────────

def test_case_1_morrison_extracted_with_anchor_conforms(shapes, tmp_path):
    ours, text = _validate(MORRISON(), shapes, tmp_path)
    assert not ours, f"the canonical extracted case was refused: {ours}" 


def test_case_2_johnson_asserted_with_signature_conforms(shapes, tmp_path):
    ours, text = _validate(JOHNSON(), shapes, tmp_path)
    assert not ours, f"the canonical asserted case was refused: {ours}" 


def test_the_three_entry_stack_conforms(shapes, tmp_path):
    """Extracted acceptance + asserted concurrence, records accumulating.

    `hasDecisionRecord` is repeatable and append-only: a package may carry the
    source's acceptance, an independent concurrence, and a program approval,
    each with its own actor, timestamp and scope.
    """
    concurrence = dict(JOHNSON())
    concurrence["decisionScope"] = "concurrence-with-prior-decision"
    concurrence["hasDecisionSignature"] = _signature("reviewer")
    ours, text = _validate([MORRISON(), concurrence], shapes, tmp_path)
    assert not ours, f"the three-entry stack was refused: {ours}" 


# ── the refusals, each seen red ─────────────────────────────────────────────

def test_an_ownerless_decision_refuses(shapes, tmp_path):
    """A verdict with no actor is a judgment nobody made."""
    rec = JOHNSON(); rec.pop("actor")
    ours, text = _validate(rec, shapes, tmp_path)
    assert ours, 'no decision-shape violation was raised'
    assert "must name the actor" in text


def test_a_decision_without_a_timestamp_refuses(shapes, tmp_path):
    rec = JOHNSON(); rec.pop("decidedAt")
    ours, text = _validate(rec, shapes, tmp_path)
    assert ours, 'no decision-shape violation was raised'
    assert "decidedAt" in text


def test_an_asserted_decision_without_a_signature_refuses(shapes, tmp_path):
    """Its actor participates in this package's production, so it signs."""
    rec = JOHNSON(); rec.pop("hasDecisionSignature")
    ours, text = _validate(rec, shapes, tmp_path)
    assert ours, 'no decision-shape violation was raised'
    assert "must carry a decision signature" in text


def test_an_extracted_decision_without_an_anchor_refuses(shapes, tmp_path):
    """Case 1's warrant removed: the claim that Morrison decided, uncited."""
    rec = MORRISON(); rec.pop("decisionAnchor")
    ours, text = _validate(rec, shapes, tmp_path)
    assert ours, 'no decision-shape violation was raised'
    assert "must cite the source passage" in text


def test_an_anchor_without_its_sha_refuses(shapes, tmp_path):
    """Pinning is what separates transcription from invention."""
    rec = MORRISON(); rec["decisionAnchor"] = {"type": "SourceAnchor",
                                               "anchorLocator": "p.12 §3.2"}
    ours, text = _validate(rec, shapes, tmp_path)
    assert ours, 'no decision-shape violation was raised'
    assert "sha256" in text


def test_an_unknown_provenance_refuses(shapes, tmp_path):
    rec = JOHNSON(); rec["decisionProvenance"] = "inferred"
    ours, text = _validate(rec, shapes, tmp_path)
    assert ours, 'no decision-shape violation was raised'
    assert "decisionProvenance must be" in text


def test_an_unknown_scope_refuses(shapes, tmp_path):
    rec = JOHNSON(); rec["decisionScope"] = "vibes"
    ours, text = _validate(rec, shapes, tmp_path)
    assert ours, 'no decision-shape violation was raised'
    assert "decisionScope must come from the closed set" in text


def test_a_signature_without_a_role_refuses(shapes, tmp_path):
    """The role is written by the signer from `--as`; its absence is malformed."""
    rec = JOHNSON()
    rec["hasDecisionSignature"] = {"type": "DecisionSignature",
                                   "signerIdentity": "X", "measurementHash": "b" * 64}
    ours, text = _validate(rec, shapes, tmp_path)
    assert ours, 'no decision-shape violation was raised'
    assert "must declare its role" in text


def test_an_unknown_signature_role_refuses(shapes, tmp_path):
    rec = JOHNSON()
    rec["hasDecisionSignature"] = _signature("rubber-stamper")
    ours, text = _validate(rec, shapes, tmp_path)
    assert ours, 'no decision-shape violation was raised'
    assert "closed set" in text


# ── the separation the two layers make ──────────────────────────────────────

def test_an_extracted_record_needs_no_encoder_signature_at_the_shape(shapes, tmp_path):
    """**Layer, not record.** Morrison's record conforms on its anchor alone.

    The `encoder-of-record` signature attests the ACT of transcription and lives
    at the decision layer; whether a package requires one to be complete is the
    protocol check's business. Asserting it here would make the shape refuse a
    package the constitution permits — and would confuse a completeness question
    with a well-formedness one.
    """
    ours, text = _validate(MORRISON(), shapes, tmp_path)
    assert not ours, f"the shape demanded more than the anchor: {ours}"
    assert "encoder-of-record" not in text


# ── the derived fork, and its totality ──────────────────────────────────────

class TestDerivedFork:
    """`decisionProvenance` is a READING of the anchor's form, never a second
    declaration — so the two cannot disagree. Two sources of truth for one fact
    is the disease; deriving one from the other is the cure.

    Filed with the design: Credenza's `Anchor` encoded this distinction months
    before this week existed to need it — *"anchoring a judgment to a passage
    would assert that the source said something it did not."* Two independent
    design paths converging on the same boundary is evidence the boundary is
    real rather than invented.
    """

    def test_a_ledger_address_is_an_act_of_judgment(self):
        from uofa_cli.excel_mapper import _decision_provenance
        assert _decision_provenance("ledger://demo-reviewer/entry-17") == "asserted"

    def test_a_passage_is_something_the_source_stated(self):
        from uofa_cli.excel_mapper import _decision_provenance
        assert _decision_provenance("p.12 §3.2") == "extracted"

    def test_an_archive_member_is_also_extracted(self):
        from uofa_cli.excel_mapper import _decision_provenance
        assert _decision_provenance("archive://bundle.zip/run/out.csv") == "extracted"

    def test_no_anchor_means_asserted_because_a_person_entered_it(self):
        """This once asserted that an anchorless decision carried NO fork.

        The reading was that absent and unclassifiable are different, and the
        emitter should report the missing fact rather than invent a default.
        That is true of facts; it was false of this one. A workbook decision
        citing no source is one a live person filled in -- the fork is not
        missing, it is `asserted`, and it was derivable all along.

        Leaving it absent had a cost that only showed up at the gate: the seal
        check compared against the string "asserted", so a record that DECLARED
        its fork was refused and a record that declared nothing was let through.
        Omission became the way past the constitutional boundary, and the excel
        path took it by default. The fork is now always stated; what varies is
        which one.
        """
        from uofa_cli.excel_mapper import _decision_provenance
        assert _decision_provenance("") == "asserted"
        assert _decision_provenance(None) == "asserted"
        assert _decision_provenance("   ") == "asserted"

    def test_an_absent_fork_refuses_the_seal_rather_than_being_exempt(self):
        """The gate-side half, which is what makes the emission change safe.

        A third-party emitter can still produce a forkless record. The backstop
        refuses it by name instead of quietly treating it as "not asserted",
        so the hole cannot be reopened from outside this repo.
        """
        from uofa_cli import sign_roles
        doc = {"hasDecisionRecord": {"outcome": "Accepted",
                                     "actor": "https://ex.org/org/board"}}
        assert len(sign_roles.unclassified_records(doc)) == 1
        # and a signature does not rescue it: the fork is what says whether a
        # signature was even the right warrant.
        doc["hasDecisionRecord"]["hasDecisionSignature"] = {"signatureValue": "ed25519:x"}
        assert len(sign_roles.unclassified_records(doc)) == 1
        # a stated fork is classified, signed or not
        doc["hasDecisionRecord"]["decisionProvenance"] = "extracted"
        assert sign_roles.unclassified_records(doc) == []

    def test_an_unclassifiable_form_refuses_and_names_itself(self):
        """The guard that makes the derivation trustworthy.

        Without it the empty-value genus arrives wearing a URI: an unknown
        scheme would fall through to a branch nobody chose, and the decision
        would carry a provenance no one derived.
        """
        from uofa_cli.excel_mapper import AnchorFormError, _decision_provenance
        with pytest.raises(AnchorFormError) as exc:
            _decision_provenance("https://example.org/not-an-anchor")
        assert "https" in str(exc.value)
        assert "Refusing to guess" in str(exc.value)
