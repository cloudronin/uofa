# W-EP-01 contrast — the guard rejects the vocabulary's own class

Pinned ref: **`b393530f`** — the commit immediately preceding the R1a fix, with
the guard still present at `packs/core/rules/uofa_weakener.rules:39`.

Machine verification for the Chapter 4 sentence describing W-EP-01 as guarding on
an undeclared class. Built before the fix so the pre-fix behaviour stays citable
after the catalog changes.

## The two fixtures

Identical in every respect except one token — the `type` of the bound claim:

| Fixture | claim `type` | expands to | declared? |
|---|---|---|---|
| `typed-claim.jsonld` | `Claim` | `uofa:Claim` via `@vocab` | **no** — declared nowhere |
| `typed-assuranceclaim.jsonld` | `AssuranceClaim` | `uofa:AssuranceClaim` | yes — in the shapes and context |

Both define the claim and give it no `prov:wasDerivedFrom`, which is the W-EP-01
defeater the rule exists to catch.

## Result

```
typed-claim.jsonld            W-EP-01 [Critical] — 1 hit
typed-assuranceclaim.jsonld   W-EP-01 SILENT
```

Raw output in [`RESULTS.txt`](RESULTS.txt).

## What this means — the silence is the defect

The firing is not the finding. **The silence is.**

Both packages carry the same orphan claim. W-EP-01's purpose is to catch exactly
that. It catches the one typed with a class the vocabulary **does not declare**,
and misses the one typed with the class the vocabulary **does** declare and the
canonical examples actually use.

So the guard added in `205cc90e` does not test "is this claim real". It tests "is
this claim typed with `uofa:Claim`" — an IRI reachable only through `@vocab`,
defined in no shape and no context. A correctly typed claim cannot satisfy it.

That is why the rule stopped matching the 2026-04-26 corpus, and why INV-21 found
the corpus load-bearing on the undeclared side of the split: the generator emits
`type: Claim` precisely because that is what the rule requires, so correcting the
rules to `uofa:AssuranceClaim` without regenerating would silence W-EP-01 on all
71 packages rather than fix it. R1a therefore drops the guard rather than
retargeting it.

## Reproducing

```bash
uofa rules studies/phase3_stage4/w-ep-01-contrast/typed-claim.jsonld --rules packs/core/rules/uofa_weakener.rules --context spec/context/v0.5.jsonld --format summary
```

Swap the fixture for `typed-assuranceclaim.jsonld` for the silent case. Both must
be run at ref `b393530f` or earlier; after the R1a fix lands, the guard is gone
and **both** fixtures fire, which is the intended post-fix behaviour and not a
contradiction of this record.

## A note on the fixtures' `@context`

They carry the published v0.5 context rather than an inline one. An inline
`@vocab`-only context expands `bindsClaim`'s string value as a **literal** rather
than an IRI, and the rule then matches nothing — both fixtures fall silent for a
reason that has nothing to do with the guard. The first build of this fixture hit
exactly that and is recorded here so the next person does not repeat it.
