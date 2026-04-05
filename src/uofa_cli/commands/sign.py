"""uofa sign — sign a UofA evidence package with ed25519."""

from __future__ import annotations

from pathlib import Path

from uofa_cli.integrity import sign_file
from uofa_cli.output import step_header, result_line, info
from uofa_cli import paths

HELP = "sign (or re-sign) a UofA file"


def add_arguments(parser):
    parser.add_argument("file", type=Path, help="UofA JSON-LD file to sign")
    parser.add_argument("--key", "-k", type=Path, required=True, help="ed25519 private key (PEM)")
    parser.add_argument("--context", "-c", type=Path, help="JSON-LD context file")
    parser.add_argument("--output", "-o", type=Path, help="output path (default: overwrite input)")


def run(args) -> int:
    if not args.file.exists():
        raise FileNotFoundError(f"File not found: {args.file}")
    if not args.key.exists():
        raise FileNotFoundError(f"Private key not found: {args.key}. Generate one: uofa keygen {args.key}")

    ctx = args.context or paths.context_file()
    step_header(f"Signing {args.file.name}")

    sha256_hex, sig_hex = sign_file(args.file, args.key, ctx, args.output)

    result_line("Signed", True)
    info(f"SHA-256: {sha256_hex}")
    info(f"Signature: {sig_hex[:32]}...")
    info(f"Sealed: {args.output or args.file}")
    return 0
