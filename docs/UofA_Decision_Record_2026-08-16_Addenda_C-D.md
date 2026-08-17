# UofA Author Decision Record 2026-08-16 — Addenda C and D

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

## Restated: W-EP-01 and the gate denominator

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
