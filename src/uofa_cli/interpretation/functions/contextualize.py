"""Severity contextualization function (spec v0.4 §2.3, P-G).

ONE LLM call per command. Model sees every firing's context and
produces a relative ranking 1..N where rank 1 is most consequential
for this package's specific COU. Distinct from the rule's static
severity field — the contextual rank weights by COU stakes, evidence
centrality, and compound interactions.

Output goes into the envelope's `contextual_severity` slot, keyed by
patternId, with `{rank, rationale}` per entry.
"""

from __future__ import annotations

import json
import logging

from uofa_cli.interpretation.cache import ExplanationCache, compute_key
from uofa_cli.interpretation.context import FiringContext, ViolationContext
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


_CONTEXTUALIZE_SCHEMA = {
    "type": "object",
    "properties": {
        "contextual_severity": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "rank": {"type": "integer"},
                    "rationale": {"type": "string"},
                },
                "required": ["rank"],
            },
        },
    },
    "required": ["contextual_severity"],
}


@applies_to_commands("rules", "check", "shacl")
def contextualize_severity(
    *,
    command: str,
    contexts: list,
    structured_output,
    backend,
    options,
    cache: ExplanationCache | None = None,
) -> dict:
    """Rank firings 1..N by contextual importance.

    Returns ``{"contextual_severity": {patternId: {rank, rationale}}}``.
    The single LLM call sees every firing + its affected evidence + the
    COU framing and produces the ranking in one pass — separate calls
    per item would give the model no comparative context to rank from.
    """
    pack_name = options.pack_name
    if not has_template("rules", "contextualize", pack_name):
        log.warning(
            "No `rules/contextualize.jinja2` template for pack %r; skipping",
            pack_name,
        )
        return {}

    if command == "shacl":
        items = [c for c in contexts if isinstance(c, ViolationContext)]
        if not has_template("shacl", "contextualize", pack_name):
            return {}
    else:
        items = [c for c in contexts if isinstance(c, FiringContext)]

    if not items:
        return {}

    if options.max_items is not None and options.max_items > 0:
        items = _top_n(items, options.max_items)

    template_command = "shacl" if command == "shacl" else "rules"
    firings_text = _render_firings_block(items)
    template_vars = {
        "firings_text": firings_text,
        "cou": _first_cou(items),
        "pack": _first_pack(items),
    }
    prompt = render(template_command, "contextualize", pack_name, **template_vars)

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
        with spinner_factory("Ranking contextual severity..."):
            if backend.supports_structured_output():
                try:
                    result = backend.generate_structured(prompt, _CONTEXTUALIZE_SCHEMA, gen_options)
                except NotImplementedError:
                    result = _generate_and_parse(backend, prompt, gen_options)
            else:
                result = _generate_and_parse(backend, prompt, gen_options)
    except (LLMError, json.JSONDecodeError, ValueError) as exc:
        log.warning("contextualize failed: %s", getattr(exc, "diagnostic", exc))
        return {}

    raw = result.get("contextual_severity", {}) if isinstance(result, dict) else {}
    out_dict: dict = {}
    if isinstance(raw, dict):
        for pid, info in raw.items():
            if not isinstance(info, dict):
                continue
            out_dict[str(pid)] = {
                "rank": int(info.get("rank", 0)) if str(info.get("rank", "")).lstrip("-").isdigit() else 0,
                "rationale": str(info.get("rationale", "")).strip(),
            }

    out = {"contextual_severity": out_dict}
    if cache is not None and cache_key is not None:
        cache.put(cache_key, out)
    return out
