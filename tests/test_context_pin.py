"""The signing context is pinned, because it *is* the signature.

`integrity.resolve_context` inlines the `@context` into the document before
hashing, so the context file's bytes land inside the hash preimage. Measured on
a minimal three-field document (`@context`, `id`, `type`):

    preimage bytes: 7238   context share: 98.2%

That is the whole point of this module. Over 98% of what every UofA signature
commits to is the contents of `spec/context/v0.5.jsonld`. Editing that file by
one byte silently invalidates every package ever signed against it, and the
only symptom is `uofa verify` printing "Hash match: False" with nothing to say
why.

This is not hypothetical. `tests/test_context_resolution.py` records that a
previous move of the context file broke verification for 5 shipped packages.

These tests convert that silent breakage into a red build.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from uofa_cli import paths
from uofa_cli.excel_mapper import CONTEXT_URL

# The context every shipped signed package resolves to, and its digest.
#
# If you are here because this test failed: you edited spec/context/v0.5.jsonld.
# Do not update this constant to make the test pass. Every package signed
# against the old bytes will stop verifying, including the 32 shipped examples.
# Add a NEW version file (v0.8.jsonld), point CONTEXT_URL at it, and pin that
# instead -- old packages keep resolving to the old file and keep verifying.
#: Every context version this repo has signed against, and the bytes it signed
#: against. **Append-only.** Removing an entry unguards the packages signed
#: under it -- that file can then be edited with nothing noticing, which is the
#: single failure this module exists to prevent.
#:
#: v0.5 -> v0.8 was taken 2026-08-24 by the route the note above prescribes: a
#: NEW file was added and CONTEXT_URL repointed, v0.5.jsonld untouched. Old
#: packages keep naming v0.5, keep resolving to it, and keep verifying.
PINNED_CONTEXT_SHA256S = {
    "v0.5.jsonld": "e62e1e236088502e6f7179b1e0e60bc35164ba5bffc6927658b1352bb61b1872",
    "v0.8.jsonld": "59029321aeb887e5ce527e6f3e97414e08c0f38bd68d02ada8a059ac5e7c5c12",
}

#: What NEW packages are signed against. Every entry above is still guarded.
PINNED_CONTEXT_NAME = "v0.8.jsonld"
PINNED_CONTEXT_SHA256 = PINNED_CONTEXT_SHA256S[PINNED_CONTEXT_NAME]

_UNPIN_HINT = (
    "\n\nEditing this file invalidates EVERY signature issued against it -- "
    "including the shipped examples -- and the failure surfaces only as "
    "'Hash match: False' with no diagnostic.\n"
    "If the change is intentional: add a new spec/context/vX.Y.jsonld, point "
    "excel_mapper.CONTEXT_URL at it, and pin the new file here. Do not edit "
    "a context version that packages are already signed against."
)


def _context_path(name: str) -> Path:
    return paths.find_repo_root() / "spec" / "context" / name


def test_signing_context_digest_is_pinned():
    """The bytes that 98% of every signature commits to have not moved.

    Every pinned version, not only the current one. A new version is a loud,
    deliberate act; an edit to a superseded one is silent and strands packages
    already shipped, which is the direction that actually costs.
    """
    for name, pinned in sorted(PINNED_CONTEXT_SHA256S.items()):
        path = _context_path(name)
        assert path.exists(), f"pinned context is missing: {path}"

        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == pinned, (
            f"spec/context/{name} changed.\n"
            f"  pinned:   {pinned}\n"
            f"  actual:   {actual}" + _UNPIN_HINT
        )


def test_context_url_points_at_the_pinned_version():
    """Bumping CONTEXT_URL without re-pinning would sign against unpinned bytes."""
    assert CONTEXT_URL.endswith(f"/{PINNED_CONTEXT_NAME}"), (
        f"excel_mapper.CONTEXT_URL is {CONTEXT_URL!r}, which does not name the "
        f"pinned context {PINNED_CONTEXT_NAME!r}. New packages would be signed "
        f"against a context this test does not guard." + _UNPIN_HINT
    )


def test_context_is_the_dominant_share_of_the_hash_preimage():
    """Documents the coupling this module exists to guard, and fails loudly if
    resolve_context ever stops inlining -- which would silently re-hash the world."""
    from uofa_cli import integrity

    doc = {"@context": CONTEXT_URL, "id": "urn:uofa:test", "type": "UnitOfAssurance"}
    resolved = integrity.resolve_context(dict(doc), Path("unused.jsonld"), None)
    assert isinstance(resolved.get("@context"), dict), (
        "resolve_context no longer inlines the context. Every existing signature "
        "was computed over the inlined form and will stop verifying."
    )

    with_ctx, _ = integrity.canonicalize_and_hash(integrity.strip_integrity_fields(resolved))
    without_ctx, _ = integrity.canonicalize_and_hash(integrity.strip_integrity_fields(dict(doc)))
    share = (len(with_ctx) - len(without_ctx)) / len(with_ctx)
    assert share > 0.9, (
        f"context is only {share:.1%} of the preimage; this test's premise has "
        f"changed and the pin above may no longer be load-bearing."
    )


def _signed_shipped_packages() -> list[Path]:
    root = paths.find_repo_root()
    candidates = [
        *root.glob("packs/**/*.jsonld"),
        *root.glob("specs/calibration/packages/*.jsonld"),
    ]
    signed = []
    for p in candidates:
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(doc, dict):
            continue
        digest = doc.get("hash") or ""
        # validate --verify uses the same rule: an all-zero hash is a placeholder.
        if digest and not digest.endswith("0" * 64):
            signed.append(p)
    return signed


def test_every_signed_package_resolves_to_a_pinned_context():
    """A signed package referencing an unpinned context is unguarded: that file
    can be edited without any test noticing, and the package stops verifying."""
    packages = _signed_shipped_packages()
    if not packages:
        pytest.skip("no signed packages in this checkout")

    unpinned = []
    for p in packages:
        doc = json.loads(p.read_text(encoding="utf-8"))
        ref = doc.get("@context")
        if not isinstance(ref, str):
            # Two shipped nasa-7009b packages name no context and are signed in
            # exactly that state; resolve_context leaves them alone.
            continue
        # Any PINNED version, not just the current one: a package signed under
        # v0.5 stays guarded by v0.5's digest. Requiring the newest here would
        # demand re-signing the world on every context bump, which is the
        # opposite of what pinning is for.
        if not any(ref.endswith(f"/{n}") for n in PINNED_CONTEXT_SHA256S):
            unpinned.append(f"{p.relative_to(paths.find_repo_root())} -> {ref}")

    assert not unpinned, (
        "signed packages reference a context version that is not pinned here:\n  "
        + "\n  ".join(unpinned)
        + "\nAdd its digest to this module, or re-sign them against the pinned context."
    )
