"""Output formatters for InterpretationEnvelope (spec v0.4 §4.6, P-M).

Pure functions: each takes an envelope and returns a string. `cli.py` uses
them via the `Format` dispatch table; consumers wanting the rendered string
without printing (Tauri, tests, debug tooling) call them directly.

Four formats per spec:
- text: ANSI-colored CLI output, integrates `output.py` severity badges
- json: spec §4.5 envelope serialization (machine-readable; Tauri consumes this)
- markdown: GitHub-flavored, suitable for PR comments / issue bodies
- html: standalone fragment suitable for embedding in reports

The text formatter is the only one that mutates output via `output.py`'s
ANSI helpers — those auto-disable when `--no-color` is set or `NO_COLOR`
is in the env, so the formatter is safe in non-TTY contexts too.
"""

from __future__ import annotations

import html
import json as _json
from typing import Literal

from uofa_cli.interpretation.envelope import InterpretationEnvelope
from uofa_cli.output import color, severity_badge

Format = Literal["text", "json", "markdown", "html"]


# ── Public dispatch ────────────────────────────────────────


def render_envelope(env: InterpretationEnvelope, *, format: Format = "text") -> str:
    """Render `env` to the requested format. Pure function — no I/O."""
    if format == "json":
        return render_json(env)
    if format == "markdown":
        return render_markdown(env)
    if format == "html":
        return render_html(env)
    return render_text(env)


# ── JSON ───────────────────────────────────────────────────


def render_json(env: InterpretationEnvelope) -> str:
    """Spec §4.5 envelope, pretty-printed. Stable contract for Tauri."""
    return _json.dumps(env.to_dict(), indent=2)


# ── Text (ANSI-colored CLI) ────────────────────────────────


