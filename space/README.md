---
title: UofA Gap-Finder
emoji: 🔎
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
short_description: Find credibility-evidence gaps vs V&V 40 or NASA-7009B
---

# UofA Gap-Finder

Upload a folder of model-credibility evidence and get a fast, honest readout of
your gaps — which credibility factors are missing and which weakeners fire —
against **ASME V&V 40** or **NASA-STD-7009B**.

The flow: upload (or try the sample) → the rule router picks a standard → the
model reads your evidence **privately, inside this Space** → you confirm what it
understood (status only) → a free completeness + weakeners summary.

It reports completeness and weakeners; it does **not** stamp an Accepted /
Not-Accepted verdict — that's a human decision.

## Privacy

Evidence is read by a local model running in this container (no third-party
API). Each request uses a temporary directory that is deleted afterwards;
documents and the generated bundle are never persisted, and payloads are not
logged.

## Build & run (local)

The image is split so HF's builder stays under its 30-min limit:
`space/Dockerfile.base` carries the heavy layers (JAR, wheel, JRE, Ollama
runtime, baked ~3 GB model) and is prebuilt in CI → GHCR; `space/Dockerfile` is
the thin `FROM <base> + COPY space/` that HF actually builds.

For a self-contained **local** build, build the base first (from the **repo
root** — it needs `src/`, `packs/`, `spec/`, and the weakener engine), then the
thin app image on top of it:

```bash
# 1. heavy base (JAR + wheel + Ollama + ~3 GB model) — tagged so step 2 finds it
docker build -f space/Dockerfile.base -t ghcr.io/cloudronin/uofa-demo-base:latest .
# 2. thin app image on top, then run
docker build -f space/Dockerfile -t uofa-space .
docker run --rm -p 7860:7860 uofa-space            # CPU (extraction is slow)
docker run --rm --gpus all -p 7860:7860 uofa-space # GPU (Ollama auto-detects)
```

Then open http://localhost:7860.

Set `UOFA_SPACE_MODEL=mock` to drive the UI without running the model (returns
canned extraction data) — useful for development.

## What's inside

- `app.py` — Gradio Blocks wizard (thin UI).
- `wizard.py` / `pipeline.py` — step logic and the in-process pipeline over `uofa`.
- `router.py` — pre-extract standard router.
- `summary.py` — completeness + weakeners computation.
- `Dockerfile` / `start.sh` — image with Ollama + JRE 17 + qwen3.5:4b baked in.

## Deploying to a HuggingFace Space

HuggingFace Docker Spaces expect the `Dockerfile` at the Space repo root. When
publishing, place this Space's contents at the root (or mirror the `uofa` repo
and ensure the build context includes `src/`, `packs/`, and `spec/`).
