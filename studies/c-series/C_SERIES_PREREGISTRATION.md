# C-series — pre-registration

**Filed and committed before C-1 launches.** Nothing in this document is edited
during the batch window. Where it is wrong, it is wrong on the record.

Authorized 2026-08-28: ten runs, ~$20 total metered extraction, expressly
approved as the named exception to the $5 standing cap. If any single run's
meter runs anomalously past the T-8/T-9 evidence (~$2/run), the batch stops and
reports rather than spending through it.

The T-series exit condition was met by T-8 and T-9: two consecutive unsteered
runs on pv1 ending at a signature that verifies. This series counts.

## Change note — 2026-08-29, before C-1

**Amended once, before any run, with the reasoning on the record rather than
silently.**

C-1's first launch attempt was **refused by the harness**, not by a person:
`run_t.py`'s tiered room gate (author's ruling, 2026-08-26) holds that a C-run
requires a provably bare room, because the claim as first drafted said "given
**only** the task and a browser" and a citation resting on capabilities that
were offered and merely not reached for is the fence-that-happens-to-hold
wearing the flagship sentence. **No spend occurred; the gate fires before the
seat is created.**

The gate's refusal cites a measurement from 2026-08-26, and measurements go
stale, so it was re-run first: every candidate mechanism reports counts
identical to baseline (§2). The floor is genuinely irremovable on this build.

**So the claim re-scopes rather than the gate relaxing.** §5's primary sentence
now says what the instrument can actually prove, §2 states the room as it is,
and `run_t.py`'s tier table gains the second road explicitly — a C-run requires
*either* a provably bare room *or* the amended claim language plus a clean
touch audit. Nothing about touch-void weakens.

**Second amendment, same sitting, before any run: §2's build pin was
defective.** It froze the build *stamp* (`0.1.0+<HEAD>`), which moves on every
commit including docs, rather than the *application*. The stamp was already
stale when C-1 was first attempted, and pinning it would have made §6's per-run
notes violate §2 ten times over while the application never moved. Re-pinned to
`carries 716d92d9` — the last commit touching `credenza/` — which is the
question `deploy_check.py` already asks. Verified before re-pinning: `git diff
7ca51e9..HEAD -- credenza/ deploy/ pyproject.toml` is **empty**, so the
application is byte-identical to the one T-8 and T-9 ran against.

Recorded as a second amendment rather than folded into the first, because a
pre-registration that quietly revises its own freeze set is worth less than one
that shows where it was wrong. **Both amendments precede C-1. The document
freezes at launch.**

---

## 1. The denominator, declared blind

**Ten runs, C-1 through C-10.** All ten launch regardless of interim results.
The rate is published wherever it lands.

- **No run is re-rolled.** A run that ends badly is a run that ended badly.
- **No ending is re-read.** The readings in §4 are fixed here and are the only
  ones applied.
- **No stopping early on a streak, in either direction.** Ten signatures and
  zero signatures are both reported at ten.

**Void grounds, and they are exhaustive.** A run is void — not counted, with the
denominator preserved by running a replacement — only on instrument-failure
grounds already codified before this series:

| ground | how it is detected |
|---|---|
| seat gate mismatch | `run_t.py`'s lineage check: recorded ≠ reported |
| room violation | bundled skills / subagent types differ from approved |
| tool-surface breach | any non-browser tool in the child transcript (§2.2) |
| deploy drift | `deploy_check.py` disagrees on either signal |
| pins not comparable | §2's condition pins UNANSWERABLE or DIFFERENT |

**A run is never void on its ending.** Every void is recorded with its cause in
the batch report's void ledger.

## 2. The freeze set, pinned by value

| pin | frozen value |
|---|---|
| prompt | **pv1**, unchanged since T-1 |
| prompt hash | `35033e4b585b7065dea9d11044632b4a49841adbb870726540d18b3e0368f57d` |
| **application** | `716d92d9` — the last commit touching `credenza/`, which is what a build *carries* |
| wheel | `uofa==0.16.0` |
| source | `NTRS-20200002832-Johnson-2020.pdf` |
| source sha256 | `1b767b2d4128dcc67bdb6803fe33034e6551cf29d605e5675ef6e17819fde3c1` |
| backend | `hosted` |
| extractor | `openai-compatible/anthropic/claude-sonnet-5 via openrouter.ai` |

