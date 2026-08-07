#!/usr/bin/env python3
"""Generate credibility-assessment papers seeded on the real ones.

A sibling to `generate_extract_corpus.py`, not an extension of it. That script is
parameter-driven, emits markdown, and one bundle is one model; this one takes a
seed paper, emits LaTeX -> PDF, and one paper assesses several models across
several mechanisms. Entangling them would make both worse. What is reusable is
imported: `sparse_scope`, `_make_backend`, `_approx_tokens`,
`_parse_json_response`, and the `--max-cost` spend guard.

Requirements are R1-R9 in `docs/seeded-corpus-spec.md`. Two properties of this
design are worth stating here because they are easy to undo by accident.

## Three steps, and the third reads the compiled PDF

    plan  -> what this paper assesses: 2-3 models x 2-4 mechanisms, which
             factors are reported / omitted / mentioned ambiguously, which
             deviation from the standard it makes
    write -> the paper's content, as structure (see latex_render: the model
             never writes a backslash)
    gold  -> evidence spans per (model x mechanism x factor), read back from
             the COMPILED text

Gold is a separate call against the compiled document, not the plan. Test 3 this
session showed same-pass gold is not measurably circular (76.9% against a 71.4%
real baseline, Fisher p = 1.000), so the separation is not about circularity --
it is that reading back the PDF catches spans LaTeX moved, hyphenated or split
across columns, which are exactly the spans the router will have to find.

## Omission is structural, never requested

`sparse_scope` names the subset a paper MAY discuss and withholds the rest. Asked
in a prompt to omit 40% of factors, the model complied at 8-21% however the
instruction was worded. R5 is the single difference the circularity tests found
-- seeded papers reported a clean finding for all thirteen factors, real ones do
not -- so this is the mechanism that closes it, and the acceptance gate checks
the result rather than trusting the prompt.

## Contamination

* Generation sees the seed's DOCUMENT text and never its ground truth.
* `evidence_keywords` may not seed a matcher.
* Gold is authored by one model family; the agreement check must come from
  another (`--gold-model` and `--agreement-model` are asserted cross-family).
* Output goes to a new directory. The existing corpora are never written to.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import pathlib
import random
import re
import sys
from datetime import datetime, timezone

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

import latex_render as LR  # noqa: E402
from generate_extract_corpus import (  # noqa: E402
    _approx_tokens, _make_backend, _parse_json_response, sparse_scope,
)
from uofa_cli import excel_constants as ec  # noqa: E402
from uofa_cli.adversarial.model_costs import assert_priced, estimate_cost  # noqa: E402
from uofa_cli.llm.backend import GenerationOptions  # noqa: E402

# The three seeds. elemance and morrison are held back -- see the plan: they
# carry the failure modes least replaceable by anything generated (2 models x 4
# mechanisms; two contexts of use, which is K8's only failure), and anything
# trained on this corpus must have somewhere clean to be measured.
SEEDS = {
    "opensim": ("extract_corpus_real/bundle_real_opensim_knee", "7009A"),
    "bologna": ("extract_corpus_vv40/bundle_bologna_bcthip", "V&V40"),
    "nagaraja": ("extract_corpus_vv40/bundle_nagaraja", "V&V40"),
}
HELD_BACK = ("elemance", "morrison")

# Distinct subject matter per paper, so diversity is designed in rather than
# hoped for. Five demo papers off one template scored 0.898 mean pairwise cosine
# against a real 0.141 and every one of them was flagged as a twin; prose style
# alone does not separate papers, subject matter does.
DOMAINS = [
    ("total knee replacement", "wear and contact mechanics", "explicit FEA"),
    ("coronary stent", "fatigue and radial strength", "implicit FEA"),
    ("centrifugal blood pump", "hemolysis and shear exposure", "CFD"),
    ("spinal pedicle screw", "pullout and bone purchase", "implicit FEA"),
    ("cranial impact protection", "skull and brain kinematics", "explicit FEA"),
    ("aortic valve leaflet", "coaptation and stress", "FSI"),
    ("bone cement mantle", "crack initiation and creep", "implicit FEA"),
    ("intravascular catheter", "trackability and flow resistance", "CFD"),
    ("hip resurfacing", "load transfer and stress shielding", "implicit FEA"),
    ("respiratory drug delivery", "particle deposition", "CFD"),
    ("transcatheter delivery system", "deployment force", "explicit FEA"),
    ("dental implant", "osseointegration loading", "implicit FEA"),
    ("infusion pump tubing", "occlusion detection", "CFD"),
    ("external fixator", "construct stiffness", "implicit FEA"),
    ("cardiac lead", "flex fatigue life", "explicit FEA"),
    ("oxygenator fibre bundle", "gas transfer", "CFD"),
    ("orthopaedic plate", "screw load sharing", "implicit FEA"),
    ("neurovascular coil", "packing density", "explicit FEA"),
    ("prosthetic foot", "energy return", "implicit FEA"),
    ("ventricular assist inflow", "thrombogenic potential", "CFD"),
]

PLAN_PROMPT = """\
You are planning a credibility assessment paper for a medical device \
computational model, to be written under {standard}.

