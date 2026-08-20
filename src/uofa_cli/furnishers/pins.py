"""Source pins: what was read, and what was measured.

Addendum v0.2 A9.1, as ruled 2026-08-11. Two pin types, never interchangeable,
because they support different claims:

  **artifact pin** -- source URL + content hash. Claims "this exact content was
  read". Supports RE-DERIVATION: re-fetch and get identical bytes, forever.
  Model cards, eval reports, corpus rows.

  **occasion pin** -- subject identifier + version claim + timestamp. Claims
  "this subject was measured at this time". Supports RE-PERFORMANCE, not
  re-derivation: run it again and the result may legitimately differ. Live
  furnisher runs against a hosted endpoint.

A consumer must never read an occasion pin as though re-fetching it would
reproduce the measurement. It will not, and a difference between two
performances is not evidence of tampering.

**Nothing here is declared in `spec/context/v0.5.jsonld`, deliberately.** That
file sets `"@vocab": "https://uofa.net/vocab#"`, so an undeclared term already
expands to `uofa:<term>` and both rdflib and Jena see it. And the context is
INLINED into the document before hashing, so adding a term there invalidates
every signed bundle in the repo -- a one-line addition once put the Morrison
reference example into C1 failure while C2 and C3 stayed green. Vocabulary is
free to add here and expensive to add there (AGENTS.md §13).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

ARTIFACT = "artifact"
OCCASION = "occasion"


def content_hash(text: str | bytes) -> str:
    """sha256 of content, the form both pin types and the gold set already use."""
    raw = text.encode("utf-8") if isinstance(text, str) else text
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def artifact_pin(source_url: str, content: str | bytes, *, fetched_at: str,
                 revision: str = "", revision_kind: str = "") -> dict[str, Any]:
    """A pin that supports re-derivation.

    `revision` should be the hash of the CONTENT THAT WAS READ, not of its
    container. For an HF model card that is the `README.md` blob oid, never the
    repo sha: the repo sha moves when any file changes, so pinning it marks a
    byte-identical card stale on a weights re-upload -- a badge going amber for
    a reason the reader cannot see and the card cannot support.
    """
    return artifact_pin_for_digest(
        source_url, content_hash(content), fetched_at=fetched_at,
        revision=revision, revision_kind=revision_kind,
    )


def artifact_pin_for_digest(source_url: str, digest: str, *, fetched_at: str,
                            revision: str = "",
                            revision_kind: str = "") -> dict[str, Any]:
    """`artifact_pin` for a caller that has already streamed the content.

    Same pin, same claim; the only difference is who computed the digest. A
    405 MB solver archive cannot be handed to `artifact_pin` as bytes, and
    reading it into memory to pin it would defeat the streaming the seal path
    exists to do. `digest` must be in the `sha256:<hex>` form `content_hash`
    returns -- anything else is a caller bug and is rejected here rather than
    written into a package that claims to be re-derivable.
    """
    if not (digest.startswith("sha256:") and len(digest) == 71):
        raise ValueError(
            f"digest must be 'sha256:<64 hex>' as content_hash returns, got {digest!r}")
    pin: dict[str, Any] = {
        "pinType": ARTIFACT,
        "sourceUrl": source_url,
        "contentHash": digest,
        "fetchedAt": fetched_at,
        "supports": "re-derivation",
    }
    if revision:
        pin["revision"] = revision
        pin["revisionKind"] = revision_kind or "unspecified"
    return pin


def occasion_pin(subject_id: str, *, measured_at: str, version_claim: str = "",
                 claimed_by: str = "") -> dict[str, Any]:
    """A pin that supports re-performance only.

    `version_claim` is what the provider ASSERTS, not what the assessor verified.
    A hosted endpoint's identity can change under a stable name with no notice
    and nothing to diff, so this records an assertion and says so. Absent
    `version_claim` is the normal case and is not a defect.
    """
    pin: dict[str, Any] = {
        "pinType": OCCASION,
        "subjectId": subject_id,
        "measuredAt": measured_at,
        "supports": "re-performance",
        "identityAssertedBy": claimed_by or "provider",
        "verifiedByAssessor": False,
    }
    if version_claim:
        pin["versionClaim"] = version_claim
    return pin


def attach(bundle: dict, pin: dict) -> None:
    """Append a pin to the bundle, de-duplicated by its identifying field."""
    pins = list(bundle.get("sourcePin") or [])
    key = "sourceUrl" if pin["pinType"] == ARTIFACT else "subjectId"
    pins = [p for p in pins if not (p.get("pinType") == pin["pinType"]
                                    and p.get(key) == pin.get(key))]
    pins.append(pin)
    bundle["sourcePin"] = pins


def re_derivable(bundle: dict) -> bool:
    """Whether every pin on the bundle supports re-derivation.

    False as soon as one occasion pin is present, which is the honest reading:
    a bundle mixing a pinned card with a live furnisher run is re-derivable in
    part and re-performable in the rest, and the weaker claim governs what the
    card may promise (A6's per-section claim line).
    """
    pins = bundle.get("sourcePin") or []
    return bool(pins) and all(p.get("pinType") == ARTIFACT for p in pins)


def summary(bundle: dict) -> str:
    """One line for the readout. Says which claim each pin supports."""
    pins = bundle.get("sourcePin") or []
    if not pins:
        return "no source pins recorded"
    art = sum(1 for p in pins if p.get("pinType") == ARTIFACT)
    occ = len(pins) - art
    parts = []
    if art:
        parts.append(f"{art} artifact pin{'s' if art != 1 else ''} (re-derivable)")
    if occ:
        parts.append(f"{occ} occasion pin{'s' if occ != 1 else ''} (re-performable only)")
    return "; ".join(parts)
