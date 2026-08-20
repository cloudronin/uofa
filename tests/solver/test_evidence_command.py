"""`uofa evidence` — the command surface and its structured contract."""

from __future__ import annotations

import argparse
import io
import json
from contextlib import redirect_stderr, redirect_stdout

import pytest

from uofa_cli.commands import evidence


def _args(**kw):
    ns = argparse.Namespace(source=None, source_map=None, fetched_at=None,
                            members=False, output=None, evidence_command="inventory",
                            no_color=True, verbose=False)
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


def test_run_structured_prints_nothing(evidence_folder, capsys):
    """run() is the I/O shell; run_structured() must be silent.

    Same contract as tests/test_command_structured.py — a structured entry point
    that prints makes every caller emit the readout twice.
    """
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        result = evidence.run_structured(_args(source=evidence_folder))
    assert out.getvalue() == ""
    assert err.getvalue() == ""
    assert result.seal.n_files == 2


def test_inventory_writes_no_sidecar(evidence_folder):
    result = evidence.run_structured(_args(source=evidence_folder))
    assert result.sidecar is None


def test_seal_writes_the_sidecar(evidence_folder, tmp_path):
    out = tmp_path / "evidence.json"
    result = evidence.run_structured(
        _args(source=evidence_folder, evidence_command="seal", output=out))
    assert result.sidecar == out
    doc = json.loads(out.read_text())
    assert doc["artifactManifest"]


def test_default_sidecar_path_is_derived_from_the_source(evidence_folder):
    result = evidence.run_structured(
        _args(source=evidence_folder, evidence_command="seal"))
    assert result.sidecar.name == f"{evidence_folder.name}-evidence.json"


def test_sealed_but_unread_is_success_not_failure(evidence_folder):
    """The exit code must not punish an archive full of binaries.

    A sealed-and-reported `.mechdb` is the designed outcome, so a non-zero exit
    would train operators to ignore the code on every real evidence folder.
    """
    result = evidence.run_structured(_args(source=evidence_folder))
    assert any(not m.read for a in result.seal.artifacts for m in a.members)
    assert result.exit_code == 0


def test_missing_source_is_a_usage_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        evidence.run(_args(source=tmp_path / "nope", evidence_command="inventory"))


def test_no_subcommand_returns_usage_exit_code(capsys):
    assert evidence.run(_args(evidence_command=None)) == 2


def test_source_map_file_formats_agree(tmp_path):
    """JSON object and the two-column text form must load identically."""
    from uofa_cli.solver import seal as sealmod
    a = tmp_path / "m.json"
    a.write_text(json.dumps({"x.wbpz": "https://example.invalid/x"}))
    b = tmp_path / "m.txt"
    b.write_text("# comment\nx.wbpz  https://example.invalid/x\n")
    assert sealmod.load_source_map(a) == sealmod.load_source_map(b)
