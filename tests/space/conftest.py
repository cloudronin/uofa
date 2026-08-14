"""Shared fixtures for the Gap-Finder Space tests.

Puts the repo root on sys.path so `import space.*` resolves (the `space`
package lives at the repo root, outside the installed `uofa_cli` wheel).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Skip Java/Jena-dependent assertions when the engine jar isn't built.
JAVA_AVAILABLE = shutil.which("java") is not None
ENGINE_JAR = _REPO_ROOT / "src" / "weakener-engine" / "target" / "uofa-weakener-engine-0.1.0.jar"
needs_jar = pytest.mark.skipif(
    not (JAVA_AVAILABLE and ENGINE_JAR.exists()),
    reason="java + built weakener-engine JAR required",
)


@pytest.fixture
def text_corpus(tmp_path: Path) -> Path:
    """A tiny readable evidence dir (no PDF deps needed; mock ignores content)."""
    (tmp_path / "evidence.txt").write_text(
        "Credibility assessment evidence for a computational model.\n",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def demo_key_env(tmp_path_factory, monkeypatch):
    """Configure a throwaway demo issuer keypair for one test.

    The real demo private key is a deployment secret and is deliberately not in
    this repo, so tests cannot sign with it. They generate their own and
    re-point the trust anchor at the matching public half -- which exercises the
    whole mechanism (sign -> re-verify -> ship the key in the zip) without
    anyone ever committing a private key to make a test pass.

    Yields the public key path.
    """
    from uofa_cli import integrity, paths
    from space import pipeline

    key_dir = tmp_path_factory.mktemp("demo-key")
    key, pub = integrity.generate_keypair(key_dir / "demo.key")
    monkeypatch.setattr(paths, "demo_pubkey", lambda root=None: pub)
    monkeypatch.setenv(pipeline.SIGNING_KEY_FILE_ENV, str(key))
    monkeypatch.delenv(pipeline.SIGNING_KEY_ENV, raising=False)
    return pub


@pytest.fixture(autouse=True)
def _no_ambient_signing_key(monkeypatch, request):
    """Tests that do not ask for a key must not inherit one from the shell.

    Otherwise a developer with the demo key exported would see different
    behaviour from CI, and the unsigned-path assertions would quietly stop
    testing the unsigned path."""
    if "demo_key_env" in request.fixturenames:
        return
    from space import pipeline

    monkeypatch.delenv(pipeline.SIGNING_KEY_ENV, raising=False)
    monkeypatch.delenv(pipeline.SIGNING_KEY_FILE_ENV, raising=False)


@pytest.fixture(autouse=True)
def _no_ambient_hosted_inference(monkeypatch):
    """Tests must never reach a paid provider.

    A developer with TOGETHER_API_KEY (or the UOFA_SPACE_LLM_* vars) exported
    would otherwise see the UI tests make live network calls, and behave
    differently from CI. Clearing the declaration is enough: space_llm_config()
    returns None without a backend, which is the local path every test wants.
    """
    from space import llm_env

    for var in (llm_env.BACKEND_ENV, llm_env.MODEL_ENV,
                llm_env.BASE_URL_ENV, llm_env.KEY_ENV_ENV):
        monkeypatch.delenv(var, raising=False)
    try:
        from space import app
    except Exception:
        return   # gradio absent; the app-level tests are skipped anyway
    monkeypatch.setattr(app, "_LLM_CONFIG", None, raising=False)


@pytest.fixture
def assert_clean_state():
    """Assert a finished run left no temp dir and no /tmp debug file."""
    from space.pipeline import DEBUG_RESPONSE_FILE

    def _check(work_dir: Path | None = None):
        assert not DEBUG_RESPONSE_FILE.exists(), "extractor /tmp debug file was not scrubbed"
        if work_dir is not None:
            assert not work_dir.exists(), f"work_dir not torn down: {work_dir}"

    return _check
