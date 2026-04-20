"""Tests for the adversarialProvenance block hash (§8.1)."""

from __future__ import annotations

from uofa_cli.adversarial.hash_utils import (
    HASH_FIELD,
    compute_provenance_block_hash,
    verify_provenance_block_hash,
)


def _sample_block() -> dict:
    return {
        "generatorVersion": "0.1.0",
        "promptTemplateId": "d3_undercutting_inference.W_AR_05",
        "specId": "adv-2026-001-w-ar-05",
        "generationModel": "claude-opus-4-7",
        "modelParams": {"temperature": 0.7, "seed": 20260419, "max_tokens": 4000},
        "generationTimestamp": "2026-04-19T14:23:01Z",
        "targetWeakener": "W-AR-05",
    }


def test_hash_is_deterministic():
    block = _sample_block()
    h1 = compute_provenance_block_hash(block)
    h2 = compute_provenance_block_hash(block)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_hash_excludes_own_field():
    """Changing provenanceBlockHash itself must not change the computed hash."""
    block = _sample_block()
    base = compute_provenance_block_hash(block)
    block[HASH_FIELD] = "sha256:deadbeef"
    after = compute_provenance_block_hash(block)
    assert base == after


def test_verify_detects_tampering():
    block = _sample_block()
    block[HASH_FIELD] = f"sha256:{compute_provenance_block_hash(block)}"
    ok, stored, recomputed = verify_provenance_block_hash(block)
    assert ok
    assert stored == recomputed

    # Tamper with a non-hash field.
    block["targetWeakener"] = "W-AR-01"
    ok2, stored2, recomputed2 = verify_provenance_block_hash(block)
    assert not ok2
    assert stored2 != recomputed2


def test_verify_missing_hash_field():
    block = _sample_block()
    ok, stored, recomputed = verify_provenance_block_hash(block)
    assert not ok
    assert stored == ""
    assert len(recomputed) == 64


def test_hash_stable_across_key_reordering():
    block_a = {"b": 2, "a": 1, "c": 3}
    block_b = {"a": 1, "c": 3, "b": 2}
    assert compute_provenance_block_hash(block_a) == compute_provenance_block_hash(block_b)


def test_hash_changes_when_call_metadata_changes():
    """v1.2 callMetadata is nested inside the block; any change must flip the hash."""
    base = _sample_block()
    base["callMetadata"] = {
        "dropParamsActive": True,
        "deprecationFallbackFired": False,
        "shaclRetries": 0,
        "modelRequested": "claude-opus-4-7",
        "modelReturned": "claude-opus-4-7",
        "litellmVersion": "1.34.5",
    }
    h_before = compute_provenance_block_hash(base)

    mutated = {**base, "callMetadata": {**base["callMetadata"], "deprecationFallbackFired": True}}
    h_after = compute_provenance_block_hash(mutated)

    assert h_before != h_after, "hash must change when callMetadata changes"
