"""Cross-item pattern recognition (spec v0.4 §2.4, P-H).

ONE LLM call per command. Model sees ALL firings together and surfaces
emergent patterns visible only across multiple findings — coverage gaps,
evidence-flow weaknesses, factor-family concentration, etc. The
value-add over per-firing explanations is the cross-cutting view.

Output goes into the envelope's `cross_patterns` list slot. Per spec
§2.6, applies only to rules + check (not diff or shacl — diff is
already cross-by-construction; shacl violations are typically too
isolated for cross-pattern signal).
"""

from __future__ import annotations

import json
import logging

from uofa_cli.interpretation.cache import ExplanationCache, compute_key
from uofa_cli.interpretation.context import FiringContext
from uofa_cli.interpretation.dispatcher import applies_to_commands
from uofa_cli.interpretation.envelope import INTERPRETATION_VERSION
from uofa_cli.interpretation.functions.group import (
    _first_cou,
    _first_pack,
    _generate_and_parse,
    _noop_cm,
    _render_firings_block,
    _top_n,
)
from uofa_cli.interpretation.templates import has_template, render
from uofa_cli.llm.backend import GenerationOptions
from uofa_cli.llm.errors import LLMError

log = logging.getLogger(__name__)


_CROSS_SCHEMA = {
    "type": "object",
    "properties": {
        "cross_patterns": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "involved_firings": {
                        "type": "array", "items": {"type": "string"},
                    },
                },
                "required": ["name", "description"],
            },
        },
    },
    "required": ["cross_patterns"],
}


@applies_to_commands("rules", "check")
def cross_pattern_recognition(
    *,
    command: str,
    contexts: list,
    structured_output,
    backend,
    options,
    cache: ExplanationCache | None = None,
) -> dict:
    """Surface 0-5 emergent cross-item patterns.

    Returns ``{"cross_patterns": [{name, description, involved_firings}]}``
    for merge into the envelope's `cross_patterns` list.
    """
    pack_name = options.pack_name
    if not has_template("rules", "cross", pack_name):
        log.warning(
            "No `rules/cross.jinja2` template for pack %r; skipping",
            pack_name,
        )
        return {}

    items = [c for c in contexts if isinstance(c, FiringContext)]
    if len(items) < 2:
        # Cross-item pattern recognition needs at least two items by
        # definition. Skip silently for single-firing packages.
        return {}

    if options.max_items is not None and options.max_items > 0:
        items = _top_n(items, options.max_items)

    firings_text = _render_firings_block(items)
    template_vars = {
        "firings_text": firings_text,
        "cou": _first_cou(items),
        "pack": _first_pack(items),
    }
    prompt = render("rules", "cross", pack_name, **template_vars)

    cache_key = None
    if cache is not None:
        cache_key = compute_key(
            prompt=prompt,
            backend=backend.name(),
            model=backend.model(),
            interp_version=INTERPRETATION_VERSION,
        )
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    gen_options = GenerationOptions(
        temperature=0.0,
        max_tokens=4096,
        extra={"think": False},
    )

    spinner_factory = getattr(options, "spinner_factory", None) or _noop_cm
    try:
        with spinner_factory("Surfacing cross-cutting patterns..."):
            if backend.supports_structured_output():
                try:
                    result = backend.generate_structured(prompt, _CROSS_SCHEMA, gen_options)
                except NotImplementedError:
                    result = _generate_and_parse(backend, prompt, gen_options)
            else:
                result = _generate_and_parse(backend, prompt, gen_options)
    except (LLMError, json.JSONDecodeError, ValueError) as exc:
        log.warning("cross failed: %s", getattr(exc, "diagnostic", exc))
        return {}

    raw = result.get("cross_patterns", []) if isinstance(result, dict) else []
    out_list: list = []
    for p in raw:
        if not isinstance(p, dict):
            continue
        name = str(p.get("name", "")).strip()
        if not name:
            continue
        out_list.append({
            "name": name,
            "description": str(p.get("description", "")).strip(),
            "involved_firings": [str(f) for f in (p.get("involved_firings") or [])],
        })

    out = {"cross_patterns": out_list}
    if cache is not None and cache_key is not None:
        cache.put(cache_key, out)
    return out
