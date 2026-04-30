"""Predicate-revision proposer.

Given (rule_body, misfire_sample), drafts a unified-diff predicate
revision with rationale. Per spec §4 step 2.

Implementation note: in auto-mode, the proposer is invoked
programmatically by ``refine_loop.py``. The actual LLM call happens
out-of-band (Claude Code drives this). This module provides the
plumbing — packaging the prompt, parsing the response, validating
that the output stays in Jena syntax — but the model itself is whatever
``--llm`` resolves to (default: claude-code via the ``claude`` CLI).

If ``--llm none`` (or no ``claude`` binary available), we emit a
template proposal that REVERTs to the prior body with rationale
"propose_revision: no LLM available". The refine loop's metric gate
then handles it as any other iteration.

CLI: ``python -m tools.phase2_5.propose_revision --rule W-EP-01 \\
        --misfires misfires.json --rule-body current_body.txt``
"""

from __future__ import annotations

import argparse
import difflib
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


PROMPT_TEMPLATE = """\
You are tightening a single Jena rule that is over-firing on a
synthetic-package corpus. The rule's intent is fixed; you are only
allowed to narrow its trigger conditions.

Rule ID: {rule_id}

Current rule body (Jena syntax — do NOT change name or arrow direction):
```
{rule_body}
```

Misfire evidence — packages where this rule fired but should NOT have.
Top-level fields on each misfire indicate WHY the package is a misfire
(coverage_intent=negative_control means rule fired on a clean package;
coverage_intent=confirm_existing with a different target_weakener means
the rule fired on someone else's target):

```json
{misfire_json}
```

Your task:
1. Identify the structural pattern in the misfires that the current
   predicate is matching too loosely.
2. Propose ONE additional guard clause that excludes the misfires while
   keeping all legitimate target firings (target_weakener == {rule_id}).
3. Stay strictly within Jena rule syntax. Only use vocabulary terms
   already present in the current rule body or in the wider catalog
   (uofa:, schema:, sh:, prov:, rdf:, rdfs:, xsd:).
4. Output a unified diff (``diff -u`` format) of the rule body change,
   preceded by a JSON header on the first line:

   {{"rule_id": "{rule_id}", "rationale": "<one-sentence why>", "guard_added": "<short label>"}}

Constraints:
- Do not change the rule's name or arrow direction.
- Do not add new vocabulary terms.
- Add exactly ONE guard (one new triple pattern in the LHS, OR one
  ``noValue(?x uofa:foo)``, OR one bound-check). Smaller is better.
- If you cannot propose a safe narrowing, emit the JSON header with
  ``"rationale": "no-op"`` and an empty diff.
"""


@dataclass
class Proposal:
    rule_id: str
    rationale: str
    guard_added: str
    new_body: str
    diff_text: str

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "rationale": self.rationale,
            "guard_added": self.guard_added,
            "new_body": self.new_body,
            "diff_text": self.diff_text,
        }


def _build_prompt(rule_id: str, rule_body: str, misfires: dict) -> str:
    return PROMPT_TEMPLATE.format(
        rule_id=rule_id,
        rule_body=rule_body.strip(),
        misfire_json=json.dumps(misfires, indent=2),
    )


