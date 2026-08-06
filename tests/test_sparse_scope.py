"""The sparse scope sampler: omission is structural, not requested.

Sparse bundles exist to stop `control_constant_list` -- a function that prints
the standard's checklist and reads nothing -- from being unbeatable. Its
precision is 1 minus the corpus omission rate, so an under-omitting corpus makes
detection unmeasurable.

Asking the model to omit produced 8-21% across five rounds of increasingly
emphatic wording, because Step A is never given the factor list: it was being
asked to subtract a fraction from a set it held only in its head. These tests
pin the properties of naming the *included* set instead.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))

from generate_extract_corpus import (  # noqa: E402
    SOURCE_GENERATION_PROMPT,
    _SPARSE_COVERAGE,
    sparse_scope,
)

VV40 = [f"vv40_factor_{i}" for i in range(13)]
NASA = [f"nasa_factor_{i}" for i in range(19)]

# The downstream guard in _validate_full_schema rejects a sparse bundle that
# omits less than this. Sampling must clear it with room for a writer that
# drifts and mentions one extra topic.
GUARD_MIN_OMISSION = 0.30


@pytest.mark.parametrize("factors", [VV40, NASA], ids=["vv40", "nasa"])
def test_omission_clears_the_guard_with_margin(factors):
    scope = sparse_scope(factors, "bundle_x_001")
    omission = 1 - len(scope) / len(factors)
    assert omission >= GUARD_MIN_OMISSION + 0.10, (
        f"omission {omission:.0%} leaves no margin over the {GUARD_MIN_OMISSION:.0%} "
        f"guard; one drifted mention would fail the bundle"
    )


@pytest.mark.parametrize("factors", [VV40, NASA], ids=["vv40", "nasa"])
def test_scope_is_a_subset_and_never_empty(factors):
    scope = sparse_scope(factors, "bundle_x_001")
    assert scope, "a document with nothing in scope has nothing to write"
    assert set(scope) <= set(factors)
    assert len(scope) == len(set(scope)), "a repeated factor would overstate coverage"


def test_deterministic_for_a_given_bundle():
    # Regenerating one bundle must reproduce the same document scope, or the
    # ground truth on disk stops describing what the generator would now write.
    assert sparse_scope(VV40, "bundle_a") == sparse_scope(VV40, "bundle_a")


def test_varies_across_bundles():
    # A fixed subset would leave the same factors unrepresented corpus-wide,
    # and any extractor would be scored only on the half that always appears.
    distinct = {tuple(sparse_scope(VV40, f"bundle_{i}")) for i in range(20)}
    assert len(distinct) > 10, f"only {len(distinct)} distinct scopes in 20 bundles"


def test_every_factor_appears_in_scope_somewhere():
    counts = Counter()
    for i in range(48):
        counts.update(sparse_scope(VV40, f"bundle_vv40_{i:03d}"))
    never = [f for f in VV40 if not counts[f]]
    assert not never, f"factors no sparse bundle ever discusses: {never}"


def test_step_b_is_not_told_the_scope():
    """Ground truth must record what is on the page, not what was intended.

    If the scope leaked into the ground-truth prompt, `expected_status` would
    encode the generator's intent and the >=30%-absent guard would be checking
    the sampler against itself rather than checking whether the writer complied.
    """
    from generate_extract_corpus import GROUND_TRUTH_EXTRACTION_PROMPT

    assert "scope_block" not in GROUND_TRUTH_EXTRACTION_PROMPT
    assert "Topics in scope" not in GROUND_TRUTH_EXTRACTION_PROMPT


def test_non_sparse_prompt_carries_no_scope_section():
    rendered = SOURCE_GENERATION_PROMPT.format(
        standard="vv40", domain="cfd", quality="complete",
        format="report-md", scope_block="",
    )
    assert "Topics in scope" not in rendered, (
        "a complete bundle must discuss the whole checklist"
    )


def test_coverage_constant_is_below_the_guard_complement():
    # _SPARSE_COVERAGE and the guard are set in different places; this fails
    # loudly if someone raises coverage past what the guard will accept.
    assert _SPARSE_COVERAGE <= 1 - GUARD_MIN_OMISSION - 0.10
