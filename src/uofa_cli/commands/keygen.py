"""uofa keygen — generate ed25519 keypair for signing UofA packages."""

from __future__ import annotations

from pathlib import Path

from uofa_cli.integrity import generate_keypair
from uofa_cli.output import result_line, info, error

HELP = "generate ed25519 keypair for signing"


def add_arguments(parser):
    parser.add_argument("path", type=Path, help="path for the private key (e.g., keys/my-project.key)")
    parser.add_argument("--force", action="store_true",
                        help="overwrite an existing keypair (every package signed "
                             "with the old key stops verifying)")


def run(args) -> int:
    try:
        key_path, pub_path = generate_keypair(args.path, force=args.force)
    except FileExistsError as exc:
        error(str(exc))
        return 2
    result_line("Keypair generated", True)
    info(f"Private key: {key_path}")
    info(f"Public key:  {pub_path}")
    info(f"Keep {key_path.name} private. Commit {pub_path.name} to your repo.")
    return 0
