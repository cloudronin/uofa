"""uofa sign — sign a UofA evidence package with ed25519.

Synthetic adversarial samples are refused here at command layer. The
``integrity.sign_file`` helper stays purely cryptographic; refusal is a
command-level policy (v1.1 §10.2).
"""

from __future__ import annotations

import json
from pathlib import Path

from uofa_cli.integrity import sign_file
from uofa_cli.output import error, info, result_line, step_header
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
        raise FileNotFoundError(
            f"Private key not found: {args.key}. Generate one: uofa keygen {args.key}"
        )

    if _is_synthetic(args.file):
        error(
            "refusing to sign a synthetic adversarial sample. "
            "Synthetic packages are not valid evidence and cannot be signed."
        )
        return 2

    ctx = args.context or paths.context_file()
    step_header(f"Signing {args.file.name}")

    sha256_hex, sig_hex = sign_file(args.file, args.key, ctx, args.output)

    result_line("Signed", True)
    info(f"SHA-256: {sha256_hex}")
    info(f"Signature: {sig_hex[:32]}...")
    info(f"Sealed: {args.output or args.file}")
    return 0


def _is_synthetic(path: Path) -> bool:
    try:
        doc = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(doc, dict):
        return False
    if doc.get("synthetic") is True:
        return True
    type_val = doc.get("type") or doc.get("@type") or []
    if isinstance(type_val, str):
        type_val = [type_val]
    return "uofa:SyntheticAdversarialSample" in type_val
