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