def render_text(env: InterpretationEnvelope) -> str:
    """ANSI-colored CLI rendering — `output.py` color helpers honor NO_COLOR."""
    if env.interpretation is None:
        return ""
    interp = env.interpretation
    lines: list[str] = []
    lines.append("")
    lines.append(color("══ Interpretation ══", "bold"))
    lines.append(f"  Backend: {color(interp.interpretation_backend, 'cyan')}"
                 f" / {color(interp.interpretation_model, 'cyan')}")
    lines.append(f"  Functions run: {', '.join(interp.functions_run) or color('(none)', 'dim')}")
    lines.append("")

    if interp.explanations:
        lines.append(color("Explanations:", "bold"))
        for e in interp.explanations:
            pid = e.get("patternId", "?")
            sev = e.get("severity", "?")
            err = color(" [unavailable]", "red") if e.get("error") else ""
            lines.append(f"  {severity_badge(sev)} {color(pid, 'bold')}{err}")
            # v0.4.0 schema: three prose fields. Render each on a labeled
            # line so the structure is scannable. Skip empty fields.
            for label, key in (
                ("Affected evidence", "affected_evidence_summary"),
                ("Gap", "gap_description"),
                ("Relevance to COU", "relevance_to_cou"),
            ):
                value = e.get(key, "") or ""
                if not value:
                    continue
                lines.append(f"      {color(label + ':', 'cyan')}")
                for body_line in value.splitlines():
                    lines.append(f"        {body_line}")
            lines.append("")

    if interp.groupings:
        lines.append(color(f"Groupings ({len(interp.groupings)}):", "bold"))
        for theme, info in interp.groupings.items():
            # P-F: each value is now a dict {kind, members, rationale}.
            # Older callers may have stored a bare list; handle both.
            if isinstance(info, dict):
                kind = info.get("kind", "")
                members = info.get("members", [])
                rationale = info.get("rationale", "")
                kind_str = f" [{kind}]" if kind else ""
                members_str = ", ".join(members) if isinstance(members, list) else str(members)
                lines.append(f"  • {color(theme, 'cyan')}{color(kind_str, 'dim')}")
                if members_str:
                    lines.append(f"      members: {members_str}")
                if rationale:
                    for body_line in rationale.splitlines():
                        lines.append(f"      {body_line}")
            else:
                # Back-compat: bare list of members
                members_str = ", ".join(info) if isinstance(info, list) else str(info)
                lines.append(f"  • {color(theme, 'cyan')}: {members_str}")
        lines.append("")

    if interp.contextual_severity:
        lines.append(color("Contextual severity (1 = most consequential for this COU):", "bold"))
        # Sort by rank ascending so the most-important firing prints first
        sorted_items = sorted(
            interp.contextual_severity.items(),
            key=lambda kv: kv[1].get("rank", 99) if isinstance(kv[1], dict) else 99,
        )
        for pid, info in sorted_items:
            if isinstance(info, dict):
                rank = info.get("rank", "?")
                rationale = info.get("rationale", "")
                lines.append(f"  {color(f'#{rank}', 'bold')} {color(pid, 'cyan')}")
                if rationale:
                    for body_line in rationale.splitlines():
                        lines.append(f"      {body_line}")
            else:
                lines.append(f"  • {color(pid, 'bold')}: rank {info}")
        lines.append("")

    if interp.cross_patterns:
        lines.append(color(f"Cross-item patterns ({len(interp.cross_patterns)}):", "bold"))
        for pat in interp.cross_patterns:
            if isinstance(pat, dict):
                name = pat.get("name", "(unnamed)")
                desc = pat.get("description", "")
                involved = pat.get("involved_firings", [])
                lines.append(f"  • {color(name, 'cyan')}")
                if involved:
                    lines.append(f"      involves: {', '.join(involved)}")
                if desc:
                    for body_line in desc.splitlines():
                        lines.append(f"      {body_line}")
            else:
                lines.append(f"  • {color(str(pat), 'cyan')}")
        lines.append("")

    if interp.narratives:
        lines.append(color(f"Surviving-set narratives ({len(interp.narratives)}):", "bold"))
        for n in interp.narratives:
            cou = n.get("cou", "?") if isinstance(n, dict) else "?"
            text = n.get("text", "") if isinstance(n, dict) else str(n)
            lines.append(f"  • {color(cou, 'cyan')}")
            for body_line in text.splitlines():
                lines.append(f"      {body_line}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ── Markdown ──────────────────────────────────────────────


def render_markdown(env: InterpretationEnvelope) -> str:
    """GitHub-flavored markdown — suitable for PR comments, issue bodies, docs."""
    if env.interpretation is None:
        return ""
    interp = env.interpretation
    lines: list[str] = []
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(f"_Backend: `{interp.interpretation_backend}` / `{interp.interpretation_model}`_  ")
    lines.append(f"_Functions run: {', '.join(f'`{n}`' for n in interp.functions_run) or '_none_'}_")
    lines.append("")

    if interp.explanations:
        lines.append("### Explanations")
        lines.append("")
        for e in interp.explanations:
            pid = e.get("patternId", "?")
            sev = e.get("severity", "?")
            err_marker = " ⚠️ unavailable" if e.get("error") else ""
            lines.append(f"#### `{pid}` ({sev}){err_marker}")
            lines.append("")
            # Round 1 schema: four prose fields. Render each as a labeled
            # subsection with bold label + body paragraph. Skip empty fields.
            any_field = False
            for label, key in (
                ("Affected evidence", "affected_evidence_summary"),
                ("Gap", "gap_description"),
                ("Relevance to COU", "relevance_to_cou"),
            ):
                value = e.get(key, "") or ""
                if not value:
                    continue
                lines.append(f"**{label}:** {value}")
                lines.append("")
                any_field = True
            if not any_field:
                lines.append("_No explanation produced._")
                lines.append("")

    if interp.groupings:
        lines.append(f"### Groupings ({len(interp.groupings)})")
        lines.append("")
        for theme, info in interp.groupings.items():
            if isinstance(info, dict):
                kind = info.get("kind", "")
                members = info.get("members", [])
                rationale = info.get("rationale", "")
                kind_suffix = f" _({kind})_" if kind else ""
                members_str = ", ".join(f"`{m}`" for m in members) if isinstance(members, list) else f"`{members}`"
                lines.append(f"#### {theme}{kind_suffix}")
                lines.append("")
                if members_str:
                    lines.append(f"**Members:** {members_str}")
                    lines.append("")
                if rationale:
                    lines.append(rationale)
                    lines.append("")
            else:
                members_str = ", ".join(f"`{m}`" for m in info) if isinstance(info, list) else f"`{info}`"
                lines.append(f"- **{theme}**: {members_str}")
        lines.append("")

    if interp.contextual_severity:
        lines.append("### Contextual severity")
        lines.append("")
        lines.append("_Ranked 1..N where 1 is most consequential for this COU._")
        lines.append("")
        sorted_items = sorted(
            interp.contextual_severity.items(),
            key=lambda kv: kv[1].get("rank", 99) if isinstance(kv[1], dict) else 99,
        )
        for pid, info in sorted_items:
            if isinstance(info, dict):
                rank = info.get("rank", "?")
                rationale = info.get("rationale", "")
                lines.append(f"#### #{rank} — `{pid}`")
                lines.append("")
                if rationale:
                    lines.append(rationale)
                    lines.append("")
            else:
                lines.append(f"- `{pid}` — rank {info}")
        lines.append("")

    if interp.cross_patterns:
        lines.append(f"### Cross-item patterns ({len(interp.cross_patterns)})")
        lines.append("")
        for pat in interp.cross_patterns:
            if isinstance(pat, dict):
                name = pat.get("name", "(unnamed)")
                desc = pat.get("description", "")
                involved = pat.get("involved_firings", [])
                lines.append(f"#### {name}")
                lines.append("")
                if involved:
                    lines.append(f"**Involves:** {', '.join(f'`{p}`' for p in involved)}")
                    lines.append("")
                if desc:
                    lines.append(desc)
                    lines.append("")
            else:
                lines.append(f"- {pat}")
        lines.append("")

    if interp.narratives:
        lines.append(f"### Surviving-set narratives ({len(interp.narratives)})")
        lines.append("")
        for n in interp.narratives:
            cou = n.get("cou", "?") if isinstance(n, dict) else "?"
            text = n.get("text", "") if isinstance(n, dict) else str(n)
            lines.append(f"#### {cou}")
            lines.append("")
            lines.append(text)
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ── HTML ──────────────────────────────────────────────────


def render_html(env: InterpretationEnvelope) -> str:
    """Standalone HTML fragment. Suitable for embedding in `<div>` containers
    or copying into a report builder. Not a full document — caller wraps if
    needed (in a `<html><body>` shell). All user-visible text is escaped.

    The CSS class names follow `uofa-explain-*` for safe namespacing.
    """
    if env.interpretation is None:
        return ""
    interp = env.interpretation
    parts: list[str] = []
    parts.append('<div class="uofa-explain">')
    parts.append('<h2 class="uofa-explain-heading">Interpretation</h2>')
    parts.append('<p class="uofa-explain-meta">')
    parts.append(f'<em>Backend: <code>{html.escape(interp.interpretation_backend)}</code> / '
                 f'<code>{html.escape(interp.interpretation_model)}</code></em><br>')
    parts.append('<em>Functions run: ')
    if interp.functions_run:
        parts.append(", ".join(f'<code>{html.escape(n)}</code>' for n in interp.functions_run))
    else:
        parts.append('<em>none</em>')
    parts.append('</em></p>')

    if interp.explanations:
        parts.append('<section class="uofa-explain-explanations">')
        parts.append('<h3>Explanations</h3>')
        for e in interp.explanations:
            pid = html.escape(str(e.get("patternId", "?")))
            sev = html.escape(str(e.get("severity", "?")))
            err_attr = ' data-error="true"' if e.get("error") else ""
            parts.append(f'<article class="uofa-explain-firing"{err_attr}>')
            parts.append(f'<h4><code>{pid}</code> '
                         f'<span class="uofa-explain-sev sev-{sev.lower()}">{sev}</span>'
                         '</h4>')
            # Round 1 schema: four prose fields rendered as labeled <dl>
            # entries (definition list — semantic + good for screen readers).
            any_field = False
            dl_parts: list[str] = []
            for label, key, css_key in (
                ("Affected evidence", "affected_evidence_summary", "evidence"),
                ("Gap", "gap_description", "gap"),
                ("Relevance to COU", "relevance_to_cou", "relevance"),
            ):
                value = e.get(key, "") or ""
                if not value:
                    continue
                any_field = True
                dl_parts.append(
                    f'<dt class="uofa-explain-{css_key}-label">{html.escape(label)}</dt>'
                    f'<dd class="uofa-explain-{css_key}">{html.escape(value)}</dd>'
                )
            if any_field:
                parts.append('<dl class="uofa-explain-fields">')
                parts.extend(dl_parts)
                parts.append('</dl>')
            parts.append('</article>')
        parts.append('</section>')

    if interp.groupings:
        parts.append('<section class="uofa-explain-groupings">')
        parts.append(f'<h3>Groupings ({len(interp.groupings)})</h3>')
        for theme, info in interp.groupings.items():
            theme_safe = html.escape(str(theme))
            if isinstance(info, dict):
                kind = html.escape(str(info.get("kind", "")))
                members = info.get("members", [])
                rationale = html.escape(str(info.get("rationale", "")))
                members_html = (
                    ", ".join(f'<code>{html.escape(str(m))}</code>' for m in members)
                    if isinstance(members, list) else f'<code>{html.escape(str(members))}</code>'
                )
                # Hoist the kind-span out of the f-string: nested f-strings
                # with escaped quotes are a Python 3.12+ feature, and we
                # support 3.11 per pyproject.toml requires-python.
                kind_class = kind.replace(" ", "-")
                kind_span = f' <span class="kind">({kind})</span>' if kind else ""
                parts.append(f'<article class="uofa-explain-grouping kind-{kind_class}">')
                parts.append(f'<h4>{theme_safe}{kind_span}</h4>')
                if members_html:
                    parts.append(f'<p class="members"><strong>Members:</strong> {members_html}</p>')
                if rationale:
                    parts.append(f'<p class="rationale">{rationale}</p>')
                parts.append('</article>')
            else:
                members_html = (
                    ", ".join(f'<code>{html.escape(str(m))}</code>' for m in info)
                    if isinstance(info, list) else f'<code>{html.escape(str(info))}</code>'
                )
                parts.append(f'<p><strong>{theme_safe}</strong>: {members_html}</p>')
        parts.append('</section>')

    if interp.contextual_severity:
        parts.append('<section class="uofa-explain-contextual">')
        parts.append('<h3>Contextual severity</h3>')
        parts.append('<p class="uofa-explain-meta"><em>Ranked 1..N where 1 is most consequential for this COU.</em></p>')
        sorted_items = sorted(
            interp.contextual_severity.items(),
            key=lambda kv: kv[1].get("rank", 99) if isinstance(kv[1], dict) else 99,
        )
        parts.append('<ol class="uofa-explain-rank">')
        for pid, info in sorted_items:
            pid_safe = html.escape(str(pid))
            if isinstance(info, dict):
                rationale = html.escape(str(info.get("rationale", "")))
                parts.append(f'<li><code>{pid_safe}</code>')
                if rationale:
                    parts.append(f' — {rationale}')
                parts.append('</li>')
            else:
                parts.append(f'<li><code>{pid_safe}</code> — rank {html.escape(str(info))}</li>')
        parts.append('</ol>')
        parts.append('</section>')

    if interp.cross_patterns:
        parts.append('<section class="uofa-explain-cross">')
        parts.append(f'<h3>Cross-item patterns ({len(interp.cross_patterns)})</h3>')
        for pat in interp.cross_patterns:
            if isinstance(pat, dict):
                name = html.escape(str(pat.get("name", "(unnamed)")))
                desc = html.escape(str(pat.get("description", "")))
                involved = pat.get("involved_firings", [])
                parts.append(f'<article class="uofa-explain-pattern"><h4>{name}</h4>')
                if involved:
                    involved_html = ", ".join(f'<code>{html.escape(str(p))}</code>' for p in involved)
                    parts.append(f'<p class="involved"><strong>Involves:</strong> {involved_html}</p>')
                if desc:
                    parts.append(f'<p>{desc}</p>')
                parts.append('</article>')
            else:
                parts.append(f'<p>{html.escape(str(pat))}</p>')
        parts.append('</section>')

    if interp.narratives:
        parts.append('<section class="uofa-explain-narratives">')
        parts.append(f'<h3>Surviving-set narratives ({len(interp.narratives)})</h3>')
        for n in interp.narratives:
            cou = html.escape(str(n.get("cou", "?") if isinstance(n, dict) else "?"))
            text = html.escape(str(n.get("text", "") if isinstance(n, dict) else n))
            parts.append(f'<article class="uofa-explain-narrative"><h4>{cou}</h4>')
            parts.append(f'<p>{text}</p>')
            parts.append('</article>')
        parts.append('</section>')

    parts.append('</div>')
    return "\n".join(parts) + "\n"
