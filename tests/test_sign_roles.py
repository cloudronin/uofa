"""The unified signing surface's refusals — each seen red before believed.

One party, one act, one command. Scopes are the format's business; commands are
the party's, so the act count follows the PARTY count rather than the scope
count. What must never happen is one signature spanning both scopes: an issuer
seal covering a judgment is infrastructure vouching for a human commitment.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from uofa_cli import integrity, paths, sign_roles

REPO = Path(__file__).resolve().parents[1]


def _uofa(*args, cwd=None):
    return subprocess.run([sys.executable, "-m", "uofa_cli", *args],
                          capture_output=True, text=True, cwd=str(cwd or REPO))


def _pkg(tmp_path, *, decision=None, name="p.jsonld"):
    doc = {
        "@context": "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.9.jsonld",
        "id": "urn:uofa:t", "type": "UnitOfAssurance",
        "conformsToProfile": "ProfileMinimal",
    }
    if decision is not None:
        doc["hasDecisionRecord"] = decision
    p = tmp_path / name
    p.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return p


def _key(tmp_path, name="k"):
    key, _pub = integrity.generate_keypair(tmp_path / f"{name}.key")
    return key


ASSERTED = {"type": "DecisionRecord", "outcome": "Accepted",
            "actor": "https://example.org/org/reviewer", "decidedAt": "2026-09-09T10:00:00Z",
            "decisionProvenance": "asserted"}
EXTRACTED = {"type": "DecisionRecord", "outcome": "Accepted",
             "actor": "https://example.org/org/morrison", "decidedAt": "2019-06-01T00:00:00Z",
             "decisionProvenance": "extracted",
             "decisionAnchor": {"type": "SourceAnchor", "anchorLocator": "p.12 §3.2",
                                "anchorSha256": "a" * 64}}


# ── §3.1 ────────────────────────────────────────────────────────────────────

def test_bare_sign_on_a_decision_carrying_package_refuses_and_teaches(tmp_path):
    pkg = _pkg(tmp_path, decision=ASSERTED)
    r = _uofa("sign", str(pkg), "--key", str(_key(tmp_path)))
    assert r.returncode == 2, r.stdout
    out = r.stdout + r.stderr
    assert "--as" in out, "the refusal must name the flag that resolves it"
    assert "issuer" in out, "and the roles available"


# ── §3.2 / §3.3 — the fork decides ──────────────────────────────────────────

def test_issuer_alone_seals_an_unsigned_asserted_verdict_and_names_it(tmp_path):
    """This once asserted a REFUSAL, and the refusal was wrong.

    The stated rationale was that the seal must not close around an unsigned
    verdict -- but the seal never closes around the verdict at all: the
    measurement view excludes the decision layer by construction, which is A6's
    whole purpose and the property `test_a_seal_survives_a_decision_added_
    afterwards` pins. Refusing here made the lawful multi-party order
    unreachable: the issuer could not seal until the reviewer signed, and the
    reviewer could not sign until a seal existed. Both parties, both orders.

    Completeness is a question about the PACKAGE, so `uofa check` owns it (see
    tests/test_two_party_signing_order.py). What the signer owes is to say so.
    """
    pkg = _pkg(tmp_path, decision=ASSERTED)
    r = _uofa("sign", str(pkg), "--key", str(_key(tmp_path)), "--as", "issuer")
    out = r.stdout + r.stderr
    assert r.returncode == 0, out
    assert "unsigned asserted" in out, "the incompleteness must be named, not silent"
    assert "signature owed" in out


def test_issuer_alone_is_permitted_when_the_only_records_are_extracted(tmp_path):
    """Morrison's shape. The source never signs; the anchor is their
    attestation, and the seal excludes the decision layer by construction."""
    pkg = _pkg(tmp_path, decision=EXTRACTED)
    r = _uofa("sign", str(pkg), "--key", str(_key(tmp_path)), "--as", "issuer")
    out = r.stdout + r.stderr
    assert "asserted decision" not in out
    assert r.returncode != 2, out


# ── §3.5 ────────────────────────────────────────────────────────────────────

def test_an_unknown_role_refuses_and_names_the_closed_set(tmp_path):
    pkg = _pkg(tmp_path)
    r = _uofa("sign", str(pkg), "--key", str(_key(tmp_path)), "--as", "rubber-stamper")
    assert r.returncode == 2
    out = r.stdout + r.stderr
    assert "rubber-stamper" in out and "reviewer" in out


# ── §3.4 — wrong key class, both directions ─────────────────────────────────

class TestWrongKeyClass:
    """Derived from the key itself, never from what the caller says it is."""

    def test_the_issuer_key_may_not_sign_a_judgment(self, monkeypatch, tmp_path):
        key, pub = integrity.generate_keypair(tmp_path / "issuer.key")
        monkeypatch.setattr(paths, "issuer_pubkey", lambda root=None: pub)
        with pytest.raises(sign_roles.RoleError) as exc:
            sign_roles.assert_key_matches_roles(key, ("reviewer",))
        assert "ISSUER key" in str(exc.value)

    def test_the_reviewer_key_may_not_make_the_seal(self, monkeypatch, tmp_path):
        key, pub = integrity.generate_keypair(tmp_path / "rev.key")
        monkeypatch.setattr(paths, "reviewer_pubkey", lambda root=None: pub)
        with pytest.raises(sign_roles.RoleError) as exc:
            sign_roles.assert_key_matches_roles(key, ("issuer",))
        assert "REVIEWER key" in str(exc.value)

    def test_an_unrecognised_key_is_permitted(self, tmp_path):
        """A customer signs with their own key and this tool holds no registry
        of them. What is refused is a key we CAN identify, used out of class."""
        key = _key(tmp_path, "stranger")
        sign_roles.assert_key_matches_roles(key, ("reviewer",))
        sign_roles.assert_key_matches_roles(key, ("issuer",))


# ── §4 regression pin ───────────────────────────────────────────────────────

def test_a_decision_free_package_signs_exactly_as_before(tmp_path):
    """The consolidation must not move the ordinary path by one byte."""
    pkg = _pkg(tmp_path)
    r = _uofa("sign", str(pkg), "--key", str(_key(tmp_path)))
    assert r.returncode == 0, r.stdout + r.stderr
    signed = json.loads(pkg.read_text())
    assert signed["signature"].startswith("ed25519:")
    assert signed["hash"].startswith("sha256:")


# ── repeatability ───────────────────────────────────────────────────────────

def test_decision_records_reads_one_or_many(tmp_path):
    assert len(sign_roles.decision_records({"hasDecisionRecord": ASSERTED})) == 1
    assert len(sign_roles.decision_records(
        {"hasDecisionRecord": [ASSERTED, EXTRACTED]})) == 2
    assert sign_roles.decision_records({}) == []


def test_only_asserted_records_are_owed_a_signature():
    doc = {"hasDecisionRecord": [ASSERTED, EXTRACTED]}
    owed = sign_roles.unsigned_asserted(doc)
    assert len(owed) == 1 and owed[0]["decisionProvenance"] == "asserted"


# ── §3.6 — the stale-bundle rule ────────────────────────────────────────────

def test_a_decision_role_refuses_without_a_measurement_seal(tmp_path):
    """A decision signature binds the RECOMPUTED measurement hash, so there must
    be a seal to bind to. Signing a judgment over an unsealed package leaves the
    chain's first link missing."""
    pkg = _pkg(tmp_path, decision=ASSERTED)
    r = _uofa("sign", str(pkg), "--key", str(_key(tmp_path)), "--as", "reviewer")
    assert r.returncode == 2
    out = r.stdout + r.stderr
    assert "no measurement seal" in out
    assert "issuer,reviewer" in out, "the refusal must teach the composed form"


