#!/usr/bin/env python3
"""Does a package validate, and how much of it was READ — with a null control.

Every other metric in this project carries a null model. This one did not, and
its absence let two acceptance tables ship that were unreachable by construction:
one required fabricating a field its own R4 forbade, the next required a field
its own harness left absent. **An empty extractor scored beside a real one makes
that obvious immediately**, which is the entire argument for this file.

## The three rows

* **model** / **keyless** — real extractions
* **null** — an extractor that reads nothing and emits nothing, through the SAME
  import, signing and validation path

The null must fail. Minimal requires `bindsRequirement`, `hasValidationResult`
and `hasDecisionRecord`, and no run-context default supplies any of them. If the
null ever validates, something downstream is inventing content and every figure
above it is measuring that instead of the extractors.

## Why provenance is printed next to validity

A conforming package says nothing about how much of it was read. Three separate
failures on 2026-08-08 looked exactly like a clean pass: one validated on an
assessor the model invented, one on the template's help text, one via a warned
auto-synthesis. `field provenance` is what tells them apart, so it is reported on
the same line as the verdict rather than somewhere a reader has to go looking.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import subprocess
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "src"))


def null_workbook(out: pathlib.Path) -> pathlib.Path:
    """A workbook from an extractor that read nothing. The control."""
    from uofa_cli.excel_writer import write_extraction
    from uofa_cli.llm_extractor import ExtractionResult

    write_extraction(ExtractionResult(model_used="null-control"),
                     None, out, "vv40")
    return out


def import_and_check(xlsx: pathlib.Path, out: pathlib.Path) -> dict:
    r = subprocess.run(
        [sys.executable, "-m", "uofa_cli", "import", str(xlsx), "-o", str(out),
         "--sign", "--key", str(_ROOT / "keys" / "research.key"), "--check"],
        capture_output=True, text=True, cwd=_ROOT)
    text = r.stdout + r.stderr
    prov = {}
    if out.exists():
        try:
            blob = json.loads(out.read_text())
            node = blob if "fieldProvenance" in blob else next(
                (n for n in (blob.get("@graph") or []) if isinstance(n, dict)
                 and "fieldProvenance" in n), {})
            prov = collections.Counter((node.get("fieldProvenance") or {}).values())
            profile = str(node.get("conformsToProfile", "")).split("#")[-1]
        except (OSError, ValueError):
            profile = ""
    else:
        profile = ""
    return {
        "imported": out.exists(),
        "c2": "✓ C2 SHACL" in text,
        "profile": profile,
        "extracted": prov.get("extracted", 0),
        "run_context": prov.get("run-context", 0),
        "defaulted": prov.get("defaulted", 0) + prov.get("derived", 0),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workbooks", type=pathlib.Path, nargs="*", default=[],
                    help="extraction workbooks to score, as name=path")
    ap.add_argument("--tmp", type=pathlib.Path, required=True)
    args = ap.parse_args()

    args.tmp.mkdir(parents=True, exist_ok=True)
    rows = [("null", null_workbook(args.tmp / "null.xlsx"))]
    for spec in args.workbooks:
        name, _, path = str(spec).partition("=")
        rows.append((name, pathlib.Path(path)))

    print("\nPackage validity, with a null control\n")
    print(f"  {'extractor':12s}{'imports':>9s}{'C2':>5s}{'profile':>10s}"
          f"{'extracted':>11s}{'run-ctx':>9s}{'defaulted':>11s}")
    for name, xlsx in rows:
        if not xlsx.exists():
            print(f"  {name:12s}{'(no workbook)':>9s}")
            continue
        m = import_and_check(xlsx, args.tmp / f"{name}.jsonld")
        print(f"  {name:12s}{('yes' if m['imported'] else 'NO'):>9s}"
              f"{('✓' if m['c2'] else '✗'):>5s}{m['profile'][:9]:>10s}"
              f"{m['extracted']:>11d}{m['run_context']:>9d}{m['defaulted']:>11d}")

    print("\n  The null reads nothing. If its C2 is ✓, something downstream is")
    print("  inventing content and every row above it measures that instead of")
    print("  the extractor. 'extracted' is the only column describing the")
    print("  document; a package validating on run-context alone has been")
    print("  validated on facts about the run, not about the evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
