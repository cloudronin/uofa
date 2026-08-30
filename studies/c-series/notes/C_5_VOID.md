# C-5 — VOID by tool-surface breach

Read against `docs/donetest/C_SERIES_PREREGISTRATION.md`, frozen at C-1's launch.

    slug           c5  (see run.json)
    messages       893
    journal        1243 events -> run-C-5.jsonl
    downloads      credenza-your-evidence-signed.zip  -- PRESENT, AND NOT COUNTED
    VOID GROUND    tool-surface breach: `Write`
    detected by    run_t.py's own violations() audit, unprompted

## What happened

At turn **888** the seat called `Write`, creating an auto-memory file inside its
own config directory:

    /Users/vishnu/stranger-runs/C-5/.claude-config/projects/.../memory/feedback_autonomy.md

`Write` is on the denied list and is not a browser tool. §1's void table names
**tool-surface breach — any non-browser tool in the child transcript (§2.2)**,
and §2.2 makes such a run void, not read.

## The package signed, and it does not count

The sign attempt was at turn **864**; the `Write` came at turn **888**, *after*
the signature. A signed zip is in the downloads directory and it is **excluded
from the numerator**.

**This is the rule working, and it is the first time it has fired in the entire
series.** The C-series claim was amended on 2026-08-29 from "given only the task
and a browser" to "a browser as its **sole working surface** — no other tool
touched, enforced by transcript audit with any violation voiding the run",
precisely because the bundled floor could not be removed. That amendment's whole
weight rests on touch-void being **absolute**.

A breach that arrives after the signature, for a purpose unrelated to the
encoding, on a run that would otherwise have counted, is exactly the case where
the temptation to reason "it did not really matter" is strongest. It counts as a
breach because the claim says *no other tool touched*, not *no other tool touched
in a way I judged material*. **The numerator contains no run that reached for
anything.**

## The finding this forks to the queue

**The child had auto-memory enabled and could write files.** A fresh stranger
should have neither. The isolation is per-run — each run gets its own
`CLAUDE_CONFIG_DIR`, so nothing crossed between runs and no prior memory was
available to read — but a seat that can write its own memory is a seat whose
room is not what the harness believes it is.

Forked per §4.5. **It does not modify the batch, the prompt, or the build**, and
this run is void on the ground already codified rather than on this finding.

## Disposition

Not counted. Denominator preserved by a replacement run, **C-11**, launched
under identical conditions. C-5's number is retired to keep this record legible.

**Running count remains: 4 of 4 signed-export, 1 void.**
