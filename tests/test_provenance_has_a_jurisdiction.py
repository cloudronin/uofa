"""A package cannot state a fork its vocabulary lacks.

Reported live: `uofa verify packs/vv40/examples/morrison/cou1/...` printed

    decision 1: provenance '<absent>' — the fork says which warrant is owed,
    so this record cannot be checked at all.

beside two PASSING signatures. The package declares context **v0.5**, and
`decisionProvenance` arrived in **v0.9** — the term is not in its vocabulary, so
the message described this checker's expectation rather than the package's
condition, and read to anyone running it as though the package were broken.

The same shape `protocol_check` already fixed for the run-log pins. Refusing a
package for lacking a field that did not exist when it was written punishes age
rather than negligence.

**The split is deliberate.** `verify` READS an existing artifact and advises.
`sign_package_scoped` makes a NEW claim today and still refuses — but names age
as the cause, so the fix is re-importing rather than hunting for a field.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from uofa_cli import package_policy, sign_roles

MORRISON = Path("packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld")


def _forkless_at(version_ref: str) -> dict:
    """A package with one decision record that states no fork.

    Built with the real block key rather than a guessed one -- the first draft
    used "decision" and `decision_records` found nothing, so the test passed
    for the wrong reason on the case it exists to catch.
    """
    from uofa_cli.package_policy import DECISION_BLOCK_KEY

    return {"@context": version_ref,
            DECISION_BLOCK_KEY: [{"id": "d1", "outcome": "Accepted"}]}


# ── the era rule ────────────────────────────────────────────────────────────

def test_the_shipped_example_predates_the_term():
    """The real package that reported this, read from the repo."""
    doc = json.loads(MORRISON.read_text(encoding="utf-8"))
    assert sign_roles.context_version(doc) == (0, 5)
    assert sign_roles.predates_provenance(doc)


def test_a_current_package_does_not_predate_it():
    assert not sign_roles.predates_provenance(
        _forkless_at("x/v0.9.jsonld"))


def test_an_inlined_context_is_not_treated_as_old():
    """A resolved or signed document inlines its context and declares no
    version. Silence is not a claim of age — and such a document is usually
    SIGNED, so the term was available when it was made."""
    assert not sign_roles.predates_provenance({"@context": {"a": "b"}})
    assert not sign_roles.predates_provenance({})


@pytest.mark.parametrize("ref,old", [
    ("x/v0.5.jsonld", True), ("x/v0.8.jsonld", True),
    ("x/v0.9.jsonld", False), ("x/v0.10.jsonld", False),
])
def test_the_boundary_is_the_version_that_introduced_the_term(ref, old):
    assert sign_roles.predates_provenance(_forkless_at(ref)) is old


# ── the check still has teeth where it should ───────────────────────────────

def test_a_current_package_with_no_fork_is_still_unclassified():
    """The whole point of the era rule is that it narrows, not weakens."""
    assert len(sign_roles.unclassified_records(
        _forkless_at("x/v0.9.jsonld"))) == 1


def test_the_old_package_is_still_unclassified_too():
    """`unclassified_records` is unchanged: it reports the fact. Only the
    CALLERS decide whether that fact is a refusal or a note."""
    doc = json.loads(MORRISON.read_text(encoding="utf-8"))
    assert len(sign_roles.unclassified_records(doc)) == 1


# ── verify advises; signing refuses ─────────────────────────────────────────

def test_verify_advises_rather_than_warns_on_an_old_package(capsys):
    """The reported symptom, as a test."""
    from uofa_cli.commands import verify as V

    doc = json.loads(MORRISON.read_text(encoding="utf-8"))
    V._report_record(doc, doc["decision"][0] if isinstance(doc.get("decision"), list)
                     else sign_roles.decision_records(doc)[0],
                     1, [], set(), MORRISON, [])
    out = capsys.readouterr().out
    assert "predates the term" in out and "advised, not refused" in out
    assert "cannot be checked at all" not in out


def test_signing_still_refuses_but_names_age_as_the_cause():
    """Signing makes a claim TODAY. The refusal stays; the message improves."""
    with pytest.raises(package_policy.PackagePolicyError) as e:
        package_policy.sign_package_scoped(MORRISON, issuer_key_bytes=b"x")
    msg = str(e.value)
    assert "predates" in msg and "v0.5" in msg
    assert "re-import" in msg, "the refusal does not say how to fix it"
