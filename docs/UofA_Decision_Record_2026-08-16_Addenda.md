# UofA Author Decision Record 2026-08-16 — Addenda C, D and E

*(Filename carries no letter range: further addenda append here rather than forcing a rename. Cited in earlier commits as `…_Addenda_C-D.md`; git tracks the rename.)*

Status: RULED
Date: 2026-08-16
Owner: Vishnu Vettrivel
Parent: `UofA_Decision_Record_2026-08-16.md`, committed alone at `fad31cf5` with addenda A (W-AR-03 class) and B (enrichment-split gate treatment).

Carried in a separate file rather than appended to the parent, because two sessions
were writing that afternoon and a conflicted merge of the ruling record is the one
merge worth never having. A4 cites both commits; the parent record and this file are
one document for citation purposes. Fold them together at the next quiet point.

**Both rulings below are recorded before Arm M is scored, and before the operators
they govern are written.** That ordering is the point, and it is the same discipline
`fad31cf5` established for the twelve original rulings.

---

## Addendum C — Class B funded in full; phase cap 22h

**Ruling.** All **8** Class B (`MUT-ANT-*`) operators are funded. The enrichment
family is not cut.

**Rationale, recorded because it is the load-bearing part.** With the `iso42001`
recovery path falsified, the choice was clean: fund all eight, or gate over the
subset that happened to be cheap. **A gate evaluated over the cheap subset is the
pattern this program exists to kill.** Selecting the measured set by implementation
cost, after seeing which patterns were expensive, is post-hoc scoping — the same
defect as retroactive thresholding, arriving by a different door. Eight operators at
30–45 minutes each is 4–6h, and each produces either a recall row or a finding.

**"Uncoverable within budget" is withdrawn as an available verdict.** It remains
legitimate only for a pattern that *cannot be mutated*, which none of the eight are.
A pattern that is merely expensive gets built.

**Cap moves to ~22h** for the phase. Past that, escalate rather than absorb. The
growth is operator count and machine runs, not new design, so the ceiling is not
expected to bind.

## Addendum D — the substrate set is five, per the measurement

**Ruling.** All **five** distinct encoded packages are substrates: `morrison/cou1`,
`morrison/cou2`, `nagaraja/cou1`, and both NASA HPT configurations. Delta scoring
against each substrate's own baseline.

**Rationale.** The three-substrate working set rested on a flat-probe artifact that
read the HPT packages as empty. Corrected, v2.1 §8's original five-package ruling is
the *measured* answer rather than only the ruled one. Marginal cost is mostly machine
time — deterministic mutations, exhaustive sites, local runs — plus two baseline
measurements. W-AR-05 also gains cross-substrate `n` it otherwise lacked.

> **Open against this ruling, flagged not resolved.** Session 1's third pass on those
> two files (`d77f39ce`) reports that the HPT `.jsonld` files contain only stored
> `WeakenerAnnotation` nodes — no `UnitOfAssurance`, which 24 of 29 rules require — so
> the 17 and 20 are annotations read back, not inferences, and no encoded HPT package
> exists in the repo. I verified the composition independently: cou1 is 17 annotations
> plus an `@id`/`hasWeakener` stub, cou2 is 20 plus a stub, no `UnitOfAssurance` in
> either. **If that holds, addendum D's premise is the artifact it was meant to
> correct**, and the substrate set is five ruled / three executable until an HPT
> package is encoded (an extraction step, out of phase scope). Recorded here rather
> than silently reverted, because a ruling withdrawn on evidence belongs in the record
> as much as one made on it. Author to confirm which way this lands; the phase
> proceeds on three and adds the HPT pair the moment a package exists.

## Addendum E — the SHACL-conformance split is Arm M's organizing structure

**Ruling, as issued.**

The rule catalog's job is catching defects that schema validation can't see. A mutant
that flunks the SHACL profile never tests the rules; it tests the schema. So:

1. **Record SHACL profile status for every mutant** (the full stack already runs for
   layer attribution; this is the same data, elevated).
2. **Split the corpus and the report on it:**
   - **Conformant-but-flawed** (passes the profile, carries the injected defect): this
     is the true test of the rule catalog. Headline per-pattern recall and the
     GATE-H3 evaluation come from this group only.
   - **Schema-caught** (mutation breaks profile conformance): report as
     defense-in-depth evidence at the validation layer, not as rule-engine
     detections. These confirm C2 does its job; they say nothing about C3.
