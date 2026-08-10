"""raidex furnisher adapter, tested against verbatim published records.

Fixtures are real bytes from cloudronin/raidex-results (see
tests/fixtures/raidex/README.md). Editing one to make a test pass would turn a
real furnisher property into a fiction, which is the failure this whole layer
exists to catch.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from uofa_cli.furnishers import GROUP_B_RESULT_PROPERTIES, VALUE_ONLY_FIELDS
from uofa_cli.furnishers import raidex

_FIX = Path(__file__).parent / "fixtures" / "raidex"
_RECORDS = sorted(_FIX.glob("*.json"))
_BASE = "https://example.org/m"

# Coverage is read from the record, never assumed: two fixtures are 9/9 and two
# are 8/9 with a genuinely excluded constituent.
_EXPECTED_COVERAGE = {
    "anthropic__claude-sonnet-5.json": ("9/9", 0),
    "huggingface__google__gemma-3-27b-it.json": ("9/9", 0),
    "openai__gpt-5.6.json": ("8/9", 1),
    "xai__grok-4.5.json": ("8/9", 1),
}


def _furnish(path: Path):
    fetched = raidex.fetch_record("", local_path=path)
    assert fetched.ok, f"{path.name}: {fetched.status} {fetched.detail}"
    return raidex.furnish(fetched.record, _BASE, str(path))


def test_fixtures_present():
    assert _RECORDS, "no raidex fixtures — re-fetch per tests/fixtures/raidex/README.md"


@pytest.mark.parametrize("path", _RECORDS, ids=lambda p: p.name)
def test_coverage_and_exclusions_match_the_record(path):
    ev = _furnish(path)
    coverage, n_excluded = _EXPECTED_COVERAGE[path.name]
    assert ev.coverage == coverage
    assert len(ev.excluded) == n_excluded
    # 9 constituents + 1 composite, minus whatever the record excluded.
    assert ev.n_nodes == 10 - n_excluded


@pytest.mark.parametrize("path", _RECORDS, ids=lambda p: p.name)
def test_excluded_constituent_never_becomes_a_node(path):
    """A constituent raidex could not score must not appear as a result.

    A node asserting "measured, score unknown" is a fabricated measurement. The
    exclusion is what rai_coverage counts; reporting it as an exclusion reports
    the composite-exclusion rule working.
    """
    ev = _furnish(path)
    excluded_keys = {e["constituent"] for e in ev.excluded}
    node_ids = {n["id"] for n in ev.nodes}
    for key in excluded_keys:
        assert f"{_BASE}/validation/raidex-{key}" not in node_ids
    for node in ev.nodes:
        assert node.get("metricValue") is not None, f"{node['id']} has no score"


@pytest.mark.parametrize("path", _RECORDS, ids=lambda p: p.name)
def test_exclusion_reason_is_classified_never_raw(path):
    """The record's `error` is a traceback containing the operator's filesystem
    paths, and these bundles get published. Reasons are classified, never copied."""
    ev = _furnish(path)
    known = {label for label, _ in raidex._EXCLUSION_CLASSES} | {raidex._UNCLASSIFIED}
    for exc in ev.excluded:
        assert exc["reason"] in known, f"unclassified reason leaked: {exc['reason']!r}"
        assert "/Users/" not in exc["reason"]
        assert "Traceback" not in exc["reason"]
        assert len(exc["reason"]) < 40


@pytest.mark.parametrize("path", _RECORDS, ids=lambda p: p.name)
def test_only_bbq_carries_uncertainty(path):
    """The asymmetry that makes W-AL-01 discriminate instead of blanket-fire.

    `bbq` publishes a real float `acc_stderr`; the other eight constituents and
    the composite publish none. If this ever becomes "all" or "none", the
    selective-firing property is gone and the readout stops distinguishing a
    furnisher that reports uncertainty from one that does not.
    """
    ev = _furnish(path)
    with_uq = {n["id"].rsplit("-", 1)[-1] for n in ev.nodes
               if "hasUncertaintyQuantification" in n}
    assert with_uq == {"bbq"}, f"expected only bbq to carry UQ, got {with_uq}"


@pytest.mark.parametrize("path", _RECORDS, ids=lambda p: p.name)
def test_absence_is_omission_never_a_falsy_value(path):
    """Every Group-B rule tests noValue(). A `false` or `"N/A"` would make the
    triple exist and silence the rule — satisfying a constraint with a plausible
    value, the defect AGENTS.md §13 calls out as rewarding fabrication."""
    ev = _furnish(path)
    for node in ev.nodes:
        for key, value in node.items():
            assert value is not None, f"{node['id']}.{key} is None"
            assert value != "N/A", f"{node['id']}.{key} is the string 'N/A'"
            if key in GROUP_B_RESULT_PROPERTIES or key == "hasUncertaintyQuantification":
                assert value is not False, (
                    f"{node['id']}.{key} is False — absence must be omission, "
                    "or the rule that tests for it goes silent"
                )


@pytest.mark.parametrize("path", _RECORDS, ids=lambda p: p.name)
def test_generalized_claim_is_on_the_composite_only(path):
    """COMPOUND-EV-02 must fire once per model, not once per constituent."""
    ev = _furnish(path)
    marked = [n["id"] for n in ev.nodes if n.get("generalizedClaim")]
    assert marked == [f"{_BASE}/validation/raidex-composite"]


@pytest.mark.parametrize("path", _RECORDS, ids=lambda p: p.name)
def test_every_node_carries_a_generating_activity(path):
    """raidex records when and how each number was produced, so core's W-EP-02
    must not report "no provenance chain" about it. A false finding spends the
    reader's trust on a gap that is not there."""
    ev = _furnish(path)
    for node in ev.nodes:
        activity = node.get("wasGeneratedBy")
        assert isinstance(activity, dict) and activity.get("id")
        assert activity.get("type") == "prov:Activity"


