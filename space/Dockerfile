# syntax=docker/dockerfile:1
#
# UofA Gap-Finder — HuggingFace Docker Space (THIN image; this is what HF builds).
#
# Every heavy layer (Jena JAR, uofa wheel, JRE 17, Ollama runtime, and the ~3 GB
# qwen3.5:4b model) lives in the prebuilt BASE image, built by CI and pushed to
# GHCR — see space/Dockerfile.base and .github/workflows/deploy-space.yml. HF's
# builder only pulls that base and copies the app code, so the build finishes in
# a couple of minutes, comfortably inside HF's 30-minute build limit. (Baking the
# 3 GB model on HF's own builder is what caused "Build error: Job timeout".)
#
# The base is pinned to :latest; CI's `base` job refreshes it immediately before
# each Space sync, so `FROM …:latest` always matches the current source.
#
# NOTE: the GHCR package `uofa-demo-base` must be PUBLIC for HF's anonymous
# builder to pull it (one-time toggle — see space/DEPLOY.md §1).

FROM ghcr.io/cloudronin/uofa-demo-base:latest

# App code only — editing a .py here re-runs just this cheap COPY on HF's builder.
COPY --chown=user:user space/ /home/user/app/space/

USER user
WORKDIR /home/user/app
EXPOSE 7860
ENTRYPOINT ["bash", "space/start.sh"]
