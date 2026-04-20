#!/usr/bin/env bash
# Phase 1 acceptance script — UofA_Adversarial_Gen_Spec_v1.1 §11.4.
#
# Runs all 8 acceptance steps end-to-end against the live Claude API.
# Requires: ANTHROPIC_API_KEY, Java 17+, uofa installed with `pip install -e .[llm]`.
#
# Usage:
#   export ANTHROPIC_API_KEY=sk-ant-...
#   bash tests/adversarial/test_acceptance.sh
#
# Expected budget: ~$1.50-$2.00 against claude-opus-4-7.

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

SPEC=specs/w_ar_05_baseline.yaml
OUT=out/adversarial/w_ar_05
KEY=keys/research

fail() { echo "❌ $1" >&2; exit 1; }
pass() { echo "✓ $1"; }

# ── Step 1: clean output ────────────────────────────────────
rm -rf "$OUT"
mkdir -p "$OUT"
pass "step 1: clean output dir"

# ── Step 2: generate ────────────────────────────────────────
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    fail "ANTHROPIC_API_KEY not set"
fi
uofa adversarial generate --spec "$SPEC" --out "$OUT" --force
pass "step 2: generation complete"

# ── Step 3: manifest + ≥3 variant files ─────────────────────
[ -f "$OUT/manifest.json" ] || fail "step 3: manifest.json missing"
variants=$(ls "$OUT"/*.jsonld 2>/dev/null | wc -l | tr -d ' ')
[ "$variants" -ge 3 ] || fail "step 3: only $variants variants, need >= 3"
pass "step 3: manifest present + $variants variants"

# ── Step 4: each variant passes SHACL ───────────────────────
# `uofa check` exits 1 when C1 integrity fails (expected on unsigned synthetic
# packages), so we capture output with `|| true` and grep locally rather than
# piping (which would trip pipefail).
shacl_fail=0
for f in "$OUT"/*.jsonld; do
    output=$(uofa check "$f" --skip-rules --build 2>&1 || true)
    if ! echo "$output" | grep -q "✓ C2"; then
        shacl_fail=$((shacl_fail + 1))
        echo "  SHACL failed: $(basename "$f")"
    fi
done
[ "$shacl_fail" -eq 0 ] || fail "step 4: $shacl_fail variants failed SHACL"
pass "step 4: all $variants variants pass SHACL"

# ── Step 5: at least one triggers W-AR-05 ───────────────────
hits=0
for f in "$OUT"/*.jsonld; do
    output=$(uofa check "$f" --build 2>&1 || true)
    if echo "$output" | grep -q "W-AR-05"; then
        hits=$((hits + 1))
    fi
done
[ "$hits" -ge 1 ] || fail "step 5: zero W-AR-05 firings across $variants variants"
pass "step 5: $hits/$variants variants trigger W-AR-05"

# ── Step 6: sign refuses synthetic ──────────────────────────
V01=$(ls "$OUT"/*.jsonld | head -1)
if ! uofa keygen "$KEY" 2>/dev/null | grep -q "Private key"; then
    # keygen may have already produced keys — acceptable.
    [ -f "$KEY" ] || fail "step 6: keygen failed and $KEY missing"
fi
sign_output=$(uofa sign "$V01" --key "$KEY" 2>&1 || true)
echo "$sign_output" | grep -q "refusing to sign" \
    || fail "step 6: sign did NOT refuse synthetic (output: $sign_output)"
pass "step 6: sign refuses synthetic"

# ── Step 7: verify detects sed-strip tamper ─────────────────
TAMPERED=$(mktemp -t adv-tamper.XXXXXX.jsonld)
cp "$V01" "$TAMPERED"
# Portable sed: strip the synthetic: true flag.
python - <<PY
from pathlib import Path
p = Path("$TAMPERED")
p.write_text(p.read_text().replace('"synthetic": true', '"synthetic": false'))
PY
verify_output=$(uofa verify "$TAMPERED" 2>&1 || true)
echo "$verify_output" | grep -q "hash does not match" \
    || fail "step 7: verify did NOT detect tamper (output: $verify_output)"
rm -f "$TAMPERED"
pass "step 7: verify detects sed-strip tamper"

# ── Step 8: circularity rejects explicit extract-model override ─
set +e
uofa adversarial generate --spec "$SPEC" --out /tmp/circ_test \
    --model qwen3:4b >/tmp/circ_out 2>&1
circ_exit=$?
set -e
[ "$circ_exit" -eq 4 ] || fail "step 8: expected exit 4, got $circ_exit"
grep -q "circular" /tmp/circ_out \
    || fail "step 8: 'circular' missing from output"
rm -f /tmp/circ_out
pass "step 8: circular model override exits 4"

echo
echo "════════════════════════════════════════════════════════"
echo "  🎉 All 8 acceptance steps passed."
echo "════════════════════════════════════════════════════════"
