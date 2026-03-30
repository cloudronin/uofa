"""uofa validate — SHACL validation (and optional integrity check) on all example UofA files."""

from pathlib import Path

from uofa_cli.output import step_header, result_line, color
from uofa_cli.shacl_friendly import run_shacl, print_violations
from uofa_cli.integrity import verify_file
from uofa_cli import paths

HELP = "validate all examples against SHACL profiles"

_EXCLUDE_DIRS = {"templates", "starters"}


def add_arguments(parser):
    parser.add_argument("--dir", type=Path, help="directory to scan (default: examples/)")
    parser.add_argument("--verify", action="store_true",
                        help="also verify hash + signature integrity on each file")
    parser.add_argument("--pubkey", type=Path, help="ed25519 public key (default: keys/research.pub)")


def run(args) -> int:
    examples = args.dir or paths.examples_dir()
    if not examples.exists():
        raise FileNotFoundError(f"Examples directory not found: {examples}")

    step_header("SHACL validation: all examples")

    files = sorted(
        f for f in examples.rglob("*.jsonld")
        if not any(part in _EXCLUDE_DIRS for part in f.parts)
    )

    if not files:
        result_line("No .jsonld files found", False)
        return 1

    shacl = paths.shacl_schema()
    passed = 0
    failed = 0

    for f in files:
        conforms, violations = run_shacl(f, shacl)
        rel = f.relative_to(examples.parent) if examples.parent in f.parents else f
        result_line(str(rel), conforms)
        if conforms:
            passed += 1
        else:
            failed += 1
            print_violations(violations)

    print()
    total = passed + failed
    if failed == 0:
        result_line(f"All {total} example(s) conform", True)
    else:
        result_line(f"{failed}/{total} example(s) failed", False)

    # ── Optional integrity verification ───────────────────────
    if args.verify:
        step_header("Integrity verification: all examples")
        pubkey = args.pubkey or paths.default_pubkey()
        if not pubkey.exists():
            result_line("Public key not found", False, str(pubkey))
            return 1

        ctx = paths.context_file()
        v_passed = 0
        v_failed = 0

        for f in files:
            rel = f.relative_to(examples.parent) if examples.parent in f.parents else f
            try:
                hash_ok, sig_ok = verify_file(f, pubkey, ctx)
                ok = hash_ok and sig_ok
                detail = ""
                if not hash_ok:
                    detail = "hash mismatch"
                elif not sig_ok:
                    detail = "signature invalid"
                result_line(str(rel), ok, detail)
                if ok:
                    v_passed += 1
                else:
                    v_failed += 1
            except Exception as exc:
                result_line(str(rel), False, str(exc))
                v_failed += 1

        print()
        v_total = v_passed + v_failed
        if v_failed == 0:
            result_line(f"All {v_total} example(s) verified", True)
        else:
            result_line(f"{v_failed}/{v_total} example(s) failed integrity check", False)

        failed += v_failed

    return 0 if failed == 0 else 1
