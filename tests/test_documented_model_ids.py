"""Every model id this project documents must be one that can actually run.

**This is the routing-bug class, generalized.** `test_extract_prompt_routing`
pins that a delivered prompt is the *right* prompt, because a prompt that never
reaches the model is indistinguishable from a model that ignores it. The same
shape applies one layer out: **a documented configuration that cannot run is the
same defect as a prompt that never gets sent.** Both look correct in the
artifact and fail only when someone tries to use them.

The instance that produced this file: `claude-sonnet-5-2026` appeared in 43
places across 20 files -- README, four docs pages, the published website, the
SME review tooling, two `src/` docstrings, five test modules, and, worst,
`interpretation/degrade.py`'s user-facing error message. That id returns HTTP
404. The error message a user reaches *because their LLM is already broken*
prescribed a config that cannot run. Found 2026-08-15 while resolving the
frontier arm of `studies/model-selection`, where the declaration pinned the
documented string and every bundle failed.

**Hermetic by default.** The default test resolves nothing over the network --
this repo removed its last network dependency in the same week (see
`shacl_friendly._load_data_graph`) and re-adding one here to check model ids
would trade a documentation defect for a flake. Instead it pins documented ids
against `KNOWN_GOOD`, each entry carrying the date and status it was verified
at. The live check is opt-in via `UOFA_RUN_REAL_LLM=1`, matching the convention
the real-LLM e2e tests already use.

That split is the honest one: the cheap test catches *drift*, which is what
actually happened here, and the expensive test catches *a vendor retiring an
id*, which is the other way this breaks.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Model ids this project may document, each with the evidence for it.
#
#   claude-sonnet-5                           HTTP 200, verified 2026-08-15
#   meta-llama/Llama-3.3-70B-Instruct-Turbo   ran 3x as the model-selection
#                                             incumbent arm, 2026-08-15
#   Qwen/Qwen2.5-72B-Instruct                 ran 3x as family-72b, 2026-08-15
#   qwen3.5:4b                                bundled local model, installed by
#                                             `uofa setup`; ran as local-4b
#   llama3.3:70b                              an Ollama tag. Ollama ids are
#                                             whatever the user has pulled, so
#                                             there is no registry to check one
#                                             against -- listed as a documented
#                                             EXAMPLE, not as a verified id.
#   gpt-4o                                    OpenAI's published id
#
# `claude-sonnet-5-2026` is deliberately ABSENT: HTTP 404, verified 2026-08-15.
#
# `meta-llama/Llama-3.3-70B-Instruct` (no -Turbo) is also absent, and the docs
# that showed it were changed to -Turbo rather than the id being allowlisted.
# Together's model list returned 403 with the key available on 2026-08-16, so it
# could not be verified either way -- and an unverifiable id is exactly what
# this file exists to keep out of the docs. -Turbo has positive evidence behind
# it; the bare id has none. Documenting the one we measured is the whole point.
KNOWN_GOOD = {
    "claude-sonnet-5",
    "qwen3.5:4b",
    "llama3.3:70b",
    "gpt-4o",
    "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "Qwen/Qwen2.5-72B-Instruct",
}

# Files that record a BROKEN id on purpose, as dated history. History is not
# edited to make a test pass -- that would destroy the evidence the finding
# rests on, and the rule against it is why these are listed rather than fixed.
HISTORY_EXEMPT = {
    "studies/model-selection/DECLARATION.md",       # the declaration + its correction
    "dev/tools/scripts/model_selection.py",          # comment recording the 404
    "src/uofa_cli/interpretation/degrade.py",        # comment recording what it read until 2026-08-16
    "tests/test_documented_model_ids.py",            # this file's own docstring
}

# How a model id appears in a config example or a command line.
PATTERNS = (
    re.compile(r'model\s*=\s*"([^"]+)"'),
    re.compile(r"--explain-model[= ]+([^\s\\`'\"\]]+)"),
    re.compile(r"UOFA_EXPLAIN_MODEL=([^\s\\`'\"]+)"),
)

# `uofa --help` output in the CLI reference renders argparse usage lines like
# `[--explain-model EXPLAIN_MODEL]`. The metavar is a placeholder, not an id, and
# matching it produced four false positives on the first run of this file.
# Recognised by shape (SCREAMING_SNAKE) rather than by listing the four sites,
# so new --help output cannot reintroduce them.
_METAVAR = re.compile(r"^[A-Z][A-Z0-9_]*$")

DOC_GLOBS = ("README.md", "docs/**/*.md", "site/src/content/docs/**/*.md")


def _documented_ids() -> list[tuple[str, str, int]]:
    """Every (model_id, relative_path, line_no) a reader could copy-paste."""
    found: list[tuple[str, str, int]] = []
    paths: list[Path] = []
    for glob in DOC_GLOBS:
        paths.extend(REPO_ROOT.glob(glob))
    for path in sorted(set(paths)):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in HISTORY_EXEMPT:
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for pat in PATTERNS:
                for m in pat.finditer(line):
                    mid = m.group(1)
                    if _METAVAR.match(mid):
                        continue
                    found.append((mid, rel, n))
    return found


def test_the_scan_actually_finds_documented_model_ids():
    """Guard the guard: a scan that matches nothing would pass vacuously.

    §13 -- a check that cannot fail is not a check. If the doc format changes
    so `PATTERNS` stops matching, the real assertion below would go green while
    checking nothing, so the population is pinned as non-empty first.

    **The threshold is deliberately well below the current count.** A working
    tree sees ~20 ids; a fresh checkout sees ~10, because
    `site/src/content/docs/docs/` and `readme.md` are gitignored and generated
    from `docs/` by `sync-readmes.mjs` (docs/ is the single source of truth, so
    the site copies are not a second place to fix). Pinning at the observed
    count would make this fail whenever a documented example is legitimately
    removed. Five is enough to distinguish "the patterns still work" from
    "the patterns match nothing", which is the only thing this guard is for.
    """
    found = _documented_ids()
    assert len(found) >= 5, (
        f"only {len(found)} documented model ids found; the scan patterns have "
        "probably drifted from the docs' format and the real check below is "
        "now vacuous"
    )


def test_documented_model_ids_are_runnable():
    """No doc may show a model id that is known not to resolve."""
    bad = [(mid, rel, n) for mid, rel, n in _documented_ids()
           if mid not in KNOWN_GOOD]
    assert not bad, (
        "documentation shows model ids that are not known-good:\n"
        + "\n".join(f"  {rel}:{n}  {mid!r}" for mid, rel, n in bad)
        + "\n\nEither correct the id, or add it to KNOWN_GOOD with the date "
          "and HTTP status you verified it at."
    )


def test_the_degraded_path_prescribes_a_runnable_config():
    """The rescue path specifically -- it is read when things are already broken.

    Called out separately from the doc sweep because it is the highest-harm
    instance and the one a doc-only scan would miss: it lives in `src/`, is
    emitted at runtime, and reaches a user who is mid-failure.
    """
    from uofa_cli.interpretation.degrade import _standard_suggestions

    prescribed = [
        m.group(1)
        for s in _standard_suggestions()
        for m in re.finditer(r'model\s*=\s*"([^"]+)"', s.instructions or "")
    ]
    assert prescribed, (
        "no suggestion prescribes a model any more; either the rescue path "
        "changed shape or this pin is now checking nothing"
    )
    bad = [m for m in prescribed if m not in KNOWN_GOOD]
    assert not bad, (
        f"the degraded-path suggestion prescribes {bad!r}, which is not "
        "known-good. This string is handed to a user whose LLM is already "
        "failing, so a broken id here costs them a second debugging cycle."
    )


@pytest.mark.skipif(
    os.environ.get("UOFA_RUN_REAL_LLM") != "1",
    reason="set UOFA_RUN_REAL_LLM=1 to resolve documented model ids for real",
)
def test_documented_ids_resolve_against_the_provider():
    """Opt-in: catches a vendor retiring an id, which the hermetic pin cannot.

    Deliberately gated. The hermetic test above catches drift between docs and
    a verified list, which is the failure that actually occurred. This one
    catches the other direction and costs a network round trip, so it runs only
    when asked.
    """
    import anthropic  # noqa: PLC0415

    client = anthropic.Anthropic()
    for mid in sorted(m for m in KNOWN_GOOD if m.startswith("claude-")):
        client.models.retrieve(mid)  # raises NotFoundError on a dead id
