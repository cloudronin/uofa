"""Gradio wizard for the UofA Gap-Finder Space.

Thin UI over space.wizard (which holds the testable step logic). Flow:
  upload/sample -> route (confirm standard) -> extract -> confirm status
  -> free summary -> contact capture.

Set UOFA_SPACE_MODEL=mock to drive the UI locally without Ollama.
"""

from __future__ import annotations

import os
import queue
import threading
from pathlib import Path

import gradio as gr

from space import leadcapture, pipeline, wizard
from uofa_cli import paths

PACK_LABELS = {"vv40": "ASME V&V 40", "nasa-7009b": "NASA-STD-7009B"}
PACK_CHOICES = [(label, pid) for pid, label in PACK_LABELS.items()]
STATUS_CHOICES = ["assessed", "not-assessed", "scoped-out", "not-applicable"]

_MODEL = os.environ.get("UOFA_SPACE_MODEL") or None  # None -> bundled qwen3.5:4b
# In-container the wheel bundles packs/ under uofa_cli/_data/repo; an env var lets
# a deployment point elsewhere without code changes.
_SAMPLE_DIR = Path(
    os.environ.get("UOFA_SPACE_SAMPLE_DIR")
    or paths.find_repo_root() / "packs" / "vv40" / "examples" / "morrison" / "source"
)

COLD_START_NOTE = (
    "Your documents are read **privately inside this Space**. Nothing is stored "
    "or sent to a third party. The first analysis after the Space wakes can take "
    "a few minutes while the model loads."
)

# Dark theme to match uofa.net. The Space is embedded via an <iframe>, so the
# body needs a SOLID dark background (a transparent body would show the iframe's
# default white, since there's no dark parent behind it inside the frame). A
# neutral gray hue sits closer to the site's near-black than gradio's slate.
# Block borders/shadows are zeroed to avoid stray divider rules.
THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.orange,
    neutral_hue=gr.themes.colors.gray,
).set(
    block_border_width="0px",
    block_shadow="none",
    panel_border_width="0px",
)

CSS = """
.gradio-container { max-width: 900px !important; margin: 0 auto !important;
  font-family: var(--sl-font, Inter, system-ui, sans-serif); }
/* Long headlines must wrap, not clip, at narrow widths. */
.gradio-container h1, .gradio-container h2, .gradio-container h3 {
  overflow-wrap: anywhere; word-break: break-word; white-space: normal;
  font-size: clamp(1.1rem, 4vw, 1.6rem); line-height: 1.3; }
/* Hide the default Gradio footer (Use via API / Built with Gradio / Settings). */
footer { display: none !important; }
/* Empty/placeholder markdown blocks must not render as stray rules. */
.prose:empty, .md:empty { display: none !important; margin: 0 !important;
  padding: 0 !important; border: 0 !important; }
/* Themed focus ring (replaces the browser-default blue). */
*:focus-visible { outline: 2px solid var(--sl-color-accent, #f97316) !important;
  outline-offset: 2px; border-radius: 4px; }
/* Lightweight step header. */
.step-tag { font-size: 0.8rem; letter-spacing: 0.04em; text-transform: uppercase;
  opacity: 0.7; margin-bottom: 0.25rem; }
.factor-levels { opacity: 0.6; font-size: 0.85em; }
"""


def _hide():
    return gr.update(visible=False)


def _show():
    return gr.update(visible=True)


def _step_tag(n: int, label: str) -> str:
    return f"<div class='step-tag'>Step {n} of 4 · {label}</div>"


# Outputs for the prepare/route transition (order matters; see wiring).
# [read_progress, upload_group, route_group, why_md, pack_radio, analyze_btn,
#  route_warn, corpus_state, decision_state, warnings_state, source_name_state, error_md]


