#!/usr/bin/env bash
# Commit + push the Stage 2 production run progress so another clone can
# `git pull` and resume. On-demand and best-effort — NOT called by the
# unattended judge wrapper (git is kept out of the run path so judging stays
# bulletproof). Pushes over HTTPS via the gh credential helper (works while
# the 1Password SSH agent is down). Run this on the ACTIVE runner before any
# cross-machine handoff. See dev/build/adversarial/phase3/production/RESUME.md.
set -uo pipefail

REPO="${UOFA_REPO:-/Users/vishnu/Library/CloudStorage/Dropbox/Praxis/uofa_github}"
cd "$REPO" || { echo "repo not found: $REPO"; exit 1; }
PROD="dev/build/adversarial/phase3/production"

# Stage only durable state: the per-judge JSONL, the manifests, and the daily
# status line. Never the runtime scratch (run.log, launchd.*.log, the lock).
git add "$PROD"/run-1/judgments_*.jsonl 2>/dev/null || true
git add "$PROD"/run-1/*manifest*.json 2>/dev/null || true
[ -f "$PROD/daily_status.log" ] && git add "$PROD/daily_status.log" 2>/dev/null || true

if git diff --cached --quiet; then
  echo "sync_run: nothing new to push"; exit 0
fi

counts=""
for f in "$PROD"/run-1/judgments_*.jsonl; do
  [ -e "$f" ] && counts="$counts $(basename "$f" .jsonl)=$(wc -l < "$f" | tr -d ' ')"
done

git commit --no-gpg-sign -q -m "run(stage2): progress$counts" || { echo "sync_run: commit failed"; exit 1; }

HELPER=(-c credential.helper='' -c credential.helper='!gh auth git-credential')
URL="https://github.com/cloudronin/uofa.git"
# Rebase onto the remote first (single-runner model means this is normally a
# no-op), then push. If the push is rejected, the commit is safe locally.
git "${HELPER[@]}" pull --rebase --no-edit "$URL" main >/dev/null 2>&1 || true
if git "${HELPER[@]}" push "$URL" HEAD:main; then
  echo "sync_run: pushed$counts"
else
  echo "sync_run: push failed (commit is local — retry, or resolve a rebase conflict from a second runner)"; exit 1
fi
