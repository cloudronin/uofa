#!/usr/bin/env bash
# Phase 3 Stage 2 — unattended daily judge pass (spec Part 3.4).
#
# Sources the four production credentials, runs ONE idempotent --resume pass
# over the 4,556-package bundle, and appends a one-line status to
# daily_status.log. Safe to run daily from launchd/cron: --resume skips
# already-judged cases, the Gemini daily cap halts each pass once it is hit,
# and --max-cost hard-stops the spend. A mid-run kill loses at most one
# in-flight case (the runner streams per-task writes).
#
# Overridable via env: UOFA_REPO, UOFA_JUDGE_ENV, UOFA_PYTHON,
# UOFA_PROMPT_VERSION (set to v1.2.0 ONLY if gate-7 PASS; default v1.1.0).
set -uo pipefail

REPO="${UOFA_REPO:-/Users/vishnu/Library/CloudStorage/Dropbox/Praxis/uofa_github}"
ENV_FILE="${UOFA_JUDGE_ENV:-$HOME/.uofa/judge.env}"
PY="${UOFA_PYTHON:-/Users/vishnu/miniconda3/bin/python}"
UOFA="$(dirname "$PY")/uofa"
PROMPT_VERSION="${UOFA_PROMPT_VERSION:-v1.1.0}"
BUNDLE="$REPO/dev/build/adversarial/phase2/2026-04-26/judge_ready_bundle.tgz"
OUT="$REPO/dev/build/adversarial/phase3/production/run-1"
STATUS_LOG="$REPO/dev/build/adversarial/phase3/production/daily_status.log"
mkdir -p "$OUT" "$(dirname "$STATUS_LOG")"

stamp() { date -u +%FT%TZ; }

# 1. Credentials. chmod-600 file; Judge C (SambaNova) needs SAMBANOVA_API_KEY,
#    NOT HF_TOKEN — the provider does not fall back to HF_TOKEN.
if [ ! -f "$ENV_FILE" ]; then
  echo "$(stamp) FATAL missing_env_file $ENV_FILE" >> "$STATUS_LOG"; exit 78
fi
set -a; . "$ENV_FILE"; set +a
for v in OPENAI_API_KEY GEMINI_API_KEY SAMBANOVA_API_KEY MISTRAL_API_KEY; do
  if [ -z "${!v:-}" ]; then
    echo "$(stamp) FATAL unset_key $v" >> "$STATUS_LOG"; exit 78
  fi
done

# 2. One judge pass (idempotent; daily Gemini RPD cap; $400 hard budget stop).
"$UOFA" adversarial judge \
  --in "$BUNDLE" \
  --judges openai,gemini,hf-llama \
  --out "$OUT" \
  --prompt-version "$PROMPT_VERSION" \
  --concurrency 5 \
  --concurrency-per-judge "gemini=20,openai=10,hf-llama=10" \
  --max-requests-per-judge "gemini=950" \
  --max-cost 400 \
  --resume >> "$OUT/run.log" 2>&1
RC=$?

# 3. One-line end-of-day status: per-judge case counts, spend to date, errors.
counts=""
for f in "$OUT"/judgments_*.jsonl; do
  [ -e "$f" ] || continue
  counts="$counts $(basename "$f" .jsonl)=$(wc -l < "$f" | tr -d ' ')"
done
spend="?"
if [ -f "$OUT/cost_manifest.json" ]; then
  spend=$("$PY" -c "import json,sys;print(f\"{json.load(open(sys.argv[1])).get('running_total_usd',0):.2f}\")" "$OUT/cost_manifest.json" 2>/dev/null || echo "?")
fi
errs=$(grep -ciE 'error|exception|traceback' "$OUT/run.log" 2>/dev/null || echo 0)
echo "$(stamp) rc=$RC prompt=$PROMPT_VERSION spend=\$$spend errors=$errs cases:$counts" >> "$STATUS_LOG"
exit $RC
