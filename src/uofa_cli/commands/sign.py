"""uofa sign — sign a UofA evidence package with ed25519.

Synthetic adversarial samples are refused (v1.1 §10.2). The ``integrity``
helpers stay purely cryptographic; the refusal is policy, and it now lives in
``package_policy`` so that every signer — this command, the demo Space, any
future service — applies the same one. It used to be a private predicate here,
with a second, separately-written copy in ``verify.py``.
"""

from __future__ import annotations

from pathlib import Path

from uofa_cli import package_policy
from uofa_cli.integrity import sign_file
from uofa_cli.output import error, info, result_line, step_header

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

    try:
        package_policy.assert_signable(package_policy.load_doc(args.file))
    except package_policy.PackagePolicyError as exc:
        error(exc.reason)
        return 2

    # Explicit override only: resolve_context prefers the package's own
    # @context when the user did not name one.
    ctx = args.context
    step_header(f"Signing {args.file.name}")

    sha256_hex, sig_hex = sign_file(args.file, args.key, ctx, args.output)

    result_line("Signed", True)
    info(f"SHA-256: {sha256_hex}")
    info(f"Signature: {sig_hex[:32]}...")
    info(f"Sealed: {args.output or args.file}")
    return 0
