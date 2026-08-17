# INV-8 — Where judge output is load-bearing for H3

Status: **ESCALATED — re-scoped against parent spec v2.0.** The original
escalation is **resolved by the author**; a larger one replaces it. A later
addendum **falsifies** this file's own typing hypothesis — read it first.
Date: 2026-08-16 (two addenda same day: Phase 2.5a §0.1, then v2.0)
Feeds: parent A2, D2, D7, A1, B2; Phase 2.5a

---

# ADDENDUM 2 — Phase 2.5a §0.1 precondition check (supersedes the typing hypothesis)

First entry of Phase 2.5a's evidence trail, per that spec's §0.1, which required
this check before any mutation code was written and required its result recorded
here either way. **The check falsified the hypothesis**, so the spec's escalation
branch was taken: the operators were redesigned rather than built on a false theory.

## What this replaces

The v2.0 addendum below closes with a labelled **HYPOTHESIS**: that W-EP-03,
W-CON-03 and W-AR-04 score 0.000 because Jena's `lessThan` / `greaterThan` fail
silently on mistyped literals. It recommended opening two or three failing packages
to settle it. That check is now run. **The hypothesis is wrong.**

## Finding 1 — typing is correct and was never the problem

`spec/context/v0.5.jsonld` declares:

| Property | Context declaration |
|---|---|
| `dataVintage` | `{"@id": "uofa:dataVintage", "@type": "xsd:dateTime"}` |
| `modelRevisionDate` | `{"@id": "uofa:modelRevisionDate", "@type": "xsd:dateTime"}` |
| `evidenceTimestamp`, `signatureTimestamp` | both `xsd:dateTime` |
| `modelVersion`, `currentModelVersion` | untyped — correct; W-AR-04 uses `notEqual` on strings |

JSON-LD expansion therefore yields properly typed literals and the comparisons work.

## Finding 2 — the rule's antecedent never binds

Measured across **all 180** committed `w-ep-03` packages under
`dev/build/adversarial/phase2/2026-04-26/confirm_existing/`:

- **180/180** have **zero** ValidationResults carrying `wasGeneratedBy`. W-EP-03
  requires `hasValidationResult → prov:wasGeneratedBy → prov:used →
  Dataset.dataVintage` ([rules:67-83](packs/core/rules/uofa_weakener.rules)); with
  no `wasGeneratedBy` the body cannot bind at all.
- **65/180** park their datasets under `dataset` / `datasets` /
  `uofa:bindsDatasetInline` — **terms absent from the context** — so expansion
  silently drops those nodes before the engine sees them.
- The staleness is real in the prose (descriptions explain it) and real in the
  values (vintage `2025-10-10T14:30:00Z` < revision `2025-11-03T08:00:00Z`). It is
  absent from the graph.

## Finding 3 — no substrate can host these mutations either

Checked every example package across all five packs:

| Substrate | `modelRevisionDate` | `currentModelVersion` | `signatureTimestamp` | `hasEvidence` | inline `bindsRequirement` | `activityType` | results w/ `wasGeneratedBy` |
|---|---|---|---|---|---|---|---|
| morrison/cou1 | — | — | — | — | 0/1 | — | 0 / 3 |
| morrison/cou2 | — | — | — | — | 0/1 | — | **3 / 3** |
| nagaraja/cou1 | — | — | — | — | 0/1 | — | 0 / 6 |
| aero cou1 / cou2 | — | — | — | — | — | — | **0 results at all** |
| iso42001 hybrid/cou2 | — | ✓ | — | ✓ | — | — | — |

**Four of the seventeen MECHANICAL rules read structures that no encoding produced
by the project's own protocol ever instantiates** — W-EP-03, W-AR-04, W-CON-03 and
W-AR-03 (`bindsRequirement` is a bare IRI everywhere, so `requiredVerificationMethod`
has nothing to bind to; `activityType` appears nowhere).

This is a catalog-coverage finding and it outranks the recall number it was meant to
unblock. Measuring these four on enriched packages demonstrates the rules *work*, not
that they will ever *fire* on real evidence. It belongs in Ch4 regardless of what
Arm M measures, and it feeds v0.6: encodings should instantiate `wasGeneratedBy`
chains and inline their requirements. Scored per the Decision Record's addendum B
(commit `fad31cf5`): the gate evaluates on the full battery, and the as-encoded vs
enrichment-required split is reported alongside as the ecological-validity result.

## Finding 4 — the assessment stack order differs from what Phase 2.5a §1.3 assumed

