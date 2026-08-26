"""The multi-party order, end to end: seal first, decision after, seal survives.

This flow was unreachable. `--as issuer` refused while an asserted record was
unsigned, and a decision role refused while no seal existed -- so the Space could
not seal until the reviewer signed, and the reviewer could not sign until the
Space sealed. Both parties refused in both orders, and the excel path emits
asserted records by default, so this was the *ordinary* Credenza flow.

The refusal's rationale did not survive the architecture: the seal never wraps
the decision at all -- the measurement view excludes it by construction, which is
A6's whole purpose. Sealing an incomplete package is lawful and honest; SAYING it
is incomplete is the signer's job, and REFUSING it is the completeness gate's.
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
def package(tmp_path):
    from generator import SPECS, generate_fixture

    xlsx = tmp_path / "wb.xlsx"
    generate_fixture(SPECS["e2e-clean-vv40"]["data"], xlsx)
    out = tmp_path / "pkg.jsonld"
    r = _uofa("import", xlsx, "--output", out, "--pack", "vv40")
    assert r.returncode == 0, r.stderr + r.stdout
    return out


@pytest.fixture
def keys(tmp_path):
    space, reviewer = tmp_path / "space.key", tmp_path / "reviewer.key"
    for k in (space, reviewer):
        assert _uofa("keygen", k).returncode == 0
    return space, reviewer


def test_the_space_seals_an_unsigned_verdict_and_says_so(package, keys):
    """Step 1. The seal lands, and the warning is ASSERTED, not merely tolerated.

    A silent seal here would be the original defect: a package that looks
    officially sealed while carrying a judgment nobody stood behind, with
    nothing in the output to say so.
    """
    space, _ = keys
    r = _uofa("sign", package, "--key", space, "--as", "issuer")
    assert r.returncode == 0, r.stderr + r.stdout

    out = r.stderr + r.stdout
    assert "unsigned asserted" in out, "the incompleteness must be NAMED"
    assert "signature owed" in out
    assert json.loads(package.read_text()).get("signature", "").startswith("ed25519:")


def test_check_refuses_the_package_until_its_decider_signs(package, keys):
    """Step 2. Completeness is the gate's question, not the signer's."""
    space, _ = keys
    assert _uofa("sign", package, "--key", space, "--as", "issuer").returncode == 0

    r = _uofa("check", package, "--skip-rules", "--pubkey",
              space.with_suffix(".pub"), "--pack", "vv40")
    assert r.returncode != 0, "an unsigned asserted verdict is an incomplete package"
    assert "C1b" in r.stdout or "awaiting" in r.stdout


def test_a_second_party_signs_afterwards_and_the_seal_survives(package, keys):
    """Step 3+4. The order that was unreachable, now end to end and green.

    Two DIFFERENT keys: this is the multi-party case, not the composed solo act.
    The seal was computed over the measurement view, so the decision arriving
    afterwards does not disturb it -- which is exactly what A6 designed the
    two-scope split to guarantee.
    """
    space, reviewer = keys
    assert _uofa("sign", package, "--key", space, "--as", "issuer").returncode == 0
    sealed = json.loads(package.read_text())["signature"]

    r = _uofa("sign", package, "--key", reviewer, "--as", "reviewer")
    assert r.returncode == 0, r.stderr + r.stdout

    after = json.loads(package.read_text())
    assert after["signature"] == sealed, \
        "the decision must not disturb the seal -- that is the two-scope promise"
    assert after["hasDecisionRecord"]["hasDecisionSignature"]["signatureRole"] == "reviewer"

    r = _uofa("check", package, "--skip-rules", "--pubkey",
              space.with_suffix(".pub"), "--pack", "vv40")
    assert r.returncode == 0, r.stderr + r.stdout


def test_verify_reports_the_two_parties_as_independent(package, keys):
    """Independence is derived from key IDENTITY, never key count."""
    space, reviewer = keys
    _uofa("sign", package, "--key", space, "--as", "issuer")
    _uofa("sign", package, "--key", reviewer, "--as", "reviewer")

    r = _uofa("verify", package, "--pubkey", space.with_suffix(".pub"),
              "--decision-pubkey", reviewer.with_suffix(".pub"))
    assert r.returncode == 0, r.stderr + r.stdout
    assert "independent attestation" in r.stdout


def test_the_solo_composed_act_reports_as_single_party(package, keys):
    """The same package, one party wearing both hats: legitimate, and labeled."""
    space, _ = keys
    assert _uofa("sign", package, "--key", space,
                 "--as", "issuer,reviewer").returncode == 0
    r = _uofa("verify", package, "--pubkey", space.with_suffix(".pub"),
              "--decision-pubkey", space.with_suffix(".pub"))
    assert r.returncode == 0
    assert "single-party configuration" in r.stdout
