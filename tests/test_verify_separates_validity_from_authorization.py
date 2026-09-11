"""`verify` must not let a valid signature read as an authorized decision.

**Post-freeze correction, raised 2026-09-11 while scoping the OpenStetho case.**
Separately identifiable from the praxis test set by that date and this filename.

`sign_roles.derive_relation` already computes what a reviewer signature MEANS --
`decider`, `transcription-attestation`, `concurrence`, or `unrelated` -- read off
the record's fork and the signer's identity against the record's actor. It is
carefully written and thoroughly unit-tested. One of those tests
(`test_distinct_identities_that_naive_normalisation_would_collide_stay_distinct`)
names the exact failure this file exists to close:

    verify would simply report `decider` where the truth is `unrelated`, with
    full authority, and no artifact would show the substitution.

**`derive_relation` is not called anywhere in `commands/verify.py`.** The
reporting line is

    result_line(f"{prefix}: {role} signature valid", True, str(actor))

which states a CRYPTOGRAPHIC fact and prints the actor beside it as the detail,
so a reader sees a green tick against a name that the signer may have nothing to
do with. Observed live, before this fix, on a package signed by a freshly
generated key over a decision authored by a machine identity:

      ✓   decision 2: reviewer signature valid  urn:uofa:agent:automated-reviewer

The tool held the answer `unrelated` and did not say it.

Cryptographic validity and authorization are two claims. The signature check
answers "were these bytes signed by the holder of this key". It does not answer
"was this party entitled to make this judgment". Reporting only the first, with
the second's subject printed next to it, invites the reader to conclude both.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from uofa_cli import integrity, sign_roles

REPO = Path(__file__).resolve().parents[1]
CTX = "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.9.jsonld"


def _uofa(*args):
    return subprocess.run([sys.executable, "-m", "uofa_cli", *args],
                          capture_output=True, text=True, cwd=str(REPO))


def _signed_by_a_stranger(tmp_path, actor):
    """A package whose decision signature is valid and whose signer is not the
    actor. Signed through the real command, so nothing here asserts a shape the
    product does not actually produce."""
    doc = {
        "@context": CTX,
        "id": "urn:uofa:authorization-probe",
        "type": "UnitOfAssurance",
        "conformsToProfile": "ProfileMinimal",
        "hasDecisionRecord": {
            "type": "DecisionRecord",
            "outcome": "Accepted",
            "actor": actor,
            "decidedAt": "2026-09-11T00:00:00Z",
            "decisionProvenance": "asserted",
        },
    }
    pkg = tmp_path / "probe.jsonld"
    pkg.write_text(json.dumps(doc, indent=2), encoding="utf-8")

    key, pub = integrity.generate_keypair(tmp_path / "stranger.key")
    out = tmp_path / "signed.jsonld"
    r = _uofa("sign", str(pkg), "--key", str(key), "--as", "issuer,reviewer",
              "-o", str(out))
    assert r.returncode == 0, f"the fixture did not sign: {r.stdout}{r.stderr}"
    return out, pub


def test_the_derivation_this_file_defends_really_is_not_a_pass(tmp_path):
    """The fixture is pointless unless the relation genuinely is not `decider`.

    CORRECTED 2026-09-11 under the trust-boundary ruling: a handle names a person
    and a fingerprint names a key, and nothing in a package binds one to the
    other -- so this is `indeterminate`, NOT `unrelated`. Reporting `unrelated`
    here would state "two different parties", which no check established.
    """
    out, _pub = _signed_by_a_stranger(tmp_path, "https://example.org/org/someone-else")
    doc = json.loads(out.read_text(encoding="utf-8"))
    rec = sign_roles.decision_records(doc)[0]
    signer = rec["hasDecisionSignature"]["signerIdentity"]

    assert sign_roles.derive_relation(rec, signer) == sign_roles.INDETERMINATE
    assert sign_roles.derive_relation(rec, signer) != sign_roles.DECIDER


def test_verify_names_the_authorization_relation_not_only_the_signature(tmp_path):
    """The defect, stated as the assertion that catches it.

    A cryptographically valid signature by a party who authored nothing must not
    be reported as bare success. The reader has to be able to tell the two claims
    apart from the output alone.
    """
    actor = "https://example.org/org/someone-else"
    out, pub = _signed_by_a_stranger(tmp_path, actor)

    r = _uofa("verify", str(out), "--pubkey", str(pub), "--decision-pubkey", str(pub))
    printed = r.stdout + r.stderr

    assert "signature valid" in printed, \
        f"the fixture did not reach the signature check at all:\n{printed}"

    assert (sign_roles.INDETERMINATE in printed
            or "NOT ESTABLISHED" in printed
            or "not assessed" in printed), (
        "verify reported a valid signature and said nothing about authorization. "
        "The signer-actor relationship here is NOT ESTABLISHED and the output "
        "does not carry it:\n" + printed)


def test_the_actor_is_not_presented_as_vouched_for(tmp_path):
    """The narrower half: printing the actor as the DETAIL of a green line is
    what makes a reader read authorization into a cryptographic check.

    Whatever the final wording, the actor must not appear as the sole trailing
    detail of an unqualified success line.
    """
    actor = "https://example.org/org/someone-else"
    out, pub = _signed_by_a_stranger(tmp_path, actor)

    r = _uofa("verify", str(out), "--pubkey", str(pub), "--decision-pubkey", str(pub))
    for line in (r.stdout + r.stderr).splitlines():
        if "signature valid" not in line:
            continue
        if actor in line:
            assert (sign_roles.INDETERMINATE in line
                    or "NOT ESTABLISHED" in line
                    or "not assessed" in line), (
                "the actor is printed as the detail of an unqualified success "
                f"line, which reads as though they were vouched for:\n  {line}")


def test_a_real_decider_still_reads_as_a_pass(tmp_path):
    """The positive counterpart. A guard that cannot pass is not a guard.

    Here the signer IS the actor, so the relation is `decider` and the line must
    not be hedged into looking like a problem.
    """
    key, pub = integrity.generate_keypair(tmp_path / "rev.key")
    from uofa_cli.interrogate.signing import fingerprint_from_private_key
    signer = fingerprint_from_private_key(key)

    doc = {
        "@context": CTX,
        "id": "urn:uofa:decider-probe",
        "type": "UnitOfAssurance",
        "conformsToProfile": "ProfileMinimal",
        "hasDecisionRecord": {
            "type": "DecisionRecord",
            "outcome": "Accepted",
            "actor": signer,
            "decidedAt": "2026-09-11T00:00:00Z",
            "decisionProvenance": "asserted",
        },
    }
    pkg = tmp_path / "d.jsonld"
    pkg.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    out = tmp_path / "d-signed.jsonld"
    r = _uofa("sign", str(pkg), "--key", str(key), "--as", "issuer,reviewer",
              "-o", str(out))
    assert r.returncode == 0, f"{r.stdout}{r.stderr}"

    signed = json.loads(out.read_text(encoding="utf-8"))
    rec = sign_roles.decision_records(signed)[0]
    assert sign_roles.derive_relation(
        rec, rec["hasDecisionSignature"]["signerIdentity"]) == sign_roles.DECIDER, \
        "the positive fixture is pointless unless the relation really is `decider`"

    v = _uofa("verify", str(out), "--pubkey", str(pub), "--decision-pubkey", str(pub))
    assert v.returncode == 0, f"a decider-signed package must still verify:\n{v.stdout}{v.stderr}"
    assert sign_roles.UNRELATED not in (v.stdout + v.stderr), \
        "a genuine decider must not be reported as unrelated"


# ── end-to-end relation matrix, driven through the real signing command ─────
#
# The unit tests in `test_sign_roles.py` hand `derive_relation` a written-out
# signer identity. The product writes a `sha256:` fingerprint. That gap is how a
# broken `_FINGERPRINT` pattern survived: the tests exercised a shape the product
# never produces. Every case below therefore signs with `uofa sign` and reads the
# signer identity back OUT OF THE ARTIFACT.


def _sign_and_relate(tmp_path, record, name):
    """Sign a record for real and return (relation, signer_identity, record)."""
    doc = {
        "@context": CTX,
        "id": f"urn:uofa:matrix-{name}",
        "type": "UnitOfAssurance",
        "conformsToProfile": "ProfileMinimal",
        "hasDecisionRecord": dict(record),
    }
    pkg = tmp_path / f"{name}.jsonld"
    pkg.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    key, pub = integrity.generate_keypair(tmp_path / f"{name}.key")
    out = tmp_path / f"{name}-signed.jsonld"
    r = _uofa("sign", str(pkg), "--key", str(key), "--as", "issuer,reviewer",
              "-o", str(out))
    assert r.returncode == 0, f"{r.stdout}{r.stderr}"

    signed = json.loads(out.read_text(encoding="utf-8"))
    rec = sign_roles.decision_records(signed)[0]
    sig = rec.get("hasDecisionSignature") or {}
    signer = sig.get("signerIdentity")
    assert signer and signer.startswith("sha256:"), \
        f"the product's signer identity changed shape: {signer!r}"
    return sign_roles.derive_relation(rec, signer), signer, rec, out, pub


def test_e2e_a_key_signing_its_own_named_act_reads_as_decider(tmp_path):
    """The only configuration that currently reaches `decider`: the record names
    its decider BY KEY. Pinned through the real command so the emitted
    fingerprint form is the thing under test."""
    key, _pub = integrity.generate_keypair(tmp_path / "pre.key")
    from uofa_cli.interrogate.signing import fingerprint_from_private_key
    fp = fingerprint_from_private_key(key)

    doc = {"@context": CTX, "id": "urn:uofa:e2e-decider", "type": "UnitOfAssurance",
           "conformsToProfile": "ProfileMinimal",
           "hasDecisionRecord": {"type": "DecisionRecord", "outcome": "Accepted",
                                 "actor": fp, "decidedAt": "2026-09-11T00:00:00Z",
                                 "decisionProvenance": "asserted"}}
    pkg = tmp_path / "e2e.jsonld"
    pkg.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    out = tmp_path / "e2e-signed.jsonld"
    r = _uofa("sign", str(pkg), "--key", str(key), "--as", "issuer,reviewer", "-o", str(out))
    assert r.returncode == 0, f"{r.stdout}{r.stderr}"

    rec = sign_roles.decision_records(json.loads(out.read_text(encoding="utf-8")))[0]
    assert sign_roles.derive_relation(
        rec, rec["hasDecisionSignature"]["signerIdentity"]) == sign_roles.DECIDER


def test_e2e_an_unrelated_key_does_not_read_as_decider(tmp_path):
    rel, _signer, _rec, _out, _pub = _sign_and_relate(
        tmp_path,
        {"type": "DecisionRecord", "outcome": "Accepted",
         "actor": "https://example.org/org/someone-else",
         "decidedAt": "2026-09-11T00:00:00Z", "decisionProvenance": "asserted"},
        "stranger")
    assert rel != sign_roles.DECIDER
    assert rel != sign_roles.CONCURRENCE


def test_e2e_a_machine_actor_never_reads_as_decider(tmp_path):
    """A fingerprint and a `urn:` are both INFRASTRUCTURE. Same class must not
    mean same party, and a machine must not reach `decider` by class alone."""
    rel, _signer, _rec, _out, _pub = _sign_and_relate(
        tmp_path,
        {"type": "DecisionRecord", "outcome": "Accepted",
         "actor": "urn:uofa:agent:automated-reviewer",
         "decidedAt": "2026-09-11T00:00:00Z", "decisionProvenance": "asserted"},
        "machine")
    # A `urn:` name and a key fingerprint are both INFRASTRUCTURE but are not the
    # same KIND of identifier, and nothing binds them -- so the honest answer is
    # that no relation was established, not that they are different parties.
    assert rel == sign_roles.INDETERMINATE
    assert rel != sign_roles.DECIDER


def test_e2e_an_extracted_record_reads_as_transcription_attestation(tmp_path):
    """The source never signs; the signer attests the faithfulness of the
    transcription. Distinct from deciding, and it must stay distinct."""
    rel, _signer, _rec, _out, _pub = _sign_and_relate(
        tmp_path,
        {"type": "DecisionRecord", "outcome": "Accepted",
         "actor": "https://example.org/org/the-source",
         "decidedAt": "2019-06-01T00:00:00Z", "decisionProvenance": "extracted",
         "decisionAnchor": {"type": "SourceAnchor", "anchorLocator": "p.12 §3.2",
                            "anchorSha256": "a" * 64}},
        "extracted")
    assert rel == sign_roles.TRANSCRIPTION_ATTESTATION
    assert rel != sign_roles.DECIDER


def test_e2e_an_uncomparable_actor_reports_uncertainty_not_a_finding(tmp_path):
    """A Credenza session namespace is not in the grammar. The answer must be
    `indeterminate` -- neither authorized nor refuted."""
    rel, _signer, _rec, _out, _pub = _sign_and_relate(
        tmp_path,
        {"type": "DecisionRecord", "outcome": "Accepted",
         "actor": "https://credenza.review/ns/anon-00d2/session/",
         "decidedAt": "2026-09-11T00:00:00Z", "decisionProvenance": "asserted"},
        "session")
    assert rel == sign_roles.INDETERMINATE
    assert rel not in (sign_roles.DECIDER, sign_roles.UNRELATED)


def test_a_fingerprint_is_never_promoted_to_a_person(tmp_path):
    """Parsing establishes FORM, never custody. A fingerprint identifies a key;
    whether a person holds it is not readable off the bytes."""
    key, _pub = integrity.generate_keypair(tmp_path / "p.key")
    from uofa_cli.interrogate.signing import fingerprint_from_private_key
    fp = fingerprint_from_private_key(key)
    assert sign_roles.classify_identity(fp) == sign_roles.INFRASTRUCTURE
    assert sign_roles.classify_identity(fp) != sign_roles.PERSON


def test_the_documented_usage_cannot_currently_reach_decider(tmp_path):
    """**The authorization defect the parser fix does NOT close.**

    `uofa decision record --actor` documents the value as "an org-scoped handle
    IRI (https://…/org/<handle>)" -- a PERSON. The signature carries a key
    fingerprint -- INFRASTRUCTURE. Nothing in the package binds the key to the
    handle, so the tool's own documented usage derives `unrelated` even when the
    named reviewer is the person who actually signed.

    This test PINS THE DEFECT so a fix cannot land silently and so nobody reads
    the parser repair as having closed it. When reviewer keys are bound to
    authorized actor identities, this test should be the one that fails, and it
    should be replaced rather than deleted.
    """
    rel, signer, _rec, _out, _pub = _sign_and_relate(
        tmp_path,
        {"type": "DecisionRecord", "outcome": "Accepted",
         "actor": "https://uofa.net/org/j-smith",
         "decidedAt": "2026-09-11T00:00:00Z", "decisionProvenance": "asserted"},
        "documented")
    assert sign_roles.classify_identity("https://uofa.net/org/j-smith") == sign_roles.PERSON
    assert sign_roles.classify_identity(signer) == sign_roles.INFRASTRUCTURE
    assert not sign_roles.identities_are_bindable("https://uofa.net/org/j-smith", signer)
    assert rel == sign_roles.INDETERMINATE, (
        "The documented usage names a PERSON and signs with a KEY, and UofA binds "
        "neither to the other -- by ruling, it must not try. The honest report is "
        "`indeterminate`. Project authorization is Credenza's to establish; if "
        "this ever reads `decider`, UofA has started inferring authority from an "
        "identifier form and that is the thing to undo.")
