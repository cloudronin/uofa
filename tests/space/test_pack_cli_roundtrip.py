"""The done-gate: `uofa verify` (CLI) passes on a pack produced by the web path.

In-process assertions are not enough here. The claim being tested is that a
person who downloads the zip and follows VERIFY.txt gets rc 0 -- so these drive
the real command in a real subprocess, from the extracted directory, with
exactly the arguments VERIFY.txt prints.

A round-trip test that can only pass is not evidence, so the tamper case is
part of the gate rather than an extra.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from space import pipeline
from uofa_cli.card_bundle import deterministic_import_dict

REPO_ROOT = Path(__file__).resolve().parents[2]

_CARD = "# A model\n\nTrained on public data. Evaluated on a held-out split.\n"


def run_uofa(*args, cwd: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(REPO_ROOT / "src"), env.get("PYTHONPATH", "")])
    return subprocess.run(
        [sys.executable, "-m", "uofa_cli.cli", *args],
        capture_output=True, text=True, env=env, cwd=cwd,
    )


@pytest.fixture
def extracted_pack(tmp_path, demo_key_env):
    """A pack built by the web path, unzipped exactly as a user would."""
    data = deterministic_import_dict(_CARD, "model-credibility", "org/m",
                                     "https://huggingface.co/org/m")
    work, out = tmp_path / "work", tmp_path / "out"
    work.mkdir()
    payload = pipeline.finalize_from_data(
        data, "model-credibility", work, source_name="card.md",
        assess_sufficiency=False, pack_out_dir=out)

    ex = tmp_path / "extracted"
    with zipfile.ZipFile(payload["download"]["zip_path"]) as zf:
        zf.extractall(ex)
    return ex


def test_cli_verify_passes_on_a_web_produced_pack(extracted_pack):
    """THE done-gate."""
    r = run_uofa("verify", "uofa.jsonld", "--pubkey", "keys/demo.pub", cwd=extracted_pack)
    assert r.returncode == 0, f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    assert "Hash match" in r.stdout
    assert "Signature valid" in r.stdout


def test_cli_verify_fails_on_a_tampered_pack(extracted_pack):
    """The other half of the gate: the signature has to actually bind."""
    pkg = extracted_pack / "uofa.jsonld"
    doc = json.loads(pkg.read_text(encoding="utf-8"))
    doc["id"] = str(doc.get("id", "")) + "-tampered"
    pkg.write_text(json.dumps(doc, indent=2), encoding="utf-8")

    r = run_uofa("verify", "uofa.jsonld", "--pubkey", "keys/demo.pub", cwd=extracted_pack)
    assert r.returncode == 1, f"tampered package verified! stdout:\n{r.stdout}"


def test_cli_verify_fails_against_the_wrong_trust_anchor(extracted_pack):
    """A demo package must not verify as a research package. The demo key is
    deliberately not the default anchor, so `--pubkey` is a visible act of
    choosing to trust the demo issuer."""
    r = run_uofa("verify", "uofa.jsonld",
                 "--pubkey", str(REPO_ROOT / "keys" / "research.pub"), cwd=extracted_pack)
    assert r.returncode == 1


def test_cli_verify_without_pubkey_does_not_silently_trust_the_demo(extracted_pack):
    """No flag means the default research anchor, which must reject this."""
    r = run_uofa("verify", "uofa.jsonld", cwd=extracted_pack)
    assert r.returncode != 0


def test_cli_check_needs_no_pack_flag(extracted_pack):
    """`validatedWithPacks` is stamped into the package, so a recipient does not
    have to be told which standards profile to validate against. C1 integrity is
    the assertion here; SHACL findings are a statement about the evidence."""
    r = run_uofa("check", "uofa.jsonld", "--pubkey", "keys/demo.pub", cwd=extracted_pack)
    combined = r.stdout + r.stderr
    assert "unknown pack" not in combined.lower()
    assert "C1" in combined or "Integrity" in combined
    assert "Hash match" in combined or "integrity" in combined.lower()


def test_verify_txt_command_is_the_one_that_works(extracted_pack):
    """Whatever VERIFY.txt tells the user to run must be what we just proved
    works. A drifted instruction is a broken artifact even if the code is fine."""
    text = (extracted_pack / "VERIFY.txt").read_text(encoding="utf-8")
    assert "uofa verify uofa.jsonld --pubkey keys/demo.pub" in text
    line = "uofa verify uofa.jsonld --pubkey keys/demo.pub"
    r = run_uofa(*line.split()[1:], cwd=extracted_pack)
    assert r.returncode == 0
