"""`space/DEPLOY.md` may only instruct an operator to set variables the code reads.

An operator follows the deploy guide literally. If the guide names a secret the
Space never reads, they will set it, see nothing happen, and have no way to tell
a configuration mistake from a broken build.

That is not hypothetical. Until 2026-09-08 the guide described
`UOFA_DEMO_SIGNING_KEY` as a second secret that "signs the decision" against
`keys/demo-reviewer.pub`. **No code has ever read it.** `space/pipeline.py`
defines `UOFA_ISSUER_SIGNING_KEY` and `UOFA_ISSUER_SIGNING_KEY_FILE` and nothing
else. The guide documented a decision signature the implementation deliberately
does not create, which is the most sensitive thing it could have been wrong
about: a service key standing in for a human reviewer is exactly what the
signing surface spec forbids.

This is the routing-defect shape one layer out, the same one
`tests/test_documented_model_ids.py` guards for model ids: **a documented
configuration that cannot work is the same defect as a setting that never gets
read.** Both look right in the artifact and fail only when someone follows them.

Historical notes are exempt. A dated correction has to be able to name the wrong
variable in order to record what was wrong, so blockquote lines are skipped.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEPLOY_DOC = REPO_ROOT / "space" / "DEPLOY.md"
SPACE_DIR = REPO_ROOT / "space"

_ENV_NAME = re.compile(r"UOFA_[A-Z0-9_]+")

# `UOFA_SPACE_LLM_` appears as a prefix in prose describing the family of
# UOFA_SPACE_LLM_* settings. It is not a variable anyone sets.
PROSE_PREFIXES = {"UOFA_SPACE_LLM_"}


def _names_the_code_reads() -> set[str]:
    """Every UOFA_* name appearing as a string literal in space/*.py."""
    found: set[str] = set()
    for py in sorted(SPACE_DIR.glob("*.py")):
        for m in re.finditer(r'"(UOFA_[A-Z0-9_]+)"', py.read_text(encoding="utf-8")):
            found.add(m.group(1))
    return found


def _names_the_doc_instructs() -> list[tuple[str, int]]:
    """UOFA_* names the guide tells an operator to set, with line numbers.

    Blockquote lines are skipped: a dated correction must be able to name the
    variable it is correcting.
    """
    out: list[tuple[str, int]] = []
    for n, line in enumerate(DEPLOY_DOC.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith(">"):
            continue
        for m in _ENV_NAME.finditer(line):
            name = m.group(0)
            if name in PROSE_PREFIXES:
                continue
            out.append((name, n))
    return out


def test_the_scan_finds_env_names_at_all():
    """Guard the guard: a regex that matches nothing would pass vacuously."""
    assert len(_names_the_doc_instructs()) >= 5
    assert len(_names_the_code_reads()) >= 5


def test_deploy_doc_only_names_variables_the_code_reads():
    code = _names_the_code_reads()
    bad = [(name, n) for name, n in _names_the_doc_instructs() if name not in code]
    assert not bad, (
        "space/DEPLOY.md instructs an operator to set variables no code reads:\n"
        + "\n".join(f"  DEPLOY.md:{n}  {name}" for name, n in bad)
        + "\n\nEither the code should read it, or the guide should stop asking "
          "for it. A secret nobody reads is indistinguishable from a broken "
          "deploy."
    )


def test_the_issuer_key_is_the_one_the_guide_documents():
    """The signing secret specifically, by name, both directions."""
    doc = DEPLOY_DOC.read_text(encoding="utf-8")
    instructed = {name for name, _ in _names_the_doc_instructs()}

    assert "UOFA_ISSUER_SIGNING_KEY" in instructed, (
        "the guide no longer names the issuer signing key an operator must set"
    )
    assert "UOFA_DEMO_SIGNING_KEY" not in instructed, (
        "UOFA_DEMO_SIGNING_KEY is back outside a historical note. No code reads "
        "it, and it previously claimed a decision signature the Space must not "
        "create."
    )
    assert "issuer seal" in doc.lower(), (
        "the guide must state that the Space applies an issuer seal only, so a "
        "reader cannot mistake a valid signature for an acceptance decision"
    )