def test_a_reviewer_role_with_nothing_to_sign_refuses(tmp_path):
    """`--as reviewer` on a package carrying no decision record at all is a
    claim about nothing — a signature with no act under it."""
    pkg = _pkg(tmp_path)
    r = _uofa("sign", str(pkg), "--key", str(_key(tmp_path)), "--as", "issuer,reviewer")
    assert r.returncode == 2
    assert "nothing to sign" in (r.stdout + r.stderr)


# ── §4 — composed is sugar, never a third mechanism ─────────────────────────

def test_composed_equals_sequential(tmp_path):
    """One party wearing two hats must produce what the lawful two-step produces.

    The sequential leg is the multi-party order, and it only works because the
    measurement view EXCLUDES the decision layer: the issuer seals, a decision
    is added afterwards, and the seal still verifies. That exclusion is what
    lets two parties act independently without re-sealing.

    Sealing a package that ALREADY carries an unsigned asserted verdict is
    refused (§3.2), so the sequential leg cannot start from the composed leg's
    input — which is the rule working, not an asymmetry.

    If these ever diverge, the composed form has become a third signing path
    rather than sugar over the same two.
    """
    key = _key(tmp_path)

    composed = _pkg(tmp_path, decision=ASSERTED, name="composed.jsonld")
    a = _uofa("sign", str(composed), "--key", str(key), "--as", "issuer,reviewer")
    assert a.returncode == 0, a.stdout + a.stderr

    seq = _pkg(tmp_path, name="seq.jsonld")                 # sealed with no decision
    b = _uofa("sign", str(seq), "--key", str(key), "--as", "issuer")
    assert b.returncode == 0, b.stdout + b.stderr
    doc = json.loads(seq.read_text())
    doc["hasDecisionRecord"] = dict(ASSERTED)               # the decider arrives after
    seq.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    c = _uofa("sign", str(seq), "--key", str(key), "--as", "reviewer")
    assert c.returncode == 0, c.stdout + c.stderr

    da, db = json.loads(composed.read_text()), json.loads(seq.read_text())

    def _shape(d):
        sig = d["hasDecisionRecord"]["hasDecisionSignature"]
        return {
            "hash": d["hash"], "signature": d["signature"],
            "role": sig["signatureRole"], "signer": sig["signerIdentity"],
            "measurementHash": sig["measurementHash"],
            "signatureValue": sig["signatureValue"],
        }

    assert _shape(da) == _shape(db), "composed and sequential diverged"


