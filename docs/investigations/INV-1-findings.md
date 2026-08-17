# INV-1 — MECHANICAL/JUDGMENT classification of all 23 patterns

Status: **CLOSED by author ruling.** Both escalations are resolved; the ruled
partition supersedes the §3 table's own totals.
Date: 2026-08-16 (v2.0 addendum, then closed by the Decision Record)
Feeds: parent A1, A2, A5, B1 (`uofa verify-labels`), D7, and **GATE-H3**

---

# RULED PARTITION — read this before §3

`docs/UofA_Decision_Record_2026-08-16.md`, committed alone at **`fad31cf5`**, rules
all three open questions this file raised. **The partition below is authoritative
and is what the Phase 2.5a operator registry reads.** §3's per-pattern rationales
stand as the evidence; only the class assignments for W-PROV-01 and W-AR-03, and the
totals, are superseded.

| Class | n | Patterns |
|---|---|---|
| **MECHANICAL** | **17** | W-EP-01/02/03, W-AL-01/02, W-ON-01/02, W-AR-03/04/05, W-SI-01/02, W-CON-02/03/04/05, **W-PROV-01** |
| **JUDGMENT** | **4** | W-EP-04, W-AR-01, W-AR-02, W-CON-01 |
| Excluded, reported separately as composition results | 2 | COMPOUND-01, COMPOUND-03 |

**GATE-H3's MECHANICAL denominator is 17**, over the 21 base patterns.

| This file said | Ruling | Basis |
|---|---|---|
| W-PROV-01 **JUDGMENT** (§3 row 21) | **MECHANICAL** (ruling 4) | The operative criterion is re-derivability of the label as the rule exists at v0.5.15.1 — this file's Layer 1 — not input provenance. `isFoundationalEvidence` is a structural declaration |
| W-AR-03 **ambiguous**, both readings given (§4 E1) | **MECHANICAL** (addendum A) | Same criterion. Its comparison runs on declared package fields, so a script re-derives it. The missing `sh:in` vocabulary makes the rule *weaker, not human-dependent*; ruling 5 deferred the hardening, not the classification |
| COMPOUND-01 **unclassifiable**, three options offered (§4 E2) | **Excluded** (ruling 3) | Option 3 taken: label classes and gates scope to the 21 base patterns; compounds reported separately. `label_class=COMPOSITE` or null in the B1 schema |

**The criterion, stated once and reused verbatim in the A1 Ch3 text:**
`isFoundationalEvidence` is a *structural declaration* of the package as encoded;
`factorStatus` and `hasOffsetRationale` are *dispositional*. That is why W-PROV-01
and W-AR-03 are MECHANICAL while W-EP-04, W-AR-01, W-AR-02 and W-CON-01 are not.
The ruling is pattern-specific and does **not** generalize to the dispositional
four; the operator registry carries this rationale as data so the asymmetry is
auditable.

One consequence worth carrying into Ch3: **the ruling adopts Layer 1 of §2's
two-layer test as the operative one.** §2's Layer 2 analysis is not discarded — it
is what distinguishes structural declarations from dispositions, and it is the
reason the ruling can be pattern-specific rather than sweeping. Ch3 should present
the two layers as this file does and then name Layer 1 as the criterion
`label_class` encodes.

---

# ADDENDUM — re-investigated against parent spec v2.0

## The provisional table is carried forward verbatim, so the correction still applies

v2.0 §A1 clause 1 restates the provisional assignment **identically** to the R-spec
v0.1 table this finding tested:

> MECHANICAL = W-PROV-01, W-SI-01..02, W-CON-01..05 (where the rule is field
> comparison), W-AR-01..05 (where the rule is structural presence/absence);
> JUDGMENT = W-EP-01..04, W-AL-01..02, W-ON-01..02, COMPOUND-01, COMPOUND-03.

§5 of this finding stands unchanged: **that assignment is wrong on 13 of 23 rows**
when tested against rule logic, in the patterned way described there. Nothing in
v2.0 supplies new evidence bearing on the classification, and the classification is
therefore unrevised. The `label_class` values that ship must come from §3, not from
the provisional table.

## What changed: the partition is now load-bearing for a numeric gate

Under v1.1 the partition scoped κ and F1 statements. Under v2.0 it **sets the pass
mark**. GATE-H3 (§0.1):

> MECHANICAL-class detection gated at **≥95%**… JUDGMENT-class and overall gated at
> **≥80%**. False positives **<10%**, per class.

