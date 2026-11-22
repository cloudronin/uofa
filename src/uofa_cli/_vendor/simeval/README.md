# Vendored: FDA SimEval `calcverif`

This folder holds one module from the FDA SimEval project, copied without change.

| | |
|---|---|
| Source | https://github.com/OSEL-DAM/SimEval |
| Commit | `4a70fd3b364c0d4aa14d49a433ba7c4994c04cc3` |
| Upstream path | `src/calcverif.py` |
| License | CC0-1.0 (`LICENSE`), plus the FDA software disclaimer (`fda_software_disclaimer.txt`) |

## Files and their sha256

| File | sha256 |
|---|---|
| `calcverif.py` | `e4ddc15558ce64c8c55253c4d7efc7c6679f52e47dc0e740f42872c33bef5a5d` |
| `LICENSE` | `6d489af6292662d9e36d34ce49423784984a5f6e41d7b58f49b01264df59fa03` |
| `fda_software_disclaimer.txt` | `b8ed549f22c7bc7a7a3048e016016dac5c00a2f91f7b90a8611f32a36f788cf4` |

`tests/solver/test_simeval_vendor.py` asserts each digest. `__init__.py` files
in this folder and its parent are empty and are not upstream files.

## Unmodified

`calcverif.py` is byte-identical to the upstream file at the commit above. It is
never edited here. UofA calls it through `uofa_cli.solver.mesh_study`, which
reads the tool's results and recovers values the tool computes but does not
return (safety factor, convergence type) by calling the tool's own methods.

## Derived work notice

UofA's calculation verification feature is derived from FDA SimEval. Use of this
code in UofA does not imply endorsement by the FDA and confers no advantage in
regulatory decisions. See `fda_software_disclaimer.txt`.

## Dependencies

The module imports numpy, pandas, scipy and matplotlib at the top of the file.
They are not core UofA dependencies. Install them with:

    pip install 'uofa[calcverif]'
