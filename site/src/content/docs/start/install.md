---
title: Install
description: Install the UofA CLI locally or open a pre-configured Codespace.
---

## Fastest option: Codespace

[Open in GitHub Codespaces](https://codespaces.new/cloudronin/uofa?quickstart=1) — Python, Java, Maven, and the `uofa` CLI are pre-installed. Skip the local install entirely.

## Local install

```bash
# Install the uofa CLI with the Excel + extract pipelines
pip install -e '.[excel,extract]'

# One-time: detect/install Ollama, pull qwen3.5:4b (~3 GB)
# Skip if you only plan to use hosted LLMs via --model
uofa setup

# Java 17+ and Maven 3.8+ (needed for the rule engine, C3)
java -version   # should show 17+
mvn -version    # should show 3.8+
```

End users installing from PyPI: `pip install 'uofa[excel,extract]'` instead of the editable form.

### What the extras do

| Extra | Adds | Needed for |
|---|---|---|
| `[excel]` | `openpyxl` | `uofa import` from a workbook |
| `[extract]` | `litellm`, `pdfplumber`, `python-docx`, `jinja2`, … | `uofa extract` (LLM-backed evidence pre-fill) and `uofa --explain` |

Omit both if you only work with JSON-LD directly. If you'll only use hosted LLMs (Claude, GPT, Gemini) for extract, you still need `[extract]` (it brings in litellm), but you can skip `uofa setup` — `--model anthropic/claude-...` and friends talk to the provider directly.

### What `uofa setup` does

`uofa setup` is the post-pip step that gets the local extract path working:

- Detects an existing Ollama on the machine (BYO), or downloads a UofA-managed copy
- Pulls the default `qwen3.5:4b` model (~3 GB) — override with `--model`
- Use `--bundle <file>` to install from an offline tarball for air-gapped hosts
- Use `--create-bundle <file>` first on a connected machine to produce that tarball

Run `uofa setup uninstall` to remove the UofA-managed runtime and model later.

## What needs what

| Component | Required for | How |
|---|---|---|
| Python 3.10+ | C1 (integrity) and C2 (SHACL) | system / pyenv / uv |
| openpyxl | `uofa import` (Excel) | `pip install -e '.[excel]'` |
| litellm + readers | `uofa extract` | `pip install -e '.[extract]'` |
| Ollama + `qwen3.5:4b` | local `uofa extract` | `uofa setup` |
| Java 17+ | C3 (Jena rule engine) | OpenJDK or equivalent |
| Maven 3.8+ | Building the Jena fat JAR | one-time |

If Java is unavailable on your machine, run `uofa check FILE --skip-rules` to bypass the rule engine. SHACL validation and signature verification still work.

## Verify the install

```bash
uofa --version
uofa packs                 # list installed domain packs
uofa validate              # validate all bundled examples
uofa setup verify          # optional: extract a known fixture, assert F1 >= 0.95
```

If `uofa validate` reports zero failures, your install is good. `uofa setup verify` additionally confirms the local model produces good output before you point it at real evidence.
