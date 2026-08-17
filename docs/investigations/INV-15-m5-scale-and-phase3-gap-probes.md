# INV-15 — M5 scale validation, gap-probe swamping, and whether Phase 3's Tier-1 result survives it

Status: **CLOSED** — the validation gap is closed; the Phase 3 concern it raised is
answered and does not hold
Date: 2026-08-17
Feeds: A4, the Phase 2.5a report's coverage statement, Ch4's Tier-1 narrative

## 1. The M5 scale gap is closed

The `analyze` fix (`548224d1`) was validated end to end on the v0.5.13 holdout — 39
specs. The Phase 2.5a report named the untested remainder honestly: whether it
scales to M5's 381 specs and 4,601 packages.

Run over M5's `gap_probe` tier, every `out_dir` stale (66/66), so the fix is the
only thing that can produce rows:

| | |
|---|---|
| Specs | **66** — 1.7× the previously tested count |
| Packages | **330** — 8× the previously tested volume |
| Specs skipped for unresolvable manifest | **0** |
| Packages classified | **330** |
| Exit | 0, outcomes/matrix/summary/report all written |

What remains untested is 4,601 packages rather than 330 — a **resource** question
(memory, parallelism, wall-clock), not a logic one. The resolution path itself was
already proven at full M5 scale: 381/381 specs resolve, no `spec_id` collisions.

**The `$386 / 14h` figure in `PHASE2_STATUS_REPORT.md:55` is for *regenerating* the
corpus and is not what a full M5 re-analysis costs.** Packages are
catalog-version-independent, so re-analysis is Jena time at zero LLM spend — the
same insight that made Arm G free.

## 2. Every M5 gap probe is COV-WRONG, and four rules explain it

| outcome | n |
|---|---|
| COV-WRONG | **329** |
| GEN-INVALID | 1 |

Four rules fire on **329 of 329**: **W-AL-01, W-AR-05, W-EP-02, W-ON-02.**

A gap probe exists to exhibit a defect the catalog does *not* cover, so any firing
makes it COV-WRONG. With four rules firing on every package, the probe's own defect
never gets a clean read — the signal is swamped before it can be assessed.

### The mechanism is not the vacuous-noValue pathology

Worth recording because the pattern matches Finding 3 exactly and the inference was
wrong. Measured:

```
validation-result shapes: {'inline': 981}      ← all inline, no bare IRIs
COU shapes:               {'neither': 330}
```

The results are **inline and genuinely omit** `hasUncertaintyQuantification`,
`comparedAgainst` and `wasGeneratedBy`. The three rules fire **correctly**, not
vacuously. W-ON-02 likewise: every COU lacks both an operating envelope and an
applicability constraint.

Different cause from Finding 3, same consequence. And it is the phase's lead
finding from a third angle: the generator does not populate these three properties,
just as it does not build `modelRevisionDate`, `currentModelVersion`,
`signatureTimestamp` or `activityType`. One blind spot, different fields.

## 3. Phase 3's Tier-1 result survives this — by design, not by luck

**The concern.** Phase 3's judge ensemble classified gap-probe candidates into six
verdicts, including REAL-GAP and EXISTING-RULE-MISBEHAVIOR. If four rules fire on
every candidate, "an existing rule already misbehaves here" is trivially true of
all of them, which could bias the panel against REAL-GAP — or, if the panel
disregarded firings entirely, could make REAL-GAP unearned. Either way the
**6 of 6 Tier-1 supported** result would be resting on an artifact.

**It is not.** The judge schema carries a dedicated `alternative_rule_analysis`
field whose purpose is to force exactly that confrontation before a REAL-GAP
verdict. Across the 288 Tier-1 candidate judgments from judge A:

| | |
|---|---|
| `alternative_rule_analysis` empty | **0 / 288** |
| Explicitly names ≥1 of the four always-firing rules | **237 / 288** |
| W-ON-02 / W-AR-05 / W-AL-01 / W-EP-02 named | 198 / 181 / 108 / 101 |

Representative, on `adv-2026-p2-104-fidelity_high-v02` (verdict REAL-GAP, 0.84):

