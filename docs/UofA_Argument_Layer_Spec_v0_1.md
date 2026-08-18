# UofA Argument Layer — proposal v0.1

Status: **PROPOSAL** — open questions marked, not yet ruled
Date: 2026-08-18
Motivated by: [INV-20](investigations/INV-20-rq1-schema-adequacy.md), [INV-21](investigations/INV-21-claim-node-conventions.md)
Sibling: [UofA Requirement Layer](UofA_Requirement_Layer_Spec_v0_1.md) — shares piece 1
Target: a new context version, additive — no existing package changes
Prototype: `dev/prototypes/argument-layer/` — draft rules, fixtures and measured results

## The problem in one line

UofA records the evidence a decision rests on and the claim it supports. It has
no way to record the **step between them**, so whether the evidence actually
supports the claim is settled by reading prose.

## Why that is not a small omission

The vocabulary states the gap in its own words. `uofa:AssuranceClaim` is
declared as:

> "The proposition the evidence is offered in support of. Naming it separately
> is what lets a reviewer ask whether the evidence actually supports it."

The stated purpose is to make support inspectable. The class carries **zero
declared properties**, so nothing can say what supports it or how.
`uofa:WeakenerAnnotation` is declared as:

> "A condition under which the stated evidence does not support the claim it is
> offered for."

That describes a defeater on an *inference step* — GSN's SupportedBy, SACM's
`AssertedInference`, Toulmin's rebuttal. There is no inference step in the model.
The catalog has defeaters and nothing for them to defeat, so every weakener
attaches via `affectedNode` to a node rather than to a step.

The plumbing to reach a claim is not the missing part. `uofa:bindsClaim` is
fully declared (`rdfs:domain uofa:UnitOfAssurance`, `rdfs:range
uofa:AssuranceClaim`), is present in all 71 adjudication packages and all six
canonical examples, and is already traversed by rules (`w_ep01`,
`w_prov01_seed_claim`). What is missing is anything to find on arrival — which
is why the repo has drifted into four incompatible conventions for the same
property (INV-21).

## What the decision records actually assert

Two Stage 4 rows, adjudicated OUT-OF-SCOPE because their defeater is prose.
Both are Morrison COU1, both `Accepted`, both at MRL 2.

**Row 16** (`...119-confusion-necessary-sufficient_high-v03`) argues that
satisfying `RH < 1` — which the same paragraph establishes as *"the established
regulatory acceptance metric for Class II CPB devices"*, i.e. a gate that must be
passed — *"constitutes sufficient evidence that the computational model meets the
safety goal of this COU."*

**Row 54** (`..._medium-v02`) argues that because *"the RH threshold alarm is
present and was triggered correctly in bench-scale validation"*, the model
*"will correctly identify hemolysis-adverse operating conditions in the full
device tolerance study"*, and separately that the seven assessed factors meeting
their required levels **confirms** *"that the RH threshold mechanism functions as
intended."*

Both are instantiated from the **same generator spec**
(`specs/gap_probe/greenwell_suf_confusion_necessary_sufficient.yaml`), so shared
structure is partly by construction and is *not* evidence of generality. What is
not by construction is that the two intensities produced materially different
rationale prose and two different structural signatures — row 16's defect is
modality, row 54's is quantity. One defeater family, two shapes:

| | Row 16 | Row 54 |
|---|---|---|
| **Modality** | a *necessary* condition is used as *sufficient* | — |
| **Quantity** | — | claim is about detection *sensitivity*; grounds are gate *presence* and 13% agreement |
| **Scope** | 5 evaluated conditions → the COU tolerance study | 5 bench points → the full tolerance study |
| **Compliance appeal** | "not required at this risk level ⟹ do not affect the sufficiency" | "seven factors meet required levels, confirming the mechanism functions" |

None of these is a defect in the *evidence*. Every structural fact in row 16 is
correct and the package is V&V 40 compliant. What is defective is the step from
the evidence to the conclusion — the thing with no representation.

**The evidence base is one defeater family.** Whether these four rules cover the
other fourteen gap-probe specs is untested, and is the first thing to measure
before any of this ships.

## Design position: derive, never author

The failure mode to design against is already measured.
`requiredVerificationMethod` is declared, is read by W-AR-03, and is populated in
**1 of 78** packages. Optional structure in this project goes unpopulated. An
argument layer that must be hand-authored will be empty in exactly the same way.

