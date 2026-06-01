"""Bakeoff runner — generate stock-model answers over the corpus, then score.

The thin half of the Gate (the scorecard in ``score.py`` is the substantive
half). For each answer-keyed row it builds the **retrieval surface** P0 uses
(instruction + the fired pattern's definition + D-category + measures + case
context + standard anchor + the §5B action vocabulary), generates a structured
answer with the **stock model** (Ollama/Qwen via the shared LLM backend), and
normalizes it for ``score.scorecard``.

Re-pointable: the same prompt + schema serve the **explanation** task and the
**disposition** task — both ask for a selected §5B action class + a verbalized
confidence; the disposition slice just carries harder, adjudicated keys.

Run it:  ``python -m harness.bakeoff.run_p0 --corpus harness/bakeoff/corpus``
The model is whatever the project ``[llm]`` config resolves (the appliance's
bundled Qwen by default). Pass ``--model`` / ``--backend`` to pin a gate size.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# The §5B action vocabulary the model must select from (kept in sync with score.py).
ACTION_CLASSES = ["supply-evidence", "acquire-validation", "restrict-cou", "accept-residual-risk", "reject"]

ANSWER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "finding": {"type": "string"},
        "why_fired": {"type": "string"},
        "recommended_action": {"type": "string"},
        "action_class": {"type": "string", "enum": ACTION_CLASSES},
        "confidence": {"type": "string"},
        "escalate": {"type": "boolean"},
    },
    "required": ["finding", "action_class", "confidence", "escalate"],
}


# Ablation conditions — vary ONLY what the prompt reveals, to measure the lift the
# weakener catalog/rule gives (see harness/bakeoff/ablation.py).
# `raw_artifact` is the coverage experiment's K1 (Experiment B): the model reads the
# UNSTRUCTURED evidence package as prose (the defeater present but unflagged), no SIP
# fields, no catalog — the buyer's "paste the docs into a good LLM" alternative.
CONDITIONS = ("full", "fired_flag", "definition_only", "catalog_ablated", "measures_only", "raw_artifact")

FULL_INSTR_DEFAULT = (
    "A weakener fired on a credibility evidence package. Using ONLY the supplied pattern "
    "definition and measures, explain what the flag means, why it fired, and what the engineer "
    "should do. Stay within measure-don't-judge: report on the evidence package, never on "
    "whether the model is correct."
)
# Neutral instruction for the ablated conditions — does NOT presuppose a problem, and is
# identical across fire and control cells (so it never leaks the fire/suppress polarity).
ABLATED_INSTR = (
    "You are reviewing a physics-AI surrogate's credibility evidence package. From the "
    "information below, decide whether the package adequately supports the surrogate's use for "
    "its context of use, and choose the single most appropriate action. If the evidence is "
    "adequate the right action may be to accept; if it is not, choose the action that addresses "
    "the gap. Stay within measure-don't-judge: report on the evidence package, never on whether "
    "the model is correct."
)


def _footer() -> str:
    return (
        "\nChoose ONE recommended action_class from this controlled vocabulary "
        f"(§5B): {ACTION_CLASSES}.\n"
        "Report a verbalized confidence (high / medium / low or a 0-1 number) and set "
        "escalate=true if you are not confident enough to recommend a disposition.\n"
        "Respond as JSON: {finding, why_fired, recommended_action, action_class, confidence, escalate}."
    )


def build_prompt(row: dict, condition: str = "full", measures_variant: str = "named") -> str:
    """Assemble the prompt for one row under an ablation ``condition``.

    The output schema, the §5B menu, and everything held out (answer_key, hardness,
    provenance) are identical across conditions — only the *revealed* inputs change,
    so the gate metrics are directly comparable and their difference is the lift.

    ``measures_variant``: ``"named"`` uses the conclusion-bearing measures;
    ``"raw"`` uses the de-named ``measures_raw`` (raw signals — the fair detection test).
    """
    inp = row.get("input", {})
    pattern = inp.get("fired_pattern", {})
    chosen = inp.get("measures_raw") or inp.get("measures", {}) if measures_variant == "raw" else inp.get("measures", {})
    measures = "MEASURES:\n" + json.dumps(chosen, indent=2)
    context = "CASE CONTEXT:\n" + json.dumps(inp.get("case_context", {}), indent=2)

    if condition == "full":
        body = [inp.get("instruction", FULL_INSTR_DEFAULT), "",
                f"FIRED PATTERN: {pattern.get('id', '?')}  (D-category: {pattern.get('d_category', '?')})",
                f"DEFINITION: {pattern.get('definition', '')}",
                f"STANDARD ANCHOR: {pattern.get('standard_anchor', '')}", "", measures, "", context]
    elif condition == "fired_flag":
        body = [ABLATED_INSTR + " A weakener rule fired on this package; its definition is withheld.",
                "", f"FIRED PATTERN: {pattern.get('id', '?')}  (definition withheld)", "", measures, "", context]
    elif condition == "definition_only":
        body = [ABLATED_INSTR + " Consider whether the following candidate concern applies, judging only from the measures.",
                "", f"CANDIDATE CONCERN: {pattern.get('definition', '')}", "", measures, "", context]
    elif condition == "catalog_ablated":
        body = [ABLATED_INSTR, "", measures, "", context]
    elif condition == "measures_only":
        body = [ABLATED_INSTR, "", measures]
    elif condition == "raw_artifact":
        artifact = inp.get("raw_artifact")
        if not artifact:
            raise ValueError(f"row {row.get('row_id')} has no raw_artifact (coverage cells only)")
        body = [ABLATED_INSTR, "",
                "INTENDED USE: " + inp.get("case_context", {}).get("cou", ""), "",
                "EVIDENCE PACKAGE (as supplied by the surrogate's authors):", artifact]
    else:
        raise ValueError(f"unknown ablation condition: {condition!r} (use one of {CONDITIONS})")
    return "\n".join(body) + "\n" + _footer()


def _infer_action_class(text: str) -> str | None:
    """Fallback class inference from free text when the model didn't emit one."""
    low = (text or "").lower()
    for cls in ACTION_CLASSES:
        if cls in low or cls.replace("-", " ") in low:
            return cls
    return None


