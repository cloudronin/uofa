"""Plain-language firing explanation (spec v0.4 §2.1, P-B).

Per-firing LLM call producing 2-4 sentences of human-readable explanation
grounded in the firing's specific context (pattern ID, severity, hits, COU,
optional rule description). One LLM call per firing; the dispatcher merges
results into the InterpretationEnvelope's `explanations` slot.

Hard kill criterion (spec §8.3): SME-rated quality ≥ 80% useful-and-correct
on a 30-firing Morrison COU1 sample after one round of prompt iteration. If
missed, the entire interpretation work stops. The bundled prompt template
lives at `templates/rules/explain.jinja2` and is the surface to iterate on.
"""

from __future__ import annotations

import json
import logging
from contextlib import contextmanager

from uofa_cli.interpretation.cache import ExplanationCache, compute_key
from uofa_cli.interpretation.context import (
    DifferenceContext,
    FiringContext,
    ViolationContext,
)
from uofa_cli.interpretation.dispatcher import applies_to_commands
from uofa_cli.interpretation.envelope import INTERPRETATION_VERSION
from uofa_cli.interpretation.templates import has_template, render
from uofa_cli.llm.backend import GenerationOptions
from uofa_cli.llm.errors import LLMError

log = logging.getLogger(__name__)


@contextmanager
def _noop_cm(label: str = ""):  # noqa: ARG001
    """Fallback for callers that don't supply a spinner_factory in options."""
    yield


# Tight schema lets `generate_structured` enforce shape on backends that
# support response_format. Aligns with the JSON shape requested at the
# bottom of the prompt template.
#
# Round 1 (P-B): replaced single `explanation` with three structured
# fields per SME doc Task 2.4 — the split forces the model to do each
# piece of analytical work explicitly rather than producing prose that
# can elide any of them.
#
# Round 1 follow-up: dropped `confidence` because two iterations on
# bundled qwen3.5:4b produced 11/11 "high" regardless of explicit
# criteria. The model can't self-assess on this task; an always-true
# signal is misleading, so the honest answer is to remove the field
# rather than ship a misleading one.
_EXPLANATION_SCHEMA = {
    "type": "object",
    "properties": {
        "patternId": {"type": "string"},
        "severity": {"type": "string"},
        "affected_evidence_summary": {"type": "string"},
        "gap_description": {"type": "string"},
        "relevance_to_cou": {"type": "string"},
    },
    "required": ["patternId", "affected_evidence_summary", "gap_description"],
}


@applies_to_commands("rules", "check", "diff", "shacl")
def explain(
    *,
    command: str,
    contexts: list,
    structured_output,
    backend,
    options,
    cache: ExplanationCache | None = None,
) -> dict:
    """Run plain-language explanation per item.

    For rules / check: one explanation per FiringContext (uses
    `templates/rules/explain.jinja2`).
    For diff: one explanation per DifferenceContext (uses
    `templates/diff/explain.jinja2`, P-J / v0.6.1).
    For shacl: one explanation per ViolationContext (uses
    `templates/shacl/explain.jinja2`, P-K / v0.6.2).

    Returns ``{"explanations": [...]}`` for merge into the envelope.
    Failures on individual items are logged + a fallback dict is
    emitted with `error: True` so a single backend hiccup doesn't blow
    up the whole batch.

    `cache`, when provided AND `options.no_cache is False`, is used to
    short-circuit per-item LLM calls. Cache key includes prompt +
    backend + model + interpretation version.
    """
    pack_name = options.pack_name

    if command == "diff":
        return _explain_diff_contexts(
            contexts, pack_name, backend, options, cache,
        )
    if command == "shacl":
        return _explain_shacl_contexts(
            contexts, pack_name, backend, options, cache,
        )

    # rules / check path: filter to FiringContext (check mode passes
    # ViolationContext instances too; explain-for-shacl is P-K).
    if not has_template("rules", "explain", pack_name):
        log.warning(
            "No `rules/explain.jinja2` template found for pack %r; skipping",
            pack_name,
        )
        return {"explanations": []}

    firing_contexts = [c for c in contexts if isinstance(c, FiringContext)]
    if not firing_contexts:
        return {"explanations": []}

    if options.max_items is not None and options.max_items > 0:
        firing_contexts = _top_n_by_severity(firing_contexts, options.max_items)

    gen_options = _default_gen_options(options)
    use_cache = cache is not None and not getattr(options, "no_cache", False)
    spinner_factory = getattr(options, "spinner_factory", None) or _noop_cm
    n = len(firing_contexts)

    explanations: list[dict] = []
    for i, ctx in enumerate(firing_contexts, 1):
        with spinner_factory(f"[{i}/{n}] Explaining {ctx.pattern_id}..."):
            explanation = _explain_one(
                ctx, pack_name, backend, gen_options,
                cache=cache if use_cache else None,
            )
        explanations.append(explanation)
    return {"explanations": explanations}


