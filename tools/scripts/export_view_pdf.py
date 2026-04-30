#!/usr/bin/env python3
"""Export an HTML coverage report (or a specific View) to PDF.

Phase 2 v1.8 §11.1 Figure 3.x candidate. Reads ``coverage/index.html``
produced by ``uofa adversarial analyze`` and writes a PDF copy. WeasyPrint
is the rendering engine; install via ``pip install -e '.[export]'``.

Usage:
    python tools/scripts/export_view_pdf.py \\
        --report build/.../coverage/index.html \\
        --view 2 \\
        --output build/.../figure_3_x.pdf

When ``--view`` is set to 1, 2, or 3, the script extracts only the
matching ``<section>`` (and its sibling header) from the rendered HTML
before invoking the PDF writer; without ``--view`` the whole report is
exported. ``<details>`` collapsibles are forced open at export time
because some PDF engines do not honor browser interaction state.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_FORCE_DETAILS_OPEN_CSS = """
<style>
  details { display: block; }
  details summary { cursor: default; }
  details:not([open]) > *:not(summary) { display: revert; }
  details > *:not(summary) { display: revert !important; }
</style>
"""


def _slice_view(html: str, view: int) -> str:
    """Extract the section anchored at ``id="viewN"`` (and its containing
    header). Falls back to returning *html* unchanged when the anchor is
    absent."""
    anchor_pat = re.compile(
        rf'<h2[^>]*id=["\']view{view}["\'][^>]*>.*?(?=<h2[^>]*id=|<footer|</body>)',
        re.DOTALL | re.IGNORECASE,
    )
    m = anchor_pat.search(html)
    if not m:
        return html
    head_match = re.search(r"<head>.*?</head>", html, re.DOTALL | re.IGNORECASE)
    head = head_match.group(0) if head_match else "<head></head>"
    body_inner = m.group(0)
    return (
        f"<!DOCTYPE html><html>{head}<body>"
        f"{_FORCE_DETAILS_OPEN_CSS}"
        f"{body_inner}"
        f"</body></html>"
    )


def export_to_pdf(html_path: Path, pdf_path: Path, view: int | None) -> None:
    """Render *html_path* to *pdf_path*. If *view* is set, slice first."""
    try:
        import weasyprint  # type: ignore
    except ImportError as e:
        raise SystemExit(
            "weasyprint is required for PDF export. "
            "Install with: pip install -e '.[export]'"
        ) from e

    html = html_path.read_text()
    if view is not None:
        html = _slice_view(html, view)
    else:
        # Force details open even on full-document export
        html = html.replace("</head>", _FORCE_DETAILS_OPEN_CSS + "</head>", 1)

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    weasyprint.HTML(string=html, base_url=str(html_path.parent)).write_pdf(
        target=str(pdf_path)
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report", type=Path, required=True, help="path to coverage/index.html")
    p.add_argument(
        "--view",
        type=int,
        choices=[1, 2, 3],
        default=None,
        help="extract just this view (1, 2, or 3); omit for full report",
    )
    p.add_argument("--output", type=Path, required=True, help="output PDF path")
    args = p.parse_args(argv)

    if not args.report.exists():
        print(f"Error: report not found: {args.report}", file=sys.stderr)
        return 2
    export_to_pdf(args.report, args.output, args.view)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
