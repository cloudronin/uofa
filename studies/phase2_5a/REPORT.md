# Phase 2.5a — Arm M report

Catalog **v0.5.15.1** (frozen). Measured 2026-08-16. Re-derive with
`PYTHONPATH=src python studies/phase2_5a/run_arm_m.py`; per-mutant records in
`results.json`, profile status in `conformance.json`, substrate validity in
`STEP-0C-PRECONDITION.md`.

---

## The finding

**Three rules that scored 0.000 recall at every measured catalog version detect
their defect correctly the moment their antecedent exists in the package.**

W-EP-03, W-AR-04 and W-CON-03 were the catalog's persistent zeros — 0.000 at the
M5 baseline (v0.5.7) and 0.000 again at the v0.5.13 holdout. Given a package that
instantiates the structures they read, each fires on the first mutant and on every
mutant: 3 of 3 sites each, across three substrates.

**The rules were never broken. No encoding the project produces instantiates what
they read.** `modelRevisionDate`, `currentModelVersion`, `signatureTimestamp`,
`activityType`, `referencesIdentifier`, `hasVerificationActivity` and an inlined
`bindsRequirement` appear in **zero** of the seven example packages across five
packs. A rule cannot fire on a structure the corpus never builds, and a zero
recorded against it measures the corpus, not the rule.

This is measured, not inferred, and it is the phase's result. It was invisible
before this arm existed because the generator that produced Phase 2/2.5's corpus
has the same blind spot as the encodings do.

### The same finding from three other directions

| | |
|---|---|
| **W-EP-01** scores 20/20 on the v0.5.13 holdout and **cannot fire on any conformant package.** Its guard names `uofa:Claim`; the schema declares `uofa:AssuranceClaim` and makes it `bindsClaim`'s `rdfs:range`. The synthetic corpus emits bare `type: "Claim"`, which resolves through `@vocab` to the undeclared class and fires the rule. Every real encoding uses `AssuranceClaim`, or no type at all. | generator disagrees with schema |
| **W-ON-02** fires on **all three** case-study encodings unmutated. Every one has a Context of Use bounded by neither an applicability constraint nor an operating envelope. Its detection needed no injection; producing a recall row required manufacturing a clean state first. | encodings disagree with catalog |
| **27 of 48 baseline findings are vacuous.** W-AL-01, W-AR-05 and W-EP-02 test `noValue` on a ValidationResult, so a package referencing results as bare IRIs fires all three on every result. Inlining morrison/cou1's three results — same IRIs, same count, nothing else altered — takes them 3/3/3 → **0/0/0**. | catalog discriminates on serialization shape |

Stated once: **the generator and the encodings disagree about what the rules read,
and the catalog was tuned against the generator.** The controlled demonstration is
the inline experiment — one package, one variable, evidence untouched. The
morrison COU1-vs-COU2 contrast corroborates it but is not a control, since the two
are different Contexts of Use and could legitimately differ in evidence.

---

## Arm G — the version-consistent pair, at no LLM cost

The manuscript currently pairs **CE recall 73.4% at v0.5.7** with **NC clean 97.1%
at v0.5.15.1**. Two catalog versions, one table. Now resolved:

| | corpus | v0.5.13 (recorded) | **v0.5.15.1 (measured)** |
|---|---|---|---|
| CE recall, evaluable rows | v0.5.13 holdout, 378 packages | 288/378 = 76.2% | **287/378 = 75.9%** |
| NC clean rate | v0.5.15.1 NC holdout, 171 validated | — | **97.1%** |

**Scope that rides with the 97.1% wherever it appears.** It is measured on negative
controls *constructed to carry no catalog-detectable weakness*, bounded contexts of
use included. That construction is correct, not convenient — a true negative for a
presence-checking rule must actually have the property present, and a control that
omits the field is a package with that defect, not a clean one. The same catalog
scores **8/176 = 4.5%** on the unpatched M5 NC corpus, which is **a detection result,
not a competing specificity figure**: those packages genuinely lack applicability
bounds, nobody injected the absence, and W-ON-02 reporting it on 158 of 176 is the
rule working. Decomposition of the 0% → 97.1% trajectory at
[INV-16](../../docs/investigations/INV-16-nc-trajectory-decomposition.md).

**The delta is exactly one package**, and it is attributable: W-CON-01 goes 20/20 →
19/20. That is the single rule-body change between the v0.5.13 holdout tag and
v0.5.15.1 — `notEqual(?status, 'not-assessed')`, added at v0.5.14. Everything else
in that diff is comments, and every other pattern's count is identical.