def _explain_diff_contexts(
    contexts: list,
    pack_name: str,
    backend,
    options,
    cache: ExplanationCache | None,
) -> dict:
    """Per-difference explanation for `diff` command (P-J / v0.6.1)."""
    if not has_template("diff", "explain", pack_name):
        log.warning(
            "No `diff/explain.jinja2` template found for pack %r; skipping",
            pack_name,
        )
        return {"explanations": []}

    diff_contexts = [c for c in contexts if isinstance(c, DifferenceContext)]
    if not diff_contexts:
        return {"explanations": []}

    # max_items truncation by severity rank then alphabetical patternId
    # (no `hits` on diff contexts since each represents one divergence).
    if options.max_items is not None and options.max_items > 0:
        diff_contexts = sorted(
            diff_contexts,
            key=lambda c: (_SEVERITY_RANK.get(c.severity, 99), c.pattern_id),
        )[:options.max_items]

    gen_options = _default_gen_options(options)
    use_cache = cache is not None and not getattr(options, "no_cache", False)
    spinner_factory = getattr(options, "spinner_factory", None) or _noop_cm
    n = len(diff_contexts)

    explanations: list[dict] = []
    for i, ctx in enumerate(diff_contexts, 1):
        with spinner_factory(f"[{i}/{n}] Explaining diff {ctx.pattern_id}..."):
            explanations.append(_explain_one_difference(
                ctx, pack_name, backend, gen_options,
                cache=cache if use_cache else None,
            ))
    return {"explanations": explanations}


def _explain_shacl_contexts(
    contexts: list,
    pack_name: str,
    backend,
    options,
    cache: ExplanationCache | None,
) -> dict:
    """Per-violation explanation for `shacl` command (P-K / v0.6.2)."""
    if not has_template("shacl", "explain", pack_name):
        log.warning(
            "No `shacl/explain.jinja2` template found for pack %r; skipping",
            pack_name,
        )
        return {"explanations": []}

    violation_contexts = [c for c in contexts if isinstance(c, ViolationContext)]
    if not violation_contexts:
        return {"explanations": []}

    if options.max_items is not None and options.max_items > 0:
        violation_contexts = sorted(
            violation_contexts,
            key=lambda c: (_SEVERITY_RANK.get(c.severity, 99), c.constraint_path),
        )[:options.max_items]

    gen_options = _default_gen_options(options)
    use_cache = cache is not None and not getattr(options, "no_cache", False)
    spinner_factory = getattr(options, "spinner_factory", None) or _noop_cm
    n = len(violation_contexts)

    explanations: list[dict] = []
    for i, ctx in enumerate(violation_contexts, 1):
        with spinner_factory(f"[{i}/{n}] Explaining {ctx.constraint_path}..."):
            explanations.append(_explain_one_violation(
                ctx, pack_name, backend, gen_options,
                cache=cache if use_cache else None,
            ))
    return {"explanations": explanations}


