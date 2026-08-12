"""The gated keyless table route, as wired into the report path.

Route v1 was gated 2026-08-12 on 60 unseen author-labeled cards: false-fire
2/27 (7.4%), false-clear 1/33 (3.0%). It is cleared for **table-borne P2 only**.

These tests cover the wiring, not the route's accuracy — that is what the
holdout measured and `tests/test_keyless_route_is_frozen.py` protects.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))

from uofa_cli.furnishers import table_uq  # noqa: E402

LM_EVAL = ("| Task |Version| Metric |Value |   |Stderr|\n"
           "|arc   |      0|acc     |0.5401|±  |0.0146|")
INLINE = "| `bs4-e10` | 0.5204 | 0.5597 | 0.5409 ± 0.0222 |"
EMPTY_HEADER = "| Task |Stderr|\n|wikitext|  |"


def test_reads_a_columnar_dispersion():
    got = table_uq.read(LM_EVAL)
    assert got and got["value"] == "0.0146"
    assert got["branch"] == "columnar"


def test_reads_an_inline_dispersion():
    got = table_uq.read(INLINE)
    assert got and got["branch"] == "inline"
    assert "0.0222" in got["value"]


def test_empty_header_column_yields_nothing():
    """The holdout's sharpest trap: a `Stderr` header with no values under it.

    Four such cards were in the gate and the route declined all four, because it
    requires a NUMBER in the column. A route matching on the header alone would
    have credited every one with an uncertainty it does not state.
    """
    assert table_uq.read(EMPTY_HEADER) is None


def test_prose_is_not_this_routes_job():
    assert table_uq.read("We report accuracy of 71.2 +/- 0.4 on MMLU.") is None


def test_every_emission_carries_a_quotable_span():
    """A property with no quotable anchor is inference wearing extraction's
    clothes. "Stated, not inferable" binds the machine as it bound the labelers,
    and a deterministic reader can satisfy it exactly, since it holds the cell."""
    node: dict = {}
    assert table_uq.attach(node, LM_EVAL) is True
    prov = node["uqProvenance"]
    assert prov["route"] == table_uq.ROUTE_VERSION
    assert prov["branch"] in ("inline", "columnar")
    assert prov["matchedCell"], "an emission with no matched cell is unauditable"
    assert "0.0146" in prov["matchedCell"]
    assert prov["gate"], "the emission must name the gate that qualified it"


def test_published_limitations_travel_with_every_emission():
    """v1's two measured defects are properties of the row, so a reader of any
    single emission can see them without finding the study."""
    node: dict = {}
    table_uq.attach(node, LM_EVAL)
    limits = " ".join(node["uqProvenance"]["knownLimitations"]).lower()
    assert "reward_std" in limits or "compound" in limits
    assert "se" in limits and "w-al-01" in limits


def test_never_overwrites_a_backend_reading():
    """Two routes disagreeing is a finding. Silently preferring one erases it."""
    node = {"hasUncertaintyQuantification": True, "uqMethod": "from the backend"}
    assert table_uq.attach(node, INLINE) is False
    assert node["uqMethod"] == "from the backend"


def test_multi_node_cards_are_left_alone():
    """The route was gated on a CARD-level question; a ValidationResult is
    per-benchmark. A card reporting five benchmarks with one stderr would have
    that value attached to all five — asserting four things nobody measured."""
    from uofa_cli.card_bundle import _attach_table_uncertainty

    nodes = [{"name": "arc"}, {"name": "hellaswag"}]
    _attach_table_uncertainty(nodes, LM_EVAL)
    assert all("hasUncertaintyQuantification" not in n for n in nodes)

    one = [{"name": "arc"}]
    _attach_table_uncertainty(one, LM_EVAL)
    assert one[0]["hasUncertaintyQuantification"] is True
