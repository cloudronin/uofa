# UofA Requirement Layer — proposal v0.1

Status: **PROPOSAL** — open questions marked, not yet ruled
Date: 2026-08-18
Motivated by: [INV-19](investigations/INV-19-requirement-layer-absent.md), [INV-18](investigations/INV-18-w-con-02-scope.md)
Target: a new context version (v0.8), additive — no existing package changes

## The problem in one line

UofA can determine whether a credibility assessment was *adequately conducted*.
It cannot determine whether the model *meets its requirement*, because a
requirement's content has nowhere structured to live.

## Why that is not a small omission

The existing catalog is deterministic about the shape of the credibility
argument: bindings present, chains intact, gradations compared. `W-AR-02`
already does a numeric comparison — `achievedLevel < requiredLevel` — so the
pattern of "required value versus achieved value, checked mechanically" is
native to the model. It is simply pointed at **assessment gradation levels**
rather than at **engineering quantities**.

One level down, where the physics is, there is nothing. `uofa:Requirement` is
declared as a class with zero properties. So are `uofa:OperatingEnvelope` and
`uofa:ApplicabilityConstraint`. Each is a room built for a constraint, with no
way to state one — and prose has filled all three, because the content has to go
somewhere.

The consequence is that any weakener touching requirement satisfaction must
infer from narrative, which is the failure mode the project exists to remove and
has separately measured at roughly 200 judgments corpus-wide (INV-17).

## What V&V 40 actually asks for

Sampled from `packs/vv40/examples/morrison/cou1`, the hand-authored canonical
case. Real acceptance criteria sort into four shapes, and only one is a value
bound:

| Shape | Example | Representable today |
|---|---|---|
| Gradation goal | "Goal (b)" | **yes** — `requiredLevel` |
| Required activity, with cardinality | "compare against Hariharan benchmarks"; "repeated five times"; "≥3 systematically refined meshes" | no |
| Region containment | "validation point lies within the COU operating range" | no |
| Value bound | "RH < 1"; "GCI below 5%" | no |

A single constraint primitive therefore covers about a quarter of what the
standard asks. Three kinds of decidable check are needed, not one.

## Two requirement layers

This is the distinction the model currently lacks.

**Credibility goals** — V&V 40 Table 3/4, "what rigour was required." Modelled
today; this is what the weakener catalog checks.

**Device requirements** — "hemolysis shall not exceed predicate levels", RH < 1.
**No representation at all.** `bindsRequirement` names one by IRI and its content
lives nowhere.

The canonical example shows the two colliding. The *Output comparison*
credibility goal reaches out and quotes the device threshold —
*"difference between CFD and experimental RH small relative to safety threshold
(RH < 1)"* — embedding the only genuinely checkable engineering constraint in
that factor set as prose inside a credibility goal, because there is no
requirement layer to put it in.

## Design position: reference, project, never author

UofA is not a requirements management system and must not become one. Formal
requirements live in DOORS, Jama, Polarion, a SysML v2 model, or a controlled
document. UofA references the authority and projects **only the machine-relevant
facts** needed for weakener analysis.

A projection is trustworthy only if it is pinned and auditable, so a reference
carries four things, not one:

```
externalRef   IRI            which requirement
              fetchHint      where to get it        (schema:url — exists, unused on bindings)
              version        which revision
              contentHash    what it said when projected
```

The content hash is what makes this different from today's bare IRI. The package
hash covers only the package's own serialization, so without it a requirement can
be revised after signing and the package still verifies clean.

Every projected constraint additionally retains **the source expression
verbatim**. UofA reasons over the small structured form; the verbatim text makes
a mis-projection detectable rather than silent.

## Borrowing the SysML v2 frame

SysML v2 makes a `requirement def` a kind of `constraint def`, with three parts
that carry the weight:

- **`subject`** — exactly one; what the requirement is about
- **`assume constraint`** — the preconditions under which it applies
- **`require constraint`** — what must hold

The `assume` / `require` split is the part this proposal most needs. The two
hemolysis requirements in `adv-2026-p2-111-inconsistent_medium-v02` disagree
partly on bounds, but mostly because nothing states *when each applies* — whether
the secondary supersedes, refines, or holds jointly with the primary. In SysML v2
that is a visible modelling error. In UofA today there is nowhere to have said it.

Mapping:

| SysML v2 | UofA |
|---|---|
| requirement identity + source | `externalRef` above |
| `subject` | the quantity or entity constrained |
| `assume constraint` | `ApplicabilityConstraint` — the empty class, finally populated |
| `require constraint` | **new** — the hole this proposal fills |
| attribute + unit | quantity identity + unit, below |
| `satisfy` | the existing binding |
| `verify` | `hasValidationResult`, `hasVerificationActivity` |

## The five pieces, in dependency order

**1. Quantity identity — the decision that matters.**
A declared way to name a quantity such that a requirement, a model output and a
measurement are known to refer to the same one. `quantityOfInterest` is already
used in the corpus and declared nowhere. Everything else is a join that fails
without it.

**2. Constraint.** `(quantity, operator, value, unit)`, conjoined. Atomic bounds.

**3. Requirement projection.** `externalRef` + `subject` + `assume[]` + `require[]`.

**4. Result-to-quantity link.** A validation result declares which quantity it
reports. Largely a matter of admitting terms already in use —
`comparisonValue`, `acceptanceThreshold`, `quantityOfInterest` are all present in
the corpus and absent from the vocabulary.

**5. Satisfaction check.** Reported value against required bound. Trivial once
1–4 exist; numeric comparison will want the SPARQL pre-pass pattern already
established by `W-SURR-03` and the iso42001 derivations.

Piece 1 is the design work. Pieces 2–5 are vocabulary and one rule.

## What becomes checkable

- a reported value outside a required bound — *does the model meet the requirement*
- two requirements over the same quantity with disjoint satisfying sets — the
  `p2-111` defeater, currently invisible
- an evaluation outside the assumed applicability region — `W-SURR-03`
  generalised out of the surrogate pack
- a requirement with an empty `assume` set — usually a modelling error

## Open questions — to be ruled, not assumed

**Q1. Expressiveness ceiling.** Atomic conjoined bounds, or full expression
trees? Full SysML v2 fidelity means shipping an expression evaluator into a rule
engine that already needs SPARQL pre-passes for simple numeric containment.
Recommendation: atomic bounds, source expression retained. **Not yet ruled.**

**Q2. Quantity identity mechanism.** Minted IRIs per quantity, an external
ontology, or ISO-80000 quantity kinds? Everything downstream inherits this.

**Q3. Units.** Two bounds in different units are not comparable, and silent
coercion produces a wrong answer that validates. Minimum viable: a required unit
token per bound, and refusal to compare across mismatched units.

**Q4. Scope of the credibility claim.** Is satisfaction checking *part of* what
UofA asserts, or a layer deliberately beside it? This determines whether the
limitations chapter reads "we do not check this" or "we check this as of v0.8",
and it is a positioning decision rather than a technical one.

## Compatibility

Additive. A new context version leaves every existing package pinned to
`@context .../v0.5.jsonld` untouched and still verifiable against the frozen
`/schemas/v0.5.json` (PR #76). The Phase 2 corpus of 4,556 packages and the
Phase 3 judgments keep their hashes, their signatures and their validity.

The schema freeze convention shipped 2026-08-18 is what makes this safe: a new
context version can add vocabulary without moving anything already published.