3. **Operator-design preference, applied in the redesign pass:** where a pattern can
   be exercised by either deleting a mandatory field (likely schema-caught) or
   corrupting a value in place (stays conformant), **prefer the corruption form**.
   Valid-but-wrong is both the harder test and the realistic threat model: a package
   that fails schema validation gets bounced at intake; the dangerous package
   conforms and is still wrong. Where only the deletion form exists, keep it and let
   it land in the schema-caught group honestly.
4. **New precondition test, one-time:** before any scoring, assert the five unmutated
   substrates pass `verify` and run `check` cleanly apart from their known measured
   baselines, at the shipped catalog version. The report must be able to say
   "mutation started from valid packages" **with a citation, not an implication**.
5. **Manifest gains a field:** expected catch layer per mutant (schema vs rules), set
   by the operator's design intent, compared against the measured catch layer.
   Divergences (expected rules, caught by schema, or vice versa) are findings, and
   cheap ones.

Note the interaction with the enrichment-class operators: their added structures must
themselves be profile-conformant, or the enrichment produces a schema-caught mutant
and the target rule never runs. **Add a conformance assertion after enrichment, before
violation.**

None of this changes the gate, the denominator, or the substrate set. It changes
**which mutants count toward the gate: conformant-but-flawed only.**

### Flagged against E, not a change to it

E's closing line holds for every pattern that *has* a conformant-but-flawed form. Three
may not have one, and they are a specific three:

| Pattern | Operator | Field | Profile-mandatory? |
|---|---|---|---|
| W-SI-01 | delete the signature | `uofa:signature` | **yes** — carries `sh:minCount` |
| W-ON-01 | delete the Context of Use | `uofa:hasContextOfUse` | **yes** — carries `sh:minCount` |
| W-SI-02 | `noValue` on required bindings | — | **yes** — flagged SHACL-mandatory since v1.0 §1.3 |

Each is a pure presence/absence rule with **no value to corrupt in place**, so
preference 3 has nothing to prefer: the deletion form is the only form, and deleting a
`sh:minCount` field breaks conformance by construction. Under E they land in the
schema-caught group and produce **no headline recall row**.

**These are exactly the three patterns that have never produced a confirmed detection
at any catalog version.** E supplies the explanation: they cannot reach the rule layer
in a conformant pipeline, because the schema catches their defect first. That is the
positive architectural claim v1.0 §1.3 item 4 anticipated, and arriving at it by
measurement rather than assertion is a better result than a recall number would have
been.

The open question is arithmetic, and it must be settled **before scoring**, alongside
the 16-vs-17 confirmation: with three of the sixteen unable to produce a conformant
mutant, does the GATE-H3 denominator stay **16** (the three score zero, costing ~19
points against a ≥95% bar), or become **13** (the three are reported as architecturally
unreachable rather than missed)? At a ≥95% gate this is not a rounding question — it
is the difference between a gate that can pass and one that cannot, and deciding it
after seeing the split would be precisely the post-hoc scoping addendum C rules out.

Recommendation: **13**, with the three reported as a named architectural finding. A
pattern the schema catches first has not been missed by the rule engine; counting it
as a miss measures the wrong layer, which is the whole point of E. But it is the
author's call and it is not made here.

## Addendum F — the gate denominator is 13, with four named exclusions

**Ruling, as issued.** *(The ruling stands. Its stated mechanism was falsified within
the hour — see "Correction to F's rationale" below, which is the version that goes to
A4. The issued text is retained unedited because F named its own reversal condition and
the reversal is part of the record.)*

> ~~**The denominator is 13, with the three schema-intercepted patterns reported as
> architecturally unreachable.**~~ The gate's question is *"does the rule engine detect
> defects it can see."* ~~A defect the schema intercepts before the rule layer runs is
> not a rule-engine miss; it is the completeness layer doing its job upstream.~~
> Scoring those three as zeros would make the gate measure **the architecture's
> layering rather than the catalog's detection**, and a gate that cannot mathematically
> pass regardless of rule quality is not a gate — it is a foregone conclusion wearing
> one.
>
> ~~The three get their own labeled row: *unreachable at the rule layer in a conformant
> pipeline, defect class caught by the completeness profile*~~, with the measurement
> that proved it.

