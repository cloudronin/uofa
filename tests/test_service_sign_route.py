"""`package_policy.sign_package_scoped` — the door a service signs through.

`sign_package` produces ONE signature over the whole document, and
`assert_issuable` refuses it for anything carrying a judgment. A hosted product
that emits decision records therefore had no path through the policy layer at
all: the only signer a UI is supposed to call could not sign what the UI makes.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tests" / "fixtures" / "import"))


def _uofa(*args):
    return subprocess.run([sys.executable, "-m", "uofa_cli", *[str(a) for a in args]],
                          capture_output=True, text=True, cwd=str(REPO_ROOT))


@pytest.fixture
def keys(tmp_path):
    issuer, reviewer = tmp_path / "iss.key", tmp_path / "rev.key"
    for k in (issuer, reviewer):
        assert _uofa("keygen", k).returncode == 0
    return issuer, reviewer


@pytest.fixture
def decision_pkg(tmp_path):
    from generator import SPECS, generate_fixture

    xlsx = tmp_path / "wb.xlsx"
    generate_fixture(SPECS["e2e-clean-vv40"]["data"], xlsx)
    out = tmp_path / "pkg.jsonld"
    assert _uofa("import", xlsx, "--output", out, "--pack", "vv40").returncode == 0
    return out


@pytest.fixture
def decision_free_pkg(tmp_path):
    out = tmp_path / "plain.jsonld"
    out.write_text(json.dumps({
        "@context": "https://uofa.net/spec/context/v0.9.jsonld",
        "id": "https://uofa.net/t/plain", "type": "UnitOfAssurance",
        "name": "no judgment here",
    }, indent=2), encoding="utf-8")
    return out


def test_a_decision_free_package_is_sealed_the_legacy_way(decision_free_pkg, keys):
    """The routing rule, and it cost a live bug to learn.

    The scoped signer originally used the measurement-view hash unconditionally.
    For a package with no decision layer the whole document IS the measurement
    view, and the CLI signs it with `sign_file` -- so those packages were sealed
    under a scope no verifier checks them against: correctly signed, and reported
    broken. The signer must route on what the package carries, exactly as verify
    does.
    """
    from uofa_cli.package_policy import sign_package_scoped

    issuer, _ = keys
    sign_package_scoped(decision_free_pkg, issuer_key_path=issuer)
    r = _uofa("verify", decision_free_pkg, "--pubkey", issuer.with_suffix(".pub"))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Hash match" in r.stdout


def test_two_scopes_and_two_keys_read_as_independent(decision_pkg, keys):
    from uofa_cli.package_policy import sign_package_scoped

    issuer, reviewer = keys
    result = sign_package_scoped(decision_pkg,
                                 issuer_key_path=issuer, reviewer_key_path=reviewer)
    assert result["decision_records_signed"] == 1
    assert result["decision_signatures_owed"] == 0
    assert result["complete"] is True

    r = _uofa("verify", decision_pkg, "--pubkey", issuer.with_suffix(".pub"),
              "--decision-pubkey", reviewer.with_suffix(".pub"))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "independent attestation" in r.stdout


def test_without_a_reviewer_key_the_package_is_sealed_and_honestly_owed(decision_pkg, keys):
    """The lawful multi-party interim, not a failure.

    The seal excludes the decision layer precisely so it can be applied before a
    decision is signed and survive one arriving later.
    """
    from uofa_cli.package_policy import sign_package_scoped

    issuer, _ = keys
    result = sign_package_scoped(decision_pkg, issuer_key_path=issuer)
    assert result["decision_records_signed"] == 0
    assert result["decision_signatures_owed"] == 1
    assert result["complete"] is False

    r = _uofa("check", decision_pkg, "--skip-rules", "--pack", "vv40",
              "--pubkey", issuer.with_suffix(".pub"))
    assert r.returncode != 0, "an unsigned asserted verdict is an incomplete package"


def test_an_unclassified_record_is_refused_before_any_cryptography(decision_pkg, keys):
    """A refused document must never be partially signed."""
    from uofa_cli.package_policy import PackagePolicyError, sign_package_scoped

    doc = json.loads(decision_pkg.read_text(encoding="utf-8"))
    doc["hasDecisionRecord"].pop("decisionProvenance")
    before = json.dumps(doc, indent=2)
    decision_pkg.write_text(before, encoding="utf-8")

    issuer, _ = keys
    with pytest.raises(PackagePolicyError):
        sign_package_scoped(decision_pkg, issuer_key_path=issuer)
    assert decision_pkg.read_text(encoding="utf-8") == before, \
        "the file must be untouched when the policy refuses"


def test_an_in_memory_pem_signs_without_touching_the_filesystem(decision_pkg, keys):
    """The hosted case: the key arrives as a secret and must not be written to
    the filesystem the process serves downloads from."""
    from uofa_cli.package_policy import sign_package_scoped

    issuer, reviewer = keys
    result = sign_package_scoped(
        decision_pkg,
        issuer_key_bytes=issuer.read_bytes(),
        reviewer_key_bytes=reviewer.read_bytes())
    assert result["complete"] is True

    r = _uofa("verify", decision_pkg, "--pubkey", issuer.with_suffix(".pub"),
              "--decision-pubkey", reviewer.with_suffix(".pub"))
    assert r.returncode == 0, r.stdout + r.stderr