def test_a_seal_survives_a_decision_added_afterwards(tmp_path):
    """The property the whole two-scope design rests on.

    If adding a decision invalidated the seal, every multi-party flow would
    require re-sealing — and the issuer would end up re-attesting a package
    whose judgment arrived after it looked.
    """
    from uofa_cli.interrogate.signing import measurement_hash

    pkg = _pkg(tmp_path)
    key = _key(tmp_path)
    assert _uofa("sign", str(pkg), "--key", str(key), "--as", "issuer").returncode == 0

    doc = json.loads(pkg.read_text())
    sealed = doc["hash"].split(":", 1)[1]
    doc["hasDecisionRecord"] = dict(ASSERTED)
    assert measurement_hash(doc) == sealed, (
        "adding a decision moved the measurement hash -- the exclusion that makes "
        "independent parties possible is broken")


def test_the_composed_act_is_atomic(tmp_path, monkeypatch):
    """Both signatures land or neither touches disk.

    A package sealed but with its verdict unsigned states something nobody
    meant, and is indistinguishable from one where the second party simply has
    not signed yet.
    """
    pkg = _pkg(tmp_path, decision=ASSERTED)
    before = pkg.read_text()

    import uofa_cli.sign_roles as sr
    monkeypatch.setattr(sr, "sign_decision_records",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))

    from uofa_cli.commands import sign as sign_cmd

    class _Args:
        file = pkg
        key = _key(tmp_path)
        context = None
        output = None
        roles = "issuer,reviewer"

    with pytest.raises(RuntimeError):
        sign_cmd._sign_with_roles(_Args(), json.loads(before), ("issuer", "reviewer"))

    assert pkg.read_text() == before, "a half-attested artifact reached disk"


