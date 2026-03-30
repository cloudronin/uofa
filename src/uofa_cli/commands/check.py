"""uofa check — run the full C1+C2+C3 pipeline on a UofA file."""

from pathlib import Path

from uofa_cli.output import header, step_header, result_line, color
from uofa_cli.shacl_friendly import run_shacl, print_results
from uofa_cli.integrity import verify_file
from uofa_cli import paths

HELP = "full pipeline: SHACL + integrity + rules (C1+C2+C3)"


def add_arguments(parser):
    parser.add_argument("file", type=Path, help="UofA JSON-LD file to check")
    parser.add_argument("--pubkey", type=Path, help="ed25519 public key")
    parser.add_argument("--context", "-c", type=Path, help="JSON-LD context file")
    parser.add_argument("--rules", "-r", type=Path, help="path to .rules file")
    parser.add_argument("--skip-rules", action="store_true", help="skip the Jena rule engine (no Java required)")
    parser.add_argument("--build", action="store_true", help="auto-build the Jena JAR if missing")


def run(args) -> int:
    if not args.file.exists():
        raise FileNotFoundError(f"File not found: {args.file}")

    ctx = args.context or paths.context_file()
    results = {}

    # ── C2: SHACL ─────────────────────────────────────────────
    step_header("C2: SHACL profile validation")
    conforms, violations = run_shacl(args.file, paths.shacl_schema())
    print_results(conforms, violations)
    results["C2 SHACL"] = conforms

    # ── C1: Integrity ─────────────────────────────────────────
    step_header("C1: Integrity verification (hash + signature)")
    pubkey = args.pubkey or paths.default_pubkey()
    if pubkey.exists():
        hash_ok, sig_ok = verify_file(args.file, pubkey, ctx)
        result_line("Hash match", hash_ok)
        result_line("Signature valid", sig_ok)
        results["C1 Integrity"] = hash_ok and sig_ok
    else:
        result_line("Integrity check", False, f"public key not found: {pubkey}")
        results["C1 Integrity"] = False

    # ── C3: Rules ─────────────────────────────────────────────
    import sys
    sys.stdout.flush()
    if args.skip_rules:
        results["C3 Rules"] = None
    else:
        from uofa_cli.commands import rules as rules_mod
        import argparse
        rules_args = argparse.Namespace(
            file=args.file,
            rules=args.rules,
            context=args.context,
            build=args.build,
            raw=False,
        )
        try:
            rc = rules_mod.run(rules_args)
            results["C3 Rules"] = (rc == 0)
        except FileNotFoundError as exc:
            result_line("Rule engine", False, str(exc).split("\n")[0])
            results["C3 Rules"] = False

    # ── Summary ───────────────────────────────────────────────
    header(f"Summary: {args.file.name}")
    all_ok = True
    for label, ok in results.items():
        if ok is None:
            result_line(label, True, "skipped")
        else:
            result_line(label, ok)
            if not ok:
                all_ok = False

    return 0 if all_ok else 1