**The application cannot move mid-count, and that is the thing pinned.** No
wheel releases during the window, and no commit touching `credenza/`, `deploy/`
or `pyproject.toml`.

**Why the pin is `carries`, not the build stamp.** The stamp is `0.1.0+<HEAD>`
and moves on *every* commit — including a docs commit that changes no
application byte. This document originally froze `0.1.0+7ca51e93`, which was
already stale before C-1's first launch attempt, while the application had not
moved at all. Pinning it would report a violation every time a run note is
committed and stay silent about nothing real. `deploy_check.py` already asks the
right question — *is the expected commit an ancestor of the deployed one* — and
its `carries` value is what §6's per-run check records.

**This resolves a conflict between §2 and §6 that the first draft could not
satisfy.** The deploy workflow triggers on `dev/**` and `tests/**` by design (a
comment in it records that a tests-only commit once ran no CI, so the filter was
widened deliberately), and per-run notes live in `dev/donetest/`. Under a
build-stamp pin, **writing the record the batch requires would violate the
freeze the batch requires** — ten times. Under an application pin, a note
commit redeploys an identical application and the freeze is intact, which is
both true and checkable.

**The room, stated as it is.** The CLI binary bundles **7 skills**
(`update-config`, `debug`, `simplify`, `batch`, `loop`, `schedule`,
`claude-api`) and **4 built-in subagent types** (`general-purpose`,
`statusline-setup`, `Explore`, `Plan`) that **cannot be removed on this build**.
Re-measured 2026-08-29 against children's own init events — `--tools ""`,
`--agents {}`, `--disable-slash-commands`, `--setting-sources ""` and `--bare`
all report counts identical to baseline (`dev/stranger/probe_room.py` is that
measurement's record). **No counted run invoked any**, and the transcript audit
that proves it is part of each run's record; a run that touches one is void.

**The comparability guard's three-state law governs.** Every run's pins are read
from **its own signed package's `RUN_LOG.md`** — the artifact a third party
gets, not the app's state and not this harness's memory of what it launched —
plus `Source sha256` computed from the bytes in the run's own `source/`, which
no run log carries. `dev/stranger/c_pins.py` performs this and is the void
mechanism; it was validated before C-1 against T-9 (all four SAME) and T-8
(`Prompt hash` UNANSWERABLE → void), so it is known to fire in both directions.

**One distinction this series must draw, drawn here rather than mid-batch.**

- `Prompt hash`, `Source sha256` and `Backend` are **condition pins**. Disagreement
  or unanswerability means *this was not the experiment* — the run was a trial of
  some other condition. **Void.**
- `Extractor model` is **reported, and does not void.** A sentinel there means the
  extraction *failed*, which is the frozen condition producing a failure, not a
  different condition being tried. Voiding it would let the rate quietly exclude
  the product's own bad days, which is the opposite of publishing whatever
  results. **It counts, and the failure is named in the run's note.**

This is an interpretive call on the authorizing order's phrase "must read same,
not unanswerable". It is stated before run one so it cannot be adjusted after
seeing the rate.

## 3. Known-defect disclosure, stated rather than discovered

**The build carries the unwritable-labels defect.** `Pack version` and `Standard`
render `awaiting the pack` permanently: nothing in `credenza/` assigns either
field, so no act by any reviewer can fill them, and A-3 passes regardless.

It was reported independently by **two seats** — T-8 and T-9 — both of which
**signed past it**. It is non-blocking. It is filed in `AGENTS.md` with a
mechanical guard (`tests/test_a3_pins_version_like_the_shapes.py` asserts these
two fields have no writer, and will fail the day either gains one, demanding
their promotion to `RunLog.PINS`).

**Its fix is deliberately queued behind this batch so the build cannot move
mid-count.** The C-series therefore ships on a build with a known, twice-reported
defect, by choice, and that choice is recorded here rather than surfaced in
review. Both pins are ADVISORY in the comparability guard, so the defect does
not make any two runs incomparable.

## 4. The endings taxonomy, fixed in advance

| ending | what the downloads directory holds |
|---|---|
| **`signed-export`** | a signed zip that **verifies under the published wheel** — measurement hash, measurement signature, and decision signature under independent keys. **This is the numerator.** |
| **`download`** | the unsigned export alone |
| **`none`** | nothing exported |
| **`unresolvable`** | act-observability failure: the sign act fired and the instrument could not capture it |

`unresolvable` should be extinct under the deploy-4 rail — T-6's blindness is
fixed and six scripted walks plus two T-runs have captured the file since. It is
declared anyway **so it cannot be invented later** to reclassify an ending that
disappoints.

**The downloads directory is the oracle.** Not the transcript, not the seat's
account of what it did, not a server-side check that the package *would* sign.
**Wheel verification is run per package from a fresh environment** and its
transcript is recorded in that run's note; a signed zip that does not verify is
`download`, not `signed-export`.

## 5. The claim

**Primary — the rate.**

> In N of 10 pre-registered trials, an unsteered frontier-model reviewer, given
> the task statement and **a browser as its sole working surface — eleven
> browser tools, no other tool touched, enforced by transcript audit with any
> violation voiding the run** — completed the encoding protocol through
> signature: producing a package that verifies under the published `uofa` wheel
> (measurement hash, measurement signature, decision signature under
> independent keys).

**Why this sentence and not "given only the task and a browser".** The bundled
floor in §2 is irremovable, so the stronger sentence would be false in the way
that matters most: the capabilities were present and merely unused. This trades
*"only a browser was **present**"* for *"only a browser was **used**, provably"*,
which is the truthful version — no instrument can remove the model's training
either, and what a citation can honestly rest on is what the record proves was
touched. Touch-void keeps its full strictness: **the numerator contains no run
that reached for anything.**

**Composition — what the signatures attest.** The signed packages assert
completion of the governed review **with dispositions recorded where evidence
was unrecoverable**. They are *not* assertions that achieved levels meet
requirements. Expected texture, from T-8 and T-9: `Conditional` decisions;
`not-recoverable` and `source-absent` dispositions; REQ values extractor-inferred
and disowned in prose.

**Out of scope, stated.**

- **Soundness of the extraction.** The REQ-invention finding is a known
  instrument limitation: predeclared levels in this source are legible only as
  cell shading, so a text-fed extractor sees a gap and fills it. T-9 found this
  from the seat.
- **Assessment quality of the source paper.** Not evaluated.
- **Human-reviewer executability.** Carried by the earlier stranger evidence, not
  by this series. This is a model-reviewer claim.

## 6. Per-run record discipline

Each C-run gets its own note against this document, carrying: the ending; the
pins comparison (`c_pins.py` output verbatim); the verification transcript from a
fresh environment; message count; a dispositions summary; and anything the seat
reports.

**No interpretation beyond the fixed readings.** Findings the seats surface fork
to the queue per §4.5 and **never** modify the batch, the prompt, or the build
mid-count.

---

## Batch mechanics

**Sequential.** The Space is stateful and in-memory: one live run at a time,
fresh slug each. The ephemerality rule is observed — any artifact that matters is
exported at creation.

**Standing gates apply to every launch:** deploy-freshness, seat, room,
isolation, prompt-against-pass-line.

**Between runs: nothing changes.**

**If a product defect blocks a run in a new way**, that run records its ending
honestly (likely `download`, with the blocker named), **counts against the
denominator**, and the defect queues. The rate absorbs reality; that is what
publishing-whatever-results means.

## After C-10

One document: the rate, the composition table across all ten, the void ledger if
any, and the verification transcripts. The v0.2 adoption event and the
unwritable-labels deploy unfreeze behind it.

**No analysis beyond the pre-registered claims without a separate order.**

## Standing laws throughout

Artifact over account. The downloads directory decides endings. Every citation
names its file. Nothing edits pv1, the build, or any shipped record during the
window.
