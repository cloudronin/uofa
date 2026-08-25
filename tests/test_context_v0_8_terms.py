"""A package declaring v0.8 carries v0.8's terms.

`CONTEXT_URL` sat at v0.5 while the repository shipped v0.7, so every emitted
package declared a context two versions behind what it was written against -- a
declaration stating something the artifact did not do. The bump and the emission
land together for exactly that reason, and this is the fixture that keeps them
together: a package declaring v0.8 while emitting v0.7 terms would be the same
defect reborn for the width of one commit.
"""

from __future__ import annotations

import json
from pathlib import Path

from uofa_cli.excel_constants import (CONTEXT_URL, JUDGMENT_TOKENS,
                                      LEVEL_TOKENS)

SPEC = Path(__file__).resolve().parents[1] / "spec" / "context"

V0_8_TERMS = ("requiredLevelProvenance", "LevelAffirmation",
              "hasLevelAffirmation", "affirmedAt")


def _ctx(version: str) -> dict:
    return json.loads((SPEC / f"{version}.jsonld").read_text())["@context"]


def test_the_declared_context_exists_and_defines_what_the_emitter_uses():
    """The declaration and the artifact, checked against each other."""
    declared = CONTEXT_URL.rsplit("/", 1)[-1].removesuffix(".jsonld")
    path = SPEC / f"{declared}.jsonld"
    assert path.exists(), (
        f"packages declare {declared!r} and no such context ships in this "
        f"repository -- the declaration names a file that does not exist")
    ctx = _ctx(declared)
    missing = [t for t in V0_8_TERMS if t not in ctx]
    assert not missing, (
        f"packages declare {declared!r}, the emitter writes {V0_8_TERMS}, and "
        f"that context defines none of {missing}")


def test_v0_8_is_additive_over_v0_7():
    """No existing term changes meaning -- unlike v0.5 -> v0.7, which removed
    fourteen. That asymmetry is why the bump needed checking rather than
    assuming."""
    v7, v8 = _ctx("v0.7"), _ctx("v0.8")
    assert not (set(v7) - set(v8)), (
        f"v0.8 removed terms v0.7 defined: {sorted(set(v7) - set(v8))}")
    changed = [k for k, v in v7.items() if v8.get(k) != v]
    assert not changed, f"v0.8 changed the meaning of {changed}"
    assert set(v8) - set(v7) == set(V0_8_TERMS)


def test_confirmed_is_not_in_the_package_vocabulary():
    """The whole point. `confirmed` is the encoding tool's LOCATION act --
    anchoring produces it -- and exporting it as a judgment claim is the
    ambiguity this version exists to kill."""
    assert "confirmed" not in LEVEL_TOKENS
    assert "confirmed" not in JUDGMENT_TOKENS


def test_every_judgment_token_is_in_the_vocabulary():
    """A token that claims a judgment but cannot be written is a rule about an
    empty set."""
    assert JUDGMENT_TOKENS <= set(LEVEL_TOKENS)
