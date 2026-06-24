# syntax=docker/dockerfile:1
#
# UofA Gap-Finder — HuggingFace Docker Space.
#
# One self-contained image: the uofa wheel (open core + vv40 + nasa-7009b, with
# the Jena rule-engine JAR bundled in) + JRE 17 for C3 weakeners + Ollama with
# the qwen3.5:4b extract model baked in + the Gradio app. Evidence is read
# privately in-container; nothing is sent to a third party.
#
# Build from the REPO ROOT (needs src/, packs/, spec/, weakener-engine):
#     docker build -f space/Dockerfile -t uofa-space .
# Run:
#     docker run --rm -p 7860:7860 uofa-space        # CPU (slow extract)
#     docker run --rm --gpus all -p 7860:7860 uofa-space   # GPU (Ollama auto-detects)
#
# The ~3 GB model is the LAST heavy layer so iterating the app code above it
# never re-pulls it.

# ── Stage 1: build the Jena rule-engine JAR ──────────────────────────────────
FROM maven:3-eclipse-temurin-17 AS jar
WORKDIR /build
COPY src/weakener-engine/ ./src/weakener-engine/
RUN cd src/weakener-engine && mvn -q -DskipTests package

# ── Stage 2: build the wheel with the JAR + packs/spec force-included ─────────
FROM python:3.11-slim-bookworm AS wheel
WORKDIR /build
COPY . .
COPY --from=jar /build/src/weakener-engine/target/uofa-weakener-engine-0.1.0.jar \
     src/weakener-engine/target/uofa-weakener-engine-0.1.0.jar
RUN pip install --no-cache-dir hatchling \
 && UOFA_BUNDLE_JAR=1 pip wheel --no-deps -w /wheels .

# ── Stage 3: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    HOME=/home/user \
    OLLAMA_HOST=127.0.0.1:11434 \
    OLLAMA_MODELS=/home/user/.ollama/models \
    UOFA_SPACE_MODEL=qwen3.5:4b \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860

# JRE 17 for the rule engine (C3) + curl/zstd to fetch the pinned Ollama runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
        openjdk-17-jre-headless curl ca-certificates zstd procps \
 && rm -rf /var/lib/apt/lists/*

# Ollama runtime, pinned + arch-aware (matches Dockerfile.appliance).
ARG TARGETARCH
RUN set -eu; \
    case "${TARGETARCH:-amd64}" in \
      amd64) OLLAMA_ARCH=amd64 ;; \
      arm64) OLLAMA_ARCH=arm64 ;; \
      *) echo "unsupported TARGETARCH=${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    curl -fsSL "https://github.com/ollama/ollama/releases/download/v0.21.2/ollama-linux-${OLLAMA_ARCH}.tar.zst" \
        -o /tmp/ollama.tar.zst \
 && tar -I zstd -xf /tmp/ollama.tar.zst -C /usr/local \
 && rm /tmp/ollama.tar.zst \
 && ollama --version

# Install the app: uofa[extract] (from the wheel) + Gradio + lead-capture deps.
COPY --from=wheel /wheels/ /wheels/
COPY space/requirements.txt /tmp/space-requirements.txt
RUN pip install --no-cache-dir --retries 5 --timeout 60 "$(echo /wheels/uofa-*.whl)[extract]" \
 && pip install --no-cache-dir -r /tmp/space-requirements.txt

# HF Spaces run as a non-root user (UID 1000); the baked model must live in a
# dir that user owns, so create the user and pull the model as that user.
RUN useradd -m -u 1000 user
COPY --chown=user:user space/ /home/user/app/space/
USER user
WORKDIR /home/user/app

# Bake the ship-target model (LAST heavy layer; ~3 GB). Air-gap-faithful — no
# pull at run time.
RUN set -eu; \
    ollama serve >/tmp/ollama-build.log 2>&1 & \
    for _ in $(seq 1 60); do curl -sf http://127.0.0.1:11434/api/version >/dev/null 2>&1 && break; sleep 1; done; \
    ollama pull qwen3.5:4b; \
    pkill -f "ollama serve" || true

EXPOSE 7860
ENTRYPOINT ["bash", "space/start.sh"]
