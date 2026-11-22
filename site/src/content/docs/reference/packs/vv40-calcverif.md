---
title: vv40 calculation verification (default off)
description: Run the FDA SimEval calcverif tool on a declared mesh study, seal the result into the signed package, and check it with four default-off W-CV rules in the vv40 pack.
---

**Calculation verification** asks one question of an evidence folder: does the
mesh study in it support the discretization error number the report claims?

![How a mesh study becomes checkable evidence in UofA](/diagrams/calcverif-evidence-flow.svg)

UofA runs the FDA SimEval `calcverif` tool on a mesh convergence table you
declare, records what the tool computes, folds that record into the package
before it is signed, and checks it with four rules. UofA measures and compares.
It does not say which number is right.

The four rules ship in the `vv40` pack as a **default-off block**. They run
only when you pass `--calcverif`. Without the flag nothing changes.

## Install

```bash
pip install 'uofa[calcverif,excel]'
```

The `calcverif` extra adds numpy, pandas, scipy and matplotlib, which the tool
imports. The core install does not need them. Without them, a declared study is
recorded as `not-run` with reason `dependency-missing`. The `excel` extra is
for the import step below, which reads an `.xlsx` workbook; leave it out only
if you never import from Excel.

## Run it

```bash
uofa evidence seal evidence/ --mesh-study study.json -o evidence.json
uofa import workbook.xlsx --evidence evidence.json --pack vv40 -o pkg.jsonld --sign --key k.key
uofa check pkg.jsonld --pubkey k.pub --calcverif
```

`study.json` declares the table, the columns, the refinement kind, and
optionally a formal order and a reported index. Nothing is inferred from column
names, and an unknown key is an error, so a typo cannot quietly become "absent".

```json
{
  "schemaVersion": "uofa-mesh-study/v0.1",
  "studies": [
    {
      "id": "max-velocity",
      "forFactorType": "Discretization error",
      "table": "mesh_convergence_study.csv",
      "quantityColumn": "max_velocity",
      "refinement": { "column": "element_count", "kind": "element-count", "dimension": 3 },
      "formalOrder": 2.0,
      "reported": { "value": 0.3, "units": "%", "basis": "relative", "source": "Report Table 3" }
    }
  ]
}
```

## What the record holds

One `calculationVerification` record per declared study. The tool's numbers
(observed order, Richardson value, the grid convergence index, absolute and
relative) are kept as the tool returned them. What the tool computes but does
not return is recovered from the tool itself, never re-decided:

- the convergence type, from the tool's own oscillation check;
- the constrained order, from the tool's own constraint function;
- the safety factor, by solving the tool's index formula backward (1.25 or 3).

Three statuses are kept apart, because they support different claims:

| Status | Meaning |
|---|---|
| `computed` | The tool returned numbers. |
| `no-estimate` | The tool ran on the data and refused: the quantity diverges, or oscillates across only three meshes. |
| `not-run` | UofA could not run the tool: dependency missing, table not sealed, invalid input, fewer than three levels. This is the assessor's gap, not the record's, and no rule fires on it. |

The table's bytes are hashed when they are read and must match the seal. A
value that was not declared is left out of the record, never filled in.

## The four rules

Each rule joins the study to its factor by the shared factor name and requires
the factor to be recorded as assessed.

| Id | Severity | Reports |
|---|---|---|
| W-CV-01 | High | The reported index disagrees with the recomputed one by more than the declared tolerance (25 %, relative). Which is correct is not established. |
| W-CV-02 | High | The study yields no estimate, and the factor is recorded as assessed. |
| W-CV-03 | Medium | The observed order differs from the declared formal order by more than 10 %. |
| W-CV-04 | Medium | The finest three meshes converge monotonically, but a coarser triplet diverges or oscillates. |

They stay silent, by structure, when no study is supplied, when the study is
`not-run`, when the comparison is `not-comparable`, when no formal order is
declared, and when the factor is not assessed.

## Demonstration: a real study, then two kinds of tampering

