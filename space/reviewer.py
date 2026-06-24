"""Reviewer view: render the shared analysis object as one print-clean HTML
panel for a non-simulation reader (regulatory associate, FDA reviewer).

Pure and framework-free (string in, string out) so it is unit-testable without
Gradio. The six sections are plain semantic HTML wrapped in
`#ri-reviewer-host .ri-reviewer`; the app's @media print rule isolates that
subtree for Save-as-PDF. Trust is presented as computable gate pass/fail plus
plain signals, never a holistic "trustworthy: yes/no" verdict.

This file does NO interpretation of the payload: it calls build_reviewer_state
once, asserts the invariants, and renders purely from that single ReviewerState
(see space/reviewer_state.py). No panel computes its own counts, statuses, or
completeness, so the panels cannot drift into a contradictory page.
"""

from __future__ import annotations

import html

from space.reviewer_state import (
    ReviewerInvariantError,
    ReviewerState,
    Status,
    assert_reviewer_invariants,
    build_reviewer_state,
    sev_label,
)

__all__ = ["render_reviewer_html", "ReviewerInvariantError"]

INDICATIVE = "Indicative summary, not a formal acceptance decision."

# status -> (sort rank, css class). Gaps first, scoped-out last.
_STATUS_RANK = {Status.NOT_STATED: 0, Status.EVIDENCED: 1, Status.NOT_APPLICABLE: 2}
_STATUS_CLASS = {Status.NOT_STATED: "ri-no", Status.EVIDENCED: "ri-yes", Status.NOT_APPLICABLE: "ri-na"}


def _e(value) -> str:
    return html.escape(str(value)) if value is not None else ""


def _plural(n: int, singular: str, plural: str) -> str:
    return singular if n == 1 else plural


def _risk_phrase(mrl) -> str:
    if mrl is None:
        return "Not stated in the evidence"
    return f"Level {mrl} (higher levels require stronger evidence)"


def _section_context(s: ReviewerState) -> str:
    body = (f"<p>{_e(s.cou_description)}</p>" if s.cou_description
            else "<p>The evidence did not state a context of use in plain terms.</p>")
    device_line = f"<li><b>Device class:</b> {_e(s.device_class)}</li>" if s.device_class else ""
    return f"""
    <section>
      <h2>What this model was used for</h2>
      <p class="ri-lead">{_e(s.cou_name)}</p>
      {body}
      <ul class="ri-meta">
        <li><b>Assessed against:</b> {_e(s.standard)}</li>
        <li><b>Risk tier:</b> {_e(_risk_phrase(s.risk_level))}</li>
        {device_line}
      </ul>
    </section>"""


def _reconcile_clause(s: ReviewerState) -> str:
    """One sentence that ties the completeness % to the same required/concern
    data the rest of the page uses, so the panels read as one story."""
    level = f" at Level {s.risk_level}" if s.risk_level is not None else ""
    if s.required_all_accounted:
        tail = f"all factors required{level} are accounted for."
    else:
        bits = []
        if s.missing:
            k = len(s.missing)
            bits.append(f"{k} {_plural(k, 'factor', 'factors')} required{level} still "
                        f"{_plural(k, 'needs', 'need')} evidence (listed below)")
        if s.open_high_count:
            m = s.open_high_count
            bits.append(f"{m} high-severity {_plural(m, 'concern', 'concerns')} "
                        f"{_plural(m, 'remains', 'remain')} open")
        tail = "; ".join(bits) + " before this is review-ready."
    return f"{s.completeness_pct}% of all factors evidenced; {tail}"


def _section_glance(s: ReviewerState) -> str:
    sev_txt = ", ".join(
        f"{s.severity_counts[k]} {sev_label(k)}"
        for k in ("Critical", "High", "Medium", "Low") if s.severity_counts.get(k)
    ) or "none"
    auth_txt = "Yes" if s.authenticity.get("signed") else "No (unsigned demo)"
    return f"""
    <section>
      <h2>At a glance</h2>
      <dl class="ri-glance">
        <div><dt>Completeness</dt><dd>{s.completeness_pct}%</dd></div>
        <div><dt>Factors evidenced</dt><dd>{s.n_evidenced} of {s.n_expected}</dd></div>
        <div><dt>Concerns (weakeners)</dt><dd>{_e(sev_txt)}</dd></div>
        <div><dt>Authenticity verified</dt><dd>{auth_txt}</dd></div>
        <div><dt>Gate checks passed</dt><dd>{s.gates['passed']} of {s.gates['total']}</dd></div>
      </dl>
      <p class="ri-note">{_e(_reconcile_clause(s))}</p>
      <p class="ri-note">{INDICATIVE} Gate checks below are structural validity and
      completeness; they are not a judgment of whether to accept the model.</p>
    </section>"""


def _section_factors(s: ReviewerState) -> str:
    rows = sorted(s.factors, key=lambda f: (_STATUS_RANK[f.status], f.name))
    body = "".join(
        f"<tr class='{_STATUS_CLASS[f.status]}'><td>{_e(f.plain_name)}</td>"
        f"<td>{_e(f.what_it_means)}</td>"
        f"<td class='ri-stat'>{_e(f.status.value)}</td></tr>"
        for f in rows
    )
    return f"""
    <section>
      <h2>Credibility factors</h2>
      <table class="ri-factors">
        <thead><tr><th>Factor</th><th>What it means</th><th>Status</th></tr></thead>
        <tbody>{body}</tbody>
      </table>
    </section>"""


def _section_concerns(s: ReviewerState) -> str:
    if not s.concerns:
        return """
    <section>
      <h2>Concerns found</h2>
      <p>No concerns were flagged against this evidence.</p>
    </section>"""
    items = []
    for conc in s.concerns:
        hits_txt = f" (seen {conc.hits} times)" if conc.hits > 1 else ""
        where = f" Relates to: {_e(', '.join(conc.factors))}." if conc.factors else ""
        items.append(f"<li><b>{_e(conc.label)} concern{hits_txt}.</b> {_e(conc.description)}{where}</li>")
    return f"""
    <section>
      <h2>Concerns found</h2>
      <ul class="ri-concerns">{''.join(items)}</ul>
    </section>"""


def _section_missing(s: ReviewerState) -> str:
    if not s.missing:
        return """
    <section>
      <h2>What is still missing</h2>
      <p>Nothing required is missing: every required factor was evidenced or scoped out.</p>
    </section>"""
    by_name = {f.name: f for f in s.factors}
    items = "".join(
        f"<li><b>{_e(by_name[n].plain_name)}.</b> {_e(by_name[n].what_it_means)}</li>"
        for n in s.missing
    )
    return f"""
    <section>
      <h2>What is still missing</h2>
      <p>Ask the submitter to provide evidence for:</p>
      <ul class="ri-missing">{items}</ul>
    </section>"""


def _section_authenticity(s: ReviewerState) -> str:
    auth = s.authenticity
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
    """Render the shared analysis object as the reviewer verdict panel.

    Derives one ReviewerState, asserts the frozen invariants, then renders every
    section from that state. The content is wrapped in #ri-reviewer-host; the
    Save-as-PDF button lives in app.py as a gradio Button with a js= handler that
    clones this host into a clean white print window."""
    state = build_reviewer_state(analysis, gloss)
    assert_reviewer_invariants(state)
    return (
        _STYLE
        + '<div id="ri-reviewer-host"><div class="ri-reviewer">'
        + _section_context(state)
        + _section_glance(state)
        + _section_factors(state)
        + _section_concerns(state)
        + _section_missing(state)
        + _section_authenticity(state)
        + "</div></div>"
    )