So the layer is an **extraction target**, not an authoring burden. `uofa extract`
(`src/uofa_cli/commands/extract_cmd.py`) already has the right shape — documents
in, structured out, HITL review, then signed import — and V&V 40 supplies most of
the argument skeleton for free, since the framework *is* an argument outline
(COU → question → factors → gradation goals → decision). Extraction therefore has
to fill only the steps the template does not determine. In Morrison COU1 that is
precisely the step row 16 gets wrong.

Two consequences follow, and both are load-bearing:

1. **Spans, not inventions.** An extracted-with-attribution argument is one
   located in what the assessor actually wrote. That is what makes a reasoning
   chain defensible between reasoners, which is the property the corpus lacks.
   The existing attribution work (`attribution-sentence-index`, `evidence-span`,
   `published-rationale-ceiling`) is the mechanism.
2. **The producer materialises joins.** Not a stylistic choice — see
   *Encoding constraints* below, where it is forced by the rule engine.

## Borrowing the GSN / SACM frame

Nothing here is novel; the mapping is deliberately boring so the layer inherits
two decades of assurance-case practice.

| UofA | SACM | GSN | Toulmin |
|---|---|---|---|
| `AssuranceClaim` | `Claim` | Goal | Claim |
| `InferenceStep` | `AssertedInference` | SupportedBy + Strategy | Warrant-bearing step |
| `hasGround` | `AssertedEvidence` | Solution | Data |
| `warrantKind` | (inference description) | Strategy type | Warrant |
| `hasRebuttal` → `WeakenerAnnotation` | `AssertedChallenge` | (undercut) | Rebuttal |

The one deviation worth stating: UofA keeps `warrantKind` a **closed
vocabulary** rather than free text. A free-text warrant is prose again, and
prose is the thing being removed.

## The pieces, in dependency order

**1. Quantity identity.** Identical to piece 1 of the requirement layer proposal
and *the same decision, not a parallel one*. A declared way to name a quantity so
that a requirement, a model output, a measurement and a claim are known to refer
to the same one. Everything below is a join that fails without it. The prototype
demonstrated the point negatively: matching on node-IRI coincidence rather than a
declared `quantityId` both misses real matches and makes the join invisible to
the engine.

**2. Claim interior.** `claimText` (verbatim), `aboutQuantity` → QuantityRef,
`overScope` → ScopeRef, `claimModality` ∈ {necessary, sufficient, contributory},
`claimKind` ∈ {model-behaviour, assessment-rigour, compliance-status},
`aboutRequirement` → `uofa:Requirement`.

**3. The inference step.** `uofa:InferenceStep` with `supportsClaim` (exactly 1),
`hasGround` (1..n, evidence or claim), `warrantKind`, `hasRebuttal`. This is the
element the model does not have.

**4. Scope algebra.** `ScopeRef` as `(dimension, populationId, coversValues |
coversRange)`. The prototype implements population identity only; real coverage
is an open question below.

**5. Ground-coverage summary.** Per inference step, the set of quantities and
populations its grounds address, emitted by the producer. Forced by the engine,
not by taste — see below.

Piece 1 is the design work, and it is already on the table. Pieces 2–5 are
vocabulary and four rules.

## What becomes checkable

Four rules, prototyped and measured against the two real packages
(`dev/prototypes/argument-layer/RESULTS.md`):

| Rule | Fires when | Catches |
|---|---|---|
| **W-ARG-01** quantity gap | the conclusion's quantity is addressed by no ground | row 54 (primary) |
| **W-ARG-02** scope undercoverage | the conclusion's population is covered by no ground | rows 16, 54 |
| **W-ARG-03** modality substitution | a `sufficient` conclusion drawn from a `necessary` ground, warranted only by direct measurement | row 16 (primary) |
| **W-ARG-04** compliance appeal | an `assessment-rigour` ground offered for a `model-behaviour` conclusion | rows 16, 54 |

Each row has a **distinct primary defect**, so the two are not one pattern seen
twice. And the discriminating control matters more than the positives: a
*repaired* row 16 — same package, same evidence, same quantity and scope, with
the conclusion restated as `contributory` — is **silent on all four rules**. The
rules key on the defect, not on the presence of the layer.

## Encoding constraints — discovered, not assumed

