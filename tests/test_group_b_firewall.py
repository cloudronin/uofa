"""The firewall: neither layer's weakeners fire on the other's absent inputs.

This is the honesty guardrail of the model-credibility pack, stated in its spec
as a hard constraint. A comprehensive pack that fires benchmark weakeners on a
model with no benchmarks reproduces exactly the failure the sufficiency work was
built to close, and one that marks a model down on documentation completeness
for lacking evaluation factors it never claimed does the same thing in the other
direction.

**The firewall is enforced by structure, not by suppression.** Every Group-B rule
binds `(?uofa uofa:hasValidationResult ?vr)`, so with no such node the rules
cannot match. Group A's shape requires a `factorStandard` match, so each group's
shapes stay silent on the other's factors. There is no dispatcher to fail open
and no filter to forget — but "cannot happen by construction" is exactly the
claim that needs a test, because the construction is one clause in a rule body
that a later edit can drop without anything else noticing.

Run against real cohort members: the raidex cohort splits naturally, since the
API-hosted models have no HuggingFace card at all while the `huggingface__*`
ones have both.
"""

from __future__ import annotations

import collections
import json
import pathlib
import tempfile

import pytest

from uofa_cli import card_bundle, paths
from uofa_cli.excel_constants import AI_800_3_FACTOR_NAMES
from uofa_cli.commands import report as report_mod
from uofa_cli.furnishers import raidex
from uofa_cli.weakener_focus import attributable_factors, expected_factors

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_FIX = _ROOT / "tests" / "fixtures" / "raidex"
_CARD = _ROOT / "packs" / "mrm-nist" / "examples" / "olmo2-13b-instruct" / "card.md"

_HAS_JAR = paths.jar_path().exists()
_needs_engine = pytest.mark.skipif(not _HAS_JAR, reason="weakener engine JAR not built")

GROUP_B_PREFIXES = ("W-EV-", "COMPOUND-EV-")


def _card_bundle():
    bundle, _, _ = card_bundle.card_to_bundle(
        _CARD.read_text(), "mrm-nist",
        model_id="allenai/OLMo-2-13B-Instruct", allow_llm=False)
    return bundle


def _with_raidex(bundle, fixture="openai__gpt-5.6.json"):
    fetched = raidex.fetch_record("", local_path=_FIX / fixture)
    assert fetched.ok
    evidence = raidex.furnish(fetched.record, bundle["id"], "test")
    out = dict(bundle)
    out["hasValidationResult"] = evidence.nodes
    return out


def _fire(bundle) -> collections.Counter:
    path = pathlib.Path(tempfile.mkdtemp()) / "b.jsonld"
    path.write_text(json.dumps(bundle))
    counts: collections.Counter = collections.Counter()
    for firing in report_mod._firings(path, "mrm-nist"):
        pid = firing.get("patternId") or firing.get("pattern_id")
        counts[str(pid)] += 1
    return counts


def _group_b(counts) -> set[str]:
    return {p for p in counts if p.startswith(GROUP_B_PREFIXES)}


@_needs_engine
def test_card_only_model_fires_no_group_b_weakeners():
    """Direction 1: a model card with no reported evaluation.

    Zero eval-sufficiency weakeners — not N failures. The absence of benchmark
    evidence is a stated N/A in the readout, never a wall of red.
    """
    counts = _fire(_card_bundle())
    fired = _group_b(counts)
    assert not fired, (
        f"Group-B weakeners fired on a model with no reported evaluation: {sorted(fired)}. "
        "A rule body must have lost its hasValidationResult clause."
    )
    assert counts, "expected the card-only bundle to still produce Group-A findings"


@_needs_engine
def test_group_b_weakeners_appear_once_evidence_exists():
    """The complement: with evidence present the same rules must actually fire.

    Without this, `test_card_only_model_fires_no_group_b_weakeners` would pass
    just as well against rules that never fire at all — a green light for a
    firewall made of nothing.
    """
    fired = _group_b(_fire(_with_raidex(_card_bundle())))
    assert {"W-EV-GEN-02", "W-EV-DET-03", "W-EV-NULL-04",
            "W-EV-COU-05", "W-EV-CAP-06"} <= fired


