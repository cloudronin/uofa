#!/usr/bin/env bash
# Phase 2.5 Phase A — production CLI hook validation
# Generates ~20 NC packages via the v0.5.12.1 production CLI to confirm
# the post-LLM hook block (envelope / offset rationale / SA stubs) fires
# on real LLM output.
#
# Usage:
#   ./run_phase_a.sh [/path/to/anthropic.key] [out_dir]
#
# Defaults: /tmp/anthropic_test.key, /tmp/v0512_1_phase_a
#
# The key file is sourced inline into ANTHROPIC_API_KEY for the duration
# of this Bash invocation. Claude Code's sandbox redacts the user's
# *pre-existing* ANTHROPIC_API_KEY env var, but inline-set values within
# a single Bash call persist (verified empirically). The key is never
# echoed.

set -e

KEY_FILE="${1:-/tmp/anthropic_test.key}"
OUT_DIR="${2:-/tmp/v0512_1_phase_a}"

if [ ! -s "$KEY_FILE" ]; then
    echo "FATAL: key file not present or empty: $KEY_FILE" >&2
    echo "Write the new ANTHROPIC_API_KEY to that path (e.g. via your shell):" >&2
    echo "  printf '%s' 'sk-ant-...' > $KEY_FILE" >&2
    exit 1
fi

export ANTHROPIC_API_KEY="$(cat "$KEY_FILE")"
unset ANTHROPIC_BASE_URL  # avoid Claude Code proxy redirection

echo "=== Phase A: production CLI hook validation ==="
echo "  out: $OUT_DIR"
echo "  key length: ${#ANTHROPIC_API_KEY}  (must be > 0)"
echo "  --max-cost: \$10 (cap with ~100% headroom over expected ~\$5 spend)"
echo "  --parallel: 3"
echo

# Cost preview first (no LLM calls)
echo "=== Cost preview ==="
uofa adversarial run \
    --batch specs/negative_controls \
    --out "$OUT_DIR" \
    --max-cost 10 \
    --parallel 3 \
    --cost-preview

echo
echo "=== Live generation ==="
uofa adversarial run \
    --batch specs/negative_controls \
    --out "$OUT_DIR" \
    --max-cost 10 \
    --parallel 3

echo
echo "=== Done ==="
echo "Generated NC packages in: $OUT_DIR"
echo "Run audit: python tools/phase2_5/audit_phase_a.py $OUT_DIR"
