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

**What works** — the W-PROV-01 discipline: `noValue` may test only triples
present in the input. The producer emits the ground-coverage summary
(`groundQuantity`, `groundPopulation`) as original triples, computed from
`hasGround`, and rules negate over a single declared triple. All results in
experiments 1 and 2 use this encoding.

This is not merely a workaround. It forces a split worth adopting deliberately:
**SHACL checks the package is internally consistent** (does the summary match
`hasGround`? — a join with negation, native to `sh:sparql`), **the rule engine
checks the argument is sound.**

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
