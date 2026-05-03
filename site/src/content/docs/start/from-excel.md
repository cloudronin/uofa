---
title: Excel on-ramp
description: Fill an Excel workbook and convert it to a signed JSON-LD evidence package in one command.
---

For simulation engineers who prefer working in a spreadsheet, the Excel import pipeline produces a signed JSON-LD evidence package in a single command.

## One-command import

```bash
# Start from the filled example or a pack template
cp packs/vv40/templates/uofa-starter-filled.xlsx my-assessment.xlsx

# Edit my-assessment.xlsx in Excel — fill in your project details,
# credibility factors, validation results, and decision

# Import, sign, and validate in one step
uofa import my-assessment.xlsx --sign --key keys/research.key --check --pack vv40
```

The Excel template has five sheets:

| Sheet | What goes here |
|---|---|
| Assessment Summary | Project name, COU, decision, dates |
| Model & Data | Model URI, datasets, source documents |
| Validation Results | Per-result name, metric, comparator |
| Credibility Factors | Per-factor name, required level, achieved level, rationale |
| Decision | Decision text, decided by, criteria reference |

Factor names and categories are pre-populated. You fill in levels, rationale, and status. The import command generates URIs, assigns `factorStandard`, tracks provenance, and writes a complete JSON-LD file.

## Pack-specific behaviour

| Pack | Factor count | Level range | Notes |
|---|---|---|---|
| `vv40` | 13 | 1–5 | ASME V&V 40-2018 taxonomy. Default. |
| `nasa-7009b` | 19 | 0–4 | NASA-STD-7009B. `assessmentPhase` auto-assigned. |

Pass `--pack nasa-7009b` to use the NASA template:

```bash
uofa import my-assessment.xlsx --pack nasa-7009b --sign --key keys/aero.key --check
```

## What the importer guarantees

| Feature | Detail |
|---|---|
| URI generation | Stable per-row URIs from sheet position and project name |
| Provenance | An `ImportActivity` entry with timestamp, source file, and tool version |
| Error messages | Sheet name and cell reference (e.g. `[Credibility Factors!C7] Required Level must be 1-5`) |
| SHACL-synced | Factor names, level ranges, and enums are generated from SHACL via `uofa schema --emit python` |

## Where to start

Either:

- Copy `packs/vv40/templates/uofa-starter-filled.xlsx` and edit your details over the working example, or
- Copy `packs/vv40/templates/vv40-template.xlsx` for an empty form
