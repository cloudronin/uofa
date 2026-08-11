"""The derived JSON Schema must be exactly what the generator produces.

AGENTS.md §4 tells contributors not to hand-edit derived artifacts and to
regenerate them instead. That instruction is only safe if regenerating is a
no-op — and for a while it was not:

`_run_json` read `paths.shacl_schema()` (core shapes only) while the committed
`spec/schemas/uofa.schema.json` had been generated with vv40 active. Following
the documented instruction therefore *deleted* the `hasContextOfUse` definition
and downgraded the `deviceClass` enum to a bare string. Nothing failed; the
artifact just quietly lost constraints, which is the §13 shape where the
instrument reports success.

The reverse drift was live too, and mattered more. Core deliberately stopped
requiring `hasContextOfUse` at the Minimal profile on 2026-08-08, because
requiring it meant NASA-7009A packages could only validate by inventing the
field — and two of them "validated on a context of use a model had made up."
That fix never reached the derived schema, so anyone validating against the
shipped JSON Schema was still being pushed to fabricate exactly that field. A
result that does not propagate to the artifacts restating it is not retired.

So: regeneration is pinned as a no-op, in both directions.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from uofa_cli import paths

REPO = paths.find_repo_root()
COMMITTED = REPO / "spec" / "schemas" / "uofa.schema.json"


def _profile(schema: dict, title: str) -> dict:
    """The body sub-schema for a named profile branch.

    `title` sits on the oneOf branch; the properties/required live in its
    second allOf member. Resolved through a helper so a structural change
    fails loudly here instead of making every lookup silently return nothing.
    """
    for branch in schema["oneOf"]:
        if branch.get("title") == title:
            return branch["allOf"][1]
    raise AssertionError(
        f"no {title!r} branch in the schema; branches are "
        f"{[b.get('title') for b in schema['oneOf']]}")


def _regenerate(tmp_path: Path) -> dict:
    out = tmp_path / "regen.schema.json"
    proc = subprocess.run(
        [sys.executable, "-m", "uofa_cli.cli", "schema", "--emit", "json", "-o", str(out)],
        cwd=REPO, capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"schema generation failed:\n{proc.stdout}\n{proc.stderr}"
    return json.loads(out.read_text())


def test_regenerating_the_schema_is_a_no_op(tmp_path):
    """`uofa schema --emit json` with default packs must reproduce the artifact."""
    regenerated = _regenerate(tmp_path)
    committed = json.loads(COMMITTED.read_text())
    assert regenerated == committed, (
        "spec/schemas/uofa.schema.json is not what the generator produces. Either "
        "the shapes changed and the artifact was not regenerated (run `uofa schema "
        "--emit json -o spec/schemas/uofa.schema.json`), or the artifact was "
        "hand-edited, or the generator resolves a different set of shape files "
        "than the one that produced the committed copy."
    )


def test_generator_reads_pack_shapes_not_only_core(tmp_path):
    """Pack shapes RDF-merge onto the core body shapes; core alone loses them.

    Pinned by content rather than by inspecting the call, so it still fails if
    someone reintroduces a core-only read by another route.
    """
    schema = _regenerate(tmp_path)
    complete = _profile(schema, "Complete Profile")

    assert "hasContextOfUse" in complete["properties"], (
        "hasContextOfUse is gone from the Complete profile — the generator is "
        "reading core shapes only again (vv40_shapes.ttl contributes it)"
    )
    device = complete["properties"].get("deviceClass", {})
    assert "N/A" in device.get("enum", []), (
        "deviceClass lost its vv40 enum — 'N/A' exists so a non-regulated context "
        "of use does not have to claim a device class it does not have"
    )


def test_minimal_profile_does_not_require_a_context_of_use():
    """The 2026-08-08 decision must hold in the derived artifact, not just the SHACL.

    Requiring it at Minimal is what made NASA-7009A packages validate on a
    fabricated context of use. A schema that still requires it re-creates the
    incentive in every editor that consumes the schema.
    """
    committed = json.loads(COMMITTED.read_text())
    minimal = _profile(committed, "Minimal Profile")
    assert "hasContextOfUse" not in minimal.get("required", []), (
        "the Minimal profile requires hasContextOfUse; core dropped that "
        "requirement deliberately so 7009A documents need not invent the field"
    )