Below is an excerpt of a REAL published paper of this kind, provided only so you \
match its register, structure and level of technical detail. Do not reuse its \
device, its numbers, or its sentences.

<real_paper_excerpt>
{seed_excerpt}
</real_paper_excerpt>

Plan a DIFFERENT paper about: a {device}, assessed for {concern}, modelled with \
{method}.

The paper must assess {n_models} computational models across {n_mech} \
mechanisms, and score every credibility factor SEPARATELY for each \
(model x mechanism) pair.

The paper may discuss ONLY these credibility factors:
{scope}

It must say nothing about any other factor. This is a constraint on the paper's \
content, not a formatting instruction: the other factors are simply not topics \
this paper covers.

Of the factors listed above, choose about a fifth to report AMBIGUOUSLY -- a \
passing mention in the prose that a careful reader might or might not count as \
evidence for that factor. The rest are reported clearly.

The paper must also deviate from the standard in exactly one of these ways, \
stated confidently and never flagged as a deviation:
  renamed_input     - use a different name for one of the standard's inputs
  undefined_value   - give an input a value the standard does not define
  compound_result   - report a compound level such as "low-medium"
  private_scale     - report on a numeric scale the standard does not define

{standard_rules}

Return ONLY JSON:
{{
  "title": "...",
  "runhead": "short running head",
  "device": "...",
  "models": [{{"name": "...", "what_it_computes": "..."}}],
  "mechanisms": [{{"name": "...", "why_it_matters": "..."}}],
  "clear_factors": ["..."],
  "ambiguous_factors": ["..."],
  "deviation": {{"kind": "one of the four above", "detail": "how it appears"}},
  "sections": ["ordered section headings for this paper"]
}}
"""

_VV40_RULES = """\
Under ASME V&V 40 the paper MUST state a context of use and a model risk level, \
each with its rationale."""
_7009A_RULES = """\
Under NASA-STD-7009A the paper MUST NOT state a "context of use" or a "model \
risk level". Those concepts do not exist in this standard; writing them would be \
a factual error."""

WRITE_PROMPT = """\
Write the paper planned below, as a journal article under {standard}.

<plan>
{plan}
</plan>

Rules that decide whether this paper is usable:

1. For each factor in "clear_factors", state its finding ONCE in the body prose, \
in a section far from where the factor is named, and phrase it WITHOUT using the \
factor's own words. A reader should have to understand the sentence to know it \
is the evidence. Fewer than 3 of the findings may contain the factor's canonical \
name.

2. For each factor in "ambiguous_factors", mention the topic in passing without \
clearly reporting a finding.

3. Score every factor separately for each (model x mechanism) pair. Never merge \
them.

4. Include a summary table whose rows restate findings that are ALSO in the \
prose, with the numbers in the prose.

5. Say nothing about any credibility factor not in the plan.

6. Write 5000-9000 words of real technical prose. Full paragraphs, specific \
numbers, named methods. Not an outline.

Return ONLY JSON. Every string is PLAIN TEXT -- no LaTeX, no markdown, no \
backslashes; the renderer adds all formatting.

{{
  "title": "...", "runhead": "...", "abstract": "...",
  "keywords": "three \\\\sep separated keywords",
  "authors": ["..."], "affiliations": ["..."],
  "sections": [
    {{"heading": "...", "level": 1,
      "paragraphs": ["...", "..."],
      "rubric": {{"factor": "...", "rungs": ["a text", "b text", "c text", "d text"]}},
      "figure": "full-width figure caption, or null",
      "table": {{"caption": "...",
                "rows": [["factor name", "level", "one-line basis"]]}}}}
  ]
}}

