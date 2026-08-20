"""Gradio wizard for the UofA Gap-Finder Space.

Thin UI over space.wizard (which holds the testable step logic). Flow:
  upload/sample -> route (confirm standard) -> extract -> confirm status
  -> free summary -> contact capture.

Set UOFA_SPACE_MODEL=mock to drive the UI locally without Ollama.
"""

from __future__ import annotations

import html as html_mod
import os
import queue
import threading
from pathlib import Path

import gradio as gr

from space import (curated, leadcapture, llm_env, pipeline, ratelimit, reviewer,
                   solver_panel, wizard)
from space.gloss import gloss_for, load_gloss
from uofa_cli import paths

PACK_LABELS = {"vv40": "ASME V&V 40", "nasa-7009b": "NASA-STD-7009B"}
PACK_CHOICES = [(label, pid) for pid, label in PACK_LABELS.items()]
STATUS_CHOICES = ["assessed", "not-assessed", "scoped-out", "not-applicable"]

# Plain-language gloss, loaded once; shared by the reviewer render and the
# author confirm accordion (one lookup, never duplicated).
_GLOSS = load_gloss()

_MODEL = os.environ.get("UOFA_SPACE_MODEL") or None  # None -> bundled qwen3.5:4b
# Resolved once at import, mirroring _MODEL. None means "use the local path",
# which is what an unconfigured deployment and every test should get. The
# autouse fixture in tests/space/conftest.py nulls this too, so a developer with
# a provider key exported does not silently make the UI tests hit the network.
_LLM_CONFIG = llm_env.space_llm_config()
# In-container the wheel bundles packs/ under uofa_cli/_data/repo; an env var lets
# a deployment point elsewhere without code changes.
_SAMPLE_DIR = Path(
    os.environ.get("UOFA_SPACE_SAMPLE_DIR")
    or paths.find_repo_root() / "packs" / "vv40" / "examples" / "morrison" / "source"
)

def _cold_start_note() -> str:
    """The pre-upload disclosure. Rendered above the file picker, deliberately.

    Two claims that must not be conflated: this Space stores nothing, which
    stays true, and nothing leaves it, which does not once a hosted model reads
    the documents. Keeping the storage claim while dropping the transmission
    one is the whole job here.
    """
    if not llm_env.is_remote(_LLM_CONFIG):
        return (
            "Your documents are read **privately inside this Space** by a local "
            "model. Nothing is stored and nothing is sent to a third party. The "
            "first analysis after the Space wakes can take a few minutes while "
            "the model loads."
        )
    return (
        f"Your documents are sent to a **hosted model** "
        f"({llm_env.provider_label(_LLM_CONFIG)}) to be read, then discarded. "
        "This Space stores nothing: each run uses a temporary directory that is "
        "deleted when it finishes, and no document is logged. But the text does "
        "leave this Space. **If your evidence is confidential, do not upload it "
        "here** - run the CLI on your own machine instead, where the model runs "
        "locally and nothing leaves your environment.\n\n"
        "Pasting a public model card sends only text that is already public."
    )


COLD_START_NOTE = _cold_start_note()

# Dark theme to match uofa.net. The Space is embedded via an <iframe>, so the
# body needs a SOLID dark background (a transparent body would show the iframe's
# default white, since there's no dark parent behind it inside the frame). A
# neutral gray hue sits closer to the site's near-black than gradio's slate.
# Block borders/shadows are zeroed to avoid stray divider rules.
# Match uofa.net exactly (tokens from site/src/styles/custom.css): flat black
# #0c0d0e everywhere, only inputs elevated to #131418 so the actionable areas
# read as interactive. Body = IBM Plex Sans, mono = IBM Plex Mono (headings use
# Fraunces via CSS below). Text #e8e6e1 / muted #9a988f, border #25262c. The app
# is forced dark via ?__theme=dark in the embed, so the _dark variants render.
THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.orange,
    neutral_hue=gr.themes.colors.gray,
    font=[gr.themes.GoogleFont("IBM Plex Sans"), "ui-sans-serif", "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("IBM Plex Mono"), "ui-monospace", "monospace"],
).set(
    body_background_fill="#0c0d0e",
    body_background_fill_dark="#0c0d0e",
    background_fill_primary_dark="#0c0d0e",
    background_fill_secondary_dark="#0c0d0e",
    block_background_fill_dark="#0c0d0e",
    block_border_width="0px",
    block_shadow="none",
    panel_border_width="0px",
    border_color_primary_dark="#25262c",
    body_text_color_dark="#e8e6e1",
    body_text_color_subdued_dark="#9a988f",
    input_background_fill_dark="#131418",   # actionable inputs stay elevated
    input_border_color_dark="#25262c",
)

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&display=swap');

