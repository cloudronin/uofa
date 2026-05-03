"""Surviving-set narrative function (spec v0.4 §2.5, P-I).

Per spec §2.6 this applies ONLY to `check`, and ONLY when check has
produced C4 output (surviving sets per COU after prioritization). C4
isn't currently part of the rule engine's output — when it lands,
this function will read `structured_output['c4_surviving_sets']` and
generate per-COU narratives.

For v0.6.0: registered for `check` so the dispatcher matrix matches
spec §2.6, but returns empty when no C4 data is present (the always
case today). Plumbing ready for switch-on.
"""

from __future__ import annotations

import json
import logging

from uofa_cli.interpretation.cache import ExplanationCache, compute_key
from uofa_cli.interpretation.dispatcher import applies_to_commands
from uofa_cli.interpretation.envelope import INTERPRETATION_VERSION
from uofa_cli.interpretation.functions.group import _generate_and_parse, _noop_cm, _render_firings_block
from uofa_cli.interpretation.templates import has_template, render
from uofa_cli.llm.backend import GenerationOptions
from uofa_cli.llm.errors import LLMError

log = logging.getLogger(__name__)


_NARRATIVE_SCHEMA = {
    "type": "object",
    "properties": {
        "narrative": {
            "type": "object",
            "properties": {
                "cou": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["text"],
        },
    },
    "required": ["narrative"],
}


@applies_to_commands("check")
def surviving_set_narrative(
    *,
    command: str,
    contexts: list,
    structured_output,
    backend,
    options,
    cache: ExplanationCache | None = None,
) -> dict:
    """Generate per-COU surviving-set narrative when C4 output is present.

    Returns ``{"narratives": [{cou, text}]}`` with one entry per COU
    that has surviving firings after prioritization. Returns empty
    when `structured_output` lacks `c4_surviving_sets` (the v0.6.0
    state — C4 isn't generated yet).

    Spec §2.5 + §2.6: applies only to `check` mode and only when C4 is
    present. Engineered to silently no-op rather than warn — most v0.6.0
    runs will skip this function, and that's expected behavior, not a
    misconfiguration.
    """
    pack_name = options.pack_name
    if not has_template("rules", "narrative", pack_name):
        return {}

    # Look for C4 output in the structured payload. Shape (when present):
    #   structured_output["c4_surviving_sets"] = [
    #       {"cou": "<COU name>", "firings": [...], "rationale": "..."},
    #       ...
    #   ]
    if not isinstance(structured_output, dict):
        return {}
    surviving_sets = structured_output.get("c4_surviving_sets")
    if not surviving_sets:
        return {}

    gen_options = GenerationOptions(
        temperature=0.0,
        max_tokens=4096,
        extra={"think": False},
    )

    spinner_factory = getattr(options, "spinner_factory", None) or _noop_cm
    narratives: list[dict] = []
    for entry in surviving_sets:
        if not isinstance(entry, dict):
            continue
        cou_name = str(entry.get("cou", ""))
        surviving = entry.get("firings", [])
        prioritization = str(entry.get("rationale", ""))

        # Build a synthetic FiringContext-like text block for the prompt.
        # When surviving sets are stored as raw firing dicts, render with
        # the same helper as group.py so the model sees a consistent shape.
        from uofa_cli.interpretation.context import FiringContext
        fake_contexts = [
            FiringContext(
                pattern_id=str(f.get("patternId", "")),
                severity=str(f.get("severity", "Medium")),
                hits=int(f.get("hits", 0)),
                description=str(f.get("description", "")),
            )
            for f in surviving if isinstance(f, dict)
        ]
        firings_text = _render_firings_block(fake_contexts)

        template_vars = {
            "cou": _cou_dict_from_name(cou_name, contexts),
            "surviving_firings_text": firings_text,
            "prioritization_rationale": prioritization,
        }
        prompt = render("rules", "narrative", pack_name, **template_vars)

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
                narratives.append(cached)
                continue

        try:
            with spinner_factory(f"Generating narrative for {cou_name or 'COU'}..."):
                if backend.supports_structured_output():
                    try:
                        result = backend.generate_structured(prompt, _NARRATIVE_SCHEMA, gen_options)
                    except NotImplementedError:
                        result = _generate_and_parse(backend, prompt, gen_options)
                else:
                    result = _generate_and_parse(backend, prompt, gen_options)
        except (LLMError, json.JSONDecodeError, ValueError) as exc:
            log.warning("narrative failed for COU %s: %s", cou_name, getattr(exc, "diagnostic", exc))
            continue

        narrative = result.get("narrative", {}) if isinstance(result, dict) else {}
        if not isinstance(narrative, dict):
            continue
        normalized = {
            "cou": str(narrative.get("cou") or cou_name),
            "text": str(narrative.get("text", "")).strip(),
        }
        if cache is not None and cache_key is not None:
            cache.put(cache_key, normalized)
        narratives.append(normalized)

    return {"narratives": narratives}


def _cou_dict_from_name(cou_name: str, contexts: list) -> dict:
    """Find the matching CouContext among `contexts` so the template can
    use cou.device_class etc. Falls back to a name-only dict."""
    from dataclasses import asdict
    for ctx in contexts:
        cou = getattr(ctx, "cou", None)
        if cou is not None and getattr(cou, "name", "") == cou_name:
            return asdict(cou)
    return {"name": cou_name}
