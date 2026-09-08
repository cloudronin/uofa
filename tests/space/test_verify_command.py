"""The re-verify command shown on screen must name files the zip contains.

The signed result page prints a command a reviewer is invited to copy and run
against the package they just downloaded. It named `keys/demo.pub`. The pack
contains `keys/uofa-issuer.pub`. Copying it produced a missing-file error.

Found 2026-09-08, minutes after the Space's issuer signing key was configured.
The defect had been unreachable until then: with no key there is no signed
package, no download control, and no command on screen. **Turning the gate green
is what made it visible**, which is the argument for re-running a verification
pass after a blocker clears rather than assuming the unblocked path is fine.

`VERIFY.txt` *inside* the zip was always correct, because it is formatted from
`PACK_MEMBER_JSONLD` and `PACK_MEMBER_PUBKEY`, and
`test_pack_cli_roundtrip.py::test_verify_txt_command_is_the_one_that_works`
pins it. The on-screen string was a second, hand-written copy of the same
instruction, and only the copy drifted.

This is the same class as `tests/test_documented_model_ids.py` and
`tests/space/test_deploy_doc_env_names.py`: **an instruction that cannot be
followed is the same defect as a setting that is never read.** All three look
right in the artifact and fail only when someone acts on them. The shared cause
is a second copy of a name that already had an authoritative source.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from space.gloss import load_gloss
from space.pipeline import (
    PACK_MEMBER_JSONLD,
    PACK_MEMBER_PUBKEY,
    _authenticity_block,
)
from space.reviewer import render_reviewer_html

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_FIX = Path(__file__).with_name("fixtures")
GLOSS = load_gloss()


def _signed_payload():
    payload = json.loads((_FIX / "morrison_cou1_state.json").read_text(encoding="utf-8"))
    payload["context"]["authenticity"] = _authenticity_block(
        signed=True,
        package_hash="sha256:" + "0" * 64,
        integrity_checked=True,
    )
    return payload


def test_the_command_names_the_members_the_pack_actually_holds():
    """Built from the pack constants, so it cannot drift from the zip."""
    cmd = _authenticity_block(signed=True, package_hash="sha256:x")["verify_command"]

    assert PACK_MEMBER_JSONLD in cmd, f"{cmd!r} does not name the signed file"
    assert PACK_MEMBER_PUBKEY in cmd, f"{cmd!r} does not name the packed pubkey"


def test_the_rendered_page_shows_that_command_and_not_a_hardcoded_one():
    """End to end: what a reader copies off the screen."""
    html = render_reviewer_html(_signed_payload(), GLOSS)
    expected = _authenticity_block(signed=True, package_hash="sha256:x")["verify_command"]

    assert expected in html, (
        f"the signed page does not show {expected!r}; a second copy of the "
        "command has been introduced somewhere"
    )
    assert "keys/demo.pub" not in html, (
        "keys/demo.pub is back on screen. It is not a member of the pack, so a "
        "reader copying this command gets a missing-file error."
    )


def test_the_unsigned_page_offers_no_package_command():
    """No package means no command claiming one can be verified.

    The unsigned branch deliberately carries no `verify_command`; the renderer
    falls back to generic help rather than printing an instruction for a file
    the reader was never given.
    """
    assert "verify_command" not in _authenticity_block()

    payload = json.loads((_FIX / "morrison_cou1_state.json").read_text(encoding="utf-8"))
    payload["context"]["authenticity"] = _authenticity_block()
    html = render_reviewer_html(payload, GLOSS)

    assert PACK_MEMBER_PUBKEY not in html, (
        "the unsigned page names a packed key, implying a downloadable package "
        "that was never produced"
    )


@pytest.mark.parametrize("member", [PACK_MEMBER_JSONLD, PACK_MEMBER_PUBKEY])
def test_pack_member_names_are_not_empty(member):
    """Guard the guard: empty constants would make every check above vacuous."""
    assert member and member.strip()


# ── the same instruction, wherever it is printed ─────────────

# Docs a user follows to check a pack the Space produced. Each is in the
# verification spec's scope.
_DOCS = ("space/README.md", "space/DEPLOY.md", "docs/credibility-inspector.md")


def _verify_commands_in_docs() -> list[tuple[str, str, int]]:
    """Every `uofa verify` line in those docs, as (doc, line, line_no).

    Blockquote and comment lines are skipped so a dated correction can quote the
    command it is correcting.
    """
    out = []
    for rel in _DOCS:
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            s = line.strip()
            if s.startswith((">", "#", "//")):
                continue
            if "uofa verify" in s:
                out.append((rel, s, n))
    return out


def test_the_docs_scan_finds_commands_at_all():
    """Guard the guard: matching nothing would pass vacuously."""
    assert _verify_commands_in_docs(), (
        "no `uofa verify` command found in any user-facing doc; the scan has "
        "drifted from how they are written"
    )


def test_no_doc_tells_a_user_to_name_a_file_the_pack_lacks():
    """Every path a documented verify command names must be a pack member.

    `space/README.md` documented `--decision-pubkey keys/demo-reviewer.pub` and
    `docs/credibility-inspector.md` documented `--pubkey keys/demo-reviewer.pub`.
    Neither file is in the pack, whose five members are fixed constants, so both
    commands failed on a missing file. The README's also implied a decision
    signature the Space deliberately does not create.

    Fifth instance of one shape in this workstream: an instruction that cannot be
    followed, because a name was copied instead of read from its source.
    """
    from space import pipeline

    members = {
        pipeline.PACK_MEMBER_JSONLD, pipeline.PACK_MEMBER_REPORT,
        pipeline.PACK_MEMBER_MANIFEST, pipeline.PACK_MEMBER_PUBKEY,
        pipeline.PACK_MEMBER_VERIFY,
    }
    bad = []
    for rel, line, n in _verify_commands_in_docs():
        for tok in line.replace("\\", " ").split():
            looks_like_a_packed_path = tok.startswith("keys/") or tok.endswith(".jsonld")
            if looks_like_a_packed_path and tok not in members:
                bad.append((rel, n, tok, line))
    assert not bad, (
        "documented verify commands name files the pack does not contain:\n"
        + "\n".join(f"  {rel}:{n}  {tok!r}\n    {line}" for rel, n, tok, line in bad)
        + f"\n\nPack members are: {sorted(members)}"
    )


# ── signed is not the same fact as downloadable ──────────────


def test_a_signed_run_with_no_pack_does_not_promise_a_download():
    """The page must not point at a button that is not there.

    Signing reads the PRIVATE key from the environment. Assembling the pack
    needs the PUBLIC half on disk. Those can disagree, and on 2026-09-08 the
    deployed Space had the first without the second: the readout rendered its
    signed branch, said "Download the package below and re-check it yourself",
    and offered no download.

    `test_without_a_signing_key_the_run_stays_unsigned` covers the no-key case.
    Nothing covered signed-yet-no-pack, so the suite could not see it.
    """
    payload = json.loads((_FIX / "morrison_cou1_state.json").read_text(encoding="utf-8"))
    auth = _authenticity_block(signed=True, package_hash="sha256:" + "0" * 64,
                               integrity_checked=True)
    auth["pack_available"] = False
    payload["context"]["authenticity"] = auth
    html = render_reviewer_html(payload, GLOSS)

    assert "Download the package below" not in html, (
        "the page promises a download on a run that produced no package"
    )
    assert "could not" in html and "assemble" in html, (
        "the page does not say the package could not be assembled, so a reader "
        "cannot tell a missing button from a missing signature"
    )
    # The signature itself is still real and must still be reported.
    assert "Signed by the demo issuer key" in html


def test_a_signed_run_with_a_pack_still_promises_the_download():
    """The normal case must be unchanged by the guard above."""
    payload = json.loads((_FIX / "morrison_cou1_state.json").read_text(encoding="utf-8"))
    auth = _authenticity_block(signed=True, package_hash="sha256:" + "0" * 64,
                               integrity_checked=True)
    auth["pack_available"] = True
    payload["context"]["authenticity"] = auth

    assert "Download the package below" in render_reviewer_html(payload, GLOSS)


def test_a_caller_that_never_asks_for_a_pack_is_not_told_one_is_missing():
    """Absent means not applicable, not failed.

    The CLI report path builds an authenticity block and never requests a pack.
    It must keep the original wording rather than reporting a failure that did
    not happen.
    """
    payload = json.loads((_FIX / "morrison_cou1_state.json").read_text(encoding="utf-8"))
    auth = _authenticity_block(signed=True, package_hash="sha256:" + "0" * 64,
                               integrity_checked=True)
    assert "pack_available" not in auth, (
        "the authenticity block now claims pack availability at construction, "
        "before the pack is built; that is the conflation this guards"
    )
    payload["context"]["authenticity"] = auth

    assert "Download the package below" in render_reviewer_html(payload, GLOSS)
