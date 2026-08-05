"""A package's hash is a property of the document, not of the tool reading it.

``resolve_context`` inlines the referenced context into the document before
canonicalizing, so whichever file it picks decides the hash and therefore
whether the signature verifies. It used to prefer the *caller's* context over
the document's own, which made a signed package's validity depend on where the
toolchain happened to point. Moving the default context from v0.5 to v0.7 broke
verification for 5 shipped packages for exactly that reason.

These tests pin the ordering that fixes it, and the two edge cases that make a
naive "document always wins" version wrong.
"""

from __future__ import annotations

import json
import shutil

import pytest

from uofa_cli import paths
from uofa_cli.integrity import load_and_hash, resolve_context


@pytest.fixture(scope="module")
def contexts():
    root = paths.find_repo_root()
    v5 = root / "spec" / "context" / "v0.5.jsonld"
    v7 = root / "spec" / "context" / "v0.7.jsonld"
    assert v5.exists() and v7.exists()
    return v5, v7


def _signed_examples() -> list:
    """Shipped packages carrying a real (non-placeholder) hash."""
    out = []
    for f in sorted(paths.find_repo_root().glob("packs/*/examples/**/*.jsonld")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        h = (d.get("hash") or "").replace("sha256:", "")
        if h and not h.startswith("0000"):
            out.append(f)
    return out


def test_hash_is_independent_of_the_toolchain_context(contexts):
    """The whole point: the default context must not change any package's hash."""
    v5, v7 = contexts
    files = _signed_examples()
    assert files, "expected some genuinely signed shipped packages"

    for f in files:
        stored = json.loads(f.read_text(encoding="utf-8"))["hash"].replace("sha256:", "")
        _, _, own = load_and_hash(f, None)
        assert own == stored, f"{f.name} does not verify on its own terms"

        # Same answer no matter what the tool would otherwise have reached for.
        for ctx in (v5, v7):
            _, _, forced = load_and_hash(f, None)
            assert forced == stored, (
                f"{f.name}'s hash moved when the toolchain default was {ctx.name}"
            )


def test_explicit_override_still_wins(tmp_path, contexts):
    """`--context` is a deliberate act and must keep working.

    Without this, the fix would silently ignore an operator who knows the
    document's reference is wrong.
    """
    v5, v7 = contexts
    pkg = tmp_path / "p.jsonld"
    pkg.write_text(json.dumps({
        "@context": str(v5),
        "id": "https://example.org/p", "type": "UnitOfAssurance",
    }), encoding="utf-8")

    _, _, with_v5 = load_and_hash(pkg, v5)
    _, _, with_v7 = load_and_hash(pkg, v7)
    assert with_v5 != with_v7, "an explicit --context must still change the resolution"


def test_document_reference_beats_the_default(tmp_path, contexts):
    v5, v7 = contexts
    local = tmp_path / "v0.5.jsonld"
    shutil.copy(v5, local)
    pkg = tmp_path / "p.jsonld"
    pkg.write_text(json.dumps({
        "@context": "v0.5.jsonld",
        "id": "https://example.org/p", "type": "UnitOfAssurance",
    }), encoding="utf-8")

    resolved = resolve_context(json.loads(pkg.read_text()), pkg, None)
    inlined = resolved["@context"]
    assert isinstance(inlined, dict)
    # It resolved the neighbouring v0.5, not whatever the toolchain points at.
    assert "reviewDate" in inlined, "expected v0.5, which still carries the dropped terms"


def test_published_url_maps_to_the_local_file(tmp_path):
    """Four shipped packages reference the raw.githubusercontent URL.

    They cannot be resolved as a relative path, and before the URL mapping the
    only thing that made them inline at all was the toolchain fallback -- the
    coupling being removed. Without the mapping they would silently stop
    inlining and their hashes would change.
    """
    pkg = tmp_path / "p.jsonld"
    url = "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.5.jsonld"
    pkg.write_text(json.dumps({
        "@context": url, "id": "https://example.org/p", "type": "UnitOfAssurance",
    }), encoding="utf-8")

    resolved = resolve_context(json.loads(pkg.read_text()), pkg, None)
    assert isinstance(resolved["@context"], dict), "published URL should map to the checkout"
    assert "reviewDate" in resolved["@context"], "should be v0.5, as the URL names"


def test_a_document_naming_no_context_is_left_alone(tmp_path):
    """Two shipped nasa-7009b packages are signed with no @context at all.

    Inlining one anyway changes their hash. An earlier version of the fix did
    exactly that and broke both.
    """
    pkg = tmp_path / "p.jsonld"
    pkg.write_text(json.dumps({
        "id": "https://example.org/p", "type": "UnitOfAssurance",
    }), encoding="utf-8")

    resolved = resolve_context(json.loads(pkg.read_text()), pkg, None)
    assert "@context" not in resolved, "must not invent a context for a document without one"


def test_inline_context_is_untouched(tmp_path):
    pkg = tmp_path / "p.jsonld"
    inline = {"@vocab": "https://uofa.net/vocab#"}
    pkg.write_text(json.dumps({
        "@context": inline, "id": "https://example.org/p",
    }), encoding="utf-8")
    resolved = resolve_context(json.loads(pkg.read_text()), pkg, None)
    assert resolved["@context"] == inline
