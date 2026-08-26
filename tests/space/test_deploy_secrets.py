"""The last gate before a public push.

`space/deploy_to_hf.py` uploads the whole `space/` tree to a PUBLIC HuggingFace
Space repo. The demo issuer's private key reaches that Space only as a settings
secret; a copy of it committed as a file, or sitting in a local `.env`, would be
published the moment CI ran.

DENY is a substring filter and a rename can slip past it, so `main()` carries an
independent hard refusal. These tests exercise that refusal directly rather than
trusting the two layers to agree.
"""

from __future__ import annotations

import pytest

pytest.importorskip("huggingface_hub")

from space import deploy_to_hf


class _Op:
    """Minimal stand-in for CommitOperationAdd (only the path is inspected)."""

    def __init__(self, path):
        self.path_in_repo = path


@pytest.mark.parametrize("path", [
    "space/demo.key",
    "keys/research.key",
    "space/signing.pem",
    "space/.env",
    "space/.env.production",
    "space/config/.env.local",
])
def test_secret_shaped_paths_are_refused(path):
    assert deploy_to_hf._secrets_in([_Op(path)]) == [path]


@pytest.mark.parametrize("path", [
    "space/app.py",
    "space/README.md",
    "keys/uofa-issuer.pub",
    "space/environment.md",
    "space/keyboard.py",
])
def test_ordinary_paths_are_allowed(path):
    """`environment.md` and `keyboard.py` both contain the substring 'env'/'key';
    the guard must match suffixes, not any occurrence."""
    assert deploy_to_hf._secrets_in([_Op(path)]) == []


def test_deny_list_covers_the_same_suffixes():
    """DENY filters during collection, _secrets_in refuses at the end. If they
    drift, the cheap filter stops catching what the hard gate is watching for."""
    for token in (".key", ".pem", ".env"):
        assert token in deploy_to_hf.DENY


def test_real_payload_carries_no_secrets():
    """The actual upload set for this checkout, not a synthetic one."""
    assert deploy_to_hf._secrets_in(deploy_to_hf.build_operations()) == []
