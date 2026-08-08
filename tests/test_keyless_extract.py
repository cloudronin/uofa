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


def test_no_route_properties_emit_null_and_say_why(package):
    """The three failing properties must never carry a plausible-looking value."""
    for prop in ("uofa:bindsRequirement", "uofa:hasValidationResult",
                 "uofa:hasDecisionRecord"):
        v = package[prop]
        assert v["value"] is None, (
            f"{prop} has no keyless route that beats its control, so any value "
            f"here is fabrication that would satisfy minCount")
        assert v["method"] == "no-keyless-route"
        # The reason must name the measurement, so a reader can check it.
        assert any(c.isdigit() for c in v["reason"]), (
            f"{prop}'s reason cites no number: {v['reason']!r}")


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
