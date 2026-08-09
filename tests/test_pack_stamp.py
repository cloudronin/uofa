"""A package must validate the same way for everyone who runs it.

Before R0b a package recorded nothing about its standard, so validation was
relative to a `--pack` flag the operator remembered to pass — defaulting to
`vv40`. A NASA-STD-7009B package validated as plain `uofa shacl pkg.jsonld` was
therefore asked for a V&V 40 context of use and failed for a reason belonging to
a different standard.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from uofa_cli import paths


class _Args:
    def __init__(self, file, active_packs=None):
        self.file = file
        self.active_packs = active_packs


def _write(tmp_path, name, node):
    p = tmp_path / name
    p.write_text(json.dumps({"@graph": [node]}))
    return p


def test_a_stamped_package_resolves_to_its_own_packs(tmp_path):
    p = _write(tmp_path, "nasa.jsonld", {"validatedWithPacks": ["nasa-7009b"]})
    assert paths.resolve_active_packs(_Args(p)) == ["nasa-7009b"]


def test_an_explicit_flag_still_wins(tmp_path):
    """The stamp is a default, not a lock — an operator can always override."""
    p = _write(tmp_path, "nasa.jsonld", {"validatedWithPacks": ["nasa-7009b"]})
    assert paths.resolve_active_packs(_Args(p, ["vv40"])) == ["vv40"]


def test_an_unstamped_package_falls_back(tmp_path):
    """All 64 packages predate the stamp; the fallback must stay the default."""
    p = _write(tmp_path, "old.jsonld", {"conformsToProfile": "x"})
    assert paths.resolve_active_packs(_Args(p)) == ["vv40"]


def test_an_unreadable_file_does_not_masquerade_as_unstamped(tmp_path):
    """A lookup wrapped in a catch-all turns a bug into a plausible default.

    The first version caught bare `Exception` and called `pathlib.Path` in a
    module importing only `Path`, so every call raised NameError and returned
    None — reporting "no pack recorded" for every package in the repo, which
    looks exactly like the correct answer for the 64 that genuinely have none.
    """
    src = pathlib.Path(paths.__file__).read_text()
    body = src.split("def packs_recorded_in")[1].split("\ndef ")[0]
    assert "except Exception" not in body, (
        "catch-all around the stamp lookup; a NameError here is indistinguishable "
        "from an unstamped package")
    assert "pathlib.Path(" not in body, "paths.py imports Path, not pathlib"


def test_the_mapper_records_the_pack_set_it_built_under():
    """Recorded as the pack SET, because a standard does not resolve uniquely.

    ASME-VV40-2018 is declared by vv40, disposition and surrogate alike, so
    standard -> pack is ambiguous and only the pack set answers "how was this
    validated when it was made".
    """
    src = pathlib.Path(
        paths.__file__).parent.joinpath("excel_mapper.py").read_text()
    assert '"validatedWithPacks": list(packs)' in src


def test_every_pack_declares_its_standards():
    """The stamp is only meaningful while packs say what they cover."""
    root = pathlib.Path(paths.__file__).parent.parent.parent / "packs"
    if not root.is_dir():
        pytest.skip("packs/ not present")
    for manifest in sorted(root.glob("*/pack.json")):
        d = json.loads(manifest.read_text())
        assert "standards" in d, f"{manifest.parent.name} declares no standards key"


def test_the_cli_default_is_none_so_no_flag_stays_distinguishable():
    """The default belongs to the resolver, not the parser.

    `cli.py` used to set `args.active_packs = ... or ["vv40"]`, applying the
    default at parse time. A command then could not tell an explicit
    `--pack vv40` from a defaulted one, so the warning that says "no pack
    recorded, I assumed vv40" was unreachable — and an unstamped 7009A package
    validated as V&V 40 in silence, which is the defect the stamp exists to
    close.
    """
    src = (pathlib.Path(paths.__file__).parent / "cli.py").read_text()
    assert 'args.pack or ["vv40"]' not in src, (
        "the parser is applying the pack default again; None is the only value "
        "that keeps 'no flag was given' answerable")
    assert "args.active_packs = _pre_args.pack or args.pack or None" in src


def test_the_shipped_7009a_examples_are_stamped():
    """They are the artefacts demonstrating the standard, and the fallback's worst case.

    Unstamped, they resolve to the `vv40` default and are validated against a
    standard they do not follow.
    """
    root = pathlib.Path(paths.__file__).parent.parent.parent
    examples = sorted((root / "packs" / "nasa-7009b" / "examples").rglob("*.jsonld"))
    if not examples:
        pytest.skip("nasa-7009b examples not present")
    for f in examples:
        assert paths.packs_recorded_in(f) == ["nasa-7009b"], (
            f"{f.name} records {paths.packs_recorded_in(f)}; unstamped it would "
            f"validate as vv40")
