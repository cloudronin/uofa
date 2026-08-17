# INV-14 — least-blast-radius fix for the stale `out_dir` pointers

Status: **RECOMMENDATION, with the patch written and validated**
Date: 2026-08-16
Feeds: A4 (the disclosed patch the ruling anticipated), Phase 2 reproducibility

## The defect, scoped

`uofa adversarial analyze` produces zero rows on every committed Phase 2 corpus
and exits 0. `batch_manifest.json` records each spec's `out_dir` under the
generation-time output root, which has been renamed twice — `out/` → `dev/build/`
in Phase D, then nested under `dev/` in Phase E.

**The breakage is total, not partial:**

| Corpus | stale `out_dir` | intent-dir naming |
|---|---|---|
| `2026-04-26` (M5) | **381 / 381** | `confirm_existing/`, `gap_probe/`, `interaction/`, `negative_controls/` |
| `holdout-…-v0513` | **39 / 39** | `ce/`, `gp/`, `int/`, `nc/` |
| `holdout-…-v0515` | **90 / 90** | `negative_controls/` |

Note the two layouts differ, so any fix that hard-codes subdirectory names works
on one corpus and not the other.

`out_dir` enters at exactly **one line** ([classifier.py:367](src/uofa_cli/adversarial/classifier.py))
and is used for exactly two things: locating `manifest.json`, and resolving
relative package paths. Both targets live inside the batch directory the caller
already passes as `--in`.

## Candidates, by blast radius

| # | Fix | Touches | Radius | Verdict |
|---|---|---|---|---|
| **A** | **Re-anchor on `--in` when `out_dir` misses** | ~14 lines, one function | Code only. Frozen artifacts untouched. No behaviour change when `out_dir` is valid. Fixes all three corpora and any future rename | **RECOMMENDED** |
| B | Rewrite `out_dir` in the committed manifests | 510 entries across 3+ frozen artifacts | Changes content hashes of frozen Phase 2 outputs; needs freeze disclosure; fixes nothing for the next rename | Rejected |
| C | Ship a sidecar path-map file | New artifact + the same code change A needs | Strictly worse than A — same code edit, plus a file to keep in sync | Rejected |
| D | `--rebase-paths` flag | ~10 lines + docs | Requires the operator to know the corpus is broken. The failure is **silent**, so they will not | Rejected |

B is what the ruling anticipated ("a repaired pointer file can ship later as a
disclosed patch"). A is strictly cheaper and touches nothing frozen, so it is
offered as the better form of the same intent.

## The recommended patch

At the existing miss-branch, before warning and skipping:

```python
recovered = next(iter(sorted(in_dir.glob(f"*/{spec_id}/manifest.json"))), None)
if recovered is None:
    warn(f"  (no per-spec manifest for {spec_id}; skipping)")
    continue
per_spec_manifest_path = recovered
spec_out_dir = recovered.parent
```

Globbing one level is what makes it layout-agnostic — it covers
`confirm_existing/` and `ce/` without naming either.

### Validation

| Check | Result |
|---|---|
| Resolution across all three corpora | **510 / 510** specs resolve |
| Ambiguous `spec_id` (glob could match two dirs) | **none** in any corpus — 381, 39 and 90 unique spec dirs |
| Patched analyzer on the v0.5.13 holdout | **CE 287/378 = 75.9%** |
| Independent cross-check (`run_arm_g.py`, different code path) | **287/378 = 75.9%** — agrees |
| Committed `summary.csv`, produced at v0.5.13 | 288/378 = 76.2% — differs by the one package of the W-CON-01 guard, as expected |
| `tests/adversarial` + `tests/scripts` | **786 passed, 4 skipped** |

Two independent implementations agreeing on 287, and the 288 → 287 delta landing
exactly on the one known rule change, is the strongest available evidence that the
fix recovers the *right* rows rather than merely some rows.

**Behaviour when `out_dir` is valid is unchanged** — the fallback sits inside the
existing `if not …exists()` branch, so a healthy corpus never reaches it.

## CORRECTION — there is no silent exit 0

**I reported that `analyze` exits 0 on an empty result. That was wrong, and the
error was mine.**

`classifier.py:841-842` already does the right thing:

```python
if not rows:
    warn("no per-package rows produced; nothing to write")
    return 1
```

Tested directly against a batch whose specs cannot resolve:

```
$ uofa adversarial analyze --in /tmp/emptybatch --out /tmp/emptyout   # no pipe
real exit code: 1

$ uofa adversarial analyze --in /tmp/emptybatch --out /tmp/emptyout | tail -1
piped exit code: 0
```

Every observation of "exit code 0" in this session came through
`... 2>&1 | tail`, and a shell pipeline reports the **last** command's status.
`tail` succeeded. The analyzer did not.

**So no exit-code change is landed, and none is needed.** The tool has been
failing loudly the entire time.

Two consequences worth carrying:

1. **The silent-null catalogue entry for this instance is wrong as first written**
   and is corrected in [INV-6 addendum 2](INV-6-findings.md). The defect here is
   the stale pointer alone — real, total, and fixed by the patch above. The
   "silent" half was my measurement.
2. **It is instance #6 of the catalogue's own pattern, produced by me**, and the
   one where the plausible-looking wrong result would have had shipped code blamed
   for a defect it does not have. `| tail` swallowing an exit code is exactly the
   shape the catalogue describes: nothing threw, the number looked like an answer,
   and the answer was about the wrong process.

## Coverage statement

**Searched.** `classifier.py` lines 320-420 read in full; repo-wide grep for
`out_dir` across `src/uofa_cli/adversarial/`. All three committed corpora probed
for stale-pointer counts, intent-dir naming, spec-dir counts and `spec_id`
collisions. Patch applied and the shipped analyzer run end to end on the v0.5.13
holdout, cross-checked against an independent implementation and against the
committed `summary.csv`.

**Not verified.**
- The patched analyzer was run on **one** corpus (v0.5.13 holdout). Resolution was
  proved for all three; a full analyze run on M5 (381 specs, 6,281 CE packages)
  would take hours of Jena time and was not performed. Worth doing before the fix
  is relied on for M5-derived numbers.
- `spec_path` (used for the D1 per-COU baseline key at
  [classifier.py:384](src/uofa_cli/adversarial/classifier.py)) is **also** a
  generation-time path — `/tmp/holdout_specs/ce/w-al-01.yaml` in the v0.5.13
  batch. It is already wrapped in a bare `except: pass`, so it fails silently and
  degrades `baseline_key` to None rather than breaking the run. **Not fixed here**,
  and it means per-COU recall columns are empty on the committed corpora. Same
  defect class, separate decision, and it should be checked before any per-COU
  figure is quoted.
- The patch is **uncommitted pending the author's call** on whether a code fix is
  the right form of the disclosed patch.
