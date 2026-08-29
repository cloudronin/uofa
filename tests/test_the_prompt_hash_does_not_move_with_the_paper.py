"""`Prompt hash` must identify the instructions, not the paper.

Every package this product has ever emitted carries `Prompt hash: _not
recorded_`, and every gate every run has cleared, it cleared with the field
blank. The comparability guard reports that state as UNANSWERABLE rather than as
a match — two runs that cannot answer are not two runs that agree — and it is
what gates the C-series: a rate over runs that cannot be shown to share a prompt
is a rate over nothing in particular.

It was found from the other side too. T-8, an unsteered stranger with no access
to any of this reasoning, read its own run log after extraction, saw `Prompt
hash: "awaiting the extraction"`, and filed it as an escalation.

**The scoping is the whole design.** A digest over the assembled prompt moves
with the source document: two runs given identical instructions on two papers
would report different prompts, and the only pair that could ever match is two
runs on the same paper — which is the one comparison a prompt identity is not
needed for. Digesting the instruction half answers the question the field is
named for: were these two extractions told to do the same thing?
"""
from __future__ import annotations

import hashlib

import pytest

from uofa_cli.llm_extractor import (
    ExtractionResult,
    build_prompt,
    prompt_instructions,
    prompt_sha256,
)

PACK = "nasa-7009b"
CORPUS_A = "=== SOURCE: johnson-2020.pdf ===\n[p.7] The model was calibrated.\n"
CORPUS_B = "=== SOURCE: entirely-different.pdf ===\n[p.1] Nothing alike.\n" * 40


@pytest.fixture
def selfcontained(tmp_path):
    p = tmp_path / "prompt.txt"
    p.write_text("Extract the factors.\n\n{corpus}\n\nReturn JSON.", encoding="utf-8")
    return p


@pytest.fixture
def legacy(tmp_path):
    p = tmp_path / "legacy.txt"
    p.write_text("Extract the factors. No placeholder here.", encoding="utf-8")
    return p


# ── the property the field exists for ────────────────────────────────────────

@pytest.mark.parametrize("shape", ["selfcontained", "legacy"])
def test_the_hash_is_the_same_for_two_different_papers(shape, request):
    """The defect this whole field would have had, on both prompt shapes."""
    path = request.getfixturevalue(shape)
    assert build_prompt(CORPUS_A, path, PACK) != build_prompt(CORPUS_B, path, PACK), \
        "this fixture's two corpora are not actually different"
    assert prompt_sha256(path, PACK) == prompt_sha256(path, PACK)

    digest_a = hashlib.sha256(
        build_prompt(CORPUS_A, path, PACK).encode("utf-8")).hexdigest()
    digest_b = hashlib.sha256(
        build_prompt(CORPUS_B, path, PACK).encode("utf-8")).hexdigest()
    assert digest_a != digest_b, "the naive digest is corpus-sensitive, as expected"
    assert prompt_sha256(path, PACK) not in (digest_a, digest_b), \
        "the recorded hash is a digest of the assembled prompt, so it moves with " \
        "the paper and cannot answer 'same prompt'"


@pytest.mark.parametrize("shape", ["selfcontained", "legacy"])
def test_the_hash_moves_when_the_instructions_move(shape, request):
    """The other half. A constant would satisfy the test above."""
    path = request.getfixturevalue(shape)
    before = prompt_sha256(path, PACK)
    path.write_text(path.read_text(encoding="utf-8").replace(
        "Extract the factors", "Extract the factors CAREFULLY"), encoding="utf-8")
    assert prompt_sha256(path, PACK) != before


def test_no_corpus_text_survives_into_the_digested_string(selfcontained, legacy):
    """Read directly, rather than inferred from two hashes being equal."""
    for path in (selfcontained, legacy):
        text = prompt_instructions(path, PACK)
        for marker in ("johnson-2020.pdf", "calibrated", "entirely-different.pdf"):
            assert marker not in text, \
                f"{marker} reached the instruction half from a corpus"


def test_the_instructions_are_not_a_second_copy_of_the_assembly(selfcontained):
    """`prompt_instructions` is `build_prompt("")`, so the two cannot drift.

    Pinned because the tempting implementation — re-joining the pack prompt and
    the schema by hand — is a duplicate of `build_prompt`'s body that goes stale
    the first time the assembly changes, silently, in the direction of a hash
    that no longer describes what was sent.
    """
    assert prompt_instructions(selfcontained, PACK) == \
        build_prompt("", selfcontained, PACK)


def test_a_missing_prompt_file_still_yields_a_digest(tmp_path):
    """`iso42001`, `surrogate` and `disposition` carry no prompt. A run with no
    pack prompt has instructions all the same — the schema half — and a run log
    that says `_not recorded_` would be indistinguishable from today's gap."""
    missing = tmp_path / "nope.txt"
    assert not missing.exists()
    digest = prompt_sha256(missing, PACK)
    assert len(digest) == 64 and int(digest, 16) >= 0


# ── it reaches the artifact ──────────────────────────────────────────────────

def test_the_result_carries_the_field():
    assert ExtractionResult().prompt_sha256 == "", \
        "the default must be empty, so an unset hash is legible as unrecorded " \
        "rather than as a hash of nothing"


def test_extract_stamps_the_hash_beside_the_model(monkeypatch, selfcontained):
    """The run log's pins travel together or the comparability guard reports
    UNANSWERABLE on a run that could have answered."""
    from uofa_cli import llm_extractor as X

    monkeypatch.setattr(X, "_call_and_parse_with_retry",
                        lambda *a, **k: {"assessment_summary": {}})
    monkeypatch.setattr(X, "_save_debug_response", lambda *a, **k: None)

    class _Corpus:
        chunks: list = []
        total_tokens = 10
        file_manifest: list = []
        warnings: list = []

    result = X.extract(_Corpus(), "some/model", PACK,
                       pack_prompt_path=selfcontained, token_budget=24000)
    assert result.model_used == "some/model"
    assert result.prompt_sha256 == prompt_sha256(selfcontained, PACK)


# ── the consumer can only read what the CLI prints ──────────────────────────

def test_the_cli_prints_the_hash_it_actually_used():
    """Credenza reads the run log's facts from this stdout and never from the
    configuration it passed in — `Extraction.model` is "read from the CLI's own
    output, never from the configuration that was passed in", because "writing
    what we asked for when we cannot tell what answered is the exact defect A-3
    exists to prevent". The prompt is the same kind of fact.

    So the line must come off `result`, not off a local recomputation of what
    the command believes it sent.
    """
    import inspect

    from uofa_cli.commands import extract_cmd

    body = inspect.getsource(extract_cmd.run)
    assert "result.prompt_sha256" in body, \
        "the CLI does not print the hash, so no consumer can record one"
    assert "Prompt sha256:" in body, \
        "the printed label moved; credenza parses it out of stdout"


def test_the_keyless_path_claims_no_prompt():
    """It sends none. A hash there would describe instructions that do not
    exist, which is the overclaim the sentinel discipline exists to prevent."""
    import inspect

    from uofa_cli.commands import extract_cmd

    body = inspect.getsource(extract_cmd.run)
    guard = body.index("if result.prompt_sha256:")
    keyless = body.index("Extracting without a model (keyless)")
    assert keyless < guard, "the keyless branch now reaches the hash line"
    assert 'model = "keyless"' in body
