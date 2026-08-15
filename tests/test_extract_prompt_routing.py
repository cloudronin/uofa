"""`uofa extract --pack X` must send the model pack X's prompt.

Found while triaging the nasa-7009b COU2 regression (factor F1 0.593, gate
FAIL). `paths.extract_prompt()` had no `pack_name` parameter, so it resolved
through `pack_dir()` with its `active=["vv40"]` default and returned the V&V 40
prompt for every pack. `extract_cmd` called it with no pack and passed the
result straight to `build_prompt`.

So a NASA extraction asked the model to fill in 13 V&V 40 factors. The model
did exactly that -- and also reported `standards_reference: ASME-VV40-2018` for
a NASA-STD-7009B assessment, which is the same bug seen from the other end.

Nothing downstream caught it. `_json_to_result` picks NASA_ALL_FACTOR_NAMES
from the `pack_name` it *was* given, and the workbook writer pre-fills all 19
rows from the pack, so the artifact looked like a NASA extraction in which the
model had declined to fill six factors. Measured: 13 of 19 factors in 27 of 27
NASA extractions, and per-factor F1 exactly 0.000 for those six on both the dev
and held-out test splits, against exactly 1.000 for all thirteen V&V 40 factors.

A prompt-text test could not have caught this: the NASA prompt was correct and
complete the whole time, and named all six factors. What was wrong was that it
was never sent. These tests check delivery, not content --
test_extract_prompt_absence_rule.py checks content.

See studies/nasa-prompt-routing/FINDINGS.md.
"""

from __future__ import annotations

import inspect

import pytest

from uofa_cli import excel_constants, paths
from uofa_cli.commands import extract_cmd

# Packs whose extract prompt is a distinct file with a distinct factor list.
PACKS = ["vv40", "nasa-7009b"]

NASA_ONLY_FACTORS = [
    f for f in excel_constants.NASA_ALL_FACTOR_NAMES
    if f not in excel_constants.VV40_FACTOR_NAMES
]


@pytest.mark.parametrize("pack", PACKS)
def test_prompt_resolves_inside_the_requested_pack(pack):
    resolved = paths.extract_prompt(pack)
    assert resolved.parent.parent.name == pack, (
        f"extract_prompt({pack!r}) resolved to {resolved}, which is not in "
        f"packs/{pack}/. A pack-blind resolver returns the active-pack default "
        f"for every pack, which is how NASA extractions were run on the V&V 40 "
        f"prompt."
    )
    assert resolved.is_file(), f"{resolved} does not exist"


def test_nasa_prompt_names_every_nasa_only_factor():
    """The delivered prompt must define the six factors the pack scores.

    Six missing factor definitions do not surface as an error anywhere: the
    model returns the thirteen it was given, the workbook still shows nineteen
    rows, and the six blanks read as the model's judgment rather than as a
    question never asked.
    """
    body = paths.extract_prompt("nasa-7009b").read_text(encoding="utf-8")
    missing = [f for f in NASA_ONLY_FACTORS if f.lower() not in body.lower()]
    assert not missing, (
        f"The prompt delivered for pack nasa-7009b does not define "
        f"{len(missing)} of its own factors: {missing}. Extractions will be "
        f"missing exactly these, silently."
    )


def test_vv40_prompt_does_not_carry_the_nasa_factors():
    """The converse, so the test above cannot be satisfied by one merged prompt.

    Without this, resolving every pack to a single 19-factor prompt would pass
    the NASA check while asking V&V 40 users about factors their pack does not
    have.
    """
    body = paths.extract_prompt("vv40").read_text(encoding="utf-8")
    leaked = [f for f in NASA_ONLY_FACTORS if f.lower() in body.lower()]
    assert not leaked, (
        f"The V&V 40 prompt defines NASA-only factors {leaked}. A V&V 40 "
        f"extraction would then emit factors the pack cannot score."
    )


def test_extract_prompt_accepts_a_pack_name():
    """Guard the signature itself.

    The defect was an absent parameter, not a wrong argument. A caller passing
    the pack correctly is no protection if the callee cannot receive it, and
    that is exactly the state this repo shipped in.
    """
    params = inspect.signature(paths.extract_prompt).parameters
    assert "pack_name" in params, (
        "paths.extract_prompt lost its pack_name parameter. Every caller then "
        "silently gets the active-pack default."
    )
    assert list(params)[0] == "pack_name", (
        "pack_name must stay first, matching pack_dir/pack_manifest, so a "
        "positional call resolves the pack rather than the repo root."
    )


def test_the_extract_command_passes_its_pack_through():
    """The wiring, not just the helper.

    `paths.extract_prompt` can take a pack and still be called without one --
    which is the bug as it actually shipped. Read the call site.
    """
    source = inspect.getsource(extract_cmd)
    assert "paths.extract_prompt(pack_name)" in source, (
        "extract_cmd no longer passes pack_name to paths.extract_prompt. "
        "The model will be sent the active pack's prompt regardless of --pack."
    )