`rubric`, `figure` and `table` are optional per section; use null where absent. \
Include at least 6 rubric blocks across the paper, each a ladder of increasing \
rigour for one factor, in the standard's own style.
"""

GOLD_PROMPT = """\
Below is the extracted text of a credibility assessment paper, exactly as a \
document reader produced it. Line breaks, hyphenation and column order are the \
reader's, not the author's.

The paper assesses these models: {models}
across these mechanisms: {mechanisms}

<document>
{document}
</document>

Use ONLY these factor names, exactly as written. They are the standard's \
checklist; a label that is not on this list is not a credibility factor:

{factors}

For EVERY (model x mechanism x factor) combination where this document reports a \
finding, return the sentence that carries the evidence, copied VERBATIM from the \
text above including any hyphenation or spacing damage.

Judge only what is on the page. If a factor is mentioned but no finding is \
reported, mark it "ambiguous". If it is absent, omit it entirely.

Do not treat the summary table as evidence when the same finding also appears in \
the prose -- prefer the prose sentence. Table rows are the last resort.

Return ONLY JSON:
{{"findings": [
  {{"model": "...", "mechanism": "...", "factor": "...",
    "level": "...", "span": "verbatim sentence", "status": "clear|ambiguous"}}
]}}
"""


def _seed_text(tag: str, chars: int = 14000) -> str:
    """Document text of a seed paper. Its ground truth is never read."""
    from uofa_cli.readers.pdf_reader import read_pdf
    src = _ROOT / "tests" / "fixtures" / SEEDS[tag][0] / "source"
    text = "\n".join(c.text for p in sorted(src.glob("*.pdf")) for c in read_pdf(p))
    return text[:chars]


def _factors(standard: str) -> list[str]:
    return list(ec.VV40_FACTOR_NAMES if standard == "V&V40"
                else ec.NASA_ALL_FACTOR_NAMES)


def _family(model: str) -> str:
    m = model.split("/")[-1]
    return "anthropic" if m.startswith("claude") else "openai"


def parse_or_salvage(raw: str) -> tuple[dict, int]:
    """Parse the response; if it was cut off mid-structure, recover what closed.

    Returns (parsed, sections_lost).

    A write response truncated at the token limit is a JSONDecodeError, and
    discarding it throws away the whole paper -- one pilot run lost $0.219 that
    way. A paper with fifteen of its eighteen sections is still a usable paper,
    and the acceptance gate will reject it on word count if it is not.

    The recovery walks back to the last position where closing the open
    containers yields valid JSON, which is the end of the last complete section.
    """
    try:
        return _parse_json_response(raw), 0
    except (json.JSONDecodeError, ValueError):
        pass
    s = raw.strip()
    if s.startswith("```"):
        s = "\n".join(s.splitlines()[1:])
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
    ends = [m.start() + 1 for m in re.finditer(r"\}", s)]
    for cut in reversed(ends[-400:]):
        for suffix in ("]}", "}]}", "}", ""):
            try:
                d = json.loads(s[:cut] + suffix)
            except (json.JSONDecodeError, ValueError):
                continue
            if isinstance(d, dict) and d.get("sections"):
                return d, max(0, len(ends) - ends.index(cut) - 1)
    raise RuntimeError(
        f"unparseable and unsalvageable ({len(raw):,} chars, "
        f"ends {s[-80:]!r})")


def _row3(r) -> tuple[str, str, str] | None:
    """Coerce a model-written table row to (factor, level, basis).

    The schema asks for three cells and a real run returned 11 rows of two out of
    53 -- the model merged level and basis, or omitted the basis. Unpacking
    strictly threw away an otherwise good paper that had already cost $0.17 to
    write, two calls after the mistake. Model output is negotiated, not
    guaranteed; the escaping in `latex_render.sanitize` is where strictness
    belongs, not here.
    """
    if isinstance(r, dict):
        r = [r.get("factor"), r.get("level"), r.get("basis")]
    if not isinstance(r, (list, tuple)) or not r:
        return None
    cells = [("" if c is None else str(c)).strip() for c in r]
    cells = (cells + ["", ""])[:3] if len(cells) < 3 else cells[:3]
    return (cells[0], cells[1], cells[2]) if cells[0] else None


def build_body(sections: list[dict], device: str = "the device") -> str:
    """Model content -> LaTeX, via the renderer's helpers. No model markup."""
    out, saw_figure = [], False
    for s in sections:
        if not isinstance(s, dict) or not s.get("heading"):
            continue
        paras = [p for p in (s.get("paragraphs") or []) if isinstance(p, str) and p.strip()]
        out.append(LR.section(str(s["heading"]), paras,
                              level=min(3, max(1, int(s.get("level") or 1)))))
        if s.get("figure"):
            out.append(LR.wide_figure(str(s["figure"])))
            saw_figure = True
        r = s.get("rubric")
        if isinstance(r, dict) and r.get("factor") and r.get("rungs"):
            rungs = [str(x) for x in r["rungs"] if str(x).strip()]
            if rungs:
                out.append(LR.rubric_block(str(r["factor"]), rungs))
        t = s.get("table")
        if isinstance(t, dict) and t.get("rows"):
            rows = [x for x in (_row3(r) for r in t["rows"]) if x]
            if rows:
                out.append(LR.factor_table(rows, str(t.get("caption") or "Summary")))
    if not saw_figure:
        # R1 wants a full-width float: it puts a single-column region on a
        # two-column page, which is the case the gutter detector has to survive.
        # The run that prompted this produced none, so it is guaranteed here
        # rather than left to whether the model felt like it.
        out.insert(1, LR.wide_figure(
            f"Overview of the {device} geometry, load cases and the mechanisms "
            f"assessed, shown across the full page width."))
    # Equations and a reference list. Both are universal in real journal papers
    # and were absent from every generated one, which is why the pilot came out
    # 65-72% sentence-like against a real 46-56%: real papers are 38-46% short
    # fragments and the generated ones only 19-27%. The gap is structural, not a
    # matter of prose style.
    if len(out) > 3:
        out.insert(len(out) // 2, LR.equations(
            ["CI_{score}", "\\varepsilon_{rel}", "U_{val}"]))
    out.append(LR.bibliography(_REFS, seed=abs(hash(device)) % 10_000))
    return "\n\n".join(out)