Worth recording precisely because [rules:376-387](packs/core/rules/uofa_weakener.rules)
*argues* the guard is recall-neutral: *"no CE target uses 'not-assessed' as the
trigger, so adding the exclusion guard doesn't change the rule's CE-target firing
behavior."* Measured, it changes it by one CE package in twenty. The argument was
nearly right; the phase's standard is that nearly-right arguments get measured.

### No generation was needed

P25-A's scoping budgeted `API key + ~$30–50`, for generating a *fresh* holdout.
That buys holdout hygiene a fixed-corpus two-version comparison does not need:
adversarial packages are catalog-version-independent, so CE recall at v0.5.15.1 is a
**re-classification** of committed packages. Cost: Jena time. Re-derive with
`PYTHONPATH=src python studies/phase2_5a/run_arm_g.py`; rows in `arm_g_results.json`.

### Two denominators are in circulation, and the report must name one

`288/420 = 68.6%` (the Phase 2.5 status report) and `288/378 = 76.2%`
(`summary.csv`) are **the same measurement**. The first includes 40 GEN-INVALID
packages in the denominator; the second excludes them. The manuscript's M5 figure
says "73.4% **(evaluable rows)**", i.e. the exclusion convention, and this report
follows it.

The 40 are the entire CE corpus for **W-ON-01 and W-SI-01** — `shaclFailed: 20` on
both specs, every package. The generator could not produce a valid package
exhibiting either defect, which is why the original analysis reported those two
patterns not-measurable. It is also the same fact Arm M reaches from the other
direction: both are `sh:minCount` fields, so the flaw and profile-conformance
cannot coexist. **Two independent arms, one conclusion.**

*(An earlier pass of this script reported 78.3% by counting those 40 as hits —
`_classify` was called with `package_exists=True` unconditionally, and the files are
on disk, so nothing announced the error. It disagreed with both recorded figures,
which is what prompted the reconciliation.)*

## GATE-H3

**Split verdict. MECHANICAL passes; overall fails.**

| Clause | Bar | Measured | |
|---|---|---|---|
| MECHANICAL detection | ≥95% | **35/35 = 100.0%** (Arm M, denominator 13) | **PASS** |
| Overall detection | ≥80% | **287/378 = 75.9%** (Arm G, CE recall at v0.5.15.1) | **FAIL** |
| False positives, per class | <10% | MECHANICAL 9 firings / JUDGMENT 1, over the 171-package holdout **constructed to carry no catalog-detectable weakness** (scope above) | PASS |

Reported as a split rather than resolved to one number. The MECHANICAL result is
about patterns whose defect is expressible and injectable; the overall figure is
carried by the JUDGMENT-class and generator-produced corpus, where three patterns
(W-AR-04, W-EP-03, W-CON-03) contribute 0/20 each for the reason §"The finding"
gives — the generator never builds the structures they read. **Those same three
score 3/3 under Arm M once the structure exists.** The gate's two clauses are
measuring different things, and the split is the honest way to say so.

**Evaluated once.** Neither number is revisited.

### The MECHANICAL half, in detail

**MECHANICAL = 35/35 = 100.0%**, against a ≥95% bar. **Evaluated once.**

Denominator **13** per Decision Record addendum F, computed from measured status
rather than set (`operators.gate_denominator()` — a mismatch would be a finding,
not a config fix):

```
 17   MECHANICAL partition (scopes the battery, not the gate)
 -1   W-EP-01                       unfireable as shipped
 -3   W-ON-01, W-SI-01, W-SI-02     zero conformant-but-flawed mutants, measured
 =13
```

### What the 16-denominator version would have scored

**Also 100.0%.** Required by addendum F condition 2, and the answer is worth
stating plainly: the three excluded patterns contribute **zero conformant defect
instances** either way, so the rate is identical at 35/35. What the denominator
changes is how many patterns contribute a row — 13 of 13, versus 13 of 16 with
three structurally unable to.

**The exclusion is not outcome-determinative.** It cannot be read as selecting a
denominator that flatters the number, because the number does not move.

### The honest qualification

100% is measured over **35 defect instances across 13 patterns**, and the shape of
that n matters more than the headline:

- **Five patterns rest on n=3, two on n=1.** A Wilson 95% interval on 1/1 spans
  roughly [0.21, 1.00]; on 3/3 roughly [0.44, 1.00]. Patterns clearing on wide
  intervals: **W-AL-02 and W-CON-04 (n=1)**; **W-AL-01, W-AR-03, W-AR-04, W-AR-05,
  W-CON-02, W-CON-03, W-CON-05, W-EP-02, W-EP-03, W-ON-02, W-PROV-01 (n=3)**. That
  is every gate pattern.
- **8 of the 13 are enrichment patterns** — their defect is expressible only in a
  package built to express it. The gate is majority-enrichment, which is a
  different object from a majority as-encoded gate.
- **5 of the 13 are as-encoded** (W-AL-01, W-AL-02, W-AR-05, W-CON-04, W-EP-02),
  and four of those five exist on exactly one substrate.

The honest reading: **where a defect is expressible, the catalog detects it
reliably.** Whether the defects the catalog detects are the defects real evidence
carries is a different question, and §"The finding" is the evidence that it is
substantially not.

---

## Per-pattern results

`n` is engine-measured mutation sites, not element counts. Every mutant is
delta-scored against its own baseline — the substrate for Class A, the
enriched-clean package for Class B.

| Pattern | class | n | conformant n | detected | gate row | expected layer | measured layer |
|---|---|---|---|---|---|---|---|
| W-AL-01 | A | 3 | 3 | 3/3 | ✓ | rules | rules |
| W-AL-02 | A | 1 | 1 | 1/1 | ✓ | rules | rules |
| W-AR-05 | A | 3 | 3 | 3/3 | ✓ | rules | rules |
| W-CON-04 | A | 1 | 1 | 1/1 | ✓ | rules | rules |
| W-EP-02 | A | 3 | 3 | 3/3 | ✓ | rules | rules |
| W-AR-03 | B | 3 | 3 | 3/3 | ✓ | rules | rules |
| W-AR-04 | B | 3 | 3 | 3/3 | ✓ | rules | rules |
| W-CON-02 | B | 3 | 3 | 3/3 | ✓ | rules | rules |
| W-CON-03 | B | 3 | 3 | 3/3 | ✓ | rules | rules |
| W-CON-05 | B | 3 | 3 | 3/3 | ✓ | rules | rules |
| W-EP-03 | B | 3 | 3 | 3/3 | ✓ | rules | rules |
| W-ON-02 | B | 3 | 3 | 3/3 | ✓ | rules | rules |
| W-PROV-01 | B | 3 | 3 | 3/3 | ✓ | rules | rules |
| **W-ON-01** | A | 3 | **0** | 3/3 | — | schema+rules | **schema+rules** |
| **W-SI-01** | A | 3 | **0** | 3/3 | — | schema+rules | **schema+rules** |
| **W-SI-02** | A | 6 | **0** | 6/6 | — | schema+rules | **schema+rules** |
| **W-EP-01** | B | 3 | 3 | 3/3 | — | rules | rules |

Expected and measured catch layers agree on every row. No divergence finding.

## Schema-caught table (addendum F condition 1)

Reported **beside** the rule-layer table, not in place of it, so total cross-layer
detection is visible.

| Pattern | mutants | caught by C2 | caught by C3 | headline row |
|---|---|---|---|---|
| W-ON-01 | 3 | 3 | 3 | no |
| W-SI-01 | 3 | 3 | 3 | no |
| W-SI-02 | 6 | 6 | 6 | no |

**Both layers catch all twelve.** This is redundant coverage, not a handoff.
`check.run_structured` runs C2 → C1 → C2.5 → C3 with **no short-circuit on
non-conformance**: on a schema-caught mutant the pipeline reports C2 ✗, C1 ✗ and
C3 ✓ having fired the target. So these three patterns are excluded from the gate
because they admit no conformant-but-flawed mutant — **not** because the schema
intercepts them before the rules run, which is measurably not what the pipeline
does.

That two independent layers detect the same defect class is a stronger property
than either alone, and it is the honest version of the architectural claim.

## Suppression analysis

12 of 50 mutants suppressed a baseline finding. **All twelve are correct
consequences of the mutation, not defects** — each removes a parent structure a
second rule needed in order to bind:

