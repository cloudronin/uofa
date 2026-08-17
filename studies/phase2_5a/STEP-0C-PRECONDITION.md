# Phase 2.5a step 0c — precondition: mutation started from valid packages

Addendum E condition 4. Run once, before any scoring, so the report can cite
this rather than imply it. Catalog v0.5.15.1; commit `3b063f1e`;
measured 2026-08-17.

## Verdict

| Substrate | `verify` hash | `verify` signature | C2 SHACL | C1 integrity | C3 rules | baseline findings |
|---|---|---|---|---|---|---|
| morrison/cou1 | match | valid | conforms | pass | runs | 11 |
| morrison/cou2 | match | valid | conforms | pass | runs | 18 |
| nagaraja/cou1 | match | valid | conforms | pass | runs | 19 |

**All three substrates are valid, signed, profile-conformant packages at v0.5.15.1.**
Every conformance split in Arm M is therefore caused by the mutation, not inherited
from the substrate. The report cites this file rather than implying it.

Two notes the report needs alongside:

- The **baseline findings are not all substantive.** 27 of the 48 are vacuous
  `noValue` firings on bare-IRI validation results — see PRECONDITION-INVENTORY.md
  Finding 3. A substrate being valid and a substrate being clean are different
  claims, and only the first is established here.
- `verify` passes on all three **because they are signed with the research key**.
  Mutants are not re-signed, so `verify` is not part of the mutant scoring path;
  `check` and `rules` are. MUT-DEL-05 strips the signature deliberately while
  leaving the hash covering the original bytes, which is the tamper artifact
  W-SI-01 exists to catch.

## uofa-morrison-cou1

```
$ uofa verify packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld
  
  ══ C1: Integrity verification (hash + signature) ══
    ✓ Hash match
    ✓ Signature valid

$ uofa check --pack vv40 packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld
  ══ C2: SHACL profile validation ══
    ✓ SHACL validation  Conforms
  ══ C1: Integrity verification (hash + signature) ══
    ✓ Hash match
    ✓ Signature valid
  ══ C3: Jena rule engine — weakener detection ══
    SUMMARY: 11 weakener(s) detected
    ✓ C2 SHACL
    ✓ C1 Integrity
    ✓ C3 Rules
```

## uofa-morrison-cou2

```
$ uofa verify packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld
  
  ══ C1: Integrity verification (hash + signature) ══
    ✓ Hash match
    ✓ Signature valid

$ uofa check --pack vv40 packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld
  ══ C2: SHACL profile validation ══
    ✓ SHACL validation  Conforms
  ══ C1: Integrity verification (hash + signature) ══
    ✓ Hash match
    ✓ Signature valid
  ══ C3: Jena rule engine — weakener detection ══
    SUMMARY: 18 weakener(s) detected
    ✓ C2 SHACL
    ✓ C1 Integrity
    ✓ C3 Rules
```

## uofa-nagaraja-cou1

```
$ uofa verify packs/vv40/examples/nagaraja/cou1/uofa-nagaraja-cou1.jsonld
  
  ══ C1: Integrity verification (hash + signature) ══
    ✓ Hash match
    ✓ Signature valid

$ uofa check --pack vv40 packs/vv40/examples/nagaraja/cou1/uofa-nagaraja-cou1.jsonld
  ══ C2: SHACL profile validation ══
    ✓ SHACL validation  Conforms
  ══ C1: Integrity verification (hash + signature) ══
    ✓ Hash match
    ✓ Signature valid
  ══ C3: Jena rule engine — weakener detection ══
    SUMMARY: 19 weakener(s) detected
    ✓ C2 SHACL
    ✓ C1 Integrity
    ✓ C3 Rules
```

