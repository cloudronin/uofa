# Decision Record addendum — 2026-08-19 (DRAFT, author commits)

W11 of the Ch4 Numbers and Repairs spec. **Not committed.** Drafted for author
sign-off, in the format of `docs/UofA_Decision_Record_2026-08-16.md`.

Append to that record as *Addenda C–E*, or open a dated successor record; the
existing file's Addenda section says both of its addenda were committed in the
same commit as the record above, so a successor may be cleaner than reopening it.

---

## Rulings taken 2026-08-19

| # | Topic | Decision | Consequence |
|---|---|---|---|
| R1a | W-EP-01 claim-type guard | **REMOVE.** `(?claim rdf:type uofa:Claim)` drops; W-EP-01 fires on any `bindsClaim` target lacking derivation. No typed-claim requirement introduced | Restores the behaviour the 2026-04-26 corpus was recorded under. Landed as a disclosed post-freeze correction with a CHANGELOG entry |
| R1b | Stage 4 adjudication basis | **STANDS AS RULED**, against recorded generation-time `rules_fired`, including rows #3 and #65 | Stage 4 report carries one disclosure: 63 of 65 comparable packages diverged under the current catalog, traced to `205cc90e` |
| R1c | P25-A ordering | **NUMBERS STAND** as measured at v0.5.15.1. R1a lands after, disclosed. No re-run | Chapter states catalog versions explicitly wherever a number is cited |
| R2 | Tier-1 restatement | **READING B.** Six candidates restated as "6 of 6 confirmed as real weaknesses, located at the schema boundary rather than inside catalog scope." Finding relocates RQ3 → RQ1 | Author writes the reclassification paragraph; support dug at `studies/phase3_stage4/TIER1_SUPPORT.md` |
| R3 | INV-22 OOS calibration | **OUT OF SCOPE**, deferred post-defense. One line in Ch5 future work | No work item |
| R4 | ERM override stratum | **ENSEMBLE-RELIABILITY FINDING**, reported as measured in §4.3.6. Not a catalog finding | The gate FAIL decomposes into two findings with different subjects; see Addendum F |
| R5 | NASA H1 substrates | **ENCODE PROPERLY**, sequenced behind A7. The protocol is written first; the NASA encoding is then the first encoding governed by it — extract → review → import → sign, both COUs, author review pass | Closes E2 at five rows; §4.1 leads with "encoded under the published protocol" true at n=5. Hand-crafted fixtures stay untouched as C3 isolation artifacts |
| — | Chapter placement | Stage 4 numbers get a new **§4.3.6**, "the generation arm, adjudicated"; the REAL-GAP / OUT-OF-SCOPE mass hands forward to §4.5 as the third side of the boundary | Results Chapter Structure otherwise holds |

---

## Addendum C — five corrections to the spec's own premises

The spec's §2 requires every load-bearing claim be verified against the artifact
tree before it is written into an output. Applying that rule to the spec itself
found five errors. Two changed the work; none changed a ruling.

**C1 — R1a says "all three rule sites". There is one.**
`packs/core/rules/uofa_weakener.rules` carries three occurrences of `uofa:Claim`,
but only line 39 is a guard clause. Lines 29 and 31 are comments describing it.
INV-21's "`uofa:Claim` **3**" was a raw occurrence count and the spec read it as
three rule sites. **The ruling's intent is unaffected** — the guard is removed
either way — so the fix proceeded, with the two comment lines *rewritten* to
record the removal rather than deleted.

**C2 — W7 was already complete.** `studies/d6-rederivation/FINDINGS.md`:
*"COMPLETE. D6 drafting is unblocked."* 384/427 re-derives, the equality holds in
**both** directions (Direction 2: "HOLDS, 0 counterexamples"), all three checks
pass against a pinned revision the script refuses to run without. The two
`datasetcard_info` → `modelcard_info` sites are also already fixed. The item's
0.25–3h range collapsed to a verify step.

**C3 — W2 resolved to its "unchanged" branch.** Recomputing all 50 convergent
majorities under first-wins dedup changes **zero** of them. Only one convergent
case has a conflicting retry at all, and it does not flip a 2-of-3 majority. The
override rate is **0.2130 under both policies**. The two-policy inconsistency is
real and should be reconciled — last-wins recommended, since it is what
`align_trios` already does and therefore what every shipped figure was computed
under — but no reported number depends on the choice.

