"""protocol-check — the scriptable subset of the encoding protocol.

Fixtures are built from the shipped nasa-7009b template rather than hand-authored, so a
template change surfaces here instead of silently making the checks vacuous.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

openpyxl = pytest.importorskip("openpyxl")

from uofa_cli import protocol_check  # noqa: E402
from uofa_cli.protocol_check import ANCHOR_HEADER, check_package, check_workbook  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "packs" / "nasa-7009b" / "templates" / "nasa-7009b-template.xlsx"
REVIEWED = REPO / "dev" / "build" / "pilot-johnson" / "johnson-extracted.xlsx"


def _verdict(results, name_fragment):
    for r in results:
        if name_fragment in r.name:
            return r
    raise AssertionError(f"no check named like {name_fragment!r} in {[r.name for r in results]}")


def _add_anchor_column(path: Path, value: str = "p.1") -> None:
    """Give every populated data row an anchor, the state a reviewed workbook is in."""
    wb = openpyxl.load_workbook(path)
    for sheet, (first_header, offset) in protocol_check._SHEETS.items():
        if sheet not in wb.sheetnames:
            continue
        ws = wb[sheet]
        head = protocol_check._sheet_header_row(ws, first_header)
        if head is None:
            continue
        last = max(c for c in range(1, 40) if ws.cell(row=head, column=c).value) or 1
        ws.cell(row=head, column=last + 1).value = ANCHOR_HEADER
        for row in range(head + offset, ws.max_row + 1):
            if any(ws.cell(row=row, column=c).value not in (None, "") for c in range(1, last + 1)):
                ws.cell(row=row, column=last + 1).value = value
    wb.save(path)


def _blank_template(tmp_path: Path) -> Path:
    """The template with its description rows cleared, so only seeded defects remain."""
    out = tmp_path / "wb.xlsx"
    shutil.copy2(TEMPLATE, out)
    wb = openpyxl.load_workbook(out)
    for sheet, (first_header, _) in protocol_check._SHEETS.items():
        if sheet not in wb.sheetnames:
            continue
        ws = wb[sheet]
        head = protocol_check._sheet_header_row(ws, first_header)
        if head is None:
            continue
        for col in range(1, 40):
            ws.cell(row=head + 1, column=col).value = None
    wb.save(out)
    return out


# ── workbook-side ────────────────────────────────────────────────────────────

def test_missing_anchor_column_fails(tmp_path):
    wb = _blank_template(tmp_path)
    assert not _verdict(check_workbook(wb, TEMPLATE), "anchor column present").passed


def test_anchor_column_present_passes(tmp_path):
    wb = _blank_template(tmp_path)
    _add_anchor_column(wb)
    assert _verdict(check_workbook(wb, TEMPLATE), "anchor column present").passed


def test_unanchored_populated_row_fails(tmp_path):
    wb = _blank_template(tmp_path)
    _add_anchor_column(wb)
    book = openpyxl.load_workbook(wb)
    ws = book["Credibility Factors"]
    acol = protocol_check._anchor_col(ws)
    ws.cell(row=5, column=acol).value = None  # a factor row loses its anchor
    book.save(wb)
    result = _verdict(check_workbook(wb, TEMPLATE), "anchor non-empty")
    assert not result.passed
    assert "Credibility Factors row 5" in result.detail


def test_template_placeholder_left_in_data_row_fails(tmp_path):
    """The exact defect the pilot's raw extract shipped six times (F-3d)."""
    wb = _blank_template(tmp_path)
    _add_anchor_column(wb)
    hints = protocol_check._template_placeholders(TEMPLATE)
    assert hints, "template carries no description-row hints to detect"
    book = openpyxl.load_workbook(wb)
    ws = book["Assessment Summary"]
    head = protocol_check._sheet_header_row(ws, "Project Name")
    ws.cell(row=head + 2, column=1).value = sorted(hints)[0]
    acol = protocol_check._anchor_col(ws)
    ws.cell(row=head + 2, column=acol).value = "p.1"
    book.save(wb)
    assert not _verdict(check_workbook(wb, TEMPLATE), "placeholder").passed


def test_placeholder_check_skipped_without_a_template(tmp_path):
    wb = _blank_template(tmp_path)
    _add_anchor_column(wb)
    assert _verdict(check_workbook(wb, None), "placeholder").skipped


def _set_levels(path: Path, pairs: list[tuple[int, int]], criteria: str | None = None) -> None:
    book = openpyxl.load_workbook(path)
    ws = book["Credibility Factors"]
    head = protocol_check._sheet_header_row(ws, "Factor Type")
    for i, (req, ach) in enumerate(pairs):
        row = head + 2 + i
        ws.cell(row=row, column=3).value = req
        ws.cell(row=row, column=4).value = ach
        if criteria:
            ws.cell(row=row, column=5).value = criteria
    book.save(path)


def test_required_equal_to_achieved_everywhere_fails(tmp_path):
    """The seventeen-of-seventeen synthesized column the pilot shipped (F-3b)."""
    wb = _blank_template(tmp_path)
    _add_anchor_column(wb)
    _set_levels(wb, [(3, 3), (4, 4), (2, 2)])
    result = _verdict(check_workbook(wb, TEMPLATE), "required differs")
    assert not result.passed
    assert "unreviewed" in result.detail


