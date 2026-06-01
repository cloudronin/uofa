#!/usr/bin/env bash
# UofA appliance demo entrypoint: signals-in → explained, signed, verdict-free
# evidence-out. PhysicsNeMo (the signal source) feeds the appliance through the
# SIP interface; the in-container stock model decodes the flags as labeled
# reference-annotation (never the adjudicator).
set -euo pipefail

WORK=/work
ADAPTERS=/app/examples/sip_adapters
SCOPE=/app/docker/appliance/demo_scope.json
PHYSICSNEMO_URL="${PHYSICSNEMO_URL:-http://physicsnemo:8000}"

echo "══════════════════════════════════════════════════════════════════"
echo "  UofA concept appliance — surrogate-confidence demo"
echo "══════════════════════════════════════════════════════════════════"

# 1) In-container Ollama (the stock explainer endpoint, [llm] base_url).
echo "→ starting the stock explainer (Ollama: qwen2.5:7b)…"
ollama serve >/tmp/ollama.log 2>&1 &
for _ in $(seq 1 60); do
  curl -sf http://127.0.0.1:11434/api/version >/dev/null 2>&1 && break
  sleep 1
done

# 2) Wait for the PhysicsNeMo signal source (compose starts it first).
echo "→ waiting for the PhysicsNeMo signal source at ${PHYSICSNEMO_URL}…"
for _ in $(seq 1 120); do
  curl -sf "${PHYSICSNEMO_URL}/health" >/dev/null 2>&1 && break
  sleep 2
done
curl -sf "${PHYSICSNEMO_URL}/health" || { echo "PhysicsNeMo not reachable"; exit 1; }

# 3) Ephemeral measurement key + the canonical benchmark points (pulled FROM the
#    signal source so the surrogate predictions and the reference truth align).
curl -sf "${PHYSICSNEMO_URL}/benchmark" -o "${WORK}/benchmark.json"
python - <<'PY'
import json
from pathlib import Path
import numpy as np
from uofa_cli import integrity
key = Path("/work/sip.key")
if not key.exists():
    integrity.generate_keypair(key)
b = json.loads(Path("/work/benchmark.json").read_text())
np.savez("/work/bench.npz", inputs=np.array(b["inputs"], dtype=float),
         input_names=np.array(b["input_names"]))
PY

# 4) MEASURE: PhysicsNeMo signals → signed, verdict-free evidence bundle.
echo ""
echo "→ interrogating the surrogate (PhysicsNeMo signals → signed evidence)…"
uofa interrogate \
  --adapter   "${ADAPTERS}/physicsnemo_adapter.py:PhysicsNeMoAdapter" \
  --reference "${ADAPTERS}/physicsnemo_reference.py:PhysicsNeMoReference" \
  --benchmark "${WORK}/bench.npz" \
  --scope     "${SCOPE}" \
  -o "${WORK}/bundle.json" --key "${WORK}/sip.key"

# 5) Map the signed bundle → surrogate-pack COU (the v2 reader).
python /app/docker/appliance/sip_to_cou.py "${WORK}/bundle.json" "${WORK}/sip.pub" "${WORK}/cou.jsonld"
cd "${WORK}"

# 6) GUARDRAIL — the basic, engineer-commanded action leg closes the "with
#    confidence" loop: the firings → a signed, action-region response (restrict
#    the COU when the surrogate is out of competence). It ACTS; it never
#    adjudicates, and exposes no Product-B fixing logic (spec §6).
echo ""
echo "→ basic guardrail (engineer-commanded) acting on the firings…"
uofa guardrail "${WORK}/cou.jsonld" --pack surrogate --key "${WORK}/sip.key" -o "${WORK}/cou_guarded.jsonld"

# 7) CHECK + EXPLAIN. `check` runs the derivation pre-pass (→ W-SURR-03 on the
#    out-of-envelope evaluation point) + rules + OOS, with --explain decoding each
#    firing as reference-annotation. `rules` alone skips the derivation, so the
#    out-of-envelope flag would never materialize.
echo ""
echo "══════════════════════════════════════════════════════════════════"
echo "  Weakener firings + reference-annotation (decode, NOT a verdict)"
echo "  The signed evidence adjudicates; the explanation only decodes."
echo "══════════════════════════════════════════════════════════════════"
# `uofa check` returns non-zero when C1/C2 fail; the mapped COU is intentionally
# NOT an independently-signed Complete package (the signed artifact is the SIP
# bundle above), so a non-zero check exit here is EXPECTED — the C3 firings +
# the explanation are the demo payload. The 7B explainer runs on CPU, so also
# bound it (a GPU host removes the wait — the explanation is think-time work).
EXPLAIN_TIMEOUT="${EXPLAIN_TIMEOUT:-600}"
timeout "${EXPLAIN_TIMEOUT}" uofa check "${WORK}/cou.jsonld" --pack surrogate --explain \
  || echo "  (check exit non-zero — expected: the COU is not independently signed; or the CPU explanation exceeded ${EXPLAIN_TIMEOUT}s)"

echo ""
echo "✓ Demo complete: signals-in → guardrail action + explained, signed, verdict-free evidence-out."
echo "  Signed bundle:  ${WORK}/bundle.json   (verify: uofa verify ${WORK}/bundle.json)"
echo "  Guarded COU:    ${WORK}/cou_guarded.jsonld   (signed, action-region guardrailAction)"
