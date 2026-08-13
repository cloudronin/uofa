"""The downloadable pack: shape, contents, honesty, and lifetime.

The done-gate (`uofa verify` passing on a web-produced pack) lives in
`test_pack_cli_roundtrip.py`, which drives the real CLI. These tests cover the
in-process contract: what goes in the zip, what the readout is allowed to claim
about it, and what happens when no signing key is configured.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from space import pipeline, wizard
from uofa_cli import integrity
from uofa_cli.card_bundle import deterministic_import_dict

_CARD = "# A model\n\nTrained on public data. Evaluated on a held-out split.\n"

EXPECTED_MEMBERS = {
    "uofa.jsonld", "report.md", "MANIFEST.json", "keys/demo.pub", "VERIFY.txt",
}


@pytest.fixture
def built_pack(tmp_path, demo_key_env):
    """One signed pack, plus the payload that produced it."""
    data = deterministic_import_dict(_CARD, "model-credibility", "org/m",
                                     "https://huggingface.co/org/m")
    work, out = tmp_path / "work", tmp_path / "out"
    work.mkdir()
    payload = pipeline.finalize_from_data(
        data, "model-credibility", work, source_name="card.md",
        assess_sufficiency=False, pack_out_dir=out)
    return payload, Path(payload["download"]["zip_path"])


# ── shape ────────────────────────────────────────────────────────


def test_finalize_emits_a_signed_pack(built_pack):
    payload, zip_path = built_pack
    assert zip_path.exists()
    assert len(payload["download"]["hash"]) == 64
    assert payload["download"]["filename"].startswith("uofa-pack-model-credibility-")
    assert payload["download"]["filename"].endswith(".zip")


def test_pack_zip_layout_is_exactly_the_five_members(built_pack):
    _, zip_path = built_pack
    with zipfile.ZipFile(zip_path) as zf:
        assert set(zf.namelist()) == EXPECTED_MEMBERS


def test_manifest_digests_match_the_members(built_pack):
    """MANIFEST is what makes report.md non-repudiable: without it the report is
    unsigned text sitting beside a signed graph, swappable by anyone."""
    _, zip_path = built_pack
    with zipfile.ZipFile(zip_path) as zf:
        manifest = json.loads(zf.read("MANIFEST.json"))
        for name, declared in manifest["members"].items():
            import hashlib
            actual = hashlib.sha256(zf.read(name)).hexdigest()
            assert declared == f"sha256:{actual}", f"{name} digest does not match"


def test_manifest_records_the_context_digest(built_pack):
    """The field that turns a future 'Hash match: False' into a diagnosis.

    Over 98% of the signed preimage is the inlined @context, so a verifier whose
    copy differs is by far the likeliest cause of a mismatch."""
    from tests.test_context_pin import PINNED_CONTEXT_SHA256

    _, zip_path = built_pack
    with zipfile.ZipFile(zip_path) as zf:
        manifest = json.loads(zf.read("MANIFEST.json"))
    assert manifest["contextSha256"] == PINNED_CONTEXT_SHA256


def test_manifest_names_the_verifiable_member(built_pack):
    """The zip is packaging; exactly one member carries the signature."""
    _, zip_path = built_pack
    with zipfile.ZipFile(zip_path) as zf:
        manifest = json.loads(zf.read("MANIFEST.json"))
    assert manifest["verifiableMember"] == "uofa.jsonld"
    assert manifest["signedBy"] == "keys/demo.pub"


def test_packed_jsonld_verifies_against_the_packed_key(built_pack, tmp_path):
    _, zip_path = built_pack
    ex = tmp_path / "ex"
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(ex)
    assert integrity.verify_file(ex / "uofa.jsonld", ex / "keys" / "demo.pub") == (True, True)


def test_verify_txt_states_what_a_signature_does_not_mean(built_pack):
    """A green 'signed' badge on a demo package is a stronger claim than the
    evidence supports. The instructions have to say so in words."""
    _, zip_path = built_pack
    with zipfile.ZipFile(zip_path) as zf:
        text = zf.read("VERIFY.txt").decode("utf-8")
    assert "uofa verify uofa.jsonld --pubkey keys/demo.pub" in text
    lowered = text.lower()
    assert "not mean" in lowered
    assert "demonstration" in lowered
    assert "fingerprint" in lowered, "must point at an independent copy of the key"


# ── honesty of the readout ───────────────────────────────────────


def test_signed_readout_reports_the_real_hash_and_a_checked_signature(built_pack):
    payload, _ = built_pack
    auth = payload["context"]["authenticity"]
    assert auth["signed"] is True
    assert auth["integrity_checked"] is True, (
        "the Space must re-verify what it hands out, not merely assert that it signed"
    )
    assert auth["package_hash"] == f"sha256:{payload['download']['hash']}"
    assert "demo" in auth["signer"].lower()


def test_signed_statement_never_reads_as_acceptance(built_pack):
    payload, _ = built_pack
    statement = payload["context"]["authenticity"]["statement"].lower()
    assert "demonstration issuer key" in statement
    for forbidden in ("accepted", "approved", "endorsed", "validated by"):
        assert forbidden not in statement, f"signed statement implies {forbidden!r}"


# ── no key configured ────────────────────────────────────────────


def test_without_a_signing_key_the_run_stays_unsigned(tmp_path):
    """A missing deployment secret degrades to today's behaviour. It must not
    500, and it must not claim a signature it does not have."""
    data = deterministic_import_dict(_CARD, "model-credibility", "org/m",
                                     "https://huggingface.co/org/m")
    work, out = tmp_path / "work", tmp_path / "out"
    work.mkdir()
    payload = pipeline.finalize_from_data(
        data, "model-credibility", work, source_name="card.md",
        assess_sufficiency=False, pack_out_dir=out)

    assert "download" not in payload
    auth = payload["context"]["authenticity"]
    assert auth["signed"] is False
    assert auth["package_hash"] is None
    assert "unsigned demo" in auth["statement"]


def test_signing_key_material_prefers_the_in_memory_pem(monkeypatch, tmp_path):
    """The hosted process serves downloads out of a temp dir; a private key on
    that filesystem is one path bug away from being one of them."""
    key_file = tmp_path / "k.key"
    key_file.write_text("FILE-PEM", encoding="utf-8")
    monkeypatch.setenv(pipeline.SIGNING_KEY_ENV, "ENV-PEM")
    monkeypatch.setenv(pipeline.SIGNING_KEY_FILE_ENV, str(key_file))

    path, pem = pipeline.signing_key_material()
    assert path is None and pem == b"ENV-PEM"


def test_signing_key_material_is_empty_when_unconfigured(monkeypatch):
    monkeypatch.delenv(pipeline.SIGNING_KEY_ENV, raising=False)
    monkeypatch.delenv(pipeline.SIGNING_KEY_FILE_ENV, raising=False)
    assert pipeline.signing_key_material() == (None, None)


# ── lifetime ─────────────────────────────────────────────────────


def test_work_dir_is_torn_down_but_the_pack_survives(tmp_path, demo_key_env, assert_clean_state):
    """The retention split: intermediates and the raw graph still die with the
    request; only the finished zip outlives it."""
    src = tmp_path / "e.txt"
    src.write_text("ASME V&V 40 context of use, model risk.", encoding="utf-8")
    prep = wizard.prepare([src])
    ext = wizard.extract(prep.payload["corpus"], "vv40", model="mock")

    out = wizard.new_pack_dir()
    res = wizard.finalize(ext.payload["result"], "vv40", {}, pack_out_dir=out)

    assert res.ok, res.user_message
    assert Path(res.payload["download"]["zip_path"]).exists()
    assert_clean_state()
    wizard.discard_pack_dir(out)


def test_discard_pack_dir_removes_the_download(tmp_path, demo_key_env):
    out = wizard.new_pack_dir()
    (out / "probe.zip").write_bytes(b"x")
    wizard.discard_pack_dir(out)
    assert not out.exists()


def test_discard_pack_dir_refuses_paths_it_did_not_create(tmp_path):
    """Start-over passes whatever is in session state. A blank or foreign value
    must not delete something else."""
    victim = tmp_path / "not-ours"
    victim.mkdir()
    wizard.discard_pack_dir(victim)
    wizard.discard_pack_dir(None)
    wizard.discard_pack_dir("")
    assert victim.exists()


def test_sweep_drops_stale_packs_and_keeps_fresh_ones(monkeypatch):
    import time

    fresh, stale = wizard.new_pack_dir(), wizard.new_pack_dir()
    old = time.time() - (wizard.PACK_TTL_SECONDS + 60)
    import os
    os.utime(stale, (old, old))

    wizard._sweep_stale_packs()

    assert fresh.exists()
    assert not stale.exists()
    wizard.discard_pack_dir(fresh)
