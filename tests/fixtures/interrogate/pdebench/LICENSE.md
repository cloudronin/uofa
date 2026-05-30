# PDEBench breadth-check fixtures — LICENSE PRECONDITION (gate, read first)

**Status: empty by design.** No PDEBench data is committed here yet.

PDEBench (NeurIPS 2022, DaRUS doi:10.18419/darus-2986 data, darus-2987 models)
is the cross-PDE breadth check confirming the surrogate pack + SIP are not
airfoil-specific. PDEBench code is MIT and most data is CC-BY — **but parts of
the suite fall under a Nvidia (NLE) academic-use-only carve-out.**

## Precondition — nothing lands in this directory until ALL of the following hold

1. **Per-file license confirmed CC-BY.** For each small baseline/reference slice
   you intend to commit, confirm it is CC-BY and **NOT** under the NLE
   academic-use-only carve-out. Check the specific DaRUS record for that file.
2. **Attribution preserved.** Keep the upstream attribution and the DaRUS DOI
   with each committed file.
3. **Per-file license manifest.** Record every committed file in a
   `LICENSE_MANIFEST.json` in this directory with fields:
   `{ "file", "license" (e.g. "CC-BY-4.0"), "source_doi", "attribution" }`.

Only CC-BY-confirmed slices may be vendored as committed fixtures. AirfRANS
(ODbL share-alike) is **never** committed — it is pulled on demand by the eval
harness (`make interrogate-corpus`, `UOFA_AIRFRANS_DIR`).

## Why a gate, not a convenience

Committing an NLE-carve-out file here would relicense it under the repo's
Apache-2.0 umbrella by implication and ship it to every clone. The breadth-check
test (`tests/surrogate/test_pdebench_breadth.py`) is skipped while this
directory holds no `LICENSE_MANIFEST.json` + data, so CI stays green and the
precondition cannot be silently bypassed.
