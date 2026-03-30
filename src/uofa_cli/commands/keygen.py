"""uofa keygen — generate ed25519 keypair for signing UofA packages."""

from pathlib import Path

from uofa_cli.integrity import generate_keypair
from uofa_cli.output import result_line, info

HELP = "generate ed25519 keypair for signing"


def add_arguments(parser):
    parser.add_argument("path", type=Path, help="path for the private key (e.g., keys/my-project.key)")


def run(args) -> int:
    key_path, pub_path = generate_keypair(args.path)
    result_line("Keypair generated", True)
    info(f"Private key: {key_path}")
    info(f"Public key:  {pub_path}")
    info(f"Keep {key_path.name} private. Commit {pub_path.name} to your repo.")
    return 0