### Correction to F's rationale — the ruling of 13 is unaffected

**F named its own reversal condition: *"if any of the three turns out to reach the rule
layer, the exclusion is wrong and the denominator moves back."* They reach the rule
layer.** The condition fired, and it fired on the rationale, not on the arithmetic.

**Verified in the code, not inferred.** `check.run_structured` runs C2 → C1 → C2.5 → C3
**unconditionally**: there is no early return anywhere between the SHACL stage and the
rules stage, and the only guard on the rules stage is the `--skip-rules` flag. Nothing
short-circuits on non-conformance. Measured corpus-wide, **12 of 23 Class A mutants are
non-conformant *and* rule-layer-caught** — the same measurement that made the
`caught_by` finding useful. **Nothing is intercepted.**

**Provenance of the error, recorded because the record's credibility depends on it.**
"Architecturally unreachable" and "intercepts before C3 runs" originated with me
(session 2), inferred from a static read of `sh:minCount` in the shapes file. The read
was correct; the inference was not. Deleting a `sh:minCount` field does break profile
conformance — it does **not** stop the rule engine from running, because the pipeline
has no such gate. That is the identical error class this session has been catching in
others all afternoon: **a real check at one layer reported as a conclusion about the
stack.** Caught by measurement rather than by review, one CLI invocation, and A4 is
precisely where a committee member would have found it.

**The corrected rationale, which is what A4 carries:**

1. Addendum E scores the gate on **conformant-but-flawed mutants only**. That rule is
   about **threat realism**, not about layering: a package that fails schema validation
   gets bounced at intake, so detecting one says little about the dangerous case, which
   conforms and is still wrong.
2. W-SI-01, W-ON-01 and W-SI-02 admit **zero conformant mutants** — measured, recorded
   in `studies/phase2_5a/conformance.json`. Their defect necessarily breaks the profile,
   so no conformant-but-flawed mutant of them can exist.
3. Having no gate-eligible mutant, they carry no headline recall row and leave the
   denominator. **13.**
4. **Separately and importantly: the rule engine does detect them.** Measured, on
   non-conformant mutants. The exclusion is therefore a statement about *what can be
   scored under E*, and says nothing whatever about rule quality.

Same denominator, and now a reason that survives the CLI invocation that killed the
first one.

### Measured outcome of F's condition 2 — the exclusion changed nothing

Arm M (`008626f2`) answers condition 2's requirement to state what the 16-denominator
version would have scored: **it scores 100.0% as well.** The three excluded patterns
contribute zero conformant instances either way, so the *rate* does not move — only the
count of patterns contributing a row, 13 of 13 against 13 of 16.

**The exclusion is therefore not outcome-determinative, and that belongs early in the
measurement report rather than in a sensitivity note.** *"Three patterns were excluded
on stated principle before scoring, and the exclusion turned out not to change the
result"* is the strongest good-faith evidence the phase produces, precisely because the
decision **could not have been reward-seeking** — it was recorded, dated and committed
before any number existed to reward it. A favourable number would have been weaker
evidence than this one is.

**The corrected finding is the better one.** Not *"the schema catches it, so the rules
never see it"* — a handoff — but **"both layers independently catch it."** That is
genuine defense in depth, and it makes the schema-caught table required by F's condition
1 *more* interesting rather than less: it demonstrates **redundant coverage**, two
independent layers each detecting the same defect class, which is a stronger property
than either layer's coverage alone. The "positive architectural claim" inherited from
spec v1.0 §1.3 item 4 needs this same edit wherever it appears.

**Two conditions, so this cannot be read as gate-softening.**

1. **The schema-caught demonstrations still run and still report.** The three deletion
   mutants get built, the completeness layer catches them, and **that table appears
   beside the rule-layer table**, so total system detection across layers is visible
   and the committee sees that nothing was quietly dropped.
2. **The audit-trail entry states the arithmetic plainly:** denominator 13, **what the
   16-version would have scored**, and why the 13 framing is the honest one. Disclosed
   reasoning before measurement is exactly what distinguishes this from post-hoc
   scoping, and the timestamp will show it.

