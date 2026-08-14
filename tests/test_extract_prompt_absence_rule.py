"""Absence of evidence must not be reported as evidence.

Found during the C3 hosted-inference spike. Given a shopping list as evidence,
Llama-3.3-70B returned all 13 vv40 factors with `status: assessed` while its own
rationales said "No evidence of software quality assurance found in the provided
documents." The status is what drives the completeness math, so the readout came
out as:

    no weakeners fired; 13 of 13 credibility factors assessed.

A shopping list scored a perfect credibility assessment. The bundled qwen3.5:4b
did not do this, so it was a regression the model swap would have introduced.

The rule already existed in the prompts, buried in a bullet list well below the
FACTOR block spec it governed; the model followed the spec and skimmed the
bullets. The fix states the test at the point of use, in terms of the exact
contradiction observed.

These tests guard the prompt text. The live behaviour they exist because of is
only reachable with a real model, so it lives in the spike harness rather than
here (running it in CI would mean an API key and per-run cost). What CI can
guarantee is that the rule does not get edited away.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from uofa_cli import paths

PROMPTS = [
    "packs/vv40/prompts/vv40_extract_prompt.txt",
    "packs/nasa-7009b/prompts/nasa_7009b_extract_prompt.txt",
    "packs/model-credibility/prompts/model_credibility_extract_prompt.txt",
]


def _text(rel: str) -> str:
    return (paths.find_repo_root() / rel).read_text(encoding="utf-8")


@pytest.mark.parametrize("rel", PROMPTS)
def test_prompt_states_the_absence_rule(rel):
    body = _text(rel)
    assert "claim about the CORPUS" in body, (
        f"{rel} lost the status/absence rule. Without it a model can mark every "
        f"factor assessed while its rationale reports no evidence, and a corpus "
        f"of unrelated documents scores as fully evidenced."
    )
    assert "MUST be `not-assessed`" in body


@pytest.mark.parametrize("rel", PROMPTS)
def test_absence_rule_sits_with_the_field_it_governs(rel):
    """It was already stated, and ignored, when it lived 14 lines away among
    eight other bullets. Proximity is the fix, so proximity is what is pinned."""
    body = _text(rel)
    lines = body.splitlines()
    status_line = next(i for i, l in enumerate(lines) if l.startswith("status: assessed"))
    rule_line = next(i for i, l in enumerate(lines) if "claim about the CORPUS" in l)
    assert 0 < rule_line - status_line <= 3, (
        f"{rel}: the absence rule drifted {rule_line - status_line} lines from the "
        f"`status:` field it governs. It was ignored at that distance before."
    )


@pytest.mark.parametrize("rel", PROMPTS)
def test_prompt_names_the_contradiction_not_just_the_rule(rel):
    """'Set not-assessed when there is no evidence' was already present and did
    not work. What changed the behaviour was naming the specific contradiction:
    a rationale reporting absence beside an assessed status."""
    body = _text(rel)
    assert "contradiction" in body.lower()
    assert "absent, not found" in body


def test_scoped_out_is_distinguished_from_silence():
    """Packs offering `scoped-out` must not let it absorb 'nothing was said'.
    Deliberate exclusion is a claim; silence is the absence of one."""
    for rel in PROMPTS:
        body = _text(rel)
        if "scoped-out" not in body:
            continue
        assert "different claim from silence" in body, (
            f"{rel} offers scoped-out without distinguishing it from silence"
        )
