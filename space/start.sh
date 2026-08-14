#!/usr/bin/env bash
# Container entrypoint.
#
# This used to bring up a local Ollama daemon, wait up to 60s for it, and then
# BLOCK on a pre-warm request until ~3 GB of weights were resident -- Gradio did
# not start listening until all of that finished, which was a large share of the
# Space's cold start. Inference is now a hosted API call, so there is nothing to
# warm and the app can start immediately.
set -euo pipefail

echo "[start] launching Gradio app on ${GRADIO_SERVER_PORT:-7860}…"
exec python -m space.app
