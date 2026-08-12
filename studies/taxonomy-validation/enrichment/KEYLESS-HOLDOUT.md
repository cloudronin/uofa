# Keyless route: holdout gate

**Declared 2026-08-12, before the route is run on any holdout case.**

The in-sample 0/25 (`KEYLESS-ROUTE.md`) is a development record: the route was
diagnosed and repaired against those cases. This gate is what decides whether it
enters the qualification table or wires into `card_prose`.

## The bar, declared first

Unchanged from A16.4: **false-fire ≤ 10%, false-clear ≤ 5%, per property.**

A route that fails either direction does not ship. A route that cannot be
measured in a direction does not claim that direction.

## What the holdout can and cannot be, measured before drawing

The gold set is the obvious independent ground truth — 150 cards, labeled before
this route existed, never seen by it. It re-attaches from the pinned Liang
parquet at 150/150 by `row_hash`.

**But the gold set has zero P2 positives** (149 absent, 1 unclear). That is the
original 0/150 prevalence finding, and it has a hard consequence here:

| Direction | What it needs | Available now? |
|---|---|---|
| **false-clear** — route invents an uncertainty that is not stated | table-bearing cards labeled P2 `absent` | **yes: 69 gold cards** carry a markdown table in eval scope, all labeled absent |
| **false-fire** — route misses a stated uncertainty | table-borne P2 **positives** the route has not seen | **no** — the gold set contains none |

Measured on those 69: **zero mention any dispersion token** (`±`, `stderr`,
`std err`). So they are a clean negative control — tables with no uncertainty to
find, which is exactly what a false-clear test needs.

## Arm 1 — false-clear, runnable now

**Population:** the 69 gold cards with a markdown table under an evaluation
heading, labeled P2 `absent`. Never seen by the route; labeled before it existed.

**Pass condition:** ≤5% false-clear, i.e. **at most 3 of 69** may produce a value.

**What a failure would mean:** the columnar route matches a header like `SE` or
`Error` that means something else in context — a genuine risk, since `SE` is also
"standard error of the *estimate*" in some tables and an abbreviation elsewhere.
This arm is the one that catches over-eager column matching.

## Arm 2 — false-fire, BLOCKED on labeling

**Population needed:** table-borne P2 positives outside the enrichment stratum,
spanning the format variety the route has never been tested on:

- `stefan-it` five-run tables (in-sample; need unseen siblings)
- HTML `<table>` markup rather than pipe-delimited markdown
- `model-index`-rendered result tables
- lm-eval-harness variants beyond the repaired header shape

**Blocked because these require labels**, and self-labeling a holdout for a route
I wrote is the circularity this gate exists to prevent. The draw goes to the
author queue in the seven-flip format like every other adjudication.

**Consequence, stated plainly:** until Arm 2 runs, the route may be reported as
*"false-clear qualified, false-fire unqualified for want of an unseen positive
set"*. It may **not** enter the qualification table as passing, and it may not
wire into `card_prose` — a route qualified in one direction only is exactly the
half-measured instrument this study keeps catching in other things.

## What this gate does NOT test

**Corpus-scale null-model comparison.** `keyless_extractor.py`'s contract is that
every confidence is what a route scored against reading nothing. On a stratum
selected for a property, a null model scores 100% false-fire by construction, so
the comparison is trivially won and means nothing. A shipped route needs the
corpus-scale version before it carries a confidence number.

## Order

1. Arm 1 now — it needs no new labels and can fail today.
2. Arm 2 draw prepared and sent to the author queue.
3. Neither the qualification row nor the `card_prose` wiring happens until both
   arms have run.


---

# RESULT — Arm 1 as drawn is VACUOUS. The gate moves to modelbiome.

**Run 2026-08-12, immediately after declaring the bar.**

## Arm 1 passed, and the pass means nothing

Route produced a value on **0 of 69** unseen table-bearing gold cards, against a
pass condition of ≤3. By the declared bar that is a PASS.

**It does not count.** Checking whether the test could have failed:

- **0 of the 69** contain a table header the columnar branch would match.
- So the **columnar branch — the exact branch repaired in-sample — never
  executed.** The 0/69 exercised only the inline branch, and only its negative
  case: "a table with no `±` in it yields no `±`."

That is close to a tautology, and this repository's own §13 rule says a check
that cannot fail is not a check. The PASS is withdrawn as evidence.

## The population is empty in Liang, not merely small

Searched the whole pinned corpus:

| | count |
|---|---:|
| Liang eval-bearing cards with a markdown table | **11,540** |
| …containing a header the columnar branch matches | **0** |

Zero out of eleven and a half thousand. The `Stderr`-header table is an
lm-eval-harness output convention that **postdates the 2023-10 snapshot**. Liang
cannot test this route in either direction, because the format the route targets
did not exist when Liang was collected.

