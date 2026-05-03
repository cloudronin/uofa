"""Grouping / clustering function (spec v0.4 §2.2, P-F).

ONE LLM call per command (not per-firing) — the model sees every
firing's affected evidence and produces themed clusters. Three grouping
types per spec: same-pattern, same-node, conceptual.

Output goes into the envelope's `groupings` slot as a dict keyed by
cluster name. Each value carries `kind`, `members` (patternId list),
and `rationale`.
"""

from __future__ import annotations

import json
import logging
from contextlib import contextmanager

from uofa_cli.interpretation.cache import ExplanationCache, compute_key
from uofa_cli.interpretation.context import FiringContext, ViolationContext
from uofa_cli.interpretation.dispatcher import applies_to_commands
from uofa_cli.interpretation.envelope import INTERPRETATION_VERSION
from uofa_cli.interpretation.templates import has_template, render
from uofa_cli.llm.backend import GenerationOptions
from uofa_cli.llm.errors import LLMError

log = logging.getLogger(__name__)


@contextmanager
def _noop_cm(label: str = ""):  # noqa: ARG001
    yield


_GROUPING_SCHEMA = {
    "type": "object",
    "properties": {
        "groupings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "kind": {
                        "type": "string",
                        "enum": ["same-pattern", "same-node", "conceptual"],
                    },
                    "members": {"type": "array", "items": {"type": "string"}},
                    "rationale": {"type": "string"},
                },
                "required": ["name", "members"],
            },
        },
    },
    "required": ["groupings"],
}


@applies_to_commands("rules", "check", "shacl")
def group_firings(
    *,
    command: str,
    contexts: list,
    structured_output,
    backend,
    options,
    cache: ExplanationCache | None = None,
) -> dict:
    """Cluster firings into themed groups for triage.

    Returns ``{"groupings": {<name>: {kind, members, rationale}}}`` for
    merge into the envelope. The dict shape (not list) matches the
    envelope's `groupings` slot — multiple clusters with the same name
    would silently overwrite, but that's an LLM bug worth catching loudly
    rather than papering over.
    """
    pack_name = options.pack_name
    if not has_template("rules", "group", pack_name):
        log.warning(
            "No `rules/group.jinja2` template found for pack %r; skipping",
            pack_name,
        )
        return {}

    # shacl uses ViolationContext; rules/check use FiringContext. For
    # P-F we ship rules/check; shacl support is P-K and gets its own
    # template at `templates/shacl/group.jinja2`.
    if command == "shacl":
        items = [c for c in contexts if isinstance(c, ViolationContext)]
        # No shacl/group.jinja2 yet → silently skip (P-K territory).
        if not has_template("shacl", "group", pack_name):
            return {}
    else:
        items = [c for c in contexts if isinstance(c, FiringContext)]

    if not items:
        return {}

    # max_items truncation: the model sees fewer firings to cluster, but
    # the clusters it produces are still complete for the items it sees
    if options.max_items is not None and options.max_items > 0:
        items = _top_n(items, options.max_items)

    template_command = "shacl" if command == "shacl" else "rules"
    firings_text = _render_firings_block(items)
    template_vars = {
        "firings_text": firings_text,
        "cou": _first_cou(items),
        "pack": _first_pack(items),
    }
    prompt = render(template_command, "group", pack_name, **template_vars)

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
        with spinner_factory(f"Grouping {len(items)} firings..."):
            if backend.supports_structured_output():
                try:
                    result = backend.generate_structured(prompt, _GROUPING_SCHEMA, gen_options)
                except NotImplementedError:
                    result = _generate_and_parse(backend, prompt, gen_options)
            else:
                result = _generate_and_parse(backend, prompt, gen_options)
    except (LLMError, json.JSONDecodeError, ValueError) as exc:
        log.warning("group failed: %s", getattr(exc, "diagnostic", exc))
        return {}

    # Normalize: result has shape {"groupings": [{name, kind, members, rationale}]}
    # Envelope wants dict keyed by name. Convert here.
    groupings_list = result.get("groupings", []) if isinstance(result, dict) else []
    out_dict: dict = {}
    for g in groupings_list:
        if not isinstance(g, dict):
            continue
        name = str(g.get("name", "")).strip()
        if not name:
            continue
        out_dict[name] = {
            "kind": str(g.get("kind", "")),
            "members": [str(m) for m in (g.get("members") or [])],
            "rationale": str(g.get("rationale", "")).strip(),
        }

    out = {"groupings": out_dict}
    if cache is not None and cache_key is not None:
        cache.put(cache_key, out)
    return out


# ── Internals ──────────────────────────────────────────────


def _render_firings_block(contexts: list) -> str:
    """Pre-format the firings list for the prompt template.

    One block per firing showing patternId, severity, hits, description,
    and the resolved affected evidence labels. Designed so the model
    sees each firing in a consistent, scannable format rather than
    interpolating raw FiringContext repr.
    """
    lines: list[str] = []
    for i, ctx in enumerate(contexts, start=1):
        if isinstance(ctx, FiringContext):
            lines.append(f"{i}. {ctx.pattern_id} ({ctx.severity}, {ctx.hits} hits)")
            if ctx.description:
                lines.append(f"   What it detects: {ctx.description}")
            if ctx.affected_evidence:
                labels = ", ".join(
                    e.get("label") or e.get("iri", "?")
                    for e in ctx.affected_evidence
                )
                lines.append(f"   Affected: {labels}")
            if ctx.constituent_firings:
                cons = ", ".join(
                    f"{c['patternId']}({c['severity']})"
                    for c in ctx.constituent_firings
                )
                lines.append(f"   Constituents: {cons}")
        elif isinstance(ctx, ViolationContext):
            lines.append(f"{i}. SHACL violation on {ctx.constraint_path} ({ctx.severity})")
            if ctx.affected_node:
                lines.append(f"   Affected node: {ctx.affected_node}")
            if ctx.description:
                lines.append(f"   Issue: {ctx.description}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _first_cou(contexts: list) -> dict:
    """First non-empty COU context across the items, as a dict for templates."""
    from dataclasses import asdict
    for ctx in contexts:
        cou = getattr(ctx, "cou", None)
        if cou is not None:
            return asdict(cou)
    return {}


def _first_pack(contexts: list) -> dict:
    """First non-empty pack context across the items, as a dict for templates."""
    from dataclasses import asdict
    for ctx in contexts:
        pack = getattr(ctx, "pack", None)
        if pack is not None:
            return asdict(pack)
    return {}


def _generate_and_parse(backend, prompt: str, gen_options: GenerationOptions) -> dict:
    """Fallback for backends without structured-output support."""
    text = backend.generate(prompt, gen_options).strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise


_SEVERITY_RANK = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


def _top_n(contexts: list, n: int) -> list:
    """Severity-then-hits sort, take top N. Mirrors explain.py's truncation."""
    def key(c):
        sev = getattr(c, "severity", "Medium")
        hits = getattr(c, "hits", 0)
        return (_SEVERITY_RANK.get(sev, 99), -hits)
    return sorted(contexts, key=key)[:n]