def _default_gen_options(options) -> GenerationOptions:
    return GenerationOptions(
        temperature=0.0,
        max_tokens=4096,
        timeout_seconds=options.timeout_seconds if hasattr(options, "timeout_seconds") else None,
        # Qwen3.5 + similar thinking-mode models consume the entire token
        # budget on hidden reasoning by default, returning empty content
        # for short tasks like this one. Explanation is translation, not
        # reasoning — turn thinking off so the model spends its budget
        # on the user-facing JSON output.
        extra={"think": False},
    )


# ── Internals ──────────────────────────────────────────────


def _explain_one(
    ctx: FiringContext,
    pack_name: str,
    backend,
    gen_options: GenerationOptions,
    *,
    cache: ExplanationCache | None = None,
) -> dict:
    """Render the prompt + call the backend + parse the result.

    When `cache` is non-None, looks up the result by content-derived key
    before calling the backend; on miss, calls the backend and stores the
    successful result (errors are NOT cached — a transient failure
    shouldn't poison subsequent runs).
    """
    template_vars = ctx.to_template_vars()
    prompt = render("rules", "explain", pack_name, **template_vars)

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

    try:
        if backend.supports_structured_output():
            try:
                result = backend.generate_structured(
                    prompt, _EXPLANATION_SCHEMA, gen_options,
                )
            except NotImplementedError:
                result = _generate_and_parse(backend, prompt, gen_options)
        else:
            result = _generate_and_parse(backend, prompt, gen_options)
    except (LLMError, json.JSONDecodeError, ValueError) as exc:
        # Non-fatal for the whole batch — emit a fallback so the envelope
        # stays well-formed and the user sees which firings didn't get an
        # explanation. `error: True` is the structural signal that this
        # explanation is degraded (callers can branch on it). Catches:
        # - LLMError: backend-level failures (auth, rate limit, timeout, ...)
        # - JSONDecodeError: model returned empty / unparseable text
        # - ValueError: brace-match fallback couldn't extract JSON
        diagnostic = exc.diagnostic if isinstance(exc, LLMError) else str(exc)
        log.warning(
            "explain failed for firing %s: %s", ctx.pattern_id, diagnostic,
        )
        return {
            "patternId": ctx.pattern_id,
            "severity": ctx.severity,
            "affected_evidence_summary": "",
            "gap_description": f"(explanation unavailable: {diagnostic})",
            "relevance_to_cou": "",
            "error": True,
        }

    # Defensive normalization. Round 1 hardening (post-SME bug report):
    # `patternId` and `severity` are authoritative from the firing context,
    # NOT from the model's response. The model is asked to echo them back
    # for schema-compliance reasons, but its echo can hallucinate (we
    # observed `W-AL-01` → `W-AL-AL-01` in one Round 1 run). Trusting the
    # context value closes that whole class of identifier-hallucination
    # bugs at one stroke.
    #
    # Prose fields (affected_evidence_summary, gap_description,
    # relevance_to_cou) come from the model — that's the whole point —
    # but we coerce to str + strip so misshapen responses don't leak
    # untyped values into the envelope.
    out = {
        "patternId": ctx.pattern_id,
        "severity": ctx.severity,
        "affected_evidence_summary": str(result.get("affected_evidence_summary") or "").strip(),
        "gap_description": str(result.get("gap_description") or "").strip(),
        "relevance_to_cou": str(result.get("relevance_to_cou") or "").strip(),
    }
    if cache is not None and cache_key is not None:
        cache.put(cache_key, out)
    return out


def _generate_and_parse(backend, prompt: str, gen_options: GenerationOptions) -> dict:
    """Fallback for backends without structured-output support."""
    text = backend.generate(prompt, gen_options)
    text = text.strip()
    # Strip markdown code fences if present — same treatment as
    # llm_extractor._parse_response, kept local to avoid coupling.
    if text.startswith("```"):
        # Strip ```json or ``` opening + closing fence
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Last-ditch brace match — extract the first {...} block
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise


