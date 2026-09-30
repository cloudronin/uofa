"""`uofa extract` refuses a pack it cannot fill, before anything is sent.

Found while planning the ISO 42001 readiness module. `iso42001` names no
extract prompt and no workbook template, and `uofa extract --pack iso42001`
never said so. `paths.extract_prompt` resolved to the pack directory,
`build_prompt` found no prompt in it and sent the generic schema instead --
V&V 40's factors on a 1-5 scale -- and `_find_pack_template` fell back to the
core workbook. The run called a model, wrote a V&V 40 workbook for an AI
management system, and exited 0.

Measured before the fix, with the free mock backend on the Morrison corpus:
`iso42001`, `surrogate`, `disposition` and `model-credibility` each exited 0
with "13 factors mapped", and so did a misspelled `--pack nope`. `core` names
a prompt file that does not exist.

`--keyless` had the same hole from the other side. It knows two factor sets,
and every pack that is not NASA was handed the V&V 40 one: `--keyless --pack
iso42001` also exited 0 with a workbook.

The rule now: a pack can be extracted only when it names an extract prompt
and a workbook template and both files exist. `--keyless` sends no prompt, so
it needs the template and one of the two factor sets it was built for.
Anything else exits 2 -- before setup is checked, before a file is read, and
before any model is called.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from uofa_cli import document_reader, keyless_extractor, llm_extractor, paths, setup_state
from uofa_cli.commands import extract_cmd

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "tests" / "fixtures" / "extract" / "morrison-evidence-cou1"


def _names_both(pack: str) -> bool:
    """Read the manifest here, rather than asking the code under test."""
    manifest = paths.pack_manifest(pack)
    home = paths.pack_dir(pack)
    return all(manifest.get(key) and (home / manifest[key]).is_file()
               for key in ("prompt", "template"))


ALL_PACKS = paths.list_packs()
FILLABLE = [p for p in ALL_PACKS if _names_both(p)]
UNFILLABLE = [p for p in ALL_PACKS if p not in FILLABLE]
KEYLESS_REFUSED = [p for p in ALL_PACKS if p not in ("vv40", "nasa-7009b")]


class _Reached(Exception):
    """Raised by a trapped step, so a run stops where it arrived."""


@pytest.fixture
def reached(monkeypatch, tmp_path):
    """Trap every step a refused run must not reach, and record arrivals."""
    log: list[str] = []

    def trap(owner, attr, label):
        def _stop(*_a, **_k):
            log.append(label)
            raise _Reached(label)
        monkeypatch.setattr(owner, attr, _stop)

    trap(setup_state, "assert_ready", "setup check")
    trap(document_reader, "discover_files", "file discovery")
    trap(llm_extractor, "extract", "model call")
    trap(keyless_extractor, "extract", "keyless extraction")
    # No uofa.toml above the working directory, and nothing written into the repo.
    monkeypatch.chdir(tmp_path)
    return log


def _run(*flags, pack):
    parser = argparse.ArgumentParser()
    extract_cmd.add_arguments(parser)
    args = parser.parse_args([str(CORPUS), *flags])
    args.pack = [pack]
    args.active_packs = [pack]
    try:
        return extract_cmd.run(args)
    except _Reached:
        return None


def test_the_split_is_what_the_packs_declare():
    """Pinned, so a pack gaining a prompt and a template is a visible change."""
    assert FILLABLE == ["nasa-7009b", "vv40"]
    assert {"iso42001", "surrogate", "disposition", "model-credibility",
            "core"} <= set(UNFILLABLE)


# ── the refusal ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("pack", UNFILLABLE)
def test_a_pack_it_cannot_fill_exits_2_before_anything_runs(pack, reached, capsys):
    """No `--model`, so the default local model would demand `uofa setup`.
    The pack is the more basic fact, and it is the one reported."""
    assert _run(pack=pack) == 2
    assert reached == [], f"a refused run still reached: {reached}"
    assert f"'{pack}'" in capsys.readouterr().err


@pytest.mark.parametrize("pack", UNFILLABLE)
def test_a_remote_model_is_refused_the_same_way(pack, reached):
    """A cloud model skips the setup check, so it gets closest to a paid call."""
    assert _run("--model", "anthropic/claude-x", pack=pack) == 2
    assert reached == []


def test_a_pack_that_does_not_exist_is_refused(reached, capsys):
    assert _run("--model", "mock", pack="nope") == 2
    assert reached == []
    err = capsys.readouterr().err
    assert "'nope'" in err and "not found" in err


def test_the_refusal_says_which_half_is_missing(reached, capsys):
    _run(pack="iso42001")
    err = capsys.readouterr().err
    assert "no extract prompt" in err and "no workbook template" in err

    _run(pack="model-credibility")
    err = capsys.readouterr().err
    assert "no workbook template" in err
    assert "no extract prompt" not in err, "model-credibility names its prompt"


def test_a_named_file_that_is_missing_is_named(reached, capsys):
    """`core` names prompts/extract_prompt.txt, and there is no such file."""
    _run(pack="core")
    err = capsys.readouterr().err
    assert "prompts/extract_prompt.txt" in err and "does not exist" in err


def test_the_refusal_names_the_packs_that_can_be_extracted(reached, capsys):
    _run(pack="iso42001")
    out = capsys.readouterr().out
    assert all(p in out for p in FILLABLE), out


# ── keyless ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("pack", KEYLESS_REFUSED)
def test_keyless_refuses_a_pack_outside_its_two_factor_sets(pack, reached, capsys):
    assert _run("--keyless", pack=pack) == 2
    assert reached == []
    err = capsys.readouterr().err
    assert f"'{pack}'" in err and "--keyless" in err


def test_the_keyless_extractor_itself_refuses_a_foreign_pack():
    """Held in the library too, so a caller that skips the CLI cannot get a
    V&V 40 result back for a pack it never described."""
    empty = SimpleNamespace(chunks=[], file_manifest=[], total_tokens=0)
    with pytest.raises(ValueError, match="iso42001"):
        keyless_extractor.extract(empty, "iso42001")


# ── the gate lets the right packs through ────────────────────────────────────

@pytest.mark.parametrize("pack", FILLABLE)
def test_a_pack_it_can_fill_goes_on_to_read_the_files(pack, reached):
    assert _run("--model", "mock", pack=pack) is None
    assert reached == ["file discovery"]


@pytest.mark.parametrize("pack", ["vv40", "nasa-7009b"])
def test_keyless_goes_on_for_its_two_factor_sets(pack, reached):
    assert _run("--keyless", pack=pack) is None
    assert reached == ["file discovery"]


# ── through the real entry point ─────────────────────────────────────────────

@pytest.mark.parametrize("flags", [["--model", "mock"], ["--keyless"]],
                         ids=["model", "keyless"])
def test_the_command_exits_2_and_writes_nothing(flags, tmp_path):
    out = tmp_path / "x.xlsx"
    run = subprocess.run(
        [sys.executable, "-m", "uofa_cli", "extract", str(CORPUS),
         "--pack", "iso42001", *flags, "-o", str(out)],
        capture_output=True, text=True, cwd=tmp_path,
    )
    assert run.returncode == 2, run.stdout + run.stderr
    assert not out.exists()
    assert "Discovering files" not in run.stdout
