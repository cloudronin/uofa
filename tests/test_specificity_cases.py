"""Integrity of the specificity case set (`tests/fixtures/specificity/cases.json`).

The cases come from the A16 enrichment stratum and test the two directions the
gold set cannot:

  expected=absent   Characteristic language present, property absent. If
                    extraction reads "Within ±1 Level" as uncertainty it
                    populates the field and SILENCES a warranted weakener.
  expected=present  The property is genuinely stated. A rule firing here accuses
                    a published card of an omission it did not commit.

**These tests do not run the extractor.** The prose path is backend-required and
has no production caller yet, so asserting extractor behaviour would mean
half-wiring it here. What they do assert is that the case set is still capable of
testing it -- an excerpt that lost its lure, or an expectation that drifted
from the label it copies, is a fixture that has stopped measuring anything while
continuing to pass. That failure mode is the reason this file exists.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))

CASES_PATH = _REPO / "tests/fixtures/specificity/cases.json"
ENRICHED_PROPERTIES = {"P2_uncertainty", "P5_null_baseline", "P6_claimed_cou",
                       "P7_confound_control"}
# Licence discipline: excerpts are quoted spans, not redistributed cards. The
# corpus is CC-BY-4.0 (A17.3) and card_id attributes each one, but a "minimal
# span" that grew to a whole card is no longer minimal.
MAX_EXCERPT_CHARS = 1200


@pytest.fixture(scope="module")
def payload() -> dict:
    if not CASES_PATH.exists():
        pytest.skip("specificity cases not built")
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def cases(payload) -> list[dict]:
    return payload["cases"]


def test_every_absent_case_still_carries_its_lure(cases):
    """The lure IS the test. An excerpt without it exercises nothing.

    This already caught two real bugs: matched_pattern was split on `|` while the
    patterns themselves contain `|`, and the label sheet truncates eval_sections
    at 30,000 chars so espnet config dumps carried their match past the cut.
    Both produced excerpts that looked fine and tested nothing.
    """
    missing = [c["card_id"] for c in cases
               if c["expected"] == "absent"
               and c["matched_text"] not in c["excerpt"]]
    assert not missing, f"absent cases whose excerpt lost the lure: {missing}"


def test_hard_assert_is_confined_to_mechanical_absences(cases):
    """Only mechanically-determined cases may ever fail a test.

    Labels are machine-drafted. "Within ±1 Level is a tolerance band" is a fact
    about the text; "this card states a context of use" is a clause reading.
    Promoting a reading into hard_assert would let a drafted judgment fail the
    build -- including the four 2026-08-11 flips, which rest on a clause and
    correctly did not earn it.
    """
    for c in cases:
        if not c["hard_assert"]:
            continue
        assert c["expected"] == "absent", (
            f"{c['card_id']}: hard_assert on a `present` case -- that is a "
            "judgment about what the card states, not a fact about its text")
        assert c["reason"], f"{c['card_id']}: hard_assert with no stated reason"


def test_label_status_is_machine_drafted(payload, cases):
    """Labels are machine-drafted, permanently (A16.3 amended 2026-08-11).

    This replaces `test_nothing_is_silently_promoted_to_gold`, which guarded a
    confirmation path that no longer exists. That test asserted the labels were
    still marked pending — a guard against promotion to a state the study has
    since dropped, which would have kept passing while protecting nothing.

    What survives is narrower and true: the status is stated, and it is stated
    as settled rather than pending, so no reader infers that confirmation is
    still coming.
    """
    assert "machine-drafted" in payload["label_status"].lower()
    assert all(c["label_status"] == "machine-drafted" for c in cases)


def test_no_duplicate_card_property_pairs(cases):
    seen: dict[tuple[str, str], int] = {}
    for c in cases:
        key = (c["card_id"], c["property"])
        seen[key] = seen.get(key, 0) + 1
    dupes = {k: n for k, n in seen.items() if n > 1}
    assert not dupes, f"a card cannot hold two verdicts on one property: {dupes}"


def test_excerpts_stay_minimal_spans(cases):
    over = [(c["card_id"], len(c["excerpt"])) for c in cases
            if len(c["excerpt"]) > MAX_EXCERPT_CHARS]
    assert not over, f"excerpts grew past a minimal span: {over}"


def test_cases_cover_only_the_enriched_properties(cases):
    got = {c["property"] for c in cases}
    assert got <= ENRICHED_PROPERTIES, f"unexpected property in case set: {got}"


def test_row_hashes_are_well_formed(cases):
    bad = [c["card_id"] for c in cases
           if not re.fullmatch(r"[0-9a-f]{16}", c["row_hash"])]
    assert not bad, f"row_hash must tie a label to exact text: {bad}"


def test_expectations_match_the_committed_labels(cases):
    """The case set's `expected` is a COPY of a label, and copies drift.

    They did: correcting the labels (v3 adoption plus four adjudicated flips)
    left eight cases asserting the pre-correction expectation, so the fixture
    and the label file disagreed about what the same card states. A measurement
    scored against the stale copy would have been attributed to the extractor.

    Same failure as the sheet-versus-prompt drift, one layer down. The guard is
    the same: the copy is checked against its source, every run.
    """
    import csv
    csv.field_size_limit(10 ** 9)
    labels_path = (_REPO / "studies/taxonomy-validation/enrichment/"
                   "enriched_labels.csv")
    if not labels_path.exists():
        pytest.skip("labels not present")

    labels = {}
    with labels_path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            for prop in ENRICHED_PROPERTIES:
                labels[(row["card_id"], prop)] = (row.get(prop) or "").strip().lower()

    drift = [(c["card_id"], c["property"], c["expected"],
              labels.get((c["card_id"], c["property"])))
             for c in cases
             if labels.get((c["card_id"], c["property"])) not in (None, c["expected"])]
    assert not drift, f"cases disagree with the committed labels: {drift[:5]}"


def test_absent_cases_survive_the_prefilters_own_exclusions(cases):
    """These must be the EXTRACTOR's problem, not the search filter's.

    The enrichment search already drops matches that are not prose -- template
    headings and SentencePiece vocabulary dumps. Any absent case whose lure the
    filter would itself have excluded is not evidence about extraction; it is a
    case the pipeline never delivers. Keeping one here would inflate the
    apparent difficulty of the set.
    """
    sys.path.insert(0, str(_REPO / "studies/taxonomy-validation/enrichment"))
    from search import _excluded_by  # noqa: E402

    leaked = []
    for c in cases:
        if c["expected"] != "absent" or not c["matched_text"]:
            continue
        m = re.search(re.escape(c["matched_text"]), c["excerpt"])
        if m and _excluded_by(c["excerpt"], m):
            leaked.append((c["card_id"], c["matched_text"]))
    assert not leaked, (
        f"absent cases the search filter would have excluded anyway: {leaked}")