def _stream_prepare(sources, source_name):
    """Generator: stream per-file reading progress, then reveal the Route step."""
    q: queue.Queue = queue.Queue()
    holder: dict = {}

    def worker():
        holder["outcome"] = wizard.prepare(sources, on_progress=lambda m: q.put(("msg", m)))
        q.put(("done", None))

    threading.Thread(target=worker, daemon=True).start()

    log: list[str] = []
    while True:
        kind, msg = q.get()
        if kind == "done":
            break
        log.append(f"- {msg}")
        yield (
            gr.update(value="**Reading evidence**\n" + "\n".join(log), visible=True),
            _hide(), _hide(), gr.update(), gr.update(), gr.update(), gr.update(),
            None, None, None, source_name, gr.update(value="", visible=False),
        )

    outcome = holder["outcome"]
    if not outcome.ok:
        yield (
            _hide(), _show(), _hide(), gr.update(), gr.update(), gr.update(), gr.update(),
            None, None, None, source_name,
            gr.update(value=f"⚠️ {outcome.user_message}", visible=True),
        )
        return

    decision = outcome.payload["decision"]
    low = wizard.requires_confirmation(decision)
    yield (
        _hide(),                                          # read_progress
        _hide(),                                          # upload_group
        _show(),                                          # route_group
        gr.update(value=f"**Routing.** {decision.why}"),  # why_md
        gr.update(value=decision.primary),                # pack_radio
        gr.update(interactive=not low),                   # analyze_btn (gated if low-confidence)
        gr.update(visible=low),                           # route_warn
        outcome.payload["corpus"],
        decision,
        outcome.payload["warnings"],
        source_name,
        gr.update(value="", visible=False),
    )


def _detect_from_upload(files):
    sources = [Path(f) for f in (files or [])]
    if not sources:
        yield (
            _hide(), _show(), _hide(), gr.update(), gr.update(), gr.update(), gr.update(),
            None, None, None, "upload",
            gr.update(value="⚠️ Add at least one evidence document, or try the sample.", visible=True),
        )
        return
    yield from _stream_prepare(sources, "upload")


def _detect_from_sample():
    yield from _stream_prepare([_SAMPLE_DIR], "morrison-sample")


def _enable_analyze():
    # Any explicit radio selection enables Continue (covers the low-confidence case).
    return gr.update(interactive=True)


# Outputs for extract transition:
# [route_group, extract_group, confirm_group, extract_progress, confirm_intro,
#  result_state, status_state, error_md]


def _run_extract(corpus, pack):
    """Generator: show a working message, run extraction, reveal the confirm step."""
    yield (
        _hide(), _show(), _hide(),
        gr.update(value="Analyzing your evidence with the model. This runs "
                        "privately and can take a few minutes.", visible=True),
        gr.update(), None, {}, gr.update(value="", visible=False),
    )
    outcome = wizard.extract(corpus, pack, model=_MODEL)
    if not outcome.ok:
        yield (
            _show(), _hide(), _hide(), gr.update(visible=False), gr.update(),
            None, {}, gr.update(value=f"⚠️ {outcome.user_message}", visible=True),
        )
        return

    rows = outcome.payload["rows"]
    seed = {r["factor_type"]: r["status"] for r in rows}
    intro = (
        f"{_step_tag(3, 'Confirm')}\n\n### Confirm what we understood\n\nWe read "
        f"**{len(rows)} credibility factors** from your evidence. Correct any status "
        "we got wrong. That is the only thing you need to touch."
    )
    yield (
        _hide(),                   # route_group
        _hide(),                   # extract_group
        _show(),                   # confirm_group
        gr.update(visible=False),  # extract_progress
        gr.update(value=intro),    # confirm_intro
        outcome.payload["result"], # result_state (drives the dynamic factor radios)
        seed,                      # status_state (seeded with extracted statuses)
        gr.update(value="", visible=False),
    )


