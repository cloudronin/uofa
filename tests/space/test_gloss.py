"""Gloss coverage + lookup tests."""

from __future__ import annotations

from space.gloss import gloss_for, load_gloss
from uofa_cli.excel_constants import NASA_ALL_FACTOR_NAMES, VV40_FACTOR_NAMES


def test_every_factor_has_a_nonempty_gloss():
    g = load_gloss()
    for name in set(VV40_FACTOR_NAMES) | set(NASA_ALL_FACTOR_NAMES):
        entry = g.get(name)
        assert entry, f"no gloss for {name!r}"
        assert entry.get("plain_name"), f"blank plain_name for {name!r}"
        assert entry.get("what_it_means"), f"blank what_it_means for {name!r}"


def test_metadata_keys_excluded():
    g = load_gloss()
    assert not any(k.startswith("_") for k in g)  # _README dropped


def test_gloss_for_falls_back_when_missing():
    out = gloss_for("Not a real factor", load_gloss())
    assert out["plain_name"] == "Not a real factor"
    assert out["what_it_means"] == ""
