"""Resolve a `uofa report` source (local bundle vs HF model id vs model URL) and
fetch the model card. Read-side only — no engine, no extraction here.

Source detection is conservative: a `.jsonld`/`.json` path or any existing file is a
local bundle (the deterministic report path, untouched); an `owner/model` id or a
`huggingface.co/owner/model` URL is the card path; everything else errors. HuggingFace
*space* and *dataset* URLs are rejected — mrm-nist assesses model cards.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_HF_URL = re.compile(r"^https?://(?:www\.)?huggingface\.co/(?P<rest>.+)$", re.IGNORECASE)
_ID = re.compile(r"^[A-Za-z0-9][\w.-]*/[\w.-]+$")

# Below this word count the card carries no assessable documentation (mirrors the
# corpus inclusion protocol's content floor); treated the same as a missing card.
_CONTENT_FLOOR_WORDS = 50


@dataclass(frozen=True)
class CardFetch:
    text: str
    status: str          # "ok" | "gated" | "notfound" | "empty" | "error"
    detail: str = ""
    sha: str | None = None

    @property
    def has_card(self) -> bool:
        return self.status == "ok"


def resolve_source(source: str) -> tuple[str, str]:
    """Classify a report source. Returns (kind, value):

      ("file", path)          — a local bundle (.jsonld/.json or an existing file)
      ("id",   "owner/model") — an HF model id or model URL (parsed to owner/model)
      ("error", message)      — unrecognized or unsupported
    """
    s = (source or "").strip()
    if not s:
        return ("error", "no source given")

    # Local bundle wins: an explicit bundle extension or an existing path. (Checked
    # first so a typo'd local path is never silently sent to the Hub.)
    if s.lower().endswith((".jsonld", ".json")) or Path(s).exists():
        return ("file", s)

    m = _HF_URL.match(s)
    if m:
        rest = re.split(r"[?#]", m.group("rest"))[0].strip("/")
        if rest.startswith(("spaces/", "datasets/")):
            kind = rest.split("/", 1)[0][:-1]  # "space" | "dataset"
            return ("error",
                    f"that is a HuggingFace {kind} URL — mrm-nist assesses model cards "
                    f"(huggingface.co/owner/model).")
        parts = [p for p in rest.split("/") if p]
        if not parts:
            return ("error", f"could not parse a model id from {source!r}")
        # owner/model for the usual form; a single segment is a canonical model.
        return ("id", "/".join(parts[:2]) if len(parts) >= 2 else parts[0])

    if _ID.match(s):
        return ("id", s)

    return ("error",
            f"{source!r} is not a local bundle, an HF model id (owner/model), or an "
            f"HF model URL (https://huggingface.co/owner/model).")


def fetch_card(model_id: str, revision: str | None = None) -> CardFetch:
    """Fetch a model card via huggingface_hub. Network/permission/absence outcomes
    map to a typed status (never an exception past the boundary), so the caller can
    render an honest no-card readout for gated/missing/empty cards rather than a
    hollow all-weakeners page."""
    try:
        from huggingface_hub import ModelCard
    except ImportError:
        return CardFetch("", "error",
                         "huggingface_hub is not installed (pip install huggingface_hub).")

    try:
        card = ModelCard.load(model_id)            # full card text incl. YAML frontmatter
        text = (card.content or "").strip()
    except Exception as exc:                        # classify by exception name / HTTP status
        name = type(exc).__name__
        code = getattr(getattr(exc, "response", None), "status_code", None)
        if "Gated" in name or code == 403:
            return CardFetch("", "gated", f"{model_id} is private or gated (403).")
        if "NotFound" in name or code == 404:
            return CardFetch("", "notfound", f"{model_id} has no published model card (404).")
        return CardFetch("", "error", f"{name}: {exc}")

    if len(text.split()) < _CONTENT_FLOOR_WORDS:
        return CardFetch(text, "empty",
                         f"the card has fewer than {_CONTENT_FLOOR_WORDS} words of documentation.")

    sha = None
    try:  # best-effort revision pin for provenance; never fatal
        from huggingface_hub import model_info
        sha = model_info(model_id, revision=revision).sha
    except Exception:
        pass
    return CardFetch(text, "ok", "", sha)