def _finalize(result, pack, status_state, warnings, source_name):
    outcome = wizard.finalize(
        result, pack, status_state or {}, source_name=source_name, warnings=warnings
    )
    if not outcome.ok:
        return (_show(), _hide(), gr.update(value=f"⚠️ {outcome.user_message}", visible=True),
                gr.update(), gr.update(), gr.update(), None)

    p = outcome.payload
    c = p["completeness"]

    # Headline (gaps-led) + honest indicative line.
    head = (
        f"{_step_tag(4, 'Your gaps')}\n\n## {p['headline']}\n\n"
        "*Indicative summary, not a formal acceptance decision.*"
    )

    # Gaps first: weakeners, then unassessed factors.
    gaps = []
    if p["weakeners"]:
        gaps.append("**Weakeners fired:**")
        for w in p["weakeners"]:
            fac = f", {', '.join(w['factors'])}" if w.get("factors") else ""
            gaps.append(f"- `{w['patternId']}` [{w.get('severity')}] ×{w.get('hits')}{fac}")
    else:
        gaps.append("**Weakeners:** none fired. 🎉")
    if c["missing"]:
        gaps.append("\n**Not assessed:** " + ", ".join(c["missing"]))
    gaps_md = "\n".join(gaps)

    # Completeness + structural, second.
    tail = [f"**Completeness:** {c['n_assessed']} of {c['n_expected']} factors assessed."]
    if c["excluded"]:
        tail.append("**Excluded (scoped-out / N/A):** " + ", ".join(c["excluded"]))
    struct = p["structural"]
    if struct["conforms"]:
        tail.append("**Structural validity:** conforms.")
    else:
        tail.append(f"**Structural validity:** {_issue_phrase(struct['n'])}.")
    tail_md = "\n\n".join(tail)

    return (
        _hide(),                              # confirm_group
        _show(),                              # summary_group
        gr.update(value="", visible=False),   # error_md
        gr.update(value=head),                # summary_md (headline, gaps-led)
        gr.update(value=gaps_md),             # weakeners_md (gaps first)
        gr.update(value=tail_md),             # structural_md (completeness + structural)
        p,                                    # summary_state (for lead capture)
    )


def _capture(email, pack, summary):
    result = leadcapture.capture_lead(email, pack=pack, summary=summary)
    if not result.accepted:
        return gr.update(value="Please enter a valid email.", visible=True)
    # Sink failure never blocks the unlock; the lead is queued to the fallback.
    return gr.update(
        value="Thanks. We will be in touch with the fuller write-up. "
              "(Your evidence was not stored.)",
        visible=True,
    )


def _start_over():
    return (
        _show(), _hide(), _hide(), _hide(), _hide(),   # upload, route, extract, confirm, summary
        gr.update(value="", visible=False),            # error_md
        None, None, None, {}, None,                    # corpus, decision, result, status, warnings
    )


def _factor_label(row: dict) -> str:
    """Row label: factor + status, and the level pair only when it's a gap
    (achieved below required) so 13 identical 'required 3 / achieved 3' lines
    don't add noise."""
    ft, status = row["factor_type"], row["status"]
    req, ach = row.get("required_level"), row.get("achieved_level")
    suffix = ""
    if isinstance(req, int) and isinstance(ach, int) and ach < req:
        suffix = f"  ·  needs L{req}, has L{ach}"
    return f"{ft}  ·  {status}{suffix}"


def _issue_phrase(n: int) -> str:
    return f"{n} issue{'' if n == 1 else 's'} found"


