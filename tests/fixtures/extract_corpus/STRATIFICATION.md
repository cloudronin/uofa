# UofA Extract Eval Corpus — Stratification

Source: `Product Requirements/UofA_Extract_Prompt_Iteration_Spec_v1.md` §3.

This corpus is **synthetic by construction**. It exists to (a) catch prompt
brittleness across format and domain variation that the two real cases
(Morrison + aero HPT) cannot expose, and (b) provide a held-out test set so
future prompt edits can be measured rather than guessed.

## Stratification dimensions

| Dimension | Values | Rationale |
|---|---|---|
| Standard | `vv40` (13 factors), `nasa-7009b` (19 factors) | Both packs ship; both have published case studies. |
| Domain | `cfd`, `fea`, `cht` (coupled thermal-fluid) | Three distinct numerical regimes, varying terminology. |
| Quality | `complete`, `sparse`, `ambiguous` | Real evidence ranges from well-documented to under-specified to internally contradictory. |
| Format | `report-md`, `memo`, `slides` | Format variance stresses the chunk-and-prompt path. |

## Cell counts

| Split | Standards × Domains | Bundles per cell | Total |
|---|---|---|---|
| dev  | 2 × 3 = 6 cells | 5 | **30** |
| test | 2 × 3 = 6 cells | 3 (+2 fillers) | **20** |

The dev/test split is locked at corpus generation time. The test set is
sentinel-protected (see `test/.test_set_lock`) and the batch harness must
refuse to run it unless `--allow-test` is passed AND the prompt version
string contains neither `iter` nor `dev`.

## Quality × format combinations within each cell

**Dev (5 per cell):** chosen so each cell exercises all 3 qualities and all 3
formats, with mild over-sampling on `complete`/`sparse` (more common in the
wild) and `report-md`/`memo` (more common evidence shapes).

| Slot | Quality | Format |
|---|---|---|
| 1 | complete  | report-md |
| 2 | sparse    | memo |
| 3 | ambiguous | slides |
| 4 | complete  | memo |
| 5 | sparse    | report-md |

**Test (3 base per cell, diagonal only):**

| Slot | Quality | Format |
|---|---|---|
| 1 | complete  | report-md |
| 2 | sparse    | memo |
| 3 | ambiguous | slides |

**Test fillers (2 extras to reach 20):**

| Bundle | Quality | Format |
|---|---|---|
| `bundle_vv40_cfd_009` | complete  | memo |
| `bundle_nasa_fea_009` | ambiguous | memo |

These fillers test format×quality crosses the diagonal misses, without
disturbing the per-cell symmetry of the base 18 test bundles.

## Bundle ID convention

`bundle_<std>_<dom>_<NNN>` where:
- `<std>` ∈ {`vv40`, `nasa`} (`nasa` is shorthand for the `nasa-7009b` pack)
- `<dom>` ∈ {`cfd`, `fea`, `cht`}
- `<NNN>` zero-padded; `001-005` are dev, `006-009` are test

Example: `bundle_vv40_cfd_001` is the first dev bundle for V&V 40 + CFD
(slot 1: complete, report-md). `bundle_nasa_fea_009` is the test filler for
NASA-7009B + FEA (ambiguous, memo).

## Bundle structure

```
bundle_<id>/
├── source/                     # 1-3 evidence documents (any format)
│   ├── report.md              # or memo.md, slides.md
│   └── (optional) appendix.md
├── ground_truth.json          # canonical extract output (v0.5.x JSON-LD)
└── metadata.json              # {standard, domain, quality, format, ...}
```

`source/` may contain `.md`, `.txt`, `.csv`, `.docx`, or `.pdf` depending on
the format slot. `report-md` and `memo` produce markdown; `slides` produces a
markdown file in slide-style notation. Real-world `docx`/`pdf` formats are
covered by the existing Morrison + aero fixtures, not this synthetic corpus.

## Manifest files

- `dev_manifest.json` — 30 dev bundle entries with full stratification
- `test_manifest.json` — 20 test bundle entries with full stratification

These are the source of truth for the corpus generator and the batch harness.
The generator reads them to know what to produce; the harness reads them to
know what to score. Bundle directories that exist on disk but aren't in the
manifest are ignored. Bundles in the manifest but missing on disk are
treated as a generation failure.

## Anti-overfit guards (spec §5.3, §10)

- **Test set never inspected during iteration.** The 20 test bundles get
  generated alongside the 30 dev bundles in one corpus build, then are
  isolated. Hand-verification spot-checks 30% of dev only.
- **`.test_set_lock` sentinel file** lives in `test/`. The batch harness
  refuses to score the test set unless `--allow-test` is explicitly passed
  AND `--prompt-version` matches neither `iter` nor `dev`.
- **Generation prompt overfit risk.** If the corpus generation prompt and
  the extract prompt are both written with the same "good" formatting in
  mind, the corpus may be artificially easy. The corpus generator
  explicitly varies format, terminology, and ordering. Verification spot-
  checks for cases where source phrasing differs from the canonical factor
  name (e.g., "mesh refinement study" instead of "discretization error").
