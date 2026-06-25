"""The suggested-example list for the live card path.

The examples are no longer static renders — clicking one runs the same live pathway
as a pasted id (fetch -> extract -> report). These checks just guard that the example
ids are well-formed and classify as id-mode (the curated factor-status reference and
its divergence test live in tests/test_report_card.py).
"""

from __future__ import annotations

from space import curated
from uofa_cli import hf_card


def test_example_models_present():
    assert len(curated.EXAMPLE_MODELS) == 3
    assert all(isinstance(m, str) and isinstance(r, str) and r for m, r in curated.EXAMPLE_MODELS)


def test_example_ids_resolve_to_id_mode():
    # Each suggested example must route through the card (id) path, not be mistaken
    # for a file or rejected.
    for model_id, _role in curated.EXAMPLE_MODELS:
        kind, value = hf_card.resolve_source(model_id)
        assert kind == "id" and value == model_id
