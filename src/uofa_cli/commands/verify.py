"""uofa verify — verify hash and signature of a UofA file."""

from pathlib import Path

from uofa_cli.integrity import verify_file
from uofa_cli.output import step_header, result_line
from uofa_cli import paths

HELP = "verify hash + ed25519 signature (C1 integrity)"


def add_arguments(parser):
    parser.add_argument("file", type=Path, help="UofA JSON-LD file to verify")
    parser.add_argument("--pubkey", type=Path, help="ed25519 public key (default: keys/research.pub)")
    parser.add_argument("--context", "-c", type=Path, help="JSON-LD context file")


def run(args) -> int:
    if not args.file.exists():
        raise FileNotFoundError(f"File not found: {args.file}")

    pubkey = args.pubkey or paths.default_pubkey()
    if not pubkey.exists():
        raise FileNotFoundError(f"Public key not found: {pubkey}")

    ctx = args.context or paths.context_file()
    step_header("C1: Integrity verification (hash + signature)")

    hash_ok, sig_ok = verify_file(args.file, pubkey, ctx)

    result_line("Hash match", hash_ok)
    result_line("Signature valid", sig_ok)

    return 0 if (hash_ok and sig_ok) else 1
