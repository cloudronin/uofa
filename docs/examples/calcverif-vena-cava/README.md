# Calculation verification: inferior vena cava mesh study

A real eight-mesh convergence study, run through `uofa evidence seal
--mesh-study` and checked with the default-off W-CV rules.

## Where the numbers come from

The element counts and both quantity columns are copied from FDA SimEval's
calculation-verification notebook, `notebooks/PdeCalculationVerification.ipynb`
at commit `4a70fd3b364c0d4aa14d49a433ba7c4994c04cc3`, section "Fluid flow in
the inferior vena cava". Upstream reports them from:

> B. Craven, K. Aycock, K. Manning. Steady Flow in a Patient-Averaged Inferior
> Vena Cava: Part II, Computational Fluid Dynamics Verification and
> Validation. Cardiovascular Engineering and Technology, 2018.

The study used OpenFOAM with a second-order finite volume method, on
unstructured, uniformly refined meshes from 0.8 to 102.5 million elements.
The notebook writes the counts as `1e6 * [102.5, 51.16, …]`; here they are
written out as integers. The notebook gives no units for the two quantities,
so `study.json` declares none. Absent means absent.

There is **no formal order** in `study.json`. Upstream's notebook explains why
it passes none: the scheme is formally second order for velocity and
pressure, but the theoretical rate for a location-dependent maximum and for
helicity is unclear. This example follows upstream and declares none, rather
than filling in a plausible 2.

There is **no reported index** either, so nothing is compared and W-CV-01
cannot fire. The record says what the tool computes from the table.

| File | What it is |
|---|---|
| `evidence/ivc_mesh_study.csv` | Element count, maximum velocity magnitude, volume-averaged helicity, finest first. |
| `study.json` | Two studies on the same table, one per quantity, element counts in 3D, no formal order, no reported index. |

## Run it, then tamper with it

Three steps, run from this folder with `pip install 'uofa[calcverif,excel]'`
(`calcverif` runs the SimEval tool; `excel` lets `uofa import` read the
workbook). The outputs below are from one run on the `feat/vv40-calcverif` branch. Hashes and
keys differ on every run; everything else should match.

The vv40 starter workbook stands in for an assessment here. It is a
placeholder, not the Craven study's credibility assessment. On its own it
fails two C2 fields and has one decision record awaiting a signature; a
plain import of the same workbook, with no mesh study, shows the same.

Every file whose name contains `DELIBERATELY-ALTERED` was edited by hand on
purpose, to show what the checks do with it. None of them is committed; the
commands below create them.

### Step 1: clean

Seal the study, import it into the workbook, sign, verify, check.

```bash
uofa evidence seal evidence --mesh-study study.json -o evidence.json
```

```bash
uofa keygen demo.key
```

```bash
uofa import ../../../packs/vv40/templates/uofa-starter-filled.xlsx --evidence evidence.json --pack vv40 -o vena-cava.jsonld --sign --key demo.key
```

```bash
uofa verify vena-cava.jsonld --pubkey demo.pub
```

```bash
uofa check vena-cava.jsonld --pubkey demo.pub --calcverif
```

Import output:

```
Evidence sidecar folded in: 1 artifactManifest, 2 calculationVerification
✓ Imported  vena-cava.jsonld
✓ Signed
  SHA-256: c62e3bef74b613eb...
```

`uofa verify` output (exit 0):

```
══ C1: Integrity verification (measurement seal + decision layer) ══
  sealed under the legacy whole-document scope (pre two-scope model).
  verified against: demo.pub (named with --pubkey)
  ✓ Measurement hash match
  ✓ Measurement signature valid
  decision layer: 1 record(s)
```

`uofa check --calcverif` output, C3 part. The core weakeners in the middle
come from the placeholder workbook and are trimmed here. There is no W-CV
line:

```
SUMMARY: 18 weakener(s) detected
⚡ COMPOUND-01 [Critical] — 2 hit(s)
⚡ COMPOUND-03 [High] — 1 hit(s)
⚠ W-AL-02 [Medium] — 1 hit(s)
⚠ W-AR-01 [Critical] — 10 hit(s)
⚠ W-AR-05 [High] — 2 hit(s)
⚠ W-CON-04 [Medium] — 1 hit(s)
⚠ W-ON-02 [High] — 1 hit(s)
  calculation-verification rules on (--calcverif): vv40/rules/calcverif/calcverif_v0.1.rules
Summary: vena-cava.jsonld
  ✗ C2 SHACL
  ✓ C1 Integrity
  ✗ C1b Decision layer complete  1 asserted record(s) awaiting their decider's signature
  ✓ C3 Rules
```

### Step 2: a quiet change inside the signed package

Copy the signed package and change one recorded number in the copy: the
relative index for maximum velocity, made smaller. Nothing else changes.

```bash
cp vena-cava.jsonld vena-cava.DELIBERATELY-ALTERED.jsonld
```