@pytest.mark.parametrize("path", _RECORDS, ids=lambda p: p.name)
def test_adapter_emits_only_declared_properties(path):
    """Whatever the adapter writes must be in the contract the A1 lint checks."""
    allowed = (
        GROUP_B_RESULT_PROPERTIES
        | VALUE_ONLY_FIELDS
        | {"hasUncertaintyQuantification", "uqMethod", "wasGeneratedBy"}
    )
    ev = _furnish(path)
    for node in ev.nodes:
        undeclared = set(node) - allowed
        assert not undeclared, (
            f"{node['id']} emits undeclared properties {sorted(undeclared)}; add them "
            "to uofa_cli.furnishers or the coverage lint cannot see them"
        )


def test_na_string_is_read_as_absent():
    """bbq's raw carries 26 sub-scores whose stderr is the STRING "N/A" alongside
    one real float. Reading a sentinel as a value would silence W-AL-01 on a
    result that has no uncertainty at all."""
    assert raidex._as_number("N/A") is None
    assert raidex._as_number(None) is None
    assert raidex._as_number("") is None
    assert raidex._as_number(True) is None      # bool is an int subclass
    assert raidex._as_number(0.0408) == pytest.approx(0.0408)
    assert raidex._as_number(0) == 0.0          # a real zero is a real score


def test_stderr_finder_ignores_na_sentinels():
    raw = {"t": {"acc_stderr,none": 0.04083,
                 "amb_bias_score_Age_stderr,none": "N/A",
                 "other_stderr,none": None}}
    found = raidex._find_stderr(raw)
    assert found is not None and found[0] == pytest.approx(0.04083)
    assert raidex._find_stderr({"t": {"x_stderr,none": "N/A"}}) is None
    assert raidex._find_stderr({}) is None


def test_missing_model_is_notfound_not_an_error(tmp_path):
    """Most models have no raidex run. The honest readout is "no reported
    evaluation to assess", not a failure."""
    fetched = raidex.fetch_record("nobody/nothing", local_path=tmp_path / "absent.json")
    assert fetched.status == "notfound"


def test_schema_drift_is_named_not_crashed(tmp_path):
    """The dataset has already shifted once — a `judge` field broke its own
    viewer — so drift is demonstrated, not hypothetical."""
    p = tmp_path / "drifted.json"
    p.write_text(json.dumps({"config": {}, "results": {}}))   # no `composite`
    fetched = raidex.fetch_record("x/y", local_path=p)
    assert fetched.status == "schema"
    assert "composite" in fetched.detail

    p.write_text("not json at all")
    assert raidex.fetch_record("x/y", local_path=p).status == "unreadable"
