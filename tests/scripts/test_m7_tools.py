"""Tests for the M7 export tooling under ``scripts/``.

Phase 2 v1.8 §11 / §16:
- ``scripts/export_view_pdf.py``        — HTML → PDF (Figure 3.x)
- ``scripts/export_view3_markdown.py``  — outcomes.csv → Markdown table
- ``scripts/build_phase2_review_packet.py`` — master Phase 3 handoff doc

Tests use hand-crafted fixtures (small outcomes.csv + batch_manifest.json)
rather than running the full analyze pipeline so they stay fast and don't
depend on a smoke-test snapshot.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
SCRIPTS = REPO_ROOT / "scripts"


def _load_script(filename: str):
    """Import a scripts/*.py module by file path (not on sys.path)."""
    spec = importlib.util.spec_from_file_location(
        f"scripts.{filename.replace('.py', '')}", SCRIPTS / filename
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {filename}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


# ───────────────────── fixtures ─────────────────────


def _make_outcomes(path: Path, rows: list[dict]) -> None:
    """Write a minimal outcomes.csv with the columns the M7 scripts read."""
    fields = [
        "spec_id", "outcome_class", "coverage_intent",
        "source_taxonomy", "section_6_7_candidate",
        "target_weakener", "rules_fired",
    ]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def _smoke_outcomes() -> list[dict]:
    """4 hand-crafted rows spanning all three batteries."""
    return [
        {"spec_id": "s1", "outcome_class": "COV-HIT",
         "coverage_intent": "confirm_existing", "target_weakener": "W-AR-01",
         "rules_fired": "W-AR-01"},
        {"spec_id": "s2", "outcome_class": "COV-HIT",
         "coverage_intent": "confirm_existing", "target_weakener": "W-EP-01",
         "rules_fired": "W-EP-01"},
        {"spec_id": "s3", "outcome_class": "COV-MISS",
         "coverage_intent": "gap_probe",
         "source_taxonomy": "gohar/evidence_validity/data-drift",
         "section_6_7_candidate": "True"},
        {"spec_id": "s4", "outcome_class": "COV-CLEAN-WRONG",
         "coverage_intent": "negative_control"},
    ]


# ───────────────────── export_view3_markdown ─────────────────────


def test_view3_markdown_computes_metrics_correctly(tmp_path):
    mod = _load_script("export_view3_markdown.py")
    metrics = mod.compute_view3_metrics(_smoke_outcomes())
    # 2/2 confirm hits → 100%
    assert metrics["catalog_recall"] == 1.0
    # 1/1 NC wrong → precision = 0%
    assert metrics["catalog_precision_1_minus_fpr"] == 0.0
    # 1/1 gap_probe miss → 100%
    assert metrics["gap_probe_miss_rate"] == 1.0
    assert metrics["n_confirm"] == 2
    assert metrics["n_nc"] == 1
    assert metrics["n_gp"] == 1


def test_view3_markdown_renders_table(tmp_path):
    mod = _load_script("export_view3_markdown.py")
    outcomes_path = tmp_path / "outcomes.csv"
    _make_outcomes(outcomes_path, _smoke_outcomes())
    out_path = tmp_path / "view3.md"
    rc = mod.main(["--outcomes", str(outcomes_path), "--output", str(out_path)])
    assert rc == 0
    body = out_path.read_text()
    assert "View 3 — Catalog precision / recall summary" in body
    assert "Catalog recall" in body
    assert "100.0%" in body  # 2/2 confirm hits
    assert "0.0%" in body    # NC precision (1/1 wrong)


def test_view3_markdown_returns_2_when_outcomes_missing(tmp_path):
    mod = _load_script("export_view3_markdown.py")
    rc = mod.main([
        "--outcomes", str(tmp_path / "no-such.csv"),
        "--output", str(tmp_path / "x.md"),
    ])
    assert rc == 2


# ───────────────────── build_phase2_review_packet ─────────────────────


def _make_batch_dir(tmp_path: Path) -> Path:
    """Construct a minimal batch dir with manifest + coverage/outcomes.csv."""
    batch = tmp_path / "2026-05-16"
    coverage = batch / "coverage"
    coverage.mkdir(parents=True)
    _make_outcomes(coverage / "outcomes.csv", _smoke_outcomes())
    (batch / "batch_manifest.json").write_text(json.dumps({
        "batchId": "batch-20260516000000",
        "timestamp": "2026-05-16T00:00:00Z",
        "toolVersion": "uofa-cli 0.5.5",
        "generatorVersion": "0.1.0",
        "specsLoaded": 60,
        "specsSucceeded": 58,
        "specsGenInvalid": 2,
        "totalPackages": 4440,
        "estimatedCostUsd": 285.42,
        "subtletyOverride": ["low", "medium", "high"],
        "baseCouOverride": ["packs/vv40/examples/morrison/cou1"],
        "modelsOverride": None,
        "strictCircularity": True,
        "halted": False,
    }, indent=2))
    return batch


def test_review_packet_includes_required_sections(tmp_path):
    mod = _load_script("build_phase2_review_packet.py")
    batch = _make_batch_dir(tmp_path)
    out = tmp_path / "phase2_review_packet.md"
    rc = mod.main(["--batch-dir", str(batch), "--output", str(out)])
    assert rc == 0
    body = out.read_text()
    # Required sections
    assert "# Phase 2 → Phase 3 review packet" in body
    assert "## Batch metadata" in body
    assert "## View 3" in body or "## View 3 — catalog" in body
    assert "## COV-MISS / COV-WRONG inventory" in body
    assert "## Reviewer questions" in body
    # Manifest values surface
    assert "batch-20260516000000" in body
    assert "4440" in body
    # Miss inventory groups by source_taxonomy + flags §6.7 candidate
    assert "gohar/evidence_validity/data-drift" in body
    assert "★" in body


def test_review_packet_handles_missing_review_index_gracefully(tmp_path):
    mod = _load_script("build_phase2_review_packet.py")
    batch = _make_batch_dir(tmp_path)
    out = tmp_path / "phase2_review_packet.md"
    mod.main(["--batch-dir", str(batch), "--output", str(out)])
    # No review_packets/INDEX.md in the fixture batch
    body = out.read_text()
    assert "Per-spec reviewer packets" in body
    assert "Not generated yet" in body
    assert "uofa adversarial prep-review" in body  # actionable hint


def test_review_packet_returns_2_when_batch_dir_missing(tmp_path):
    mod = _load_script("build_phase2_review_packet.py")
    rc = mod.main([
        "--batch-dir", str(tmp_path / "no-such"),
        "--output", str(tmp_path / "x.md"),
    ])
    assert rc == 2


# ───────────────────── export_view_pdf ─────────────────────


def test_export_view_pdf_slice_view_extracts_section(tmp_path):
    """Unit-test the HTML slicing without invoking weasyprint (which has a
    heavy native toolchain)."""
    mod = _load_script("export_view_pdf.py")
    html = """<!DOCTYPE html><html><head><title>x</title></head><body>
<h2 id="view1">View 1</h2><p>v1 body</p>
<h2 id="view2">View 2</h2><p>v2 body</p>
<h2 id="view3">View 3</h2><p>v3 body</p>
</body></html>"""
    out = mod._slice_view(html, 2)
    assert "v2 body" in out
    assert "v1 body" not in out
    assert "v3 body" not in out
    # CSS to force <details open> always present after slicing
    assert "details" in out and "display: revert" in out


def test_export_view_pdf_returns_2_when_report_missing(tmp_path):
    mod = _load_script("export_view_pdf.py")
    rc = mod.main([
        "--report", str(tmp_path / "nope.html"),
        "--output", str(tmp_path / "x.pdf"),
    ])
    assert rc == 2


def test_export_view_pdf_full_render_when_weasyprint_available(tmp_path):
    """End-to-end PDF render when weasyprint is installed (skip otherwise)."""
    pytest.importorskip("weasyprint")
    mod = _load_script("export_view_pdf.py")
    html_path = tmp_path / "report.html"
    html_path.write_text(
        "<!DOCTYPE html><html><head><title>x</title></head><body>"
        "<h2 id='view2'>View 2</h2><p>hello</p>"
        "</body></html>"
    )
    pdf_path = tmp_path / "out.pdf"
    rc = mod.main([
        "--report", str(html_path),
        "--view", "2",
        "--output", str(pdf_path),
    ])
    assert rc == 0
    assert pdf_path.exists()
    # Sanity-check: file is a real PDF (PDF magic bytes are %PDF-)
    assert pdf_path.read_bytes()[:5] == b"%PDF-"
