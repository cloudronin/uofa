"""The pre-registered catalog must be the catalog the pack actually ships.

A pre-registration freezes a rule set so results cannot be explained after the
fact. That guarantee is void if the frozen set drifts from the code: figures get
reported for rules that were renamed, and rules that shipped get no figures at
all.

This is not hypothetical. An earlier draft of A16.2 froze `W-EV-UQ-01`, which had
been withdrawn because core's W-AL-01 already fires on the same property and the
same node, and `W-EV-COV-09`, which was renamed COR-09 because "coverage" was the
reading the design ruling rejected. It was caught by reading, two exchanges
before the freeze. Reading is not a control.

Drift is the one error a pre-registration cannot recover from, because the
artifact's whole value is that it was fixed before the result was visible -- so
it cannot be corrected afterwards without destroying what it certifies.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from uofa_cli import paths

_PREREG = Path(__file__).resolve().parents[1] / "studies" / "taxonomy-validation" / "PREREGISTRATION.md"
_ID = re.compile(r"\| (W-EV-[A-Z]+-\d+|COMPOUND-EV-\d+) \|")


@pytest.mark.skipif(not _PREREG.exists(), reason="pre-registration not yet drafted")
def test_frozen_catalog_is_exactly_what_the_pack_declares():
    declared = set(paths.detection_config(paths.pack_manifest("mrm-nist"))["patternIds"])
    frozen = set(_ID.findall(_PREREG.read_text()))

    assert frozen, "no rules parsed from the pre-registration catalog table"
    only_pack = declared - frozen
    only_prereg = frozen - declared
    assert not only_pack, (
        f"the pack ships rules the pre-registration does not freeze: {sorted(only_pack)}. "
        "They would be validated by nothing.")
    assert not only_prereg, (
        f"the pre-registration freezes rules the pack does not ship: {sorted(only_prereg)}. "
        "Figures would be reported for rules that do not exist.")


@pytest.mark.skipif(not _PREREG.exists(), reason="pre-registration not yet drafted")
def test_withdrawn_rules_are_not_silently_reintroduced():
    """W-EV-UQ-01 and W-EV-COV-09 must appear only as recorded exclusions."""
    text = _PREREG.read_text()
    for withdrawn in ("W-EV-UQ-01", "W-EV-COV-09"):
        assert f"| {withdrawn} |" not in text, (
            f"{withdrawn} is back in the catalog table; it was withdrawn/renamed")
        assert withdrawn in text, (
            f"{withdrawn} is not mentioned at all -- the exclusion should be "
            "recorded so it reads as deliberate rather than forgotten")


@pytest.mark.skipif(not _PREREG.exists(), reason="pre-registration not yet drafted")
def test_the_register_is_empty_before_freeze():
    """A16.2: no rule with a structurally always-true firing condition."""
    from uofa_cli.furnishers import PENDING_EMISSION
    assert PENDING_EMISSION == {}, (
        f"PENDING_EMISSION is non-empty: {sorted(PENDING_EMISSION)}. Those rules "
        "fire unconditionally and have no defined precision, so they cannot enter "
        "validation on either settle path.")