Three of the four rules need set-level negation ("no ground…", "every
ground…"), which Jena rules express only existentially. The obvious encoding —
seed a per-step marker with a forward rule, then `noValue` it — **was tried and
measurably fails**. On the sound control it fired even though a probe showed the
marker and the conclusion value to be identical on the same subject:

```
cou1-rh-to-fitness  _groundQuantity  "relative-hemolysis-index"
cou1-rh-to-fitness  _conclQuantity   "relative-hemolysis-index"
```

Jena evaluates `noValue` at rule activation, not at fixpoint. This is the hazard
the core catalog already documents on W-PROV-01, and the prototype reproduces it.
Reordering the rule file does not fix it, and one of the two structurally
identical rules happened to pass — so an encoding of this shape passing its tests
is not evidence that it is correct.

One discipline that works, and that W-PROV-01 already follows: **`noValue` may
test only triples present in the input.** Hence piece 5 — the producer emits the
ground-coverage summary, and rules negate over a single declared triple.

**But forward RETE is the wrong engine for most of this.** The repo already
ships `net.uofa.oos.OOSEngine`: path-two LHS-decomposition over Jena **backward**
syntax (`[head <- body]`), which walks body clauses in declared order with
binding propagation and reports the first clause that fails. Negation is by
clause failure, so the activation race cannot arise; `sufficiency_starts_at`
already separates discriminator from sufficiency clauses; and the output names
the missing subgoal rather than raising a boolean. Piece 5 is therefore a
property of the prototype's engine choice, not a constraint on the layer.

The genuine architectural point is a different one — **two questions, two
engines**:

| Question | Mechanism | Verdict |
|---|---|---|
| Can UofA evaluate this claim at all? | OOS, backward, clause failure | OUT-OF-SCOPE |
| Is the declared argument sound? | forward weakener on a declared inference step | weakener fires |

Rows 16 and 54 were ruled OUT-OF-SCOPE, which is the first question; the W-ARG
rules answer the second. Both are wanted and OOS comes first. Critically, an OOS
rule for the argument gap still needs the claim to carry structure — the vv40
OOS rules already reach evidence via `(?claim uofa:hasSupportingEvidence ?e)`,
which **0 of 71** adjudication packages and **0 of 3** vv40 canonical examples
populate. So this layer is a precondition for both paths, not an alternative to
either.

## Profile gating

Rules fire only on packages declaring `uofa:ProfileArgument`. Legacy packages,
all six canonical examples and all 9,115 corpus files are untouched; conformance
is opt-in and enforced only once opted into. Verified: every negative control is
silent, including the unmodified sources of rows 16 and 54.

The precedent is exact. `ProfileDisposition` is marked *"v0.6 additive"* in
`packs/core/shapes/uofa_shacl.ttl` — a fourth `sh:in` value plus a dispatch
branch to its own body shape — and one core rule is already profile-gated.

The alternative policies were considered and rejected. *Fire on absence* would
flag essentially every package, reproducing W-ON-02, which fires on 65 of 71
queue packages and teaches nothing. *Check declared structure only, silently* is
the `requiredVerificationMethod` failure mode: 1 of 78.

## Open questions — to be ruled, not assumed

**Q1. Scope algebra ceiling.** Population identity is decidable and nearly
free; real coverage (numeric ranges, subset containment, cross-dimension
products) needs the SPARQL pre-pass pattern established by `W-SURR-03`. Where
does this stop? The requirement layer asks the same question about constraint
expressions and should be answered once, for both.

**Q2. Universal vs existential W-ARG-04.** The prototype fires when *an*
assessment-rigour ground is offered for a behavioural conclusion. The stricter
reading — *only* such grounds — needs the SPARQL pre-pass. Is the existential
form too noisy in practice? Unknown until it runs on a real corpus.

**Q3. May `hasGround` cross packages?** An argument that grounds in another
UofA's claim is the natural way to compose assurance, and also the natural way
to build an unverifiable chain.

**Q4. Is `warrantKind` closed?** Argued closed above. A closed vocabulary that
is too small pushes authors back into `claimText`.

**Q5. What happens to the three legacy `bindsClaim` conventions?** INV-21 has
the measurements. Under `ProfileArgument` the claim must be inline and typed
`AssuranceClaim`; whether the other conventions are deprecated, migrated, or
left alone is unruled.

**Q6. `uofa:Claim` vs `uofa:AssuranceClaim`.** The rules guard on the former,
which is declared nowhere; the vocabulary and canonical examples use the latter.
This is a live defect independent of this proposal (INV-21) and should be fixed
before rules are written against claim structure.

## Compatibility

Additive. No existing package changes, no existing rule changes, no shape
changes that alter current validation outcomes. `ProfileArgument` adds one
`sh:in` value and one dispatch branch. Existing packages neither declare the
profile nor carry inference steps, so every W-ARG rule is silent on them by
construction — verified across the canonical examples and the adjudication
corpus.

The one non-additive item is Q6, which is a bug fix rather than a feature.
