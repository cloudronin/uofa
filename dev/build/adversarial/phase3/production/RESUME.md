# Stage 2 production run — status + cross-machine resume

**Decision:** gate-7 RELAX → prompt **v1.1.0** (see [`../GATE7_DECISION.md`](../GATE7_DECISION.md)).
**Panel:** A `openai/gpt-5.4`, B `gemini/gemini-2.5-pro`, C `Llama-4-Maverick` **via OpenRouter** (re-routed 2026-07-16 after SambaNova deprecated the model; the first ~1,180 C judgments were on SambaNova); arbiter E `mistral-large-2411` (Stage 3b).
**Budget:** ~$262 envelope, `--max-cost 400` hard stop.
**Corpus:** 4,556 packages (`../../phase2/2026-04-26/judge_ready_bundle.tgz`).

## Progress — STAGE 2 COMPLETE (2026-07-20)

| Judge | unique / 4,556 |
|---|---:|
| A (openai `gpt-5.4`) | **4,556 ✅** |
| B (gemini `gemini-2.5-pro`) | **4,556 ✅** |
| C (llama / OpenRouter) | **4,556 ✅** |

**All 4,556 cases judged by all three judges.** Total spend ~$174 (envelope ~$262, cap $400). The final pass ran to completion without hitting the Gemini cap (672 requests, exactly the remainder). Nothing further to run for Stage 2; next are Stage 3 triage and Stage 4 adjudication.


## How resume works

The per-judge JSONL in `run-1/` **is** the resume state. `--resume` skips any case already complete across **all** judges; a case missing from any judge is re-judged for all judges. When judges are unevenly complete (as during the Judge C outage) this leaves **duplicate rows** in the already-complete judges — harmless, since triage dedups by `case_id`, but it inflates raw line counts and spend. Pulling these files onto another clone lets it continue exactly where this one left off.

## Move the run to a different computer

Run **one** machine at a time, or the two clones diverge and their pushes conflict.

**1. On the machine you're leaving** (the current runner): push the latest, then stop its scheduler.
```
bash dev/tools/scripts/sync_run.sh
launchctl unload ~/Library/LaunchAgents/com.uofa.judge-daily.plist
```

**2. On the new machine:**
```
git pull
```
- **Credentials** (never in git): `cp dev/tools/scripts/judge.env.example ~/.uofa/judge.env`, fill the 4 keys — `OPENAI_API_KEY`, `GEMINI_API_KEY`, **`OPENROUTER_API_KEY`** (Judge C), `MISTRAL_API_KEY` — then `chmod 600 ~/.uofa/judge.env`.
- **Python env**: a Python ≥3.10 with this repo installed (`pip install -e '.[judge]'`). Note its `python` and `uofa` paths.
- **Keep awake**: `sudo pmset -a sleep 0 disablesleep 1`.

**3. Fire / schedule on the new machine.** If its paths differ from this Mac, pass overrides (the wrapper reads `UOFA_REPO`, `UOFA_PYTHON`, `UOFA_JUDGE_ENV`):
```
UOFA_REPO="$PWD" UOFA_PYTHON="$(command -v python)" \
  bash dev/tools/scripts/run_judge_daily.sh        # one pass now; --resume continues
```
For the daily schedule, edit the absolute paths in `dev/tools/scripts/com.uofa.judge-daily.plist` to the new machine, `cp` it to `~/Library/LaunchAgents/`, then `launchctl load` it.

## Keeping the remote current

This commit is a snapshot; the active runner keeps judging (~950 more/day) without auto-pushing (git is deliberately kept out of the unattended wrapper so judging stays bulletproof). **Before any handoff, run `bash dev/tools/scripts/sync_run.sh` on the active runner** to push the latest, then `git pull` on the target.

## When complete (~4,556 per judge)

Stage 3 triage (`uofa adversarial triage` — low-confidence routing already wired, default on) and Stage 4 adjudication are the next phases, out of scope for this run.
