---
title: "Authoring on-ramp: evidence to signed UofA"
description: From an evidence folder to a signed, validated UofA package — extract proposes, you review, import signs.
---

This is the fastest path from the evidence you already have to a signed, validated UofA package. It does not require JSON-LD or RDF. You work in a spreadsheet you already know how to read, and the tool does the rest.

The path has three stages: extract, review, import. Extract is optional. If you would rather fill the workbook by hand, skip to step 2.

## 1. Extract a first pass from your evidence

Point `uofa extract` at a folder of source material. It reads the documents and proposes values for each credibility factor, one sheet per factor.

```bash
uofa extract ./evidence --pack vv40 -o assessment.xlsx
```

Use `--pack nasa-7009b` for the aerospace factor set. Extract is model-assisted, so it is fast but not authoritative. It is a starting point for review, not a verdict.

**Before your first extract:** the local extract path needs a model on disk. Install with `pip install 'uofa[extract]'` (or `pip install -e '.[extract]'` from a clone), then run `uofa setup` once to pull the default `qwen3.5:4b` model (~3 GB). See [Install](/start/install/) for the full prerequisites. If you'll only ever pass `--model` for a hosted LLM, skip `uofa setup`.

**On sensitive evidence:** extract runs fully local with a model served by Ollama, so nothing leaves your machine. A hosted model is also supported through the `--model` flag if your evidence is not sensitive and you want higher extraction quality. See [LLM configuration](/docs/llm-config/).

## 2. Review the workbook

Open `assessment.xlsx`. Each factor is on its own sheet, with confidence coloring that shows where extraction was uncertain. Check those first. Correct levels, add the acceptance criteria the model could not infer, and fill anything left blank.

This step is the point of the whole on-ramp. Extract makes the gaps machine-checkable, but the engineer is the one who decides what is true. Nothing downstream trusts a value you have not reviewed.

If you skipped extract, start here: open a blank workbook scaffolded by `uofa init`, and fill it in directly.

## 3. Import to a signed package

One command turns the reviewed workbook into signed, validated JSON-LD, with completeness and integrity checks built in.

```bash
$ uofa import assessment.xlsx --pack vv40 --sign --key research.key --check
  ✓ signed with ed25519
  ✓ SHACL Complete profile conforms
  → assessment.jsonld
```

The result is portable, tamper-evident, and ready for the rule engine. From here, run [`uofa rules`](/reference/cli/) to detect weakeners, or [`uofa diff`](/reference/cli/) to compare two contexts of use.

## What you get

Minutes from an evidence folder to a signed package a reviewer can verify without reading the prose behind it. The spreadsheet is where humans review. The rule engine is where machines verify. The two stay separate on purpose.
