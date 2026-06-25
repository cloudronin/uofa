"""Regenerate the MRM-NIST curated 3-card readouts (S0, the demo).

Fetches each card's live README via huggingface_hub, then runs the UNCHANGED 23
core weakener patterns through the shared report pipeline (compute_findings +
build_report_state + the six invariants) against the mrm-nist factor set, and
writes the committed artifacts per card under packs/mrm-nist/examples/<key>/:

  - card.md       : the fetched card text at build time (provenance snapshot;
                    a note when the repo ships no README, e.g. ChemBERTa)
  - state.json    : the analysis payload the gallery renders
  - reviewer.html : the standalone reviewer readout (browser-openable / Save-as-PDF)

Provenance / honesty: the per-factor statuses are the human-curated reading of
the real card text in curated_cards.py — the locked "reuse extractor + curate"
choice. (An LLM first pass is unavailable in this build env, so the statuses are
read directly from the fetched card and committed with provenance — the same
discipline as the Morrison reviewer fixtures, tests/space/fixtures/_generate.py.)
The engine, shapes, and .rules are untouched; only the read-side is curated.

Run:  .venv/bin/python packs/mrm-nist/examples/_generate.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[2]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_HERE))

from uofa_cli.excel_mapper import map_to_jsonld  # noqa: E402
from uofa_cli.report_state import (  # noqa: E402
    build_report_state, assert_report_invariants, compute_findings,
)
from space import pipeline  # noqa: E402
from space.curated import standalone_html  # noqa: E402
from space.gloss import load_gloss  # noqa: E402
from curated_cards import CARDS, build_import_dict  # noqa: E402


def _fetch_card(model_id: str) -> tuple[str, str]:
    """Best-effort live fetch of the card README. Returns (text, provenance_note)."""
    try:
        from huggingface_hub import ModelCard
        return ModelCard.load(model_id).content or "", "fetched live via huggingface_hub"
    except Exception as exc:  # no README, gated, offline, etc.
        return "", f"no README via huggingface_hub ({type(exc).__name__})"


def build_payload(card) -> dict:
    """Curated statuses -> UofA JSON-LD -> SHACL + engine -> analysis payload."""
    data = build_import_dict(card)
    doc = map_to_jsonld(data, packs=["mrm-nist"], source_path=Path(card.model_id))
    pipeline._assign_factor_ids(doc)

    work = Path(tempfile.mkdtemp(prefix="mrm-gen-"))
    jsonld = work / "uofa.jsonld"
    jsonld.write_text(json.dumps(doc, indent=2), encoding="utf-8")

    conforms, violations = pipeline._run_check(jsonld, "mrm-nist")
    firings = pipeline._run_weakeners(jsonld, "mrm-nist")
    statuses = {f["factor_type"]: f["status"] for f in data["factors"]}

    payload = compute_findings(
        "mrm-nist", statuses, {"conforms": conforms, "violations": violations}, firings
    )
    payload["context"] = pipeline._build_context(data["summary"], "mrm-nist")
    payload["context"]["extraction_provenance"] = card.extraction_provenance
    payload["context"]["documentation_status"] = card.documentation_status
    payload["warnings"] = []
    payload["_curated"] = {
        "key": card.key,
        "model_id": card.model_id,
        "role": card.role,
        "provenance": card.provenance,
    }
    return payload


def main() -> None:
    gloss = load_gloss()
    for card in CARDS:
        card_text, note = _fetch_card(card.model_id)
        payload = build_payload(card)

        # Honest-readout gate: refuse to write a self-contradictory page.
        assert_report_invariants(build_report_state(payload, gloss))

        out = _HERE / card.key
        out.mkdir(parents=True, exist_ok=True)
        (out / "card.md").write_text(
            card_text or f"# {card.model_id}\n\n_{note}; {card.provenance}_\n",
            encoding="utf-8",
        )
        (out / "state.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        (out / "reviewer.html").write_text(standalone_html(payload, gloss), encoding="utf-8")

        c = payload["completeness"]
        in_scope = c["denom"]
        print(f"{card.key:26} | {note:42} | completeness {c['n_assessed']}/{in_scope} "
              f"| weakeners {len(payload['weakeners'])}")
    print("done — wrote card.md + state.json + reviewer.html per example")


if __name__ == "__main__":
    main()
