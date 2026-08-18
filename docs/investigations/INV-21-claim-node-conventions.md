# INV-21 — the claim node has four conventions, no interior, and the rules guard on a class that does not exist

Status: **OPEN** — measured; the `uofa:Claim` mismatch is a live defect
Date: 2026-08-18
Found during: building the argument-layer prototype for [INV-20](INV-20-rq1-schema-adequacy.md)
Feeds: [UofA Argument Layer proposal](../UofA_Argument_Layer_Spec_v0_1.md), RQ1
Related: [INV-19](INV-19-requirement-layer-absent.md) — the same shape one layer down

## The finding in one line

`bindsClaim` is the one part of the assurance case that is fully wired — declared,
ranged, universally populated, already traversed by rules — and it leads to a
node with nothing in it, which is why four incompatible conventions have grown up
around it and why the rules guard on a class that is declared nowhere.

## What is wired correctly

Worth stating first, because it changes what the fix costs.

```
uofa:bindsClaim a rdf:Property ;
    rdfs:domain uofa:UnitOfAssurance ;
    rdfs:range  uofa:AssuranceClaim .
```

Declared with both domain and range. Present in **all 71** adjudication packages
and **all 6** canonical examples. Already traversed by two core rules (`w_ep01`,
`w_prov01_seed_claim`). Weakeners can already *reach* the claim — nothing about
the path needs building.

`uofa:AssuranceClaim` then carries **0 declared properties**.

## Seven conventions for one property

Same property, mutually incompatible shapes, none of them enforced:

| Where | `bindsClaim` is |
|---|---|
| `packs/core/templates/uofa-complete-skeleton.jsonld` — what authors copy | bare IRI string |
| `packs/vv40/examples/morrison/cou1`, `.../nagaraja/cou1` | bare IRI, no node anywhere |
| `packs/vv40/examples/morrison/cou2` | inline node: prose `description`, flat `prov:wasDerivedFrom` bag of 4 IRIs, `acceptanceCriteria` whose content is also a prose `description` |
| `packs/iso42001/examples/hybrid/cou1` | **array** of two pack-typed claims (`aims:AIPolicyAppropriatenessClaim`) with `hasSupportingEvidence`, including nested evidence nodes |
| **69** of the 71 adjudication packages | bare IRI, no node anywhere |
| the other **2** — the queue's W-EP-01 targets | bare IRI, with the claim defined elsewhere under an undeclared container (`nodes`, `claims`), typed `Claim` |
| what the OOS rules *read* — `packs/{vv40,iso42001,surrogate}/rules/oos/oos_v0.1.rules` | a claim node with `uofa:hasSupportingEvidence` |

The morrison/cou2 form is the closest thing to a structured claim in the repo,
and it is still a bundle rather than an argument: `wasDerivedFrom` names four
evidence IRIs without saying what each contributes, which is the un-reified
inference step INV-20 describes.

Nothing enforces any of this. `AssuranceClaim` has no properties, so no shape
constrains what goes inside, and each pack solved it locally. `bindsClaim` is
never an inline node in the corpus; the two packages that define a claim at all
put it somewhere else entirely, which is its own convention and is covered
below.

The last row is the consequential one. Every vv40 OOS rule reaches evidence
through `(?claim uofa:hasSupportingEvidence ?e)`, and that property is carried
by **0 of 71** adjudication packages and **0 of 3** vv40 canonical examples —
only the 2 iso42001 examples populate it. So the OOS subsystem is written
against a claim interior that vv40 packages do not have, and is blocked by the
same emptiness as the weakener catalog. Confirmed by running
`uofa check --oos` on the row 16 package: **0 judgment-required gaps**, with no
OOS rule discriminating on an argument- or sufficiency-shaped defeater either.

## The live defect

The core rules guard on **`uofa:Claim`**:

```
[w_ep01:
    (?uofa uofa:bindsClaim ?claim)
    (?claim rdf:type uofa:Claim)          # <- not a declared class
    noValue(?claim, prov:wasDerivedFrom)
    ...
```

