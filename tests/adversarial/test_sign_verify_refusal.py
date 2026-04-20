"""End-to-end tests for sign/verify refusal of synthetic samples (§10.2)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MOCK_FIXTURE = REPO_ROOT / "tests" / "adversarial" / "fixtures" / "mock_response.jsonld"


def run_uofa(*args, env: dict | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "uofa_cli.cli", *args],
        capture_output=True,
        text=True,
        env=full_env,
        cwd=cwd or REPO_ROOT,
    )


@pytest.fixture
def synthetic_sample(tmp_path) -> Path:
    """Generate one synthetic package using the mock LLM and return its path."""
    out_dir = tmp_path / "synth"
    result = run_uofa(
        "adversarial",
        "generate",
        "--spec",
        "tests/adversarial/fixtures/spec_w_ar_05_valid.yaml",
        "--out",
        str(out_dir),
        "--model",
        "mock",
        "--allow-circular-model",
        env={"UOFA_ADVERSARIAL_MOCK_FIXTURE": str(MOCK_FIXTURE)},
    )
    assert result.returncode == 0, result.stderr
    jsonld_files = sorted(out_dir.glob("*.jsonld"))
    assert jsonld_files, "generator produced no synthetic samples"
    return jsonld_files[0]


@pytest.fixture
def research_key(tmp_path) -> Path:
    """Create a throwaway ed25519 keypair for sign tests."""
    from uofa_cli.integrity import generate_keypair

    key = tmp_path / "key.pem"
    generate_keypair(key)
    return key


def test_sign_refuses_synthetic(synthetic_sample, research_key):
    result = run_uofa("sign", str(synthetic_sample), "--key", str(research_key))
    assert result.returncode == 2
    combined = (result.stderr + result.stdout).lower()
    assert "refusing to sign" in combined
    assert "synthetic" in combined


def test_verify_refuses_synthetic(synthetic_sample):
    result = run_uofa("verify", str(synthetic_sample))
    assert result.returncode == 2
    combined = (result.stderr + result.stdout).lower()
    assert "refusing to verify" in combined


def test_verify_warns_on_flag_strip(synthetic_sample, tmp_path):
    """Step 7 of spec §11.4 acceptance test: sed-strip the synthetic flag
    and confirm verify prints 'hash does not match'."""
    tampered = tmp_path / "tampered.jsonld"
    original = synthetic_sample.read_text()
    tampered.write_text(original.replace('"synthetic": true', '"synthetic": false'))

    result = run_uofa("verify", str(tampered))
    combined = result.stderr + result.stdout
    assert "hash does not match" in combined.lower()
    assert result.returncode == 2


def test_verify_warns_on_block_tamper(synthetic_sample, tmp_path):
    """Tamper with a field inside adversarialProvenance; block-hash mismatch
    warning must fire with 'hash does not match'."""
    tampered = tmp_path / "tampered.jsonld"
    doc = json.loads(synthetic_sample.read_text())
    # Mutate a field inside the provenance block without touching the hash.
    doc["adversarialProvenance"]["targetWeakener"] = "W-AR-99"
    tampered.write_text(json.dumps(doc, indent=2))

    result = run_uofa("verify", str(tampered))
    combined = result.stderr + result.stdout
    assert "hash does not match" in combined.lower()


def test_sign_still_works_on_non_synthetic(tmp_path, research_key):
    """Regression: signing a normal (non-synthetic) file must still succeed."""
    pkg = {
        "@context": "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.4.jsonld",
        "id": "https://uofa.net/test/normal",
        "type": "UnitOfAssurance",
        "conformsToProfile": "https://uofa.net/vocab#ProfileMinimal",
        "bindsRequirement": "https://uofa.net/test/req",
        "hasContextOfUse": "https://uofa.net/test/cou",
        "hasValidationResult": ["https://uofa.net/test/vr"],
        "hasDecisionRecord": "https://uofa.net/test/dr",
        "generatedAtTime": "2026-04-19T00:00:00Z",
    }
    path = tmp_path / "normal.jsonld"
    path.write_text(json.dumps(pkg, indent=2))
    result = run_uofa("sign", str(path), "--key", str(research_key))
    assert result.returncode == 0, result.stderr