Actual order in `check.run_structured`
([commands/check.py:130-215](src/uofa_cli/commands/check.py)):

1. **C2 SHACL** — `run_shacl_multi`
2. **C1 Integrity** — `verify_file` — *before the rule engine, not after*
3. **C2.5 Derivation pre-pass** — SPARQL CONSTRUCT; may hand C3 an
   `enriched_package_path` **instead of the mutant on disk**
4. **C3 Rules** — Jena, on `effective_package`

§1.3 guessed "SHACL → rules → signature". Both corrections matter for the
`caught_by` attribution: signature verification is second, and there is a fourth
layer the spec does not mention. Verified inert for this work — `vv40`,
`nasa-7009b` and `core` declare no `derivations` key — but `caught_by` needs a
`derivations` value and the report must state the pre-pass was a no-op, or a reader
cannot tell whether C3 saw the mutant.

**This triggers Phase 2.5a §4.4** (stack order differs from what the manuscript
describes → report before writing the attribution). Ch3's description should be
checked against this order.

## Finding 5 — the issuer path refuses to sign mutants

`package_policy.sign_package` calls `assert_issuable(doc)`, and `is_synthetic`
([package_policy.py:52-64](src/uofa_cli/package_policy.py)) returns True for
`synthetic: true`. `uofa verify` refuses such packages outright (exit 2).

So **MUT-INT-02 as drafted — re-sign after mutation, to model a
fraudulent-but-valid package — cannot be built** while mutants are honestly marked
synthetic. That is not a gap to engineer around; it is a second instance of Phase
2.5a §1.3 item 4's positive architectural claim: *the production signing path cannot
be used to produce a fraudulent-but-valid package.* Reported as a finding.
Consequences carried into the design: mutants stay marked synthetic, signature-family
operators mutate already-signed substrate bytes, and the walkthrough uses
`uofa check` / `uofa detect` — never `uofa verify` — on a mutant.

## Coverage statement (addendum 2)

**Searched.** All 180 `w-ep-03` packages parsed and quantified for the
`wasGeneratedBy` chain and undefined-term dataset placement; three read field by
field. `spec/context/v0.5.jsonld` for the six comparison properties. Every
`*.jsonld` example across `packs/{vv40,nasa-7009b,iso42001,surrogate}/examples/`
for the seven preconditions in Finding 3. `commands/check.py:130-215` read for the
stack order. `packs/{vv40,nasa-7009b,core,surrogate}/pack.json` for `derivations`
declarations. `package_policy.py` for `is_synthetic` / `assert_issuable`.
`rdflib` 7.4.0 confirmed to ship `compare.to_isomorphic` / `graph_diff`.

**NOT verified.** No mutation was performed and no rule was re-run; Findings 1-3 are
from source and corpus inspection. Finding 3's claim is about *these* packs — a
substrate outside the repository could instantiate the missing structures. The
`iso42001` hybrid examples carry `currentModelVersion` and `hasEvidence` and were
**not** evaluated as mutation substrates, being outside Phase 2.5a's declared
three-substrate scope; if the enrichment cost proves high they are worth a look.

---

# ADDENDUM 1 — re-investigated against parent spec v2.0

## Correction first: Phase 3 did run, and the Tier-1 gate passed

The original finding stated that the Phase 3 production run "never fired" and that
Stages 3-5 have zero output artifacts. **That is wrong.** Two mistakes compounded:
I believed `dev/build/` was gitignored (it is force-tracked —
`.gitignore:41-43`), and I sourced the stage status from
`PHASE3_STATUS_REPORT.md`, whose own header says it is a point-in-time report
carrying a 2026-07-17 update — three days before the work completed.

The committed record:

| Stage | Status | Artifact | Commit |
|---|---|---|---|
| 2 — full-corpus judgment | **COMPLETE** | `production/run-1/judgments_{A,B,C}.jsonl`, 4,556/4,556 judged by all three | `30e02b7e`, 2026-07-19 |
| 3 — triage | **COMPLETE** | `triage/triage_summary.json`, `adjudication_queue.csv`, `tier1_real_gap_candidates.csv` | `e3d9bed8`, 2026-07-19 |
| 4 — author adjudication | **prepared, not performed** | `triage/adjudication_worksheet.csv` + `ADJUDICATION_INSTRUCTIONS.md` for the 21-case queue, plus a 50-case CONVERGENT spot-check | `943048e4`, `4205f293`, 2026-07-20 |
| 5 — formalization / case-study re-run | not started | — | — |

Substance, from `STAGE3_RESULT.md` (2026-07-20):

