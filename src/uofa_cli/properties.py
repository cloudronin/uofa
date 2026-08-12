"""Group-B property definitions: one source, two rendered artifacts.

    python -m uofa_cli.properties --check     # verify both artifacts are current
    python -m uofa_cli.properties --write     # re-render them from source

The labeling instruction sheet and the extraction prompt both describe the same
seven properties. Written independently they drifted, silently, for months --
P7's sheet counted "ablations offered as controls" while the prompt named
neither ablations nor limitation statements, and three model families scored
100% false-fire on P7 as a direct consequence (see
`studies/taxonomy-validation/enrichment/CONSTRUCT-DRIFT.md`).

Neither document was edited carelessly. Two faithful paraphrases of one intent
drift because nothing holds them together. So they no longer paraphrase: both
RENDER from `packs/model-credibility/properties/P*.json`, into marker-delimited regions,
and a test asserts the committed regions are byte-identical to a fresh render.

A definition changes in the JSON or it does not change.

**Rendering the prompt changes what was measured.** Its hash is pinned into
every specificity result, so a re-render is a new measurement and belongs to a
new pinned row -- never a fix folded into an existing table.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from uofa_cli import paths

SHEET = "docs/A16_3_gold_labeling_instructions_v0_1.md"
PROMPT = "packs/model-credibility/prompts/card_eval_extract_prompt.txt"

SHEET_MARKERS = ("<!-- BEGIN property-definitions -->",
                 "<!-- END property-definitions -->")
PROMPT_MARKERS = ("# BEGIN property-fields", "# END property-fields")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load(pack: str = "model-credibility") -> list[dict]:
    """Every property definition, ordered P1..P7."""
    directory = paths.pack_dir(pack) / "properties"
    out = [json.loads(p.read_text(encoding="utf-8"))
           for p in sorted(directory.glob("P*.json"))]
    if not out:
        raise FileNotFoundError(f"no property definitions in {directory}")
    return out


def render_sheet(props: list[dict]) -> str:
    """The instruction sheet's §2 body — what a human labeler reads."""
    lines: list[str] = []
    for p in props:
        lines.append(f"### {p['id'].split('_')[0]}. `{p['vocab']}` — {p['title']}")
        if p.get("claim"):
            lines.append(f"- **The claim:** {p['claim']}")
        lines.append("- **Present:** " + "; ".join(p["present"]) + ".")
        lines.append("- **Absent:** " + "; ".join(p["absent"]) + ".")
        if p.get("note"):
            lines.append(f"- {p['note']}")
        if p.get("worked_negative"):
            # The negative example is the half a definition usually omits, and
            # it is where the 2026-08-11 label review found every over-generous
            # call. Stating what does NOT count is not padding.
            lines.append(f"- **Does NOT count:** {p['worked_negative']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_prompt_fields(props: list[dict]) -> str:
    """The extraction prompt's field block — what the model reads.

    Same definitions, compressed to one line per field because the prompt is
    read per-call. Compression is mechanical: the present-examples become the
    field description, so the model is asked for exactly what the sheet counts.
    """
    lines: list[str] = []
    for p in props:
        if p["field"] == "metric_value":
            continue                     # carries its own format spec in the prompt
        desc = "; ".join(p["present"]) + "; blank if absent"
        if p.get("worked_negative"):
            # The blank rule comes BEFORE the negative example, so "blank if
            # absent" attaches to the property rather than trailing a paragraph
            # about what does not count -- where it reads as part of the
            # counter-example.
            desc += f".\n  DOES NOT COUNT: {p['worked_negative']}"
        lines.append(f"{p['field']}: <{desc}>")
    return "\n".join(lines) + "\n"


def _region(text: str, markers: tuple[str, str]) -> tuple[int, int]:
    begin, end = markers
    i, j = text.find(begin), text.find(end)
    if i == -1 or j == -1:
        raise ValueError(f"markers {begin!r}/{end!r} not found")
    return i + len(begin), j


def current(path: Path, markers: tuple[str, str]) -> str:
    text = path.read_text(encoding="utf-8")
    lo, hi = _region(text, markers)
    return text[lo:hi].strip("\n") + "\n"


def write(path: Path, markers: tuple[str, str], body: str) -> None:
    text = path.read_text(encoding="utf-8")
    lo, hi = _region(text, markers)
    path.write_text(text[:lo] + "\n" + body + text[hi:], encoding="utf-8")


def targets(pack: str = "model-credibility") -> list[tuple[Path, tuple[str, str], str]]:
    props = load(pack)
    root = _repo_root()
    return [
        (root / SHEET, SHEET_MARKERS, render_sheet(props)),
        (root / PROMPT, PROMPT_MARKERS, render_prompt_fields(props)),
    ]


def check(pack: str = "model-credibility") -> list[str]:
    """Paths whose committed region differs from a fresh render."""
    stale = []
    for path, markers, body in targets(pack):
        try:
            if current(path, markers) != body:
                stale.append(str(path.relative_to(_repo_root())))
        except (ValueError, FileNotFoundError):
            stale.append(f"{path.name} (markers missing)")
    return stale


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--pack", default="model-credibility")
    args = ap.parse_args()

    if args.write:
        for path, markers, body in targets(args.pack):
            write(path, markers, body)
            print(f"  rendered {path.relative_to(_repo_root())}")
        return 0

    stale = check(args.pack)
    if stale:
        print("  STALE (run --write):")
        for s in stale:
            print(f"    {s}")
        return 1
    print("  both artifacts match the property source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