@_needs_engine
def test_evidence_without_a_card_gives_an_honest_no_card_readout():
    """Direction 3 (addendum v0.4 §A13.7.2): furnished evidence, no model card.

    Running benchmarks does not document a model. A fine-tune or API-hosted model
    with a live raidex run and no published card must get the honest no-card
    result in Group A next to a fully populated Group B -- not Group-A credit for
    having been measured, and not Group-B silence for having no card.

    This is the real shape of half the raidex cohort: `anthropic/*`, `openai/*`
    and `xai/*` have raidex records and no HuggingFace card at all.
    """
    bundle = _card_bundle()
    # No card: nothing in the documentation layer is evidenced.
    bundle["hasCredibilityFactor"] = [
        {**f, "factorStatus": "not-assessed"} for f in bundle["hasCredibilityFactor"]
    ]
    bundle = _with_raidex(bundle, "anthropic__claude-sonnet-5.json")

    counts = _fire(bundle)
    assert {"W-EV-GEN-02", "W-EV-DET-03", "W-EV-NULL-04"} <= _group_b(counts), (
        "Group B went silent on a model that has reported evaluation but no card"
    )

    statuses = {f["factorType"]: f["factorStatus"] for f in bundle["hasCredibilityFactor"]}
    assert set(statuses) == set(expected_factors("mrm-nist"))
    assert not any(s == "assessed" for s in statuses.values()), (
        "furnished benchmark evidence credited a documentation factor -- running a "
        "benchmark is not documenting a model"
    )


def test_group_b_factors_never_enter_the_completeness_denominator():
    """Direction 2: a card-only model is not marked down for eval factors.

    `expected_factors` is the denominator and the factor grid. Group-B names in
    it would score a documented model 11/23 instead of 11/17 — the same failure
    as direction 1, arriving through arithmetic instead of through a rule.
    """
    completeness = set(expected_factors("mrm-nist"))
    assert not (set(AI_800_3_FACTOR_NAMES) & completeness)
    assert set(AI_800_3_FACTOR_NAMES) <= set(attributable_factors("mrm-nist"))


@_needs_engine
def test_shacl_stays_clean_across_both_groups():
    """Neither group's factor-name shape may flag the other's factors."""
    for label, bundle in (("card-only", _card_bundle()),
                          ("card+raidex", _with_raidex(_card_bundle()))):
        path = pathlib.Path(tempfile.mkdtemp()) / "b.jsonld"
        path.write_text(json.dumps(bundle))
        result = report_mod._shacl(path, "mrm-nist")
        offending = [v for v in result.get("violations", [])
                     if "factorType" in str(v.get("message", ""))]
        assert not offending, f"{label}: factor-name shape violations {offending}"


@_needs_engine
def test_uncertainty_findings_are_selective_not_blanket():
    """W-AL-01 must skip the one constituent that furnishes a standard error.

    This is the evidence that the assessment discriminates rather than
    blanket-failing. If it ever covers every node, either the adapter stopped
    reading bbq's stderr or something started emitting a placeholder.
    """
    bundle = _with_raidex(_card_bundle())
    path = pathlib.Path(tempfile.mkdtemp()) / "b.jsonld"
    path.write_text(json.dumps(bundle))

    n_results = len(bundle["hasValidationResult"])
    by_pattern = {}
    for firing in report_mod._firings(path, "mrm-nist"):
        pid = str(firing.get("patternId") or firing.get("pattern_id"))
        by_pattern[pid] = len(firing.get("affected_nodes") or [])

    assert by_pattern.get("W-AL-01") == n_results - 1, (
        f"W-AL-01 hit {by_pattern.get('W-AL-01')} of {n_results} results; expected all "
        "but bbq, which publishes a real acc_stderr"
    )
    assert by_pattern.get("W-EV-DET-03") == n_results, (
        "no constituent furnishes a determinism statement, so DET-03 should hit all"
    )


@_needs_engine
def test_compound_ev_01_is_silent_without_an_operator_supplied_mrl():
    """The honest N/A falls out of rule structure, not a renderer special case.

    Keyed on `decisionRiskLevel` (bound to --mrl), NOT `modelRiskLevel` — which
    every mrm-nist bundle already carries as the assumed posture of 3, and which
    would therefore make this rule fire unconditionally.
    """
    bundle = _with_raidex(_card_bundle())
    assert bundle.get("modelRiskLevel") == 3, "the assumed-posture precondition changed"
    assert "COMPOUND-EV-01" not in _fire(bundle)

    scoped = dict(bundle)
    scoped["decisionRiskLevel"] = 3
    assert "COMPOUND-EV-01" in _fire(scoped)


