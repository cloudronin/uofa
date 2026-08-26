# UofA Spec — Term Registry and Generated Contexts v1.0

Date: 2026-09-11
Status: QUEUED — post-release build item, sequenced by the author behind step 7's wheel, the sign route, and run 26. Estimate: half an afternoon — the hard parts (freeze semantics, regeneration-no-op tests, drift guards) already exist field-tested in `uofa schema` and lift verbatim (§3). No urgency; nothing depends on it.
Origin: `uofa:introducedIn` gave the SHACL layer single-definition maintenance — one living shapes graph, per-era jurisdiction, no drifting file copies. The same cannot be done to the JSON-LD contexts directly: a context is not law applied to documents but part of what a document's bytes mean — the term-to-IRI mapping sits in the hash preimage and every consumer's expansion, so contexts must remain frozen per-version editions. This spec captures the half that CAN be unified: single-definition authoring one layer up, with the frozen editions generated rather than hand-maintained.

## 1. The principle

Shapes are law — one living statute book with effective dates. Contexts are language — frozen editions that keep old utterances permanently interpretable. The registry unifies the *authoring* of the language while the *published editions* stay per-era and immutable: one legislative history, many frozen printings, nobody edits last year's printing.

## 2. The registry

One master file (`spec/term_registry.{yaml|ttl}` — format Claude Code's call, human-diffable required), the sole hand-edited source of vocabulary truth. Per term:

| field | meaning |
|---|---|
| `term` | the JSON-LD key |
| `iri` | the mapped IRI |
| `type` | `@id`, datatype, container mapping — whatever the context entry needs |
| `introducedIn` | first context version carrying the term |
| `retiredIn` | version at which the term stops being emitted (e.g. `signerKind`, retired pre-release inside the v0.9 line) — retirement is an authoring-history fact; it never removes the term from editions already frozen |
| `kind` | person-class / infrastructure / act-reference / structural — the identity-grammar classification where applicable |
| `definition` | one sentence, the term's meaning of record |

Registry rules: append-only in spirit — a term's `introducedIn` is never re-dated; definitions may be clarified but the clarification is a dated note, not a rewrite; an unversioned or malformed entry fails the build (totality — ambiguity cannot become an escape hatch).

## 3. Generation

**Build this as a sibling of the existing generator — `uofa schema` (src/uofa_cli/commands/schema.py) already invented the house disciplines, field-tested. Reuse them verbatim rather than re-deriving:**

- **The `--freeze` semantics lift whole**: frozen editions refuse overwrite, with deliberately no `--force` — the existing docstring states the law better than this spec did: "rewriting a published version silently is the failure the versioning scheme exists to prevent, and a flag offering it would hand the guarantee straight back." A wrong frozen edition gets a new version or a hand edit whose commit explains itself; both leave a trace.
- **The regeneration-no-op test shape copies** (`test_schema_regeneration.py`'s pattern, born from the incident where regenerating silently deleted `hasContextOfUse` because the generator read fewer sources than the artifact was built from): CI pins that regeneration reproduces the committed artifacts exactly.
- **The drift-test pattern copies** (`test_excel_constants_derived.py`'s shape) for any hybrid or transcribed surface (the reference doc's tables).
- **The naming discipline is already set**: frozen schemas mirror `spec/context/vX.Y.jsonld` so consumers line versions up without a lookup table; generated context editions keep that exact naming.
- Surface: plausibly `uofa vocab` beside `uofa schema`, or an `--emit context` mode — Claude Code's call; the command tree should read as the pair it is.

The resulting architecture, stated once: **two masters, two generators, one discipline.** The shapes graph (law, with `uofa:introducedIn` jurisdiction) generates the JSON Schema and import constants; the term registry (language) generates the frozen context editions. Every generated artifact in the repo carries the same three guarantees: single source, deterministic regeneration pinned green, published versions immutable with the refusal built in.

Mechanics:
- The generator emits each per-version context file from the registry: version N's context = all terms with `introducedIn ≤ N` and (`retiredIn` absent or `> N`), rendered in the canonical serialization (sorted keys, fixed formatting) so generation is deterministic byte-for-byte.
- Generated files are build artifacts in the repo, digest-pinned exactly as today. The pins' append-only discipline is unchanged — the registry does not replace the pins; it feeds them.
- Hand edits to generated context files are forbidden by CI (see §4). The registry is the only door.

## 4. The proof obligations (all red-first)

1. **Generation idempotence against shipped history**: the generator, run against the registry, reproduces the shipped v0.5 … v0.9 context files byte-for-byte. This is the load-bearing test — it proves the registry is a faithful history, not a rewrite. If any shipped edition cannot be regenerated exactly, the registry is wrong and gets fixed; the shipped bytes never move.
2. **Determinism**: two runs, identical output, asserted.
3. **Frozen-artifact guard**: CI fails if a generated context file differs from the generator's output (catches hand edits) — the same shape as `test_frozen_artifacts.py`, applied to the editions.
4. **Retirement semantics**: `signerKind`'s registry entry proves a retired term is absent from the edition that retired it and present in none after — while any edition frozen before retirement is untouched.
5. **Pin coherence**: every generated edition's digest matches its pin entry; a new edition requires a new pin entry (append-only), never a pin update.

## 5. What this buys

- The last hand-maintained version family in the repo goes away; vocabulary changes become one-line registry edits plus a generated, pinned edition.
- "What vocabulary existed at v0.7" becomes a filter over the registry, mirroring the shapes' queryable jurisdiction.
- The reference doc's term tables and the identity-grammar table can be generated from the registry (same transcribed-from-source discipline as the hygiene fixture's table), removing another drift surface.
- Future context versions (v0.10+) are born from the registry with their history attached, and the two-dialects disease loses its last habitat: a term cannot acquire a second spelling without the registry showing two entries side by side.

## 6. Out of scope

Changing any shipped context byte (forbidden forever). Runtime behavior — consumers and the resolver see identical files; this is an authoring-and-build change only. SHACL (already solved by `uofa:introducedIn`). Any praxis claim — post-freeze tooling, invisible to the manuscript.

## 7. One line

The shapes got one statute book with effective dates; the contexts get one legislative history with frozen printings — single-definition authoring everywhere, immutable law and language at every era, and no version family left for drift to live in.