| Operator | suppressed | why it is correct |
|---|---|---|
| MUT-DEL-03 (W-EP-02) | W-PROV-01 −1 | deleting `wasGeneratedBy` removes a provenance edge, so a node leaves scope |
| MUT-DEL-04 (W-ON-01) | W-ON-02 −1 | deleting the COU removes what W-ON-02 binds to |
| MUT-DEL-06 (W-SI-02), cou1/nagaraja | W-AL-01, W-AR-05, W-EP-02 −3/−6 each | deleting `hasValidationResult` removes the bare-IRI results whose **vacuous** firings those were — Finding 3 reproducing under mutation |
| MUT-DEL-06 (W-SI-02), cou2 | W-PROV-01 −3 | the deleted results were in provenance scope |
| MUT-ANT-08 (W-EP-01) | W-PROV-01 −1 | **operator artifact**: the enrichment replaces `bindsClaim` rather than augmenting it, so the original claim's subtree leaves scope. Excluded from the gate anyway; worth fixing if this operator is ever scored |

The delta check earned its place before this run. MUT-REF-01's original design
looked like a clean 4/4 miss and was in fact a mutation that made the detector
*quieter* — every single-edit form on W-PROV-01 suppresses rather than adds. An
absolute check would have reported a rule defect that does not exist.

## Method notes

- **Ground truth is the manifest, by construction.** Site, before/after values and
  diff hash come from the canonical graph diff; only the target pattern — the label
  being declared — comes from the operator.
- **Liveness by RDF canonicalization**, `rdflib.compare.to_isomorphic`, not
  `integrity.canonicalize_and_hash`, which is sorted-key JSON and would have read a
  JSON-visible edit that vanished on expansion as live.
- **Class B baselines are enriched-clean, not the substrate.** Diffing against the
  raw substrate would fold the enrichment into the record and the manifest would
  claim it as part of the injected defect.
- **Conformance is asserted after enrichment, before violation**, and raises. A
  non-conformant enrichment removes a gate-eligible pattern from a denominator of
  13 for a reason unrelated to detection.
- **Coupled mutants score once.** MUT-DEL-07 and MUT-DEL-08 produce a
  byte-identical mutant (equal diff hashes): on nagaraja/cou1 one deletion of
  `hasSensitivityAnalysis` fires both W-AL-02 and W-CON-04. One test case, two
  expected findings, counted once. Two rules reading one field is a
  catalog-redundancy observation; the diff-derived manifest catches it by
  construction rather than by anyone noticing.
- **Measured denominators beat projected ones**, twice over: the step-1 probe put
  W-SI-02 at 15 sites (it is 6 — the rule fires on whole-property absence, not per
  element) and W-PROV-01 at 4 additive sites (there are none; it needed
  reclassification to enrichment). The implementation plan's prose said "Class A,
  13 patterns" and enumerated 12. The registry is counted, never read off a list.

## Coverage statement

**Measured.** 50 mutants over 17 operators and 3 substrates, all live, all scored.
Every mutant through `uofa rules`, `uofa shacl` and `uofa check` at v0.5.15.1.
Substrate validity established in `STEP-0C-PRECONDITION.md` (all three verify and
conform before mutation). Profile status per mutant in `conformance.json`.

**Not measured.**
- **Arm G ran on the v0.5.13 holdout re-classified at v0.5.15.1, not on a fresh
  corpus.** That is the right comparison for a two-version question and it cost
  nothing, but it is not a fresh holdout: these packages were spent at v0.5.13.
  Since no rule was tuned against them between the two versions — the only change
  is the W-CON-01 guard — re-measuring does not leak, but a fresh battery would
  still be the stronger artifact if the ~$50 is ever spent.
- **gap-probe and interaction arms are reported as counts only** (35 and 9
  evaluable rows, no target firings). Gap probes carry no target weakener, so
  "recall" is undefined for them; the Tier-1 gap analysis they feed is Phase 3's,
  not this report's.
- **Three substrates, not five.** The two NASA HPT `.jsonld` files are weakener
  reports, not packages: `@graph` of 17 (cou1) and 20 (cou2) `WeakenerAnnotation`
  nodes plus an `@id`/`hasWeakener` stub, no `UnitOfAssurance`. Stripping the stored
  annotations and re-running yields `0 triples, 0 inferred, 0 detected`. No encoded
  HPT package exists in the repo.
- **Wilson intervals are stated qualitatively above, not computed per row.** They
  should be computed before the table reaches Ch4.
- **W-EP-01's contrast variant is described but not built.** The report claims the
  rule stays silent when the claim is typed `AssuranceClaim` through the identical
  violation; that follows from the rule body and from every substrate's behaviour,
  but the paired mutant has not been run. Build it before the claim is printed.
- The `iso42001` and `surrogate` packages were not used as substrates.
