# Stage 2 production launch — operator checklist

**Status: ARMED.** Gate-7 resolved (RELAX), production prompt frozen at **v1.1.0**, credentials in place, smoke and resume verified. Three operator actions remain to fire: disable Mac sleep, install the LaunchAgent, start Day 1. **Arm-only: the author pulls the trigger.**

## Launch summary

The Stage 2 production judgment runs the three-judge ensemble — Judge A `gpt-5.4` (openai), Judge B `gemini-2.5-pro` (gemini), Judge C `Llama-4-Maverick` (hf-llama / SambaNova) — with Judge E `mistral-large-2411` arbitrating the Stage 3b disagreement queue, over the 4,556-package corpus at `dev/build/adversarial/phase2/2026-04-26/judge_ready_bundle.tgz`. The frozen prompt is **v1.1.0** under the **gate-7 RELAX** path: the one permitted tuning iteration (v1.2.0) lifted Judge B's UNCERTAIN accuracy from 20% to 60% but could not be promoted because Judge C's recorded run failed the 80% accuracy gate, so production uses the v1.1.0 baseline with gate 7 relaxed per the spec v1.7 §15.1 #7 amendment (see `GATE7_DECISION.md`). The run is a 5-day multi-day schedule bounded by Gemini's 1,000 RPD cap (950/day), with `thinking_enabled=false` to match calibration, a $400 hard budget stop on an envelope of about $262, and `--resume` idempotency proven (interrupted runs re-judge only missing cases, no duplicates). Fired before June 12, it completes around June 16 to 17, well inside the June 13 to July 4 unattended window.

## Done (verified)
- [x] Gate-7 decision recorded → RELAX, prompt **v1.1.0** (`GATE7_DECISION.md`, `calibration-v5/gate7_result.md`)
- [x] `~/.uofa/judge.env` present, `chmod 600`, four keys set (incl. `SAMBANOVA_API_KEY`)
- [x] Smoke green: 3 trio judges on v1.1.0 produce valid verdicts; Judge E proven in calibration v5
- [x] Resume-proof: idempotent re-run skips done cases; interruption re-judges only the missing case; zero duplicates

## Operator actions to fire
1. **Disable sleep** (needs sudo): `sudo pmset -a sleep 0 disablesleep 1`. Keep the Mac powered and on the network June 13 – July 4. launchd does not wake a sleeping Mac or back-fill missed days.
2. **Install the LaunchAgent:**
   ```
   cp dev/tools/scripts/com.uofa.judge-daily.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.uofa.judge-daily.plist
   ```
3. **Fire Day 1** now rather than waiting for the 09:00 schedule:
   ```
   bash dev/tools/scripts/run_judge_daily.sh
   ```
   (The wrapper already defaults `UOFA_PROMPT_VERSION=v1.1.0`.) launchd re-runs it daily at 09:00 local; `--resume` makes each pass idempotent.

## The command the wrapper runs (reference)
```
uofa adversarial judge \
  --in dev/build/adversarial/phase2/2026-04-26/judge_ready_bundle.tgz \
  --judges openai,gemini,hf-llama \
  --out dev/build/adversarial/phase3/production/run-1/ \
  --prompt-version v1.1.0 --concurrency 5 \
  --concurrency-per-judge "gemini=20,openai=10,hf-llama=10" \
  --max-requests-per-judge "gemini=950" --max-cost 400 --resume
```

## Last-mile go / no-go (operator confirms)
- [ ] Calibration v5 and Day-1 on different UTC days, or Day-1 Gemini cap at 900 (the v5 run was 2026-06-10; firing 2026-06-11+ is clear)
- [ ] Mac sleep disabled; powered and networked for the window
- [ ] LaunchAgent loaded
- [ ] First pass started; `daily_status.log` shows a line

## Monitoring
`tail dev/build/adversarial/phase3/production/daily_status.log` → one line per run: `rc`, prompt version, spend to date, error count, per-judge case counts. **Watch Judge C** — it showed a 5/30 schema-failure rate in calibration v5; `--resume` self-heals these across passes, but a persistent high C-failure rate slows completion and adds re-judge cost. Done when all judges reach ~4,556. Stage 3 triage (low-confidence routing already wired, default on) and Stage 4 adjudication resume on the author's return.
