"""Stable JSON serializer for derivation pre-pass results.

Mirrors `uofa_cli.oos.snapshot` design: serialize the DerivationResult
into a deterministic JSON structure suitable for inclusion in unified
check reports. Key load-bearing rule: when derivations are disabled, the
caller passes None and the field is OMITTED entirely from the output
JSON (not serialized as null) — this preserves byte-identical
backward-compatible reports for packs that don't declare derivations.
"""

from __future__ import annotations

from typing import Any

from uofa_cli.derivations.runner import DerivationResult


def to_stable_dict(result: DerivationResult | None) -> dict[str, Any] | None:
    """Convert a DerivationResult into a stable, JSON-serializable dict.

    Returns None when result is None (derivations disabled). Caller MUST
    omit the field entirely when this returns None — never include a
    `derivations: null` key (load-bearing for byte-identical reports).
    """
    if result is None:
        return None

    return {
        "enabled": True,
        "provenance": result.provenance,
        "construct_count": result.construct_count,
        "derived_triple_count": result.derived_triple_count,
        "elapsed_seconds": round(result.elapsed_seconds, 3),
    }