def test_the_signature_binds_the_recomputed_measurement_hash(tmp_path):
    """Tamper-evidence: altering any measurement must break the decision
    signature, which is what chains the judgment to the evidence it judged."""
    pkg = _pkg(tmp_path, decision=ASSERTED)
    key = _key(tmp_path)
    assert _uofa("sign", str(pkg), "--key", str(key),
                 "--as", "issuer,reviewer").returncode == 0

    from uofa_cli.interrogate.signing import measurement_hash
    doc = json.loads(pkg.read_text())
    bound = doc["hasDecisionRecord"]["hasDecisionSignature"]["measurementHash"]
    assert bound == measurement_hash(doc), "the signature does not bind this package"

    doc["conformsToProfile"] = "ProfileComplete"          # touch a measurement
    assert measurement_hash(doc) != bound, (
        "altering a measurement left the bound hash unchanged -- the chain is not "
        "tamper-evident")


# ── §8: the derivation is the only place these words exist ──────────────────

class TestDerivedRelation:
    """Constitutional surface: decider / transcription-attestation /
    concurrence are COMPUTED from facts the artifact already carries, and
    stored nowhere.

    The four-role vocabulary they replaced had a live misdeclaration channel —
    sign your own verdict as `encoder-of-record` and ownership is softened in
    the permanent record, uncatchably, because the flag WAS the truth-source.
    Deriving closes that by construction: a derived relation cannot disagree
    with the record, because it is a reading of it.
    """

    REV_A = "https://example.org/org/reviewer-a"
    REV_B = "https://example.org/org/reviewer-b"

    def test_case_1_morrison_is_a_transcription_attestation(self):
        """The judgment stays the source's; the signer attests the transcription.
        Any signer yields this — Morrison never signs, so no actor can match."""
        rec = dict(EXTRACTED, role="Morrison et al. 2019")
        assert sign_roles.derive_relation(rec, self.REV_A) == \
            sign_roles.TRANSCRIPTION_ATTESTATION
        line = sign_roles.describe_relation(rec, sign_roles.TRANSCRIPTION_ATTESTATION)
        assert "Morrison" in line and "cited passage" in line

    def test_case_2_johnson_is_the_decider(self):
        rec = dict(ASSERTED, actor=self.REV_A)
        assert sign_roles.derive_relation(rec, self.REV_A) == sign_roles.DECIDER

    def test_a_stacked_concurrence_reads_as_concurrence(self):
        rec = dict(ASSERTED, actor=self.REV_B,
                   decisionScope="concurrence-with-prior-decision")
        assert sign_roles.derive_relation(rec, self.REV_B) == sign_roles.CONCURRENCE

    def test_a_signer_who_authored_nothing_reads_as_unrelated(self):
        """Never silently promoted to decider: a signature that matches no
        record this signer authored is exactly that, and says so."""
        rec = dict(ASSERTED, actor=self.REV_A)
        assert sign_roles.derive_relation(rec, self.REV_B) == sign_roles.UNRELATED

    def test_the_three_entry_stack_derives_all_three(self):
        """Two distinct reviewer keys, so derivation and independence are both
        exercised before any real second party exists."""
        source = dict(EXTRACTED, role="Morrison et al. 2019")
        decision = dict(ASSERTED, actor=self.REV_A)
        concur = dict(ASSERTED, actor=self.REV_B,
                      decisionScope="concurrence-with-prior-decision")
        assert sign_roles.derive_relation(source, self.REV_A) == \
            sign_roles.TRANSCRIPTION_ATTESTATION
        assert sign_roles.derive_relation(decision, self.REV_A) == sign_roles.DECIDER
        assert sign_roles.derive_relation(concur, self.REV_B) == sign_roles.CONCURRENCE

    def test_independence_is_derived_from_identity_not_count(self):
        one = [{"signerIdentity": self.REV_A}, {"signerIdentity": self.REV_A}]
        two = [{"signerIdentity": self.REV_A}, {"signerIdentity": self.REV_B}]
        assert "single-party" in sign_roles.independence(one), (
            "two envelopes with one identity is one party wearing two hats")
        assert "independent attestation" in sign_roles.independence(two)