**C4 — W5's expected n-distribution was wrong.** The spec expects "five patterns
at n=3, two at n=1". Measured across 17 patterns and 50 mutants: **14 at n=3, 2
at n=1, and one at n=6** (W-SI-02). See Addendum D for why the n=6 matters and
then does not.

**C5 — the W-ON-02 figure is version-dependent.** "Fires on 65/71 queue packages"
is correct **at the recorded generation-time catalog**. Under the current catalog
it is **69/71**. The ledger row carries both with explicit version labels. This
is the first live instance of exactly the class R1c exists to prevent, found
before the ledger that was built to catch it.

---

## Addendum D — the Wilson intervals, and the level a claim can rest on

Ruling 1 held GATE-H3 as set and ruling 4 accepted W-PROV-01's classification on
re-derivability rather than score. Adding confidence intervals to the Arm M
per-pattern table (W5) makes the precision limit explicit, and it is starker than
anticipated.

**All 13 gate patterns have a Wilson 95% floor below 0.5.** A perfect 3/3 gives
[0.439, 1.000]; a perfect 1/1 gives [0.207, 1.000]. No gate row supports a point
estimate printed without its interval beside it.

**Exactly one pattern clears 0.5 — and it is not in the gate.** W-SI-02 is 6/6 on
raw mutation sites, giving [0.610, 1.000]. But its **conformant n is 0**: it is
one of three patterns (with W-ON-01 and W-SI-01) excluded from the gate because
their mutants are caught by the schema before rules run. Its interval is
therefore **not a rules-detection figure** and must not be quoted as one.

**Resolution — pool the gate, do not claim per pattern.** Aggregated over the
gate denominator the result is **35/35 = 1.0000, Wilson [0.9011, 1.0000]**. That
is the interval a chapter claim rests on. The per-pattern table is shown *with*
its intervals for honesty, not as a set of per-pattern claims, and carries the
qualitative sentence that per-pattern n is too small to support one. W-SI-02's
clean interval takes a footnote saying its conformant n is 0, so it demonstrates
**schema capture, not rule detection**.

Nothing here is ruled — the per-pattern floors near 0.44 at n=3 were the expected
outcome of the mutation budget, and this is a statement about that budget rather
than about the catalog. It is recorded so position 8 does not have to rediscover
which level the claim sits at.

Artifact: `studies/phase2_5a/wilson_intervals.py` and `wilson_intervals.json`.

---

## Addendum E — the Tier-1 restatement completes a deferred claim

R2 is easier to write than it looks, because the original claim already scoped
itself. `dev/build/adversarial/phase3/STAGE3_RESULT.md:56`:

> **Stage 4 has not run.** These are ensemble candidates. The spec makes author
> adjudication the step that confirms a REAL-GAP, so the defensible present claim
> is that **6 of 6 Tier-1 candidates have majority-judge support, not that 6 of 6
> are confirmed real gaps**. Self-blinded adjudication of a sample is what
> converts the one into the other.

Stage 4 has now run and did not convert it: all **12 of 12** REAL-GAP spot-check
cases were ruled OUT-OF-SCOPE. So R2 **completes a deliberately deferred claim
rather than retracting an overreach**, which is both a more accurate paragraph
and a considerably easier one.

Two supporting facts belong in it:

**The ensemble was reading the packages.** Grounding, scoped to the 496 REAL-GAP
verdicts whose probe points at *no* Tier-1 candidate — where the prompt header
offered nothing to echo — shows **0.0% zero-echo**, median 17 package-distinctive
tokens. The override is a disagreement about what counts as a gap, not a failure
of attention.

**The author's policy is written down.** From the sitting's cheat sheet: *"Real
weakness but substantive/prose-level, not structural → OUT-OF-SCOPE… these are
boundary-section material."* Note it differs slightly from the adjudication
instructions' definition (`ADJUDICATION_INSTRUCTIONS.md:66`), and the twelve
rulings follow the cheat sheet. Worth naming, since the two are not identical.

---

## Addendum F — the gate FAIL decomposes into two findings, R4

**Ruling: the ERM result is a finding about the instrument, not the catalog.**

