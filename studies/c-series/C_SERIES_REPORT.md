# C-series — the batch report

Read against `docs/donetest/C_SERIES_PREREGISTRATION.md`, frozen at C-1's
launch. **No analysis beyond the pre-registered claims.**

---

## The rate

> **In 10 of 10 pre-registered trials**, an unsteered frontier-model reviewer,
> given the task statement and **a browser as its sole working surface — eleven
> browser tools, no other tool touched, enforced by transcript audit with any
> violation voiding the run** — completed the encoding protocol through
> signature: producing a package that verifies under the published `uofa` wheel
> (measurement hash, measurement signature, decision signature under
> independent keys).

Ten counted runs, ten `signed-export` endings. One run voided on a codified
instrument-failure ground and was replaced; the void is ledgered below.

Every ending was read from the run's **downloads directory**. Every package was
verified **from a fresh environment**, using only the anchors the zip itself
ships.

## Composition across the ten counted runs

| run | ending | judged | not-recoverable | source-absent | cells | ambiguity | messages |
|---|---|---|---|---|---|---|---|
| C-1 | signed-export | 0 | 17 | 2 | 56 | 4 | 1033 |
| C-2 | signed-export | 0 | 10 | 9 | 34 | 4 | 799 |
| C-3 | signed-export | 0 | 18 | 1 | 58 | 5 | 936 |
| C-4 | signed-export | **6** | 10 | 3 | 54 | 4 | 899 |
| C-6 | signed-export | 0 | 17 | 2 | 56 | 4 | 785 |
| C-7 | signed-export | 0 | 18 | 0 | 58 | 4 | 1345 |
| C-8 | signed-export | 0 | 19 | 0 | 58 | 3 | 809 |
| C-9 | signed-export | 0 | 15 | 4 | 51 | 3 | 805 |
| C-10 | signed-export | 0 | 18 | 1 | 58 | 2 | 958 |
| C-11 | signed-export | 0 | 17 | 2 | 56 | 3 | 783 |

**What the signatures attest.** Completion of the governed review **with
dispositions recorded where evidence was unrecoverable**. They are *not*
assertions that achieved levels meet requirements. Nine of ten packages
explicitly declined to claim judgment, their covers reading *"No required level
was judged … this package does not claim otherwise."* C-4 is the exception and
judged 6 over a denominator that correctly shrank by excluding the 13 it could
not reach.

**Every cover was clean on both once-false sentences**: `"still unsigned"` 0
occurrences and the judgment overclaim 0 occurrences, in all ten.

## Pins — every counted run was a trial of the frozen condition

All ten read `same` on all four condition pins, from **their own signed
packages' `RUN_LOG.md`**, plus `Source sha256` computed from each run's own
source bytes:

    Prompt hash      35033e4b585b7065dea9d11044632b4a49841adbb870726540d18b3e0368f57d
    Source sha256    1b767b2d4128dcc67bdb6803fe33034e6551cf29d605e5675ef6e17819fde3c1
    Backend          hosted
    Extractor model  openai-compatible/anthropic/claude-sonnet-5 via openrouter.ai

`dev/stranger/c_pins.py --run N`, exit 0, ten times.

## Void ledger

| run | ground | detail |
|---|---|---|
| C-5 | tool-surface breach | `Write` at turn 888 — an auto-memory file in the child's own config dir. Signed at turn 864; **the signature is excluded from the numerator.** |

**One void, and it is the rule working.** The claim was amended before C-1 from
"given only the task and a browser" to "a browser as its sole working surface —
no other tool touched", because the CLI's bundled floor proved irremovable. That
amendment's whole weight rests on touch-void being absolute. Its first real test
was the hardest case: a breach that arrived *after* the signature, for a purpose
unrelated to the encoding, on a run that would otherwise have counted. It voided
anyway, detected by `run_t.py`'s own audit without prompting.

**The numerator contains no run that reached for anything.**

## Verification transcripts

Each counted run, `uofa==0.16.0` in a clean venv, anchors from inside the zip:

    ✓ Measurement hash match
    ✓ Measurement signature valid
    ✓ decision 1: reviewer signature valid
      issuer and decision scopes signed by different keys — independent attestation

    10 packages · 3 checks each · 30 passed, 0 failed

Per-run records: `dev/donetest/c-series/C_*_NOTE.md`, and `C_5_VOID.md`.

## Out of scope, as pre-registered

- **Soundness of the extraction.** The REQ-invention finding stands as a known
  instrument limitation: predeclared levels in this source are legible only as
  cell shading, so a text-fed extractor sees a gap and fills it.
- **Assessment quality of the source paper.** Not evaluated.
- **Human-reviewer executability.** Carried by the earlier stranger evidence,
  not by this series. This is a model-reviewer claim.

## The known defect, as disclosed before the batch

The build carried the twice-reported unwritable-labels defect throughout:
`Pack version` and `Standard` render `awaiting the pack` permanently, nothing in
`credenza/` assigns them, and A-3 passes regardless. Disclosed in §3 before C-1,
non-blocking, and its fix deliberately queued behind the batch so the build could
not move mid-count. **It moved nothing:** all ten runs signed past it, as T-8 and
T-9 had.

## What unfreezes now

The v0.2 adoption event and the unwritable-labels deploy.
