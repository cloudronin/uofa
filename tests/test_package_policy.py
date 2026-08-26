"""The refusal seam: what may be signed, and by whom.

`tests/adversarial/test_sign_verify_refusal.py` covers the CLI behaviour and
passes unchanged after the extraction -- that is the regression proof. These
tests cover the module's own contract, including the issuer tier that has no
CLI surface.
"""

from __future__ import annotations

import json

import pytest

from uofa_cli import integrity, package_policy
from uofa_cli.package_policy import PackagePolicyError


def _write(tmp_path, doc, name="pkg.jsonld"):
    p = tmp_path / name
    p.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return p


BENIGN = {"@context": {"uofa": "https://example.org/#"}, "id": "urn:uofa:t", "type": "UnitOfAssurance"}


# ── is_synthetic: the single definition ──────────────────────────


@pytest.mark.parametrize("doc", [
    {"synthetic": True},
    {"type": "uofa:SyntheticAdversarialSample"},
    {"type": ["UnitOfAssurance", "uofa:SyntheticAdversarialSample"]},
    {"@type": "uofa:SyntheticAdversarialSample"},
])
def test_is_synthetic_detects_every_marker_form(doc):
    assert package_policy.is_synthetic(doc) is True


@pytest.mark.parametrize("doc", [None, {}, BENIGN, {"synthetic": False}, {"synthetic": "true"}])
def test_is_synthetic_is_false_for_real_packages(doc):
    """`synthetic: "true"` is a string, not the flag -- matching the original
    predicate's `is True` check rather than loosening it."""
    assert package_policy.is_synthetic(doc) is False


def test_load_doc_treats_unreadable_input_as_no_signal(tmp_path):
    assert package_policy.load_doc(tmp_path / "missing.jsonld") is None
    bad = tmp_path / "bad.jsonld"
    bad.write_text("{not json", encoding="utf-8")
    assert package_policy.load_doc(bad) is None
    arr = tmp_path / "arr.jsonld"
    arr.write_text("[1,2]", encoding="utf-8")
    assert package_policy.load_doc(arr) is None


# ── the two tiers ────────────────────────────────────────────────


def test_assert_signable_refuses_synthetic():
    with pytest.raises(PackagePolicyError, match="synthetic adversarial sample"):
        package_policy.assert_signable({"synthetic": True})


def test_assert_signable_allows_a_decision_block():
    """`uofa sign` behaviour is unchanged by the extraction: the decision-block
    refusal is an *issuer* rule, not a universal one. A user signing with their
    own key is not the section 12 hazard."""
    package_policy.assert_signable({**BENIGN, "hasDecisionRecord": {"decidedBy": "x"}})


def test_assert_issuable_refuses_a_decision_block():
    with pytest.raises(PackagePolicyError, match="AGENTS.md section 12"):
        package_policy.assert_issuable({**BENIGN, "hasDecisionRecord": {"decidedBy": "x"}})


def test_assert_issuable_still_refuses_synthetic():
    with pytest.raises(PackagePolicyError, match="synthetic adversarial sample"):
        package_policy.assert_issuable({"synthetic": True})


def test_assert_issuable_allows_a_plain_package():
    package_policy.assert_issuable(BENIGN)


# ── sign_package ─────────────────────────────────────────────────


def test_sign_package_signs_and_verifies(tmp_path):
    key, pub = integrity.generate_keypair(tmp_path / "demo.key")
    pkg = _write(tmp_path, BENIGN)

    sha, sig = package_policy.sign_package(pkg, key)

    assert len(sha) == 64 and len(sig) == 128
    assert integrity.verify_file(pkg, pub) == (True, True)


def test_sign_package_refuses_before_touching_the_file(tmp_path):
    """A refused package must not be partially signed -- policy runs before
    any cryptography, so the file on disk is untouched."""
    key, _ = integrity.generate_keypair(tmp_path / "demo.key")
    pkg = _write(tmp_path, {**BENIGN, "synthetic": True})
    before = pkg.read_text(encoding="utf-8")

    with pytest.raises(PackagePolicyError):
        package_policy.sign_package(pkg, key)

    assert pkg.read_text(encoding="utf-8") == before


def test_sign_package_refuses_issuer_signing_over_a_decision(tmp_path):
    key, _ = integrity.generate_keypair(tmp_path / "demo.key")
    pkg = _write(tmp_path, {**BENIGN, "hasDecisionRecord": {"decidedBy": "eng"}})

    with pytest.raises(PackagePolicyError, match="section 12"):
        package_policy.sign_package(pkg, key)


def test_sign_package_accepts_an_in_memory_key(tmp_path):
    """The hosted path receives the PEM as a secret and must never write the
    private key to a filesystem the same process serves downloads from."""
    key, pub = integrity.generate_keypair(tmp_path / "demo.key")
    pem = key.read_bytes()
    key.unlink()

    pkg = _write(tmp_path, BENIGN)
    package_policy.sign_package(pkg, key_bytes=pem)

    assert integrity.verify_file(pkg, pub) == (True, True)


def test_in_memory_and_on_disk_keys_produce_identical_signatures(tmp_path):
    key, _ = integrity.generate_keypair(tmp_path / "demo.key")
    a = _write(tmp_path, BENIGN, "a.jsonld")
    b = _write(tmp_path, BENIGN, "b.jsonld")

    assert (package_policy.sign_package(a, key)
            == package_policy.sign_package(b, key_bytes=key.read_bytes()))


def test_sign_hash_requires_exactly_one_key_source(tmp_path):
    key, _ = integrity.generate_keypair(tmp_path / "demo.key")
    with pytest.raises(ValueError, match="exactly one"):
        integrity.sign_hash("ab" * 32)
    with pytest.raises(ValueError, match="exactly one"):
        integrity.sign_hash("ab" * 32, key, key_bytes=key.read_bytes())
