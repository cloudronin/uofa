#!/usr/bin/env bash
# Container entrypoint: bring up the local Ollama daemon, pre-warm the baked
# model so the first user doesn't eat the load spike, then launch the Gradio app.
set -euo pipefail

MODEL="${UOFA_SPACE_MODEL:-qwen3.5:4b}"

echo "[start] launching ollama daemon…"
ollama serve >/tmp/ollama.log 2>&1 &

# Wait for the daemon to accept connections.
for _ in $(seq 1 60); do
  if curl -sf http://127.0.0.1:11434/api/version >/dev/null 2>&1; then
    echo "[start] ollama is up"
    break
  fi
  sleep 1
done

# Pre-warm: load the model into memory and keep it resident.
echo "[start] pre-warming ${MODEL}…"
curl -sf http://127.0.0.1:11434/api/generate \
  -d "{\"model\":\"${MODEL}\",\"prompt\":\"ok\",\"stream\":false,\"keep_alive\":\"1h\"}" \
  >/dev/null 2>&1 || echo "[start] pre-warm skipped (model loads on first request)"

echo "[start] launching Gradio app on ${GRADIO_SERVER_PORT:-7860}…"
exec python -m space.app