The spot-check override gate fails at **0.213** against ≤0.10, and it fails on
**EXISTING-RULE-MISBEHAVIOR** (7 of 12, contributing **0.149**) more than on
REAL-GAP (12 of 12, contributing 0.064). Set REAL-GAP aside entirely and the gate
still fails at 0.149. The chapter reports that honestly, including the sentence
that **the gate fails on ERM alone**, and then states what the overrides mean.

**The direction of the overrides is the finding.** All seven ran the same way:
the ensemble asserted a rule was misbehaving, and on author review it was not —
4 became GENERATOR-ARTIFACT (the package never instantiated its defeater, so
there was nothing for the rule to miss) and 3 became CORRECT-DETECTION (the rule
behaved). The ensemble **over-attributed misbehaviour to rules**. That is a
statement about the judges' reliability on that stratum, and it is **favourable
to the catalog**, not adverse to it.

So the single failing number carries two findings with different subjects:

| Stratum | Finding | Subject |
|---|---|---|
| REAL-GAP 12/12 | the gaps are real and sit at the **schema boundary**, outside catalog scope (R2) | the schema |
| ERM 7/12 | the ensemble's misbehaviour stratum was **unreliable**, over-attributing to rules | the instrument |

Neither is a finding that the catalog is wrong. The two strata that assert the
catalog works — CORRECT-DETECTION and GENERATOR-ARTIFACT, carrying 68% of the
population — went **23 of 23 with zero overrides**.

Measured in `studies/phase3_stage4/REPORT.md`; per-stratum table in
`stage4_readouts.json`.

---

## Addendum G — three findings from the E2/E3 close-out

### Fixture provenance divergence, routed to A4

The two hand-crafted NASA fixtures are **not what their committed generator
produces**. `tests/fixtures/extract/_build_aero_fixtures.py:224-225` writes
all-zero placeholder `hash` and `signature`; the committed files carry
real-shaped values that **do not verify** — C1 Integrity fails on both. So either
they were signed after generation with material that no longer matches, or edited
after signing.

**Ruled: not repaired, not re-signed, not regenerated.** Their value now is that
they document the gap. One A4 appendix line item, resolution deferred to the R5
encoding which supersedes them as the citable NASA artifacts.

It also **independently confirms R5**. H1's gate requires signatures at 100%, so
unsigned-or-unverifiable fixtures could never have entered it. The encoding was
the right call on grounds established before this was found.

### The wiring-origin correction

The author's guess was that the `992955ac` pack-directory refactor broke the aero
test wiring. **The trace says otherwise.** `992955ac` is 2026-04-04 and predates
the aero work entirely. The tests were written in `1caced19` on 2026-04-18, the
same day `61c914c3` shipped the hand-crafted fixtures "for isolating C3 rule
correctness from LLM/import non-determinism", and were pointed at the annotation
snapshots from the start. **The wire was never right, rather than broken later.**

Recorded because the distinction matters for A4: it is not a regression, so there
is no window during which a working check silently stopped working. It is a
test that never checked what it claimed to.

### The confirm-only instrument tally is three

Three guards that can confirm but cannot falsify, found independently in one
session:

1. **`check-pages.mjs`** asserts the published page contains "11 weakeners across
   5 patterns" — it checks the page says what it says, so it cannot detect the
   number going stale against the catalog.
2. **The OOS calibration set** (INV-22) — 16 packages, all `out_of_scope`, none
   expected to clear. A rule that can only report a gap scores perfectly, and 10
   of 16 were exactly that.
3. **The snapshot-reading test** — asserted a pattern name against a file
   containing it as data, 0 triples inferred. Green either way.

They share one shape, and this formulation is chapter-bound:

> **a test whose passing condition is satisfied by the artifact rather than by
> the behaviour the artifact is supposed to exercise.**

Each was found by asking what the instrument would do if the thing it measures
were broken — the question the argument-layer prototype's repaired control was
built to ask. One Ch5 sentence covers all three.

### A note on how these were found

Two of this session's corrections overrode plausible authored guesses: E1's
escalation (the spec's `0.964 vs 0.960` pair was right; the escalation reflected
not having found `extract_eval_v1.md`) and the `992955ac` attribution above. Both
were resolved by tracing to the artifact rather than reasoning from the record.
That is what the spec's §2 rule buys, and it is the argument for keeping it
binding on the author's own statements as well as on the session's.
