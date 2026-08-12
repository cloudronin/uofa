"""The gated keyless route's BEHAVIOUR is immutable.

A route version is frozen once it has been through the holdout gate: the
qualification row asserts measured properties, and changing the code would
silently change what that row means.

**Why a token stream and not `ast.dump`.** The first version of this guard
hashed `ast.dump()`, which passed locally and FAILED IN CI — that output is
Python-version-dependent, so the pin only reproduced on the interpreter that
computed it. A freeze that fires on a different Python is a freeze that gets
disabled. Token types and strings are language-level and stable across releases.

Comments and docstrings are excluded so prose may improve; logic may not move.

If this fails, the route's behaviour changed. That is not a bug to patch here:
it means a new route version exists, and it qualifies against a NEW holdout draw
-- never against rows 2, 29 or 41, which caught v1's published defects.
"""

from __future__ import annotations

import hashlib
import io
import tokenize
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
ROUTE = _REPO / "studies/taxonomy-validation/enrichment/keyless_route.py"

# Pinned at the gate, 2026-08-12: false-fire 2/27 (7.4%), false-clear 1/33 (3.0%)
# on 60 unseen author-labeled cards.
GATED_BEHAVIOUR_SHA = "cb6bf5291ccb542b"

_SKIP = (tokenize.COMMENT, tokenize.NL, tokenize.ENCODING)
_PRE_DOCSTRING = (None, tokenize.INDENT, tokenize.NEWLINE, tokenize.DEDENT)


def _behaviour_sha(path: Path) -> str:
    src = path.read_text(encoding="utf-8")
    out: list[tuple[str, str]] = []
    prev: int | None = None
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type in _SKIP:
            continue
        if tok.type == tokenize.STRING and prev in _PRE_DOCSTRING:
            prev = tok.type                      # a docstring; not behaviour
            continue
        # tok_name, not the integer: token type NUMBERS can shift when a
        # release adds a type, and that would fire the freeze on a Python
        # upgrade -- the same class of defect as the ast.dump version this
        # replaces, just rarer.
        out.append((tokenize.tok_name[tok.type], tok.string))
        prev = tok.type
    return hashlib.sha256(repr(out).encode()).hexdigest()[:16]


def test_gated_route_behaviour_has_not_changed():
    assert _behaviour_sha(ROUTE) == GATED_BEHAVIOUR_SHA, (
        "the gated keyless route's logic changed. Its qualification row reports "
        "measurements of the OLD logic. Create route v2 and gate it against a "
        "fresh holdout draw; do not edit v1 and reuse its row.")


def test_docstrings_may_still_be_edited():
    """The freeze must not fire on prose, or it gets disabled the first time
    someone improves a comment."""
    original = ROUTE.read_text(encoding="utf-8")
    before = _behaviour_sha(ROUTE)
    try:
        ROUTE.write_text(original.replace(
            '"""The keyless table route for P2 uncertainty',
            '"""EDITED PROSE. The keyless table route for P2 uncertainty', 1),
            encoding="utf-8")
        assert _behaviour_sha(ROUTE) == before, (
            "a docstring edit moved the behaviour hash -- the freeze would fire "
            "on documentation and would be disabled within a week")
    finally:
        ROUTE.write_text(original, encoding="utf-8")


def test_a_logic_change_is_caught():
    """The guard must fail on the exact repair the ruling forbids: relaxing the
    SE header match to fix the row-2 false-clear."""
    original = ROUTE.read_text(encoding="utf-8")
    try:
        ROUTE.write_text(
            original.replace(r"std(?:ev)?|se|95%", r"std(?:ev)?|95%"),
            encoding="utf-8")
        assert _behaviour_sha(ROUTE) != GATED_BEHAVIOUR_SHA, (
            "the freeze did not notice a HEADER pattern change -- it is not "
            "guarding behaviour")
    finally:
        ROUTE.write_text(original, encoding="utf-8")