/* Left-aligned and full-width so it flows with the (left-aligned) page column,
   not centered inside the iframe. */
.gradio-container { max-width: 100% !important; margin: 0 !important;
  padding-left: 0 !important; padding-right: 0 !important;
  font-family: 'IBM Plex Sans', ui-sans-serif, system-ui, sans-serif;
  font-size: 16px; line-height: 1.65; color: #e8e6e1; background: #0c0d0e; }
/* gradio's .app wrapper adds large horizontal padding (var(--size-8)); zero it
   so content sits flush-left at the page column edge. */
.gradio-container .app { padding-left: 0 !important; padding-right: 0 !important;
  max-width: 100% !important; margin: 0 !important; }

/* Headings: Fraunces serif at uofa.net sizes/weights. */
.gradio-container h1, .gradio-container h2, .gradio-container h3 {
  font-family: 'Fraunces', ui-serif, Georgia, serif; color: #e8e6e1;
  letter-spacing: -0.02em; line-height: 1.15;
  overflow-wrap: anywhere; word-break: break-word; white-space: normal; }
.gradio-container h1 { font-size: clamp(2.2rem, 5vw, 3.2rem); font-weight: 400; }
.gradio-container h2 { font-size: 1.875rem; font-weight: 500; }
.gradio-container h3 { font-size: 1.375rem; font-weight: 500; }

/* Inline emphasis + code, like the site (italic -> brass accent). */
.gradio-container em { color: #d4a35a; font-style: italic; }
.gradio-container strong { color: #e8e6e1; font-weight: 500; }
.gradio-container code { font-family: 'IBM Plex Mono', ui-monospace, monospace;
  background: #131418; border: 1px solid #25262c; color: #d4a35a;
  padding: 1px 6px; border-radius: 4px; }

/* Flatten text containers (groups/blocks) to the page black; inputs/buttons
   keep their elevation via the theme tokens. */
.gradio-container .block, .gradio-container .form,
.gradio-container .gr-group, .gradio-container .panel,
.gradio-container .gap { background: #0c0d0e !important; }

/* Hide the default Gradio footer (Use via API / Built with Gradio / Settings). */
footer { display: none !important; }
/* Empty/placeholder markdown blocks must not render as stray rules. */
.prose:empty, .md:empty { display: none !important; margin: 0 !important;
  padding: 0 !important; border: 0 !important; }
/* Focus ring in the site's brass accent. */
*:focus-visible { outline: 2px solid #d4a35a !important;
  outline-offset: 2px; border-radius: 4px; }
/* Lightweight step header. */
.step-tag { font-size: 0.8rem; letter-spacing: 0.04em; text-transform: uppercase;
  color: #9a988f; margin-bottom: 0.25rem; }
.factor-levels { color: #9a988f; font-size: 0.85em; }
"""

# Save-as-PDF: clone the reviewer content (#ri-reviewer-host) into a clean
# white-background window and print that. Runs as a gradio Button js= handler
# (gr.HTML may strip inline onclick; a global @media print gets mangled by
# gradio's CSS scoping). Falls back to window.print() if a popup is blocked.
_PRINT_JS = """
() => {
  const s = document.getElementById('ri-reviewer-host');
  const w = window.open('', '_blank', 'width=840,height=1100');
  if (!w) { window.print(); return; }
  w.document.write('<!doctype html><meta charset=utf-8><title>Credibility Inspector</title>'
    + '<style>body{font-family:Georgia,serif;color:#111;margin:2.5rem;line-height:1.55}'
    + 'h2{margin:1.3rem 0 .4rem}.ri-lead{font-size:1.1rem}'
    + 'table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:6px 8px;'
    + 'border-bottom:1px solid #ccc;vertical-align:top}th{font-size:.75rem;text-transform:uppercase;color:#555}'
    + 'dl{display:grid;grid-template-columns:1fr 1fr;gap:8px}dt{color:#555;font-size:.72rem;text-transform:uppercase}dd{margin:0}'
    + 'pre{background:#f2f2f2;padding:8px;border-radius:4px}.ri-note{color:#555}</style>'
    + (s ? s.innerHTML : document.body.innerHTML));
  w.document.close(); w.focus();
  setTimeout(() => w.print(), 300);
}
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


def _book(outcome, pack) -> None:
    """Record what a completed run cost, successful or not.

    Failures are booked too: a timeout or a parse error still consumed tokens
    at the provider, and a ledger that only counted successes would under-count
    exactly when something is going wrong repeatedly.

    Tokens are estimated. `generate()` returns a bare string, so provider usage
    is not available without changing the shared CLI interface; input comes from
    the corpus count we already compute and output from the response length we
    already hold. Good to roughly the right factor, which is what a budget guard
    needs, and stored as `estimated_usd` so it is never mistaken for an invoice.
    """
    result = (outcome.payload or {}).get("result") if outcome.ok else None
    inp = int(getattr(result, "corpus_tokens", 0) or 0)
    raw = getattr(result, "raw_json", "") or ""
    out = max(len(raw) // 4, 256)   # floor: a failed call still cost something
    try:
        ratelimit.record(pack=pack, input_tokens=inp, output_tokens=out,
                         llm_config=_LLM_CONFIG)
    except Exception:  # noqa: BLE001 - accounting must never fail a user's run
        pass


def _run_extract(corpus, pack, runs_used):
    """Generator: show a working message, run extraction, reveal the confirm step.

    `runs_used` is this session's metered-run count, held in gr.State. The
    budget check runs BEFORE the model call so a refusal costs nothing, and the
    counter advances only for calls that were actually billable."""
    metered = llm_env.is_remote(_LLM_CONFIG)
    allowed, refusal = ratelimit.consume(runs_used or 0, metered=metered)
    if not allowed:
        yield (
            _show(), _hide(), _hide(), gr.update(visible=False), gr.update(),
            None, {}, gr.update(value=refusal, visible=True), runs_used,
        )
        return
    runs_used = (runs_used or 0) + (1 if metered else 0)

    yield (
        _hide(), _show(), _hide(),
        # One source for this sentence: pipeline._reading_message branches on the
        # same config the request will use, so the in-flight copy cannot promise
        # privacy the backend is not providing.
        gr.update(value=pipeline._reading_message(_LLM_CONFIG), visible=True),
        gr.update(), None, {}, gr.update(value="", visible=False), runs_used,
    )
    outcome = wizard.extract(corpus, pack, model=_MODEL, llm_config=_LLM_CONFIG)
    if metered:
        _book(outcome, pack)
    if not outcome.ok:
        yield (
            _show(), _hide(), _hide(), gr.update(visible=False), gr.update(),
            None, {}, gr.update(value=f"⚠️ {outcome.user_message}", visible=True),
            runs_used,
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
        runs_used,                 # runs_state
    )


def _render_results(p):
    """Build the Step-5 result surfaces (author headline/gaps/tail markdown + reviewer
    HTML) from a finalize/card payload. Shared by the upload path (_finalize) and the
    card path (_run_card) so both render an identical results view. The author 'gaps'
    view, like the reviewer panel, declines sufficiency in heuristic mode rather than
    reporting 'none fired'."""
    c = p["completeness"]
    assessed = (p.get("context") or {}).get("sufficiency_assessed", True)

    head = (
        f"{_step_tag(4, 'Your gaps')}\n\n## {p['headline']}\n\n"
        "*Indicative summary, not a formal acceptance decision.*"
    )

    gaps = []
    if not assessed:
        gaps.append("**Sufficiency (weakener) analysis:** not assessed in heuristic mode - "
                    "run with an LLM backend for the weakener findings.")
    elif p["weakeners"]:
        gaps.append("**Weakeners fired:**")
        for w in p["weakeners"]:
            fac = f", {', '.join(w['factors'])}" if w.get("factors") else ""
            gaps.append(f"- `{w['patternId']}` [{w.get('severity')}] ×{w.get('hits')}{fac}")
    else:
        gaps.append("**Weakeners:** none fired. 🎉")
    if c["missing"]:
        gaps.append("\n**Not assessed:** " + ", ".join(c["missing"]))
    gaps_md = "\n".join(gaps)

    tail = [f"**Completeness:** {c['n_assessed']} of {c['n_expected']} factors assessed."]
    if c["excluded"]:
        tail.append("**Excluded (scoped-out / N/A):** " + ", ".join(c["excluded"]))
    struct = p["structural"]
    if struct["conforms"]:
        tail.append("**Structural validity:** conforms.")
    else:
        tail.append(f"**Structural validity:** {_issue_phrase(struct['n'])}.")
    solver_md = solver_panel.render(p.get("solverEvidence"))
    if solver_md:
        tail.append(solver_md)
    tail_md = "\n\n".join(tail)

    # build_reviewer_state derives an invariant-satisfying state by construction,
    # so this never trips in practice; we still refuse to emit a misleading page
    # if a future payload shape ever violates an invariant.
    try:
        reviewer_html = reviewer.render_reviewer_html(p, _GLOSS)
    except reviewer.ReviewerInvariantError as exc:
        reviewer_html = (
            '<div id="ri-reviewer-host"><div class="ri-reviewer">'
            "<h2>Reviewer summary unavailable</h2>"
            "<p>This evidence produced an internally inconsistent assessment that we "
            "will not summarize for a reviewer. See the Author view for the raw findings.</p>"
            f"<p class='ri-note'>{html_mod.escape(str(exc))}</p>"
            "</div></div>"
        )
    return head, gaps_md, tail_md, reviewer_html


def _pack_update(payload):
    """Show the download only when this run actually produced a signed pack.

    Two failure shapes to keep apart: no signing key configured (the Space is
    unsigned, as it has always been) and a run that errored. Both must leave the
    control hidden with no value, never pointing at an earlier run's file."""
    download = (payload or {}).get("download")
    if not download:
        return gr.update(value=None, visible=False)
    return gr.update(value=download["zip_path"], visible=True)


def _finalize(result, pack, status_state, warnings, source_name, pack_dir):
    wizard.discard_pack_dir(pack_dir)          # supersede the previous run's file
    pack_dir = wizard.new_pack_dir()
    outcome = wizard.finalize(
        result, pack, status_state or {}, source_name=source_name, warnings=warnings,
        pack_out_dir=pack_dir, llm_config=_LLM_CONFIG,
    )
    if not outcome.ok:
        return (_show(), _hide(), gr.update(value=f"⚠️ {outcome.user_message}", visible=True),
                gr.update(), gr.update(), gr.update(), None, gr.update(),
                gr.update(), gr.update(), gr.update(),  # view_toggle, author/reviewer panel (no-op)
                _pack_update(None), pack_dir)

    p = outcome.payload
    head, gaps_md, tail_md, reviewer_html = _render_results(p)
    return (
        _hide(),                              # confirm_group
        _show(),                              # summary_group
        gr.update(value="", visible=False),   # error_md
        gr.update(value=head),                # summary_md (author: headline, gaps-led)
        gr.update(value=gaps_md),             # weakeners_md (author: gaps first)
        gr.update(value=tail_md),             # structural_md (author: completeness + structural)
        p,                                    # summary_state (for lead capture)
        gr.update(value=reviewer_html),       # reviewer_html (reviewer view)
        # This handler owns showing the result: default to the Reviewer view so a
        # run always opens on it, regardless of the toggle's prior position.
        gr.update(value="Reviewer"),          # view_toggle
        _hide(),                              # author_panel
        _show(),                              # reviewer_panel
        _pack_update(p),                      # pack_btn
        pack_dir,                             # pack_dir_state
    )


# Outputs for the card path (_run_card): step groups + card_progress + the Step-5
# result surfaces. See the build() wiring for the exact component list.


def _run_card(model_id, pack_dir, runs_used):
    """Card path: fetch an HF model card and report, skipping route/extract/confirm.
    Generator: yields a working state, then the result (or an error). Hard-routes
    model-credibility; the readout discloses extraction provenance + the MRL assumption."""
    model_id = (model_id or "").strip()
    if not model_id:
        yield (_show(), _hide(), _hide(), _hide(), _hide(), gr.update(visible=False),
               gr.update(value="⚠️ Paste a model id (owner/model) or a model URL first.", visible=True),
               gr.update(), gr.update(), gr.update(), None, gr.update(),
               gr.update(), gr.update(), gr.update(), _pack_update(None), pack_dir, runs_used)
        return

    metered = llm_env.is_remote(_LLM_CONFIG)
    allowed, refusal = ratelimit.consume(runs_used or 0, metered=metered)
    if not allowed:
        yield (_show(), _hide(), _hide(), _hide(), _hide(), gr.update(visible=False),
               gr.update(value=refusal, visible=True),
               gr.update(), gr.update(), gr.update(), None, gr.update(),
               gr.update(), gr.update(), gr.update(), _pack_update(None), pack_dir, runs_used)
        return
    runs_used = (runs_used or 0) + (1 if metered else 0)

    wizard.discard_pack_dir(pack_dir)          # supersede the previous run's file
    pack_dir = wizard.new_pack_dir()

    yield (_hide(), _hide(), _hide(), _hide(), _hide(),
           gr.update(value=f"Fetching the public model card for **{model_id}** and analyzing it. "
                           "This can take a few minutes the first time...", visible=True),
           gr.update(value="", visible=False),
           gr.update(), gr.update(), gr.update(), None, gr.update(),
           gr.update(), gr.update(), gr.update(), _pack_update(None), pack_dir, runs_used)

    outcome = wizard.card_report(model_id, model=_MODEL, llm_config=_LLM_CONFIG,
                                   pack_out_dir=pack_dir)
    if metered:
        _book(outcome, "model-credibility")
    if not outcome.ok:
        yield (_show(), _hide(), _hide(), _hide(), _hide(), gr.update(visible=False),
               gr.update(value=f"⚠️ {outcome.user_message}", visible=True),
               gr.update(), gr.update(), gr.update(), None, gr.update(),
               gr.update(), gr.update(), gr.update(), _pack_update(None), pack_dir, runs_used)
        return

    p = outcome.payload
    head, gaps_md, tail_md, reviewer_html = _render_results(p)
    yield (_hide(), _hide(), _hide(), _hide(), _show(),     # upload, route, extract, confirm, summary
           gr.update(visible=False),                         # card_progress
           gr.update(value="", visible=False),               # error_md
           gr.update(value=head), gr.update(value=gaps_md), gr.update(value=tail_md),
           p,                                                 # summary_state
           gr.update(value=reviewer_html),
           gr.update(value="Reviewer"), _hide(), _show(),    # view_toggle, author_panel, reviewer_panel
           _pack_update(p), pack_dir, runs_used)             # pack_btn, pack_dir_state, runs_state


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


def _switch_view(choice):
    """Pure client-side view flip; touches no state and re-runs nothing."""
    reviewer_first = (choice == "Reviewer")
    return (gr.update(visible=not reviewer_first),  # author_panel
            gr.update(visible=reviewer_first))      # reviewer_panel


def _start_over(pack_dir):
    """Full reset to step 1. Hiding the step groups is not enough: the result
    components (reviewer HTML, the author markdowns, the picked file) keep their
    last values, so a stale report shows through if a group ever fails to
    collapse. Blank every content surface as well as resetting the states, so
    Start over always lands on a clean upload step.

    The download gets the same treatment and then some: a stale *file* is worse
    than a stale render, because the user walks away with a signed package
    describing someone else's evidence. Clear the control and delete the
    directory behind it."""
    wizard.discard_pack_dir(pack_dir)
    return (
        # step groups
        _show(), _hide(), _hide(), _hide(), _hide(),   # upload, route, extract, confirm, summary
        _hide(), _hide(), _hide(),                     # read_progress, extract_progress, card_progress
        # content surfaces (cleared, not just hidden)
        gr.update(value="", visible=False),            # error_md
        gr.update(value=""),                           # confirm_intro
        gr.update(value=""),                           # reviewer_html
        gr.update(value=""),                           # summary_md
        gr.update(value=""),                           # weakeners_md
        gr.update(value=""),                           # structural_md
        gr.update(value="", visible=False),            # capture_msg
        gr.update(value=""),                           # email_box
        gr.update(value=None),                         # file_input
        gr.update(value=""),                           # card_input
        # states
        None, None, None, {}, None, None,              # corpus, decision, result, status, warnings, summary
        # view: reset the toggle to its default and hide BOTH panels. A panel must
        # never be shown while its parent summary_group is hidden: Gradio renders
        # the visible child and drags the hidden parent back into view. _finalize
        # (which actually shows summary_group) owns re-showing the reviewer panel.
        gr.update(value="Reviewer"),                   # view_toggle
        _hide(), _hide(),                              # author_panel, reviewer_panel
        gr.update(value=None, visible=False),          # pack_btn
        None,                                          # pack_dir_state
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
    with gr.Blocks(title="Credibility Inspector", analytics_enabled=False, fill_width=True) as demo:
        gr.Markdown("# Credibility Inspector\nInspect model-credibility evidence "
                    "against ASME V&V 40 or NASA-STD-7009B, for the reviewer judging a "
                    "package or the engineer assembling one.")

        corpus_state = gr.State(None)
        decision_state = gr.State(None)
        result_state = gr.State(None)
        status_state = gr.State({})
        warnings_state = gr.State(None)
        source_name_state = gr.State("upload")
        summary_state = gr.State(None)
        pack_dir_state = gr.State(None)   # this session's downloadable pack dir
        runs_state = gr.State(0)          # metered analyses this session has run

        error_md = gr.Markdown(visible=False)

        # ── Step 1: start - a model card (live), or upload evidence ──
        with gr.Group(visible=True) as upload_group:
            gr.Markdown(_step_tag(1, "Start") + "\n\n" + COLD_START_NOTE)
            gr.Markdown("### Report on a model card\nPaste a HuggingFace **model id** "
                        "(`owner/model`) or model URL to fetch its card and get a live "
                        "weakener report against the NIST AI RMF documentation factors.")
            card_input = gr.Textbox(label="HuggingFace model id or URL",
                                    placeholder="allenai/OLMo-2-1124-13B-Instruct")
            card_btn = gr.Button("Get weakener report →", variant="primary")
            gr.Markdown("Or try a suggested example:")
            with gr.Row():
                example_btns = [gr.Button(mid.split("/")[-1], size="sm")
                                for mid, _role in curated.EXAMPLE_MODELS]
            gr.Markdown("---\n### Or inspect an evidence bundle\nDrop **evidence documents** "
                        "(PDF, DOCX, XLSX, CSV, TXT) for ASME V&V 40 or NASA-STD-7009B. "
                        "You can add several files.")
            file_input = gr.File(label="Evidence documents", file_count="multiple")
            with gr.Row():
                detect_btn = gr.Button("Detect standard →", variant="primary")
                sample_btn = gr.Button("Try a sample evidence set")
        read_progress = gr.Markdown(visible=False)
        card_progress = gr.Markdown(visible=False)

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
                    # Lead with the shared gloss so a non-expert understands the factor.
                    g = gloss_for(row["factor_type"], _GLOSS)
                    meaning = f"**{g['plain_name']}.** {g['what_it_means']}\n\n" if g.get("what_it_means") else ""
                    with gr.Accordion("what we read", open=False):
                        gr.Markdown(meaning + str(row.get("rationale") or "No rationale captured."))

                    def _upd(val, st, _ft=row["factor_type"]):
                        st = dict(st or {})
                        st[_ft] = val
                        return st

                    rad.change(_upd, inputs=[rad, status_state], outputs=[status_state])

            gaps_btn = gr.Button("See my gaps →", variant="primary")

        # ── Step 5: results, two views off one analysis ──────
        with gr.Group(visible=False) as summary_group:
            view_toggle = gr.Radio(
                ["Reviewer", "Author (Gap-Finder)"], value="Reviewer", label="View",
                info="Reviewer: plain-language verdict for someone judging this package. "
                     "Author: the gap list for whoever is assembling the evidence.",
            )
            # Reviewer is the default; Author is one toggle away.
            with gr.Group(visible=True) as reviewer_panel:
                reviewer_html = gr.HTML()
                with gr.Row():
                    pdf_btn = gr.Button("Save as PDF", size="sm")
                    # DownloadButton, not gr.File: a filebox here would read as a
                    # second upload target next to the one in Step 1, which is the
                    # opposite of what it does. Hidden until a run actually signs
                    # a package -- see _pack_update. No .click handler; the
                    # component serves whatever path is set as its value.
                    pack_btn = gr.DownloadButton(
                        "Download UofA package", size="sm", visible=False)
            with gr.Group(visible=False) as author_panel:
                summary_md = gr.Markdown()      # headline (gaps-led) + indicative line
                weakeners_md = gr.Markdown()    # weakeners + not-assessed (the gaps)
                structural_md = gr.Markdown()   # completeness + structural (second)
            # Optional consult footer, shared by both views. Never a wall.
            with gr.Group() as capture_footer:
                gr.Markdown("---\n### Want a per-factor consult?\n"
                            "Leave your email for a detailed write-up or a consult. "
                            "**Your evidence is not stored.**")
                email_box = gr.Textbox(label="Email", placeholder="you@org.com")
                capture_btn = gr.Button("Request a consult", variant="primary")
                capture_msg = gr.Markdown(visible=False)

        start_over_btn = gr.Button("↺ Start over")

        prepare_outputs = [
            read_progress, upload_group, route_group, why_md, pack_radio, analyze_btn,
            route_warn, corpus_state, decision_state, warnings_state, source_name_state, error_md,
        ]
        detect_btn.click(_detect_from_upload, inputs=[file_input], outputs=prepare_outputs)
        sample_btn.click(_detect_from_sample, inputs=None, outputs=prepare_outputs)

        # Card path: the id/URL box and the suggested-example buttons both run the same
        # live pathway (fetch + extract + report), skipping route/extract/confirm.
        card_outputs = [
            upload_group, route_group, extract_group, confirm_group, summary_group,
            card_progress, error_md, summary_md, weakeners_md, structural_md,
            summary_state, reviewer_html, view_toggle, author_panel, reviewer_panel,
            pack_btn, pack_dir_state, runs_state,
        ]
        card_btn.click(_run_card, inputs=[card_input, pack_dir_state, runs_state], outputs=card_outputs)
        for _ex_btn, (_ex_mid, _ex_role) in zip(example_btns, curated.EXAMPLE_MODELS):
            _ex_btn.click(lambda _m=_ex_mid: _m, inputs=None, outputs=[card_input]).then(
                _run_card, inputs=[card_input, pack_dir_state, runs_state], outputs=card_outputs)

        pack_radio.change(_enable_analyze, inputs=None, outputs=[analyze_btn])

        analyze_btn.click(
            _run_extract,
            inputs=[corpus_state, pack_radio, runs_state],
            outputs=[route_group, extract_group, confirm_group, extract_progress,
                     confirm_intro, result_state, status_state, error_md, runs_state],
        )

        gaps_btn.click(
            _finalize,
            inputs=[result_state, pack_radio, status_state, warnings_state, source_name_state,
                    pack_dir_state],
            outputs=[confirm_group, summary_group, error_md, summary_md, weakeners_md,
                     structural_md, summary_state, reviewer_html,
                     view_toggle, author_panel, reviewer_panel, pack_btn, pack_dir_state],
        )

        # `.input` (user-interaction only), NOT `.change`: a programmatic reset of
        # the toggle (Start over sets it back to "Reviewer") must not re-fire
        # _switch_view, which would re-show reviewer_panel and drag its hidden
        # parent (summary_group) back into view, leaving a stray panel after reset.
        view_toggle.input(_switch_view, inputs=[view_toggle],
                          outputs=[author_panel, reviewer_panel])

        pdf_btn.click(None, js=_PRINT_JS)  # client-side print, no pipeline work

        capture_btn.click(_capture, inputs=[email_box, pack_radio, summary_state], outputs=[capture_msg])

        start_over_btn.click(
            _start_over,
            inputs=[pack_dir_state],
            outputs=[upload_group, route_group, extract_group, confirm_group, summary_group,
                     read_progress, extract_progress, card_progress,
                     error_md, confirm_intro, reviewer_html, summary_md, weakeners_md,
                     structural_md, capture_msg, email_box, file_input, card_input,
                     corpus_state, decision_state, result_state, status_state,
                     warnings_state, summary_state,
                     view_toggle, author_panel, reviewer_panel,
                     pack_btn, pack_dir_state],
        )

    return demo


if __name__ == "__main__":
    # Gradio 6: theme/css go to launch(); the API page is closed via queue(api_open=False).
    build().queue(default_concurrency_limit=1, api_open=False).launch(
        server_name="0.0.0.0", server_port=7860, theme=THEME, css=CSS
    )