This is a recency finding with teeth: **the gold set is not a usable holdout for
any route targeting a post-2023 card convention.** That applies beyond this
route, and it is worth carrying into the study — the A16 corpus validates
instruments against 2023 publishing practice, and card formats have moved.

## Consequence for the gate

Both arms move to a fresh **modelbiome** draw, excluding every card the route has
seen. Populations being drawn:

- **positives** — unseen cards whose eval tables carry a dispersion, split by
  `inline` (`±` in a cell), `columnar` (a `Stderr`-style header), and `both`, so
  the repaired branch is tested on formats it was not repaired against.
- **near-negatives** — unseen cards whose eval sections use `std`/`error`/`se`
  language **without** stating a dispersion. This is the population Arm 1 needed
  and Liang could not supply: tables that give the columnar branch something to
  match wrongly.

**Both need labels**, and self-labeling a holdout for a route I wrote is the
circularity this gate exists to prevent. The draw goes to the author queue in the
seven-flip format.

**Status: the route remains unqualified in both directions.** It may not enter
the qualification table and may not wire into `card_prose`. The in-sample 0/25
stands as a development record and nothing more.


---

# GATE RESULT — passes both directions, on a route frozen first

**Run 2026-08-12** against 60 author-labeled unseen cards (27 present, 33 absent,
0 unclear). The route was **committed unchanged before scoring** (`2b3189d3`,
`keyless_route.py`) and verified to reproduce its in-sample 0/25 first, so the
gate scored a fixed artifact.

| Direction | Result | Bar | |
|---|---:|---|---|
| false-fire | **2/27 (7.4%)** | ≤10% | PASS |
| false-clear | **1/33 (3.0%)** | ≤5% | PASS |

Overall agreement 57/60 (95.0%).

## How this must be stated

**"Route agreement with machine-drafted labels on unseen cards"** — not route
accuracy. The holdout arbiter is machine-drafted like every other label in the
corrected regime. For P2's lexical character that is a distinction without much
daylight, but it is the honest phrasing and the study uses it.

And per the sizing declared before the draw: 27 positives resolves to ~3.7%, so
**7.4% is "did not fail", not "passed at 7.4%"**. The interval is wide. The gate's
job was to catch a route that does not work, and it did not catch one.

## The designed traps, and what they caught

| Trap | Rows | Result |
|---|---|---|
| **empty `Stderr` header**, all cells blank (perplexity-only runs) | 11, 20, 53, 59 | **4/4 correct.** The route requires a *number* in the column, so a bare header yields nothing. A route matching on the header alone would have false-cleared all four. |
| **`_` separator variant**, `±` mangled in the pipeline | 15, 48 | **2/2 correct** — and via the *columnar* branch, which never needed the glyph. The two branches covered each other. |
| **metric-name traps** (`SE`, WER, AER, `Variation`) | 2, 6, 8, 18, 19, 24, 25, 45 | **7/8.** WER/AER/`Variation` all correctly declined. `SE` was the casualty. |

## The three disagreements, diagnosed and NOT fixed

**Two false-fires, one cause.** Rows 29 and 41 (`sgoodfriend` RL cards) carry
`reward_std` / `reward_mean` columns. `HEADER` is anchored (`^std$`), so a
**compound header** like `reward_std` does not match. Row 29 is also the author's
recorded judgment call — a `reward_std` of literally `0`, labeled present on the
grounds that a stated zero dispersion is still a stated dispersion.

**One false-clear, and it is the designed trap working.** Row 2
(`HaronW/EmbodiedAgent`) has metric columns `UE | PoE | PlE | SE | EE`. The route
read `SE` as standard error and returned `93.75`.

**`SE` is genuinely ambiguous from the header alone**, and the docstring's stated
defence — anchoring, so `SE` inside `SEQ_LEN` does not match — is exactly
insufficient here, because this `SE` *does* stand alone. A value of 93.75 is a
strong signal it is not a standard error (dispersions are small relative to their
metric), but that is a heuristic, not a field read, and adding it would make the
route something other than the deterministic reader D2 licenses.

**Neither is repaired.** Repairing a route against the cases that caught it is
the in-sample loop this gate exists to break. Any change is a **new route needing
a new gate**, and these two limitations are now published properties of this one:

- compound dispersion headers (`reward_std`) are not read
- a standalone `SE` metric column is misread as standard error

## Status

The route **enters the qualification table** as the first `code`-pinned row, and
is cleared to wire into `card_prose` for **table-borne P2 only**. It remains
silent on prose and on P6/P7 by construction.

The P5 table extension is authorized behind this same gate and has not been
built.
