# Argument-layer prototype — measured results

Date: 2026-08-18
Engine: `uofa rules` (Apache Jena GenericRuleReasoner, FORWARD_RETE)
Rules: `w_arg_draft.rules` · Context: `context-v0.5-argument.jsonld`

Everything below was run, not reasoned about. Failures are recorded alongside
successes, in the order they happened.

---

## Experiment 1 — do the rules find the defect?

| Fixture | Fired | On |
|---|---|---|
| `row16-argument.jsonld` | **W-ARG-01, W-ARG-02, W-ARG-03** | `cou1-rh-to-fitness` |
| `row54-argument.jsonld` | **W-ARG-01 ×2, W-ARG-02 ×2, W-ARG-04** | `cou1-gate-to-detection`, `cou1-factors-to-mechanism` |

Both rows fire their predicted **primary** rule — W-ARG-03 (modality
substitution) for row 16, W-ARG-01 (quantity gap) for row 54.

Caveat on how much that shows: the two packages are instantiated from the **same
generator spec** (`greenwell_suf_confusion_necessary_sufficient.yaml`) at
different intensities, so they are siblings, not independent cases. What is still
informative is that one defeater family produced two *different* structural
signatures, and the rules distinguished them. Coverage of the other 14 gap-probe
specs is untested.

Row 54 firing W-ARG-04 on `cou1-factors-to-mechanism` is the rationale's second
move caught in isolation: *"the seven assessed credibility factors all meet or
exceed their required levels, confirming that the RH threshold mechanism
functions as intended"* — an assessment-rigour ground offered for a
model-behaviour conclusion.

## Experiment 2 — do they discriminate, or just detect structure?

The question a positive result cannot answer on its own.

| Control | Expected | Result |
|---|---|---|
| `row16-repaired.jsonld` — same package, same evidence, same quantity and scope, conclusion restated `contributory` | silent | **silent (0)** |
| `packs/vv40/examples/morrison/cou2` | silent (no profile) | **silent (0)** |
| `packs/vv40/examples/morrison/cou1` | silent (no profile) | **silent (0)** |
| `packs/iso42001/examples/hybrid/cou1` | silent (no profile) | **silent (0)** |
| all **71** adjudication packages, unmodified | silent (no profile) | **silent — 0 firings on 71/71** |

The repaired fixture is the load-bearing one: it carries the full argument
layer and the profile, and differs from the firing version only in the strength
of what it claims. The rules key on the defect, not on the layer's presence.

---

## Experiment 3 — the encoding that failed

**The obvious encoding of set-level negation does not work in this engine.**

Three of the four rules need "no ground addresses Q", which Jena expresses only
existentially. The standard workaround is to seed a per-step marker with a
forward rule and then `noValue` it:

```
[w_arg01_seed:   (?i uofa:hasGround ?g) (?g uofa:aboutQuantity ?q)
                 -> (?i uofa:_groundQuantity ?q) ]
[w_arg01_detect: ... (?c uofa:aboutQuantity ?q)
                 noValue(?i, uofa:_groundQuantity, ?q) ... ]
```

This **fired on the sound control**. A probe rule that materialised both sides
showed the values to be identical, on the same subject:

```
cou1-rh-to-fitness  _groundQuantity  "relative-hemolysis-index"
cou1-rh-to-fitness  _conclQuantity   "relative-hemolysis-index"
```

so `noValue` should have been false. Jena evaluates `noValue` at rule
activation, not at fixpoint — the hazard the core catalog documents on
W-PROV-01, reproduced here.

Two things were tried and did **not** fix it:

1. **Reordering** — hoisting both seed rules above every detect rule. No change.
   The race is in RETE activation scheduling, not file order.
2. **Changing the join to a literal** — routing quantity identity through a
   declared `quantityId` string instead of the node IRI, making W-ARG-01
   structurally identical to W-ARG-02. No change.

Worth recording: **W-ARG-02, structurally identical, passed throughout.** Had the
prototype only tested W-ARG-02, the encoding would have looked correct. A rule of
this shape passing its tests is not evidence that it is sound.

**What this prototype used** — the W-PROV-01 discipline: `noValue` may test only
triples present in the input. The producer emits the ground-coverage summary
(`groundQuantity`, `groundPopulation`) as original triples, computed from
`hasGround`, and rules negate over a single declared triple. All results in
experiments 1 and 2 use this encoding.

