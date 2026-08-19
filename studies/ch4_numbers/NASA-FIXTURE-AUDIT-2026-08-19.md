# NASA aerospace fixture audit — 2026-08-19

Item 2 of the author's E2/E3 close-out. Establishes that
`tests/fixtures/extract/aero-cou{1,2}-imported.jsonld` are **live rule
substrates**, and records their baseline ahead of the protocol encoding
sequenced behind A7.

Re-derive:

```bash
uofa rules tests/fixtures/extract/aero-cou1-imported.jsonld --pack nasa-7009b --format summary
```

## Result

| | aero-cou1-imported | aero-cou2-imported |
|---|---|---|
| `UnitOfAssurance` node | **yes** | **yes** |
| decision | Accepted | `Not Accepted` ⚠ |
| model risk level | 3 | 4 |
| credibility factors | 19 | 19 |
| data-graph triples | 213 | 205 |
| **triples inferred** | **172** | **125** |
| weakeners detected | **23** | **18** |
| SHACL | **pass** | **✗ FAIL** (1 violation) |
| integrity (hash + signature) | **✗ FAIL** | **✗ FAIL** |
| signature present | **yes** ⚠ | **yes** ⚠ |

Firings, current catalog (post-R1a):

- **COU1** — W-AR-02 ×3, COMPOUND-01 ×10, COMPOUND-03 ×2, W-EP-04, W-AL-02,
  W-CON-04, W-ON-02, W-PROV-01, W-NASA-02/03/06 ×1 each.
- **COU2** — **no W-AR-02**, W-EP-04 ×5, COMPOUND-01 ×5, COMPOUND-03, W-AL-02,
  W-CON-04, W-ON-02, W-PROV-01, W-NASA-02/03/06 ×1 each.

**They are live substrates.** 172 and 125 inferred triples against the annotation
snapshots' **0**. The commit message's claim — built "for isolating C3 rule
correctness from LLM/import non-determinism" — holds.

## Two escalations

Both were named in the escalation criteria and both fired.

### 1. Signature present where none was expected, and it does not verify

The expectation was "real firings, no signature". Both fixtures carry a
**populated** `signature` and `hash`, `signatureAlg: ed25519`,
`canonicalizationAlg: json-sortkeys/v1` — and **C1 Integrity fails on both**,
hash and signature.

The provenance question is sharper than "why is there a signature". Their
committed generator, `tests/fixtures/extract/_build_aero_fixtures.py:224-225`,
writes **all-zero placeholders**:

```python
"hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
"signature": "ed25519:0000…" + "0" * 64,
```

The committed fixtures do not carry zeros. They carry real-shaped values
(`sha256:9d844f6c…`, `ed25519:1e72e3d3…`) that **do not verify**. So either the
fixtures were signed after generation with a key whose material no longer
matches, or they were edited after signing. Either way the generator no longer
reproduces the committed files, and neither file is integrity-clean.

**Not acted on.** This is a provenance question, and A4's audit-trail appendix is
the place it lands.

### 2. COU2 fails SHACL on a one-character enum mismatch

```
[High] decision
       Required: one of {Accepted, Not accepted}
       Actual:   Not Accepted
```

Capital **A** in "Accepted" where the profile enum wants lowercase. One field,
one character.

It does not affect the tests repointed at it — W-AR-02 requires
`outcome = 'Accepted'`, and both spellings differ from that — but **the fixture
is not SHACL-clean and must not be cited as one**. Left unfixed deliberately:
correcting it changes a committed fixture whose hash already fails, and the
disposition was explicit that fixtures are not to be tuned.

## Bearing on item 6

When the protocol encoding runs behind A7, this is the before-state. These
fixtures stay untouched as the C3 isolation artifacts they are; the protocol
encoding is a new artifact. Both defects above belong to the fixtures, not to the
encoding that will replace them as H1 substrates — and neither should be
inherited by it.