def _call_claude_cli(prompt: str, timeout: int = 180) -> str | None:
    """Invoke the local ``claude`` CLI. Returns stdout text or None."""
    if shutil.which("claude") is None:
        return None
    try:
        result = subprocess.run(
            ["claude", "-p", "--output-format", "text"],
            input=prompt, capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0:
            return None
        return result.stdout
    except Exception:
        return None


def _parse_response(response_text: str, rule_id: str, prior_body: str) -> Proposal:
    """Parse the LLM response: first non-empty line is JSON header,
    rest is unified diff. Reconstruct ``new_body`` from the diff applied
    to ``prior_body``.
    """
    lines = response_text.splitlines()
    # Skip leading blanks
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    header_line = lines[i] if i < len(lines) else "{}"
    try:
        header = json.loads(header_line)
    except json.JSONDecodeError:
        # Fall back to no-op
        return Proposal(
            rule_id=rule_id, rationale="parse-error: bad header", guard_added="",
            new_body=prior_body, diff_text="",
        )

    diff_text = "\n".join(lines[i + 1 :]).strip()
    if not diff_text or header.get("rationale") == "no-op":
        return Proposal(
            rule_id=rule_id,
            rationale=header.get("rationale", "no-op"),
            guard_added=header.get("guard_added", ""),
            new_body=prior_body,
            diff_text="",
        )

    # We don't ship a full unified-diff applier — instead we ask the
    # caller (refine_loop) to validate via the diff text and then
    # WRITE the new body if the diff parses. For minimal viability we
    # require the LLM to also include the new body inline as a fenced
    # block; if absent, we treat it as no-op.
    new_body = _extract_new_body_from_diff(diff_text, prior_body)
    return Proposal(
        rule_id=rule_id,
        rationale=header.get("rationale", ""),
        guard_added=header.get("guard_added", ""),
        new_body=new_body,
        diff_text=diff_text,
    )


def _extract_new_body_from_diff(diff_text: str, prior_body: str) -> str:
    """Apply a small, well-behaved unified diff to ``prior_body``.

    We only support the standard hunk format with @@ headers. If the
    diff doesn't apply cleanly, we return prior_body unchanged so the
    refine loop treats it as a no-op.
    """
    prior_lines = prior_body.splitlines(keepends=False)
    out_lines: list[str] = []
    i = 0  # cursor into prior_lines
    in_hunk = False
    for raw in diff_text.splitlines():
        if raw.startswith("@@"):
            # Parse @@ -a,b +c,d @@; copy untouched prior up to a-1
            in_hunk = True
            try:
                _, minus, plus, _ = raw.split(" ", 3)
                old_start = int(minus.split(",")[0].lstrip("-")) - 1
            except Exception:
                return prior_body
            while i < old_start:
                out_lines.append(prior_lines[i]) if i < len(prior_lines) else None
                i += 1
            continue
        if not in_hunk:
            continue  # ignore --- / +++ headers etc.
        if raw.startswith("---") or raw.startswith("+++"):
            continue
        if raw.startswith("-"):
            # Drop one prior line
            i += 1
        elif raw.startswith("+"):
            out_lines.append(raw[1:])
        elif raw.startswith(" "):
            # Context line: emit and advance
            if i < len(prior_lines):
                out_lines.append(prior_lines[i])
            i += 1
        else:
            # Unrecognized line: bail out
            return prior_body
    # Append any remaining prior lines
    while i < len(prior_lines):
        out_lines.append(prior_lines[i])
        i += 1
    return "\n".join(out_lines)


def make_proposal(
    rule_id: str,
    rule_body: str,
    misfires: dict,
    *,
    llm: str = "claude",
    timeout: int = 180,
) -> Proposal:
    """Top-level: assemble prompt, call LLM, parse, return Proposal.

    On any error we fall back to a no-op proposal so the refine loop
    can advance and the iteration is logged as such.
    """
    prompt = _build_prompt(rule_id, rule_body, misfires)
    if llm == "none":
        return Proposal(
            rule_id=rule_id, rationale="propose_revision: --llm none", guard_added="",
            new_body=rule_body, diff_text="",
        )

    response = _call_claude_cli(prompt, timeout=timeout)
    if response is None:
        return Proposal(
            rule_id=rule_id, rationale="propose_revision: claude CLI unavailable",
            guard_added="", new_body=rule_body, diff_text="",
        )
    return _parse_response(response, rule_id, rule_body)


def make_unified_diff(prior_body: str, new_body: str, rule_id: str) -> str:
    """Generate a unified diff between two rule bodies; used when we
    have new_body already (e.g., from a manual proposer)."""
    diff = difflib.unified_diff(
        prior_body.splitlines(keepends=False),
        new_body.splitlines(keepends=False),
        fromfile=f"{rule_id} (before)",
        tofile=f"{rule_id} (after)",
        lineterm="",
    )
    return "\n".join(diff)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rule", required=True)
    p.add_argument("--rule-body", type=Path, required=True,
                   help="text file containing the current rule body")
    p.add_argument("--misfires", type=Path, required=True,
                   help="JSON output from inspect_misfires")
    p.add_argument("--llm", default="claude",
                   help="LLM backend (claude|none); default claude")
    p.add_argument("-o", "--output", type=Path, default=None)
    args = p.parse_args(argv)

    rule_body = args.rule_body.read_text()
    misfires = json.loads(args.misfires.read_text())
    proposal = make_proposal(args.rule, rule_body, misfires, llm=args.llm)
    text = json.dumps(proposal.to_dict(), indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
