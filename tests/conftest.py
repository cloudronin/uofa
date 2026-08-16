"""Test-suite-wide fixtures.

Currently provides:
- `_isolate_explain_cache` (autouse): redirects the interpretation cache
  to a per-test tmp dir so cached LLM-result rows from one test never
  leak into another. Without this, tests that run identical mock prompts
  see cache hits and skip backend calls — surfacing as `len(calls) == 0`
  failures.

The fixture is opt-out by yielding without monkeypatching when the
cache module isn't importable (graceful — pre-Phase-N tests still work).
"""

from __future__ import annotations

import pathlib

import pytest


@pytest.fixture(autouse=True)
def _isolate_explain_cache(monkeypatch, tmp_path):
    """Redirect the interpretation cache to a per-test sqlite file.

    Autouse + scope=function (default) so every test gets a fresh DB.
    The override is on `default_db_path()`, so any code that constructs
    `ExplanationCache()` with no args picks up the tmp path.
    """
    try:
        # Use string-based monkeypatch so this still works if the module
        # is rewritten — and so we don't import-fail when the cache module
        # is absent (e.g. pre-Phase-N codepaths or smaller-test runs).
        monkeypatch.setattr(
            "uofa_cli.interpretation.cache.default_db_path",
            lambda: tmp_path / "explain.db",
        )
    except (AttributeError, ModuleNotFoundError):
        pass
    yield


_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_LOCAL_CONTEXT = _REPO_ROOT / "spec" / "context" / "v0.5.jsonld"


@pytest.fixture(autouse=True, scope="session")
def _resolve_jsonld_context_offline():
    """Serve the project's own JSON-LD @context from disk, never over HTTP.

    253 fixtures carry ``@context`` as
    ``https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.5.jsonld``,
    and rdflib fetches it for real on every parse. That made the suite depend
    on a third party being reachable, and it bit: under ``-n auto`` a run died
    with ``http.client.RemoteDisconnected`` when concurrent workers hit the
    same host. Serial runs hid it by fetching once per process and getting
    lucky.

    Three separate problems, one cause:

    - **Non-hermetic.** A network blip fails a test that asserts nothing about
      the network.
    - **Slow.** ~0.12s per cold parse, and `test_import_corpus.py` spawns a
      fresh subprocess per test, so it pays that ~246 times.
    - **A moving target.** The URL points at ``main``. A change to the context
      on ``main`` silently changes what every branch validates against,
      including branches cut before the change.

    The URL is imported from `excel_constants` rather than retyped, so this
    mapping cannot drift from the value the writer actually emits.

    **Any other remote context raises**, rather than falling back to the
    network. A new non-hermetic dependency should fail at the commit that adds
    it, naming the URL, instead of surfacing months later as an intermittent
    red -- §13's fail-loud rule, applied to the test harness itself.

    **This is a backstop, not the fix.** The real repair is in the CLI:
    `shacl_friendly._load_data_graph` and `derivations/runner` now resolve the
    context through `integrity.resolve_context`, which maps the published URL
    to the copy shipped under `spec/context/` (`uofa_cli/_data/repo/spec` in a
    wheel). That covers subprocess tests too -- verified by running a real
    `uofa shacl` with every socket blocked, which conforms; the pre-fix code
    path raises `URLError` under the same conditions.

    This fixture stays because it catches the case the CLI fix cannot: a test
    that constructs an rdflib Graph itself, or a *new* remote context added
    later. It fails loudly and names the URL rather than reaching the network.
    """
    import json

    from rdflib.plugins.shared.jsonld import context as _ctx

    from uofa_cli.excel_constants import CONTEXT_URL

    if not _LOCAL_CONTEXT.is_file():
        raise RuntimeError(
            f"local JSON-LD context missing at {_LOCAL_CONTEXT}; refusing to "
            "fall back to the network"
        )

    local_doc = json.loads(_LOCAL_CONTEXT.read_text(encoding="utf-8"))
    original = _ctx.source_to_json

    def _offline_source_to_json(source, *args, **kwargs):
        if isinstance(source, str) and source.startswith(("http://", "https://")):
            if source == CONTEXT_URL:
                return local_doc, None
            raise RuntimeError(
                f"test attempted to fetch a remote JSON-LD context: {source}. "
                "Vendor it under spec/context/ and map it in "
                "tests/conftest.py::_resolve_jsonld_context_offline, or use a "
                "relative @context path."
            )
        return original(source, *args, **kwargs)

    _ctx.source_to_json = _offline_source_to_json
    try:
        yield
    finally:
        _ctx.source_to_json = original


@pytest.fixture(scope="session")
def signing_keypair(tmp_path_factory):
    """A throwaway ed25519 keypair for tests that need *a* signer.

    The repo deliberately ships no private key, so tests must generate their
    own. Nothing here verifies against the repo's trust anchor
    (`keys/research.pub`) -- these tests only need a self-consistent pair, and
    any test that also runs `uofa check`/`verify` on the result must pass the
    matching `--pubkey` rather than falling back to the repo default.

    Session-scoped: generation is the only cost and no test mutates the key.
    Returns `(key_path, pub_path)`, the two halves side by side, so callers
    relying on `key.with_suffix('.pub')` resolve correctly.
    """
    from uofa_cli.integrity import generate_keypair

    return generate_keypair(tmp_path_factory.mktemp("signing") / "test-signing.key")


# ── the extracted corpus the pinning tests read ──────────────

_EXTRACTED_JSON = pathlib.Path(__file__).parent / "fixtures" / "extract_corpus" / "extracted_rows.json"


# Moved to `tests/extracted_corpus.py`. `from conftest import ...` is ambiguous
# -- `tests/space/conftest.py` registers under the same bare name -- and in a
# full run the wrong one won, so two tests that passed in isolation failed in CI
# with an ImportError. Re-exported here so nothing that reaches for them breaks.
from extracted_corpus import (  # noqa: E402,F401
    extracted_corpus_by_bundle,
    extracted_corpus_rows,
)