# Real papers carry 30-80 references, and within that range the count decides the
# segmentation profile, because author initials shatter each entry into 1-2 word
# fragments -- `Qasim, X.`, `[10] F.T.`, `S., Delp, D.` are all real segments from
# Bologna and OpenSim. Measured across the three pilot papers:
#
#     refs   sentence-like mean
#      46          0.423
#      34          0.465   <- real is 0.46
#      24          0.504
#      16          0.537
#
# Chosen because it lands the profile AND sits in the real range, not by picking
# a number and hoping. Without any bibliography the pilot came out at 0.652.
_REFS = 34


# Per-step wall-clock budgets. The shared factory's 240s is sized for the
# markdown generator's short calls; the first pilot spent $0.04 and produced
# nothing because all three papers cleared the plan step and then timed out
# writing. Asking gpt-5 for 5000-9000 words of prose plus its reasoning is
# minutes of generation, not seconds.
TIMEOUTS = {"plan": 300.0, "write": 1500.0, "gold": 900.0}

# Gold runs once per MODEL rather than once for the whole paper. One call had to
# enumerate every (model x mechanism x factor) inside a single completion budget
# that gpt-5 also draws reasoning from: two of three papers returned zero bytes
# and the third returned four findings out of an available eighty. Splitting by
# model bounds each output, and it hands the call an explicit scope -- the same
# correction that has now been needed five times in this work.
GOLD_MAX_TOKENS = 32000


def _ask(backend, step: str, prompt: str, max_tokens: int = 16000,
         temperature: float = 0.7, save_to: pathlib.Path | None = None
         ) -> tuple[str, int, int]:
    """One call. Returns (text, tokens_in, tokens_out).

    The budget is generous because gpt-5 draws reasoning tokens from the same
    allowance as the completion: a budget sized for the visible answer alone
    returns an empty string rather than an error. The backend already handles
    that family's other two quirks -- `max_completion_tokens` instead of
    `max_tokens`, and rejecting any non-default temperature -- so temperature is
    passed here and dropped there when unsupported.
    """
    text = backend.generate(prompt, GenerationOptions(
        temperature=temperature, max_tokens=max_tokens,
        timeout_seconds=TIMEOUTS[step]))
    # Written BEFORE anything can reject it. --save-raw used to run after the
    # parse, so the one response worth inspecting -- the one that failed to
    # parse -- was the only one not kept. That discarded $0.219 of output whose
    # defect could then only be guessed at.
    if save_to is not None:
        save_to.parent.mkdir(parents=True, exist_ok=True)
        save_to.write_text(text or "")
    if not (text or "").strip():
        raise RuntimeError(
            f"{step}: empty response. gpt-5 draws reasoning tokens from the "
            f"completion budget, so a max_tokens of {max_tokens} may have been "
            "spent before any visible output.")
    return text, _approx_tokens(prompt), _approx_tokens(text)