> "**W-AL-01 fired**, but the core problem is not generic absence of uncertainty
> quantification alone; it is that the validation evidence and QoIs are inadequate
> to test the known abstraction gap introduced by the Newtonian model-form
> assumption. **W-AR-05 comparator absence also does not fit well** because
> experimental comparators do exist; what is missing is a fidelity-relevant
> comparison or metric sensitive to the omitted rheology."

The judges saw the firings, named them, and argued why they do not capture the
defect. The concern is answered.

### The instrument disagreement appears inside the judge arm

Read that W-AR-05 sentence again. **W-AR-05 fired** — the validation result carries
no `comparedAgainst`. The judge writes that *"experimental comparators do exist."*

Both statements are true. The comparator exists in the package's prose; it does not
exist as the property the rule reads.

This is a fourth independent instance of the phase's central finding, alongside
W-EP-01, W-ON-02 and the vacuous baselines — and it is the most useful one for the
manuscript, because it is a documented case of an LLM judge and a deterministic
rule disagreeing **because they are reading different things about the same
package**. That is a concrete argument for the label-class partition rather than an
abstract one, and it is in the committed judgment record rather than constructed
for the purpose.

## 4. Chapter material: the W-AR-05 case

Flagged so it is not lost, per author ruling. It costs nothing because it is
already in the committed July judgment record.

On `adv-2026-p2-104-fidelity_high-v02`, judge A returned REAL-GAP at 0.84 with:

> "W-AR-05 comparator absence also does not fit well because **experimental
> comparators do exist**; what is missing is a fidelity-relevant comparison or
> metric sensitive to the omitted rheology."

**W-AR-05 fired on that package** — the validation result carries no
`comparedAgainst`. The judge says comparators exist. **Both are true.** The
comparator lives in the package's prose; it does not live in the property the rule
reads.

That is the thesis in one example: **evidence that exists in prose is invisible to
machine checking until it is captured structurally.** A deterministic rule and an
LLM judge, given the same package, disagree — not because either is wrong, but
because one reads the graph and the other reads the narrative.

It belongs in the chapter beside the three-rules finding. The three-rules finding
shows a rule that cannot fire because the structure was never built; this shows the
evidence *was* there and the structure still was not. Same gap, opposite ends: one
where the corpus omits what the rule reads, one where the corpus has the substance
and omits the encoding.

## Coverage statement

**Measured.** M5 `gap_probe` tier isolated and run through `uofa adversarial
analyze` at v0.5.15.1 with all 66 `out_dir` pointers stale. Outcome distribution
and per-package `rules_fired` read from the produced `outcomes.csv`. All 330
gap-probe packages parsed for validation-result and COU shape. Tier-1 candidate
ids read from `triage/tier1_real_gap_candidates.csv` (310 rows, 6 tier-1 ids) and
joined against `production/run-1/judgments_A.jsonl`.

**Not measured.**
- **The W-AR-05 case in §4 is a single judgment.** Whether other judgments show the
  same prose-versus-property split is unchecked, and the chapter should either
  present it as the one worked example it is or the pattern should be counted first.
- **Judges B and C were not examined.** The 237/288 figure is judge A only. The
  ensemble verdict is majority-of-three, so a full check would read all three.
- **The 237/288 count is a substring match** for rule ids in
  `alternative_rule_analysis`. It establishes that the judges *engaged* those rules;
  it does not establish that the reasoning is sound. One record was read in full.
- **51 of 288 name none of the four.** Not inspected. They may cite other rules,
  reason structurally without naming ids, or be thin — unknown.
- **Full M5 re-analysis (4,601 packages) was not run.** Scale is proven to 330. The
  full run is separately gated on **P2-A** (`PHASE2_STATUS_REPORT.md:54`), the open
  author decision on whether to re-baseline Phase 2 at v0.5.15.1 — producing that
  number would resolve P2-A by fait accompli.
- **M5 is the training corpus** for Phase 2.5's refinement loop, so any recall
  figure from it at v0.5.15.1 is optimistic in a way the holdout figure is not, and
  would need that caveat wherever it appears.
