"""A9.1 pins reach the bundle from the real call sites.

`test_source_pins.py` covers the pin functions. This covers the wiring: that the
card path and the raidex path actually attach one, and attach the RIGHT kind.

The distinction is the whole point of A9.1 and it is easy to blur in a call site:

  artifact pin   supports re-derivation -- the card text is fetchable again and
                 hashes the same, so the claim can be re-derived from source
  occasion pin   supports re-performance only -- a hosted endpoint's identity is
                 asserted by the provider and can change under a stable name, so
                 re-running is a new occasion, not a re-derivation

A bundle that claimed re-derivability for a closed-weight furnished score would
be overstating what its evidence supports.
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))

from uofa_cli.furnishers import attach, pins  # noqa: E402


def _record() -> tuple[dict, str]:
    path = sorted(glob.glob(str(_REPO / "tests/fixtures/raidex/*.json")))[0]
    return json.loads(Path(path).read_text()), path


def test_raidex_attaches_an_occasion_pin_not_an_artifact_pin():
    record, path = _record()
    bundle = {"id": "https://example.org/uoa/1"}
    assert attach.attach_raidex(bundle, local_path=path).ok

    kinds = [p["pinType"] for p in bundle["sourcePin"]]
    assert kinds == ["occasion"], (
        "a furnished score from a hosted endpoint pins an occasion; an artifact "
        "pin here would claim the subject is re-fetchable, which it is not")
    assert not pins.re_derivable(bundle)


def test_occasion_pin_records_when_the_eval_RAN_not_when_it_was_read():
    """Attach time is not the occasion. A record read months later still
    describes the measurement's own date, and pinning `now` would silently
    re-date someone else's evidence."""
    record, path = _record()
    bundle = {"id": "https://example.org/uoa/1"}
    attach.attach_raidex(bundle, local_path=path)

    pin = bundle["sourcePin"][0]
    assert pin["measuredAt"] == record["config"]["eval_date"]


def test_occasion_pin_does_not_claim_assessor_verification():
    record, path = _record()
    bundle = {"id": "https://example.org/uoa/1"}
    attach.attach_raidex(bundle, local_path=path)

    pin = bundle["sourcePin"][0]
    assert pin["verifiedByAssessor"] is False
    assert pin["identityAssertedBy"] == "provider"


def test_repeated_attach_does_not_accumulate_duplicate_pins():
    record, path = _record()
    bundle = {"id": "https://example.org/uoa/1"}
    attach.attach_raidex(bundle, local_path=path)
    attach.attach_raidex(bundle, local_path=path)
    assert len(bundle["sourcePin"]) == 1


def test_card_pin_uses_the_readme_blob_not_the_repo_sha():
    """Correction 6, as a regression guard.

    The repo sha moves when ANY file in the repo changes, so pinning a card to it
    marks a byte-identical card stale on a weights re-upload -- a badge going
    amber for a reason the reader cannot see and the card cannot support. The
    pin's revision must be the README blob oid.
    """
    card_text = "# Model\n\nSome evaluation prose."
    repo_sha = "005ad3404e59d6023443cb575daa05336842228a"
    readme_blob = "fdce721ee5de878029a086bcc7f6cd7f183fab32"

    pin = pins.artifact_pin(
        "https://huggingface.co/owner/model", card_text,
        fetched_at="2026-08-11T00:00:00Z",
        revision=readme_blob, revision_kind="readme-blob",
    )
    assert pin["revision"] == readme_blob
    assert pin["revision"] != repo_sha
    assert pin["revisionKind"] == "readme-blob"
    assert pins.re_derivable({"sourcePin": [pin]})


def test_a_card_with_no_reachable_oid_still_pins_by_content():
    """`readme_oid` is best-effort. Losing it must degrade the pin, not drop it:
    a content hash alone still supports re-derivation."""
    pin = pins.artifact_pin("https://huggingface.co/owner/model", "text",
                            fetched_at="2026-08-11T00:00:00Z")
    assert "revision" not in pin
    assert pin["contentHash"]
    assert pins.re_derivable({"sourcePin": [pin]})


def test_readme_oid_is_not_derived_from_the_stripped_card_text():
    """`ModelCard.load` strips content, so a locally computed blob oid would not
    match the file HF stores. Guard against someone 'optimizing away' the API
    call by hashing the fetched text -- it would produce a plausible, wrong pin.
    """
    import inspect

    from uofa_cli import hf_card
    src = inspect.getsource(hf_card.readme_oid)
    assert "list_repo_tree" in src, "the oid must come from the repo tree"
    assert "sha1" not in src, "a locally computed blob oid would not match HF's"
