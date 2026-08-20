#!/usr/bin/env python3
"""The done-test: can a fresh session execute the protocol with no other context?

The protocol's citable property is that it is executable by someone who is not its author.
This runs the cheapest available someone: an API session whose only prompt is the protocol,
in a sandbox where the repository does not exist.

## Isolation is structural, not promised

Every bash command runs inside a fresh user+mount namespace with a tmpfs mounted over the
repository path, so the pilot's artifacts are not merely off-limits, they are absent. A
session that tries to read them sees an empty directory. That is what makes the transcript
citable rather than trusted.

The CLI is a built wheel installed into its own virtualenv, not the editable install used
elsewhere in this session. `pyproject.toml` force-includes packs, spec and specs into the
wheel, so a wheel-installed CLI resolves them with no repository present, which is what a
third-party encoder actually has. An editable install would resolve through the repo and
quietly defeat the test.

## Two models, named separately

The agent following the document and the extractor it invokes are different models and the
results record both. Conflating them would create the same lineage ambiguity the protocol's
own extractor rule exists to prevent.

Run:  python run_donetest.py --run 1
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import anthropic

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SCRATCH = Path("/tmp/claude-0/-home-user-uofa/129710c2-c0c2-5ab7-8eba-c831ccfd5aac/scratchpad")

AGENT_MODEL = "claude-opus-5"
EXTRACTOR_MODEL = "claude-sonnet-5"          # named to the runner, not injected behind it
EXTRACTOR_BACKEND = "anthropic"

PROTOCOL = REPO / "docs" / "Encoding_Protocol_v0_1_DRAFT.md"
SOURCE_PDF = REPO / "dev" / "build" / "pilot-johnson" / "source" / "NTRS-20200002832-Johnson-2020.pdf"
DONETEST_VENV = SCRATCH / "donetest-venv"

# Paths masked inside the sandbox namespace. The repo is the one that matters; the rest are
# belt and braces against a session that goes looking.
MASKED = ["/home/user/uofa"]

MAX_TURNS = 60
TOOL_TIMEOUT = 900


def build_sandbox(run: int) -> Path:
    box = Path(f"/tmp/donetest-run{run}")
    if box.exists():
        shutil.rmtree(box)
    (box / "source").mkdir(parents=True)
    (box / "work").mkdir()
    shutil.copy2(PROTOCOL, box / "ENCODING_PROTOCOL.md")
    shutil.copy2(SOURCE_PDF, box / "source" / SOURCE_PDF.name)
    return box


def run_bash(cmd: str, box: Path) -> tuple[str, int]:
    """Execute one command inside a namespace where the repository does not exist."""
    masks = "; ".join(f"mount -t tmpfs none {p} 2>/dev/null" for p in MASKED)
    inner = f"{masks}; cd {box} && {cmd}"
    env = dict(os.environ)
    env["PATH"] = f"{DONETEST_VENV / 'bin'}:/usr/local/bin:/usr/bin:/bin"
    try:
        p = subprocess.run(
            ["unshare", "-Um", "--map-root-user", "sh", "-c", inner],
            capture_output=True, text=True, timeout=TOOL_TIMEOUT, env=env,
        )
        out = (p.stdout or "") + (("\n[stderr]\n" + p.stderr) if p.stderr else "")
        return out[:60000] or "(no output)", p.returncode
    except subprocess.TimeoutExpired:
        return f"(timed out after {TOOL_TIMEOUT}s)", 124


def environment_note(box: Path) -> str:
    """The facts a third-party encoder would have. Nothing about the protocol's content."""
    return f"""You are performing one reference encoding by following the document below. The
document is the whole of your instructions.

Your working environment:

- The source document is at `source/{SOURCE_PDF.name}`. It is the only source.
- Your working directory is `work/`. Put everything you produce there.
- The `uofa` CLI is on PATH.
- The extraction backend available to you is `{EXTRACTOR_BACKEND}` with model
  `{EXTRACTOR_MODEL}`, reached with `--extract-backend {EXTRACTOR_BACKEND}
  --extract-model {EXTRACTOR_MODEL}`. `ANTHROPIC_API_KEY` is already set.
- `python3` is available with `openpyxl` and `pdfplumber` installed.
- Every shell command starts in the directory holding `ENCODING_PROTOCOL.md`.

Work autonomously and do not ask for confirmation. If the document does not answer a
question you need answered, say so explicitly in your final message rather than guessing.
When you are finished, list what you produced and where.

--- BEGIN ENCODING_PROTOCOL.md ---
{(box / "ENCODING_PROTOCOL.md").read_text(encoding="utf8")}
--- END ENCODING_PROTOCOL.md ---
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=int, required=True)
    args = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set", file=sys.stderr)
        return 1

    box = build_sandbox(args.run)
    client = anthropic.Anthropic()
    tools = [{"type": "bash_20250124", "name": "bash"}]
    messages = [{"role": "user", "content": environment_note(box)}]
    transcript = {
        "run": args.run,
        "agent_model": AGENT_MODEL,
        "extractor_model": f"{EXTRACTOR_BACKEND}/{EXTRACTOR_MODEL}",
        "protocol_sha": subprocess.run(["sha256sum", str(PROTOCOL)],
                                       capture_output=True, text=True).stdout.split()[0],
        "sandbox": str(box),
        "masked_paths": MASKED,
        "turns": [],
    }
    started = time.time()

    for turn in range(MAX_TURNS):
        with client.messages.stream(
            model=AGENT_MODEL,
            max_tokens=64000,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            tools=tools,
            messages=messages,
        ) as stream:
            resp = stream.get_final_message()

        blocks = []
        for b in resp.content:
            if b.type == "text":
                blocks.append({"type": "text", "text": b.text})
            elif b.type == "tool_use":
                blocks.append({"type": "tool_use", "input": b.input})
        transcript["turns"].append({"n": turn, "stop_reason": resp.stop_reason,
                                    "blocks": blocks})

        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            transcript["final_text"] = "\n".join(
                b.text for b in resp.content if b.type == "text")
            break

        # All tool_result blocks go back in a single user message.
        results = []
        for b in resp.content:
            if b.type != "tool_use":
                continue
            cmd = b.input.get("command", "")
            out, rc = run_bash(cmd, box)
            print(f"  [turn {turn}] $ {cmd[:110]}")
            transcript["turns"][-1].setdefault("tool_calls", []).append(
                {"command": cmd, "returncode": rc, "output": out[:4000]})
            results.append({"type": "tool_result", "tool_use_id": b.id,
                            "content": out, "is_error": rc != 0})
        messages.append({"role": "user", "content": results})
    else:
        transcript["final_text"] = f"(hit the {MAX_TURNS}-turn ceiling)"

    transcript["elapsed_s"] = round(time.time() - started, 1)
    transcript["produced"] = sorted(
        str(p.relative_to(box)) for p in box.rglob("*") if p.is_file())
    out = HERE / f"transcript-run{args.run}.json"
    out.write_text(json.dumps(transcript, indent=1, default=str), encoding="utf8")
    print(f"\nturns {len(transcript['turns'])}  elapsed {transcript['elapsed_s']}s")
    print(f"transcript -> {out}")
    print("produced:")
    for f in transcript["produced"]:
        print("   ", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
