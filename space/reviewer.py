"""Reviewer view: render the shared analysis object as one print-clean HTML
panel for a non-simulation reader (regulatory associate, FDA reviewer).

Pure and framework-free (string in, string out) so it is unit-testable without
Gradio. The six sections are plain semantic HTML wrapped in
`#ri-reviewer-host .ri-reviewer`; the app's @media print rule isolates that
subtree for Save-as-PDF. Trust is presented as computable gate pass/fail plus
plain signals, never a holistic "trustworthy: yes/no" verdict.
"""

from __future__ import annotations

import html

from space.gloss import gloss_for
from space.summary import expected_factors

_SEV_WORD = {
    "Critical": "Critical concern",
    "High": "High concern",
    "Medium": "Moderate concern",
    "Low": "Low concern",
}
_SEV_RANK = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}

INDICATIVE = "Indicative summary, not a formal acceptance decision."


def _e(value) -> str:
    return html.escape(str(value)) if value is not None else ""


def _gates(analysis: dict) -> dict:
    """Two computable checks (not a verdict)."""
    structural_ok = bool(analysis.get("structural", {}).get("conforms"))
    completeness_ok = not analysis.get("completeness", {}).get("missing")
    return {"structural": structural_ok, "completeness": completeness_ok,
            "passed": int(structural_ok) + int(completeness_ok), "total": 2}


def _risk_phrase(mrl) -> str:
    if mrl is None:
        return "Not stated in the evidence"
    return f"Level {mrl} (higher levels require stronger evidence)"


def _section_context(ctx: dict) -> str:
    cou = ctx.get("cou_name") or "Not stated"
    desc = (ctx.get("cou_description") or "").strip()
    standard = ctx.get("standard") or ctx.get("pack") or "Not stated"
    risk = _risk_phrase(ctx.get("model_risk_level"))
    device = ctx.get("device_class")
    body = f"<p>{_e(desc)}</p>" if desc else "<p>The evidence did not state a context of use in plain terms.</p>"
    device_line = f"<li><b>Device class:</b> {_e(device)}</li>" if device else ""
    return f"""
    <section>
      <h2>What this model was used for</h2>
      <p class="ri-lead">{_e(cou)}</p>
      {body}
      <ul class="ri-meta">
        <li><b>Assessed against:</b> {_e(standard)}</li>
        <li><b>Risk tier:</b> {_e(risk)}</li>
        {device_line}
      </ul>
    </section>"""


def _section_glance(analysis: dict) -> str:
    c = analysis.get("completeness", {})
    n_assessed, denom = c.get("n_assessed", 0), c.get("denom", 0) or 0
    n_expected = c.get("n_expected", 0)
    pct = round(100 * n_assessed / denom) if denom else 0
    sev = analysis.get("weakener_severity", {}) or {}
    sev_txt = ", ".join(f"{sev[s]} {s}" for s in ("Critical", "High", "Medium", "Low") if sev.get(s)) or "none"
    auth = analysis.get("context", {}).get("authenticity", {})
    auth_txt = "Yes" if auth.get("signed") else "No (unsigned demo)"
    g = _gates(analysis)
    return f"""
    <section>
      <h2>At a glance</h2>
      <dl class="ri-glance">
        <div><dt>Completeness</dt><dd>{pct}%</dd></div>
        <div><dt>Factors evidenced</dt><dd>{n_assessed} of {n_expected}</dd></div>
        <div><dt>Concerns (weakeners)</dt><dd>{_e(sev_txt)}</dd></div>
        <div><dt>Authenticity verified</dt><dd>{auth_txt}</dd></div>
        <div><dt>Gate checks passed</dt><dd>{g['passed']} of {g['total']}</dd></div>
      </dl>
      <p class="ri-note">{INDICATIVE} Gate checks below are structural validity and
      completeness; they are not a judgment of whether to accept the model.</p>
    </section>"""


def _factor_status(name: str, c: dict) -> tuple[int, str, str]:
    """(sort_rank, label, css_class). Missing first, then assessed, excluded last."""
    if name in (c.get("missing") or []):
        return 0, "Not evidenced", "ri-no"
    if name in (c.get("excluded") or []):
        return 2, "Scoped out / N/A", "ri-na"
    if name in (c.get("assessed") or []):
        return 1, "Evidenced", "ri-yes"
    return 1, "Not stated", "ri-na"


def _section_factors(analysis: dict, gloss: dict) -> str:
    pack = analysis.get("pack", "vv40")
    c = analysis.get("completeness", {})
    rows = []
    for name in expected_factors(pack):
        rank, label, cls = _factor_status(name, c)
        g = gloss_for(name, gloss)
        rows.append((rank, name, g, label, cls))
    rows.sort(key=lambda r: (r[0], r[1]))
    body = "".join(
        f"<tr class='{cls}'><td>{_e(g['plain_name'])}</td>"
        f"<td>{_e(g['what_it_means'])}</td>"
        f"<td class='ri-stat'>{_e(label)}</td></tr>"
        for _rank, _name, g, label, cls in rows
    )
    return f"""
    <section>
      <h2>Credibility factors</h2>
      <table class="ri-factors">
        <thead><tr><th>Factor</th><th>What it means</th><th>Status</th></tr></thead>
        <tbody>{body}</tbody>
      </table>
    </section>"""