class TestActorHygiene:
    """Actor-match is what the derivation stands on, so it is strict about form.

    The `file://` class of bug — a bare name landing in an `@id` field and
    resolving against wherever the document happened to sit — would silently
    corrupt every relation computed here, because two different parties could
    normalise to the same accidental path. It is refused rather than compared.
    """

    def test_canonical_identity_forms_match(self):
        rec = dict(ASSERTED, actor="https://example.org/org/rev")
        assert sign_roles.derive_relation(rec, "https://example.org/org/rev") == \
            sign_roles.DECIDER
        assert sign_roles.derive_relation(rec, " HTTPS://example.org/org/rev ") == \
            sign_roles.DECIDER, "surrounding space and case must not split a party"

    def test_a_file_path_actor_never_matches(self):
        rec = dict(ASSERTED, actor="file:///Users/someone/V.%20Vettrivel")
        assert sign_roles.derive_relation(
            rec, "file:///Users/someone/V.%20Vettrivel") == sign_roles.UNRELATED

    def test_empty_and_non_string_actors_never_match(self):
        for bad in ("", "   ", None, 42, {"@id": "x"}):
            rec = dict(ASSERTED, actor=bad)
            assert sign_roles.derive_relation(rec, bad) == sign_roles.UNRELATED


# ── the identity grammar ────────────────────────────────────────────────────
#
# The Attestation Model Complete Reference transcribes its custody section from
# THESE cases. Doc and guard read one source, so they cannot drift.

LEGAL_IDENTITIES = [
    ("https://uofa.net/org/demo-reviewer", sign_roles.PERSON),
    ("https://acme.example/org/j-smith", sign_roles.PERSON),
    ("urn:uofa:space:deployment", sign_roles.INFRASTRUCTURE),
    ("aa:bb:cc:dd:ee:ff:00:11:22:33", sign_roles.INFRASTRUCTURE),
    ("ledger://review-2026/entry-14", sign_roles.ACT_REFERENCE),
]

REFUSED_IDENTITIES = [
    "file:///Users/vishnu/packages/V.%20Vettrivel",  # the one that actually bit
    "path://team/reviewer",
    "J. Smith",          # a bare name resolves against wherever the doc sits
    "",
    "   ",
    None,
    42,
]


@pytest.mark.parametrize("value,expected", LEGAL_IDENTITIES)
def test_the_grammar_classifies_every_legal_form(value, expected):
    assert sign_roles.classify_identity(value) == expected


@pytest.mark.parametrize("value", REFUSED_IDENTITIES)
def test_the_grammar_refuses_rather_than_guesses(value):
    """Totality: an unclassifiable identity names itself, it does not pass through.

    Absent is not unclassifiable. A grammar that shrugged and returned a default
    would let the empty-value genus in through the door that carries every
    derived relation.
    """
    with pytest.raises(sign_roles.IdentityFormError):
        sign_roles.classify_identity(value)


def test_an_act_reference_is_not_a_party_and_cannot_match():
    """`ledger://` names an ACT. Two records citing one ledger entry are not the
    same actor, and letting an act reference match would make every record
    anchored to the same entry read as self-decided."""
    entry = "ledger://review-2026/entry-14"
    assert sign_roles.classify_identity(entry) == sign_roles.ACT_REFERENCE
    assert not sign_roles.identity_is_comparable(entry)
    rec = {"decisionProvenance": "asserted", "actor": entry}
    assert sign_roles.derive_relation(rec, entry) == sign_roles.UNRELATED


