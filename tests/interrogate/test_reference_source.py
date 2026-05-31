"""P4 §3a — the ReferenceSource interface: the pluggable boundary for truth.

Covers the whole contract (serve + generate) even though only serve is exercised
by Product A's evidence path:
- a serve-only FileReferenceSource serves precomputed reference/constraint/UQ
  data and declares it cannot generate (capability-detection, no dead method);
- a custom serve+generate source resolves by class reference and its generate
  capability is invocable only after supports_generate() says so;
- load_reference_source dispatches a data-file path to FileReferenceSource and a
  class reference to a custom source, rejecting non-ReferenceSource targets.

Firewall (§3a): both halves sit on the reference side — a source provides the
truth SIP measures against, never a verdict. (The byte-identical golden gate
covers that routing truth through this interface didn't perturb the bundle.)
"""

from __future__ import annotations

from pathlib import Path

import pytest

from uofa_cli.interrogate import reference_source as rs
from uofa_cli.interrogate.loader import Reference

FIXTURE = Path(__file__).parent / "fixtures" / "stub_reference_source.py"


def _write_ref(tmp_path: Path) -> Path:
    np = pytest.importorskip("numpy")
    p = tmp_path / "ref.npz"
    np.savez(p, **{
        "ref__cl": np.array([0.5, 0.8]),
        "ref__cd": np.array([0.02, 0.03]),
        "constraint__continuity": np.array([0.001, -0.002]),
        "lower__cl": np.array([0.45, 0.75]),
        "upper__cl": np.array([0.55, 0.85]),
    })
    return p


def test_file_source_serves_precomputed(tmp_path):
    src = rs.FileReferenceSource(_write_ref(tmp_path))
    assert set(src.reference()) == {"cl", "cd"}
    assert "continuity" in src.constraint_fields()
    assert "cl" in src.uq_intervals()


def test_file_source_is_serve_only(tmp_path):
    src = rs.FileReferenceSource(_write_ref(tmp_path))
    assert src.supports_generate() is False
    # Capability-detection, not a dead method: generate raises a clear refusal.
    with pytest.raises(NotImplementedError, match="serve-only"):
        src.generate(inputs=[[1.0]])


def test_to_reference_materializes_container(tmp_path):
    ref = rs.to_reference(rs.FileReferenceSource(_write_ref(tmp_path)))
    assert isinstance(ref, Reference)
    assert set(ref.reference) == {"cl", "cd"}
    assert "continuity" in ref.constraint_fields
    assert "cl" in ref.uq_intervals


def test_load_data_path_resolves_to_file_source(tmp_path):
    assert isinstance(rs.load_reference_source(_write_ref(tmp_path)), rs.FileReferenceSource)


def test_load_class_ref_resolves_custom_source():
    src = rs.load_reference_source(f"{FIXTURE}:StubServeSource")
    assert isinstance(src, rs.ReferenceSource)
    assert src.reference() == {"cl": [0.5, 0.8]}
    assert src.supports_generate() is False


def test_generating_source_capability_detection():
    src = rs.load_reference_source(f"{FIXTURE}:StubGenSource")
    assert src.supports_generate() is True  # consumer asks before invoking
    assert src.generate([[1.0], [2.0]]) == {"cl": [0.2]}


def test_load_rejects_non_reference_source():
    with pytest.raises(ValueError, match="ReferenceSource subclass"):
        rs.load_reference_source(f"{FIXTURE}:NotASource")