def _section_concerns(analysis: dict, gloss: dict) -> str:
    weak = sorted(analysis.get("weakeners", []) or [],
                  key=lambda w: _SEV_RANK.get(w.get("severity"), 9))
    if not weak:
        return """
    <section>
      <h2>Concerns found</h2>
      <p>No concerns were flagged against this evidence.</p>
    </section>"""
    items = []
    for w in weak:
        sev = _SEV_WORD.get(w.get("severity"), w.get("severity") or "Concern")
        why = (w.get("description") or "").strip()
        facs = w.get("factors") or []
        if not why and facs:
            why = gloss_for(facs[0], gloss).get("what_it_means", "")
        where = f" Relates to: {_e(', '.join(facs))}." if facs else ""
        hits = w.get("hits")
        hits_txt = f" (seen {hits} times)" if isinstance(hits, int) and hits > 1 else ""
        items.append(f"<li><b>{_e(sev)}{hits_txt}.</b> {_e(why)}{where}</li>")
    return f"""
    <section>
      <h2>Concerns found</h2>
      <ul class="ri-concerns">{''.join(items)}</ul>
    </section>"""


def _section_missing(analysis: dict, gloss: dict) -> str:
    missing = analysis.get("completeness", {}).get("missing") or []
    if not missing:
        return """
    <section>
      <h2>What is still missing</h2>
      <p>Nothing required is missing: every expected factor was assessed or scoped out.</p>
    </section>"""
    items = "".join(
        f"<li><b>{_e(gloss_for(n, gloss)['plain_name'])}.</b> "
        f"{_e(gloss_for(n, gloss)['what_it_means'])}</li>"
        for n in missing
    )
    return f"""
    <section>
      <h2>What is still missing</h2>
      <p>Ask the submitter to provide evidence for:</p>
      <ul class="ri-missing">{items}</ul>
    </section>"""


def _section_authenticity(analysis: dict) -> str:
    auth = analysis.get("context", {}).get("authenticity", {})
    if auth.get("signed"):
        verdict = "Verified"
        detail = (f"<li><b>Signed by:</b> {_e(auth.get('signer'))}</li>"
                  f"<li><b>Content hash:</b> <code>{_e(auth.get('package_hash'))}</code></li>")
    else:
        verdict = "Unverified (demo)"
        detail = f"<p>{_e(auth.get('statement'))}</p>"
    return f"""
    <section>
      <h2>Authenticity</h2>
      <p><b>Status:</b> {verdict}</p>
      {detail}
      <p>A technical colleague can re-verify a signed package with:</p>
      <pre class="ri-cmd">uofa check &lt;package&gt;.jsonld</pre>
    </section>"""


_STYLE = """
<style>
.ri-reviewer { font-family: 'IBM Plex Sans', system-ui, sans-serif; color: #e8e6e1;
  line-height: 1.6; max-width: 60rem; }
.ri-reviewer h2 { font-family: 'Fraunces', Georgia, serif; font-weight: 500;
  font-size: 1.375rem; margin: 1.6rem 0 0.5rem; }
.ri-reviewer .ri-lead { font-size: 1.1rem; }
.ri-reviewer .ri-note { color: #9a988f; font-size: 0.9rem; }
.ri-reviewer ul, .ri-reviewer dl { margin: 0.5rem 0; }
.ri-reviewer .ri-glance { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem; }
.ri-reviewer .ri-glance dt { color: #9a988f; font-size: 0.8rem; text-transform: uppercase;
  letter-spacing: 0.03em; }
.ri-reviewer .ri-glance dd { margin: 0; font-size: 1.05rem; }
.ri-reviewer table.ri-factors { width: 100%; border-collapse: collapse; }
.ri-reviewer .ri-factors th, .ri-reviewer .ri-factors td { text-align: left;
  padding: 0.45rem 0.6rem; border-bottom: 1px solid #25262c; vertical-align: top; }
.ri-reviewer .ri-factors th { color: #9a988f; font-size: 0.8rem; text-transform: uppercase; }
.ri-reviewer .ri-stat { white-space: nowrap; font-weight: 500; }
.ri-reviewer tr.ri-no .ri-stat { color: #c97864; }
.ri-reviewer tr.ri-yes .ri-stat { color: #7eb87a; }
.ri-reviewer tr.ri-na .ri-stat { color: #9a988f; }
.ri-reviewer .ri-cmd { background: #131418; border: 1px solid #25262c; border-radius: 6px;
  padding: 0.5rem 0.75rem; font-family: 'IBM Plex Mono', monospace; color: #d4a35a; }
.ri-reviewer .ri-pdf-btn { margin-top: 1.5rem; background: #131418; color: #e8e6e1;
  border: 1px solid #3a3b42; border-radius: 6px; padding: 0.5rem 1rem; cursor: pointer;
  font-family: inherit; }
</style>"""


def render_reviewer_html(analysis: dict, gloss: dict | None = None) -> str:
    """Render the shared analysis object as the reviewer verdict panel."""
    ctx = analysis.get("context", {}) or {}
    return (
        _STYLE
        + '<div id="ri-reviewer-host"><div class="ri-reviewer">'
        + _section_context(ctx)
        + _section_glance(analysis)
        + _section_factors(analysis, gloss)
        + _section_concerns(analysis, gloss)
        + _section_missing(analysis, gloss)
        + _section_authenticity(analysis)
        + '<button class="ri-pdf-btn" onclick="window.print()">Save as PDF</button>'
        + "</div></div>"
    )
