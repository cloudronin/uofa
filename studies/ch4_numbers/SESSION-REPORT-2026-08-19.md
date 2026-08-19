# Ch4 Numbers and Repairs — session report, 2026-08-19

Item 5 of the E2/E3 close-out. Covers the spec's eleven work items, the four
dispositions, and the E2/E3 close-out items 1–4. Item 6 is recorded as a ruling
only; no work started.

---

## What landed

**All eleven spec items.** W1 Stage 4 report · W2 discharged by review · W3 the
R1a guard removal · W4 the pinned pre-fix contrast · W5 Wilson intervals · W6 the
ledger · W7 verified already complete · W8 status-table strikes · W9 escalated as
a triage list · W10 Tier-1 support · W11 addendum draft.

**Four dispositions.** R4 added as a ruling and Addendum F · E1 traced and
resolved · Wilson resolved at the aggregate · W3 landed with docstring extension
rather than rewrite.

**E2/E3 close-out items 1–4**, below.

## Corrections the session made to its own inputs

Nine, all logged where they apply. The spec's §2 rule — verify before writing —
produced every one of them.

| | Correction |
|---|---|
| C1 | R1a's "all three rule sites" is **one** guard clause plus two comments |
| C2 | W7 was already complete; 0.25–3h collapsed to a verify |
| C3 | W2 resolved to its unchanged branch; rate identical under both dedup policies |
| C4 | W5's expected n-distribution is 14/2/1, not 5/2 |
| C5 | W-ON-02 is 65/71 **or** 69/71 depending on catalog version |
| — | "11 of 16" OOS rules corrected to **10 of 16** (INV-22) |
| — | E1 escalated wrongly; the trace found `extract_eval_v1.md` and the spec's pair was right |
| — | Morrison COU1 has **three** counts in circulation, not one |
| — | The aero wiring origin is `1caced19`, not `992955ac` — which predates the aero work |

## Items 1–4 of the close-out

**Item 1 — repointed.** Both aero tests read annotation snapshots inferring **0
triples**, so the positive test asserted stored data and the negative test
asserted the absence of something nothing could produce. Now read
`tests/fixtures/extract/aero-cou{1,2}-imported.jsonld` at **172 / 125** inferred
triples. A guard asserting `"Inferred 0 new triples"` is absent prevents silent
regression. Origin corrected: the tests were written in `1caced19` the same day
`61c914c3` shipped the fixtures, and pointed at the snapshots from the start.

**Item 2 — audited**, `NASA-FIXTURE-AUDIT-2026-08-19.md`. Both are live
substrates. **Two escalation criteria fired**, both reported and neither fixed:
signatures present that do **not verify**, against a generator that writes
all-zero placeholders; and COU2 failing SHACL on `"Not Accepted"` vs
`"Not accepted"`, one character.

**Item 3 — three ledger rows.** Arm M's three substrates named and pinned, so the
35/35 aggregate stands. The NASA artifact inventory in three classes. E2 marked
**PENDING-ENCODING**, and §4.1's lead sentence held until n settles.

**Item 4 — E3 closed on option B.** Headline 3/33 = 0.0909; 5.5× labelled the
all-six sensitivity lift; disclosure sentence entered with its three grounds. No
fresh run.

## Mutator verification, entered as fact

Arm M mutated **three** substrates — `morrison/cou1`, `morrison/cou2`,
`nagaraja/cou1` — pinned identically in `run_arm_m.py:39` and `results.json`. No
NASA file among them. The 35/35 aggregate and every per-pattern figure stand
without re-examination.

**This session's finding independently reproduces a disclosed caveat.** The Phase
2.5a REPORT already carried "Three substrates, not five" with the same diagnosis:
annotation nodes, no `UnitOfAssurance`, strip-and-rerun yields zero. Arriving at
it from the H1 side, without having read that caveat, is corroboration rather
than discovery — and it is the reason the finding could be entered as fact
immediately instead of costing a re-run.

Two further REPORT caveats are **closed by this session**: Wilson intervals
computed per row, and the W-EP-01 contrast variant built.

## The confirm-only instrument tally is now three

Three guards that can confirm but cannot falsify, found independently, all in one
session. They share one Ch5 sentence.

1. **`check-pages.mjs` string assertion** — verifies the published page contains
   "11 weakeners across 5 patterns". It checks the page says what it says, so it
   cannot detect the number going stale against the catalog.
2. **The OOS calibration set** (INV-22) — 16 packages, all `out_of_scope`, none
   expected to clear. A rule that can only report a gap scores perfectly, and 10
   of 16 were exactly that.
3. **The snapshot-reading test** (item 1) — asserted a pattern name against a
   file containing it as data, with 0 triples inferred. Green either way.

The shape is identical each time: **a test whose passing condition is satisfied
by the artifact rather than by the behaviour the artifact is supposed to
exercise.** Each was found by asking what the instrument would do if the thing it
measures were broken — the same question the argument-layer prototype's repaired
control asks, and the reason that control was built.

## Item 6 — recorded, not started

**NASA gets encoded properly**, sequenced behind A7. The protocol is written
first; the NASA encoding is then the first encoding governed by it — extract →
review → import → sign, both COUs, author review pass. That closes E2 at five
rows and makes §4.1's "encoded under the published protocol" true at n = 5.

Precondition is a document that does not exist yet and is author work. **Not
started.** When it runs, the hand-crafted fixtures stay untouched as the C3
isolation artifacts they are.

## Final ledger sweep

| Status | Rows |
|---|---:|
| entered | **95** |
| PENDING-ENCODING | **3** |
| **ESCALATION** | **0** |
| total | **98** |

The three PENDING-ENCODING rows are the two NASA substrates in §4.1's H1 table
and the single H1 row in §4.6's gate summary. They share **one** dependency: the
R5 protocol encoding, sequenced behind A7.

E1 resolved · E2 pending-encoding · E3 closed on option B · E4 closed (§4.4
entered from the pinned D6 re-derivation) · E5 pending-encoding. **No escalation
remains.**

The two NASA H1 rows are left **blank rather than filled from the snapshots**.
Those files' SHACL and integrity passes are vacuous — `targetClass
uofa:UnitOfAssurance` matches nothing — so entering their green marks would be
entering a green that means nothing. That is the same confirm-only shape tallied
above, and declining to enter it is the tally's first practical use.

## What remains open

- **E2** — PENDING-ENCODING (item 6).
- **§4.1 lead sentence** — waits on n.
- **E5** — the H1 rows of the gate summary, same dependency.
- **W9** — 64 bare `v0.6`/`v0.7` occurrences across 20 files, triaged into three
  groups, awaiting review. Most of the volume is the vocabulary line, where
  rewriting to "catalog v0.6" would be wrong.
- **W11** — addendum draft for sign-off; the Decision Record itself untouched.
- **Fixture provenance** — non-verifying signatures, for A4.
- **Two review-list items** — `README.md:167` and `docs/design.md:9` state 11
  without a version label. The next tag after R1a merges is when that bites.
