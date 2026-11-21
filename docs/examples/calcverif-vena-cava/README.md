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

## Run it

From this folder, with `pip install 'uofa[calcverif]'`:

```bash
uofa evidence seal evidence --mesh-study study.json -o evidence.json
```

```bash
uofa keygen demo.key
```

```bash
uofa import ../../../packs/vv40/templates/uofa-starter-filled.xlsx --evidence evidence.json --pack vv40 -o vena-cava.jsonld --sign --key demo.key --check --calcverif
```

The vv40 starter workbook stands in for an assessment here. It is a
placeholder, not the Craven study's credibility assessment.

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
