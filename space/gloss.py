"""Plain-language gloss for credibility factors.

A single static asset (gloss.json) maps each canonical factor name to a
lawyer-readable plain_name + what_it_means. Both views read it through the one
lookup here (gloss_for) so the mapping is never duplicated.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_PATH = Path(__file__).with_name("gloss.json")


@lru_cache(maxsize=1)
def load_gloss() -> dict:
    """Load the gloss once. Keys starting with '_' (e.g. _README) are metadata."""
    raw = json.loads(_PATH.read_text(encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def gloss_for(name: str, gloss: dict | None = None) -> dict:
    """The single factor -> plain-language lookup, used by both views.

    Falls back to the raw name if a factor is somehow missing from the gloss,
    so a view never renders blank.
    """
    g = gloss if gloss is not None else load_gloss()
    return g.get(name) or {"standard": "", "plain_name": name, "what_it_means": ""}
