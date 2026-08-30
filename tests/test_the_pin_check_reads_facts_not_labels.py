"""`run log carries its pins` must test the VALUES. SF-10.

It was a substring test over the whole document —

    absent = [f for f in RUN_LOG_FIELDS if f.lower() not in lowered]

— and `"model" in text.lower()` is satisfied by the LABEL in
`| Extractor model | _not recorded_ |`. So a run log carrying every pin's name
and no pin's value passed a check named "run log carries its pins". It carried
the labels.

The vacuous-green family's purest instance in the wheel: not a check that fails
to fire, but one whose success condition was mis-stated — presence of a name
read as presence of a fact — in the tool that exists to catch exactly that.

Later pins are gated by the era the package declares, because a value-reading
check without a jurisdiction key retroactively indicts every honest pre-v0.16
package. That is the global-`CONTEXT_URL` mistake, which 183 fixture failures
voted down once already.
"""
from __future__ import annotations

import pytest

from uofa_cli.protocol_check import (
    RUN_LOG_FIELDS,
    RUN_LOG_FIELDS_BY_ERA,
    _era_tuple,
    _pin_is_recorded,
    _run_log_values,
)

HOLLOW = """# Run log
| field | value |
|---|---|
| Extractor model | _not recorded_ |
| Backend | _not recorded_ |
| site commit | _not recorded_ |
| repo head | _not recorded_ |
| base_uri | _not recorded_ |
"""

CARRIED = """# Run log
| field | value |
|---|---|
| Extractor model | openai-compatible/anthropic/claude-sonnet-5 via openrouter.ai |
| Backend | hosted |
| site commit | d40f1cec7cc1dc00ea677b2673e22ee308908fe0 |
| repo head | 0.1.0+7ca51e93 |
| base_uri | https://credenza.review/ns/anon-ad66/session |
| Prompt hash | 35033e4b585b7065dea9d11044632b4a49841adbb870726540d18b3e0368f57d |
| Pins era | v0.16 |
"""


def _absent(text: str, fields=RUN_LOG_FIELDS) -> list[str]:
    values = _run_log_values(text)
    return [f for f in fields if not _pin_is_recorded(values, f)]


# ── the defect ───────────────────────────────────────────────────────────────

def test_a_log_of_labels_without_facts_is_refused():
    """The exact document that used to pass. Measured: absent == [], PASS."""
    assert _absent(HOLLOW) == list(RUN_LOG_FIELDS), (
        "a run log whose every pin reads `_not recorded_` still passes")


def test_a_log_that_carries_its_pins_passes():
    """The other half. A stricter check that refuses everything is not a check."""
    assert _absent(CARRIED) == []


@pytest.mark.parametrize("marker", [
    "_not recorded_", "not recorded", "awaiting the pack",
    "awaiting the extraction", "bundled sample -- no extractor ran", "", "--",
])
def test_every_absence_marker_reads_as_absent(marker):
    """Each of these is a run log SAYING a fact is missing. None is a fact."""
    text = f"| field | value |\n|---|---|\n| Backend | {marker} |\n"
    assert _absent(text, ("backend",)) == ["backend"]


def test_the_check_is_not_a_substring_test_any_more():
    """Read the source, because the defect was invisible in behaviour until a
    package existed that had labels and no facts."""
    import inspect

    from uofa_cli import protocol_check

    body = inspect.getsource(protocol_check)
    assert "_run_log_values" in body and "_pin_is_recorded" in body
    assert "absent = [f for f in RUN_LOG_FIELDS if f.lower() not in lowered]" \
        not in body, "the substring test is back"


# ── jurisdiction: advised, not refused ──────────────────────────────────────

def test_a_package_predating_a_pin_is_advised_not_refused():
    """A-7's vocabulary: a package whose declared context predates the
    vocabulary cannot answer, and is advised rather than refused."""
    for introduced, pins in RUN_LOG_FIELDS_BY_ERA:
        assert _era_tuple("") < _era_tuple(introduced), (
            f"a log declaring no era must sort below {introduced}")


def test_the_era_ordering_is_the_grandfathering_rule():
    assert _era_tuple("") == ()
    assert _era_tuple("v0.16") < _era_tuple("v0.17")
    assert _era_tuple("") < _era_tuple("v0.16")


def test_every_later_pin_names_the_era_that_made_it_recordable():
    """A pin gated on an era whose writer did not exist there is a wall."""
    eras = [e for e, _ in RUN_LOG_FIELDS_BY_ERA]
    assert eras == sorted(eras, key=_era_tuple), "eras out of order"
    assert "prompt hash" in dict(RUN_LOG_FIELDS_BY_ERA)["v0.16"]
    assert set(dict(RUN_LOG_FIELDS_BY_ERA)["v0.17"]) == {"pack version", "standard"}


# ── the crown jewels are not re-graded ──────────────────────────────────────

C_SERIES_RUN_LOG = """# Run log
| field | value |
|---|---|
| Extractor model | openai-compatible/anthropic/claude-sonnet-5 via openrouter.ai |
| Agent model | claude-opus-5 |
| Backend | hosted |
| Prompt hash | 35033e4b585b7065dea9d11044632b4a49841adbb870726540d18b3e0368f57d |
| App build | 0.1.0+7ca51e93 |
| site commit | d40f1cec7cc1dc00ea677b2673e22ee308908fe0 |
| repo head | 0.1.0+7ca51e93 |
| base_uri | https://credenza.review/ns/anon-ad66/session |
| Protocol version | 0.1 |
"""


def test_the_c_series_packages_pass_the_stricter_check():
    """**Nothing ships that re-grades the counted runs.**

    The ten C-series packages are the evidence behind a published completion
    rate. A stricter check that failed them would not be a fix; it would be a
    retroactive edit to a reported result. Verified against a real C-series run
    log, reproduced verbatim.
    """
    assert _absent(C_SERIES_RUN_LOG) == []
    values = _run_log_values(C_SERIES_RUN_LOG)
    assert _pin_is_recorded(values, "prompt hash"), (
        "a C-series package fails the v0.16 pin it was the first to carry")


def test_a_c_series_package_is_advised_on_the_pins_it_predates():
    """It declares no v0.17 era, so `pack version` and `standard` are advised.
    Refusing them would indict ten packages for lacking a writer that did not
    exist when they were made."""
    values = _run_log_values(C_SERIES_RUN_LOG)
    declared = values.get("pins era", "")
    for pin in dict(RUN_LOG_FIELDS_BY_ERA)["v0.17"]:
        assert not _pin_is_recorded(values, pin)
    assert _era_tuple(declared) < _era_tuple("v0.17"), (
        "the package would be REFUSED rather than advised")
