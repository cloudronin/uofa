"""SHA-256 hash for the adversarialProvenance block (v1.1 §8.1).

The hash covers the block contents with sorted keys, excluding the
``provenanceBlockHash`` field itself. This lets ``uofa verify`` detect
tampering with the synthetic-marker state without requiring separate
signing infrastructure.
"""

from __future__ import annotations

import hashlib
import json

PROVENANCE_BLOCK_KEY = "adversarialProvenance"
HASH_FIELD = "provenanceBlockHash"


def compute_provenance_block_hash(block: dict) -> str:
    """Return the hex SHA-256 digest of *block* minus the hash field.

    The caller is responsible for prepending any ``sha256:`` prefix.
    """
    stripped = {k: v for k, v in block.items() if k != HASH_FIELD}
    canonical = json.dumps(stripped, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_provenance_block_hash(block: dict) -> tuple[bool, str, str]:
    """Recompute the block hash and compare it to the stored value.

    Returns (ok, stored_hex, recomputed_hex). *stored_hex* has any
    ``sha256:`` prefix stripped. *ok* is False if the field is missing.
    """
    stored_raw = block.get(HASH_FIELD, "")
    stored_hex = stored_raw.split(":", 1)[1] if ":" in stored_raw else stored_raw
    recomputed = compute_provenance_block_hash(block)
    return stored_hex == recomputed, stored_hex, recomputed
