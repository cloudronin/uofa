"""A diagnostic on stdout is data corruption when stdout is a contract.

Caught by CI, not by this suite, and worth pinning here so the next one is not.

`rules --format json` has a machine-readable stdout: `site/scripts/check-counts.mjs`
runs it per example and `JSON.parse`s the result. When context resolution grew a
never-silent fallback note, that note was printed with `output.info` -- which
writes to stdout -- and two shipped examples that legitimately declare no
context started producing:

    check-counts: aero-cou1: stdout was not JSON: Unexpected token 'o',
    "    no context "... is not valid JSON

The behaviour was right and the channel was wrong. Never-silent is a property of
the message reaching a reader, not of which stream carries it: stderr is read by
humans and captured by logs, and does not sit inside somebody's parser.

The two aero examples are the fixture precisely because they declare no context
and are signed in that state -- so the fallback genuinely fires on them, and a
test using a package that declares one would prove nothing.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SNAPSHOT = REPO / "snapshots" / "example-counts.json"

pytestmark = pytest.mark.skipif(
    shutil.which("java") is None, reason="the rules engine needs java")


def _examples() -> list[tuple[str, str, str]]:
    if not SNAPSHOT.exists():
        return []
    data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    out = []
    for name, spec in data.items():
        if isinstance(spec, dict) and spec.get("file") and spec.get("pack"):
            out.append((name, spec["pack"], spec["file"]))
    return out


@pytest.mark.parametrize("name,pack,rel", _examples())
def test_rules_json_stdout_is_parseable(name, pack, rel):
    """Exactly what check-counts does, asserted here so CI is not the first to know."""
    path = REPO / rel
    if not path.exists():
        pytest.skip(f"{rel} not in this checkout")

    proc = subprocess.run(
        [sys.executable, "-m", "uofa_cli", "--pack", pack, "rules", str(path),
         "--format", "json"],
        capture_output=True, text=True, cwd=REPO)

    try:
        json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        first = proc.stdout.strip().splitlines()[:1]
        pytest.fail(
            f"{name}: stdout is not JSON ({exc}). Something wrote a diagnostic "
            f"to a stream a parser owns. First line: {first}")


@pytest.mark.parametrize("name,pack,rel", _examples())
def test_an_undeclared_context_is_still_reported_on_stderr(name, pack, rel):
    """The other half: moving the note must not silence it.

    A fix that satisfies the parser by dropping the message would trade one
    silent substitution for another, which is the failure the note exists to
    prevent.
    """
    path = REPO / rel
    if not path.exists():
        pytest.skip(f"{rel} not in this checkout")

    doc = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(doc.get("@context"), str):
        pytest.skip(f"{name} declares a context; no fallback to report")

    proc = subprocess.run(
        [sys.executable, "-m", "uofa_cli", "--pack", pack, "rules", str(path),
         "--format", "json"],
        capture_output=True, text=True, cwd=REPO)
    assert "context" in proc.stderr.lower(), (
        f"{name} declares no context and nothing said which one was used")
