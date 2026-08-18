# INV-18 — the reference-resolution rule reads one optional field and misses every load-bearing one

Status: **OPEN** — measured; the fix is a design call, not a bug fix
Date: 2026-08-18
Found during: Stage 4 author adjudication, row 11 (`adv-2026-p2-016-w-con-02_high_morrison-cou2-v05`)
Feeds: catalog scope review; Ch5 limitations

## The question

W-CON-02 exists to catch a real defeater: *a citation you cannot follow is not
evidence.* The catalog states it as

> UofA references an identifier whose target does not resolve within the graph and
> has no documented external-fetch hint.

Adjudicating a case where it fired, the reference it flagged turned out to be a
live DOI returning HTTP 200, while five other references in the same package
pointed at IRIs that resolve nowhere. That inverts the rule's stated purpose, so:
**which references does W-CON-02 actually police, and are they the ones that
matter?**

## Headline

**It reads one optional field. Every reference that carries the credibility
argument is outside its scope — and in the shipped examples, all of them dangle.**

| | |
|---|---|
| IRI-valued fields the rule inspects | **1** (`uofa:referencesIdentifier`) |
| Dangling references in the adjudicated package | **8**, of which **1** was flagged |
| The flagged one | **resolves** (HTTP 200) |
| The seven unflagged | do not resolve; `uofa.net/synth/*` returns **404** |
| Canonical `vv40/morrison/cou1` | **7 of 7** references dangle |
| Canonical `vv40/nagaraja/cou1` | **7 of 7** references dangle |

## What the rule matches

```
[w_con02:
    (?subj uofa:referencesIdentifier ?obj)
    noValue(?obj, rdf:type)
    noValue(?obj, schema:url)
    ...
```

Fires when the target of `referencesIdentifier` is neither described in the graph
nor given a fetch hint. Confirmed behaviourally by running the engine on four
variants of the same package:

| `referencesIdentifier` | W-CON-02 |
|---|---|
| `"https://doi.org/10.1016/j.ymeth.2024.03.003"` | fires |
| `{"id": …, "type": "CreativeWork"}` | silent |
| `{"id": …, "url": …}` | silent |
| `{"id": …}` | fires |

The last row is the control that matters: wrapping the IRI in a node object is not
what suppresses it — acquiring `rdf:type` or `schema:url` is. **No value of the
identifier string changes anything.** A real DOI and `10.0000/fake-paper` fire
identically.

The corpus confirms the scope is exactly this one field: of the 71 adjudication
packages, **5 carry `referencesIdentifier` and W-CON-02 fired on exactly those 5.**

## What it does not match

In the adjudicated package, eight IRI references have no target described anywhere
in the document:

```
DANGLING  bindsRequirement       uofa.net/synth/req/vad-hemolysis-absolute-threshold   404
DANGLING  bindsClaim             uofa.net/synth/claim/cfd-hemolysis-below-clinical-…
DANGLING  bindsModel             uofa.net/synth/model/cfd-centrifugal-pump-hemolysis   404
DANGLING  bindsDataset           uofa.net/synth/data/fda-pump-piv-experimental
DANGLING  bindsDataset           uofa.net/synth/data/monte-carlo-uq-hemolysis-runs
DANGLING  wasAttributedTo        uofa.net/synth/org/morrison-credibility-team
DANGLING  wasDerivedFrom         doi.org/10.1115/1.4023070
DANGLING  referencesIdentifier   doi.org/10.1016/j.ymeth.2024.03.003                   200  ← flagged
```

`bindsRequirement`, `bindsModel` and `bindsDataset` are the bindings that say which
requirement, which model and which data the assurance case is about. They are
`sh:minCount` mandatory. None is checked for resolvability.

## Not a synthetic-data artifact

The obvious objection is that adversarial packages use invented `uofa.net/synth/*`
IRIs, so of course they dangle. The canonical examples say otherwise:

```
vv40/morrison/cou1        7 refs   7 dangling
vv40/nagaraja/cou1        7 refs   7 dangling
vv40/morrison/cou2        6 refs   6 dangling
iso42001/hybrid/cou1      3 refs   3 dangling
iso42001/hybrid/cou2      3 refs   3 dangling
surrogate/airfrans/cou1   1 ref    1 dangling
surrogate/airfrans/cou2   1 ref    1 dangling
```

These are hand-authored, signed, published, and used in the README walkthrough and
on the site. **Every IRI reference in every one of them dangles.** Whatever the
rule is measuring, it is not measuring this.

## The design call this raises

The defeater is not "the identifier is external" — external IRIs are what the data
model is for, and `bindsRequirement` pointing into a requirements system is normal
practice. The defeater is *external **and** no stated way to reach it*, which is
already W-CON-02's own `schema:url` logic. Applying that logic consistently across
IRI-valued properties is the obvious extension.

The uncomfortable consequence is that it would fire on **every package the project
ships**, including all the canonical examples. That cuts two ways and the evidence
does not settle which:

- the packages genuinely are not self-contained and nothing in the catalog notices; or
- a rule firing on 100% of the corpus is miscalibrated rather than revealing.

A severity gradient is the likely resolution — a mandatory binding with no fetch
hint weighs differently from an optional citation — but that is a decision about
what the catalog is for, not something this investigation can measure its way to.
**Recorded here so the choice is made deliberately rather than inherited.**

## What this does not license

It is not grounds for overturning a W-CON-02 firing. Cheat-sheet trap 2 applies
directly: the rule's shape is "X present, Y absent", both conditions genuinely
hold, and calling the firing wrong *because the DOI resolves* is the misreading
that trap warns about. The rule behaved as written. Its scope being wrong
elsewhere is a separate finding, which is this one.

## Reproducing

```bash
# scope: which fields the rule reads, and which dangle
python - <<'PY'
import json, glob
FIELDS=('bindsRequirement','bindsClaim','bindsModel','bindsDataset',
        'wasAttributedTo','wasDerivedFrom','referencesIdentifier')
def described(d, ids=None):
    ids = set() if ids is None else ids
    if isinstance(d, dict):
        if 'id' in d and len(d) > 1: ids.add(d['id'])
        for v in d.values(): described(v, ids)
    elif isinstance(d, list):
        for v in d: described(v, ids)
    return ids
for f in sorted(glob.glob('packs/*/examples/**/*.jsonld', recursive=True)):
    d = json.load(open(f)); ids = described(d)
    refs = [x for k in FIELDS for x in
            (d.get(k) if isinstance(d.get(k), list) else [d.get(k)]) if isinstance(x, str)]
    print(f"{len(refs):>3} refs {len([x for x in refs if x not in ids]):>3} dangling  {f}")
PY

# behaviour: what suppresses the firing
uofa rules <package-with-referencesIdentifier>.jsonld | grep W-CON-02
```