def test_distinct_identities_that_naive_normalisation_would_collide_stay_distinct():
    """The collision half of the disease, and the one no error message reveals.

    Two real reviewers, both handle `j-smith`, under different authorities. Any
    normalisation that reduced an identity to its last path segment -- a
    display-name shortener, a "friendly handle" helper -- would fuse them into
    one party. Nothing would raise: verify would simply report `decider` where
    the truth is `unrelated`, with full authority, and no artifact would show
    the substitution. So the derivation compares whole identities, end to end.
    """
    acme = "https://acme.example/org/j-smith"
    globex = "https://globex.example/org/j-smith"
    assert acme.rsplit("/", 1)[-1] == globex.rsplit("/", 1)[-1], \
        "the fixture is pointless unless these really do collide when shortened"

    for who in (acme, globex):
        assert sign_roles.classify_identity(who) == sign_roles.PERSON

    rec = {"decisionProvenance": "asserted", "actor": acme}
    # Acme's own reviewer decided it.
    assert sign_roles.derive_relation(rec, acme) == sign_roles.DECIDER
    # Globex's reviewer, sharing only a handle, did not.
    assert sign_roles.derive_relation(rec, globex) == sign_roles.UNRELATED


def test_case_folds_but_does_not_otherwise_normalise():
    """Case-insensitivity is a property of the scheme and host, and treating one
    identity written two ways as two parties would be the opposite error. What
    it must NOT do is strip, shorten, or canonicalise the path."""
    rec = {"decisionProvenance": "asserted",
           "actor": "https://ACME.example/org/J-Smith"}
    assert sign_roles.derive_relation(
        rec, "https://acme.example/org/j-smith") == sign_roles.DECIDER
    assert sign_roles.derive_relation(
        rec, "https://acme.example/org/j-smith/") == sign_roles.UNRELATED


# ── doc/guard anti-drift ────────────────────────────────────────────────────

REFERENCE_DOC = (
    Path(__file__).resolve().parents[1]
    / "docs" / "UofA_Attestation_Model_Complete_Reference_v1_0.md")
BEGIN = "<!-- BEGIN identity-grammar (generated from tests/test_sign_roles.py) -->"
END = "<!-- END identity-grammar -->"


def render_identity_table() -> str:
    """The reference's identity-grammar block, rendered from the cases above.

    Prose describing a guard drifts from it the first time the guard changes and
    nothing fails. Generating the prose FROM the fixture and asserting the file
    matches makes drift a red test rather than a discovery.
    """
    lines = [BEGIN,
             "",
             "| identity | class | what it names |",
             "|---|---|---|"]
    means = {
        sign_roles.PERSON: "a party who can decide; may match a signer",
        sign_roles.INFRASTRUCTURE: "a tool, deployment, or key; may match a signer",
        sign_roles.ACT_REFERENCE: "an **act**, not a party — never matches a signer",
    }
    for value, cls in LEGAL_IDENTITIES:
        lines.append(f"| `{value}` | {cls} | {means[cls]} |")
    lines.append("")
    lines.append("Refused, each naming its own form rather than defaulting:")
    lines.append("")
    for value in REFUSED_IDENTITIES:
        if not isinstance(value, str):
            shown = f"a non-string (`{value!r}`)"
        elif not value:
            shown = "the empty string"
        elif not value.strip():
            shown = "whitespace only"
        else:
            shown = f"`{value}`"
        lines.append(f"- {shown}")
    lines.append("")
    lines.append(END)
    return "\n".join(lines)


def test_the_reference_transcribes_the_fixture():
    text = REFERENCE_DOC.read_text(encoding="utf-8")
    assert BEGIN in text and END in text, (
        f"{REFERENCE_DOC.name} lost its generated identity-grammar block")
    block = text[text.index(BEGIN):text.index(END) + len(END)]
    assert block == render_identity_table(), (
        "the reference and the guard disagree about the identity grammar. "
        "Regenerate: python3 -m pytest tests/test_sign_roles.py --write-identity-doc")