def test_one_differing_factor_passes(tmp_path):
    wb = _blank_template(tmp_path)
    _add_anchor_column(wb)
    _set_levels(wb, [(3, 3), (2, 4), (4, 4)])
    assert _verdict(check_workbook(wb, TEMPLATE), "required differs").passed


def test_recorded_waiver_releases_the_level_check(tmp_path):
    wb = _blank_template(tmp_path)
    _add_anchor_column(wb)
    _set_levels(wb, [(3, 3), (4, 4)], criteria="Validation waived by Technical Authority")
    assert _verdict(check_workbook(wb, TEMPLATE), "required differs").passed


@pytest.mark.skipif(not REVIEWED.exists(), reason="pilot workbook not present")
def test_reviewed_pilot_workbook_passes_every_workbook_check():
    for r in check_workbook(REVIEWED, TEMPLATE):
        assert r.passed or r.skipped, f"{r.name}: {r.detail}"


# ── package-side ─────────────────────────────────────────────────────────────

GOOD_RUN_LOG = (
    "# Run log\n\n"
    "model: anthropic/claude-sonnet-5\nbackend: anthropic\n"
    "site commit: 31cb466\nrepo HEAD: abc1234\nbase_uri: https://uofa.net\n"
)


def _package_dir(tmp_path: Path, *, ambiguity: str | None, run_log: str | None) -> Path:
    pkg = tmp_path / "pkg.jsonld"
    pkg.write_text("{}", encoding="utf8")
    if ambiguity is not None:
        (tmp_path / "AMBIGUITY_LOG.md").write_text(ambiguity, encoding="utf8")
    if run_log is not None:
        (tmp_path / "RUN_LOG.md").write_text(run_log, encoding="utf8")
    return pkg


def test_missing_ambiguity_log_fails(tmp_path):
    pkg = _package_dir(tmp_path, ambiguity=None, run_log=GOOD_RUN_LOG)
    assert not _verdict(check_package(pkg), "ambiguity log").passed


def test_empty_ambiguity_log_fails(tmp_path):
    pkg = _package_dir(tmp_path, ambiguity="   \n", run_log=GOOD_RUN_LOG)
    assert not _verdict(check_package(pkg), "ambiguity log").passed


def test_complete_run_log_passes(tmp_path):
    pkg = _package_dir(tmp_path, ambiguity="A-01 ...", run_log=GOOD_RUN_LOG)
    for r in check_package(pkg):
        assert r.passed or r.skipped, f"{r.name}: {r.detail}"


def test_run_log_missing_a_pin_fails(tmp_path):
    pkg = _package_dir(tmp_path, ambiguity="A-01 ...",
                       run_log=GOOD_RUN_LOG.replace("base_uri: https://uofa.net\n", ""))
    result = _verdict(check_package(pkg), "carries its pins")
    assert not result.passed
    assert "base_uri" in result.detail


def test_signing_in_a_pilot_run_log_fails(tmp_path):
    pkg = _package_dir(tmp_path, ambiguity="A-01 ...",
                       run_log=GOOD_RUN_LOG + "\npilot run\nuofa import x.xlsx --sign --key k\n")
    assert not _verdict(check_package(pkg), "no signing").passed


def test_prohibition_of_signing_is_not_a_use(tmp_path):
    """"no --sign" in a pilot log is the rule being stated, not broken."""
    pkg = _package_dir(tmp_path, ambiguity="A-01 ...",
                       run_log=GOOD_RUN_LOG + "\npilot run\nImport target: no --sign anywhere.\n")
    assert _verdict(check_package(pkg), "no signing").passed


def test_signing_check_skipped_when_run_log_is_not_pilot_labeled(tmp_path):
    pkg = _package_dir(tmp_path, ambiguity="A-01 ...",
                       run_log=GOOD_RUN_LOG + "\nuofa import x.xlsx --sign --key k\n")
    assert _verdict(check_package(pkg), "no signing").skipped


# ── CLI wiring ───────────────────────────────────────────────────────────────

def _uofa(*args, cwd=REPO):
    return subprocess.run([sys.executable, "-m", "uofa_cli", *args],
                          cwd=cwd, capture_output=True, text=True)


@pytest.mark.skipif(not REVIEWED.exists(), reason="pilot workbook not present")
def test_import_protocol_check_exits_non_zero_on_failure(tmp_path):
    """A package with no ambiguity log beside it must not pass the gate.

    Uses the reviewed pilot workbook because the gate runs after import succeeds; a
    workbook that fails import validation exits non-zero for a different reason and
    would make this test vacuous.
    """
    out = tmp_path / "out.jsonld"
    proc = _uofa("import", str(REVIEWED), "--pack", "nasa-7009b",
                 "--protocol-check", "-o", str(out))
    assert proc.returncode != 0, proc.stdout + proc.stderr
    assert "protocol-check" in proc.stdout
    assert "ambiguity log" in proc.stdout


@pytest.mark.skipif(not REVIEWED.exists(), reason="pilot workbook not present")
def test_import_without_the_flag_does_not_gate(tmp_path):
    """The gate is opt-in; the same import succeeds without the flag."""
    out = tmp_path / "out.jsonld"
    proc = _uofa("import", str(REVIEWED), "--pack", "nasa-7009b", "-o", str(out))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "protocol-check" not in proc.stdout


def test_extract_flag_is_accepted_and_documented():
    proc = _uofa("extract", "--help")
    assert proc.returncode == 0
    assert "--protocol-check" in proc.stdout
    assert "Informational" in proc.stdout or "informational" in proc.stdout
