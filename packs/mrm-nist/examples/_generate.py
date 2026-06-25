"""Refresh the committed MRM-NIST example card snapshots (card.md).

Fetches each suggested example's live README via huggingface_hub and writes it to
packs/mrm-nist/examples/<key>/card.md. These snapshots are the committed reference the
LLM-vs-deterministic divergence test reads (tests/test_report_card.py). The demo Space
renders the examples LIVE (fetch + extract + report), not from any committed payload --
so there is no static state.json/reviewer.html to regenerate here anymore.

Run:  python packs/mrm-nist/examples/_generate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[2]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_HERE))

from curated_cards import CARDS  # noqa: E402


def _fetch(model_id: str) -> tuple[str, str]:
    try:
        from huggingface_hub import ModelCard
        return ModelCard.load(model_id).content or "", "fetched live via huggingface_hub"
    except Exception as exc:  # no README, gated, offline
        return "", f"no README via huggingface_hub ({type(exc).__name__})"


def main() -> None:
    for card in CARDS:
        text, note = _fetch(card.model_id)
        out = _HERE / card.key
        out.mkdir(parents=True, exist_ok=True)
        (out / "card.md").write_text(
            text or f"# {card.model_id}\n\n_{note}; {card.provenance}_\n", encoding="utf-8")
        print(f"{card.key:26} | {note}")
    print("done - wrote card.md per example")


if __name__ == "__main__":
    main()