**The stacked 16-vs-17 question resolves as previously ruled:** W-EP-01, whose guard
names a class the schema never defines, stays out and is reported as a **discovered
catalog defect**.

### The final arithmetic

| Step | n | Excluded | Ground |
|---|---|---|---|
| MECHANICAL partition | **17** | — | Rulings 3, 4 and addendum A. Scopes the battery and per-class coverage |
| less unfireable-as-shipped | 16 | **W-EP-01** | Guard requires `uofa:Claim`; the schema declares only `AssuranceClaim` and makes it `bindsClaim`'s range. Scores 1.000 on synthetic packages typed against a class that does not exist. **Discovered catalog defect** |
| less no-gate-eligible-mutant | **13** | **W-SI-01, W-ON-01, W-SI-02** | Pure presence/absence rules with no value to corrupt, so their defect necessarily breaks the profile: **zero conformant-but-flawed mutants exist** (measured, `studies/phase2_5a/conformance.json`). Under E only conformant mutants score, so they carry no headline row. **The rule engine does detect them** on non-conformant mutants — both layers catch independently |

**GATE-H3 is evaluated over 13.** All four exclusions are individually named,
mechanism'd, and dated **before scoring**. That last clause is the one doing the work:
the same four exclusions decided after seeing the numbers would be indistinguishable
from tuning, and the only thing separating the two is this record and its timestamp.

### What this supersedes

The "Gate denominator: 16" table in the section below is **superseded by F**. It is
retained rather than edited, because the record of what was thought at 17:20 is part of
what makes the 13 credible at 18:00 — a denominator that moved twice, in public, with
reasons attached each time, is a different object from one that arrived at 13 quietly.

## Restated: W-EP-01 and the gate denominator (superseded by addendum F — retained as record)

The prior ruling holds and the measured 20/20 sharpens it. W-EP-01 scores **perfect
recall on a corpus that types claims against `uofa:Claim`, a class the schema never
declares**, and has **zero possible recall on conformant evidence**, where claims are
typed `AssuranceClaim` or untyped. That is not a detection result. It is a
measurement of the disagreement between the generator and the encodings.

**Gate denominator: 16.** Derived as the 17 MECHANICAL patterns *less W-EP-01*, which
is reported separately with its mechanism named rather than carried as a plain row in
the MECHANICAL rollup. Recorded explicitly because the gate is evaluated **once** and
its denominator must not be arguable afterwards:

| Figure | Value | What it is |
|---|---|---|
| MECHANICAL partition | **17** | Pattern-set size; scopes the mutation battery and per-class coverage |
| GATE-H3 denominator | **16** | 17 less W-EP-01, reported separately |
| Gate measurement basis | defect **instances** | Per A5's effective-n rule, not pattern count |

> **Author check before Arm M scores.** This reads the "16-pattern denominator" as
> 17 − W-EP-01. The alternative reading is that 16 was a slip for 17 with W-EP-01
> retained in the rollup. One line either way settles it, and it must be settled
> before scoring rather than after.

## Reporting: lead with the instrument disagreement

The report's first paragraph is the finding, not the gate.

**"The generator and the encodings disagree about what the rules actually read, and
the catalog was tuned against the generator."** W-EP-01 scores 20/20 on a class the
schema never declares; W-ON-02 cannot be scored in Arm M at all because every real
encoding already violates it. Those are the same finding seen from both ends.

**The controlled demonstration — added 2026-08-16, and it is stronger than either
anecdote.** W-AL-01, W-AR-05 and W-EP-02 test `noValue(?result, <property>)`. A
package that references its validation results as **bare IRIs** gives the rules a
node with no properties, so all three succeed vacuously and fire on every result.
Inline morrison/cou1's three results — same IRIs, same count, only the three
properties the rules read, nothing else touched — and the three patterns go from
**3/3/3 to 0/0/0**. Across the substrates, **27 of 48 baseline firings are vacuous**,
and the split is exactly the inline/bare-IRI split.

