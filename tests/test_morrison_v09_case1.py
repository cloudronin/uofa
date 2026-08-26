"""Case 1, end to end, with throwaway keys: the source already decided.

Morrison's credibility assessment team accepted the model in 2019 and published
that acceptance. UofA transcribes it. The invariants this proves:

- the decision record's warrant is its ANCHOR, not a signature;
- no signature from Morrison's team exists, and the format never implies one could;
- the issuer seal covers the measurement view and is lawful over an extracted
  record with no live decider (§3.3);
- `check` does NOT report the package incomplete: nothing is owed, because an
  extracted record's warrant is already present.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SIBLINGS = {cou: REPO_ROOT / "packs/vv40/examples/morrison-v09" / cou
            / f"uofa-morrison-v09-{cou}.jsonld" for cou in ("cou1", "cou2")}


def _uofa(*args):
    return subprocess.run([sys.executable, "-m", "uofa_cli", *[str(a) for a in args]],
                          capture_output=True, text=True, cwd=str(REPO_ROOT))


@pytest.fixture
def throwaway_key(tmp_path):
    """A key that exists for one test run. No production key is ever needed to
    prove this round trip, and no key identity in the tree implies an
    endorsement nobody gave."""
    key = tmp_path / "fixture.key"
    assert _uofa("keygen", key).returncode == 0
    return key


def _stage(tmp_path, cou, *, with_archive=True, corrupt_source=False):
    """Stage the package AND its archive, the way a real handoff travels.

    An `archive://` locator names something inside the package's own archive, so
    a package that arrives without it is genuinely unresolvable -- that is a
    state to test, not a state to engineer around.
    """
    src = SIBLINGS[cou]
    dst = tmp_path / src.name
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    if with_archive:
        pdf = (REPO_ROOT / "packs/vv40/examples/morrison/source"
               / f"decision_rationale_{cou}.pdf")
        out = tmp_path / "morrison" / "source" / pdf.name
        out.parent.mkdir(parents=True, exist_ok=True)
        data = pdf.read_bytes()
        out.write_bytes(data + b"\n%% altered" if corrupt_source else data)
    return dst


@pytest.fixture(params=sorted(SIBLINGS))
def staged(request, tmp_path):
    return _stage(tmp_path, request.param)


def test_an_extracted_record_takes_the_issuer_seal_alone(staged, throwaway_key):
    """§3.3: no live decider means no decision role is owed."""
    r = _uofa("sign", staged, "--key", throwaway_key, "--as", "issuer")
    assert r.returncode == 0, r.stderr + r.stdout
    assert "unsigned asserted" not in (r.stderr + r.stdout), \
        "an extracted record owes no signature, so nothing should be warned about"


def test_verify_reports_the_anchor_as_the_warrant(staged, throwaway_key):
    assert _uofa("sign", staged, "--key", throwaway_key, "--as", "issuer").returncode == 0
    r = _uofa("verify", staged, "--pubkey", throwaway_key.with_suffix(".pub"))
    assert r.returncode == 0, r.stderr + r.stdout
    assert "extracted" in r.stdout and "anchor resolves" in r.stdout
    assert "signature valid" not in r.stdout.lower().replace("measurement signature valid", ""), \
        "no decision signature exists here and none should be claimed"


def test_the_source_never_signs(staged):
    rec = json.loads(staged.read_text(encoding="utf-8"))["hasDecisionRecord"]
    assert rec["decisionProvenance"] == "extracted"
    assert "hasDecisionSignature" not in rec
    assert rec["decisionAnchor"]["anchorLocator"].startswith("archive://")


def test_check_does_not_call_an_extracted_package_incomplete(staged, throwaway_key):
    """The completeness gate must distinguish 'nobody signed' from 'nobody owes'."""
    assert _uofa("sign", staged, "--key", throwaway_key, "--as", "issuer").returncode == 0
    r = _uofa("check", staged, "--skip-rules", "--pubkey",
              throwaway_key.with_suffix(".pub"), "--pack", "vv40")
    assert "awaiting" not in r.stdout, \
        "an extracted record's warrant is its anchor; nothing is owed"


# ── the anchor round-trip ladder ────────────────────────────────────────────
#
# Red-pending since the decision-anchor work began, and green only now that the
# resolver actually opens the file. Each rung is a different answer, and the
# whole point is that they stay different: "I checked and it matches" is not
# "I checked and it does not" is not "I could not check".


def test_intact_source_resolves(tmp_path, throwaway_key):
    pkg = _stage(tmp_path, "cou1")
    assert _uofa("sign", pkg, "--key", throwaway_key, "--as", "issuer").returncode == 0
    r = _uofa("verify", pkg, "--pubkey", throwaway_key.with_suffix(".pub"))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "anchor resolves" in r.stdout
    assert "sha256 verified against" in r.stdout, \
        "the report must say what it opened, or the check is unauditable"


def test_a_corrupted_source_is_caught_and_both_hashes_named(tmp_path, throwaway_key):
    """The rung that proves the check can fail at all.

    Before the resolver opened anything, this exact package reported
    "anchor resolves" -- a green about a file nobody read.
    """
    pkg = _stage(tmp_path, "cou1", corrupt_source=True)
    assert _uofa("sign", pkg, "--key", throwaway_key, "--as", "issuer").returncode == 0
    r = _uofa("verify", pkg, "--pubkey", throwaway_key.with_suffix(".pub"))
    out = r.stdout + r.stderr
    assert r.returncode != 0, "a false transcription claim must fail the package"
    assert "DOES NOT match" in out
    assert "pinned:" in out and "actual:" in out, "name both hashes"
    assert "decision 1" in out, "name the record"


def test_a_missing_source_is_unresolvable_not_failed(tmp_path, throwaway_key):
    """A stranger with the package but not the archive.

    They must be told neither "verified" nor "tampered". Could-not-check is
    never checked-and-wrong, and silence is neither.
    """
    pkg = _stage(tmp_path, "cou1", with_archive=False)
    assert _uofa("sign", pkg, "--key", throwaway_key, "--as", "issuer").returncode == 0
    r = _uofa("verify", pkg, "--pubkey", throwaway_key.with_suffix(".pub"))
    out = r.stdout + r.stderr
    assert r.returncode == 0, "unreachable is not a package failure"
    assert "not available to resolve" in out
    assert "DOES NOT match" not in out and "anchor resolves" not in out, \
        "unreachable must not borrow either verdict"


def test_an_anchor_with_no_pin_cannot_be_checked_and_says_so(tmp_path, throwaway_key):
    pkg = _stage(tmp_path, "cou1")
    doc = json.loads(pkg.read_text(encoding="utf-8"))
    doc["hasDecisionRecord"]["decisionAnchor"].pop("anchorSha256")
    pkg.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    assert _uofa("sign", pkg, "--key", throwaway_key, "--as", "issuer").returncode == 0
    r = _uofa("verify", pkg, "--pubkey", throwaway_key.with_suffix(".pub"))
    assert "no sha256 pin" in (r.stdout + r.stderr)


def test_stripping_the_anchor_is_a_shacl_violation(tmp_path):
    """The other half of the ladder: the shape refuses an unanchored extraction."""
    pkg = _stage(tmp_path, "cou1")
    doc = json.loads(pkg.read_text(encoding="utf-8"))
    doc["hasDecisionRecord"].pop("decisionAnchor")
    pkg.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    r = subprocess.run(
        [sys.executable, "-m", "uofa_cli", "shacl", str(pkg), "--pack", "vv40"],
        capture_output=True, text=True, cwd=str(REPO_ROOT))
    assert r.returncode != 0
    assert "decisionAnchor" in (r.stdout + r.stderr)