def build() -> gr.Blocks:
    with gr.Blocks(title="UofA Gap-Finder", analytics_enabled=False) as demo:
        gr.Markdown("# UofA Gap-Finder\nSee where your model-credibility evidence has "
                    "gaps, against ASME V&V 40 or NASA-STD-7009B.")

        corpus_state = gr.State(None)
        decision_state = gr.State(None)
        result_state = gr.State(None)
        status_state = gr.State({})
        warnings_state = gr.State(None)
        source_name_state = gr.State("upload")
        summary_state = gr.State(None)

        error_md = gr.Markdown(visible=False)

        # ── Step 1: upload ───────────────────────────────────
        with gr.Group(visible=True) as upload_group:
            gr.Markdown(_step_tag(1, "Upload") + "\n\n" + COLD_START_NOTE)
            gr.Markdown("Drop your **evidence documents** here (PDF, DOCX, XLSX, CSV, "
                        "TXT). You can add several files.")
            file_input = gr.File(label="Evidence documents", file_count="multiple")
            with gr.Row():
                detect_btn = gr.Button("Detect standard →", variant="primary")
                sample_btn = gr.Button("Try a sample evidence set")
        read_progress = gr.Markdown(visible=False)

        # ── Step 2: route ────────────────────────────────────
        with gr.Group(visible=False) as route_group:
            gr.Markdown(_step_tag(2, "Confirm standard"))
            why_md = gr.Markdown()
            route_warn = gr.Markdown(
                "⚠️ Low-confidence routing. Pick the standard before continuing.",
                visible=False,
            )
            pack_radio = gr.Radio(choices=PACK_CHOICES, label="Standard", value="vv40")
            analyze_btn = gr.Button("Analyze evidence →", variant="primary")

        # ── Step 3: extract (transient) ──────────────────────
        with gr.Group(visible=False) as extract_group:
            extract_progress = gr.Markdown()

        # ── Step 4: confirm status ───────────────────────────
        with gr.Group(visible=False) as confirm_group:
            confirm_intro = gr.Markdown()

            @gr.render(inputs=[result_state])
            def render_factors(result):
                rows = pipeline.factor_rows(result) if result else []
                for row in rows:
                    rad = gr.Radio(choices=STATUS_CHOICES, value=row["status"],
                                   label=_factor_label(row))
                    # The factor name is already in the radio label above, so the
                    # accordion just says "what we read" (no redundant name echo).
                    with gr.Accordion("what we read", open=False):
                        gr.Markdown(str(row.get("rationale") or "No rationale captured."))

                    def _upd(val, st, _ft=row["factor_type"]):
                        st = dict(st or {})
                        st[_ft] = val
                        return st

                    rad.change(_upd, inputs=[rad, status_state], outputs=[status_state])

            gaps_btn = gr.Button("See my gaps →", variant="primary")

        # ── Step 5: summary + capture ────────────────────────
        with gr.Group(visible=False) as summary_group:
            summary_md = gr.Markdown()      # headline (gaps-led) + indicative line
            weakeners_md = gr.Markdown()    # weakeners + not-assessed (the gaps)
            structural_md = gr.Markdown()   # completeness + structural (second)
            gr.Markdown("---\n### Want the full write-up?\n"
                        "Leave your email for the detailed per-factor report or a consult. "
                        "**Your evidence is not stored.**")
            email_box = gr.Textbox(label="Email", placeholder="you@org.com")
            capture_btn = gr.Button("Send me the full write-up", variant="primary")
            capture_msg = gr.Markdown(visible=False)

        start_over_btn = gr.Button("↺ Start over")

        prepare_outputs = [
            read_progress, upload_group, route_group, why_md, pack_radio, analyze_btn,
            route_warn, corpus_state, decision_state, warnings_state, source_name_state, error_md,
        ]
        detect_btn.click(_detect_from_upload, inputs=[file_input], outputs=prepare_outputs)
        sample_btn.click(_detect_from_sample, inputs=None, outputs=prepare_outputs)
        pack_radio.change(_enable_analyze, inputs=None, outputs=[analyze_btn])

        analyze_btn.click(
            _run_extract,
            inputs=[corpus_state, pack_radio],
            outputs=[route_group, extract_group, confirm_group, extract_progress,
                     confirm_intro, result_state, status_state, error_md],
        )

        gaps_btn.click(
            _finalize,
            inputs=[result_state, pack_radio, status_state, warnings_state, source_name_state],
            outputs=[confirm_group, summary_group, error_md, summary_md, weakeners_md,
                     structural_md, summary_state],
        )

        capture_btn.click(_capture, inputs=[email_box, pack_radio, summary_state], outputs=[capture_msg])

        start_over_btn.click(
            _start_over,
            inputs=None,
            outputs=[upload_group, route_group, extract_group, confirm_group, summary_group,
                     error_md, corpus_state, decision_state, result_state, status_state,
                     warnings_state],
        )

    return demo


if __name__ == "__main__":
    # Gradio 6: theme/css go to launch(); the API page is closed via queue(api_open=False).
    build().queue(default_concurrency_limit=1, api_open=False).launch(
        server_name="0.0.0.0", server_port=7860, theme=THEME, css=CSS
    )