So every row in §3 now moves a threshold. Three consequences the author should see
before `label_class` is committed:

**1. The correction moves seven patterns into the ≥95% bucket.** W-EP-01/02/03,
W-AL-01/02 and W-ON-01/02 were provisionally JUDGMENT (gate ≥80%) and are
MECHANICAL on rule logic (gate ≥95%). That is the right classification, and it
raises the bar those seven must clear.

**2. It moves four out.** W-PROV-01, W-CON-01, W-AR-01 and W-AR-02 were
provisionally MECHANICAL and are JUDGMENT on rule logic — so they are gated at
≥80%, not ≥95%. This matters concretely: **W-PROV-01's measured recall is 0.672**
(M5 baseline), which fails ≥95% and also fails ≥80%. Under the provisional table it
would have been a MECHANICAL-class failure at the higher bar.

**3. The measured result inverts the gate's own premise.** GATE-H3 justifies the
≥95% MECHANICAL clause with "(the holdout supports it)". Aggregating the committed
per-pattern outcomes by this finding's partition:

| Catalog version | MECHANICAL | JUDGMENT |
|---|---|---|
| M5 baseline v0.5.7 | **0.5908** | **0.9368** |
| holdout v0.5.13 | **0.7260** | **0.9160** |

The MECHANICAL class is the *worse* performer at both versions. Full analysis,
per-pattern diagnosis, and the sequencing consequence are in
[INV-8's addendum](INV-8-findings.md); it is recorded there rather than duplicated
because it is H3's gate, not A1's.

**The empirical corroboration is worth noting here, though:** §3 row 3 flagged that
W-EP-03's `lessThan` needs comparably-typed literals and would silently fail
otherwise, and recommended a `verify-labels` determinism assertion. W-EP-03 scores
**0.000 recall at every measured version**, as do the other two value-comparison
rules (W-CON-03, W-AR-04). That is exactly the predicted failure signature.

## The two escalations, re-put with v2.0's stakes attached

Both are unchanged as questions. What changed is the cost of getting them wrong.

**E1 — W-AR-03.** Under v2.0 the choice decides whether W-AR-03 is gated at ≥95% or
≥80%. Its measured recall is **1.000** at M5 and **1.000** at v0.5.13, so it clears
either gate today and the decision is currently free. **Take it now, while it is
free** — committing `sh:in` vocabularies for `activityType` and
`requiredVerificationMethod` (~1h) resolves it to MECHANICAL on evidence rather
than on preference, and a decision taken before the measurement cannot be
retroactive thresholding later.

**E2 — COMPOUND-01.** Now materially more urgent. COMPOUND-01's recall is **1.000**
at M5 but **0.000** at the v0.5.13 holdout, and `PHASE2_5_STATUS_REPORT.md:23,36`
records it as the one rule left **unlocked** ("train recall 0.5714,
refinement-stuck", on a corpus dependency on the since-fixed W-EP-01 bug). Under
GATE-H3 it fails whichever class it lands in. Of the three options in §4:

- **Option 3 (exclude compounds from the partition and scope the gates to the 21
  base patterns) is now the recommended one**, and it should be paired with an A4
  disclosure of why. It is honest, it is stated once in Ch3, and it stops a rule
  with a known corpus dependency from deciding a hypothesis.
- Option 1 (per-instance class) remains the better long-term design and can follow
  later; it does not need to gate the defense.

## A1's done-gate is not currently reachable, for a reason outside A1

A1's done-gate is *"23 patterns classified and confirmed; verify-labels passes on
all three case-study bundles; no unscoped metric statement in Ch3."* The first two
clauses are reachable now — this finding supplies the classification, and §6
specifies the wrapper at 2-3h. The third is not: **there are no per-class detection
numbers at the shipped catalog version to scope Ch3's statements to**, because CE
recall was never re-measured at v0.5.15.1. A1 can be built and shipped; the Ch3
sentences it feeds wait on P25-A. See INV-8's addendum.

## Coverage statement (addendum)

**Searched.** v2.0 §0.1 (GATE-H2, GATE-H3), §A1 in full, §A2 clause 3, §A5's metrics
table, §D7's rung contents. Three committed per-pattern `summary.csv` artifacts
(M5 v0.5.7, holdout v0.5.13, holdout v0.5.15.1) parsed and aggregated by this
finding's partition. `PHASE2_5_STATUS_REPORT.md:13,23,36,62` for the lock roster and
COMPOUND-01's status.

**NOT changed.** No rule was re-read and no classification was revised; v2.0
contains no new evidence about rule logic. The two escalations remain open
questions for the author, not resolved ones.

---

# ORIGINAL FINDING (v1.1-based, retained for the record)

## 1. Catalog source of truth

| Question | Answer | Citation |
|---|---|---|
| Where does the catalog live? | **Both.** The pattern *set* is data (`patternIds` in a pack manifest); the pattern *semantics* are code (Jena forward-chaining rules). | [packs/core/pack.json:25-49](packs/core/pack.json), [packs/core/rules/uofa_weakener.rules](packs/core/rules/uofa_weakener.rules) |
| Which artifact is canonical at v0.5.15.1? | `packs/core/rules/uofa_weakener.rules` at tag `v0.5.15.1-phase2v3-shacl-threadsafe-and-sa-boolean` → commit `7716ebe4bf72c907b80e963772a6eb5aba2093d4`, 2026-04-29 11:15:52 −0700 | `git log -1 v0.5.15.1-phase2v3-shacl-threadsafe-and-sa-boolean` |
| Is HEAD's rule file the frozen one? | **Yes, semantically identical.** The only diff from the freeze tag to HEAD is one copyright line (`crediblesimulation.com` → `uofa.net`) in commit `8d1d42fd`. Zero rule-body changes. | `git diff v0.5.15.1-…..HEAD -- packs/core/rules/uofa_weakener.rules` |
| Is the count 23? | Yes. 21 `W-*` + `COMPOUND-01` + `COMPOUND-03`. `COMPOUND-02` is commented out ([rules:600-623](packs/core/rules/uofa_weakener.rules)) and excluded everywhere. | [pack.json:25-49](packs/core/pack.json); classifier's independent list [classifier.py:57-70](src/uofa_cli/adversarial/classifier.py) |

Other packs ship additional patterns (`W-NASA-01..06`, `W-SURR-01..03`, the ten
`W-EV-*`/`COMPOUND-EV-*` of `model-credibility`). **They are not part of the 23**
and are out of scope for A1 as written. Flag for the author: A1's manuscript text
should say "the 23 core patterns", not "the catalog", or the model-credibility
pack's ten rules inherit an unstated class.

## 2. The classification test has two layers, and they disagree

Applying the spec's definition literally produces a result that must be stated
carefully, because a careless reading makes all 23 MECHANICAL and a different
careless reading makes all 23 JUDGMENT.

**Layer 1 — rule evaluation over a pinned package.** Every one of the 23 rules is
a Jena `GenericRuleReasoner` (FORWARD_RETE) rule whose entire body is triple
matching, `noValue`, `notEqual`, `lessThan`/`greaterThan`, and `makeSkolem`. There
is no callout, no model, no human input, no per-case parameter. **At this layer all
23 are MECHANICAL and the re-derivation is one command.** This is the layer
`uofa verify-labels` operates on, and it is a real and defensible claim.

**Layer 2 — provenance of the input fields.** The spec's JUDGMENT clause bites
here: *"or an input that is itself an adjudication."* Some rules read fields that
are transcriptions of the source document (dates, version strings, published
factor levels); others read fields that record **the encoder's disposition about
the evidence** — `factorStatus`, `hasOffsetRationale`, `isFoundationalEvidence`,
`assuranceLevel`. A rule whose firing turns on one of those is author-dependent no
matter how deterministic the rule body is.

**The classification below is Layer 2**, because Layer 2 is what the committee's
question ("are the labels objective or author-dependent?") actually asks. Layer 1
is reported alongside it as the re-derivability guarantee.

That Morrison COU1's `hasOffsetRationale` was **added to the example package after
the fact**, specifically to change a rule's firing behaviour, is the clearest
available demonstration that Layer 2 is not a theoretical concern:
commit `5d75b48e` (2026-04-28) inserted an `OffsetRationale` node into
`packs/vv40/examples/nagaraja/cou1/uofa-nagaraja-cou1.jsonld` and the rule comment
at [rules:233-241](packs/core/rules/uofa_weakener.rules) states the purpose plainly.

## 3. The 23 rows

Line numbers are into `packs/core/rules/uofa_weakener.rules`.

| # | Pattern | Class | Rule artifact | Re-derivation entrypoint | Rationale (one sentence) | Edge-case notes |
|---|---|---|---|---|---|---|
| 1 | W-EP-01 | **MECHANICAL** | rules:36-49 | `uofa rules <pkg> --pack <p>` | Fires on structural absence of `prov:wasDerivedFrom` from an inline-typed Claim; no field read is a disposition. | The `(?claim rdf:type uofa:Claim)` guard added in Phase 2.5 is what makes it mechanical rather than vacuous — without it the rule fired on every NC (comment, rules:29-35). |
| 2 | W-EP-02 | **MECHANICAL** | rules:52-64 | same | `noValue(?result, prov:wasGeneratedBy)` — pure presence/absence. | — |
| 3 | W-EP-03 | **MECHANICAL** | rules:67-83 | same | `lessThan(dataVintage, modelRevisionDate)` compares two transcribed dates. | Determinism caveat, not a class change: Jena `lessThan` needs both literals typed comparably; a mistyped `xsd:string` date silently fails to fire. Worth a `verify-labels` assertion. |
| 4 | W-EP-04 | **JUDGMENT** | rules:86-100 | n/a | Requires `factorStatus 'not-assessed'` — deciding a factor is unassessed rather than assessed-at-a-low-level is the encoder's disposition. | The `greaterThan(?mrl, 2)` threshold is **catalog-fixed, not per-case**, so the threshold is not what makes this JUDGMENT; `factorStatus` is. If `modelRiskLevel` is itself assigned rather than transcribed (the corpus survey found risk level stated in ~2% of documents — [docs/real-corpus-supply-survey.md:149-151](docs/real-corpus-supply-survey.md)), that is a second judgment input. |
| 5 | W-AL-01 | **MECHANICAL** | rules:107-119 | same | `noValue(?result, uofa:hasUncertaintyQuantification)` — presence/absence of one property. | Strongest empirical support of any row: the raidex furnisher sets this property **only** from a genuine numeric stderr with no human in the loop ([furnishers/raidex.py:281-289](src/uofa_cli/furnishers/raidex.py)), and the cohort study exercises it over 427 results. |
| 6 | W-AL-02 | **MECHANICAL** | rules:135-147 | same | Two top-level booleans: `hasUncertaintyQuantification == true` and `noValue hasSensitivityAnalysis`. | The v0.5.9 rewrite is *why* it is mechanical; the predecessor matched a non-existent declared property and fired vacuously (comment, rules:122-134). |
| 7 | W-ON-01 | **MECHANICAL** | rules:154-165 | same | `noValue(?uofa, uofa:hasContextOfUse)` — a single absence check. | — |
| 8 | W-ON-02 | **MECHANICAL** | rules:168-181 | same | Two `noValue` checks on the COU node. | **Corpus-validity note, not a class change:** the Phase 2.5 NC regeneration inserts placeholder `ApplicabilityConstraint`/`OperatingEnvelope` stubs explicitly documented as "not substantively meaningful," purely to suppress this rule's `noValue` ([adversarial/skeleton.py:70-95](src/uofa_cli/adversarial/skeleton.py)). The label stays mechanically re-derivable; what it measures on that corpus is weaker than it looks. Flag for A4. |
| 9 | W-AR-01 | **JUDGMENT** | rules:197-213 | n/a | Guarded on `factorStatus ∉ {scoped-out, not-applicable}`, so the encoder's status assignment gates firing. | Do **not** classify the W-AR family as a block — see rows 12 and 13. The v0.5.12 guard was added precisely because status assignment was driving firings (comment, rules:189-196). |
| 10 | W-AR-02 | **JUDGMENT** | rules:242-259 (+ derive rule 225-231) | n/a | Suppressed by `hasOffsetRationale → refersToFactor`, an encoder-authored justification for accepting a shortfall. | The canonical demonstration: `5d75b48e` added the offset node to Nagaraja COU1 to stop the rule firing. Also reads `requiredLevel`/`achievedLevel`, which are transcriptions only where the source prints a per-factor table. |
| 11 | W-AR-03 | **AMBIGUOUS — see §4** | rules:264-280 | (contingent) | `notEqual(requiredVerificationMethod, activityType)` on two **unconstrained free-text strings**. | Neither property carries `sh:in` or any enumeration in the shapes ([uofa_shacl.ttl:469-475](packs/core/shapes/uofa_shacl.ttl)) or the context ([spec/context/v0.5.jsonld:232,258](spec/context/v0.5.jsonld)). |
| 12 | W-AR-04 | **MECHANICAL** | rules:285-301 | same | `notEqual(cfg.modelVersion, uofa.currentModelVersion)` — two transcribed version strings. | Same free-string caveat as W-AR-03 in principle, but version identifiers are copied from the record rather than chosen from a vocabulary, so the encoder is transcribing, not disposing. |
| 13 | W-AR-05 | **MECHANICAL** | rules:304-316 | same | `noValue(?result, uofa:comparedAgainst)` — one absence check. | This is the pattern the B2 demo is built around (skeleton-mode MVP); its mechanical status is what makes that demo honest. |
| 14 | W-SI-01 | **MECHANICAL** | rules:323-334 | same | `noValue(?uofa, uofa:signature)`; the field is tool-generated, never encoder-authored. | — |
| 15 | W-SI-02 | **MECHANICAL** | rules:337-348, 350-361 | same | Two rule bodies, one pattern id; both pure `noValue` on required bindings. | **Two rule blocks share one `patternId`.** `verify-labels` must key on `(patternId, affectedNode, description)`, not `patternId` alone, or the two firings collapse. |
| 16 | W-CON-01 | **JUDGMENT** | rules:388-407 | n/a | Guarded on `factorStatus ∉ {scoped-out, not-applicable, not-assessed}`. | The `not-assessed` exclusion was added at v0.5.14 from a holdout finding (comment, rules:376-387). Classifying W-CON as a block would be wrong: 01 is JUDGMENT, 02–05 are MECHANICAL. |
| 17 | W-CON-02 | **MECHANICAL** | rules:459-471 | same | Graph reachability: target of `referencesIdentifier` has neither `rdf:type` nor `schema:url`. | Uses `rdf:type` as a "defined locally" proxy for RETE-safety reasons (comment, rules:452-458). Deterministic, but the proxy is a modelling choice worth one sentence in Ch3. |
| 18 | W-CON-03 | **MECHANICAL** | rules:430-444 | same | `greaterThan(evidenceTimestamp, signatureTimestamp)` — one is tool-generated, one transcribed. | Same literal-typing caveat as W-EP-03. |
| 19 | W-CON-04 | **MECHANICAL** | rules:415-427 | same | `conformsToProfile == ProfileComplete` and `noValue hasSensitivityAnalysis`; the profile declaration is independently checkable against the SHACL profile shapes. | Deliberately narrow-scoped for v0.5 (comment, rules:409-414); the wider ProfileComplete checks live in SHACL, not here. |
| 20 | W-CON-05 | **MECHANICAL** | rules:484-496 | same | Existential graph check: no Evidence anywhere links to the declared activity via `prov:wasGeneratedBy`. | — |
| 21 | W-PROV-01 | **JUDGMENT** | rules:518-557 (5-rule chain) | n/a | The BFS closure is pure reachability, but the detector is **suppressed by `uofa:isFoundationalEvidence = true`**, an encoder marking that says "stop asking about this node." | **This reverses the R-spec's provisional assignment**, which listed W-PROV-01 as the flagship MECHANICAL pattern. Reading: a flag whose only function is to change a rule's verdict is an adjudication, however cheap it is to set. If the author rules that `isFoundationalEvidence` is a *structural* declaration (like `conformsToProfile`) rather than a disposition, this row moves to MECHANICAL — that is an author call, not an evidence question. |
| 22 | COMPOUND-01 | **PER-INSTANCE — see §4** | rules:573-598 | (contingent) | Fires on coexistence of any non-compound Critical and any non-compound High annotation; its class is the join of the two contributing patterns' classes. | Critical sources span both classes (W-EP-01 M, W-ON-01 M, W-AR-01 J, W-AR-02 J, W-PROV-01 J), so a single blanket class is not derivable from the rule. |
| 23 | COMPOUND-03 | **JUDGMENT** | rules:626-645 | n/a | Requires `assuranceLevel ≠ 'Low'`; the assurance level is an encoder assignment, and the rule additionally inherits the class of whichever Critical pattern triggered it. | — |

**Totals as investigated: 15 MECHANICAL · 6 JUDGMENT · 2 escalated.**
**Totals as ruled (authoritative): 17 MECHANICAL · 4 JUDGMENT, over 21 base
patterns** — see the RULED PARTITION section at the top of this file. W-PROV-01
(row 21) and W-AR-03 (row 11) move to MECHANICAL; COMPOUND-01 and COMPOUND-03 leave
the partition entirely. The rationales in the rows below are unchanged and remain
the evidence the ruling was taken against.

## 4. Escalations (spec stop condition: ambiguous after reading the code)

### E1 — W-AR-03: two defensible readings, no code fact settles it

*Reading A (MECHANICAL).* The rule body is `notEqual` on two package-resident
literals. Given a pinned bundle it re-derives deterministically. The encoder's
vocabulary choice is an *encoding* question, not a *labelling* question, and by
that logic every string field would make its rule JUDGMENT.

*Reading B (JUDGMENT).* Neither `requiredVerificationMethod` nor `activityType`
is constrained to any vocabulary — no `sh:in`, no enumeration, no normalisation.
The rule therefore fires on any string mismatch, including a synonym or a
capitalisation difference between two fields the same encoder wrote. "Did the
activity answer the requirement's method?" is prose interpretation being
performed by the encoder and then rubber-stamped by string inequality.

Both readings are presented rather than resolved, per the spec. **A cheap
disambiguator exists:** add `sh:in` enumerations for both properties. If the
author is willing to commit a controlled vocabulary, W-AR-03 becomes
unambiguously MECHANICAL and the total goes to 16/6/1.

### E2 — COMPOUND-01: not classifiable as one pattern

The rule's inputs are other rules' outputs, and those span both classes.
Three options, all author calls:
1. **Per-instance class** — emit `label_class` on the annotation, computed as the
   join of the two `escalationSource` annotations' classes. Most honest; costs a
   small change to the emitter, and the rule already materialises
   `uofa:escalationSource` for both parents (rules:594-595), so the data is there.
2. **Blanket JUDGMENT** — safe, but discards the case where two MECHANICAL
   Criticals coexist, which is exactly the injected-flaw territory A1 wants to
   claim.
3. **Exclude compounds from the partition** and scope κ/F1 to the 21 base
   patterns. Simplest; needs one sentence in Ch3.

COMPOUND-03 has the same inheritance issue but resolves to JUDGMENT anyway on
`assuranceLevel`, so only COMPOUND-01 is open.

## 5. Disagreement with the parent spec's provisional table

The R-spec's provisional assignment ([UofA_Committee_Response_Spec_v0_1.md:35-41])
is **wrong on 13 of 23 rows** when tested against rule logic, and wrong in a
patterned way: it appears to have been assigned by *uncertainty-category name*
(epistemic/aleatory/ontological sound judgmental; structural/consistency sound
mechanical) rather than by what the rules read.

| Family | Provisional | This finding | Why |
|---|---|---|---|
| W-EP-01..03 | JUDGMENT | **MECHANICAL** | Pure `noValue`/date-comparison bodies. W-EP-01 and W-EP-02 are among the simplest rules in the catalog. |
| W-EP-04 | JUDGMENT | JUDGMENT ✓ | Agrees, but for a different reason (`factorStatus`, not the category). |
| W-AL-01..02 | JUDGMENT | **MECHANICAL** | Both are presence/absence on top-level booleans. |
| W-ON-01..02 | JUDGMENT | **MECHANICAL** | Both are `noValue` on the COU. |
| W-PROV-01 | MECHANICAL | **JUDGMENT** | `isFoundationalEvidence` suppression flag. |
| W-SI-01..02 | MECHANICAL | MECHANICAL ✓ | |
| W-CON-01..05 | MECHANICAL "where field comparison" | **01 JUDGMENT, 02-05 MECHANICAL** | Split, as the parent spec anticipated. |
| W-AR-01..05 | MECHANICAL "where structural" | **01,02 JUDGMENT · 03 ambiguous · 04,05 MECHANICAL** | Split, as the parent spec anticipated. |
| COMPOUND-01/03 | JUDGMENT | **01 per-instance · 03 JUDGMENT** | |

Net effect on A1's argument: **it gets stronger, not weaker.** The provisional
table put the entire epistemic/aleatory/ontological block in the author-dependent
class; rule logic moves seven of those nine into the machine-re-derivable class.
The MECHANICAL class is 15 patterns, not 13, and it now contains W-AL-01 — the
one pattern with an at-scale external demonstration behind it (427 results,
`studies/cohort-2026-08`).

## 6. Re-derivation entrypoint (spec step 4)

**A single entrypoint already exists and covers all 23 patterns.** There is no
per-pattern entrypoint and none is needed.

```bash
uofa rules <package.jsonld> --pack <pack>
```

- Structured API: `uofa_cli.commands.rules.run_structured(args) -> RulesResult`
  ([commands/rules.py:1-7,44+](src/uofa_cli/commands/rules.py)). Returns typed
  firings, so `verify-labels` needs no stdout parsing.
- The adversarial classifier already does exactly this re-derivation, per package,
  as a subprocess ([classifier.py:206-226](src/uofa_cli/adversarial/classifier.py)),
  and classifies against a declared target with **zero** human or model input
  ([classifier.py:229-273](src/uofa_cli/adversarial/classifier.py)). That function
  is a working proof of the A1 claim and should be cited in Ch3.
- Whole-pipeline variant (adds C1 integrity + C2 SHACL):
  `uofa check <pkg>` → `commands.check.run_structured`.

### Smallest `uofa verify-labels` wrapper

No new inference code. The command is:

1. Load the pinned bundle manifest (list of package paths + expected findings).
2. For each package call `rules.run_structured` in-process.
3. Compare observed `(patternId, severity, affectedNode)` triples against the
   package's recorded `hasWeakener` annotations, **restricted to the MECHANICAL
   rows of §3**.
4. Exit non-zero on any mismatch; print the diff grouped by pattern.

Two implementation notes that will otherwise bite:
- **W-SI-02 emits two distinct findings under one `patternId`** (rules:337,350).
  Key comparisons on the annotation identity, not the pattern id.
- **COMPOUND-01/03 must be excluded or per-instance-classed** (E2) before the
  comparison, or every bundle containing one JUDGMENT Critical will report a
  spurious mismatch.

Estimated effort: **2-3h**, entirely plumbing, consistent with parent B1's 3-4h
for all of B1's items.

## 7. Coverage statement

**Searched.** All 23 rule bodies read end to end in
`packs/core/rules/uofa_weakener.rules` (645 lines, whole file). Pack manifest
`packs/core/pack.json`. Catalog enumerator `src/uofa_cli/commands/catalog.py`.
Independent pattern list in `src/uofa_cli/adversarial/classifier.py:57-70`. SHACL
shapes `packs/core/shapes/uofa_shacl.ttl` grepped for `activityType`,
`requiredVerificationMethod`, `sh:in`, `ProfileMinimal`, `ProfileComplete`.
JSON-LD context `spec/context/v0.5.jsonld` for the same properties. Git: tag
resolution for `v0.5.15.1-*`, and `git diff <tag>..HEAD` on the rules file, the
pack manifest, and the shapes. Repo-wide grep for `label_class`, `labelClass`,
`MECHANICAL`, `JUDGMENT` across `*.py`, `*.json`, `*.md`, `*.ttl` — **no existing
implementation found**, so this is a greenfield classification, not a
confirmation. Furnisher `src/uofa_cli/furnishers/raidex.py` for the W-AL-01
evidence. Commit `5d75b48e` diff for the W-AR-02 offset evidence.

**Search terms derived from the classification's own definition** (not from the
provisional table): `noValue`, `notEqual`, `lessThan`, `greaterThan`,
`makeSkolem`, `factorStatus`, `isFoundationalEvidence`, `hasOffsetRationale`,
`assuranceLevel`, `conformsToProfile`, `sh:in`.

**NOT searched.**
- The Jena engine's own evaluation semantics (`src/weakener-engine/`, Java) were
  not read. The classification assumes `GenericRuleReasoner` FORWARD_RETE is
  deterministic for a fixed input graph. That assumption is load-bearing for the
  Layer-1 claim and is *not* verified here. Two rule comments (rules:452-458,
  478-483) record past RETE ordering bugs, so the assumption has been violated
  before. **Recommend `verify-labels` include a same-input-twice determinism
  check**, which converts the assumption into a measurement.
- Patterns outside core (`W-NASA-*`, `W-SURR-*`, `W-EV-*`, `COMPOUND-EV-*`) were
  enumerated but not classified — out of A1's stated scope.
- No rule was executed against a pinned bundle as part of this item; the
  classification is from source reading. Running `verify-labels` against the three
  case-study bundles is A1's done-gate, not INV-1's.
- `docs/adversarial.md` and `uofa_weakener_patterns.md` (the prose taxonomy in
  `Praxis/Writing/Drafts/`) were not read; the rules file was treated as the sole
  authority on rule logic, which is what the item asks for.
