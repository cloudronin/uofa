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
