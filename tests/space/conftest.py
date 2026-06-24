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
def assert_clean_state():
    """Assert a finished run left no temp dir and no /tmp debug file."""
    from space.pipeline import DEBUG_RESPONSE_FILE

    def _check(work_dir: Path | None = None):
        assert not DEBUG_RESPONSE_FILE.exists(), "extractor /tmp debug file was not scrubbed"
        if work_dir is not None:
            assert not work_dir.exists(), f"work_dir not torn down: {work_dir}"

    return _check