- `uofa:Claim` — **declared nowhere**. Not in the shapes, not in any context. It
  reaches `uofa:` only through `@vocab`.
- `uofa:AssuranceClaim` — declared in the shapes, mapped explicitly in the
  context, and used by the canonical examples.
- Occurrences in `packs/core/rules/uofa_weakener.rules`: `uofa:Claim` **3**,
  `uofa:AssuranceClaim` **0**.

They are different IRIs. A claim typed `AssuranceClaim` — the type the
vocabulary defines and morrison/cou2 uses — cannot match that guard.

## Consequence: the recorded corpus outcomes are stale

The guard was added in `205cc90e` (2026-04-27, *"refine W-EP-01 to recall=1.0,
nc_fpr=0.0"*). The adjudication corpus folder is dated **2026-04-26**. Because
every corpus package binds its claim as a bare IRI with no inline node, the
guard no longer matches any of them.

Re-running the current core catalog across all 71 packages:

| | |
|---|---|
| Not comparable — recorded `rules_fired: []` (SHACL-invalid, rules never ran) | 6 |
| Comparable | 65 |
| → identical to recorded | **2** |
| → differ from recorded | **63** |

No longer fires: `W-EP-01` **63**, `COMPOUND-01` 39, `COMPOUND-03` 31,
`W-AL-02` 3, `W-CON-01` 1. Newly fires: `W-AL-02` 1. Both compound rules chain
off another weakener having fired, so one guard cascaded into three.

### Effect on the Stage 4 adjudication

Eight rows would see `target_rule_fired` change. **Six are a measurement
artifact:** `uofa rules` runs no SHACL pre-pass, so on the mandatory-field
packages (rows 4, 5, 14, 19, 23, 30 — W-SI-01 / W-ON-01) the rule fires where the
real pipeline stopped at SHACL and recorded nothing. Those six are already ruled
GENERATOR-ARTIFACT and this is consistent with that ruling.

**Two are genuine** — both packages SHACL-valid, signature and context of use
present:

| Row | Package | Target | Recorded | Current | Adjudicated |
|---|---|---|---|---|---|
| **#3** | `adv-2026-p2-021-compound-01_medium_morrison-cou1-v04` | COMPOUND-01 | fired | **does not fire** | CORRECT-DETECTION |
| **#65** | `adv-2026-p2-010-w-al-02_medium_nagaraja-cou1-v02` | W-AL-02 | did not fire | **fires** | not yet reached |

Reported, not acted on. Nothing in the worksheet was modified.

## The generator depends on the undeclared side of the mismatch

The stale-outcome sweep left two comparable packages identical to their recorded
outcomes. They are not a random pair, and what they have in common closes the
argument.

Both are the queue's only `confirm_existing` targets for **W-EP-01** — the rule
carrying the `uofa:Claim` guard — and they are the **only 2 of 71** packages in
which the claim IRI is defined as a node at all. Every other package leaves
`bindsClaim` dangling, which is why the guard stopped matching them.

| Row | Claim node lives at | Declared `type` |
|---|---|---|
| #41 | `/nodes[0]` | `Claim` |
| #55 | `/claims[0]` | `Claim` |

Three things follow.

**The generator synthesises a claim node only when a rule needs one to fire.**
Nothing else in the corpus defines one, so the claim interior exists in exactly
the two packages whose target rule would otherwise miss.

**It reaches for the class the rules use, not the one the vocabulary declares.**
`type: Claim` expands through `@vocab` to `uofa:Claim` — the class declared
nowhere. Had the generator emitted `AssuranceClaim`, the class the vocabulary
actually defines and the canonical examples use, W-EP-01 would not fire on these
two either. So the `uofa:Claim` / `uofa:AssuranceClaim` split is not a dormant
inconsistency: **the corpus is load-bearing on the undeclared side of it**, and
correcting the rules to `uofa:AssuranceClaim` without regenerating would silence
W-EP-01 on all 71.

**`nodes` and `claims` are two further ad-hoc containers**, neither declared
anywhere, and they differ between two packages built by the same generator for
the same rule. That brings the conventions above to seven, and none of them is
constrained by a shape, because `AssuranceClaim` still has no properties.

This is the same cause as the rest of the note seen from the producer's side:
with no declared interior, even the tool that writes the corpus has to invent
one, and it invents a different one each time.

## Why this sits under INV-20 rather than beside it

INV-20 argues that UofA captures the assessment and not the assurance case, and
names the absent inference element as the deepest of three layers. INV-21 is the
measurement of what sits at the top of that stack: the claim node itself. The
class exists, the path to it is wired, and the interior is empty — so producers
improvised four shapes and the rules drifted onto a class name that was never
declared.

It is the same shape INV-19 found one layer down, where `uofa:Requirement`,
`uofa:OperatingEnvelope` and `uofa:ApplicabilityConstraint` are equally empty
rooms. Three empty rooms and a missing corridor is a pattern, not three bugs.

## What would close it

1. Fix `uofa:Claim` → `uofa:AssuranceClaim` in the three rule sites, and decide
   what W-EP-01 is meant to do on a bare-IRI claim. This is a bug fix,
   independent of any proposal.
2. Re-run the corpus, or state in the Stage 4 write-up that `rules_fired` is a
   generation-time record and 63 of 65 comparable packages have since diverged.
3. Give `AssuranceClaim` an interior, so the conventions have a reason to
   converge — the [argument layer proposal](../UofA_Argument_Layer_Spec_v0_1.md),
   prototyped in `dev/prototypes/argument-layer/`.

Item 1 should land before item 3: writing rules against claim structure while
the rules point at an undeclared class would bake the mismatch in. It also
cannot land alone — the corpus depends on `uofa:Claim`, so correcting the rules
without regenerating would silence W-EP-01 across all 71 packages.

## Reproducing

```bash
# the mismatch
grep -c "uofa:Claim\b"        packs/core/rules/uofa_weakener.rules   # 3
grep -c "uofa:AssuranceClaim" packs/core/rules/uofa_weakener.rules   # 0
grep -c "uofa:Claim a "       packs/core/shapes/uofa_shacl.ttl       # 0
```

```bash
# claim is a bare IRI in every corpus package
/Users/vishnu/miniconda3/bin/python -c "
import json,glob
n=sum(isinstance(json.load(open(f)).get('bindsClaim'),dict) for f in glob.glob('dev/build/adversarial/phase2/2026-04-26/adjudication_packages/packages/*.jsonld'))
print('packages with an inline claim node:', n)"   # 0
```

```bash
# ... but two define the claim elsewhere, under an undeclared container
/Users/vishnu/miniconda3/bin/python -c "
import json,glob
for f in sorted(glob.glob('dev/build/adversarial/phase2/2026-04-26/adjudication_packages/packages/*.jsonld')):
    d=json.load(open(f)); c=d.get('bindsClaim')
    for k in ('nodes','claims'):
        for n in d.get(k,[]):
            if n.get('id')==c: print(k, n.get('type'), f.split('/')[-1])"   # 2 hits, type 'Claim'
```

```bash
# when the guard landed, versus the corpus date
git log --format="%h %ad %s" --date=short -S"(?claim rdf:type uofa:Claim)" -- packs/core/rules/uofa_weakener.rules
```

Full sweep method and per-row detail: `dev/prototypes/argument-layer/RESULTS.md`,
experiment 4.

## Coverage statement

Searched: `packs/**` and `spec/**` for `bindsClaim`, `AssuranceClaim`, `Claim`
across `*.ttl`, `*.jsonld` and `*.rules`; all 71 adjudication packages and all 6
canonical examples for claim shape; the full core rules file for class
references. Not searched: the other 9,044 files of the phase-2 bundle (the 71
are the adjudication sample), and pack-local shapes beyond `iso42001` and
`surrogate`, which reference `AssuranceClaim` but were not audited for their own
claim conventions.
