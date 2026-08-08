"""The keyless extractor must account for every required property, and lie about none.

Two of these tests exist because the first draft of `keyless_extract.py` failed
them. `hasCredibilityFactor` was listed in `ROUTES` as routed and never emitted,
and nothing noticed -- the same class of defect the module was written to catch.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))

keyless_extract = pytest.importorskip("keyless_extract")
K3c = pytest.importorskip("keyless_k3c_named_entities")

SEEDED = _ROOT / "tests" / "fixtures" / "extract_corpus_seeded" / "holdout"


@pytest.fixture(scope="module")
def package():
    """One real seeded document, extracted. Not a hand-built dict.

    A fixture that constructs the expected output cannot catch a property the
    extractor never emits, which is exactly the bug these tests exist for.
    """
    import json

    from keyless_pipeline_registry import read
    bundles = [b for b in sorted(SEEDED.glob("bundle_*")) if (b / "source").is_dir()]
    if not bundles:
        pytest.skip("seeded corpus not present")
    b = bundles[0]
    gt = json.loads((b / "ground_truth.json").read_text())
    return keyless_extract.extract(read(b), gt.get("standard", "V&V40"))


def test_every_required_property_is_accounted_for(package):
    """Silence about a property is indistinguishable from deciding to skip it."""
    missing = [p for p in keyless_extract.required_properties() if p not in package]
    assert not missing, (
        f"{missing} are required by the shape and absent from the output "
        f"entirely. Emit them as absent with a reason, or they read as an "
        f"oversight rather than a decision.")


def test_the_required_list_comes_from_the_shape_not_a_literal():
    """A hand-kept copy of the shape's requirements is a copy that drifts."""
    req = keyless_extract.required_properties()
    assert len(req) == 13, f"expected the 13 CompleteBody properties, got {len(req)}"
    src = (_ROOT / "dev" / "tools" / "scripts" / "keyless_extract.py").read_text()
    body = src.split("def required_properties")[1].split("\ndef ")[0]
    assert "uofa_shacl.ttl" in body, "the list must be read from the shape file"


def test_author_supplied_properties_emit_null_and_say_why(package):
    """Nothing an extractor cannot know may carry a plausible-looking value."""
    for prop in keyless_extract.OUT_OF_SCOPE:
        v = package[prop]
        assert v["value"] is None, (
            f"{prop} is not an extractor's to supply, so any value here is "
            f"fabrication that would satisfy minCount")
        assert v["method"] == "no-keyless-route"
        assert v["reason"], f"{prop} is absent without saying why"


def test_binds_requirement_is_author_supplied_not_a_failed_route(package):
    """The decision of 2026-08-08, pinned so it is not quietly reverted.

    `bindsRequirement` means the engineering requirement the model is trusted to
    help satisfy. It was measured at 0.026 and then 0.032 against gold that is
    81% acceptance criteria -- the generator asked for "an acceptance target the
    paper states it must meet" and filed the answers under `requirements`. Only
    30% of papers cite a standard at all, so the property is not extractable from
    a paper and an extractor that emitted one would be inventing it.
    """
    assert "bindsRequirement" not in keyless_extract.ROUTES, (
        "bindsRequirement is author-supplied; it must not carry a route and a "
        "confidence, because that invites someone to improve the number")
    v = package["uofa:bindsRequirement"]
    assert v["value"] is None
    assert "design history file" in v["reason"] or "author" in v["reason"].lower()


def test_the_two_recovered_routes_are_not_silently_dropped(package):
    """hasValidationResult and hasDecisionRecord have trained routes now."""
    for prop in ("hasValidationResult", "hasDecisionRecord"):
        assert prop in keyless_extract.ROUTES, (
            f"{prop} has a trained route that beats its control; dropping it "
            f"from ROUTES would re-record it as unextractable")
        assert keyless_extract.ROUTES[prop][0] == "trained"


def test_every_emitted_value_carries_its_provenance(package):
    """A value without a method and a confidence cannot be audited later."""
    for prop, v in package.items():
        assert "method" in v and "confidence" in v, prop
        if v["value"] not in (None, [], ""):
            assert 0.0 < v["confidence"] <= 1.0, (
                f"{prop} was emitted with confidence {v['confidence']}")


def test_confidence_matches_the_measured_figure(package):
    """Confidences are measurements, so they must equal the recorded ones."""
    for prop, v in package.items():
        if v["value"] in (None, [], ""):
            continue
        key = prop if prop in keyless_extract.ROUTES else prop.split(":")[1]
        if key in keyless_extract.ROUTES:
            assert v["confidence"] == pytest.approx(
                keyless_extract.ROUTES[key][2]), (
                f"{prop} reports a confidence that is not its measured figure")


def test_context_of_use_is_absent_on_7009a():
    """NASA-STD-7009A defines no context of use; a value there is invented."""
    import json

    from keyless_pipeline_registry import read
    for b in sorted(SEEDED.glob("bundle_*")):
        if not (b / "ground_truth.json").exists():
            continue
        gt = json.loads((b / "ground_truth.json").read_text())
        if gt.get("standard") == "V&V40":
            continue
        pkg = keyless_extract.extract(read(b), gt["standard"])
        assert pkg["uofa:hasContextOfUse"]["value"] is None, (
            f"{b.name} is {gt['standard']}, which has no context of use")
        return
    pytest.skip("no 7009A document in the holdout")