That is a controlled comparison rather than an observation: one package, one variable,
nine weakeners appearing and disappearing on **serialization shape alone, with the
evidence untouched**. Morrison COU1 and COU2 corroborate it from the corpus side —
same study, nine-weakener delta on those patterns, the difference being that COU1
references results by IRI and COU2 inlines them — though that pair carries a genuine
confound, being two different Contexts of Use. **Lead with the inline experiment**,
which has none, and cite the COU pair as corroboration.

This is the thesis demonstrated on the project's own instrument: a defect class that
is invisible to a generator-scored arm and obvious to a deterministic one.

It is a stronger contribution than the gate number whichever way the gate lands,
because it is exactly the class of defect that is **invisible without a deterministic
arm and machine-checkable ground truth** — the praxis thesis demonstrated on the
praxis's own toolchain.

GATE-H3 is still evaluated once, honestly, against the denominator above, and its
result is reported whichever way it lands. It is simply not the lead.

---

## Addendum G — P2-A closes, and the residual queue is dispositioned

Status: RULED
Date: **2026-08-17**

**One filter was applied to every item: does it change a chapter sentence before the
defense?** Recorded because the filter did more work than any individual ruling, and
because it is the reusable part.

### G.1 — P2-A closes today, in three separate rulings

P2-A ("decide whether to re-baseline Phase 2 on the v0.5.15.1 catalog") was treated
as one decision and is actually three. Ruled separately.

| Question | Ruling | Basis |
|---|---|---|
| **Re-baseline the figures** | **DONE** | The full battery is re-analyzed at v0.5.15.1 — all four intents, 4,601 packages, zero LLM cost (`98959943`). Every M5 number has a current-catalog counterpart and the chapter cites the version-consistent pair. |
| **Re-judge the corpus** | **NO — declined, not deferred** | The judge panel validated the adversarial corpus's *realism*, and that corpus is frozen. After this month's reframe the detection numbers no longer route through judges at all. Re-judging buys a cleaner footnote at real cost and touches nothing load-bearing. **Future work, with the cost stated.** |
| **Regenerate the corpus** | **NO** | Same logic as the standing ruling. The generator's blind spots are now a documented finding rather than a defect to design around, and a regenerated corpus would test a **new instrument** — that is the next paper, not this praxis. |

**The decision was very nearly taken against a stale premise.** Three live documents
still asserted that no full-battery re-run existed, which the merged run had already
overtaken. Corrected before the ruling, not after. **That sequence — correct the
premise, then decide — is the defect this month has been curing, applied to itself.**

### G.2 — Residual dispositions

| Item | Ruling | Why |
|---|---|---|
| **Issue #67** (stale `spec_path`, empty per-COU columns) | **Split.** Do the loud-failure half now — narrow the bare `except: pass` so the missed lookup is visible. Leave the path repair parked at point-of-use. | Ten minutes, and it is **entry #7** in the silent-null catalogue (`INV-6-findings.md`), which had six entries and not eight when this was ruled; no chapter sentence quotes a per-COU figure. **Guarded:** if any coverage-delta column reaches a chapter table, the path fix fires first — same shape as the contrast-variant rule at `REPORT.md:296`. |
| **Intermediate-version curve** (where along seven catalog versions the 4.5 points arrive) | **Skip.** One line in future work. | Free Jena time is not free author attention. The chapter's claim is endpoint-to-endpoint and the decomposition is already measured; the interior is a curiosity. |
| **v0.5.12 hybrid corpus** (31/180 non-conformant today) | **Quoting ban, stated in the audit appendix.** | So a reader who finds those numbers learns why nothing cites them, rather than inferring an oversight. |
| **W-AR-05 as chapter material** | **Count it before the chapter uses it.** | The only residual that is genuinely load-bearing: the results structure leans on it as *the* prose-invisibility example. Grep the committed judgment records for the same shape — rule fired on absence, judge cited prose. Siblings upgrade it to a measured pattern with a count; none makes "one recorded instance" an honest label. **Either outcome beats a committee member asking "how often?" and the answer being unknown.** |
| **Six May issues** (#15–#19, #22) | **Untouched.** | None changes a chapter sentence. |

### G.3 — What this addendum does not do

It does not reopen the M5 adjudication (Addendum-level ruling of 2026-08-17, recorded
at `M5-REBASELINE-PREDECLARATION.md` §ADJUDICATION), and it does not revise the
97.1% or its scope. It closes P2-A and empties the residual queue.