```bash
python3 -c 'import re,pathlib; p=pathlib.Path("vena-cava.DELIBERATELY-ALTERED.jsonld"); t,n=re.subn(r"(\"cvGciRelative\": )[0-9.eE+-]+", r"\g<1>0.0005", p.read_text(), count=1); p.write_text(t); print("edited", n, "value")'
```

```bash
diff vena-cava.jsonld vena-cava.DELIBERATELY-ALTERED.jsonld
```

```
25c25
<       "cvGciRelative": 0.0011787627288742059,
---
>       "cvGciRelative": 0.0005,
```

```bash
uofa verify vena-cava.DELIBERATELY-ALTERED.jsonld --pubkey demo.pub
```

Output (exit 1):

```
══ C1: Integrity verification (measurement seal + decision layer) ══
  verified against: demo.pub (named with --pubkey)
  ✗ Measurement hash match
  ✗ Measurement signature valid
  decision layer: 1 record(s)
```

The record was folded into the package before it was hashed and signed, so it
sits inside the signature. One changed number breaks it.

### Step 3: a changed table, read against the original seal

Copy the sealed table into a new folder and change one value in the copy: the
finest-mesh maximum velocity, 0.25233 to 0.25333.

```bash
mkdir DELIBERATELY-ALTERED-evidence && cp evidence/ivc_mesh_study.csv DELIBERATELY-ALTERED-evidence/
```

```bash
python3 -c 'import pathlib; p=pathlib.Path("DELIBERATELY-ALTERED-evidence/ivc_mesh_study.csv"); t=p.read_text(); assert t.count("102500000,0.25233,")==1; p.write_text(t.replace("102500000,0.25233,","102500000,0.25333,")); print("edited 1 value")'
```

```bash
diff evidence/ivc_mesh_study.csv DELIBERATELY-ALTERED-evidence/ivc_mesh_study.csv
```

```
2c2
< 102500000,0.25233,0.45549
---
> 102500000,0.25333,0.45549
```

Now run the wrapper on the altered folder, against the digests the original
seal recorded in `evidence.json`. No CLI command points the wrapper at an
older seal: `uofa evidence seal` always seals and reads in the same run. So
this step calls the same function the CLI calls:

```bash
python - <<'EOF'
import json, pathlib
from uofa_cli import paths
from uofa_cli.solver import mesh_study
from uofa_cli.weakener_focus import attributable_factors
# The digests the ORIGINAL seal recorded, read from its sidecar.
sealed = {a["path"]: a["sha256"] for a in json.loads(pathlib.Path("evidence.json").read_text())["artifactManifest"]}
studies = mesh_study.load_declaration(pathlib.Path("study.json"), attributable_factors("vv40"))
identity = paths.detection_config(paths.pack_manifest("vv40"))["quantityIdentity"]
records = mesh_study.run_studies(studies, pathlib.Path("DELIBERATELY-ALTERED-evidence"), sealed, identity)
print("\n".join(mesh_study.summarise(records)))
EOF
```

Output:

```
ivc-max-velocity (Discretization error): not run (table-not-sealed)
  the bytes read from ivc_mesh_study.csv are not the bytes the seal recorded
ivc-helicity (Discretization error): not run (table-not-sealed)
  the bytes read from ivc_mesh_study.csv are not the bytes the seal recorded
```

The wrapper hashes the bytes it actually reads and compares them with the
seal. Different bytes, no run, and no number is produced from them.
`not-run` is the assessor's gap, so no W-CV rule fires on it.

### A reported value that disagrees

This example carries no reported index, on purpose. For a reported index that
disagrees with the recomputed one (W-CV-01), see
[`../calcverif-starter/`](../calcverif-starter/README.md), which uses
upstream test data with a made-up reported value.

## What it shows

Both quantities converge monotonically on every triplet, so the tool uses its
many-mesh method (`largeN_mono`). The seal readout:

```
What the mesh study says
  ivc-max-velocity (Discretization error): computed, method largeN_mono
    observed order 3.011, no formal order declared, safety factor 3
    index: 0.001179 relative, 0.0002974 absolute; no reported value
  ivc-helicity (Discretization error): computed, method largeN_mono
    observed order 2.249, no formal order declared, safety factor 3
    index: 0.01908 relative, 0.008691 absolute; no reported value
```

With no formal order the tool uses its larger safety factor (3), and the
record's order agreement is `no-formal-order`. With `--calcverif` the W-CV
rules are loaded and report nothing: no reported index (W-CV-01), an estimate
was computed (W-CV-02), no formal order to compare against (W-CV-03), and
every triplet converges monotonically (W-CV-04). That silence comes from the
rule structure, not from wording.

Upstream notes that its results differ slightly from the publication's own
verification, for two reasons: the publication used a different way of
computing the index, and these values are rounded to five decimals.
