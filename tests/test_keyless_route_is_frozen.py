"""The gated keyless route's BEHAVIOUR is immutable.

A route version is frozen once it has been through the holdout gate: the
qualification row asserts measured properties, and changing the code would
silently change what that row means.

Hashing the file would make the freeze unusable -- a typo fix or a clearer
docstring would trip it, and a guard that fires on documentation gets disabled.
So this pins the **executable structure** with docstrings stripped. Comments and
prose may improve; logic may not move.

If this fails, the route's behaviour changed. That is not a bug to patch here:
it means a new route version exists, and it qualifies against a NEW holdout draw
-- never against rows 2, 29 or 41, which caught v1's published defects.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
ROUTE = _REPO / "studies/taxonomy-validation/enrichment/keyless_route.py"

# Pinned at the gate, 2026-08-12: false-fire 2/27 (7.4%), false-clear 1/33 (3.0%)
# on 60 unseen author-labeled cards.
GATED_BEHAVIOUR_SHA = "5820ec5b19cd1a1a"


def _behaviour_sha(path: Path) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]
    return hashlib.sha256(
        ast.dump(ast.fix_missing_locations(tree)).encode()).hexdigest()[:16]


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
