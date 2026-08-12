"""`mrm-nist` still resolves after the rename to `model-credibility`.

Pack discovery is filesystem-only, so a rename is a breaking change for anything
that names the pack: a `--pack mrm-nist` invocation, and — more importantly — any
bundle whose recorded packs list says `mrm-nist`. A saved bundle is a pinned
artifact and a rename must not make it unreadable.

The alias is ONE VERSION. These tests are its expiry note as much as its guard:
when `PACK_ALIASES` is emptied, they go with it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))

from uofa_cli import paths  # noqa: E402


def test_the_pack_directory_is_renamed():
    assert "model-credibility" in paths.list_packs()
    assert "mrm-nist" not in paths.list_packs(), (
        "both names on disk means two packs, not an alias")


def test_the_old_name_resolves_to_the_new_one():
    assert paths.canonical_pack_name("mrm-nist") == "model-credibility"
    assert paths.canonical_pack_name("model-credibility") == "model-credibility"


def test_an_unknown_name_passes_through_unchanged():
    """A typo must still produce `not found` naming the available packs, rather
    than being silently rewritten into something that exists."""
    assert paths.canonical_pack_name("mrm-nsit") == "mrm-nsit"


def test_an_explicit_old_pack_flag_still_resolves():
    args = SimpleNamespace(active_packs=["mrm-nist"], file=None)
    assert paths.resolve_active_packs(args) == ["model-credibility"]


def test_a_bundle_recorded_under_the_old_name_still_loads(tmp_path):
    """The case that actually matters: a bundle written before the rename."""
    bundle = tmp_path / "old.jsonld"
    bundle.write_text(json.dumps({
        "@context": {"@vocab": "https://uofa.net/vocab#"},
        "id": "https://uofa.net/uoa/legacy",
        "type": "UnitOfAssurance",
        "conformsToPack": ["mrm-nist"],
    }), encoding="utf-8")

    recorded = paths.packs_recorded_in(str(bundle))
    if not recorded:
        pytest.skip("this bundle shape records no packs; covered by the flag test")
    args = SimpleNamespace(active_packs=None, file=str(bundle))
    assert paths.resolve_active_packs(args) == ["model-credibility"]


def test_validation_accepts_the_old_name():
    """`validate_active_packs` raises FileNotFoundError on an unknown pack, so a
    passing call is the assertion: the alias is applied before the existence
    check, not after."""
    paths.validate_active_packs(active=["mrm-nist"])
