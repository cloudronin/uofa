"""Load the committed MRM-NIST curated card readouts for the worked-examples gallery.

Pure read-side: the gallery renders these pre-computed payloads with the shared
reviewer renderer at runtime - no LLM, no rule engine, no network. The payloads
are produced at build time by `packs/mrm-nist/examples/_generate.py` and committed
under `packs/mrm-nist/examples/<key>/state.json`. If the directory is absent (e.g.
the examples were not generated), `load_curated()` returns [] and the gallery is
simply not shown.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from uofa_cli import paths

# Gallery display order: strong → popular-but-holey → no-card. By example key.
_ORDER = ("olmo2-13b-instruct", "twitter-roberta-sentiment", "chemberta-77m-mtr")


def _examples_dir() -> Path:
    return paths.pack_dir("mrm-nist") / "examples"


@lru_cache(maxsize=1)
def load_curated() -> list[dict]:
    """Committed curated readouts in display order. Each item:
    {key, model_id, role, payload}. Missing files are skipped."""
    base = _examples_dir()
    out: list[dict] = []
    for key in _ORDER:
        f = base / key / "state.json"
        if not f.exists():
            continue
        payload = json.loads(f.read_text(encoding="utf-8"))
        meta = payload.get("_curated", {}) or {}
        out.append({
            "key": key,
            "model_id": meta.get("model_id") or (payload.get("context") or {}).get("project_name") or key,
            "role": meta.get("role", ""),
            "payload": payload,
        })
    return out


# Standalone wrapper: the reviewer fragment is dark-themed (light text), so a
# self-contained file needs a solid dark page + the two web fonts the fragment
# CSS references. Used for the committed reviewer.html browser artifact (and its
# golden test); the in-app gallery renders the bare fragment into the app chrome.
_STANDALONE_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Credibility Inspector - {title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono&display=swap" rel="stylesheet">
<style>
  html,body {{ margin:0; background:#0c0d0e; color:#e8e6e1;
    font-family:'IBM Plex Sans',ui-sans-serif,system-ui,sans-serif; }}
  .wrap {{ max-width:64rem; margin:0 auto; padding:2.5rem 1.5rem 4rem; }}
  .ri-kicker {{ color:#9a988f; font-size:.8rem; letter-spacing:.04em;
    text-transform:uppercase; margin-bottom:.25rem; }}
  .ri-title {{ font-family:'Fraunces',Georgia,serif; font-size:1.6rem; margin:0 0 1.5rem; }}
  .ri-title code {{ font-family:'IBM Plex Mono',monospace; font-size:1.1rem; color:#d4a35a; }}
</style></head>
<body><div class="wrap">
  <div class="ri-kicker">MRM-NIST · NIST AI RMF documentation profile · {role}</div>
  <h1 class="ri-title"><code>{model_id}</code></h1>
  {fragment}
</div></body></html>
"""


def standalone_html(payload: dict, gloss: dict | None = None) -> str:
    """Wrap the shared reviewer fragment in a self-contained dark page for a
    browser/Save-as-PDF artifact. Deterministic given the payload (its golden
    test regenerates and byte-compares)."""
    from space.reviewer import render_reviewer_html  # local: avoid import cycle at module load

    meta = payload.get("_curated", {}) or {}
    ctx = payload.get("context", {}) or {}
    model_id = meta.get("model_id") or ctx.get("project_name") or "model card"
    return _STANDALONE_PAGE.format(
        title=model_id,
        role=meta.get("role", ""),
        model_id=model_id,
        fragment=render_reviewer_html(payload, gloss),
    )
