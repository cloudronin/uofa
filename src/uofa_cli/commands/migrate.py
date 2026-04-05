"""uofa migrate — upgrade UofA JSON-LD files from v0.3 to v0.4."""

from __future__ import annotations

import json
from pathlib import Path

from uofa_cli.output import step_header, info, result_line, error

HELP = "migrate UofA files from v0.3 to v0.4"


def add_arguments(parser):
    parser.add_argument("file", type=Path, help="UofA JSON-LD file to migrate")
    parser.add_argument("--from", dest="from_ver", default="v0.3",
                        help="source version (default: v0.3)")
    parser.add_argument("--to", dest="to_ver", default="v0.4",
                        help="target version (default: v0.4)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print changes without modifying the file")


def run(args) -> int:
    if not args.file.exists():
        raise FileNotFoundError(f"File not found: {args.file}")

    step_header(f"Migrating {args.file.name} from {args.from_ver} to {args.to_ver}")

    with open(args.file) as f:
        doc = json.load(f)

    changes = 0

    # 1. Update @context path
    ctx = doc.get("@context", "")
    if isinstance(ctx, str) and "v0.3" in ctx:
        new_ctx = ctx.replace("v0.3", "v0.4")
        doc["@context"] = new_ctx
        info(f"  @context: {ctx}")
        info(f"        --> {new_ctx}")
        changes += 1

    # 2. Add factorStandard to each CredibilityFactor
    factors = doc.get("hasCredibilityFactor", [])
    if not isinstance(factors, list):
        factors = [factors]

    factor_count = 0
    for factor in factors:
        if isinstance(factor, dict) and "factorStandard" not in factor:
            factor["factorStandard"] = "ASME-VV40-2018"
            factor_count += 1

    if factor_count > 0:
        changes += factor_count
        info(f"  Added factorStandard to {factor_count} CredibilityFactor(s)")

    if changes == 0:
        result_line("Migration", True, "file already at v0.4 — no changes needed")
        return 0

    if args.dry_run:
        info(f"\n  Dry run: {changes} change(s) would be applied. File not modified.")
        return 0

    # Write migrated file
    with open(args.file, "w") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write("\n")

    result_line("Migration", True, f"{changes} change(s) applied")

    # Warn about invalidated signature
    if doc.get("hash") and not doc["hash"].endswith("0" * 64):
        from uofa_cli.output import color
        info(f"  {color('Warning:', 'yellow')} Content modified — existing hash/signature are now invalid.")
        info(f"  Re-sign with: uofa sign {args.file} --key YOUR_KEY")

    return 0
