"""Regression: SHACL OR-constraint drill-in for the profile body shapes.

Bug context (May 25, 2026 — surfaced via the NAFEMS demo): a user ran
``uofa shacl aero-cou1.jsonld --pack nasa-7009b`` and got a single
rolled-up violation::

    [Critical] Profile: Required fields for the declared profile are missing.
        Fix: Check that all required fields for your profile are present.
        Run `uofa shacl FILE --raw` for details.

The OR-constraint on ``UnitOfAssurance_ProfileShape`` (sh:or between
``UnitOfAssurance_MinimalBody`` and ``UnitOfAssurance_CompleteBody``)
collapsed every inner property-shape failure into one opaque message.
Running ``--raw`` only added the SHACL stack trace; it still didn't say
WHICH field was missing or invalid.

Fix (``src/uofa_cli/shacl_friendly.py``): when the OR-constraint fires
on the profile dispatcher, drill into the body shape the document
claims via ``conformsToProfile``, walk its ``sh:property`` shapes by
hand against the data graph, and emit one structured violation per
failing constraint (path, requirement, actual value, fix suggestion).

This file pins the actual bytes from the May-25 demo run so the
drill-in can't silently regress to the rollup.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uofa_cli.shacl_friendly import run_shacl_multi
from uofa_cli import paths

FAILING_XLSX = (Path(__file__).parent / "fixtures" / "regression"
                / "shacl-or-drill-in" / "aero-cou1-failing.jsonld")
MORRISON_COU1 = (Path(__file__).parent.parent / "packs" / "vv40"
                 / "examples" / "morrison" / "cou1" / "uofa-morrison-cou1.jsonld")


@pytest.mark.skipif(not FAILING_XLSX.exists(),
                    reason=f"missing fixture: {FAILING_XLSX}")
class TestOrDrillInOnAeroCou1:
    """The pinned aero-cou1 file declares ProfileComplete but is missing
    bindsModel + bindsDataset. The drill-in must surface those field-level
    violations — not the legacy single 'Profile' rollup.

    It also carries an off-enum deviceClass ('Class II (safety-critical
    propulsion)'), which used to be a third violation here. It no longer fires
    under nasa-7009b: the FDA enum moved out of core into
    packs/vv40/shapes/vv40_shapes.ttl, because imposing medical device classes
    on aerospace packages inverted the constraint -- turbomachinery models that
    invented "Class II" passed while ones that honestly wrote "Turbomachinery
    (Centrifugal Pump)" failed. The enum drill-in is still covered, against the
    pack that still declares it: see TestEnumDrillInUnderVv40 below.
    """

    @pytest.fixture(scope="class")
    def violations(self):
        shapes = paths.all_shacl_schemas(active=["nasa-7009b"])
        conforms, violations = run_shacl_multi(FAILING_XLSX, shapes)
        assert conforms is False
        return violations

    def test_drill_in_replaced_rollup(self, violations):
        # The legacy "Profile" rollup has path="Profile" and no
        # 'requirement' / 'actual' fields. If drill-in worked, the
        # violations carry the new field shape.
        assert all(v.get("requirement") is not None for v in violations), (
            f"drill-in didn't kick in; some violations are legacy rollups: {violations}"
        )

    def test_violations_count(self, violations):
        # 2 known failures: bindsModel missing, bindsDataset missing.
        # deviceClass was a third until the FDA enum became pack-scoped.
        # (bindsRequirement and wasDerivedFrom appear to satisfy nodeKind
        # sh:IRI after JSON-LD coerces their string values to file:// URIs —
        # separate concern, not in scope for this fix.)
        assert len(violations) == 2, (
            f"expected 3 violations on the pinned fixture; got {len(violations)}: "
            f"{[v.get('path') for v in violations]}"
        )

    def test_each_violation_names_the_failing_field(self, violations):
        paths_failed = {v["path"] for v in violations}
        assert paths_failed == {"bindsModel", "bindsDataset"}, (
            f"unexpected violations: {paths_failed}"
        )

    def test_each_violation_carries_required_and_actual(self, violations):
        for v in violations:
            assert v["requirement"], f"missing requirement: {v}"
            assert v["actual"], f"missing actual: {v}"
            assert v["fix"], f"missing fix: {v}"
            assert v.get("profile") == "ProfileComplete", (
                f"violation should be tagged with the declared profile: {v}"
            )

    def test_min_count_violations_say_MISSING(self, violations):
        # bindsModel and bindsDataset are absent entirely — their "actual"
        # field should be the explicit MISSING marker, not an empty
        # string or random value.
        missing = [v for v in violations if v["path"] in ("bindsModel", "bindsDataset")]
        assert len(missing) == 2
        for v in missing:
            assert v["actual"] == "MISSING", f"{v['path']}: actual should be MISSING"
            assert "minCount" in v["requirement"]

    def test_deviceclass_no_longer_fires_under_a_non_medical_pack(self, violations):
        """The pack-scoping, asserted where it would otherwise look like a loss.

        The fixture still carries an off-enum deviceClass. Under nasa-7009b that
        is no longer a violation, because the FDA classification is a property
        of the medical regulatory regime rather than of every package.
        """
        assert "deviceClass" not in {v["path"] for v in violations}

    def test_fix_suggestions_are_actionable(self, violations):
        # Each fix string must be concrete (not the legacy generic
        # "check fields" message), and shouldn't tell the user to run
        # --raw — drill-in IS the friendly mode now.
        for v in violations:
            assert "Run `uofa shacl FILE --raw` for details" not in v["fix"], (
                f"{v['path']}: fix shouldn't refer back to --raw; that was "
                f"the dead-end the drill-in replaces"
            )


@pytest.mark.skipif(not FAILING_XLSX.exists(),
                    reason=f"missing fixture: {FAILING_XLSX}")
class TestEnumDrillInUnderVv40:
    """The enum drill-in, moved to the pack that still declares the enum.

    `deviceClass` used to exercise this under nasa-7009b. The FDA classification
    is now scoped to vv40, where V&V 40's medical-device remit makes it
    meaningful, so the same fixture and the same off-enum value test the same
    reporting path under the pack that constrains it.

    What must survive is the property the original bug was about: an enum
    violation has to name the allowed set and echo what the user actually wrote,
    rather than collapsing into the opaque 'Profile' rollup.
    """

    @pytest.fixture(scope="class")
    def violations(self):
        shapes = paths.all_shacl_schemas(active=["vv40"])
        conforms, violations = run_shacl_multi(FAILING_XLSX, shapes)
        assert conforms is False
        return violations

    def test_enum_violation_names_the_allowed_set(self, violations):
        dc = next((v for v in violations if v["path"] == "deviceClass"), None)
        assert dc is not None, (
            "deviceClass should still be constrained under vv40; if this fails "
            "the enum was dropped rather than moved. Violations: "
            f"{[v.get('path') for v in violations]}")
        assert "Class I" in dc["requirement"] and "Class II" in dc["requirement"]
        assert "safety-critical propulsion" in dc["actual"]

    def test_na_is_allowed_so_a_non_device_can_say_so(self, violations):
        """The reason the enum gained N/A rather than staying strict.

        A V&V 40 assessment of something that is not a regulated device needs a
        way to record that without either inventing a class or failing
        validation. Before this, 14 turbomachinery packages passed by claiming
        "Class II".
        """
        dc = next(v for v in violations if v["path"] == "deviceClass")
        assert "N/A" in dc["requirement"]


@pytest.mark.skipif(not MORRISON_COU1.exists(),
                    reason="Morrison pre-built fixture not available")
class TestDrillInDoesNotTriggerOnConformingDocs:
    """Negative control — the canonical Morrison cou1 jsonld must still
    pass cleanly (conforms=True, no violations). Guards against the
    drill-in machinery accidentally synthesizing false-positive
    violations on conforming inputs.
    """

    def test_morrison_cou1_conforms(self):
        shapes = paths.all_shacl_schemas(active=["vv40"])
        conforms, violations = run_shacl_multi(MORRISON_COU1, shapes)
        assert conforms is True, (
            f"Morrison cou1 should conform; got violations: {violations}"
        )
        assert violations == []