def _explain_one_difference(
    ctx: DifferenceContext,
    pack_name: str,
    backend,
    gen_options: GenerationOptions,
    *,
    cache: ExplanationCache | None = None,
) -> dict:
    """Per-difference variant of `_explain_one`. Renders diff/explain.jinja2
    and produces the same 3-field output shape so `explanations` slot is
    homogeneous regardless of source command."""
    template_vars = ctx.to_template_vars()
    prompt = render("diff", "explain", pack_name, **template_vars)

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

    try:
        if backend.supports_structured_output():
            try:
                result = backend.generate_structured(prompt, _EXPLANATION_SCHEMA, gen_options)
            except NotImplementedError:
                result = _generate_and_parse(backend, prompt, gen_options)
        else:
            result = _generate_and_parse(backend, prompt, gen_options)
    except (LLMError, json.JSONDecodeError, ValueError) as exc:
        diagnostic = exc.diagnostic if isinstance(exc, LLMError) else str(exc)
        log.warning(
            "explain (diff) failed for difference %s: %s", ctx.pattern_id, diagnostic,
        )
        return {
            "patternId": ctx.pattern_id,
            "severity": ctx.severity,
            "affected_evidence_summary": "",
            "gap_description": f"(explanation unavailable: {diagnostic})",
            "relevance_to_cou": "",
            "error": True,
        }

    out = {
        "patternId": ctx.pattern_id,    # authoritative; ignore model echo
        "severity": ctx.severity,
        "affected_evidence_summary": str(result.get("affected_evidence_summary") or "").strip(),
        "gap_description": str(result.get("gap_description") or "").strip(),
        "relevance_to_cou": str(result.get("relevance_to_cou") or "").strip(),
    }
    if cache is not None and cache_key is not None:
        cache.put(cache_key, out)
    return out


def _explain_one_violation(
    ctx: ViolationContext,
    pack_name: str,
    backend,
    gen_options: GenerationOptions,
    *,
    cache: ExplanationCache | None = None,
) -> dict:
    """Per-violation variant of `_explain_one`. Renders shacl/explain.jinja2.

    Output uses the same 3-field shape as rules/diff explanations so the
    envelope's `explanations` slot is homogeneous regardless of source
    command. `patternId` field carries the SHACL constraint path
    (e.g. "uofa:hasContextOfUse") rather than a weakener pattern ID.
    """
    template_vars = ctx.to_template_vars()
    prompt = render("shacl", "explain", pack_name, **template_vars)

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

    try:
        if backend.supports_structured_output():
            try:
                result = backend.generate_structured(prompt, _EXPLANATION_SCHEMA, gen_options)
            except NotImplementedError:
                result = _generate_and_parse(backend, prompt, gen_options)
        else:
            result = _generate_and_parse(backend, prompt, gen_options)
    except (LLMError, json.JSONDecodeError, ValueError) as exc:
        diagnostic = exc.diagnostic if isinstance(exc, LLMError) else str(exc)
        log.warning(
            "explain (shacl) failed for violation %s: %s",
            ctx.constraint_path, diagnostic,
        )
        return {
            "patternId": ctx.constraint_path,
            "severity": ctx.severity,
            "affected_evidence_summary": "",
            "gap_description": f"(explanation unavailable: {diagnostic})",
            "relevance_to_cou": "",
            "error": True,
        }

    out = {
        "patternId": ctx.constraint_path,   # authoritative; ignore model echo
        "severity": ctx.severity,
        "affected_evidence_summary": str(result.get("affected_evidence_summary") or "").strip(),
        "gap_description": str(result.get("gap_description") or "").strip(),
        "relevance_to_cou": str(result.get("relevance_to_cou") or "").strip(),
    }
    if cache is not None and cache_key is not None:
        cache.put(cache_key, out)
    return out


_SEVERITY_RANK = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


def _top_n_by_severity(contexts: list[FiringContext], n: int) -> list[FiringContext]:
    """Sort by (severity rank ASC, hits DESC) and take the first n.

    Implements `--explain-max-items` semantics from spec §3.2: "Limit
    interpretation to top N items by severity." Hits is the secondary
    sort so within a severity tier, more-frequent patterns come first.
    """
    return sorted(
        contexts,
        key=lambda c: (_SEVERITY_RANK.get(c.severity, 99), -c.hits),
    )[:n]
