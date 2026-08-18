# Argument-layer prototype

A working test of whether the argument a decision record asserts **in prose** can
be checked **structurally** — so that weakeners operate on the reasoning chain,
not just on the evidence chain.

Design: [`docs/UofA_Argument_Layer_Spec_v0_1.md`](../../../docs/UofA_Argument_Layer_Spec_v0_1.md)
Measured results: [`RESULTS.md`](RESULTS.md)

This is a **prototype**. Nothing here is in the catalog, the vocabulary, the
shapes or the published context. It changes no existing file.

## What is here

| | |
|---|---|
| `w_arg_draft.rules` | draft W-ARG-01..04, profile-gated on `uofa:ProfileArgument` |
| `context-v0.5-argument.jsonld` | v0.5 + the 7 argument terms — the exact context delta the layer needs |
| `build_fixtures.py` | derives the fixtures from the real adjudication packages |
| `fixtures/row16-argument.jsonld` | Stage 4 row 16, argument declared |
| `fixtures/row54-argument.jsonld` | Stage 4 row 54, argument declared |
| `fixtures/row16-repaired.jsonld` | row 16 with a **sound** argument — the discriminating control |

## Running it

```bash
uofa rules dev/prototypes/argument-layer/fixtures/row16-argument.jsonld --rules dev/prototypes/argument-layer/w_arg_draft.rules --context dev/prototypes/argument-layer/context-v0.5-argument.jsonld --format summary
```

Swap the fixture for `row54-argument.jsonld` or `row16-repaired.jsonld`. Both
`--rules` and `--context` are required: without `--context` the engine resolves
the package's published v0.5 context, which lacks the argument terms.

Regenerate the fixtures and the context delta:

```bash
/Users/vishnu/miniconda3/bin/python dev/prototypes/argument-layer/build_fixtures.py
```

## How the fixtures relate to the real packages

Each fixture is its source package plus exactly three edits, which
`build_fixtures.py` prints on every run so the claim stays checkable:

- `conformsToProfile` → `ProfileArgument` (the gate the rules check)
- `bindsClaim` → an inline, typed `AssuranceClaim` instead of a bare IRI
- `hasInferenceStep` added

**The rationale prose is left exactly as written.** The structure is asserted
alongside it, which is what `uofa extract` would emit.

## The fixtures are hand-authored, and that is the point of tension

The spec's central design position is that nothing in a UofA should be
hand-authored — an argument layer that must be authored will go unpopulated
exactly as `requiredVerificationMethod` did (1 of 78 packages).

These fixtures are hand-authored anyway, because they are a **proof device**:
they exist to answer "if the structure were present, would the rules find the
defect?" They are not evidence that authoring works, and nothing here should be
read as a demonstration that it does. The production path is extraction with
span attribution, with a human reviewing the output.

## Status

All four rules behave as intended on the two real cases; the sound control is
silent; the profile gate holds across the canonical examples and all 71
adjudication packages. Two findings came out of building it — a reproducible
Jena `noValue` race and a stale-outcome discrepancy in the corpus. Both are in
[`RESULTS.md`](RESULTS.md).
