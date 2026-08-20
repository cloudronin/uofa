"""Protocol-check — mechanical conformance checks for a reference encoding.

These are the scriptable subset of `docs/Encoding_Protocol_v0_1_DRAFT.md`, seeded by
finding F-6c of the Johnson pilot. They exist so that no workbook reaches the author's
review pass while it still fails a check a machine could have run.

## Why a flag and not a command

The checks have no state of their own and nothing to orchestrate. They are assertions
about an artifact that `extract` has just written or that `import` has just been handed,
so they ride those commands rather than adding a third that would need to be told where
to look.

## Why the two commands behave differently

Every check here describes a *reviewed* workbook. A freshly extracted one has no citation
anchors, because anchors are what the review pass produces, so on `extract` the flag
prints the table and leaves the exit code alone: it is telling the encoder what review has
to produce, not failing them for not having done it yet. On `import` the workbook is the
reviewed one and the checks are gates, so any failure exits non-zero.

## Placeholder detection is pack-derived, not hardcoded

Every pack template carries a description row under each header row, and its strings are
exactly the hint text that leaks into data rows when the extractor writes nothing
(F-3d). The placeholder set is read from the active pack's own template rather than listed
here, so a pack that changes its hints does not silently stop being checked.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from uofa_cli.excel_constants import SHEET_NAMES

ANCHOR_HEADER = "Source Anchor"

# Files the protocol requires beside a package. Names are conventions rather than
# schema, so they are matched case-insensitively against a small candidate set.
AMBIGUITY_LOG_NAMES = ("ambiguity_log.md", "ambiguity-log.md", "ambiguitylog.md")
RUN_LOG_NAMES = ("run_log.md", "run-log.md", "runlog.md")

# Section 3 of the protocol names these as the run log's mandatory pins.
RUN_LOG_FIELDS = ("model", "backend", "site commit", "repo head", "base_uri")

# A run log that labels itself a pilot must not record a signing step, because a pilot
# runs before the protocol governs it and nothing it produces may be signed.
PILOT_MARKERS = ("pilot", "PILOT")


@dataclass(frozen=True)
class CheckResult:
    """One check, its verdict, and enough detail to act on a failure."""

    name: str
    passed: bool
    detail: str = ""
    skipped: bool = False


def _sheet_header_row(ws, first_header: str) -> int | None:
    for row in range(1, 12):
        for col in range(1, 40):
            value = ws.cell(row=row, column=col).value
            if isinstance(value, str) and value.strip() == first_header:
                return row
    return None


def _anchor_col(ws) -> int | None:
    for col in range(1, 40):
        for row in range(1, 12):
            if ws.cell(row=row, column=col).value == ANCHOR_HEADER:
                return col
    return None


# Sheet -> the header string that identifies its header row, and the first data row
# offset below it. The description row sits between them.
_SHEETS = {
    SHEET_NAMES["summary"]: ("Project Name", 2),
    SHEET_NAMES["model_data"]: ("Entity Type", 2),
    SHEET_NAMES["validation"]: ("Result Name", 2),
    SHEET_NAMES["factors"]: ("Factor Type", 2),
    SHEET_NAMES["decision"]: ("Decision Outcome", 2),
}


def _template_placeholders(template_path: Path | None) -> set[str]:
    """The hint strings a pack's own template puts in its description rows."""
    if not template_path or not template_path.exists():
        return set()
    import openpyxl

    wb = openpyxl.load_workbook(template_path)
    hints: set[str] = set()
    for sheet, (first_header, _) in _SHEETS.items():
        if sheet not in wb.sheetnames:
            continue
        ws = wb[sheet]
        head = _sheet_header_row(ws, first_header)
        if head is None:
            continue
        for col in range(1, 40):
            value = ws.cell(row=head + 1, column=col).value
            if isinstance(value, str) and len(value.strip()) > 3:
                hints.add(value.strip())
    return hints


def check_workbook(path: Path, template_path: Path | None = None) -> list[CheckResult]:
    """Workbook-side checks. See the module docstring for what these assume."""
    import openpyxl

    results: list[CheckResult] = []
    wb = openpyxl.load_workbook(path)
    placeholders = _template_placeholders(template_path)

    missing_col: list[str] = []
    unanchored: list[str] = []
    leaked: list[str] = []

    for sheet, (first_header, data_offset) in _SHEETS.items():
        if sheet not in wb.sheetnames:
            continue
        ws = wb[sheet]
        head = _sheet_header_row(ws, first_header)
        if head is None:
            continue
        acol = _anchor_col(ws)
        if acol is None:
            missing_col.append(sheet)
        start = head + data_offset
        for row in range(start, ws.max_row + 1):
            limit = acol if acol else 40
            values = [ws.cell(row=row, column=c).value for c in range(1, limit)]
            populated = [v for v in values if v not in (None, "")]
            if not populated:
                continue
            if acol and not ws.cell(row=row, column=acol).value:
                unanchored.append(f"{sheet} row {row}")
            for v in populated:
                if isinstance(v, str) and v.strip() in placeholders:
                    leaked.append(f"{sheet} row {row}: {v.strip()[:40]}")

    results.append(CheckResult(
        "anchor column present",
        not missing_col,
        "missing on " + ", ".join(missing_col) if missing_col else "on every data sheet",
    ))
    results.append(CheckResult(
        "anchor non-empty per populated row",
        not unanchored,
        f"{len(unanchored)} row(s) unanchored: " + "; ".join(unanchored[:4])
        if unanchored else "every populated row carries an anchor",
    ))
    results.append(CheckResult(
        "no template placeholder text in data rows",
        not leaked,
        f"{len(leaked)} leak(s): " + "; ".join(leaked[:3]) if leaked
        else ("clean" if placeholders else "no template available to compare against"),
        skipped=not placeholders,
    ))
    results.append(_check_levels(wb))
    return results