def _normalize(row: dict, out: dict) -> dict:
    """Reduce a raw model answer to the fields ``score.score_row`` consumes."""
    action_class = out.get("action_class") or _infer_action_class(out.get("recommended_action", ""))
    return {
        "row_id": row.get("row_id"),
        "action_class": action_class,
        "confidence": out.get("confidence", "medium"),
        "escalate": bool(out.get("escalate", False)),
        "raw": out,
    }


def generate_answer(backend, row: dict, *, condition: str = "full",
                    measures_variant: str = "named", seed: int = 0,
                    temperature: float = 0.0) -> dict:
    """Generate one structured answer for a row via the stock model backend.

    ``temperature`` defaults to 0.0 (greedy/deterministic — the canonical operating
    point and what the recorded runs use). At temp 0 the ``seed`` is inert; set
    temperature > 0 for a genuine multi-seed sampling-robustness check."""
    from uofa_cli.llm import GenerationOptions

    prompt = build_prompt(row, condition, measures_variant)
    options = GenerationOptions(temperature=temperature, seed=seed, max_tokens=700)
    if backend.supports_structured_output():
        out = backend.generate_structured(prompt, ANSWER_SCHEMA, options)
    else:
        text = backend.generate(prompt, options)
        out = _parse_json(text)
    return _normalize(row, out if isinstance(out, dict) else {})


def _parse_json(text: str) -> dict:
    """Best-effort JSON extraction from a free-text completion."""
    text = (text or "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except ValueError:
            pass
    return {}


def load_corpus(corpus_dir: str | Path) -> list[dict]:
    """Load every ``*.json`` answer-keyed row under ``corpus_dir`` (sorted)."""
    rows = []
    for path in sorted(Path(corpus_dir).glob("*.json")):
        rows.append(json.loads(path.read_text(encoding="utf-8")))
    return rows


def run_corpus(rows: list[dict], backend=None, *, condition: str = "full",
               measures_variant: str = "named", seed: int = 0,
               temperature: float = 0.0) -> list[dict]:
    """Generate answers for every row under ``condition``. ``backend`` defaults to the
    project config (the appliance's bundled stock model); pass one in tests."""
    if backend is None:
        from uofa_cli.llm import get_backend
        backend = get_backend()
    answers = []
    for i, row in enumerate(rows, 1):
        print(f"  [{i}/{len(rows)}] {condition}/{measures_variant} seed={seed} T={temperature}: "
              f"{row.get('row_id')}", flush=True)
        answers.append(generate_answer(backend, row, condition=condition,
                                       measures_variant=measures_variant, seed=seed,
                                       temperature=temperature))
    return answers


def main(argv: list[str] | None = None) -> int:
    from harness.bakeoff import score

    parser = argparse.ArgumentParser(description="Run the P0 bakeoff (stock-local floor test).")
    parser.add_argument("--corpus", type=Path, default=Path("harness/bakeoff/corpus"))
    parser.add_argument("--model", help="override [llm] model (the gate size, e.g. qwen2.5:7b)")
    parser.add_argument("--backend", help="override [llm] backend (default: project config)")
    parser.add_argument("--alpha", type=float, default=0.02, help="selective-risk bound (default 0.02)")
    parser.add_argument("--output", type=Path, help="write answers + scorecard JSON here")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    rows = load_corpus(args.corpus)
    if not rows:
        print(f"no corpus rows under {args.corpus}")
        return 2

    backend = None
    if args.model or args.backend:
        from uofa_cli.llm import get_backend
        overrides = {k: v for k, v in (("model", args.model), ("backend", args.backend)) if v}
        backend = get_backend(cli_overrides=overrides)

    answers = run_corpus(rows, backend, seed=args.seed)
    card = score.scorecard(rows, answers, alpha=args.alpha)
    read = score.gate_read(card)

    print(json.dumps({"scorecard": card, "gate_read": read}, indent=2))
    if args.output:
        args.output.write_text(json.dumps({"answers": answers, "scorecard": card, "gate_read": read},
                                          indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