- CONVERGENT **4,535 (99.5%)**; DISAGREEMENT **21 (0.5%)** — against the pilot's 9%
  projection of ~410. Stage 4 is *"a single sitting rather than a multi-week
  effort."*
- **All 6 of 6 Tier-1 candidates supported** (commit subject `e3d9bed8`);
  `tier1_real_gap_candidates.csv` shows unanimous REAL-GAP verdicts at confidences
  0.80-1.00.
- Gate 7 was resolved on the **RELAX** path with a full decision record
  (`GATE7_DECISION.md`, 2026-06-10) that includes the amended clause text, a drafted
  Ch3 disclosure paragraph, and a named residual risk.

**What this changes.** The removal-list entry below is unchanged in *kind* — v2.0's
GATE-H3 contains no Tier-1 clause, so the author has still taken the judge leg out
of H3 — but it is no longer "a leg with no number." It is a leg with a **positive
result the author chose not to gate on**, which is a much better position: it can
be relabelled as secondary characterization per A2 §1 ("they may remain as
clearly-labeled secondary characterization") and reported as the v0.6 catalog
increment, rather than deleted. The manuscript's `[PLACEHOLDER, expected mid-July]`
at ¶460 is fillable today from committed artifacts.

**What this does not change.** Everything in the sections below that concerns the
*mechanical* leg — GATE-H3's per-class arithmetic, the MECHANICAL/JUDGMENT
inversion, the version-mismatch, and P25-A — is independent of Phase 3 and stands.

## What v2.0 settled

The original escalation asked the author to choose among three options for H3's
gap-validation leg. **v2.0 chose, and the choice is Option A.** GATE-H3 (§0.1)
defines H3 entirely in terms of injected-flaw detection rates per label class:

> MECHANICAL-class detection gated at **≥95%** (the holdout supports it);
> JUDGMENT-class and overall gated at **≥80%**. False positives **<10%**, per
> class, measured by A3.

There is no Tier-1 ≥3-of-6 adjudication gate anywhere in v2.0, and A2 §1 now says
plainly to remove judge output from the H3 support chain. **The judge leg is gone
by author decision.** §3's removal list is therefore executed, not pending, and the
relabel and prose-defect lists below stand unchanged and should proceed.

## What replaced it: GATE-H3 is not met, and the class that fails is the one v2.0 assumed safe

**Correction to my earlier coverage statement.** I wrote that the Phase 2/2.5
outcome artifacts were gitignored and therefore unopened. That was wrong:
`.gitignore:41-43` ignores `dev/build/*` but **force-tracks
`dev/build/adversarial/` and `dev/build/phase2_5/`**. 10,103 Phase 2 files and 113
Phase 2.5 files are committed, including per-pattern `summary.csv` at three catalog
versions. I have now read them and computed per-label-class recall against my INV-1
partition.

| Catalog version | Artifact | MECHANICAL recall | JUDGMENT recall | Overall |
|---|---|---|---|---|
| M5 baseline v0.5.7 | `dev/build/adversarial/phase2/2026-04-26/coverage/summary.csv` | **0.5908** (1295/2192) | **0.9368** (1008/1076) | 0.7343 (the manuscript's 73.4%) |
| holdout v0.5.13 | `dev/build/phase2_5/shared/per_iter_outcomes/holdout_v0513/summary.csv` | **0.7260** (159/219) | **0.9160** (109/119) | **0.7619** (288/378) |
| holdout v0.5.15.1 | `dev/build/phase2_5/shared/per_iter_outcomes/holdout_v0515/summary.csv` | **no CE rows** | **no CE rows** | **not measured** |

**Against GATE-H3, using the best available measurement (v0.5.13):**

| Gate | Required | Measured | Verdict |
|---|---|---|---|
| MECHANICAL detection | ≥95% | **72.6%** | **FAILS by 22 points** |
| JUDGMENT detection | ≥80% | **91.6%** | passes |
| Overall detection | ≥80% | **76.2%** | **FAILS by 4 points** |
| False positives, MECHANICAL | <10% | 9 rule-firings over the 171-package v0.5.15.1 holdout | passes |
| False positives, JUDGMENT | <10% | 1 rule-firing | passes |

**The inversion is the finding.** GATE-H3's parenthetical — *"MECHANICAL-class
detection gated at ≥95% (the holdout supports it)"* — is the one premise the data
contradicts. The MECHANICAL class is the **worse**-performing class on recall, at
both measured versions, by 19-21 points. The JUDGMENT class comfortably clears the
gate it was given.

## Why MECHANICAL underperforms — and why it is fixable

Not a rule defect. Every MECHANICAL zero is a **generation** artifact:

| Pattern | v0.5.7 | v0.5.13 | Why it scores 0 |
|---|---|---|---|
| W-EP-03 | 0.000 | 0.000 | Needs `dataVintage < modelRevisionDate` as two comparably-typed literals. Jena's `lessThan` silently fails on a mistyped literal — **the exact caveat flagged at INV-1 §3 row 3, now empirically corroborated.** |
| W-CON-03 | 0.000 | 0.000 | Same, `greaterThan` on two timestamps |
| W-AR-04 | 0.000 | 0.000 | Needs two `modelVersion` strings that differ; the generator writes them consistently |
| W-SI-02 | 0.000 | recovered | Fires on absent `bindsRequirement` / `hasValidationResult` — both **ProfileMinimal-mandatory**, so a package exhibiting the flaw fails SHACL and the generator retries it away |
| W-AL-02 | 0.000 | recovered | fixed by the v0.5.9 schema-aligned rewrite |
| W-ON-01, W-SI-01 | not_measurable | not_measurable | 0 CE rows at both versions; the manuscript's "two structurally untestable patterns" (¶472) |

The pattern is consistent: **the MECHANICAL class is precisely where an LLM
generator behind a SHACL gate cannot produce the flaw.** Delete-a-field and
set-a-value defects either get validated away or get written with the wrong
literal type.

**This is what makes INV-11's deterministic mutator load-bearing rather than
optional.** A mutator that deletes `comparedAgainst`, or writes a correctly-typed
`dataVintage` one day before `modelRevisionDate`, produces the flaw by
construction — for exactly the 15 MECHANICAL patterns, and exactly the five that
currently score zero. GATE-H3's MECHANICAL ≥95% is **unreachable** with the current
generator and **reachable by construction** with the mutator. See INV-11 addendum.

## A2 §3's new null-control standard, and a version-mismatch it exposes

v2.0 adds a requirement that did not exist in v1.1:

> "Apply the H2 null-control standard throughout: every headline metric reported
> beside a null that a non-reading system would achieve, so no H3 number repeats
> the detection-at-ceiling failure H2 caught in itself."

Two consequences.

**(a) The natural null for injected-flaw detection is the always-fires system**,
which scores recall 1.000 and FP 1.000. So the null-control discipline for H3
reduces to reporting recall **beside** the false-positive rate from the same run,
per class. That is cheap and mostly already designed in.

**(b) It exposes a pairing the manuscript currently makes and should not.** The
headline pair "CE recall 73.4%, NC clean 97.1%" pairs a **v0.5.7** recall with a
**v0.5.15.1** specificity. `PHASE2_5_STATUS_REPORT.md:34` (deviation D1) says so
directly: *"CE recall (68.6% baseline) and gap-probe were validated
separately/earlier and not re-measured at v0.5.15.1."* Reporting them side by side
as a recall/precision pair for one catalog is a version-skew error of the same
family as the one H2 caught in itself — and A2 §3's own standard forbids it.

The two figures also move in opposite directions across the refinement, which is
the whole point: MECHANICAL recall rose 0.59 → 0.73 while NC firings fell to near
zero. That is a real and reportable trade, but it needs one measurement at one
version to state.

## The single measurement that unblocks rank 1

**P25-A — the full-battery holdout on v0.5.15.1** (CE recall + gap-probe +
interaction, not just NC). `PHASE2_5_STATUS_REPORT.md:46-48` already scopes it:
**3-5h active plus analysis, API key, ~$30-50**, and calls it *"the highest-value
remaining 2.5 item."*

It is now more than that. Without it:
- GATE-H3 cannot be evaluated at the shipped catalog version at all;
- A2 §3's null-control standard cannot be honoured, because recall and FP come
  from different versions;
- A1's done-gate ("no unscoped metric statement in Ch3") has no per-class numbers
  at the shipped version to scope to;
- D7's Demonstrated rung has no injected-flaw detection figure at v0.5.15.1.

Ranks 1 and 2 of v2.0's priority ordering both sit on it. **It should be scheduled
before A2's text is written**, not after, or the Ch3/Ch4 numbers get written twice.

If P25-A runs *after* the INV-11 mutator lands, it measures the MECHANICAL class on
deterministically injected flaws — which is both what GATE-H3 needs and what the
committee's letter literally described. That ordering is worth the extra few hours.

## Escalation (revised)

**Not a request to choose an option — a request to accept a sequencing
consequence.** GATE-H3 as written is not met by any committed measurement, and the
MECHANICAL ≥95% clause rests on a parenthetical the data contradicts. Three ways
forward, and they are not mutually exclusive:

| # | Action | Cost | Effect |
|---|---|---|---|
| 1 | **Run P25-A at v0.5.15.1** | 3-5h + ~$50 | Produces the per-class numbers GATE-H3 is written against. Necessary in every scenario. |
| 2 | **Build the INV-11 mutator first, then run P25-A** | +4-6h | Removes the generation artifact that depresses MECHANICAL recall. The only route by which ≥95% is plausibly reachable. |
| 3 | **Re-scope GATE-H3's MECHANICAL clause** to the sub-class that is measurable (excluding W-ON-01 and W-SI-01, permanently not_measurable under any generator, and disclosing them under A5's "not measurable" rule) | text only | Honest, and needed regardless — two of the fifteen MECHANICAL patterns have never had a CE row at any version. |

**Recommendation put to the author, not taken:** 2 then 1, with 3 in the text
either way. Note that GATE-H3 is author-set and disclosed in A4 (§0.1), so revising
the ≥95% figure before measurement is legitimate — but revising it *after* seeing
P25-A's result would be exactly the retroactive thresholding v2.0's GATE-H2
rationale condemns. **Decide the number before P25-A runs.**

## Coverage statement (addendum)

**Searched.** `.gitignore:33-46` for the force-tracking rules; `git ls-files
dev/build/adversarial/phase2/` (10,103 files) and `dev/build/phase2_5/` (113).
Read and parsed three committed `summary.csv` files with `csv.DictReader`,
aggregating `confirm_existing_hits / confirm_existing_count` and
`negative_control_firings` by INV-1 label class. `PHASE2_5_STATUS_REPORT.md` lines
13, 23, 26, 34, 36, 46-48, 62, 70 for the lock roster, validation scope, deviations
and the P25-A costing. v2.0 §0.1, A2, A5, A1, D7 read in full.

**NOT verified.** P25-A was not run — no measurement was taken here, only existing
committed measurements re-aggregated. The literal-typing explanation for the three
value-comparison zeros (W-EP-03, W-CON-03, W-AR-04) is **HYPOTHESIS**: it is
consistent with the rule bodies, with Jena's silent-failure behaviour on mistyped
literals, and with the pattern of which rules score zero, but no failing package was
opened to confirm it. Opening two or three `dev/build/adversarial/phase2/2026-04-26/confirm_existing/…w-ep-03…`
packages and checking the `dataVintage` literal's datatype would settle it in about
15 minutes, and it is worth doing before the mutator is specified.

---

# ORIGINAL FINDING (v1.1-based, retained for the record)

## Headline

H3's support chain has **two legs**, and the manuscript's own amendment introduced
the second one:

| Leg | Source class | Status |
|---|---|---|
| **CE recall ≥80%** — confirm-existing specs produce COV-HIT / COV-HIT-PLUS | **(b) deterministic rule output** — no judge anywhere | measured: 73.4% (baseline catalog) |
| **Tier-1 gap adjudication ≥3 of 6** — candidate gaps confirmed as REAL-GAP | **(c) judge output** + author adjudication | **pending; the production run never fired** |

The second leg is the A2 problem, and it is sharper than "judges appear in the
chain": the judge-derived leg **replaced** the original manifest-derived
gap-validation clause because that clause turned out to be unsatisfiable by the
emitted data. Removing the judges does not restore the original H3; it leaves H3's
gap-validation half with nothing behind it. That is an author decision, not a
rewrite.

## 1. The H3 chain as currently written

Source: `Praxis/Writing/Drafts/UofA Praxis Draft 072726.docx` (2026-07-26, the most
recent full draft), text extracted with `python-docx`; paragraph indices are into
that extraction and are given so the author can locate each sentence.

| # | Location | Sentence / number | Source class |
|---|---|---|---|
| H3-1 | §1.6, ¶107 | *"H3 is supported if ≥80% of confirmed present specifications generates either COV-HIT or COV-HIT-PLUS, and at least one COV-MISS pattern from gap-probing specifications validates against the packages provided by Morrison and Nagaraja."* | **(b)** both clauses — COV-* labels are rule-engine outputs |
| H3-2 | §3.7, ¶382 | *"H3 is evaluated directly from these outputs… at least 80% of confirm-existing specifications produce COV-HIT or COV-HIT-PLUS, and at least one COV-MISS from the gap-probe battery validates against the Morrison and Nagaraja packages."* | **(b)** |
| H3-3 | §4.4 opener, ¶447 | *"…gap validation is scored through the Tier 1 candidate adjudication gate (≥3 of 6 confirmed)."* | **(c)** — this is the amendment that introduces judges into H3 |
| H3-4 | §4.4.1, ¶450 | 4,605 outcome rows; CE 4,005 / gap-probe 330 / NC 180 / interaction 90; **CE recall 73.4%**; NC precision 0.0% (176/180); 100% HIT-PLUS; GEN-INVALID 8.3%; cost $386.49; catalog v0.5.7 | **(b)** + **(a)** (row counts from the batch manifest) |
| H3-5 | §4.4.2, ¶454 | NC clean-rate trajectory 0% → 40.3% → 60.8% → 97.2% → **97.1% on fresh holdout (166/171, 180-package holdout)**; 7 rules locked; CE recall 68.6% at v0.5.13 vs 73.4% baseline | **(b)** |
| H3-6 | §4.4.3, ¶457 | Judge calibration: GPT-5.4 96.7%, Gemini 2.5 Pro 86.7%, Llama 4 Maverick 83.3%, arbiter Mistral 83.3%; pairwise κ 0.838/0.879/0.875; Fleiss 0.863; per-class UNCERTAIN gate A 80% / B 20% / C 0% | **(c)** — but instrument characterisation, not an H3 number (see §3) |
| H3-7 | §4.4.4, ¶460 | `[PLACEHOLDER, expected mid-July]` full-corpus judgment, triage distribution, author adjudication, **six Tier-1 candidates scored against the ≥3-of-6 gate** | **(c)** — the H3-bearing judge output |
| H3-8 | Ch4 scoring table, T14.R3 | *"H3 (as amended…) \| CE recall 73.4% (baseline catalog); **Tier 1 adjudication pending** \| [pending]"* | mixed **(b)** + **(c)** |

## 2. Provenance verdict on the mechanical leg — it is clean

This is the good news and it should be led with in A2.

The COV-* classification that produces every (b) number involves **no judge and no
model**. `_classify()` takes `(coverage_intent, target_weakener, firings,
package_exists)` and returns an outcome class by pure comparison
([adversarial/classifier.py:229-273](src/uofa_cli/adversarial/classifier.py)):

- `target_fired = bool(target_weakener and target_weakener in fired)` — the target
  comes from the spec YAML's `target.weakener` field (the manifest), the firings
  come from the rule engine.
- Firings are obtained by running the real CLI as a subprocess:
  `python -m uofa_cli rules --pack <p> <package>`
  ([classifier.py:206-211](src/uofa_cli/adversarial/classifier.py)).
- Negative controls: `if not fired: COV-CLEAN-CORRECT else COV-CLEAN-WRONG`. No
  interpretation layer.

The spec YAMLs are the manifest: e.g.
[dev/specs/confirm_existing/w-ep-01.yaml](dev/specs/confirm_existing/w-ep-01.yaml)
declares `target.weakener: W-EP-01`, `coverage_intent: confirm_existing`. 23
confirm-existing specs, 23 gap-probe, 10 negative-control, 7 interaction, 30
paraphrasing, 11 cross-pack, 9 quality-benchmark.

**One caveat A2 must state honestly and cannot skip.** The *packages* are
LLM-generated, not deterministically mutated: `generation.model: claude-sonnet-4-6`
in every spec, and the generator calls an LLM
([adversarial/generator.py:106-127, 265, 517-540](src/uofa_cli/adversarial/generator.py)).
So the pipeline is "declare the target flaw → have a model write a package
exhibiting it → check mechanically whether the rule caught it." The *label* is
manifest-derived; the *stimulus* is model-authored. That is a defensible and
common design, but it is not literally the professors' *"start with a perfect
evidence package and systematically inject known flaws."* A2's mapping table should
say so in one sentence rather than let a reader assume deterministic mutation. See
INV-11 for what a literal deterministic injector would cost.

## 3. The three lists

### Removal list — judge-derived numbers currently in the H3 chain

| Item | Location | Note |
|---|---|---|
| **Tier-1 ≥3-of-6 adjudication gate** | ¶447, ¶460, T14.R3 | The only judge-derived H3 support. **It has no number.** Escalation below. |

Nothing else needs removing, because nothing else got produced.
[PHASE3_STATUS_REPORT.md:8,24-28](PHASE3_STATUS_REPORT.md) records that Stage 2 ran
only as a **100-case stratified pilot** (the 4,556-case production run was built,
scheduled, and *held* pending the gate-7 decision), and that **Stages 3-5 have zero
output artifacts** — "triage, adjudication, agreement statistics, Tier-1 verdicts,
formalized rules, the case-study delta, and the ANOVA do not exist on disk." The
report names the ≥3-of-6 gate as *"entirely unevaluated and structurally at risk…
the single biggest threat to the praxis claim."*

### Relabel list — judge output that legitimately stays, reframed as screening

| Item | Location | Why it stays |
|---|---|---|
| Judge-ensemble calibration numbers (per-judge accuracy, pairwise κ, Fleiss 0.863) | ¶457 (§4.4.3) | Characterises the instrument, not the hypothesis. Under A2 this is "secondary characterization, clearly labeled." |
| §3.9 architecture description (six-verdict taxonomy, cross-family selection, circularity defence, arbiter) | ¶389-404 | Methodology of an apparatus that screens candidate gaps. |
| gap_probe REAL-GAP adjudication as a **stage-5 role** | §3.9.6 (¶402) | The item is explicit that this role is *different in kind* from H3 ground truth and must not be swept away with it. Keep it; label it as candidate-gap triage feeding the v0.6 increment, not as H3 evidence. |
| Realism screening of generated cases | §3.9 generally | Exactly the role A2 assigns to judges. |

**The distinction that matters:** Stage 5's judge role decides *what enters the
next catalog version*. The Tier-1 gate decides *whether H3 is supported*. Same
machinery, different load. A2 must sever the second without touching the first.

### Prose-defect list — judges described in ground-truth language where the number is not judge-derived

| # | Location | Text | Defect |
|---|---|---|---|
| P1 | ¶316 (§3.1 roadmap) | *"…the measurements, the adversarial campaign, **the LLM-as-judge ensemble**, and the validity threats…"* | Lists the judge ensemble as a co-equal pillar of the evaluation design. A reader arrives at Ch4 expecting judge output to carry results. One clause fix. |
| P2 | ¶311 (RQ3) | *"RQ3 evaluates the coverage of the weakener catalog using adversarial testing, closed-loop refinement, **and expert adjudication**"* | Puts adjudication into the research question itself. If the Tier-1 leg is dropped, RQ3's wording must change too — and RQ wording changes are Turman-review territory. |
| P3 | ¶420 (§3.10 validity threats) | *"**The LLM-as-judge methodology remains the principal validity limitation of the praxis.**"* | The most consequential framing defect. It concedes the committee's exact objection as the headline limitation — while the numbers that actually support H3 have no judge in them. Under A2 this sentence should be scoped to the catalog-refinement/formalization arm, not to the praxis. |
| P4 | ¶406 (§3.10 opener) | *"…including SHACL conformance, extraction F1, catalog coverage, **judge verdict distributions, and inter-rater agreement statistics**."* | Enumerates judge statistics among the praxis's quantitative measurements without saying which hypothesis each serves. |
| P5 | ¶447 (§4.4 opener) | *"…**an LLM-judge ensemble that adjudicates candidate gaps**"* presented as part of "the full campaign arc" that "scores H3" | Directly attributes H3 scoring to the judge arc. This is the sentence A2 rewrites first. |

P1-P5 are framing fixes, cheap, and independent of the escalation below — they
should proceed regardless of how the author rules.

## 4. Escalation

**Criterion:** *"any H3-supporting number turns out to have judge-derived
provenance with no manifest-derived equivalent available."* **Triggered**, in an
unusual form: the judge-derived leg has no number *yet*, and the manifest-derived
equivalent it replaced is **unsatisfiable**.

The chain of events, from the manuscript's own text:

1. Original H3 (¶107, ¶382) required *"at least one **COV-MISS** from the gap-probe
   battery validates against the Morrison and Nagaraja packages."*
2. The battery emitted **no COV-MISS rows at all**. ¶447: *"the dependent-measure
   outcome classes are restated in the vocabulary the battery actually emits
   (COV-HIT-PLUS / COV-WRONG / COV-CLEAN-WRONG / GEN-INVALID; **no COV-HIT or
   COV-MISS rows occur**)."* This is consistent with the rule: gap_probe returns
   `COV-MISS` only when *nothing* fires, and with FPR near 100% at v0.5.7 something
   always fired ([classifier.py:253-256](src/uofa_cli/adversarial/classifier.py);
   NC precision 0.0%, ¶450).
3. The amendment therefore rerouted gap validation to the **Tier-1 adjudication
   gate** — i.e. to the judges.
4. The Tier-1 gate never ran.

So H3 today is: leg 1 measured at 73.4% (below its own 80% gate, on the *baseline*
catalog); leg 2 pending on an apparatus that was held.

**Author decisions required. Three options, none of which I should pick:**

| Option | What H3 becomes | Cost | Risk |
|---|---|---|---|
| **A. Narrow H3 to the detection leg** | Drop gap-validation from H3 entirely; H3 = "≥80% of confirm-existing specs produce COV-HIT/HIT-PLUS." Gap discovery becomes reported future work, judges relabelled to screening. | Text only. Aligns exactly with must-have 1 and with A1's MECHANICAL class. | 73.4% baseline is below 80%; needs the re-baseline run on the refined catalog (see below) or an honest "not supported at the pre-registered gate" — which is a legitimate and defensible result. |
| **B. Re-derive a manifest-based gap criterion** | Replace COV-MISS with a criterion the battery can emit — e.g. gap-probe rows classified COV-WRONG where the fired pattern is not the probe's target, validated against Morrison/Nagaraja by hand. | Analysis of existing `outcomes.csv`; no re-run, no judges. | Changing a pre-registered dependent measure post hoc; must be disclosed in A4 alongside the original. |
| **C. Run Stage 2-5** | Keep the amended H3 as written. | ~$262-440, 5 days wall-clock, plus author adjudication that cannot be delegated ([PHASE3_STATUS_REPORT.md:24-25,58-65](PHASE3_STATUS_REPORT.md)). | Re-introduces exactly the LLM-as-judge dependence the committee asked to remove. Also inherits the gate-7 post-hoc relaxation (deviation D8), which the status report itself calls *"the deviation most open to committee challenge."* |

**Recommendation to put to the author, not a decision taken:** Option A, with the
73.4%/68.6% recall gap disclosed and the re-baseline run on the refined catalog
executed if calendar allows — `PHASE2_5_STATUS_REPORT.md:62` records that
v0.5.15.1 never re-measured CE recall, so the refined catalog's recall is
**unknown**, not known-worse. That single re-run is the cheapest thing that could
move H3 from "not supported" to a real result, and it involves no judges at all.

## Coverage statement

**Searched.** Manuscript: `UofA Praxis Draft 072726.docx` extracted in full via
`python-docx` (544 paragraphs + 15 tables → 655 lines), then grepped for `H3`,
`Hypothesis 3`, `judge`, `LLM-as-a-judge`, `adjudicat`, `COV-HIT`, `COV-MISS`,
`recall`, `73.4`, `97.1`, `F1`. In-repo manuscript sources: `docs/ch3-methods-principles.md`,
`docs/ch4-h2-section.md` (H2, not H3). Phase 3 record: `PHASE3_STATUS_REPORT.md`
read for stage status, gate values and the deviation log; `PHASE2_STATUS_REPORT.md`
and `PHASE2_5_STATUS_REPORT.md` for the 73.4% / 68.6% provenance. Code: the full
outcome classifier (`adversarial/classifier.py`, docstring + `_classify` +
`_run_rules` read directly), the generator's LLM dispatch, the spec YAML schema and
directory census (`dev/specs/*`, 113 specs), the judge subsystem inventory
(`adversarial/judge/`, 20 modules; `triage.py` and `runner.py` headers read).
Repo-wide grep for `H3\b` across `docs/`, `studies/`, `site/src`.

**Search terms derived from the question's own definition** (judge output
functioning as ground truth): `target_weakener`, `coverage_intent`, `_classify`,
`REAL-GAP`, `Tier 1`, `≥3 of 6`, `adjudicat`, `calibration`, `verdict` — i.e. both
the mechanical path and the judge path were traced independently, rather than
searching only where judges were known to appear.

**NOT searched / not verified.**
- **Older manuscript drafts were not checked.** If the committee holds a copy of an
  earlier draft (e.g. `UofA_Praxis_ Edited_Working Draft.docx`, 2026-07-10), its H3
  wording may differ and would need the same pass.
- `docs/` and `studies/` were searched for H3, but **no `studies/` directory
  contains H3 artifacts** — the Phase 2/2.5 outputs live under `dev/build/adversarial/`
  (gitignored) rather than under `studies/`. The 4,605-row `outcomes.csv` behind
  ¶450 was therefore **not opened**; its numbers are traced to the two status
  reports, which are committed, rather than to the CSV. If A4 needs the CSV itself,
  its retention status should be checked — a gitignored results directory is a
  reproducibility gap independent of this item.
- The 100-case pilot artifacts (`dev/build/adversarial/pilot/2026-05-05/`) were not
  read; the pilot is not in the H3 chain.
- No judge was run and no calibration number was re-derived.
