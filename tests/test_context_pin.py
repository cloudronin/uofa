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
#:
#: v0.8 -> v0.9 was taken 2026-08-28 by the same route, and for a reason the
#: file above could not fix: `not-recoverable` is a v0.9 term, and the closed
#: set enumerating provenance tokens is a SHAPE. Widening v0.8's list would
#: have made v0.8 packages start accepting a term v0.8 has no way to mean --
#: the identical silent-redefinition this module exists to prevent, one layer
#: up from the bytes. v0.8.jsonld is untouched and still pinned.
#: **v0.1-v0.4, v0.6 and v0.7 were added to this table on 2026-09-14**, when
#: `test_every_context_file_on_disk_is_pinned` was written and found them
#: sitting in `spec/context/` guarded by nothing. Pinning them today freezes
#: them FROM today; it does not certify that they are what they were, because no
#: record of that survives to check against. That is still the whole value on
#: offer -- an unpinned file can be edited with nothing noticing, and these six
#: now cannot.
#:
#: v0.9 -> v0.10 was taken 2026-09-14 by the same route, for the attribution
#: attestations: 29 terms ADDED, 0 terms changed meaning, v0.9.jsonld untouched.
#:
#: **It is pinned here before any package names it as `@context`**, which is a
#: departure from the three above and is deliberate. An attestation carries
#: `contextVersion` INSIDE the bytes the attestation authority signs -- the
#: signed statement says "read my terms against v0.10" and nothing fetches
#: anything to check that. So the meaning of an already-signed attestation
#: depends on these bytes exactly as a package's hash depends on the bytes of
#: the context it names, and an edit here would silently re-mean statements
#: already made. Waiting for the first `@context: v0.10` package would leave
#: that window open for the whole of the Credenza integration.
PINNED_CONTEXT_SHA256S = {
    "v0.1.jsonld": "36bedb55490f5b81714b21114e478df33e0c44112808f21c5605cd70ec7a65af",
    "v0.2.jsonld": "8c2b2bc503314d6a59d85603e75ed8140f4d7e8a2017375f82522c2e21dbab56",
    "v0.3.jsonld": "81fa41b60a7af7ef95070dfbabeb37207899a42345a886775e38b8eac26564df",
    "v0.4.jsonld": "83c549ef1a96df18a2adf226335464b6e5fc5495b5f9a0322589baf2cfeb1410",
    "v0.5.jsonld": "e62e1e236088502e6f7179b1e0e60bc35164ba5bffc6927658b1352bb61b1872",
    "v0.6.jsonld": "8e8a53739c6a459354c31e18bff2299df5031e244a02f3995e040e76776b329f",
    "v0.7.jsonld": "034b90270d15dc1ec3631a2139b7a9ddbcdcc8704fc0e3b58435621677ad30b3",
    "v0.8.jsonld": "59029321aeb887e5ce527e6f3e97414e08c0f38bd68d02ada8a059ac5e7c5c12",
    "v0.9.jsonld": "fb13c9a913f2e77d965e172b55c91fc38989d1255cd2e99beb449e284cdf2615",
    "v0.10.jsonld": "27e557a10d291453fafd5aa0262450cc4d589ccf96aa5f12731a54dc16d77112",
}

#: What a package declaring nothing is signed against. Every entry above is
#: still guarded, and the emitter may write any of them -- see the test below,
#: which checks the whole table rather than this one name.
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


def test_every_context_the_emitter_can_write_is_pinned():
    """The one name above stopped being the whole answer.

    The emitter declares the version the WORKBOOK declares, so which context a
    package is signed against is now a function of its source. Guarding only the
    default would leave every other reachable version unpinned -- editable with
    nothing noticing, which is the single failure this module exists to prevent.
    """
    from uofa_cli.excel_constants import CONTEXT_URLS

    unpinned = sorted(url.rsplit("/", 1)[-1] for url in CONTEXT_URLS.values()
                      if url.rsplit("/", 1)[-1] not in PINNED_CONTEXT_SHA256S)
    assert not unpinned, (
        f"the emitter can write {unpinned}, which this module does not guard."
        + _UNPIN_HINT
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


def test_every_context_file_on_disk_is_pinned():
    """The gap the table above could not see: it guards the files it LISTS.

    A new `spec/context/vX.Y.jsonld` added and not listed here is unguarded --
    editable with nothing noticing -- and every test in this module passes,
    because each one starts from the table. That is how v0.10 was first added:
    written, shipped in the same change as the attestations whose signed
    payloads name it, and pinned nowhere.

    Nothing has to REFERENCE a context for its bytes to be load-bearing. This
    asks the directory instead of the table, so the omission cannot recur.
    """
    from uofa_cli import paths

    directory = paths.find_repo_root() / "spec" / "context"
    on_disk = sorted(p.name for p in directory.glob("v*.jsonld"))
    unpinned = [n for n in on_disk if n not in PINNED_CONTEXT_SHA256S]
    assert on_disk, f"no context files found in {directory}; this test is vacuous"
    assert not unpinned, (
        f"{unpinned} sit in spec/context/ with no digest pinned here, so they "
        f"can be edited and nothing will notice." + _UNPIN_HINT
    )


def test_v0_10_sorts_after_v0_9_everywhere_a_version_is_ordered():
    """**v0.10 is the first context whose minor version has two digits.**

    Under a string sort "v0.10" < "v0.9", so every "pick the newest context"
    site in this codebase silently starts picking v0.9 the moment v0.10 lands --
    and the symptom is not an error. `resolve_context` falls back to the latest
    context for any package whose declared one is unresolvable, and the note it
    prints would name v0.9 while looking entirely correct. The 32 shipped
    examples declare v0.5 and take that path on every run.

    Both orderings are numeric today. This asserts it against the real
    directory, because the bug is a one-character difference in a sort key and
    no other test in this file would notice.
    """
    from uofa_cli import paths
    from uofa_cli.vocab import _version_key

    assert paths.latest_context_file().name == "v0.10.jsonld", (
        f"latest_context_file() picked {paths.latest_context_file().name}; "
        f"a string sort puts v0.9 after v0.10")
    assert paths._context_version("v0.10.jsonld") > paths._context_version("v0.9.jsonld")
    assert _version_key("v0.10") > _version_key("v0.9")
    # And the ordering used to build the published vocabulary pages, which
    # decides which version each term is reported as introduced in.
    names = sorted(PINNED_CONTEXT_SHA256S, key=lambda n: _version_key(n[:-7]))
    assert names[-1] == "v0.10.jsonld", names