def _check_levels(wb) -> CheckResult:
    """Required equal to achieved on every factor means the column was never reviewed.

    The extract prompt sets required equal to achieved by default, so a workbook where
    that holds everywhere has not had its predeclaration located (F-3b). A recorded
    waiver in any acceptance-criteria or rationale cell releases the check.
    """
    sheet = SHEET_NAMES["factors"]
    if sheet not in wb.sheetnames:
        return CheckResult("required differs from achieved somewhere", True,
                           "no factors sheet", skipped=True)
    ws = wb[sheet]
    head = _sheet_header_row(ws, "Factor Type")
    if head is None:
        return CheckResult("required differs from achieved somewhere", True,
                           "no factor header", skipped=True)
    pairs = 0
    differing = 0
    waived = False
    for row in range(head + 2, ws.max_row + 1):
        if not ws.cell(row=row, column=1).value:
            continue
        req, ach = ws.cell(row=row, column=3).value, ws.cell(row=row, column=4).value
        for col in (5, 6):
            text = ws.cell(row=row, column=col).value
            if isinstance(text, str) and "waiv" in text.lower():
                waived = True
        if req is None or ach is None:
            continue
        pairs += 1
        if req != ach:
            differing += 1
    if pairs == 0:
        return CheckResult("required differs from achieved somewhere", True,
                           "no factor carries both levels", skipped=True)
    if differing or waived:
        return CheckResult("required differs from achieved somewhere", True,
                           f"{differing} of {pairs} differ"
                           + (", waiver recorded" if waived else ""))
    return CheckResult(
        "required differs from achieved somewhere", False,
        f"required equals achieved on all {pairs} factor(s); the extract prompt's "
        "default produces exactly this, so treat the column as unreviewed",
    )


def check_package(package_path: Path) -> list[CheckResult]:
    """Package-side checks, run against the artifacts committed beside the package."""
    results: list[CheckResult] = []
    directory = package_path.parent

    def _find(names: tuple[str, ...]) -> Path | None:
        for child in directory.iterdir():
            if child.is_file() and child.name.lower() in names:
                return child
        return None

    log = _find(AMBIGUITY_LOG_NAMES)
    if log is None:
        results.append(CheckResult("ambiguity log present", False,
                                   f"no ambiguity log beside {package_path.name}"))
    else:
        body = log.read_text(encoding="utf8", errors="replace").strip()
        results.append(CheckResult("ambiguity log present and non-empty",
                                   bool(body), f"{log.name}, {len(body)} chars"))

    run_log = _find(RUN_LOG_NAMES)
    if run_log is None:
        results.append(CheckResult("run log present", False,
                                   f"no run log beside {package_path.name}"))
        results.append(CheckResult("run log carries its pins", False, "no run log"))
        results.append(CheckResult("no signing in a pilot run log", True,
                                   "no run log", skipped=True))
        return results

    text = run_log.read_text(encoding="utf8", errors="replace")
    lowered = text.lower()
    results.append(CheckResult("run log present", True, run_log.name))

    absent = [f for f in RUN_LOG_FIELDS if f.lower() not in lowered]
    results.append(CheckResult(
        "run log carries its pins", not absent,
        "missing " + ", ".join(absent) if absent else ", ".join(RUN_LOG_FIELDS),
    ))

    is_pilot = any(m.lower() in lowered for m in PILOT_MARKERS)
    if not is_pilot:
        results.append(CheckResult("no signing in a pilot run log", True,
                                   "run log is not pilot-labeled", skipped=True))
    else:
        # A mention inside a prohibition ("no --sign", "without signing") is not a use.
        offending = [
            line.strip() for line in text.splitlines()
            if "--sign" in line
            and not any(n in line.lower() for n in ("no --sign", "without", "never", "not "))
        ]
        results.append(CheckResult(
            "no signing in a pilot run log", not offending,
            "; ".join(offending[:2])[:120] if offending else "pilot run log records no signing",
        ))
    return results


def render(results: list[CheckResult], title: str) -> bool:
    """Print the pass/fail table. Returns True when nothing failed."""
    from uofa_cli.output import step_header, result_line, info

    step_header(f"protocol-check: {title}")
    for r in results:
        if r.skipped:
            info(f"  - {r.name}  ({r.detail})")
        else:
            result_line(r.name, r.passed, r.detail)
    failed = [r for r in results if not r.passed and not r.skipped]
    if failed:
        info(f"  {len(failed)} check(s) failed")
    return not failed
