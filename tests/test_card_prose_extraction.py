"""Parsing a card's reported evaluation into ValidationResult nodes.

The parser's whole job is to distinguish "the card stated this" from "the card
did not". Every Group-B rule fires on a property's ABSENCE, so a parser that
turns "not reported" into a present value silences the check that exists to
notice the gap -- the failure the Group-B layer was built to catch, arriving from
inside the extractor.

This is the prose-side twin of the raidex adapter's `"N/A"`-string rule. Same
discipline, different route: there a sentinel arrived as a JSON string, here it
arrives as something a language model wrote because the field was empty.
"""

from __future__ import annotations

import pytest

from uofa_cli.furnishers import card_prose

_OPTIONAL = (
    "hasUncertaintyQuantification", "nullBaselineStatement",
    "harnessDeterminismStatement", "samplingAccount",
    "confoundControlStatement", "claimedCOU",
)


def _one(**fields) -> str:
    body = "\n".join(f"{k}: {v}" for k, v in fields.items())
    return f"=== VALIDATION_RESULT ===\n{body}\n"


def _parse(response: str):
    return card_prose.parse(response, "https://example.org/m")


def test_a_bare_score_yields_a_node_with_no_optional_properties():
    """The common case: cards report a number and nothing that interprets it."""
    ev = _parse(_one(name="MMLU", metric_value="71.2", shot_count="5-shot"))
    assert len(ev.nodes) == 1
    node = ev.nodes[0]
    assert node["metricValue"] == 71.2
    assert node["evidenceSource"] == "reported"
    assert [p for p in _OPTIONAL if p in node] == []


@pytest.mark.parametrize("sentinel", [
    "N/A", "n/a", "none", "None", "not reported", "not stated", "unknown",
    "-", "--", "", "  ", "null", "tbd", "?", "not applicable",
])
def test_sentinels_become_omissions_not_values(sentinel):
    """Every way a model says "absent" must leave the property OFF the node.

    A node carrying `nullBaselineStatement: "not reported"` satisfies the rule's
    noValue() check and silences W-EV-NULL-04, reporting a gap as though it were
    filled.
    """
    ev = _parse(_one(name="MMLU", metric_value="71.2",
                     uncertainty=sentinel, null_baseline=sentinel,
                     harness_determinism=sentinel, sampling_account=sentinel,
                     confound_control=sentinel, claimed_cou=sentinel))
    assert len(ev.nodes) == 1
    present = [p for p in _OPTIONAL if p in ev.nodes[0]]
    assert present == [], f"sentinel {sentinel!r} became a value in {present}"


def test_a_genuine_statement_is_kept():
    ev = _parse(_one(name="GSM8K", metric_value="84.0",
                     uncertainty="+/- 0.4", null_baseline="chance is 0% (free-response)"))
    node = ev.nodes[0]
    assert node["hasUncertaintyQuantification"] is True
    assert "+/- 0.4" in node["uqMethod"], "the stated value must survive, not just a flag"
    assert node["nullBaselineStatement"].startswith("chance is 0%")


def test_a_statement_containing_a_sentinel_word_is_not_stripped():
    """"none of the runs used sampling" is a real determinism statement."""
    ev = _parse(_one(name="ARC", metric_value="70.6",
                     harness_determinism="none of the runs used sampling; greedy decoding"))
    assert "greedy decoding" in ev.nodes[0]["harnessDeterminismStatement"]


def test_a_block_without_a_score_is_skipped_not_emitted_with_a_null():
    """A node asserting "reported, value unknown" is a fabricated reading."""
    ev = _parse(_one(name="HellaSwag", metric_value=""))
    assert ev.nodes == []
    assert ev.skipped and ev.skipped[0]["reason"] == "no numeric score stated"


def test_duplicate_benchmarks_keep_the_first_and_record_the_rest():
    ev = _parse(_one(name="MMLU", metric_value="71.2") + _one(name="MMLU", metric_value="70.0"))
    assert len(ev.nodes) == 1 and ev.nodes[0]["metricValue"] == 71.2
    assert any(s.get("reason") == "duplicate block" for s in ev.skipped)


def test_extraction_notes_are_retained():
    """What the extractor could not resolve is part of the record, not noise."""
    ev = _parse("=== EXTRACTION_NOTES ===\nnotes: Four model columns; could not "
                "tell which is this variant.\n")
    assert ev.nodes == []
    assert ev.notes and "four model columns" in ev.notes[0].lower()


def test_nodes_carry_provenance_so_core_rules_do_not_misfire():
    """Without wasGeneratedBy, core's W-EP-02 reports "no provenance chain" about
    evidence that plainly has one -- a false finding, which is worse than a
    missed one because every other finding is priced off the reader's trust."""
    ev = _parse(_one(name="MMLU", metric_value="71.2"))
    activity = ev.nodes[0]["wasGeneratedBy"]
    assert activity["type"] == "prov:Activity"
    assert "model-card" in activity["activityType"]


def test_reported_and_furnished_are_distinguishable():
    """The two sources make different claims about the same subject, and
    W-EV-COR-09 and W-EV-DIV-07 both key on telling them apart."""
    from uofa_cli.furnishers import raidex
    reported = _parse(_one(name="MMLU", metric_value="71.2")).nodes[0]
    fetched = raidex.fetch_record(
        "", local_path="tests/fixtures/raidex/huggingface__google__gemma-3-27b-it.json")
    furnished = raidex.furnish(fetched.record, "https://example.org/m", "x").nodes[0]
    assert reported["evidenceSource"] == "reported"
    assert furnished.get("evidenceSource") == "furnished"
    assert reported["id"] != furnished["id"]


def test_the_prompt_forbids_inventing_values():
    """The prompt is the other half of the guarantee; the parser cannot catch a
    fabricated number that looks real."""
    text = card_prose.prompt_path().read_text()
    assert "{corpus}" in text
    for phrase in ["Leave the field EMPTY", "Do NOT infer", "already been sliced"]:
        assert phrase in text, f"prompt lost its {phrase!r} instruction"


# ── W-EV-SUB-08's subject distinction ───────────────────────────────────────
#
# The rule's grounding is configuration control. An open-weight model retrievable
# at a pinned revision IS configuration-controlled, so firing there was a false
# finding by the rule's own doctrine -- the same class as W-EP-02 reporting "no
# provenance" on evidence that had provenance. Whether a subject is pinnable is a
# fact about hosting, not about the evaluation prose, so no judge panel could
# have settled it; it had to be fixed in the body.

def test_a_pinned_subject_satisfies_the_version_guarantee():
    ev = _parse_pinned(_one(name="MMLU", metric_value="78.6"),
                       revision="005ad3404e59d6023443cb575daa05336842228a")
    node = ev.nodes[0]
    assert node["subjectVersionGuarantee"].startswith("005ad3404e"), (
        "an open-weight model at a pinned revision has an immutable identity")


def test_an_unpinnable_subject_carries_no_guarantee():
    """API-hosted subjects, and any card whose artifact cannot be pinned."""
    ev = _parse(_one(name="MMLU", metric_value="78.6"))
    assert "subjectVersionGuarantee" not in ev.nodes[0]


def _parse_pinned(response: str, revision: str):
    return card_prose.parse(response, "https://example.org/m", subject_revision=revision)
