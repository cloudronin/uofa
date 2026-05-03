---
title: Install
description: Install the UofA CLI locally or open a pre-configured Codespace.
---

## Fastest option: Codespace

[Open in GitHub Codespaces](https://codespaces.new/cloudronin/uofa?quickstart=1) — Python, Java, Maven, and the `uofa` CLI are pre-installed. Skip the local install entirely.

## Local install

```bash
# Install the uofa CLI (includes all Python dependencies + Excel import)
pip install -e '.[excel]'

# Java 17+ and Maven 3.8+ (only needed for the rule engine, C3)
java -version   # should show 17+
mvn -version    # should show 3.8+
```

The `[excel]` extra installs `openpyxl` for Excel import. Omit it if you only work with JSON-LD directly.

## What needs what

| Component | Required for | Notes |
|---|---|---|
| Python 3.10+ | C1 (integrity) and C2 (SHACL) | Installed via `pip install -e .` |
| openpyxl | `uofa import` (Excel) | Installed via `pip install -e '.[excel]'` |
| Java 17+ | C3 (Jena rule engine) | OpenJDK or equivalent |
| Maven 3.8+ | Building the Jena fat JAR | Only needed once |

If Java is unavailable on your machine, run `uofa check FILE --skip-rules` to bypass the rule engine. SHACL validation and signature verification still work.

## Verify the install

```bash
uofa --version
uofa packs        # list installed domain packs
uofa validate     # validate all bundled examples
```

If `uofa validate` reports zero failures, your install is good.
