# Mesh study tables for the calcverif wrapper tests

Each file is named by where its numbers come from.

| Prefix | Source |
|---|---|
| `upstream_` | Inputs from FDA SimEval `test/test_calcverif.py` at commit `4a70fd3b364c0d4aa14d49a433ba7c4994c04cc3`. Upstream's own expected values are the oracle. `upstream_elements_unsorted.csv` holds upstream's element-count case with its rows deliberately out of order. |
| `synthetic_` | Made up for one edge case: a zero value on the finest mesh, a non-number, too few levels. No study behind them. |
| `morrison_` | Byte copy of `packs/vv40/examples/morrison/source/mesh_convergence_study.csv`. It is used **only** to exercise the four-level `largeN_mono` path. No reported value is ever attached to it, and no test compares it with anything. The original is not touched. |

Tests that show a reported index disagreeing with a recomputed one use `upstream_` or `synthetic_` data only.
