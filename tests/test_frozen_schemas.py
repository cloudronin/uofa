"""A frozen schema must be honest about which URL it is.

`spec/schemas/vX.Y.json` files are cut by `uofa schema --freeze vX.Y` and
published at `https://uofa.net/schemas/vX.Y.json` for adopters to pin. Unlike
`uofa.schema.json` they are never regenerated, so nothing downstream would
notice if one were wrong.

The realistic mistake is a frozen file produced by copying rather than by
`--freeze` — it would carry the unversioned `$id` while sitting at a versioned
URL, so a consumer resolving `$id` would silently be sent to the moving alias,
which is the exact thing pinning was meant to avoid. That is cheap to catch and
invisible otherwise, so it is checked here and again in the site build before
anything reaches the internet.

What this deliberately does NOT check is that a frozen file still matches the
current shapes. Divergence is the point: v0.5 records what the shapes said when
it was cut. Pinning regeneration here would turn frozen versions back into
moving ones.
"""

from __future__ import annotations

import json
import re

import pytest

from uofa_cli import paths

SCHEMAS = paths.find_repo_root() / "spec" / "schemas"
FROZEN_RE = re.compile(r"^v\d+\.\d+\.json$")


def _frozen_files():
    return sorted(p for p in SCHEMAS.glob("v*.json") if FROZEN_RE.match(p.name))


def test_at_least_one_frozen_version_exists():
    """Guards the guard: a glob that silently matches nothing passes everything."""
    assert _frozen_files(), (
        f"no frozen schema versions found in {SCHEMAS}. Cut one with "
        f"`uofa schema --freeze v0.5`, or this file's other tests are vacuous."
    )


@pytest.mark.parametrize("path", _frozen_files(), ids=lambda p: p.name)
def test_frozen_id_matches_its_own_url(path):
    schema = json.loads(path.read_text(encoding="utf-8"))
    expected = f"https://uofa.net/schemas/{path.name}"
    assert schema.get("$id") == expected, (
        f"{path.name} declares $id {schema.get('$id')!r} but publishes at {expected}. "
        f"A frozen version whose $id points elsewhere sends anyone resolving it to a "
        f"different document. Cut frozen versions with `uofa schema --freeze`, which "
        f"sets $id, rather than copying uofa.schema.json by hand."
    )


@pytest.mark.parametrize("path", _frozen_files(), ids=lambda p: p.name)
def test_frozen_schema_is_structurally_a_uofa_schema(path):
    """A truncated or half-written freeze should fail loudly, not serve 200 OK."""
    schema = json.loads(path.read_text(encoding="utf-8"))
    assert schema.get("$schema", "").startswith("https://json-schema.org/"), (
        f"{path.name} has no JSON Schema dialect declared"
    )
    titles = [branch.get("title") for branch in schema.get("oneOf", [])]
    assert titles == ["Minimal Profile", "Complete Profile"], (
        f"{path.name} has profile branches {titles}, expected the two UofA profiles"
    )