The study is the inferior vena cava flow study of Craven et al. (2018), as
tabulated in SimEval's calculation-verification notebook: eight meshes, two
quantities, no formal order and no reported index, as upstream itself declares
it. Full commands are in
[`docs/examples/calcverif-vena-cava/`](https://github.com/cloudronin/uofa/blob/main/docs/examples/calcverif-vena-cava/README.md).
The workbook is a placeholder; its own C2 and decision-layer results are the
same with or without the study. Hashes and keys differ on every run.

### 1. Clean

The seal readout:

```
What the mesh study says
  ivc-max-velocity (Discretization error): computed, method largeN_mono
    observed order 3.011, no formal order declared, safety factor 3
    index: 0.001179 relative, 0.0002974 absolute; no reported value
  ivc-helicity (Discretization error): computed, method largeN_mono
    observed order 2.249, no formal order declared, safety factor 3
    index: 0.01908 relative, 0.008691 absolute; no reported value
```

`uofa verify vena-cava.jsonld --pubkey demo.pub` (exit 0):

```
══ C1: Integrity verification (measurement seal + decision layer) ══
  sealed under the legacy whole-document scope (pre two-scope model).
  verified against: demo.pub (named with --pubkey)
  ✓ Measurement hash match
  ✓ Measurement signature valid
  decision layer: 1 record(s)
```

`uofa check vena-cava.jsonld --pubkey demo.pub --calcverif`: the rules load
and report no W-CV weakener. There is nothing to compare, an estimate was
computed, no formal order was declared, and every triplet converges.

```
  calculation-verification rules on (--calcverif): vv40/rules/calcverif/calcverif_v0.1.rules
```

### 2. A quiet change inside the signed package

In a copy of the signed package, one recorded number is edited by hand: the
relative index for maximum velocity, made smaller. Nothing else changes.

```
$ diff vena-cava.jsonld vena-cava.DELIBERATELY-ALTERED.jsonld
25c25
<       "cvGciRelative": 0.0011787627288742059,
---
>       "cvGciRelative": 0.0005,
```

`uofa verify vena-cava.DELIBERATELY-ALTERED.jsonld --pubkey demo.pub` (exit 1):

```
══ C1: Integrity verification (measurement seal + decision layer) ══
  verified against: demo.pub (named with --pubkey)
  ✗ Measurement hash match
  ✗ Measurement signature valid
  decision layer: 1 record(s)
```

The record was folded in before the package was hashed and signed, so it sits
inside the signature.

### 3. A changed table, read against the original seal

In a copy of the sealed table, one value is edited: the finest-mesh maximum
velocity, 0.25233 to 0.25333. The wrapper is then run on the altered copy
against the digests the original seal recorded:

```
ivc-max-velocity (Discretization error): not run (table-not-sealed)
  the bytes read from ivc_mesh_study.csv are not the bytes the seal recorded
ivc-helicity (Discretization error): not run (table-not-sealed)
  the bytes read from ivc_mesh_study.csv are not the bytes the seal recorded
```

No number is produced from bytes the seal did not record.

### A reported index that disagrees

The vena cava example carries no reported index, on purpose. The
[`calcverif-starter`](https://github.com/cloudronin/uofa/blob/main/docs/examples/calcverif-starter/README.md)
example does. It uses an input from SimEval's own test file and a **made-up**
reported value of 0.3 %, chosen to disagree:

```
What the mesh study says
  oracle-n3 (Discretization error): computed, method N3_mono
    observed order 1, formal order 1 (within tolerance), safety factor 1.25
    index: 0.625 relative, 1.25 absolute; reported 0.3 % relative (diverges)
```

The record's detail is `0.003 vs 0.625 fraction (tolerance 25.0%)`. With
`--calcverif`, C3 reports:

```
  ⚠ W-CV-01 [High] — 1 hit(s)
      → affected: oracle-n3
```

The finding names the study record it points at. `uofa import` gives each
folded record an IRI under the package,
`<package>/calculation-verification/<study id>`, and the readout prints its
last part.

## Source, license, and no endorsement

The calculation itself is FDA SimEval's, not UofA's.

| | |
|---|---|
| Source | [github.com/OSEL-DAM/SimEval](https://github.com/OSEL-DAM/SimEval) |
| Commit | `4a70fd3b364c0d4aa14d49a433ba7c4994c04cc3` |
| File | `src/calcverif.py`, vendored **unmodified** at `uofa_cli/_vendor/simeval/calcverif.py` |
| sha256 | `e4ddc15558ce64c8c55253c4d7efc7c6679f52e47dc0e740f42872c33bef5a5d` (checked by a test) |
| License | CC0-1.0, with the FDA software disclaimer below |

UofA's calculation verification feature is derived from FDA SimEval. **Use of
SimEval in UofA does not imply endorsement by the FDA** and confers no advantage
in regulatory decisions. The FDA software disclaimer, as distributed with
SimEval:

> This software and documentation (the "Software") were developed at the Food
> and Drug Administration (FDA) by employees of the Federal Government in the
> course of their official duties. Pursuant to Title 17, Section 105 of the
> United States Code, this work is not subject to copyright protection and is
> in the public domain. Permission is hereby granted, free of charge, to any
> person obtaining a copy of the Software, to deal in the Software without
> restriction, including without limitation the rights to use, copy, modify,
> merge, publish, distribute, sublicense, or sell copies of the Software or
> derivatives, and to permit persons to whom the Software is furnished to do
> so. FDA assumes no responsibility whatsoever for use by other parties of the
> Software, its source code, documentation or compiled executables, and makes
> no guarantees, expressed or implied, about its quality, reliability, or any
> other characteristic. Further, use of this code in no way implies endorsement
> by the FDA or confers any advantage in regulatory decisions. Although this
> software can be redistributed and/or modified freely, we ask that any
> derivative works bear some notice that they are derived from it, and any
> modified versions bear some notice that they have been modified.

The CC0 text and the disclaimer ship in the wheel
(`uofa_cli/_vendor/simeval/`) and in `LICENSES/LICENSE-simeval.txt`.
