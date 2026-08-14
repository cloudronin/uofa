"""The demo path is not a fork of the build path.

The advisors' rule for the download feature: *if the demo path can produce a
pack the CLI path would reject, that is a defect.* These tests are the
mechanical version of that rule. They exist because "we call the same function"
is an easy thing to say and an easy thing to stop being true -- a Space-only
default, a Space-only field, a Space-only base_uri, and the two paths diverge
while both still returning something that looks like a package.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from space import pipeline
from uofa_cli import integrity
from uofa_cli.card_bundle import deterministic_import_dict
from uofa_cli.excel_mapper import map_to_jsonld

_CARD = "# A model\n\nTrained on public data. Evaluated on a held-out split.\n"


@pytest.fixture
def import_data():
    return deterministic_import_dict(_CARD, "model-credibility", "org/m",
                                     "https://huggingface.co/org/m")


# Two fields carry wall-clock time, so a package hash is time-dependent by
# design: the same evidence signed twice yields different hashes. That is
# correct (they are provenance) but it means these tests must pin BOTH, and
# there are exactly two -- a build that straddles a second boundary differs in
# `generatedAtTime` and in `provenanceChain[].timestamp`. Pinning them is what
# lets everything else be compared exactly; the alternative, "compare all
# fields except a few", is how a Space-only field slips through unnoticed.
_FROZEN_TIME = "2026-01-01T00:00:00Z"
_TIME_FIELDS = ("generatedAtTime", "timestamp")


def _freeze_times(doc: dict) -> dict:
    """Normalize every wall-clock field, at any depth."""
    if isinstance(doc, dict):
        for key, value in doc.items():
            if key in _TIME_FIELDS and isinstance(value, str):
                doc[key] = _FROZEN_TIME
            else:
                _freeze_times(value)
    elif isinstance(doc, list):
        for item in doc:
            _freeze_times(item)
    return doc


def test_exactly_two_fields_vary_between_builds(import_data, tmp_path):
    """Guard the guard: if a third time-varying field appears, _freeze_times
    would silently stop normalizing the document and the equality tests below
    would start passing for the wrong reason."""
    a = json.loads(_space_built(import_data, tmp_path / "a").read_text(encoding="utf-8"))
    b = json.loads(_space_built(import_data, tmp_path / "b").read_text(encoding="utf-8"))
    assert _freeze_times(a) == _freeze_times(b), (
        "two builds of one input differ in something other than the known "
        "timestamps; the package hash is nondeterministic in a new way"
    )


def _rehash(path: Path) -> str:
    doc = _freeze_times(json.loads(path.read_text(encoding="utf-8")))
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return integrity.load_and_hash(path)[2]


def _cli_built(data, out: Path) -> Path:
    """The bytes `uofa import` writes, via the same mapper and serialization
    (commands/import_excel.py: map_to_jsonld -> json.dump(sort_keys=True))."""
    doc = map_to_jsonld(data, packs=["model-credibility"], source_path=Path("card.md"))
    pipeline._assign_factor_ids(doc)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, sort_keys=True)
    return out


def _space_built(data, work: Path) -> Path:
    """The bytes the Space writes (pipeline.finalize_from_data: indent=2, unsorted)."""
    work.mkdir(parents=True, exist_ok=True)
    pipeline.finalize_from_data(data, "model-credibility", work,
                                source_name="card.md", assess_sufficiency=False)
    return work / pipeline.PACK_MEMBER_JSONLD


def test_space_and_cli_produce_identical_hashes(import_data, tmp_path):
    """The anti-fork guard. One import dict, both build paths, same digest.

    If this fails, the Space has started emitting something the CLI would not:
    read the reported diff before touching this test."""
    cli = _cli_built(import_data, tmp_path / "cli.jsonld")
    space = _space_built(import_data, tmp_path / "space")

    cli_hash, space_hash = _rehash(cli), _rehash(space)

    if cli_hash != space_hash:
        a = json.loads(cli.read_text(encoding="utf-8"))
        b = json.loads(space.read_text(encoding="utf-8"))
        only_cli, only_space = sorted(set(a) - set(b)), sorted(set(b) - set(a))
        changed = sorted(k for k in set(a) & set(b) if a[k] != b[k])
        pytest.fail(
            f"Space and CLI documents hash differently.\n"
            f"  CLI-only fields:   {only_cli}\n"
            f"  Space-only fields: {only_space}\n"
            f"  Differing values:  {changed}"
        )


def test_on_disk_formatting_does_not_affect_the_hash(import_data, tmp_path):
    """The Space writes indent=2/unsorted, `uofa import` writes sort_keys=True.

    That difference is benign because hashing re-parses and re-canonicalizes.
    Pinned here so nobody 'fixes' the formatting into a real divergence, or
    removes the re-canonicalization believing the files already match."""
    cli = _cli_built(import_data, tmp_path / "cli.jsonld")
    space = _space_built(import_data, tmp_path / "space")

    # Same content, different serialization: sorted vs insertion order.
    a = _freeze_times(json.loads(cli.read_text(encoding="utf-8")))
    b = _freeze_times(json.loads(space.read_text(encoding="utf-8")))
    sorted_bytes = json.dumps(a, indent=2, sort_keys=True)
    unsorted_bytes = json.dumps(b, indent=2)
    assert sorted_bytes != unsorted_bytes, (
        "the two serializations are now byte-identical; this test's premise "
        "changed and its guard value should be re-examined"
    )
    assert (integrity.canonicalize_and_hash(integrity.strip_integrity_fields(a))[1]
            == integrity.canonicalize_and_hash(integrity.strip_integrity_fields(b))[1])


def test_package_is_attributed_even_without_ambient_identity(import_data, tmp_path, monkeypatch):
    """The divergence the in-process equality test could not see.

    `excel_mapper._operator_identity()` resolves UOFA_ASSESSOR -> `git config
    user.name` -> $USER. On a developer machine the git config answers, so both
    build paths get the same name and the equality test above passes. In the
    deployed container none of them resolve, wasAttributedTo comes out missing,
    and the package fails C2 on a field a CLI run would have populated: same
    input, different document, purely from the environment.

    Caught only in production, on a real download. This simulates the container
    rather than the developer machine, which is the environment that matters
    for anything the Space hands out.
    """
    # Strip every ambient identity source EXCEPT the default space.pipeline
    # installs at import, which is the thing under test. Deliberately no
    # module reload: reloading swaps class identities out from under other
    # tests (isinstance checks against _StageError start failing).
    monkeypatch.delenv("USER", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "nohome"))
    monkeypatch.setenv("PATH", "/nonexistent")   # git unreachable
    # UOFA_ASSESSOR is deliberately NOT set here: the only thing that can
    # supply it is the default space.pipeline installs at import, so deleting
    # that line has to make this test fail.

    work = tmp_path / "work"
    work.mkdir()
    pipeline.finalize_from_data(import_data, "model-credibility", work,
                                source_name="card.md", assess_sufficiency=False)
    doc = json.loads((work / pipeline.PACK_MEMBER_JSONLD).read_text(encoding="utf-8"))

    assert doc.get("wasAttributedTo"), (
        "package produced with no attribution. A signed package that declines "
        "to say who produced it contradicts its own signature, and C2 fails on "
        "a field the CLI path populates from git config."
    )


def test_pipeline_installs_an_assessor_default_at_import():
    """The guarantee the test above relies on: importing space.pipeline is
    enough for the Space to have an identity, with no deployment config."""
    import os

    assert os.environ.get("UOFA_ASSESSOR"), "no assessor default installed"
    assert "demo" in pipeline.ASSESSOR_LABEL.lower(), (
        "the Space must not attribute packages to something that reads as a "
        "person or a production issuer"
    )


def test_space_does_not_call_integrity_sign_file_directly():
    """`integrity.sign_file` is pure cryptography: it signs whatever it is given.

    The synthetic-sample and issuer-scope refusals live in package_policy. A
    Space that reached for sign_file would get the signing and none of the
    policy -- which is the exact hole package_policy was extracted to close."""
    offenders = []
    for path in Path(__file__).resolve().parents[2].joinpath("space").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "sign_file" in text:
            offenders.append(path.name)
    assert not offenders, (
        f"{offenders} reference integrity.sign_file directly. Sign through "
        f"package_policy.sign_package so the refusals apply."
    )


def test_signed_space_package_carries_no_decision_block(import_data, tmp_path, demo_key_env):
    """AGENTS.md section 12: an issuer-held key attests provenance, never a
    human judgment. The carve-out that lets the demo sign at all depends on the
    emitted package containing no decision content."""
    pipeline.finalize_from_data(import_data, "model-credibility", tmp_path,
                                source_name="org/m", assess_sufficiency=False)
    doc = json.loads((tmp_path / pipeline.PACK_MEMBER_JSONLD).read_text(encoding="utf-8"))
    assert "engineerDecision" not in doc


def test_no_absolute_host_path_leaks_into_a_signed_package(import_data, tmp_path, demo_key_env):
    """The source path is provenance, and the package is public. A container
    temp path in a signed artifact is a privacy leak, not a formatting nit."""
    work = tmp_path / "work"
    work.mkdir()
    pipeline.finalize_from_data(import_data, "model-credibility", work,
                                source_name=str(work / "uploaded.pdf"),
                                assess_sufficiency=False)
    text = (work / pipeline.PACK_MEMBER_JSONLD).read_text(encoding="utf-8")
    assert str(tmp_path) not in text, "absolute host path embedded in the package"