def generate_one(idx: int, seed_tag: str, out_root: pathlib.Path, backend,
                 gold_backend, save_raw: pathlib.Path | None) -> dict:
    """plan -> write -> render -> gold. Returns a report row."""
    started = datetime.now(timezone.utc)
    bundle_id = f"bundle_seeded_{idx:03d}_{seed_tag}"
    bdir = out_root / bundle_id
    rep = {"bundle_id": bundle_id, "seed": seed_tag, "status": "failed",
           "tokens_in": 0, "tokens_out": 0, "cost_estimate_usd": 0.0, "error": None}
    if (bdir / "ground_truth.json").exists():
        rep["status"] = "skipped"
        return rep
    try:
        standard = SEEDS[seed_tag][1]
        device, concern, method = DOMAINS[idx % len(DOMAINS)]
        rng = random.Random(f"seeded:{bundle_id}")
        scope = sparse_scope(_factors(standard), bundle_id)

        _raw = (lambda step: (save_raw / f"{bundle_id}.{step}.json") if save_raw else None)

        # Resume. A paper whose PDF compiled but whose gold failed has already
        # been paid for twice over; regenerating it from the plan discards a
        # rendered document to redo the one step that broke. Two papers in a
        # pilot sat in exactly this state.
        pdf = bdir / "source" / "paper.pdf"
        planfile = bdir / "plan.json"
        if pdf.exists() and planfile.exists():
            plan = json.loads(planfile.read_text())
            rep["resumed_from_existing_pdf"] = True
        else:
            plan_raw, ti, to = _ask(backend, "plan", PLAN_PROMPT.format(
                standard=standard, seed_excerpt=_seed_text(seed_tag),
                device=device, concern=concern, method=method,
                n_models=rng.choice([2, 2, 3]), n_mech=rng.choice([2, 3, 3, 4]),
                scope="\n".join(f"- {f}" for f in scope),
                standard_rules=_VV40_RULES if standard == "V&V40" else _7009A_RULES),
                save_to=_raw("plan"))
            rep["tokens_in"] += ti; rep["tokens_out"] += to
            plan = _parse_json_response(plan_raw)
            bdir.mkdir(parents=True, exist_ok=True)
            # Written before the write step, so a resume has what gold needs.
            planfile.write_text(json.dumps(plan, indent=2) + "\n")

            write_raw, ti, to = _ask(backend, "write", WRITE_PROMPT.format(
                standard=standard, plan=json.dumps(plan, indent=2)), max_tokens=40000,
                save_to=_raw("write"))
            rep["tokens_in"] += ti; rep["tokens_out"] += to
            content, lost = parse_or_salvage(write_raw)
            if lost:
                rep["sections_lost_to_truncation"] = lost

            spec = {"title": content["title"], "runhead": content["runhead"],
                    "authors": content["authors"],
                    "affiliations": content["affiliations"],
                    "abstract": content["abstract"], "keywords": content["keywords"],
                    "body": build_body(content["sections"], device)}
            tex = LR.render(spec)
            bad = LR.validate(tex)
            if bad:
                raise RuntimeError(f"invalid LaTeX: {bad}")
            pdf = LR.compile_pdf(tex, pdf)

        path = LR.measure(pdf)
        missing = LR.check(path)
        if missing:
            raise RuntimeError("too clean, regenerate: " + "; ".join(missing))

        from uofa_cli.readers.pdf_reader import read_pdf
        doc = "\n".join(c.text for c in read_pdf(pdf))
        mechs = ", ".join(m["name"] for m in plan["mechanisms"])
        raw_findings, empty = [], []
        for mi, m in enumerate(plan["models"]):
            g_raw, ti, to = _ask(
                gold_backend, "gold",
                # The FULL checklist for the standard, not this paper's sparse
                # scope. Without any list at all, gold invented its own labels
                # -- "Credibility matrix", "Credibility rating" -- which are
                # document artifacts rather than factors, and left one bundle
                # with zero of ten names in common with the standard's.
                #
                # Full rather than sparse so gold and the agreement annotator
                # choose from the same set: handing gold the withheld subset
                # would make selection agreement measure who knew the scope
                # rather than who read the paper.
                GOLD_PROMPT.format(models=m["name"], mechanisms=mechs,
                                   factors="\n".join(f"- {x}" for x in _factors(standard)),
                                   document=doc[:120000]),
                max_tokens=GOLD_MAX_TOKENS, save_to=_raw(f"gold{mi}"))
            rep["tokens_in"] += ti; rep["tokens_out"] += to
            try:
                got, _ = parse_or_salvage(g_raw)
            except (RuntimeError, ValueError):
                empty.append(m["name"])
                continue
            for f in got.get("findings", []):
                f.setdefault("model", m["name"])
                raw_findings.append(f)
        if not raw_findings:
            raise RuntimeError(f"gold produced nothing for any model ({empty})")
        if empty:
            rep["gold_models_without_findings"] = empty

        # A span the model did not copy verbatim is not evidence -- drop it
        # rather than let an approximate quote become the routing target.
        flat = " ".join(doc.split()).lower()
        kept = [f for f in raw_findings
                if " ".join(str(f.get("span", "")).split()).lower() in flat]
        dropped = len(raw_findings) - len(kept)

        (bdir / "ground_truth.json").write_text(json.dumps(
            {"bundle_id": bundle_id, "standard": standard, "seed": seed_tag,
             "device": device, "scope_allowed": scope,
             "models": plan["models"], "mechanisms": plan["mechanisms"],
             "deviation": plan.get("deviation"),
             "findings": kept, "spans_dropped_not_verbatim": dropped},
            indent=2) + "\n")
        (bdir / "metadata.json").write_text(json.dumps(
            {"bundle_id": bundle_id, "standard": standard, "seed": seed_tag,
             "generated_at": started.isoformat(), "pathology": path}, indent=2) + "\n")
        rep.update(status="generated", pathology=path, findings=len(kept),
                   spans_dropped=dropped)
    except Exception as exc:  # noqa: BLE001 -- one bad paper must not stop the run
        rep["error"] = f"{type(exc).__name__}: {exc}"
    rep["cost_estimate_usd"] = estimate_cost(
        backend.model_name, rep["tokens_in"] + rep["tokens_out"],
        output_ratio=rep["tokens_out"] / max(rep["tokens_in"] + rep["tokens_out"], 1))
    rep["elapsed_s"] = (datetime.now(timezone.utc) - started).total_seconds()
    return rep