**Correction — this was the wrong lesson to draw.** The measured race above is
real and reproducible, but the conclusion originally recorded here ("set-level
negation needs producer-materialized joins") was wrong, because it assumed the
forward RETE engine was the only option. It is not.

The repo already ships a second engine built for exactly this class of question:
`net.uofa.oos.OOSEngine`, path-two LHS-decomposition over **Jena backward
syntax** (`[head <- body]`). It does not ask the reasoner to prove the head; it
walks the body clauses in declared order with binding propagation and reports
the **first clause that fails**. Negation is by clause failure, so the
activation race cannot arise by construction, and `sufficiency_starts_at`
already separates discriminator clauses from sufficiency clauses — the same
split this prototype hand-rolled with profile gating.

It also emits more than a boolean: `missing_subgoal`, `missing_evidence_type`,
`would_support_defeater_evaluation`, and a verdict of **OUT-OF-SCOPE**. See
`packs/{vv40,iso42001,surrogate}/rules/oos/oos_v0.1.rules`,
`docs/oos_production_v0_1.md`, and `uofa check --oos`.

The producer-materialized-join workaround is therefore a property of *this
prototype's* engine choice, not a constraint on the argument layer. The SHACL
split it implied is not forced.

---

## Experiment 4 — the corpus outcomes are stale

Not part of the design question. Found while establishing a baseline, and
reported because it bears on the Stage 4 adjudication in progress.

`.outcome.json` records what fired when the corpus was generated. Re-running the
**current** core catalog over all 71 packages:

| | |
|---|---|
| Not comparable — recorded `rules_fired: []`, i.e. SHACL-invalid so rules never ran | 6 |
| Comparable | 65 |
| → identical to recorded | **2** |
| → differ from recorded | **63** |

Rules that no longer fire: `W-EP-01` **63**, `COMPOUND-01` 39, `COMPOUND-03` 31,
`W-AL-02` 3, `W-CON-01` 1. Newly firing: `W-AL-02` 1.

One cause explains nearly all of it. Commit `205cc90e` (2026-04-27, *"refine
W-EP-01 to recall=1.0, nc_fpr=0.0"*) added a `(?claim rdf:type uofa:Claim)`
guard to W-EP-01. Every corpus package binds its claim as a **bare IRI with no
inline node**, so the guard no longer matches, and both compound rules chain off
other weakeners having fired. The corpus folder is dated 2026-04-26 — one day
before the guard.

### Effect on the adjudication

Eight rows would see `target_rule_fired` change. **Six are an artifact of how
this was measured, not drift:** `uofa rules` runs no SHACL pre-pass, so on the
mandatory-field packages (rows 4, 5, 14, 19, 23, 30 — W-SI-01 / W-ON-01) the rule
fires where the real pipeline stopped at SHACL and recorded nothing. All six are
already ruled GENERATOR-ARTIFACT, and this is consistent with that ruling rather
than a challenge to it.

**Two are genuine.** Both packages are SHACL-valid — signature and context of
use present — so the comparison is sound:

| Row | Package | Target | Recorded | Current | Adjudicated |
|---|---|---|---|---|---|
| **#3** | `adv-2026-p2-021-compound-01_medium_morrison-cou1-v04` | COMPOUND-01 | fired | **does not fire** | CORRECT-DETECTION |
| **#65** | `adv-2026-p2-010-w-al-02_medium_nagaraja-cou1-v02` | W-AL-02 | did not fire | **fires** | not yet reached |

Row 3 was ruled on a target that the current catalog does not fire. Row 65 has
not been reached yet and would otherwise be judged against a stale negative.

Reported, not acted on. Nothing in the worksheet was modified.

---

## Experiment 5 — what the existing OOS engine says about row 16

Prompted by the observation that the repo already has backward-chaining rules
which detect negatives. Run:

```bash
uofa check <row16 package> --oos
```

Result: **0 judgment-required gaps.** Two independent reasons, worth separating
because they point at different things.

**1. No rule discriminates on this defeater.** The five vv40 OOS rules gate on
`adversarialProvenance.sourceTaxonomy` matching `oos/subjective-model-form-adequacy`,
`.../tacit-knowledge`, `.../behavioral-compliance`, `.../jurisdictional-alignment`,
`.../clinical-arbitration`. Row 16's taxonomy is none of these. There is no OOS
rule for an argument- or sufficiency-shaped gap.

**2. The sufficiency clauses bind a structure vv40 packages do not have.** Every
vv40 OOS rule reaches evidence through `(?claim uofa:hasSupportingEvidence ?e)`:

| | carries `hasSupportingEvidence` |
|---|---|
| 71 adjudication packages | **0** |
| vv40 canonical examples | **0** |
| iso42001 canonical examples | 2 |

So the vv40 OOS rules are written against a claim interior that vv40 packages do
not populate. This is a **fifth** claim-node convention beyond the four INV-21
records, and it means the OOS subsystem is blocked by the same empty-claim
problem — not only the weakener catalog.

### What this implies for the design

Two different questions want two different engines, and conflating them was the
error in this prototype's framing:

| Question | Mechanism | Verdict |
|---|---|---|
| Can UofA evaluate this claim at all? | OOS, backward, clause failure | OUT-OF-SCOPE |
| Is the declared argument sound? | forward weakener on a declared inference step | weakener fires |

Rows 16 and 54 were adjudicated **OUT-OF-SCOPE**, which is the first question.
This prototype answers the second. Both are wanted, and OOS comes first — but an
OOS rule for the argument gap still needs the claim to carry structure, so the
representation work in the spec is a precondition for both paths rather than an
alternative to either.

## Experiment 6 — can OOSEngine carry the argument layer?

Two questions were left open by experiment 5. Both are now answered.

### Does binding propagation handle conclusion-bound-tested-against-grounds?

**Bindings do propagate** forward across sufficiency clauses
(`OOSEngine.walkSufficiency`, lines 178-211): each clause is resolved against
the accumulated map, unbound variables become `Node.ANY`, and matches are bound
via `putIfAbsent`.

**But there is no backtracking.** The walk calls `data.getGraph().find(...)`,
takes `it.next()` — the *first* triple returned — commits to it, and moves on.
If that binding makes a later clause fail, the rule reports failure rather than
trying the next candidate.

W-ARG-01's shape is *"does **any** ground address quantity Q"*. That is exactly
an existential over a multi-valued property, and it needs the backtracking that
is absent. So **W-ARG-01 and W-ARG-02 are not expressible correctly in OOS
v0.1** as it stands.

### This is not hypothetical — the shipped rules have it

Two packages were built from the row 16 package, both given
`sourceTaxonomy: oos/subjective-model-form-adequacy` so
`oos_modelform_adequacy_warranted` applies, and both given a claim with **two**
supporting-evidence items, one of which is the required
`uofa:StructuredComparisonStudy`. They differ only in JSON array order, which is
semantically nothing in RDF — verified identical: both graphs carry both
`hasSupportingEvidence` links and both type the same node
`StructuredComparisonStudy`.

| Fixture | Required evidence present? | `uofa check --oos` |
|---|---|---|
| `A_required_first.jsonld` | **yes** | **1 gap — "missing structured model-form comparison studies"** |
| `B_required_second.jsonld` | **yes** | 0 gaps |

Package A is a **false OUT-OF-SCOPE**: the rule reports missing exactly the
evidence the package contains. Which of the two orderings fails depends on the
order the Jena model returns triples, not on the document.

This affects every OOS rule whose sufficiency clauses traverse a multi-valued
property — which is all nine, since `hasSupportingEvidence` is multi-valued by
nature. Any claim carrying more than one supporting evidence item can produce a
spurious gap. It is a defect in the engine, not in the rules.

### Does modality mismatch fit the sufficiency frame?

Yes, and more cleanly than the quantity check. *"The bundle warrants this claim
only if it contains a warrant licensing the step"* is a natural sufficiency
clause, and because an inference step declares a single `warrantKind`, it is a
single-valued lookup that never needs backtracking.

So the split is sharper than experiment 5 suggested:

| Rule | OOS-expressible today |
|---|---|
| W-ARG-03 modality substitution | **yes** — single-valued warrant lookup |
| W-ARG-04 compliance appeal | yes, in its existential form |
| W-ARG-01 quantity gap | **no** — needs backtracking over grounds |
| W-ARG-02 scope undercoverage | **no** — same |

OOS remains the right frame for "can UofA evaluate this claim at all". It cannot
yet carry the two rules that quantify over grounds, and fixing that is an engine
change — add candidate backtracking to `walkSufficiency`, or push the existential
into the SPARQL pre-pass the discriminator phase already uses.

## Caveats

- **The fixtures are hand-authored.** They answer "if the structure were present,
  would the rules find the defect?" — nothing more. The spec's position is that
  this layer must be *derived*; these fixtures are not evidence that authoring
  works.
- **Four rules, two real cases.** Enough to show the design is implementable and
  discriminating; not enough to characterise precision or recall.
- **Scope coverage is population identity only.** Numeric range containment is
  unimplemented and is an open question in the spec.
- **W-ARG-04 is existential.** It fires when *an* assessment-rigour ground
  appears, not only when all grounds are. The stricter form needs the SPARQL
  pre-pass.

## Reproducing

```bash
/Users/vishnu/miniconda3/bin/python dev/prototypes/argument-layer/build_fixtures.py
```

```bash
uofa rules dev/prototypes/argument-layer/fixtures/row16-argument.jsonld --rules dev/prototypes/argument-layer/w_arg_draft.rules --context dev/prototypes/argument-layer/context-v0.5-argument.jsonld --format summary
```
