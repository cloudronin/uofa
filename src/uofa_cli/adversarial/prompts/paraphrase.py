"""Phase 2 v1.8 §7.6 paraphrasing layer.

Tests rule-firing robustness against wording variations of the canonical
prompts. Two paraphrase variants (``p1`` and ``p2``) are deterministic
text substitutions applied to the parent template's render output —
rather than 20 hand-authored module copies — so the canonical templates
remain a single source of truth and snapshots stay reproducible.

The substitutions deliberately avoid altering schema instructions
(field names, JSON shape, SHACL trigger language) so a paraphrased
package still has the same structural goal; only descriptive prose,
section headers, and tone shift.

Per §7.6 selection (10 specs × 3 paraphrases × 3 variants = 90 packages),
the goal is to test whether the LLM's ability to generate triggering
structures is robust to non-structural prompt variations.
"""

from __future__ import annotations

#: Paraphrase 1 — academic / formal register. Section headers and
#: descriptive prose shift; structural directives (SCHEMA RULES, *_TRIGGER
#: blocks, field names) are deliberately preserved.
_SUBSTITUTIONS_P1: dict[str, str] = {
    # System-prompt-level
    "You generate synthetic simulation-credibility evidence":
        "You produce synthetic simulation-credibility artifacts",
    "Packages are used to test a weakener-detection system":
        "These artifacts exercise an automated weakener-detection pipeline",
    "Plausible on a quick read.":
        "Superficially plausible to a domain expert.",
    "Output ONLY the JSON-LD package as a single valid JSON object.":
        "Emit ONLY the JSON-LD package as a single valid JSON object.",
    # User-prompt-level (descriptive headers only — never schema directives)
    "Target weakener:":
        "Targeted defeater pattern:",
    "Subtlety level:":
        "Plausibility tier:",
    "Base COU skeleton (preserve the identity block verbatim in the output):":
        "Provided COU skeleton — copy the identity block verbatim:",
    "Factor scaffolding —":
        "Credibility-factor scaffold —",
    "Task: generate":
        "Task: produce",
}

#: Paraphrase 2 — terse / imperative register. Mirrors many prompt-injection
#: defenses' compressed style.
_SUBSTITUTIONS_P2: dict[str, str] = {
    # System-prompt-level
    "You generate synthetic simulation-credibility evidence in JSON-LD for ASME\nV&V 40 analysis.":
        "Produce synthetic V&V 40 simulation-credibility evidence in JSON-LD.",
    "Requirements:":
        "Constraints:",
    "Plausible on a quick read.":
        "Reads as plausible at first glance.",
    "Output ONLY the JSON-LD package as a single valid JSON object. No commentary.\nNo markdown fences. No trailing text. Close every brace.":
        "Return only the JSON-LD object. No prose, no fences, no trailing text.",
    # User-prompt-level
    "Target weakener:":
        "Weakener:",
    "Defeater type:":
        "Defeater:",
    "Subtlety level:":
        "Subtlety:",
    "Task: generate":
        "Generate",
    "Base COU skeleton (preserve the identity block verbatim in the output):":
        "COU skeleton (identity block must be preserved verbatim):",
}

_SUBSTITUTION_TABLES: dict[str, dict[str, str]] = {
    "p0": {},
    "p1": _SUBSTITUTIONS_P1,
    "p2": _SUBSTITUTIONS_P2,
}


def apply_paraphrase(
    variant: str, system_prompt: str, user_prompt: str
) -> tuple[str, str]:
    """Return paraphrased ``(system_prompt, user_prompt)`` for *variant*.

    ``variant="p0"`` is the identity (no-op) and is the default for any
    spec that does not opt into paraphrasing.
    """
    table = _SUBSTITUTION_TABLES.get(variant) or {}
    sys_p = system_prompt
    user_p = user_prompt
    for old, new in table.items():
        sys_p = sys_p.replace(old, new)
        user_p = user_p.replace(old, new)
    return sys_p, user_p


def is_paraphrased(variant: str) -> bool:
    """True when *variant* is a non-identity paraphrase."""
    return variant in {"p1", "p2"}
