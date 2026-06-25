"""Suggested example model cards for the demo Space's live card path.

The three cards are run through the SAME live pathway as a pasted id (fetch ->
extract -> report) when clicked - they are not static renders. The curated
factor-status reference (the divergence baseline) lives in
`packs/mrm-nist/examples/curated_cards.py`, not here.
"""

from __future__ import annotations

# (model_id, role). Clicking an example prefills the id box and runs the live path.
EXAMPLE_MODELS: list[tuple[str, str]] = [
    ("allenai/OLMo-2-1124-13B-Instruct", "Frontier, well-documented"),
    ("cardiffnlp/twitter-roberta-base-sentiment", "Popular, holey"),
    ("DeepChem/ChemBERTa-77M-MTR", "Thin - ships no card"),
]