def _load_key(path: pathlib.Path | None, var: str) -> None:
    """Put a key in the environment without it reaching the repo or the shell."""
    if os.environ.get(var) or path is None:
        return
    if not path.exists():
        raise SystemExit(f"{var} not set and {path} does not exist")
    os.environ[var] = path.read_text().strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--seeds", default="opensim,bologna,nagaraja")
    ap.add_argument("--model", default="gpt-5")
    ap.add_argument("--gold-model", default=None,
                    help="defaults to --model; must differ in family from "
                         "--agreement-model")
    ap.add_argument("--agreement-model", default="claude-sonnet-4-6",
                    help="not called here; asserted cross-family so the corpus "
                         "cannot be built in a shape the check cannot validate")
    ap.add_argument("--output-root", type=pathlib.Path, required=True)
    ap.add_argument("--max-cost", type=float, default=2.0)
    ap.add_argument("--parallel", type=int, default=3)
    ap.add_argument("--save-raw", type=pathlib.Path, default=None)
    ap.add_argument("--openai-key-file", type=pathlib.Path, default=None)
    ap.add_argument("--anthropic-key-file", type=pathlib.Path, default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="plan the run and render one paper from canned content, "
                         "with no API calls")
    args = ap.parse_args()

    seeds = [s.strip() for s in args.seeds.split(",") if s.strip()]
    # Held-back first: these ARE valid documents, so "unknown seed" would be both
    # wrong and unhelpful. Checking membership first made this branch dead code.
    held = [s for s in seeds if s in HELD_BACK]
    if held:
        raise SystemExit(
            f"{held} is held back and must not seed generation. elemance and "
            "morrison carry the failure modes least replaceable by anything "
            "generated, and they are the only clean measurement surface left "
            "for a model trained on this corpus.")
    bad = [s for s in seeds if s not in SEEDS]
    if bad:
        raise SystemExit(f"unknown seed(s) {bad}; known: {sorted(SEEDS)}")

    gold_model = args.gold_model or args.model
    if _family(gold_model) == _family(args.agreement_model):
        raise SystemExit(
            f"gold model {gold_model!r} and agreement model "
            f"{args.agreement_model!r} are the same family. Same family twice "
            "measures determinism, not reliability -- the cross-family split is "
            "what made the circularity result meaningful.")

    if args.output_root.exists() and any(args.output_root.glob("bundle_*")):
        print(f"  note: {args.output_root} already has bundles; existing ones "
              f"are skipped, never overwritten")

    if args.dry_run:
        print(f"\nDRY RUN — {args.count} papers into {args.output_root}")
        print(f"  seeds {seeds}  ·  held back {list(HELD_BACK)}")
        print(f"  write={args.model}  gold={gold_model} ({_family(gold_model)})  "
              f"agreement={args.agreement_model} ({_family(args.agreement_model)})")
        for i in range(args.count):
            tag = seeds[i % len(seeds)]
            dev, concern, method = DOMAINS[i % len(DOMAINS)]
            std = SEEDS[tag][1]
            sc = sparse_scope(_factors(std), f"bundle_seeded_{i:03d}_{tag}")
            print(f"  {i:3d}  {tag:9s} {std:6s} {dev:32s} {len(sc):2d}/"
                  f"{len(_factors(std)):2d} factors in scope")
        print("\n  rendering one paper from canned content to prove the "
              "render->measure->gate path...")
        p = LR.compile_pdf(LR.render(LR.demo_spec(0)),
                           args.output_root / "_dryrun" / "paper.pdf")
        m = LR.measure(p)
        miss = LR.check(m)
        print(f"  {p}: {'OK' if not miss else 'MISSING ' + '; '.join(miss)}")
        print("  no API calls made, nothing billed")
        return 0

    _load_key(args.openai_key_file, "OPENAI_API_KEY")
    _load_key(args.anthropic_key_file, "ANTHROPIC_API_KEY")
    # --max-cost is the only bound on the bill, and estimate_cost returns 0.0 for
    # an unpriced model, which would accumulate $0 and never reach the ceiling.
    assert_priced(args.model)
    assert_priced(gold_model)

    backend = _make_backend(args.model)
    gold_backend = backend if gold_model == args.model else _make_backend(gold_model)
    args.output_root.mkdir(parents=True, exist_ok=True)

    print(f"\nGenerating {args.count} papers into {args.output_root}")
    print(f"  write={args.model}  gold={gold_model}  max_cost=${args.max_cost:.2f}")

    spent, reports, halted = 0.0, [], False
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as ex:
        futs = {ex.submit(generate_one, i, seeds[i % len(seeds)], args.output_root,
                          backend, gold_backend, args.save_raw): i
                for i in range(args.count)}
        for fut in concurrent.futures.as_completed(futs):
            try:
                r = fut.result()
            except concurrent.futures.CancelledError:
                continue
            reports.append(r)
            spent += r["cost_estimate_usd"]
            print(f"  [{len(reports)}/{args.count}] {r['bundle_id']:28s} "
                  f"{r['status']:9s} (${r['cost_estimate_usd']:.3f}, "
                  f"total ${spent:.2f})")
            if r["error"]:
                print(f"      {r['error'][:160]}")
            if spent >= args.max_cost and not halted:
                print(f"\n!! --max-cost ${args.max_cost:.2f} reached; cancelling.")
                halted = True
                for f in futs:
                    if not f.done():
                        f.cancel()

    ok = sum(1 for r in reports if r["status"] == "generated")
    (args.output_root / "generation_report.json").write_text(json.dumps(
        {"generated_at": datetime.now(timezone.utc).isoformat(),
         "model": args.model, "gold_model": gold_model, "seeds": seeds,
         "n_generated": ok, "n_failed": sum(1 for r in reports if r["status"] == "failed"),
         "total_cost_estimate_usd": round(spent, 4), "halted_at_max_cost": halted,
         "reports": reports}, indent=2) + "\n")
    print(f"\n  generated {ok}/{args.count}, ${spent:.2f}")
    print(f"  NEXT: python dev/tools/scripts/corpus_profile.py --corpus "
          f"{args.output_root}")
    print("  The corpus is not usable until that exits 0.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
