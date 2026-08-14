"""The wheel's signing context is byte-identical to the checkout's.

`tests/test_context_pin.py` pins the context file so it cannot change silently.
This closes the other axis: the hosted Space runs a pip-installed wheel and
resolves `spec/context/v0.5.jsonld` from the bundled snapshot at
`uofa_cli/_data/repo/`, while anyone verifying from a git checkout resolves it
from the working tree. Same logical path, two files.

Since over 98% of a signature's hash preimage is that file's contents, a wheel
whose copy differed by one byte would produce packages that verify inside the
Space and fail everywhere else -- with no diagnostic beyond "Hash match: False".
The force-include config makes that unlikely; this proves it empirically rather
than by reading pyproject.toml.

Skipped when the build backend is unavailable (offline), matching
tests/interrogate/test_wheel_schema_reachable.py, which this mirrors.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from tests.test_context_pin import PINNED_CONTEXT_NAME, PINNED_CONTEXT_SHA256

REPO_ROOT = Path(__file__).resolve().parents[1]
WHEEL_CONTEXT_PATH = f"uofa_cli/_data/repo/spec/context/{PINNED_CONTEXT_NAME}"
WHEEL_DEMO_PUBKEY_PATH = "uofa_cli/_data/repo/keys/demo.pub"


@pytest.fixture(scope="session")
def built_wheel(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("wheel")
    try:
        subprocess.run(
            [sys.executable, "-m", "build", "--wheel", "--outdir", str(out)],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=900, check=True,
        )
    except Exception as exc:  # build backend / network unavailable
        pytest.skip(f"wheel build unavailable: {exc}")
    wheels = list(out.glob("*.whl"))
    if not wheels:
        pytest.skip("no wheel produced")
    return wheels[0]


def test_wheel_context_is_byte_identical_to_the_checkout(built_wheel):
    with zipfile.ZipFile(built_wheel) as zf:
        assert WHEEL_CONTEXT_PATH in zf.namelist(), (
            f"{WHEEL_CONTEXT_PATH} missing from the wheel: a pip-installed uofa "
            f"could not resolve the context it signs against."
        )
        wheel_digest = hashlib.sha256(zf.read(WHEEL_CONTEXT_PATH)).hexdigest()

    assert wheel_digest == PINNED_CONTEXT_SHA256, (
        "the wheel's signing context differs from the pinned checkout copy.\n"
        f"  pinned: {PINNED_CONTEXT_SHA256}\n"
        f"  wheel:  {wheel_digest}\n"
        "Packages signed by a wheel-based deployment would fail verification "
        "from a source checkout, reported only as a hash mismatch."
    )


def test_wheel_ships_the_demo_trust_anchor(built_wheel):
    """The hosted Space re-verifies what it signs, and every pack carries this
    key. Both need it present after a non-editable install."""
    with zipfile.ZipFile(built_wheel) as zf:
        assert WHEEL_DEMO_PUBKEY_PATH in zf.namelist()
        packed = zf.read(WHEEL_DEMO_PUBKEY_PATH)
    assert packed == (REPO_ROOT / "keys" / "demo.pub").read_bytes()


def test_wheel_ships_no_private_key(built_wheel):
    """A private key in a published wheel would be worse than one in git."""
    with zipfile.ZipFile(built_wheel) as zf:
        keys = [n for n in zf.namelist() if n.endswith(".key") or n.endswith(".pem")]
        pem_bodies = [n for n in zf.namelist()
                      if n.endswith(".pub") and b"PRIVATE KEY" in zf.read(n)]
    assert not keys, f"private key material in the wheel: {keys}"
    assert not pem_bodies, f"public key file containing a private key: {pem_bodies}"
