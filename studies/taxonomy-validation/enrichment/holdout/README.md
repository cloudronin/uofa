# Keyless holdout labeling set — 60 rows

**For author labeling.** One column to fill: `P2_uncertainty` ∈
{`present`, `absent`, `unclear`}, per the unchanged A16.3 sheet.

The question is only: **do the evaluation sections state an uncertainty for a
reported score?** (`±`, stderr, CI, variance across runs/seeds, or an explicit
statistical qualifier attached to a result.)

## Why this set exists

The keyless table route was developed and repaired against the enrichment cases,
so its 0/25 is in-sample. `KEYLESS-HOLDOUT.md` declared the gate; the gold set
turned out to be unusable for it — **0 of 11,540 Liang table-bearing cards carry
the header format the route targets**, because that format postdates the 2023
snapshot. So the holdout is drawn from modelbiome instead.

## The draw

Seed `20260812`, recorded in `manifest.json`. Drawn from **42,914 unseen
table-bearing cards** — every card in the enrichment case set is excluded, so the
route has seen none of these.

| Stratum | n | What it tests |
|---|---:|---|
| `positive-columnar` | 15 | the branch that was **repaired in-sample**, on formats it was not repaired against |
| `positive-inline` | 15 | the `±`-in-a-cell branch |
| `near-negative` | 30 | tables using `std`/`error`/`se` language **without** stating a dispersion — the population that gives the columnar branch something to match *wrongly*, and the one Liang could not supply |

Rows are shuffled, so the stratum is not inferable from position. `arm` and
`route_branch` are recorded for analysis; **ignore them while labeling** — they
say what the pipeline thought, and that is the thing under test.

## Sizing, and its honest limit

60 rows resolves to ~3% per stratum, which is enough to fail the ≤10% false-fire
and ≤5% false-clear bars decisively but **not enough to certify a rate near
them**. A route landing at 7% false-fire on 30 positives has a wide interval and
should be reported as "did not fail" rather than "passed at 7%".

That is a deliberate trade: the gate's job is to catch a route that does not
work, not to publish a precise number for one that does.

## What happens after

Labels feed both holdout arms at once. The route may enter the qualification
table or wire into `card_prose` **only** if both arms clear. Until then it is
unqualified in both directions and the in-sample 0/25 is a development record.
