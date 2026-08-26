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

The flow: upload (or try the sample) → the rule router picks a standard → a
hosted model reads your evidence → you confirm what it understood (status only)
→ a free completeness + weakeners summary → download the assurance package.

It reports completeness and weakeners; it does **not** stamp an Accepted /
Not-Accepted verdict — that's a human decision.

## The downloadable package

"Download UofA package" gives you a zip built by the same code path as the CLI's
`uofa import`. The file that carries the assurance is `uofa.jsonld`; the report,
manifest, public key, and instructions beside it are convenience copies.

```
unzip uofa-pack-*.zip
uofa verify uofa.jsonld \
  --pubkey keys/uofa-issuer.pub \
  --decision-pubkey keys/demo-reviewer.pub
```

**What a valid signature means here.** Only that the file is unmodified since
this demo produced it. It is not a review and not an acceptance decision. The
signing key is a *demonstration issuer key* held by the demo, not a research or
production key, and not anyone's decision key — so a demo package can never be
mistaken for a formally issued one (it does not verify against the default trust
anchor; `--pubkey` is required, deliberately).

The public key travels inside the zip so verification works offline. A trust
anchor shipped inside the artifact it validates only proves self-consistency, so
compare it against this independent copy:

```
keys/uofa-issuer.pub    sha256:ead2e1e1068f8c6da14b2c9c384e4d00d8900308ad2e406fe294330ce0edd81d
keys/demo-reviewer.pub  sha256:3605a146f4880d9f7a29db6ef5629655091d2ecd0c2b9919cbe49d90d65d83c8
```

## Privacy

**Your documents leave this Space.** Evidence is read by a hosted model
(Together AI), so the text of what you upload is sent there to be processed.
Together's data-handling terms govern what happens to it in transit and at
rest; check them before uploading anything you would not send to a third-party
API.

What remains true: this Space stores nothing. Each request uses a temporary
directory that is deleted afterwards, and payloads are not logged by us. That
is a claim about OUR handling, not about the provider's -- turning off our own
logging does not stop theirs.

**If your evidence is confidential, do not upload it here.** Run the CLI on
your own machine instead, where a local model reads it and nothing leaves your
environment:

```bash
pip install "uofa[extract]"
uofa extract ./evidence --pack vv40
```

Pasting a public model card sends only text that is already public.

One exception, by design: if you generate a package, that zip is written to a
separate directory so it survives long enough for you to download it. It is
deleted when you hit "Start over", when you run another analysis, and in any
case within 30 minutes. Your uploaded documents are never retained.

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
