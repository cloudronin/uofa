# Calculation verification starter

A minimal mesh study run through `uofa evidence seal --mesh-study`, folded into
a package, and checked with the default-off W-CV rules.

**The data is not from any real study.** The three mesh sizes and quantity
values are an input from FDA SimEval's own test file (`test/test_calcverif.py`
at commit `4a70fd3`, `test_N3_monotonic_const_r`), where upstream states the
expected results. The reported value in `study.json` is made up, and chosen to
disagree with the recomputed index, so that W-CV-01 has something to report.

| File | What it is |
|---|---|
| `evidence/mesh_study.csv` | The table: three mesh sizes, finest first. |
| `study.json` | The declaration: which table, which columns, formal order 1, and a synthetic reported index of 0.3 % (relative). |
| `expected-evidence.json` | The sidecar `uofa evidence seal` writes for this folder. Regenerating it must reproduce it apart from `generatedAt` (tested in `tests/test_calcverif_pipeline_e2e.py`). |

## Run it

From this folder, with `pip install 'uofa[calcverif]'`:

```bash
uofa evidence seal evidence --mesh-study study.json -o evidence.json
```

```bash
uofa keygen demo.key
```

```bash
uofa import ../../../packs/vv40/templates/uofa-starter-filled.xlsx --evidence evidence.json --pack vv40 -o starter.jsonld --sign --key demo.key --check --calcverif
```

The seal readout includes:

```
What the mesh study says
  oracle-n3 (Discretization error): computed, method N3_mono
    observed order 1, formal order 1 (within tolerance), safety factor 1.25
    index: 0.625 relative, 1.25 absolute; reported 0.3 % relative (diverges)
```

With `--calcverif`, C3 reports `W-CV-01 [High]`: the reported index and the
recomputed one differ by more than the declared tolerance (25 %, relative).
Which of the two is right is not established here. Without `--calcverif` the
W-CV rules are not loaded and nothing from this study is reported.

The starter workbook itself fails two C2 fields (its decision cell and device
class). That is independent of the mesh study: a plain import of the same
workbook fails the same two.