@_needs_engine
def test_cou_05_severity_tracks_the_flag_but_the_finding_tracks_the_record():
    """--cou selects severity; it never creates the finding.

    The regression this guards: a rule discriminating only on the operator's flag
    would manufacture a Critical against a model whose card properly states its
    context of use — reporting on the operator's input instead of the evidence.
    """
    bundle = _with_raidex(_card_bundle())

    def severity_of(b):
        path = pathlib.Path(tempfile.mkdtemp()) / "b.jsonld"
        path.write_text(json.dumps(b))
        for firing in report_mod._firings(path, "mrm-nist"):
            if str(firing.get("patternId") or firing.get("pattern_id")) == "W-EV-COU-05":
                return firing.get("severity")
        return None

    assert severity_of(bundle) == "High"
    scoped = dict(bundle)
    scoped["decisionContextOfUse"] = "screening triage for X"
    assert severity_of(scoped) == "Critical"

    # And the boundary case: the record states its COU, so no finding at all —
    # even though an assessment context was supplied.
    documented = dict(scoped)
    documented["hasValidationResult"] = [
        {**n, "claimedCOU": "stated in the published record"}
        for n in scoped["hasValidationResult"]
    ]
    assert severity_of(documented) is None, (
        "W-EV-COU-05 fired against a record that states its context of use"
    )


# ── W-EV-COR-09: corroboration absent vs never attempted ────────────────────
#
# The rule sits on the firewall line. It must fire on "no independent evidence
# corroborates any reported score" (a statement about the published record) and
# NEVER on "the furnisher does not cover this model" (a fact about the assessor's
# roster). The second would penalize an absence the vendor never claimed to fill.
#
# The exclusion is structural: the rule body requires a furnished result to exist.
# These tests pin that it stays structural, because a wording-only guarantee
# survives exactly until someone edits the rule body.

def _vr(slug, source, **extra):
    node = {"id": f"https://example.org/m/validation/{slug}", "type": "ValidationResult",
            "name": slug, "metricValue": 70.0, "evidenceSource": source}
    node.update(extra)
    return node


def _fire_on_nodes(tmp_path, nodes):
    """patternIds firing on a bundle carrying `nodes`, via the production path."""
    import json
    from uofa_cli.commands import report as R
    bundle, _p, _s = card_bundle.card_to_bundle(
        _CARD.read_text(), "mrm-nist", model_id="a/b", allow_llm=False)
    bundle["hasValidationResult"] = nodes
    bundle["_sufficiencyAssessed"] = True
    path = tmp_path / "b.jsonld"
    path.write_text(json.dumps(bundle))
    state = R.build_report_state(R.analysis_for(bundle, path, "mrm-nist"))
    return {c.pattern_id for c in state.concerns}


@_needs_engine
def test_cor09_silent_when_no_furnisher_ran(tmp_path):
    """Reported scores alone: corroboration was never ATTEMPTED, so no finding.

    This is the reading the rule must not take. A card-only assessment saying
    "nothing corroborates these scores" would be reporting the absence of a
    furnisher run as a defect in the vendor's record.
    """
    fired = _fire_on_nodes(tmp_path, [_vr("mmlu", "reported"), _vr("gsm8k", "reported")])
    assert "W-EV-COR-09" not in fired, (
        "COR-09 fired with no furnished evidence in the bundle - it is reporting "
        "the assessor's roster as a property of the published record")


@_needs_engine
def test_cor09_fires_when_furnished_evidence_corroborates_nothing(tmp_path):
    """Both sources present, disjoint constituents: corroboration was possible to
    look for and was not found. That is a statement about the record."""
    fired = _fire_on_nodes(tmp_path, [_vr("mmlu", "reported"), _vr("gsm8k", "reported"),
                             _vr("bbq", "furnished"), _vr("wmdp", "furnished")])
    assert "W-EV-COR-09" in fired


@_needs_engine
def test_cor09_silent_on_a_corroborated_score(tmp_path):
    """A reported score with a furnished counterpart is corroborated; no finding."""
    fired = _fire_on_nodes(tmp_path, [
        _vr("simpleqa", "reported",
            corroboratedBy="https://example.org/m/validation/simpleqa-furnished"),
        _vr("simpleqa-furnished", "furnished"),
    ])
    assert "W-EV-COR-09" not in fired
