"""The probe that found the extract-prompt routing bug, by being wrong.

Kept because its negative result is the finding. See FINDINGS.md.

The question it was built to answer: the shipped extractor emitted exactly the
13 ASME V&V 40 factors and none of the 6 NASA-only ones, in 27 of 27 NASA
extractions, with zero variance. Not truncation -- the saved raw response was
6.4 KB against a 16,384-token cap and ended in a complete DECISION block. Two
hypotheses, with different fixes:

  H-placement  "Include ALL 19 factors" sits ~120 lines below the factor list,
               under "## Rules". The model takes the "### V&V 40 Factors (13)"
               heading as the whole task. Same failure mode as the shopping-list
               finding, where this model skimmed a rule 14 lines below the spec
               it governed (studies/prompt-absence/).

  H-capability The model cannot hold 19 factor blocks in one response.

Arm A is the shipped NASA prompt. Arm B is the same prompt with the count
instruction moved adjacent to the list and restated at the FACTOR block spec.
Three runs each, same corpus, same session.

    A shipped    [6, 6, 6]      NASA-only factors emitted, per run
    B relocated  [6, 6, 6]

Both arms returned all 19 factors every time. Neither hypothesis survived --
and that is what located the bug. The shipped NASA prompt worked perfectly
whenever it was actually delivered, which meant it was not being delivered.
`paths.extract_prompt()` took no pack name and returned the V&V 40 prompt for
every pack.

The distinguishing detail between this probe and the shipped pipeline is one
line: the probe reads `packs/nasa-7009b/prompts/...` explicitly, and
`extract_cmd` called `paths.extract_prompt()` with no argument.

The shipped prompt file is not modified by this script.

    UOFA_OPENAI_COMPATIBLE_API_KEY=... python studies/nasa-prompt-routing/probe_nasa_block.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from uofa_cli.document_reader import read_corpus  # noqa: E402
from uofa_cli.llm.config import LLMConfig  # noqa: E402
from uofa_cli.llm_extractor import _call_llm, assemble_corpus_text  # noqa: E402

PROMPT = ROOT / "packs/nasa-7009b/prompts/nasa_7009b_extract_prompt.txt"
EVIDENCE = ROOT / "tests/fixtures/extract/aero-evidence-cou2"

# The legacy "<backend>@<url>|<model>" string is a score_extraction.py
# convention that it turns into CLI flags; _legacy_model_to_config does not
# understand it and falls back to Ollama. Build the config the flags build.
CONFIG = LLMConfig(
    backend="openai-compatible",
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    base_url="https://api.together.xyz/v1",
    api_key_env="UOFA_OPENAI_COMPATIBLE_API_KEY",
)
N_RUNS = 3

# The six that never appear. Canonical spelling, from the pack.
NASA_SIX = [
    "Data pedigree",
    "Development technical review",
    "Development process and product management",
    "Results uncertainty",
    "Results robustness",
    "Use history",
]

# Arm B: the count instruction, adjacent to the list it counts. Inserted
# immediately after factor 19's definition, i.e. at the end of the factor
# section rather than 120 lines downstream.
ADJACENT_RULE = """
### Completeness requirement for this section

The list above has **19** factors: 13 from ASME V&V 40 (numbered 1-13) and 6
from NASA-STD-7009B (numbered 14-19). This document is a NASA-STD-7009B
assessment, so all 19 apply. Emit one `=== FACTOR ===` block for each of the 19,
including 14-19, in the order listed. A NASA factor with no evidence in the
corpus still gets a block, with `status: not-assessed`. Emitting only the 13
V&V 40 factors is an incomplete extraction.
"""

# Arm B, second half: the same count restated where the blocks are written.
BLOCK_REMINDER = (
    "=== FACTOR ===\n"
    "(emit 19 of these: factors 1-13 from V&V 40, then factors 14-19 from "
    "NASA-STD-7009B -- Data pedigree, Development technical review, "
    "Development process and product management, Results uncertainty, "
    "Results robustness, Use history)\n"
)


def build_arm_b(text: str) -> str:
    """Relocate the completeness instruction. Nothing else changes."""
    anchor = "\n## Required Level Estimation"
    if anchor not in text:
        raise SystemExit("anchor '## Required Level Estimation' not found")
    text = text.replace(anchor, "\n" + ADJACENT_RULE + anchor, 1)

    # Restate at the block spec. Only the first occurrence, which is the spec;
    # later ones are inside the Rules prose.
    if "=== FACTOR ===\nfactor_type:" not in text:
        raise SystemExit("FACTOR block spec not found")
    text = text.replace(
        "=== FACTOR ===\nfactor_type:",
        BLOCK_REMINDER + "factor_type:",
        1,
    )
    return text


def emitted_factors(raw: str) -> list[str]:
    return [m.strip() for m in re.findall(r"^factor_type:\s*(.+)$", raw, re.M)]


def nasa_hits(names: list[str]) -> list[str]:
    low = [n.lower() for n in names]
    return [f for f in NASA_SIX if f.lower() in low]


def main() -> None:
    paths = sorted(p for p in EVIDENCE.iterdir() if p.name != "EVIDENCE_MANIFEST.txt")
    corpus_text = assemble_corpus_text(read_corpus(paths))

    shipped = PROMPT.read_text(encoding="utf-8")
    arm_b_prompt = build_arm_b(shipped)
    Path(__file__).with_name("probe_arm_b_prompt.txt").write_text(arm_b_prompt)
    print(f"arm B prompt: {len(arm_b_prompt) - len(shipped):+d} chars vs shipped\n")

    # Arm A is run here too rather than leaning on the 27 archived extractions,
    # so both arms see the same corpus text in the same session and the only
    # difference between them is where the count instruction sits.
    arms = {"A shipped": shipped, "B relocated": arm_b_prompt}
    totals: dict[str, list[int]] = {}

    for label, template in arms.items():
        counts = []
        for run in range(1, N_RUNS + 1):
            raw = _call_llm(
                template.replace("{corpus}", corpus_text),
                "unused-when-llm_config-given",
                "nasa-7009b",
                llm_config=CONFIG,
            )
            slug = label.split()[0].lower()
            Path(__file__).with_name(f"probe_arm_{slug}_raw_{run}.txt").write_text(raw)

            names = emitted_factors(raw)
            hits = nasa_hits(names)
            counts.append(len(hits))
            print(f"{label} run {run}: {len(names)} factor blocks, "
                  f"{len(hits)}/6 NASA-only, {len(raw)} bytes, "
                  f"{'complete' if '=== DECISION ===' in raw else 'NO DECISION BLOCK'}")
            if hits:
                print(f"    got: {', '.join(hits)}")
        totals[label] = counts

    print("\nNASA-only factors emitted, per run:")
    for label, counts in totals.items():
        print(f"  {label:<14s} {counts}")


if __name__ == "__main__":
    main()
